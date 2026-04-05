# app.py – COMPLETE POLISHED VERSION
# Multi-Company Odoo Operations Dashboard
# Features: Inventory, POS, Sales, Purchase, Visualization Modes, Theme Switcher, AI Chat Panel

import io
import re
import hashlib
import time
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Multi‑Company Ops Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Dark": {
        "bg": "linear-gradient(135deg,#0f0c29,#302b63,#24243e)",
        "sidebar_bg": "linear-gradient(180deg,#1a1a2e 0%,#16213e 100%)",
        "card_bg": "linear-gradient(145deg,#1e1e3f,#2d2b55)",
        "accent1": "#667eea",
        "accent2": "#f093fb",
        "accent3": "#43e97b",
        "text": "#e8e8ff",
        "text_muted": "#a0aec0",
        "text_label": "#c4b5fd",
        "border": "#ffffff18",
        "input_bg": "#1e1e3f",
        "metric_gradient": "linear-gradient(90deg,#667eea,#f093fb)",
        "tab_active": "linear-gradient(90deg,#667eea,#764ba2)",
        "title_gradient": "linear-gradient(90deg,#667eea,#f093fb,#43e97b,#667eea)",
        "button_gradient": "linear-gradient(90deg,#667eea,#764ba2,#f093fb,#667eea)",
        "chat_bg": "#1a1a2e",
        "chat_user_bg": "linear-gradient(135deg,#667eea,#764ba2)",
        "chat_bot_bg": "linear-gradient(135deg,#2d2b55,#1e1e3f)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#667eea","#f093fb","#43e97b","#f6d365","#fda085","#a18cd1","#96fbc4"],
    },
    "Light": {
        "bg": "linear-gradient(135deg,#f0f4ff,#ffffff,#f8f0ff)",
        "sidebar_bg": "linear-gradient(180deg,#ffffff 0%,#f0f4ff 100%)",
        "card_bg": "linear-gradient(145deg,#ffffff,#f8f8ff)",
        "accent1": "#4f46e5",
        "accent2": "#9333ea",
        "accent3": "#16a34a",
        "text": "#1e1b4b",
        "text_muted": "#6b7280",
        "text_label": "#4f46e5",
        "border": "#e5e7eb",
        "input_bg": "#ffffff",
        "metric_gradient": "linear-gradient(90deg,#4f46e5,#9333ea)",
        "tab_active": "linear-gradient(90deg,#4f46e5,#7c3aed)",
        "title_gradient": "linear-gradient(90deg,#4f46e5,#9333ea,#16a34a,#4f46e5)",
        "button_gradient": "linear-gradient(90deg,#4f46e5,#7c3aed,#9333ea,#4f46e5)",
        "chat_bg": "#f9fafb",
        "chat_user_bg": "linear-gradient(135deg,#4f46e5,#7c3aed)",
        "chat_bot_bg": "linear-gradient(135deg,#f3f4f6,#e5e7eb)",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#4f46e5","#9333ea","#16a34a","#d97706","#dc2626","#0891b2","#7c3aed"],
    },
    "Luxury": {
        "bg": "linear-gradient(135deg,#0a0800,#1a1400,#0d0a00)",
        "sidebar_bg": "linear-gradient(180deg,#0f0c00 0%,#1a1400 100%)",
        "card_bg": "linear-gradient(145deg,#1a1400,#2a2000)",
        "accent1": "#d4af37",
        "accent2": "#f5c842",
        "accent3": "#c8a415",
        "text": "#f5e6c8",
        "text_muted": "#a89060",
        "text_label": "#d4af37",
        "border": "#d4af3722",
        "input_bg": "#1a1400",
        "metric_gradient": "linear-gradient(90deg,#d4af37,#f5c842)",
        "tab_active": "linear-gradient(90deg,#d4af37,#c8a415)",
        "title_gradient": "linear-gradient(90deg,#d4af37,#f5c842,#fff7d4,#d4af37)",
        "button_gradient": "linear-gradient(90deg,#d4af37,#c8a415,#f5c842,#d4af37)",
        "chat_bg": "#0a0800",
        "chat_user_bg": "linear-gradient(135deg,#d4af37,#c8a415)",
        "chat_bot_bg": "linear-gradient(135deg,#2a2000,#1a1400)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#d4af37","#f5c842","#c8a415","#fff7d4","#a89060","#8b7536","#f0e68c"],
    },
    "Glass": {
        "bg": "linear-gradient(135deg,#0a0a1a 0%,#1a0a2e 50%,#0a1a2e 100%)",
        "sidebar_bg": "linear-gradient(180deg,rgba(255,255,255,0.05) 0%,rgba(255,255,255,0.02) 100%)",
        "card_bg": "linear-gradient(145deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04))",
        "accent1": "#00d4ff",
        "accent2": "#ff6b9d",
        "accent3": "#00ff88",
        "text": "#ffffff",
        "text_muted": "#aaaacc",
        "text_label": "#00d4ff",
        "border": "rgba(255,255,255,0.15)",
        "input_bg": "rgba(255,255,255,0.08)",
        "metric_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d)",
        "tab_active": "linear-gradient(90deg,rgba(0,212,255,0.3),rgba(255,107,157,0.3))",
        "title_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d,#00ff88,#00d4ff)",
        "button_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d,#00ff88,#00d4ff)",
        "chat_bg": "rgba(0,0,0,0.4)",
        "chat_user_bg": "linear-gradient(135deg,rgba(0,212,255,0.3),rgba(255,107,157,0.3))",
        "chat_bot_bg": "linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04))",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#00d4ff","#ff6b9d","#00ff88","#ffd700","#ff6b35","#a855f7","#34d399"],
    },
}

def get_theme():
    return st.session_state.get("theme", "Dark")

def th(key):
    return THEMES[get_theme()][key]

