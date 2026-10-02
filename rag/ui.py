"""Shared UI helpers for the BI-Tutor Streamlit app.

Visual style mirrors the BIA-Vorlesungsfolien (Lehrstuhl fuer ABWL und
Wirtschaftsinformatik 1, Universitaet Stuttgart): white background, a
dezent cyan accent (#00B0E0), anthracite title typography, slim rules
and cyan bullet markers.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from .config import settings


# -- Design Tokens (extracted from the Vorlesungsfolien) ------------------
COL_CYAN = "#00B0E0"
COL_CYAN_DARK = "#0096C0"
COL_CYAN_SOFT = "#E6F7FD"
COL_TITLE = "#2b2b2b"
COL_TEXT = "#333333"
COL_TEXT_MUTED = "#888888"
COL_BG = "#ffffff"
COL_BG_SOFT = "#f6f7f9"
COL_BORDER = "#e0e0e0"
COL_BORDER_SOFT = "#eeeeee"
COL_OK = "#2e8b57"
COL_WARN = "#b8860b"

CHAIR_NAME = "Lehrstuhl für ABWL und Wirtschaftsinformatik 1"
CHAIR_AUTHOR = "Universität Stuttgart"

# Knowledge-base category labels, shared by the Dialog filter and the Quiz
# page. Keys match the category keys produced by rag.chain / rag.ingestion.
CATEGORY_LABELS = {
    "Vorlesung": "Vorlesungen",
    "Uebung": "Übungen",
    "Altklausur": "Altklausuren",
}


_CSS = f"""
<style>
/* ---------- Streamlit clutter ausblenden ---------- */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}
[data-testid="stHeader"] {{
  background: transparent;
  /* WICHTIG: keine height:0 - sonst verschwindet der Sidebar-Toggle */
}}
/* Nur die Deploy-/Menue-Aktionen verstecken, NICHT die ganze Toolbar -
   sonst nimmt man in Streamlit 1.40+ auch den Sidebar-Toggle mit. */
header [data-testid="stToolbarActions"] {{ visibility: hidden; }}
header [data-testid="stMainMenu"] {{ visibility: hidden; }}

/* Sidebar-Toggle (Pfeil zum Aus-/Einklappen) immer sichtbar mit eigenem
   Hintergrund, damit er auf transparentem Header nicht verschwindet. */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="headerNoPadding"] {{
  visibility: visible !important;
  display: flex !important;
  opacity: 1 !important;
  color: {COL_TITLE} !important;
  background: {COL_BG_SOFT} !important;
  border: 1px solid {COL_BORDER} !important;
  border-radius: 6px !important;
  z-index: 1000 !important;
}}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="stSidebarCollapseButton"]:hover,
button[kind="headerNoPadding"]:hover {{
  background: {COL_BG} !important;
  border-color: {COL_CYAN} !important;
}}

/* ---------- Streamlit Auto-Sidebar-Nav verstecken (eigene Topnav) ---------- */
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* ---------- Horizontale Top-Navigation (Browser-Tab-Stil) ---------- */
.bi-topnav {{
  display: flex;
  gap: 0.15rem;
  border-bottom: 1px solid {COL_BORDER};
  margin: 0 -0.5rem 1.8rem -0.5rem;
  padding: 0 0.5rem;
}}
.bi-topnav__item {{
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.85rem 1.15rem 0.85rem 1.05rem;
  color: {COL_TEXT_MUTED};
  text-decoration: none;
  font-weight: 500;
  font-size: 0.92rem;
  letter-spacing: 0.005em;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.12s ease, border-color 0.12s ease, background 0.12s ease;
  cursor: pointer;
}}
.bi-topnav__item:hover {{
  color: {COL_TITLE};
  background: {COL_BG_SOFT};
}}
.bi-topnav__item.is-active {{
  color: {COL_TITLE};
  border-bottom-color: {COL_CYAN};
  font-weight: 600;
}}
.bi-topnav__icon {{
  display: inline-flex; align-items: center;
  width: 16px; height: 16px;
}}
.bi-topnav__icon svg {{ width: 100%; height: 100%; stroke: currentColor; fill: none; }}
.bi-topnav__item.is-active .bi-topnav__icon svg {{ stroke: {COL_CYAN}; }}

