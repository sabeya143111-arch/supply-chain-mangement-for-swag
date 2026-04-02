import io
import hashlib
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import altair as alt
import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

st.set_page_config(
    page_title="SWAG Sales & Purchase Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: #05070d;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(52,152,219,0.12) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 80% 90%, rgba(46,204,113,0.06) 0%, transparent 60%);
    min-height: 100vh;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080b12 0%, #05070d 100%) !important;
    border-right: 1px solid rgba(52,152,219,0.12) !important;
    box-shadow: 4px 0 40px rgba(0,0,0,0.6);
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] *, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div { color: #c8d6e8 !important; }

.sidebar-logo {
    background: linear-gradient(135deg, rgba(52,152,219,0.15), rgba(46,204,113,0.08));
    border-bottom: 1px solid rgba(52,152,219,0.15);
    padding: 20px 16px 16px;
    margin: -1rem -1rem 16px;
    text-align: center;
}
.sidebar-logo-text {
    font-size: 1.3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #3498db, #2ecc71);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}
.sidebar-logo-sub {
    font-size: 0.65rem;
    color: #5a7a9a !important;
    margin-top: 2px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.sidebar-user-card {
    background: linear-gradient(135deg, rgba(52,152,219,0.1), rgba(46,204,113,0.05));
    border: 1px solid rgba(52,152,219,0.2);
    border-radius: 12px;
    padding: 12px 14px;
    margin: 8px 0 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sidebar-avatar {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #3498db, #2ecc71);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.sidebar-user-name {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #e8edf2 !important;
}
.sidebar-user-role {
    font-size: 0.62rem !important;
    color: #5a7a9a !important;
}

.dashboard-hero {
    background: linear-gradient(135deg, rgba(12,16,24,0.95) 0%, rgba(8,12,20,0.95) 100%);
    border: 1px solid rgba(52,152,219,0.12);
    border-radius: 24px;
    padding: 34px 38px;
    margin-bottom: 26px;
    position: relative;
    overflow: hidden;
}
.dashboard-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 60% 80% at 0% 50%, rgba(52,152,219,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 40% 60% at 100% 50%, rgba(46,204,113,0.05) 0%, transparent 60%);
    pointer-events: none;
}
.dashboard-hero::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(52,152,219,0.5) 30%, rgba(46,204,113,0.5) 70%, transparent 100%);
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(52,152,219,0.1);
    border: 1px solid rgba(52,152,219,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.68rem;
    font-weight: 700;
    color: #3498db;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.hero-eyebrow-dot {
    width: 5px; height: 5px;
    background: #2ecc71;
    border-radius: 50%;
}
.hero-title {
    font-size: 2.35rem;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1.15;
    margin-bottom: 10px;
    color: #f0f4f8;
}
.hero-title-accent {
    background: linear-gradient(90deg, #3498db, #2ecc71, #3498db);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    font-size: 0.92rem;
    color: #5a7a9a;
    line-height: 1.6;
    max-width: 640px;
    margin-bottom: 0;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px;
    margin: 20px 0;
}
.kpi-card {
    background: rgba(12,16,24,0.82);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 22px 20px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #3498db, #2ecc71);
}
.kpi-card-bg {
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 40%;
    background: radial-gradient(ellipse at 80% 50%, rgba(52,152,219,0.05), transparent 70%);
    pointer-events: none;
}
.kpi-icon {
    font-size: 1.6rem;
    margin-bottom: 14px;
    display: block;
    opacity: 0.9;
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 6px;
    background: linear-gradient(135deg, #ffffff, #a8c8e8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.kpi-label {
    font-size: 0.7rem;
    color: #4a6880;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 18px;
}
.section-header-bar {
    width: 3px; height: 22px;
    background: linear-gradient(180deg, #3498db, #2ecc71);
    border-radius: 2px;
    flex-shrink: 0;
}
.section-header-title {
    font-size: 1rem;
    font-weight: 700;
    color: #e8edf2;
    letter-spacing: -0.2px;
    line-height: 1.2;
}
.section-header-sub {
    font-size: 0.68rem;
    color: #4a6880;
    margin-top: 1px;
}
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(52,152,219,0.15), rgba(46,204,113,0.1), transparent);
    margin: 24px 0;
}

.chart-card {
    background: rgba(10,13,20,0.72);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.chart-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(ellipse 40% 40% at 100% 0%, rgba(52,152,219,0.03), transparent);
    pointer-events: none;
}
.chart-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #6b8ab0;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.chart-title-accent {
    display: inline-block;
    width: 3px; height: 14px;
    background: linear-gradient(180deg, #3498db, #2ecc71);
    border-radius: 2px;
}

.table-wrapper {
    width: 100%;
    overflow-x: auto;
    border-radius: 18px;
    background: rgba(8,11,18,0.8);
    border: 1px solid rgba(255,255,255,0.05);
    margin: 12px 0;
}
.premium-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}
.premium-table thead tr {
    background: rgba(5,7,13,0.9);
    border-bottom: 1px solid rgba(52,152,219,0.2);
}
.premium-table thead th {
    color: #3498db;
    font-weight: 700;
    padding: 14px 18px;
    text-align: center;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    white-space: nowrap;
}
.premium-table tbody tr {
    transition: all 0.15s ease;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}
.premium-table tbody tr:nth-child(even) {
    background: rgba(255,255,255,0.01);
}
.premium-table tbody td {
    padding: 11px 18px;
    text-align: center;
    color: #c8d6e8;
    vertical-align: middle;
}
.premium-table tbody td:first-child {
    font-weight: 700;
    color: #4aa8e0;
}

.info-banner {
    background: rgba(52,152,219,0.07);
    border: 1px solid rgba(52,152,219,0.2);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 12px 0;
    font-size: 0.82rem;
    color: #6b8ab0;
}
.warn-banner {
    background: rgba(241,196,15,0.07);
    border: 1px solid rgba(241,196,15,0.2);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 12px 0;
    font-size: 0.82rem;
    color: #c9a227;
}

.pagination-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 10px 0;
    font-size: 0.82rem;
    color: #6b8ab0;
}
.page-info {
    background: rgba(52,152,219,0.1);
    border: 1px solid rgba(52,152,219,0.25);
    border-radius: 8px;
    padding: 4px 14px;
    color: #3498db;
    font-weight: 700;
    font-size: 0.8rem;
}

.footer {
    text-align: center;
    padding: 28px 0 16px;
    color: #2a3a4a;
    font-size: 0.68rem;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 48px;
    letter-spacing: 0.3px;
}
.footer span { color: #3a5a7a; }

.stButton > button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #c8d6e8 !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    transition: all 0.25s ease !important;
    padding: 8px 18px !important;
}
.stButton > button:hover {
    background: rgba(52,152,219,0.1) !important;
    border-color: rgba(52,152,219,0.35) !important;
    color: #e8edf2 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1e5a8e, #1a4a7a) !important;
    border: 1px solid rgba(52,152,219,0.5) !important;
    color: #fff !important;
}
.stTextInput > div > div > input,
.stDateInput > div > div > input,
.stMultiSelect > div > div,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #e8edf2 !important;
}
.stTextInput label, .stDateInput label, .stMultiSelect label, .stSelectbox label, .stRadio label {
    color: #6b8ab0 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
}
.stDownloadButton > button {
    background: rgba(52,152,219,0.07) !important;
    border: 1px solid rgba(52,152,219,0.2) !important;
    color: #4aa8e0 !important;
    border-radius: 10px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #6b8ab0 !important;
    border-radius: 10px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(52,152,219,0.2), rgba(46,204,113,0.1)) !important;
    color: #e8edf2 !important;
    border: 1px solid rgba(52,152,219,0.3) !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #05070d; }
