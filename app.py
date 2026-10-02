"""Streamlit chat UI for the BI-Tutor RAG prototype.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from rag.chain import stream_answer, warm_up
from rag.config import settings
from rag.ui import (
    apply_theme,
    render_topnav,
    render_header,
    render_section,
    render_kicker,
    render_source_card,
    render_meta,
    render_slide_footer,
    render_slide_toggle,
    model_status_label,
    CATEGORY_LABELS,
)

ROOT = Path(__file__).resolve().parent
TEST_CASES = ROOT / "evaluation" / "test_cases.json"


apply_theme(page_title="BI-Tutor")
render_topnav(active="dialog")
render_header(
    title="Business Intelligence & Analytics: Tutor",
    tagline="Didaktischer Assistent auf Basis der Vorlesungs-, Übungs- und Klausurmaterialien",
    status_label=model_status_label(),
)


@st.cache_resource(show_spinner="BI-Tutor wird initialisiert (einmalig pro Session) …")
def _warmup_once():
    warm_up()
    return True


_warmup_once()


@st.cache_data(show_spinner=False)
def _load_sample_questions() -> list[dict]:
    try:
        cases = json.loads(TEST_CASES.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    cases.sort(key=lambda c: (not c.get("in_scope", True), c.get("priority") != "hoch"))
    return cases[:6]


def _render_sources(
    sources: list[dict],
    retrieval_s: float | None = None,
    *,
    key_prefix: str = "live",
):
    with st.expander("Quellen anzeigen", expanded=False):
        if not sources:
            st.write("_Keine Quellen gefunden._")
            return
        if retrieval_s is not None:
            st.caption(
                f"Retrieval {retrieval_s * 1000:.0f} ms · {len(sources)} Chunks"
            )
        for i, src in enumerate(sources, start=1):
            render_source_card(i, src)
            render_slide_toggle(src, key=f"slide_{key_prefix}_{i}")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Konfiguration")
    st.markdown(
        f"<div style='font-size:0.85rem; line-height:1.7;'>"
        f"<div><span style='color:#6b6f76;'>Modell</span> &nbsp; <code>{settings.openai_model}</code></div>"
        f"<div><span style='color:#6b6f76;'>Top-k</span> &nbsp; {settings.top_k}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### Wissensbasis")
    selected_categories = st.multiselect(
        "Quellen einschränken",
        options=list(CATEGORY_LABELS.keys()),
        default=list(CATEGORY_LABELS.keys()),
        format_func=lambda c: CATEGORY_LABELS[c],
        help=(
            "Worauf der Tutor seine Antwort stützen darf. Standard: alle "
            "Materialien. Beispiel: nur Altklausuren, um klausurnah zu üben."
        ),
    )
    if not selected_categories:
        st.caption("Keine Auswahl → es werden alle Materialien durchsucht.")
    elif len(selected_categories) < len(CATEGORY_LABELS):
        scope = ", ".join(CATEGORY_LABELS[c] for c in selected_categories)
        st.caption(f"Aktiver Filter: {scope}")

    st.divider()
    st.markdown("### Dialog")
    use_history = st.checkbox(
        "Folgefragen-Kontext aktiv",
        value=True,
        help=(
            "Bei Folgefragen wird die Frage automatisch in eine eigenständige "
            "Frage umformuliert und die letzten Turns werden weitergegeben."
        ),
    )
    if st.button("Dialog zurücksetzen", use_container_width=True):
        st.session_state.history = []
        st.session_state.pop("pending_question", None)
        st.rerun()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []


# ---------------------------------------------------------------------------
# Welcome (empty state)
# ---------------------------------------------------------------------------
if not st.session_state.history:
    render_section(
        kicker="Lernziel",
        title="Stellen Sie Ihre Frage zur Vorlesung",
        lead=(
            "Der Tutor antwortet ausschließlich auf Basis der hinterlegten "
            "Vorlesungs-, Übungs- und Klausurmaterialien und benennt seine "
            "Quellen mit Folie und Modul."
        ),
    )

    render_kicker("Beispielfragen")
    samples = _load_sample_questions()
    cols = st.columns(2)
    for i, s in enumerate(samples):
        with cols[i % 2]:
            label = s.get("question", "")
            cat = s.get("category") or ""
            req = s.get("requirement") or ""
            help_txt = f"Typ {s.get('type')} – {cat} ({req})" if s.get("type") else None
            if st.button(label, key=f"hero_sample_{s['id']}", help=help_txt, use_container_width=True):
                st.session_state.pending_question = label
                st.rerun()


# ---------------------------------------------------------------------------
# Chat history replay
# ---------------------------------------------------------------------------
for idx, turn in enumerate(st.session_state.history):
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn["role"] == "assistant":
            if turn.get("rewritten_query"):
                st.caption(f"Umformuliert für Retrieval: {turn['rewritten_query']}")
            _render_sources(
                turn.get("sources", []), turn.get("retrieval_s"),
                key_prefix=f"hist{idx}",
            )
            render_meta(
                latency_s=turn.get("latency_s"),
                refused=bool(turn.get("refused")),
                sources_count=len(turn.get("sources") or []),
            )
            if not turn.get("refused"):
                # vorhergehende user-Frage finden
                prior_q = ""
                for h in reversed(st.session_state.history[:idx]):
                    if h["role"] == "user":
                        prior_q = h["content"]; break
                if st.button(
                    "Im Forum diskutieren", key=f"forum_jump_hist_{idx}",
                    help="Neuer Forum-Thread mit dieser Frage und der Tutor-Antwort.",
                ):
                    sources = turn.get("sources") or []
                    top_module = sources[0].get("module") if sources else None
                    cite = ""
                    if sources:
                        s0 = sources[0]
                        cite = (
                            f"\n\n_Tutor-Antwort, gestützt auf {s0.get('document')}, "
                            f"Folie {s0.get('slide')} ({s0.get('module')})._"
                        )
                    st.session_state["forum_prefill"] = {
                        "title": prior_q[:140],
                        "body": turn["content"] + cite,
                        "module": top_module,
                    }
                    st.switch_page("pages/3_Forum.py")


# ---------------------------------------------------------------------------
# Input + response cycle
# ---------------------------------------------------------------------------
pending = st.session_state.pop("pending_question", None)
typed = st.chat_input("Frage zur BI-Vorlesung stellen …")
prompt = pending or typed

if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history_payload = (
            [
                {"role": h["role"], "content": h["content"]}
                for h in st.session_state.history[:-1]
                if h["role"] in ("user", "assistant")
            ]
            if use_history
            else []
        )

        status_box = st.status("Suche relevante Vorlesungs-Folien …", expanded=True)
        try:
            handle = stream_answer(
                prompt, history=history_payload, categories=selected_categories
            )
        except Exception as e:
            status_box.update(label="Fehler beim Retrieval", state="error")
            st.error(f"Fehler beim Retrieval: {e}")
            st.stop()

        with status_box:
            if selected_categories and len(selected_categories) < len(CATEGORY_LABELS):
                scope = ", ".join(CATEGORY_LABELS[c] for c in selected_categories)
                st.write(f"**Quellen-Filter aktiv:** {scope}")
            if handle.rewritten_query:
                st.write(f"**Frage umformuliert:** _{handle.rewritten_query}_")
            st.write(
                f"**{len(handle.sources)} relevante Chunks** gefunden "
                f"({handle.retrieval_s * 1000:.0f} ms)."
            )
            st.write("Antwort wird generiert …")
        status_box.update(label="Antwort wird gestreamt …", state="running")

        try:
            full_text = st.write_stream(handle.tokens)
        except Exception as e:
            status_box.update(label="Fehler beim Streaming", state="error")
            st.error(f"Fehler beim Streaming: {e}")
            st.stop()

        status_box.update(
            label=f"Fertig in {handle.latency_s:.2f} s",
            state="complete",
            expanded=False,
        )
        _render_sources(
            handle.sources, handle.retrieval_s,
            key_prefix=f"new{len(st.session_state.history)}",
        )
        render_meta(
            latency_s=handle.latency_s,
            refused=handle.refused,
            sources_count=len(handle.sources),
        )

        # Forum-Verlinkung: Frage + Antwort in das Forum übernehmen
        if not handle.refused:
            top_module = handle.sources[0].get("module") if handle.sources else None
            cite = ""
            if handle.sources:
                s0 = handle.sources[0]
                cite = (
                    f"\n\n_Tutor-Antwort, gestützt auf {s0.get('document')}, "
                    f"Folie {s0.get('slide')} ({s0.get('module')})._"
                )
            if st.button(
                "Im Forum diskutieren", key=f"forum_jump_{len(st.session_state.history)}",
                help="Erstellt einen neuen Thread mit dieser Frage und der Tutor-Antwort als Aufhänger.",
            ):
                st.session_state["forum_prefill"] = {
                    "title": prompt[:140],
                    "body": (full_text or handle.answer) + cite,
                    "module": top_module,
                }
                st.switch_page("pages/3_Forum.py")

    st.session_state.history.append(
        {
            "role": "assistant",
            "content": full_text or handle.answer,
            "sources": handle.sources,
            "latency_s": round(handle.latency_s, 2),
            "retrieval_s": round(handle.retrieval_s, 3),
            "refused": handle.refused,
            "rewritten_query": handle.rewritten_query,
        }
    )


render_slide_footer()
