# app.py — SWAG EXECUTIVE DASHBOARD — REDESIGNED v5.0
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
    page_title="SWAG Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 0: COLOR UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def hex_to_rgba(hex_color: str, alpha: float = 0.18) -> str:
    """Convert hex color to rgba() string safe for Plotly fillcolor."""
    try:
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6:
            return f"rgba(102,126,234,{alpha})"
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(102,126,234,{alpha})"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: THEMES — RETAIL OPERATIONS EXECUTIVE
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Retail Operations Pro": {
        "bg": "#f5f7fc",
        "sidebar_bg": "#ffffff",
        "card_bg": "#ffffff",
        "card_bg_solid": "#ffffff",
        "accent1": "#1e3a8a",      # Deep navy
        "accent2": "#3b82f6",      # Bright blue
        "accent3": "#10b981",      # Emerald
        "accent4": "#f59e0b",      # Amber
        "text": "#0f172a",
        "text_muted": "#64748b",
        "text_label": "#334155",
        "border": "#e2e8f0",
        "input_bg": "#ffffff",
        "metric_gradient": "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
        "tab_active": "#1e3a8a",
        "title_gradient": "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
        "button_gradient": "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#1e3a8a", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4"],
        "danger": "#dc2626",
        "warning": "#f59e0b",
        "success": "#10b981",
        "shadow": "0 4px 12px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)",
        "shadow_hover": "0 12px 24px -8px rgba(0,0,0,0.08)",
    },
    "Luxury Dark": {
        "bg": "#0b0f15",
        "sidebar_bg": "#151a23",
        "card_bg": "#1e2430",
        "card_bg_solid": "#1e2430",
        "accent1": "#d4af37",      # Gold
        "accent2": "#f5c842",      # Light gold
        "accent3": "#4ade80",      # Green
        "accent4": "#f87171",      # Red
        "text": "#f1f5f9",
        "text_muted": "#94a3b8",
        "text_label": "#cbd5e1",
        "border": "#2d3748",
        "input_bg": "#1e2430",
        "metric_gradient": "linear-gradient(135deg, #d4af37 0%, #f5c842 100%)",
        "tab_active": "#d4af37",
        "title_gradient": "linear-gradient(135deg, #d4af37 0%, #f5c842 100%)",
        "button_gradient": "linear-gradient(135deg, #d4af37 0%, #f5c842 100%)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#d4af37", "#f5c842", "#4ade80", "#f87171", "#60a5fa", "#c084fc", "#f472b6", "#2dd4bf"],
        "danger": "#f87171",
        "warning": "#fbbf24",
        "success": "#4ade80",
        "shadow": "0 8px 16px rgba(0,0,0,0.2)",
        "shadow_hover": "0 16px 32px rgba(0,0,0,0.3)",
    },
    "Boardroom Light": {
        "bg": "#fafafa",
        "sidebar_bg": "#ffffff",
        "card_bg": "#ffffff",
        "card_bg_solid": "#ffffff",
        "accent1": "#4f46e5",      # Indigo
        "accent2": "#7c3aed",      # Purple
        "accent3": "#059669",      # Green
        "accent4": "#d97706",      # Amber
        "text": "#111827",
        "text_muted": "#6b7280",
        "text_label": "#374151",
        "border": "#e5e7eb",
        "input_bg": "#ffffff",
        "metric_gradient": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
        "tab_active": "#4f46e5",
        "title_gradient": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
        "button_gradient": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#4f46e5", "#7c3aed", "#059669", "#d97706", "#dc2626", "#0891b2", "#8b5cf6", "#ec4899"],
        "danger": "#dc2626",
        "warning": "#d97706",
        "success": "#059669",
        "shadow": "0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03)",
        "shadow_hover": "0 10px 20px -8px rgba(0,0,0,0.08)",
    },
}

def get_theme():
    t_val = st.session_state.get("theme", "Retail Operations Pro")
    return t_val if t_val in THEMES else "Retail Operations Pro"

def th(key):
    return THEMES[get_theme()].get(key, "")