def build_css(t):
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,html,body,[class*="css"]{{font-family:'IBM Plex Sans Arabic','Space Grotesk',sans-serif;box-sizing:border-box;}}
.stApp{{background:{t["bg"]};min-height:100vh;}}
section[data-testid="stSidebar"]{{background:{t["sidebar_bg"]}!important;border-right:1px solid {t["border"]};backdrop-filter:blur(20px);}}
section[data-testid="stSidebar"] *,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] div{{color:{t["text"]}!important;}}
section[data-testid="stSidebar"] input{{color:{t["input_bg"]}!important;}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInDown{{from{{opacity:0;transform:translateY(-30px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes bounceIn{{0%{{transform:scale(0.2) rotate(-10deg);opacity:0}}60%{{transform:scale(1.2) rotate(5deg);opacity:1}}80%{{transform:scale(0.9)}}100%{{transform:scale(1);opacity:1}}}}
@keyframes shimmer{{0%{{background-position:-400% center}}100%{{background-position:400% center}}}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 {t["accent1"]}44}}50%{{box-shadow:0 0 20px 8px {t["accent1"]}22}}}}
@keyframes glow{{0%,100%{{text-shadow:0 0 10px {t["accent1"]}88}}50%{{text-shadow:0 0 30px {t["accent2"]}cc,0 0 60px {t["accent1"]}88}}}}
@keyframes slideInLeft{{from{{opacity:0;transform:translateX(-40px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes slideInRight{{from{{opacity:0;transform:translateX(40px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
@keyframes btnShine{{0%{{background-position:-200% center}}100%{{background-position:200% center}}}}
@keyframes countUp{{from{{opacity:0;transform:scale(0.5)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes chatSlideIn{{from{{opacity:0;transform:translateX(20px)}}to{{opacity:1;transform:translateX(0)}}}}
.login-orb{{width:120px;height:120px;border-radius:50%;background:{t["button_gradient"]};display:flex;align-items:center;justify-content:center;font-size:3rem;margin:0 auto 20px;animation:float 3s ease-in-out infinite,bounceIn 1s ease forwards;box-shadow:0 8px 40px {t["accent1"]}66,0 0 60px {t["accent2"]}33;}}
.login-title{{font-size:2.4rem;font-weight:700;background:{t["title_gradient"]};background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s linear infinite,fadeInDown 0.8s ease forwards;text-align:center;margin-bottom:6px;}}
.login-subtitle{{color:{t["text_label"]}!important;font-size:0.95rem;text-align:center;animation:fadeInUp 1s ease forwards;margin-bottom:28px;}}
.login-card{{background:{t["card_bg"]};border:1px solid {t["border"]};border-radius:20px;padding:32px 36px;width:100%;animation:fadeInUp 0.9s ease forwards,pulse 3s infinite;backdrop-filter:blur(20px);}}
.stTextInput input,.stNumberInput input,.stTextArea textarea{{background:{t["input_bg"]}!important;border:1px solid {t["accent1"]}66!important;border-radius:10px!important;color:{t["text"]}!important;caret-color:{t["text_label"]}!important;transition:all 0.3s ease!important;}}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{{border-color:{t["accent1"]}!important;box-shadow:0 0 0 3px {t["accent1"]}33!important;}}
.stTextInput label,.stNumberInput label,.stTextArea label{{color:{t["text_label"]}!important;font-weight:600!important;}}
.stFormSubmitButton button,.stButton button[kind="primary"]{{background:{t["button_gradient"]}!important;background-size:300% auto!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important;font-size:1rem!important;padding:12px!important;animation:btnShine 3s linear infinite!important;transition:transform 0.2s,box-shadow 0.2s!important;box-shadow:0 4px 20px {t["accent1"]}55!important;}}
.stFormSubmitButton button:hover,.stButton button[kind="primary"]:hover{{transform:translateY(-2px) scale(1.02)!important;box-shadow:0 8px 30px {t["accent1"]}99!important;}}
.stButton button[kind="secondary"]{{background:{t["card_bg"]}!important;border:1px solid {t["accent1"]}66!important;color:{t["text_label"]}!important;border-radius:10px!important;}}
.stButton button[kind="secondary"]:hover{{background:{t["tab_active"]}!important;color:white!important;}}
.stButton button{{color:{t["text_label"]}!important;}}
.stDownloadButton button{{background:{t["card_bg"]}!important;border:1px solid {t["accent1"]}66!important;border-radius:10px!important;color:{t["text_label"]}!important;font-size:0.78rem!important;font-weight:600!important;padding:6px 14px!important;transition:all 0.25s ease!important;}}
.stDownloadButton button:hover{{background:{t["tab_active"]}!important;color:white!important;border-color:transparent!important;transform:translateY(-2px) scale(1.04)!important;}}
.dash-header{{text-align:center;padding:16px 0 24px;animation:fadeInDown 0.6s ease forwards;}}
.dash-title{{font-size:2.4rem;font-weight:700;background:{t["title_gradient"]};background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 4s linear infinite,glow 3s ease-in-out infinite;}}
.dash-subtitle{{color:{t["text_muted"]};font-size:0.95rem;margin-top:-4px;}}
[data-testid="stMetric"]{{background:{t["card_bg"]}!important;border:1px solid {t["border"]}!important;border-radius:16px!important;padding:16px 20px!important;animation:countUp 0.6s ease forwards;transition:transform 0.2s,box-shadow 0.2s;backdrop-filter:blur(10px);}}
[data-testid="stMetric"]:hover{{transform:translateY(-4px);box-shadow:0 8px 30px {t["accent1"]}44;}}
[data-testid="stMetricLabel"]{{color:{t["text_muted"]}!important;font-size:0.82rem!important;}}
[data-testid="stMetricValue"]{{font-size:1.7rem!important;font-weight:700!important;background:{t["metric_gradient"]};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.stTabs [data-baseweb="tab-list"]{{background:{t["card_bg"]};border-radius:12px;padding:4px;gap:4px;border:1px solid {t["border"]};}}
.stTabs [data-baseweb="tab"]{{color:{t["text_muted"]}!important;border-radius:10px!important;font-size:0.83rem!important;font-weight:600!important;padding:8px 16px!important;transition:all 0.2s ease!important;}}
.stTabs [aria-selected="true"]{{background:{t["tab_active"]}!important;color:white!important;box-shadow:0 4px 12px {t["accent1"]}55!important;}}
.info-banner{{background:linear-gradient(135deg,{t["accent1"]}22,{t["accent1"]}11);border-left:4px solid {t["accent1"]};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{t["text"]}!important;animation:slideInLeft 0.4s ease;}}
.warn-banner{{background:linear-gradient(135deg,#f59e0b22,#f59e0b11);border-left:4px solid #f59e0b;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#fcd34d!important;}}
.alert-banner{{background:linear-gradient(135deg,#f43f5e22,#f43f5e11);border-left:4px solid #f43f5e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{t["text"]}!important;animation:pulse 2s infinite;}}
.ok-banner{{background:linear-gradient(135deg,#22c55e22,#22c55e11);border-left:4px solid #22c55e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#86efac!important;}}
.snap-card{{background:{t["card_bg"]};border:1px solid {t["border"]};border-radius:14px;padding:16px 20px;font-size:0.87rem;color:{t["text"]}!important;line-height:2;animation:slideInRight 0.5s ease;box-shadow:0 4px 20px #00000055;backdrop-filter:blur(10px);}}
.snap-card b{{color:{t["text_label"]}!important;}}
.badge-ok{{background:linear-gradient(90deg,#065f46,#047857);color:#d1fae5!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}}
.badge-off{{background:linear-gradient(90deg,#991b1b,#b91c1c);color:#fee2e2!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}}
.stRadio label,.stRadio div[role="radiogroup"] label span,[data-testid="stToggle"] label,.stCheckbox label{{color:{t["text"]}!important;}}
div[data-testid="stRadio"] p{{color:{t["text"]}!important;}}
h1,h2,h3,h4,h5,h6{{color:{t["text"]}!important;}}
.stMarkdown p,.stMarkdown li{{color:{t["text_label"]}!important;}}
.stCaption,[data-testid="stCaptionContainer"] p{{color:{t["text_muted"]}!important;}}
.stAlert p{{color:#1a1a2e!important;font-weight:600;}}
[data-testid="stExpander"]{{background:{t["card_bg"]}!important;border:1px solid {t["border"]}!important;border-radius:12px!important;}}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{{color:{t["text_label"]}!important;}}
[data-testid="stFileUploader"]{{background:{t["card_bg"]}!important;border:2px dashed {t["accent1"]}66!important;border-radius:14px!important;}}
hr{{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,{t["accent1"]}66,transparent)!important;margin:16px 0!important;}}
[data-testid="stProgressBar"]>div{{background:{t["button_gradient"]}!important;border-radius:10px!important;}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:{t["card_bg"]};}}
::-webkit-scrollbar-thumb{{background:{t["tab_active"]};border-radius:10px;}}
.stNumberInput button{{color:{t["text_label"]}!important;background:{t["card_bg"]}!important;}}
footer{{visibility:hidden;}}
[data-baseweb="tag"]{{background:{t["accent1"]}33!important;color:{t["text_label"]}!important;}}
[data-baseweb="select"] div{{background:{t["input_bg"]}!important;color:{t["text"]}!important;border-color:{t["accent1"]}55!important;}}
.dataframe{{font-family:'IBM Plex Sans Arabic',sans-serif;border-collapse:collapse;width:100%;background:{t["card_bg"]};color:{t["text"]};border-radius:12px;overflow:hidden;}}
.dataframe th{{background:{t["tab_active"]};color:white;padding:10px 12px;text-align:center;font-weight:600;}}
.dataframe td{{padding:8px 12px;text-align:center;border-bottom:1px solid {t["border"]};}}
.dataframe tr:hover{{background:{t["accent1"]}11;}}
.chat-container{{background:{t["chat_bg"]};border:1px solid {t["border"]};border-radius:16px;padding:16px;max-height:400px;overflow-y:auto;margin-bottom:12px;backdrop-filter:blur(10px);}}
.chat-msg-user{{background:{t["chat_user_bg"]};color:white;border-radius:12px 12px 4px 12px;padding:10px 14px;margin:6px 0 6px 40px;font-size:0.88rem;animation:chatSlideIn 0.3s ease;box-shadow:0 2px 8px {t["accent1"]}33;}}
.chat-msg-bot{{background:{t["chat_bot_bg"]};color:{t["text"]};border:1px solid {t["border"]};border-radius:12px 12px 12px 4px;padding:10px 14px;margin:6px 40px 6px 0;font-size:0.88rem;animation:chatSlideIn 0.3s ease;}}
.chat-label-user{{text-align:right;font-size:0.72rem;color:{t["text_muted"]};margin-bottom:2px;}}
.chat-label-bot{{text-align:left;font-size:0.72rem;color:{t["text_muted"]};margin-bottom:2px;}}
.kpi-tile{{background:{t["card_bg"]};border:1px solid {t["border"]};border-radius:14px;padding:20px;text-align:center;animation:countUp 0.6s ease forwards;transition:all 0.3s ease;backdrop-filter:blur(10px);}}
.kpi-tile:hover{{transform:translateY(-6px);box-shadow:0 12px 40px {t["accent1"]}44;border-color:{t["accent1"]}66;}}
.kpi-tile .kpi-value{{font-size:2rem;font-weight:700;background:{t["metric_gradient"]};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.kpi-tile .kpi-label{{font-size:0.8rem;color:{t["text_muted"]};margin-top:4px;}}
.kpi-tile .kpi-icon{{font-size:1.8rem;margin-bottom:8px;}}
.viz-selector{{background:{t["card_bg"]};border:1px solid {t["border"]};border-radius:12px;padding:12px 16px;margin-bottom:16px;}}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]

VIZ_MODES = [
    "📋 Table", "📊 Bar Chart", "📈 Line Chart", "🍕 Pie Chart",
    "🍩 Donut Chart", "📉 Area Chart", "🔘 Scatter Chart", "🏆 KPI Tiles",
    "🗂️ Funnel Chart", "📡 Radar Chart", "🔺 Pyramid", "📊 Stacked Bar",
]

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    return ar if get_lang() == "AR" else en

def get_system_name(key):
    cfg = st.secrets.get(key, {})
    return cfg.get("name_ar", cfg.get("name", key)) if get_lang() == "AR" else cfg.get("name", key)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
_DEF = {
    "authenticated": False,
    "user_email": "",
    "lang": "EN",
    "theme": "Dark",
    "inventory_df": None,
    "inventory_branch_df": None,
    "pos_df": None,
    "sales_df": None,
    "purchase_df": None,
    "chat_history": [],
    "inv_viz_mode": "📋 Table",
    "pos_viz_mode": "📋 Table",
    "sales_viz_mode": "📋 Table",
    "pur_viz_mode": "📋 Table",
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# SESSION LOGIN RESTORE
# ─────────────────────────────────────────────────────────────────────────────
_COOKIE_SECRET = "swag_2025_secure"

def _make_token(email):
    return hashlib.sha256(f"{_COOKIE_SECRET}_{email}".encode()).hexdigest()[:32]

def _verify_token(email, token):
    return bool(email and token and token == _make_token(email))

def restore_session():
    if st.session_state.get("authenticated"):
        return
    try:
        params = st.query_params
        email = params.get("u", "")
        token = params.get("t", "")
        if email and token and _verify_token(email, token):
            st.session_state.authenticated = True
            st.session_state.user_email = email
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# XML-RPC HELPERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def _proxy(url, ep):
    return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{ep}", allow_none=True)

@st.cache_data(ttl=28800, show_spinner=False)
def _auth(url, db, user, key):
    try:
        uid = _proxy(url, "common").authenticate(db, user, key, {})
        return uid or None
    except Exception:
        return None

def _x(url, db, uid, key, model, method, domain, kw):
    return _proxy(url, "object").execute_kw(db, uid, key, model, method, domain, kw)

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def localize_columns(df):
    if df is None or df.empty:
        return df
    rename_map = {
        "System": t("System", "النظام"),
        "Model Code": t("Model Code", "رمز الموديل"),
        "Product": t("Product", "المنتج"),
        "Sale Price": t("Sale Price", "سعر البيع"),
        "On Hand": t("On Hand", "متوفر"),
        "Branch": t("Branch", "الفرع"),
        "Location": t("Location", "الموقع"),
        "Date": t("Date", "التاريخ"),
        "POS Order": t("POS Order", "طلب نقطة بيع"),
        "Customer": t("Customer", "العميل"),
        "Cashier": t("Cashier", "الكاشير"),
        "Category": t("Category", "الفئة"),
        "Qty": t("Qty", "الكمية"),
        "Unit Price": t("Unit Price", "سعر الوحدة"),
        "Subtotal": t("Subtotal", "المجموع الفرعي"),
        "SO": t("SO", "أمر بيع"),
        "Vendor": t("Vendor", "المورد"),
        "Receipt Location": t("Receipt Location", "موقع الاستلام"),
        "Purchase Qty": t("Purchase Qty", "كمية الشراء"),
        "Order ID": t("Order ID", "رقم الطلب"),
        "Total Amount": t("Total Amount", "المبلغ الإجمالي"),
        "Bill Number": t("Bill Number", "رقم الفاتورة"),
    }
    to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
    return df.rename(columns=to_rename)

def prepare_df(df):
    if df is None or df.empty:
        return df
    df = localize_columns(df)
    if "_status" in df.columns:
        df = df.drop(columns=["_status"])
    numeric_cols = [
        "On Hand", "Sale Price", "Qty", "Unit Price", "Subtotal", "Purchase Qty",
        t("On Hand", "متوفر"), t("Sale Price", "سعر البيع"),
        t("Qty", "الكمية"), t("Unit Price", "سعر الوحدة"),
        t("Subtotal", "المجموع الفرعي"), "Total Amount", t("Total Amount", "المبلغ الإجمالي"),
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        try:
            from openpyxl.styles import Font, Alignment
            ws = writer.sheets["Data"]
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
        except Exception:
            pass
    return output.getvalue()

def to_excel_branch_matrix(branch_df):
    if branch_df is None or branch_df.empty:
        return b""
    branch_df = localize_columns(branch_df)
    branch_col = t("Branch", "الفرع")
    model_col = t("Model Code", "رمز الموديل")
    qty_col = t("On Hand", "متوفر")
    if branch_col not in branch_df.columns or model_col not in branch_df.columns:
        return b""
    pivot = branch_df.pivot_table(
        index=model_col, columns=branch_col, values=qty_col,
        aggfunc="sum", fill_value=0,
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pivot.to_excel(writer, sheet_name="Branch_Matrix")
        try:
            from openpyxl.styles import Font, Alignment, PatternFill
            ws = writer.sheets["Branch_Matrix"]
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
        except Exception:
            pass
    return output.getvalue()

def dl_name(prefix, ext):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# TABLE DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
def _render_html_table(df, max_rows=1000):
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data to display.','لا توجد بيانات للعرض.')}</div>", unsafe_allow_html=True)
        return
    table_css = f"""
    <style>
    .dataframe{{font-family:'IBM Plex Sans Arabic',sans-serif;border-collapse:collapse;width:100%;
    background:{th("card_bg")};color:{th("text")};border-radius:12px;overflow:hidden;}}
    .dataframe th{{background:{th("tab_active")};color:white;padding:10px 12px;text-align:center;font-weight:600;}}
    .dataframe td{{padding:8px 12px;text-align:center;border-bottom:1px solid {th("border")};}}
    .dataframe tr:hover{{background:{th("accent1")}11;}}
    </style>
    """
    st.markdown(table_css, unsafe_allow_html=True)
    st.markdown(
        df.head(max_rows).to_html(classes="dataframe", index=False, escape=False),
        unsafe_allow_html=True,
    )
    if len(df) > max_rows:
        st.caption(f"Showing first {max_rows} of {len(df)} rows.")

def display_df(df, thresh=None):
    if df is None or df.empty:
        return df
    filtered_df = df.copy()
    if thresh is not None and isinstance(thresh, (int, float)):
        on_hand_col = None
        for col in ["On Hand", t("On Hand", "متوفر")]:
            if col in filtered_df.columns:
                on_hand_col = col
                break
        if on_hand_col:
            filtered_df[on_hand_col] = pd.to_numeric(filtered_df[on_hand_col], errors="coerce").fillna(0)
            filtered_df = filtered_df[filtered_df[on_hand_col] <= thresh]
    _render_html_table(filtered_df)
    return filtered_df

# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def render_visualization(df, viz_mode, x_col, y_col, label=None):
    """Universal visualization renderer based on selected mode."""
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data available for visualization.','لا توجد بيانات متاحة للتصور.')}</div>", unsafe_allow_html=True)
        return

    colors = th("plotly_colors")
    tmpl = th("plotly_template")
    paper_bg = "rgba(0,0,0,0)"
    plot_bg = "rgba(0,0,0,0)"

    def apply_theme(fig):
        fig.update_layout(
            paper_bgcolor=paper_bg,
            plot_bgcolor=plot_bg,
            font=dict(color=th("text"), family="IBM Plex Sans Arabic"),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    if x_col not in df.columns or y_col not in df.columns:
        st.warning(f"Columns not found: {x_col}, {y_col}")
        return

    df_plot = df.copy()
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce").fillna(0)
    df_plot = df_plot.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False)

    if viz_mode == "📋 Table":
        _render_html_table(df)

    elif viz_mode == "📊 Bar Chart":
        fig = px.bar(df_plot.head(20), x=x_col, y=y_col, title=label or "",
                     color=y_col, color_continuous_scale=["#667eea", "#f093fb"],
                     template=tmpl)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "📈 Line Chart":
        fig = px.line(df_plot.head(30), x=x_col, y=y_col, title=label or "",
                      markers=True, template=tmpl,
                      color_discrete_sequence=[th("accent1")])
        fig.update_traces(line_width=3, marker_size=8)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "🍕 Pie Chart":
        top_n = df_plot.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, title=label or "",
                     color_discrete_sequence=colors, template=tmpl)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "🍩 Donut Chart":
        top_n = df_plot.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, hole=0.5,
                     title=label or "", color_discrete_sequence=colors, template=tmpl)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "📉 Area Chart":
        fig = px.area(df_plot.head(30), x=x_col, y=y_col, title=label or "",
                      template=tmpl, color_discrete_sequence=[th("accent1")])
        fig.update_traces(fillcolor=f"{th('accent1')}44", line_color=th("accent1"))
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "🔘 Scatter Chart":
        fig = px.scatter(df_plot.head(30), x=x_col, y=y_col, title=label or "",
                         size=y_col, color=y_col,
                         color_continuous_scale=["#667eea", "#f093fb"], template=tmpl)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "🏆 KPI Tiles":
        top_n = df_plot.head(8)
        cols = st.columns(min(4, len(top_n)))
        for i, (_, row) in enumerate(top_n.iterrows()):
            with cols[i % 4]:
                val = row[y_col]
                name = str(row[x_col])[:20]
                st.markdown(f"""
                <div class='kpi-tile'>
                  <div class='kpi-icon'>📦</div>
                  <div class='kpi-value'>{val:,.0f}</div>
                  <div class='kpi-label'>{name}</div>
                </div>
                """, unsafe_allow_html=True)

    elif viz_mode == "🗂️ Funnel Chart":
        top_n = df_plot.head(10)
        fig = go.Figure(go.Funnel(
            y=top_n[x_col].astype(str),
            x=top_n[y_col],
            textinfo="value+percent initial",
            marker_color=colors[:len(top_n)],
        ))
        fig.update_layout(title=label or "")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "📡 Radar Chart":
        top_n = df_plot.head(8)
        cats = top_n[x_col].astype(str).tolist()
        vals = top_n[y_col].tolist()
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=cats + [cats[0]],
            fill='toself',
            fillcolor=f"{th('accent1')}44",
            line_color=th("accent1"),
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)), title=label or "")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "🔺 Pyramid":
        top_n = df_plot.head(10).sort_values(y_col)
        fig = px.bar(top_n, x=y_col, y=x_col, orientation='h',
                     title=label or "", template=tmpl,
                     color=y_col, color_continuous_scale=["#667eea", "#f093fb"])
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    elif viz_mode == "📊 Stacked Bar":
        if "System" in df.columns or t("System","النظام") in df.columns:
            sys_col = t("System", "النظام") if t("System","النظام") in df.columns else "System"
            df_stack = df.groupby([x_col, sys_col])[y_col].sum().reset_index()
            fig = px.bar(df_stack, x=x_col, y=y_col, color=sys_col,
                         title=label or "", barmode="stack", template=tmpl,
                         color_discrete_sequence=colors)
            st.plotly_chart(apply_theme(fig), use_container_width=True)
        else:
            fig = px.bar(df_plot.head(20), x=x_col, y=y_col, title=label or "",
                         template=tmpl, color_discrete_sequence=colors)
            st.plotly_chart(apply_theme(fig), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# VIZ MODE SELECTOR
# ─────────────────────────────────────────────────────────────────────────────
def viz_mode_selector(key):
    st.markdown(f"<div class='viz-selector'>", unsafe_allow_html=True)
    mode = st.selectbox(
        f"📊 {t('Visualization Mode','نمط العرض')}",
        VIZ_MODES,
        index=VIZ_MODES.index(st.session_state.get(key, "📋 Table")),
        key=key,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return mode

# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_inventory_cached(codestuple=(), exact=False):
    all_rows = []
    all_branch_rows = []

    for key in SYSTEM_KEYS:
        cfg = st.secrets.get(key)
        if not cfg:
            continue
        uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
        if not uid:
            continue

        u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]
        system_name = get_system_name(key)

        try:
            prod_domain = []
            if codestuple:
                if exact:
                    prod_domain = [("default_code", "in", list(codestuple))]
                else:
                    clauses = [("default_code", "=ilike", f"{c}%") for c in codestuple]
                    prod_domain = ([clauses[0]] if len(clauses) == 1
                                   else ["|"] * (len(clauses) - 1) + clauses)

            products = _x(u, db, uid, ak, "product.template", "search_read",
                          [prod_domain] if prod_domain else [[]],
                          {"fields": ["id", "name", "default_code", "list_price", "categ_id"],
                           "limit": 5000})
            if not products:
                continue

            prod_ids = [p["id"] for p in products]
            tmpl_to_model = {p["id"]: (p.get("default_code") or "").strip() for p in products}
            tmpl_to_name = {p["id"]: p.get("name", "") for p in products}
            tmpl_to_price = {p["id"]: float(p.get("list_price") or 0) for p in products}

            quants = _x(u, db, uid, ak, "stock.quant", "search_read",
                        [[("product_id.product_tmpl_id", "in", prod_ids),
                          ("location_id.usage", "=", "internal")]],
                        {"fields": ["product_id", "location_id", "quantity",
                                    "product_id.product_tmpl_id"],
                         "limit": 50000})

            tmpl_qty: dict = {}
            for q in quants:
                tmpl_id_raw = q.get("product_id.product_tmpl_id")
                if isinstance(tmpl_id_raw, list):
                    tmpl_id = tmpl_id_raw[0]
                else:
                    pid_raw = q.get("product_id")
                    tmpl_id = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
                qty = float(q.get("quantity") or 0)
                tmpl_qty[tmpl_id] = tmpl_qty.get(tmpl_id, 0) + qty

                loc = q.get("location_id")
                loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
                model_code = tmpl_to_model.get(tmpl_id, "")
                if model_code:
                    all_branch_rows.append({
                        "System": system_name,
                        "Branch": loc_name,
                        "Model Code": model_code,
                        "On Hand": qty,
                    })

            for tmpl_id in prod_ids:
                all_rows.append({
                    "System": system_name,
                    "Model Code": tmpl_to_model.get(tmpl_id, ""),
                    "Product": tmpl_to_name.get(tmpl_id, ""),
                    "Sale Price": tmpl_to_price.get(tmpl_id, 0),
                    "On Hand": tmpl_qty.get(tmpl_id, 0),
                    "_status": "OK",
                })
        except Exception:
            continue

    total_df = (pd.DataFrame(all_rows) if all_rows
                else pd.DataFrame(columns=["System", "Model Code", "Product", "Sale Price", "On Hand", "_status"]))
    branch_df = (pd.DataFrame(all_branch_rows)[["System", "Branch", "Model Code", "On Hand"]]
                 if all_branch_rows
                 else pd.DataFrame(columns=["System", "Branch", "Model Code", "On Hand"]))

    return total_df, branch_df

def fetch_inventory_data(codestuple=(), exact=False):
    return fetch_inventory_cached(codestuple=codestuple, exact=exact)

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_for_system(system_key, model_code, date_from, date_to):
    _empty_cols = ["Date", "PO", "Vendor", "Receipt Location", "Category",
                   "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "System"]
    empty_df = pd.DataFrame(columns=_empty_cols)

    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        po_domain = [
            ["date_approve", ">=", f"{date_from} 00:00:00"],
            ["date_approve", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["purchase", "done"]],
        ]
        pos = _x(u, db, uid, ak, "purchase.order", "search_read", [po_domain],
                 {"fields": ["id", "name", "partner_id", "date_approve", "state"],
                  "limit": 2000})
        if not pos:
            return empty_df

        po_ids = [p["id"] for p in pos]
        po_map = {p["id"]: p for p in pos}

        lines = _x(u, db, uid, ak, "purchase.order.line", "search_read",
                   [[["order_id", "in", po_ids]]],
                   {"fields": ["order_id", "product_id", "product_qty",
                               "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        prod_ids = list({l["product_id"][0] for l in lines
                         if isinstance(l.get("product_id"), list)})
        products = _x(u, db, uid, ak, "product.product", "search_read",
                      [[["id", "in", prod_ids]]],
                      {"fields": ["id", "default_code", "name", "categ_id"],
                       "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        pickings = _x(u, db, uid, ak, "stock.picking", "search_read",
                      [[["origin", "in", [p["name"] for p in pos]],
                        ["picking_type_code", "=", "incoming"]]],
                      {"fields": ["origin", "location_dest_id"], "limit": 2000})
        receipt_map: dict = {}
        for pick in pickings:
            loc = pick.get("location_dest_id")
            loc_name = (loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc) if loc else "")
            receipt_map[pick.get("origin", "")] = loc_name

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            po = po_map.get(oid, {})
            if not po:
                continue
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})
            model_code_val = (prod.get("default_code") or "").strip()
            if model_code and model_code_val:
                if not model_code_val.upper().startswith(model_code.upper()):
                    continue
            receipt_loc = receipt_map.get(po.get("name", ""), "")
            categ_obj = prod.get("categ_id")
            category = (categ_obj[1] if isinstance(categ_obj, list) and len(categ_obj) > 1 else "")
            partner_obj = po.get("partner_id")
            vendor = (partner_obj[1] if isinstance(partner_obj, list) and len(partner_obj) > 1 else "")
            rows.append({
                "System": system_name,
                "Date": str(po.get("date_approve", ""))[:10],
                "PO": po.get("name", ""),
                "Vendor": vendor,
                "Receipt Location": receipt_loc,
                "Category": category,
                "Model Code": model_code_val,
                "Product": prod.get("name", ""),
                "Qty": float(line.get("product_qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_purchase_multi(selected_keys, model_code, date_from, date_to):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_purchase_for_system, k, model_code, date_from, date_to): k
                for k in selected_keys}
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True)

@st.cache_data(ttl=3600, show_spinner=False)
def get_purchase_summary_by_model(model_codes_tuple, date_from, date_to):
    if not model_codes_tuple:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])
    swag_cfg = st.secrets.get("SWAG")
    if not swag_cfg:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])
    uid = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
    if not uid:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])
    try:
        domain = [
            ["order_id.date_approve", ">=", f"{date_from} 00:00:00"],
            ["order_id.date_approve", "<=", f"{date_to} 23:59:59"],
            ["order_id.state", "in", ["purchase", "done"]],
            ["product_id.default_code", "in", list(model_codes_tuple)],
        ]
        lines = _x(swag_cfg["url"], swag_cfg["db"], uid, swag_cfg["api_key"],
                   "purchase.order.line", "search_read", [domain],
                   {"fields": ["product_id", "product_qty"], "limit": 10000})
        if not lines:
            return pd.DataFrame(columns=["Model Code", "Purchase Qty"])
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _x(swag_cfg["url"], swag_cfg["db"], uid, swag_cfg["api_key"],
                      "product.product", "search_read", [[["id", "in", prod_ids]]],
                      {"fields": ["id", "default_code"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p.get("default_code", "") for p in products}
        summary: dict = {}
        for line in lines:
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            model = prod_map.get(pid, "")
            if model:
                summary[model] = summary.get(model, 0) + float(line.get("product_qty") or 0)
        return pd.DataFrame(list(summary.items()), columns=["Model Code", "Purchase Qty"])
    except Exception:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])

# ─────────────────────────────────────────────────────────────────────────────
# POS FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_pos_for_system(system_key, date_from, date_to, branch_filter, model_filter):
    empty_df = pd.DataFrame(columns=[
        "System", "Date", "POS Order", "Branch", "Customer", "Cashier",
        "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "Total Amount"
    ])
    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        order_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["paid", "done", "invoiced"]],
        ]
        orders = _x(u, db, uid, ak, "pos.order", "search_read", [order_domain],
                    {"fields": ["id", "name", "date_order", "amount_total", "user_id",
                                "session_id", "partner_id", "lines"],
                     "limit": 5000})
        if not orders:
            return empty_df

        session_ids = list({o["session_id"][0] for o in orders if o.get("session_id")})
        branch_map = {}
        if session_ids:
            sessions = _x(u, db, uid, ak, "pos.session", "search_read",
                          [[["id", "in", session_ids]]],
                          {"fields": ["id", "config_id"], "limit": len(session_ids) + 10})
            config_ids = list({s["config_id"][0] for s in sessions if s.get("config_id")})
            if config_ids:
                configs = _x(u, db, uid, ak, "pos.config", "search_read",
                             [[["id", "in", config_ids]]],
                             {"fields": ["id", "name"], "limit": len(config_ids) + 10})
                config_name = {c["id"]: c["name"] for c in configs}
                for s in sessions:
                    branch_map[s["id"]] = config_name.get(
                        s["config_id"][0] if isinstance(s.get("config_id"), list) else s.get("config_id"), "Unknown")

        line_ids = []
        for o in orders:
            if o.get("lines"):
                line_ids.extend(o["lines"])
        if not line_ids:
            return empty_df

        lines = _x(u, db, uid, ak, "pos.order.line", "search_read",
                   [[["id", "in", line_ids]]],
                   {"fields": ["order_id", "product_id", "qty", "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        order_map = {o["id"]: o for o in orders}

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = (_x(u, db, uid, ak, "product.product", "search_read",
                       [[["id", "in", prod_ids]]],
                       {"fields": ["id", "default_code", "name", "categ_id"],
                        "limit": len(prod_ids) + 20}) if prod_ids else [])
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id")
            order = order_map.get(oid)
            if not order:
                continue

            sess_id = order.get("session_id")
            sess_id = sess_id[0] if isinstance(sess_id, list) else sess_id
            branch_name = branch_map.get(sess_id, "Unknown")
            if branch_filter and branch_filter.strip():
                if branch_filter.lower() not in branch_name.lower():
                    continue

            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})
            model_code = (prod.get("default_code") or "").strip()
            if model_filter and model_filter.strip():
                if not model_code.upper().startswith(model_filter.upper()):
                    continue

            partner = order.get("partner_id")
            customer = (partner[1] if isinstance(partner, list) and len(partner) > 1 else "")
            user = order.get("user_id")
            cashier = (user[1] if isinstance(user, list) and len(user) > 1 else "")

            rows.append({
                "System": system_name,
                "Date": str(order.get("date_order", ""))[:10],
                "POS Order": order.get("name", ""),
                "Branch": branch_name,
                "Customer": customer,
                "Cashier": cashier,
                "Model Code": model_code,
                "Product": prod.get("name", ""),
                "Qty": float(line.get("qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_pos_multi(selected_keys, date_from, date_to, branch_filter, model_filter):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_pos_for_system, k, date_from, date_to, branch_filter, model_filter): k
                for k in selected_keys}
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# SALES FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sales_for_system(system_key, date_from, date_to, model_filter):
    empty_df = pd.DataFrame(columns=[
        "System", "Date", "SO", "Customer", "Model Code", "Product",
        "Qty", "Unit Price", "Subtotal", "Total Amount", "State"
    ])
    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        so_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["sale", "done"]],
        ]
        orders = _x(u, db, uid, ak, "sale.order", "search_read", [so_domain],
                    {"fields": ["id", "name", "date_order", "amount_total",
                                "partner_id", "state", "order_line"],
                     "limit": 5000})
        if not orders:
            return empty_df

        line_ids = []
        for o in orders:
            if o.get("order_line"):
                line_ids.extend(o["order_line"])
        if not line_ids:
            return empty_df

        lines = _x(u, db, uid, ak, "sale.order.line", "search_read",
                   [[["id", "in", line_ids]]],
                   {"fields": ["order_id", "product_id", "product_uom_qty",
                               "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        order_map = {o["id"]: o for o in orders}

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = (_x(u, db, uid, ak, "product.product", "search_read",
                       [[["id", "in", prod_ids]]],
                       {"fields": ["id", "default_code", "name", "categ_id"],
                        "limit": len(prod_ids) + 20}) if prod_ids else [])
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id")
            order = order_map.get(oid)
            if not order:
                continue

            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})
            model_code = (prod.get("default_code") or "").strip()
            if model_filter and model_filter.strip():
                if not model_code.upper().startswith(model_filter.upper()):
                    continue

            partner = order.get("partner_id")
            customer = (partner[1] if isinstance(partner, list) and len(partner) > 1 else "")

            rows.append({
                "System": system_name,
                "Date": str(order.get("date_order", ""))[:10],
                "SO": order.get("name", ""),
                "Customer": customer,
                "Model Code": model_code,
                "Product": prod.get("name", ""),
                "Qty": float(line.get("product_uom_qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
                "State": order.get("state", ""),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_sales_multi(selected_keys, date_from, date_to, model_filter):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_sales_for_system, k, date_from, date_to, model_filter): k
                for k in selected_keys}
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# AI CHAT PANEL (Rule-based with optional LLM)
# ─────────────────────────────────────────────────────────────────────────────
def get_ai_response(user_msg: str) -> str:
    """Rule-based assistant that answers from loaded session data."""
    msg = user_msg.lower().strip()

    inv_df = st.session_state.get("inventory_df")
    pos_df = st.session_state.get("pos_df")
    sales_df = st.session_state.get("sales_df")
    pur_df = st.session_state.get("purchase_df")

    qc = t("On Hand", "متوفر")
    sp = t("Sale Price", "سعر البيع")
    mc = t("Model Code", "رمز الموديل")
    qty_col = t("Qty", "الكمية")
    sub_col = t("Subtotal", "المجموع الفرعي")
    total_col = t("Total Amount", "المبلغ الإجمالي")
    so_col = t("SO", "أمر بيع")
    branch_col = t("Branch", "الفرع")
    vendor_col = t("Vendor", "المورد")
    customer_col = t("Customer", "العميل")

    # Inventory queries
    if any(k in msg for k in ["inventory", "stock", "مخزون", "متوفر", "zero", "low"]):
        if inv_df is None or inv_df.empty:
            return t("📦 No inventory data loaded. Please refresh the Inventory tab first.",
                     "📦 لا توجد بيانات مخزون محملة. يرجى تحديث تبويب المخزون أولاً.")
        qty = pd.to_numeric(inv_df.get(qc, pd.Series()), errors="coerce").fillna(0)
        total = int(qty.sum())
        zero_count = int((qty == 0).sum())
        low_count = int(((qty > 0) & (qty <= 5)).sum())
        models = inv_df[mc].nunique() if mc in inv_df.columns else 0
        val = (qty * pd.to_numeric(inv_df.get(sp, pd.Series(0)), errors="coerce").fillna(0)).sum()

        if "zero" in msg or "صفر" in msg:
            zero_items = inv_df[qty == 0][mc].head(5).tolist() if mc in inv_df.columns else []
            return t(f"🔴 {zero_count} products have zero stock. Examples: {', '.join(map(str,zero_items))}",
                     f"🔴 {zero_count} منتج بدون مخزون. أمثلة: {', '.join(map(str,zero_items))}")
        if "low" in msg or "منخفض" in msg:
            return t(f"⚠️ {low_count} products have low stock (≤5 units).",
                     f"⚠️ {low_count} منتج بمخزون منخفض (≤5 وحدات).")
        if "top" in msg or "أعلى" in msg:
            if mc in inv_df.columns and qc in inv_df.columns:
                top = inv_df.groupby(mc)[qc].sum().sort_values(ascending=False).head(5)
                lines = [f"  • {k}: {v:,.0f}" for k, v in top.items()]
                return t(f"🏆 Top 5 models by qty:\n" + "\n".join(lines),
                         f"🏆 أعلى 5 موديلات بالكمية:\n" + "\n".join(lines))
        return t(f"📦 Inventory Summary:\n  • Total Qty: {total:,}\n  • Total Value: SAR {val:,.2f}\n  • Models: {models}\n  • Zero Stock: {zero_count}\n  • Low Stock (≤5): {low_count}",
                 f"📦 ملخص المخزون:\n  • إجمالي الكمية: {total:,}\n  • القيمة الإجمالية: {val:,.2f} ر.س\n  • الموديلات: {models}\n  • بدون مخزون: {zero_count}\n  • مخزون منخفض (≤5): {low_count}")

    # POS queries
    if any(k in msg for k in ["pos", "cashier", "كاشير", "نقطة بيع", "bill", "فاتورة"]):
        if pos_df is None or pos_df.empty:
            return t("🛒 No POS data loaded. Please refresh the POS tab first.",
                     "🛒 لا توجد بيانات نقاط البيع. يرجى تحديث التبويب أولاً.")
        pos_order_col = t("POS Order", "طلب نقطة بيع")
        unique_orders = pos_df.drop_duplicates(subset=[pos_order_col]) if pos_order_col in pos_df.columns else pos_df
        total_amt = unique_orders[total_col].sum() if total_col in unique_orders.columns else 0
        bills = len(unique_orders)
        avg = total_amt / bills if bills > 0 else 0
        if "cashier" in msg or "كاشير" in msg:
            if "Cashier" in pos_df.columns or t("Cashier","الكاشير") in pos_df.columns:
                cash_col = t("Cashier","الكاشير") if t("Cashier","الكاشير") in pos_df.columns else "Cashier"
                top = unique_orders.groupby(cash_col)[total_col].sum().sort_values(ascending=False).head(3)
                lines = [f"  • {k}: SAR {v:,.2f}" for k, v in top.items()]
                return t("👤 Top Cashiers:\n" + "\n".join(lines),
                         "👤 أفضل الكاشيرين:\n" + "\n".join(lines))
        if "branch" in msg or "فرع" in msg:
            if branch_col in unique_orders.columns:
                top = unique_orders.groupby(branch_col)[total_col].sum().sort_values(ascending=False)
                lines = [f"  • {k}: SAR {v:,.2f}" for k, v in top.items()]
                return t("🏪 Branch POS Sales:\n" + "\n".join(lines),
                         "🏪 مبيعات الفروع:\n" + "\n".join(lines))
        return t(f"🛒 POS Summary:\n  • Total Sales: SAR {total_amt:,.2f}\n  • Bills: {bills:,}\n  • Avg Bill: SAR {avg:,.2f}",
                 f"🛒 ملخص نقاط البيع:\n  • إجمالي المبيعات: {total_amt:,.2f} ر.س\n  • الفواتير: {bills:,}\n  • متوسط الفاتورة: {avg:,.2f} ر.س")

    # Sales queries
    if any(k in msg for k in ["sale", "مبيعات", "order", "طلب", "customer", "عميل"]):
        if sales_df is None or sales_df.empty:
            return t("🛍️ No sales data loaded. Please refresh the Sales tab first.",
                     "🛍️ لا توجد بيانات مبيعات. يرجى تحديث التبويب أولاً.")
        total_sales = sales_df[total_col].sum() if total_col in sales_df.columns else 0
        orders = sales_df[so_col].nunique() if so_col in sales_df.columns else 0
        avg_ord = total_sales / orders if orders > 0 else 0
        if "customer" in msg or "عميل" in msg:
            if customer_col in sales_df.columns:
                unique_so = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
                top = unique_so.groupby(customer_col)[total_col].sum().sort_values(ascending=False).head(5)
                lines = [f"  • {k}: SAR {v:,.2f}" for k, v in top.items()]
                return t("👥 Top Customers:\n" + "\n".join(lines),
                         "👥 أفضل العملاء:\n" + "\n".join(lines))
        return t(f"🛍️ Sales Summary:\n  • Total Sales: SAR {total_sales:,.2f}\n  • Orders: {orders:,}\n  • Avg Order: SAR {avg_ord:,.2f}",
                 f"🛍️ ملخص المبيعات:\n  • إجمالي المبيعات: {total_sales:,.2f} ر.س\n  • الطلبات: {orders:,}\n  • متوسط الطلب: {avg_ord:,.2f} ر.س")

    # Purchase queries
    if any(k in msg for k in ["purchase", "مشتريات", "vendor", "مورد", "po", "buy"]):
        if pur_df is None or pur_df.empty:
            return t("🛒 No purchase data loaded. Please refresh the Purchase tab first.",
                     "🛒 لا توجد بيانات مشتريات. يرجى تحديث التبويب أولاً.")
        total_qty = pd.to_numeric(pur_df.get(qty_col, pd.Series()), errors="coerce").fillna(0).sum()
        total_val = pd.to_numeric(pur_df.get(sub_col, pd.Series()), errors="coerce").fillna(0).sum()
        if "vendor" in msg or "مورد" in msg:
            if vendor_col in pur_df.columns:
                top = pur_df.groupby(vendor_col)[sub_col].sum().sort_values(ascending=False).head(5)
                lines = [f"  • {k}: SAR {v:,.2f}" for k, v in top.items()]
                return t("📋 Top Vendors:\n" + "\n".join(lines),
                         "📋 أفضل الموردين:\n" + "\n".join(lines))
        return t(f"🛒 Purchase Summary:\n  • Total Qty: {total_qty:,.0f}\n  • Total Value: SAR {total_val:,.2f}",
                 f"🛒 ملخص المشتريات:\n  • إجمالي الكمية: {total_qty:,.0f}\n  • القيمة الإجمالية: {total_val:,.2f} ر.س")

    # Help
    if any(k in msg for k in ["help", "مساعدة", "what", "ماذا", "how", "كيف"]):
        return t(
            "💡 I can help you with:\n  • Inventory summary & alerts\n  • POS sales & cashier performance\n  • Sales orders & customer analysis\n  • Purchase history & vendor analysis\n\nTry asking: 'top inventory models', 'POS branch sales', 'top customers', 'vendor summary'",
            "💡 يمكنني مساعدتك في:\n  • ملخص المخزون والتنبيهات\n  • مبيعات نقاط البيع وأداء الكاشير\n  • أوامر البيع وتحليل العملاء\n  • تاريخ المشتريات وتحليل الموردين\n\nجرب: 'أعلى موديلات المخزون'، 'مبيعات فروع POS'، 'أفضل العملاء'"
        )

    return t(
        "🤖 I can analyze your loaded data. Try asking about inventory, POS, sales, or purchases. Type 'help' for suggestions.",
        "🤖 يمكنني تحليل البيانات المحملة. جرب السؤال عن المخزون أو نقاط البيع أو المبيعات أو المشتريات. اكتب 'مساعدة' للاقتراحات."
    )

def show_chat_panel():
    st.markdown(f"### 🤖 {t('AI Assistant','المساعد الذكي')}")
    st.markdown(f"<div class='info-banner'>💡 {t('Ask questions about your loaded data. No API key required.','اسأل عن بياناتك المحملة. لا حاجة لمفتاح API.')}</div>", unsafe_allow_html=True)

    # Quick suggestion buttons
    suggestions = [
        t("📦 Inventory summary", "📦 ملخص المخزون"),
        t("🔴 Zero stock items", "🔴 عناصر بدون مخزون"),
        t("🏪 POS branch sales", "🏪 مبيعات فروع POS"),
        t("👥 Top customers", "👥 أفضل العملاء"),
        t("📋 Top vendors", "📋 أفضل الموردين"),
        t("💡 Help", "💡 مساعدة"),
    ]

    cols = st.columns(3)
    for i, sug in enumerate(suggestions):
        if cols[i % 3].button(sug, key=f"chat_sug_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": sug})
            response = get_ai_response(sug)
            st.session_state.chat_history.append({"role": "bot", "content": response})

    # Chat history display
    history_html = "<div class='chat-container'>"
    if not st.session_state.chat_history:
        history_html += f"<div style='color:{th('text_muted')};text-align:center;padding:20px;font-size:0.9rem;'>"
        history_html += t("👋 Hello! Ask me anything about your dashboard data.", "👋 مرحباً! اسأل عن بيانات لوحتك.") + "</div>"
    for msg in st.session_state.chat_history[-20:]:
        if msg["role"] == "user":
            history_html += f"<div class='chat-label-user'>{t('You','أنت')}</div>"
            history_html += f"<div class='chat-msg-user'>{msg['content']}</div>"
        else:
            history_html += f"<div class='chat-label-bot'>🤖 AI</div>"
            history_html += f"<div class='chat-msg-bot'>{msg['content'].replace(chr(10),'<br>')}</div>"
    history_html += "</div>"
    st.markdown(history_html, unsafe_allow_html=True)

    # Input
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            t("Type your question...", "اكتب سؤالك..."),
            key="chat_input", label_visibility="collapsed",
            placeholder=t("e.g. Show me low stock items...", "مثال: أظهر لي المخزون المنخفض..."),
        )
    with col_send:
        if st.button(t("Send", "إرسال"), type="primary", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                response = get_ai_response(user_input)
                st.session_state.chat_history.append({"role": "bot", "content": response})
                st.rerun()

    if st.button(t("🗑️ Clear Chat", "🗑️ مسح المحادثة"), use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown(build_css(THEMES[get_theme()]), unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-orb'>📊</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>Multi‑Company Ops</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-subtitle'>Powered by Odoo · Sign in to continue</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
            if submitted:
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    token = _make_token(email)
                    st.query_params.update({"u": email, "t": token})
                    st.rerun()
                else:
                    st.error("Please enter your credentials")
        st.markdown("</div>", unsafe_allow_html=True)

def do_logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    theme = get_theme()
    st.markdown(build_css(THEMES[theme]), unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### ⚙️ {t('Settings','الإعدادات')}")

        # Theme Switcher
        st.markdown(f"**🎨 {t('Theme','المظهر')}**")
        new_theme = st.selectbox(
            t("Select Theme", "اختر المظهر"),
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(theme),
            key="theme_select",
            label_visibility="collapsed",
        )
        if new_theme != theme:
            st.session_state.theme = new_theme
            st.rerun()

        st.divider()

        # Language
        lc = st.radio(t("🌐 Language","🌐 اللغة"), ["EN","AR"],
                      index=0 if get_lang() == "EN" else 1, horizontal=True)
        if lc != get_lang():
            st.session_state.lang = lc
            st.rerun()

        st.divider()

        # System status
        st.markdown(f"**🏢 {t('Connected Systems','الأنظمة المتصلة')}**")
        for key in SYSTEM_KEYS:
            cfg = st.secrets.get(key, {})
            name = get_system_name(key)
            if cfg:
                st.markdown(f"<span class='badge-ok'>✓ {name}</span>&nbsp;", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='badge-off'>✗ {name}</span>&nbsp;", unsafe_allow_html=True)

        st.divider()
        st.markdown(f"👤 **{st.session_state.user_email}**")
        if st.button(f"🚪 {t('Logout','تسجيل الخروج')}", use_container_width=True):
            do_logout()

    # ── HEADER ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='dash-header'>
        <div class='dash-title'>📊 Multi‑Company Operations Dashboard</div>
        <div class='dash-subtitle'>{t('Inventory · POS · Sales · Purchase · AI Assistant','المخزون · نقاط البيع · المبيعات · المشتريات · المساعد الذكي')}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    # ── MAIN TABS ─────────────────────────────────────────────────────────────
    tab_inv, tab_pos, tab_sales, tab_pur, tab_chat = st.tabs([
        f"📦 {t('Inventory','المخزون')}",
        f"🛒 {t('POS','نقاط البيع')}",
        f"🛍️ {t('Sales','المبيعات')}",
        f"🔖 {t('Purchase','المشتريات')}",
        f"🤖 {t('AI Chat','المساعد')}",
    ])

    # =========================================================================
    # INVENTORY TAB
    # =========================================================================
    with tab_inv:
        st.markdown(f"### 📦 {t('Inventory Overview','نظرة عامة على المخزون')}")

        # Controls
        co1, co2 = st.columns([2, 2])
        with co1:
            company_options = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            selected_company = st.selectbox(t("Select Company","اختر الشركة"), options=company_options, index=0, key="inv_company")
            inv_keys = (SYSTEM_KEYS if selected_company == t("All Companies","جميع الشركات")
                        else [k for k in SYSTEM_KEYS if get_system_name(k) == selected_company])
        with co2:
            low_thresh = st.number_input(t("Low stock threshold","حد المخزون المنخفض"),
                                         min_value=0, max_value=1000, value=5, step=1, key="inv_low_thresh")

        fc1, fc2 = st.columns([3, 1])
        with fc1:
            model_filter = st.text_input(t("Model Code (optional)","رمز الموديل (اختياري)"), key="inv_model_filter").strip()
        with fc2:
            exact_match = st.toggle(t("Exact match","تطابق تام"), value=False, key="inv_exact")

        viz_mode = viz_mode_selector("inv_viz_mode")

        if st.button(f"🔄 {t('Refresh Inventory','تحديث المخزون')}", type="primary"):
            with st.spinner(t("Fetching inventory data...","جاري جلب بيانات المخزون...")):
                codes = tuple([model_filter]) if model_filter else ()
                total_df, branch_df = fetch_inventory_data(codestuple=codes, exact=exact_match)

                # Filter by selected companies only
                sys_col_local = t("System","النظام") if t("System","النظام") in (total_df.columns if total_df is not None else []) else "System"
                if not total_df.empty and selected_company != t("All Companies","جميع الشركات"):
                    total_df = total_df[total_df[sys_col_local] == selected_company] if sys_col_local in total_df.columns else total_df

                # Purchase Qty overlay for SWAG
                mc_col = "Model Code"
                swag_sys_name = get_system_name("SWAG")
                if not total_df.empty and "System" in total_df.columns:
                    swag_mask = total_df["System"] == swag_sys_name
                    if swag_mask.any() and mc_col in total_df.columns:
                        model_codes_swag = total_df.loc[swag_mask, mc_col].dropna().unique().tolist()
                        if model_codes_swag:
                            end_date = datetime.now().date()
                            start_date = end_date - timedelta(days=365)
                            pur_summary = get_purchase_summary_by_model(
                                tuple(model_codes_swag),
                                start_date.strftime("%Y-%m-%d"),
                                end_date.strftime("%Y-%m-%d"),
                            )
                            if not pur_summary.empty:
                                total_df = total_df.merge(pur_summary[["Model Code","Purchase Qty"]],
                                                          on="Model Code", how="left")
                                total_df["Purchase Qty"] = total_df["Purchase Qty"].fillna(0).astype(int)
                                total_df.loc[~swag_mask, "Purchase Qty"] = 0
                            else:
                                total_df["Purchase Qty"] = 0
                        else:
                            total_df["Purchase Qty"] = 0
                    else:
                        total_df["Purchase Qty"] = 0
                else:
                    if not total_df.empty:
                        total_df["Purchase Qty"] = 0

                total_df = prepare_df(total_df)
                branch_df = prepare_df(branch_df)
                st.session_state.inventory_df = total_df
                st.session_state.inventory_branch_df = branch_df

        total_df = st.session_state.get("inventory_df")
        branch_df = st.session_state.get("inventory_branch_df")

        if total_df is None or total_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t(\"Click 'Refresh Inventory' to load data.\",\"اضغط تحديث المخزون لتحميل البيانات.\")}</div>", unsafe_allow_html=True)
        else:
            qc = t("On Hand","متوفر")
            sp = t("Sale Price","سعر البيع")
            mc = t("Model Code","رمز الموديل")
            prod_c = t("Product","المنتج")
            br_c = t("Branch","الفرع")

            qty_s = pd.to_numeric(total_df.get(qc, pd.Series()), errors="coerce").fillna(0)
            price_s = pd.to_numeric(total_df.get(sp, pd.Series()), errors="coerce").fillna(0)
            total_qty = int(qty_s.sum())
            total_value = (qty_s * price_s).sum()
            distinct_models = total_df[mc].nunique() if mc in total_df.columns else 0
            distinct_branches = (branch_df[br_c].nunique()
                                 if branch_df is not None and not branch_df.empty and br_c in branch_df.columns else 0)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(t("Total Stock Qty","إجمالي الكمية"), f"{total_qty:,.0f}")
            c2.metric(t("Inventory Value (SAR)","قيمة المخزون (ر.س)"), f"{total_value:,.2f}")
            c3.metric(t("Distinct Models","عدد الموديلات"), distinct_models)
            c4.metric(t("Distinct Branches","عدد الفروع"), distinct_branches)
            st.divider()

            # Stock alerts
            qty_num = pd.to_numeric(total_df.get(qc, pd.Series()), errors="coerce").fillna(0)
            zero_stock = total_df[qty_num == 0]
            low_stock = total_df[(qty_num > 0) & (qty_num <= low_thresh)]
            if not zero_stock.empty:
                st.markdown(f"<div class='alert-banner'>⚠️ {len(zero_stock)} {t('products have zero stock','منتج بدون مخزون')}</div>", unsafe_allow_html=True)
            if not low_stock.empty:
                st.markdown(f"<div class='alert-banner'>🔴 {len(low_stock)} {t('low stock items','عناصر منخفضة المخزون')} ≤ {low_thresh}</div>", unsafe_allow_html=True)

            # Visualization
            st.markdown(f"#### 📊 {t('Inventory Visualization','تصور المخزون')}")
            if mc in total_df.columns and qc in total_df.columns:
                render_visualization(total_df, viz_mode, mc, qc, t("Stock by Model","المخزون حسب الموديل"))
            st.divider()

            # Branch chart
            if (branch_df is not None and not branch_df.empty and br_c in branch_df.columns and qc in branch_df.columns):
                st.markdown(f"#### 🏪 {t('Branch-wise Stock','المخزون حسب الفرع')}")
                branch_summary = branch_df.groupby(br_c)[qc].sum().reset_index().sort_values(qc, ascending=False)
                st.bar_chart(branch_summary.set_index(br_c)[qc], use_container_width=True)
                st.dataframe(branch_summary, use_container_width=True)
                st.divider()

            # Detailed table
            st.markdown(f"#### 📋 {t('Detailed Inventory','المخزون التفصيلي')}")
            filtered_inv = display_df(total_df, thresh=low_thresh)
            st.markdown("<br>", unsafe_allow_html=True)

            # Downloads
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button("⬇️ CSV", to_csv(filtered_inv), dl_name("inventory","csv"), "text/csv", use_container_width=True)
            with d2:
                st.download_button("⬇️ Excel", to_excel(filtered_inv), dl_name("inventory","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with d3:
                if branch_df is not None and not branch_df.empty:
                    filtered_branch = (branch_df[branch_df[mc].str.contains(model_filter, case=False, na=False)]
                                       if model_filter else branch_df)
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel','Excel مصفوفة الفروع')}",
                        to_excel_branch_matrix(filtered_branch),
                        dl_name("branch_matrix","xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    # =========================================================================
    # POS TAB
    # =========================================================================
    with tab_pos:
        st.markdown(f"### 🛒 {t('POS Sales','مبيعات نقاط البيع')}")

        pos_co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
        pos_co = st.selectbox(t("Select Company","اختر الشركة"), options=pos_co_opts, index=0, key="pos_company")
        pos_keys = (SYSTEM_KEYS if pos_co == t("All Companies","جميع الشركات")
                    else [k for k in SYSTEM_KEYS if get_system_name(k) == pos_co])

        pdc1, pdc2 = st.columns(2)
        with pdc1:
            pos_date_from = st.date_input(t("From","من"), value=datetime.now().date()-timedelta(days=30), key="pos_date_from")
        with pdc2:
            pos_date_to = st.date_input(t("To","إلى"), value=datetime.now().date(), key="pos_date_to")

        pfc1, pfc2 = st.columns(2)
        with pfc1:
            pos_branch_filter = st.text_input(t("Branch (optional)","الفرع (اختياري)"), key="pos_branch_filter").strip()
        with pfc2:
            pos_model_filter = st.text_input(t("Model Code (optional)","رمز الموديل (اختياري)"), key="pos_model_filter").strip()

        pos_viz_mode = viz_mode_selector("pos_viz_mode")

        if st.button(f"🔄 {t('Refresh POS Data','تحديث بيانات نقاط البيع')}", type="primary"):
            with st.spinner(t("Fetching POS data...","جاري جلب بيانات نقاط البيع...")):
                pos_df = fetch_pos_multi(pos_keys, pos_date_from.strftime("%Y-%m-%d"),
                                         pos_date_to.strftime("%Y-%m-%d"),
                                         pos_branch_filter, pos_model_filter)
                st.session_state.pos_df = prepare_df(pos_df)

        pos_df = st.session_state.get("pos_df")

        if pos_df is None or pos_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t(\"Click 'Refresh POS Data' to load data.\",\"اضغط تحديث بيانات نقاط البيع لتحميل البيانات.\")}</div>", unsafe_allow_html=True)
        else:
            qty_col = t("Qty","الكمية")
            total_col = t("Total Amount","المبلغ الإجمالي")
            sub_col = t("Subtotal","المجموع الفرعي")
            branch_col = t("Branch","الفرع")
            cashier_col = t("Cashier","الكاشير")
            mc = t("Model Code","رمز الموديل")
            date_col = t("Date","التاريخ")
            pos_order_col = t("POS Order","طلب نقطة بيع")

            unique_orders = (pos_df.drop_duplicates(subset=[pos_order_col])
                             if pos_order_col in pos_df.columns else pos_df)
            total_sales_amt = unique_orders[total_col].sum() if total_col in unique_orders.columns else 0
            total_qty_v = pos_df[qty_col].sum() if qty_col in pos_df.columns else 0
            total_bills = len(unique_orders)
            avg_bill = total_sales_amt / total_bills if total_bills > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("Total Sales (SAR)","إجمالي المبيعات (ر.س)"), f"{total_sales_amt:,.2f}")
            m2.metric(t("Total Qty","إجمالي الكمية"), f"{total_qty_v:,.0f}")
            m3.metric(t("Number of Bills","عدد الفواتير"), f"{total_bills:,}")
            m4.metric(t("Average Bill (SAR)","متوسط الفاتورة (ر.س)"), f"{avg_bill:,.2f}")
            st.divider()

            # Visualization
            st.markdown(f"#### 📊 {t('POS Visualization','تصور نقاط البيع')}")
            if branch_col in unique_orders.columns and total_col in unique_orders.columns:
                render_visualization(unique_orders, pos_viz_mode, branch_col, total_col,
                                     t("Sales by Branch","المبيعات حسب الفرع"))
            elif mc in pos_df.columns and qty_col in pos_df.columns:
                render_visualization(pos_df, pos_viz_mode, mc, qty_col,
                                     t("Qty by Model","الكمية حسب الموديل"))
            st.divider()

            # Branch-wise
            if branch_col in unique_orders.columns and total_col in unique_orders.columns:
                branch_sales = unique_orders.groupby(branch_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False)
                st.markdown(f"#### 🏪 {t('Branch-wise POS Sales','مبيعات نقاط البيع حسب الفرع')}")
                st.bar_chart(branch_sales.set_index(branch_col)[total_col], use_container_width=True)
                st.dataframe(branch_sales, use_container_width=True)
                st.divider()

            # Cashier
            if cashier_col in unique_orders.columns and total_col in unique_orders.columns:
                cashier_sales = unique_orders.groupby(cashier_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False)
                st.markdown(f"#### 👤 {t('Cashier-wise Sales','المبيعات حسب الكاشير')}")
                st.dataframe(cashier_sales, use_container_width=True)
                st.divider()

            # Top products
            if mc in pos_df.columns and qty_col in pos_df.columns:
                top_products = pos_df.groupby(mc)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False).head(10)
                st.markdown(f"#### 🏆 {t('Top Products by Qty','أفضل المنتجات بالكمية')}")
                st.bar_chart(top_products.set_index(mc)[qty_col], use_container_width=True)
                st.divider()

            # Daily trend
            if date_col in unique_orders.columns and total_col in unique_orders.columns:
                daily = unique_orders.copy()
                daily[date_col] = pd.to_datetime(daily[date_col], errors="coerce").dt.date
                daily_trend = daily.groupby(date_col)[total_col].sum().reset_index().sort_values(date_col)
                st.markdown(f"#### 📈 {t('Daily Sales Trend','الاتجاه اليومي للمبيعات')}")
                st.line_chart(daily_trend.set_index(date_col)[total_col], use_container_width=True)
                st.divider()

            # Detailed table
            st.markdown(f"#### 📋 {t('Detailed POS Transactions','تفاصيل معاملات نقاط البيع')}")
            display_df(pos_df)
            st.markdown("<br>", unsafe_allow_html=True)

            p1, p2 = st.columns(2)
            with p1:
                st.download_button("⬇️ CSV", to_csv(pos_df), dl_name("pos","csv"), "text/csv", use_container_width=True)
            with p2:
                st.download_button("⬇️ Excel", to_excel(pos_df), dl_name("pos","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # SALES TAB
    # =========================================================================
    with tab_sales:
        st.markdown(f"### 🛍️ {t('Sales Orders','أوامر البيع')}")

        sales_co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
        sales_co = st.selectbox(t("Select Company","اختر الشركة"), options=sales_co_opts, index=0, key="sales_company")
        sales_keys = (SYSTEM_KEYS if sales_co == t("All Companies","جميع الشركات")
                      else [k for k in SYSTEM_KEYS if get_system_name(k) == sales_co])

        sc1, sc2 = st.columns(2)
        with sc1:
            sales_date_from = st.date_input(t("From","من"), value=datetime.now().date()-timedelta(days=30), key="sales_date_from")
        with sc2:
            sales_date_to = st.date_input(t("To","إلى"), value=datetime.now().date(), key="sales_date_to")

        sales_model_filter = st.text_input(t("Model Code (optional)","رمز الموديل (اختياري)"), key="sales_model_filter").strip()

        sales_viz_mode = viz_mode_selector("sales_viz_mode")

        if st.button(f"🔄 {t('Refresh Sales Data','تحديث بيانات المبيعات')}", type="primary"):
            with st.spinner(t("Fetching sales data...","جاري جلب بيانات المبيعات...")):
                sales_df = fetch_sales_multi(sales_keys, sales_date_from.strftime("%Y-%m-%d"),
                                             sales_date_to.strftime("%Y-%m-%d"), sales_model_filter)
                st.session_state.sales_df = prepare_df(sales_df)

        sales_df = st.session_state.get("sales_df")

        if sales_df is None or sales_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t(\"Click 'Refresh Sales Data' to load.\",\"اضغط تحديث بيانات المبيعات لتحميل البيانات.\")}</div>", unsafe_allow_html=True)
        else:
            qty_col = t("Qty","الكمية")
            total_col = t("Total Amount","المبلغ الإجمالي")
            customer_col = t("Customer","العميل")
            mc = t("Model Code","رمز الموديل")
            date_col = t("Date","التاريخ")
            so_col = t("SO","أمر بيع")

            total_sales_amt = sales_df[total_col].sum() if total_col in sales_df.columns else 0
            total_qty_v = sales_df[qty_col].sum() if qty_col in sales_df.columns else 0
            total_orders = sales_df[so_col].nunique() if so_col in sales_df.columns else 0
            avg_order = total_sales_amt / total_orders if total_orders > 0 else 0

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric(t("Total Sales (SAR)","إجمالي المبيعات (ر.س)"), f"{total_sales_amt:,.2f}")
            sm2.metric(t("Total Qty","إجمالي الكمية"), f"{total_qty_v:,.0f}")
            sm3.metric(t("Number of Orders","عدد الطلبات"), f"{total_orders:,}")
            sm4.metric(t("Average Order (SAR)","متوسط الطلب (ر.س)"), f"{avg_order:,.2f}")
            st.divider()

            # Visualization
            st.markdown(f"#### 📊 {t('Sales Visualization','تصور المبيعات')}")
            if mc in sales_df.columns and qty_col in sales_df.columns:
                render_visualization(sales_df, sales_viz_mode, mc, qty_col,
                                     t("Qty by Model","الكمية حسب الموديل"))
            st.divider()

            # Top customers
            unique_so = (sales_df.drop_duplicates(subset=[so_col])
                         if so_col in sales_df.columns else sales_df)
            if customer_col in unique_so.columns and total_col in unique_so.columns:
                customer_sales = unique_so.groupby(customer_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False).head(10)
                st.markdown(f"#### 👥 {t('Top Customers by Sales','أفضل العملاء حسب المبيعات')}")
                st.dataframe(customer_sales, use_container_width=True)
                st.divider()

            # Top products
            if mc in sales_df.columns and qty_col in sales_df.columns:
                top_products = sales_df.groupby(mc)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False).head(10)
                st.markdown(f"#### 🏆 {t('Top Products by Qty','أفضل المنتجات بالكمية')}")
                st.bar_chart(top_products.set_index(mc)[qty_col], use_container_width=True)
                st.divider()

            # Daily trend
            if date_col in unique_so.columns and total_col in unique_so.columns:
                daily = unique_so.copy()
                daily[date_col] = pd.to_datetime(daily[date_col], errors="coerce").dt.date
                daily_trend = daily.groupby(date_col)[total_col].sum().reset_index().sort_values(date_col)
                st.markdown(f"#### 📈 {t('Daily Sales Trend','الاتجاه اليومي للمبيعات')}")
                st.line_chart(daily_trend.set_index(date_col)[total_col], use_container_width=True)
                st.divider()

            # Detailed table
            st.markdown(f"#### 📋 {t('Detailed Sales Orders','تفاصيل أوامر البيع')}")
            display_df(sales_df)
            st.markdown("<br>", unsafe_allow_html=True)

            s1, s2 = st.columns(2)
            with s1:
                st.download_button("⬇️ CSV", to_csv(sales_df), dl_name("sales","csv"), "text/csv", use_container_width=True)
            with s2:
                st.download_button("⬇️ Excel", to_excel(sales_df), dl_name("sales","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # PURCHASE TAB
    # =========================================================================
    with tab_pur:
        st.markdown(f"### 🔖 {t('Purchase History','تاريخ المشتريات')}")

        pur_co_opts = [t("All Companies","جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
        pur_co = st.selectbox(t("Select Company","اختر الشركة"), options=pur_co_opts, index=0, key="pur_company")
        pur_keys = (SYSTEM_KEYS if pur_co == t("All Companies","جميع الشركات")
                    else [k for k in SYSTEM_KEYS if get_system_name(k) == pur_co])

        pur_model = st.text_input(t("Model Code (optional)","رمز الموديل (اختياري)"), key="pur_model").strip()

        pc1, pc2 = st.columns(2)
        with pc1:
            pur_date_from = st.date_input(t("From","من"), value=datetime.now().date()-timedelta(days=90), key="pur_date_from")
        with pc2:
            pur_date_to = st.date_input(t("To","إلى"), value=datetime.now().date(), key="pur_date_to")

        pur_viz_mode = viz_mode_selector("pur_viz_mode")

        if st.button(f"🔄 {t('Refresh Purchase','تحديث المشتريات')}", type="primary"):
            with st.spinner(t("Fetching purchase data...","جاري جلب بيانات المشتريات...")):
                pur_df = fetch_purchase_multi(pur_keys, pur_model,
                                              pur_date_from.strftime("%Y-%m-%d"),
                                              pur_date_to.strftime("%Y-%m-%d"))
                st.session_state.purchase_df = prepare_df(pur_df)

        pur_df = st.session_state.get("purchase_df")

        if pur_df is None or pur_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t(\"Click 'Refresh Purchase' to load.\",\"اضغط تحديث المشتريات لتحميل البيانات.\")}</div>", unsafe_allow_html=True)
        else:
            qty_col_pur = t("Qty","الكمية")
            sub_col_pur = t("Subtotal","المجموع الفرعي")
            vendor_col = t("Vendor","المورد")
            mc = t("Model Code","رمز الموديل")
            date_col = t("Date","التاريخ")

            total_p_qty = int(pd.to_numeric(pur_df.get(qty_col_pur, pd.Series()), errors="coerce").fillna(0).sum())
            total_p_val = pd.to_numeric(pur_df.get(sub_col_pur, pd.Series()), errors="coerce").fillna(0).sum()
            total_vendors = pur_df[vendor_col].nunique() if vendor_col in pur_df.columns else 0

            pm1, pm2, pm3 = st.columns(3)
            pm1.metric(t("Total Purchase Qty","إجمالي كمية الشراء"), f"{total_p_qty:,}")
            pm2.metric(t("Total Purchase Value (SAR)","إجمالي قيمة الشراء (ر.س)"), f"{total_p_val:,.2f}")
            pm3.metric(t("Distinct Vendors","عدد الموردين"), f"{total_vendors:,}")
            st.divider()

            # Visualization
            st.markdown(f"#### 📊 {t('Purchase Visualization','تصور المشتريات')}")
            if vendor_col in pur_df.columns and sub_col_pur in pur_df.columns:
                render_visualization(pur_df, pur_viz_mode, vendor_col, sub_col_pur,
                                     t("Purchase Value by Vendor","قيمة الشراء حسب المورد"))
            elif mc in pur_df.columns and qty_col_pur in pur_df.columns:
                render_visualization(pur_df, pur_viz_mode, mc, qty_col_pur,
                                     t("Qty by Model","الكمية حسب الموديل"))
            st.divider()

            # Vendor summary
            if vendor_col in pur_df.columns and sub_col_pur in pur_df.columns:
                vendor_summary = pur_df.groupby(vendor_col)[sub_col_pur].sum().reset_index().sort_values(sub_col_pur, ascending=False).head(10)
                st.markdown(f"#### 🏭 {t('Top Vendors by Value','أفضل الموردين بالقيمة')}")
                st.dataframe(vendor_summary, use_container_width=True)
                st.divider()

            # Receipt location summary
            loc_col = t("Receipt Location","موقع الاستلام")
            if loc_col in pur_df.columns and qty_col_pur in pur_df.columns:
                loc_summary = pur_df.groupby(loc_col)[qty_col_pur].sum().reset_index().sort_values(qty_col_pur, ascending=False)
                st.markdown(f"#### 📍 {t('Receipt Location Summary','ملخص مواقع الاستلام')}")
                st.dataframe(loc_summary, use_container_width=True)
                st.divider()

            # Daily trend
            if date_col in pur_df.columns and sub_col_pur in pur_df.columns:
                daily_pur = pur_df.copy()
                daily_pur[date_col] = pd.to_datetime(daily_pur[date_col], errors="coerce").dt.date
                daily_pur_trend = daily_pur.groupby(date_col)[sub_col_pur].sum().reset_index().sort_values(date_col)
                st.markdown(f"#### 📈 {t('Daily Purchase Trend','الاتجاه اليومي للمشتريات')}")
                st.line_chart(daily_pur_trend.set_index(date_col)[sub_col_pur], use_container_width=True)
                st.divider()

            st.markdown(f"#### 📋 {t('Detailed Purchase History','تفاصيل تاريخ المشتريات')}")
            display_df(pur_df)
            st.markdown("<br>", unsafe_allow_html=True)

            pd1, pd2 = st.columns(2)
            with pd1:
                st.download_button("⬇️ CSV", to_csv(pur_df), dl_name("purchase","csv"), "text/csv", use_container_width=True)
            with pd2:
                st.download_button("⬇️ Excel", to_excel(pur_df), dl_name("purchase","xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # AI CHAT TAB
    # =========================================================================
    with tab_chat:
        show_chat_panel()

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
