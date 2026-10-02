"""Forum-Page: Threads + Replies fuer den BI-Tutor.

Routing via Query-Param `?thread=<id>`:
- ohne Param  -> Listenansicht aller Threads
- mit Param   -> Detailansicht eines Threads
"""
from __future__ import annotations

import html
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.ui import (  # noqa: E402
    apply_theme,
    render_topnav,
    render_header,
    render_section,
    render_slide_footer,
    model_status_label,
    role_badge_html,
    status_pill_html,
)
from forum import (  # noqa: E402
    init_db,
    list_threads,
    get_thread,
    get_posts,
    create_thread,
    reply_to_thread,
    toggle_pinned,
    toggle_resolved,
    toggle_endorsed,
    available_modules,
    ROLES,
    ROLE_STUDENT,
    ROLE_PROF,
)


init_db()

apply_theme(page_title="BI-Tutor · Forum")
render_topnav(active="forum")
render_header(
    title="Business Intelligence & Analytics: Forum",
    tagline="Austausch zwischen Studierenden, Tutor:innen und Lehrenden",
    status_label=model_status_label(),
)


# ---------------------------------------------------------------------------
# Identity (Sidebar)
# ---------------------------------------------------------------------------
def _identity_block():
    if "forum_identity" not in st.session_state:
        st.session_state.forum_identity = {"name": "", "role": ROLE_STUDENT}

    with st.sidebar:
        st.markdown("### Identität")
        ident = st.session_state.forum_identity
        ident["name"] = st.text_input(
            "Anzeigename",
            value=ident["name"],
            placeholder="z. B. Marie K.",
        )
        ident["role"] = st.selectbox(
            "Rolle",
            options=ROLES,
            index=ROLES.index(ident["role"]),
        )
        st.caption(
            "Name + Rolle werden nur bei Ihren eigenen Beiträgen gespeichert."
        )

        st.divider()
        st.markdown("### Filter")
        st.session_state.setdefault("forum_only_open", False)
        st.session_state.setdefault("forum_only_pinned", False)
        st.session_state.setdefault("forum_module", "(alle)")

        st.session_state.forum_only_open = st.checkbox(
            "Nur offene Threads", value=st.session_state.forum_only_open
        )
        st.session_state.forum_only_pinned = st.checkbox(
            "Nur angepinnte Threads", value=st.session_state.forum_only_pinned
        )
        st.session_state.forum_module = st.selectbox(
            "Modul",
            options=["(alle)"] + available_modules(),
            index=(["(alle)"] + available_modules()).index(st.session_state.forum_module),
        )

    return st.session_state.forum_identity


identity = _identity_block()


def _identity_ready() -> bool:
    return bool(identity["name"].strip())


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
qp = st.query_params
thread_id_str = qp.get("thread")
try:
    thread_id = int(thread_id_str) if thread_id_str else None
except ValueError:
    thread_id = None


def _go(thread_id: int | None) -> None:
    if thread_id is None:
        st.query_params.clear()
    else:
        st.query_params["thread"] = str(thread_id)
    st.rerun()