def th_color(key, fallback="#1e3a8a"):
    val = str(THEMES[get_theme()].get(key, fallback) or fallback).strip()
    if re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", val):
        return val
    m = re.search(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", val)
    return f"#{m.group(1)}" if m else fallback

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: CSS — PROFESSIONAL REDESIGN
# ─────────────────────────────────────────────────────────────────────────────
def build_css():
    border_val = th("border")
    card_bg_solid = th("card_bg_solid")
    tab_active = th("tab_active")
    a1 = th_color("accent1")
    a2 = th_color("accent2")
    a3 = th_color("accent3")
    warning_color = th_color("warning", "#f59e0b")
    danger_color = th_color("danger", "#dc2626")
    success_color = th_color("success", "#10b981")
    shadow = th("shadow")
    shadow_hover = th("shadow_hover")
    is_rtl = get_lang() == "AR"
    dir_style = "direction: rtl; text-align: right;" if is_rtl else "direction: ltr; text-align: left;"
    body_dir = "rtl" if is_rtl else "ltr"
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    html {{ direction: {body_dir}; }}
    body {{ background: {th("bg")}; color: {th("text")}; }}
    .stApp {{ background: {th("bg")}; }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {th("sidebar_bg")} !important;
        border-right: 1px solid {border_val};
        box-shadow: none;
    }}
    section[data-testid="stSidebar"] * {{ color: {th("text")} !important; }}
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background: {th("input_bg")} !important;
        border: 1px solid {border_val} !important;
        border-radius: 8px !important;
        color: {th("text")} !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 0.75rem !important;
        transition: all 0.15s ease;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: {a1} !important;
        box-shadow: 0 0 0 2px {hex_to_rgba(a1, 0.1)} !important;
    }}
    label, .stTextInput label, .stNumberInput label {{ color: {th("text_label")} !important; font-weight: 500; font-size: 0.8rem; }}
    
    /* Buttons */
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        border: 1px solid {border_val} !important;
        background: {th("card_bg")} !important;
        color: {th("text")} !important;
    }}
    .stButton > button:hover {{
        background: {th("border")} !important;
        transform: translateY(-1px);
        box-shadow: {shadow} !important;
    }}
    .stButton > button[kind="primary"] {{
        background: {th("button_gradient")} !important;
        color: white !important;
        border: none !important;
        box-shadow: {shadow} !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: {shadow_hover} !important;
        transform: translateY(-1px);
    }}
    .stDownloadButton > button {{
        background: {th("card_bg")} !important;
        border: 1px solid {border_val} !important;
        border-radius: 8px !important;
        color: {th("text")} !important;
        font-size: 0.8rem !important;
        padding: 0.3rem 0.8rem !important;
    }}
    .stDownloadButton > button:hover {{
        background: {th("button_gradient")} !important;
        color: white !important;
        border-color: transparent !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent;
        gap: 2px;
        border-bottom: 1px solid {border_val};
        padding-bottom: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {th("text_muted")} !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        background: transparent !important;
        border: none !important;
        margin-right: 2px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {tab_active} !important;
        background: transparent !important;
        border-bottom: 3px solid {tab_active} !important;
        font-weight: 600 !important;
    }}
    
    /* Metric Cards */
    [data-testid="stMetric"] {{
        background: {th("card_bg")};
        border: 1px solid {border_val};
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        box-shadow: {shadow};
        transition: all 0.2s ease;
    }}
    [data-testid="stMetric"]:hover {{
        box-shadow: {shadow_hover};
        transform: translateY(-2px);
    }}
    [data-testid="stMetricLabel"] {{
        color: {th("text_muted")} !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: {th("text")} !important;
    }}
    
    /* Banners */
    .info-banner {{ background: {hex_to_rgba(a1, 0.08)}; border-left: 4px solid {a1}; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 1rem 0; color: {th("text")}; }}
    .warn-banner {{ background: {hex_to_rgba(warning_color, 0.08)}; border-left: 4px solid {warning_color}; border-radius: 8px; padding: 0.8rem 1.2rem; }}
    .alert-banner {{ background: {hex_to_rgba(danger_color, 0.08)}; border-left: 4px solid {danger_color}; border-radius: 8px; padding: 0.8rem 1.2rem; }}
    .ok-banner {{ background: {hex_to_rgba(success_color, 0.08)}; border-left: 4px solid {success_color}; border-radius: 8px; padding: 0.8rem 1.2rem; }}
    
    /* Cards */
    .exec-card {{
        background: {th("card_bg")};
        border: 1px solid {border_val};
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: {shadow};
        color: {th("text")};
    }}
    
    /* KPI Tiles */
    .kpi-tile {{
        background: {th("card_bg")};
        border: 1px solid {border_val};
        border-radius: 20px;
        padding: 1.5rem 1rem;
        text-align: center;
        box-shadow: {shadow};
        transition: all 0.2s ease;
    }}
    .kpi-tile:hover {{
        box-shadow: {shadow_hover};
        transform: translateY(-3px);
    }}
    .kpi-tile .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {a1};
        line-height: 1.2;
    }}
    .kpi-tile .kpi-label {{
        font-size: 0.75rem;
        color: {th("text_muted")};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.5rem;
    }}
    .kpi-tile .kpi-icon {{
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        opacity: 0.8;
    }}
    
    /* Section Headers */
    .section-header {{
        font-size: 1rem;
        font-weight: 600;
        color: {th("text_label")};
        margin: 1.5rem 0 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    /* Tables */
    .dataframe-wrap table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: {th("card_bg")};
        border-radius: 12px;
        overflow: hidden;
        box-shadow: {shadow};
        border: 1px solid {border_val};
        font-size: 0.85rem;
    }}
    .dataframe-wrap th {{
        background: {th("card_bg_solid")};
        color: {th("text_label")};
        font-weight: 600;
        padding: 0.8rem 1rem;
        text-align: left;
        border-bottom: 1px solid {border_val};
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    .dataframe-wrap td {{
        padding: 0.7rem 1rem;
        border-bottom: 1px solid {border_val};
        color: {th("text")};
    }}
    .dataframe-wrap tr:last-child td {{ border-bottom: none; }}
    .dataframe-wrap tr:hover td {{ background: {hex_to_rgba(a1, 0.04)}; }}
    
    /* Pagination */
    .pagination-bar {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 1rem;
    }}
    .page-info {{
        background: {th("card_bg")};
        border: 1px solid {border_val};
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-size: 0.8rem;
        color: {th("text_muted")};
    }}
    
    /* Login Page */
    .login-container {{
        display: flex;
        min-height: 100vh;
        background: {th("bg")};
    }}
    .login-left {{
        flex: 1;
        background: {th("sidebar_bg")};
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 3rem;
        border-right: 1px solid {border_val};
    }}
    .login-right {{
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 3rem;
    }}
    .login-card {{
        max-width: 400px;
        width: 100%;
        background: {th("card_bg")};
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: {shadow_hover};
        border: 1px solid {border_val};
    }}
    .login-title {{
        font-size: 2rem;
        font-weight: 700;
        color: {th("text")};
        margin-bottom: 0.5rem;
    }}
    .login-subtitle {{
        color: {th("text_muted")};
        margin-bottom: 2rem;
        font-size: 0.9rem;
    }}
    .brand-block {{
        text-align: center;
    }}
    .brand-icon {{
        font-size: 3.5rem;
        margin-bottom: 1rem;
    }}
    .brand-name {{
        font-size: 1.8rem;
        font-weight: 700;
        background: {th("title_gradient")};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* Chat */
    .chat-container {{
        background: {th("card_bg")};
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid {border_val};
        box-shadow: {shadow};
    }}
    .chat-message-user {{
        background: {th("button_gradient")};
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0 0.5rem 3rem;
        max-width: 80%;
        align-self: flex-end;
    }}
    .chat-message-bot {{
        background: {th("card_bg_solid")};
        border: 1px solid {border_val};
        border-radius: 18px 18px 18px 4px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 3rem 0.5rem 0;
        max-width: 80%;
    }}
    .chat-insight-block {{
        background: {hex_to_rgba(a1, 0.05)};
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid {hex_to_rgba(a1, 0.2)};
    }}
    
    /* RTL adjustments */
    {f'''
    [dir="rtl"] .stTabs [data-baseweb="tab"] {{ margin-left: 2px; margin-right: 0; }}
    [dir="rtl"] .dataframe-wrap th {{ text-align: right; }}
    [dir="rtl"] .dataframe-wrap td {{ text-align: right; }}
    [dir="rtl"] .chat-message-user {{ margin: 0.5rem 3rem 0.5rem 0; border-radius: 18px 18px 18px 4px; }}
    [dir="rtl"] .chat-message-bot {{ margin: 0.5rem 0 0.5rem 3rem; border-radius: 18px 18px 4px 18px; }}
    ''' if is_rtl else ''}
    
    footer {{ visibility: hidden; }}
    </style>
    """

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: CONSTANTS & CONFIG (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]
ROWS_PER_PAGE = 30
VIZ_MODES = [
    "📋 List View", "🏆 KPI Tiles", "📊 Column Chart", "📉 Horizontal Bar",
    "📈 Line Chart", "📉 Area Chart", "🍕 Pie Chart", "🍩 Donut Chart",
    "📊 Stacked Column", "🔘 Scatter Chart", "🗂️ Funnel Chart", "📡 Radar Chart",
]

RAW_COLS = {
    "system": "System", "model_code": "Model Code", "product": "Product",
    "sale_price": "Sale Price", "on_hand": "On Hand", "purchase_qty_col": "Purchase Qty",
    "branch": "Branch", "location": "Location", "date": "Date", "pos_order": "POS Order",
    "customer": "Customer", "cashier": "Cashier", "category": "Category", "qty": "Qty",
    "unit_price": "Unit Price", "subtotal": "Subtotal", "total_amount": "Total Amount",
    "so": "SO", "vendor": "Vendor", "receipt_location": "Receipt Location", "po": "PO", "state": "State",
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: LANGUAGE / LOCALIZATION (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    return ar if get_lang() == "AR" else en

_COL_MAP = {
    "System": ("System", "النظام"), "Model Code": ("Model Code", "رمز الموديل"),
    "Product": ("Product", "المنتج"), "Sale Price": ("Sale Price", "سعر البيع"),
    "On Hand": ("On Hand", "متوفر"), "Purchase Qty": ("Purchase Qty", "كمية الشراء"),
    "Branch": ("Branch", "الفرع"), "Location": ("Location", "الموقع"),
    "Date": ("Date", "التاريخ"), "POS Order": ("POS Order", "طلب نقطة بيع"),
    "Customer": ("Customer", "العميل"), "Cashier": ("Cashier", "الكاشير"),
    "Category": ("Category", "الفئة"), "Qty": ("Qty", "الكمية"),
    "Unit Price": ("Unit Price", "سعر الوحدة"), "Subtotal": ("Subtotal", "المجموع الفرعي"),
    "Total Amount": ("Total Amount", "المبلغ الإجمالي"), "SO": ("SO", "أمر بيع"),
    "Vendor": ("Vendor", "المورد"), "Receipt Location": ("Receipt Location", "موقع الاستلام"),
    "PO": ("PO", "أمر شراء"), "State": ("State", "الحالة"),
    "Revenue (SAR)": ("Revenue (SAR)", "الإيرادات (ر.س)"),
    "Bills": ("Bills", "الفواتير"), "Orders": ("Orders", "الطلبات"),
    "Spend (SAR)": ("Spend (SAR)", "الإنفاق (ر.س)"),
}

def col(raw_name: str) -> str:
    if raw_name in _COL_MAP:
        en, ar = _COL_MAP[raw_name]
        return ar if get_lang() == "AR" else en
    return raw_name

def localize_df(df: pd.DataFrame) -> pd.DataFrame:
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
# SECTION 5: SESSION STATE DEFAULTS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False, "user_email": "", "lang": "EN",
    "theme": "Retail Operations Pro",
    "inventory_df": None, "inventory_branch_df": None, "pos_df": None,
    "sales_df": None, "purchase_df": None,
    "inv_diag": [], "pos_diag": [], "sales_diag": [], "pur_diag": [],
    "inv_last_refresh": None, "pos_last_refresh": None,
    "sales_last_refresh": None, "pur_last_refresh": None,
    "inv_viz_mode": "📋 List View", "pos_viz_mode": "📋 List View",
    "sales_viz_mode": "📋 List View", "pur_viz_mode": "📋 List View",
    "inv_page": 0, "inv_full_page": 0, "pos_page": 0, "pos_branch_page": 0,
    "pos_cashier_page": 0, "sales_page": 0, "sales_cust_page": 0,
    "pur_page": 0, "pur_vendor_page": 0, "chat_history": [], "login_error": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: AUTH (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
_COOKIE_SECRET = "swag_exec_2025_v3"

def _make_token(email: str) -> str:
    return hashlib.sha256(f"{_COOKIE_SECRET}_{email}".encode()).hexdigest()[:32]

def _verify_token(email: str, token: str) -> bool:
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

def attempt_login(email: str, password: str) -> tuple:
    if not email or not password:
        return False, t("Please enter email and password.", "يرجى إدخال البريد الإلكتروني وكلمة المرور.")
    login_candidates = []
    if "LOGIN" in st.secrets:
        login_candidates.append(("LOGIN", st.secrets["LOGIN"]))
    for key in SYSTEM_KEYS:
        cfg = st.secrets.get(key)
        if cfg and cfg.get("url") and cfg.get("db"):
            login_candidates.append((key, cfg))
    if not login_candidates:
        return False, t("No Odoo connection configured in secrets.", "لا يوجد اتصال Odoo مُكوَّن.")
    last_error = ""
    for source_key, cfg in login_candidates:
        url = cfg.get("url", "").rstrip("/")
        db = cfg.get("db", "")
        if not url or not db:
            last_error = f"[{source_key}] Missing url or db."
            continue
        try:
            proxy = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid = proxy.authenticate(db, email, password, {})
            if uid and isinstance(uid, int) and uid > 0:
                return True, ""
            else:
                last_error = t(f"Login failed for {email} on {db}.", f"فشل تسجيل الدخول لـ {email} على {db}.")
        except xmlrpc.client.Fault as e:
            last_error = f"[{source_key}] Odoo error: {e.faultString}"
        except ConnectionRefusedError:
            last_error = f"[{source_key}] Connection refused: {url}"
        except OSError as e:
            last_error = f"[{source_key}] Network error: {e}"
        except Exception as e:
            last_error = f"[{source_key}] Error: {type(e).__name__}: {e}"
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
# SECTION 7: XML-RPC HELPERS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def _get_proxy(url: str, endpoint: str):
    return xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/{endpoint}", allow_none=True)

@st.cache_data(ttl=28800, show_spinner=False)
def _odoo_auth(url: str, db: str, user: str, api_key: str):
    try:
        uid = _get_proxy(url, "common").authenticate(db, user, api_key, {})
        return uid if (uid and isinstance(uid, int) and uid > 0) else None
    except Exception:
        return None

def _odoo_call(url, db, uid, api_key, model, method, domain, kwargs):
    return _get_proxy(url, "object").execute_kw(db, uid, api_key, model, method, domain, kwargs)

def _get_system_conn(key: str) -> tuple:
    cfg = st.secrets.get(key)
    if not cfg:
        return None, None, None, None, key, f"[{key}] Not configured."
    url = cfg.get("url", "").rstrip("/")
    db = cfg.get("db", "")
    user = cfg.get("user", "")
    api_key = cfg.get("api_key", "")
    name = get_system_name(key)
    if not url:
        return None, None, None, None, name, f"[{key}] Missing 'url'."
    if not db:
        return None, None, None, None, name, f"[{key}] Missing 'db'."
    if not user or not api_key:
        return None, None, None, None, name, f"[{key}] Missing 'user' or 'api_key'."
    uid = _odoo_auth(url, db, user, api_key)
    if not uid:
        return url, db, None, api_key, name, f"[{key}] Auth failed."
    return url, db, uid, api_key, name, None

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: DATA UTILITIES (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
_NUMERIC_RAW = ["Sale Price", "On Hand", "Purchase Qty", "Qty", "Unit Price", "Subtotal", "Total Amount"]

def coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    for c in _NUMERIC_RAW:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def safe_get_col(df: pd.DataFrame, raw_name: str) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    if raw_name in df.columns:
        return pd.to_numeric(df[raw_name], errors="coerce").fillna(0)
    localized = col(raw_name)
    if localized in df.columns:
        return pd.to_numeric(df[localized], errors="coerce").fillna(0)
    return pd.Series([0.0] * len(df))

def safe_get_str_col(df: pd.DataFrame, raw_name: str) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=str)
    if raw_name in df.columns:
        return df[raw_name]
    localized = col(raw_name)
    if localized in df.columns:
        return df[localized]
    return pd.Series([""] * len(df))

def has_col(df: pd.DataFrame, raw_name: str) -> bool:
    if df is None or df.empty:
        return False
    return (raw_name in df.columns) or (col(raw_name) in df.columns)

def get_display_col(df: pd.DataFrame, raw_name: str) -> str:
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
    return output.getvalue()

def to_excel_branch_matrix(branch_df: pd.DataFrame) -> bytes:
    if branch_df is None or branch_df.empty:
        return b""
    branch_c = get_display_col(branch_df, "Branch")
    model_c = get_display_col(branch_df, "Model Code")
    qty_c = get_display_col(branch_df, "On Hand")
    if branch_c not in branch_df.columns or model_c not in branch_df.columns:
        return b""
    try:
        pivot = branch_df.pivot_table(index=model_c, columns=branch_c, values=qty_c, aggfunc="sum", fill_value=0)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pivot.to_excel(writer, sheet_name="Branch_Matrix")
        return output.getvalue()
    except Exception:
        return b""

def dl_name(prefix: str, ext: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: PAGINATED TABLE RENDERER (unchanged logic, styling updated via CSS)
# ─────────────────────────────────────────────────────────────────────────────
def render_paginated_table(df: pd.DataFrame, page_key: str, rows_per_page: int = ROWS_PER_PAGE):
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data to display.','لا توجد بيانات للعرض.')}</div>", unsafe_allow_html=True)
        return
    if len(df.columns) == 0:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('Data has no columns.','البيانات ليس لها أعمدة.')}</div>", unsafe_allow_html=True)
        return
    total_rows = len(df)
    total_pages = max(1, math.ceil(total_rows / rows_per_page))
    current = min(st.session_state.get(page_key, 0), total_pages - 1)
    st.session_state[page_key] = current
    start = current * rows_per_page
    end = min(start + rows_per_page, total_rows)
    page_df = df.iloc[start:end]
    display_df = localize_df(page_df)
    header_html = "".join(f"<th>{c}</th>" for c in display_df.columns)
    rows_html = ""
    for _, row in display_df.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row.values)
        rows_html += f"<tr>{cells}</tr>"
    st.markdown(
        f"<div class='dataframe-wrap'><table><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='pagination-bar'><span class='page-info'>"
        f"{t('Showing','عرض')} {start+1}–{end} {t('of','من')} {total_rows} &nbsp;|&nbsp; "
        f"{t('Page','صفحة')} {current+1}/{total_pages}</span></div>",
        unsafe_allow_html=True,
    )
    c1, c2, _, c4, c5 = st.columns([1, 1, 2, 1, 1])
    if c1.button("⏮", key=f"{page_key}_first", use_container_width=True):
        st.session_state[page_key] = 0
        st.rerun()
    if c2.button("◀", key=f"{page_key}_prev", use_container_width=True):
        st.session_state[page_key] = max(0, current - 1)
        st.rerun()
    if c4.button("▶", key=f"{page_key}_next", use_container_width=True):
        st.session_state[page_key] = min(total_pages - 1, current + 1)
        st.rerun()
    if c5.button("⏭", key=f"{page_key}_last", use_container_width=True):
        st.session_state[page_key] = total_pages - 1
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: VISUALIZATION ENGINE (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def apply_plotly_theme(fig):
    if fig is None:
        return fig
    a1 = th_color("accent1")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=th("text"), family="Inter", size=12),
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=th("border"), font=dict(size=11)),
        title_font=dict(size=14, color=th("text_label"), family="Inter"),
    )
    fig.update_xaxes(gridcolor=th("border"), linecolor=th("border"), tickfont=dict(size=11))
    fig.update_yaxes(gridcolor=th("border"), linecolor=th("border"), tickfont=dict(size=11))
    return fig

def render_visualization(df: pd.DataFrame, viz_mode: str, x_raw: str, y_raw: str, label: str = "", color_raw: str = None):
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data for visualization.','لا توجد بيانات للتصور.')}</div>", unsafe_allow_html=True)
        return
    x_col = get_display_col(df, x_raw)
    y_col = get_display_col(df, y_raw)
    if x_col not in df.columns:
        st.warning(f"⚠️ {t('Column not found','العمود غير موجود')}: {x_raw}")
        return
    if y_col not in df.columns:
        st.warning(f"⚠️ {t('Column not found','العمود غير موجود')}: {y_raw}")
        return
    colors = th("plotly_colors")
    tmpl = th("plotly_template")
    a1 = th_color("accent1")
    a2 = th_color("accent2")
    a1_fill = hex_to_rgba(a1, 0.2)
    df_plot = df.copy()
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce").fillna(0)
    x_label = col(x_raw)
    y_label = col(y_raw)
    if viz_mode == "📋 List View":
        render_paginated_table(df, f"viz_table_{abs(hash(label or x_raw)) % 10**8}")
        return
    df_agg = df_plot.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False)
    if viz_mode == "🏆 KPI Tiles":
        top_n = df_agg.head(8)
        icons = ["📦", "🏆", "⭐", "💎", "🔥", "📈", "🎯", "✅"]
        cols_n = min(4, len(top_n))
        if cols_n == 0:
            return
        tile_cols = st.columns(cols_n)
        for i, (_, row) in enumerate(top_n.iterrows()):
            with tile_cols[i % cols_n]:
                st.markdown(
                    f"<div class='kpi-tile'><div class='kpi-icon'>{icons[i % len(icons)]}</div>"
                    f"<div class='kpi-value'>{row[y_col]:,.0f}</div>"
                    f"<div class='kpi-label'>{str(row[x_col])[:22]}</div></div>",
                    unsafe_allow_html=True,
                )
        return
    elif viz_mode == "📊 Column Chart":
        fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label, color=y_col,
                     color_continuous_scale=[a1, a2], template=tmpl, text_auto=".2s",
                     labels={x_col: x_label, y_col: y_label})
        fig.update_traces(marker_line_width=0)
    elif viz_mode == "📉 Horizontal Bar":
        fig = px.bar(df_agg.head(15), x=y_col, y=x_col, orientation="h", title=label, color=y_col,
                     color_continuous_scale=[a1, a2], template=tmpl, text_auto=".2s",
                     labels={x_col: x_label, y_col: y_label})
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(marker_line_width=0)
    elif viz_mode == "📈 Line Chart":
        fig = px.line(df_agg.head(30), x=x_col, y=y_col, title=label, markers=True,
                      template=tmpl, color_discrete_sequence=[a1],
                      labels={x_col: x_label, y_col: y_label})
        fig.update_traces(line_width=2.5, marker_size=7, line_color=a1, marker_color=a2)
    elif viz_mode == "📉 Area Chart":
        fig = px.area(df_agg.head(30), x=x_col, y=y_col, title=label, template=tmpl,
                      color_discrete_sequence=[a1], labels={x_col: x_label, y_col: y_label})
        fig.update_traces(fillcolor=a1_fill, line_color=a1, line_width=2.5)
    elif viz_mode == "🍕 Pie Chart":
        top_n = df_agg.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, title=label,
                     color_discrete_sequence=colors, template=tmpl, hole=0)
        fig.update_traces(textposition="inside", textinfo="percent+label")
    elif viz_mode == "🍩 Donut Chart":
        top_n = df_agg.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, hole=0.58, title=label,
                     color_discrete_sequence=colors, template=tmpl)
        fig.update_traces(textposition="inside", textinfo="percent+label")
    elif viz_mode == "📊 Stacked Column":
        sys_col = get_display_col(df_plot, "System")
        stack_by = get_display_col(df_plot, color_raw) if color_raw else (sys_col if sys_col in df_plot.columns else None)
        if stack_by and stack_by in df_plot.columns:
            df_stack = df_plot.groupby([x_col, stack_by])[y_col].sum().reset_index()
            fig = px.bar(df_stack, x=x_col, y=y_col, color=stack_by, title=label,
                         barmode="stack", template=tmpl, color_discrete_sequence=colors,
                         labels={x_col: x_label, y_col: y_label})
        else:
            fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label, template=tmpl,
                         color_discrete_sequence=colors, text_auto=".2s",
                         labels={x_col: x_label, y_col: y_label})
    elif viz_mode == "🔘 Scatter Chart":
        fig = px.scatter(df_agg.head(30), x=x_col, y=y_col, title=label, size=y_col, color=y_col,
                         color_continuous_scale=[a1, a2], template=tmpl, size_max=50,
                         labels={x_col: x_label, y_col: y_label})
    elif viz_mode == "🗂️ Funnel Chart":
        top_n = df_agg.head(10)
        fig = go.Figure(go.Funnel(
            y=top_n[x_col].astype(str), x=top_n[y_col],
            textinfo="value+percent initial", marker_color=colors[:len(top_n)],
        ))
        fig.update_layout(title=label)
    elif viz_mode == "📡 Radar Chart":
        top_n = df_agg.head(8)
        cats = top_n[x_col].astype(str).tolist()
        vals = top_n[y_col].tolist()
        if len(cats) < 3:
            st.info(t("Radar chart needs ≥3 data points.", "مخطط الرادار يحتاج 3 نقاط على الأقل."))
            return
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", fillcolor=a1_fill, line_color=a1, line_width=2,
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, gridcolor=th("border")),
                angularaxis=dict(gridcolor=th("border")),
            ), title=label,
        )
    else:
        fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label, template=tmpl,
                     color_discrete_sequence=colors)
    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

def viz_mode_selector(state_key: str) -> str:
    return st.selectbox(
        f"📊 {t('Visualization Mode','نمط العرض')}",
        VIZ_MODES,
        index=VIZ_MODES.index(st.session_state.get(state_key, "📋 List View")),
        key=state_key,
    )

def render_daily_trend_chart(df: pd.DataFrame, date_raw: str, value_raw: str, title: str, color_key: str = "accent1"):
    if df is None or df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No data for trend chart.','لا توجد بيانات لمخطط الاتجاه.')}</div>", unsafe_allow_html=True)
        return
    date_c = get_display_col(df, date_raw)
    value_c = get_display_col(df, value_raw)
    if date_c not in df.columns:
        st.warning(f"⚠️ {t('Date column missing.','عمود التاريخ غير موجود.')}")
        return
    if value_c not in df.columns:
        st.warning(f"⚠️ {t('Value column missing.','عمود القيمة غير موجود.')}")
        return
    daily = df.copy()
    daily[date_c] = pd.to_datetime(daily[date_c], errors="coerce").dt.date
    daily = daily[pd.notna(daily[date_c])].copy()
    daily[value_c] = pd.to_numeric(daily[value_c], errors="coerce").fillna(0)
    trend = daily.groupby(date_c)[value_c].sum().reset_index().sort_values(date_c)
    if trend.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No date data for trend.','لا توجد بيانات تواريخ.')}</div>", unsafe_allow_html=True)
        return
    a = th_color(color_key)
    a_fill = hex_to_rgba(a, 0.18)
    fig = px.area(
        trend, x=date_c, y=value_c, title=title,
        template=th("plotly_template"),
        color_discrete_sequence=[a],
        labels={date_c: col(date_raw), value_c: col(value_raw)},
    )
    fig.update_traces(
        fillcolor=a_fill,
        line_color=a,
        line_width=2.5,
    )
    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

def render_exec_summary(df, value_raw, label_raw, section_title, top_n=5, bottom_n=3):
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
    border_v = th("border")
    a1_c = th_color("accent1")
    danger_c = th_color("danger", "#dc2626")
    with c1:
        st.markdown(f"**🏆 {t('Top Performers','أفضل الأداء')}**")
        html = "<div class='exec-card'>"
        for i, (_, row) in enumerate(agg.head(top_n).iterrows()):
            m = medals[i] if i < len(medals) else f"{i+1}."
            html += (
                f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
                f"border-bottom:1px solid {border_v};'>"
                f"<span>{m} {str(row[label_c])[:30]}</span>"
                f"<b style='color:{a1_c}'>{row[value_c]:,.0f}</b></div>"
            )
        st.markdown(html + "</div>", unsafe_allow_html=True)
    with c2:
        if len(agg) > top_n:
            st.markdown(f"**⚠️ {t('Needs Attention','يحتاج اهتماماً')}**")
            html = "<div class='exec-card'>"
            for _, row in agg.tail(bottom_n).sort_values(value_c).iterrows():
                html += (
                    f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
                    f"border-bottom:1px solid {border_v};'>"
                    f"<span>⚠️ {str(row[label_c])[:30]}</span>"
                    f"<b style='color:{danger_c}'>{row[value_c]:,.0f}</b></div>"
                )
            st.markdown(html + "</div>", unsafe_allow_html=True)

def show_diag(diag_list: list):
    if not diag_list:
        return
    has_err = any(d.get("level") == "error" for d in diag_list)
    has_ok = any(d.get("level") == "ok" for d in diag_list)
    if has_err:
        with st.expander(f"⚠️ {t('Load Diagnostics (errors found)','تشخيص التحميل (توجد أخطاء)')}"):
            for d in diag_list:
                icon = "✅" if d.get("level") == "ok" else "❌"
                st.markdown(f"`{icon} [{d.get('system','')}] {d.get('msg','')}`")
    elif has_ok:
        with st.expander(f"✅ {t('Load Diagnostics (all OK)','تشخيص التحميل (كل شيء سليم)')}"):
            for d in diag_list:
                st.markdown(f"`✅ [{d.get('system','')}] {d.get('msg','')}`")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11: DATA FETCHERS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_inventory_one(key: str, codes_tuple: tuple, exact: bool) -> tuple:
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
                              {"fields": ["id", "name", "default_code", "list_price"], "limit": 5000})
        if not products:
            return [], [], {"system": name, "level": "ok", "msg": "No products found."}
        prod_ids = [p["id"] for p in products]
        tmpl_to_model = {p["id"]: (p.get("default_code") or "").strip() for p in products}
        tmpl_to_name = {p["id"]: p.get("name", "") for p in products}
        tmpl_to_price = {p["id"]: float(p.get("list_price") or 0) for p in products}
        variant_products = _odoo_call(url, db, uid, ak, "product.product", "search_read",
                                      [[("product_tmpl_id", "in", prod_ids)]],
                                      {"fields": ["id", "product_tmpl_id"], "limit": 50000})
        variant_to_tmpl = {}
        for vp in variant_products:
            t_raw = vp.get("product_tmpl_id")
            tmpl_id_v = t_raw if isinstance(t_raw, int) else (t_raw[0] if isinstance(t_raw, list) else t_raw)
            variant_to_tmpl[vp["id"]] = tmpl_id_v
        variant_ids = list(variant_to_tmpl.keys())
        quants = _odoo_call(url, db, uid, ak, "stock.quant", "search_read",
                            [[("product_id", "in", variant_ids), ("location_id.usage", "=", "internal")]],
                            {"fields": ["product_id", "location_id", "quantity"], "limit": 50000})
        tmpl_qty: dict = {}
        branch_rows = []
        for q in quants:
            pid_raw = q.get("product_id")
            variant_id = pid_raw if isinstance(pid_raw, int) else (pid_raw[0] if isinstance(pid_raw, list) else pid_raw)
            tmpl_id = variant_to_tmpl.get(variant_id, variant_id)
            qty = float(q.get("quantity") or 0)
            tmpl_qty[tmpl_id] = tmpl_qty.get(tmpl_id, 0) + qty
            loc = q.get("location_id")
            loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
            mc_val = tmpl_to_model.get(tmpl_id, "")
            if mc_val:
                branch_rows.append({"System": name, "Branch": loc_name, "Model Code": mc_val, "On Hand": qty})
        total_rows = []
        for tmpl_id in prod_ids:
            total_rows.append({
                "System": name,
                "Model Code": tmpl_to_model.get(tmpl_id, ""),
                "Product": tmpl_to_name.get(tmpl_id, ""),
                "Sale Price": tmpl_to_price.get(tmpl_id, 0),
                "On Hand": tmpl_qty.get(tmpl_id, 0),
            })
        return total_rows, branch_rows, {"system": name, "level": "ok", "msg": f"Loaded {len(total_rows)} products, {len(quants)} quant records."}
    except Exception as e:
        return [], [], {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_inventory(selected_keys: list, codes_tuple: tuple = (), exact: bool = False):
    all_total, all_branch, diag = [], [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_inventory_one, k, codes_tuple, exact): k for k in selected_keys}
        for f in as_completed(futs):
            total_rows, branch_rows, d = f.result()
            all_total += total_rows
            all_branch += branch_rows
            diag.append(d)
    total_df = pd.DataFrame(all_total) if all_total else pd.DataFrame(columns=["System", "Model Code", "Product", "Sale Price", "On Hand"])
    branch_df = (pd.DataFrame(all_branch)[["System", "Branch", "Model Code", "On Hand"]]
                 if all_branch else pd.DataFrame(columns=["System", "Branch", "Model Code", "On Hand"]))
    return coerce_numerics(total_df), coerce_numerics(branch_df), diag

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_purchase_summary_one(key: str, model_codes_tuple: tuple, date_from: str, date_to: str) -> pd.DataFrame:
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return pd.DataFrame()
    try:
        domain = [
            ["order_id.date_approve", ">=", f"{date_from} 00:00:00"],
            ["order_id.date_approve", "<=", f"{date_to} 23:59:59"],
            ["order_id.state", "in", ["purchase", "done"]],
            ["product_id.default_code", "in", list(model_codes_tuple)],
        ]
        lines = _odoo_call(url, db, uid, ak, "purchase.order.line", "search_read",
                           [domain], {"fields": ["product_id", "product_qty"], "limit": 10000})
        if not lines:
            return pd.DataFrame()
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _odoo_call(url, db, uid, ak, "product.product", "search_read",
                              [[["id", "in", prod_ids]]],
                              {"fields": ["id", "default_code"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p.get("default_code", "") for p in products}
        rows = []
        for line in lines:
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
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

def fetch_purchase_summary(selected_keys, model_codes_tuple, date_from, date_to):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(_fetch_purchase_summary_one, k, model_codes_tuple, date_from, date_to) for k in selected_keys]
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])
    combined = pd.concat(results, ignore_index=True)
    return combined.groupby("Model Code")["Purchase Qty"].sum().reset_index()

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_purchase_one(key: str, model_filter: str, date_from: str, date_to: str) -> tuple:
    _empty = pd.DataFrame(columns=["System", "Date", "PO", "Vendor", "Receipt Location", "Category", "Model Code", "Product", "Qty", "Unit Price", "Subtotal"])
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return _empty, {"system": name, "level": "error", "msg": err}
    try:
        po_domain = [
            ["date_approve", ">=", f"{date_from} 00:00:00"],
            ["date_approve", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["purchase", "done"]],
        ]
        pos_list = _odoo_call(url, db, uid, ak, "purchase.order", "search_read",
                              [po_domain], {"fields": ["id", "name", "partner_id", "date_approve", "state"], "limit": 2000})
        if not pos_list:
            return _empty, {"system": name, "level": "ok", "msg": "No purchase orders found."}
        po_ids = [p["id"] for p in pos_list]
        po_map = {p["id"]: p for p in pos_list}
        lines = _odoo_call(url, db, uid, ak, "purchase.order.line", "search_read",
                           [[["order_id", "in", po_ids]]],
                           {"fields": ["order_id", "product_id", "product_qty", "price_unit", "price_subtotal"], "limit": 20000})
        if not lines:
            return _empty, {"system": name, "level": "ok", "msg": "No purchase lines found."}
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _odoo_call(url, db, uid, ak, "product.product", "search_read",
                              [[["id", "in", prod_ids]]],
                              {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p for p in products}
        pickings = _odoo_call(url, db, uid, ak, "stock.picking", "search_read",
                              [[["origin", "in", [p["name"] for p in pos_list]], ["picking_type_code", "=", "incoming"]]],
                              {"fields": ["origin", "location_dest_id"], "limit": 2000})
        receipt_map = {}
        for pick in pickings:
            loc = pick.get("location_dest_id")
            loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
            receipt_map[pick.get("origin", "")] = loc_name
        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            po = po_map.get(oid, {})
            if not po:
                continue
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})
            mc_val = (prod.get("default_code") or "").strip()
            if model_filter and not mc_val.upper().startswith(model_filter.upper()):
                continue
            categ_obj = prod.get("categ_id")
            category = categ_obj[1] if isinstance(categ_obj, list) and len(categ_obj) > 1 else ""
            partner = po.get("partner_id")
            vendor = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            rows.append({
                "System": name, "Date": str(po.get("date_approve", ""))[:10],
                "PO": po.get("name", ""), "Vendor": vendor,
                "Receipt Location": receipt_map.get(po.get("name", ""), ""),
                "Category": category, "Model Code": mc_val,
                "Product": prod.get("name", ""),
                "Qty": float(line.get("product_qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
            })
        if not rows:
            return _empty, {"system": name, "level": "ok", "msg": "Filters produced no rows."}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = coerce_numerics(df)
        return df.sort_values("Date", ascending=False).reset_index(drop=True), {"system": name, "level": "ok", "msg": f"Loaded {len(df)} purchase lines."}
    except Exception as e:
        return _empty, {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_purchase(selected_keys, model_filter, date_from, date_to):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_purchase_one, k, model_filter, date_from, date_to): k for k in selected_keys}
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

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_pos_one(key: str, date_from: str, date_to: str, branch_filter: str, model_filter: str) -> tuple:
    _empty = pd.DataFrame(columns=["System", "Date", "POS Order", "Branch", "Customer", "Cashier", "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "Total Amount"])
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return _empty, {"system": name, "level": "error", "msg": err}
    try:
        order_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["paid", "done", "invoiced"]],
        ]
        orders = _odoo_call(url, db, uid, ak, "pos.order", "search_read",
                            [order_domain],
                            {"fields": ["id", "name", "date_order", "amount_total", "user_id", "session_id", "partner_id", "lines"], "limit": 5000})
        if not orders:
            return _empty, {"system": name, "level": "ok", "msg": "No POS orders found."}
        session_ids = list({o["session_id"][0] for o in orders if o.get("session_id")})
        branch_map = {}
        if session_ids:
            sessions = _odoo_call(url, db, uid, ak, "pos.session", "search_read",
                                  [[["id", "in", session_ids]]],
                                  {"fields": ["id", "config_id"], "limit": len(session_ids) + 10})
            config_ids = list({s["config_id"][0] for s in sessions if s.get("config_id")})
            if config_ids:
                configs = _odoo_call(url, db, uid, ak, "pos.config", "search_read",
                                     [[["id", "in", config_ids]]],
                                     {"fields": ["id", "name"], "limit": len(config_ids) + 10})
                config_name = {c["id"]: c["name"] for c in configs}
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
                           [[["id", "in", line_ids]]],
                           {"fields": ["order_id", "product_id", "qty", "price_unit", "price_subtotal"], "limit": 20000})
        if not lines:
            return _empty, {"system": name, "level": "ok", "msg": "No POS lines returned."}
        order_map = {o["id"]: o for o in orders}
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = (_odoo_call(url, db, uid, ak, "product.product", "search_read",
                               [[["id", "in", prod_ids]]],
                               {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 20})
                    if prod_ids else [])
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
            if branch_filter and branch_filter.lower() not in branch_name.lower():
                continue
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})
            mc_val = (prod.get("default_code") or "").strip()
            if model_filter and not mc_val.upper().startswith(model_filter.upper()):
                continue
            partner = order.get("partner_id")
            customer = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            user = order.get("user_id")
            cashier = user[1] if isinstance(user, list) and len(user) > 1 else ""
            rows.append({
                "System": name, "Date": str(order.get("date_order", ""))[:10],
                "POS Order": order.get("name", ""), "Branch": branch_name,
                "Customer": customer, "Cashier": cashier, "Model Code": mc_val,
                "Product": prod.get("name", ""),
                "Qty": float(line.get("qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
            })
        if not rows:
            return _empty, {"system": name, "level": "ok", "msg": "Filters produced no POS rows."}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = coerce_numerics(df)
        return df.sort_values("Date", ascending=False).reset_index(drop=True), {"system": name, "level": "ok", "msg": f"Loaded {len(df)} POS lines."}
    except Exception as e:
        return _empty, {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_pos(selected_keys, date_from, date_to, branch_filter, model_filter):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_pos_one, k, date_from, date_to, branch_filter, model_filter): k for k in selected_keys}
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

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_sales_one(key: str, date_from: str, date_to: str, model_filter: str) -> tuple:
    _empty = pd.DataFrame(columns=["System", "Date", "SO", "Customer", "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "Total Amount", "State"])
    url, db, uid, ak, name, err = _get_system_conn(key)
    if err:
        return _empty, {"system": name, "level": "error", "msg": err}
    try:
        so_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["sale", "done"]],
        ]
        orders = _odoo_call(url, db, uid, ak, "sale.order", "search_read",
                            [so_domain],
                            {"fields": ["id", "name", "date_order", "amount_total", "partner_id", "state", "order_line"], "limit": 5000})
        if not orders:
            return _empty, {"system": name, "level": "ok", "msg": "No sales orders found."}
        order_map = {o["id"]: o for o in orders}
        line_ids = []
        for o in orders:
            if o.get("order_line"):
                line_ids.extend(o["order_line"])
        if not line_ids:
            return _empty, {"system": name, "level": "ok", "msg": "No sales lines found."}
        lines = _odoo_call(url, db, uid, ak, "sale.order.line", "search_read",
                           [[["id", "in", line_ids]]],
                           {"fields": ["order_id", "product_id", "product_uom_qty", "price_unit", "price_subtotal"], "limit": 20000})
        if not lines:
            return _empty, {"system": name, "level": "ok", "msg": "No sale.order.line data."}
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = (_odoo_call(url, db, uid, ak, "product.product", "search_read",
                               [[["id", "in", prod_ids]]],
                               {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 20})
                    if prod_ids else [])
        prod_map = {p["id"]: p for p in products}
        rows = []
        for line in lines:
            oid_raw = line.get("order_id")
            oid = oid_raw[0] if isinstance(oid_raw, list) else oid_raw
            order = order_map.get(oid)
            if not order:
                continue
            pid_raw = line.get("product_id")
            pid = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
            prod = prod_map.get(pid, {})
            mc_val = (prod.get("default_code") or "").strip()
            if model_filter and not mc_val.upper().startswith(model_filter.upper()):
                continue
            partner = order.get("partner_id")
            customer = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            rows.append({
                "System": name, "Date": str(order.get("date_order", ""))[:10],
                "SO": order.get("name", ""), "Customer": customer, "Model Code": mc_val,
                "Product": prod.get("name", ""),
                "Qty": float(line.get("product_uom_qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
                "State": order.get("state", ""),
            })
        if not rows:
            return _empty, {"system": name, "level": "ok", "msg": "Filters produced no sales rows."}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = coerce_numerics(df)
        return df.sort_values("Date", ascending=False).reset_index(drop=True), {"system": name, "level": "ok", "msg": f"Loaded {len(df)} sales lines."}
    except Exception as e:
        return _empty, {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}

def fetch_sales(selected_keys, date_from, date_to, model_filter):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_sales_one, k, date_from, date_to, model_filter): k for k in selected_keys}
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
# SECTION 12: AI INSIGHTS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def _insight_block(rows_data: list) -> str:
    inner = "".join(
        f"<div class='chat-insight-row'><span class='chat-insight-key'>{k}</span><span class='chat-insight-val'>{v}</span></div>"
        for k, v in rows_data
    )
    return f"<div class='chat-insight-block'>{inner}</div>"

def get_ai_response(user_msg: str) -> tuple:
    msg = user_msg.lower().strip()
    inv_df = st.session_state.get("inventory_df")
    pos_df = st.session_state.get("pos_df")
    sales_df = st.session_state.get("sales_df")
    pur_df = st.session_state.get("purchase_df")

    def _sum(df, raw):
        return safe_get_col(df, raw).sum() if df is not None else 0

    def _nunique(df, raw):
        if df is None or df.empty:
            return 0
        c = get_display_col(df, raw)
        return df[c].nunique() if c in df.columns else 0

    def _top(df, group_raw, val_raw, n=8):
        if df is None or df.empty:
            return pd.Series(dtype=float)
        gc = get_display_col(df, group_raw)
        vc = get_display_col(df, val_raw)
        if gc not in df.columns or vc not in df.columns:
            return pd.Series(dtype=float)
        return df.groupby(gc)[vc].sum().sort_values(ascending=False).head(n)

    if any(k in msg for k in ["inventory", "stock", "مخزون", "zero", "low stock", "top product", "fast", "slow"]):
        if inv_df is None or inv_df.empty:
            return (t("📦 No inventory data loaded.", "📦 لم يتم تحميل بيانات المخزون."), None)
        qty_s = safe_get_col(inv_df, "On Hand")
        price_s = safe_get_col(inv_df, "Sale Price")
        total_qty = int(qty_s.sum())
        total_value = float((qty_s * price_s).sum())
        zero_count = int((qty_s == 0).sum())
        low_count = int(((qty_s > 0) & (qty_s <= 5)).sum())
        models = _nunique(inv_df, "Model Code")
        if any(k in msg for k in ["zero", "صفر"]):
            mc_col_n = get_display_col(inv_df, "Model Code")
            zero_mc = inv_df[qty_s == 0][mc_col_n].dropna().head(8).tolist() if mc_col_n in inv_df.columns else []
            insight = _insight_block([
                (t("Zero Stock Models", "موديلات بدون مخزون"), str(zero_count)),
                (t("Examples", "أمثلة"), ", ".join(str(x) for x in zero_mc[:4])),
                (t("Action", "إجراء"), t("Urgent Reorder", "إعادة طلب عاجل")),
            ])
            return (t(f"🔴 {zero_count} products have zero stock.", f"🔴 {zero_count} منتج بدون مخزون."), insight)
        if any(k in msg for k in ["low", "منخفض"]):
            insight = _insight_block([
                (t("Low Stock (≤5)", "مخزون منخفض"), str(low_count)),
                (t("Zero Stock", "صفر مخزون"), str(zero_count)),
            ])
            return (t(f"⚠️ {low_count} low stock, {zero_count} out of stock.", f"⚠️ {low_count} منخفض، {zero_count} صفر."), insight)
        if any(k in msg for k in ["top", "أعلى", "fast", "best"]):
            top = _top(inv_df, "Model Code", "On Hand")
            insight = _insight_block([(str(k), f"{int(v):,}") for k, v in top.items()])
            return (t("🏆 Top models by stock qty:", "🏆 أعلى موديلات:"), insight)
        risk = t("High Risk", "خطر عالٍ") if zero_count > 50 else (t("Moderate", "معتدل") if zero_count > 20 else t("Low Risk", "خطر منخفض"))
        insight = _insight_block([
            (t("Total Qty", "إجمالي الكمية"), f"{total_qty:,}"),
            (t("Total Value (SAR)", "القيمة"), f"{total_value:,.0f}"),
            (t("Models", "الموديلات"), f"{models:,}"),
            (t("Zero Stock", "صفر مخزون"), f"{zero_count:,}"),
            (t("Low Stock (≤5)", "منخفض"), f"{low_count:,}"),
        ])
        return (t(f"📦 Inventory — Risk: {risk}", f"📦 المخزون — الخطر: {risk}"), insight)

    if any(k in msg for k in ["pos", "cashier", "كاشير", "نقطة بيع", "branch", "فرع"]):
        if pos_df is None or pos_df.empty:
            return (t("🛒 No POS data loaded.", "🛒 لا توجد بيانات POS."), None)
        po_col_n = get_display_col(pos_df, "POS Order")
        unique = pos_df.drop_duplicates(subset=[po_col_n]) if po_col_n in pos_df.columns else pos_df
        total = float(safe_get_col(unique, "Total Amount").sum())
        bills = len(unique)
        avg = total / bills if bills > 0 else 0
        if any(k in msg for k in ["cashier", "كاشير"]):
            top = _top(unique, "Cashier", "Total Amount")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("👤 Cashier rankings:", "👤 ترتيب الكاشيرين:"), insight)
        if any(k in msg for k in ["branch", "فرع"]):
            top = _top(unique, "Branch", "Total Amount")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("🏪 Branch POS performance:", "🏪 أداء فروع POS:"), insight)
        insight = _insight_block([
            (t("Revenue (SAR)", "الإيرادات"), f"{total:,.0f}"),
            (t("Bills", "الفواتير"), f"{bills:,}"),
            (t("Avg Bill", "متوسط الفاتورة"), f"{avg:,.2f}"),
        ])
        return (t(f"🛒 POS — {bills:,} bills, SAR {total:,.0f}", f"🛒 POS — {bills:,} فاتورة"), insight)

    if any(k in msg for k in ["sale", "مبيعات", "customer", "عميل", "revenue"]):
        if sales_df is None or sales_df.empty:
            return (t("🛍️ No sales data loaded.", "🛍️ لا توجد بيانات مبيعات."), None)
        so_c_n = get_display_col(sales_df, "SO")
        unique = sales_df.drop_duplicates(subset=[so_c_n]) if so_c_n in sales_df.columns else sales_df
        total = float(safe_get_col(unique, "Total Amount").sum())
        orders = _nunique(unique, "SO")
        avg = total / orders if orders > 0 else 0
        if any(k in msg for k in ["customer", "عميل", "top customer"]):
            top = _top(unique, "Customer", "Total Amount")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("👥 Top customers:", "👥 أفضل العملاء:"), insight)
        insight = _insight_block([
            (t("Revenue (SAR)", "الإيراد"), f"{total:,.0f}"),
            (t("Orders", "الطلبات"), f"{orders:,}"),
            (t("Avg Order", "متوسط الطلب"), f"{avg:,.2f}"),
        ])
        return (t(f"🛍️ Sales — {orders:,} orders, SAR {total:,.0f}", f"🛍️ المبيعات — {orders:,} طلب"), insight)

    if any(k in msg for k in ["purchase", "مشتريات", "vendor", "مورد", "po"]):
        if pur_df is None or pur_df.empty:
            return (t("🔖 No purchase data loaded.", "🔖 لا توجد بيانات مشتريات."), None)
        total_val = float(safe_get_col(pur_df, "Subtotal").sum())
        total_qty = float(safe_get_col(pur_df, "Qty").sum())
        vendors = _nunique(pur_df, "Vendor")
        if any(k in msg for k in ["vendor", "مورد", "supplier"]):
            top = _top(pur_df, "Vendor", "Subtotal")
            insight = _insight_block([(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()])
            return (t("🏭 Top vendors:", "🏭 أفضل الموردين:"), insight)
        insight = _insight_block([
            (t("Spend (SAR)", "الإنفاق"), f"{total_val:,.0f}"),
            (t("Total Qty", "الكمية"), f"{total_qty:,.0f}"),
            (t("Vendors", "الموردون"), f"{vendors:,}"),
        ])
        return (t(f"🔖 Purchase — SAR {total_val:,.0f}", f"🔖 المشتريات — {total_val:,.0f} ر.س"), insight)

    if any(k in msg for k in ["overview", "dashboard", "all", "كل", "executive", "ملخص"]):
        data = []
        if inv_df is not None and not inv_df.empty:
            data.append((t("📦 Inventory Qty", "📦 المخزون"), f"{int(safe_get_col(inv_df, 'On Hand').sum()):,}"))
        if sales_df is not None and not sales_df.empty:
            so_c_n = get_display_col(sales_df, "SO")
            unique = sales_df.drop_duplicates(subset=[so_c_n]) if so_c_n in sales_df.columns else sales_df
            data.append((t("🛍️ Sales (SAR)", "🛍️ المبيعات"), f"{safe_get_col(unique, 'Total Amount').sum():,.0f}"))
        if pos_df is not None and not pos_df.empty:
            po_c_n = get_display_col(pos_df, "POS Order")
            unique = pos_df.drop_duplicates(subset=[po_c_n]) if po_c_n in pos_df.columns else pos_df
            data.append((t("🛒 POS (SAR)", "🛒 POS"), f"{safe_get_col(unique, 'Total Amount').sum():,.0f}"))
        if pur_df is not None and not pur_df.empty:
            data.append((t("🔖 Purchase (SAR)", "🔖 المشتريات"), f"{safe_get_col(pur_df, 'Subtotal').sum():,.0f}"))
        insight = _insight_block(data) if data else None
        return (t(f"💎 Executive Overview — {len(data)} modules", f"💎 نظرة تنفيذية — {len(data)} وحدات"), insight)

    return (
        t("🤖 Ask: inventory, zero stock, POS branches, top customers, vendors, executive overview.",
          "🤖 اسأل: مخزون، صفر مخزون، فروع POS، أفضل العملاء، الموردين، نظرة تنفيذية."),
        None,
    )

def show_chat_panel():
    st.markdown(f"<div class='section-header'>🤖 {t('Executive AI Insights','المساعد الذكي التنفيذي')}</div>", unsafe_allow_html=True)
    history_html = "<div style='max-height:460px;overflow-y:auto;padding:10px 4px;'>"
    if not st.session_state.chat_history:
        a1 = th_color("accent1")
        history_html += (
            f"<div style='text-align:center;padding:50px 20px;color:{th('text_muted')};'>"
            f"<div style='font-size:2.5rem;margin-bottom:14px;'>🤖</div>"
            f"<div style='font-size:0.9rem;font-weight:600;'>{t('Your AI executive assistant is ready.','مساعدك الذكي التنفيذي جاهز.')}</div>"
            f"<div style='font-size:0.78rem;margin-top:6px;'>{t('Ask about inventory, sales, POS, or purchasing.','اسأل عن المخزون، المبيعات، POS، أو المشتريات.')}</div>"
            f"</div>"
        )
    for msg_item in st.session_state.chat_history[-30:]:
        if msg_item["role"] == "user":
            history_html += f"<div class='chat-label-user'>{t('You','أنت')}</div><div class='chat-msg-user'>{msg_item['content']}</div>"
        else:
            history_html += f"<div class='chat-label-bot'>🤖 AI</div><div class='chat-msg-bot'>{msg_item['content'].replace(chr(10),'<br>')}</div>"
            if msg_item.get("insight_html"):
                history_html += msg_item["insight_html"]
    history_html += "</div>"
    st.markdown(history_html, unsafe_allow_html=True)

    chip_actions = [
        (t("💎 Overview", "💎 نظرة عامة"), t("executive overview", "نظرة تنفيذية")),
        (t("📦 Inventory", "📦 المخزون"), t("inventory summary", "ملخص المخزون")),
        (t("🔴 Zero Stock", "🔴 مخزون صفر"), t("zero stock", "مخزون صفر")),
        (t("🛒 POS Branches", "🛒 فروع POS"), t("POS branch sales", "مبيعات فروع POS")),
        (t("👥 Top Customers", "👥 أفضل العملاء"), t("top customers", "أفضل العملاء")),
        (t("🏭 Top Vendors", "🏭 أفضل الموردين"), t("top vendors", "أفضل الموردين")),
    ]
    chip_cols = st.columns(3)
    for i, (label, query) in enumerate(chip_actions):
        with chip_cols[i % 3]:
            if st.button(label, key=f"chip_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": label})
                text, insight = get_ai_response(query)
                st.session_state.chat_history.append({"role": "bot", "content": text, "insight_html": insight or ""})
                st.rerun()

    col_in, col_send, col_clear = st.columns([5, 1, 1])
    with col_in:
        user_input = st.text_input(
            t("Ask...", "اسأل..."), key="chat_input", label_visibility="collapsed",
            placeholder=t("e.g. zero stock, top customers, POS branch sales...", "مثال: صفر مخزون، أفضل العملاء..."),
        )
    with col_send:
        if st.button(t("Send", "إرسال"), type="primary", key="chat_send", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                text, insight = get_ai_response(user_input)
                st.session_state.chat_history.append({"role": "bot", "content": text, "insight_html": insight or ""})
                st.rerun()
    with col_clear:
        if st.button("🗑️", key="chat_clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13: LOGIN PAGE — REDESIGNED
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown(build_css(), unsafe_allow_html=True)
    st.markdown(f"""
    <div class="login-container">
        <div class="login-left">
            <div class="brand-block">
                <div class="brand-icon">💎</div>
                <div class="brand-name">SWAG Executive</div>
                <div style="margin-top: 1rem; color: {th("text_muted")}; font-size: 0.9rem;">
                    {t("Retail Operations Intelligence", "ذكاء عمليات التجزئة")}
                </div>
                <div style="margin-top: 2rem; font-size: 0.8rem; color: {th("text_muted")};">
                    {t("Multi-Company · Odoo Integration · Real-time Analytics", "متعدد الشركات · تكامل Odoo · تحليلات فورية")}
                </div>
            </div>
        </div>
        <div class="login-right">
            <div class="login-card">
                <div class="login-title">{t("Welcome back", "مرحباً بعودتك")}</div>
                <div class="login-subtitle">{t("Sign in to your executive dashboard", "سجل الدخول إلى لوحة التحكم التنفيذية")}</div>
    """, unsafe_allow_html=True)
    if st.session_state.get("login_error"):
        st.markdown(f"<div class='alert-banner'>❌ {st.session_state.login_error}</div>", unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input("Email / البريد الإلكتروني", placeholder="user@company.com")
        password = st.text_input("Password / كلمة المرور", type="password")
        submitted = st.form_submit_button("🚀 Sign In", type="primary", use_container_width=True)
        if submitted:
            with st.spinner(t("Authenticating...", "جاري التحقق...")):
                ok, err = attempt_login(email.strip(), password)
            if ok:
                st.session_state.authenticated = True
                st.session_state.user_email = email.strip()
                st.session_state.login_error = ""
                token = _make_token(email.strip())
                try:
                    st.query_params.update({"u": email.strip(), "t": token})
                except Exception:
                    pass
                st.rerun()
            else:
                st.session_state.login_error = err
                st.rerun()
    st.markdown("</div></div></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 14: DASHBOARD — REDESIGNED LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    st.markdown(build_css(), unsafe_allow_html=True)

    with st.sidebar:
        # Brand header
        st.markdown(
            f"""
            <div style="padding: 1.5rem 1rem; border-bottom: 1px solid {th("border")}; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.8rem;">
                    <span style="font-size: 2rem;">💎</span>
                    <div>
                        <div style="font-weight: 700; font-size: 1rem; color: {th("text")};">SWAG Executive</div>
                        <div style="font-size: 0.7rem; color: {th("text_muted")};">{st.session_state.user_email}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Theme selector
        new_theme = st.selectbox(
            f"🎨 {t('Theme','المظهر')}",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(get_theme()),
            key="theme_select",
        )
        if new_theme != get_theme():
            st.session_state.theme = new_theme
            st.rerun()
        # Language selector
        new_lang = st.radio(f"🌐 {t('Language','اللغة')}", ["EN", "AR"], index=0 if get_lang() == "EN" else 1, horizontal=True)
        if new_lang != get_lang():
            for k in ["inventory_df", "inventory_branch_df", "pos_df", "sales_df", "purchase_df", "inv_diag", "pos_diag", "sales_diag", "pur_diag"]:
                st.session_state[k] = None if "df" in k else []
            st.session_state.lang = new_lang
            _fetch_inventory_one.clear()
            _fetch_purchase_one.clear()
            _fetch_pos_one.clear()
            _fetch_sales_one.clear()
            st.rerun()
        st.divider()
        # System status
        st.markdown(f"**🏢 {t('Connected Systems','الأنظمة المتصلة')}**")
        for key in SYSTEM_KEYS:
            cfg = st.secrets.get(key, {})
            name = get_system_name(key)
            badge_color = th_color("success") if cfg.get("url") else th_color("danger")
            icon = "✓" if cfg.get("url") else "✗"
            st.markdown(f"<div style='margin:5px 0;'><span style='color:{badge_color};'>{icon}</span> {name}</div>", unsafe_allow_html=True)
        st.divider()
        # Loaded data with refresh timestamps
        st.markdown(f"**📊 {t('Loaded Data','البيانات المحملة')}**")
        for icon, name, df_key, ts_key in [
            ("📦", t("Inventory", "المخزون"), "inventory_df", "inv_last_refresh"),
            ("🛒", t("POS", "نقاط البيع"), "pos_df", "pos_last_refresh"),
            ("🛍️", t("Sales", "المبيعات"), "sales_df", "sales_last_refresh"),
            ("🔖", t("Purchase", "المشتريات"), "purchase_df", "pur_last_refresh"),
        ]:
            df = st.session_state.get(df_key)
            ts = st.session_state.get(ts_key)
            if df is not None and not df.empty:
                ts_str = f" ({ts.strftime('%H:%M')})" if ts else ""
                st.markdown(f"<div style='margin:3px 0;'>{icon} {name} ({len(df):,}){ts_str}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='margin:3px 0; color: {th('text_muted')};'>{icon} {name} —</div>", unsafe_allow_html=True)
        st.divider()
        if st.button(f"🚪 {t('Logout','تسجيل الخروج')}", use_container_width=True):
            do_logout()

    # Header
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <div>
                <h1 style="margin:0; font-weight: 700; font-size: 1.8rem; color: {th("text")};">SWAG Executive Operations</h1>
                <p style="margin:0; color: {th("text_muted")}; font-size: 0.85rem;">{t('Multi-Company · Inventory · POS · Sales · Purchasing · AI Insights','متعدد الشركات · المخزون · نقاط البيع · المبيعات · المشتريات · تحليلات ذكية')}</p>
            </div>
            <div style="background: {th("card_bg")}; border: 1px solid {th("border")}; border-radius: 30px; padding: 0.3rem 1rem; font-size: 0.8rem; color: {th("text_muted")};">
                ⚡ {t('Real-time Odoo Intelligence','تحليلات Odoo الفورية')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_inv, tab_pos, tab_sales, tab_pur, tab_chat = st.tabs([
        f"📦 {t('Inventory','المخزون')}",
        f"🛒 {t('POS','نقاط البيع')}",
        f"🛍️ {t('Sales','المبيعات')}",
        f"🔖 {t('Purchase','المشتريات')}",
        f"🤖 {t('AI Insights','تحليلات ذكية')}",
    ])

    # ── INVENTORY TAB ─────────────────────────────────────────────────────────
    with tab_inv:
        st.markdown(f"<div class='section-header'>📦 {t('Inventory Overview','نظرة عامة على المخزون')}</div>", unsafe_allow_html=True)
        # Filters row
        f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 1])
        with f1:
            co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            inv_co = st.selectbox(t("Company", "الشركة"), co_opts, key="inv_company", label_visibility="collapsed")
            inv_keys = SYSTEM_KEYS if inv_co == t("All Companies", "جميع الشركات") else [k for k in SYSTEM_KEYS if get_system_name(k) == inv_co]
        with f2:
            low_thresh = st.number_input(t("Low threshold", "حد المنخفض"), min_value=0, max_value=1000, value=5, step=1, key="inv_low_thresh", label_visibility="collapsed")
        with f3:
            model_filter = st.text_input(t("Model Code filter", "فلتر الموديل"), key="inv_model_filter", placeholder="Model code...", label_visibility="collapsed").strip()
        with f4:
            exact_match = st.toggle(t("Exact", "تطابق"), value=False, key="inv_exact")
        # Viz mode and refresh
        c1, c2 = st.columns([3, 1])
        with c1:
            inv_viz_mode = viz_mode_selector("inv_viz_mode")
        with c2:
            if st.button(f"🔄 {t('Refresh','تحديث')}", type="primary", key="inv_refresh", use_container_width=True):
                with st.spinner(t("Fetching...", "جاري الجلب...")):
                    codes = tuple([model_filter]) if model_filter else ()
                    total_df, branch_df, diag = fetch_inventory(inv_keys, codes, exact_match)
                    if total_df is not None and not total_df.empty and "Model Code" in total_df.columns:
                        mc_vals = total_df["Model Code"].dropna().unique().tolist()
                        if mc_vals:
                            end_d = datetime.now().date()
                            start_d = end_d - timedelta(days=365)
                            pur_sum = fetch_purchase_summary(inv_keys, tuple(mc_vals), start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d"))
                            if pur_sum is not None and not pur_sum.empty:
                                total_df = total_df.merge(pur_sum, on="Model Code", how="left")
                                total_df["Purchase Qty"] = total_df["Purchase Qty"].fillna(0).astype(int)
                            else:
                                total_df["Purchase Qty"] = 0
                        else:
                            total_df["Purchase Qty"] = 0
                    st.session_state.inventory_df = coerce_numerics(total_df)
                    st.session_state.inventory_branch_df = coerce_numerics(branch_df)
                    st.session_state.inv_diag = diag
                    st.session_state.inv_page = 0
                    st.session_state.inv_full_page = 0
                    st.session_state.inv_last_refresh = datetime.now()
                    st.rerun()
        show_diag(st.session_state.get("inv_diag", []))
        total_df = st.session_state.get("inventory_df")
        branch_df = st.session_state.get("inventory_branch_df")
        if total_df is None or total_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh to load data.','اضغط تحديث لتحميل البيانات.')}</div>", unsafe_allow_html=True)
        else:
            qty_s = safe_get_col(total_df, "On Hand")
            price_s = safe_get_col(total_df, "Sale Price")
            mc_c = get_display_col(total_df, "Model Code")
            models = int(total_df[mc_c].nunique()) if mc_c in total_df.columns else 0
            br_c = get_display_col(branch_df, "Branch") if (branch_df is not None and not branch_df.empty) else "Branch"
            br_count = int(branch_df[br_c].nunique()) if (branch_df is not None and not branch_df.empty and br_c in branch_df.columns) else 0
            zero_cnt = int((qty_s == 0).sum())
            low_cnt = int(((qty_s > 0) & (qty_s <= low_thresh)).sum())
            # KPI row
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            k1.metric(t("Total Qty", "إجمالي الكمية"), f"{int(qty_s.sum()):,}")
            k2.metric(t("Value (SAR)", "القيمة"), f"{float((qty_s * price_s).sum()):,.0f}")
            k3.metric(t("Models", "الموديلات"), f"{models:,}")
            k4.metric(t("Branches", "الفروع"), f"{br_count:,}")
            k5.metric(t("Zero Stock", "صفر"), f"{zero_cnt:,}")
            k6.metric(t(f"Low ≤{low_thresh}", f"منخفض ≤{low_thresh}"), f"{low_cnt:,}")
            # Alerts
            if zero_cnt > 0:
                st.markdown(f"<div class='alert-banner'>🔴 {zero_cnt} {t('products with zero stock — reorder immediately','منتج بدون مخزون — أعد الطلب فوراً')}</div>", unsafe_allow_html=True)
            if low_cnt > 0:
                st.markdown(f"<div class='warn-banner'>⚠️ {low_cnt} {t(f'products low stock (≤{low_thresh})',f'منتج مخزون منخفض (≤{low_thresh})')}</div>", unsafe_allow_html=True)
            # Main visualization
            st.markdown(f"<div class='section-header'>📊 {t('Stock Visualization','تصور المخزون')}</div>", unsafe_allow_html=True)
            render_visualization(total_df, inv_viz_mode, "Model Code", "On Hand", t("Stock by Model", "المخزون حسب الموديل"))
            # Summary
            render_exec_summary(total_df, "On Hand", "Model Code", t("Stock Performance", "أداء المخزون"))
            # Branch distribution
            if branch_df is not None and not branch_df.empty:
                br_c2 = get_display_col(branch_df, "Branch")
                on_c = get_display_col(branch_df, "On Hand")
                if br_c2 in branch_df.columns and on_c in branch_df.columns:
                    st.markdown(f"<div class='section-header'>🏪 {t('Branch Distribution','توزيع المخزون حسب الفرع')}</div>", unsafe_allow_html=True)
                    branch_agg = branch_df.groupby(br_c2)[on_c].sum().reset_index().sort_values(on_c, ascending=False)
                    fig_b = px.bar(branch_agg, x=br_c2, y=on_c, color=on_c,
                                   color_continuous_scale=[th_color("accent1"), th_color("accent2")],
                                   template=th("plotly_template"), text_auto=".2s",
                                   labels={br_c2: col("Branch"), on_c: col("On Hand")})
                    fig_b.update_traces(marker_line_width=0)
                    st.plotly_chart(apply_plotly_theme(fig_b), use_container_width=True)
            # Low stock table
            st.markdown(f"<div class='section-header'>📋 {t('Low/Zero Stock Items','عناصر المخزون المنخفض/الصفري')}</div>", unsafe_allow_html=True)
            low_df = total_df[qty_s <= low_thresh].copy()
            render_paginated_table(low_df, "inv_page")
            with st.expander(f"📋 {t('Full Inventory Table','جدول المخزون الكامل')}"):
                render_paginated_table(total_df, "inv_full_page")
            # Downloads
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button("⬇️ CSV", to_csv(localize_df(total_df)), dl_name("inventory", "csv"), "text/csv", use_container_width=True)
            with d2:
                st.download_button("⬇️ Excel", to_excel(localize_df(total_df)), dl_name("inventory", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with d3:
                if branch_df is not None and not branch_df.empty:
                    bdf = branch_df[branch_df["Model Code"].str.contains(model_filter, case=False, na=False)] if model_filter else branch_df
                    st.download_button(
                        f"📊 {t('Branch Matrix','مصفوفة الفروع')}",
                        to_excel_branch_matrix(bdf),
                        dl_name("branch_matrix", "xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    # ── POS TAB ───────────────────────────────────────────────────────────────
    with tab_pos:
        st.markdown(f"<div class='section-header'>🛒 {t('POS Analytics','تحليلات نقاط البيع')}</div>", unsafe_allow_html=True)
        # Filters
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        with fc1:
            pos_co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            pos_co = st.selectbox(t("Company", "الشركة"), pos_co_opts, key="pos_company", label_visibility="collapsed")
            pos_keys = SYSTEM_KEYS if pos_co == t("All Companies", "جميع الشركات") else [k for k in SYSTEM_KEYS if get_system_name(k) == pos_co]
        with fc2:
            pos_viz_mode = viz_mode_selector("pos_viz_mode")
        with fc3:
            if st.button(f"🔄 {t('Refresh','تحديث')}", type="primary", key="pos_refresh", use_container_width=True):
                with st.spinner(t("Fetching...", "جاري الجلب...")):
                    df, diag = fetch_pos(pos_keys, pos_from.strftime("%Y-%m-%d"), pos_to.strftime("%Y-%m-%d"), pos_branch, pos_model)
                    st.session_state.pos_df = coerce_numerics(df) if df is not None else None
                    st.session_state.pos_diag = diag
                    st.session_state.pos_page = 0
                    st.session_state.pos_branch_page = 0
                    st.session_state.pos_cashier_page = 0
                    st.session_state.pos_last_refresh = datetime.now()
                    st.rerun()
        fd1, fd2 = st.columns(2)
        with fd1:
            pos_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=30), key="pos_date_from")
        with fd2:
            pos_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="pos_date_to")
        ff1, ff2 = st.columns(2)
        with ff1:
            pos_branch = st.text_input(t("Branch filter", "فلتر الفرع"), key="pos_branch_filter", placeholder="Branch...").strip()
        with ff2:
            pos_model = st.text_input(t("Model Code", "رمز الموديل"), key="pos_model_filter", placeholder="Model...").strip()
        show_diag(st.session_state.get("pos_diag", []))
        pos_df = st.session_state.get("pos_df")
        if pos_df is None or pos_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh to load data.','اضغط تحديث لتحميل البيانات.')}</div>", unsafe_allow_html=True)
        else:
            po_col_n = get_display_col(pos_df, "POS Order")
            unique = pos_df.drop_duplicates(subset=[po_col_n]) if po_col_n in pos_df.columns else pos_df
            total_rev = float(safe_get_col(unique, "Total Amount").sum())
            total_qty_v = float(safe_get_col(pos_df, "Qty").sum())
            total_bills = len(unique)
            avg_bill = total_rev / total_bills if total_bills > 0 else 0
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(t("Revenue (SAR)", "الإيرادات"), f"{total_rev:,.0f}")
            k2.metric(t("Units Sold", "الوحدات"), f"{total_qty_v:,.0f}")
            k3.metric(t("Bills", "الفواتير"), f"{total_bills:,}")
            k4.metric(t("Avg Bill", "متوسط الفاتورة"), f"{avg_bill:,.2f}")
            st.markdown(f"<div class='section-header'>📊 {t('POS Visualization','تصور POS')}</div>", unsafe_allow_html=True)
            if has_col(unique, "Branch") and has_col(unique, "Total Amount"):
                render_visualization(unique, pos_viz_mode, "Branch", "Total Amount", t("Revenue by Branch", "الإيرادات حسب الفرع"))
            elif has_col(pos_df, "Model Code") and has_col(pos_df, "Qty"):
                render_visualization(pos_df, pos_viz_mode, "Model Code", "Qty", t("Qty by Model", "الكمية حسب الموديل"))
            if has_col(unique, "Branch"):
                render_exec_summary(unique, "Total Amount", "Branch", t("Branch Performance", "أداء الفروع"))
                br_c_ = get_display_col(unique, "Branch")
                tot_c_ = get_display_col(unique, "Total Amount")
                po_c_ = get_display_col(unique, "POS Order")
                if br_c_ in unique.columns and tot_c_ in unique.columns:
                    br_rev = unique.groupby(br_c_)[tot_c_].sum().reset_index()
                    br_rev.columns = [br_c_, "Revenue (SAR)"]
                    if po_c_ in unique.columns:
                        br_cnt = unique.groupby(br_c_)[po_c_].count().reset_index()
                        br_cnt.columns = [br_c_, "Bills"]
                        agg_df = br_rev.merge(br_cnt, on=br_c_).sort_values("Revenue (SAR)", ascending=False)
                    else:
                        agg_df = br_rev.sort_values("Revenue (SAR)", ascending=False)
                    st.markdown(f"<div class='section-header'>🏪 {t('Branch Summary','ملخص الفروع')}</div>", unsafe_allow_html=True)
                    render_paginated_table(agg_df, "pos_branch_page")
            if has_col(unique, "Cashier"):
                ca_c_ = get_display_col(unique, "Cashier")
                tot_c_ = get_display_col(unique, "Total Amount")
                ca_agg = unique.groupby(ca_c_)[tot_c_].sum().reset_index().sort_values(tot_c_, ascending=False)
                st.markdown(f"<div class='section-header'>👤 {t('Cashier Performance','أداء الكاشير')}</div>", unsafe_allow_html=True)
                fig_ca = px.bar(ca_agg.head(10), x=ca_c_, y=tot_c_, color=tot_c_,
                                color_continuous_scale=[th_color("accent1"), th_color("accent2")],
                                template=th("plotly_template"), text_auto=".2s")
                fig_ca.update_traces(marker_line_width=0)
                st.plotly_chart(apply_plotly_theme(fig_ca), use_container_width=True)
                render_paginated_table(ca_agg, "pos_cashier_page")
            if has_col(pos_df, "Model Code") and has_col(pos_df, "Qty"):
                mc_c_ = get_display_col(pos_df, "Model Code")
                q_c_ = get_display_col(pos_df, "Qty")
                tp = pos_df.groupby(mc_c_)[q_c_].sum().reset_index().sort_values(q_c_, ascending=False).head(10)
                st.markdown(f"<div class='section-header'>🏆 {t('Top 10 Products','أفضل 10 منتجات')}</div>", unsafe_allow_html=True)
                fig_tp = px.bar(tp, x=mc_c_, y=q_c_, color=q_c_,
                                color_continuous_scale=[th_color("accent1"), th_color("accent2")],
                                template=th("plotly_template"), text_auto=".2s")
                fig_tp.update_traces(marker_line_width=0)
                st.plotly_chart(apply_plotly_theme(fig_tp), use_container_width=True)
            st.markdown(f"<div class='section-header'>📈 {t('Daily Revenue Trend','الاتجاه اليومي')}</div>", unsafe_allow_html=True)
            render_daily_trend_chart(unique, "Date", "Total Amount", t("Daily POS Revenue", "الإيراد اليومي POS"), "accent1")
            st.markdown(f"<div class='section-header'>📋 {t('POS Transactions','معاملات POS')}</div>", unsafe_allow_html=True)
            render_paginated_table(pos_df, "pos_page")
            p1, p2 = st.columns(2)
            with p1:
                st.download_button("⬇️ CSV", to_csv(localize_df(pos_df)), dl_name("pos", "csv"), "text/csv", use_container_width=True)
            with p2:
                st.download_button("⬇️ Excel", to_excel(localize_df(pos_df)), dl_name("pos", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # ── SALES TAB ─────────────────────────────────────────────────────────────
    with tab_sales:
        st.markdown(f"<div class='section-header'>🛍️ {t('Sales Analytics','تحليلات المبيعات')}</div>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        with fc1:
            s_co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            s_co = st.selectbox(t("Company", "الشركة"), s_co_opts, key="sales_company", label_visibility="collapsed")
            s_keys = SYSTEM_KEYS if s_co == t("All Companies", "جميع الشركات") else [k for k in SYSTEM_KEYS if get_system_name(k) == s_co]
        with fc2:
            sales_viz_mode = viz_mode_selector("sales_viz_mode")
        with fc3:
            if st.button(f"🔄 {t('Refresh','تحديث')}", type="primary", key="sales_refresh", use_container_width=True):
                with st.spinner(t("Fetching...", "جاري الجلب...")):
                    df, diag = fetch_sales(s_keys, s_from.strftime("%Y-%m-%d"), s_to.strftime("%Y-%m-%d"), s_model)
                    st.session_state.sales_df = coerce_numerics(df) if df is not None else None
                    st.session_state.sales_diag = diag
                    st.session_state.sales_page = 0
                    st.session_state.sales_cust_page = 0
                    st.session_state.sales_last_refresh = datetime.now()
                    st.rerun()
        fd1, fd2 = st.columns(2)
        with fd1:
            s_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=30), key="sales_date_from")
        with fd2:
            s_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="sales_date_to")
        s_model = st.text_input(t("Model Code filter", "فلتر رمز الموديل"), key="sales_model_filter", placeholder="Model...").strip()
        show_diag(st.session_state.get("sales_diag", []))
        sales_df = st.session_state.get("sales_df")
        if sales_df is None or sales_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh to load data.','اضغط تحديث لتحميل البيانات.')}</div>", unsafe_allow_html=True)
        else:
            so_col_n = get_display_col(sales_df, "SO")
            if so_col_n not in sales_df.columns:
                st.warning(f"⚠️ {t('SO column missing.','عمود SO غير موجود.')}")
            else:
                unique = sales_df.drop_duplicates(subset=[so_col_n])
                total_rev = float(safe_get_col(unique, "Total Amount").sum())
                total_orders = int(unique[so_col_n].nunique())
                total_qty_v = float(safe_get_col(sales_df, "Qty").sum())
                avg_order = total_rev / total_orders if total_orders > 0 else 0
                k1, k2, k3, k4 = st.columns(4)
                k1.metric(t("Revenue (SAR)", "الإيراد"), f"{total_rev:,.0f}")
                k2.metric(t("Units Sold", "الوحدات"), f"{total_qty_v:,.0f}")
                k3.metric(t("Orders", "الطلبات"), f"{total_orders:,}")
                k4.metric(t("Avg Order", "متوسط الطلب"), f"{avg_order:,.2f}")
                st.markdown(f"<div class='section-header'>📊 {t('Sales Visualization','تصور المبيعات')}</div>", unsafe_allow_html=True)
                render_visualization(sales_df, sales_viz_mode, "Model Code", "Qty", t("Units by Model", "الوحدات حسب الموديل"))
                if has_col(unique, "Customer"):
                    render_exec_summary(unique, "Total Amount", "Customer", t("Customer Revenue Analysis", "تحليل إيرادات العملاء"))
                    cu_c_ = get_display_col(unique, "Customer")
                    to_c_ = get_display_col(unique, "Total Amount")
                    so_c_ = get_display_col(unique, "SO")
                    cu_rev = unique.groupby(cu_c_)[to_c_].sum().reset_index()
                    cu_rev.columns = [cu_c_, "Revenue (SAR)"]
                    if so_c_ in unique.columns:
                        cu_cnt = unique.groupby(cu_c_)[so_c_].count().reset_index()
                        cu_cnt.columns = [cu_c_, "Orders"]
                        ca_df = cu_rev.merge(cu_cnt, on=cu_c_).sort_values("Revenue (SAR)", ascending=False)
                    else:
                        ca_df = cu_rev.sort_values("Revenue (SAR)", ascending=False)
                    st.markdown(f"<div class='section-header'>👥 {t('Customer Leaderboard','ترتيب العملاء')}</div>", unsafe_allow_html=True)
                    render_paginated_table(ca_df, "sales_cust_page")
                if has_col(sales_df, "Model Code") and has_col(sales_df, "Qty"):
                    mc_c_ = get_display_col(sales_df, "Model Code")
                    q_c_ = get_display_col(sales_df, "Qty")
                    tp = sales_df.groupby(mc_c_)[q_c_].sum().reset_index().sort_values(q_c_, ascending=False).head(10)
                    st.markdown(f"<div class='section-header'>🏆 {t('Top 10 Products','أفضل 10 منتجات')}</div>", unsafe_allow_html=True)
                    fig_tp = px.bar(tp, x=mc_c_, y=q_c_, color=q_c_,
                                    color_continuous_scale=[th_color("accent1"), th_color("accent2")],
                                    template=th("plotly_template"), text_auto=".2s")
                    fig_tp.update_traces(marker_line_width=0)
                    st.plotly_chart(apply_plotly_theme(fig_tp), use_container_width=True)
                st.markdown(f"<div class='section-header'>📈 {t('Daily Revenue Trend','الاتجاه اليومي للإيرادات')}</div>", unsafe_allow_html=True)
                render_daily_trend_chart(unique, "Date", "Total Amount", t("Daily Sales Revenue", "الإيراد اليومي"), "accent2")
                st.markdown(f"<div class='section-header'>📋 {t('Sales Detail','تفاصيل المبيعات')}</div>", unsafe_allow_html=True)
                render_paginated_table(sales_df, "sales_page")
                s1, s2 = st.columns(2)
                with s1:
                    st.download_button("⬇️ CSV", to_csv(localize_df(sales_df)), dl_name("sales", "csv"), "text/csv", use_container_width=True)
                with s2:
                    st.download_button("⬇️ Excel", to_excel(localize_df(sales_df)), dl_name("sales", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # ── PURCHASE TAB ──────────────────────────────────────────────────────────
    with tab_pur:
        st.markdown(f"<div class='section-header'>🔖 {t('Purchase Analytics','تحليلات المشتريات')}</div>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        with fc1:
            p_co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            p_co = st.selectbox(t("Company", "الشركة"), p_co_opts, key="pur_company", label_visibility="collapsed")
            p_keys = SYSTEM_KEYS if p_co == t("All Companies", "جميع الشركات") else [k for k in SYSTEM_KEYS if get_system_name(k) == p_co]
        with fc2:
            pur_viz_mode = viz_mode_selector("pur_viz_mode")
        with fc3:
            if st.button(f"🔄 {t('Refresh','تحديث')}", type="primary", key="pur_refresh", use_container_width=True):
                with st.spinner(t("Fetching...", "جاري الجلب...")):
                    df, diag = fetch_purchase(p_keys, p_model, p_from.strftime("%Y-%m-%d"), p_to.strftime("%Y-%m-%d"))
                    st.session_state.purchase_df = coerce_numerics(df) if df is not None else None
                    st.session_state.pur_diag = diag
                    st.session_state.pur_page = 0
                    st.session_state.pur_vendor_page = 0
                    st.session_state.pur_last_refresh = datetime.now()
                    st.rerun()
        fd1, fd2 = st.columns(2)
        with fd1:
            p_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=90), key="pur_date_from")
        with fd2:
            p_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="pur_date_to")
        p_model = st.text_input(t("Model Code filter", "فلتر رمز الموديل"), key="pur_model_filter", placeholder="Model...").strip()
        show_diag(st.session_state.get("pur_diag", []))
        pur_df = st.session_state.get("purchase_df")
        if pur_df is None or pur_df.empty:
            st.markdown(f"<div class='info-banner'>ℹ️ {t('Click Refresh to load data.','اضغط تحديث لتحميل البيانات.')}</div>", unsafe_allow_html=True)
        else:
            total_val = float(safe_get_col(pur_df, "Subtotal").sum())
            total_qty = int(safe_get_col(pur_df, "Qty").sum())
            vendors = int(pur_df["Vendor"].nunique()) if "Vendor" in pur_df.columns else 0
            pos_n = int(pur_df["PO"].nunique()) if "PO" in pur_df.columns else 0
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(t("Value (SAR)", "قيمة الشراء"), f"{total_val:,.0f}")
            k2.metric(t("Units", "الوحدات"), f"{total_qty:,}")
            k3.metric(t("Vendors", "الموردون"), f"{vendors:,}")
            k4.metric(t("POs", "أوامر"), f"{pos_n:,}")
            st.markdown(f"<div class='section-header'>📊 {t('Purchase Visualization','تصور المشتريات')}</div>", unsafe_allow_html=True)
            if has_col(pur_df, "Vendor") and has_col(pur_df, "Subtotal"):
                render_visualization(pur_df, pur_viz_mode, "Vendor", "Subtotal", t("Spend by Vendor", "الإنفاق حسب المورد"))
            elif has_col(pur_df, "Model Code") and has_col(pur_df, "Qty"):
                render_visualization(pur_df, pur_viz_mode, "Model Code", "Qty", t("Qty by Model", "الكمية حسب الموديل"))
            if has_col(pur_df, "Vendor"):
                render_exec_summary(pur_df, "Subtotal", "Vendor", t("Vendor Spend Analysis", "تحليل إنفاق الموردين"))
                vc_ = get_display_col(pur_df, "Vendor")
                sc_ = get_display_col(pur_df, "Subtotal")
                qc_ = get_display_col(pur_df, "Qty")
                vd_spend = pur_df.groupby(vc_)[sc_].sum().reset_index()
                vd_spend.columns = [vc_, "Spend (SAR)"]
                vd_qty = pur_df.groupby(vc_)[qc_].sum().reset_index()
                vd_qty.columns = [vc_, "Qty"]
                vd = vd_spend.merge(vd_qty, on=vc_).sort_values("Spend (SAR)", ascending=False)
                st.markdown(f"<div class='section-header'>🏭 {t('Vendor Leaderboard','ترتيب الموردين')}</div>", unsafe_allow_html=True)
                render_paginated_table(vd, "pur_vendor_page")
            if has_col(pur_df, "Receipt Location") and has_col(pur_df, "Qty"):
                lc_ = get_display_col(pur_df, "Receipt Location")
                qc_ = get_display_col(pur_df, "Qty")
                la = pur_df.groupby(lc_)[qc_].sum().reset_index().sort_values(qc_, ascending=False)
                st.markdown(f"<div class='section-header'>📍 {t('Receipt Location Summary','ملخص مواقع الاستلام')}</div>", unsafe_allow_html=True)
                fig_loc = px.pie(la.head(10), names=lc_, values=qc_,
                                 color_discrete_sequence=th("plotly_colors"),
                                 template=th("plotly_template"), hole=0.55)
                fig_loc.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(apply_plotly_theme(fig_loc), use_container_width=True)
            st.markdown(f"<div class='section-header'>📈 {t('Daily Purchase Trend','الاتجاه اليومي للمشتريات')}</div>", unsafe_allow_html=True)
            render_daily_trend_chart(pur_df, "Date", "Subtotal", t("Daily Purchase Spend", "الإنفاق اليومي"), "accent3")
            st.markdown(f"<div class='section-header'>📋 {t('Purchase History','تاريخ المشتريات')}</div>", unsafe_allow_html=True)
            render_paginated_table(pur_df, "pur_page")
            pd1, pd2 = st.columns(2)
            with pd1:
                st.download_button("⬇️ CSV", to_csv(localize_df(pur_df)), dl_name("purchase", "csv"), "text/csv", use_container_width=True)
            with pd2:
                st.download_button("⬇️ Excel", to_excel(localize_df(pur_df)), dl_name("purchase", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # ── AI INSIGHTS TAB ───────────────────────────────────────────────────────
    with tab_chat:
        show_chat_panel()

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()
if not st.session_state.get("authenticated"):
    show_login()
else:
    show_dashboard()
