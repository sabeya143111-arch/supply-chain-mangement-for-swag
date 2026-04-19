"""
SWAG Product Sync — Standalone App (Light Theme)
Copy products from SWAG to any target company (La Rouche, Fashion Limits, Different Clothes)
Parallel creation + smart error handling + advanced UI/animations
"""

import io
import re
import hashlib
import time
import xmlrpc.client
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SWAG Product Sync",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CSS (Light Theme – clean white/indigo) with added animations
# -----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
*,html,body,[class*="css"]{font-family:'IBM Plex Sans Arabic',sans-serif;box-sizing:border-box;}
.stApp{background:#f0f2f6;min-height:100vh;}
section[data-testid="stSidebar"]{background:#ffffff!important;border-right:1px solid #e0e7ff;}
section[data-testid="stSidebar"] *,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] div{color:#1e1b4b!important;}
section[data-testid="stSidebar"] input{color:#1e1b4b!important;}
@keyframes fadeInUp{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeInDown{from{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeInLeft{from{opacity:0;transform:translateX(-30px)}to{opacity:1;transform:translateX(0)}}
@keyframes shake{0%,100%{transform:translateX(0)}10%,30%,50%,70%,90%{transform:translateX(-5px)}20%,40%,60%,80%{transform:translateX(5px)}}
@keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 #6366f144}50%{box-shadow:0 0 20px 8px #8b5cf622}}
@keyframes glow{0%,100%{text-shadow:0 0 10px #6366f188}50%{text-shadow:0 0 30px #8b5cf6cc,0 0 60px #6366f188}}
@keyframes slideInLeft{from{opacity:0;transform:translateX(-40px)}to{opacity:1;transform:translateX(0)}}
@keyframes slideInRight{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}
@keyframes bounceIn{0%{transform:scale(0.2) rotate(-10deg);opacity:0}60%{transform:scale(1.2) rotate(5deg);opacity:1}80%{transform:scale(0.9)}100%{transform:scale(1);opacity:1}}
@keyframes countUp{from{opacity:0;transform:scale(0.5)}to{opacity:1;transform:scale(1)}}
@keyframes btnShine{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes borderGlow{0%,100%{border-color:#6366f1;box-shadow:0 0 5px #6366f144}50%{border-color:#8b5cf6;box-shadow:0 0 15px #8b5cf666}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.login-orb{width:120px;height:120px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6,#a78bfa);display:flex;align-items:center;justify-content:center;font-size:3rem;margin:0 auto 20px;animation:float 3s ease-in-out infinite,bounceIn 1s ease forwards;box-shadow:0 8px 40px #6366f166,0 0 60px #a78bfa33;}
.login-title{font-size:2.4rem;font-weight:700;background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1);background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s linear infinite,fadeInDown 0.8s ease forwards;text-align:center;margin-bottom:6px;}
.login-subtitle{color:#4b5563!important;font-size:0.95rem;text-align:center;animation:fadeInUp 1s ease forwards;margin-bottom:28px;}
.login-card{background:#ffffff;border:1px solid #e0e7ff;border-radius:20px;padding:32px 36px;width:100%;animation:fadeInUp 0.9s ease forwards,pulse 3s infinite;}
.welcome-banner{background:#eef2ff;border:1px solid #c7d2fe;border-radius:12px;padding:14px 20px;text-align:center;margin-bottom:20px;font-size:0.95rem;color:#4f46e5!important;animation:fadeInDown 0.7s ease forwards,borderGlow 3s infinite;}
.stTextInput input,.stNumberInput input,.stTextArea textarea{background:#ffffff!important;border:1px solid #c7d2fe!important;border-radius:10px!important;color:#1e1b4b!important;caret-color:#6366f1!important;transition:all 0.2s ease!important;}
.stTextInput input::placeholder,.stNumberInput input::placeholder,.stTextArea textarea::placeholder{color:#9ca3af!important;}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:#6366f1!important;box-shadow:0 0 0 3px #6366f133!important;background:#ffffff!important;}
.stTextInput label,.stNumberInput label,.stTextArea label{color:#374151!important;font-weight:600!important;}
.stFormSubmitButton button,.stButton button[kind="primary"]{background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1)!important;background-size:300% auto!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important;font-size:1rem!important;padding:12px!important;animation:btnShine 3s linear infinite!important;transition:transform 0.2s,box-shadow 0.2s!important;box-shadow:0 4px 20px #6366f155!important;}
.stFormSubmitButton button:hover,.stButton button[kind="primary"]:hover{transform:translateY(-2px) scale(1.02)!important;box-shadow:0 8px 30px #8b5cf699!important;}
.stButton button[kind="secondary"]{background:#ffffff!important;border:1px solid #c7d2fe!important;color:#4f46e5!important;border-radius:10px!important;transition:all 0.2s ease!important;}
.stButton button[kind="secondary"]:hover{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;transform:translateY(-2px);box-shadow:0 4px 12px #6366f144;}
.stButton button{color:#4f46e5!important;transition:all 0.2s ease!important;}
.stDownloadButton button{background:#ffffff!important;border:1px solid #c7d2fe!important;border-radius:10px!important;color:#4f46e5!important;font-size:0.78rem!important;font-weight:600!important;padding:6px 14px!important;transition:all 0.2s ease!important;box-shadow:0 2px 8px #00000022!important;}
.stDownloadButton button:hover{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;border-color:transparent!important;transform:translateY(-2px) scale(1.04)!important;box-shadow:0 6px 20px #6366f155!important;}
[data-testid="stMetric"]{background:#ffffff!important;border:1px solid #e0e7ff!important;border-radius:16px!important;padding:16px 20px!important;animation:countUp 0.6s ease forwards, fadeInUp 0.5s ease;transition:transform 0.2s,box-shadow 0.2s!important;}
[data-testid="stMetric"]:hover{transform:translateY(-4px);box-shadow:0 8px 30px #6366f144;}
[data-testid="stMetricLabel"]{color:#6b7280!important;font-size:0.82rem!important;}
[data-testid="stMetricValue"]{font-size:1.7rem!important;font-weight:700!important;background:linear-gradient(90deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.info-banner{background:#eef2ff;border-left:4px solid #6366f1;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#1e3a8a!important;animation:slideInLeft 0.4s ease;}
.warn-banner{background:#fffbeb;border-left:4px solid #f59e0b;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#92400e!important;}
.alert-banner{background:#fef2f2;border-left:4px solid #f43f5e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#991b1b!important;animation:pulse 2s infinite;}
.ok-banner{background:#ecfdf5;border-left:4px solid #22c55e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#065f46!important;animation:slideInDown 0.5s ease;}
.snap-card{background:#ffffff;border:1px solid #e0e7ff;border-radius:14px;padding:16px 20px;font-size:0.87rem;color:#1e1b4b!important;line-height:2;animation:slideInRight 0.5s ease;box-shadow:0 4px 20px #00000022;transition:transform 0.2s;}
.snap-card:hover{transform:translateY(-3px);}
.snap-card b{color:#4f46e5!important;}
.stRadio label,.stRadio div[role="radiogroup"] label span,[data-testid="stToggle"] label,.stCheckbox label{color:#1e1b4b!important;}
div[data-testid="stRadio"] p{color:#1e1b4b!important;}
h1,h2,h3,h4,h5,h6{color:#1e1b4b!important;}
.stMarkdown p,.stMarkdown li{color:#374151!important;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#9ca3af!important;}
.stAlert p{color:#1e1b4b!important;font-weight:600;}
[data-testid="stExpander"]{background:#ffffff!important;border:1px solid #e0e7ff!important;border-radius:12px!important;transition:all 0.2s;}
[data-testid="stExpander"]:hover{border-color:#c7d2fe;box-shadow:0 2px 8px #6366f122;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:#1e1b4b!important;}
[data-testid="stFileUploader"]{background:#ffffff!important;border:2px dashed #c7d2fe!important;border-radius:14px!important;transition:all 0.2s;}
[data-testid="stFileUploader"]:hover{border-color:#6366f1;background:#f8fafc;}
[data-testid="stFileUploader"] p,[data-testid="stFileUploader"] span{color:#4b5563!important;}
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,#c7d2fe,transparent)!important;margin:16px 0!important;}
[data-testid="stProgressBar"]>div{background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1)!important;background-size:300% auto!important;border-radius:10px!important;animation:shimmer 2s linear infinite!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#f0f2f6;}
::-webkit-scrollbar-thumb{background:#c7d2fe;border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:#8b5cf6;}
.stNumberInput button{color:#4f46e5!important;background:#ffffff!important;transition:0.2s;}
.stNumberInput button:hover{background:#eef2ff!important;}
.mono{font-family:'IBM Plex Mono',monospace;font-size:0.82rem;color:#4b5563;}
footer{visibility:hidden;}
[data-baseweb="tag"]{background:#e0e7ff!important;color:#4f46e5!important;}
[data-baseweb="select"] div{background:#ffffff!important;color:#1e1b4b!important;border-color:#c7d2fe!important;}
.error-card{background:#fef2f2;border-left:4px solid #dc2626;border-radius:10px;padding:12px 16px;margin:8px 0;font-size:0.85rem;color:#7f1d1d;font-family:monospace;animation:shake 0.4s ease;transition:all 0.2s;}
.error-card strong{color:#b91c1c;}
.error-card:hover{transform:translateX(4px);}
.step-circle{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border-radius:50%;font-weight:bold;margin-right:12px;box-shadow:0 2px 8px #6366f144;}
.section-header{display:flex;align-items:center;margin:20px 0 16px 0;}
.section-header h3{margin:0;color:#1e1b4b;}
.gradient-divider{height:3px;background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa);border-radius:3px;margin:20px 0;}
.empty-state{text-align:center;padding:40px;color:#9ca3af;font-size:1rem;}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Logo at the very top
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", width=220)
st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Initialize session state
# -----------------------------------------------------------------------------
if "sync_history" not in st.session_state:
    st.session_state.sync_history = []
if "check_results" not in st.session_state:
    st.session_state.check_results = None
if "missing_products_data" not in st.session_state:
    st.session_state.missing_products_data = None
if "retry_counts" not in st.session_state:
    st.session_state.retry_counts = {}  # code -> attempts
if "last_sync_time" not in st.session_state:
    st.session_state.last_sync_time = None


# -----------------------------------------------------------------------------
# XML‑RPC helpers
# -----------------------------------------------------------------------------
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


def call_with_retry(func, *args, retries=5, delay=4, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
    return None


# -----------------------------------------------------------------------------
# PDF parsing (same as original)
# -----------------------------------------------------------------------------
_RE_BRACKET = re.compile(r'\[([A-Za-z0-9\-_()]{3,30})\]')
_RE_SR_LINE = re.compile(
    r'(?:^|\s)([A-Z]{2,6}\d+(?:-\d+)?(?:-[A-Z0-9()]{1,10})?)\s+.{0,80}?\d+\.?\d*\s+SR',
    re.MULTILINE)
_RE_GENERAL = re.compile(
    r'\b([A-Z]{2,6}\d+(?:-\d+)?(?:-[A-Z0-9]{1,4})?(?:\([^)]{1,15}\))?)\b')
_EXCLUDE = frozenset([
    'SR','VAT','TAX','PCS','QTY','NO','REF','INV','PO','SO',
    'DO','ID','EN','AR','PDF','AED','SAR','USD','KWD','OMR',
    'BHD','JOD','EGP','TRY'
])

def _valid(code):
    c = code.strip().upper()
    return (bool(re.search(r'[A-Z]', c)) and bool(re.search(r'\d', c))
            and 4 <= len(c) <= 25 and c not in _EXCLUDE)

@st.cache_data(show_spinner=False)
def parse_invoice_pdf_cached(file_bytes):
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    text = ""
    for page in PdfReader(io.BytesIO(file_bytes)).pages:
        text += (page.extract_text() or "") + "\n"
    if not text.strip():
        return []
    raw = (_RE_BRACKET.findall(text)
           + [m.group(1) for m in _RE_SR_LINE.finditer(text)]
           + _RE_GENERAL.findall(text))
    seen, out = set(), []
    seq = 1
    for c in raw:
        u = c.strip().upper()
        if _valid(u) and u not in seen:
            seen.add(u)
            out.append({"sequence": seq, "code": u})
            seq += 1
    return out


# -----------------------------------------------------------------------------
# get_or_create helpers for category, brand, season
# -----------------------------------------------------------------------------
def get_or_create_category(target_cfg, category_name):
    if not category_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    domain = [["name", "=", category_name]]
    ids = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.category", "search", [domain], {"limit": 1}
    )
    if ids:
        return ids[0]
    new_id = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.category", "create", [{"name": category_name}], {}
    )
    return new_id

def get_or_create_brand(target_cfg, brand_name):
    if not brand_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    try:
        domain = [["name", "=", brand_name]]
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.brand", "search", [domain], {"limit": 1}
        )
        if ids:
            return ids[0]
        new_id = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.brand", "create", [{"name": brand_name}], {}
        )
        return new_id
    except Exception:
        return None

def get_or_create_season(target_cfg, season_name):
    if not season_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    try:
        domain = [["name", "=", season_name]]
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.season", "search", [domain], {"limit": 1}
        )
        if ids:
            return ids[0]
        new_id = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.season", "create", [{"name": season_name}], {}
        )
        return new_id
    except Exception:
        return None


def fetch_product_from_swag(default_code):
    """Retrieve full product details from SWAG by default_code."""
    cfg = st.secrets["SWAG"]
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return None
    domain = [["default_code", "=", default_code]]
    fields = [
        "name", "default_code", "categ_id", "brand_id", "season_id",
        "barcode", "type", "standard_price", "list_price", "compare_list_price"
    ]
    products = call_with_retry(
        _x, cfg["url"], cfg["db"], uid, cfg["api_key"],
        "product.product", "search_read", [domain], {"fields": fields, "limit": 1}
    )
    if not products:
        return None
    prod = products[0]
    # resolve names
    categ_name = None
    if prod.get("categ_id"):
        if isinstance(prod["categ_id"], list):
            categ_name = prod["categ_id"][1]
        else:
            categ_name = str(prod["categ_id"])
    brand_name = None
    if prod.get("brand_id"):
        if isinstance(prod["brand_id"], list):
            brand_name = prod["brand_id"][1]
        else:
            brand_name = str(prod["brand_id"])
    season_name = None
    if prod.get("season_id"):
        if isinstance(prod["season_id"], list):
            season_name = prod["season_id"][1]
        else:
            season_name = str(prod["season_id"])
    return {
        "name": prod.get("name", ""),
        "default_code": prod.get("default_code", ""),
        "categ_name": categ_name,
        "brand_name": brand_name,
        "season_name": season_name,
        "barcode": prod.get("barcode", ""),
        "type": prod.get("type", "product"),
        "standard_price": float(prod.get("standard_price") or 0.0),
        "list_price": float(prod.get("list_price") or 0.0),
        "compare_list_price": float(prod.get("compare_list_price") or 0.0),
    }


def create_product_in_target(target_cfg, swag_product):
    """Create a product in target company using SWAG product data."""
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        raise Exception("Authentication failed for target company")
    categ_id = get_or_create_category(target_cfg, swag_product["categ_name"]) if swag_product["categ_name"] else None
    brand_id = get_or_create_brand(target_cfg, swag_product["brand_name"]) if swag_product["brand_name"] else None
    season_id = get_or_create_season(target_cfg, swag_product["season_name"]) if swag_product["season_name"] else None
    vals = {
        "name": swag_product["name"],
        "default_code": swag_product["default_code"],
        "barcode": swag_product["barcode"],
        "type": swag_product["type"],
        "standard_price": swag_product["standard_price"],
        "list_price": swag_product.get("compare_list_price") or swag_product.get("list_price") or 0.0,
    }
    if categ_id:
        vals["categ_id"] = categ_id
    if brand_id:
        vals["brand_id"] = brand_id
    if season_id:
        vals["season_id"] = season_id
    new_id = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.product", "create", [vals], {}
    )
    return new_id


# -----------------------------------------------------------------------------
# Smart error parser
# -----------------------------------------------------------------------------
def parse_odoo_error(e):
    """Extract human-readable error from Odoo XML-RPC exception."""
    error_str = str(e)
    if hasattr(e, 'faultString'):
        error_str = e.faultString
    elif isinstance(e, xmlrpc.client.Fault):
        error_str = e.faultString
    
    if "Access denied" in error_str or "AccessError" in error_str:
        return "Access Denied — You don't have permission to create products."
    if "ValidationError" in error_str:
        if "barcode" in error_str.lower():
            return "Validation error on field 'barcode' — value must be unique."
        if "default_code" in error_str.lower():
            return "Validation error on field 'default_code' — possibly duplicate or invalid format."
        if "name" in error_str.lower():
            return "Validation error on field 'name' — missing or invalid."
        return f"Validation Error: {error_str[:200]}"
    if "unique constraint" in error_str.lower():
        return "Unique constraint violation — this product code already exists."
    if "required field" in error_str.lower():
        match = re.search(r"required field[:\s]+([\w_]+)", error_str, re.I)
        field = match.group(1) if match else "unknown"
        return f"Missing required field: '{field}'."
    if "Many2one" in error_str or "Invalid field" in error_str:
        match = re.search(r"field[:\s]+([\w_]+)", error_str, re.I)
        field = match.group(1) if match else "unknown"
        return f"Incompatible or invalid field: '{field}'. Check that the related record exists."
    if "xmlrpc.client.Fault" in error_str:
        return f"XML-RPC Fault: {error_str[:300]}"
    return error_str[:500]


# -----------------------------------------------------------------------------
# Batch check (one API call per company)
# -----------------------------------------------------------------------------
def batch_check_products(codes, target_cfg):
    """Check existence in target company and fetch SWAG product names in batch."""
    # 1. Target company: search all at once
    uid_target = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    existing_map = {code: False for code in codes}
    if uid_target:
        domain = [["default_code", "in", codes]]
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
            "product.product", "search", [domain], {"limit": len(codes)}
        )
        if ids:
            # fetch codes of found products
            products = call_with_retry(
                _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
                "product.product", "search_read", [domain], {"fields": ["default_code"], "limit": len(codes)}
            )
            for p in products:
                existing_map[p["default_code"]] = True
    
    # 2. SWAG: fetch names and existence
    swag_cfg = st.secrets["SWAG"]
    uid_swag = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
    swag_exists = {code: False for code in codes}
    product_names = {code: code for code in codes}
    if uid_swag:
        domain = [["default_code", "in", codes]]
        products = call_with_retry(
            _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
            "product.product", "search_read", [domain], {"fields": ["default_code", "name"], "limit": len(codes)}
        )
        for p in products:
            code = p["default_code"]
            swag_exists[code] = True
            product_names[code] = p.get("name", code)
    
    # Build results
    results = []
    for code in codes:
        if not swag_exists[code]:
            status = "not_in_swag"
        elif existing_map[code]:
            status = "exists"
        else:
            status = "missing"
        results.append({
            "code": code,
            "name": product_names[code],
            "status": status
        })
    return results


# -----------------------------------------------------------------------------
# Main UI
# -----------------------------------------------------------------------------

# Sidebar: Sync History
with st.sidebar:
    st.markdown("### 📜 Sync History")
    if st.session_state.sync_history:
        for idx, entry in enumerate(st.session_state.sync_history[-5:][::-1]):
            with st.expander(f"{entry['timestamp']} — {entry['company']}"):
                st.markdown(f"**Total:** {entry['total']}")
                st.markdown(f"✅ Created: {entry['created']}")
                st.markdown(f"⚠️ Skipped: {entry['skipped']}")
                st.markdown(f"❌ Failed: {entry['errors']}")
                if entry.get('retried'):
                    st.caption(f"🔄 Retried: {entry['retried']}")
    else:
        st.caption("No sync operations yet.")

st.markdown("---")

# Step 1: Company selector
st.markdown('<div class="section-header"><span class="step-circle">1</span><h3>Target Company</h3></div>', unsafe_allow_html=True)
company_map = {
    "La Rouche": "LAROUCHE",
    "Fashion Limits": "FASHION_LIMITS",
    "Different Clothes": "DIFFC"
}
selected_company_label = st.selectbox(
    "🎯 Target Company",
    list(company_map.keys()),
    key="sync_company",
    help="Select the Odoo company where products will be created."
)
target_key = company_map[selected_company_label]
target_cfg = st.secrets.get(target_key)
if not target_cfg:
    st.error(f"❌ Secrets missing for {selected_company_label}. Check your secrets.toml file.")
    st.stop()

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# Step 2: Input method
st.markdown('<div class="section-header"><span class="step-circle">2</span><h3>Product Codes Input</h3></div>', unsafe_allow_html=True)
input_method = st.radio(
    "Input method",
    ["Manual entry", "Upload PDF invoice"],
    horizontal=True,
    key="sync_method",
    help="Manually enter codes or extract from a PDF invoice."
)

codes = []
if input_method == "Manual entry":
    raw_codes = st.text_area(
        "Enter product codes (one per line)",
        height=150,
        placeholder="XP6013\nRVT196\nABC123",
        key="sync_manual_codes"
    )
    codes = [c.strip() for c in raw_codes.splitlines() if c.strip()]
else:
    pdf_file = st.file_uploader(
        "Upload PDF invoice",
        type=["pdf"],
        key="sync_pdf",
        help="Upload a PDF invoice to automatically extract product codes."
    )
    if pdf_file:
        with st.spinner("Parsing PDF..."):
            parsed = parse_invoice_pdf_cached(pdf_file.read())
        if parsed:
            codes = list(dict.fromkeys([item["code"] for item in parsed]))
            st.success(f"✅ {len(codes)} unique codes extracted.")
        else:
            st.warning("No codes found in PDF.")

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# Step 3: Check button
if st.button("🔍 Check Products", type="primary", use_container_width=False, key="sync_check", help="Check which codes exist or are missing in the target company."):
    if not codes:
        st.warning("Please enter at least one product code.")
    else:
        with st.spinner("Checking codes in batch..."):
            check_results = batch_check_products(codes, target_cfg)
            st.session_state.check_results = check_results
            
            # Prepare missing products data for preview
            missing_list = [r for r in check_results if r["status"] == "missing"]
            missing_products_data = []
            for r in missing_list:
                # fetch extra details from SWAG (categ, brand)
                swag_prod = fetch_product_from_swag(r["code"])
                missing_products_data.append({
                    "code": r["code"],
                    "name": r["name"],
                    "category": swag_prod["categ_name"] if swag_prod else "—",
                    "brand": swag_prod["brand_name"] if swag_prod else "—",
                })
            st.session_state.missing_products_data = missing_products_data

# Display check results if available
if st.session_state.check_results:
    results = st.session_state.check_results
    total = len(results)
    exists = sum(1 for r in results if r["status"] == "exists")
    missing = sum(1 for r in results if r["status"] == "missing")
    not_in_swag = sum(1 for r in results if r["status"] == "not_in_swag")
    
    # Animated stats cards
    st.markdown("### 📊 Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Total Codes", total)
    with col2:
        st.metric("✅ Already Exists", exists)
    with col3:
        st.metric("❌ Missing", missing)
    with col4:
        st.metric("⚠️ Not in SWAG", not_in_swag)
    
    st.markdown("---")
    
    # Preview table for missing products (if any)
    if missing > 0 and st.session_state.missing_products_data:
        st.markdown("### 📋 Products to Create")
        df_missing = pd.DataFrame(st.session_state.missing_products_data)
        df_missing.insert(0, "Select", True)
        edited_df = st.data_editor(
            df_missing,
            column_config={"Select": st.column_config.CheckboxColumn("Create?", default=True)},
            disabled=["code", "name", "category", "brand"],
            hide_index=True,
            use_container_width=True
        )
        selected_codes = edited_df[edited_df["Select"]]["code"].tolist()
        
        if st.button("➕ Create Selected Products", type="primary", key="create_selected", help="Create only the selected products in the target company."):
            if not selected_codes:
                st.warning("No products selected for creation.")
            else:
                # Prepare creation list
                to_create = [r for r in st.session_state.missing_products_data if r["code"] in selected_codes]
                total_to_create = len(to_create)
                progress_bar = st.progress(0, text="Starting parallel creation...")
                status_text = st.empty()
                errors_container = st.container()
                results_created = []  # store results for summary
                
                start_time = time.time()
                completed = 0
                
                def create_one(product_info):
                    code = product_info["code"]
                    try:
                        swag_prod = fetch_product_from_swag(code)
                        if not swag_prod:
                            return {"code": code, "name": product_info["name"], "status": "skipped", "reason": "Product not found in SWAG", "new_id": None}
                        new_id = create_product_in_target(target_cfg, swag_prod)
                        return {"code": code, "name": product_info["name"], "status": "created", "reason": "", "new_id": new_id}
                    except Exception as e:
                        error_msg = parse_odoo_error(e)
                        return {"code": code, "name": product_info["name"], "status": "error", "reason": error_msg, "raw_error": str(e), "new_id": None}
                
                # Parallel execution
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_info = {executor.submit(create_one, info): info for info in to_create}
                    for future in as_completed(future_to_info):
                        result = future.result()
                        results_created.append(result)
                        completed += 1
                        elapsed = time.time() - start_time
                        eta = (elapsed / completed) * (total_to_create - completed) if completed > 0 else 0
                        eta_str = f"{int(eta//60)}m {int(eta%60)}s" if eta < 3600 else f"{eta/60:.1f}m"
                        percent = int(completed / total_to_create * 100)
                        progress_bar.progress(completed / total_to_create, text=f"⚡ Creating {completed} / {total_to_create} ({percent}%) — ETA: {eta_str}")
                        current_product = result["code"]
                        status_text.markdown(f"🔄 **Currently creating:** {current_product}")
                        
                        if result["status"] == "error":
                            with errors_container:
                                st.markdown(
                                    f"""<div class='error-card'>
                                    <strong>❌ {result['code']}</strong><br>
                                    <strong>📋 Name:</strong> {result['name']}<br>
                                    <strong>⚠️ Reason:</strong> {result['reason']}<br>
                                    <strong>🔍 Raw:</strong> {result.get('raw_error', '')[:200]}...
                                    </div>""",
                                    unsafe_allow_html=True
                                )
                
                progress_bar.empty()
                status_text.empty()
                
                # Compile statistics
                created = sum(1 for r in results_created if r["status"] == "created")
                skipped = sum(1 for r in results_created if r["status"] == "skipped")
                errors = sum(1 for r in results_created if r["status"] == "error")
                
                # Success banner and confetti
                if errors == 0:
                    st.balloons()
                    st.markdown('<div class="ok-banner">🎉 All products created successfully! 🎉</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-banner">⚠️ Completed with {errors} errors. See details below.</div>', unsafe_allow_html=True)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("✅ Created", created)
                col2.metric("⚠️ Skipped", skipped)
                col3.metric("❌ Failed", errors)
                
                # Download buttons
                success_list = [{"Code": r["code"], "Name": r["name"], "New ID": r["new_id"]} for r in results_created if r["status"] == "created"]
                failed_list = [{"Code": r["code"], "Name": r["name"], "Error Reason": r["reason"]} for r in results_created if r["status"] == "error"]
                
                if success_list:
                    df_success = pd.DataFrame(success_list)
                    csv_success = df_success.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("⬇️ Download Success List (CSV)", csv_success, f"success_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv", use_container_width=False)
                if failed_list:
                    df_failed = pd.DataFrame(failed_list)
                    csv_failed = df_failed.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("⬇️ Download Failed List (CSV)", csv_failed, f"failed_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv", use_container_width=False)
                
                # Retry failed button
                if errors > 0:
                    if st.button("🔄 Retry Failed", type="secondary", key="retry_failed"):
                        # Increment retry counts
                        for r in results_created:
                            if r["status"] == "error":
                                st.session_state.retry_counts[r["code"]] = st.session_state.retry_counts.get(r["code"], 0) + 1
                        # Filter products with less than 2 retries
                        to_retry = [r for r in results_created if r["status"] == "error" and st.session_state.retry_counts.get(r["code"], 0) <= 2]
                        if not to_retry:
                            st.info("No products eligible for retry (max 2 attempts already reached).")
                        else:
                            st.session_state.missing_products_data = [{"code": r["code"], "name": r["name"], "category": "", "brand": ""} for r in to_retry]
                            st.experimental_rerun()
                
                # Save to history
                st.session_state.sync_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "company": selected_company_label,
                    "total": total_to_create,
                    "created": created,
                    "skipped": skipped,
                    "errors": errors,
                    "retried": len([r for r in results_created if r["status"] == "error" and st.session_state.retry_counts.get(r["code"], 0) > 0])
                })
                
                # Clear session state after completion (optional)
                st.session_state.check_results = None
                st.session_state.missing_products_data = None
                st.rerun()
    else:
        if missing == 0:
            st.info("✨ All codes already exist in the target company. Nothing to create.")
        elif not st.session_state.missing_products_data:
            st.info("No missing products found.")

# If no missing products after check, show empty state
elif st.session_state.check_results and sum(1 for r in st.session_state.check_results if r["status"] == "missing") == 0:
    st.markdown('<div class="empty-state">✨ All products already exist — no action needed.</div>', unsafe_allow_html=True)
