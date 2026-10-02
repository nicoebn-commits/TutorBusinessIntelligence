"""Admin dashboard for the BI-Tutor.

Streamlit multipage UI counterpart to app.py. Provides:
- System-Status: indexed chunks, modules, document coverage
- Ingestion-Controls: list PDFs in ./data, (re-)index, drop collection
- Chunk-Browser: search & filter through indexed chunks
- LLM-Probe: send a single query to the chain for debugging
"""
from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from rag.config import settings
from rag.ingestion import get_vectorstore, ingest_directory
from rag.ui import (
    apply_theme,
    render_topnav,
    render_header,
    render_section,
    render_source_card,
    render_slide_toggle,
    render_slide_footer,
    model_status_label,
)


apply_theme(page_title="BI-Tutor · Administration")
render_topnav(active="admin")
render_header(
    title="Business Intelligence & Analytics: Administration",
    tagline="Wissensbasis, Indexierung und Chunk-Diagnostik",
    status_label=model_status_label(),
)


@st.cache_resource(show_spinner=False)
def _store():
    return get_vectorstore()


@st.cache_data(show_spinner=False, ttl=10)
def _collection_stats() -> dict:
    store = _store()
    try:
        coll = store._collection
        count = coll.count()
        if count == 0:
            return {"count": 0, "by_doc": {}, "by_module": {}}
        peek = coll.get(include=["metadatas"])
        metas = peek.get("metadatas") or []
        by_doc = Counter((m or {}).get("document", "?") for m in metas)
        by_module = Counter((m or {}).get("module", "?") for m in metas)
        return {"count": count, "by_doc": dict(by_doc), "by_module": dict(by_module)}
    except Exception as e:
        return {"count": 0, "by_doc": {}, "by_module": {}, "error": str(e)}


# --- System Status ----------------------------------------------------------
render_section(
    kicker="Übersicht",
    title="System-Status",
    lead="Aktuelle Kennzahlen der Wissensbasis und der hinterlegten PDFs.",
)
stats = _collection_stats()
cols = st.columns(4)
cols[0].metric("Indexierte Chunks", stats["count"])
cols[1].metric("Dokumente", len(stats["by_doc"]))
cols[2].metric("Module", len(stats["by_module"]))
data_files = list(settings.data_dir.glob("*.pdf"))
cols[3].metric("PDFs in /data", len(data_files))

if stats.get("error"):
    st.warning(f"Chroma-Statistik fehlgeschlagen: {stats['error']}")

