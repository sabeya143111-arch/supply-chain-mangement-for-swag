"""
SWAG Product Sync — Standalone App (Light Theme)
Copy products from SWAG to any target company (La Rouche, Fashion Limits, Different Clothes)
MAXIMUM SPEED: batch API calls + parallel creation + bulk fetch
+ FULL SCAN MODE: find all missing products in one click
"""

import io
import os
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
# CSS — New editorial style (black/white/red, Space Grotesk + Inter)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f5f5f0;
    min-height: 100vh;
}

/* Sidebar — dark navy/black */
section[data-testid="stSidebar"] {
    background: #1a1a1a !important;
    border-right: none;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] input {
    background: #2a2a2a !important;
    color: #ffffff !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #1a1a1a;
}

/* Body text */
p, li, .stMarkdown, .stTextInput label, .stNumberInput label, .stTextArea label {
    color: #333333;
}

/* Primary buttons */
.stButton button[kind="primary"], .stFormSubmitButton button {
    background: #1a1a1a !important;
    color: white !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button:hover {
    background: #E63946 !important;
    transform: translateY(-2px);
}

/* Secondary buttons */
.stButton button[kind="secondary"] {
    background: transparent !important;
    border: 2px solid #1a1a1a !important;
    color: #1a1a1a !important;
    border-radius: 0 !important;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    text-transform: uppercase;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}
.stButton button[kind="secondary"]:hover {
    background: #1a1a1a !important;
    color: white !important;
    transform: translateY(-2px);
}

/* Download buttons */
.stDownloadButton button {
    background: transparent !important;
    border: 2px solid #1a1a1a !important;
    color: #1a1a1a !important;
    border-radius: 0 !important;
    font-weight: 600;
    font-size: 0.8rem;
    padding: 6px 16px !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton button:hover {
    background: #1a1a1a !important;
    color: white !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 0 !important;
    padding: 20px 16px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}
[data-testid="stMetricLabel"] {
    color: #555555 !important;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}
[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #1a1a1a !important;
    background: none !important;
    -webkit-text-fill-color: #1a1a1a !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 2px solid #e0e0e0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #555555 !important;
    border-radius: 0 !important;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.85rem;
    padding: 10px 24px !important;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    color: #E63946 !important;
    border-bottom: 3px solid #E63946 !important;
    background: transparent !important;
    box-shadow: none !important;
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #ffffff !important;
    border: 1px solid #d0d0d0 !important;
    border-radius: 0 !important;
    color: #1a1a1a !important;
    font-family: 'Inter', sans-serif;
    padding: 10px 12px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #E63946 !important;
    box-shadow: 0 0 0 2px rgba(230,57,70,0.2) !important;
}
.stTextInput label, .stNumberInput label, .stTextArea label {
    font-weight: 600;
    color: #1a1a1a;
}

/* Radio, Checkbox, Toggle */
.stRadio label, .stCheckbox label, [data-testid="stToggle"] label {
    color: #1a1a1a !important;
    font-weight: 500;
}

/* Banners */
.info-banner {
    background: #eef2ff;
    border-left: 4px solid #E63946;
    border-radius: 0;
    padding: 12px 16px;
    margin: 12px 0;
    color: #1e3a8a;
}
.warn-banner {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    border-radius: 0;
    padding: 12px 16px;
    margin: 12px 0;
    color: #92400e;
}
.alert-banner {
    background: #fef2f2;
    border-left: 4px solid #E63946;
    border-radius: 0;
    padding: 12px 16px;
    margin: 12px 0;
    color: #991b1b;
    animation: pulse 2s infinite;
}
.ok-banner {
    background: #ecfdf5;
    border-left: 4px solid #22c55e;
    border-radius: 0;
    padding: 12px 16px;
    margin: 12px 0;
    color: #065f46;
}

/* Tables (dataframe) */
.dataframe {
    font-family: 'Inter', monospace;
    border-collapse: collapse;
    width: 100%;
}
.dataframe thead tr th {
    background: #1a1a1a;
    color: white;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    padding: 12px;
    border: none;
}
.dataframe tbody tr:nth-child(even) {
    background: #fafaf5;
}
.dataframe tbody tr:hover {
    background: #fff0f0;
}

/* Progress bar */
[data-testid="stProgressBar"] > div {
    background: #E63946 !important;
    border-radius: 0 !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 0 !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 2px dashed #d0d0d0 !important;
    border-radius: 0 !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #E63946 !important;
}

/* Dividers */
hr {
    border: none !important;
    height: 1px !important;
    background: #e0e0e0 !important;
    margin: 24px 0 !important;
}

/* Error cards */
.error-card {
    background: #fef2f2;
    border-left: 4px solid #E63946;
    border-radius: 0;
    padding: 12px 16px;
    margin: 8px 0;
    font-family: 'Inter', monospace;
    font-size: 0.85rem;
    color: #7f1d1d;
}
.error-card strong {
    color: #b91c1c;
}

/* Step circles */
.step-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: #1a1a1a;
    color: white;
    border-radius: 50%;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    margin-right: 12px;
}
.section-header {
    display: flex;
    align-items: center;
    margin: 20px 0 16px;
}
.section-header h3 {
    margin: 0;
    font-weight: 800;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px;
    color: #888888;
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
}

/* Login card */
.login-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 0;
    padding: 32px 36px;
    width: 100%;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.login-orb {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: #1a1a1a;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    margin: 0 auto 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}
.login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1a1a1a, #E63946);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 6px;
}
.login-subtitle {
    color: #555555;
    font-size: 0.95rem;
    text-align: center;
    margin-bottom: 28px;
}
.welcome-banner {
    background: #f5f5f0;
    border: 1px solid #e0e0e0;
    border-radius: 0;
    padding: 14px 20px;
    text-align: center;
    margin-bottom: 20px;
    color: #1a1a1a;
}

/* Badges */
.badge-ok {
    background: #ecfdf5;
    color: #065f46;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-off {
    background: #fef2f2;
    color: #991b1b;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-err {
    background: #fffbeb;
    color: #92400e;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
}

/* Snap card */
.snap-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 0;
    padding: 16px 20px;
    font-size: 0.87rem;
    color: #1a1a1a;
    line-height: 2;
    transition: transform 0.2s;
}
.snap-card:hover {
    transform: translateY(-3px);
}
.snap-card b {
    color: #E63946;
}

/* Gradient divider */
.gradient-divider {
    height: 2px;
    background: #1a1a1a;
    margin: 20px 0;
}

/* Simple fade animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}
@keyframes shake {
    0%,100%{transform:translateX(0)}10%,30%,50%,70%,90%{transform:translateX(-4px)}20%,40%,60%,80%{transform:translateX(4px)}
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Logo at the very top (gracefully handle missing file)
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=220)
    else:
        st.markdown(
            "<div style='text-align: center; font-size: 1.8rem; font-weight: 800; font-family: Space Grotesk; color: #1a1a1a;'>🔄 SWAG Product Sync</div>",
            unsafe_allow_html=True
        )
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
if "full_scan_results" not in st.session_state:
    st.session_state.full_scan_results = None  # store missing list for full scan


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


def call_with_retry(func, *args, retries=3, delay=2, **kwargs):
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
# get_or_create helpers for category, brand, season (unchanged)
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


# -----------------------------------------------------------------------------
# BULK fetch from SWAG (one API call)
# -----------------------------------------------------------------------------
def fetch_products_bulk_from_swag(codes_list):
    """Fetch all needed product data from SWAG in a single call."""
    if not codes_list:
        return {}
    cfg = st.secrets["SWAG"]
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return {}
    domain = [["default_code", "in", codes_list]]
    # We fetch product.template because it contains the required fields (categ_id, brand_id, season_id)
    fields = [
        "name", "default_code", "categ_id", "brand_id", "season_id",
        "barcode", "type", "standard_price", "list_price", "compare_list_price"
    ]
    try:
        recs = call_with_retry(
            _x, cfg["url"], cfg["db"], uid, cfg["api_key"],
            "product.template", "search_read", [domain],
            {"fields": fields, "limit": len(codes_list) + 50}
        )
    except Exception:
        # Fallback to product.product if product.template fails
        recs = call_with_retry(
            _x, cfg["url"], cfg["db"], uid, cfg["api_key"],
            "product.product", "search_read", [domain],
            {"fields": fields, "limit": len(codes_list) + 50}
        )
    result = {}
    for r in recs or []:
        code = r.get("default_code", "")
        if not code:
            continue
        # extract names from many2one tuples
        categ_name = None
        if r.get("categ_id") and isinstance(r["categ_id"], list) and len(r["categ_id"]) > 1:
            categ_name = r["categ_id"][1]
        brand_name = None
        if r.get("brand_id") and isinstance(r["brand_id"], list) and len(r["brand_id"]) > 1:
            brand_name = r["brand_id"][1]
        season_name = None
        if r.get("season_id") and isinstance(r["season_id"], list) and len(r["season_id"]) > 1:
            season_name = r["season_id"][1]
        result[code] = {
            "name": r.get("name", ""),
            "default_code": code,
            "categ_name": categ_name,
            "brand_name": brand_name,
            "season_name": season_name,
            "barcode": r.get("barcode", ""),
            "type": r.get("type", "consu"),
            "standard_price": float(r.get("standard_price") or 0.0),
            "list_price": float(r.get("list_price") or 0.0),
            "compare_list_price": float(r.get("compare_list_price") or 0.0),
        }
    return result


def create_product_in_target(target_cfg, product_data):
    """Create a product in target company using pre‑fetched SWAG data."""
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        raise Exception("Authentication failed for target company")
    categ_id = get_or_create_category(target_cfg, product_data["categ_name"]) if product_data.get("categ_name") else None
    brand_id = get_or_create_brand(target_cfg, product_data["brand_name"]) if product_data.get("brand_name") else None
    season_id = get_or_create_season(target_cfg, product_data["season_name"]) if product_data.get("season_name") else None
    vals = {
        "name": product_data["name"],
        "default_code": product_data["default_code"],
        "barcode": product_data.get("barcode", ""),
        "type": product_data.get("type", "consu"),
        "standard_price": product_data.get("standard_price", 0.0),
        "list_price": product_data.get("compare_list_price") or product_data.get("list_price") or 0.0,
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
# Batch check (TWO API calls total)
# -----------------------------------------------------------------------------
def batch_check_products(codes, target_cfg):
    """Check existence in target company and fetch SWAG product names in TWO API calls."""
    # 1. Target company: one search_read call to get existing codes
    uid_target = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    existing_map = {code: False for code in codes}
    if uid_target:
        domain = [["default_code", "in", codes]]
        existing_products = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
            "product.product", "search_read", [domain],
            {"fields": ["default_code"], "limit": len(codes) + 50}
        )
        if existing_products:
            for p in existing_products:
                code = p.get("default_code")
                if code:
                    existing_map[code] = True
    
    # 2. SWAG: one search_read call to get names and existence
    swag_cfg = st.secrets["SWAG"]
    uid_swag = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
    swag_exists = {code: False for code in codes}
    product_names = {code: code for code in codes}
    if uid_swag:
        domain = [["default_code", "in", codes]]
        swag_products = call_with_retry(
            _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
            "product.product", "search_read", [domain],
            {"fields": ["default_code", "name"], "limit": len(codes) + 50}
        )
        if swag_products:
            for p in swag_products:
                code = p.get("default_code")
                if code:
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
# FULL SCAN function (two API calls total)
# -----------------------------------------------------------------------------
def full_scan(target_cfg):
    """Fetch all products from SWAG and target, return missing products list."""
    swag_cfg = st.secrets["SWAG"]
    # Step 1: Authenticate
    uid_swag = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
    uid_target = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid_swag or not uid_target:
        raise Exception("Authentication failed for SWAG or target company.")
    
    # Step 2: Fetch all SWAG products (with default_code)
    swag_domain = [["default_code", "!=", False]]
    swag_fields = ["default_code", "name", "categ_id", "brand_id"]
    swag_all = call_with_retry(
        _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
        "product.template", "search_read", [swag_domain],
        {"fields": swag_fields, "limit": 5000, "order": "id asc"}
    )
    if not swag_all:
        swag_all = []
    swag_dict = {}
    for p in swag_all:
        code = p.get("default_code")
        if code:
            # extract names
            categ_name = None
            if p.get("categ_id") and isinstance(p["categ_id"], list) and len(p["categ_id"]) > 1:
                categ_name = p["categ_id"][1]
            brand_name = None
            if p.get("brand_id") and isinstance(p["brand_id"], list) and len(p["brand_id"]) > 1:
                brand_name = p["brand_id"][1]
            swag_dict[code] = {
                "code": code,
                "name": p.get("name", code),
                "category": categ_name or "—",
                "brand": brand_name or "—"
            }
    
    # Step 3: Fetch all target products (only default_code)
    target_domain = [["default_code", "!=", False]]
    target_all = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
        "product.template", "search_read", [target_domain],
        {"fields": ["default_code"], "limit": 5000}
    )
    if not target_all:
        target_all = []
    target_codes = {p.get("default_code") for p in target_all if p.get("default_code")}
    
    # Step 4: Find missing
    missing = []
    for code, data in swag_dict.items():
        if code not in target_codes:
            missing.append(data)
    
    return missing, len(swag_dict), len(target_codes)


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

# =============================================================================
# NEW: FULL SCAN MODE
# =============================================================================
st.markdown("### 🔍 FULL SCAN — Find all missing products")
st.markdown("Scan all products in SWAG and compare with the target company (fast: only 2 API calls).")
full_scan_company_map = {
    "La Rouche": "LAROUCHE",
    "Fashion Limits": "FASHION_LIMITS",
    "Different Clothes": "DIFFC"
}
full_scan_selected_label = st.selectbox(
    "Target Company for Full Scan",
    list(full_scan_company_map.keys()),
    key="full_scan_company"
)
full_scan_target_key = full_scan_company_map[full_scan_selected_label]
full_scan_target_cfg = st.secrets.get(full_scan_target_key)

if st.button("🔍 Scan Now", type="primary", key="full_scan_button", help="Fetch all products from SWAG and target company to find missing ones."):
    if not full_scan_target_cfg:
        st.error(f"❌ Secrets missing for {full_scan_selected_label}. Check your secrets.toml file.")
    else:
        with st.spinner(f"🔍 Scanning SWAG & {full_scan_selected_label}..."):
            try:
                missing_list, total_swag, total_target = full_scan(full_scan_target_cfg)
                st.session_state.full_scan_results = {
                    "missing": missing_list,
                    "total_swag": total_swag,
                    "total_target": total_target,
                    "company": full_scan_selected_label,
                    "target_cfg": full_scan_target_cfg
                }
            except Exception as e:
                st.error(f"❌ Scan failed: {str(e)}")
                st.session_state.full_scan_results = None

# Display full scan results if available
if st.session_state.get("full_scan_results"):
    res = st.session_state.full_scan_results
    missing = res["missing"]
    total_swag = res["total_swag"]
    total_target = res["total_target"]
    company = res["company"]
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total in SWAG", total_swag)
    col2.metric(f"✅ Already in {company}", total_target)
    col3.metric("❌ Missing", len(missing))
    
    if len(missing) == 0:
        st.markdown(f'<div class="ok-banner">✅ All SWAG products already exist in {company}!</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"#### 📋 Missing Products ({len(missing)} items)")
        # Show up to 500 rows
        show_missing = missing[:500]
        df_missing = pd.DataFrame(show_missing)
        if len(missing) > 500:
            st.info(f"Showing first 500 of {len(missing)} missing products. Download CSV for full list.")
        st.dataframe(df_missing, use_container_width=True, hide_index=True)
        
        # Download button
        csv_full = pd.DataFrame(missing).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "⬇️ Download Missing List CSV",
            csv_full,
            f"missing_products_{company}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv",
            use_container_width=False
        )
        
        # Create All Missing button
        if st.button("➕ Create All Missing", type="primary", key="full_scan_create"):
            # Prepare creation list
            to_create = missing  # list of dicts with code, name, category, brand
            total_to_create = len(to_create)
            if total_to_create == 0:
                st.info("No missing products to create.")
            else:
                progress_bar = st.progress(0, text="Starting parallel creation...")
                status_text = st.empty()
                errors_container = st.container()
                results_created = []
                
                # Bulk fetch all product data from SWAG
                missing_codes = [item["code"] for item in to_create]
                swag_bulk_data = fetch_products_bulk_from_swag(missing_codes)
                
                completed = 0
                
                def create_one(product_info):
                    code = product_info["code"]
                    prod_data = swag_bulk_data.get(code)
                    if not prod_data:
                        return {"code": code, "name": product_info["name"], "status": "skipped", "reason": "Product not found in SWAG", "new_id": None}
                    try:
                        new_id = create_product_in_target(res["target_cfg"], prod_data)
                        return {"code": code, "name": product_info["name"], "status": "created", "reason": "", "new_id": new_id}
                    except Exception as e:
                        error_msg = parse_odoo_error(e)
                        return {"code": code, "name": product_info["name"], "status": "error", "reason": error_msg, "raw_error": str(e), "new_id": None}
                
                with ThreadPoolExecutor(max_workers=8) as executor:
                    future_to_info = {executor.submit(create_one, info): info for info in to_create}
                    for future in as_completed(future_to_info):
                        result = future.result()
                        results_created.append(result)
                        completed += 1
                        percent = int(completed / total_to_create * 100)
                        progress_bar.progress(completed / total_to_create, text=f"⚡ Creating {completed} / {total_to_create} ({percent}%)")
                        status_text.markdown(f"🔄 **{completed} / {total_to_create}** completed")
                        
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
                
                created = sum(1 for r in results_created if r["status"] == "created")
                skipped = sum(1 for r in results_created if r["status"] == "skipped")
                errors = sum(1 for r in results_created if r["status"] == "error")
                
                if errors == 0:
                    st.balloons()
                    st.markdown('<div class="ok-banner">🎉 All products created successfully! 🎉</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-banner">⚠️ Completed with {errors} errors. See details below.</div>', unsafe_allow_html=True)
                
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
                
                # Save to history
                st.session_state.sync_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "company": company,
                    "total": total_to_create,
                    "created": created,
                    "skipped": skipped,
                    "errors": errors,
                    "retried": 0
                })
                
                # Clear results to avoid re-running
                st.session_state.full_scan_results = None
                st.rerun()

st.markdown("---")
st.markdown("### ✍️ Manual Sync (Targeted Products)")
st.markdown("For specific product codes, use the manual method below.")

# =============================================================================
# EXISTING MANUAL SYNC CODE (unchanged)
# =============================================================================
# Step 1: Company selector (existing)
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
        with st.spinner("Checking codes in batch (2 API calls)..."):
            check_results = batch_check_products(codes, target_cfg)
            st.session_state.check_results = check_results
            
            # Prepare missing products data for preview
            missing_list = [r for r in check_results if r["status"] == "missing"]
            missing_products_data = []
            # Bulk fetch missing products from SWAG (one call) to get category/brand for preview
            if missing_list:
                missing_codes = [r["code"] for r in missing_list]
                swag_bulk = fetch_products_bulk_from_swag(missing_codes)
                for r in missing_list:
                    prod = swag_bulk.get(r["code"], {})
                    missing_products_data.append({
                        "code": r["code"],
                        "name": r["name"],
                        "category": prod.get("categ_name", "—"),
                        "brand": prod.get("brand_name", "—"),
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
                
                # BULK fetch all product data from SWAG in ONE call
                missing_codes_to_fetch = [item["code"] for item in to_create]
                swag_bulk_data = fetch_products_bulk_from_swag(missing_codes_to_fetch)
                
                completed = 0
                
                def create_one(product_info):
                    code = product_info["code"]
                    prod_data = swag_bulk_data.get(code)
                    if not prod_data:
                        return {"code": code, "name": product_info["name"], "status": "skipped", "reason": "Product not found in SWAG", "new_id": None}
                    try:
                        new_id = create_product_in_target(target_cfg, prod_data)
                        return {"code": code, "name": product_info["name"], "status": "created", "reason": "", "new_id": new_id}
                    except Exception as e:
                        error_msg = parse_odoo_error(e)
                        return {"code": code, "name": product_info["name"], "status": "error", "reason": error_msg, "raw_error": str(e), "new_id": None}
                
                # Parallel execution with ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=8) as executor:
                    future_to_info = {executor.submit(create_one, info): info for info in to_create}
                    for future in as_completed(future_to_info):
                        result = future.result()
                        results_created.append(result)
                        completed += 1
                        percent = int(completed / total_to_create * 100)
                        progress_bar.progress(completed / total_to_create, text=f"⚡ Creating {completed} / {total_to_create} ({percent}%)")
                        status_text.markdown(f"🔄 **{completed} / {total_to_create}** completed")
                        
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
                            st.rerun()
                
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
                
                # Clear session state after completion
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
