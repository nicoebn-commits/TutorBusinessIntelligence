"""RAG chain for the BI-Tutor.

Enforces SRS requirements:
- F1: answers strictly from retrieved context
- F5: politely refuses out-of-scope questions
- N3: explicit uncertainty instead of hallucination (faithfulness)

The public surface is `answer(question)` which returns a structured dict.
The Evaluation harness uses this same function so UI and tests share one
code path.
"""
from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterator

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

from .config import settings
from .ingestion import (
    get_vectorstore,
    get_all_documents,
    category_for_module,
    ALL_CATEGORIES,
)


SYSTEM_PROMPT = """\
Du bist der "BI-Tutor", ein didaktischer Assistent fuer Studierende der \
Veranstaltung *Business Intelligence & Analytics*. Du beantwortest \
ausschliesslich Fragen auf Basis des dir bereitgestellten \
Vorlesungs-Kontexts.

ANFORDERUNGEN AUS DER SRS:
- F1 Dokumentenbasierung: Antworte nur aus dem Kontext.
- F2 Quellenangabe: Jede inhaltliche Antwort muss inline-zitieren UND \
  am Ende eine "Quellen:"-Liste enthalten.
- F3 Adaptive Erklaerung: Erkenne Hinweise wie "einfach", "Erstsemester", \
  "in einfachen Worten" und passe Sprachniveau, Beispiele und Tiefe an. \
  Nutze bei Bedarf Alltagsanalogien.
- F4 Glossar: Bei reinen Definitionsfragen ("Was bedeutet ...?", \
  "Definiere ...") antworte praezise und kurz (1-3 Saetze), gefolgt von \
  einer optionalen Erlaeuterung.
- F5 Themenfokus: Fachfremde Fragen ablehnen (siehe Regel 2).
- N2 Korrektheit: Inhalte muessen vorlesungskonform sein.
- N3 Faithfulness: Keine erfundenen Konzepte, keine erfundenen Quellen.

STRIKTE REGELN:
1. ANTWORTE AUSSCHLIESSLICH AUS DEM KONTEXT. Falls die noetigen \
   Informationen im Kontext fehlen, sage woertlich: "Das kann ich auf \
   Basis der Vorlesungsmaterialien nicht sicher beantworten." Erfinde \
   nichts - auch keine plausibel klingenden, aber nicht im Kontext \
   belegten Konzepte (z. B. "Delta-Cube-Modell").
2. FACHFREMDE / OUT-OF-SCOPE FRAGEN (z. B. Wetter, Politik, Smalltalk, \
   andere Studiengaenge, allgemeine IT abseits BI) lehnst du hoeflich ab. \
   Antworte dann mit: "Diese Frage liegt ausserhalb des BI-Tutor-Scopes. \
   Bitte stelle eine Frage zur Business-Intelligence-Vorlesung."
3. EXPLIZITE QUELLENANGABE (PFLICHT): \
   (a) Setze fuer jede inhaltliche Aussage eine Inline-Quellenangabe \
       im Format [Dokument, Folie X] oder kurz [Folie X]. \
   (b) Beende JEDE inhaltliche Antwort mit einem Block: \
\
       Quellen: \
       - <Dokumentname>, Folie <X> (<Modul>) \
       - ... \
\
   (c) Liste nur Quellen, die tatsaechlich genutzt wurden - nicht \
       jeden Kontext-Chunk. Erfinde nie Folien- oder Dokumentnamen. \
   (d) Bei Ablehnungen (Regel 1 oder 2) entfaellt die Quellenliste.
4. SEI DIDAKTISCH: kurze Definition zuerst, dann optional Beispiel, \
   optional Bezug zu BI-Praxis. Bei Vergleichsfragen strukturierte \
   Gegenueberstellung (Zweck, Datenmodell, Nutzungskontext, ...).
5. UNSICHERHEIT TRANSPARENT MACHEN: "Der Kontext deutet darauf hin, dass \
   ..., enthaelt aber keine explizite Definition." Lieber Unsicherheit \
   eingestehen als raten.

KONTEXT (Vorlesungsausschnitte mit Quellenangabe):
{context}
"""

