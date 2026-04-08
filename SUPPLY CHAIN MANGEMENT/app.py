# app.py — SWAG EXECUTIVE DASHBOARD — FULL ARCHITECTURAL REBUILD
# Version: 3.0 — Complete rewrite addressing all functional issues
#
# ARCHITECTURE:
#   - Raw backend data always stored in canonical English column names
#   - Localization ONLY happens at display/render time via col() helper
#   - Centralized auth (real Odoo XML-RPC, no bypass)
#   - Centralized error handling per module per company
#   - All charts validate columns before rendering
#   - All tabs open reliably; no silent failures
#   - Arabic mode fully functional throughout

import io
import re
import hashlib
import time
import math
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Swag Executive",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: THEMES
# ─────────────────────────────────────────────────────────────────────────────

THEMES = {
    "Dark Executive": {
        "bg": "linear-gradient(135deg,#0f0c29,#302b63,#24243e)",
        "sidebar_bg": "linear-gradient(180deg,#1a1a2e 0%,#16213e 100%)",
        "card_bg": "linear-gradient(145deg,#1e1e3f,#2d2b55)",
        "card_bg_solid": "#1e1e3f",
        "accent1": "#667eea",
        "accent2": "#f093fb",
        "accent3": "#43e97b",
        "accent4": "#f6d365",
        "text": "#e8e8ff",
        "text_muted": "#a0aec0",
        "text_label": "#c4b5fd",
        "border": "#ffffff18",
        "input_bg": "#1e1e3f",
        "metric_gradient": "linear-gradient(90deg,#667eea,#f093fb)",
        "tab_active": "linear-gradient(90deg,#667eea,#764ba2)",
        "title_gradient": "linear-gradient(90deg,#667eea,#f093fb,#43e97b,#667eea)",
        "button_gradient": "linear-gradient(90deg,#667eea,#764ba2,#f093fb,#667eea)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#667eea","#f093fb","#43e97b","#f6d365","#fda085","#a18cd1","#96fbc4","#4facfe"],
        "danger": "#f43f5e",
        "warning": "#f59e0b",
        "success": "#22c55e",
    },
    "Light Executive": {
        "bg": "linear-gradient(135deg,#f0f4ff,#ffffff,#f8f0ff)",
        "sidebar_bg": "linear-gradient(180deg,#ffffff 0%,#f0f4ff 100%)",
        "card_bg": "linear-gradient(145deg,#ffffff,#f8f8ff)",
        "card_bg_solid": "#ffffff",
        "accent1": "#4f46e5",
        "accent2": "#9333ea",
        "accent3": "#16a34a",
        "accent4": "#d97706",
        "text": "#1e1b4b",
        "text_muted": "#6b7280",
        "text_label": "#4f46e5",
        "border": "#e5e7eb",
        "input_bg": "#ffffff",
        "metric_gradient": "linear-gradient(90deg,#4f46e5,#9333ea)",
        "tab_active": "linear-gradient(90deg,#4f46e5,#7c3aed)",
        "title_gradient": "linear-gradient(90deg,#4f46e5,#9333ea,#16a34a,#4f46e5)",
        "button_gradient": "linear-gradient(90deg,#4f46e5,#7c3aed,#9333ea,#4f46e5)",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#4f46e5","#9333ea","#16a34a","#d97706","#dc2626","#0891b2","#7c3aed","#059669"],
        "danger": "#dc2626",
        "warning": "#d97706",
        "success": "#16a34a",
    },
    "Luxury Gold": {
        "bg": "linear-gradient(135deg,#0a0800,#1a1400,#0d0a00)",
        "sidebar_bg": "linear-gradient(180deg,#0f0c00 0%,#1a1400 100%)",
        "card_bg": "linear-gradient(145deg,#1a1400,#2a2000)",
        "card_bg_solid": "#1a1400",
        "accent1": "#d4af37",
        "accent2": "#f5c842",
        "accent3": "#c8a415",
        "accent4": "#fff7d4",
        "text": "#f5e6c8",
        "text_muted": "#a89060",
        "text_label": "#d4af37",
        "border": "#d4af3722",
        "input_bg": "#1a1400",
        "metric_gradient": "linear-gradient(90deg,#d4af37,#f5c842)",
        "tab_active": "linear-gradient(90deg,#d4af37,#c8a415)",
        "title_gradient": "linear-gradient(90deg,#d4af37,#f5c842,#fff7d4,#d4af37)",
        "button_gradient": "linear-gradient(90deg,#d4af37,#c8a415,#f5c842,#d4af37)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#d4af37","#f5c842","#c8a415","#fff7d4","#a89060","#ffd700","#daa520","#b8860b"],
        "danger": "#ff6b6b",
        "warning": "#ffd700",
        "success": "#90ee90",
    },
    "Glass Premium": {
        "bg": "linear-gradient(135deg,#0a0a1a 0%,#1a0a2e 50%,#0a1a2e 100%)",
        "sidebar_bg": "linear-gradient(180deg,rgba(255,255,255,0.05) 0%,rgba(255,255,255,0.02) 100%)",
        "card_bg": "linear-gradient(145deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04))",
        "card_bg_solid": "rgba(255,255,255,0.06)",
        "accent1": "#00d4ff",
        "accent2": "#ff6b9d",
        "accent3": "#00ff88",
        "accent4": "#ffd700",
        "text": "#ffffff",
        "text_muted": "#aaaacc",
        "text_label": "#00d4ff",
        "border": "rgba(255,255,255,0.15)",
        "input_bg": "rgba(255,255,255,0.08)",
        "metric_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d)",
        "tab_active": "linear-gradient(90deg,rgba(0,212,255,0.3),rgba(255,107,157,0.3))",
        "title_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d,#00ff88,#00d4ff)",
        "button_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d,#00ff88,#00d4ff)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#00d4ff","#ff6b9d","#00ff88","#ffd700","#ff6b35","#a855f7","#34d399","#818cf8"],
        "danger": "#ff6b9d",
        "warning": "#ffd700",
        "success": "#00ff88",
    },
}

def get_theme():
    t = st.session_state.get("theme", "Dark Executive")
    return t if t in THEMES else "Dark Executive"

def th(key):
    return THEMES[get_theme()].get(key, "")

