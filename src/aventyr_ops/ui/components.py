from __future__ import annotations

import base64
import re
from collections.abc import Iterable
from decimal import Decimal
from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import BaseModel

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@lru_cache(maxsize=1)
def _wordmark_data_uri() -> str:
    raw = (_ASSETS_DIR / "aventyr-wordmark.webp").read_bytes()
    return f"data:image/webp;base64,{base64.b64encode(raw).decode('ascii')}"


BRAND = {
    "bg": "#0A1628",
    "bg_2": "#0B1A33",
    "bg_3": "#0E1F3C",
    "ink": "#F3F6FB",
    "ink_2": "#D6DEEA",
    "ink_3": "#A8B5C8",
    "ink_4": "#7F8FA6",
    "hair": "rgba(255,255,255,0.08)",
    "hair_2": "rgba(255,255,255,0.14)",
    "cyan": "#00C8FF",
    "cyan_line": "rgba(0,200,255,0.35)",
    "cyan_soft": "rgba(0,200,255,0.10)",
    "green": "#2BDD8A",
    "green_line": "rgba(43,221,138,0.40)",
    "amber": "#F0B845",
    "amber_line": "rgba(240,184,69,0.45)",
    "red": "#F0667E",
    "red_line": "rgba(240,102,126,0.45)",
}


