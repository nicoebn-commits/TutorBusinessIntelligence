"""On-demand PDF slide rendering.

Used by the Streamlit UI to show the actual slide as an image directly
underneath a retrieved source card. PyMuPDF is already a dependency for
the ingestion preview scripts.

The functions here are pure - no Streamlit imports - so the caller is
free to cache them with st.cache_data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from .config import settings


def render_slide_png(
    document_name: Optional[str],
    slide_number: Optional[int],
    *,
    dpi: int = 110,
) -> Optional[bytes]:
    """Render a 1-indexed slide of `data/<document_name>` to PNG bytes.

    Returns None if the document is missing, slide is out of range, or
    PyMuPDF fails for any reason. Designed for use behind a UI cache:
    callers should wrap this with @st.cache_data so the same slide is
    only rendered once per session.
    """
    if not document_name or slide_number is None:
        return None
    try:
        slide_number = int(slide_number)
    except (TypeError, ValueError):
        return None
    if slide_number < 1:
        return None

    path: Path = settings.data_dir / document_name
    if not path.exists():
        return None

    try:
        doc = fitz.open(str(path))
    except Exception:
        return None
    try:
        if slide_number > len(doc):
            return None
        pix = doc[slide_number - 1].get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    except Exception:
        return None
    finally:
        try:
            doc.close()
        except Exception:
            pass