c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="bi-kicker">Chunks pro Dokument</div>', unsafe_allow_html=True)
    if stats["by_doc"]:
        st.dataframe(
            pd.DataFrame(
                sorted(stats["by_doc"].items(), key=lambda kv: -kv[1]),
                columns=["Dokument", "Chunks"],
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Keine Chunks indexiert.")

with c2:
    st.markdown('<div class="bi-kicker">Chunks pro Modul</div>', unsafe_allow_html=True)
    if stats["by_module"]:
        st.dataframe(
            pd.DataFrame(
                sorted(stats["by_module"].items(), key=lambda kv: -kv[1]),
                columns=["Modul", "Chunks"],
            ),
            hide_index=True,
            use_container_width=True,
        )

st.divider()

# --- Ingestion --------------------------------------------------------------
render_section(
    kicker="Wissensbasis",
    title="Ingestion",
    lead="PDFs aus dem Ordner ./data einlesen, chunken und in die Vektor-Datenbank schreiben.",
)

with st.expander("PDFs im Ordner ./data", expanded=False):
    if not data_files:
        st.warning("Keine PDFs gefunden. Lege Vorlesungsfolien in `./data` ab.")
    else:
        sizes = pd.DataFrame(
            [
                {
                    "Datei": p.name,
                    "Groesse (MB)": round(p.stat().st_size / 1_048_576, 2),
                }
                for p in sorted(data_files)
            ]
        )
        st.dataframe(sizes, hide_index=True, use_container_width=True)

action_cols = st.columns(2)
with action_cols[0]:
    reset = st.checkbox(
        "Collection vor (Re-)Ingest leeren",
        value=False,
        help="Alle vorhandenen Chunks loeschen und komplett neu indexieren.",
    )
    if st.button("PDFs (re-)indexieren", type="primary", use_container_width=True):
        with st.spinner("Indexiere PDFs ..."):
            try:
                n = ingest_directory(reset=reset)
                _collection_stats.clear()
                st.success(f"{n} Chunks indexiert.")
                st.rerun()
            except FileNotFoundError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Fehler: {e}")

with action_cols[1]:
    confirm = st.text_input(
        "Tippe `LEEREN` zur Bestaetigung",
        help="Gesamten Chroma-Ordner loeschen. Nicht ruecksetzbar.",
    )
    if st.button("Vektor-DB komplett löschen", use_container_width=True):
        if confirm.strip() == "LEEREN":
            try:
                shutil.rmtree(settings.chroma_dir, ignore_errors=True)
                _collection_stats.clear()
                st.success("Chroma-DB geloescht. Bitte App neu starten.")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler: {e}")
        else:
            st.warning("Bestaetigung fehlt - tippe LEEREN ins Feld links.")

st.divider()

# --- Chunk-Browser ----------------------------------------------------------
render_section(
    kicker="Diagnostik",
    title="Chunk-Browser",
    lead="Semantische Suche über alle indexierten Chunks. Nützlich, um Retrieval-Qualität zu prüfen.",
)

search_cols = st.columns([3, 2, 1])
with search_cols[0]:
    query = st.text_input("Semantische Suche", placeholder="z.B. Star-Schema, OLAP, ETL ...")
with search_cols[1]:
    docs_available = ["(alle)"] + sorted(stats["by_doc"].keys())
    doc_filter = st.selectbox("Dokument-Filter", docs_available)
with search_cols[2]:
    top_k = st.number_input("Top-k", min_value=1, max_value=50, value=10, step=1)

if query.strip():
    with st.spinner("Suche ..."):
        try:
            results = _store().similarity_search_with_score(query, k=int(top_k))
        except Exception as e:
            st.error(f"Suche fehlgeschlagen: {e}")
            results = []
    if doc_filter != "(alle)":
        results = [(d, s) for (d, s) in results if d.metadata.get("document") == doc_filter]

    st.caption(f"{len(results)} Treffer")
    for i, (d, score) in enumerate(results, start=1):
        meta = d.metadata
        src = {
            "document": meta.get("document", "?"),
            "slide": meta.get("slide", "?"),
            "module": meta.get("module", "?"),
            "preview": d.page_content[:400] + ("..." if len(d.page_content) > 400 else ""),
        }
        render_source_card(i, src)
        st.caption(f"Distance {score:.3f} · chunk_id `{meta.get('chunk_id', '?')}`")
        render_slide_toggle(src, key=f"chunk_slide_{i}_{meta.get('chunk_id','x')}")

st.divider()

# --- LLM-Probe --------------------------------------------------------------
render_section(
    kicker="Diagnostik",
    title="LLM-Probe",
    lead="Direkte Abfrage der vollen Chain (Retrieval + LLM) mit kompakter Metadaten-Ansicht.",
)

with st.form("probe", clear_on_submit=False):
    question = st.text_input(
        "Frage",
        placeholder="Was ist Retrieval-Augmented Generation?",
    )
    submit = st.form_submit_button("Frage senden", type="primary")

if submit and question.strip():
    from rag.chain import answer
    with st.spinner("Anfrage laeuft ..."):
        try:
            r = answer(question).to_dict()
        except Exception as e:
            st.error(f"Fehler: {e}")
            st.stop()
    m = st.columns(4)
    m[0].metric("Latency", f"{r['latency_s']:.2f} s")
    m[1].metric("Sources", len(r["sources"]))
    m[2].metric("Refused", "ja" if r["refused"] else "nein")
    m[3].metric("Modell", settings.openai_model)

    st.markdown("**Antwort:**")
    st.markdown(r["answer"])

    with st.expander("Retrieve-Treffer", expanded=True):
        for i, s in enumerate(r["sources"], start=1):
            render_source_card(i, s)
            render_slide_toggle(s, key=f"probe_slide_{i}")


render_slide_footer()