USER_PROMPT = "Frage: {question}"


REWRITE_PROMPT = """\
Du erhaeltst den bisherigen Gespraechsverlauf zwischen einem Studierenden \
und einem BI-Tutor sowie eine neue Folgefrage. Deine Aufgabe: Schreibe die \
Folgefrage in eine vollstaendig eigenstaendige Frage um, sodass sie auch \
ohne Gespraechsverlauf eindeutig retrievebar ist.

Regeln:
- Loese Pronomen ("es", "das", "dieser") und elliptische Bezuege auf.
- Behalte fachliche Begriffe woertlich bei.
- Falls die Folgefrage bereits eigenstaendig ist, gib sie unveraendert zurueck.
- Antworte AUSSCHLIESSLICH mit der eigenstaendigen Frage, ohne Praefix \
  oder Anfuehrungszeichen.

Gespraechsverlauf:
{history}

Folgefrage: {question}
Eigenstaendige Frage:"""


HISTORY_TURNS = 6     # Number of past turns surfaced to the answering LLM
REWRITE_TRUNCATE = 240  # Per-turn char cap for the rewrite prompt


# Heuristik: nur dann den Rewrite-LLM-Call ausloesen, wenn die Frage
# wirklich nach einem Folgefragen-Kontext aussieht.
_REFERENCE_TOKENS = re.compile(
    r"\b(es|das|dies|diese[mrs]?|dieselbe[ns]?|dasselbe|dem|dazu|davon|"
    r"darueber|darin|darauf|hier|sowas|so etwas|mehr dazu|"
    r"warum|wieso|und|auch|weiter|naeher|genauer|nochmal)\b",
    re.IGNORECASE,
)


def _should_rewrite(question: str, history: list[dict[str, str]] | None) -> bool:
    """Skip the rewriter when the question is clearly self-contained."""
    if not history:
        return False
    words = question.split()
    if len(words) <= 3:
        return True
    if len(words) <= 12 and _REFERENCE_TOKENS.search(question):
        return True
    return False


@dataclass
class TutorAnswer:
    question: str
    answer: str
    sources: list[dict[str, Any]]
    latency_s: float
    refused: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "sources": self.sources,
            "latency_s": round(self.latency_s, 3),
            "refused": self.refused,
        }


def _format_context(docs: list[Document]) -> str:
    blocks = []
    for i, d in enumerate(docs, start=1):
        meta = d.metadata
        tag = f"[Quelle {i}: {meta.get('document', '?')}, Folie {meta.get('slide', '?')}, Modul {meta.get('module', '?')}]"
        blocks.append(f"{tag}\n{d.page_content.strip()}")
    return "\n\n---\n\n".join(blocks) if blocks else "(kein Kontext gefunden)"


def _docs_to_sources(docs: list[Document]) -> list[dict[str, Any]]:
    return [
        {
            "document": d.metadata.get("document", "unbekannt"),
            "slide": d.metadata.get("slide"),
            "module": d.metadata.get("module"),
            "chunk_id": d.metadata.get("chunk_id"),
            "preview": d.page_content[:280].replace("\n", " ").strip() + ("..." if len(d.page_content) > 280 else ""),
        }
        for d in docs
    ]


_REFUSAL_RE = re.compile(
    r"(ausserhalb|au(?:ß|ss)erhalb)\s+des\s+bi[- ]?tutor[- ]?scopes?"
    r"|nicht\s+sicher\s+beantworten"
    r"|kann\s+ich\s+(?:auf\s+basis|leider)\s+(?:der\s+)?vorlesungsmaterialien?",
    re.IGNORECASE,
)


def _is_refusal(text: str) -> bool:
    """Detect both scope refusals and ``not in materials'' refusals.

    The system prompt asks for German answers, so the model regularly
    writes ``ausserhalb'' with sharp-s. The regex covers both spellings
    plus the ``Das kann ich auf Basis der Vorlesungsmaterialien ...''
    variant.
    """
    return bool(_REFUSAL_RE.search(text))


