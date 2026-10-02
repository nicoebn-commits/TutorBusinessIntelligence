"""Evaluation dashboard for the BI-Tutor.

Streamlit page on top of evaluation/run_eval.py:
- Trigger eval runs inline (with --judge toggle, version tag).
- Browse past reports stored in evaluation/results/.
- Show summary metrics + per-case drilldown.
- Compare two report versions side-by-side.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "evaluation" / "results"
CASES_PATH = ROOT / "evaluation" / "test_cases.json"

sys.path.insert(0, str(ROOT))

from rag.ui import (  # noqa: E402
    apply_theme,
    render_topnav,
    render_header,
    render_section,
    render_slide_footer,
    model_status_label,
)

apply_theme(page_title="BI-Tutor · Evaluation")
render_topnav(active="evaluation")
render_header(
    title="Business Intelligence & Analytics: Evaluation",
    tagline="Quantitative Metriken nach Automation.md zuzüglich LLM-as-a-Judge",
    status_label=model_status_label(),
)


# --- Run -------------------------------------------------------------------
render_section(
    kicker="Lauf",
    title="Neuer Eval-Run",
    lead="Die Testfälle aus evaluation/test_cases.json gegen das aktuelle System laufen lassen.",
)

with st.expander("Testfälle (evaluation/test_cases.json)", expanded=False):
    try:
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "id": c["id"],
                        "type": c.get("type"),
                        "category": c.get("category"),
                        "requirement": c.get("requirement"),
                        "priority": c.get("priority"),
                        "in_scope": c.get("in_scope", True),
                        "should_refuse": c.get("should_refuse", False),
                        "question": c["question"],
                    }
                    for c in cases
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Konnte Testfaelle nicht laden: {e}")
        cases = []

run_cols = st.columns([2, 1, 1])
with run_cols[0]:
    version_tag = st.text_input(
        "Versions-Tag",
        value=f"v{datetime.now():%Y%m%d-%H%M}",
        help="Wird im Report-Dateinamen verwendet.",
    )
with run_cols[1]:
    use_judge = st.checkbox(
        "LLM-as-a-Judge",
        value=False,
        help="Zusaetzlicher LLM-Call pro Testfall - kostet mehr Tokens.",
    )
with run_cols[2]:
    st.write("")
    run_clicked = st.button("Eval starten", type="primary", use_container_width=True)


def _run_eval(version: str, judge: bool, cases: list[dict]) -> dict:
    from evaluation.run_eval import _evaluate_case, _summary  # type: ignore

    rows = []
    progress = st.progress(0.0)
    status = st.empty()
    for i, case in enumerate(cases, start=1):
        status.markdown(f"**{i}/{len(cases)}** - `{case['id']}`: {case['question']}")
        try:
            row = _evaluate_case(case, use_judge=judge)
        except Exception as e:
            row = {"id": case["id"], "question": case["question"], "error": str(e), "passed": False}
        rows.append(row)
        progress.progress(i / len(cases))
    progress.empty()
    status.empty()

    summary = _summary([r for r in rows if "error" not in r])
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = RESULTS_DIR / f"{stamp}_{version}.json"
    out_path.write_text(
        json.dumps({"version": version, "summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"path": out_path, "summary": summary, "rows": rows}


if run_clicked and cases:
    result = _run_eval(version_tag, use_judge, cases)
    st.success(f"Fertig. Report: `{result['path'].relative_to(ROOT)}`")
    st.session_state["last_eval_report"] = str(result["path"])
    st.rerun()


st.divider()

# --- Browse reports --------------------------------------------------------
render_section(
    kicker="Reports",
    title="Vergangene Eval-Runs",
    lead="Versionierte Reports auswählen und Metriken vergleichen.",
)

reports = sorted(RESULTS_DIR.glob("*.json"), reverse=True)

if not reports:
    st.info("Noch keine Reports. Starte einen Run oberhalb.")
    st.stop()


def _label(p: Path) -> str:
    return p.stem


select_cols = st.columns(2)
with select_cols[0]:
    primary = st.selectbox(
        "Primaerer Report",
        options=reports,
        format_func=_label,
        index=0,
    )
with select_cols[1]:
    compare_to = st.selectbox(
        "Vergleichs-Report (optional)",
        options=[None, *reports],
        format_func=lambda p: "(keiner)" if p is None else _label(p),
        index=0,
    )


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


primary_data = _load(primary)
compare_data = _load(compare_to) if compare_to else None


# --- Summary metrics -------------------------------------------------------
st.subheader("Zusammenfassung")
summary = primary_data.get("summary", {})

metric_keys = [
    ("pass_rate", "Pass-Rate"),
    ("scope_accuracy", "Scope-Erkennung"),
    ("source_rate", "Quellenquote"),
    ("avg_latency_s", "Latenz ⌀ (s)"),
    ("refusal_rate", "Ablehnungsrate"),
    ("avg_keyword_score", "Keyword-Score ⌀"),
]
cols = st.columns(len(metric_keys))
for c, (k, label) in zip(cols, metric_keys):
    val = summary.get(k)
    delta = None
    if compare_data:
        prev = compare_data.get("summary", {}).get(k)
        if isinstance(val, (int, float)) and isinstance(prev, (int, float)):
            delta = val - prev
            delta = round(delta, 3)
    c.metric(label, val if val is not None else "-", delta=delta if delta else None)

judge_keys = [k for k in summary if k.startswith("judge_avg_")]
if judge_keys:
    st.subheader("LLM-as-a-Judge (Mittelwerte 0-5)")
    j_cols = st.columns(len(judge_keys))
    for c, k in zip(j_cols, judge_keys):
        label = k.replace("judge_avg_", "").capitalize()
        val = summary[k]
        delta = None
        if compare_data:
            prev = compare_data.get("summary", {}).get(k)
            if isinstance(val, (int, float)) and isinstance(prev, (int, float)):
                delta = round(val - prev, 3)
        c.metric(label, val, delta=delta if delta else None)


# --- Per-case table --------------------------------------------------------
st.subheader("Pro Testfall")

rows = primary_data.get("rows", [])
table = pd.DataFrame(
    [
        {
            "id": r.get("id"),
            "passed": r.get("passed"),
            "type": r.get("type"),
            "requirement": r.get("requirement"),
            "scope_ok": r.get("scope_ok"),
            "source_ok": r.get("source_ok"),
            "latency_s": r.get("latency_s"),
            "keyword_score": r.get("keyword_score"),
            "refused": r.get("refused"),
            "judge_overall": (r.get("judge") or {}).get("overall"),
            "question": r.get("question"),
        }
        for r in rows
    ]
)
st.dataframe(table, hide_index=True, use_container_width=True)


# --- Per-case drilldown ----------------------------------------------------
st.subheader("Drilldown")
case_ids = [r.get("id") for r in rows]
pick = st.selectbox("Testfall waehlen", options=case_ids)
selected = next((r for r in rows if r.get("id") == pick), None)

if selected:
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"**Frage:** {selected.get('question')}")
        st.markdown("**Antwort:**")
        st.markdown(selected.get("answer") or "_(keine Antwort)_")
        if selected.get("error"):
            st.error(selected["error"])
        first = selected.get("first_source")
        if first:
            st.caption(
                f"Top-Quelle: {first.get('document')} - Folie {first.get('slide')} "
                f"(Modul {first.get('module')})"
            )
        judge = selected.get("judge")
        if judge:
            st.markdown("**Judge-Bewertung:**")
            st.write(judge)
    with cols[1]:
        st.metric("Passed", "ja" if selected.get("passed") else "nein")
        st.metric("Latency (s)", selected.get("latency_s"))
        st.metric("Sources", selected.get("sources_count"))
        st.metric("Keyword-Score", selected.get("keyword_score"))


# --- Download --------------------------------------------------------------
st.divider()
st.download_button(
    label="Report als JSON herunterladen",
    data=primary.read_text(encoding="utf-8"),
    file_name=primary.name,
    mime="application/json",
)


render_slide_footer()