/* ---------- Globale Typografie ---------- */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
  font-family: "Calibri", "Segoe UI", -apple-system, BlinkMacSystemFont,
               "Helvetica Neue", Arial, sans-serif;
  color: {COL_TEXT};
  background: {COL_BG};
}}
.block-container {{
  padding-top: 1.4rem !important;
  padding-bottom: 5rem !important;
  max-width: 1080px !important;
}}
h1, h2, h3, h4 {{
  color: {COL_TITLE};
  font-weight: 700;
  letter-spacing: -0.005em;
}}
h1 {{ font-size: 1.7rem; }}
h2 {{ font-size: 1.2rem; margin-top: 1.4rem; }}
h3 {{ font-size: 1.0rem; margin-top: 1.0rem; }}

p, li, .stMarkdown {{ color: {COL_TEXT}; line-height: 1.6; }}

/* Cyan bullet markers wie auf den Folien */
.stMarkdown ul li::marker {{ color: {COL_CYAN}; font-size: 1.1em; }}
.stMarkdown ol li::marker {{ color: {COL_CYAN}; }}

/* ---------- Slide-Header ---------- */
.bi-slide-header {{
  border-bottom: 1px solid {COL_BORDER};
  padding: 0.2rem 0 1.1rem 0;
  margin-bottom: 1.6rem;
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 2rem; flex-wrap: wrap;
}}
.bi-slide-header__main {{ flex: 1 1 auto; min-width: 0; }}
.bi-slide-header__chair {{
  font-size: 0.78rem; color: {COL_TEXT_MUTED};
  letter-spacing: 0.01em; margin-bottom: 0.25rem;
}}
.bi-slide-header__title {{
  font-size: 1.55rem; font-weight: 700; color: {COL_TITLE};
  margin: 0; letter-spacing: -0.01em; line-height: 1.2;
}}
.bi-slide-header__sub {{
  font-size: 0.92rem; color: {COL_TEXT}; margin-top: 0.35rem;
}}
.bi-slide-header__status {{
  display: inline-flex; align-items: center; gap: 0.5rem;
  font-size: 0.78rem; color: {COL_TITLE};
  border: 1px solid {COL_BORDER}; padding: 0.4rem 0.85rem;
  background: {COL_BG}; font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  white-space: nowrap;
}}
.bi-slide-header__status::before {{
  content: ""; width: 8px; height: 8px; border-radius: 50%;
  background: {COL_CYAN};
}}

/* ---------- Section-Block (Slide-Body-Imitation) ---------- */
.bi-section {{ margin: 1.2rem 0 1.6rem 0; }}
.bi-section__kicker {{
  font-size: 0.75rem; color: {COL_CYAN_DARK};
  font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.4rem;
  display: flex; align-items: center; gap: 0.5rem;
}}
.bi-section__kicker::before {{
  content: ""; width: 8px; height: 8px; background: {COL_CYAN};
  display: inline-block; border-radius: 50%;
}}
.bi-section__title {{
  font-size: 1.3rem; font-weight: 700; color: {COL_TITLE};
  margin: 0 0 0.45rem 0;
}}
.bi-section__lead {{
  color: {COL_TEXT}; font-size: 0.94rem; line-height: 1.65; max-width: 70ch;
}}

/* ---------- Kicker (small section label) ---------- */
.bi-kicker {{
  font-size: 0.75rem; color: {COL_CYAN_DARK};
  font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 1.4rem 0 0.55rem 0;
}}

/* ---------- Buttons / Tiles ---------- */
[data-testid="stButton"] > button {{
  border-radius: 3px;
  border: 1px solid {COL_BORDER};
  background: {COL_BG};
  color: {COL_TITLE};
  font-weight: 500;
  font-size: 0.9rem;
  padding: 0.7rem 0.95rem;
  transition: border-color 0.12s ease, background 0.12s ease, color 0.12s ease;
  text-align: left;
  justify-content: flex-start;
  white-space: normal;
  line-height: 1.4;
  min-height: 3rem;
}}
[data-testid="stButton"] > button:hover {{
  border-color: {COL_CYAN};
  background: {COL_CYAN_SOFT};
  color: {COL_TITLE};
}}
[data-testid="stButton"] > button[kind="primary"] {{
  background: {COL_CYAN};
  border-color: {COL_CYAN};
  color: #ffffff;
}}
[data-testid="stButton"] > button[kind="primary"]:hover {{
  background: {COL_CYAN_DARK};
  border-color: {COL_CYAN_DARK};
  color: #ffffff;
}}