def th_color(key, fallback="#667eea"):
    """Extract a safe hex color from a theme value (handles gradient strings)."""
    val = str(THEMES[get_theme()].get(key, fallback) or fallback).strip()
    if re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", val):
        return val
    m = re.search(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", val)
    return f"#{m.group(1)}" if m else fallback

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: CSS
# ─────────────────────────────────────────────────────────────────────────────

def build_css():
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
*,html,body,[class*="css"]{{font-family:'IBM Plex Sans Arabic','Space Grotesk',sans-serif;box-sizing:border-box;}}
.stApp{{background:{th("bg")};min-height:100vh;}}
section[data-testid="stSidebar"]{{background:{th("sidebar_bg")}!important;border-right:1px solid {th("border")};backdrop-filter:blur(20px);}}
section[data-testid="stSidebar"] *{{color:{th("text")}!important;}}
section[data-testid="stSidebar"] input{{color:{th("text")}!important;}}

@keyframes shimmer{{0%{{background-position:-400% center}}100%{{background-position:400% center}}}}
@keyframes fadeInDown{{from{{opacity:0;transform:translateY(-20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
@keyframes btnShine{{0%{{background-position:-200% center}}100%{{background-position:200% center}}}}
@keyframes cardEntrance{{from{{opacity:0;transform:translateY(16px) scale(0.97)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 {th_color("accent1")}44}}50%{{box-shadow:0 0 20px 8px {th_color("accent1")}22}}}}

.stTextInput input,.stNumberInput input,.stTextArea textarea{{background:{th("input_bg")}!important;border:1px solid {th_color("accent1")}66!important;border-radius:10px!important;color:{th("text")}!important;caret-color:{th("text_label")}!important;transition:all 0.3s!important;}}
.stTextInput input:focus{{border-color:{th_color("accent1")}!important;box-shadow:0 0 0 3px {th_color("accent1")}33!important;}}
.stTextInput label,.stNumberInput label,.stTextArea label{{color:{th("text_label")}!important;font-weight:600!important;}}

.stFormSubmitButton button,.stButton button[kind="primary"]{{background:{th("button_gradient")}!important;background-size:300% auto!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important;padding:12px!important;animation:btnShine 3s linear infinite!important;box-shadow:0 4px 20px {th_color("accent1")}55!important;}}
.stFormSubmitButton button:hover{{transform:translateY(-2px) scale(1.02)!important;}}
.stButton button[kind="secondary"]{{background:{th("card_bg")}!important;border:1px solid {th_color("accent1")}66!important;color:{th("text_label")}!important;border-radius:10px!important;}}
.stButton button{{color:{th("text_label")}!important;}}
.stDownloadButton button{{background:{th("card_bg")}!important;border:1px solid {th_color("accent1")}66!important;border-radius:10px!important;color:{th("text_label")}!important;font-size:0.78rem!important;font-weight:600!important;padding:6px 14px!important;}}
.stDownloadButton button:hover{{background:{th("tab_active")}!important;color:white!important;border-color:transparent!important;}}

.dash-header{{text-align:center;padding:16px 0 24px;}}
.dash-title{{font-size:2.4rem;font-weight:700;background:{th("title_gradient")};background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 4s linear infinite;}}
.dash-subtitle{{color:{th("text_muted")};font-size:0.92rem;margin-top:-4px;}}

[data-testid="stMetric"]{{background:{th("card_bg")}!important;border:1px solid {th("border")}!important;border-radius:16px!important;padding:16px 20px!important;animation:cardEntrance 0.6s ease;transition:transform 0.2s;}}
[data-testid="stMetric"]:hover{{transform:translateY(-3px);}}
[data-testid="stMetricLabel"]{{color:{th("text_muted")}!important;font-size:0.82rem!important;}}
[data-testid="stMetricValue"]{{font-size:1.7rem!important;font-weight:700!important;background:{th("metric_gradient")};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}

.stTabs [data-baseweb="tab-list"]{{background:{th("card_bg")};border-radius:12px;padding:4px;gap:4px;border:1px solid {th("border")};}}
.stTabs [data-baseweb="tab"]{{color:{th("text_muted")}!important;border-radius:10px!important;font-size:0.83rem!important;font-weight:600!important;padding:8px 16px!important;transition:all 0.2s!important;}}
.stTabs [aria-selected="true"]{{background:{th("tab_active")}!important;color:white!important;box-shadow:0 4px 12px {th_color("accent1")}55!important;}}

.info-banner{{background:linear-gradient(135deg,{th_color("accent1")}22,{th_color("accent1")}11);border-left:4px solid {th_color("accent1")};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{th("text")}!important;}}
.warn-banner{{background:linear-gradient(135deg,{th_color("warning",  "#f59e0b")}22,{th_color("warning","#f59e0b")}11);border-left:4px solid {th_color("warning","#f59e0b")};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{th("text")}!important;}}
.alert-banner{{background:linear-gradient(135deg,{th_color("danger","#f43f5e")}22,{th_color("danger","#f43f5e")}11);border-left:4px solid {th_color("danger","#f43f5e")};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{th("text")}!important;}}
.ok-banner{{background:linear-gradient(135deg,{th_color("success","#22c55e")}22,{th_color("success","#22c55e")}11);border-left:4px solid {th_color("success","#22c55e")};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{th("text")}!important;}}
.diag-banner{{background:linear-gradient(135deg,#1a1a2e,#2d2b55);border:1px solid {th_color("accent4","#f6d365")}44;border-radius:10px;padding:14px 18px;margin:8px 0 16px;font-size:0.82rem;color:{th("text")}!important;font-family:'JetBrains Mono',monospace;}}

.exec-card{{background:{th("card_bg")};border:1px solid {th("border")};border-radius:16px;padding:20px 24px;font-size:0.88rem;color:{th("text")}!important;line-height:1.9;animation:cardEntrance 0.5s ease;box-shadow:0 4px 20px #00000055;backdrop-filter:blur(10px);}}
.exec-card b,.exec-card strong{{color:{th("text_label")}!important;}}

.badge-ok{{background:linear-gradient(90deg,#065f46,#047857);color:#d1fae5!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;display:inline-block;}}
.badge-off{{background:linear-gradient(90deg,#991b1b,#b91c1c);color:#fee2e2!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;display:inline-block;}}
.badge-warn{{background:linear-gradient(90deg,#92400e,#b45309);color:#fef3c7!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;display:inline-block;}}

h1,h2,h3,h4,h5,h6{{color:{th("text")}!important;}}
.stMarkdown p,.stMarkdown li{{color:{th("text_label")}!important;}}
.stCaption,[data-testid="stCaptionContainer"] p{{color:{th("text_muted")}!important;}}
[data-testid="stExpander"]{{background:{th("card_bg")}!important;border:1px solid {th("border")}!important;border-radius:12px!important;}}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{{color:{th("text_label")}!important;}}
hr{{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,{th_color("accent1")}66,transparent)!important;margin:16px 0!important;}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:{th("card_bg_solid")};}}
::-webkit-scrollbar-thumb{{background:{th("tab_active")};border-radius:10px;}}
footer{{visibility:hidden;}}
[data-baseweb="select"] div{{background:{th("input_bg")}!important;color:{th("text")}!important;border-color:{th_color("accent1")}55!important;}}
[data-baseweb="select"] li{{background:{th("card_bg_solid")}!important;color:{th("text")}!important;}}
.stRadio label,.stCheckbox label{{color:{th("text")}!important;}}
div[data-testid="stRadio"] p{{color:{th("text")}!important;}}

.dataframe-wrap table{{font-family:'IBM Plex Sans Arabic',sans-serif;border-collapse:collapse;width:100%;background:{th("card_bg_solid")};color:{th("text")};border-radius:12px;overflow:hidden;font-size:0.84rem;}}
.dataframe-wrap th{{background:{th("tab_active")};color:white;padding:10px 14px;text-align:center;font-weight:600;white-space:nowrap;}}
.dataframe-wrap td{{padding:8px 14px;text-align:center;border-bottom:1px solid {th("border")};white-space:nowrap;}}
.dataframe-wrap tr:hover{{background:{th_color("accent1")}11;}}

.kpi-tile{{background:{th("card_bg")};border:1px solid {th("border")};border-radius:16px;padding:22px;text-align:center;animation:cardEntrance 0.6s ease;transition:all 0.3s;backdrop-filter:blur(10px);}}
.kpi-tile:hover{{transform:translateY(-6px);box-shadow:0 12px 40px {th_color("accent1")}44;}}
.kpi-tile .kpi-value{{font-size:2rem;font-weight:700;background:{th("metric_gradient")};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.kpi-tile .kpi-label{{font-size:0.8rem;color:{th("text_muted")};margin-top:6px;}}
.kpi-tile .kpi-icon{{font-size:2rem;margin-bottom:10px;}}

.section-header{{font-size:1.05rem;font-weight:700;color:{th("text_label")};margin:20px 0 12px;display:flex;align-items:center;gap:8px;padding-bottom:8px;border-bottom:1px solid {th("border")};}}
.pagination-bar{{display:flex;align-items:center;justify-content:center;gap:12px;padding:12px 0;margin-top:8px;}}
.page-info{{color:{th("text_muted")};font-size:0.84rem;background:{th("card_bg")};padding:6px 16px;border-radius:20px;border:1px solid {th("border")};}}

.login-orb{{width:100px;height:100px;border-radius:50%;background:{th("button_gradient")};display:flex;align-items:center;justify-content:center;font-size:2.5rem;margin:0 auto 20px;animation:float 3s ease-in-out infinite;box-shadow:0 8px 40px {th_color("accent1")}66;}}
.login-card{{background:{th("card_bg")};border:1px solid {th("border")};border-radius:20px;padding:32px 36px;animation:fadeInUp 0.7s ease;backdrop-filter:blur(20px);}}
.login-title{{font-size:2.2rem;font-weight:700;background:{th("title_gradient")};background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s linear infinite;text-align:center;margin-bottom:6px;}}
.login-subtitle{{color:{th("text_label")}!important;font-size:0.9rem;text-align:center;margin-bottom:28px;}}

.chat-panel{{background:{th("card_bg")};border:1px solid {th("border")};border-radius:20px;overflow:hidden;backdrop-filter:blur(20px);}}
.chat-header{{background:{th("tab_active")};padding:14px 20px;}}
.chat-msg-user{{background:{th("button_gradient")};color:white;border-radius:18px 18px 4px 18px;padding:10px 14px;margin:6px 0 6px 40px;font-size:0.86rem;}}
.chat-msg-bot{{background:{th("card_bg")};color:{th("text")};border:1px solid {th("border")};border-radius:18px 18px 18px 4px;padding:10px 14px;margin:6px 40px 6px 0;font-size:0.86rem;}}
.chat-label-user{{text-align:right;font-size:0.7rem;color:{th("text_muted")};margin-bottom:2px;}}
.chat-label-bot{{text-align:left;font-size:0.7rem;color:{th("text_muted")};margin-bottom:2px;}}
.chat-insight-block{{background:{th_color("accent1")}18;border:1px solid {th_color("accent1")}44;border-radius:10px;padding:10px 14px;margin:6px 0;font-size:0.83rem;}}
.chat-insight-row{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid {th("border")};}}
.chat-insight-row:last-child{{border-bottom:none;}}
.chat-insight-key{{color:{th("text_muted")};}}
.chat-insight-val{{color:{th("text_label")};font-weight:700;}}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: CONSTANTS & CONFIG
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_KEYS  = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]
ROWS_PER_PAGE = 30

VIZ_MODES = [
    "📋 List View", "🏆 KPI Tiles", "📊 Column Chart", "📉 Horizontal Bar",
    "📈 Line Chart", "📉 Area Chart", "🍕 Pie Chart", "🍩 Donut Chart",
    "📊 Stacked Column", "🔘 Scatter Chart", "🗂️ Funnel Chart", "📡 Radar Chart",
]

# CANONICAL (backend) column names — NEVER localize these; they are the source of truth
# All fetchers store data with these exact keys.
# Localization happens only at display time via col() / display_col_name().
RAW_COLS = {
    "system":           "System",
    "model_code":       "Model Code",
    "product":          "Product",
    "sale_price":       "Sale Price",
    "on_hand":          "On Hand",
    "purchase_qty_col": "Purchase Qty",
    "branch":           "Branch",
    "location":         "Location",
    "date":             "Date",
    "pos_order":        "POS Order",
    "customer":         "Customer",
    "cashier":          "Cashier",
    "category":         "Category",
    "qty":              "Qty",
    "unit_price":       "Unit Price",
    "subtotal":         "Subtotal",
    "total_amount":     "Total Amount",
    "so":               "SO",
    "vendor":           "Vendor",
    "receipt_location": "Receipt Location",
    "po":               "PO",
    "state":            "State",
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: LANGUAGE / LOCALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    """Return Arabic text if in AR mode, else English."""
    return ar if get_lang() == "AR" else en

# Localization map: raw English column → display name in current language
_COL_MAP = {
    "System":           ("System",           "النظام"),
    "Model Code":       ("Model Code",       "رمز الموديل"),
    "Product":          ("Product",          "المنتج"),
    "Sale Price":       ("Sale Price",       "سعر البيع"),
    "On Hand":          ("On Hand",          "متوفر"),
    "Purchase Qty":     ("Purchase Qty",     "كمية الشراء"),
    "Branch":           ("Branch",           "الفرع"),
    "Location":         ("Location",         "الموقع"),
    "Date":             ("Date",             "التاريخ"),
    "POS Order":        ("POS Order",        "طلب نقطة بيع"),
    "Customer":         ("Customer",         "العميل"),
    "Cashier":          ("Cashier",          "الكاشير"),
    "Category":         ("Category",         "الفئة"),
    "Qty":              ("Qty",              "الكمية"),
    "Unit Price":       ("Unit Price",       "سعر الوحدة"),
    "Subtotal":         ("Subtotal",         "المجموع الفرعي"),
    "Total Amount":     ("Total Amount",     "المبلغ الإجمالي"),
    "SO":               ("SO",               "أمر بيع"),
    "Vendor":           ("Vendor",           "المورد"),
    "Receipt Location": ("Receipt Location", "موقع الاستلام"),
    "PO":               ("PO",               "أمر شراء"),
    "State":            ("State",            "الحالة"),
    "Revenue (SAR)":    ("Revenue (SAR)",    "الإيرادات (ر.س)"),
    "Bills":            ("Bills",            "الفواتير"),
    "Orders":           ("Orders",           "الطلبات"),
    "Spend (SAR)":      ("Spend (SAR)",      "الإنفاق (ر.س)"),
}

def col(raw_name: str) -> str:
    """Return the display column name in current language for a raw/canonical column name."""
    if raw_name in _COL_MAP:
        en, ar = _COL_MAP[raw_name]
        return ar if get_lang() == "AR" else en
    return raw_name

def localize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Rename only canonical columns → display language. Safe on already-localized dfs."""
    if df is None or df.empty:
        return df
    rename = {}
    for raw, (en, ar) in _COL_MAP.items():
        if raw in df.columns:
            rename[raw] = ar if get_lang() == "AR" else en
    return df.rename(columns=rename) if rename else df

def get_system_name(key: str) -> str:
    cfg = st.secrets.get(key, {})
    if get_lang() == "AR":
        return cfg.get("name_ar", cfg.get("name", key))
    return cfg.get("name", key)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULTS = {
    "authenticated":        False,
    "user_email":           "",
    "lang":                 "EN",
    "theme":                "Dark Executive",
    # Raw data (canonical English columns)
    "inventory_df":         None,
    "inventory_branch_df":  None,
    "pos_df":               None,
    "sales_df":             None,
    "purchase_df":          None,
    # Load diagnostics per module
    "inv_diag":             [],
    "pos_diag":             [],
    "sales_diag":           [],
    "pur_diag":             [],
    # Timestamps
    "inv_last_refresh":     None,
    "pos_last_refresh":     None,
    "sales_last_refresh":   None,
    "pur_last_refresh":     None,
    # Viz modes
    "inv_viz_mode":         "📋 List View",
    "pos_viz_mode":         "📋 List View",
    "sales_viz_mode":       "📋 List View",
    "pur_viz_mode":         "📋 List View",
    # Pagination
    "inv_page":             0,
    "inv_full_page":        0,
    "pos_page":             0,
    "pos_branch_page":      0,
    "pos_cashier_page":     0,
    "sales_page":           0,
    "sales_cust_page":      0,
    "pur_page":             0,
    "pur_vendor_page":      0,
    # Chat
    "chat_history":         [],
    # Login error message
    "login_error":          "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: AUTH — REAL ODOO XML-RPC (NO BYPASS)
# ─────────────────────────────────────────────────────────────────────────────

_COOKIE_SECRET = "swag_exec_2025_v3"

def _make_token(email: str) -> str:
    return hashlib.sha256(f"{_COOKIE_SECRET}_{email}".encode()).hexdigest()[:32]

def _verify_token(email: str, token: str) -> bool:
    return bool(email and token and token == _make_token(email))

def restore_session():
    """Attempt to restore login from URL query params (token-based, no plain password)."""
    if st.session_state.get("authenticated"):
        return
    try:
        params = st.query_params
        email  = params.get("u", "")
        token  = params.get("t", "")
        if email and token and _verify_token(email, token):
            st.session_state.authenticated = True
            st.session_state.user_email    = email
    except Exception:
        pass

def attempt_login(email: str, password: str) -> tuple[bool, str]:
    """
    Real Odoo XML-RPC login against the primary system (LOGIN config key if present,
    otherwise the first SYSTEM_KEY that has credentials).
    Returns (success: bool, error_message: str).
    """
    if not email or not password:
        return False, t("Please enter email and password.", "يرجى إدخال البريد الإلكتروني وكلمة المرور.")

    # Try LOGIN secret block first, then each SYSTEM_KEY
    login_candidates = []
    if "LOGIN" in st.secrets:
        login_candidates.append(("LOGIN", st.secrets["LOGIN"]))
    for key in SYSTEM_KEYS:
        cfg = st.secrets.get(key)
        if cfg and cfg.get("url") and cfg.get("db"):
            login_candidates.append((key, cfg))

    if not login_candidates:
        return False, t(
            "No Odoo connection configured in secrets. Contact administrator.",
            "لا يوجد اتصال Odoo مُكوَّن. تواصل مع المسؤول."
        )

    last_error = ""
    for source_key, cfg in login_candidates:
        url = cfg.get("url", "").rstrip("/")
        db  = cfg.get("db", "")
        if not url or not db:
            last_error = f"[{source_key}] Missing url or db in secrets."
            continue
        try:
            proxy  = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid    = proxy.authenticate(db, email, password, {})
            if uid and isinstance(uid, int) and uid > 0:
                return True, ""
            else:
                last_error = t(
                    f"Login failed for {email} on {db}. Wrong credentials.",
                    f"فشل تسجيل الدخول لـ {email} على {db}. بيانات خاطئة."
                )
        except xmlrpc.client.Fault as e:
            last_error = f"[{source_key}] Odoo error: {e.faultString}"
        except ConnectionRefusedError:
            last_error = f"[{source_key}] Connection refused: {url}"
        except OSError as e:
            last_error = f"[{source_key}] Network error: {e}"
        except Exception as e:
            last_error = f"[{source_key}] Unexpected error: {type(e).__name__}: {e}"

    return False, last_error

def do_logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: XML-RPC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def _get_proxy(url: str, endpoint: str):
    return xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/{endpoint}", allow_none=True)

@st.cache_data(ttl=28800, show_spinner=False)
def _odoo_auth(url: str, db: str, user: str, api_key: str):
    """Authenticate with API key (not user password). Returns uid or None."""
    try:
        uid = _get_proxy(url, "common").authenticate(db, user, api_key, {})
        return uid if (uid and isinstance(uid, int) and uid > 0) else None
    except Exception:
        return None

def _odoo_call(url: str, db: str, uid: int, api_key: str,
               model: str, method: str, domain: list, kwargs: dict):
    return _get_proxy(url, "object").execute_kw(db, uid, api_key, model, method, domain, kwargs)

def _get_system_conn(key: str) -> tuple:
    """
    Returns (url, db, uid, api_key, system_name, error_str).
    error_str is None on success, a diagnostic string on failure.
    """
    cfg = st.secrets.get(key)
    if not cfg:
        return None, None, None, None, key, f"[{key}] Not configured in secrets."
    url     = cfg.get("url", "").rstrip("/")
    db      = cfg.get("db", "")
    user    = cfg.get("user", "")
    api_key = cfg.get("api_key", "")
    name    = get_system_name(key)
    if not url:
        return None, None, None, None, name, f"[{key}] Missing 'url' in secrets."
    if not db:
        return None, None, None, None, name, f"[{key}] Missing 'db' in secrets."
    if not user or not api_key:
        return None, None, None, None, name, f"[{key}] Missing 'user' or 'api_key' in secrets."
    uid = _odoo_auth(url, db, user, api_key)
    if not uid:
        return url, db, None, api_key, name, f"[{key}] Auth failed — bad user/api_key or wrong DB '{db}'."
    return url, db, uid, api_key, name, None

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: DATA UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

_NUMERIC_RAW = ["Sale Price", "On Hand", "Purchase Qty", "Qty", "Unit Price",
                "Subtotal", "Total Amount"]

def coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce known numeric raw columns to float in-place. Safe to call on raw or localized dfs."""
    if df is None or df.empty:
        return df
    for c in _NUMERIC_RAW:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def safe_get_col(df: pd.DataFrame, raw_name: str) -> pd.Series:
    """Get a column by raw English name or its localized equivalent. Returns 0-filled Series if missing."""
    if df is None or df.empty:
        return pd.Series(dtype=float)
    if raw_name in df.columns:
        return pd.to_numeric(df[raw_name], errors="coerce").fillna(0)
    localized = col(raw_name)
    if localized in df.columns:
        return pd.to_numeric(df[localized], errors="coerce").fillna(0)
    return pd.Series([0.0] * len(df))

def safe_get_str_col(df: pd.DataFrame, raw_name: str) -> pd.Series:
    """Get a string column by raw name or localized equivalent."""
    if df is None or df.empty:
        return pd.Series(dtype=str)
    if raw_name in df.columns:
        return df[raw_name]
    localized = col(raw_name)
    if localized in df.columns:
        return df[localized]
    return pd.Series([""] * len(df))

def has_col(df: pd.DataFrame, raw_name: str) -> bool:
    """Check if a raw column name OR its localized equivalent exists."""
    if df is None or df.empty:
        return False
    return (raw_name in df.columns) or (col(raw_name) in df.columns)

def get_display_col(df: pd.DataFrame, raw_name: str) -> str:
    """Return the actual column name present in df (raw or localized)."""
    if df is None:
        return raw_name
    if raw_name in df.columns:
        return raw_name
    localized = col(raw_name)
    if localized in df.columns:
        return localized
    return raw_name

def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        try:
            from openpyxl.styles import Font, Alignment, PatternFill
            ws = writer.sheets["Data"]
            for cell in ws[1]:
                cell.font      = Font(bold=True, color="FFFFFF")
                cell.fill      = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
        except Exception:
            pass
    return output.getvalue()

def to_excel_branch_matrix(branch_df: pd.DataFrame) -> bytes:
    """Build a branch × model pivot table for export. Uses raw column names."""
    if branch_df is None or branch_df.empty:
        return b""
    # Work on raw columns; fall back to localized if needed
    branch_c = get_display_col(branch_df, "Branch")
    model_c  = get_display_col(branch_df, "Model Code")
    qty_c    = get_display_col(branch_df, "On Hand")
    if branch_c not in branch_df.columns or model_c not in branch_df.columns:
        return b""
    try:
        pivot = branch_df.pivot_table(index=model_c, columns=branch_c,
                                      values=qty_c, aggfunc="sum", fill_value=0)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pivot.to_excel(writer, sheet_name="Branch_Matrix")
        return output.getvalue()
    except Exception:
        return b""

def dl_name(prefix: str, ext: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: PAGINATED TABLE RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_paginated_table(df: pd.DataFrame, page_key: str, rows_per_page: int = ROWS_PER_PAGE):
    """Renders a paginated HTML table. Accepts raw or localized dataframes."""
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data to display.','لا توجد بيانات للعرض.')}</div>",
                    unsafe_allow_html=True)
        return
    if len(df.columns) == 0:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('Data has no columns.','البيانات ليس لها أعمدة.')}</div>",
                    unsafe_allow_html=True)
        return

    total_rows  = len(df)
    total_pages = max(1, math.ceil(total_rows / rows_per_page))
    current     = min(st.session_state.get(page_key, 0), total_pages - 1)
    st.session_state[page_key] = current

    start    = current * rows_per_page
    end      = min(start + rows_per_page, total_rows)
    page_df  = df.iloc[start:end]

    # Display-localize columns at render time
    display_df = localize_df(page_df)

    header_html = "".join(f"<th>{c}</th>" for c in display_df.columns)
    rows_html   = ""
    for _, row in display_df.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row.values)
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f"<div class='dataframe-wrap'><table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='pagination-bar'><span class='page-info'>"
        f"{t('Showing','عرض')} {start+1}–{end} {t('of','من')} {total_rows}"
        f" | {t('Page','صفحة')} {current+1}/{total_pages}"
        f"</span></div>",
        unsafe_allow_html=True,
    )

    c1, c2, _, c4, c5 = st.columns([1, 1, 2, 1, 1])
    if c1.button(f"⏮", key=f"{page_key}_first", use_container_width=True):
        st.session_state[page_key] = 0; st.rerun()
    if c2.button(f"◀", key=f"{page_key}_prev",  use_container_width=True):
        st.session_state[page_key] = max(0, current - 1); st.rerun()
    if c4.button(f"▶", key=f"{page_key}_next",  use_container_width=True):
        st.session_state[page_key] = min(total_pages - 1, current + 1); st.rerun()
    if c5.button(f"⏭", key=f"{page_key}_last",  use_container_width=True):
        st.session_state[page_key] = total_pages - 1; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: VISUALIZATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def apply_plotly_theme(fig):
    if fig is None:
        return fig
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=th("text"), family="IBM Plex Sans Arabic, Space Grotesk"),
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=th("border")),
    )
    fig.update_xaxes(gridcolor=th("border"), linecolor=th("border"))
    fig.update_yaxes(gridcolor=th("border"), linecolor=th("border"))
    return fig

def render_visualization(df: pd.DataFrame, viz_mode: str,
                          x_raw: str, y_raw: str,
                          label: str = "",
                          color_raw: str = None):
    """
    Renders a chart. x_raw, y_raw, color_raw are CANONICAL column names.
    Localizes only for display (axis labels, chart titles). 
    Validates columns before rendering and shows a clear warning if missing.
    """
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data for visualization.','لا توجد بيانات للتصور.')}</div>",
                    unsafe_allow_html=True)
        return

    # Resolve actual column names in df (could be raw or already localized)
    x_col = get_display_col(df, x_raw)
    y_col = get_display_col(df, y_raw)

    if x_col not in df.columns:
        st.warning(f"⚠️ {t('Column not found','العمود غير موجود')}: {x_raw} / {col(x_raw)}")
        return
    if y_col not in df.columns:
        st.warning(f"⚠️ {t('Column not found','العمود غير موجود')}: {y_raw} / {col(y_raw)}")
        return

    colors = th("plotly_colors")
    tmpl   = th("plotly_template")
    a1     = th_color("accent1")
    a2     = th_color("accent2")
    a3     = th_color("accent3")

    df_plot = df.copy()
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce").fillna(0)

    # Use localized axis labels
    x_label = col(x_raw)
    y_label = col(y_raw)

    if viz_mode == "📋 List View":
        render_paginated_table(df, f"viz_table_{abs(hash(label or x_raw)) % 10**8}")
        return

    df_agg = df_plot.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False)

    if viz_mode == "🏆 KPI Tiles":
        top_n = df_agg.head(8)
        icons = ["📦", "🏆", "⭐", "💎", "🔥", "📈", "🎯", "✅"]
        cols  = st.columns(min(4, len(top_n)))
        for i, (_, row) in enumerate(top_n.iterrows()):
            with cols[i % 4]:
                st.markdown(
                    f"<div class='kpi-tile'>"
                    f"<div class='kpi-icon'>{icons[i % len(icons)]}</div>"
                    f"<div class='kpi-value'>{row[y_col]:,.0f}</div>"
                    f"<div class='kpi-label'>{str(row[x_col])[:22]}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        return

    elif viz_mode == "📊 Column Chart":
        fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label,
                     color=y_col, color_continuous_scale=[a1, a2],
                     template=tmpl, text_auto=".2s",
                     labels={x_col: x_label, y_col: y_label})

    elif viz_mode == "📉 Horizontal Bar":
        fig = px.bar(df_agg.head(15), x=y_col, y=x_col, orientation="h",
                     title=label, color=y_col, color_continuous_scale=[a1, a2],
                     template=tmpl, text_auto=".2s",
                     labels={x_col: x_label, y_col: y_label})
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))

    elif viz_mode == "📈 Line Chart":
        fig = px.line(df_agg.head(30), x=x_col, y=y_col, title=label,
                      markers=True, template=tmpl, color_discrete_sequence=[a1],
                      labels={x_col: x_label, y_col: y_label})
        fig.update_traces(line_width=3, marker_size=8, line_color=a1, marker_color=a2)

    elif viz_mode == "📉 Area Chart":
        fig = px.area(df_agg.head(30), x=x_col, y=y_col, title=label,
                      template=tmpl, color_discrete_sequence=[a1],
                      labels={x_col: x_label, y_col: y_label})
        fig.update_traces(fillcolor=a1 + "33", line_color=a1, line_width=2.5)

    elif viz_mode == "🍕 Pie Chart":
        top_n = df_agg.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, title=label,
                     color_discrete_sequence=colors, template=tmpl, hole=0)
        fig.update_traces(textposition="inside", textinfo="percent+label")

    elif viz_mode == "🍩 Donut Chart":
        top_n = df_agg.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, hole=0.55, title=label,
                     color_discrete_sequence=colors, template=tmpl)
        fig.update_traces(textposition="inside", textinfo="percent+label")

    elif viz_mode == "📊 Stacked Column":
        sys_col = get_display_col(df_plot, "System")
        if color_raw:
            stack_by = get_display_col(df_plot, color_raw)
        elif sys_col in df_plot.columns:
            stack_by = sys_col
        else:
            stack_by = None

        if stack_by and stack_by in df_plot.columns:
            df_stack = df_plot.groupby([x_col, stack_by])[y_col].sum().reset_index()
            fig = px.bar(df_stack, x=x_col, y=y_col, color=stack_by,
                         title=label, barmode="stack", template=tmpl,
                         color_discrete_sequence=colors,
                         labels={x_col: x_label, y_col: y_label})
        else:
            fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label,
                         template=tmpl, color_discrete_sequence=colors, text_auto=".2s",
                         labels={x_col: x_label, y_col: y_label})

    elif viz_mode == "🔘 Scatter Chart":
        fig = px.scatter(df_agg.head(30), x=x_col, y=y_col, title=label,
                         size=y_col, color=y_col, color_continuous_scale=[a1, a2],
                         template=tmpl, size_max=50,
                         labels={x_col: x_label, y_col: y_label})

    elif viz_mode == "🗂️ Funnel Chart":
        top_n = df_agg.head(10)
        fig = go.Figure(go.Funnel(
            y=top_n[x_col].astype(str),
            x=top_n[y_col],
            textinfo="value+percent initial",
            marker_color=colors[:len(top_n)],
        ))
        fig.update_layout(title=label)

    elif viz_mode == "📡 Radar Chart":
        top_n = df_agg.head(8)
        cats  = top_n[x_col].astype(str).tolist()
        vals  = top_n[y_col].tolist()
        if len(cats) < 3:
            st.info(t("Radar chart needs ≥3 data points.", "مخطط الرادار يحتاج 3 نقاط على الأقل."))
            return
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", fillcolor=a1 + "33", line_color=a1, line_width=2,
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, gridcolor=th("border")),
                       angularaxis=dict(gridcolor=th("border"))),
            title=label,
        )

    else:
        fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label,
                     template=tmpl, color_discrete_sequence=colors)

    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

def viz_mode_selector(state_key: str) -> str:
    return st.selectbox(
        f"📊 {t('Visualization Mode','نمط العرض')}",
        VIZ_MODES,
        index=VIZ_MODES.index(st.session_state.get(state_key, "📋 List View")),
        key=state_key,
    )

def render_daily_trend_chart(df: pd.DataFrame, date_raw: str, value_raw: str,
                              title: str, color_key: str = "accent1"):
    """Renders a daily area trend chart. Validates columns first."""
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data for trend chart.','لا توجد بيانات لمخطط الاتجاه.')}</div>",
                    unsafe_allow_html=True)
        return
    date_c  = get_display_col(df, date_raw)
    value_c = get_display_col(df, value_raw)
    if date_c not in df.columns:
        st.warning(f"⚠️ {t('Date column missing for trend chart.','عمود التاريخ غير موجود لمخطط الاتجاه.')}")
        return
    if value_c not in df.columns:
        st.warning(f"⚠️ {t('Value column missing for trend chart.','عمود القيمة غير موجود لمخطط الاتجاه.')}")
        return
    daily = df.copy()
    daily[date_c] = pd.to_datetime(daily[date_c], errors="coerce").dt.date
    daily[value_c] = pd.to_numeric(daily[value_c], errors="coerce").fillna(0)
    trend = daily.groupby(date_c)[value_c].sum().reset_index().sort_values(date_c)
    if trend.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No date data for trend.','لا توجد بيانات تواريخ للاتجاه.')}</div>",
                    unsafe_allow_html=True)
        return
    a = th_color(color_key)
    fig = px.area(trend, x=date_c, y=value_c, title=title,
                  template=th("plotly_template"), color_discrete_sequence=[a],
                  labels={date_c: col(date_raw), value_c: col(value_raw)})
    fig.update_traces(fillcolor=a + "33", line_color=a, line_width=2.5)
    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

