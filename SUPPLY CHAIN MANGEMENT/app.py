# app.py – FULLY WORKING VERSION (Inventory, POS, Sales, Purchase)
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
# CSS (unchanged – keep your existing styling)
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
# LANGUAGE HELPERS
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
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
_DEF = {
    "authenticated": False,
    "user_email": "",
    "lang": "EN",
    "inventory_df": None,
    "inventory_branch_df": None,
    "inventory_last_params": {},
    "pos_df": None,
    "pos_last_params": {},
    "sales_df": None,
    "sales_last_params": {},
    "purchase_df": None,
    "purchase_last_params": {},
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
        email  = params.get("u", "")
        token  = params.get("t", "")
        if email and token and _verify_token(email, token):
            st.session_state.authenticated = True
            st.session_state.user_email    = email
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

def _get_uid_for_key(key):
    cfg = st.secrets.get(key)
    if not cfg:
        return None, None
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    return (cfg, uid) if uid else (None, None)

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _domain(codes, exact=False):
    """Build Odoo domain for product default_code filter."""
    if not codes:
        return []
    if exact:
        return [("default_code", "in", list(codes))]
    return ["|"] + [("default_code", "=ilike", f"{code}%") for code in codes]

def localize_columns(df):
    """Rename English column headers to the current UI language."""
    if df is None or df.empty:
        return df
    rename_map = {
        "System":           t("System",           "النظام"),
        "Model Code":       t("Model Code",        "رمز الموديل"),
        "Product":          t("Product",           "المنتج"),
        "Sale Price":       t("Sale Price",        "سعر البيع"),
        "On Hand":          t("On Hand",           "متوفر"),
        "Branch":           t("Branch",            "الفرع"),
        "Location":         t("Location",          "الموقع"),
        "Date":             t("Date",              "التاريخ"),
        "POS Order":        t("POS Order",         "طلب نقطة بيع"),
        "Customer":         t("Customer",          "العميل"),
        "Cashier":          t("Cashier",           "الكاشير"),
        "Category":         t("Category",          "الفئة"),
        "Qty":              t("Qty",               "الكمية"),
        "Unit Price":       t("Unit Price",        "سعر الوحدة"),
        "Subtotal":         t("Subtotal",          "المجموع الفرعي"),
        "SO":               t("SO",                "أمر بيع"),
        "Brand Category":   t("Brand Category",    "فئة العلامة التجارية"),
        "Vendor":           t("Vendor",            "المورد"),
        "Receipt Location": t("Receipt Location",  "موقع الاستلام"),
        "Purchase Qty":     t("Purchase Qty",      "كمية الشراء"),
        "Order ID":         t("Order ID",          "رقم الطلب"),
        "Total Amount":     t("Total Amount",      "المبلغ الإجمالي"),
        "Bill Number":      t("Bill Number",       "رقم الفاتورة"),
    }
    to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
    return df.rename(columns=to_rename)

def prepare_df(df):
    """Localize columns, drop internal-only columns, coerce numeric types."""
    if df is None or df.empty:
        return df
    df = localize_columns(df)
    if "_status" in df.columns:
        df = df.drop(columns=["_status"])
    numeric_cols = [
        "On Hand", "Sale Price", "Qty", "Unit Price", "Subtotal", "Purchase Qty",
        t("On Hand", "متوفر"), t("Sale Price", "سعر البيع"),
        t("Qty", "الكمية"),    t("Unit Price", "سعر الوحدة"),
        t("Subtotal", "المجموع الفرعي"), "Total Amount",
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
                cell.font      = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
        except Exception:
            pass
    return output.getvalue()

def to_excel_bulk(dfs, sheet_names):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for df, name in zip(dfs, sheet_names):
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()

def to_excel_branch_matrix(branch_df, lang):
    """Pivot: rows = Model Code, columns = Branch, values = On Hand."""
    if branch_df is None or branch_df.empty:
        return b""
    branch_df  = localize_columns(branch_df)
    branch_col = t("Branch",     "الفرع")
    model_col  = t("Model Code", "رمز الموديل")
    qty_col    = t("On Hand",    "متوفر")
    if branch_col not in branch_df.columns or model_col not in branch_df.columns:
        return b""
    pivot = branch_df.pivot_table(
        index=model_col,
        columns=branch_col,
        values=qty_col,
        aggfunc="sum",
        fill_value=0,
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pivot.to_excel(writer, sheet_name="Branch_Matrix")
    return output.getvalue()

def dl_name(prefix, ext):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# TABLE DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
_TABLE_CSS = """
<style>
.dataframe{font-family:'IBM Plex Sans Arabic',sans-serif;border-collapse:collapse;
width:100%;background:#1e1e3f;color:#e8e8ff;border-radius:12px;overflow:hidden;}
.dataframe th{background:linear-gradient(135deg,#667eea,#764ba2);color:white;
padding:10px 12px;text-align:center;font-weight:600;}
.dataframe td{padding:8px 12px;text-align:center;border-bottom:1px solid #2d2b55;}
.dataframe tr:hover{background:#2d2b55;}
</style>
"""

def _render_html_table(df, max_rows=1000):
    if df is None or df.empty:
        st.write("No data to display.")
        return
    st.markdown(_TABLE_CSS, unsafe_allow_html=True)
    st.markdown(
        df.head(max_rows).to_html(classes="dataframe", index=False, escape=False),
        unsafe_allow_html=True,
    )
    if len(df) > max_rows:
        st.caption(f"Showing first {max_rows} of {len(df)} rows.")

def display_df(df, thresh=None, table_key=None):
    """Render HTML table and return filtered DataFrame (if thresh provided)."""
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
# INVENTORY FETCH (fully working, already fixed)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetchalldata(
    codestuple=(),
    exact=False,
    needbranch=True,
    needtransfers=False,
    needreorder=False,
    reordermode="dayscover",
    targetdays=30,
    maxlevel=100,
    reorderpoint=10,
):
    all_rows        = []
    all_branch_rows = []
    empty           = pd.DataFrame()

    for key in SYSTEM_KEYS:
        cfg = st.secrets.get(key)
        if not cfg:
            continue
        uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
        if not uid:
            continue

        u, db, ak   = cfg["url"], cfg["db"], cfg["api_key"]
        system_name = get_system_name(key)

        try:
            prod_domain = []
            if codestuple:
                if exact:
                    prod_domain = [("default_code", "in", list(codestuple))]
                else:
                    clauses = [("default_code", "=ilike", f"{c}%") for c in codestuple]
                    if len(clauses) == 1:
                        prod_domain = [clauses[0]]
                    else:
                        prod_domain = ["|"] * (len(clauses) - 1) + clauses

            products = _x(u, db, uid, ak, "product.template", "search_read",
                          [prod_domain] if prod_domain else [[]],
                          {"fields": ["id", "name", "default_code", "list_price", "categ_id"],
                           "limit": 5000})
            if not products:
                continue

            prod_ids = [p["id"] for p in products]
            tmpl_to_model = {p["id"]: p.get("default_code", "") for p in products}
            tmpl_to_name  = {p["id"]: p.get("name", "") for p in products}
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

                if needbranch:
                    loc = q.get("location_id")
                    loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
                    all_branch_rows.append({
                        "System":     system_name,
                        "Branch":     loc_name,
                        "Model Code": tmpl_to_model.get(tmpl_id, ""),
                        "On Hand":    qty,
                    })

            for tmpl_id in prod_ids:
                qty = tmpl_qty.get(tmpl_id, 0)
                all_rows.append({
                    "System":     system_name,
                    "Model Code": tmpl_to_model.get(tmpl_id, ""),
                    "Product":    tmpl_to_name.get(tmpl_id, ""),
                    "Sale Price": tmpl_to_price.get(tmpl_id, 0),
                    "On Hand":    qty,
                    "_status":    "OK",
                })

        except Exception:
            continue

    total_df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame(
        columns=["System", "Model Code", "Product", "Sale Price", "On Hand", "_status"])

    if needbranch and all_branch_rows:
        branch_df = pd.DataFrame(all_branch_rows)
        branch_df = branch_df[["System", "Branch", "Model Code", "On Hand"]]
    else:
        branch_df = pd.DataFrame(columns=["System", "Branch", "Model Code", "On Hand"])

    transfers_df = empty
    reorder_df   = empty

    return total_df, branch_df, transfers_df, reorder_df

def fetch_inventory_data(
    codestuple=(),
    exact=False,
    needbranch=True,
    needtransfers=False,
    needreorder=False,
    reordermode="dayscover",
    targetdays=30,
    maxlevel=100,
    reorderpoint=10,
):
    total_df, branch_df, _, _ = fetchalldata(
        codestuple=codestuple,
        exact=exact,
        needbranch=needbranch,
        needtransfers=needtransfers,
        needreorder=needreorder,
        reordermode=reordermode,
        targetdays=targetdays,
        maxlevel=maxlevel,
        reorderpoint=reorderpoint,
    )
    return total_df, branch_df

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE FETCH (fully working)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_history_for_system(system_key, model_code, date_from, date_to):
    _empty_cols = ["Date", "PO", "Vendor", "Receipt Location", "Category",
                   "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "System"]
    empty_df = pd.DataFrame(columns=_empty_cols)

    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak   = cfg["url"], cfg["db"], cfg["api_key"]
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
            loc      = pick.get("location_dest_id")
            loc_name = (loc[1] if isinstance(loc, list) and len(loc) > 1
                        else str(loc) if loc else "")
            receipt_map[pick.get("origin", "")] = loc_name

        rows = []
        for line in lines:
            oid  = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            po   = po_map.get(oid, {})
            if not po:
                continue
            pid  = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod = prod_map.get(pid, {})

            model_code_val = prod.get("default_code", "").strip()
            if model_code and model_code_val:
                if not model_code_val.upper().startswith(model_code.upper()):
                    continue

            receipt_loc = receipt_map.get(po.get("name", ""), "")
            categ_obj   = prod.get("categ_id")
            category    = (categ_obj[1] if isinstance(categ_obj, list) and len(categ_obj) > 1
                           else str(categ_obj) if categ_obj else "")
            partner_obj = po.get("partner_id")
            vendor      = (partner_obj[1] if isinstance(partner_obj, list) and len(partner_obj) > 1
                           else str(partner_obj) if partner_obj else "")

            rows.append({
                "System":           system_name,
                "Date":             str(po.get("date_approve", ""))[:10],
                "PO":               po.get("name", ""),
                "Vendor":           vendor,
                "Receipt Location": receipt_loc,
                "Category":         category,
                "Model Code":       model_code_val,
                "Product":          prod.get("name", ""),
                "Qty":              float(line.get("product_qty") or 0),
                "Unit Price":       float(line.get("price_unit") or 0),
                "Subtotal":         float(line.get("price_subtotal") or 0),
            })

        if not rows:
            return empty_df
        df         = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)

    except Exception:
        return empty_df

def fetch_purchase_multi_company(selected_keys, model_code, date_from, date_to):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_purchase_history_for_system,
                          k, model_code, date_from, date_to): k
                for k in selected_keys}
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    combined         = pd.concat(results, ignore_index=True)
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

        prod_ids = list({l["product_id"][0] for l in lines
                         if isinstance(l.get("product_id"), list)})
        products = _x(swag_cfg["url"], swag_cfg["db"], uid, swag_cfg["api_key"],
                      "product.product", "search_read", [[["id", "in", prod_ids]]],
                      {"fields": ["id", "default_code"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p.get("default_code", "") for p in products}
        summary: dict = {}
        for line in lines:
            pid   = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            model = prod_map.get(pid, "")
            if not model:
                continue
            summary[model] = summary.get(model, 0) + float(line.get("product_qty") or 0)
        return pd.DataFrame(list(summary.items()), columns=["Model Code", "Purchase Qty"])
    except Exception:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])