::-webkit-scrollbar-thumb { background: #1a2a3a; border-radius: 3px; }

@media (max-width: 768px) {
    .dashboard-hero { padding: 24px 20px; }
    .hero-title { font-size: 1.65rem; }
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]

C_SYSTEM     = "System"
C_DATE       = "Date"
C_PO         = "PO"
C_SO         = "SO"
C_VENDOR     = "Vendor"
C_CUSTOMER   = "Customer"
C_BRAND_CAT  = "Brand Category"
C_CATEGORY   = "Category"
C_MODEL      = "Model Code"
C_PRODUCT    = "Product"
C_QTY        = "Qty"
C_UNIT_PRICE = "Unit Price"
C_SUBTOTAL   = "Subtotal"

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE
# ─────────────────────────────────────────────────────────────────────────────
def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    return ar if get_lang() == "AR" else en

def get_dir():
    return "rtl" if get_lang() == "AR" else "ltr"

def get_system_name(key):
    cfg = st.secrets.get(key, {})
    return cfg.get("name_ar", cfg.get("name", key)) if get_lang() == "AR" else cfg.get("name", key)

_COL_LABELS_EN = {
    C_SYSTEM: "System", C_DATE: "Date", C_PO: "PO", C_SO: "SO",
    C_VENDOR: "Vendor", C_CUSTOMER: "Customer", C_BRAND_CAT: "Brand Category",
    C_CATEGORY: "Category", C_MODEL: "Model Code", C_PRODUCT: "Product",
    C_QTY: "Qty", C_UNIT_PRICE: "Unit Price", C_SUBTOTAL: "Subtotal",
}
_COL_LABELS_AR = {
    C_SYSTEM: "النظام", C_DATE: "التاريخ", C_PO: "أمر الشراء", C_SO: "أمر البيع",
    C_VENDOR: "المورد", C_CUSTOMER: "العميل", C_BRAND_CAT: "الفئة التجارية",
    C_CATEGORY: "الفئة", C_MODEL: "رمز الموديل", C_PRODUCT: "المنتج",
    C_QTY: "الكمية", C_UNIT_PRICE: "سعر الوحدة", C_SUBTOTAL: "المجموع",
}

def col_label(canonical):
    return (_COL_LABELS_AR if get_lang() == "AR" else _COL_LABELS_EN).get(canonical, canonical)

def df_for_display(df):
    if df is None or df.empty:
        return df
    label_map = _COL_LABELS_AR if get_lang() == "AR" else _COL_LABELS_EN
    return df.rename(columns={k: v for k, v in label_map.items() if k in df.columns})

# ─────────────────────────────────────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────────────────────────────────────
_DEF = {
    "authenticated": False,
    "user_email": "",
    "lang": "EN",
    "analytics_view": "purchase",
    "salesanalyticsdf": None,
    "po_analytics_df": None,
    "page_sales_detail": 0,
    "page_purchase_detail": 0,
    "page_purchase_model": 0,
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

PAGE_SIZE = 50
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
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)

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

def dl_name(tag, ext):
    return f"swag_{tag}_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# EXCEL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _style_worksheet(ws, df_clean, lang="EN"):
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    if lang == "AR":
        ws.sheet_view.rightToLeft = True

    hdr_fill = PatternFill("solid", fgColor="2C3E50")
    hdr_font = Font(bold=True, color="FFFFFF", size=11, name="Inter")
    thin = Side(border_style="thin", color="2E3B4E")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    alt_fill = PatternFill("solid", fgColor="111722")
    normal_font = Font(name="Inter", size=10, color="DDE7F3")
    num_align = Alignment(horizontal="right", vertical="center")
    center_align = Alignment(horizontal="center", vertical="center")
    total_fill = PatternFill("solid", fgColor="3498DB")
    total_font = Font(bold=True, name="Inter", color="FFFFFF")

    max_row = ws.max_row
    max_col = ws.max_column

    for col_num in range(1, max_col + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = center_align
        cell.border = border

    for row in ws.iter_rows(min_row=2, max_row=max_row):
        for cell in row:
            cell.border = border
            cell.font = normal_font
            if cell.row % 2 == 0:
                cell.fill = alt_fill
            cell.alignment = num_align if isinstance(cell.value, (int, float)) else center_align

    for col_num in range(1, max_col + 1):
        col_letter = get_column_letter(col_num)
        max_len = 0
        for r in ws.iter_rows(min_col=col_num, max_col=col_num):
            for cell in r:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    numeric_targets = []
    for idx in range(1, max_col + 1):
        h = ws.cell(row=1, column=idx).value
        if h in ["Qty", "Subtotal", "Unit Price", "الكمية", "المجموع", "سعر الوحدة"]:
            numeric_targets.append(idx)

    total_row = max_row + 1
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=1).font = total_font
    ws.cell(row=total_row, column=1).fill = total_fill
    ws.cell(row=total_row, column=1).alignment = center_align

    from openpyxl.utils import get_column_letter as gcl
    for idx in numeric_targets:
        col = gcl(idx)
        ws.cell(row=total_row, column=idx, value=f"=SUM({col}2:{col}{max_row})")
        ws.cell(row=total_row, column=idx).font = total_font
        ws.cell(row=total_row, column=idx).fill = total_fill
        ws.cell(row=total_row, column=idx).alignment = num_align

    ws.freeze_panes = "A2"

def _excel_generic(df, sheet_name="Data"):
    lang = st.session_state.get("lang", "EN")
    buf = io.BytesIO()
    clean = df.copy()
    clean = clean.rename(columns={k: v for k, v in ((_COL_LABELS_AR if lang == "AR" else _COL_LABELS_EN).items()) if k in clean.columns})
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        clean.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        _style_worksheet(writer.sheets[sheet_name[:31]], clean, lang=lang)
    return buf.getvalue()

def to_excel_purchase(df):
    return _excel_generic(df, "SWAG Purchase")

def to_excel_sales(df):
    return _excel_generic(df, "SWAG Sales")

def to_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_history_for_system(system_key, model_code, date_from, date_to):
    empty_cols = [C_SYSTEM, C_DATE, C_PO, C_VENDOR, C_BRAND_CAT, C_CATEGORY, C_MODEL, C_PRODUCT, C_QTY, C_UNIT_PRICE, C_SUBTOTAL]
    empty_df = pd.DataFrame(columns=empty_cols)
    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]

    try:
        date_from_dt = f"{date_from} 00:00:00"
        date_to_dt = f"{date_to} 23:59:59"
        line_domain = [
            ["order_id.state", "in", ["purchase", "done"]],
            ["order_id.date_order", ">=", date_from_dt],
            ["order_id.date_order", "<=", date_to_dt],
        ]
        if model_code and str(model_code).strip():
            line_domain.append(["product_id.default_code", "=", str(model_code).strip()])

        lines = _x(
            u, db, uid, ak, "purchase.order.line", "search_read", [line_domain],
            {"fields": ["order_id", "product_id", "product_qty", "price_unit"], "limit": 10000, "order": "order_id desc"}
        )
        if not lines:
            return empty_df

        order_ids = list({l["order_id"][0] for l in lines if isinstance(l.get("order_id"), list)})
        product_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})

        orders = _x(
            u, db, uid, ak, "purchase.order", "search_read", [[[ "id", "in", order_ids ]]],
            {"fields": ["id", "name", "partner_id", "date_order"], "limit": len(order_ids) + 10}
        )
        order_map = {o["id"]: o for o in orders}

        products = _x(
            u, db, uid, ak, "product.product", "search_read", [[[ "id", "in", product_ids ]]],
            {"fields": ["id", "default_code", "display_name", "categ_id", "product_tmpl_id"], "limit": len(product_ids) + 10}
        )
        prod_map = {p["id"]: p for p in products}

        tmpl_ids = list({p["product_tmpl_id"][0] for p in products if isinstance(p.get("product_tmpl_id"), list)})
        tmpl_map = {}
        if tmpl_ids:
            try:
                tmpls = _x(
                    u, db, uid, ak, "product.template", "search_read", [[[ "id", "in", tmpl_ids ]]],
                    {"fields": ["id", "x_brand_category_id"], "limit": len(tmpl_ids) + 10}
                )
                tmpl_map = {t_["id"]: t_ for t_ in tmpls}
            except Exception:
                tmpl_map = {}

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            order = order_map.get(oid, {})
            prod = prod_map.get(pid, {})

            raw_date = order.get("date_order") or ""
            try:
                date_str = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            except Exception:
                date_str = raw_date[:10] if raw_date else ""

            partner = order.get("partner_id")
            vendor = str(partner[1]) if isinstance(partner, list) and len(partner) > 1 else (str(partner) if partner else "")

            categ = prod.get("categ_id")
            category = str(categ[1]) if isinstance(categ, list) and len(categ) > 1 else (str(categ) if categ else "")

            brand_category = ""
            tmpl_ref = prod.get("product_tmpl_id")
            if isinstance(tmpl_ref, list) and tmpl_ref:
                tmpl = tmpl_map.get(tmpl_ref[0], {})
                bc = tmpl.get("x_brand_category_id")
                if isinstance(bc, list):
                    brand_category = str(bc[1]) if len(bc) > 1 else ""
                elif bc:
                    brand_category = str(bc)

            qty = float(line.get("product_qty") or 0)
            unit_price = float(line.get("price_unit") or 0)
            subtotal = round(qty * unit_price, 2)

            rows.append({
                C_SYSTEM: system_key,
                C_DATE: date_str,
                C_PO: str(order.get("name") or ""),
                C_VENDOR: vendor,
                C_BRAND_CAT: brand_category,
                C_CATEGORY: category,
                C_MODEL: str(prod.get("default_code") or ""),
                C_PRODUCT: str(prod.get("display_name") or ""),
                C_QTY: qty,
                C_UNIT_PRICE: unit_price,
                C_SUBTOTAL: subtotal,
            })

        df = pd.DataFrame(rows) if rows else empty_df
        for c in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
            if c in df.columns:
                df[c] = _to_num(df[c])
        for c in [col for col in df.columns if col not in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]]:
            df[c] = df[c].fillna("").astype(str)
        return df.sort_values(by=C_DATE, ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sales_history_for_system(system_key, model_code, date_from, date_to):
    empty_cols = [C_SYSTEM, C_DATE, C_SO, C_CUSTOMER, C_BRAND_CAT, C_CATEGORY, C_MODEL, C_PRODUCT, C_QTY, C_UNIT_PRICE, C_SUBTOTAL]
    empty_df = pd.DataFrame(columns=empty_cols)
    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]

    try:
        date_from_dt = f"{date_from} 00:00:00"
        date_to_dt = f"{date_to} 23:59:59"
        line_domain = [
            ["order_id.state", "in", ["sale", "done"]],
            ["order_id.date_order", ">=", date_from_dt],
            ["order_id.date_order", "<=", date_to_dt],
        ]
        if model_code and str(model_code).strip():
            line_domain.append(["product_id.default_code", "=", str(model_code).strip()])

        lines = _x(
            u, db, uid, ak, "sale.order.line", "search_read", [line_domain],
            {"fields": ["order_id", "product_id", "product_uom_qty", "price_unit"], "limit": 20000, "order": "order_id desc"}
        )
        if not lines:
            return empty_df

        order_ids = list({l["order_id"][0] for l in lines if isinstance(l.get("order_id"), list)})
        product_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})

        orders = _x(
            u, db, uid, ak, "sale.order", "search_read", [[[ "id", "in", order_ids ]]],
            {"fields": ["id", "name", "partner_id", "date_order"], "limit": len(order_ids) + 10}
        )
        order_map = {o["id"]: o for o in orders}

        products = _x(
            u, db, uid, ak, "product.product", "search_read", [[[ "id", "in", product_ids ]]],
            {"fields": ["id", "default_code", "display_name", "categ_id", "product_tmpl_id"], "limit": len(product_ids) + 10}
        )
        prod_map = {p["id"]: p for p in products}

        tmpl_ids = list({p["product_tmpl_id"][0] for p in products if isinstance(p.get("product_tmpl_id"), list)})
        tmpl_map = {}
        if tmpl_ids:
            try:
                tmpls = _x(
                    u, db, uid, ak, "product.template", "search_read", [[[ "id", "in", tmpl_ids ]]],
                    {"fields": ["id", "x_brand_category_id"], "limit": len(tmpl_ids) + 10}
                )
                tmpl_map = {t_["id"]: t_ for t_ in tmpls}
            except Exception:
                tmpl_map = {}

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            order = order_map.get(oid, {})
            prod = prod_map.get(pid, {})

            raw_date = order.get("date_order") or ""
            try:
                date_str = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            except Exception:
                date_str = raw_date[:10] if raw_date else ""

            partner = order.get("partner_id")
            customer = str(partner[1]) if isinstance(partner, list) and len(partner) > 1 else (str(partner) if partner else "")

            categ = prod.get("categ_id")
            category = str(categ[1]) if isinstance(categ, list) and len(categ) > 1 else (str(categ) if categ else "")

            brand_category = ""
            tmpl_ref = prod.get("product_tmpl_id")
            if isinstance(tmpl_ref, list) and tmpl_ref:
                tmpl = tmpl_map.get(tmpl_ref[0], {})
                bc = tmpl.get("x_brand_category_id")
                if isinstance(bc, list):
                    brand_category = str(bc[1]) if len(bc) > 1 else ""
                elif bc:
                    brand_category = str(bc)

            qty = float(line.get("product_uom_qty") or 0)
            unit_price = float(line.get("price_unit") or 0)
            subtotal = round(qty * unit_price, 2)

            rows.append({
                C_SYSTEM: system_key,
                C_DATE: date_str,
                C_SO: str(order.get("name") or ""),
                C_CUSTOMER: customer,
                C_BRAND_CAT: brand_category,
                C_CATEGORY: category,
                C_MODEL: str(prod.get("default_code") or ""),
                C_PRODUCT: str(prod.get("display_name") or ""),
                C_QTY: qty,
                C_UNIT_PRICE: unit_price,
                C_SUBTOTAL: subtotal,
            })

        df = pd.DataFrame(rows) if rows else empty_df
        for c in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
            if c in df.columns:
                df[c] = _to_num(df[c])
        for c in [col for col in df.columns if col not in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]]:
            df[c] = df[c].fillna("").astype(str)
        return df.sort_values(by=C_DATE, ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_all_systems_purchase_history(model_code, date_from, date_to, system_keys=None):
    keys = system_keys or SYSTEM_KEYS
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_purchase_history_for_system, k, model_code, date_from, date_to): k for k in keys}
        for f in as_completed(futs):
            try:
                df = f.result()
                if df is not None and not df.empty:
                    results.append(df)
            except Exception:
                pass
    if not results:
        return pd.DataFrame(columns=[C_SYSTEM, C_DATE, C_PO, C_VENDOR, C_BRAND_CAT, C_CATEGORY, C_MODEL, C_PRODUCT, C_QTY, C_UNIT_PRICE, C_SUBTOTAL])
    merged = pd.concat(results, ignore_index=True)
    for c in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
        merged[c] = _to_num(merged[c])
    return merged.sort_values(by=C_DATE, ascending=False).reset_index(drop=True)