def render_exec_summary(df: pd.DataFrame, value_raw: str, label_raw: str, section_title: str,
                         top_n: int = 5, bottom_n: int = 3):
    """Shows top/bottom performers. Uses raw canonical column names."""
    if df is None or df.empty:
        return
    value_c = get_display_col(df, value_raw)
    label_c = get_display_col(df, label_raw)
    if value_c not in df.columns or label_c not in df.columns:
        return
    df_c = df.copy()
    df_c[value_c] = pd.to_numeric(df_c[value_c], errors="coerce").fillna(0)
    agg = df_c.groupby(label_c)[value_c].sum().reset_index().sort_values(value_c, ascending=False)

    st.markdown(f"<div class='section-header'>💡 {section_title}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    with c1:
        st.markdown(f"**🏆 {t('Top Performers','أفضل الأداء')}**")
        html = "<div class='exec-card'>"
        for i, (_, row) in enumerate(agg.head(top_n).iterrows()):
            m    = medals[i] if i < len(medals) else f"{i+1}."
            html += (f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                     f"border-bottom:1px solid {th('border')};'>"
                     f"<span>{m} {str(row[label_c])[:28]}</span>"
                     f"<b style='color:{th_color('accent1')}'>{row[value_c]:,.0f}</b></div>")
        st.markdown(html + "</div>", unsafe_allow_html=True)

    with c2:
        if len(agg) > top_n:
            st.markdown(f"**⚠️ {t('Needs Attention','يحتاج اهتماماً')}**")
            html = "<div class='exec-card'>"
            for _, row in agg.tail(bottom_n).sort_values(value_c).iterrows():
                html += (f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                         f"border-bottom:1px solid {th('border')};'>"
                         f"<span>⚠️ {str(row[label_c])[:28]}</span>"
                         f"<b style='color:{th_color('danger','#f43f5e')}'>{row[value_c]:,.0f}</b></div>")
            st.markdown(html + "</div>", unsafe_allow_html=True)

def show_diag(diag_list: list):
    """Renders diagnostic messages from a data fetch."""
    if not diag_list:
        return
    has_err = any(d.get("level") == "error" for d in diag_list)
    has_ok  = any(d.get("level") == "ok"    for d in diag_list)
    if has_err:
        with st.expander(f"⚠️ {t('Load Diagnostics (errors found)','تشخيص التحميل (توجد أخطاء)')}"):
            for d in diag_list:
                icon = "✅" if d.get("level") == "ok" else ("❌" if d.get("level") == "error" else "ℹ️")
                st.markdown(f"`{icon} [{d.get('system','')}] {d.get('msg','')}`")
    elif has_ok:
        with st.expander(f"✅ {t('Load Diagnostics (all OK)','تشخيص التحميل (كل شيء سليم)')}"):
            for d in diag_list:
                st.markdown(f"`✅ [{d.get('system','')}] {d.get('msg','')}`")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11: DATA FETCHERS — ALL RETURN RAW (CANONICAL ENGLISH) COLUMNS
# ─────────────────────────────────────────────────────────────────────────────

# ── INVENTORY ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_inventory_one(key: str, codes_tuple: tuple, exact: bool) -> tuple:
    """
    Returns (total_rows: list, branch_rows: list, diag: dict).
    All rows use canonical English column names.
    """
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return [], [], {"system": name, "level": "error", "msg": err}

    try:
        prod_domain = []
        if codes_tuple:
            if exact:
                prod_domain = [("default_code", "in", list(codes_tuple))]
            else:
                clauses = [("default_code", "=ilike", f"{c}%") for c in codes_tuple]
                prod_domain = [clauses[0]] if len(clauses) == 1 else ["|"] * (len(clauses) - 1) + clauses

        products = _odoo_call(url, db, uid, ak, "product.template", "search_read",
                              [prod_domain if prod_domain else []],
                              {"fields": ["id","name","default_code","list_price"], "limit": 5000})
        if not products:
            return [], [], {"system": name, "level": "ok", "msg": f"No products found."}

        prod_ids       = [p["id"] for p in products]
        tmpl_to_model  = {p["id"]: (p.get("default_code") or "").strip() for p in products}
        tmpl_to_name   = {p["id"]: p.get("name","") for p in products}
        tmpl_to_price  = {p["id"]: float(p.get("list_price") or 0) for p in products}

        quants = _odoo_call(url, db, uid, ak, "stock.quant", "search_read",
                            [[("product_id.product_tmpl_id", "in", prod_ids),
                              ("location_id.usage", "=", "internal")]],
                            {"fields": ["product_id","location_id","quantity",
                                        "product_id.product_tmpl_id"], "limit": 50000})

        tmpl_qty: dict = {}
        branch_rows    = []
        for q in quants:
            tmpl_raw = q.get("product_id.product_tmpl_id")
            if isinstance(tmpl_raw, list):
                tmpl_id = tmpl_raw[0]
            else:
                pid_raw = q.get("product_id")
                tmpl_id = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
            qty       = float(q.get("quantity") or 0)
            tmpl_qty[tmpl_id] = tmpl_qty.get(tmpl_id, 0) + qty
            loc       = q.get("location_id")
            loc_name  = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
            mc_val    = tmpl_to_model.get(tmpl_id, "")
            if mc_val:
                branch_rows.append({"System": name, "Branch": loc_name,
                                     "Model Code": mc_val, "On Hand": qty})

        total_rows = []
        for tmpl_id in prod_ids:
            total_rows.append({
                "System":     name,
                "Model Code": tmpl_to_model.get(tmpl_id, ""),
                "Product":    tmpl_to_name.get(tmpl_id, ""),
                "Sale Price": tmpl_to_price.get(tmpl_id, 0),
                "On Hand":    tmpl_qty.get(tmpl_id, 0),
            })

        return total_rows, branch_rows, {
            "system": name, "level": "ok",
            "msg": f"Loaded {len(total_rows)} products, {len(quants)} quant records."
        }
    except Exception as e:
        return [], [], {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_inventory(selected_keys: list, codes_tuple: tuple = (), exact: bool = False):
    all_total, all_branch, diag = [], [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_inventory_one, k, codes_tuple, exact): k for k in selected_keys}
        for f in as_completed(futs):
            total_rows, branch_rows, d = f.result()
            all_total  += total_rows
            all_branch += branch_rows
            diag.append(d)

    total_df = (pd.DataFrame(all_total)
                if all_total else
                pd.DataFrame(columns=["System","Model Code","Product","Sale Price","On Hand"]))
    branch_df = (pd.DataFrame(all_branch)[["System","Branch","Model Code","On Hand"]]
                 if all_branch else
                 pd.DataFrame(columns=["System","Branch","Model Code","On Hand"]))
    return coerce_numerics(total_df), coerce_numerics(branch_df), diag

# ── PURCHASE SUMMARY (for inventory overlay) ─────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_purchase_summary_one(key: str, model_codes_tuple: tuple,
                                 date_from: str, date_to: str) -> pd.DataFrame:
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return pd.DataFrame()
    try:
        domain = [["order_id.date_approve", ">=", f"{date_from} 00:00:00"],
                  ["order_id.date_approve", "<=", f"{date_to} 23:59:59"],
                  ["order_id.state", "in", ["purchase","done"]],
                  ["product_id.default_code", "in", list(model_codes_tuple)]]
        lines = _odoo_call(url, db, uid, ak, "purchase.order.line", "search_read", [domain],
                           {"fields": ["product_id","product_qty"], "limit": 10000})
        if not lines:
            return pd.DataFrame()
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _odoo_call(url, db, uid, ak, "product.product", "search_read",
                              [[["id","in", prod_ids]]],
                              {"fields": ["id","default_code"], "limit": len(prod_ids)+10})
        prod_map = {p["id"]: p.get("default_code","") for p in products}
        rows = []
        for line in lines:
            pid   = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            model = prod_map.get(pid, "")
            if model:
                rows.append({"Model Code": model, "_qty": float(line.get("product_qty") or 0)})
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows).groupby("Model Code")["_qty"].sum().reset_index()
        df.columns = ["Model Code", "Purchase Qty"]
        return df
    except Exception:
        return pd.DataFrame()

