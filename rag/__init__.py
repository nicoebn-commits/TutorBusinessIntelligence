"""BI-Tutor RAG package."""
from .config import settings
from .chain import answer, build_chain
from .ingestion import ingest_directory

__all__ = ["settings", "answer", "build_chain", "ingest_directory"]
