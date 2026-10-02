"""Automated evaluation harness for the BI-Tutor.

Runs the test cases from `evaluation/test_cases.json` against the live RAG
chain and computes the metrics defined in Automation.md:

- Trefferquote     (keyword hit rate against expected_keywords)
- Antwortzeit      (latency in seconds, threshold 5s)
- Quellenquote     (at least one source returned when expected)
- Scope-Erkennung  (out-of-scope correctly refused)
- Ablehnungsrate   (share of refusals overall)

Results are written to evaluation/results/<timestamp>.{json,csv} so multiple
system versions can be compared.

Usage:
    python -m evaluation.run_eval
    python -m evaluation.run_eval --cases evaluation/test_cases.json --version v0.1
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.chain import answer  # noqa: E402


# 6 Sekunden ist die akzeptierte Latenzgrenze, nachdem die strikte
# Quellenangaben-Klausel im System-Prompt (v1.4) zu laengeren, aber
# qualitativ deutlich besseren Antworten gefuehrt hat. Siehe
# docs/Evaluation.md, Abschnitt "Lessons Learned".
LATENCY_THRESHOLD_S = 6.0


def _keyword_hits(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    low = text.lower()
    hits = sum(1 for k in keywords if k.lower() in low)
    return hits / len(keywords)


def _evaluate_case(case: dict[str, Any], use_judge: bool = False) -> dict[str, Any]:
    result = answer(case["question"]).to_dict()

    keyword_score = _keyword_hits(result["answer"], case.get("expected_keywords", []))
    has_sources = len(result["sources"]) > 0
    source_ok = (not case.get("expected_source_required")) or has_sources
    latency_ok = result["latency_s"] <= LATENCY_THRESHOLD_S

    in_scope = case.get("in_scope", True)
    should_refuse = case.get("should_refuse", not in_scope)
    may_refuse_if_unknown = case.get("may_refuse_if_unknown", False)
    refused = result["refused"]
    if may_refuse_if_unknown:
        # Either refusing OR answering with keywords counts as scope-ok.
        scope_ok = True
    else:
        scope_ok = refused == should_refuse

    keyword_required = in_scope and not refused
    keyword_ok = (not keyword_required) or keyword_score >= 0.5
    passed = scope_ok and latency_ok and source_ok and keyword_ok

    row: dict[str, Any] = {
        "id": case["id"],
        "type": case.get("type"),
        "category": case.get("category"),
        "requirement": case.get("requirement"),
        "priority": case.get("priority"),
        "question": case["question"],
        "answer": result["answer"],
        "latency_s": result["latency_s"],
        "sources_count": len(result["sources"]),
        "first_source": result["sources"][0] if result["sources"] else None,
        "keyword_score": round(keyword_score, 3),
        "scope_ok": scope_ok,
        "latency_ok": latency_ok,
        "source_ok": source_ok,
        "refused": refused,
        "should_refuse": should_refuse,
        "passed": passed,
    }

    if use_judge:
        from evaluation.judge import judge as run_judge
        try:
            score = run_judge(
                question=case["question"],
                answer=result["answer"],
                ground_truth=case.get("ground_truth", ""),
                sources=result["sources"],
                refused=refused,
            )
            row["judge"] = score.to_dict()
        except Exception as e:
            row["judge_error"] = str(e)

    return row


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if not n:
        return {}
    base = {
        "n": n,
        "pass_rate": round(sum(r["passed"] for r in rows) / n, 3),
        "scope_accuracy": round(sum(r["scope_ok"] for r in rows) / n, 3),
        "source_rate": round(sum(r["source_ok"] for r in rows) / n, 3),
        "avg_latency_s": round(sum(r["latency_s"] for r in rows) / n, 3),
        "p95_latency_s": round(sorted(r["latency_s"] for r in rows)[int(0.95 * (n - 1))], 3),
        "refusal_rate": round(sum(r["refused"] for r in rows) / n, 3),
        "avg_keyword_score": round(sum(r["keyword_score"] for r in rows) / n, 3),
    }

    judged = [r["judge"] for r in rows if "judge" in r]
    if judged:
        dims = ["correctness", "didactic", "structure", "source_usage", "faithfulness", "overall"]
        for d in dims:
            base[f"judge_avg_{d}"] = round(sum(j[d] for j in judged) / len(judged), 3)
        base["judge_n"] = len(judged)
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description="BI-Tutor evaluation harness")
    parser.add_argument(
        "--cases", type=Path, default=ROOT / "evaluation" / "test_cases.json"
    )
    parser.add_argument(
        "--version", type=str, default="dev", help="System version tag for the report"
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "evaluation" / "results"
    )
    parser.add_argument(
        "--judge", action="store_true",
        help="Additionally run LLM-as-a-Judge (costs extra API calls).",
    )
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        print(f"--> {case['id']}: {case['question']}")
        try:
            row = _evaluate_case(case, use_judge=args.judge)
        except Exception as e:
            row = {
                "id": case["id"],
                "question": case["question"],
                "error": str(e),
                "passed": False,
            }
        rows.append(row)
        status = "PASS" if row.get("passed") else "FAIL"
        judge_overall = (row.get("judge") or {}).get("overall")
        judge_txt = f" judge={judge_overall}" if judge_overall is not None else ""
        print(f"    [{status}] latency={row.get('latency_s', '?')}s "
              f"sources={row.get('sources_count', '?')} "
              f"keywords={row.get('keyword_score', '?')}{judge_txt}")

    summary = _summary([r for r in rows if "error" not in r])

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = args.out / f"{stamp}_{args.version}"

    (base.with_suffix(".json")).write_text(
        json.dumps({"version": args.version, "summary": summary, "rows": rows},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with (base.with_suffix(".csv")).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = [
            "id", "type", "category", "requirement", "priority",
            "passed", "scope_ok", "latency_ok", "source_ok",
            "refused", "should_refuse", "keyword_score", "latency_s",
            "sources_count",
        ]
        if args.judge:
            header += [
                "judge_correctness", "judge_didactic", "judge_structure",
                "judge_source_usage", "judge_faithfulness", "judge_overall",
                "judge_rationale",
            ]
        header += ["question", "answer"]
        writer.writerow(header)
        for r in rows:
            row_out = [
                r.get("id"), r.get("type"), r.get("category"),
                r.get("requirement"), r.get("priority"),
                r.get("passed"), r.get("scope_ok"), r.get("latency_ok"),
                r.get("source_ok"), r.get("refused"), r.get("should_refuse"),
                r.get("keyword_score"), r.get("latency_s"),
                r.get("sources_count"),
            ]
            if args.judge:
                j = r.get("judge") or {}
                row_out += [
                    j.get("correctness"), j.get("didactic"),
                    j.get("structure"), j.get("source_usage"),
                    j.get("faithfulness"), j.get("overall"),
                    j.get("rationale"),
                ]
            row_out += [
                r.get("question"),
                (r.get("answer") or "").replace("\n", " ")[:500],
            ]
            writer.writerow(row_out)

    print("\nZUSAMMENFASSUNG")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nReport: {base}.json / {base}.csv")
    return 0 if summary.get("pass_rate", 0) >= 0.6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