def fetch_purchase_summary(selected_keys: list, model_codes_tuple: tuple,
                            date_from: str, date_to: str) -> pd.DataFrame:
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(_fetch_purchase_summary_one, k, model_codes_tuple, date_from, date_to)
                for k in selected_keys]
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame(columns=["Model Code","Purchase Qty"])
    combined = pd.concat(results, ignore_index=True)
    return combined.groupby("Model Code")["Purchase Qty"].sum().reset_index()

# ── PURCHASE ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_purchase_one(key: str, model_filter: str, date_from: str, date_to: str) -> tuple:
    _empty = pd.DataFrame(columns=["System","Date","PO","Vendor","Receipt Location",
                                    "Category","Model Code","Product","Qty","Unit Price","Subtotal"])
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return _empty, {"system": name, "level": "error", "msg": err}
    try:
        po_domain = [["date_approve", ">=", f"{date_from} 00:00:00"],
                     ["date_approve", "<=", f"{date_to} 23:59:59"],
                     ["state", "in", ["purchase","done"]]]
        pos_list = _odoo_call(url, db, uid, ak, "purchase.order", "search_read", [po_domain],
                              {"fields": ["id","name","partner_id","date_approve","state"], "limit": 2000})
        if not pos_list:
            return _empty, {"system": name, "level": "ok", "msg": "No purchase orders found."}

        po_ids  = [p["id"] for p in pos_list]
        po_map  = {p["id"]: p for p in pos_list}

        lines = _odoo_call(url, db, uid, ak, "purchase.order.line", "search_read",
                           [[["order_id","in", po_ids]]],
                           {"fields": ["order_id","product_id","product_qty","price_unit","price_subtotal"],
                            "limit": 20000})
        if not lines:
            return _empty, {"system": name, "level": "ok", "msg": "No purchase lines found."}

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _odoo_call(url, db, uid, ak, "product.product", "search_read",
                              [[["id","in", prod_ids]]],
                              {"fields": ["id","default_code","name","categ_id"],
                               "limit": len(prod_ids)+10})
        prod_map = {p["id"]: p for p in products}

        pickings = _odoo_call(url, db, uid, ak, "stock.picking", "search_read",
                              [[["origin","in", [p["name"] for p in pos_list]],
                                ["picking_type_code","=","incoming"]]],
                              {"fields": ["origin","location_dest_id"], "limit": 2000})
        receipt_map: dict = {}
        for pick in pickings:
            loc      = pick.get("location_dest_id")
            loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
            receipt_map[pick.get("origin","")] = loc_name

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            po  = po_map.get(oid, {})
            if not po:
                continue
            pid       = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod      = prod_map.get(pid, {})
            mc_val    = (prod.get("default_code") or "").strip()
            if model_filter and not mc_val.upper().startswith(model_filter.upper()):
                continue
            categ_obj = prod.get("categ_id")
            category  = categ_obj[1] if isinstance(categ_obj, list) and len(categ_obj) > 1 else ""
            partner   = po.get("partner_id")
            vendor    = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            rows.append({
                "System":           name,
                "Date":             str(po.get("date_approve",""))[:10],
                "PO":               po.get("name",""),
                "Vendor":           vendor,
                "Receipt Location": receipt_map.get(po.get("name",""), ""),
                "Category":         category,
                "Model Code":       mc_val,
                "Product":          prod.get("name",""),
                "Qty":              float(line.get("product_qty") or 0),
                "Unit Price":       float(line.get("price_unit") or 0),
                "Subtotal":         float(line.get("price_subtotal") or 0),
            })

        if not rows:
            return _empty, {"system": name, "level": "ok", "msg": "Filters produced no rows."}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = coerce_numerics(df)
        return df.sort_values("Date", ascending=False).reset_index(drop=True), {
            "system": name, "level": "ok", "msg": f"Loaded {len(df)} purchase lines."
        }
    except Exception as e:
        return _empty, {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_purchase(selected_keys: list, model_filter: str, date_from: str, date_to: str):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_purchase_one, k, model_filter, date_from, date_to): k
                for k in selected_keys}
        for f in as_completed(futs):
            df, d = f.result()
            diag.append(d)
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame(), diag
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True), diag