def fetch_all_systems_sales_history(model_code, date_from, date_to, system_keys=None):
    keys = system_keys or SYSTEM_KEYS
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_sales_history_for_system, k, model_code, date_from, date_to): k for k in keys}
        for f in as_completed(futs):
            try:
                df = f.result()
                if df is not None and not df.empty:
                    results.append(df)
            except Exception:
                pass
    if not results:
        return pd.DataFrame(columns=[C_SYSTEM, C_DATE, C_SO, C_CUSTOMER, C_BRAND_CAT, C_CATEGORY, C_MODEL, C_PRODUCT, C_QTY, C_UNIT_PRICE, C_SUBTOTAL])
    merged = pd.concat(results, ignore_index=True)
    for c in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
        merged[c] = _to_num(merged[c])
    return merged.sort_values(by=C_DATE, ascending=False).reset_index(drop=True)

def fetch_swag_purchase_history(model_code, date_from, date_to):
    return fetch_purchase_history_for_system("SWAG", model_code, date_from, date_to)

def fetchswagsaleshistory(modelcode, datefrom, dateto):
    return fetch_sales_history_for_system("SWAG", modelcode, datefrom, dateto)

# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _section_header(title, icon="📊", subtitle=""):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-header-bar"></div>
        <div>
            <div class="section-header-title">{icon} {title}</div>
            {f'<div class="section-header-sub">{subtitle}</div>' if subtitle else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

def _divider():
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

def _premium_kpi_card(icon, value, label):
    return f"""
    <div class="kpi-card">
        <div class="kpi-card-bg"></div>
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """

def _render_kpi_grid(cards):
    st.markdown(f"<div class='kpi-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)

def _chart_card_open(title, icon="📈"):
    st.markdown(f"""
    <div class="chart-card">
        <div class="chart-title"><span class="chart-title-accent"></span>{icon} {title}</div>
    """, unsafe_allow_html=True)

def _chart_card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def _alt_base():
    return {
        "config": {
            "background": "transparent",
            "axis": {
                "labelColor": "#9bb0c5",
                "titleColor": "#d8e6f3",
                "gridColor": "rgba(255,255,255,0.08)",
                "domainColor": "rgba(255,255,255,0.15)",
                "tickColor": "rgba(255,255,255,0.15)"
            },
            "view": {"stroke": None},
            "legend": {"labelColor": "#d8e6f3", "titleColor": "#d8e6f3"},
            "title": {"color": "#e8edf2"}
        }
    }

def _alt_bar_chart(df, x_field, y_field, tooltip_fmt=",.0f", color="#3498db", height=320):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame({x_field: [], y_field: []}))
    chart = alt.Chart(df).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        color=color
    ).encode(
        x=alt.X(f"{x_field}:N", sort='-y', title=""),
        y=alt.Y(f"{y_field}:Q", title=""),
        tooltip=[
            alt.Tooltip(f"{x_field}:N", title=x_field),
            alt.Tooltip(f"{y_field}:Q", title=y_field, format=tooltip_fmt),
        ]
    ).properties(height=height)
    return chart.configure(**_alt_base()["config"])