/* ---------- Source-Card (an Folien-Aufzaehlungspunkte angelehnt) ---------- */
.bi-source-card {{
  display: grid;
  grid-template-columns: 1.3rem 1fr;
  gap: 0.7rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid {COL_BORDER_SOFT};
}}
.bi-source-card:last-child {{ border-bottom: 0; }}
.bi-source-card__bullet {{
  display: inline-block; width: 0.6rem; height: 0.6rem;
  background: {COL_CYAN}; border-radius: 50%;
  margin-top: 0.45rem;
}}
.bi-source-card__head {{
  display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: baseline;
  margin-bottom: 0.3rem;
}}
.bi-source-card__num {{
  font-variant-numeric: tabular-nums;
  font-weight: 700; color: {COL_TITLE}; font-size: 0.82rem;
}}
.bi-source-card__doc {{
  color: {COL_TITLE}; font-weight: 600; font-size: 0.93rem;
}}
.bi-source-card__meta {{
  color: {COL_TEXT_MUTED}; font-size: 0.78rem;
}}
.bi-source-card__body {{
  color: {COL_TEXT}; font-size: 0.92rem; line-height: 1.6;
}}

/* ---------- Meta-Footer-Zeile (analog Folien-Fusszeile) ---------- */
.bi-meta {{
  display: flex; gap: 1.5rem; align-items: center;
  font-size: 0.78rem; color: {COL_TEXT_MUTED};
  margin-top: 0.95rem;
  padding-top: 0.7rem;
  border-top: 1px solid {COL_BORDER};
  font-variant-numeric: tabular-nums;
}}
.bi-meta__label {{
  font-size: 0.72rem; color: {COL_TEXT_MUTED}; margin-right: 0.4rem;
  letter-spacing: 0.01em;
}}
.bi-meta__value {{ color: {COL_TITLE}; font-weight: 600; }}
.bi-meta__status--ok {{ color: {COL_OK}; }}
.bi-meta__status--warn {{ color: {COL_WARN}; }}

/* ---------- Chat-Messages ---------- */
[data-testid="stChatMessage"] {{
  background: {COL_BG};
  border: 1px solid {COL_BORDER};
  border-radius: 4px;
  padding: 1.05rem 1.25rem;
  box-shadow: none;
}}
[data-testid="stChatMessage"][data-testid*="user"] {{
  background: {COL_BG_SOFT};
  border-color: {COL_BORDER_SOFT};
}}