def _format_history_for_rewrite(history: list[dict[str, str]]) -> str:
    """Render the last few turns as a compact transcript for the rewriter."""
    if not history:
        return "(leer)"
    lines = []
    for turn in history[-HISTORY_TURNS:]:
        role = "Studierender" if turn.get("role") == "user" else "Tutor"
        text = (turn.get("content") or "").replace("\n", " ").strip()
        if len(text) > REWRITE_TRUNCATE:
            text = text[:REWRITE_TRUNCATE] + "..."
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def _history_messages(history: list[dict[str, str]]) -> list[tuple[str, str]]:
    """Last N turns as (role, content) tuples for ChatPromptTemplate."""
    if not history:
        return []
    out: list[tuple[str, str]] = []
    for turn in history[-HISTORY_TURNS:]:
        role = "user" if turn.get("role") == "user" else "assistant"
        content = (turn.get("content") or "").strip()
        if content:
            out.append((role, content))
    return out


def build_chain():
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and set the key."
        )

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=1024,
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("user", USER_PROMPT)]
    )
    store = get_vectorstore()
    retriever = store.as_retriever(search_kwargs={"k": settings.top_k})

    def _invoke(question: str) -> TutorAnswer:
        t0 = time.perf_counter()
        docs = retriever.invoke(question)
        context = _format_context(docs)
        msg = prompt.format_messages(context=context, question=question)
        resp = llm.invoke(msg)
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
        latency = time.perf_counter() - t0
        return TutorAnswer(
            question=question,
            answer=text.strip(),
            sources=_docs_to_sources(docs),
            latency_s=latency,
            refused=_is_refusal(text),
        )

    return _invoke


_chain = None
_streaming_components = None        # (llm, rewriter) — shared across scopes
_corpus_docs: list[Document] | None = None  # full corpus for BM25, loaded once
_retriever_cache: dict[tuple[str, ...], Any] = {}  # keyed by category scope


def warm_up() -> None:
    """Eagerly load LLMs + vectorstore so the first user question is fast.

    Call this once at app startup (e.g. behind @st.cache_resource) so the
    expensive sentence-transformers import + Chroma open does not happen
    during the user's first question.
    """
    global _streaming_components
    if _streaming_components is None:
        _streaming_components = _build_streaming()
    # Prime the corpus + default (unfiltered) hybrid retriever as well.
    _get_retriever(None)


def answer(question: str) -> TutorAnswer:
    """Public entry point used by the UI and the evaluation harness."""
    global _chain
    if _chain is None:
        _chain = build_chain()
    return _chain(question)


@dataclass
class StreamHandle:
    """Holder for a streaming answer.

    `tokens` is a generator yielding text chunks as Claude streams them.
    After the generator is exhausted, `answer`, `latency_s` and `refused`
    are populated. `sources` is available immediately (retrieval finishes
    before any tokens are produced).
    """
    sources: list[dict[str, Any]]
    tokens: Iterator[str]
    answer: str = ""
    latency_s: float = 0.0
    refused: bool = False
    error: str | None = None
    retrieval_s: float = 0.0
    rewritten_query: str | None = None  # set if history-aware rewrite happened


