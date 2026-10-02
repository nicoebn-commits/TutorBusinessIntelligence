"""LLM-as-a-Judge for the BI-Tutor.

Per Automation.md the quantitative metrics (latency, source rate,
scope detection, keyword matching) are complemented with a Claude-based
qualitative judge that scores didactic dimensions on a 0-5 scale.

Used by run_eval.py when --judge is passed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from rag.config import settings


JUDGE_SYSTEM = """\
Du bist ein strenger, objektiver Pruefer fuer ein RAG-basiertes Tutor-System \
fuer die Vorlesung *Business Intelligence & Analytics*.

Du erhaeltst:
- die Studierenden-Frage
- die vom Tutor gelieferte Antwort
- die Ground Truth (Soll-Antwort gemaess Vorlesung)
- die zitierten Quellen (Dokument, Folie)
- ob die Antwort eine Ablehnung war (refused)

Bewerte fuenf Dimensionen jeweils auf einer Skala von 0 (sehr schlecht) bis \
5 (sehr gut). Bewertungsdimensionen:

1. correctness     - fachliche Korrektheit ggue. Ground Truth (N2)
2. didactic        - Verstaendlichkeit / Zielgruppen-Anpassung (F3)
3. structure       - Gliederung, klare Definition zuerst, ggf. Vergleich
4. source_usage    - sinnvolle Bezugnahme auf die zitierten Quellen (F2)
5. faithfulness    - keine erfundenen Konzepte, transparente Unsicherheit (N3)

Sonderregeln:
- Wenn die Antwort eine korrekte Out-of-Scope-Ablehnung ist und die Frage \
  out-of-scope war: vergib correctness=5, faithfulness=5, source_usage=3 \
  (nicht erforderlich), didactic/structure nach Hoeflichkeit/Klarheit.
- Wenn die Antwort eine korrekte "ich weiss es nicht"-Ablehnung ist und die \
  Frage einen nicht-existierenden Begriff enthielt: faithfulness=5.
- Wenn die Antwort halluziniert (Fakten ohne Quellenbezug erfindet): \
  faithfulness=0 und correctness max 2.

Antworte AUSSCHLIESSLICH mit einem einzelnen, validen JSON-Objekt nach \
diesem Schema (keine zusaetzlichen Erklaerungen):

{{
  "correctness": <0-5>,
  "didactic": <0-5>,
  "structure": <0-5>,
  "source_usage": <0-5>,
  "faithfulness": <0-5>,
  "rationale": "<max 200 Zeichen, deutsch>"
}}
"""

JUDGE_USER = """\
Frage:
{question}

Ground Truth:
{ground_truth}

Antwort des Tutors:
{answer}

Refused: {refused}

Zitierte Quellen:
{sources}
"""


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class JudgeScore:
    correctness: float
    didactic: float
    structure: float
    source_usage: float
    faithfulness: float
    overall: float
    rationale: str
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "correctness": self.correctness,
            "didactic": self.didactic,
            "structure": self.structure,
            "source_usage": self.source_usage,
            "faithfulness": self.faithfulness,
            "overall": round(self.overall, 3),
            "rationale": self.rationale,
        }


def _format_sources(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "(keine)"
    lines = []
    for i, s in enumerate(sources, start=1):
        lines.append(
            f"{i}. {s.get('document', '?')} - Folie {s.get('slide', '?')} "
            f"(Modul: {s.get('module', '?')})"
        )
    return "\n".join(lines)


def _parse_score(text: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    if not match:
        raise ValueError(f"Judge returned no JSON: {text[:200]}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"Judge returned invalid JSON ({e}): {match.group(0)[:200]}")


_judge_llm = None


def _llm() -> ChatOpenAI:
    global _judge_llm
    if _judge_llm is None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY missing - cannot run LLM-as-a-Judge."
            )
        _judge_llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.0,
            max_tokens=512,
        )
    return _judge_llm


def judge(
    *,
    question: str,
    answer: str,
    ground_truth: str,
    sources: list[dict[str, Any]],
    refused: bool,
) -> JudgeScore:
    """Score one tutor answer along five didactic dimensions."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", JUDGE_SYSTEM), ("user", JUDGE_USER)]
    )
    msgs = prompt.format_messages(
        question=question,
        ground_truth=ground_truth or "(nicht angegeben)",
        answer=answer,
        refused=str(refused),
        sources=_format_sources(sources),
    )
    raw = _llm().invoke(msgs).content
    raw = raw if isinstance(raw, str) else str(raw)
    data = _parse_score(raw)

    fields = ["correctness", "didactic", "structure", "source_usage", "faithfulness"]
    for f in fields:
        v = float(data.get(f, 0))
        data[f] = max(0.0, min(5.0, v))
    overall = sum(data[f] for f in fields) / len(fields)

    return JudgeScore(
        correctness=data["correctness"],
        didactic=data["didactic"],
        structure=data["structure"],
        source_usage=data["source_usage"],
        faithfulness=data["faithfulness"],
        overall=overall,
        rationale=str(data.get("rationale", ""))[:300],
        raw=raw,
    )