def _alt_line_chart(df, x_field, y_field, color="#2ecc71", height=280):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame({x_field: [], y_field: []}))
    line = alt.Chart(df).mark_line(point=True, strokeWidth=3, color=color).encode(
        x=alt.X(f"{x_field}:T", title=""),
        y=alt.Y(f"{y_field}:Q", title=""),
        tooltip=[
            alt.Tooltip(f"{x_field}:T", title=x_field),
            alt.Tooltip(f"{y_field}:Q", title=y_field, format=",.2f"),
        ]
    ).properties(height=height)
    return line.configure(**_alt_base()["config"])

def _plotly_donut(labels, values, title="", height=320):
    if not _HAS_PLOTLY or not labels or not values:
        st.info("Plotly not available.")
        return
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,.2f}<br>%{percent}<extra></extra>"
    )])
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce6f2"),
        legend=dict(orientation="h", y=-0.15)
    )
    st.plotly_chart(fig, use_container_width=True)

def paginate_df(df, page_key, page_size=PAGE_SIZE):
    total_rows = len(df)
    if total_rows == 0:
        return df
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    st.session_state[page_key] = min(st.session_state[page_key], total_pages - 1)
    st.session_state[page_key] = max(0, st.session_state[page_key])

    current_page = st.session_state[page_key]
    start = current_page * page_size
    end = min(start + page_size, total_rows)
    page_df = df.iloc[start:end]

    pc1, pc2, pc3, pc4, pc5 = st.columns([1, 1, 2, 1, 1])
    with pc1:
        if st.button(f"⏮ {t('First','الأول')}", key=f"{page_key}_first", disabled=(current_page == 0)):
            st.session_state[page_key] = 0
            st.rerun()
    with pc2:
        if st.button(f"◀ {t('Prev','السابق')}", key=f"{page_key}_prev", disabled=(current_page == 0)):
            st.session_state[page_key] -= 1
            st.rerun()
    with pc3:
        st.markdown(
            f"<div class='pagination-bar'><span class='page-info'>{t('Page','صفحة')} {current_page+1} / {total_pages}</span>"
            f"<span style='color:#4a6880;font-size:0.75rem;'>({start+1}–{end} {t('of','من')} {total_rows:,} {t('rows','صف')})</span></div>",
            unsafe_allow_html=True
        )
    with pc4:
        if st.button(f"▶ {t('Next','التالي')}", key=f"{page_key}_next", disabled=(current_page >= total_pages - 1)):
            st.session_state[page_key] += 1
            st.rerun()
    with pc5:
        if st.button(f"⏭ {t('Last','الأخير')}", key=f"{page_key}_last", disabled=(current_page >= total_pages - 1)):
            st.session_state[page_key] = total_pages - 1
            st.rerun()

    return page_df

