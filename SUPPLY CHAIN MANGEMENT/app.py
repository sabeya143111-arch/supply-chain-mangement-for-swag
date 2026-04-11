# app.py — SWAG EXECUTIVE DASHBOARD — FLOW-BASED v6.0
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
    page_title="SWAG Executive Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 0: COLOR UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def hex_to_rgba(hex_color: str, alpha: float = 0.18) -> str:
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
        "accent1": "#1e3a8a",
        "accent2": "#3b82f6",
        "accent3": "#10b981",
        "accent4": "#f59e0b",
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
        "accent1": "#d4af37",
        "accent2": "#f5c842",
        "accent3": "#4ade80",
        "accent4": "#f87171",
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
        "accent1": "#4f46e5",
        "accent2": "#7c3aed",
        "accent3": "#059669",
        "accent4": "#d97706",
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
    body_dir = "rtl" if is_rtl else "ltr"
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    html {{ direction: {body_dir}; }}
    body {{ background: {th("bg")}; color: {th("text")}; }}
    .stApp {{ background: {th("bg")}; }}
    
    section[data-testid="stSidebar"] {{
        background: {th("sidebar_bg")} !important;
        border-right: 1px solid {border_val};
        box-shadow: none;
    }}
    section[data-testid="stSidebar"] * {{ color: {th("text")} !important; }}
    
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
    
    .info-banner {{ background: {hex_to_rgba(a1, 0.08)}; border-left: 4px solid {a1}; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 1rem 0; color: {th("text")}; }}
    .warn-banner {{ background: {hex_to_rgba(warning_color, 0.08)}; border-left: 4px solid {warning_color}; border-radius: 8px; padding: 0.8rem 1.2rem; }}
    .alert-banner {{ background: {hex_to_rgba(danger_color, 0.08)}; border-left: 4px solid {danger_color}; border-radius: 8px; padding: 0.8rem 1.2rem; }}
    .ok-banner {{ background: {hex_to_rgba(success_color, 0.08)}; border-left: 4px solid {success_color}; border-radius: 8px; padding: 0.8rem 1.2rem; }}
    
    .exec-card {{
        background: {th("card_bg")};
        border: 1px solid {border_val};
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: {shadow};
        color: {th("text")};
    }}
    
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
    
    .section-header {{
        font-size: 1rem;
        font-weight: 600;
        color: {th("text_label")};
        margin: 1.5rem 0 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
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
# SECTION 3: CONSTANTS & CONFIG
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]
# Also map display names to keys for flow
SYSTEM_DISPLAY = {"Manfari": "MANFARI", "Swag": "SWAG", "Laroche": "LAROCHE"}
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
# SECTION 4: LANGUAGE / LOCALIZATION
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
    "Stock Value": ("Stock Value", "قيمة المخزون"),
    "Estimated Sold": ("Estimated Sold", "المقدر مبيعاً"),
    "Sell Through %": ("Sell Through %", "نسبة البيع %"),
    "Stock Status": ("Stock Status", "حالة المخزون"),
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
# SECTION 5: SESSION STATE DEFAULTS
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
# SECTION 6: AUTH
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
# SECTION 7: XML-RPC HELPERS
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
# SECTION 8: DATA UTILITIES (unchanged from your original)
# ─────────────────────────────────────────────────────────────────────────────
_NUMERIC_RAW = ["Sale Price", "On Hand", "Purchase Qty", "Qty", "Unit Price", "Subtotal", "Total Amount", "Stock Value", "Estimated Sold"]

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
    """Convert DataFrame to Excel bytes with robust error handling."""
    if df is None or df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame({"Message": ["No data available"]}).to_excel(writer, sheet_name="Data", index=False)
        output.seek(0)
        return output.getvalue()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
    output.seek(0)
    return output.getvalue()

def to_excel_branch_matrix(branch_df: pd.DataFrame) -> bytes:
    if branch_df is None or branch_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame({"Message": ["No branch data available"]}).to_excel(writer, sheet_name="Branch_Matrix", index=False)
        output.seek(0)
        return output.getvalue()
    branch_c = get_display_col(branch_df, "Branch")
    model_c = get_display_col(branch_df, "Model Code")
    qty_c = get_display_col(branch_df, "On Hand")
    if branch_c not in branch_df.columns or model_c not in branch_df.columns:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame({"Error": ["Required columns missing for branch matrix"]}).to_excel(writer, sheet_name="Error", index=False)
        output.seek(0)
        return output.getvalue()
    try:
        branch_df[branch_c] = branch_df[branch_c].astype(str)
        branch_df[model_c] = branch_df[model_c].astype(str)
        pivot = branch_df.pivot_table(index=model_c, columns=branch_c, values=qty_c, aggfunc="sum", fill_value=0)
        pivot = pivot.astype(int)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pivot.to_excel(writer, sheet_name="Branch_Matrix")
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame({"Error": [f"Failed to create branch matrix: {str(e)}"]}).to_excel(writer, sheet_name="Error", index=False)
        output.seek(0)
        return output.getvalue()

def dl_name(prefix: str, ext: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: PAGINATED TABLE RENDERER
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
        rows_html += f"<tr>{cells}<tr>"
    st.markdown(
        f"<div class='dataframe-wrap'><table><thead><tr>{header_html}<tr></thead><tbody>{rows_html}</tbody></table></div>",
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
# SECTION 10: VISUALIZATION ENGINE
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
# SECTION 11: DATA FETCHERS (original, only inventory fetch fixed)
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
        templates = _odoo_call(url, db, uid, ak, "product.template", "search_read",
                               [prod_domain if prod_domain else []],
                               {"fields": ["id", "name", "default_code", "list_price"], "limit": 5000})
        if not templates:
            return [], [], {"system": name, "level": "ok", "msg": "No products found."}
        template_map = {t["id"]: t for t in templates}
        template_ids = list(template_map.keys())
        variants = _odoo_call(url, db, uid, ak, "product.product", "search_read",
                              [[("product_tmpl_id", "in", template_ids)]],
                              {"fields": ["id", "product_tmpl_id"], "limit": 50000})
        variant_to_tmpl = {}
        for v in variants:
            variant_id = v["id"]
            tmpl_raw = v["product_tmpl_id"]
            if isinstance(tmpl_raw, list) and len(tmpl_raw) > 0:
                tmpl_id = tmpl_raw[0]
            else:
                tmpl_id = tmpl_raw
            variant_to_tmpl[variant_id] = tmpl_id
        variant_ids = list(variant_to_tmpl.keys())
        if not variant_ids:
            total_rows = []
            branch_rows = []
            for tmpl_id, t in template_map.items():
                total_rows.append({
                    "System": name,
                    "Model Code": (t.get("default_code") or "").strip(),
                    "Product": t.get("name", ""),
                    "Sale Price": float(t.get("list_price") or 0),
                    "On Hand": 0,
                })
            return total_rows, branch_rows, {"system": name, "level": "ok", "msg": f"No variants, zero stock for {len(total_rows)} templates."}
        quants = _odoo_call(url, db, uid, ak, "stock.quant", "search_read",
                            [[("product_id", "in", variant_ids), ("location_id.usage", "=", "internal")]],
                            {"fields": ["product_id", "location_id", "quantity"], "limit": 50000})
        tmpl_qty = {}
        branch_rows = []
        for q in quants:
            prod_raw = q.get("product_id")
            if isinstance(prod_raw, list) and len(prod_raw) > 0:
                variant_id = prod_raw[0]
            else:
                variant_id = prod_raw
            tmpl_id = variant_to_tmpl.get(variant_id)
            if tmpl_id is None:
                continue
            qty = float(q.get("quantity") or 0)
            tmpl_qty[tmpl_id] = tmpl_qty.get(tmpl_id, 0) + qty
            loc = q.get("location_id")
            if isinstance(loc, list) and len(loc) > 1:
                loc_name = loc[1]
            else:
                loc_name = str(loc or "")
            mc_val = (template_map.get(tmpl_id, {}).get("default_code") or "").strip()
            if mc_val:
                branch_rows.append({
                    "System": name,
                    "Branch": loc_name,
                    "Model Code": mc_val,
                    "On Hand": qty,
                })
        total_rows = []
        for tmpl_id, t in template_map.items():
            total_rows.append({
                "System": name,
                "Model Code": (t.get("default_code") or "").strip(),
                "Product": t.get("name", ""),
                "Sale Price": float(t.get("list_price") or 0),
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
# SECTION 13: LOGIN PAGE
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
# SECTION 14: DASHBOARD — FLOW-BASED LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    st.markdown(build_css(), unsafe_allow_html=True)

    with st.sidebar:
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
        new_theme = st.selectbox(
            f"🎨 {t('Theme','المظهر')}",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(get_theme()),
            key="theme_select",
        )
        if new_theme != get_theme():
            st.session_state.theme = new_theme
            st.rerun()
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
        st.markdown(f"**🏢 {t('Connected Systems','الأنظمة المتصلة')}**")
        for key in SYSTEM_KEYS:
            cfg = st.secrets.get(key, {})
            name = get_system_name(key)
            badge_color = th_color("success") if cfg.get("url") else th_color("danger")
            icon = "✓" if cfg.get("url") else "✗"
            st.markdown(f"<div style='margin:5px 0;'><span style='color:{badge_color};'>{icon}</span> {name}</div>", unsafe_allow_html=True)
        st.divider()
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
                <p style="margin:0; color: {th("text_muted")}; font-size: 0.85rem;">{t('Multi-Company · Flow-Based Executive Dashboard','لوحة تحكم تنفيذية مبسطة')}</p>
            </div>
            <div style="background: {th("card_bg")}; border: 1px solid {th("border")}; border-radius: 30px; padding: 0.3rem 1rem; font-size: 0.8rem; color: {th("text_muted")};">
                ⚡ {t('Real-time Odoo Intelligence','تحليلات Odoo الفورية')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # EXECUTIVE KPI STRIP (top of dashboard)
    # --------------------------------------------------------------------------
    inv_df = st.session_state.get("inventory_df")
    pur_df = st.session_state.get("purchase_df")
    pos_df = st.session_state.get("pos_df")
    sales_df = st.session_state.get("sales_df")

    # Helper to compute totals across all systems
    def total_purchase_value():
        if pur_df is None or pur_df.empty:
            return 0
        return safe_get_col(pur_df, "Subtotal").sum()
    def total_received_qty():
        if pur_df is None or pur_df.empty:
            return 0
        return safe_get_col(pur_df, "Qty").sum()
    def total_stored_qty():
        if inv_df is None or inv_df.empty:
            return 0
        return int(safe_get_col(inv_df, "On Hand").sum())
    def total_sales_value():
        if sales_df is None or sales_df.empty:
            return 0
        # Use unique SOs to avoid double count
        so_col = get_display_col(sales_df, "SO")
        if so_col in sales_df.columns:
            unique = sales_df.drop_duplicates(subset=[so_col])
        else:
            unique = sales_df
        return safe_get_col(unique, "Total Amount").sum()
    def total_pos_value():
        if pos_df is None or pos_df.empty:
            return 0
        po_col = get_display_col(pos_df, "POS Order")
        if po_col in pos_df.columns:
            unique = pos_df.drop_duplicates(subset=[po_col])
        else:
            unique = pos_df
        return safe_get_col(unique, "Total Amount").sum()
    def delivered_vs_pending():
        # estimate: from sales, count done vs total
        if sales_df is None or sales_df.empty:
            return 0, 0
        so_col = get_display_col(sales_df, "SO")
        if so_col not in sales_df.columns:
            return 0, 0
        unique = sales_df.drop_duplicates(subset=[so_col])
        total_orders = len(unique)
        if "State" in unique.columns:
            delivered = unique[unique["State"].str.lower().isin(["done", "sale"])]
            delivered_count = len(delivered)
        else:
            delivered_count = 0
        return delivered_count, total_orders - delivered_count
    def low_zero_stock():
        if inv_df is None or inv_df.empty:
            return 0, 0
        qty = safe_get_col(inv_df, "On Hand")
        zero = int((qty == 0).sum())
        low = int(((qty > 0) & (qty <= 5)).sum())
        return low, zero
    def active_branches():
        branch_df = st.session_state.get("inventory_branch_df")
        if branch_df is None or branch_df.empty:
            return 0
        br_col = get_display_col(branch_df, "Branch")
        if br_col in branch_df.columns:
            return branch_df[br_col].nunique()
        return 0

    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    k1.metric(t("Purchase Value", "قيمة المشتريات"), f"SAR {total_purchase_value():,.0f}")
    k2.metric(t("Received Qty", "كمية المستلم"), f"{total_received_qty():,.0f}")
    k3.metric(t("Stored Qty", "المخزون"), f"{total_stored_qty():,}")
    k4.metric(t("Sales Value", "المبيعات"), f"SAR {total_sales_value():,.0f}")
    k5.metric(t("POS Value", "نقاط البيع"), f"SAR {total_pos_value():,.0f}")
    deliv, pend = delivered_vs_pending()
    k6.metric(t("Delivered/Pending", "تم التوصيل/معلق"), f"{deliv}/{pend}")
    low_z, zero_z = low_zero_stock()
    k7.metric(t("Low/Zero Stock", "منخفض/صفر"), f"{low_z}/{zero_z}")
    k8.metric(t("Active Branches", "الفروع النشطة"), f"{active_branches():,}")

    # --------------------------------------------------------------------------
    # FLOW OVERVIEW SECTION (3 lanes)
    # --------------------------------------------------------------------------
    st.markdown("<div class='section-header'>📊 Operational Flow Overview</div>", unsafe_allow_html=True)

    # Helper to get flow metrics per system (using actual system names from secrets)
    def get_system_metrics(system_display_name):
        # Map display name to actual key used in dataframes (System column)
        # For Manfari, the System column value might be "Manfari" or "MANFARI" – adjust if needed.
        # We'll filter by System column value (case-insensitive).
        sys_key = system_display_name.upper()
        metrics = {
            "purchase_count": 0, "purchase_value": 0,
            "receipt_count": 0, "receipt_qty": 0,
            "storage_qty": 0, "storage_value": 0,
            "sales_count": 0, "sales_value": 0,
            "pos_count": 0, "pos_value": 0,
            "invoice_count": 0, "invoice_value": 0,
            "delivery_count": 0, "delivery_pending": 0,
        }
        # Purchase
        if pur_df is not None and not pur_df.empty:
            df = pur_df[pur_df["System"].str.upper() == sys_key] if "System" in pur_df.columns else pur_df
            if not df.empty:
                metrics["purchase_count"] = df["PO"].nunique() if "PO" in df.columns else len(df)
                metrics["purchase_value"] = safe_get_col(df, "Subtotal").sum()
                if "Receipt Location" in df.columns:
                    metrics["receipt_count"] = df["Receipt Location"].nunique()
                    metrics["receipt_qty"] = safe_get_col(df, "Qty").sum()
        # Inventory
        if inv_df is not None and not inv_df.empty:
            df = inv_df[inv_df["System"].str.upper() == sys_key] if "System" in inv_df.columns else inv_df
            if not df.empty:
                metrics["storage_qty"] = int(safe_get_col(df, "On Hand").sum())
                metrics["storage_value"] = (safe_get_col(df, "On Hand") * safe_get_col(df, "Sale Price")).sum()
        # Sales
        if sales_df is not None and not sales_df.empty:
            df = sales_df[sales_df["System"].str.upper() == sys_key] if "System" in sales_df.columns else sales_df
            if not df.empty:
                so_col = get_display_col(df, "SO")
                unique = df.drop_duplicates(subset=[so_col]) if so_col in df.columns else df
                metrics["sales_count"] = len(unique)
                metrics["sales_value"] = safe_get_col(unique, "Total Amount").sum()
                metrics["invoice_count"] = len(unique)
                metrics["invoice_value"] = metrics["sales_value"]
                if "State" in df.columns:
                    delivered = df[df["State"].str.lower().isin(["done", "sale"])]
                    metrics["delivery_count"] = delivered["SO"].nunique() if "SO" in delivered.columns else len(delivered)
                    total_sales = df["SO"].nunique() if "SO" in df.columns else len(df)
                    metrics["delivery_pending"] = max(0, total_sales - metrics["delivery_count"])
        # POS
        if pos_df is not None and not pos_df.empty:
            df = pos_df[pos_df["System"].str.upper() == sys_key] if "System" in pos_df.columns else pos_df
            if not df.empty:
                po_col = get_display_col(df, "POS Order")
                unique = df.drop_duplicates(subset=[po_col]) if po_col in df.columns else df
                metrics["pos_count"] = len(unique)
                metrics["pos_value"] = safe_get_col(unique, "Total Amount").sum()
        return metrics

    # Define lanes (display names and internal key)
    lanes = ["Manfari", "Swag", "Laroche"]
    cols = st.columns(3)
    for idx, lane in enumerate(lanes):
        with cols[idx]:
            st.markdown(f"<div style='text-align:center; font-weight:600; margin-bottom:8px;'>{lane.upper()} LANE</div>", unsafe_allow_html=True)
            m = get_system_metrics(lane)
            stages = [
                ("📦 Purchase", f"{m['purchase_count']:,}", f"SAR {m['purchase_value']:,.0f}"),
                ("📥 Receipt", f"{m['receipt_count']:,}", f"Qty {m['receipt_qty']:,.0f}"),
                ("🏪 Storage", f"{m['storage_qty']:,}", f"SAR {m['storage_value']:,.0f}"),
                ("🛒 Sale/POS", f"{m['sales_count']+m['pos_count']:,}", f"SAR {m['sales_value']+m['pos_value']:,.0f}"),
                ("📄 Invoice", f"{m['invoice_count']:,}", f"SAR {m['invoice_value']:,.0f}"),
                ("🚚 Delivery", f"{m['delivery_count']:,}", f"Pending {m['delivery_pending']:,}"),
            ]
            for label, count, value in stages:
                # Color code based on pending or zero
                if "Pending" in value and m['delivery_pending'] > 0:
                    bg = hex_to_rgba(th_color("danger", "#dc2626"), 0.1)
                    border_left = f"3px solid {th_color('danger', '#dc2626')}"
                elif count == "0" or (isinstance(count, str) and count == "0") or (isinstance(count, int) and count == 0):
                    bg = hex_to_rgba(th_color("warning", "#f59e0b"), 0.05)
                    border_left = f"3px solid {th_color('warning', '#f59e0b')}"
                else:
                    bg = hex_to_rgba(th_color("accent1"), 0.05)
                    border_left = f"3px solid {th_color('accent1')}"
                st.markdown(
                    f"<div style='background:{bg}; border-radius:12px; padding:0.6rem; margin:8px 0; border-left:{border_left};'>"
                    f"<div style='font-size:0.7rem; color:{th('text_muted')};'>{label}</div>"
                    f"<div style='font-size:1rem; font-weight:600;'>{count}</div>"
                    f"<div style='font-size:0.7rem; color:{th('text_muted')};'>{value}</div></div>",
                    unsafe_allow_html=True,
                )

    # --------------------------------------------------------------------------
    # FLOW-BASED TABS
    # --------------------------------------------------------------------------
    tab_purchase, tab_receipt, tab_warehouse, tab_sales_pos, tab_invoice_delivery, tab_bottlenecks = st.tabs([
        f"📑 {t('Purchase & Request','المشتريات والطلبات')}",
        f"📥 {t('Receipt & Transfer','الاستلام والتحويل')}",
        f"🏪 {t('Warehouse Storage','تخزين المستودع')}",
        f"🛒 {t('Sales & POS','المبيعات ونقاط البيع')}",
        f"📄 {t('Invoice & Delivery','الفاتورة والتوصيل')}",
        f"⚠️ {t('Executive Bottlenecks','الاختناقات التنفيذية')}",
    ])

    # ---------- Purchase & Request Tab ----------
    with tab_purchase:
        st.markdown("<div class='section-header'>📑 Purchase & Request Overview</div>", unsafe_allow_html=True)
        if pur_df is None or pur_df.empty:
            st.info(t("No purchase data loaded. Click refresh in sidebar.", "لا توجد بيانات مشتريات. اضغط تحديث في الشريط الجانبي."))
        else:
            # KPIs
            total_po = pur_df["PO"].nunique() if "PO" in pur_df.columns else len(pur_df)
            total_val = safe_get_col(pur_df, "Subtotal").sum()
            total_qty = safe_get_col(pur_df, "Qty").sum()
            col1, col2, col3 = st.columns(3)
            col1.metric(t("Purchase Orders","أوامر الشراء"), f"{total_po:,}")
            col2.metric(t("Purchase Value","قيمة الشراء"), f"SAR {total_val:,.0f}")
            col3.metric(t("Total Qty","الكمية"), f"{total_qty:,.0f}")
            # Requested vs received gap (if Receipt Location available)
            if "Receipt Location" in pur_df.columns:
                received_lines = pur_df[pur_df["Receipt Location"].notna() & (pur_df["Receipt Location"] != "")]
                received_qty = safe_get_col(received_lines, "Qty").sum()
                gap = total_qty - received_qty
                st.metric(t("Requested vs Received Gap","الفجوة بين المطلوب والمستلم"), f"{gap:,.0f}", delta=f"{(gap/total_qty*100) if total_qty>0 else 0:.1f}%")
            # Vendor summary
            st.markdown("<div class='section-header'>🏭 Vendor Summary</div>", unsafe_allow_html=True)
            vendor_agg = pur_df.groupby("Vendor")["Subtotal"].sum().reset_index().sort_values("Subtotal", ascending=False).head(10)
            fig = px.bar(vendor_agg, x="Vendor", y="Subtotal", title=t("Top Vendors by Spend","أفضل الموردين بالإنفاق"), color="Subtotal", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
            st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            render_paginated_table(pur_df, "pur_page")
            st.download_button("⬇️ Export Purchase Data", to_csv(localize_df(pur_df)), dl_name("purchase", "csv"), "text/csv")

    # ---------- Receipt & Transfer Tab ----------
    with tab_receipt:
        st.markdown("<div class='section-header'>📥 Receipt & Transfer</div>", unsafe_allow_html=True)
        if pur_df is None or pur_df.empty:
            st.info(t("No receipt data available.", "لا توجد بيانات استلام."))
        else:
            # Receipt orders count (distinct Receipt Location)
            if "Receipt Location" in pur_df.columns:
                receipt_locs = pur_df[pur_df["Receipt Location"].notna() & (pur_df["Receipt Location"] != "")]["Receipt Location"].nunique()
                st.metric(t("Receipt Locations","مواقع الاستلام"), f"{receipt_locs:,}")
                # Pending receipt cases (where Receipt Location is empty)
                pending = pur_df[pur_df["Receipt Location"].isna() | (pur_df["Receipt Location"] == "")]
                st.metric(t("Pending Receipt Cases","حالات استلام معلقة"), f"{len(pending):,}")
                # Receipt location summary
                loc_sum = pur_df.groupby("Receipt Location")["Qty"].sum().reset_index().sort_values("Qty", ascending=False).head(10)
                fig = px.bar(loc_sum, x="Receipt Location", y="Qty", title=t("Receipt Qty by Location","كمية الاستلام حسب الموقع"), color="Qty", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            else:
                st.info("Receipt Location data not available in purchase records.")

    # ---------- Warehouse Storage Tab (Enhanced Inventory) ----------
    with tab_warehouse:
        st.markdown("<div class='section-header'>🏪 Warehouse Storage Dashboard</div>", unsafe_allow_html=True)
        # Refresh button for inventory (reuse existing refresh logic)
        # But for simplicity, we assume inventory is loaded via sidebar refresh.
        # Show inventory data if available
        inv_df_local = st.session_state.get("inventory_df")
        branch_df_local = st.session_state.get("inventory_branch_df")
        if inv_df_local is None or inv_df_local.empty:
            st.info(t("No inventory data loaded. Use refresh button in sidebar.", "لا توجد بيانات مخزون. استخدم زر التحديث في الشريط الجانبي."))
        else:
            # Derived fields
            inv_df_local["Stock Value"] = inv_df_local["On Hand"] * inv_df_local["Sale Price"]
            if "Purchase Qty" not in inv_df_local.columns:
                inv_df_local["Purchase Qty"] = 0
            inv_df_local["Estimated Sold"] = (inv_df_local["Purchase Qty"] - inv_df_local["On Hand"]).clip(lower=0)
            inv_df_local["Sell Through %"] = inv_df_local.apply(lambda r: (r["Estimated Sold"]/r["Purchase Qty"]*100) if r["Purchase Qty"]>0 else 0, axis=1)
            low_thresh = st.number_input(t("Low Stock Threshold","حد المخزون المنخفض"), min_value=0, value=5, step=1, key="wh_low_thresh")
            def status(r):
                oh = r["On Hand"]
                if oh == 0: return "Zero"
                elif oh <= low_thresh: return "Low"
                elif oh <= low_thresh*3: return "Medium"
                else: return "Healthy"
            inv_df_local["Stock Status"] = inv_df_local.apply(status, axis=1)

            # KPIs
            total_qty = int(inv_df_local["On Hand"].sum())
            total_value = inv_df_local["Stock Value"].sum()
            zero_cnt = len(inv_df_local[inv_df_local["On Hand"] == 0])
            low_cnt = len(inv_df_local[(inv_df_local["On Hand"] > 0) & (inv_df_local["On Hand"] <= low_thresh)])
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("Total On Hand","إجمالي المتوفر"), f"{total_qty:,}")
            col2.metric(t("Stock Value","قيمة المخزون"), f"SAR {total_value:,.0f}")
            col3.metric(t("Zero Stock","صفر مخزون"), f"{zero_cnt:,}")
            col4.metric(t("Low Stock","مخزون منخفض"), f"{low_cnt:,}")

            # Branch stock chart
            if branch_df_local is not None and not branch_df_local.empty:
                # Add price and value to branch
                price_map = inv_df_local.set_index("Model Code")["Sale Price"].to_dict()
                branch_df_local["Sale Price"] = branch_df_local["Model Code"].map(price_map).fillna(0)
                branch_df_local["Stock Value"] = branch_df_local["On Hand"] * branch_df_local["Sale Price"]
                branch_val = branch_df_local.groupby("Branch")["Stock Value"].sum().reset_index().sort_values("Stock Value", ascending=False).head(10)
                fig = px.bar(branch_val, x="Branch", y="Stock Value", title=t("Stock Value by Branch","قيمة المخزون حسب الفرع"), color="Stock Value", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

            # Top models by stock value
            top_models = inv_df_local.nlargest(10, "Stock Value")[["Model Code", "Stock Value"]]
            fig2 = px.bar(top_models, x="Model Code", y="Stock Value", title=t("Top 10 Models by Stock Value","أفضل 10 موديلات بقيمة المخزون"), color="Stock Value", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
            st.plotly_chart(apply_plotly_theme(fig2), use_container_width=True)

            # Stock health donut
            status_counts = inv_df_local["Stock Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig3 = px.pie(status_counts, names="Status", values="Count", hole=0.55, title=t("Stock Health Distribution","توزيع صحة المخزون"))
            st.plotly_chart(apply_plotly_theme(fig3), use_container_width=True)

            # Action tables
            st.markdown("<div class='section-header'>⚡ Actionable Items</div>", unsafe_allow_html=True)
            reorder = inv_df_local[(inv_df_local["On Hand"] > 0) & (inv_df_local["On Hand"] <= low_thresh)].copy()
            if not reorder.empty:
                reorder = reorder.sort_values(["On Hand", "Stock Value"], ascending=[True, False])
                st.subheader(t("Reorder Priority","أولوية إعادة الطلب"))
                render_paginated_table(reorder[["Model Code", "Product", "On Hand", "Stock Value", "Sell Through %"]], "inv_reorder_wh")
            dead = inv_df_local[(inv_df_local["On Hand"] > low_thresh) & (inv_df_local["Sell Through %"] <= 20)].copy()
            if not dead.empty:
                dead = dead.sort_values("Stock Value", ascending=False)
                st.subheader(t("Dead / Slow Stock","المخزون الميت/البطيء"))
                render_paginated_table(dead[["Model Code", "Product", "On Hand", "Stock Value", "Purchase Qty", "Estimated Sold", "Sell Through %"]], "inv_dead_wh")

            # Full inventory table
            with st.expander(t("Full Inventory Detail","تفاصيل المخزون الكاملة")):
                render_paginated_table(inv_df_local[["System","Model Code","Product","Sale Price","On Hand","Purchase Qty","Estimated Sold","Sell Through %","Stock Value","Stock Status"]], "inv_full_wh")

            # Exports
            col_csv, col_xls, col_mat = st.columns(3)
            with col_csv:
                st.download_button("⬇️ CSV", to_csv(localize_df(inv_df_local)), dl_name("inventory", "csv"), "text/csv")
            with col_xls:
                st.download_button("⬇️ Excel", to_excel(localize_df(inv_df_local)), dl_name("inventory", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col_mat:
                if branch_df_local is not None and not branch_df_local.empty:
                    bdf = branch_df_local.copy()
                    if not bdf.empty:
                        mat = bdf.pivot_table(index="Model Code", columns="Branch", values="On Hand", aggfunc="sum", fill_value=0)
                        out = io.BytesIO()
                        with pd.ExcelWriter(out, engine="openpyxl") as w:
                            mat.to_excel(w, sheet_name="Branch_Matrix")
                        out.seek(0)
                        st.download_button("📊 Branch Matrix", out, dl_name("branch_matrix", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ---------- Sales & POS Tab ----------
    with tab_sales_pos:
        st.markdown("<div class='section-header'>🛒 Sales & POS Performance</div>", unsafe_allow_html=True)
        # Sales section
        st.subheader(t("Sales Orders","أوامر المبيعات"))
        if sales_df is not None and not sales_df.empty:
            so_col = get_display_col(sales_df, "SO")
            unique_sales = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
            total_sales_val = safe_get_col(unique_sales, "Total Amount").sum()
            total_sales_orders = len(unique_sales)
            col1, col2 = st.columns(2)
            col1.metric(t("Sales Value","قيمة المبيعات"), f"SAR {total_sales_val:,.0f}")
            col2.metric(t("Orders","الطلبات"), f"{total_sales_orders:,}")
            if has_col(unique_sales, "Customer"):
                top_cust = unique_sales.groupby("Customer")["Total Amount"].sum().reset_index().sort_values("Total Amount", ascending=False).head(10)
                fig = px.bar(top_cust, x="Customer", y="Total Amount", title=t("Top Customers","أفضل العملاء"), color="Total Amount", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            render_paginated_table(sales_df, "sales_page")
            st.download_button("⬇️ Export Sales", to_csv(localize_df(sales_df)), dl_name("sales", "csv"), "text/csv")
        else:
            st.info(t("No sales data loaded.", "لا توجد بيانات مبيعات."))
        st.divider()
        # POS section
        st.subheader(t("Point of Sale","نقاط البيع"))
        if pos_df is not None and not pos_df.empty:
            po_col = get_display_col(pos_df, "POS Order")
            unique_pos = pos_df.drop_duplicates(subset=[po_col]) if po_col in pos_df.columns else pos_df
            total_pos_val = safe_get_col(unique_pos, "Total Amount").sum()
            total_bills = len(unique_pos)
            col1, col2 = st.columns(2)
            col1.metric(t("POS Revenue","إيرادات نقاط البيع"), f"SAR {total_pos_val:,.0f}")
            col2.metric(t("Bills","الفواتير"), f"{total_bills:,}")
            if has_col(unique_pos, "Branch"):
                branch_perf = unique_pos.groupby("Branch")["Total Amount"].sum().reset_index().sort_values("Total Amount", ascending=False).head(10)
                fig = px.bar(branch_perf, x="Branch", y="Total Amount", title=t("Branch POS Performance","أداء فروع POS"), color="Total Amount", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            if has_col(unique_pos, "Cashier"):
                cashier_perf = unique_pos.groupby("Cashier")["Total Amount"].sum().reset_index().sort_values("Total Amount", ascending=False).head(10)
                fig2 = px.bar(cashier_perf, x="Cashier", y="Total Amount", title=t("Cashier Performance","أداء الكاشير"), color="Total Amount", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
                st.plotly_chart(apply_plotly_theme(fig2), use_container_width=True)
            render_paginated_table(pos_df, "pos_page")
            st.download_button("⬇️ Export POS", to_csv(localize_df(pos_df)), dl_name("pos", "csv"), "text/csv")
        else:
            st.info(t("No POS data loaded.", "لا توجد بيانات نقاط بيع."))

    # ---------- Invoice & Delivery Tab ----------
    with tab_invoice_delivery:
        st.markdown("<div class='section-header'>📄 Invoice & Delivery Status</div>", unsafe_allow_html=True)
        if sales_df is not None and not sales_df.empty and "State" in sales_df.columns:
            so_col = get_display_col(sales_df, "SO")
            unique = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
            invoice_count = len(unique)
            invoice_value = safe_get_col(unique, "Total Amount").sum()
            # Delivery status
            delivered = unique[unique["State"].str.lower().isin(["done", "sale"])]
            delivered_count = len(delivered)
            delivered_value = safe_get_col(delivered, "Total Amount").sum()
            pending = unique[~unique["State"].str.lower().isin(["done", "sale"])]
            pending_count = len(pending)
            pending_value = safe_get_col(pending, "Total Amount").sum()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("Total Invoices","إجمالي الفواتير"), f"{invoice_count:,}")
            col2.metric(t("Invoice Value","قيمة الفواتير"), f"SAR {invoice_value:,.0f}")
            col3.metric(t("Delivered Orders","الطلبات الموصلة"), f"{delivered_count:,}", delta=f"SAR {delivered_value:,.0f}")
            col4.metric(t("Pending Delivery","معلق التوصيل"), f"{pending_count:,}", delta=f"SAR {pending_value:,.0f}", delta_color="inverse")
            # Funnel chart: Sales -> Invoiced -> Delivered
            funnel_data = pd.DataFrame({
                "Stage": ["Sales Orders", "Invoiced", "Delivered"],
                "Count": [len(unique), len(unique), delivered_count]
            })
            fig = px.funnel(funnel_data, x="Count", y="Stage", title=t("Fulfillment Funnel","مسار التنفيذ"))
            st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            # Bottleneck table: orders without delivery
            if not pending.empty:
                st.subheader(t("Orders Awaiting Delivery","طلبات في انتظار التوصيل"))
                render_paginated_table(pending[["SO", "Customer", "Total Amount", "State"]], "pending_delivery")
        else:
            st.info(t("No sales data or state column missing.", "لا توجد بيانات مبيعات أو عمود الحالة مفقود."))

    # ---------- Executive Bottlenecks Tab ----------
    with tab_bottlenecks:
        st.markdown("<div class='section-header'>⚠️ Executive Bottlenecks & Alerts</div>", unsafe_allow_html=True)
        alerts = []
        # 1. Pending receipt (from purchase)
        if pur_df is not None and not pur_df.empty and "Receipt Location" in pur_df.columns:
            pending_receipt = pur_df[pur_df["Receipt Location"].isna() | (pur_df["Receipt Location"] == "")]
            if not pending_receipt.empty:
                alerts.append(f"📥 **Pending Receipt**: {len(pending_receipt)} purchase lines not yet received.")
        # 2. Low stock / zero stock (from inventory)
        if inv_df is not None and not inv_df.empty:
            qty = safe_get_col(inv_df, "On Hand")
            zero = (qty == 0).sum()
            low = ((qty > 0) & (qty <= 5)).sum()
            if zero > 0:
                alerts.append(f"🔴 **Zero Stock**: {zero} products have zero stock. Urgent reorder needed.")
            if low > 0:
                alerts.append(f"⚠️ **Low Stock**: {low} products have low stock (≤5).")
        # 3. Dead stock (Sell Through % <= 20)
        if inv_df is not None and not inv_df.empty:
            # Need Purchase Qty for sell through
            if "Purchase Qty" in inv_df.columns:
                inv_copy = inv_df.copy()
                inv_copy["Est Sold"] = (inv_copy["Purchase Qty"] - inv_copy["On Hand"]).clip(lower=0)
                inv_copy["Sell %"] = inv_copy.apply(lambda r: (r["Est Sold"]/r["Purchase Qty"]*100) if r["Purchase Qty"]>0 else 0, axis=1)
                dead = inv_copy[(inv_copy["On Hand"] > 5) & (inv_copy["Sell %"] <= 20)]
                if not dead.empty:
                    alerts.append(f"🗄️ **Dead/Slow Stock**: {len(dead)} products with high stock but low sell-through (≤20%).")
        # 4. Delivery pending (from sales)
        if sales_df is not None and not sales_df.empty and "State" in sales_df.columns:
            so_col = get_display_col(sales_df, "SO")
            unique = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
            pending_delivery = unique[~unique["State"].str.lower().isin(["done", "sale"])]
            if not pending_delivery.empty:
                alerts.append(f"🚚 **Delivery Pending**: {len(pending_delivery)} sales orders not yet delivered.")
        # 5. Purchase without receipt (if Receipt Location missing)
        if pur_df is not None and not pur_df.empty and "Receipt Location" in pur_df.columns:
            no_receipt = pur_df[pur_df["Receipt Location"].isna() | (pur_df["Receipt Location"] == "")]
            if not no_receipt.empty:
                alerts.append(f"📦 **Purchase without Receipt**: {len(no_receipt)} purchase lines have no receipt location.")
        # 6. Received but not stored (if inventory branch has no stock for received items) – complex, skip for now

        if alerts:
            for alert in alerts:
                if "🔴" in alert or "⚠️" in alert:
                    st.markdown(f"<div class='alert-banner'>{alert}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='warn-banner'>{alert}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='ok-banner'>✅ No critical bottlenecks detected. All processes are flowing smoothly.</div>", unsafe_allow_html=True)

        # Also show a summary table of bottlenecks by system (optional)
        st.markdown("<div class='section-header'>📊 Bottleneck Summary by System</div>", unsafe_allow_html=True)
        bottleneck_data = []
        for sys in ["Manfari", "Swag", "Laroche"]:
            m = get_system_metrics(sys)
            bottleneck_data.append({
                "System": sys,
                "Pending Receipt": m['receipt_qty'] if m['receipt_qty'] > 0 else 0,  # placeholder
                "Low Stock": 0,  # would need per-system inventory
                "Delivery Pending": m['delivery_pending'],
            })
        bottleneck_df = pd.DataFrame(bottleneck_data)
        st.dataframe(bottleneck_df, use_container_width=True)

# ------------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------------
restore_session()
if not st.session_state.get("authenticated"):
    show_login()
else:
    show_dashboard()
