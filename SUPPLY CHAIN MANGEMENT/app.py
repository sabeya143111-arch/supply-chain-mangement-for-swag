"""
Multi‑Company Operations Dashboard
Inventory, Sales & Purchase for SWAG, LAROUCHE, DIFFC, FASHIONLIMITS
"""

import io
import re
import hashlib
import time
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Multi‑Company Ops Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
*,html,body,[class*="css"]{font-family:'IBM Plex Sans Arabic',sans-serif;box-sizing:border-box;}
.stApp{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);min-height:100vh;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1a2e 0%,#16213e 100%)!important;border-right:1px solid #ffffff15;}
section[data-testid="stSidebar"] *,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] div{color:#e8e8ff!important;}
section[data-testid="stSidebar"] input{color:#1a1a2e!important;}
@keyframes fadeInUp{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeInDown{from{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)}}
@keyframes bounceIn{0%{transform:scale(0.2) rotate(-10deg);opacity:0}60%{transform:scale(1.2) rotate(5deg);opacity:1}80%{transform:scale(0.9)}100%{transform:scale(1);opacity:1}}
@keyframes shimmer{0%{background-position:-400% center}100%{background-position:400% center}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 #7c3aed44}50%{box-shadow:0 0 20px 8px #7c3aed22}}
@keyframes glow{0%,100%{text-shadow:0 0 10px #667eea88}50%{text-shadow:0 0 30px #f093fbcc,0 0 60px #667eea88}}
@keyframes slideInLeft{from{opacity:0;transform:translateX(-40px)}to{opacity:1;transform:translateX(0)}}
@keyframes slideInRight{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes btnShine{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes borderGlow{0%,100%{border-color:#667eea;box-shadow:0 0 5px #667eea44}50%{border-color:#f093fb;box-shadow:0 0 15px #f093fb66}}
@keyframes countUp{from{opacity:0;transform:scale(0.5)}to{opacity:1;transform:scale(1)}}
.login-orb{width:120px;height:120px;border-radius:50%;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);display:flex;align-items:center;justify-content:center;font-size:3rem;margin:0 auto 20px;animation:float 3s ease-in-out infinite,bounceIn 1s ease forwards;box-shadow:0 8px 40px #667eea66,0 0 60px #f093fb33;}
.login-title{font-size:2.4rem;font-weight:700;background:linear-gradient(90deg,#667eea,#f093fb,#667eea);background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s linear infinite,fadeInDown 0.8s ease forwards;text-align:center;margin-bottom:6px;}
.login-subtitle{color:#c4b5fd!important;font-size:0.95rem;text-align:center;animation:fadeInUp 1s ease forwards;margin-bottom:28px;}
.login-card{background:linear-gradient(145deg,#1e1e3f,#2d2b55);border:1px solid #ffffff18;border-radius:20px;padding:32px 36px;width:100%;animation:fadeInUp 0.9s ease forwards,pulse 3s infinite;}
.welcome-banner{background:linear-gradient(135deg,#667eea22,#f093fb22);border:1px solid #667eea44;border-radius:12px;padding:14px 20px;text-align:center;margin-bottom:20px;font-size:0.95rem;color:#c4b5fd!important;animation:fadeInDown 0.7s ease forwards,borderGlow 3s infinite;}
.stTextInput input,.stNumberInput input,.stTextArea textarea{background:#1e1e3f!important;border:1px solid #667eea66!important;border-radius:10px!important;color:#e8e8ff!important;caret-color:#c4b5fd!important;transition:all 0.3s ease!important;}
.stTextInput input::placeholder,.stNumberInput input::placeholder,.stTextArea textarea::placeholder{color:#7070aa!important;}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:#667eea!important;box-shadow:0 0 0 3px #667eea33!important;background:#252550!important;}
.stTextInput label,.stNumberInput label,.stTextArea label{color:#c4b5fd!important;font-weight:600!important;}
.stFormSubmitButton button,.stButton button[kind="primary"]{background:linear-gradient(90deg,#667eea,#764ba2,#f093fb,#667eea)!important;background-size:300% auto!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important;font-size:1rem!important;padding:12px!important;animation:btnShine 3s linear infinite!important;transition:transform 0.2s,box-shadow 0.2s!important;box-shadow:0 4px 20px #667eea55!important;}
.stFormSubmitButton button:hover,.stButton button[kind="primary"]:hover{transform:translateY(-2px) scale(1.02)!important;box-shadow:0 8px 30px #764ba299!important;}
.stButton button[kind="secondary"]{background:#1e1e3f!important;border:1px solid #667eea66!important;color:#c4b5fd!important;border-radius:10px!important;}
.stButton button[kind="secondary"]:hover{background:linear-gradient(135deg,#667eea,#764ba2)!important;color:white!important;}
.stButton button{color:#c4b5fd!important;}
.stDownloadButton button{background:linear-gradient(135deg,#1e1e3f,#2d2b55)!important;border:1px solid #667eea66!important;border-radius:10px!important;color:#c4b5fd!important;font-size:0.78rem!important;font-weight:600!important;padding:6px 14px!important;transition:all 0.25s ease!important;box-shadow:0 2px 8px #00000044!important;}
.stDownloadButton button:hover{background:linear-gradient(135deg,#667eea,#764ba2)!important;color:white!important;border-color:transparent!important;transform:translateY(-2px) scale(1.04)!important;box-shadow:0 6px 20px #667eea55!important;}
.dash-header{text-align:center;padding:16px 0 24px;animation:fadeInDown 0.6s ease forwards;}
.dash-title{font-size:2.4rem;font-weight:700;background:linear-gradient(90deg,#667eea,#f093fb,#43e97b,#667eea);background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 4s linear infinite,glow 3s ease-in-out infinite;}
.dash-subtitle{color:#a0aec0;font-size:0.95rem;margin-top:-4px;}
[data-testid="stMetric"]{background:linear-gradient(135deg,#1e1e3f,#2d2b55)!important;border:1px solid #ffffff15!important;border-radius:16px!important;padding:16px 20px!important;animation:countUp 0.6s ease forwards;transition:transform 0.2s,box-shadow 0.2s;}
[data-testid="stMetric"]:hover{transform:translateY(-4px);box-shadow:0 8px 30px #667eea44;}
[data-testid="stMetricLabel"]{color:#a0aec0!important;font-size:0.82rem!important;}
[data-testid="stMetricValue"]{font-size:1.7rem!important;font-weight:700!important;background:linear-gradient(90deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.stTabs [data-baseweb="tab-list"]{background:linear-gradient(90deg,#1e1e3f,#2d2b55);border-radius:12px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{color:#a0aec0!important;border-radius:10px!important;font-size:0.83rem!important;font-weight:600!important;padding:8px 16px!important;transition:all 0.2s ease!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#667eea,#764ba2)!important;color:white!important;box-shadow:0 4px 12px #667eea55!important;}
.info-banner{background:linear-gradient(135deg,#1e3a5f,#1e3a5f99);border-left:4px solid #3b82f6;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#93c5fd!important;animation:slideInLeft 0.4s ease;}
.warn-banner{background:linear-gradient(135deg,#3b2a0a,#3b2a0a99);border-left:4px solid #f59e0b;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#fcd34d!important;}
.alert-banner{background:linear-gradient(135deg,#3b0a1e,#3b0a1e99);border-left:4px solid #f43f5e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#fca5a5!important;animation:pulse 2s infinite;}
.ok-banner{background:linear-gradient(135deg,#0a3b1e,#0a3b1e99);border-left:4px solid #22c55e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#86efac!important;}
.snap-card{background:linear-gradient(145deg,#1e1e3f,#2d2b55);border:1px solid #ffffff18;border-radius:14px;padding:16px 20px;font-size:0.87rem;color:#e8e8ff!important;line-height:2;animation:slideInRight 0.5s ease;box-shadow:0 4px 20px #00000055;}
.snap-card b{color:#c4b5fd!important;}
.sys-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
.sys-row span{color:#e8e8ff!important;}
.badge-ok{background:linear-gradient(90deg,#065f46,#047857);color:#d1fae5!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}
.badge-off{background:linear-gradient(90deg,#991b1b,#b91c1c);color:#fee2e2!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}
.badge-err{background:linear-gradient(90deg,#78350f,#92400e);color:#fef3c7!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}
.stRadio label,.stRadio div[role="radiogroup"] label span,[data-testid="stToggle"] label,.stCheckbox label{color:#e8e8ff!important;}
div[data-testid="stRadio"] p{color:#e8e8ff!important;}
h1,h2,h3,h4,h5,h6{color:#e8e8ff!important;}
.stMarkdown p,.stMarkdown li{color:#c4b5fd!important;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#8888bb!important;}
.stAlert p{color:#1a1a2e!important;font-weight:600;}
[data-testid="stExpander"]{background:linear-gradient(135deg,#1e1e3f,#2d2b55)!important;border:1px solid #ffffff18!important;border-radius:12px!important;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:#c4b5fd!important;}
[data-testid="stFileUploader"]{background:linear-gradient(135deg,#1e1e3f,#2d2b55)!important;border:2px dashed #667eea66!important;border-radius:14px!important;}
[data-testid="stFileUploader"] p,[data-testid="stFileUploader"] span{color:#c4b5fd!important;}
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,#667eea66,transparent)!important;margin:16px 0!important;}
[data-testid="stProgressBar"]>div{background:linear-gradient(90deg,#667eea,#f093fb)!important;border-radius:10px!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#1a1a2e;}
::-webkit-scrollbar-thumb{background:linear-gradient(#667eea,#764ba2);border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:#f093fb;}
.stNumberInput button{color:#c4b5fd!important;background:#2d2b55!important;}
.mono{font-family:'IBM Plex Mono',monospace;font-size:0.82rem;color:#c4b5fd;}
footer{visibility:hidden;}
[data-baseweb="tag"]{background:#667eea33!important;color:#c4b5fd!important;}
[data-baseweb="select"] div{background:#1e1e3f!important;color:#e8e8ff!important;border-color:#667eea55!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE
# ─────────────────────────────────────────────────────────────────────────────
def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    return ar if get_lang() == "AR" else en

def get_system_name(key):
    cfg = st.secrets.get(key, {})
    return cfg.get("name_ar", cfg.get("name", key)) if get_lang() == "AR" else cfg.get("name", key)

def translate_system_names(df):
    if df is None or df.empty:
        return df
    sys_col = t("System", "النظام")
    if sys_col not in df.columns:
        return df
    key_to_name = {k: get_system_name(k) for k in SYSTEM_KEYS}
    out = df.copy()
    out[sys_col] = out[sys_col].map(lambda v: key_to_name.get(v, v))
    return out

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS (cleaned)
# ─────────────────────────────────────────────────────────────────────────────
_DEF = {
    "authenticated": False,
    "user_email": "",
    "lang": "EN",
    # Inventory
    "inventory_df": None,
    "inventory_branch_df": None,
    "inventory_last_params": {},
    # Sales
    "sales_df": None,
    "sales_last_params": {},
    # Purchase
    "purchase_df": None,
    "purchase_last_params": {},
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# SESSION LOGIN RESTORE (unchanged)
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
# XML-RPC HELPERS (unchanged)
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

def _get_uid_for_key(key):
    cfg = st.secrets.get(key)
    if not cfg:
        return None, None
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    return (cfg, uid) if uid else (None, None)

# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN BUILDER (for inventory)
# ─────────────────────────────────────────────────────────────────────────────
def _domain(codes, exact):
    if not codes:
        return []  # all products
    if exact:
        return [["default_code", "in", codes]]
    if len(codes) == 1:
        return [["default_code", "=like", f"{codes[0]}%"]]
    parts = [["default_code", "=like", f"{c}%"] for c in codes]
    return ["|"] * (len(parts) - 1) + parts

# ─────────────────────────────────────────────────────────────────────────────
# EXCEL HELPERS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def _style_worksheet(ws, df_clean, lang="EN"):
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.formatting.rule import DataBarRule, ColorScaleRule, CellIsRule
    from openpyxl.chart import BarChart, Reference
    if lang == "AR":
        ws.sheet_view.rightToLeft = True
    hdr_fill = PatternFill("solid", fgColor="4B0082")
    hdr_font = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
    hdr_align = Alignment(horizontal="center", vertical="center")
    thin = Side(border_style="thin", color="D0D0D0")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    alt_fill = PatternFill("solid", fgColor="F3EFFF")
    zero_fill = PatternFill("solid", fgColor="FFE0E0")
    zero_font = Font(color="CC0000", bold=True, name="Calibri")
    normal_font = Font(name="Calibri", size=10)
    num_align = Alignment(horizontal="right", vertical="center")
    center_align = Alignment(horizontal="center", vertical="center")
    total_fill = PatternFill("solid", fgColor="2E2E2E")
    total_font = Font(bold=True, name="Calibri", color="FFFFFF")
    max_row = ws.max_row
    max_col = ws.max_column
    ws.row_dimensions[1].height = 28
    for col_num in range(1, max_col + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = hdr_align
        cell.border = border
    col_names = [ws.cell(row=1, column=c).value for c in range(1, max_col + 1)]
    on_hand_col = sale_price_col = loc_col = branch_col = model_col = None
    for i, name in enumerate(col_names, 1):
        if name in ("On Hand", "متوفر"):
            on_hand_col = i
        if name in ("Sale Price", "سعر البيع"):
            sale_price_col = i
        if name in ("Location", "الموقع"):
            loc_col = i
        if name in ("Branch", "الفرع"):
            branch_col = i
        if name in ("Model Code", "رمز الموديل"):
            model_col = i
    for row in ws.iter_rows(min_row=2, max_row=max_row):
        is_zero = False
        if on_hand_col:
            val = ws.cell(row=row[0].row, column=on_hand_col).value
            is_zero = (val is None or
                       str(val).strip() in ['0', 'Not Available', 'غير متوفر', '—', '-', ''] or
                       val == 0)
        for cell in row:
            cell.border = border
            cell.font = zero_font if is_zero else normal_font
            if is_zero:
                cell.fill = zero_fill
            elif cell.row % 2 == 0:
                cell.fill = alt_fill
            cell.alignment = num_align if isinstance(cell.value, (int, float)) else center_align
        ws.row_dimensions[row[0].row].height = 18
    for col_num in range(1, max_col + 1):
        col_letter = get_column_letter(col_num)
        max_len = 0
        for r in ws.iter_rows(min_col=col_num, max_col=col_num):
            for cell in r:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(max_col)}{max_row}"
    if on_hand_col and max_row > 1:
        col_letter = get_column_letter(on_hand_col)
        ws.conditional_formatting.add(
            f"{col_letter}2:{col_letter}{max_row}",
            DataBarRule(start_type="min", end_type="max", color="4472C4"))
    if sale_price_col and max_row > 1:
        col_letter = get_column_letter(sale_price_col)
        ws.conditional_formatting.add(
            f"{col_letter}2:{col_letter}{max_row}",
            ColorScaleRule(start_type="min", start_color="63BE7B",
                           mid_type="percentile", mid_value=50, mid_color="FFEB84",
                           end_type="max", end_color="F8696B"))
    if on_hand_col and max_row > 1:
        col_letter = get_column_letter(on_hand_col)
        low_stock_fill = PatternFill("solid", fgColor="FFF2CC")
        low_stock_font = Font(color="7F6000", bold=True, name="Calibri")
        ws.conditional_formatting.add(
            f"{col_letter}2:{col_letter}{max_row}",
            CellIsRule(operator="lessThanOrEqual", formula=["3"],
                       fill=low_stock_fill, font=low_stock_font))
    total_row = max_row + 1
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=1).font = total_font
    ws.cell(row=total_row, column=1).fill = total_fill
    ws.cell(row=total_row, column=1).alignment = Alignment(horizontal="center")
    if on_hand_col:
        col = get_column_letter(on_hand_col)
        ws.cell(row=total_row, column=on_hand_col,
                value=f"=SUM({col}2:{col}{max_row})")
        ws.cell(row=total_row, column=on_hand_col).font = total_font
        ws.cell(row=total_row, column=on_hand_col).fill = total_fill
        ws.cell(row=total_row, column=on_hand_col).alignment = Alignment(horizontal="center")
    ws.row_dimensions[total_row].height = 20
    ws.sheet_properties.tabColor = "667EEA"
    footer_row = total_row + 2
    ws.cell(row=footer_row, column=1,
            value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  SWAG Dashboard")
    ws.cell(row=footer_row, column=1).font = Font(italic=True, color="888888", size=9, name="Calibri")
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.print_title_rows = "1:1"
    ws.print_area = f"A1:{get_column_letter(max_col)}{max_row}"
    ws.oddHeader.center.text = "SWAG Product Report"
    ws.oddHeader.center.font = "Calibri,Bold"
    ws.oddFooter.center.text = "Page &P of &N  |  Generated: &D"
    ws.sheet_view.zoomScale = 85
    if loc_col:
        ws.column_dimensions[get_column_letter(loc_col)].width = 35
        for row_num in range(2, max_row + 1):
            ws.cell(row=row_num, column=loc_col).alignment = Alignment(
                wrap_text=True, vertical="center", horizontal="left")
            ws.row_dimensions[row_num].height = 28
    if on_hand_col and model_col and max_row > 2:
        chart = BarChart()
        chart.type = "bar"
        chart.shape = 4
        chart.title = "Stock by Branch"
        chart.style = 10
        chart.y_axis.title = "On Hand"
        chart.x_axis.title = "Branch"
        chart.width = 20
        chart.height = 12
        data_ref = Reference(ws, min_col=on_hand_col, min_row=1, max_row=max_row)
        cats_ref = Reference(ws, min_col=model_col, min_row=2, max_row=max_row)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats_ref)
        ws.add_chart(chart, f"A{max_row + 5}")

def to_csv(df):
    return df.drop(columns=["_status"], errors="ignore").to_csv(index=False).encode("utf-8-sig")

def to_excel(df):
    lang = st.session_state.get('lang', 'EN')
    buf = io.BytesIO()
    clean = df.drop(columns=['_status'], errors='ignore').copy()
    on_hand_col = 'On Hand' if 'On Hand' in clean.columns else (
        'متوفر' if 'متوفر' in clean.columns else None)
    if on_hand_col:
        na_text = 'غير متوفر' if lang == 'AR' else 'Not Available'
        clean[on_hand_col] = clean[on_hand_col].apply(
            lambda x: na_text if (pd.isna(x) or str(x).strip() in ['0', '']) or x == 0 else x)
    desired_order = [
        t("Model Code", "رمز الموديل"), t("System", "النظام"),
        t("Branch", "الفرع"), t("Location", "الموقع"),
        t("Sale Price", "سعر البيع"), t("On Hand", "متوفر"),
    ]
    ordered_cols = [c for c in desired_order if c in clean.columns]
    remaining = [c for c in clean.columns if c not in ordered_cols]
    clean = clean[ordered_cols + remaining]
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        clean.to_excel(w, index=False, sheet_name='Data')
        _style_worksheet(w.sheets['Data'], clean, lang=lang)
    return buf.getvalue()

def to_excel_bulk(df):
    lang = st.session_state.get("lang", "EN")
    buf = io.BytesIO()
    sys_col = t("System", "النظام")
    _desired = [
        t("Model Code", "رمز الموديل"), t("System", "النظام"),
        t("Branch", "الفرع"), t("Location", "الموقع"),
        t("Sale Price", "سعر البيع"), t("On Hand", "متوفر"),
    ]
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        def _ws(data, name):
            c = data.drop(columns=["_status"], errors="ignore").copy()
            on_hand_col = t("On Hand", "متوفر")
            if on_hand_col in c.columns:
                na_text = 'غير متوفر' if lang == 'AR' else 'Not Available'
                c[on_hand_col] = c[on_hand_col].apply(
                    lambda x: na_text if (pd.isna(x) or str(x).strip() in ['0', '']) or x == 0 else x)
            _ordered = [col for col in _desired if col in c.columns]
            _remaining = [col for col in c.columns if col not in _ordered]
            c = c[_ordered + _remaining]
            c.to_excel(w, index=False, sheet_name=name[:31])
            _style_worksheet(w.sheets[name[:31]], c, lang=lang)
        _ws(df, t("All Systems", "كل الأنظمة"))
        if sys_col in df.columns:
            for key in SYSTEM_KEYS:
                nm = get_system_name(key)
                sub = df[df[sys_col] == nm]
                if not sub.empty:
                    _ws(sub, nm)
    return buf.getvalue()

def to_excel_branch_matrix(df_branch_filtered, lang="EN"):
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    if df_branch_filtered is None or df_branch_filtered.empty:
        return b""

    col_model = t("Model Code", "رمز الموديل")
    col_branch = t("Branch", "الفرع")
    col_location = t("Location", "الموقع")
    col_price = t("Sale Price", "سعر البيع")
    col_onhand = t("On Hand", "متوفر")
    col_product = t("Product", "المنتج")
    label_pur = t("Purchase Qty", "كمية المشتريات")

    df = df_branch_filtered.copy()
    pivot_col = col_location if col_location in df.columns else (
        col_branch if col_branch in df.columns else None)
    if pivot_col is None:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="BranchMatrix")
        return buf.getvalue()

    if col_onhand in df.columns:
        df[col_onhand] = pd.to_numeric(df[col_onhand], errors="coerce").fillna(0)
    else:
        df[col_onhand] = 0

    if col_model not in df.columns:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="BranchMatrix")
        return buf.getvalue()

    pivot = (df.pivot_table(index=col_model, columns=pivot_col,
                            values=col_onhand, aggfunc="sum", fill_value=0)
             .reset_index())
    pivot.columns.name = None

    if col_price in df.columns:
        price_map = df.groupby(col_model)[col_price].first().reset_index()
        pivot = pivot.merge(price_map, on=col_model, how="left")
        pivot[col_price] = pd.to_numeric(pivot[col_price], errors="coerce").fillna(0).round(2)
    else:
        pivot[col_price] = 0.0

    product_map = {}
    total_df_ss = st.session_state.get("inventory_df")
    if total_df_ss is not None and not total_df_ss.empty:
        if col_model in total_df_ss.columns and col_product in total_df_ss.columns:
            product_map = total_df_ss.groupby(col_model)[col_product].first().dropna().to_dict()
    pivot[col_product] = pivot[col_model].map(product_map).fillna("")

    purchase_qty_map = {}
    if total_df_ss is not None and not total_df_ss.empty:
        for possible in ["Purchase Qty", "كمية المشتريات", label_pur]:
            if possible in total_df_ss.columns and col_model in total_df_ss.columns:
                tmp = total_df_ss.groupby(col_model)[possible].sum().to_dict()
                if tmp:
                    purchase_qty_map = tmp
                    break

    if not purchase_qty_map:
        unique_models = pivot[col_model].dropna().unique().tolist()
        if unique_models:
            try:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=365)
                pur_df = get_purchase_summary_by_model(
                    tuple(unique_models),
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"))
                if not pur_df.empty:
                    purchase_qty_map = dict(zip(pur_df["Model Code"], pur_df["Purchase Qty"]))
            except Exception:
                pass

    pivot[label_pur] = pivot[col_model].map(purchase_qty_map).fillna(0).astype(int)

    fixed_left = [col_model, col_product, col_price, label_pur]
    loc_columns = sorted(c for c in pivot.columns if c not in fixed_left)
    ordered = [c for c in fixed_left if c in pivot.columns] + loc_columns
    pivot = pivot[ordered]

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pivot.to_excel(writer, index=False, sheet_name="BranchMatrix")
        ws = writer.sheets["BranchMatrix"]
        if lang == "AR":
            ws.sheet_view.rightToLeft = True
        hdr_fill = PatternFill("solid", fgColor="4B0082")
        hdr_font = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
        hdr_align = Alignment(horizontal="center", vertical="center")
        thin = Side(border_style="thin", color="D0D0D0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        alt_fill = PatternFill("solid", fgColor="F3EFFF")
        norm_font = Font(name="Calibri", size=10)
        num_align = Alignment(horizontal="right", vertical="center")
        ctr_align = Alignment(horizontal="center", vertical="center")
        tot_fill = PatternFill("solid", fgColor="2E2E2E")
        tot_font = Font(bold=True, color="FFFFFF", name="Calibri")
        zero_fill = PatternFill("solid", fgColor="FFF2CC")
        zero_font = Font(color="7F6000", bold=True, name="Calibri")
        max_row = ws.max_row
        max_col = ws.max_column
        col_names_ws = [ws.cell(row=1, column=c).value for c in range(1, max_col + 1)]
        ws.row_dimensions[1].height = 28
        for c in range(1, max_col + 1):
            cell = ws.cell(row=1, column=c)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = hdr_align
            cell.border = border
        for row_idx in range(2, max_row + 1):
            for col_idx in range(1, max_col + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                col_name = col_names_ws[col_idx - 1]
                is_loc = col_name not in (col_model, col_product, col_price, label_pur, None)
                cell.border = border
                cell.font = norm_font
                if row_idx % 2 == 0:
                    cell.fill = alt_fill
                if is_loc and isinstance(cell.value, (int, float)) and cell.value == 0:
                    cell.fill = zero_fill
                    cell.font = zero_font
                cell.alignment = (num_align if isinstance(cell.value, (int, float)) else ctr_align)
            ws.row_dimensions[row_idx].height = 18
        for c in range(1, max_col + 1):
            col_letter = get_column_letter(c)
            max_len = max((len(str(ws.cell(row=r, column=c).value or ""))
                           for r in range(1, max_row + 1)), default=8)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(max_col)}{max_row}"
        total_row = max_row + 1
        tc = ws.cell(row=total_row, column=1, value=t("TOTAL", "الإجمالي"))
        tc.font = tot_font
        tc.fill = tot_fill
        tc.alignment = ctr_align
        ws.row_dimensions[total_row].height = 22
        for c_idx, c_name in enumerate(col_names_ws, start=1):
            if c_name in (None, col_model, col_product, col_price):
                continue
            cl = get_column_letter(c_idx)
            tot = ws.cell(row=total_row, column=c_idx)
            tot.value = f"=SUM({cl}2:{cl}{max_row})"
            tot.font = tot_font
            tot.fill = tot_fill
            tot.alignment = num_align
        footer_row = total_row + 2
        ws.cell(row=footer_row, column=1,
                value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  SWAG Dashboard"
                ).font = Font(italic=True, color="888888", size=9, name="Calibri")
        ws.sheet_properties.tabColor = "667EEA"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.print_title_rows = "1:1"
        ws.print_area = f"A1:{get_column_letter(max_col)}{max_row}"
        ws.sheet_view.zoomScale = 85
    return buf.getvalue()

def dl_name(tag, ext):
    return f"swag_{tag}_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# QTY DISPLAY HELPER
# ─────────────────────────────────────────────────────────────────────────────
def get_qty_display(qty, lang="EN"):
    try:
        v = float(qty)
        if pd.isna(v) or v == 0:
            return "❌ لا يوجد" if lang == "AR" else "❌ Not Available"
        return int(v)
    except Exception:
        return "❌ لا يوجد" if lang == "AR" else "❌ Not Available"

# ─────────────────────────────────────────────────────────────────────────────
# HTML TABLE CSS & RENDERERS
# ─────────────────────────────────────────────────────────────────────────────
_TABLE_CSS = """<style>
.swag-wrap{width:100%;overflow-x:auto;border-radius:16px;box-shadow:0 4px 32px rgba(0,0,0,.5);margin-bottom:4px;}
.swag-tbl{width:100%;border-collapse:collapse;font-family:'IBM Plex Sans Arabic',sans-serif;font-size:.84rem;}
.swag-tbl thead tr{background:linear-gradient(90deg,#667eea,#764ba2,#9b59b6);}
.swag-tbl thead th{color:#fff;font-weight:700;padding:14px 16px;text-align:center;white-space:nowrap;letter-spacing:.4px;border:none;position:sticky;top:0;z-index:2;}
.swag-tbl thead th:first-child{border-radius:16px 0 0 0;}
.swag-tbl thead th:last-child{border-radius:0 16px 0 0;}
.swag-tbl tbody tr:nth-child(odd){background:#1a1a3e;}
.swag-tbl tbody tr:nth-child(odd) td{color:#e8e8ff;}
.swag-tbl tbody tr:nth-child(even){background:#22224a;}
.swag-tbl tbody tr:nth-child(even) td{color:#c4b5fd;}
.swag-tbl tbody td{padding:10px 16px;text-align:center;border-bottom:1px solid #ffffff08;transition:background .15s,color .15s;}
.swag-tbl tbody td.cf{font-weight:700;color:#a78bfa!important;border-right:2px solid #667eea33;}
.swag-tbl tbody tr:hover td{background:#3b2f7a!important;color:#fff!important;}
.swag-tbl tbody tr:hover td.cf{color:#f093fb!important;}
.swag-tbl tbody tr.rl td{background:#3b0a1e!important;color:#fca5a5!important;font-weight:600;}
.swag-tbl tbody tr.rl:hover td{background:#5b1030!important;color:#ffd5d5!important;}
.swag-tbl tbody tr.hi td{background:#1a3b1a!important;color:#86efac!important;font-weight:600;}
.swag-tbl tbody tr.na-row td{background:#2a1a1a!important;opacity:.82;}
.swag-tbl tbody td.na-cell{color:#f97316!important;font-weight:700;letter-spacing:.3px;}
</style>"""

def _render_html_table(df_display):
    if df_display is None or df_display.empty:
        st.info(t("No data.", "لا بيانات."))
        return
    cols = df_display.columns.tolist()
    th_ = "".join(f"<th>{c}</th>" for c in cols)

    def _row(idx_row):
        _, row = idx_row
        cells = "".join(
            f'<td class="cf">{v}</td>' if ci == 0 else f"<td>{v}</td>"
            for ci, v in enumerate(row))
        return f"<tr>{cells}</tr>"

    tbody = "".join(_row(x) for x in df_display.iterrows())
    st.markdown(
        f'{_TABLE_CSS}<div class="swag-wrap">'
        f'<table class="swag-tbl"><thead><tr>{th_}</tr></thead>'
        f'<tbody>{tbody}</tbody></table></div>',
        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COLUMN MAPS
# ─────────────────────────────────────────────────────────────────────────────
_COL_MAP_EN = {
    "System": "System", "Model Code": "Model Code", "Product": "Product",
    "Sale Price": "Sale Price", "On Hand": "On Hand", "Branch": "Branch",
    "Location": "Location", "Reference": "Reference", "Type": "Type",
    "State": "State", "From": "From", "To": "To", "Qty": "Qty",
    "Scheduled": "Scheduled", "Sold(30d)": "Sold(30d)", "Daily Vel": "Daily Vel",
    "Days Left": "Days Left", "Suggest": "Suggest", "Priority": "Priority",
    "Purchase Qty": "Purchase Qty",
}
_COL_MAP_AR = {
    "System": "النظام", "Model Code": "رمز الموديل", "Product": "المنتج",
    "Sale Price": "سعر البيع", "On Hand": "متوفر", "Branch": "الفرع",
    "Location": "الموقع", "Reference": "المرجع", "Type": "النوع",
    "State": "الحالة", "From": "من", "To": "إلى", "Qty": "الكمية",
    "Scheduled": "المجدول", "Sold(30d)": "مباع(30ي)", "Daily Vel": "معدل/يوم",
    "Days Left": "أيام متبقية", "Suggest": "المقترح", "Priority": "الأولوية",
    "Purchase Qty": "كمية المشتريات",
}

def localize_columns(df):
    if df is None or df.empty:
        return df
    col_map = _COL_MAP_AR if get_lang() == "AR" else _COL_MAP_EN
    return df.rename(columns=col_map)

def prepare_df(df):
    df = localize_columns(df)
    df = translate_system_names(df)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# FETCH INVENTORY DATA (refactored for multi‑company, all products optional)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_inventory_data(company_keys, model_codes=None, exact=False, need_branch=False):
    """
    Fetch inventory (total and branch) for selected companies.
    If model_codes is None or empty, fetch all products (domain=[]).
    """
    if not company_keys:
        return pd.DataFrame(), pd.DataFrame()

    # Build domain: if model_codes provided, use _domain; else empty list = all products
    codes_list = [c.strip() for c in model_codes] if model_codes else None
    dom = _domain(codes_list, exact) if codes_list else []

    CS = "System"
    CM = "Model Code"
    CPR = "Product"
    CP = "Sale Price"
    CQ = "On Hand"
    CB = "Branch"
    CL = "Location"

    def _one(key):
        cfg = st.secrets.get(key)
        sn = key
        R = {"total": [], "branch": []}
        if not cfg:
            R["total"].append({CS: sn, CM: "—", CPR: "No config", CP: 0.0, CQ: 0, "_status": "ERROR"})
            return R
        uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
        if not uid:
            R["total"].append({CS: sn, CM: "—", CPR: "⚠️ Auth failed", CP: 0.0, CQ: 0, "_status": "ERROR"})
            return R
        u = cfg["url"]
        db = cfg["db"]
        ak = cfg["api_key"]
        try:
            prods = _x(u, db, uid, ak, "product.product", "search_read", [dom],
                       {"fields": ["id", "display_name", "default_code", "qty_available", "list_price"],
                        "limit": 2000, "order": "default_code asc"})
            if not prods:
                R["total"].append({CS: sn, CM: "—", CPR: "Not found", CP: 0.0, CQ: 0, "_status": "NOT_FOUND"})
                return R
            pids = [p["id"] for p in prods]
            pmap = {p["id"]: p for p in prods}
            for p in prods:
                R["total"].append({
                    CS: sn, CM: p.get("default_code") or "—",
                    CPR: p.get("display_name") or "",
                    CP: float(p.get("list_price") or 0),
                    CQ: int(p.get("qty_available") or 0),
                    "_status": "OK"})

            if need_branch:
                internal_locs = _x(u, db, uid, ak, "stock.location", "search_read",
                                   [[["usage", "=", "internal"], ["active", "=", True]]],
                                   {"fields": ["id"], "limit": 10000})
                internal_ids = {l["id"] for l in internal_locs}
                qs = _x(u, db, uid, ak, "stock.quant", "search_read",
                        [[["product_id", "in", pids],
                          ["location_id", "in", list(internal_ids)],
                          ["quantity", ">", 0]]],
                        {"fields": ["product_id", "location_id", "quantity"], "limit": 5000})
                for q in qs:
                    pid = q["product_id"][0] if isinstance(q.get("product_id"), list) else None
                    loc = q.get("location_id") or [None, "—"]
                    ln = loc[1] if isinstance(loc, list) else str(loc)
                    pm = pmap.get(pid, {})
                    R["branch"].append({
                        CS: sn, CB: ln, CL: ln,  # CL used for matrix
                        CM: pm.get("default_code") or "—",
                        CP: float(pm.get("list_price") or 0),
                        CQ: int(q.get("quantity") or 0), "_status": "OK"})
        except Exception as e:
            R["total"].append({CS: sn, CM: "—", CPR: f"❌ {e}", CP: 0.0, CQ: 0, "_status": "ERROR"})
        return R

    all_total = []
    all_branch = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_one, k): k for k in company_keys}
        for f in as_completed(futs):
            r = f.result()
            all_total.extend(r["total"])
            all_branch.extend(r["branch"])

    def _df(rows, cols):
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)

    total_df = _df(all_total, ["System", "Model Code", "Product", "Sale Price", "On Hand", "_status"])
    branch_df = _df(all_branch, ["System", "Branch", "Location", "Model Code", "Sale Price", "On Hand", "_status"])
    return total_df, branch_df

# Legacy purchase summary for branch matrix (unchanged)
@st.cache_data(ttl=3600, show_spinner=False)
def get_purchase_summary_by_model(model_codes_tuple, date_from, date_to):
    empty_df = pd.DataFrame(columns=["Model Code", "Purchase Qty"])
    cfg = st.secrets.get("SWAG")
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df
    u = cfg["url"]
    db = cfg["db"]
    ak = cfg["api_key"]
    try:
        line_domain = [
            ["order_id.state", "in", ["purchase", "done"]],
            ["order_id.date_order", ">=", f"{date_from} 00:00:00"],
            ["order_id.date_order", "<=", f"{date_to} 23:59:59"],
        ]
        if model_codes_tuple:
            line_domain.append(["product_id.default_code", "in", list(model_codes_tuple)])
        lines = _x(u, db, uid, ak, "purchase.order.line", "search_read", [line_domain],
                   {"fields": ["product_id", "product_qty"], "limit": 10000, "order": "id desc"})
        if not lines:
            return empty_df
        product_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _x(u, db, uid, ak, "product.product", "search_read",
                      [[["id", "in", product_ids]]],
                      {"fields": ["id", "default_code"], "limit": len(product_ids) + 10})
        prod_map = {p["id"]: p for p in products}
        agg = {}
        for line in lines:
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})
            mc = prod.get("default_code", "").strip()
            if not mc:
                continue
            agg[mc] = agg.get(mc, 0) + float(line.get("product_qty") or 0)
        if not agg:
            return empty_df
        df = pd.DataFrame([{"Model Code": mc, "Purchase Qty": qty} for mc, qty in agg.items()])
        return df.groupby("Model Code", as_index=False)["Purchase Qty"].sum()
    except Exception:
        return empty_df

# ─────────────────────────────────────────────────────────────────────────────
# MULTI‑COMPANY SALES (unchanged from earlier version)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sales_history_for_system(system_key, model_code, date_from, date_to):
    empty = pd.DataFrame(columns=[
        "Date", "SO", "Customer", "Branch", "Brand Category", "Category",
        "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "System"])

    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        domain = [
            ["order_id.state", "in", ["sale", "done"]],
            ["order_id.date_order", ">=", f"{date_from} 00:00:00"],
            ["order_id.date_order", "<=", f"{date_to} 23:59:59"],
        ]
        if model_code:
            domain.append(["product_id.default_code", "=like", f"{model_code}%"])

        lines = _x(u, db, uid, ak, "sale.order.line", "search_read", [domain],
                   {"fields": ["order_id", "product_id", "product_uom_qty", "price_unit", "price_subtotal"],
                    "limit": 15000, "order": "order_id desc"})
        if not lines:
            return empty

        order_ids = list({l["order_id"][0] for l in lines if isinstance(l.get("order_id"), list)})
        # Try branch_id field; fallback if not present
        try:
            orders = _x(u, db, uid, ak, "sale.order", "search_read",
                        [[["id", "in", order_ids]]],
                        {"fields": ["id", "name", "partner_id", "date_order", "branch_id"],
                         "limit": len(order_ids) + 10})
            has_branch = True
        except Exception:
            orders = _x(u, db, uid, ak, "sale.order", "search_read",
                        [[["id", "in", order_ids]]],
                        {"fields": ["id", "name", "partner_id", "date_order"],
                         "limit": len(order_ids) + 10})
            has_branch = False

        order_map = {o["id"]: o for o in orders}

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _x(u, db, uid, ak, "product.product", "search_read",
                      [[["id", "in", prod_ids]]],
                      {"fields": ["id", "default_code", "name", "categ_id", "product_tmpl_id"],
                       "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        tmpl_ids = list({p["product_tmpl_id"][0] for p in products
                         if isinstance(p.get("product_tmpl_id"), list)})
        tmpl_map = {}
        if tmpl_ids:
            for brand_field in ("x_studio_brand_category", "x_brand_category_id"):
                try:
                    tmpls = _x(u, db, uid, ak, "product.template", "search_read",
                               [[["id", "in", tmpl_ids]]],
                               {"fields": ["id", brand_field], "limit": len(tmpl_ids) + 10})
                    tmpl_map = {tt["id"]: (tt, brand_field) for tt in tmpls}
                    break
                except Exception:
                    continue

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            o = order_map.get(oid, {})
            p = prod_map.get(pid, {})

            # Branch
            if has_branch:
                branch_obj = o.get("branch_id")
                branch = (branch_obj[1] if isinstance(branch_obj, list) and len(branch_obj) > 1
                          else (str(branch_obj) if branch_obj else "Unknown"))
            else:
                branch = "N/A"

            # Category
            categ_obj = p.get("categ_id")
            categ = (categ_obj[1] if isinstance(categ_obj, list) and len(categ_obj) > 1
                     else (str(categ_obj) if categ_obj else ""))

            # Brand category
            brand_cat = ""
            tmpl_ref = p.get("product_tmpl_id")
            tid = tmpl_ref[0] if isinstance(tmpl_ref, list) else tmpl_ref
            if tid and tid in tmpl_map:
                tmpl, brand_field = tmpl_map[tid]
                raw = tmpl.get(brand_field, "")
                brand_cat = (raw[1] if isinstance(raw, list) and len(raw) > 1
                             else (str(raw) if raw else ""))

            partner_obj = o.get("partner_id")
            customer = (partner_obj[1] if isinstance(partner_obj, list) and len(partner_obj) > 1
                        else (str(partner_obj) if partner_obj else ""))
            prod_name_ref = line.get("product_id")
            product_display = (prod_name_ref[1] if isinstance(prod_name_ref, list) and len(prod_name_ref) > 1
                               else p.get("name", ""))
            raw_date = str(o.get("date_order", ""))
            date_val = raw_date[:10] if raw_date else ""

            rows.append({
                "System": system_name,
                "Date": date_val,
                "SO": o.get("name", ""),
                "Customer": customer,
                "Branch": branch,
                "Brand Category": brand_cat or "(No Brand)",
                "Category": categ or "(No Category)",
                "Model Code": str(p.get("default_code", "")).strip(),
                "Product": product_display,
                "Qty": float(line.get("product_uom_qty") or 0),
                "Unit Price": float(line.get("price_unit") or 0),
                "Subtotal": float(line.get("price_subtotal") or 0),
            })

        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)

    except Exception:
        return empty

def fetch_sales_multi_company(selected_keys, model_code, date_from, date_to):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_sales_history_for_system, k, model_code, date_from, date_to): k
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
# MULTI‑COMPANY PURCHASE (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_history_for_system(system_key, model_code, date_from, date_to):
    empty_cols = ["Date", "PO", "Vendor", "Brand Category", "Category",
                  "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "System",
                  "Receipt Location"]
    empty_df = pd.DataFrame(columns=empty_cols)

    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        line_domain = [
            ["order_id.state", "in", ["purchase", "done"]],
            ["order_id.date_order", ">=", f"{date_from} 00:00:00"],
            ["order_id.date_order", "<=", f"{date_to} 23:59:59"],
        ]
        if model_code and model_code.strip():
            line_domain.append(["product_id.default_code", "=", model_code.strip()])

        lines = _x(u, db, uid, ak, "purchase.order.line", "search_read", [line_domain],
                   {"fields": ["order_id", "product_id", "product_qty", "price_unit"],
                    "limit": 5000, "order": "order_id desc"})
        if not lines:
            return empty_df

        order_ids = list({l["order_id"][0] for l in lines if isinstance(l.get("order_id"), list)})
        product_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})

        orders = _x(u, db, uid, ak, "purchase.order", "search_read",
                    [[["id", "in", order_ids]]],
                    {"fields": ["id", "name", "partner_id", "date_order"], "limit": len(order_ids) + 10})
        order_map = {o["id"]: o for o in orders}

        products = _x(u, db, uid, ak, "product.product", "search_read",
                      [[["id", "in", product_ids]]],
                      {"fields": ["id", "default_code", "display_name", "categ_id", "product_tmpl_id"],
                       "limit": len(product_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        tmpl_ids = list({p["product_tmpl_id"][0] for p in products
                         if isinstance(p.get("product_tmpl_id"), list)})
        tmpl_map = {}
        if tmpl_ids:
            try:
                tmpls = _x(u, db, uid, ak, "product.template", "search_read",
                           [[["id", "in", tmpl_ids]]],
                           {"fields": ["id", "x_brand_category_id"], "limit": len(tmpl_ids) + 10})
                tmpl_map = {tt["id"]: tt for tt in tmpls}
            except Exception:
                pass

        # Receipt locations
        po_to_receipt_loc = {}
        try:
            pickings = _x(u, db, uid, ak, "stock.picking", "search_read",
                          [[["purchase_id", "in", order_ids],
                            ["picking_type_code", "=", "incoming"],
                            ["state", "=", "done"]]],
                          {"fields": ["purchase_id", "location_dest_id"], "limit": 5000})
            for pk in pickings:
                po_ref = pk.get("purchase_id")
                po_id = po_ref[0] if isinstance(po_ref, list) else po_ref
                loc = pk.get("location_dest_id")
                loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
                if po_id and loc_name:
                    po_to_receipt_loc[po_id] = loc_name
        except Exception:
            pass

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            order = order_map.get(oid, {})
            prod = prod_map.get(pid, {})

            raw_date = order.get("date_order") or ""
            try:
                date_str = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            except:
                date_str = raw_date[:10] if raw_date else "—"

            partner = order.get("partner_id")
            vendor = partner[1] if isinstance(partner, list) else (str(partner) if partner else "—")
            categ = prod.get("categ_id")
            category = categ[1] if isinstance(categ, list) else (str(categ) if categ else "")
            brand_category = ""
            tmpl_ref = prod.get("product_tmpl_id")
            if isinstance(tmpl_ref, list) and tmpl_ref:
                tmpl = tmpl_map.get(tmpl_ref[0], {})
                bc = tmpl.get("x_brand_category_id")
                if isinstance(bc, list):
                    brand_category = bc[1] if len(bc) > 1 else ""
                elif bc:
                    brand_category = str(bc)

            qty = float(line.get("product_qty") or 0)
            price = float(line.get("price_unit") or 0)
            receipt_loc = po_to_receipt_loc.get(oid, "")

            rows.append({
                "System": system_name,
                "Date": date_str,
                "PO": order.get("name") or "—",
                "Vendor": vendor,
                "Brand Category": brand_category,
                "Category": category,
                "Model Code": prod.get("default_code") or "",
                "Product": prod.get("display_name") or "",
                "Qty": qty,
                "Unit Price": price,
                "Subtotal": round(qty * price, 2),
                "Receipt Location": receipt_loc,
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        return df.sort_values(by="Date", ascending=False).reset_index(drop=True)

    except Exception:
        return empty_df

def fetch_purchase_multi_company(selected_keys, model_code, date_from, date_to):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_purchase_history_for_system, k, model_code, date_from, date_to): k
                for k in selected_keys}
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True).sort_values("Date", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXCEL EXPORT: PURCHASE & SALES (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def to_excel_purchase(df):
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    buf = io.BytesIO()
    clean = df.copy()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        clean.to_excel(w, index=False, sheet_name="Purchase")
        ws = w.sheets["Purchase"]
        hdr_fill = PatternFill("solid", fgColor="4B0082")
        hdr_font = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
        hdr_align = Alignment(horizontal="center", vertical="center")
        thin = Side(border_style="thin", color="D0D0D0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        alt_fill = PatternFill("solid", fgColor="F3EFFF")
        norm_font = Font(name="Calibri", size=10)
        num_align = Alignment(horizontal="right", vertical="center")
        ctr_align = Alignment(horizontal="center", vertical="center")
        tot_fill = PatternFill("solid", fgColor="2E2E2E")
        tot_font = Font(bold=True, name="Calibri", color="FFFFFF")
        max_row, max_col = ws.max_row, ws.max_column
        ws.row_dimensions[1].height = 28
        for col_num in range(1, max_col + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = hdr_align
            cell.border = border
        for row in ws.iter_rows(min_row=2, max_row=max_row):
            for cell in row:
                cell.border = border
                cell.font = norm_font
                if cell.row % 2 == 0:
                    cell.fill = alt_fill
                cell.alignment = num_align if isinstance(cell.value, (int, float)) else ctr_align
            ws.row_dimensions[row[0].row].height = 18
        for col_num in range(1, max_col + 1):
            col_letter = get_column_letter(col_num)
            max_len = max((len(str(ws.cell(row=r, column=col_num).value or ""))
                           for r in range(1, max_row + 1)), default=8)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(max_col)}{max_row}"
        tot_row = max_row + 1
        ws.cell(row=tot_row, column=1, value="TOTAL").font = tot_font
        ws.cell(row=tot_row, column=1).fill = tot_fill
        ws.cell(row=tot_row, column=1).alignment = Alignment(horizontal="center")
        col_names = [ws.cell(row=1, column=c).value for c in range(1, max_col + 1)]
        for cname in ("Qty", "Subtotal"):
            if cname in col_names:
                ci = col_names.index(cname) + 1
                cl = get_column_letter(ci)
                ws.cell(row=tot_row, column=ci, value=f"=SUM({cl}2:{cl}{max_row})")
                ws.cell(row=tot_row, column=ci).font = tot_font
                ws.cell(row=tot_row, column=ci).fill = tot_fill
                ws.cell(row=tot_row, column=ci).alignment = Alignment(horizontal="center")
        ws.row_dimensions[tot_row].height = 20
        ws.sheet_properties.tabColor = "667EEA"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.print_title_rows = "1:1"
        ws.sheet_view.zoomScale = 85
    return buf.getvalue()

def to_excel_sales(df):
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    buf = io.BytesIO()
    clean = df.copy()
    if "Date" in clean.columns:
        clean["Date"] = clean["Date"].astype(str).str[:10]
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        clean.to_excel(w, index=False, sheet_name="Sales")
        ws = w.sheets["Sales"]
        hdr_fill = PatternFill("solid", fgColor="1a6b3c")
        hdr_font = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
        hdr_align = Alignment(horizontal="center", vertical="center")
        thin = Side(border_style="thin", color="D0D0D0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        alt_fill = PatternFill("solid", fgColor="E8F5E9")
        norm_font = Font(name="Calibri", size=10)
        num_align = Alignment(horizontal="right", vertical="center")
        ctr_align = Alignment(horizontal="center", vertical="center")
        tot_fill = PatternFill("solid", fgColor="2E2E2E")
        tot_font = Font(bold=True, name="Calibri", color="FFFFFF")
        max_row, max_col = ws.max_row, ws.max_column
        ws.row_dimensions[1].height = 28
        for c in range(1, max_col + 1):
            cell = ws.cell(row=1, column=c)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = hdr_align
            cell.border = border
        for row in ws.iter_rows(min_row=2, max_row=max_row):
            for cell in row:
                cell.border = border
                cell.font = norm_font
                cell.fill = alt_fill if cell.row % 2 == 0 else PatternFill()
                cell.alignment = num_align if isinstance(cell.value, (int, float)) else ctr_align
            ws.row_dimensions[row[0].row].height = 18
        for c in range(1, max_col + 1):
            cl = get_column_letter(c)
            mxl = max((len(str(ws.cell(row=r, column=c).value or "")) for r in range(1, max_row + 1)), default=8)
            ws.column_dimensions[cl].width = min(max(mxl + 3, 12), 50)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(max_col)}{max_row}"
        tot_row = max_row + 1
        tot_cell = ws.cell(row=tot_row, column=1, value="TOTAL")
        tot_cell.font = tot_font
        tot_cell.fill = tot_fill
        tot_cell.alignment = ctr_align
        col_names = [ws.cell(row=1, column=c).value for c in range(1, max_col + 1)]
        for cname in ("Qty", "Subtotal"):
            if cname in col_names:
                ci = col_names.index(cname) + 1
                cl = get_column_letter(ci)
                ws.cell(row=tot_row, column=ci, value=f"=SUM({cl}2:{cl}{max_row})")
                ws.cell(row=tot_row, column=ci).font = tot_font
                ws.cell(row=tot_row, column=ci).fill = tot_fill
                ws.cell(row=tot_row, column=ci).alignment = ctr_align
        ws.sheet_properties.tabColor = "43e97b"
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY DF (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def display_df(df, thresh=0, table_key="tbl"):
    if df is None or df.empty:
        st.info(t("No data.", "لا بيانات."))
        return pd.DataFrame()

    work = df.copy()
    sys_col = t("System", "النظام")
    mc_col = t("Model Code", "رمز الموديل")
    pr_col = t("Product", "المنتج")
    br_col = t("Branch", "الفرع")
    loc_col = t("Location", "الموقع")
    qc = t("On Hand", "متوفر")
    pc = t("Sale Price", "سعر البيع")
    has_sys = sys_col in work.columns
    has_br = br_col in work.columns

    fc = st.columns([2, 2, 2, 1.5])

    if has_sys:
        all_sys = sorted(work[sys_col].dropna().unique().tolist())
        with fc[0]:
            sel_sys = st.multiselect(
                f"🏢 {t('Company', 'الشركة')}", options=all_sys, default=all_sys,
                key=f"{table_key}_sys")
        if sel_sys:
            work = work[work[sys_col].isin(sel_sys)]

    if has_br:
        all_br = sorted(work[br_col].dropna().unique().tolist())
        with fc[1]:
            sel_br = st.multiselect(
                f"🏪 {t('Branch', 'الفرع')}", options=all_br, default=all_br,
                key=f"{table_key}_br")
        if sel_br:
            work = work[work[br_col].isin(sel_br)]

    with fc[2]:
        q = st.text_input(
            f"🔍 {t('Search model / product', 'بحث موديل / منتج')}",
            value="", placeholder=t("e.g. XP6013 or Shirt", "مثال: XP6013"),
            key=f"{table_key}_q").strip()
    if q:
        ql = q.lower()
        mask = pd.Series([False] * len(work), index=work.index)
        for col in [mc_col, pr_col, loc_col]:
            if col in work.columns:
                mask = mask | work[col].fillna("").str.lower().str.contains(ql, regex=False)
        work = work[mask]

    with fc[3]:
        sortable = [c for c in work.columns if c != "_status"]
        sort_by = st.selectbox(
            f"↕️ {t('Sort by', 'ترتيب')}", options=["—"] + sortable, index=0,
            key=f"{table_key}_sort")
    if sort_by and sort_by != "—" and sort_by in work.columns:
        try:
            work = work.sort_values(
                by=sort_by,
                key=lambda s: pd.to_numeric(s, errors="coerce").fillna(0)
                if pd.api.types.is_numeric_dtype(pd.to_numeric(s, errors="coerce"))
                else s,
                ascending=True)
        except Exception:
            work = work.sort_values(by=sort_by)

    if work.empty:
        st.warning(t("⚠️ No rows match your filters.", "لا توجد نتائج بعد الفلتر."))
        return pd.DataFrame()

    if qc in work.columns:
        raw_q = pd.to_numeric(work[qc], errors="coerce")
        mn, mx = int(raw_q.min() or 0), int(raw_q.max() or 0)
        if mx > mn:
            qr = st.slider(f"📦 {t('Qty range', 'نطاق الكمية')}",
                           min_value=mn, max_value=mx, value=(mn, mx),
                           key=f"{table_key}_qrange")
            raw_q2 = pd.to_numeric(work[qc], errors="coerce")
            work = work[(raw_q2 >= qr[0]) & (raw_q2 <= qr[1])]

    ok_work = work[work["_status"] == "OK"] if "_status" in work.columns else work
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric(t("Rows", "الصفوف"), len(work))
    if qc in ok_work.columns:
        sm2.metric(t("Total Qty", "إجمالي الكمية"),
                   int(pd.to_numeric(ok_work[qc], errors="coerce").fillna(0).sum()))
    if pc in ok_work.columns:
        vp = pd.to_numeric(ok_work[pc], errors="coerce")
        sm3.metric(t("Avg Price", "متوسط السعر"),
                   f"{vp[vp > 0].mean():.2f} SAR" if not vp[vp > 0].empty else "—")
    if has_sys and sys_col in ok_work.columns:
        sm4.metric(t("Companies", "الشركات"), ok_work[sys_col].nunique())

    show = work.drop(columns=["_status"], errors="ignore").copy()
    _raw_qty = (pd.to_numeric(work[qc], errors="coerce").fillna(0)
                if qc in work.columns else pd.Series(dtype=float, index=work.index))

    if pc in show.columns:
        show[pc] = pd.to_numeric(show[pc], errors="coerce").map(
            lambda v: f"{v:.2f} SAR" if pd.notna(v) else "—")
    if qc in show.columns:
        _lang = get_lang()
        show[qc] = pd.to_numeric(show[qc], errors="coerce").map(
            lambda v: get_qty_display(v, _lang))

    low_idx = set()
    if thresh > 0 and qc in work.columns:
        raw_q3 = pd.to_numeric(work[qc], errors="coerce")
        low_idx = set(work.index[(raw_q3 > 0) & (raw_q3 <= thresh)])

    _zero_set = set(_raw_qty.index[_raw_qty == 0]) if not _raw_qty.empty else set()
    _na_label_en = "❌ Not Available"
    _na_label_ar = "❌ لا يوجد"

    cols = show.columns.tolist()
    th_ = "".join(f"<th>{c}</th>" for c in cols)

    def _row(idx_row):
        i, row = idx_row
        is_zero = i in _zero_set
        cls = " na-row" if is_zero else (" rl" if i in low_idx else "")
        cells = "".join(
            f'<td class="cf">{v}</td>' if ci == 0
            else (f'<td class="na-cell">{v}</td>'
                  if is_zero and isinstance(v, str) and v in (_na_label_en, _na_label_ar)
                  else f"<td>{v}</td>")
            for ci, v in enumerate(row))
        return f'<tr class="{cls}">{cells}<tr>'

    tbody = "".join(_row(x) for x in show.iterrows())
    st.markdown(
        f'{_TABLE_CSS}<div class="swag-wrap">'
        f'<table class="swag-tbl"><thead><tr>{th_}</tr></thead>'
        f'<tbody>{tbody}</tbody></table></div>',
        unsafe_allow_html=True)
    st.caption(f"📊 {len(show)} {t('rows shown', 'صفوف معروضة')} "
               f"/ {len(df)} {t('total', 'إجمالي')}")
    return work.drop(columns=["_status"], errors="ignore").copy()

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    _, _, lc = st.columns([2, 1, 0.5])
    with lc:
        lg = st.radio("", ["EN", "AR"], horizontal=True,
                      index=0 if get_lang() == "EN" else 1,
                      label_visibility="collapsed", key="llr")
        if lg != get_lang():
            st.session_state.lang = lg
            st.rerun()

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div style='display:flex;flex-direction:column;align-items:center;padding:20px 0 8px;'>
            <div class='login-orb'>📊</div>
            <div class='login-title'>Multi‑Company Ops Dashboard</div>
            <div class='login-subtitle'>Inventory · Sales · Purchase</div>
        </div>""", unsafe_allow_html=True)
        wm = ("🌙 مرحباً بك — سجّل دخولك للمتابعة" if get_lang() == "AR"
              else "👋 Welcome back! Sign in to continue.")
        st.markdown(f"<div class='welcome-banner'>{wm}</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        with st.form("lf", clear_on_submit=False):
            em = st.text_input(
                "📧 Email" if get_lang() == "EN" else "📧 البريد الإلكتروني",
                placeholder="you@swag.com.sa")
            pw = st.text_input(
                "🔑 Password" if get_lang() == "EN" else "🔑 كلمة المرور",
                type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            sub = st.form_submit_button(
                "🚀 Sign In" if get_lang() == "EN" else "🚀 تسجيل الدخول",
                use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)
        if sub:
            if not em or not pw:
                st.error(t("Fill in both fields.", "يرجى ملء جميع الحقول."))
                return
            if "LOGIN" not in st.secrets:
                st.error("❌ [LOGIN] section missing in secrets.toml")
                return
            cfg = st.secrets["LOGIN"]
            if "url" not in cfg or "db" not in cfg:
                st.error("❌ LOGIN.url or LOGIN.db missing in secrets.toml")
                return
            with st.spinner(t("⚡ Signing in…", "⚡ جارٍ تسجيل الدخول…")):
                try:
                    proxy = xmlrpc.client.ServerProxy(
                        f"{cfg['url']}/xmlrpc/2/common", allow_none=True)
                    uid = proxy.authenticate(cfg["db"], em, pw, {})
                    if uid:
                        token = _make_token(em)
                        st.query_params["u"] = em
                        st.query_params["t"] = token
                        st.session_state.authenticated = True
                        st.session_state.user_email = em
                        time.sleep(0.3)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(t("❌ Wrong email or password.",
                                   "❌ بريد إلكتروني أو كلمة مرور خاطئة."))
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")
        st.markdown("""<p style='text-align:center;color:#4a4a6a;font-size:.75rem;margin-top:24px;'>
        © 2025 SWAG Fashion · Powered by Odoo · Built with ❤️</p>""",
                    unsafe_allow_html=True)

def do_logout():
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD (new structure)
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    # Sidebar (only language and logout)
    with st.sidebar:
        st.markdown(f"### ⚙️ {t('Settings', 'الإعدادات')}")
        lc2 = st.radio(t("🌐 Language", "🌐 اللغة"), ["EN", "AR"],
                       index=0 if get_lang() == "EN" else 1, horizontal=True)
        if lc2 != get_lang():
            st.session_state.lang = lc2
            st.rerun()
        st.divider()
        st.markdown(f"👤 **{st.session_state.user_email}**")
        if st.button(f"🚪 {t('Logout', 'تسجيل الخروج')}", use_container_width=True):
            do_logout()

    # Header
    st.markdown(f"""
    <div class='dash-header'>
        <div class='dash-title'>📊 Multi‑Company Operations Dashboard</div>
        <div class='dash-subtitle'>{t('Inventory, Sales & Purchase across 4 Odoo systems',
                                       'المخزون والمبيعات والمشتريات عبر 4 أنظمة أودو')}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    # Create tabs
    tab_inv, tab_sales, tab_pur = st.tabs([
        f"📦 {t('Inventory', 'المخزون')}",
        f"🛍️ {t('Sales', 'المبيعات')}",
        f"🛒 {t('Purchase', 'المشتريات')}"
    ])

    # =========================================================================
    # INVENTORY TAB
    # =========================================================================
    with tab_inv:
        st.markdown(f"### 📦 {t('Inventory Overview', 'نظرة عامة على المخزون')}")

        # Company selector
        company_options = ["All Companies"] + [get_system_name(k) for k in SYSTEM_KEYS]
        selected_company = st.selectbox(
            t("Select Company", "اختر الشركة"),
            options=company_options,
            index=0,
            key="inv_company"
        )
        # Map to system keys
        if selected_company == "All Companies":
            inv_keys = SYSTEM_KEYS
        else:
            # find key by display name
            inv_keys = [k for k in SYSTEM_KEYS if get_system_name(k) == selected_company]

        # Filters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            model_filter = st.text_input(
                t("Model Code (optional)", "رمز الموديل (اختياري)"),
                placeholder=t("e.g. XP6013 — blank = all products", "مثال: XP6013 — فارغ = كل المنتجات"),
                key="inv_model_filter"
            ).strip()
        with col2:
            exact_match = st.toggle(t("Exact match only", "تطابق تام فقط"), value=False, key="inv_exact")
        with col3:
            low_thresh = st.number_input(
                t("Low stock threshold (qty ≤)", "حد المخزون المنخفض (كمية ≤)"),
                min_value=0, max_value=1000, value=5, step=1, key="inv_low_thresh"
            )

        refresh_btn = st.button(f"🔄 {t('Refresh Inventory', 'تحديث المخزون')}", type="primary")

        if refresh_btn:
            with st.spinner(t("Fetching inventory data...", "جاري جلب بيانات المخزون...")):
                total_df, branch_df = fetch_inventory_data(
                    company_keys=inv_keys,
                    model_codes=[model_filter] if model_filter else None,
                    exact=exact_match,
                    need_branch=True
                )
                # Add purchase qty for SWAG if needed (for matrix)
                if selected_company == "All Companies" or "SWAG" in inv_keys:
                    swag_sys_name = get_system_name("SWAG")
                    swag_mask = total_df[t("System", "النظام")] == swag_sys_name
                    if swag_mask.any():
                        model_codes_swag = total_df.loc[swag_mask, t("Model Code", "رمز الموديل")].dropna().unique().tolist()
                        if model_codes_swag:
                            end_date = datetime.now().date()
                            start_date = end_date - timedelta(days=365)
                            pur_summary = get_purchase_summary_by_model(
                                tuple(model_codes_swag),
                                start_date.strftime("%Y-%m-%d"),
                                end_date.strftime("%Y-%m-%d"))
                            if not pur_summary.empty:
                                pur_renamed = pur_summary.rename(columns={"Model Code": t("Model Code", "رمز الموديل")})
                                total_df = total_df.merge(pur_renamed[[t("Model Code", "رمز الموديل"), "Purchase Qty"]],
                                                          on=t("Model Code", "رمز الموديل"), how="left")
                                total_df["Purchase Qty"] = total_df["Purchase Qty"].fillna(0).astype(int)
                                total_df.loc[~swag_mask, "Purchase Qty"] = 0
                            else:
                                total_df["Purchase Qty"] = 0
                        else:
                            total_df["Purchase Qty"] = 0
                    else:
                        total_df["Purchase Qty"] = 0
                else:
                    total_df["Purchase Qty"] = 0

                total_df = prepare_df(total_df)
                branch_df = prepare_df(branch_df)
                st.session_state.inventory_df = total_df
                st.session_state.inventory_branch_df = branch_df
                st.session_state.inventory_last_params = {
                    "company": selected_company,
                    "model": model_filter,
                    "exact": exact_match
                }

        # Load from session if available
        total_df = st.session_state.get("inventory_df")
        branch_df = st.session_state.get("inventory_branch_df")

        if total_df is None or total_df.empty:
            st.info(t("Click 'Refresh Inventory' to load data.", "اضغط 'تحديث المخزون' لتحميل البيانات."))
        else:
            # Metrics
            qc = t("On Hand", "متوفر")
            sys_col = t("System", "النظام")
            ok_total = total_df[total_df["_status"] == "OK"] if "_status" in total_df.columns else total_df
            total_qty = int(pd.to_numeric(ok_total[qc], errors="coerce").fillna(0).sum())
            distinct_models = ok_total[t("Model Code", "رمز الموديل")].nunique()
            st.metric(t("Total Stock Qty", "إجمالي الكمية"), f"{total_qty:,}")
            st.metric(t("Distinct Models", "عدد الموديلات"), distinct_models)

            # Branch-wise stock (if branch data exists)
            if branch_df is not None and not branch_df.empty:
                st.markdown(f"#### 🏪 {t('Branch-wise Stock', 'المخزون حسب الفرع')}")
                branch_col = t("Branch", "الفرع")
                qty_col = t("On Hand", "متوفر")
                branch_summary = branch_df.groupby(branch_col)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False)
                st.bar_chart(branch_summary.set_index(branch_col)[qty_col], use_container_width=True)
                st.markdown(f"**{t('Top Branches by Stock', 'أعلى الفروع بالمخزون')}**")
                st.dataframe(branch_summary.head(10), use_container_width=True)

            # Top models by stock
            st.markdown(f"#### 🏆 {t('Top Models by Stock', 'أعلى الموديلات بالمخزون')}")
            top_models = ok_total.groupby(t("Model Code", "رمز الموديل"))[qc].sum().reset_index().sort_values(qc, ascending=False).head(10)
            st.bar_chart(top_models.set_index(t("Model Code", "رمز الموديل"))[qc], use_container_width=True)

            # Low stock items
            if low_thresh > 0:
                low_stock = ok_total[(pd.to_numeric(ok_total[qc], errors="coerce") > 0) &
                                     (pd.to_numeric(ok_total[qc], errors="coerce") <= low_thresh)]
                if not low_stock.empty:
                    st.markdown(f"<div class='alert-banner'>🔴 {len(low_stock)} {t('low stock items', 'عناصر منخفضة المخزون')} ≤ {low_thresh}</div>", unsafe_allow_html=True)
                    st.dataframe(low_stock[[t("Model Code", "رمز الموديل"), t("Product", "المنتج"), qc]], use_container_width=True)
                else:
                    st.success(t("No low stock items above threshold.", "لا توجد عناصر منخفضة المخزون فوق الحد."))

            # Detailed inventory table
            st.markdown(f"#### 📋 {t('Detailed Inventory', 'المخزون التفصيلي')}")
            filtered_inv = display_df(total_df, thresh=low_thresh, table_key="inv_detail")
            st.markdown("<br>", unsafe_allow_html=True)

            # Export buttons
            exp1, exp2, exp3 = st.columns(3)
            with exp1:
                st.download_button("⬇️ CSV", to_csv(total_df), dl_name("inventory", "csv"), "text/csv", use_container_width=True)
            with exp2:
                st.download_button("⬇️ Excel", to_excel(total_df), dl_name("inventory", "xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with exp3:
                # Branch matrix export (uses current filtered branch data)
                if branch_df is not None and not branch_df.empty:
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel', 'Excel مصفوفة الفروع')}",
                        to_excel_branch_matrix(branch_df, get_lang()),
                        dl_name("branch_matrix", "xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel', 'Excel مصفوفة الفروع')}",
                        data=b"",
                        file_name="placeholder.xlsx",
                        disabled=True,
                        use_container_width=True
                    )

    # =========================================================================
    # SALES TAB
    # =========================================================================
    with tab_sales:
        st.markdown(f"### 🛍️ {t('Sales Analytics', 'تحليلات المبيعات')}")
        st.markdown(
            "<div class='info-banner'>📌 "
            + t("Sales orders with state: sale / done. "
                "Branch data requires <code>branch_id</code> field on <code>sale.order</code>. "
                "Systems without this field will show <b>N/A</b> in the Branch column.",
                "أوامر البيع بالحالة: مباع / منجز. "
                "بيانات الفروع تتطلب حقل <code>branch_id</code> على <code>sale.order</code>. "
                "الأنظمة التي لا تحتوي على هذا الحقل ستظهر <b>غير متاح</b> في عمود الفرع.")
            + "</div>", unsafe_allow_html=True)

        # Company selector
        sales_company = st.selectbox(
            t("Select Company", "اختر الشركة"),
            options=company_options,
            index=0,
            key="sales_company"
        )
        if sales_company == "All Companies":
            sales_keys = SYSTEM_KEYS
        else:
            sales_keys = [k for k in SYSTEM_KEYS if get_system_name(k) == sales_company]

        # Date range and model filter
        col_d1, col_d2, col_d3 = st.columns([1, 1, 2])
        with col_d1:
            date_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=30), key="sales_from")
        with col_d2:
            date_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="sales_to")
        with col_d3:
            sales_model = st.text_input(
                t("Model Code (optional)", "رمز الموديل (اختياري)"),
                placeholder=t("e.g. XP6013 — blank = all", "مثال: XP6013 — فارغ = الكل"),
                key="sales_model"
            ).strip()

        fetch_sales = st.button(f"🔄 {t('Refresh Sales', 'تحديث المبيعات')}", type="primary")

        if fetch_sales:
            with st.spinner(t("Fetching sales data...", "جاري جلب بيانات المبيعات...")):
                sales_df = fetch_sales_multi_company(
                    selected_keys=sales_keys,
                    model_code=sales_model if sales_model else None,
                    date_from=date_from.strftime("%Y-%m-%d"),
                    date_to=date_to.strftime("%Y-%m-%d")
                )
                st.session_state.sales_df = sales_df
                st.session_state.sales_last_params = {
                    "company": sales_company,
                    "from": str(date_from),
                    "to": str(date_to),
                    "model": sales_model
                }

        sales_df = st.session_state.get("sales_df")
        if sales_df is None or sales_df.empty:
            st.info(t("Click 'Refresh Sales' to load data.", "اضغط 'تحديث المبيعات' لتحميل البيانات."))
        else:
            # Metrics
            total_qty = sales_df["Qty"].sum()
            total_rev = sales_df["Subtotal"].sum()
            cust_count = sales_df["Customer"].nunique()
            prod_count = sales_df["Model Code"].nunique()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("Total Qty Sold", "إجمالي الكميات المباعة"), f"{total_qty:,.0f}")
            m2.metric(t("Total Revenue (SAR)", "إجمالي الإيراد (ر.س)"), f"{total_rev:,.2f}")
            m3.metric(t("Customers", "العملاء"), cust_count)
            m4.metric(t("Products", "المنتجات"), prod_count)
            st.divider()

            # Branch-wise sales (if branch column exists)
            if "Branch" in sales_df.columns:
                branch_sales = sales_df.groupby("Branch").agg(Qty=("Qty", "sum"), Revenue=("Subtotal", "sum")).reset_index()
                branch_sales = branch_sales.sort_values("Revenue", ascending=False)
                st.markdown(f"#### 🏪 {t('Branch-wise Sales', 'المبيعات حسب الفرع')}")
                bc1, bc2 = st.columns(2)
                with bc1:
                    st.markdown(f"**📦 {t('By Qty', 'حسب الكمية')}**")
                    st.bar_chart(branch_sales.set_index("Branch")["Qty"], use_container_width=True)
                with bc2:
                    st.markdown(f"**💰 {t('By Revenue', 'حسب الإيراد')}**")
                    st.bar_chart(branch_sales.set_index("Branch")["Revenue"], use_container_width=True)
                st.markdown(f"**{t('Top Branches', 'أعلى الفروع')}**")
                st.dataframe(branch_sales.head(10), use_container_width=True)
                st.divider()

            # Top customers
            top_cust = sales_df.groupby("Customer")["Subtotal"].sum().reset_index().sort_values("Subtotal", ascending=False).head(10)
            st.markdown(f"#### 👑 {t('Top Customers by Revenue', 'أعلى العملاء حسب الإيراد')}")
            st.bar_chart(top_cust.set_index("Customer")["Subtotal"], use_container_width=True)
            st.divider()

            # Top products
            top_prod_qty = sales_df.groupby(["Model Code", "Product"])["Qty"].sum().reset_index().sort_values("Qty", ascending=False).head(10)
            st.markdown(f"#### 🏆 {t('Top Products by Qty', 'أعلى المنتجات حسب الكمية')}")
            st.bar_chart(top_prod_qty.set_index("Model Code")["Qty"], use_container_width=True)
            st.dataframe(top_prod_qty[["Model Code", "Product", "Qty"]], use_container_width=True)
            st.divider()

            # Top categories
            top_cat = sales_df.groupby("Category")["Qty"].sum().reset_index().sort_values("Qty", ascending=False).head(10)
            st.markdown(f"#### 🗂️ {t('Top Categories by Qty', 'أعلى الفئات حسب الكمية')}")
            st.bar_chart(top_cat.set_index("Category")["Qty"], use_container_width=True)
            st.divider()

            # Daily trend
            daily = sales_df.copy()
            daily["Date"] = pd.to_datetime(daily["Date"], errors="coerce")
            daily = daily.dropna(subset=["Date"])
            if not daily.empty:
                daily_trend = daily.groupby(daily["Date"].dt.date).agg(Qty=("Qty", "sum"), Revenue=("Subtotal", "sum")).reset_index()
                daily_trend = daily_trend.set_index("Date")
                st.markdown(f"#### 📈 {t('Daily Sales Trend', 'اتجاه المبيعات اليومي')}")
                st.line_chart(daily_trend[["Qty", "Revenue"]], use_container_width=True)
            else:
                st.info(t("No date data for trend.", "لا تتوفر بيانات للاتجاه."))
            st.divider()

            # Full detail table
            st.markdown(f"#### 📋 {t('Sales Detail', 'تفاصيل المبيعات')}")
            show_sales = sales_df.copy()
            show_sales["Date"] = show_sales["Date"].astype(str).str[:10]
            show_sales["Unit Price"] = show_sales["Unit Price"].map(lambda v: f"{v:.2f} SAR")
            show_sales["Subtotal"] = show_sales["Subtotal"].map(lambda v: f"{v:,.2f} SAR")
            show_sales["Qty"] = show_sales["Qty"].map(lambda v: f"{v:,.0f}")
            _render_html_table(show_sales)
            st.caption(f"📊 {len(show_sales)} {t('rows', 'صفوف')}")
            st.markdown("<br>", unsafe_allow_html=True)

            # Export
            exp_s1, exp_s2 = st.columns(2)
            export_sales = sales_df.copy()
            export_sales["Date"] = export_sales["Date"].astype(str).str[:10]
            with exp_s1:
                st.download_button("⬇️ CSV", export_sales.to_csv(index=False).encode("utf-8-sig"),
                                   dl_name("sales", "csv"), "text/csv", use_container_width=True)
            with exp_s2:
                st.download_button("⬇️ Excel", to_excel_sales(export_sales), dl_name("sales", "xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # PURCHASE TAB
    # =========================================================================
    with tab_pur:
        st.markdown(f"### 🛒 {t('Purchase Analytics', 'تحليلات المشتريات')}")
        st.markdown(
            "<div class='warn-banner'>⚠️ <b>"
            + t("Purchase Branch Note", "ملاحظة فروع المشتريات")
            + "</b> — "
            + t(
                "Standard Odoo <code>purchase.order</code> has no native branch field. "
                "The <b>Receipt Location</b> column is derived from the linked incoming stock receipt "
                "(<code>stock.picking</code> destination). "
                "It reflects <em>where goods were received</em>, not a formal organisational branch.",
                "نموذج <code>purchase.order</code> في أودو القياسي لا يحتوي على حقل فرع أصلي. "
                "عمود <b>موقع الاستلام</b> مشتق من وصل الاستلام المرتبط "
                "(<code>stock.picking</code> الوجهة). "
                "يعكس <em>مكان استلام البضاعة</em> وليس فرعاً تنظيمياً رسمياً.")
            + "</div>", unsafe_allow_html=True)

        # Company selector
        pur_company = st.selectbox(
            t("Select Company", "اختر الشركة"),
            options=company_options,
            index=0,
            key="pur_company"
        )
        if pur_company == "All Companies":
            pur_keys = SYSTEM_KEYS
        else:
            pur_keys = [k for k in SYSTEM_KEYS if get_system_name(k) == pur_company]

        # Date range and model filter
        col_p1, col_p2, col_p3 = st.columns([1, 1, 2])
        with col_p1:
            pur_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=365), key="pur_from")
        with col_p2:
            pur_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="pur_to")
        with col_p3:
            pur_model = st.text_input(
                t("Model Code (optional)", "رمز الموديل (اختياري)"),
                placeholder=t("e.g. RVT196 — blank = all", "مثال: RVT196 — فارغ = الكل"),
                key="pur_model"
            ).strip()

        fetch_pur = st.button(f"🔄 {t('Refresh Purchase', 'تحديث المشتريات')}", type="primary")

        if fetch_pur:
            with st.spinner(t("Fetching purchase data...", "جاري جلب بيانات المشتريات...")):
                pur_df = fetch_purchase_multi_company(
                    selected_keys=pur_keys,
                    model_code=pur_model if pur_model else None,
                    date_from=pur_from.strftime("%Y-%m-%d"),
                    date_to=pur_to.strftime("%Y-%m-%d")
                )
                st.session_state.purchase_df = pur_df
                st.session_state.purchase_last_params = {
                    "company": pur_company,
                    "from": str(pur_from),
                    "to": str(pur_to),
                    "model": pur_model
                }

        pur_df = st.session_state.get("purchase_df")
        if pur_df is None or pur_df.empty:
            st.info(t("Click 'Refresh Purchase' to load data.", "اضغط 'تحديث المشتريات' لتحميل البيانات."))
        else:
            # Metrics
            total_qty = pur_df["Qty"].sum()
            total_amt = pur_df["Subtotal"].sum()
            distinct_products = pur_df["Model Code"].nunique()
            distinct_vendors = pur_df["Vendor"].nunique()
            pm1, pm2, pm3, pm4 = st.columns(4)
            pm1.metric(t("Total Qty Purchased", "إجمالي الكمية المشتراة"), f"{total_qty:,.0f}")
            pm2.metric(t("Total Amount (SAR)", "إجمالي المبلغ (ر.س)"), f"{total_amt:,.2f}")
            pm3.metric(t("Products", "المنتجات"), distinct_products)
            pm4.metric(t("Vendors", "الموردين"), distinct_vendors)
            st.divider()

            # Top products
            top_prod = pur_df.groupby(["Model Code", "Product"])["Qty"].sum().reset_index().sort_values("Qty", ascending=False).head(10)
            st.markdown(f"#### 🏆 {t('Top Products by Qty', 'أعلى المنتجات حسب الكمية')}")
            st.bar_chart(top_prod.set_index("Model Code")["Qty"], use_container_width=True)
            st.divider()

            # Top categories
            top_cat = pur_df.groupby("Category")["Qty"].sum().reset_index().sort_values("Qty", ascending=False).head(10)
            st.markdown(f"#### 🗂️ {t('Top Categories by Qty', 'أعلى الفئات حسب الكمية')}")
            st.bar_chart(top_cat.set_index("Category")["Qty"], use_container_width=True)
            st.divider()

            # Receipt location summary (if available)
            if "Receipt Location" in pur_df.columns:
                loc_data = pur_df[pur_df["Receipt Location"].notna() & (pur_df["Receipt Location"] != "")]
                if not loc_data.empty:
                    loc_sum = loc_data.groupby("Receipt Location")["Qty"].sum().reset_index().sort_values("Qty", ascending=False).head(10)
                    st.markdown(f"#### 📍 {t('Top Receipt Locations', 'أعلى مواقع الاستلام')}")
                    st.bar_chart(loc_sum.set_index("Receipt Location")["Qty"], use_container_width=True)
                    st.divider()

            # Vendor summary
            vendor_sum = pur_df.groupby("Vendor").agg(Total_Qty=("Qty", "sum"), Total_Amount=("Subtotal", "sum")).reset_index().sort_values("Total_Qty", ascending=False).head(10)
            st.markdown(f"#### 🏪 {t('Top Vendors', 'أعلى الموردين')}")
            st.dataframe(vendor_sum, use_container_width=True)
            st.divider()

            # Full detail table
            st.markdown(f"#### 📋 {t('Purchase Detail', 'تفاصيل المشتريات')}")
            show_pur = pur_df.drop(columns=["Receipt Location"], errors="ignore").copy()
            show_pur["Unit Price"] = show_pur["Unit Price"].map(lambda v: f"{v:.2f} SAR")
            show_pur["Subtotal"] = show_pur["Subtotal"].map(lambda v: f"{v:,.2f} SAR")
            show_pur["Qty"] = show_pur["Qty"].map(lambda v: f"{v:,.0f}")
            _render_html_table(show_pur)
            st.caption(f"📊 {len(show_pur)} {t('rows', 'صفوف')}")
            st.markdown("<br>", unsafe_allow_html=True)

            # Export
            exp_p1, exp_p2 = st.columns(2)
            with exp_p1:
                st.download_button("⬇️ CSV", pur_df.to_csv(index=False).encode("utf-8-sig"),
                                   dl_name("purchase", "csv"), "text/csv", use_container_width=True)
            with exp_p2:
                st.download_button("⬇️ Excel", to_excel_purchase(pur_df), dl_name("purchase", "xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