def render_premium_table(df_show, page_key=None, page_size=PAGE_SIZE):
    if df_show is None or df_show.empty:
        st.markdown("<div class='info-banner'>ℹ️ No data available.</div>", unsafe_allow_html=True)
        return
    if page_key:
        df_show = paginate_df(df_show, page_key, page_size)
    cols = df_show.columns.tolist()
    dir_attr = f'dir="{get_dir()}"' if get_lang() == "AR" else ""
    th_html = "".join(f"<th>{col}</th>" for col in cols)
    tbody_rows = []
    for _, row in df_show.iterrows():
        cells = [f"<td>{val}</td>" for _, val in row.items()]
        tbody_rows.append(f"<tr>{''.join(cells)}</tr>")
    tbody_html = "".join(tbody_rows)
    st.markdown(f"""
    <div class="table-wrapper">
        <table class="premium-table" {dir_attr}>
            <thead><tr>{th_html}</tr></thead>
            <tbody>{tbody_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

def _format_detail_table(df, is_sales=True):
    show = df.copy()
    if C_UNIT_PRICE in show.columns:
        show[C_UNIT_PRICE] = _to_num(show[C_UNIT_PRICE]).map(lambda v: f"{v:,.2f} SAR")
    if C_SUBTOTAL in show.columns:
        show[C_SUBTOTAL] = _to_num(show[C_SUBTOTAL]).map(lambda v: f"{v:,.2f} SAR")
    if C_QTY in show.columns:
        show[C_QTY] = _to_num(show[C_QTY]).map(lambda v: f"{v:,.0f}")
    if C_SYSTEM in show.columns:
        show[C_SYSTEM] = show[C_SYSTEM].map(lambda k: get_system_name(k) if k in SYSTEM_KEYS else k)
    return df_for_display(show)

def _top10_group(df, group_cols, value_col, topn=10):
    if df is None or df.empty:
        return pd.DataFrame(columns=(group_cols if isinstance(group_cols, list) else [group_cols]) + [value_col])
    gcols = group_cols if isinstance(group_cols, list) else [group_cols]
    out = df.groupby(gcols, as_index=False)[value_col].sum().sort_values(value_col, ascending=False).head(topn).reset_index(drop=True)
    out[value_col] = _to_num(out[value_col])
    return out

# ─────────────────────────────────────────────────────────────────────────────
# KPI ROWS
# ─────────────────────────────────────────────────────────────────────────────
def _sales_kpi_row(df):
    total_qty = float(_to_num(df[C_QTY]).sum()) if C_QTY in df.columns else 0
    total_amt = float(_to_num(df[C_SUBTOTAL]).sum()) if C_SUBTOTAL in df.columns else 0
    n_customers = int(df[C_CUSTOMER].nunique()) if C_CUSTOMER in df.columns else 0
    n_products = int(df[C_MODEL].nunique()) if C_MODEL in df.columns else 0
    n_orders = int(df[C_SO].nunique()) if C_SO in df.columns else 0
    avg_price = float(_to_num(df[C_UNIT_PRICE]).replace(0, pd.NA).dropna().mean()) if C_UNIT_PRICE in df.columns and not df.empty else 0

    cards = [
        _premium_kpi_card("📦", f"{total_qty:,.0f}", t("Total Qty Sold", "إجمالي الكمية المباعة")),
        _premium_kpi_card("💰", f"{total_amt:,.2f}", t("Total Sales (SAR)", "إجمالي المبيعات")),
        _premium_kpi_card("👤", str(n_customers), t("Customers", "العملاء")),
        _premium_kpi_card("🏷️", str(n_products), t("Products", "المنتجات")),
        _premium_kpi_card("🧾", str(n_orders), t("Orders", "الطلبات")),
        _premium_kpi_card("📊", f"{avg_price:,.2f}", t("Avg Unit Price", "متوسط سعر الوحدة")),
    ]
    _render_kpi_grid(cards)

def _purchase_kpi_row(df):
    total_qty = float(_to_num(df[C_QTY]).sum()) if C_QTY in df.columns else 0
    total_amt = float(_to_num(df[C_SUBTOTAL]).sum()) if C_SUBTOTAL in df.columns else 0
    n_vendors = int(df[C_VENDOR].nunique()) if C_VENDOR in df.columns else 0
    n_products = int(df[C_MODEL].nunique()) if C_MODEL in df.columns else 0
    n_orders = int(df[C_PO].nunique()) if C_PO in df.columns else 0
    avg_price = float(_to_num(df[C_UNIT_PRICE]).replace(0, pd.NA).dropna().mean()) if C_UNIT_PRICE in df.columns and not df.empty else 0

    cards = [
        _premium_kpi_card("📦", f"{total_qty:,.0f}", t("Total Qty Purchased", "إجمالي الكمية المشتراة")),
        _premium_kpi_card("💰", f"{total_amt:,.2f}", t("Total Purchase (SAR)", "إجمالي المشتريات")),
        _premium_kpi_card("🏭", str(n_vendors), t("Vendors", "الموردون")),
        _premium_kpi_card("🏷️", str(n_products), t("Products", "المنتجات")),
        _premium_kpi_card("🧾", str(n_orders), t("POs", "أوامر الشراء")),
        _premium_kpi_card("📊", f"{avg_price:,.2f}", t("Avg Unit Price", "متوسط سعر الوحدة")),
    ]
    _render_kpi_grid(cards)

# ─────────────────────────────────────────────────────────────────────────────
# SALES VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_sales_analytics():
    _section_header(
        t("Sales Analytics — All Systems", "تحليلات المبيعات — كل الأنظمة"),
        "💰",
        t("Sales orders from all configured Odoo systems", "أوامر البيع من جميع الأنظمة المُعدَّة")
    )
    st.markdown(
        "<div class='info-banner'>📌 " +
        t("Sales orders from all configured systems (state: sale / done). Use filters to narrow down.",
          "أوامر البيع من جميع الأنظمة المُعدَّة (الحالة: sale / done). استخدم الفلاتر للتضييق.") +
        "</div>",
        unsafe_allow_html=True
    )

    default_from = datetime.now().date() - timedelta(days=365)
    default_to = datetime.now().date()

    c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1.3, 1.4])
    with c1:
        model_input = st.text_input(
            f"🔖 {t('Model Code (optional)', 'رمز الموديل (اختياري)')}",
            placeholder=t("e.g. RVT196 — blank = all", "مثال: RVT196 — فارغ = الكل"),
            key="sales_model_input"
        ).strip()
    with c2:
        date_from = st.date_input(f"📅 {t('From', 'من')}", value=default_from, key="sales_date_from")
    with c3:
        date_to = st.date_input(f"📅 {t('To', 'إلى')}", value=default_to, key="sales_date_to")
    with c4:
        sys_names = [get_system_name(k) for k in SYSTEM_KEYS]
        system_sel = st.multiselect(f"🏢 {t('System','النظام')}", options=sys_names, default=sys_names, key="sales_system_sel")
        disp2key = {get_system_name(k): k for k in SYSTEM_KEYS}
        selected_system_keys = [disp2key.get(d, d) for d in system_sel] or SYSTEM_KEYS
    with c5:
        cached_df = st.session_state.get("salesanalyticsdf")
        customer_options = []
        if cached_df is not None and not cached_df.empty and C_CUSTOMER in cached_df.columns:
            customer_options = sorted(cached_df[C_CUSTOMER].dropna().astype(str).unique().tolist())
        customer_sel = st.multiselect(
            f"👤 {t('Customer', 'العميل')}",
            options=customer_options,
            default=[],
            placeholder=t("All Customers", "كل العملاء"),
            key="sales_customer_sel"
        )

    if st.button(f"🔍 {t('Fetch Sales Analytics', 'جلب تحليلات المبيعات')}", type="primary", key="fetch_sales_btn"):
        with st.spinner(t("Fetching sales data...", "جلب بيانات المبيعات...")):
            fetched = fetch_all_systems_sales_history(
                model_code=None,
                date_from=date_from.strftime("%Y-%m-%d"),
                date_to=date_to.strftime("%Y-%m-%d"),
                system_keys=selected_system_keys
            )
        st.session_state.salesanalyticsdf = fetched
        st.session_state.page_sales_detail = 0
        st.rerun()

    full_df = st.session_state.get("salesanalyticsdf")
    if full_df is None:
        st.markdown(f"<div class='info-banner'>👆 {t('Select date range and click Fetch Sales Analytics.','حدد التاريخ واضغط جلب تحليلات المبيعات.')}</div>", unsafe_allow_html=True)
        return
    if full_df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No sales found for this period.','لا توجد مبيعات لهذه الفترة.')}</div>", unsafe_allow_html=True)
        return

    sales_df = full_df.copy()
    for nc in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
        if nc in sales_df.columns:
            sales_df[nc] = _to_num(sales_df[nc])

    if C_SYSTEM in sales_df.columns:
        sales_df = sales_df[sales_df[C_SYSTEM].isin(selected_system_keys)].copy()
    if customer_sel and C_CUSTOMER in sales_df.columns:
        sales_df = sales_df[sales_df[C_CUSTOMER].isin(customer_sel)].copy()

    model_df = None
    if model_input and C_MODEL in sales_df.columns:
        model_df = sales_df[sales_df[C_MODEL].str.upper() == model_input.upper()].copy()

    _divider()
    _section_header(t("Sales KPIs", "مؤشرات المبيعات"), "📊")
    _sales_kpi_row(sales_df)

    _divider()
    _section_header(t("Top 10 Analytics", "أفضل 10 تحليلات"), "🏆")

    prod_qty = _top10_group(sales_df.assign(**{C_MODEL: sales_df[C_MODEL].replace("", "(No Code)").fillna("(No Code)")}), [C_MODEL, C_PRODUCT], C_QTY)
    prod_amt = _top10_group(sales_df.assign(**{C_MODEL: sales_df[C_MODEL].replace("", "(No Code)").fillna("(No Code)")}), [C_MODEL, C_PRODUCT], C_SUBTOTAL)
    cust_amt = _top10_group(sales_df.assign(**{C_CUSTOMER: sales_df[C_CUSTOMER].replace("", "(No Customer)").fillna("(No Customer)")}), C_CUSTOMER, C_SUBTOTAL)
    cat_qty = _top10_group(sales_df.assign(**{C_CATEGORY: sales_df[C_CATEGORY].replace("", "(No Category)").fillna("(No Category)")}), C_CATEGORY, C_QTY)
    brand_qty = _top10_group(sales_df.assign(**{C_BRAND_CAT: sales_df[C_BRAND_CAT].replace("", "(No Brand)").fillna("(No Brand)")}), C_BRAND_CAT, C_QTY)

    col_a, col_b = st.columns(2)
    with col_a:
        _chart_card_open(t("Top 10 Products by Qty", "أعلى 10 منتجات حسب الكمية"), "📦")
        st.altair_chart(_alt_bar_chart(prod_qty, C_MODEL, C_QTY, color="#2ecc71"), use_container_width=True)
        _chart_card_close()
    with col_b:
        _chart_card_open(t("Top 10 Products by Sales Amount", "أعلى 10 منتجات حسب قيمة المبيعات"), "💰")
        st.altair_chart(_alt_bar_chart(prod_amt, C_MODEL, C_SUBTOTAL, tooltip_fmt=",.2f", color="#3498db"), use_container_width=True)
        _chart_card_close()

    col_c, col_d = st.columns(2)
    with col_c:
        _chart_card_open(t("Top 10 Customers by Sales Amount", "أعلى 10 عملاء حسب قيمة المبيعات"), "👤")
        st.altair_chart(_alt_bar_chart(cust_amt, C_CUSTOMER, C_SUBTOTAL, tooltip_fmt=",.2f", color="#9b59b6"), use_container_width=True)
        _chart_card_close()
    with col_d:
        _chart_card_open(t("Top 10 Categories by Qty", "أعلى 10 فئات حسب الكمية"), "🏷️")
        st.altair_chart(_alt_bar_chart(cat_qty, C_CATEGORY, C_QTY, color="#e67e22"), use_container_width=True)
        _chart_card_close()

    _chart_card_open(t("Top 10 Brand Categories by Qty", "أعلى 10 فئات علامة تجارية حسب الكمية"), "🧩")
    st.altair_chart(_alt_bar_chart(brand_qty, C_BRAND_CAT, C_QTY, color="#e74c3c"), use_container_width=True)
    _chart_card_close()

    _divider()
    _section_header(t("Share Analysis", "تحليل الحصص"), "🥧")
    d1, d2, d3 = st.columns(3)
    with d1:
        _plotly_donut(cat_qty[C_CATEGORY].tolist(), cat_qty[C_QTY].tolist(), title=t("Category Share", "حصة الفئة"))
    with d2:
        _plotly_donut(brand_qty[C_BRAND_CAT].tolist(), brand_qty[C_QTY].tolist(), title=t("Brand Category Share", "حصة الفئة التجارية"))
    with d3:
        top_c = cust_amt.head(10).copy()
        if len(cust_amt) > 10:
            others = float(cust_amt.iloc[10:][C_SUBTOTAL].sum())
            top_c.loc[len(top_c)] = ["Others", others]
        _plotly_donut(top_c[C_CUSTOMER].tolist(), top_c[C_SUBTOTAL].tolist(), title=t("Customer Share", "حصة العملاء"))

    _divider()
    _section_header(t("Sales Trend", "اتجاه المبيعات"), "📈")
    trend_df = sales_df.copy()
    trend_df["DateX"] = pd.to_datetime(trend_df[C_DATE], errors="coerce")
    trend_df = trend_df.dropna(subset=["DateX"])
    qty_trend = trend_df.groupby("DateX", as_index=False)[C_QTY].sum().sort_values("DateX")
    amt_trend = trend_df.groupby("DateX", as_index=False)[C_SUBTOTAL].sum().sort_values("DateX")

    lt1, lt2 = st.columns(2)
    with lt1:
        _chart_card_open(t("Qty Sold Over Time", "الكمية المباعة عبر الزمن"), "📦")
        st.altair_chart(_alt_line_chart(qty_trend, "DateX", C_QTY, color="#2ecc71"), use_container_width=True)
        _chart_card_close()
    with lt2:
        _chart_card_open(t("Sales Amount Over Time", "قيمة المبيعات عبر الزمن"), "💰")
        st.altair_chart(_alt_line_chart(amt_trend, "DateX", C_SUBTOTAL, color="#3498db"), use_container_width=True)
        _chart_card_close()

    _divider()
    _section_header(t("Single Model Sales Detail", "تفاصيل مبيعات موديل واحد"), "🔍")

    if not model_input:
        st.markdown(f"<div class='info-banner'>💡 {t('Enter a Model Code above to see single-model sales analytics.','أدخل رمز الموديل أعلاه لعرض تحليلات موديل واحد.')}</div>", unsafe_allow_html=True)
    elif model_df is not None and model_df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No sales records found for this model.','لا توجد سجلات مبيعات لهذا الموديل.')}</div>", unsafe_allow_html=True)
    elif model_df is not None:
        sm_qty = float(_to_num(model_df[C_QTY]).sum())
        sm_amt = float(_to_num(model_df[C_SUBTOTAL]).sum())
        sm_cust = int(model_df[C_CUSTOMER].nunique()) if C_CUSTOMER in model_df.columns else 0
        _render_kpi_grid([
            _premium_kpi_card("📦", f"{sm_qty:,.0f}", t("Total Qty (this model)", "إجمالي الكمية")),
            _premium_kpi_card("💰", f"{sm_amt:,.2f}", t("Total Sales (SAR)", "إجمالي المبيعات")),
            _premium_kpi_card("👤", str(sm_cust), t("Customers", "العملاء")),
        ])

        mtrend = model_df.copy()
        mtrend["DateX"] = pd.to_datetime(mtrend[C_DATE], errors="coerce")
        mtrend = mtrend.dropna(subset=["DateX"])
        mtrend = mtrend.groupby("DateX", as_index=False)[C_QTY].sum().sort_values("DateX")

        _chart_card_open(f"{t('Sales Qty Over Time', 'كمية المبيعات عبر الزمن')} — {model_input}", "📈")
        st.altair_chart(_alt_line_chart(mtrend, "DateX", C_QTY, color="#2ecc71"), use_container_width=True)
        _chart_card_close()

        top_model_customers = _top10_group(model_df.assign(**{C_CUSTOMER: model_df[C_CUSTOMER].replace("", "(No Customer)").fillna("(No Customer)")}), C_CUSTOMER, C_QTY)
        mc1, mc2 = st.columns([1.6, 1])
        with mc1:
            _chart_card_open(t("Top Customers for this Model", "أعلى العملاء لهذا الموديل"), "👤")
            st.altair_chart(_alt_bar_chart(top_model_customers, C_CUSTOMER, C_QTY, color="#9b59b6"), use_container_width=True)
            _chart_card_close()
        with mc2:
            _plotly_donut(top_model_customers[C_CUSTOMER].tolist(), top_model_customers[C_QTY].tolist(), title=t("Customer Share", "حصة العملاء"))

    _divider()
    _section_header(t("Full Sales Detail", "تفاصيل المبيعات الكاملة"), "📋")
    show_df = model_df if (model_input and model_df is not None and not model_df.empty) else sales_df
    render_premium_table(_format_detail_table(show_df, is_sales=True), page_key="page_sales_detail")

    st.markdown("<br>", unsafe_allow_html=True)
    d1, d2, _ = st.columns([1, 1, 2])
    export_df = show_df.copy()
    tag = f"sales_{model_input.upper()}" if model_input else "sales_overall"
    d1.download_button("⬇️ CSV", to_csv(export_df), dl_name(tag, "csv"), "text/csv", use_container_width=True)
    d2.download_button("⬇️ Excel", to_excel_sales(export_df), dl_name(tag, "xlsx"),
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_purchase_analytics():
    _section_header(
        t("Purchase Analytics — All Systems", "تحليلات المشتريات — كل الأنظمة"),
        "🛒",
        t("Purchase orders from all configured Odoo systems", "أوامر الشراء من جميع الأنظمة المُعدَّة")
    )
    st.markdown(
        "<div class='info-banner'>📌 " +
        t("Purchase orders from all configured systems (state: purchase / done). Use filters to narrow down.",
          "أوامر الشراء من جميع الأنظمة المُعدَّة (الحالة: purchase / done). استخدم الفلاتر للتضييق.") +
        "</div>",
        unsafe_allow_html=True
    )

    default_from = datetime.now().date() - timedelta(days=365)
    default_to = datetime.now().date()

    c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1.3, 1.4])
    with c1:
        model_input = st.text_input(
            f"🔖 {t('Model Code (optional)', 'رمز الموديل (اختياري)')}",
            placeholder=t("e.g. RVT196 — blank = all", "مثال: RVT196 — فارغ = الكل"),
            key="purchase_model_input"
        ).strip()
    with c2:
        date_from = st.date_input(f"📅 {t('From', 'من')}", value=default_from, key="purchase_date_from")
    with c3:
        date_to = st.date_input(f"📅 {t('To', 'إلى')}", value=default_to, key="purchase_date_to")
    with c4:
        sys_names = [get_system_name(k) for k in SYSTEM_KEYS]
        system_sel = st.multiselect(f"🏢 {t('System','النظام')}", options=sys_names, default=sys_names, key="purchase_system_sel")
        disp2key = {get_system_name(k): k for k in SYSTEM_KEYS}
        selected_system_keys = [disp2key.get(d, d) for d in system_sel] or SYSTEM_KEYS
    with c5:
        cached_df = st.session_state.get("po_analytics_df")
        vendor_options = []
        if cached_df is not None and not cached_df.empty and C_VENDOR in cached_df.columns:
            vendor_options = sorted(cached_df[C_VENDOR].dropna().astype(str).unique().tolist())
        vendor_sel = st.multiselect(
            f"🏭 {t('Vendor', 'المورد')}",
            options=vendor_options,
            default=[],
            placeholder=t("All Vendors", "كل الموردين"),
            key="purchase_vendor_sel"
        )

    if st.button(f"🔍 {t('Fetch Purchase Analytics', 'جلب تحليلات المشتريات')}", type="primary", key="fetch_purchase_btn"):
        with st.spinner(t("Fetching purchase data...", "جلب بيانات المشتريات...")):
            fetched = fetch_all_systems_purchase_history(
                model_code=None,
                date_from=date_from.strftime("%Y-%m-%d"),
                date_to=date_to.strftime("%Y-%m-%d"),
                system_keys=selected_system_keys
            )
        st.session_state.po_analytics_df = fetched
        st.session_state.page_purchase_detail = 0
        st.rerun()

    full_df = st.session_state.get("po_analytics_df")
    if full_df is None:
        st.markdown(f"<div class='info-banner'>👆 {t('Select date range and click Fetch Purchase Analytics.','حدد التاريخ واضغط جلب تحليلات المشتريات.')}</div>", unsafe_allow_html=True)
        return
    if full_df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No purchases found for this period.','لا توجد مشتريات لهذه الفترة.')}</div>", unsafe_allow_html=True)
        return

    purchase_df = full_df.copy()
    for nc in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
        if nc in purchase_df.columns:
            purchase_df[nc] = _to_num(purchase_df[nc])

    if C_SYSTEM in purchase_df.columns:
        purchase_df = purchase_df[purchase_df[C_SYSTEM].isin(selected_system_keys)].copy()
    if vendor_sel and C_VENDOR in purchase_df.columns:
        purchase_df = purchase_df[purchase_df[C_VENDOR].isin(vendor_sel)].copy()

    model_df = None
    if model_input and C_MODEL in purchase_df.columns:
        model_df = purchase_df[purchase_df[C_MODEL].str.upper() == model_input.upper()].copy()

    _divider()
    _section_header(t("Purchase KPIs", "مؤشرات المشتريات"), "📊")
    _purchase_kpi_row(purchase_df)

    _divider()
    _section_header(t("Top 10 Analytics", "أفضل 10 تحليلات"), "🏆")

    prod_qty = _top10_group(purchase_df.assign(**{C_MODEL: purchase_df[C_MODEL].replace("", "(No Code)").fillna("(No Code)")}), [C_MODEL, C_PRODUCT], C_QTY)
    prod_amt = _top10_group(purchase_df.assign(**{C_MODEL: purchase_df[C_MODEL].replace("", "(No Code)").fillna("(No Code)")}), [C_MODEL, C_PRODUCT], C_SUBTOTAL)
    vendor_amt = _top10_group(purchase_df.assign(**{C_VENDOR: purchase_df[C_VENDOR].replace("", "(No Vendor)").fillna("(No Vendor)")}), C_VENDOR, C_SUBTOTAL)
    cat_qty = _top10_group(purchase_df.assign(**{C_CATEGORY: purchase_df[C_CATEGORY].replace("", "(No Category)").fillna("(No Category)")}), C_CATEGORY, C_QTY)
    brand_qty = _top10_group(purchase_df.assign(**{C_BRAND_CAT: purchase_df[C_BRAND_CAT].replace("", "(No Brand)").fillna("(No Brand)")}), C_BRAND_CAT, C_QTY)

    col_a, col_b = st.columns(2)
    with col_a:
        _chart_card_open(t("Top 10 Products by Qty", "أعلى 10 منتجات حسب الكمية"), "📦")
        st.altair_chart(_alt_bar_chart(prod_qty, C_MODEL, C_QTY, color="#2ecc71"), use_container_width=True)
        _chart_card_close()
    with col_b:
        _chart_card_open(t("Top 10 Products by Purchase Amount", "أعلى 10 منتجات حسب قيمة الشراء"), "💰")
        st.altair_chart(_alt_bar_chart(prod_amt, C_MODEL, C_SUBTOTAL, tooltip_fmt=",.2f", color="#3498db"), use_container_width=True)
        _chart_card_close()

    col_c, col_d = st.columns(2)
    with col_c:
        _chart_card_open(t("Top 10 Vendors by Purchase Amount", "أعلى 10 موردين حسب قيمة الشراء"), "🏭")
        st.altair_chart(_alt_bar_chart(vendor_amt, C_VENDOR, C_SUBTOTAL, tooltip_fmt=",.2f", color="#9b59b6"), use_container_width=True)
        _chart_card_close()
    with col_d:
        _chart_card_open(t("Top 10 Categories by Qty", "أعلى 10 فئات حسب الكمية"), "🏷️")
        st.altair_chart(_alt_bar_chart(cat_qty, C_CATEGORY, C_QTY, color="#e67e22"), use_container_width=True)
        _chart_card_close()

    _chart_card_open(t("Top 10 Brand Categories by Qty", "أعلى 10 فئات علامة تجارية حسب الكمية"), "🧩")
    st.altair_chart(_alt_bar_chart(brand_qty, C_BRAND_CAT, C_QTY, color="#e74c3c"), use_container_width=True)
    _chart_card_close()

    _divider()
    _section_header(t("Share Analysis", "تحليل الحصص"), "🥧")
    d1, d2, d3 = st.columns(3)
    with d1:
        _plotly_donut(cat_qty[C_CATEGORY].tolist(), cat_qty[C_QTY].tolist(), title=t("Category Share", "حصة الفئة"))
    with d2:
        _plotly_donut(brand_qty[C_BRAND_CAT].tolist(), brand_qty[C_QTY].tolist(), title=t("Brand Category Share", "حصة الفئة التجارية"))
    with d3:
        top_v = vendor_amt.head(10).copy()
        if len(vendor_amt) > 10:
            others = float(vendor_amt.iloc[10:][C_SUBTOTAL].sum())
            top_v.loc[len(top_v)] = ["Others", others]
        _plotly_donut(top_v[C_VENDOR].tolist(), top_v[C_SUBTOTAL].tolist(), title=t("Vendor Share", "حصة الموردين"))

    _divider()
    _section_header(t("Purchase Trend", "اتجاه المشتريات"), "📈")
    trend_df = purchase_df.copy()
    trend_df["DateX"] = pd.to_datetime(trend_df[C_DATE], errors="coerce")
    trend_df = trend_df.dropna(subset=["DateX"])
    qty_trend = trend_df.groupby("DateX", as_index=False)[C_QTY].sum().sort_values("DateX")
    amt_trend = trend_df.groupby("DateX", as_index=False)[C_SUBTOTAL].sum().sort_values("DateX")

    lt1, lt2 = st.columns(2)
    with lt1:
        _chart_card_open(t("Qty Purchased Over Time", "الكمية المشتراة عبر الزمن"), "📦")
        st.altair_chart(_alt_line_chart(qty_trend, "DateX", C_QTY, color="#2ecc71"), use_container_width=True)
        _chart_card_close()
    with lt2:
        _chart_card_open(t("Purchase Amount Over Time", "قيمة المشتريات عبر الزمن"), "💰")
        st.altair_chart(_alt_line_chart(amt_trend, "DateX", C_SUBTOTAL, color="#3498db"), use_container_width=True)
        _chart_card_close()

    _divider()
    _section_header(t("Single Model Purchase Detail", "تفاصيل شراء موديل واحد"), "🔍")

    if not model_input:
        st.markdown(f"<div class='info-banner'>💡 {t('Enter a Model Code above to see single-model purchase analytics.','أدخل رمز الموديل أعلاه لعرض تحليلات شراء موديل واحد.')}</div>", unsafe_allow_html=True)
    elif model_df is not None and model_df.empty:
        st.markdown(f"<div class='info-banner'>ℹ️ {t('No purchase records found for this model.','لا توجد سجلات شراء لهذا الموديل.')}</div>", unsafe_allow_html=True)
    elif model_df is not None:
        pm_qty = float(_to_num(model_df[C_QTY]).sum())
        pm_amt = float(_to_num(model_df[C_SUBTOTAL]).sum())
        pm_vendors = int(model_df[C_VENDOR].nunique()) if C_VENDOR in model_df.columns else 0
        _render_kpi_grid([
            _premium_kpi_card("📦", f"{pm_qty:,.0f}", t("Total Qty (this model)", "إجمالي الكمية")),
            _premium_kpi_card("💰", f"{pm_amt:,.2f}", t("Total Purchase (SAR)", "إجمالي المشتريات")),
            _premium_kpi_card("🏭", str(pm_vendors), t("Vendors", "الموردون")),
        ])

        mtrend = model_df.copy()
        mtrend["DateX"] = pd.to_datetime(mtrend[C_DATE], errors="coerce")
        mtrend = mtrend.dropna(subset=["DateX"])
        mtrend = mtrend.groupby("DateX", as_index=False)[C_QTY].sum().sort_values("DateX")

        _chart_card_open(f"{t('Purchase Qty Over Time', 'كمية الشراء عبر الزمن')} — {model_input}", "📈")
        st.altair_chart(_alt_line_chart(mtrend, "DateX", C_QTY, color="#e67e22"), use_container_width=True)
        _chart_card_close()

        top_model_vendors = _top10_group(model_df.assign(**{C_VENDOR: model_df[C_VENDOR].replace("", "(No Vendor)").fillna("(No Vendor)")}), C_VENDOR, C_QTY)
        mv1, mv2 = st.columns([1.6, 1])
        with mv1:
            _chart_card_open(t("Top Vendors for this Model", "أعلى الموردين لهذا الموديل"), "🏭")
            st.altair_chart(_alt_bar_chart(top_model_vendors, C_VENDOR, C_QTY, color="#9b59b6"), use_container_width=True)
            _chart_card_close()
        with mv2:
            _plotly_donut(top_model_vendors[C_VENDOR].tolist(), top_model_vendors[C_QTY].tolist(), title=t("Vendor Share", "حصة الموردين"))

    _divider()
    _section_header(t("Full Purchase Detail", "تفاصيل المشتريات الكاملة"), "📋")
    show_df = model_df if (model_input and model_df is not None and not model_df.empty) else purchase_df
    render_premium_table(_format_detail_table(show_df, is_sales=False), page_key="page_purchase_detail")

    st.markdown("<br>", unsafe_allow_html=True)
    d1, d2, _ = st.columns([1, 1, 2])
    export_df = show_df.copy()
    tag = f"purchase_{model_input.upper()}" if model_input else "purchase_overall"
    d1.download_button("⬇️ CSV", to_csv(export_df), dl_name(tag, "csv"), "text/csv", use_container_width=True)
    d2.download_button("⬇️ Excel", to_excel_purchase(export_df), dl_name(tag, "xlsx"),
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def _render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-logo">
            <div class="sidebar-logo-text">📊 SWAG</div>
            <div class="sidebar-logo-sub">{t('Sales & Purchase Intelligence', 'تحليلات المبيعات والمشتريات')}</div>
        </div>
        """, unsafe_allow_html=True)

        email_short = st.session_state.get("user_email", "") or "user@swag.local"
        st.markdown(f"""
        <div class="sidebar-user-card">
            <div class="sidebar-avatar">👤</div>
            <div>
                <div class="sidebar-user-name">{email_short}</div>
                <div class="sidebar-user-role">{t('Administrator', 'مدير النظام')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        lang_choice = st.radio("🌐 Language", ["EN", "AR"], index=0 if get_lang() == "EN" else 1, horizontal=True)
        if lang_choice != get_lang():
            st.session_state.lang = lang_choice
            st.rerun()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#3498db;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>📊 {t('Analytics Views', 'طرق العرض')}</div>", unsafe_allow_html=True)

        current_view = st.session_state.get("analytics_view", "purchase")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"💰 {t('Sales', 'المبيعات')}", type="primary" if current_view == "sales" else "secondary", use_container_width=True, key="nav_sales_btn"):
                st.session_state.analytics_view = "sales"
                st.rerun()
        with col2:
            if st.button(f"🛒 {t('Purchase', 'المشتريات')}", type="primary" if current_view == "purchase" else "secondary", use_container_width=True, key="nav_purchase_btn"):
                st.session_state.analytics_view = "purchase"
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def show_hero(current_view):
    if current_view == "sales":
        title_main = t("Sales", "المبيعات")
        title_accent = t("Analytics", "التحليلات")
        eyebrow = t("SALES INTELLIGENCE", "تحليلات المبيعات")
        subtitle = t("Premium real-time analytics across configured Odoo systems. Track customers, products, categories, and growth trends.",
                     "تحليلات فورية مميزة عبر أنظمة أودو المُعدَّة. تتبع العملاء والمنتجات والفئات واتجاهات النمو.")
    else:
        title_main = t("Purchase", "المشتريات")
        title_accent = t("Analytics", "التحليلات")
        eyebrow = t("PURCHASE INTELLIGENCE", "تحليلات المشتريات")
        subtitle = t("Premium procurement analytics across configured Odoo systems. Track vendors, products, categories, and buying trends.",
                     "تحليلات مشتريات مميزة عبر أنظمة أودو المُعدَّة. تتبع الموردين والمنتجات والفئات واتجاهات الشراء.")

    st.markdown(f"""
    <div class='dashboard-hero'>
        <div class='hero-eyebrow'>
            <span class='hero-eyebrow-dot'></span>
            {eyebrow}
        </div>
        <div class='hero-title'>
            {title_main} <span class='hero-title-accent'>{title_accent}</span>
        </div>
        <div class='hero-subtitle'>{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def main():
    restore_session()
    _render_sidebar()

    current_view = st.session_state.get("analytics_view", "purchase")
    show_hero(current_view)

    if current_view == "sales":
        show_sales_analytics()
    else:
        show_purchase_analytics()

    st.markdown(
        "<div class='footer'>© 2026 <span>SWAG Fashion</span> · Powered by <span>Odoo ERP</span> · Sales & Purchase Dashboard</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