/* ---------- Chat-Input ---------- */
.stChatInputContainer textarea,
[data-testid="stChatInput"] textarea {{
  border-radius: 3px !important;
  border-color: {COL_BORDER} !important;
}}
.stChatInputContainer textarea:focus,
[data-testid="stChatInput"] textarea:focus {{
  border-color: {COL_CYAN} !important;
  box-shadow: none !important;
}}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
  background: {COL_BG_SOFT};
  border-right: 1px solid {COL_BORDER};
}}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {{
  font-size: 0.72rem; text-transform: uppercase;
  letter-spacing: 0.1em; color: {COL_TEXT_MUTED};
  font-weight: 700;
  margin-top: 1rem; margin-bottom: 0.4rem;
}}
[data-testid="stSidebar"] hr {{
  margin: 0.85rem 0; border-color: {COL_BORDER_SOFT};
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button {{
  font-size: 0.85rem; min-height: 2.4rem; padding: 0.45rem 0.75rem;
}}

/* ---------- Expander ---------- */
[data-testid="stExpander"] {{
  border: 1px solid {COL_BORDER};
  border-radius: 4px;
  background: {COL_BG};
}}
[data-testid="stExpander"] summary {{
  font-weight: 600;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: {COL_CYAN_DARK};
  padding: 0.55rem 0.8rem;
}}

/* ---------- Inputs / Selects ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox > div > div {{
  border-radius: 3px !important;
  border-color: {COL_BORDER} !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus,
.stNumberInput input:focus {{
  border-color: {COL_CYAN} !important;
  box-shadow: none !important;
}}

/* ---------- Tables ---------- */
[data-testid="stDataFrame"] {{
  border: 1px solid {COL_BORDER}; border-radius: 4px; overflow: hidden;
}}

/* ---------- Metric ---------- */
[data-testid="stMetric"] {{
  background: {COL_BG};
  padding: 0.85rem 1rem;
  border: 1px solid {COL_BORDER};
  border-radius: 4px;
}}
[data-testid="stMetricValue"] {{
  font-size: 1.6rem; font-weight: 700; color: {COL_TITLE};
}}
[data-testid="stMetricLabel"] {{
  color: {COL_TEXT_MUTED}; font-size: 0.78rem;
  letter-spacing: 0.02em;
}}

/* ---------- Slide-Footer ---------- */
.bi-slide-footer {{
  margin-top: 3rem;
  padding-top: 0.85rem;
  border-top: 1px solid {COL_BORDER};
  display: flex; justify-content: space-between;
  font-size: 0.74rem; color: {COL_TEXT_MUTED};
}}

/* ---------- Forum: Rolle-Badge ---------- */
.bi-role {{
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.12rem 0.55rem; font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.02em; border-radius: 2px; border: 1px solid;
  text-transform: none;
}}
.bi-role--student   {{ color: #555; border-color: #d0d0d0; background: #fafafa; }}
.bi-role--tutor     {{ color: {COL_CYAN_DARK}; border-color: {COL_CYAN}; background: {COL_CYAN_SOFT}; }}
.bi-role--prof      {{ color: #ffffff; border-color: {COL_TITLE}; background: {COL_TITLE}; }}

/* ---------- Forum: Status-Pills ---------- */
.bi-pill {{
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.12rem 0.55rem; font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.02em; border-radius: 2px; border: 1px solid;
}}
.bi-pill--pinned    {{ color: #8a6d00; border-color: #e0b800; background: #fff7d6; }}
.bi-pill--resolved  {{ color: #1c6e3d; border-color: #6cc28d; background: #e9f7ef; }}
.bi-pill--module    {{ color: {COL_CYAN_DARK}; border-color: {COL_CYAN}; background: {COL_CYAN_SOFT}; }}

/* ---------- Forum: Thread-Karte (Listenansicht) ---------- */
.bi-thread {{
  display: grid; grid-template-columns: 1fr auto; gap: 0.6rem;
  padding: 1rem 1.1rem; border: 1px solid {COL_BORDER};
  background: {COL_BG}; margin-bottom: 0.6rem;
  border-left: 3px solid {COL_BORDER};
  transition: border-left-color 0.12s ease, box-shadow 0.12s ease;
}}
.bi-thread:hover {{ border-left-color: {COL_CYAN}; }}
.bi-thread--pinned {{ border-left-color: #e0b800; }}
.bi-thread--resolved {{ border-left-color: #6cc28d; }}
.bi-thread__title {{
  font-size: 1.02rem; font-weight: 700; color: {COL_TITLE};
  margin: 0 0 0.25rem 0; line-height: 1.35;
}}
.bi-thread__excerpt {{
  font-size: 0.88rem; color: {COL_TEXT}; line-height: 1.5;
  margin-bottom: 0.45rem;
}}
.bi-thread__meta {{
  display: flex; gap: 0.45rem; align-items: center; flex-wrap: wrap;
  font-size: 0.76rem; color: {COL_TEXT_MUTED};
}}
.bi-thread__count {{
  align-self: start;
  text-align: right; font-size: 0.78rem; color: {COL_TEXT_MUTED};
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}}
.bi-thread__count strong {{ color: {COL_TITLE}; font-size: 1.05rem; font-weight: 700; }}

/* ---------- Forum: Post-Karte (Detailansicht) ---------- */
.bi-post {{
  display: grid; grid-template-columns: 11rem 1fr; gap: 1.2rem;
  padding: 1rem 0; border-top: 1px solid {COL_BORDER};
}}
.bi-post--first {{ border-top: 0; }}
.bi-post--endorsed {{
  background: linear-gradient(to right, {COL_CYAN_SOFT} 0, transparent 12px);
}}
.bi-post__author {{
  display: flex; flex-direction: column; gap: 0.3rem;
}}
.bi-post__author-name {{
  font-weight: 700; color: {COL_TITLE}; font-size: 0.92rem; line-height: 1.3;
}}
.bi-post__author-time {{
  font-size: 0.74rem; color: {COL_TEXT_MUTED};
  font-variant-numeric: tabular-nums;
}}
.bi-post__body {{
  color: {COL_TEXT}; font-size: 0.94rem; line-height: 1.6;
}}
.bi-post__endorse {{
  display: inline-flex; align-items: center; gap: 0.3rem;
  font-size: 0.72rem; color: {COL_CYAN_DARK}; font-weight: 600;
  margin-top: 0.4rem;
}}
.bi-post__endorse::before {{
  content: ""; width: 7px; height: 7px; background: {COL_CYAN}; border-radius: 50%;
}}

/* ---------- Identitaets-Block in der Forum-Sidebar ---------- */
.bi-identity {{
  background: {COL_BG}; border: 1px solid {COL_BORDER};
  padding: 0.7rem 0.85rem; margin-bottom: 0.6rem;
}}
.bi-identity__row {{
  display: flex; gap: 0.5rem; align-items: center;
  font-size: 0.85rem; color: {COL_TITLE};
}}
.bi-identity__label {{ color: {COL_TEXT_MUTED}; font-size: 0.74rem; }}
</style>
"""


def apply_theme(*, page_title: str, page_icon: str = "", layout: str = "wide") -> None:
    """Page config + global CSS injection."""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon or None,
        layout=layout,
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS, unsafe_allow_html=True)


# --- Top-Navigation -------------------------------------------------------
_TOPNAV_ITEMS = [
    ("dialog",     "Dialog",         "/",            "chat"),
    ("forum",      "Forum",          "/Forum",       "users"),
    ("quiz",       "Quiz",           "/Quiz",        "quiz"),
    ("admin",      "Administration", "/Admin",       "settings"),
    ("evaluation", "Evaluation",     "/Evaluation",  "chart"),
]

_SVG_ICONS = {
    "chat":     '<svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    "users":    '<svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "settings": '<svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "chart":    '<svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="3" y1="20" x2="21" y2="20"/></svg>',
    "quiz":     '<svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/><circle cx="12" cy="12" r="10"/></svg>',
}


def render_topnav(active: str) -> None:
    """Horizontal top navigation in the style of professional web apps."""
    items_html = ""
    for key, label, href, icon in _TOPNAV_ITEMS:
        cls = "bi-topnav__item is-active" if key == active else "bi-topnav__item"
        items_html += (
            f'<a class="{cls}" href="{href}" target="_self">'
            f'  <span class="bi-topnav__icon">{_SVG_ICONS[icon]}</span>'
            f'  <span>{label}</span>'
            f'</a>'
        )
    st.markdown(
        f'<nav class="bi-topnav">{items_html}</nav>',
        unsafe_allow_html=True,
    )


def render_header(
    title: str,
    tagline: str | None = None,
    status_label: str | None = None,
    breadcrumb: str | None = None,
) -> None:
    """Slide-style title header: chair label above, bold title, optional sub.

    `breadcrumb` is used for the small chair label override (default: chair).
    """
    chair = breadcrumb or CHAIR_NAME
    sub_html = (
        f'<div class="bi-slide-header__sub">{tagline}</div>'
        if tagline else ""
    )
    status_html = (
        f'<div class="bi-slide-header__status">{status_label}</div>'
        if status_label else ""
    )
    st.markdown(
        f"""
<div class="bi-slide-header">
  <div class="bi-slide-header__main">
    <div class="bi-slide-header__chair">{chair}</div>
    <h1 class="bi-slide-header__title">{title}</h1>
    {sub_html}
  </div>
  {status_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_section(kicker: str, title: str, lead: str = "") -> None:
    """Cyan-bullet kicker + heading + optional lead."""
    lead_html = f'<div class="bi-section__lead">{lead}</div>' if lead else ""
    st.markdown(
        f"""
<div class="bi-section">
  <div class="bi-section__kicker">{kicker}</div>
  <div class="bi-section__title">{title}</div>
  {lead_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_kicker(text: str) -> None:
    """Small uppercase cyan label between blocks."""
    st.markdown(f'<div class="bi-kicker">{text}</div>', unsafe_allow_html=True)


def render_source_card(index: int, src: dict[str, Any]) -> None:
    """Source card with cyan bullet, hierarchic typography, no badges."""
    doc = src.get("document", "—")
    slide = src.get("slide", "—")
    module = src.get("module", "—")
    preview = (src.get("preview") or "").replace("\n", " ")
    st.markdown(
        f"""
<div class="bi-source-card">
  <span class="bi-source-card__bullet"></span>
  <div>
    <div class="bi-source-card__head">
      <span class="bi-source-card__num">{index:02d}</span>
      <span class="bi-source-card__doc">{doc}</span>
      <span class="bi-source-card__meta">Folie {slide} · {module}</span>
    </div>
    <div class="bi-source-card__body">{preview}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_meta(latency_s: float | None = None, refused: bool = False, sources_count: int | None = None) -> None:
    """Footer strip beneath an answer (echoes the slide-footer style)."""
    parts: list[str] = []
    if sources_count is not None:
        parts.append(
            f'<span><span class="bi-meta__label">Quellen</span>'
            f'<span class="bi-meta__value">{sources_count}</span></span>'
        )
    if latency_s is not None:
        parts.append(
            f'<span><span class="bi-meta__label">Latenz</span>'
            f'<span class="bi-meta__value">{latency_s:.2f} s</span></span>'
        )
    status_cls = "bi-meta__status--warn" if refused else "bi-meta__status--ok"
    status_txt = "Ablehnung · Unsicherheit" if refused else "Beantwortet"
    parts.append(
        f'<span><span class="bi-meta__label">Status</span>'
        f'<span class="bi-meta__value {status_cls}">{status_txt}</span></span>'
    )
    st.markdown(f'<div class="bi-meta">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_slide_footer(left: str | None = None) -> None:
    """Optional slide-footer mit Lehrstuhl-Info links + Seitenkennung rechts."""
    st.markdown(
        f"""
<div class="bi-slide-footer">
  <span>{left or CHAIR_AUTHOR + ' · ' + CHAIR_NAME}</span>
  <span>BI-Tutor · Prototyp</span>
</div>
        """,
        unsafe_allow_html=True,
    )


def model_status_label() -> str:
    """Status pill content (oben rechts im Header)."""
    return f"OpenAI · {settings.openai_model}"


# ---------------------------------------------------------------------------
# Forum-spezifische kleine Helfer
# ---------------------------------------------------------------------------
def role_badge_html(role: str) -> str:
    """Return inline-HTML snippet for a colored role badge."""
    cls = {
        "Studierend": "bi-role--student",
        "Tutor:in": "bi-role--tutor",
        "Professor:in": "bi-role--prof",
    }.get(role, "bi-role--student")
    return f'<span class="bi-role {cls}">{role}</span>'


def status_pill_html(label: str, kind: str) -> str:
    return f'<span class="bi-pill bi-pill--{kind}">{label}</span>'


# ---------------------------------------------------------------------------
# Slide preview (lazy)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=200)
def _cached_slide_png(document: str, slide: int) -> bytes | None:
    from .slides import render_slide_png
    return render_slide_png(document, slide)


def render_slide_toggle(src: dict[str, Any], *, key: str) -> None:
    """Small toggle beneath a source card that lazy-renders the slide."""
    doc = src.get("document")
    slide = src.get("slide")
    if not doc or slide is None:
        return
    show = st.toggle("Folie als Bild anzeigen", key=key, value=False)
    if show:
        img = _cached_slide_png(doc, slide)
        if img:
            st.image(img, use_container_width=True)
            st.caption(f"{doc} · Folie {slide}")
        else:
            st.caption("_Folie konnte nicht gerendert werden._")
