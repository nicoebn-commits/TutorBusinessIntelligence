"""Quiz-Page: generiert Multiple-Choice-Quizze aus der Wissensbasis.

- Themen-Scope via Freitext + dem geteilten Kategorie-Filter
  (Vorlesungen / Übungen / Altklausuren).
- Fragen werden vom LLM strikt aus dem abgerufenen Vorlesungskontext erzeugt
  (eine korrekte Option, plus Begründung & Quelle je Frage).
- Auswertung passiert deterministisch im Client; Ergebnis lebt nur in der
  Session (keine Persistenz).
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.chain import generate_quiz, warm_up, DIFFICULTY_LEVELS  # noqa: E402
from rag.ui import (  # noqa: E402
    apply_theme,
    render_topnav,
    render_header,
    render_section,
    render_slide_footer,
    model_status_label,
    CATEGORY_LABELS,
)


apply_theme(page_title="BI-Tutor · Quiz")
render_topnav(active="quiz")
render_header(
    title="Business Intelligence & Analytics: Quiz",
    tagline="Selbsttest mit Multiple-Choice-Fragen aus den Vorlesungs-, Übungs- und Klausurmaterialien",
    status_label=model_status_label(),
)


@st.cache_resource(show_spinner="BI-Tutor wird initialisiert (einmalig pro Session) …")
def _warmup_once():
    warm_up()
    return True


_warmup_once()


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
def _clear_answers() -> None:
    for key in [k for k in st.session_state if k.startswith("quiz_ans_")]:
        del st.session_state[key]


def _reset_quiz() -> None:
    st.session_state.pop("quiz", None)
    st.session_state.pop("quiz_submitted", None)
    _clear_answers()


# ---------------------------------------------------------------------------
# Konfiguration / Generierung
# ---------------------------------------------------------------------------
quiz = st.session_state.get("quiz")

render_section(
    kicker="Selbsttest",
    title="Quiz erstellen",
    lead=(
        "Wählen Sie ein Thema und den Materialumfang. Der Tutor erzeugt daraus "
        "Multiple-Choice-Fragen ausschließlich auf Basis der hinterlegten "
        "Materialien und nennt zu jeder Frage die Quelle."
    ),
)

with st.expander("Quiz-Einstellungen", expanded=quiz is None):
    with st.form("quiz_config"):
        topic = st.text_input(
            "Thema (optional)",
            placeholder="z. B. Star-Schema, ETL-Prozess, OLAP …",
            help="Leer lassen, um Fragen aus einer zufälligen Auswahl des Materials zu ziehen.",
        )
        c1, c2 = st.columns(2)
        with c1:
            categories = st.multiselect(
                "Materialumfang",
                options=list(CATEGORY_LABELS.keys()),
                default=list(CATEGORY_LABELS.keys()),
                format_func=lambda c: CATEGORY_LABELS[c],
                help="Worauf die Fragen sich stützen. Beispiel: nur Altklausuren.",
            )
        with c2:
            difficulty = st.select_slider(
                "Schwierigkeit",
                options=list(DIFFICULTY_LEVELS),
                value="mittel",
            )
        num_questions = st.slider(
            "Anzahl Fragen", min_value=3, max_value=10, value=5, step=1
        )
        generate = st.form_submit_button("Quiz generieren", type="primary")

    if generate:
        _reset_quiz()
        with st.spinner("Fragen werden erstellt …"):
            try:
                new_quiz = generate_quiz(
                    topic,
                    categories=categories,
                    num_questions=num_questions,
                    difficulty=difficulty,
                )
            except Exception as e:
                st.error(f"Fehler bei der Quiz-Erstellung: {e}")
                st.stop()
        if new_quiz.error and not new_quiz.questions:
            st.error(new_quiz.error)
        else:
            st.session_state["quiz"] = new_quiz
            st.session_state["quiz_submitted"] = False
            st.rerun()


quiz = st.session_state.get("quiz")
if not quiz or not quiz.questions:
    render_slide_footer()
    st.stop()


# ---------------------------------------------------------------------------
# Quiz beantworten
# ---------------------------------------------------------------------------
st.divider()
meta_bits = [f"{len(quiz.questions)} Fragen", f"Schwierigkeit: {quiz.difficulty}"]
if quiz.topic:
    meta_bits.insert(0, f"Thema: {quiz.topic}")
st.caption(" · ".join(meta_bits))


def _render_form() -> None:
    with st.form("quiz_form"):
        for i, q in enumerate(quiz.questions):
            st.markdown(f"**Frage {i + 1}.** {q.question}")
            st.radio(
                "Antwort auswählen",
                options=list(range(len(q.options))),
                format_func=lambda x, q=q: q.options[x],
                index=None,
                key=f"quiz_ans_{i}",
                label_visibility="collapsed",
            )
            st.divider()
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Auswerten", type="primary", use_container_width=True)
    if submitted:
        st.session_state["quiz_submitted"] = True
        st.rerun()


def _render_results() -> None:
    total = len(quiz.questions)
    correct = sum(
        1
        for i, q in enumerate(quiz.questions)
        if st.session_state.get(f"quiz_ans_{i}") == q.correct_index
    )
    pct = round(100 * correct / total) if total else 0

    m1, m2 = st.columns([1, 3])
    with m1:
        st.metric("Ergebnis", f"{correct}/{total}", delta=f"{pct} %")
    with m2:
        st.progress(correct / total if total else 0.0)
        if pct >= 80:
            st.success("Sehr gut! Du beherrschst dieses Thema sicher.")
        elif pct >= 50:
            st.info("Solide Basis – einzelne Punkte lohnt es zu wiederholen.")
        else:
            st.warning("Noch ausbaufähig – schau dir die markierten Quellen an.")

    st.divider()

    for i, q in enumerate(quiz.questions):
        ans = st.session_state.get(f"quiz_ans_{i}")
        is_correct = ans == q.correct_index
        head = "✅" if is_correct else "❌"
        st.markdown(f"**{head} Frage {i + 1}.** {q.question}")
        for j, opt in enumerate(q.options):
            if j == q.correct_index:
                st.markdown(f"- **{opt}** &nbsp;✓ _richtig_", unsafe_allow_html=True)
            elif j == ans:
                st.markdown(f"- {opt} &nbsp;✗ _deine Wahl_", unsafe_allow_html=True)
            else:
                st.markdown(f"- {opt}")
        if ans is None:
            st.caption("Nicht beantwortet.")
        if q.explanation:
            st.info(q.explanation)
        src = q.source or {}
        if src.get("document"):
            st.caption(
                f"Quelle: {src['document']} · Folie {src.get('slide', '?')} "
                f"· {src.get('module', '?')}"
            )
        st.divider()

    a1, a2 = st.columns(2)
    with a1:
        if st.button("Nochmal versuchen", use_container_width=True):
            st.session_state["quiz_submitted"] = False
            _clear_answers()
            st.rerun()
    with a2:
        if st.button("Neues Quiz", type="primary", use_container_width=True):
            _reset_quiz()
            st.rerun()


if st.session_state.get("quiz_submitted"):
    _render_results()
else:
    _render_form()


render_slide_footer()