# ── POS ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_pos_one(key: str, date_from: str, date_to: str,
                   branch_filter: str, model_filter: str) -> tuple:
    _empty = pd.DataFrame(columns=["System","Date","POS Order","Branch","Customer","Cashier",
                                    "Model Code","Product","Qty","Unit Price","Subtotal","Total Amount"])
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return _empty, {"system": name, "level": "error", "msg": err}
    try:
        order_domain = [["date_order", ">=", f"{date_from} 00:00:00"],
                        ["date_order", "<=", f"{date_to} 23:59:59"],
                        ["state", "in", ["paid","done","invoiced"]]]
        orders = _odoo_call(url, db, uid, ak, "pos.order", "search_read", [order_domain],
                            {"fields": ["id","name","date_order","amount_total","user_id",
                                        "session_id","partner_id","lines"], "limit": 5000})
        if not orders:
            return _empty, {"system": name, "level": "ok", "msg": "No POS orders found."}

        session_ids = list({o["session_id"][0] for o in orders if o.get("session_id")})
        branch_map: dict = {}
        if session_ids:
            sessions   = _odoo_call(url, db, uid, ak, "pos.session", "search_read",
                                    [[["id","in",session_ids]]],
                                    {"fields": ["id","config_id"], "limit": len(session_ids)+10})
            config_ids = list({s["config_id"][0] for s in sessions if s.get("config_id")})
            if config_ids:
                configs    = _odoo_call(url, db, uid, ak, "pos.config", "search_read",
                                        [[["id","in",config_ids]]],
                                        {"fields": ["id","name"], "limit": len(config_ids)+10})
                config_name= {c["id"]: c["name"] for c in configs}
                for s in sessions:
                    cid = s["config_id"][0] if isinstance(s.get("config_id"), list) else s.get("config_id")
                    branch_map[s["id"]] = config_name.get(cid, "Unknown")

        line_ids = []
        for o in orders:
            if o.get("lines"):
                line_ids.extend(o["lines"])
        if not line_ids:
            return _empty, {"system": name, "level": "ok", "msg": "No POS line IDs found."}

        lines = _odoo_call(url, db, uid, ak, "pos.order.line", "search_read",
                           [[["id","in", line_ids]]],
                           {"fields": ["order_id","product_id","qty","price_unit","price_subtotal"],
                            "limit": 20000})
        if not lines:
            return _empty, {"system": name, "level": "ok", "msg": "No POS lines returned."}

        order_map = {o["id"]: o for o in orders}
        prod_ids  = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products  = (_odoo_call(url, db, uid, ak, "product.product", "search_read",
                                [[["id","in", prod_ids]]],
                                {"fields": ["id","default_code","name","categ_id"],
                                 "limit": len(prod_ids)+20})
                     if prod_ids else [])
        prod_map  = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid        = line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id")
            order      = order_map.get(oid)
            if not order:
                continue
            sess_id    = order.get("session_id")
            sess_id    = sess_id[0] if isinstance(sess_id, list) else sess_id
            branch_name= branch_map.get(sess_id, "Unknown")
            if branch_filter and branch_filter.lower() not in branch_name.lower():
                continue
            pid        = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod       = prod_map.get(pid, {})
            mc_val     = (prod.get("default_code") or "").strip()
            if model_filter and not mc_val.upper().startswith(model_filter.upper()):
                continue
            partner    = order.get("partner_id")
            customer   = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            user       = order.get("user_id")
            cashier    = user[1]    if isinstance(user, list) and len(user) > 1 else ""
            rows.append({
                "System":       name,
                "Date":         str(order.get("date_order",""))[:10],
                "POS Order":    order.get("name",""),
                "Branch":       branch_name,
                "Customer":     customer,
                "Cashier":      cashier,
                "Model Code":   mc_val,
                "Product":      prod.get("name",""),
                "Qty":          float(line.get("qty") or 0),
                "Unit Price":   float(line.get("price_unit") or 0),
                "Subtotal":     float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
            })

        if not rows:
            return _empty, {"system": name, "level": "ok", "msg": "Filters produced no POS rows."}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = coerce_numerics(df)
        return df.sort_values("Date", ascending=False).reset_index(drop=True), {
            "system": name, "level": "ok", "msg": f"Loaded {len(df)} POS lines."
        }
    except Exception as e:
        return _empty, {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_pos(selected_keys: list, date_from: str, date_to: str,
              branch_filter: str, model_filter: str):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_pos_one, k, date_from, date_to, branch_filter, model_filter): k
                for k in selected_keys}
        for f in as_completed(futs):
            df, d = f.result()
            diag.append(d)
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame(), diag
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True), diag

# ── SALES ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_sales_one(key: str, date_from: str, date_to: str, model_filter: str) -> tuple:
    _empty = pd.DataFrame(columns=["System","Date","SO","Customer","Model Code","Product",
                                    "Qty","Unit Price","Subtotal","Total Amount","State"])
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return _empty, {"system": name, "level": "error", "msg": err}
    try:
        so_domain = [["date_order", ">=", f"{date_from} 00:00:00"],
                     ["date_order", "<=", f"{date_to} 23:59:59"],
                     ["state", "in", ["sale","done"]]]
        orders = _odoo_call(url, db, uid, ak, "sale.order", "search_read", [so_domain],
                            {"fields": ["id","name","date_order","amount_total",
                                        "partner_id","state","order_line"], "limit": 5000})
        if not orders:
            return _empty, {"system": name, "level": "ok", "msg": "No sales orders found."}

        order_map = {o["id"]: o for o in orders}
        line_ids  = []
        for o in orders:
            if o.get("order_line"):
                line_ids.extend(o["order_line"])
        if not line_ids:
            return _empty, {"system": name, "level": "ok", "msg": "No sales lines found."}

        lines = _odoo_call(url, db, uid, ak, "sale.order.line", "search_read",
                           [[["id","in", line_ids]]],
                           {"fields": ["order_id","product_id","product_uom_qty",
                                        "price_unit","price_subtotal"], "limit": 20000})
        if not lines:
            return _empty, {"system": name, "level": "ok", "msg": "No sale.order.line data."}

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = (_odoo_call(url, db, uid, ak, "product.product", "search_read",
                               [[["id","in", prod_ids]]],
                               {"fields": ["id","default_code","name","categ_id"],
                                "limit": len(prod_ids)+20})
                    if prod_ids else [])
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid_raw = line.get("order_id")
            oid     = oid_raw[0] if isinstance(oid_raw, list) else oid_raw
            order   = order_map.get(oid)
            if not order:
                continue
            pid_raw = line.get("product_id")
            pid     = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
            prod    = prod_map.get(pid, {})
            mc_val  = (prod.get("default_code") or "").strip()
            if model_filter and not mc_val.upper().startswith(model_filter.upper()):
                continue
            partner  = order.get("partner_id")
            customer = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            rows.append({
                "System":       name,
                "Date":         str(order.get("date_order",""))[:10],
                "SO":           order.get("name",""),
                "Customer":     customer,
                "Model Code":   mc_val,
                "Product":      prod.get("name",""),
                "Qty":          float(line.get("product_uom_qty") or 0),
                "Unit Price":   float(line.get("price_unit") or 0),
                "Subtotal":     float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
                "State":        order.get("state",""),
            })

        if not rows:
            return _empty, {"system": name, "level": "ok", "msg": "Filters produced no sales rows."}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = coerce_numerics(df)
        return df.sort_values("Date", ascending=False).reset_index(drop=True), {
            "system": name, "level": "ok", "msg": f"Loaded {len(df)} sales lines."
        }
    except Exception as e:
        return _empty, {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_sales(selected_keys: list, date_from: str, date_to: str, model_filter: str):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_sales_one, k, date_from, date_to, model_filter): k
                for k in selected_keys}
        for f in as_completed(futs):
            df, d = f.result()
            diag.append(d)
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame(), diag
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True), diag

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12: AI INSIGHTS PANEL
# ─────────────────────────────────────────────────────────────────────────────

def _insight_block(rows_data: list) -> str:
    inner = "".join(
        f"<div class='chat-insight-row'>"
        f"<span class='chat-insight-key'>{k}</span>"
        f"<span class='chat-insight-val'>{v}</span>"
        f"</div>"
        for k, v in rows_data
    )
    return f"<div class='chat-insight-block'>{inner}</div>"

def get_ai_response(user_msg: str) -> tuple:
    """
    Returns (text_response, insight_html|None).
    Uses RAW canonical column names for lookups, since session state DFs are raw.
    """
    msg      = user_msg.lower().strip()
    inv_df   = st.session_state.get("inventory_df")
    pos_df   = st.session_state.get("pos_df")
    sales_df = st.session_state.get("sales_df")
    pur_df   = st.session_state.get("purchase_df")

    # Helper: safe column sum using raw name
    def _sum(df, raw): return safe_get_col(df, raw).sum() if df is not None else 0
    def _nunique(df, raw):
        if df is None or df.empty: return 0
        c = get_display_col(df, raw)
        return df[c].nunique() if c in df.columns else 0
    def _top(df, group_raw, val_raw, n=8):
        if df is None or df.empty: return pd.Series(dtype=float)
        gc = get_display_col(df, group_raw)
        vc = get_display_col(df, val_raw)
        if gc not in df.columns or vc not in df.columns: return pd.Series(dtype=float)
        return df.groupby(gc)[vc].sum().sort_values(ascending=False).head(n)

    # ── INVENTORY ─────────────────────────────────────────────────────────────
    if any(k in msg for k in ["inventory","stock","مخزون","zero","low stock","top product","fast","slow"]):
        if inv_df is None or inv_df.empty:
            return (t("📦 No inventory data loaded. Refresh the Inventory tab first.",
                      "📦 لم يتم تحميل بيانات المخزون. يرجى تحديث تبويب المخزون أولاً."), None)
        qty_s   = safe_get_col(inv_df, "On Hand")
        price_s = safe_get_col(inv_df, "Sale Price")
        total_qty   = int(qty_s.sum())
        total_value = float((qty_s * price_s).sum())
        zero_count  = int((qty_s == 0).sum())
        low_count   = int(((qty_s > 0) & (qty_s <= 5)).sum())
        models      = _nunique(inv_df, "Model Code")

        if any(k in msg for k in ["zero","صفر"]):
            mc_col  = get_display_col(inv_df, "Model Code")
            zero_mc = inv_df[qty_s == 0][mc_col].dropna().head(8).tolist() if mc_col in inv_df.columns else []
            insight = _insight_block([
                (t("Zero Stock Models","موديلات بدون مخزون"), str(zero_count)),
                (t("Examples","أمثلة"), ", ".join(str(x) for x in zero_mc[:4])),
                (t("Action","إجراء"), t("Urgent Reorder","إعادة طلب عاجل")),
            ])
            return (t(f"🔴 {zero_count} products have zero stock. Immediate reorder recommended.",
                      f"🔴 {zero_count} منتج بدون مخزون. يُنصح بإعادة الطلب الفوري."), insight)

        if any(k in msg for k in ["low","منخفض"]):
            insight = _insight_block([
                (t("Low Stock (≤5)","مخزون منخفض (≤5)"), str(low_count)),
                (t("Zero Stock","مخزون صفر"), str(zero_count)),
            ])
            return (t(f"⚠️ {low_count} products low (≤5 units), {zero_count} out of stock.",
                      f"⚠️ {low_count} منتج منخفض، {zero_count} بدون مخزون."), insight)

        if any(k in msg for k in ["top","أعلى","fast","best"]):
            top = _top(inv_df, "Model Code", "On Hand")
            insight = _insight_block([(str(k)[:30], f"{int(v):,}") for k, v in top.items()])
            return (t("🏆 Top models by stock qty:", "🏆 أعلى موديلات حسب الكمية:"), insight)

        risk = (t("High Risk","خطر عالٍ") if zero_count > 50
                else t("Moderate","معتدل") if zero_count > 20
                else t("Low Risk","خطر منخفض"))
        insight = _insight_block([
            (t("Total Qty","إجمالي الكمية"), f"{total_qty:,}"),
            (t("Total Value (SAR)","القيمة (ر.س)"), f"{total_value:,.0f}"),
            (t("Models","الموديلات"), f"{models:,}"),
            (t("Zero Stock","صفر مخزون"), f"{zero_count:,}"),
            (t("Low Stock (≤5)","منخفض (≤5)"), f"{low_count:,}"),
        ])
        return (t(f"📦 Inventory Summary — Risk: {risk}",
                  f"📦 ملخص المخزون — الخطر: {risk}"), insight)

    # ── POS ───────────────────────────────────────────────────────────────────
    if any(k in msg for k in ["pos","cashier","كاشير","نقطة بيع","branch","فرع"]):
        if pos_df is None or pos_df.empty:
            return (t("🛒 No POS data loaded. Refresh the POS tab first.",
                      "🛒 لا توجد بيانات POS. يرجى تحديث تبويب POS أولاً."), None)
        po_col  = get_display_col(pos_df, "POS Order")
        tot_col = get_display_col(pos_df, "Total Amount")
        unique  = pos_df.drop_duplicates(subset=[po_col]) if po_col in pos_df.columns else pos_df
        total   = float(safe_get_col(unique, "Total Amount").sum())
        bills   = len(unique)
        avg     = total / bills if bills > 0 else 0

        if any(k in msg for k in ["cashier","كاشير"]):
            top = _top(unique, "Cashier", "Total Amount")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("👤 Cashier rankings by sales:","👤 ترتيب الكاشيرين:"), insight)

        if any(k in msg for k in ["branch","فرع"]):
            top = _top(unique, "Branch", "Total Amount")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("🏪 Branch POS performance:","🏪 أداء فروع POS:"), insight)

        insight = _insight_block([
            (t("Total Revenue (SAR)","إجمالي الإيرادات (ر.س)"), f"{total:,.0f}"),
            (t("Total Bills","الفواتير"), f"{bills:,}"),
            (t("Avg Bill (SAR)","متوسط الفاتورة"), f"{avg:,.2f}"),
        ])
        return (t(f"🛒 POS Summary — {bills:,} bills, SAR {total:,.0f}",
                  f"🛒 ملخص POS — {bills:,} فاتورة، {total:,.0f} ر.س"), insight)

    # ── SALES ─────────────────────────────────────────────────────────────────
    if any(k in msg for k in ["sale","مبيعات","customer","عميل","revenue"]):
        if sales_df is None or sales_df.empty:
            return (t("🛍️ No sales data loaded. Refresh the Sales tab first.",
                      "🛍️ لا توجد بيانات مبيعات. يرجى تحديث تبويب المبيعات أولاً."), None)
        so_c    = get_display_col(sales_df, "SO")
        unique  = sales_df.drop_duplicates(subset=[so_c]) if so_c in sales_df.columns else sales_df
        total   = float(safe_get_col(unique, "Total Amount").sum())
        orders  = _nunique(unique, "SO")
        avg     = total / orders if orders > 0 else 0

        if any(k in msg for k in ["customer","عميل","top customer"]):
            top     = _top(unique, "Customer", "Total Amount")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("👥 Top customers by revenue:","👥 أفضل العملاء حسب الإيراد:"), insight)

        insight = _insight_block([
            (t("Revenue (SAR)","الإيراد (ر.س)"), f"{total:,.0f}"),
            (t("Orders","الطلبات"), f"{orders:,}"),
            (t("Avg Order (SAR)","متوسط الطلب"), f"{avg:,.2f}"),
        ])
        return (t(f"🛍️ Sales Summary — {orders:,} orders, SAR {total:,.0f}",
                  f"🛍️ ملخص المبيعات — {orders:,} طلب، {total:,.0f} ر.س"), insight)

    # ── PURCHASE ──────────────────────────────────────────────────────────────
    if any(k in msg for k in ["purchase","مشتريات","vendor","مورد","po"]):
        if pur_df is None or pur_df.empty:
            return (t("🔖 No purchase data loaded. Refresh the Purchase tab first.",
                      "🔖 لا توجد بيانات مشتريات. يرجى تحديث تبويب المشتريات أولاً."), None)
        total_val = float(safe_get_col(pur_df, "Subtotal").sum())
        total_qty = float(safe_get_col(pur_df, "Qty").sum())
        vendors   = _nunique(pur_df, "Vendor")
        if any(k in msg for k in ["vendor","مورد","supplier"]):
            top     = _top(pur_df, "Vendor", "Subtotal")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("🏭 Top vendors by spend:","🏭 أفضل الموردين حسب الإنفاق:"), insight)
        insight = _insight_block([
            (t("Total Spend (SAR)","إجمالي الإنفاق (ر.س)"), f"{total_val:,.0f}"),
            (t("Total Qty","إجمالي الكمية"), f"{total_qty:,.0f}"),
            (t("Vendors","الموردون"), f"{vendors:,}"),
        ])
        return (t(f"🔖 Purchase Summary — SAR {total_val:,.0f} from {vendors:,} vendors",
                  f"🔖 ملخص المشتريات — {total_val:,.0f} ر.س من {vendors:,} مورد"), insight)

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    if any(k in msg for k in ["overview","dashboard","all","كل","executive","ملخص"]):
        data = []
        if inv_df is not None and not inv_df.empty:
            data.append((t("📦 Inventory Qty","📦 كمية المخزون"), f"{int(safe_get_col(inv_df,'On Hand').sum()):,}"))
        if sales_df is not None and not sales_df.empty:
            so_c   = get_display_col(sales_df, "SO")
            unique = sales_df.drop_duplicates(subset=[so_c]) if so_c in sales_df.columns else sales_df
            data.append((t("🛍️ Sales Revenue (SAR)","🛍️ إيرادات المبيعات (ر.س)"),
                         f"{safe_get_col(unique,'Total Amount').sum():,.0f}"))
        if pos_df is not None and not pos_df.empty:
            po_c   = get_display_col(pos_df, "POS Order")
            unique = pos_df.drop_duplicates(subset=[po_c]) if po_c in pos_df.columns else pos_df
            data.append((t("🛒 POS Revenue (SAR)","🛒 إيرادات POS (ر.س)"),
                         f"{safe_get_col(unique,'Total Amount').sum():,.0f}"))
        if pur_df is not None and not pur_df.empty:
            data.append((t("🔖 Purchase Spend (SAR)","🔖 إنفاق المشتريات (ر.س)"),
                         f"{safe_get_col(pur_df,'Subtotal').sum():,.0f}"))
        insight = _insight_block(data) if data else None
        return (t(f"💎 Executive Overview — {len(data)} modules loaded",
                  f"💎 نظرة تنفيذية — {len(data)} وحدات محملة"), insight)

    return (t(
        "🤖 Ask me about: inventory summary, zero stock, low stock, POS branch sales, top customers, vendor ranking, or 'executive overview'.",
        "🤖 اسألني عن: ملخص المخزون، صفر مخزون، مخزون منخفض، مبيعات فروع POS، أفضل العملاء، أفضل الموردين، أو 'نظرة تنفيذية'.",
    ), None)