def page_chrome() -> None:
    st.set_page_config(
        page_title="Aventyr Ops",
        page_icon="https://www.aventyr.ai/favicon.ico",
        layout="wide",
        initial_sidebar_state="auto",
    )
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

          html, body, [class*="css"], .stApp, .stMarkdown, .stMarkdown p, .stMarkdown li,
          div, span, button, input, label, select, textarea {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
          }}
          .mono, .mono * {{ font-family: 'JetBrains Mono', ui-monospace, SF Mono, Menlo, monospace !important; }}

          .stApp {{ background: {BRAND['bg']}; color: {BRAND['ink']}; }}
          .block-container {{
            padding: 0 !important;
            max-width: none !important;
          }}
          header[data-testid="stHeader"] {{
            background: transparent;
            height: 0;
            pointer-events: none;
          }}
          /* Streamlit's dev toolbar contains the Deploy button, overflow menu,
             and the sidebar expand toggle. Hide the dev controls at every width
             and pin the expand toggle to the viewport so the user can always
             reopen the sidebar after collapsing it (mobile or desktop). The
             toolbar wrapper is pointer-transparent so it doesn't block clicks
             on the workbench beneath it. */
          [data-testid="stToolbar"] {{
            display: block !important;
            pointer-events: none;
          }}
          [data-testid="stToolbarActions"],
          [data-testid="stAppDeployButton"],
          [data-testid="stMainMenu"] {{ display: none !important; }}
          [data-testid="stDecoration"] {{ display: none; }}
          [data-testid="stExpandSidebarButton"] {{
            position: fixed !important;
            top: 0.55rem !important;
            left: 0.65rem !important;
            z-index: 1001 !important;
            pointer-events: auto;
            background: rgba(10,22,40,0.82) !important;
            border: 1px solid {BRAND['hair_2']} !important;
            border-radius: 6px !important;
            padding: 0.32rem 0.42rem !important;
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
          }}
          [data-testid="stExpandSidebarButton"]:hover {{
            border-color: {BRAND['cyan']} !important;
          }}
          [data-testid="stExpandSidebarButton"] svg,
          [data-testid="stExpandSidebarButton"] span {{ color: {BRAND['cyan']} !important; }}

          /* Desktop: sidebar is permanent furniture. Force it visible
             regardless of any persisted collapsed state in localStorage,
             and hide both toggle controls (collapse inside the sidebar +
             the floating expand pill at top-left). Mobile keeps the
             overlay/toggle behavior defined in the ≤760px media query. */
          @media (min-width: 761px) {{
            [data-testid="stSidebar"] {{
              transform: none !important;
              opacity: 1 !important;
              visibility: visible !important;
              pointer-events: auto !important;
            }}
            [data-testid="stSidebarCollapseButton"],
            [data-testid="stExpandSidebarButton"] {{
              display: none !important;
            }}
          }}

          /* Hide default Streamlit footer */
          footer {{ display: none; }}

          /* ===== Sidebar ===== */
          [data-testid="stSidebar"] {{
            background: {BRAND['bg']};
            border-right: 1px solid {BRAND['hair']};
            width: 224px !important;
            min-width: 224px !important;
          }}
          [data-testid="stSidebar"] > div:first-child {{
            padding: 1.4rem 0.9rem 1.4rem;
          }}
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ margin: 0; }}

          .sb-brand {{
            display: flex; align-items: center;
            padding: 0.45rem 0.45rem 1.55rem;
          }}
          .sb-brand .sb-logo {{
            display: block;
            height: 32px; width: auto;
            max-width: 100%;
            user-select: none;
            -webkit-user-drag: none;
          }}
          .sb-section {{
            display: flex; align-items: center; gap: 0.5rem;
            padding: 0.95rem 0.55rem 0.55rem;
            color: {BRAND['ink_4']};
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.66rem; letter-spacing: 0.18em;
            text-transform: uppercase; font-weight: 600;
          }}
          .sb-section::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: {BRAND['hair']};
          }}
          .sb-foot {{
            margin-top: 1.4rem; padding: 0.85rem 0.5rem 0;
            border-top: 1px solid {BRAND['hair']};
            color: {BRAND['ink_3']}; font-size: 0.78rem;
            line-height: 1.6;
          }}
          .sb-foot b {{ color: {BRAND['ink_2']}; font-weight: 500; }}

          /* Sidebar radio styled as nav links */
          [data-testid="stSidebar"] [role="radiogroup"] {{
            gap: 0.18rem !important;
            display: flex; flex-direction: column;
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label {{
            display: flex !important;
            align-items: center;
            padding: 0.55rem 0.7rem 0.55rem 2.35rem;
            border-radius: 6px;
            color: {BRAND['ink_3']};
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            position: relative;
            transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
          }}
          /* Monoline icon, masked by SVG, colored by background-color so it
             can pick up hover/active states without swapping the URL. */
          [data-testid="stSidebar"] [role="radiogroup"] > label::before {{
            content: '';
            position: absolute;
            left: 0.7rem; top: 50%;
            width: 17px; height: 17px;
            transform: translateY(-50%);
            background-color: {BRAND['ink_4']};
            -webkit-mask-repeat: no-repeat;
            mask-repeat: no-repeat;
            -webkit-mask-position: center;
            mask-position: center;
            -webkit-mask-size: contain;
            mask-size: contain;
            transition: background-color 0.18s ease;
          }}
          /* Streamlit hides its own radio dot via this descendant div */
          [data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child {{
            display: none !important;
          }}
          /* Per-item icons. SVGs are minimal Lucide-style monolines, URL-encoded
             inline so the bundle is self-contained. */
          [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(1)::before {{
            -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='2' x2='12' y2='22'/%3E%3Cpath d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/%3E%3C/svg%3E");
            mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='2' x2='12' y2='22'/%3E%3Cpath d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/%3E%3C/svg%3E");
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(2)::before {{
            -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/%3E%3Cpath d='M13.73 21a2 2 0 0 1-3.46 0'/%3E%3C/svg%3E");
            mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/%3E%3Cpath d='M13.73 21a2 2 0 0 1-3.46 0'/%3E%3C/svg%3E");
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(3)::before {{
            -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
            mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(4)::before {{
            -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 17 2 2 4-4'/%3E%3Cpath d='m3 7 2 2 4-4'/%3E%3Cpath d='M13 6h8'/%3E%3Cpath d='M13 12h8'/%3E%3Cpath d='M13 18h8'/%3E%3C/svg%3E");
            mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 17 2 2 4-4'/%3E%3Cpath d='m3 7 2 2 4-4'/%3E%3Cpath d='M13 6h8'/%3E%3Cpath d='M13 12h8'/%3E%3Cpath d='M13 18h8'/%3E%3C/svg%3E");
          }}
          /* Hover: subtle white tint + lift icon to ink_2 */
          [data-testid="stSidebar"] [role="radiogroup"] > label:hover {{
            background: rgba(255,255,255,0.035);
            color: {BRAND['ink_2']};
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:hover::before {{
            background-color: {BRAND['ink_2']};
          }}
          /* Primary product (first item — Alarm Billing) reads as primary
             through a slightly heavier weight + a gap before the secondary
             items. No hairline divider — it intersected the active bg tint
             awkwardly. */
          [data-testid="stSidebar"] [role="radiogroup"] > label:first-child {{
            color: {BRAND['ink_2']};
            font-weight: 600;
            margin-bottom: 0.5rem;
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:first-child::before {{
            background-color: {BRAND['ink_3']};
          }}
          /* Active state: cyan tint background, cyan icon, ink-white text. The
             icon + bg tint do all the work — no extra accent dot. */
          [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {{
            background: rgba(0,200,255,0.09);
            color: {BRAND['ink']};
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked)::before {{
            background-color: {BRAND['cyan']};
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label[data-baseweb="radio"] p {{
            color: inherit !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            letter-spacing: -0.005em;
          }}
          [data-testid="stSidebar"] [role="radiogroup"] > label:first-child[data-baseweb="radio"] p {{
            font-weight: 600 !important;
          }}

          /* ===== Main area ===== */
          [data-testid="stMain"] {{
            background: {BRAND['bg']};
          }}
          [data-testid="stMain"] > div:first-child,
          [data-testid="stMain"] [data-testid="stMainBlockContainer"],
          [data-testid="stMain"] .stMainBlockContainer {{
            padding: 0 !important;
            max-width: none !important;
          }}
          [data-testid="stMain"] [data-testid="stVerticalBlock"],
          [data-testid="stMain"] .stVerticalBlock {{ gap: 0 !important; }}
          /* Streamlit's stMarkdownContainer ships with margin-bottom: -16px,
             which collapses ~1rem off every workbench gap. Zero it so the
             margins/paddings in this stylesheet are the actual rendered gaps. */
          [data-testid="stMain"] [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
          .main-wrap {{ padding-bottom: 3rem; }}

          /* ===== Toolbar ===== */
          .wb-toolbar {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 0.95rem 1.6rem;
            border-bottom: 1px solid {BRAND['hair']};
            position: sticky; top: 0; z-index: 10;
            background: rgba(10,22,40,0.92);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
          }}
          .wb-crumb {{
            font-size: 0.78rem; color: {BRAND['ink_3']};
            letter-spacing: 0.02em;
          }}
          .wb-crumb b {{ color: {BRAND['ink']}; font-weight: 600; }}
          .wb-crumb .sep {{ color: {BRAND['ink_4']}; margin: 0 0.45rem; }}
          .wb-actions {{
            display: flex; gap: 0.55rem; align-items: center;
          }}
          .wb-status {{
            display: inline-flex; align-items: center; gap: 0.45rem;
            padding: 0.32rem 0.7rem; border-radius: 999px;
            font-size: 0.74rem; color: {BRAND['ink_2']};
            border: 1px solid {BRAND['hair_2']};
            background: rgba(255,255,255,0.03);
          }}
          .wb-status .dot {{
            width: 6px; height: 6px; border-radius: 50%;
            background: {BRAND['green']};
          }}

          /* ===== Head ===== */
          .wb-head {{
            padding: 1.4rem 1.6rem 0.4rem;
          }}
          .wb-head .deck {{
            color: {BRAND['ink_3']}; font-size: 0.8rem;
            letter-spacing: 0.04em; margin-bottom: 0.35rem;
          }}
          .wb-head .deck b {{ color: {BRAND['ink_2']}; font-weight: 500; }}
          .wb-head h1 {{
            font-size: 1.55rem; font-weight: 600;
            letter-spacing: -0.022em; margin: 0 0 0.55rem;
            color: {BRAND['ink']};
          }}
          .wb-head p {{
            color: {BRAND['ink_2']}; font-size: 0.95rem;
            margin: 0; max-width: 760px; line-height: 1.6;
          }}

          /* ===== KPI row ===== */
          .wb-kpi-row {{
            display: flex; flex-wrap: wrap;
            padding: 1.2rem 1.6rem 1.3rem;
            border-bottom: 1px solid {BRAND['hair']};
          }}
          .wb-kpi {{
            flex: 1 1 0; min-width: 150px;
            padding: 0 1.4rem; position: relative;
          }}
          .wb-kpi:first-child {{ padding-left: 0; }}
          .wb-kpi:last-child {{ padding-right: 0; }}
          .wb-kpi + .wb-kpi {{ border-left: 1px solid {BRAND['hair']}; }}
          .wb-kpi .l {{
            color: {BRAND['ink_3']}; font-size: 0.74rem;
            letter-spacing: 0.04em; font-weight: 500;
          }}
          .wb-kpi .v {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-feature-settings: 'tnum' 1;
            font-weight: 600; font-size: 1.65rem;
            line-height: 1.1; letter-spacing: -0.02em;
            color: {BRAND['ink']}; margin-top: 0.4rem;
          }}
          .wb-kpi .s {{
            color: {BRAND['ink_3']}; font-size: 0.78rem;
            margin-top: 0.25rem;
          }}
          .wb-kpi.ok .v {{ color: {BRAND['green']}; }}
          .wb-kpi.warn .v {{ color: {BRAND['amber']}; }}
          .wb-kpi.cyan .v {{ color: {BRAND['cyan']}; }}

          /* ===== Section ===== */
          .wb-section {{ padding: 1.6rem 1.6rem 0; }}
          /* Workbench toolbar row: lays the picker + action button inline,
             aligned to the section's 1.6rem inset. Streamlit wraps
             st.columns in stLayoutWrapper, which sits as the next sibling
             of the wb-toolbar-pad's element container, so we walk that
             relationship with :has() + adjacent. */
          [data-testid="stElementContainer"]:has(.wb-toolbar-pad)
            + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] {{
            padding: 0.85rem 1.6rem 0.55rem;
            gap: 0.55rem !important;
            align-items: center;
          }}
          [data-testid="stElementContainer"]:has(.wb-toolbar-pad)
            + [data-testid="stLayoutWrapper"] [data-testid="stColumn"] {{
            min-width: 0;
          }}
          [data-testid="stElementContainer"]:has(.wb-toolbar-pad)
            + [data-testid="stLayoutWrapper"] .stButton > button {{
            white-space: nowrap;
            padding: 0.5rem 1.1rem;
          }}
          [data-testid="stElementContainer"]:has(.wb-toolbar-pad)
            + [data-testid="stLayoutWrapper"] .stButton > button p {{
            white-space: nowrap;
          }}
          .wb-section-head {{
            display: flex; align-items: baseline; justify-content: space-between;
            margin-bottom: 0.9rem; padding-bottom: 0.55rem;
            border-bottom: 1px solid {BRAND['hair']};
          }}
          .wb-section-head h2 {{
            font-size: 0.84rem; font-weight: 600;
            color: {BRAND['ink']}; margin: 0;
            letter-spacing: -0.005em;
          }}
          .wb-section-head .meta {{
            color: {BRAND['ink_3']}; font-size: 0.78rem;
            font-family: 'JetBrains Mono', ui-monospace, monospace;
          }}

          /* ===== Master table ===== */
          .wb-table-wrap {{ width: 100%; overflow-x: auto; }}
          .wb-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            table-layout: fixed;
            border: 0;
          }}
          .wb-table thead th, .wb-table tbody td {{ border: 0; background: transparent; }}
          /* Streamlit's table reset puts a faint top border on every tr;
             strip it so only the borders we author (group-break bottoms,
             tbody td bottoms) render. */
          .wb-table tr {{ border: 0 !important; }}
          /* Column headers are redundant once buckets and group breaks
             (BILLABLE · 8 / HELD · 2 / SKIPPED · 2) carry the status legend.
             Hiding the thead row removes a competing label stack between the
             buckets and the first group break. */
          .wb-table thead {{ display: none; }}
          .wb-table tbody td {{
            padding: 0.95rem 1rem;
            border-bottom: 1px solid {BRAND['hair']};
            font-size: 0.88rem; color: {BRAND['ink']};
            vertical-align: middle;
            word-wrap: break-word; overflow-wrap: anywhere;
          }}
          .wb-table tbody td:first-child {{ padding-left: 0; }}
          .wb-table tbody td:last-child {{ padding-right: 0; }}
          .wb-table tbody tr:hover td {{ background: rgba(255,255,255,0.018); }}
          .wb-table tbody tr:last-child td {{ border-bottom: 0; }}
          .wb-table col.col-id {{ width: 6rem; }}
          .wb-table col.col-status {{ width: 7.2rem; }}
          .wb-table col.col-cust {{ width: auto; }}
          .wb-table col.col-reason {{ width: auto; }}
          .wb-table col.col-owner {{ width: 9rem; }}
          .wb-table col.col-amt {{ width: 6rem; }}
          .wb-table td.id {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.85rem; color: {BRAND['ink_2']};
            white-space: nowrap;
          }}
          .wb-table td.amt {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-feature-settings: 'tnum' 1;
            text-align: right; font-weight: 600;
            white-space: nowrap;
          }}
          .wb-table td.amt.muted {{ color: {BRAND['ink_4']}; font-weight: 400; }}
          .wb-table td.amt.hold {{ color: {BRAND['amber']}; font-weight: 600; font-size: 0.78rem; letter-spacing: 0.06em; }}
          .wb-table td.tag {{ white-space: nowrap; }}
          .wb-table td.cust .name {{ color: {BRAND['ink']}; font-size: 0.9rem; line-height: 1.35; }}
          .wb-table td.cust .site {{ color: {BRAND['ink_3']}; font-size: 0.78rem; margin-top: 0.2rem; line-height: 1.35; }}
          .wb-table td.reason {{ color: {BRAND['ink_2']}; font-size: 0.85rem; line-height: 1.45; }}
          .wb-table td.reason.empty {{ color: {BRAND['ink_4']}; }}
          .wb-table td.owner {{ color: {BRAND['ink_3']}; font-size: 0.83rem; }}
          .row-tag {{
            display: inline-block;
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            padding: 0.2rem 0.5rem; border-radius: 4px;
            font-size: 0.68rem; letter-spacing: 0.08em;
            border: 1px solid transparent;
            background: transparent;
            white-space: nowrap;
          }}
          .row-tag.ok {{ color: {BRAND['green']}; border-color: {BRAND['green_line']}; }}
          .row-tag.warn {{ color: {BRAND['amber']}; border-color: {BRAND['amber_line']}; }}
          .row-tag.skip {{ color: {BRAND['ink_4']}; border-color: {BRAND['hair_2']}; }}
          .row-tag.risk {{ color: {BRAND['red']}; border-color: {BRAND['red_line']}; }}

          /* ===== Status bucket row ===== */
          .wb-buckets {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.6rem;
            margin: 0 1.6rem 1.1rem;
          }}
          .wb-bucket {{
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: baseline;
            gap: 0.6rem;
            padding: 0.6rem 0.85rem;
            border: 1px solid {BRAND['hair']};
            border-top: 2px solid {BRAND['hair_2']};
            border-radius: 6px;
            background: rgba(255,255,255,0.015);
          }}
          .wb-bucket.ok {{ border-top-color: {BRAND['green']}; }}
          .wb-bucket.warn {{ border-top-color: {BRAND['amber']}; }}
          .wb-bucket.skip {{ border-top-color: {BRAND['hair_2']}; }}
          .wb-bucket .num {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-feature-settings: 'tnum' 1;
            font-size: 1.25rem; font-weight: 700;
            line-height: 1; color: {BRAND['ink']};
            letter-spacing: -0.02em;
          }}
          .wb-bucket.ok .num {{ color: {BRAND['green']}; }}
          .wb-bucket.warn .num {{ color: {BRAND['amber']}; }}
          .wb-bucket.skip .num {{ color: {BRAND['ink_3']}; }}
          .wb-bucket .lbl {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.7rem; letter-spacing: 0.1em;
            color: {BRAND['ink_3']}; text-transform: uppercase;
            font-weight: 600;
          }}
          .wb-bucket .note {{
            font-size: 0.78rem; color: {BRAND['ink_3']};
            text-align: right;
          }}

          /* ===== Group divider rows inside master table ===== */
          .wb-table tr.group-break td {{
            padding: 1.05rem 0 0.5rem;
            border-bottom: 1px solid {BRAND['hair_2']};
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.7rem; letter-spacing: 0.12em;
            color: {BRAND['ink_4']}; font-weight: 600;
            text-transform: uppercase;
          }}
          .wb-table tr.group-break td:first-child {{ padding-left: 0; }}
          .wb-table tr.group-break:first-child td {{ padding-top: 0; }}

          /* ===== Workflow strip ===== */
          .wb-work {{
            display: grid; grid-template-columns: repeat(4, 1fr);
            margin-top: 0.4rem;
          }}
          .wb-work .step {{
            padding: 1rem 1.4rem 1.05rem 0;
            border-right: 1px solid {BRAND['hair']};
          }}
          .wb-work .step:not(:first-child) {{ padding-left: 1.4rem; }}
          .wb-work .step:last-child {{ border-right: none; padding-right: 0; }}
          .wb-work .n {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.72rem; color: {BRAND['cyan']};
            font-weight: 600; letter-spacing: 0.04em;
          }}
          .wb-work .t {{
            font-weight: 600; font-size: 0.93rem;
            color: {BRAND['ink']}; margin-top: 0.35rem;
          }}
          .wb-work .d {{
            color: {BRAND['ink_3']}; font-size: 0.85rem;
            line-height: 1.55; margin-top: 0.3rem;
          }}

          /* ===== Files panel ===== */
          .wb-files {{ padding-bottom: 0.5rem; }}
          .wb-files .row {{
            display: grid; grid-template-columns: 150px 1fr 80px;
            gap: 1rem; padding: 0.8rem 0;
            border-bottom: 1px solid {BRAND['hair']};
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.82rem; align-items: center;
          }}
          .wb-files .row:last-child {{ border-bottom: none; padding-bottom: 0.6rem; }}
          .wb-files .row .label {{
            color: {BRAND['green']}; font-weight: 600;
            letter-spacing: 0.04em;
          }}
          .wb-files .row .path {{
            color: {BRAND['ink_2']}; word-break: break-all;
          }}
          .wb-files .row .sz {{
            color: {BRAND['ink_3']}; text-align: right;
          }}

          /* ===== Footnote ===== */
          .wb-footnote {{
            margin: 2rem 1.6rem 2.4rem;
            padding: 0.95rem 1.1rem;
            border-left: 2px solid {BRAND['amber_line']};
            color: {BRAND['ink_2']}; font-size: 0.86rem; line-height: 1.6;
          }}
          .wb-footnote b {{ color: {BRAND['ink']}; font-weight: 600; }}

          /* ===== Buttons ===== */
          .stButton > button {{
            font-family: 'Inter', sans-serif;
            font-weight: 500; font-size: 0.84rem;
            padding: 0.45rem 0.95rem; border-radius: 6px;
            cursor: pointer;
            border: 1px solid {BRAND['hair_2']};
            background: transparent; color: {BRAND['ink']};
            transition: border-color 0.15s, color 0.15s, background 0.15s;
            box-shadow: none;
          }}
          .stButton > button:hover {{
            border-color: {BRAND['cyan']};
            color: {BRAND['cyan']};
            background: transparent;
          }}
          .stButton > button[kind="primary"] {{
            background: {BRAND['cyan']};
            color: {BRAND['bg']};
            border-color: {BRAND['cyan']};
            font-weight: 600;
          }}
          .stButton > button[kind="primary"]:hover {{
            background: #5DDDFF; color: {BRAND['bg']};
            border-color: #5DDDFF;
          }}
          .stButton > button:focus-visible {{
            outline: 2px solid {BRAND['amber']};
            outline-offset: 2px;
          }}

          /* ===== Selectbox ===== */
          [data-baseweb="select"] > div {{
            background: rgba(255,255,255,0.025) !important;
            border-color: {BRAND['hair_2']} !important;
            border-radius: 6px !important;
            color: {BRAND['ink']} !important;
          }}
          [data-baseweb="select"] svg {{ color: {BRAND['cyan']} !important; }}
          [data-testid="stWidgetLabel"] p {{
            color: {BRAND['ink_3']} !important;
            font-size: 0.74rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            font-weight: 500 !important;
          }}

          /* ===== Expander ===== */
          [data-testid="stExpander"] {{
            background: rgba(255,255,255,0.02);
            border: 1px solid {BRAND['hair']};
            border-radius: 8px;
            box-sizing: border-box;
            max-width: 820px;
            margin: 0.6rem 1.6rem !important;
          }}
          [data-testid="stExpander"] + [data-testid="stExpander"] {{
            margin-top: 0.6rem !important;
          }}
          [data-testid="stExpander"] details[open] {{
            background: rgba(255,255,255,0.025);
          }}
          [data-testid="stExpander"] summary {{
            color: {BRAND['ink_2']};
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            padding: 0.75rem 1rem !important;
            border-bottom: 1px solid transparent;
            transition: color 0.15s, border-color 0.15s;
          }}
          [data-testid="stExpander"] details[open] summary {{
            border-bottom-color: {BRAND['hair']};
            color: {BRAND['ink']};
          }}
          [data-testid="stExpander"] summary:hover {{ color: {BRAND['cyan']}; }}
          [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p {{
            font-family: 'JetBrains Mono', ui-monospace, monospace !important;
            font-size: 0.75rem !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
            font-weight: 600 !important;
          }}
          [data-testid="stExpander"] svg {{ color: {BRAND['cyan']} !important; }}
          [data-testid="stExpander"] [data-testid="stExpanderDetails"],
          [data-testid="stExpander"] details > div {{
            padding: 0.85rem 1rem 1rem !important;
          }}
          [data-testid="stExpander"]:first-of-type {{ margin-top: 1.1rem !important; }}

          /* ===== DataFrame ===== */
          [data-testid="stDataFrame"] {{
            background: rgba(255,255,255,0.02);
            border: 1px solid {BRAND['hair']};
            border-radius: 8px; overflow: hidden;
          }}
          [data-testid="stDataFrame"] [data-testid="stElementToolbar"],
          [data-testid="stElementToolbar"] {{ display: none !important; }}

          /* ===== Inbound bubble ===== */
          .wb-bubble {{
            background: rgba(255,255,255,0.03);
            border: 1px solid {BRAND['hair_2']};
            border-radius: 10px;
            border-bottom-left-radius: 3px;
            padding: 0.8rem 1rem;
            font-size: 0.95rem; color: {BRAND['ink']};
            line-height: 1.55; margin: 0.45rem 1.6rem 0.35rem;
            max-width: 820px;
          }}
          .wb-bubble .from {{
            font-size: 0.7rem; color: {BRAND['cyan']};
            text-transform: uppercase; letter-spacing: 0.12em;
            font-weight: 600; margin-bottom: 0.45rem;
            display: flex; align-items: center; gap: 0.45rem;
          }}
          .wb-bubble .from::before {{
            content: ''; width: 6px; height: 6px;
            border-radius: 50%; background: {BRAND['cyan']};
          }}

          /* ===== Incident card ===== */
          .wb-incident {{
            border: 1px solid {BRAND['hair_2']};
            border-radius: 10px;
            padding: 0.95rem 1.15rem;
            background: rgba(255,255,255,0.02);
            max-width: 820px;
            margin: 0 1.6rem 0.45rem;
          }}
          .wb-incident.warn {{ border-color: {BRAND['amber_line']}; }}
          .wb-incident.risk {{ border-color: {BRAND['red_line']}; }}
          .wb-incident .top {{
            display: flex; justify-content: space-between;
            align-items: baseline; gap: 0.7rem;
          }}
          .wb-incident .sev {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            padding: 0.2rem 0.55rem; border-radius: 4px;
            font-size: 0.72rem; letter-spacing: 0.08em;
            font-weight: 700;
          }}
          .wb-incident .sev.s5, .wb-incident .sev.s4 {{
            color: {BRAND['red']}; border: 1px solid {BRAND['red_line']};
          }}
          .wb-incident .sev.s3 {{
            color: {BRAND['amber']}; border: 1px solid {BRAND['amber_line']};
          }}
          .wb-incident .sev.s2 {{
            color: {BRAND['cyan']}; border: 1px solid {BRAND['cyan_line']};
          }}
          .wb-incident .sev.s1 {{
            color: {BRAND['ink_4']}; border: 1px solid {BRAND['hair_2']};
          }}
          .wb-incident .type {{
            margin-left: 0.55rem;
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            color: {BRAND['ink_2']}; font-size: 0.85rem;
          }}
          .wb-incident .route {{
            color: {BRAND['ink_3']}; font-size: 0.74rem;
            text-transform: uppercase; letter-spacing: 0.1em;
            font-weight: 600;
          }}
          .wb-incident .site {{
            color: {BRAND['ink_2']}; font-size: 0.92rem;
            margin-top: 0.5rem;
          }}
          .wb-incident .action {{
            color: {BRAND['ink']}; font-size: 0.9rem;
            margin-top: 0.55rem; line-height: 1.55;
          }}

          /* ===== Work order ===== */
          .wb-order {{
            border: 1px solid {BRAND['hair_2']};
            border-left: 2px solid {BRAND['cyan']};
            border-radius: 8px;
            padding: 0.9rem 1.1rem;
            background: rgba(255,255,255,0.02);
            max-width: 820px;
            margin: 0 1.6rem 0.45rem;
          }}
          .wb-order .l {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            color: {BRAND['cyan']}; font-size: 0.72rem;
            text-transform: uppercase; letter-spacing: 0.12em;
            font-weight: 600;
          }}
          .wb-order .site {{
            font-size: 1.05rem; font-weight: 600;
            margin-top: 0.2rem; color: {BRAND['ink']};
            letter-spacing: -0.015em;
          }}
          .wb-order .meta {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.82rem; color: {BRAND['ink_3']};
            margin-top: 0.45rem;
          }}
          .wb-order .meta b {{ color: {BRAND['ink_2']}; font-weight: 500; }}

          /* ===== Candidate row ===== */
          .wb-cand {{
            display: grid;
            grid-template-columns: 64px 1fr 80px;
            gap: 1rem;
            padding: 0.85rem 0.95rem;
            border-bottom: 1px solid {BRAND['hair']};
            align-items: start;
            max-width: 820px;
            margin: 0 1.6rem;
          }}
          .wb-cand:last-child {{ border-bottom: none; }}
          .wb-cand.top {{ background: rgba(43,221,138,0.04); }}
          .wb-cand .score {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-feature-settings: 'tnum' 1;
            font-size: 1.4rem; font-weight: 600;
            color: {BRAND['ink']}; line-height: 1;
            letter-spacing: -0.02em;
            padding-top: 0.15rem;
          }}
          .wb-cand.top .score {{ color: {BRAND['green']}; }}
          .wb-cand .body .name {{
            font-weight: 600; font-size: 0.95rem;
            color: {BRAND['ink']};
          }}
          .wb-cand .body .meta {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.78rem; color: {BRAND['ink_3']};
            margin-top: 0.15rem;
          }}
          .wb-cand .body ul {{
            margin: 0.5rem 0 0; padding-left: 0;
            list-style: none;
            display: grid; gap: 0.2rem;
            font-size: 0.83rem; color: {BRAND['ink_2']};
          }}
          .wb-cand .body ul li {{
            line-height: 1.5;
            padding-left: 1rem;
            position: relative;
          }}
          .wb-cand .body ul li::before {{
            content: '';
            position: absolute;
            left: 0; top: 0.65em;
            width: 5px; height: 1px;
            background: {BRAND['ink_4']};
          }}
          .wb-cand.top .body ul li::before {{ background: {BRAND['green_line']}; }}
          .wb-cand .rank {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.7rem; color: {BRAND['ink_3']};
            text-transform: uppercase; letter-spacing: 0.1em;
            font-weight: 600; text-align: right;
            padding-top: 0.55rem;
          }}
          .wb-cand.top .rank {{ color: {BRAND['green']}; }}

          /* ===== Readiness group ===== */
          .wb-rg {{
            padding: 0.9rem 1.1rem;
            border: 1px solid {BRAND['hair']};
            border-radius: 8px;
            margin-bottom: 0.55rem;
            background: rgba(255,255,255,0.02);
          }}
          .wb-rg .title {{
            font-size: 0.78rem; font-weight: 600;
            color: {BRAND['ink']};
            margin-bottom: 0.5rem;
          }}
          .wb-rg ul {{
            margin: 0; padding-left: 1rem;
            font-size: 0.88rem; color: {BRAND['ink_2']};
          }}
          .wb-rg ul li {{ margin: 0.22rem 0; line-height: 1.55; }}

          /* ===== Banner ===== */
          .wb-banner {{
            padding: 0.7rem 1rem;
            border-radius: 6px;
            border-left: 2px solid {BRAND['hair_2']};
            background: rgba(255,255,255,0.025);
            color: {BRAND['ink_2']};
            font-size: 0.86rem; line-height: 1.5;
            max-width: 820px;
            margin: 0.5rem 1.6rem;
          }}
          .wb-banner.ok {{ border-left-color: {BRAND['green']}; }}
          .wb-banner.warn {{ border-left-color: {BRAND['amber']}; }}

          /* ===== Decision cards ===== */
          .wb-signal-row {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.7rem;
            padding: 0 1.6rem;
          }}
          /* ===== Severity panel (variation B) ===== */
          .wb-sev-panel {{
            margin: 0 1.6rem;
            display: grid;
            grid-template-columns: 110px 1fr;
            gap: 1.2rem;
            padding: 1.15rem 1.25rem;
            background: rgba(255,255,255,0.025);
            border: 1px solid {BRAND['hair_2']};
            border-radius: 10px;
          }}
          .wb-sev-block {{
            border-radius: 8px;
            padding: 0.75rem 0.8rem;
            text-align: center;
            align-self: start;
          }}
          .wb-sev-block.warn {{ background: rgba(240,184,69,0.08); border: 1px solid {BRAND['amber_line']}; }}
          .wb-sev-block.risk {{ background: rgba(240,102,126,0.08); border: 1px solid {BRAND['red_line']}; }}
          .wb-sev-block.cyan {{ background: {BRAND['cyan_soft']}; border: 1px solid {BRAND['cyan_line']}; }}
          .wb-sev-block.muted {{ background: rgba(255,255,255,0.025); border: 1px solid {BRAND['hair_2']}; }}
          .wb-sev-block .lbl {{
            color: {BRAND['ink_3']};
            font-size: 0.66rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 600;
          }}
          .wb-sev-block .num {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 1.85rem;
            font-weight: 700;
            line-height: 1;
            margin-top: 0.3rem;
            letter-spacing: -0.02em;
          }}
          .wb-sev-block.warn .num {{ color: {BRAND['amber']}; }}
          .wb-sev-block.risk .num {{ color: {BRAND['red']}; }}
          .wb-sev-block.cyan .num {{ color: {BRAND['cyan']}; }}
          .wb-sev-block.muted .num {{ color: {BRAND['ink_3']}; }}
          .wb-sev-block .of {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            color: {BRAND['ink_4']};
            font-size: 0.74rem;
            margin-top: 0.2rem;
          }}
          .wb-sev-body .top {{
            display: flex; gap: 0.6rem;
            align-items: baseline;
            flex-wrap: wrap;
          }}
          .wb-sev-body .type {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-weight: 600;
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            white-space: nowrap;
          }}
          .wb-sev-body .type.warn {{ color: {BRAND['amber']}; border: 1px solid {BRAND['amber_line']}; }}
          .wb-sev-body .type.risk {{ color: {BRAND['red']}; border: 1px solid {BRAND['red_line']}; }}
          .wb-sev-body .type.cyan {{ color: {BRAND['cyan']}; border: 1px solid {BRAND['cyan_line']}; }}
          .wb-sev-body .type.muted {{ color: {BRAND['ink_3']}; border: 1px solid {BRAND['hair_2']}; }}
          .wb-sev-body .site {{
            font-weight: 600;
            font-size: 0.98rem;
            color: {BRAND['ink']};
          }}
          .wb-sev-body .row {{
            display: grid;
            grid-template-columns: 100px 1fr;
            gap: 0.8rem;
            margin-top: 0.65rem;
            font-size: 0.88rem;
            align-items: baseline;
          }}
          .wb-sev-body .row .k {{
            color: {BRAND['ink_3']};
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 600;
            padding-top: 0.1rem;
          }}
          .wb-sev-body .row .v {{
            color: {BRAND['ink']};
            line-height: 1.55;
          }}
          .wb-sev-body .row .v .accent {{ color: {BRAND['cyan']}; }}
          .wb-sev-body .row .v .mono-tag {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.76rem;
            color: {BRAND['ink_3']};
            margin-left: 0.4rem;
          }}

          .wb-signal {{
            min-width: 0;
            border: 1px solid {BRAND['hair']};
            border-top: 2px solid {BRAND['hair_2']};
            border-radius: 8px;
            background: rgba(255,255,255,0.02);
            padding: 0.85rem 0.95rem;
          }}
          .wb-signal.ok {{ border-top-color: {BRAND['green']}; }}
          .wb-signal.warn {{ border-top-color: {BRAND['amber']}; }}
          .wb-signal.risk {{ border-top-color: {BRAND['red']}; }}
          .wb-signal.cyan {{ border-top-color: {BRAND['cyan']}; }}
          .wb-signal .label {{
            color: {BRAND['ink_3']};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 600;
          }}
          .wb-signal .value {{
            color: {BRAND['ink']};
            font-size: 1.05rem;
            font-weight: 600;
            margin-top: 0.4rem;
            line-height: 1.25;
            overflow-wrap: anywhere;
          }}
          .wb-signal.ok .value {{ color: {BRAND['green']}; }}
          .wb-signal.warn .value {{ color: {BRAND['amber']}; }}
          .wb-signal.risk .value {{ color: {BRAND['red']}; }}
          .wb-signal.cyan .value {{ color: {BRAND['cyan']}; }}
          .wb-signal .note {{
            color: {BRAND['ink_3']};
            font-size: 0.8rem;
            line-height: 1.45;
            margin-top: 0.35rem;
          }}

          /* ===== Decision packet ===== */
          .wb-packet {{
            margin: 0 1.6rem;
            border-top: 1px solid {BRAND['hair']};
          }}
          .wb-packet .row {{
            display: grid;
            grid-template-columns: 170px minmax(0, 1fr);
            gap: 1rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid {BRAND['hair']};
          }}
          .wb-packet .row:last-child {{ border-bottom: none; }}
          .wb-packet .label {{
            color: {BRAND['ink_3']};
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 0.75rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
          }}
          .wb-packet .value {{
            color: {BRAND['ink_2']};
            font-size: 0.88rem;
            line-height: 1.55;
            overflow-wrap: anywhere;
          }}
          .wb-packet .value ul {{
            margin: 0; padding-left: 1rem;
            font-size: 0.88rem; color: {BRAND['ink_2']};
          }}
          .wb-packet .value ul li {{
            margin: 0.1rem 0;
            line-height: 1.5;
            padding-left: 0.1rem;
          }}
          .wb-packet .value ul li::marker {{
            color: {BRAND['ink_4']};
            font-size: 0.85em;
          }}

          /* ===== Readiness grid ===== */
          .wb-readiness-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem 1rem;
            max-width: 980px;
            margin: 0 1.6rem;
          }}

          /* ===== Mobile ===== */
          @media (max-width: 760px) {{
            /* Sidebar overlays main content at mobile so the workbench is never
               clipped behind it. Streamlit slides the sidebar off-screen via
               transform when aria-expanded="false"; we just need position:fixed
               so the main content can take full viewport width. */
            [data-testid="stSidebar"] {{
              position: fixed !important;
              top: 0 !important;
              left: 0 !important;
              bottom: 0 !important;
              height: 100vh !important;
              width: 260px !important;
              min-width: 260px !important;
              max-width: 86vw !important;
              z-index: 1000 !important;
              border-right: 1px solid {BRAND['hair_2']};
            }}
            [data-testid="stSidebar"][aria-expanded="true"] {{
              box-shadow: 8px 0 32px rgba(0,0,0,0.55);
            }}
            /* Expand-sidebar pill is positioned in the base styles (so it's
               available on desktop too when the sidebar is collapsed). Mobile
               just inherits that styling. */
            /* Backdrop scrim — only when sidebar is open. Uses ::after on stApp
               so a tap outside dismisses the sidebar via the existing collapse
               button (Streamlit closes the sidebar on outside click already). */
            [data-testid="stApp"]:has([data-testid="stSidebar"][aria-expanded="true"])::after {{
              content: '';
              position: fixed; inset: 0;
              background: rgba(0,0,0,0.45);
              z-index: 998;
              pointer-events: none;
            }}
            /* Push the sticky workbench toolbar down so it clears the floating
               expand-sidebar button when the sidebar is closed. Allow the crumb
               to scroll horizontally instead of wrapping the timestamp. */
            .wb-toolbar {{
              padding: 0.65rem 1.1rem 0.65rem 3.1rem;
              gap: 0.6rem;
              flex-wrap: nowrap;
            }}
            .wb-crumb {{
              flex: 1 1 auto;
              min-width: 0;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }}
            .wb-status {{ flex-shrink: 0; }}
            .wb-head {{ padding: 1.1rem 1.1rem 0.3rem; }}
            .wb-head h1 {{ font-size: 1.3rem; }}
            .wb-kpi-row {{ padding: 0.9rem 1.1rem 1rem; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.9rem 1rem; }}
            .wb-kpi {{ padding: 0; min-width: 0; }}
            .wb-kpi + .wb-kpi {{ border-left: none; padding-top: 0; }}
            .wb-section {{ padding: 1.2rem 1.1rem 0; }}
            [data-testid="stExpander"] {{
              max-width: none;
              margin: 0.45rem 1.1rem !important;
            }}
            .wb-work {{ grid-template-columns: 1fr; }}
            .wb-work .step {{ padding: 0.85rem 0 0.9rem 0; border-right: none; border-bottom: 1px solid {BRAND['hair']}; }}
            .wb-work .step:not(:first-child) {{ padding-left: 0; }}
            .wb-work .step:last-child {{ border-bottom: none; }}

            /* Master run-records table → card stack at mobile */
            .wb-table-wrap {{ overflow: visible; }}
            .wb-table, .wb-table tbody {{ display: block; }}
            .wb-table colgroup {{ display: none; }}
            .wb-table thead {{ display: none; }}
            .wb-table tbody tr {{
              display: grid;
              grid-template-columns: minmax(0, 1fr) auto;
              column-gap: 0.85rem;
              row-gap: 0.35rem;
              padding: 0.85rem 0;
              border-bottom: 1px solid {BRAND['hair']};
              align-items: baseline;
            }}
            .wb-table tbody tr:last-child {{ border-bottom: none; }}
            .wb-table tbody tr.group-break {{
              padding: 0.55rem 0 0.3rem;
              display: block;
              border-bottom: 1px solid {BRAND['hair_2']};
            }}
            .wb-table tbody tr.group-break td {{
              display: block;
              padding: 0 0 0.05rem;
            }}
            .wb-table tbody td {{ display: block; padding: 0; border: 0; font-size: 0.86rem; }}
            .wb-table tbody td.id {{ grid-column: 1; }}
            .wb-table tbody td.tag {{ grid-column: 2; justify-self: end; }}
            .wb-table tbody td.cust {{ grid-column: 1 / -1; padding-top: 0.15rem; }}
            .wb-table tbody td.reason {{
              grid-column: 1 / -1;
              font-size: 0.82rem;
              color: {BRAND['ink_3']};
              line-height: 1.45;
            }}
            .wb-table tbody td.reason.empty {{ display: none; }}
            .wb-table tbody td.owner {{
              grid-column: 1;
              font-size: 0.78rem;
              color: {BRAND['ink_4']};
            }}
            .wb-table tbody td.owner:empty,
            .wb-table tbody td.owner:has(> :only-child:empty) {{ display: none; }}
            .wb-table tbody td.amt {{
              grid-column: 2;
              justify-self: end;
              font-size: 0.86rem;
            }}

            .wb-buckets {{
              grid-template-columns: 1fr;
              margin: 0 1.1rem 0.9rem;
              gap: 0.45rem;
            }}
            .wb-bucket {{ padding: 0.55rem 0.8rem; }}
            .wb-bucket .note {{ text-align: right; }}

            .wb-signal-row {{ grid-template-columns: 1fr; padding: 0 1.1rem; }}
            .wb-sev-panel {{ grid-template-columns: 1fr; margin: 0 1.1rem; gap: 0.85rem; }}
            .wb-sev-block {{ display: grid; grid-template-columns: auto 1fr auto; align-items: baseline; gap: 0.55rem; text-align: left; }}
            .wb-sev-block .num {{ margin-top: 0; }}
            .wb-packet {{ margin: 0 1.1rem; }}
            .wb-packet .row {{ grid-template-columns: 1fr; gap: 0.25rem; }}
            .wb-readiness-grid {{
              grid-template-columns: 1fr;
              max-width: none;
              margin: 0 1.1rem;
            }}
            .wb-bubble, .wb-incident, .wb-order, .wb-cand, .wb-banner {{
              max-width: none;
              margin-left: 1.1rem;
              margin-right: 1.1rem;
            }}
            .wb-files .row {{
              grid-template-columns: 110px 1fr;
              row-gap: 0.2rem;
            }}
            .wb-files .row .sz {{ grid-column: 2; text-align: left; }}
            .wb-footnote {{
              margin: 1.6rem 1.1rem 2rem;
            }}
          }}

          @media (max-width: 480px) {{
            [data-testid="stSidebar"] {{ width: 240px !important; min-width: 240px !important; max-width: 86vw !important; }}
            .wb-toolbar {{ padding: 0.7rem 0.9rem 0.7rem 3rem; }}
            .wb-head {{ padding: 1rem 0.9rem 0.25rem; }}
            .wb-head h1 {{ font-size: 1.22rem; }}
            .wb-kpi-row {{ padding: 0.8rem 0.9rem 0.95rem; gap: 0.75rem 0.85rem; }}
            .wb-section {{ padding: 1.05rem 0.9rem 0; }}
            .wb-buckets {{ margin: 0 0.9rem 0.85rem; }}
            .wb-packet, .wb-readiness-grid,
            .wb-bubble, .wb-incident, .wb-order, .wb-cand, .wb-banner {{
              margin-left: 0.9rem;
              margin-right: 0.9rem;
            }}
            [data-testid="stExpander"] {{ margin: 0.45rem 0.9rem !important; }}
            .wb-signal-row {{ padding: 0 0.9rem; }}
            .wb-sev-panel {{ margin: 0 0.9rem; }}
            .wb-footnote {{ margin: 1.4rem 0.9rem 1.8rem; }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(
        f'<div class="sb-brand">'
        f'<img class="sb-logo" src="{_wordmark_data_uri()}" '
        f'alt="Aventyr Security Corp." />'
        f'</div>',
        unsafe_allow_html=True,
    )


def sidebar_section(label: str) -> None:
    st.sidebar.markdown(
        f'<div class="sb-section">{_safe(label)}</div>',
        unsafe_allow_html=True,
    )


def sidebar_foot(html: str) -> None:
    st.sidebar.markdown(f'<div class="sb-foot">{html}</div>', unsafe_allow_html=True)


def wb_toolbar(crumb_html: str, status_text: str) -> None:
    st.markdown(
        f'<div class="wb-toolbar">'
        f'<div class="wb-crumb">{crumb_html}</div>'
        f'<div class="wb-actions">'
        f'<span class="wb-status"><span class="dot"></span>{_safe(status_text)}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def wb_head(deck: str, title: str, body: str) -> None:
    st.markdown(
        f'<div class="wb-head">'
        f'<div class="deck">{deck}</div>'
        f'<h1>{_safe(title)}</h1>'
        f'<p>{_safe(body)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_kpi_row(items: list[tuple[str, str, str | None, str]]) -> None:
    """items: (label, value, sub, kind) — kind in {ok, warn, cyan, ""}"""
    cells = []
    for label, value, sub, kind in items:
        sub_html = f'<div class="s">{_safe(sub)}</div>' if sub else ""
        cells.append(
            f'<div class="wb-kpi {_safe_class(kind)}">'
            f'<div class="l">{_safe(label)}</div>'
            f'<div class="v">{_safe(value)}</div>'
            f'{sub_html}</div>'
        )
    st.markdown(f'<div class="wb-kpi-row">{"".join(cells)}</div>', unsafe_allow_html=True)


def wb_section(title: str, meta: str | None = None) -> None:
    meta_html = f'<span class="meta">{_safe(meta)}</span>' if meta else ""
    st.markdown(
        f'<div class="wb-section"><div class="wb-section-head">'
        f'<h2>{_safe(title)}</h2>{meta_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def wb_master_table(rows: list[dict]) -> None:
    """Render the master run-records table.

    Each row: {id, status_kind, status_label, customer, site, reason, owner, amount, amount_state}.
    A row with {"group_break": True, "label": "..."} renders a thin section header inside tbody
    that groups subsequent rows (e.g., BILLABLE → HELD → SKIPPED).
    """
    body_rows = []
    for r in rows:
        if r.get("group_break"):
            body_rows.append(
                f'<tr class="group-break"><td colspan="6">{_safe(r["label"])}</td></tr>'
            )
            continue
        kind = _safe_class(r.get("status_kind", ""))
        amt_cls = "amt"
        if r.get("amount_state") == "muted":
            amt_cls = "amt muted"
        elif r.get("amount_state") == "hold":
            amt_cls = "amt hold"
        reason_raw = r.get("reason")
        reason_cls = "reason empty" if not reason_raw else "reason"
        reason_display = reason_raw or "—"
        site_html = (
            f'<div class="site">{_safe(r["site"])}</div>' if r.get("site") else ""
        )
        body_rows.append(
            f'<tr>'
            f'<td class="id">{_safe(r["id"])}</td>'
            f'<td class="tag"><span class="row-tag {kind}">{_safe(r["status_label"])}</span></td>'
            f'<td class="cust">'
            f'<div class="name">{_safe(r["customer"])}</div>'
            f'{site_html}'
            f'</td>'
            f'<td class="{reason_cls}">{_safe(reason_display)}</td>'
            f'<td class="owner">{_safe(r.get("owner") or "—")}</td>'
            f'<td class="{amt_cls}">{_safe(r.get("amount", ""))}</td>'
            f'</tr>'
        )
    st.markdown(
        f'<div class="wb-section" style="padding-top:0">'
        f'<div class="wb-table-wrap">'
        f'<table class="wb-table">'
        f'<colgroup>'
        f'<col class="col-id"><col class="col-status"><col class="col-cust">'
        f'<col class="col-reason"><col class="col-owner"><col class="col-amt">'
        f'</colgroup>'
        f'<thead><tr>'
        f'<th>Event</th><th>Status</th><th>Customer</th>'
        f'<th>Hold reason</th><th>Routed to</th><th class="right">Amount</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        f'</table></div></div>',
        unsafe_allow_html=True,
    )


def wb_work_strip(steps: list[tuple[str, str, str]]) -> None:
    """steps: list of (num, title, desc)"""
    cells = []
    for num, title, desc in steps:
        cells.append(
            f'<div class="step">'
            f'<div class="n">{_safe(num)}</div>'
            f'<div class="t">{_safe(title)}</div>'
            f'<div class="d">{_safe(desc)}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div class="wb-section" style="padding-top:0">'
        f'<div class="wb-work">{"".join(cells)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_files_panel(items: list[tuple[str, str, str]]) -> None:
    """items: list of (label, path, size)"""
    rows = []
    for label, path, size in items:
        rows.append(
            f'<div class="row">'
            f'<span class="label">{_safe(label)}</span>'
            f'<span class="path">{_safe(path)}</span>'
            f'<span class="sz">{_safe(size)}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="wb-section" style="padding-top:0">'
        f'<div class="wb-files">{"".join(rows)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_footnote(text: str, lead: str = "Demo boundary.") -> None:
    st.markdown(
        f'<div class="wb-footnote"><b>{_safe(lead)}</b> {_safe(text)}</div>',
        unsafe_allow_html=True,
    )


def wb_banner(text: str, kind: str = "") -> None:
    cls = f"wb-banner {_safe_class(kind)}".strip()
    st.markdown(f'<div class="{cls}">{_safe(text)}</div>', unsafe_allow_html=True)


def _severity_kind(severity: int) -> str:
    """Map severity 1-5 to a visual kind for the severity panel."""
    if severity >= 4:
        return "risk"
    if severity == 3:
        return "warn"
    if severity == 2:
        return "cyan"
    return "muted"


def wb_severity_panel(
    severity: int,
    incident_type: str,
    site: str,
    rows: list[tuple[str, str]],
    of_max: int = 5,
) -> None:
    """Render the severity-led incident panel (variation B)."""
    kind = _severity_kind(severity)
    row_html = "".join(
        f'<div class="row">'
        f'<span class="k">{_safe(label)}</span>'
        f'<span class="v">{_safe(value)}</span>'
        f'</div>'
        for label, value in rows
    )
    st.markdown(
        f'<div class="wb-sev-panel">'
        f'<div class="wb-sev-block {kind}">'
        f'<div class="lbl">Severity</div>'
        f'<div class="num">{int(severity)}</div>'
        f'<div class="of">of {int(of_max)}</div>'
        f'</div>'
        f'<div class="wb-sev-body">'
        f'<div class="top">'
        f'<span class="type {kind}">{_safe(incident_type.replace("_", " ").upper())}</span>'
        f'<span class="site">{_safe(site)}</span>'
        f'</div>'
        f'{row_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_signal_cards(items: list[tuple[str, str, str, str]]) -> None:
    cards = []
    for label, value, note, kind in items:
        cards.append(
            f'<div class="wb-signal {_safe_class(kind)}">'
            f'<div class="label">{_safe(label)}</div>'
            f'<div class="value">{_safe(value)}</div>'
            f'<div class="note">{_safe(note)}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="wb-signal-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def wb_packet(rows: list[tuple[str, str | list[str]]]) -> None:
    body = []
    for label, value in rows:
        if isinstance(value, (list, tuple)):
            items = "".join(f"<li>{_safe(item)}</li>" for item in value)
            value_html = f"<ul>{items}</ul>"
        else:
            value_html = _safe(value)
        body.append(
            f'<div class="row">'
            f'<div class="label">{_safe(label)}</div>'
            f'<div class="value">{value_html}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="wb-packet">{"".join(body)}</div>', unsafe_allow_html=True)


def wb_buckets(buckets: list[tuple[str, str | int, str, str]]) -> None:
    """buckets: list of (label, count, note, kind) where kind in {ok, warn, skip}."""
    cells = []
    for label, count, note, kind in buckets:
        cells.append(
            f'<div class="wb-bucket {_safe_class(kind)}">'
            f'<span class="num">{_safe(count)}</span>'
            f'<span class="lbl">{_safe(label)}</span>'
            f'<span class="note">{_safe(note)}</span>'
            f'</div>'
        )
    st.markdown(f'<div class="wb-buckets">{"".join(cells)}</div>', unsafe_allow_html=True)


def wb_inbound_bubble(from_label: str, message: str) -> None:
    st.markdown(
        f'<div class="wb-bubble">'
        f'<div class="from">{_safe(from_label)}</div>'
        f'{_safe(message)}</div>',
        unsafe_allow_html=True,
    )


def wb_incident_card(classification) -> None:
    sev = classification.severity
    cls = "wb-incident risk" if sev >= 4 else ("wb-incident warn" if sev == 3 else "wb-incident")
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="top">'
        f'<div><span class="sev s{sev}">SEV {sev}</span>'
        f'<span class="type">{_safe(classification.incident_type.replace("_", " ").upper())}</span></div>'
        f'<span class="route">{_safe(classification.route)}</span>'
        f'</div>'
        f'<div class="site">{_safe(classification.site_name)}</div>'
        f'<div class="action">{_safe(classification.action_required)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_work_order(shift) -> None:
    st.markdown(
        f'<div class="wb-order">'
        f'<div class="l">Open work order · {_safe(shift.shift_id)}</div>'
        f'<div class="site">{_safe(shift.site_name)}</div>'
        f'<div class="meta">{_safe(shift.date)} · <b>{_safe(shift.start_time)}–{_safe(shift.end_time)}</b> · '
        f'cert <b>{_safe(shift.required_certification)}</b> · {_safe(shift.priority.upper())} priority</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_candidate_row(rank: int, candidate, is_top: bool = False) -> None:
    rationale = "".join(f"<li>{_safe(r)}</li>" for r in candidate.rationale)
    label = "Top" if is_top else f"#{rank}"
    cls = "wb-cand top" if is_top else "wb-cand"
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="score">{candidate.score}</div>'
        f'<div class="body">'
        f'<div class="name">{_safe(candidate.guard_name)}</div>'
        f'<div class="meta">${candidate.hourly_rate:.2f}/hr · {_safe(candidate.guard_id)}</div>'
        f'<ul>{rationale}</ul>'
        f'</div>'
        f'<div class="rank">{_safe(label)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def wb_readiness_group(title: str, items: list[str]) -> None:
    body = "".join(f"<li>{_safe(item)}</li>" for item in items)
    st.markdown(
        f'<div class="wb-rg">'
        f'<div class="title">{_safe(title)}</div>'
        f'<ul>{body}</ul></div>',
        unsafe_allow_html=True,
    )


def wb_readiness_grid(groups: list[tuple[str, list[str]]]) -> None:
    cards = []
    for title, items in groups:
        body = "".join(f"<li>{_safe(item)}</li>" for item in items)
        cards.append(
            f'<div class="wb-rg">'
            f'<div class="title">{_safe(title)}</div>'
            f'<ul>{body}</ul></div>'
        )
    st.markdown(f'<div class="wb-readiness-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def records_table(records: Iterable[BaseModel | dict]) -> pd.DataFrame:
    rows = []
    for record in records:
        row = record.model_dump() if isinstance(record, BaseModel) else record
        rows.append({humanize_key(key): _format_value(value) for key, value in row.items()})
    return pd.DataFrame(rows)


def trace_table(trace: Iterable[BaseModel]) -> pd.DataFrame:
    return records_table(trace)


def humanize_key(key: str) -> str:
    """Convert snake_case identifiers into human-readable column labels.

    Pydantic models and dict keys we ship around in code (event_id, signal_type,
    operator_verified, …) need to read as natural language when they surface in
    dataframes the operator scans. ID-style suffixes stay uppercase so the
    column header still signals "this is an identifier".
    """
    if not key:
        return key
    parts = key.split("_")
    out = []
    for i, part in enumerate(parts):
        upper = part.upper()
        if upper in {"ID", "AR", "OK", "URL", "CSV", "MTD", "KPH"}:
            out.append(upper)
        elif i == 0:
            out.append(part.capitalize())
        else:
            out.append(part)
    return " ".join(out)


_SNAKE_VALUE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")


def _humanize_value(value):
    """Drop the underscore on snake_case enum values (signal_type, incident_type, …).

    Leaves IDs, paths, refs, and anything that isn't pure-lowercase snake_case
    untouched. The captured pattern is `letter(_letter…)+`, so "EVT-1001",
    "SITE-BRAVO/A", and "user@x.com" all stay as-is.
    """
    if isinstance(value, str) and _SNAKE_VALUE_RE.match(value):
        return value.replace("_", " ").capitalize()
    return value


def _format_value(value):
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return _humanize_value(value)


def _safe(value: object) -> str:
    return escape(str(value), quote=True)


def _safe_class(value: object) -> str:
    allowed = {"ok", "warn", "risk", "cyan", "skip", "green", "amber", ""}
    raw = str(value)
    return raw if raw in allowed else ""