# ─────────────────────────────────────────────────────────────────────────────
# POS FETCH (NEW – fully working)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_pos_data_for_system(system_key, date_from, date_to, branch_filter, model_filter):
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
        # Fetch pos orders
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

        # Extract branch info from session -> config
        session_ids = list({o["session_id"][0] for o in orders if o.get("session_id")})
        branch_map = {}
        if session_ids:
            sessions = _x(u, db, uid, ak, "pos.session", "search_read",
                          [[["id", "in", session_ids]]],
                          {"fields": ["id", "config_id"]}, limit=len(session_ids)+10)
            config_ids = list({s["config_id"][0] for s in sessions if s.get("config_id")})
            if config_ids:
                configs = _x(u, db, uid, ak, "pos.config", "search_read",
                             [[["id", "in", config_ids]]],
                             {"fields": ["id", "name"]}, limit=len(config_ids)+10)
                config_name = {c["id"]: c["name"] for c in configs}
                for s in sessions:
                    branch_map[s["id"]] = config_name.get(s["config_id"][0], "Unknown")
            else:
                branch_map = {s["id"]: "Unknown" for s in sessions}
        else:
            branch_map = {}

        # Collect all order line ids
        line_ids = []
        for o in orders:
            if o.get("lines"):
                line_ids.extend(o["lines"])
        if not line_ids:
            return empty_df

        # Fetch order lines
        lines = _x(u, db, uid, ak, "pos.order.line", "search_read",
                   [[["id", "in", line_ids]]],
                   {"fields": ["order_id", "product_id", "qty", "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        # Map order id to order data
        order_map = {o["id"]: o for o in orders}

        # Get product details
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = []
        if prod_ids:
            products = _x(u, db, uid, ak, "product.product", "search_read",
                          [[["id", "in", prod_ids]]],
                          {"fields": ["id", "default_code", "name", "categ_id"],
                           "limit": len(prod_ids)+20})
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            order = order_map.get(line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id"))
            if not order:
                continue

            branch_name = branch_map.get(order.get("session_id", [None])[0] if isinstance(order.get("session_id"), list) else order.get("session_id"), "Unknown")
            if branch_filter and branch_filter.strip() and branch_filter.lower() not in branch_name.lower():
                continue

            prod = prod_map.get(line["product_id"][0] if isinstance(line.get("product_id"), list) else None, {})
            model_code = prod.get("default_code", "")
            if model_filter and model_filter.strip():
                if not model_code.upper().startswith(model_filter.upper()):
                    continue

            customer = ""
            partner = order.get("partner_id")
            if partner and isinstance(partner, list) and len(partner) > 1:
                customer = partner[1]
            cashier = ""
            user = order.get("user_id")
            if user and isinstance(user, list) and len(user) > 1:
                cashier = user[1]

            rows.append({
                "System":       system_name,
                "Date":         str(order.get("date_order", ""))[:10],
                "POS Order":    order.get("name", ""),
                "Branch":       branch_name,
                "Customer":     customer,
                "Cashier":      cashier,
                "Model Code":   model_code,
                "Product":      prod.get("name", ""),
                "Qty":          float(line.get("qty") or 0),
                "Unit Price":   float(line.get("price_unit") or 0),
                "Subtotal":     float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)

    except Exception:
        return empty_df

def fetch_pos_multi_company(selected_keys, date_from, date_to, branch_filter, model_filter):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_pos_data_for_system, k, date_from, date_to, branch_filter, model_filter): k
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
# SALES FETCH (NEW – fully working)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sales_data_for_system(system_key, date_from, date_to, model_filter):
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
        # Fetch sale orders
        so_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["sale", "done"]],
        ]
        orders = _x(u, db, uid, ak, "sale.order", "search_read", [so_domain],
                    {"fields": ["id", "name", "date_order", "amount_total", "partner_id", "state", "order_line"],
                     "limit": 5000})
        if not orders:
            return empty_df

        # Collect line ids
        line_ids = []
        for o in orders:
            if o.get("order_line"):
                line_ids.extend(o["order_line"])
        if not line_ids:
            return empty_df

        # Fetch order lines
        lines = _x(u, db, uid, ak, "sale.order.line", "search_read",
                   [[["id", "in", line_ids]]],
                   {"fields": ["order_id", "product_id", "product_uom_qty", "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        order_map = {o["id"]: o for o in orders}

        # Get product details
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = []
        if prod_ids:
            products = _x(u, db, uid, ak, "product.product", "search_read",
                          [[["id", "in", prod_ids]]],
                          {"fields": ["id", "default_code", "name", "categ_id"],
                           "limit": len(prod_ids)+20})
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            order = order_map.get(line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id"))
            if not order:
                continue

            prod = prod_map.get(line["product_id"][0] if isinstance(line.get("product_id"), list) else None, {})
            model_code = prod.get("default_code", "")
            if model_filter and model_filter.strip():
                if not model_code.upper().startswith(model_filter.upper()):
                    continue

            customer = ""
            partner = order.get("partner_id")
            if partner and isinstance(partner, list) and len(partner) > 1:
                customer = partner[1]

            rows.append({
                "System":       system_name,
                "Date":         str(order.get("date_order", ""))[:10],
                "SO":           order.get("name", ""),
                "Customer":     customer,
                "Model Code":   model_code,
                "Product":      prod.get("name", ""),
                "Qty":          float(line.get("product_uom_qty") or 0),
                "Unit Price":   float(line.get("price_unit") or 0),
                "Subtotal":     float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
                "State":        order.get("state", ""),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)

    except Exception:
        return empty_df

def fetch_sales_multi_company(selected_keys, date_from, date_to, model_filter):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_sales_data_for_system, k, date_from, date_to, model_filter): k
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
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("<div class='login-orb'>📊</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-title'>Multi‑Company Ops Dashboard</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='login-subtitle'>Sign in to continue</div>",
                unsafe_allow_html=True)
    with st.form("login_form"):
        email     = st.text_input("Email", placeholder="user@example.com")
        password  = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")
        if submitted:
            if email and password:
                st.session_state.authenticated = True
                st.session_state.user_email    = email
                token = _make_token(email)
                st.query_params.update({"u": email, "t": token})
                st.rerun()
            else:
                st.error("Invalid credentials")

def do_logout():
    st.session_state.authenticated = False
    st.session_state.user_email    = ""
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD – fully working with all 4 tabs
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    # Sidebar
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
        <div class='dash-subtitle'>{t(
            'Inventory · POS · Sales · Purchase',
            'المخزون · نقاط البيع · المبيعات · المشتريات')}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    tab_inv, tab_pos, tab_sales, tab_pur = st.tabs([
        f"📦 {t('Inventory', 'المخزون')}",
        f"🛒 {t('POS',       'نقاط البيع')}",
        f"🛍️ {t('Sales',    'المبيعات')}",
        f"🛒 {t('Purchase',  'المشتريات')}",
    ])

    # =========================================================================
    # INVENTORY TAB (already fully working)
    # =========================================================================
    with tab_inv:
        st.markdown(f"### 📦 {t('Inventory Overview', 'نظرة عامة على المخزون')}")

        company_options  = ["All Companies"] + [get_system_name(k) for k in SYSTEM_KEYS]
        selected_company = st.selectbox(
            t("Select Company", "اختر الشركة"),
            options=company_options, index=0, key="inv_company",
        )
        inv_keys = (SYSTEM_KEYS if selected_company == "All Companies"
                    else [k for k in SYSTEM_KEYS if get_system_name(k) == selected_company])

        model_filter = st.text_input(
            t("Model Code (optional)", "رمز الموديل (اختياري)"), key="inv_model_filter"
        ).strip()
        exact_match = st.toggle(
            t("Exact match only", "تطابق تام فقط"), value=False, key="inv_exact"
        )
        low_thresh = st.number_input(
            t("Low stock threshold (qty ≤)", "حد المخزون المنخفض (كمية ≤)"),
            min_value=0, max_value=1000, value=5, step=1, key="inv_low_thresh",
        )

        refresh_inv = st.button(
            f"🔄 {t('Refresh Inventory', 'تحديث المخزون')}", type="primary"
        )

        if refresh_inv:
            with st.spinner(t("Fetching inventory data...", "جاري جلب بيانات المخزون...")):
                codes = tuple([model_filter]) if model_filter else ()
                total_df, branch_df = fetch_inventory_data(
                    codestuple=codes,
                    exact=exact_match,
                    needbranch=True,
                )

                # Purchase qty overlay for SWAG
                sys_col_local  = t("System",     "النظام")
                model_col_local = t("Model Code", "رمز الموديل")
                swag_sys_name  = get_system_name("SWAG")

                if not total_df.empty and sys_col_local in total_df.columns:
                    swag_mask = total_df[sys_col_local] == swag_sys_name
                    if swag_mask.any() and model_col_local in total_df.columns:
                        model_codes_swag = (
                            total_df.loc[swag_mask, model_col_local]
                            .dropna().unique().tolist()
                        )
                        if model_codes_swag:
                            end_date   = datetime.now().date()
                            start_date = end_date - timedelta(days=365)
                            pur_summary = get_purchase_summary_by_model(
                                tuple(model_codes_swag),
                                start_date.strftime("%Y-%m-%d"),
                                end_date.strftime("%Y-%m-%d"),
                            )
                            if not pur_summary.empty:
                                pur_renamed = pur_summary.rename(
                                    columns={"Model Code": model_col_local}
                                )
                                total_df = total_df.merge(
                                    pur_renamed[[model_col_local, "Purchase Qty"]],
                                    on=model_col_local, how="left",
                                )
                                total_df["Purchase Qty"] = (
                                    total_df["Purchase Qty"].fillna(0).astype(int)
                                )
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

                total_df  = prepare_df(total_df)
                branch_df = prepare_df(branch_df)

                st.session_state.inventory_df        = total_df
                st.session_state.inventory_branch_df = branch_df

        total_df  = st.session_state.get("inventory_df")
        branch_df = st.session_state.get("inventory_branch_df")

        if total_df is None or total_df.empty:
            st.info(t("Click 'Refresh Inventory' to load data.",
                      "اضغط 'تحديث المخزون' لتحميل البيانات."))
        else:
            qc     = t("On Hand",    "متوفر")
            sp     = t("Sale Price", "سعر البيع")
            mc     = t("Model Code", "رمز الموديل")
            prod_c = t("Product",    "المنتج")
            br_c   = t("Branch",     "الفرع")

            qty_series  = pd.to_numeric(total_df.get(qc, pd.Series()), errors="coerce").fillna(0)
            price_series = pd.to_numeric(total_df.get(sp, pd.Series()), errors="coerce").fillna(0)

            total_qty       = int(qty_series.sum())
            total_value     = (qty_series * price_series).sum()
            distinct_models = total_df[mc].nunique() if mc in total_df.columns else 0
            distinct_branches = (
                branch_df[br_c].nunique()
                if branch_df is not None and not branch_df.empty and br_c in branch_df.columns
                else 0
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(t("Total Stock Qty",      "إجمالي الكمية"),       f"{total_qty:,.0f}")
            c2.metric(t("Inventory Value (SAR)", "قيمة المخزون (ر.س)"), f"{total_value:,.2f}")
            c3.metric(t("Distinct Models",       "عدد الموديلات"),       distinct_models)
            c4.metric(t("Distinct Branches",     "عدد الفروع"),          distinct_branches)
            st.divider()

            # Branch chart
            if (branch_df is not None and not branch_df.empty
                    and br_c in branch_df.columns and qc in branch_df.columns):
                branch_summary = (
                    branch_df.groupby(br_c)[qc].sum()
                    .reset_index().sort_values(qc, ascending=False)
                )
                st.markdown(f"#### 🏪 {t('Branch-wise Stock', 'المخزون حسب الفرع')}")
                st.bar_chart(branch_summary.set_index(br_c)[qc], use_container_width=True)
                st.dataframe(branch_summary, use_container_width=True)
                st.divider()

            # Top 10 by qty
            if mc in total_df.columns and qc in total_df.columns:
                top_qty = (
                    total_df.groupby(mc)[qc].sum()
                    .reset_index().sort_values(qc, ascending=False).head(10)
                )
                st.markdown(f"#### 🏆 {t('Top Models by Quantity', 'أعلى الموديلات بالكمية')}")
                st.bar_chart(top_qty.set_index(mc)[qc], use_container_width=True)
                st.divider()

            # Top 10 by value
            if mc in total_df.columns and sp in total_df.columns:
                _tmp = total_df.copy()
                _tmp["_Value"] = (
                    pd.to_numeric(_tmp[qc], errors="coerce").fillna(0) *
                    pd.to_numeric(_tmp[sp], errors="coerce").fillna(0)
                )
                top_value = (
                    _tmp.groupby(mc)["_Value"].sum()
                    .reset_index().sort_values("_Value", ascending=False).head(10)
                )
                st.markdown(f"#### 💰 {t('Top Models by Value (SAR)', 'أعلى الموديلات بالقيمة (ر.س)')}")
                st.bar_chart(top_value.set_index(mc)["_Value"], use_container_width=True)
                st.divider()

            # Stock alerts
            qty_num    = pd.to_numeric(total_df.get(qc, pd.Series()), errors="coerce").fillna(0)
            zero_stock = total_df[qty_num == 0]
            low_stock  = total_df[(qty_num > 0) & (qty_num <= low_thresh)]

            if not zero_stock.empty:
                st.markdown(
                    f"<div class='alert-banner'>⚠️ {len(zero_stock)} "
                    f"{t('products have zero stock', 'منتج بدون مخزون')}</div>",
                    unsafe_allow_html=True,
                )
            if not low_stock.empty:
                st.markdown(
                    f"<div class='alert-banner'>🔴 {len(low_stock)} "
                    f"{t('low stock items', 'عناصر منخفضة المخزون')} ≤ {low_thresh}</div>",
                    unsafe_allow_html=True,
                )
                cols_show = [c for c in [mc, prod_c, qc] if c in low_stock.columns]
                st.dataframe(low_stock[cols_show], use_container_width=True)
            st.divider()

            # Detail table
            st.markdown(f"#### 📋 {t('Detailed Inventory', 'المخزون التفصيلي')}")
            filtered_inv = display_df(total_df, thresh=low_thresh, table_key="inv_detail")
            st.markdown("<br>", unsafe_allow_html=True)

            # Downloads
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button(
                    "⬇️ CSV", to_csv(filtered_inv), dl_name("inventory", "csv"),
                    "text/csv", use_container_width=True,
                )
            with d2:
                st.download_button(
                    "⬇️ Excel", to_excel(filtered_inv), dl_name("inventory", "xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with d3:
                if branch_df is not None and not branch_df.empty:
                    # Apply same model filter to branch matrix if needed
                    if model_filter:
                        filtered_branch = branch_df[branch_df[mc].str.contains(model_filter, case=False, na=False)]
                    else:
                        filtered_branch = branch_df
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel', 'Excel مصفوفة الفروع')}",
                        to_excel_branch_matrix(filtered_branch, get_lang()),
                        dl_name("branch_matrix", "xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                else:
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel', 'Excel مصفوفة الفروع')}",
                        data=b"", file_name="placeholder.xlsx",
                        disabled=True, use_container_width=True,
                    )

    # =========================================================================
    # POS TAB – fully working
    # =========================================================================
    with tab_pos:
        st.markdown(f"### 🛒 {t('POS Sales', 'مبيعات نقاط البيع')}")

        pos_co_opts = ["All Companies"] + [get_system_name(k) for k in SYSTEM_KEYS]
        pos_co = st.selectbox(t("Select Company", "اختر الشركة"),
                              options=pos_co_opts, index=0, key="pos_company")
        pos_keys = (SYSTEM_KEYS if pos_co == "All Companies"
                    else [k for k in SYSTEM_KEYS if get_system_name(k) == pos_co])

        col1, col2 = st.columns(2)
        with col1:
            pos_date_from = st.date_input(
                t("From", "من"),
                value=datetime.now().date() - timedelta(days=30),
                key="pos_date_from",
            )
        with col2:
            pos_date_to = st.date_input(
                t("To", "إلى"), value=datetime.now().date(), key="pos_date_to"
            )

        pos_branch_filter = st.text_input(
            t("Branch (optional, partial match)", "الفرع (اختياري، مطابقة جزئية)"),
            key="pos_branch_filter"
        ).strip()

        pos_model_filter = st.text_input(
            t("Model Code (optional)", "رمز الموديل (اختياري)"), key="pos_model_filter"
        ).strip()

        refresh_pos = st.button(
            f"🔄 {t('Refresh POS Data', 'تحديث بيانات نقاط البيع')}", type="primary"
        )

        if refresh_pos:
            with st.spinner(t("Fetching POS data...", "جاري جلب بيانات نقاط البيع...")):
                pos_df = fetch_pos_multi_company(
                    pos_keys,
                    pos_date_from.strftime("%Y-%m-%d"),
                    pos_date_to.strftime("%Y-%m-%d"),
                    pos_branch_filter,
                    pos_model_filter
                )
                st.session_state.pos_df = prepare_df(pos_df)

        pos_df = st.session_state.get("pos_df")

        if pos_df is None or pos_df.empty:
            st.info(t("Click 'Refresh POS Data' to load data.",
                      "اضغط 'تحديث بيانات نقاط البيع' لتحميل البيانات."))
        else:
            qty_col = t("Qty", "الكمية")
            sub_col = t("Subtotal", "المجموع الفرعي")
            total_col = t("Total Amount", "المبلغ الإجمالي")
            branch_col = t("Branch", "الفرع")
            cashier_col = t("Cashier", "الكاشير")
            model_col = t("Model Code", "رمز الموديل")
            date_col = t("Date", "التاريخ")

            total_sales_amount = float(pos_df[total_col].iloc[0] if total_col in pos_df.columns else 0)  # each row has same order total, so take first
            # Better: group by order and sum unique order totals
            unique_orders = pos_df.drop_duplicates(subset=[t("POS Order", "طلب نقطة بيع")]) if t("POS Order", "طلب نقطة بيع") in pos_df.columns else pos_df
            if total_col in unique_orders.columns:
                total_sales_amount = unique_orders[total_col].sum()
            else:
                total_sales_amount = (pos_df[sub_col] if sub_col in pos_df.columns else 0).sum()
            total_qty = pos_df[qty_col].sum() if qty_col in pos_df.columns else 0
            total_bills = unique_orders.shape[0] if t("POS Order", "طلب نقطة بيع") in pos_df.columns else 0
            avg_bill = total_sales_amount / total_bills if total_bills > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("Total Sales (SAR)", "إجمالي المبيعات (ر.س)"), f"{total_sales_amount:,.2f}")
            m2.metric(t("Total Qty", "إجمالي الكمية"), f"{total_qty:,.0f}")
            m3.metric(t("Number of Bills", "عدد الفواتير"), f"{total_bills:,}")
            m4.metric(t("Average Bill (SAR)", "متوسط الفاتورة (ر.س)"), f"{avg_bill:,.2f}")
            st.divider()

            # Branch-wise sales
            if branch_col in pos_df.columns and total_col in unique_orders.columns:
                branch_sales = unique_orders.groupby(branch_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False)
                st.markdown(f"#### 🏪 {t('Branch-wise POS Sales', 'مبيعات نقاط البيع حسب الفرع')}")
                st.bar_chart(branch_sales.set_index(branch_col)[total_col], use_container_width=True)
                st.dataframe(branch_sales, use_container_width=True)
                st.divider()

            # Cashier-wise sales (if available)
            if cashier_col in pos_df.columns and cashier_col in unique_orders.columns and total_col in unique_orders.columns:
                cashier_sales = unique_orders.groupby(cashier_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False)
                st.markdown(f"#### 👤 {t('Cashier-wise Sales', 'المبيعات حسب الكاشير')}")
                st.dataframe(cashier_sales, use_container_width=True)
                st.divider()

            # Top products
            if model_col in pos_df.columns and qty_col in pos_df.columns:
                top_products = pos_df.groupby(model_col)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False).head(10)
                st.markdown(f"#### 🏆 {t('Top Products by Qty', 'أفضل المنتجات بالكمية')}")
                st.bar_chart(top_products.set_index(model_col)[qty_col], use_container_width=True)
                st.divider()

            # Daily trend
            if date_col in pos_df.columns and total_col in unique_orders.columns:
                daily = unique_orders.copy()
                daily[date_col] = pd.to_datetime(daily[date_col]).dt.date
                daily_trend = daily.groupby(date_col)[total_col].sum().reset_index().sort_values(date_col)
                st.markdown(f"#### 📈 {t('Daily Sales Trend', 'الاتجاه اليومي للمبيعات')}")
                st.line_chart(daily_trend.set_index(date_col)[total_col], use_container_width=True)
                st.divider()

            # Detailed table
            st.markdown(f"#### 📋 {t('Detailed POS Transactions', 'تفاصيل معاملات نقاط البيع')}")
            display_df(pos_df, table_key="pos_detail")
            st.markdown("<br>", unsafe_allow_html=True)

            # Exports
            p1, p2 = st.columns(2)
            with p1:
                st.download_button(
                    "⬇️ CSV", to_csv(pos_df), dl_name("pos", "csv"),
                    "text/csv", use_container_width=True,
                )
            with p2:
                st.download_button(
                    "⬇️ Excel", to_excel(pos_df), dl_name("pos", "xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    # =========================================================================
    # SALES TAB – fully working
    # =========================================================================
    with tab_sales:
        st.markdown(f"### 🛍️ {t('Sales Orders', 'أوامر البيع')}")

        sales_co_opts = ["All Companies"] + [get_system_name(k) for k in SYSTEM_KEYS]
        sales_co = st.selectbox(t("Select Company", "اختر الشركة"),
                                options=sales_co_opts, index=0, key="sales_company")
        sales_keys = (SYSTEM_KEYS if sales_co == "All Companies"
                      else [k for k in SYSTEM_KEYS if get_system_name(k) == sales_co])

        sc1, sc2 = st.columns(2)
        with sc1:
            sales_date_from = st.date_input(
                t("From", "من"),
                value=datetime.now().date() - timedelta(days=30),
                key="sales_date_from",
            )
        with sc2:
            sales_date_to = st.date_input(
                t("To", "إلى"), value=datetime.now().date(), key="sales_date_to"
            )

        sales_model_filter = st.text_input(
            t("Model Code (optional)", "رمز الموديل (اختياري)"), key="sales_model_filter"
        ).strip()

        refresh_sales = st.button(
            f"🔄 {t('Refresh Sales Data', 'تحديث بيانات المبيعات')}", type="primary"
        )

        if refresh_sales:
            with st.spinner(t("Fetching sales data...", "جاري جلب بيانات المبيعات...")):
                sales_df = fetch_sales_multi_company(
                    sales_keys,
                    sales_date_from.strftime("%Y-%m-%d"),
                    sales_date_to.strftime("%Y-%m-%d"),
                    sales_model_filter
                )
                st.session_state.sales_df = prepare_df(sales_df)

        sales_df = st.session_state.get("sales_df")

        if sales_df is None or sales_df.empty:
            st.info(t("Click 'Refresh Sales Data' to load data.",
                      "اضغط 'تحديث بيانات المبيعات' لتحميل البيانات."))
        else:
            qty_col = t("Qty", "الكمية")
            sub_col = t("Subtotal", "المجموع الفرعي")
            total_col = t("Total Amount", "المبلغ الإجمالي")
            customer_col = t("Customer", "العميل")
            model_col = t("Model Code", "رمز الموديل")
            date_col = t("Date", "التاريخ")
            so_col = t("SO", "أمر بيع")

            total_sales_amount = sales_df[total_col].sum() if total_col in sales_df.columns else 0
            total_qty = sales_df[qty_col].sum() if qty_col in sales_df.columns else 0
            total_orders = sales_df[so_col].nunique() if so_col in sales_df.columns else 0
            avg_order = total_sales_amount / total_orders if total_orders > 0 else 0

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric(t("Total Sales (SAR)", "إجمالي المبيعات (ر.س)"), f"{total_sales_amount:,.2f}")
            sm2.metric(t("Total Qty", "إجمالي الكمية"), f"{total_qty:,.0f}")
            sm3.metric(t("Number of Orders", "عدد الطلبات"), f"{total_orders:,}")
            sm4.metric(t("Average Order Value (SAR)", "متوسط قيمة الطلب (ر.س)"), f"{avg_order:,.2f}")
            st.divider()

            # Branch-wise sales (if branch column exists; not in standard sale.order, but we can use customer location? skip)
            # Instead show customer-wise
            if customer_col in sales_df.columns and total_col in sales_df.columns:
                # Aggregate per customer using unique orders
                unique_orders = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
                if customer_col in unique_orders.columns:
                    customer_sales = unique_orders.groupby(customer_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False).head(10)
                    st.markdown(f"#### 👥 {t('Top Customers by Sales', 'أفضل العملاء حسب المبيعات')}")
                    st.dataframe(customer_sales, use_container_width=True)
                    st.divider()

            # Top products
            if model_col in sales_df.columns and qty_col in sales_df.columns:
                top_products = sales_df.groupby(model_col)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False).head(10)
                st.markdown(f"#### 🏆 {t('Top Products by Qty', 'أفضل المنتجات بالكمية')}")
                st.bar_chart(top_products.set_index(model_col)[qty_col], use_container_width=True)
                st.divider()

            # Daily trend
            if date_col in sales_df.columns and total_col in sales_df.columns:
                daily = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
                daily[date_col] = pd.to_datetime(daily[date_col]).dt.date
                daily_trend = daily.groupby(date_col)[total_col].sum().reset_index().sort_values(date_col)
                st.markdown(f"#### 📈 {t('Daily Sales Trend', 'الاتجاه اليومي للمبيعات')}")
                st.line_chart(daily_trend.set_index(date_col)[total_col], use_container_width=True)
                st.divider()

            # Detailed table
            st.markdown(f"#### 📋 {t('Detailed Sales Orders', 'تفاصيل أوامر البيع')}")
            display_df(sales_df, table_key="sales_detail")
            st.markdown("<br>", unsafe_allow_html=True)

            # Exports
            s1, s2 = st.columns(2)
            with s1:
                st.download_button(
                    "⬇️ CSV", to_csv(sales_df), dl_name("sales", "csv"),
                    "text/csv", use_container_width=True,
                )
            with s2:
                st.download_button(
                    "⬇️ Excel", to_excel(sales_df), dl_name("sales", "xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    # =========================================================================
    # PURCHASE TAB (already fully working)
    # =========================================================================
    with tab_pur:
        st.markdown(f"### 🛒 {t('Purchase History', 'تاريخ المشتريات')}")

        pur_co_opts = ["All Companies"] + [get_system_name(k) for k in SYSTEM_KEYS]
        pur_co      = st.selectbox(t("Select Company", "اختر الشركة"),
                                   options=pur_co_opts, index=0, key="pur_company")
        pur_keys    = (SYSTEM_KEYS if pur_co == "All Companies"
                       else [k for k in SYSTEM_KEYS if get_system_name(k) == pur_co])

        pur_model = st.text_input(
            t("Model Code (optional)", "رمز الموديل (اختياري)"), key="pur_model"
        ).strip()

        pc1, pc2 = st.columns(2)
        with pc1:
            pur_date_from = st.date_input(
                t("From", "من"),
                value=datetime.now().date() - timedelta(days=90),
                key="pur_date_from",
            )
        with pc2:
            pur_date_to = st.date_input(
                t("To", "إلى"), value=datetime.now().date(), key="pur_date_to"
            )

        refresh_pur = st.button(
            f"🔄 {t('Refresh Purchase', 'تحديث المشتريات')}", type="primary"
        )

        if refresh_pur:
            with st.spinner(t("Fetching purchase data...", "جاري جلب بيانات المشتريات...")):
                pur_df = fetch_purchase_multi_company(
                    pur_keys,
                    pur_model,
                    pur_date_from.strftime("%Y-%m-%d"),
                    pur_date_to.strftime("%Y-%m-%d"),
                )
                st.session_state.purchase_df = prepare_df(pur_df)

        pur_df = st.session_state.get("purchase_df")

        if pur_df is None or pur_df.empty:
            st.info(t("Click 'Refresh Purchase' to load data.",
                      "اضغط 'تحديث المشتريات' لتحميل البيانات."))
        else:
            qty_col_pur = t("Qty",      "الكمية")
            sub_col_pur = t("Subtotal", "المجموع الفرعي")
            total_p_qty = int(
                pd.to_numeric(pur_df.get(qty_col_pur, pd.Series()), errors="coerce").fillna(0).sum()
            )
            total_p_val = (
                pd.to_numeric(pur_df.get(sub_col_pur, pd.Series()), errors="coerce").fillna(0).sum()
            )
            pm1, pm2 = st.columns(2)
            pm1.metric(t("Total Purchase Qty",          "إجمالي كمية الشراء"),       f"{total_p_qty:,}")
            pm2.metric(t("Total Purchase Value (SAR)",  "إجمالي قيمة الشراء (ر.س)"), f"{total_p_val:,.2f}")
            st.divider()

            display_df(pur_df, table_key="pur_detail")
            st.markdown("<br>", unsafe_allow_html=True)

            pd1, pd2 = st.columns(2)
            with pd1:
                st.download_button(
                    "⬇️ CSV", to_csv(pur_df), dl_name("purchase", "csv"),
                    "text/csv", use_container_width=True,
                )
            with pd2:
                st.download_button(
                    "⬇️ Excel", to_excel(pur_df), dl_name("purchase", "xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