def _build_streaming():
    """Lazily build the shared LLMs (streaming answerer + rewriter)."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and set the key."
        )
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=1024,
        streaming=True,
    )
    # Lightweight LLM call for the standalone-question rewrite. Same model
    # but non-streaming and short max_tokens to keep cost negligible.
    rewriter = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.0,
        max_tokens=128,
    )
    return llm, rewriter


def _corpus() -> list[Document]:
    """Full indexed corpus, loaded once (BM25 needs it all in memory)."""
    global _corpus_docs
    if _corpus_docs is None:
        _corpus_docs = get_all_documents()
    return _corpus_docs


def _normalize_categories(
    categories: list[str] | tuple[str, ...] | None,
) -> tuple[str, ...] | None:
    """Sort/validate the selection; return None when it means "everything".

    An empty selection or one covering all categories is treated as "no
    filter" so the default path keeps the original full-corpus behaviour.
    """
    if not categories:
        return None
    selected = tuple(sorted(c for c in categories if c in ALL_CATEGORIES))
    if not selected or set(selected) == set(ALL_CATEGORIES):
        return None
    return selected


def _build_retriever(categories: tuple[str, ...] | None):
    """Hybrid retriever, optionally scoped to a subset of content categories.

    `categories=None` retrieves over the whole knowledge base (default). When
    a subset is given, the vector side gets a Chroma metadata filter on the
    `module` field and the BM25 side is rebuilt over only the matching chunks,
    so both halves of the ensemble respect the exact same scope.

    Hybrid-Retrieval: Volltext (BM25) + Semantik (Chroma/Vektor) per
    Reciprocal Rank Fusion. BM25 ist gut bei exakten Begriffen ("OLTP",
    "ETL", "Inmon"); Vektor faengt synonyme/paraphrasierte Formulierungen.
    """
    store = get_vectorstore()
    if categories is None:
        vector_retriever = store.as_retriever(search_kwargs={"k": settings.top_k})
        bm25_docs = _corpus()
    else:
        modules = [
            m
            for m in {d.metadata.get("module") for d in _corpus()}
            if m is not None and category_for_module(m) in categories
        ]
        # Guard the $in clause: an empty list would error, so match nothing.
        if not modules:
            modules = ["__no_such_module__"]
        vector_retriever = store.as_retriever(
            search_kwargs={
                "k": settings.top_k,
                "filter": {"module": {"$in": modules}},
            }
        )
        bm25_docs = [
            d
            for d in _corpus()
            if category_for_module(d.metadata.get("module")) in categories
        ]

    try:
        if not bm25_docs:
            return vector_retriever
        bm25 = BM25Retriever.from_documents(bm25_docs)
        bm25.k = settings.top_k
        return EnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[0.4, 0.6],
        )
    except Exception:
        # Falls BM25 nicht initialisiert werden kann, fallback auf Vektor.
        return vector_retriever


def _get_retriever(categories: list[str] | tuple[str, ...] | None):
    """Return a (cached) hybrid retriever for the given category scope."""
    norm = _normalize_categories(categories)
    key = norm or ("__all__",)
    if key not in _retriever_cache:
        _retriever_cache[key] = _build_retriever(norm)
    return _retriever_cache[key]


def _rewrite_question(question: str, history: list[dict[str, str]], rewriter) -> str:
    """LLM-rewrite the new question into a standalone form."""
    prompt = ChatPromptTemplate.from_template(REWRITE_PROMPT)
    msgs = prompt.format_messages(
        history=_format_history_for_rewrite(history),
        question=question,
    )
    raw = rewriter.invoke(msgs).content
    text = raw if isinstance(raw, str) else str(raw)
    # Strip wrapping quotes / whitespace; fall back to original on empty
    cleaned = text.strip().strip('"').strip("'").strip()
    return cleaned or question


def stream_answer(
    question: str,
    history: list[dict[str, str]] | None = None,
    categories: list[str] | None = None,
) -> StreamHandle:
    """Streaming variant of `answer`, optionally history-aware.

    Retrieval runs eagerly so the caller can show sources immediately.
    When `history` contains prior turns, the question is first rewritten
    into a standalone form (so the retriever sees a self-contained query),
    and the last `HISTORY_TURNS` turns are surfaced to the answering LLM
    via the chat prompt template (multi-turn context for the answer).

    `categories` scopes retrieval to a subset of content categories
    (Vorlesung / Uebung / Altklausur). None, empty or "all selected" means
    the whole knowledge base is searched.
    """
    global _streaming_components
    if _streaming_components is None:
        _streaming_components = _build_streaming()
    llm, rewriter = _streaming_components
    retriever = _get_retriever(categories)

    t0 = time.perf_counter()
    history = history or []
    rewritten = None
    retrieval_query = question
    if _should_rewrite(question, history):
        rewritten = _rewrite_question(question, history, rewriter)
        retrieval_query = rewritten

    docs = retriever.invoke(retrieval_query)
    retrieval_s = time.perf_counter() - t0

    msg_list: list[tuple[str, str]] = [("system", SYSTEM_PROMPT)]
    msg_list.extend(_history_messages(history))
    msg_list.append(("user", USER_PROMPT))
    prompt = ChatPromptTemplate.from_messages(msg_list)
    msgs = prompt.format_messages(
        context=_format_context(docs), question=question
    )

    sources = _docs_to_sources(docs)
    handle = StreamHandle(
        sources=sources,
        tokens=iter(()),
        retrieval_s=retrieval_s,
        rewritten_query=rewritten if rewritten and rewritten != question else None,
    )

    def _gen() -> Iterator[str]:
        collected: list[str] = []
        try:
            for chunk in llm.stream(msgs):
                text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                if not text:
                    continue
                collected.append(text)
                yield text
        except Exception as e:
            handle.error = str(e)
        finally:
            full = "".join(collected).strip()
            handle.answer = full
            handle.refused = _is_refusal(full)
            handle.latency_s = time.perf_counter() - t0

    handle.tokens = _gen()
    return handle


# ===========================================================================
# Quiz generation (Multiple-Choice, grounded in the knowledge base)
# ===========================================================================

QUIZ_SYSTEM_PROMPT = """\
Du bist der "BI-Tutor" und erstellst ein Multiple-Choice-Quiz fuer \
Studierende der Veranstaltung *Business Intelligence & Analytics*.

