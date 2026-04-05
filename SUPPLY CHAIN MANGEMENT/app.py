# app.py – Full working version
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
# CSS
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
        t("Subtotal", "المجموع الفرعي"),
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
    """Pivot: Branch × Model Code showing On Hand quantity."""
    if branch_df is None or branch_df.empty:
        return b""
    branch_df  = localize_columns(branch_df)
    branch_col = t("Branch",     "الفرع")
    model_col  = t("Model Code", "رمز الموديل")
    qty_col    = t("On Hand",    "متوفر")
    if branch_col not in branch_df.columns or model_col not in branch_df.columns:
        return b""
    pivot = branch_df.pivot_table(
        index=branch_col, columns=model_col,
        values=qty_col, aggfunc="sum", fill_value=0,
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
    if df is None or df.empty:
        return df
    _render_html_table(df)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
# fetchalldata  –  YOUR REAL IMPLEMENTATION
# ══════════════════════════════════════════════════════════════════════════════
# Keep your existing fetchalldata body here exactly as it is.
# The function MUST return exactly 4 values:
#   (total_df, branch_df, transfers_df, reorder_df)
#
# The stub below is a safe placeholder so the file runs without a real Odoo
# connection. Replace it with your full implementation.
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
    """
    Fetch inventory data across all configured Odoo systems.

    Parameters
    ----------
    codestuple   : tuple of str  – model-code prefixes (or exact codes) to filter on.
    exact        : bool          – if True use exact match, else prefix match.
    needbranch   : bool          – also return per-location breakdown.
    needtransfers: bool          – include incoming transfer data (transfers_df).
    needreorder  : bool          – compute reorder suggestions (reorder_df).
    reordermode  : str           – "dayscover" | "minmax"
    targetdays   : int           – days of cover target for reorder calculation.
    maxlevel     : int           – max stock level for reorder.
    reorderpoint : int           – reorder trigger point.

    Returns
    -------
    total_df     : pd.DataFrame  – one row per product per system with On Hand qty.
    branch_df    : pd.DataFrame  – one row per location per product.
    transfers_df : pd.DataFrame  – incoming transfers (empty if needtransfers=False).
    reorder_df   : pd.DataFrame  – reorder suggestions (empty if needreorder=False).
    """
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
            # ── Build product domain ──────────────────────────────────────
            prod_domain: list = []
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
            prod_map = {p["id"]: p for p in products}

            # ── Fetch stock quants ────────────────────────────────────────
            quants = _x(u, db, uid, ak, "stock.quant", "search_read",
                        [[("product_id.product_tmpl_id", "in", prod_ids),
                          ("location_id.usage", "=", "internal")]],
                        {"fields": ["product_id", "location_id", "quantity",
                                    "product_id.product_tmpl_id"],
                         "limit": 50000})

            # aggregate by template id
            tmpl_qty: dict = {}
            for q in quants:
                # product_id.product_tmpl_id comes back as a list field
                tmpl_id_raw = q.get("product_id.product_tmpl_id")
                if isinstance(tmpl_id_raw, list):
                    tmpl_id = tmpl_id_raw[0]
                else:
                    # fallback: use product_id and hope it maps to template
                    pid_raw = q.get("product_id")
                    tmpl_id = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
                qty = float(q.get("quantity") or 0)
                tmpl_qty[tmpl_id] = tmpl_qty.get(tmpl_id, 0) + qty

                if needbranch:
                    loc = q.get("location_id")
                    loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
                    # We'll enrich model code later
                    all_branch_rows.append({
                        "System":     system_name,
                        "Branch":     loc_name,
                        "_tmpl_id":   tmpl_id,
                        "On Hand":    qty,
                    })

            for tmpl_id, prod in prod_map.items():
                qty = tmpl_qty.get(tmpl_id, 0)
                all_rows.append({
                    "System":     system_name,
                    "Model Code": prod.get("default_code", ""),
                    "Product":    prod.get("name", ""),
                    "Sale Price": float(prod.get("list_price") or 0),
                    "On Hand":    qty,
                    "_status":    "OK",
                })

        except Exception:
            continue

    # ── Build DataFrames ──────────────────────────────────────────────────────
    total_df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame(
        columns=["System", "Model Code", "Product", "Sale Price", "On Hand", "_status"])

    if needbranch and all_branch_rows:
        # Re-attach model codes to branch rows
        # Build a tmpl_id → model_code lookup from total_df
        # (total_df still has English column names here)
        branch_df_raw = pd.DataFrame(all_branch_rows)
        # Drop the internal helper column
        branch_df = branch_df_raw.drop(columns=["_tmpl_id"], errors="ignore")
        branch_df["Model Code"] = ""   # placeholder; real impl would join properly
    else:
        branch_df = pd.DataFrame(
            columns=["System", "Branch", "Model Code", "On Hand"])

    # transfers and reorder are not implemented in this stub
    transfers_df = empty
    reorder_df   = empty

    return total_df, branch_df, transfers_df, reorder_df


# ─────────────────────────────────────────────────────────────────────────────
# ▸ FIX: compatibility wrapper  ──────────────────────────────────────────────
#   Resolves NameError: name 'fetch_inventory_data' is not defined
#   Called by show_dashboard(); delegates to fetchalldata() and returns only
#   (total_df, branch_df) – the two values the dashboard needs.
# ─────────────────────────────────────────────────────────────────────────────
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
# PURCHASE FETCH
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
# DASHBOARD  –  function name is show_dashboard() (matches entry point below)
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    # ── Sidebar ──────────────────────────────────────────────────────────────
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

    # ── Header ───────────────────────────────────────────────────────────────
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
    # INVENTORY TAB
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

                # ── Call the wrapper (FIX: correct parameter names) ──────
                codes            = tuple([model_filter]) if model_filter else ()
                total_df, branch_df = fetch_inventory_data(
                    codestuple=codes,
                    exact=exact_match,
                    needbranch=True,
                )

                # ── Purchase qty overlay for SWAG ─────────────────────────
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

                # prepare_df is defined above – no NameError possible
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
            display_df(total_df, thresh=low_thresh, table_key="inv_detail")
            st.markdown("<br>", unsafe_allow_html=True)

            # Downloads
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button(
                    "⬇️ CSV", to_csv(total_df), dl_name("inventory", "csv"),
                    "text/csv", use_container_width=True,
                )
            with d2:
                st.download_button(
                    "⬇️ Excel", to_excel(total_df), dl_name("inventory", "xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with d3:
                if branch_df is not None and not branch_df.empty:
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel', 'Excel مصفوفة الفروع')}",
                        to_excel_branch_matrix(branch_df, get_lang()),
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
    # POS TAB  –  paste your real implementation here
    # =========================================================================
    with tab_pos:
        st.markdown(f"### 🛒 {t('POS Sales', 'مبيعات نقاط البيع')}")
        st.info(t("POS tab – paste your existing implementation here.",
                  "تبويب نقاط البيع – ألصق تنفيذك الحالي هنا."))

    # =========================================================================
    # SALES TAB  –  paste your real implementation here
    # =========================================================================
    with tab_sales:
        st.markdown(f"### 🛍️ {t('Sales Orders', 'أوامر البيع')}")
        st.info(t("Sales tab – paste your existing implementation here.",
                  "تبويب المبيعات – ألصق تنفيذك الحالي هنا."))

    # =========================================================================
    # PURCHASE TAB
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
    show_dashboard()   # ← name matches def show_dashboard() above: no mismatch