def _fmt_time(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d.%m.%Y · %H:%M")
    except Exception:
        return iso


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------
def _render_list():
    render_section(
        kicker="Diskussionen",
        title="Beiträge im Forum",
        lead=(
            "Stellen Sie Fragen zur Vorlesung, teilen Sie Hinweise zu Übungen "
            "oder diskutieren Sie Klausurthemen. Beiträge der Lehrenden werden "
            "besonders markiert."
        ),
    )

    threads = list_threads(
        only_open=st.session_state.forum_only_open,
        only_pinned=st.session_state.forum_only_pinned,
        module=(
            None if st.session_state.forum_module == "(alle)"
            else st.session_state.forum_module
        ),
    )

    # Aus dem Dialog kommend? -> Formular auto-oeffnen
    if "forum_prefill" in st.session_state:
        st.session_state["forum_new_open"] = True

    cta_cols = st.columns([1, 3])
    with cta_cols[0]:
        if st.button("Neuer Beitrag", type="primary", use_container_width=True):
            st.session_state["forum_new_open"] = True
            st.rerun()

    if st.session_state.get("forum_new_open"):
        _render_new_thread_form()

    if not threads:
        st.info("Keine Threads passen zu den aktuellen Filtern.")
        return

    for t in threads:
        modifiers = []
        if t.is_pinned:
            modifiers.append("bi-thread--pinned")
        if t.is_resolved:
            modifiers.append("bi-thread--resolved")
        cls = " ".join(["bi-thread", *modifiers])

        excerpt = html.escape(t.body[:220].replace("\n", " ")) + ("…" if len(t.body) > 220 else "")
        meta_bits = [
            role_badge_html(t.role),
            f'<span>{html.escape(t.author)}</span>',
            f'<span>·</span>',
            f'<span>{_fmt_time(t.created_at)}</span>',
        ]
        if t.module:
            meta_bits.append(status_pill_html(t.module, "module"))
        if t.is_pinned:
            meta_bits.append(status_pill_html("Angepinnt", "pinned"))
        if t.is_resolved:
            meta_bits.append(status_pill_html("Beantwortet", "resolved"))

        st.markdown(
            f"""
<div class="{cls}">
  <div>
    <div class="bi-thread__title">{html.escape(t.title)}</div>
    <div class="bi-thread__excerpt">{excerpt}</div>
    <div class="bi-thread__meta">{"".join(meta_bits)}</div>
  </div>
  <div class="bi-thread__count">
    <strong>{t.reply_count}</strong><br>
    <span style="font-size:0.7rem;">Antworten</span>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        # Streamlit-Button als Klick-Wrapper (HTML-Anchors triggern keinen
        # session_state-update zuverlaessig genug fuer Query-Param-Routing)
        if st.button("Beitrag öffnen", key=f"open_thread_{t.id}", use_container_width=True):
            _go(t.id)


def _render_new_thread_form():
    prefill = st.session_state.pop("forum_prefill", None) or {}
    with st.expander("Neuer Beitrag", expanded=True):
        if prefill:
            st.caption(
                "Vorbefüllt aus dem Dialog. Sie können Titel und Antwort vor "
                "dem Posten noch anpassen."
            )
        with st.form("new_thread", clear_on_submit=True):
            title = st.text_input(
                "Titel",
                value=prefill.get("title", ""),
                placeholder="Kurze, präzise Frage",
            )
            body = st.text_area(
                "Beitrag", height=200,
                value=prefill.get("body", ""),
                placeholder="Beschreiben Sie Ihre Frage oder Beobachtung …",
            )
            mcol1, mcol2 = st.columns([2, 1])
            with mcol1:
                module_options = ["(kein)"] + available_modules()
                prefill_module = prefill.get("module")
                try:
                    default_idx = module_options.index(prefill_module) if prefill_module else 0
                except ValueError:
                    default_idx = 0
                module = st.selectbox(
                    "Modul (optional)", options=module_options, index=default_idx,
                )
            with mcol2:
                st.write("")
                submit = st.form_submit_button("Beitrag erstellen", type="primary")
            if submit:
                if not _identity_ready():
                    st.error("Bitte zuerst einen Anzeigenamen in der Sidebar setzen.")
                elif not title.strip() or not body.strip():
                    st.error("Titel und Inhalt dürfen nicht leer sein.")
                else:
                    tid = create_thread(
                        title=title,
                        body=body,
                        author=identity["name"],
                        role=identity["role"],
                        module=None if module == "(kein)" else module,
                    )
                    st.session_state["forum_new_open"] = False
                    _go(tid)
        if st.button("Schließen", key="close_new"):
            st.session_state["forum_new_open"] = False
            st.rerun()


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------
def _render_detail(t):
    back_col, ask_col = st.columns([1, 2])
    with back_col:
        if st.button("← Zurück zur Übersicht", use_container_width=True):
            _go(None)
    with ask_col:
        if st.button(
            "Diese Frage dem Tutor stellen",
            type="primary", use_container_width=True,
            help="Springt zum Dialog und stellt automatisch eine Anfrage mit dem Thread-Titel.",
        ):
            st.session_state["pending_question"] = t.title
            st.session_state["history"] = []
            st.switch_page("app.py")

    posts = get_posts(t.id)

    # Header-Pills
    pills = []
    if t.is_pinned:
        pills.append(status_pill_html("Angepinnt", "pinned"))
    if t.is_resolved:
        pills.append(status_pill_html("Beantwortet", "resolved"))
    if t.module:
        pills.append(status_pill_html(t.module, "module"))
    pill_html = "".join(pills)

    st.markdown(
        f"""
<div style="margin: 0.4rem 0 1rem 0;">
  <div style="display:flex; gap:0.4rem; align-items:center; flex-wrap:wrap; margin-bottom:0.4rem;">
    {pill_html}
  </div>
  <h1 style="font-size:1.6rem; font-weight:700; margin: 0; color:#2b2b2b;">{html.escape(t.title)}</h1>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Aktionen (für Profs)
    if identity["role"] == ROLE_PROF:
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button(
                "Pin entfernen" if t.is_pinned else "Anpinnen",
                key="toggle_pin", use_container_width=True,
            ):
                toggle_pinned(t.id); _go(t.id)
        with a2:
            if st.button(
                "Wieder öffnen" if t.is_resolved else "Als beantwortet markieren",
                key="toggle_resolved", use_container_width=True,
            ):
                toggle_resolved(t.id); _go(t.id)

    # Eröffnungs-Post
    _render_post_block(
        author=t.author, role=t.role, created_at=t.created_at,
        body=t.body, endorsed=False, first=True,
    )

    # Antworten
    for p in posts:
        _render_post_block(
            author=p.author, role=p.role, created_at=p.created_at,
            body=p.body, endorsed=bool(p.is_endorsed), first=False,
            endorse_action=(
                (lambda pid=p.id: (toggle_endorsed(pid), _go(t.id)))
                if identity["role"] == ROLE_PROF else None
            ),
            post_id=p.id,
        )

    # Antwort-Formular
    st.markdown("---")
    if not _identity_ready():
        st.info("Bitte zuerst einen Anzeigenamen in der Sidebar setzen, um zu antworten.")
        return
    with st.form("reply", clear_on_submit=True):
        body = st.text_area(
            "Antwort verfassen", height=140,
            placeholder="Ihre Antwort …",
        )
        send = st.form_submit_button("Antwort senden", type="primary")
        if send:
            if not body.strip():
                st.error("Antwort darf nicht leer sein.")
            else:
                reply_to_thread(
                    thread_id=t.id,
                    body=body,
                    author=identity["name"],
                    role=identity["role"],
                )
                _go(t.id)


def _render_post_block(*, author, role, created_at, body, endorsed, first,
                       endorse_action=None, post_id=None):
    cls = "bi-post"
    if first:
        cls += " bi-post--first"
    if endorsed:
        cls += " bi-post--endorsed"
    body_html = html.escape(body).replace("\n", "<br>")
    endorse_html = (
        '<div class="bi-post__endorse">Empfohlen vom Lehrstuhl</div>'
        if endorsed else ""
    )
    st.markdown(
        f"""
<div class="{cls}">
  <div class="bi-post__author">
    <div class="bi-post__author-name">{html.escape(author)}</div>
    <div>{role_badge_html(role)}</div>
    <div class="bi-post__author-time">{_fmt_time(created_at)}</div>
  </div>
  <div>
    <div class="bi-post__body">{body_html}</div>
    {endorse_html}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    if endorse_action and post_id is not None:
        cols = st.columns([1, 5])
        with cols[0]:
            label = "Endorsement entfernen" if endorsed else "Antwort empfehlen"
            if st.button(label, key=f"endorse_{post_id}", use_container_width=True):
                endorse_action()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if thread_id is not None:
    t = get_thread(thread_id)
    if t is None:
        st.error("Thread nicht gefunden.")
        if st.button("Zur Übersicht"):
            _go(None)
    else:
        _render_detail(t)
else:
    _render_list()


render_slide_footer()
