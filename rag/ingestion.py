"""PDF ingestion with mandatory metadata (F2 – Zitierfähigkeit).

Each chunk carries:
- document: filename of the source PDF
- module:   coarse subject area, derived from filename prefix or folder
- slide:    page number of the PDF (1-based), which corresponds to the slide
            number in BI lecture decks
- chunk_id: stable hash for deduplication
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import settings


# Order matters: the first matching pattern wins. Specific module names
# (e.g. Star-Schema) must come before broader categories (Datenmodellierung)
# because some lectures contain both terms in the filename.
_MODULE_PATTERNS = [
    # --- BIA-Vorlesung (Hauptquelle) ---
    (re.compile(r"gastvortrag", re.I), "Gastvortrag"),
    (re.compile(r"bi[_\s-]?begriff", re.I), "BI-Begriff"),
    (re.compile(r"star[_\s-]?schema", re.I), "Star-Schema"),
    (re.compile(r"datenmodellierung", re.I), "Datenmodellierung"),
    (re.compile(r"datenbereitstellung", re.I), "Datenbereitstellung"),
    (re.compile(r"analysesy[s]?teme", re.I), "Analysesysteme"),
    (re.compile(r"entwicklung[_\s-]?(?:und[_\s-]?)?betrieb", re.I), "Entwicklung & Betrieb"),
    # --- Übungen + Klausuren ---
    (re.compile(r"uebung|übung", re.I), "Uebung"),
    (re.compile(r"klausur.*loesungshinweise|altklausuren[_\s-]?loesungshinweise", re.I), "Altklausur (Loesungen)"),
    (re.compile(r"klausur", re.I), "Altklausur"),
    # --- Lehrbuch ---
    (re.compile(r"^buch\.pdf$", re.I), "Lehrbuch"),
    # --- Legacy / Praktikums-PDFs (fallen heraus sobald data/ neu ist) ---
    (re.compile(r"kickoff", re.I), "Kickoff"),
    (re.compile(r"ai[_\s-]?llm", re.I), "AI/LLM Grundlagen"),
    (re.compile(r"requirements|evaluation", re.I), "Requirements & Evaluation"),
    (re.compile(r"tool[_\s-]?konfig", re.I), "Toolkonfiguration"),
    (re.compile(r"automation", re.I), "Automation"),
]


def _infer_module(filename: str) -> str:
    for pattern, label in _MODULE_PATTERNS:
        if pattern.search(filename):
            return label
    return "BI Vorlesung"


# ---------------------------------------------------------------------------
# Coarse content categories for the knowledge-base filter (chat scope).
# Each fine-grained module maps onto exactly one of these. Lectures are the
# default bucket; only exercises ("Uebung") and past exams ("Altklausur") are
# special-cased, so new lecture modules are classified as Vorlesung for free.
# ---------------------------------------------------------------------------
CAT_VORLESUNG = "Vorlesung"
CAT_UEBUNG = "Uebung"
CAT_ALTKLAUSUR = "Altklausur"
ALL_CATEGORIES = (CAT_VORLESUNG, CAT_UEBUNG, CAT_ALTKLAUSUR)

_UEBUNG_MODULES = {"Uebung"}
_ALTKLAUSUR_MODULES = {"Altklausur", "Altklausur (Loesungen)"}


def category_for_module(module: str | None) -> str:
    """Map a fine-grained module label onto a coarse content category."""
    if module in _UEBUNG_MODULES:
        return CAT_UEBUNG
    if module in _ALTKLAUSUR_MODULES:
        return CAT_ALTKLAUSUR
    return CAT_VORLESUNG


def _chunk_id(text: str, source: str, slide: int) -> str:
    h = hashlib.sha1(f"{source}|{slide}|{text}".encode("utf-8")).hexdigest()
    return h[:16]


def _build_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )


def _load_pdfs(data_dir: Path) -> Iterable[Document]:
    pdfs = sorted(data_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"No PDFs found in {data_dir}. Drop your BI lecture slides into ./data."
        )
    for pdf in pdfs:
        loader = PyPDFLoader(str(pdf))
        for page in loader.load():
            page.metadata["document"] = pdf.name
            page.metadata["module"] = _infer_module(pdf.name)
            page.metadata["category"] = category_for_module(page.metadata["module"])
            page.metadata["slide"] = int(page.metadata.get("page", 0)) + 1
            yield page


def _split(docs: Iterable[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Document] = []
    for doc in docs:
        for sub in splitter.split_documents([doc]):
            sub.metadata["chunk_id"] = _chunk_id(
                sub.page_content, sub.metadata["document"], sub.metadata["slide"]
            )
            chunks.append(sub)
    return chunks


def get_vectorstore(embeddings: HuggingFaceEmbeddings | None = None) -> Chroma:
    embeddings = embeddings or _build_embeddings()
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings,
        persist_directory=str(settings.chroma_dir),
    )


def get_all_documents() -> list[Document]:
    """Fetch every chunk currently indexed as a list of LangChain Documents.

    Used by the BM25 side of the hybrid retriever - BM25 needs the full
    corpus in memory whereas Chroma keeps things on disk.
    """
    store = get_vectorstore()
    data = store._collection.get(include=["documents", "metadatas"])
    docs: list[Document] = []
    for text, meta in zip(data.get("documents") or [], data.get("metadatas") or []):
        docs.append(Document(page_content=text or "", metadata=meta or {}))
    return docs


def ingest_directory(data_dir: Path | None = None, *, reset: bool = False) -> int:
    """Read PDFs, chunk with metadata, write to Chroma. Returns chunk count."""
    data_dir = data_dir or settings.data_dir
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    embeddings = _build_embeddings()
    store = get_vectorstore(embeddings)

    if reset:
        try:
            store.delete_collection()
        except Exception:
            pass
        store = get_vectorstore(embeddings)

    docs = list(_load_pdfs(data_dir))
    chunks = _split(docs)
    ids = [c.metadata["chunk_id"] for c in chunks]
    store.add_documents(chunks, ids=ids)
    return len(chunks)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest BI lecture PDFs into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Wipe collection first")
    parser.add_argument("--data", type=Path, default=None, help="Override data directory")
    args = parser.parse_args()

    n = ingest_directory(args.data, reset=args.reset)
    print(f"Ingested {n} chunks into '{settings.collection_name}' at {settings.chroma_dir}")