REGELN:
1. Erstelle GENAU {n} Fragen AUSSCHLIESSLICH auf Basis des bereitgestellten \
   Kontexts. Erfinde keine Inhalte, die nicht im Kontext stehen.
2. Jede Frage hat GENAU 4 Antwortoptionen, von denen GENAU EINE korrekt ist. \
   Die Distraktoren muessen plausibel, aber eindeutig falsch sein.
3. Schwierigkeitsgrad: {difficulty}. Passe Formulierung und Tiefe an \
   (leicht = Definitionen/Grundbegriffe, mittel = Verstaendnis/Anwendung, \
   schwer = Vergleich/Transfer).
4. Begruende bei jeder Frage kurz, warum die korrekte Option richtig ist \
   ("explanation"), und gib die genutzte Quelle an (Dokument + Folie + Modul).
5. Antworte AUSSCHLIESSLICH mit gueltigem JSON in genau dieser Struktur \
   (keine Markdown-Codefences, kein Text davor oder danach):

{{
  "questions": [
    {{
      "question": "Fragetext",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "Kurze Begruendung der korrekten Antwort.",
      "source": {{"document": "Dateiname.pdf", "slide": 12, "module": "Star-Schema"}}
    }}
  ]
}}

"correct_index" ist der 0-basierte Index der korrekten Option (0-3).
Verwende durchgaengig Deutsch.