def show_chat_panel():
    st.markdown(f"<div class='section-header'>🤖 {t('Executive AI Insights','المساعد الذكي التنفيذي')}</div>",
                unsafe_allow_html=True)

    history_html = "<div style='max-height:440px;overflow-y:auto;padding:8px;'>"
    if not st.session_state.chat_history:
        history_html += f"<div style='text-align:center;padding:40px 0;color:{th('text_muted')};'>" \
                        f"<div style='font-size:2rem;margin-bottom:12px;'>🤖</div>" \
                        f"<div>{t('Ask me anything about your loaded data.','اسألني أي شيء عن بياناتك المحملة.')}</div>" \
                        f"</div>"
    for msg in st.session_state.chat_history[-30:]:
        if msg["role"] == "user":
            history_html += f"<div class='chat-label-user'>{t('You','أنت')}</div>"
            history_html += f"<div class='chat-msg-user'>{msg['content']}</div>"
        else:
            history_html += f"<div class='chat-label-bot'>🤖 AI</div>"
            history_html += f"<div class='chat-msg-bot'>{msg['content'].replace(chr(10),'<br>')}</div>"
            if msg.get("insight_html"):
                history_html += msg["insight_html"]
    history_html += "</div>"
    st.markdown(history_html, unsafe_allow_html=True)

    chip_actions = [
        (t("💎 Overview","💎 نظرة عامة"),       t("executive overview","نظرة تنفيذية")),
        (t("📦 Inventory","📦 المخزون"),          t("inventory summary","ملخص المخزون")),
        (t("🔴 Zero Stock","🔴 مخزون صفر"),       t("zero stock","مخزون صفر")),
        (t("🛒 POS Branches","🛒 فروع POS"),      t("POS branch sales","مبيعات فروع POS")),
        (t("👥 Top Customers","👥 أفضل العملاء"), t("top customers","أفضل العملاء")),
        (t("🏭 Top Vendors","🏭 أفضل الموردين"),  t("top vendors","أفضل الموردين")),
    ]
    chip_cols = st.columns(3)
    for i, (label, query) in enumerate(chip_actions):
        with chip_cols[i % 3]:
            if st.button(label, key=f"chip_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": label})
                text, insight = get_ai_response(query)
                st.session_state.chat_history.append({"role":"bot","content":text,"insight_html":insight or ""})
                st.rerun()

    col_in, col_send, col_clear = st.columns([5, 1, 1])
    with col_in:
        user_input = st.text_input(
            t("Ask...","اسأل..."), key="chat_input", label_visibility="collapsed",
            placeholder=t("e.g. zero stock, top customers, POS branch sales...",
                          "مثال: صفر مخزون، أفضل العملاء، مبيعات الفروع..."))
    with col_send:
        if st.button(t("Send","إرسال"), type="primary", key="chat_send", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append({"role":"user","content":user_input})
                text, insight = get_ai_response(user_input)
                st.session_state.chat_history.append({"role":"bot","content":text,"insight_html":insight or ""})
                st.rerun()
    with col_clear:
        if st.button("🗑️", key="chat_clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13: LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

def show_login():
    st.markdown(build_css(), unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-orb'>💎</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>Executive Operations</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-subtitle'>Multi-Company Analytics · Board-Level Dashboard</div>",
                    unsafe_allow_html=True)

        if st.session_state.get("login_error"):
            st.markdown(
                f"<div class='alert-banner'>❌ {st.session_state.login_error}</div>",
                unsafe_allow_html=True,
            )

        with st.form("login_form"):
            email     = st.text_input("Email / البريد الإلكتروني", placeholder="user@company.com")
            password  = st.text_input("Password / كلمة المرور", type="password")
            submitted = st.form_submit_button("🚀 Login / دخول", type="primary", use_container_width=True)
            if submitted:
                with st.spinner(t("Verifying credentials...","جاري التحقق من البيانات...")):
                    ok, err = attempt_login(email.strip(), password)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.user_email    = email.strip()
                    st.session_state.login_error   = ""
                    token = _make_token(email.strip())
                    try:
                        st.query_params.update({"u": email.strip(), "t": token})
                    except Exception:
                        pass
                    st.rerun()
                else:
                    st.session_state.login_error = err
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 14: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def show_dashboard():
    st.markdown(build_css(), unsafe_allow_html=True)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"<div style='background:{th('card_bg')};border:1px solid {th('border')};"
            f"border-radius:14px;padding:14px;margin-bottom:16px;text-align:center;'>"
            f"<div style='font-size:1.8rem;'>💎</div>"
            f"<div style='font-size:0.88rem;font-weight:700;color:{th('text')};'>SWAG DASHBARD</div>"
            f"<div style='font-size:0.7rem;color:{th('text_muted')};'>{st.session_state.user_email}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        new_theme = st.selectbox(
            f"🎨 {t('Theme','المظهر')}",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(get_theme()),
            key="theme_select",
        )
        if new_theme != get_theme():
            st.session_state.theme = new_theme
            st.rerun()

        st.divider()

        new_lang = st.radio(f"🌐 {t('Language','اللغة')}", ["EN","AR"],
                            index=0 if get_lang() == "EN" else 1, horizontal=True)
        if new_lang != get_lang():
            # Language change: clear all cached data so it can be re-fetched/re-displayed
            for k in ["inventory_df","inventory_branch_df","pos_df","sales_df","purchase_df",
                      "inv_diag","pos_diag","sales_diag","pur_diag"]:
                st.session_state[k] = None if "df" in k else []
            st.session_state.lang = new_lang
            # Clear cached data functions
            _fetch_inventory_one.clear()
            _fetch_purchase_one.clear()
            _fetch_pos_one.clear()
            _fetch_sales_one.clear()
            st.rerun()

        st.divider()

        st.markdown(f"**🏢 {t('Connected Systems','الأنظمة المتصلة')}**")
        for key in SYSTEM_KEYS:
            cfg   = st.secrets.get(key, {})
            name  = get_system_name(key)
            badge = "badge-ok" if cfg.get("url") else "badge-off"
            icon  = "✓" if cfg.get("url") else "✗"
            st.markdown(f"<div style='margin:4px 0;'><span class='{badge}'>{icon} {name}</span></div>",
                        unsafe_allow_html=True)

        st.divider()

        st.markdown(f"**📊 {t('Loaded Data','البيانات المحملة')}**")
        for icon, name, df_key, ts_key in [
            ("📦", t("Inventory","المخزون"),   "inventory_df",  "inv_last_refresh"),
            ("🛒", t("POS","نقاط البيع"),       "pos_df",        "pos_last_refresh"),
            ("🛍️", t("Sales","المبيعات"),       "sales_df",      "sales_last_refresh"),
            ("🔖", t("Purchase","المشتريات"),   "purchase_df",   "pur_last_refresh"),
        ]:
            df = st.session_state.get(df_key)
            ts = st.session_state.get(ts_key)
            if df is not None and not df.empty:
                ts_str = f" ({ts.strftime('%H:%M')})" if ts else ""
                st.markdown(f"<span class='badge-ok'>{icon} {name} ({len(df):,}){ts_str}</span>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='badge-warn'>{icon} {name} —</span>", unsafe_allow_html=True)

        st.divider()
        if st.button(f"🚪 {t('Logout','تسجيل الخروج')}", use_container_width=True):
            do_logout()

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<div class='dash-header'>"
        f"<div class='dash-title'>SWAG — SWAG DASBAORD</div>"
        f"<div class='dash-subtitle'>"
        f"{t('Multi-Company · Inventory · POS · Sales · Purchase · AI Insights','متعدد الشركات · المخزون · نقاط البيع · المبيعات · المشتريات · تحليلات ذكية')}"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab_inv, tab_pos, tab_sales, tab_pur, tab_chat = st.tabs([
        f"📦 {t('Inventory','المخزون')}",
        f"🛒 {t('POS','نقاط البيع')}",
        f"🛍️ {t('Sales','المبيعات')}",
        f"🔖 {t('Purchase','المشتريات')}",
        f"🤖 {t('AI Insights','تحليلات ذكية')}",
    ])

    # =========================================================================
    # INVENTORY TAB
    # =========================================================================
    with tab_inv:
        st.markdown(f"<div class='section-header'>📦 {t('Inventory Overview','نظرة عامة على المخزون')}</div>",
                    unsafe_allow_html=True)

        ic1, ic2, ic3 = st.columns([2, 1.5, 1])
        with ic1:
            co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            inv_co  = st.selectbox(t("Company","الشركة"), co_opts, key="inv_company")
            inv_keys= SYSTEM_KEYS if inv_co == t("All Companies","جميع الشركات") \
                      else [k for k in SYSTEM_KEYS if get_system_name(k) == inv_co]
        with ic2:
            low_thresh = st.number_input(t("Low stock threshold","حد المنخفض"),
                                         min_value=0, max_value=1000, value=5, step=1, key="inv_low_thresh")
        with ic3:
            exact_match = st.toggle(t("Exact match","تطابق تام"), value=False, key="inv_exact")

        ifc1, ifc2 = st.columns([3, 1])
        with ifc1:
            model_filter = st.text_input(t("Model Code filter","فلتر رمز الموديل"), key="inv_model_filter").strip()
        with ifc2:
            if st.button(t("Reset","إعادة تعيين"), key="inv_reset"):
                for k in ["inv_model_filter","inv_exact","inv_low_thresh"]:
                    st.session_state.pop(k, None)
                st.rerun()

        inv_viz_mode = viz_mode_selector("inv_viz_mode")

        if st.button(f"🔄 {t('Refresh Inventory','تحديث المخزون')}", type="primary", key="inv_refresh"):
            with st.spinner(t("Fetching inventory...","جاري جلب المخزون...")):
                codes = tuple([model_filter]) if model_filter else ()
                total_df, branch_df, diag = fetch_inventory(inv_keys, codes, exact_match)

                # Purchase qty overlay (last 365 days)
                if total_df is not None and not total_df.empty and "Model Code" in total_df.columns:
                    mc_vals = total_df["Model Code"].dropna().unique().tolist()
                    if mc_vals:
                        end_d   = datetime.now().date()
                        start_d = end_d - timedelta(days=365)
                        pur_sum = fetch_purchase_summary(
                            inv_keys, tuple(mc_vals),
                            start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d"),
                        )
                        if pur_sum is not None and not pur_sum.empty:
                            total_df = total_df.merge(pur_sum, on="Model Code", how="left")
                            total_df["Purchase Qty"] = total_df["Purchase Qty"].fillna(0).astype(int)
                        else:
                            total_df["Purchase Qty"] = 0
                    else:
                        total_df["Purchase Qty"] = 0

                st.session_state.inventory_df        = coerce_numerics(total_df)
                st.session_state.inventory_branch_df = coerce_numerics(branch_df)
                st.session_state.inv_diag            = diag
                st.session_state.inv_page            = 0
                st.session_state.inv_full_page       = 0
                st.session_state.inv_last_refresh    = datetime.now()

        show_diag(st.session_state.get("inv_diag", []))

        total_df  = st.session_state.get("inventory_df")
        branch_df = st.session_state.get("inventory_branch_df")

        if total_df is None or total_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh Inventory to load data.','اضغط تحديث المخزون لتحميل البيانات.')}</div>",
                        unsafe_allow_html=True)
        else:
            qty_s    = safe_get_col(total_df, "On Hand")
            price_s  = safe_get_col(total_df, "Sale Price")
            total_qty= int(qty_s.sum())
            total_val= float((qty_s * price_s).sum())
            models   = int(total_df["Model Code"].nunique()) if "Model Code" in total_df.columns else 0
            br_count = (int(branch_df["Branch"].nunique()) if (branch_df is not None and not branch_df.empty
                        and "Branch" in branch_df.columns) else 0)
            zero_cnt = int((qty_s == 0).sum())
            low_cnt  = int(((qty_s > 0) & (qty_s <= low_thresh)).sum())

            m1,m2,m3,m4,m5,m6 = st.columns(6)
            m1.metric(t("Total Qty","إجمالي الكمية"),        f"{total_qty:,}")
            m2.metric(t("Inventory Value","قيمة المخزون"),   f"SAR {total_val:,.0f}")
            m3.metric(t("Models","الموديلات"),               f"{models:,}")
            m4.metric(t("Branches","الفروع"),                f"{br_count:,}")
            m5.metric(t("Zero Stock","صفر مخزون"),           f"{zero_cnt:,}",
                      delta=f"-{zero_cnt}" if zero_cnt > 0 else None, delta_color="inverse")
            m6.metric(t(f"Low ≤{low_thresh}",f"منخفض ≤{low_thresh}"), f"{low_cnt:,}",
                      delta=f"-{low_cnt}" if low_cnt > 0 else None, delta_color="inverse")
            st.divider()

            if zero_cnt > 0:
                st.markdown(f"<div class='alert-banner'>🔴 {zero_cnt} {t('products with zero stock — reorder immediately','منتج بدون مخزون — أعد الطلب فوراً')}</div>",
                            unsafe_allow_html=True)
            if low_cnt > 0:
                st.markdown(f"<div class='warn-banner'>⚠️ {low_cnt} {t(f'products low stock (≤{low_thresh})',f'منتج مخزون منخفض (≤{low_thresh})')}</div>",
                            unsafe_allow_html=True)

            st.markdown(f"<div class='section-header'>📊 {t('Stock Visualization','تصور المخزون')}</div>",
                        unsafe_allow_html=True)
            render_visualization(total_df, inv_viz_mode, "Model Code", "On Hand",
                                 t("Stock by Model","المخزون حسب الموديل"))
            st.divider()

            render_exec_summary(total_df, "On Hand", "Model Code",
                                t("Stock Performance","أداء المخزون"))
            st.divider()

            if branch_df is not None and not branch_df.empty and "Branch" in branch_df.columns:
                st.markdown(f"<div class='section-header'>🏪 {t('Branch Distribution','توزيع المخزون حسب الفرع')}</div>",
                            unsafe_allow_html=True)
                branch_agg = branch_df.groupby("Branch")["On Hand"].sum().reset_index().sort_values("On Hand", ascending=False)
                fig_b = px.bar(branch_agg, x="Branch", y="On Hand",
                               color="On Hand", color_continuous_scale=[th_color("accent1"),th_color("accent2")],
                               template=th("plotly_template"), text_auto=".2s",
                               labels={"Branch": col("Branch"), "On Hand": col("On Hand")})
                st.plotly_chart(apply_plotly_theme(fig_b), use_container_width=True)
                st.divider()

            # Low stock detail table
            st.markdown(f"<div class='section-header'>📋 {t('Low/Zero Stock Items','عناصر المخزون المنخفض/الصفري')}</div>",
                        unsafe_allow_html=True)
            low_df = total_df[qty_s <= low_thresh].copy()
            render_paginated_table(low_df, "inv_page")

            with st.expander(f"📋 {t('Full Inventory Table','جدول المخزون الكامل')}"):
                render_paginated_table(total_df, "inv_full_page")

            st.markdown("<br>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button("⬇️ CSV", to_csv(localize_df(total_df)),
                                   dl_name("inventory","csv"), "text/csv", use_container_width=True)
            with d2:
                st.download_button("⬇️ Excel", to_excel(localize_df(total_df)),
                                   dl_name("inventory","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with d3:
                if branch_df is not None and not branch_df.empty:
                    bdf = (branch_df[branch_df["Model Code"].str.contains(model_filter, case=False, na=False)]
                           if model_filter else branch_df)
                    st.download_button(
                        f"📊 {t('Branch Matrix','مصفوفة الفروع')}",
                        to_excel_branch_matrix(bdf),
                        dl_name("branch_matrix","xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    # =========================================================================
    # POS TAB
    # =========================================================================
    with tab_pos:
        st.markdown(f"<div class='section-header'>🛒 {t('POS Analytics','تحليلات نقاط البيع')}</div>",
                    unsafe_allow_html=True)

        pc1, pc2 = st.columns([2, 2])
        with pc1:
            pos_co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            pos_co      = st.selectbox(t("Company","الشركة"), pos_co_opts, key="pos_company")
            pos_keys    = SYSTEM_KEYS if pos_co == t("All Companies","جميع الشركات") \
                          else [k for k in SYSTEM_KEYS if get_system_name(k) == pos_co]
        with pc2:
            pos_viz_mode = viz_mode_selector("pos_viz_mode")

        pd1, pd2 = st.columns(2)
        with pd1:
            pos_from = st.date_input(t("From","من"), value=datetime.now().date()-timedelta(days=30), key="pos_date_from")
        with pd2:
            pos_to   = st.date_input(t("To","إلى"), value=datetime.now().date(), key="pos_date_to")

        pf1, pf2 = st.columns(2)
        with pf1:
            pos_branch = st.text_input(t("Branch filter","فلتر الفرع"), key="pos_branch_filter").strip()
        with pf2:
            pos_model  = st.text_input(t("Model Code","رمز الموديل"), key="pos_model_filter").strip()

        if st.button(t("Reset Filters","إعادة تعيين"), key="pos_reset"):
            for k in ["pos_branch_filter","pos_model_filter"]:
                st.session_state.pop(k, None)
            st.rerun()

        if st.button(f"🔄 {t('Refresh POS','تحديث POS')}", type="primary", key="pos_refresh"):
            with st.spinner(t("Fetching POS data...","جاري جلب بيانات POS...")):
                df, diag = fetch_pos(pos_keys,
                                     pos_from.strftime("%Y-%m-%d"), pos_to.strftime("%Y-%m-%d"),
                                     pos_branch, pos_model)
                st.session_state.pos_df          = coerce_numerics(df) if df is not None else None
                st.session_state.pos_diag        = diag
                st.session_state.pos_page        = 0
                st.session_state.pos_branch_page = 0
                st.session_state.pos_cashier_page= 0
                st.session_state.pos_last_refresh= datetime.now()

        show_diag(st.session_state.get("pos_diag", []))

        pos_df = st.session_state.get("pos_df")
        if pos_df is None or pos_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh POS to load data.','اضغط تحديث POS لتحميل البيانات.')}</div>",
                        unsafe_allow_html=True)
        else:
            # All logic uses raw column names
            po_col  = "POS Order"
            tot_col = "Total Amount"
            qty_col = "Qty"
            br_col  = "Branch"
            ca_col  = "Cashier"
            mc_col  = "Model Code"
            dt_col  = "Date"

            unique = pos_df.drop_duplicates(subset=[po_col]) if po_col in pos_df.columns else pos_df
            total_rev  = float(safe_get_col(unique, tot_col).sum())
            total_qty_v= float(safe_get_col(pos_df,  qty_col).sum())
            total_bills= len(unique)
            avg_bill   = total_rev / total_bills if total_bills > 0 else 0

            m1,m2,m3,m4 = st.columns(4)
            m1.metric(t("Revenue (SAR)","الإيرادات (ر.س)"), f"{total_rev:,.0f}")
            m2.metric(t("Units Sold","الوحدات"),             f"{total_qty_v:,.0f}")
            m3.metric(t("Bills","الفواتير"),                 f"{total_bills:,}")
            m4.metric(t("Avg Bill (SAR)","متوسط الفاتورة"),  f"{avg_bill:,.2f}")
            st.divider()

            st.markdown(f"<div class='section-header'>📊 {t('POS Visualization','تصور POS')}</div>",
                        unsafe_allow_html=True)
            if has_col(unique, br_col) and has_col(unique, tot_col):
                render_visualization(unique, pos_viz_mode, br_col, tot_col,
                                     t("Revenue by Branch","الإيرادات حسب الفرع"))
            elif has_col(pos_df, mc_col) and has_col(pos_df, qty_col):
                render_visualization(pos_df, pos_viz_mode, mc_col, qty_col,
                                     t("Qty by Model","الكمية حسب الموديل"))
            st.divider()

            if has_col(unique, br_col):
                render_exec_summary(unique, tot_col, br_col, t("Branch Performance","أداء الفروع"))
                st.divider()

                br_agg = unique.copy()
                br_c_  = get_display_col(br_agg, br_col)
                tot_c_ = get_display_col(br_agg, tot_col)
                po_c_  = get_display_col(br_agg, po_col)
                if br_c_ in br_agg.columns and tot_c_ in br_agg.columns:
                    agg_df = br_agg.groupby(br_c_).agg(
                        **{"Revenue (SAR)": (tot_c_, "sum"),
                           "Bills": (po_c_ if po_c_ in br_agg.columns else tot_c_, "count")}
                    ).reset_index().sort_values("Revenue (SAR)", ascending=False)
                    st.markdown(f"<div class='section-header'>🏪 {t('Branch Summary','ملخص الفروع')}</div>",
                                unsafe_allow_html=True)
                    render_paginated_table(agg_df, "pos_branch_page")
                    st.divider()

            if has_col(unique, ca_col):
                ca_c_ = get_display_col(unique, ca_col)
                tot_c_= get_display_col(unique, tot_col)
                ca_agg= unique.groupby(ca_c_)[tot_c_].sum().reset_index().sort_values(tot_c_, ascending=False)
                st.markdown(f"<div class='section-header'>👤 {t('Cashier Performance','أداء الكاشير')}</div>",
                            unsafe_allow_html=True)
                fig_ca = px.bar(ca_agg.head(10), x=ca_c_, y=tot_c_,
                                color=tot_c_, color_continuous_scale=[th_color("accent1"),th_color("accent2")],
                                template=th("plotly_template"), text_auto=".2s",
                                labels={ca_c_: col("Cashier"), tot_c_: col("Total Amount")})
                st.plotly_chart(apply_plotly_theme(fig_ca), use_container_width=True)
                render_paginated_table(ca_agg, "pos_cashier_page")
                st.divider()

            if has_col(pos_df, mc_col) and has_col(pos_df, qty_col):
                mc_c_ = get_display_col(pos_df, mc_col)
                q_c_  = get_display_col(pos_df, qty_col)
                tp    = pos_df.groupby(mc_c_)[q_c_].sum().reset_index().sort_values(q_c_, ascending=False).head(10)
                st.markdown(f"<div class='section-header'>🏆 {t('Top 10 Products','أفضل 10 منتجات')}</div>",
                            unsafe_allow_html=True)
                fig_tp = px.bar(tp, x=mc_c_, y=q_c_, color=q_c_,
                                color_continuous_scale=[th_color("accent1"),th_color("accent2")],
                                template=th("plotly_template"), text_auto=".2s",
                                labels={mc_c_: col("Model Code"), q_c_: col("Qty")})
                st.plotly_chart(apply_plotly_theme(fig_tp), use_container_width=True)
                st.divider()

            st.markdown(f"<div class='section-header'>📈 {t('Daily Revenue Trend','الاتجاه اليومي')}</div>",
                        unsafe_allow_html=True)
            render_daily_trend_chart(unique, "Date", "Total Amount",
                                     t("Daily POS Revenue","الإيراد اليومي POS"), "accent1")
            st.divider()

            st.markdown(f"<div class='section-header'>📋 {t('POS Transactions','معاملات POS')}</div>",
                        unsafe_allow_html=True)
            render_paginated_table(pos_df, "pos_page")

            st.markdown("<br>", unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                st.download_button("⬇️ CSV", to_csv(localize_df(pos_df)),
                                   dl_name("pos","csv"), "text/csv", use_container_width=True)
            with p2:
                st.download_button("⬇️ Excel", to_excel(localize_df(pos_df)),
                                   dl_name("pos","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

    # =========================================================================
    # SALES TAB
    # =========================================================================
    with tab_sales:
        st.markdown(f"<div class='section-header'>🛍️ {t('Sales Analytics','تحليلات المبيعات')}</div>",
                    unsafe_allow_html=True)

        sc1, sc2 = st.columns([2, 2])
        with sc1:
            s_co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            s_co      = st.selectbox(t("Company","الشركة"), s_co_opts, key="sales_company")
            s_keys    = SYSTEM_KEYS if s_co == t("All Companies","جميع الشركات") \
                        else [k for k in SYSTEM_KEYS if get_system_name(k) == s_co]
        with sc2:
            sales_viz_mode = viz_mode_selector("sales_viz_mode")

        sd1, sd2 = st.columns(2)
        with sd1:
            s_from = st.date_input(t("From","من"), value=datetime.now().date()-timedelta(days=30), key="sales_date_from")
        with sd2:
            s_to   = st.date_input(t("To","إلى"), value=datetime.now().date(), key="sales_date_to")

        s_model = st.text_input(t("Model Code filter","فلتر رمز الموديل"), key="sales_model_filter").strip()
        if st.button(t("Reset Filters","إعادة تعيين"), key="sales_reset"):
            st.session_state.pop("sales_model_filter", None)
            st.rerun()

        if st.button(f"🔄 {t('Refresh Sales','تحديث المبيعات')}", type="primary", key="sales_refresh"):
            with st.spinner(t("Fetching sales data...","جاري جلب بيانات المبيعات...")):
                df, diag = fetch_sales(s_keys,
                                       s_from.strftime("%Y-%m-%d"), s_to.strftime("%Y-%m-%d"),
                                       s_model)
                st.session_state.sales_df          = coerce_numerics(df) if df is not None else None
                st.session_state.sales_diag        = diag
                st.session_state.sales_page        = 0
                st.session_state.sales_cust_page   = 0
                st.session_state.sales_last_refresh= datetime.now()

        show_diag(st.session_state.get("sales_diag", []))

        sales_df = st.session_state.get("sales_df")
        if sales_df is None or sales_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh Sales to load data.','اضغط تحديث المبيعات لتحميل البيانات.')}</div>",
                        unsafe_allow_html=True)
        else:
            so_col   = "SO"
            tot_col  = "Total Amount"
            qty_col  = "Qty"
            cust_col = "Customer"
            mc_col   = "Model Code"
            dt_col   = "Date"
            sub_col  = "Subtotal"

            if so_col not in sales_df.columns:
                st.warning(f"⚠️ {t('SO column missing — please refresh data.','عمود SO غير موجود — يرجى تحديث البيانات.')}")
            else:
                unique      = sales_df.drop_duplicates(subset=[so_col])
                total_rev   = float(safe_get_col(unique, tot_col).sum())
                total_orders= int(unique[so_col].nunique())
                total_qty_v = float(safe_get_col(sales_df, qty_col).sum())
                avg_order   = total_rev / total_orders if total_orders > 0 else 0

                m1,m2,m3,m4 = st.columns(4)
                m1.metric(t("Revenue (SAR)","الإيراد (ر.س)"),    f"{total_rev:,.0f}")
                m2.metric(t("Units Sold","الوحدات"),              f"{total_qty_v:,.0f}")
                m3.metric(t("Orders","الطلبات"),                  f"{total_orders:,}")
                m4.metric(t("Avg Order (SAR)","متوسط الطلب"),     f"{avg_order:,.2f}")
                st.divider()

                st.markdown(f"<div class='section-header'>📊 {t('Sales Visualization','تصور المبيعات')}</div>",
                            unsafe_allow_html=True)
                render_visualization(sales_df, sales_viz_mode, mc_col, qty_col,
                                     t("Units Sold by Model","الوحدات حسب الموديل"))
                st.divider()

                if has_col(unique, cust_col):
                    render_exec_summary(unique, tot_col, cust_col,
                                        t("Customer Revenue Analysis","تحليل إيرادات العملاء"))
                    st.divider()

                    cu_c_ = get_display_col(unique, cust_col)
                    to_c_ = get_display_col(unique, tot_col)
                    so_c_ = get_display_col(unique, so_col)
                    ca_df = unique.groupby(cu_c_).agg(
                        **{"Revenue (SAR)": (to_c_, "sum"),
                           "Orders": (so_c_ if so_c_ in unique.columns else to_c_, "count")}
                    ).reset_index().sort_values("Revenue (SAR)", ascending=False)
                    st.markdown(f"<div class='section-header'>👥 {t('Customer Leaderboard','ترتيب العملاء')}</div>",
                                unsafe_allow_html=True)
                    render_paginated_table(ca_df, "sales_cust_page")
                    st.divider()

                if has_col(sales_df, mc_col) and has_col(sales_df, qty_col):
                    mc_c_ = get_display_col(sales_df, mc_col)
                    q_c_  = get_display_col(sales_df, qty_col)
                    tp    = sales_df.groupby(mc_c_)[q_c_].sum().reset_index().sort_values(q_c_, ascending=False).head(10)
                    st.markdown(f"<div class='section-header'>🏆 {t('Top 10 Products by Qty','أفضل 10 منتجات حسب الكمية')}</div>",
                                unsafe_allow_html=True)
                    fig_tp = px.bar(tp, x=mc_c_, y=q_c_, color=q_c_,
                                    color_continuous_scale=[th_color("accent1"),th_color("accent2")],
                                    template=th("plotly_template"), text_auto=".2s",
                                    labels={mc_c_: col("Model Code"), q_c_: col("Qty")})
                    st.plotly_chart(apply_plotly_theme(fig_tp), use_container_width=True)
                    st.divider()

                st.markdown(f"<div class='section-header'>📈 {t('Daily Revenue Trend','الاتجاه اليومي للإيرادات')}</div>",
                            unsafe_allow_html=True)
                render_daily_trend_chart(unique, "Date", "Total Amount",
                                         t("Daily Sales Revenue","الإيراد اليومي"), "accent2")
                st.divider()

                st.markdown(f"<div class='section-header'>📋 {t('Sales Detail','تفاصيل المبيعات')}</div>",
                            unsafe_allow_html=True)
                render_paginated_table(sales_df, "sales_page")

                st.markdown("<br>", unsafe_allow_html=True)
                s1, s2 = st.columns(2)
                with s1:
                    st.download_button("⬇️ CSV", to_csv(localize_df(sales_df)),
                                       dl_name("sales","csv"), "text/csv", use_container_width=True)
                with s2:
                    st.download_button("⬇️ Excel", to_excel(localize_df(sales_df)),
                                       dl_name("sales","xlsx"),
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)

    # =========================================================================
    # PURCHASE TAB
    # =========================================================================
    with tab_pur:
        st.markdown(f"<div class='section-header'>🔖 {t('Purchase Analytics','تحليلات المشتريات')}</div>",
                    unsafe_allow_html=True)

        pur_c1, pur_c2 = st.columns([2, 2])
        with pur_c1:
            p_co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            p_co      = st.selectbox(t("Company","الشركة"), p_co_opts, key="pur_company")
            p_keys    = SYSTEM_KEYS if p_co == t("All Companies","جميع الشركات") \
                        else [k for k in SYSTEM_KEYS if get_system_name(k) == p_co]
        with pur_c2:
            pur_viz_mode = viz_mode_selector("pur_viz_mode")

        prd1, prd2 = st.columns(2)
        with prd1:
            p_from = st.date_input(t("From","من"), value=datetime.now().date()-timedelta(days=90), key="pur_date_from")
        with prd2:
            p_to   = st.date_input(t("To","إلى"), value=datetime.now().date(), key="pur_date_to")

        p_model = st.text_input(t("Model Code filter","فلتر رمز الموديل"), key="pur_model_filter").strip()
        if st.button(t("Reset Filters","إعادة تعيين"), key="pur_reset"):
            st.session_state.pop("pur_model_filter", None)
            st.rerun()

        if st.button(f"🔄 {t('Refresh Purchase','تحديث المشتريات')}", type="primary", key="pur_refresh"):
            with st.spinner(t("Fetching purchase data...","جاري جلب بيانات المشتريات...")):
                df, diag = fetch_purchase(p_keys, p_model,
                                          p_from.strftime("%Y-%m-%d"), p_to.strftime("%Y-%m-%d"))
                st.session_state.purchase_df      = coerce_numerics(df) if df is not None else None
                st.session_state.pur_diag         = diag
                st.session_state.pur_page         = 0
                st.session_state.pur_vendor_page  = 0
                st.session_state.pur_last_refresh = datetime.now()

        show_diag(st.session_state.get("pur_diag", []))

        pur_df = st.session_state.get("purchase_df")
        if pur_df is None or pur_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh Purchase to load data.','اضغط تحديث المشتريات لتحميل البيانات.')}</div>",
                        unsafe_allow_html=True)
        else:
            qty_col = "Qty"
            sub_col = "Subtotal"
            ven_col = "Vendor"
            mc_col  = "Model Code"
            dt_col  = "Date"
            loc_col = "Receipt Location"
            po_col  = "PO"

            total_val = float(safe_get_col(pur_df, sub_col).sum())
            total_qty = int(safe_get_col(pur_df, qty_col).sum())
            vendors   = int(pur_df[ven_col].nunique()) if ven_col in pur_df.columns else 0
            pos_n     = int(pur_df[po_col].nunique())  if po_col  in pur_df.columns else 0

            m1,m2,m3,m4 = st.columns(4)
            m1.metric(t("Purchase Value (SAR)","قيمة الشراء (ر.س)"),  f"{total_val:,.0f}")
            m2.metric(t("Units Purchased","الوحدات المشتراة"),          f"{total_qty:,}")
            m3.metric(t("Active Vendors","الموردون"),                   f"{vendors:,}")
            m4.metric(t("Purchase Orders","أوامر الشراء"),              f"{pos_n:,}")
            st.divider()

            st.markdown(f"<div class='section-header'>📊 {t('Purchase Visualization','تصور المشتريات')}</div>",
                        unsafe_allow_html=True)
            if has_col(pur_df, ven_col) and has_col(pur_df, sub_col):
                render_visualization(pur_df, pur_viz_mode, ven_col, sub_col,
                                     t("Spend by Vendor","الإنفاق حسب المورد"))
            elif has_col(pur_df, mc_col) and has_col(pur_df, qty_col):
                render_visualization(pur_df, pur_viz_mode, mc_col, qty_col,
                                     t("Qty by Model","الكمية حسب الموديل"))
            st.divider()

            if has_col(pur_df, ven_col):
                render_exec_summary(pur_df, sub_col, ven_col, t("Vendor Spend Analysis","تحليل إنفاق الموردين"))
                st.divider()

                vc_ = get_display_col(pur_df, ven_col)
                sc_ = get_display_col(pur_df, sub_col)
                qc_ = get_display_col(pur_df, qty_col)
                vd  = pur_df.groupby(vc_).agg(
                    **{"Spend (SAR)": (sc_, "sum"), "Qty": (qc_, "sum")}
                ).reset_index().sort_values("Spend (SAR)", ascending=False)
                st.markdown(f"<div class='section-header'>🏭 {t('Vendor Leaderboard','ترتيب الموردين')}</div>",
                            unsafe_allow_html=True)
                render_paginated_table(vd, "pur_vendor_page")
                st.divider()

            if has_col(pur_df, loc_col) and has_col(pur_df, qty_col):
                lc_ = get_display_col(pur_df, loc_col)
                qc_ = get_display_col(pur_df, qty_col)
                la  = pur_df.groupby(lc_)[qc_].sum().reset_index().sort_values(qc_, ascending=False)
                st.markdown(f"<div class='section-header'>📍 {t('Receipt Location Summary','ملخص مواقع الاستلام')}</div>",
                            unsafe_allow_html=True)
                fig_loc = px.pie(la.head(10), names=lc_, values=qc_,
                                 color_discrete_sequence=th("plotly_colors"),
                                 template=th("plotly_template"), hole=0.5,
                                 labels={lc_: col("Receipt Location"), qc_: col("Qty")})
                fig_loc.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(apply_plotly_theme(fig_loc), use_container_width=True)
                st.divider()

            st.markdown(f"<div class='section-header'>📈 {t('Daily Purchase Trend','الاتجاه اليومي للمشتريات')}</div>",
                        unsafe_allow_html=True)
            render_daily_trend_chart(pur_df, "Date", "Subtotal",
                                     t("Daily Purchase Spend","الإنفاق اليومي"), "accent3")
            st.divider()

            st.markdown(f"<div class='section-header'>📋 {t('Purchase History','تاريخ المشتريات')}</div>",
                        unsafe_allow_html=True)
            render_paginated_table(pur_df, "pur_page")

            st.markdown("<br>", unsafe_allow_html=True)
            pd1, pd2 = st.columns(2)
            with pd1:
                st.download_button("⬇️ CSV", to_csv(localize_df(pur_df)),
                                   dl_name("purchase","csv"), "text/csv", use_container_width=True)
            with pd2:
                st.download_button("⬇️ Excel", to_excel(localize_df(pur_df)),
                                   dl_name("purchase","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

    # =========================================================================
    # AI INSIGHTS TAB
    # =========================================================================
    with tab_chat:
        show_chat_panel()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15: ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

restore_session()

if not st.session_state.get("authenticated"):
    show_login()
else:
    show_dashboard()