KONTEXT (Vorlesungsausschnitte mit Quellenangabe):
{context}
"""

QUIZ_USER_PROMPT = (
    "Erstelle das Quiz{topic_clause}. Gib ausschliesslich das JSON zurueck."
)

DIFFICULTY_LEVELS = ("leicht", "mittel", "schwer")


@dataclass
class QuizQuestion:
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    source: dict[str, Any]


@dataclass
class Quiz:
    topic: str
    difficulty: str
    questions: list[QuizQuestion]
    sources: list[dict[str, Any]]
    error: str | None = None

    def __len__(self) -> int:
        return len(self.questions)


_quiz_llm = None


def _get_quiz_llm():
    """Lazily build a JSON-mode LLM for quiz generation."""
    global _quiz_llm
    if _quiz_llm is None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Copy .env.example to .env and set the key."
            )
        _quiz_llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.5,  # etwas Varianz fuer abwechslungsreiche Fragen
            max_tokens=3000,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
    return _quiz_llm


def _module_filter(norm: tuple[str, ...] | None) -> dict[str, Any] | None:
    """Chroma where-clause restricting `module` to the selected categories."""
    if norm is None:
        return None
    modules = [
        m
        for m in {d.metadata.get("module") for d in _corpus()}
        if m is not None and category_for_module(m) in norm
    ]
    if not modules:
        modules = ["__no_such_module__"]
    return {"module": {"$in": modules}}


def _quiz_context(
    topic: str | None,
    categories: list[str] | None,
    k: int,
) -> list[Document]:
    """Collect context chunks for the quiz, respecting the category scope.

    With a topic we run a (scoped) similarity search; without one we draw a
    random sample from the scoped corpus so the quiz covers varied material.
    """
    norm = _normalize_categories(categories)
    if topic and topic.strip():
        store = get_vectorstore()
        filt = _module_filter(norm)
        if filt is not None:
            return store.similarity_search(topic, k=k, filter=filt)
        return store.similarity_search(topic, k=k)

    pool = _corpus()
    if norm is not None:
        pool = [
            d for d in pool if category_for_module(d.metadata.get("module")) in norm
        ]
    if not pool:
        return []
    return random.sample(pool, min(k, len(pool)))


def _parse_quiz_json(raw: str) -> list[dict[str, Any]]:
    """Parse the LLM response into a list of raw question dicts.

    Tolerant: if the model wraps the JSON in prose/fences, fall back to the
    outermost ``{...}`` slice before giving up.
    """
    text = raw.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        data = json.loads(text[start : end + 1])
    questions = data.get("questions") if isinstance(data, dict) else None
    return questions if isinstance(questions, list) else []


def _coerce_question(item: dict[str, Any]) -> QuizQuestion | None:
    """Validate one raw question dict; return None if it is malformed."""
    if not isinstance(item, dict):
        return None
    q = str(item.get("question", "")).strip()
    options = item.get("options")
    if not q or not isinstance(options, list) or len(options) != 4:
        return None
    options = [str(o).strip() for o in options]
    if any(not o for o in options):
        return None
    try:
        idx = int(item.get("correct_index"))
    except (TypeError, ValueError):
        return None
    if not 0 <= idx <= 3:
        return None
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    return QuizQuestion(
        question=q,
        options=options,
        correct_index=idx,
        explanation=str(item.get("explanation", "")).strip(),
        source={
            "document": source.get("document"),
            "slide": source.get("slide"),
            "module": source.get("module"),
        },
    )


def generate_quiz(
    topic: str | None = None,
    *,
    categories: list[str] | None = None,
    num_questions: int = 5,
    difficulty: str = "mittel",
) -> Quiz:
    """Generate a multiple-choice quiz grounded in the knowledge base.

    `topic` optionally focuses the quiz on a subject; if empty, questions are
    drawn from a random sample of the (scoped) corpus. `categories` restricts
    the source material to Vorlesung / Uebung / Altklausur, reusing the same
    scope filter as the chat. Returns a `Quiz`; on failure `error` is set and
    `questions` is empty.
    """
    num_questions = max(1, min(int(num_questions), 15))
    difficulty = difficulty if difficulty in DIFFICULTY_LEVELS else "mittel"

    # Pull a bit more context than questions so the model has room to choose.
    k = max(settings.top_k, num_questions * 2)
    docs = _quiz_context(topic, categories, k)
    sources = _docs_to_sources(docs)
    if not docs:
        return Quiz(
            topic=topic or "",
            difficulty=difficulty,
            questions=[],
            sources=[],
            error="Kein passender Kontext fuer das gewaehlte Thema/den Filter gefunden.",
        )

    topic_clause = f' zum Thema "{topic.strip()}"' if topic and topic.strip() else ""
    prompt = ChatPromptTemplate.from_messages(
        [("system", QUIZ_SYSTEM_PROMPT), ("user", QUIZ_USER_PROMPT)]
    )
    msgs = prompt.format_messages(
        n=num_questions,
        difficulty=difficulty,
        context=_format_context(docs),
        topic_clause=topic_clause,
    )

    try:
        resp = _get_quiz_llm().invoke(msgs)
        raw = resp.content if isinstance(resp.content, str) else str(resp.content)
        items = _parse_quiz_json(raw)
    except Exception as e:  # network / parsing / API errors
        return Quiz(
            topic=topic or "",
            difficulty=difficulty,
            questions=[],
            sources=sources,
            error=f"Quiz konnte nicht erstellt werden: {e}",
        )

    questions = [q for q in (_coerce_question(it) for it in items) if q is not None]
    error = None if questions else "Das Modell hat keine gueltigen Fragen geliefert."
    return Quiz(
        topic=topic or "",
        difficulty=difficulty,
        questions=questions,
        sources=sources,
        error=error,
    )
