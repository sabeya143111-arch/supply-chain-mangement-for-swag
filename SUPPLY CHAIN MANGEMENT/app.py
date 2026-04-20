"""
SWAG Product Sync — Standalone App (Light Theme)
Copy products from SWAG to any target company (La Rouche, Fashion Limits, Different Clothes)
MAXIMUM SPEED: batch API calls + parallel creation + bulk fetch
+ FULL SCAN MODE: find all missing products in one click
+ VARIANT SUPPORT: detect and create product.product variants with attributes
"""

import io
import os
import re
import time
import xmlrpc.client
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SWAG Product Sync",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CSS — Editorial style (black/white/red, Space Grotesk + Inter)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #f5f5f0; min-height: 100vh; }

section[data-testid="stSidebar"] { background: #1a1a1a !important; border-right: none; }
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div { color: #ffffff !important; }
section[data-testid="stSidebar"] input { background: #2a2a2a !important; color: #ffffff !important; }

h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800; letter-spacing: -0.02em; color: #1a1a1a;
}
p, li, .stMarkdown, .stTextInput label, .stNumberInput label, .stTextArea label { color: #333333; }

.stButton button[kind="primary"], .stFormSubmitButton button {
    background: #1a1a1a !important; color: white !important; border: none !important;
    border-radius: 0 !important; font-family: 'Space Grotesk', sans-serif;
    font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
    padding: 10px 24px !important; transition: all 0.2s ease !important;
}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button:hover {
    background: #E63946 !important; transform: translateY(-2px);
}
.stButton button[kind="secondary"] {
    background: transparent !important; border: 2px solid #1a1a1a !important;
    color: #1a1a1a !important; border-radius: 0 !important;
    font-family: 'Space Grotesk', sans-serif; font-weight: 600;
    text-transform: uppercase; padding: 8px 20px !important; transition: all 0.2s ease !important;
}
.stButton button[kind="secondary"]:hover {
    background: #1a1a1a !important; color: white !important; transform: translateY(-2px);
}
.stDownloadButton button {
    background: transparent !important; border: 2px solid #1a1a1a !important;
    color: #1a1a1a !important; border-radius: 0 !important;
    font-weight: 600; font-size: 0.8rem; padding: 6px 16px !important; transition: all 0.2s ease !important;
}
.stDownloadButton button:hover { background: #1a1a1a !important; color: white !important; }

[data-testid="stMetric"] {
    background: #ffffff !important; border: 1px solid #e0e0e0 !important;
    border-radius: 0 !important; padding: 20px 16px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
[data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
[data-testid="stMetricLabel"] { color: #555555 !important; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important; font-size: 1.8rem !important;
    font-weight: 800 !important; color: #1a1a1a !important;
    background: none !important; -webkit-text-fill-color: #1a1a1a !important;
}

.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 2px solid #e0e0e0; gap: 0; }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #555555 !important; border-radius: 0 !important;
    font-family: 'Space Grotesk', sans-serif; font-weight: 600;
    text-transform: uppercase; font-size: 0.85rem; padding: 10px 24px !important; transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    color: #E63946 !important; border-bottom: 3px solid #E63946 !important;
    background: transparent !important; box-shadow: none !important;
}

.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #ffffff !important; border: 1px solid #d0d0d0 !important;
    border-radius: 0 !important; color: #1a1a1a !important;
    font-family: 'Inter', sans-serif; padding: 10px 12px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #E63946 !important; box-shadow: 0 0 0 2px rgba(230,57,70,0.2) !important;
}
.stTextInput label, .stNumberInput label, .stTextArea label { font-weight: 600; color: #1a1a1a; }
.stRadio label, .stCheckbox label, [data-testid="stToggle"] label { color: #1a1a1a !important; font-weight: 500; }

/* ── Banners ── */
.info-banner {
    background: #eef2ff; border-left: 4px solid #E63946; border-radius: 0;
    padding: 12px 16px; margin: 12px 0; color: #1e3a8a;
}
.warn-banner {
    background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 0;
    padding: 12px 16px; margin: 12px 0; color: #92400e;
}
.alert-banner {
    background: #fef2f2; border-left: 4px solid #E63946; border-radius: 0;
    padding: 12px 16px; margin: 12px 0; color: #991b1b;
}
.ok-banner {
    background: #ecfdf5; border-left: 4px solid #22c55e; border-radius: 0;
    padding: 12px 16px; margin: 12px 0; color: #065f46;
}

/* Tables */
.dataframe { font-family: 'Inter', monospace; border-collapse: collapse; width: 100%; }
.dataframe thead tr th { background: #1a1a1a; color: white; font-family: 'Space Grotesk', sans-serif; font-weight: 600; padding: 12px; border: none; }
.dataframe tbody tr:nth-child(even) { background: #fafaf5; }
.dataframe tbody tr:hover { background: #fff0f0; }

[data-testid="stProgressBar"] > div { background: #E63946 !important; border-radius: 0 !important; }
[data-testid="stExpander"] { background: #ffffff !important; border: 1px solid #e0e0e0 !important; border-radius: 0 !important; }
[data-testid="stFileUploader"] { background: #ffffff !important; border: 2px dashed #d0d0d0 !important; border-radius: 0 !important; }
[data-testid="stFileUploader"]:hover { border-color: #E63946 !important; }
hr { border: none !important; height: 1px !important; background: #e0e0e0 !important; margin: 24px 0 !important; }

.error-card {
    background: #fef2f2; border-left: 4px solid #E63946; border-radius: 0;
    padding: 12px 16px; margin: 8px 0; font-family: 'Inter', monospace;
    font-size: 0.85rem; color: #7f1d1d;
}
.error-card strong { color: #b91c1c; }

.step-circle {
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; background: #1a1a1a; color: white;
    border-radius: 50%; font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; margin-right: 12px;
}
.section-header { display: flex; align-items: center; margin: 20px 0 16px; }
.section-header h3 { margin: 0; font-weight: 800; }
.empty-state { text-align: center; padding: 60px; color: #888888; font-family: 'Inter', sans-serif; font-size: 1rem; }

.login-card { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 0; padding: 32px 36px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
.login-orb { width: 120px; height: 120px; border-radius: 50%; background: #1a1a1a; display: flex; align-items: center; justify-content: center; font-size: 3rem; margin: 0 auto 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
.login-title { font-family: 'Space Grotesk', sans-serif; font-size: 2.4rem; font-weight: 800; background: linear-gradient(135deg, #1a1a1a, #E63946); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 6px; }
.login-subtitle { color: #555555; font-size: 0.95rem; text-align: center; margin-bottom: 28px; }
.welcome-banner { background: #f5f5f0; border: 1px solid #e0e0e0; border-radius: 0; padding: 14px 20px; text-align: center; margin-bottom: 20px; color: #1a1a1a; }

.badge-ok { background: #ecfdf5; color: #065f46; border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 700; }
.badge-off { background: #fef2f2; color: #991b1b; border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 700; }
.badge-err { background: #fffbeb; color: #92400e; border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 700; }

.snap-card { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 0; padding: 16px 20px; font-size: 0.87rem; color: #1a1a1a; line-height: 2; transition: transform 0.2s; }
.snap-card:hover { transform: translateY(-3px); }
.snap-card b { color: #E63946; }

.gradient-divider { height: 2px; background: #1a1a1a; margin: 20px 0; }

/* ── Scan status card (used during/after full scan) ── */
.scan-status-card {
    background: #ffffff; border: 1px solid #e0e0e0; border-left: 4px solid #E63946;
    padding: 16px 20px; margin: 12px 0; font-family: 'Space Grotesk', sans-serif;
    font-size: 0.95rem; color: #1a1a1a;
}

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-30px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-30px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(30px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.75; }
}
@keyframes shake {
    0%,100%          { transform: translateX(0); }
    10%,30%,50%,70%,90% { transform: translateX(-5px); }
    20%,40%,60%,80%  { transform: translateX(5px); }
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Logo
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=220)
    else:
        st.markdown(
            "<div style='text-align:center;font-size:1.8rem;font-weight:800;"
            "font-family:Space Grotesk;color:#1a1a1a;'>🔄 SWAG Product Sync</div>",
            unsafe_allow_html=True,
        )
st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Session state initialisation
# -----------------------------------------------------------------------------
for key, default in [
    ("sync_history", []),
    ("check_results", None),
    ("missing_products_data", None),
    ("retry_counts", {}),
    ("last_sync_time", None),
    ("full_scan_results", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# -----------------------------------------------------------------------------
# XML-RPC helpers
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
# PDF parsing
# -----------------------------------------------------------------------------
_RE_BRACKET = re.compile(r'\[([A-Za-z0-9\-_()]{3,30})\]')
_RE_SR_LINE = re.compile(
    r'(?:^|\s)([A-Z]{2,6}\d+(?:-\d+)?(?:-[A-Z0-9()]{1,10})?)\s+.{0,80}?\d+\.?\d*\s+SR',
    re.MULTILINE,
)
_RE_GENERAL = re.compile(
    r'\b([A-Z]{2,6}\d+(?:-\d+)?(?:-[A-Z0-9]{1,4})?(?:\([^)]{1,15}\))?)\b'
)
_EXCLUDE = frozenset([
    'SR','VAT','TAX','PCS','QTY','NO','REF','INV','PO','SO',
    'DO','ID','EN','AR','PDF','AED','SAR','USD','KWD','OMR',
    'BHD','JOD','EGP','TRY',
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
    raw = (
        _RE_BRACKET.findall(text)
        + [m.group(1) for m in _RE_SR_LINE.finditer(text)]
        + _RE_GENERAL.findall(text)
    )
    seen, out, seq = set(), [], 1
    for c in raw:
        u = c.strip().upper()
        if _valid(u) and u not in seen:
            seen.add(u)
            out.append({"sequence": seq, "code": u})
            seq += 1
    return out


# -----------------------------------------------------------------------------
# get_or_create helpers — Category, Brand, Season (unchanged)
# -----------------------------------------------------------------------------
def get_or_create_category(target_cfg, category_name):
    if not category_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    ids = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.category", "search", [[["name", "=", category_name]]], {"limit": 1}
    )
    if ids:
        return ids[0]
    return call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.category", "create", [{"name": category_name}], {}
    )


def get_or_create_brand(target_cfg, brand_name):
    if not brand_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    try:
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.brand", "search", [[["name", "=", brand_name]]], {"limit": 1}
        )
        if ids:
            return ids[0]
        return call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.brand", "create", [{"name": brand_name}], {}
        )
    except Exception:
        return None


def get_or_create_season(target_cfg, season_name):
    if not season_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    try:
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.season", "search", [[["name", "=", season_name]]], {"limit": 1}
        )
        if ids:
            return ids[0]
        return call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.season", "create", [{"name": season_name}], {}
        )
    except Exception:
        return None


# =============================================================================
# === VARIANT HELPERS START ===
# =============================================================================

def get_or_create_attribute(target_cfg, attribute_name):
    """
    Get or create a product.attribute record in the target company.
    Uses the same XML-RPC + retry pattern as the category/brand/season helpers.
    """
    if not attribute_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    try:
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.attribute", "search",
            [[["name", "=", attribute_name]]], {"limit": 1}
        )
        if ids:
            return ids[0]
        new_id = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.attribute", "create",
            [{"name": attribute_name, "create_variant": "always"}], {}
        )
        return new_id
    except Exception:
        return None


def get_or_create_attribute_value(target_cfg, attribute_id, value_name):
    """
    Get or create a product.attribute.value record tied to a given attribute_id
    in the target company.
    """
    if not attribute_id or not value_name:
        return None
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        return None
    try:
        ids = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.attribute.value", "search",
            [[["attribute_id", "=", attribute_id], ["name", "=", value_name]]],
            {"limit": 1}
        )
        if ids:
            return ids[0]
        new_id = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.attribute.value", "create",
            [{"attribute_id": attribute_id, "name": value_name}], {}
        )
        return new_id
    except Exception:
        return None


def _find_variant_by_pav_ids(target_cfg, uid, tmpl_id, target_pav_ids):
    """
    Given a set of product.attribute.value IDs (target_pav_ids), find the
    product.product variant on tmpl_id whose product_template_attribute_value_ids
    correspond exactly to those pav IDs.
    Returns the variant ID or None.
    """
    if not target_pav_ids:
        return None
    try:
        # 1. Get ptav records for this template whose pav matches our values
        ptav_recs = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.template.attribute.value", "search_read",
            [[
                ["product_tmpl_id", "=", tmpl_id],
                ["product_attribute_value_id", "in", list(target_pav_ids)],
            ]],
            {"fields": ["id", "product_attribute_value_id"], "limit": 50}
        )
        our_ptav_ids = frozenset(r["id"] for r in (ptav_recs or []))
        if not our_ptav_ids:
            return None

        # 2. Find the variant whose ptav set matches exactly
        variants = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.product", "search_read",
            [[["product_tmpl_id", "=", tmpl_id]]],
            {"fields": ["id", "default_code", "product_template_attribute_value_ids"], "limit": 200}
        )
        for v in (variants or []):
            if frozenset(v.get("product_template_attribute_value_ids", [])) == our_ptav_ids:
                return v["id"]
    except Exception:
        pass
    return None

# === VARIANT HELPERS END ===


# =============================================================================
# BULK fetch from SWAG — extended with variant / attribute info
# =============================================================================
def fetch_products_bulk_from_swag(codes_list):
    """
    Fetch all needed product data from SWAG in minimal API calls.

    Extended fields (vs. original):
      • product_tmpl_id  → template_name in result dict
      • attribute_value_ids → resolved to ["Size: M", "Color: Black"] list

    Returns dict keyed by default_code.
    """
    if not codes_list:
        return {}
    cfg = st.secrets["SWAG"]
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return {}

    domain = [["default_code", "in", codes_list]]
    pp_fields = [
        "name", "default_code", "categ_id", "brand_id", "season_id",
        "barcode", "type", "standard_price", "list_price", "compare_list_price",
        "product_tmpl_id", "attribute_value_ids",
    ]

    # Prefer product.product for variant-level granularity
    recs = None
    try:
        recs = call_with_retry(
            _x, cfg["url"], cfg["db"], uid, cfg["api_key"],
            "product.product", "search_read", [domain],
            {"fields": pp_fields, "limit": len(codes_list) + 50}
        )
    except Exception:
        pass

    # Fallback: product.template (no variant fields)
    if not recs:
        tmpl_fields = [f for f in pp_fields if f not in ("product_tmpl_id", "attribute_value_ids")]
        try:
            recs = call_with_retry(
                _x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                "product.template", "search_read", [domain],
                {"fields": tmpl_fields, "limit": len(codes_list) + 50}
            )
        except Exception:
            recs = []

    recs = recs or []

    # Collect all attribute_value_ids for a single batch resolution call
    all_av_ids = set()
    for r in recs:
        for avid in (r.get("attribute_value_ids") or []):
            all_av_ids.add(avid)

    # One call to resolve all attribute values → "AttributeName: ValueName"
    av_label_map: dict[int, str] = {}
    if all_av_ids:
        try:
            av_recs = call_with_retry(
                _x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                "product.attribute.value", "search_read",
                [[["id", "in", list(all_av_ids)]]],
                {"fields": ["name", "attribute_id"], "limit": len(all_av_ids) + 10}
            )
            for av in (av_recs or []):
                attr_name = (
                    av["attribute_id"][1]
                    if isinstance(av.get("attribute_id"), (list, tuple))
                    else "?"
                )
                av_label_map[av["id"]] = f"{attr_name}: {av['name']}"
        except Exception:
            pass

    def _m2o(record, field):
        """Extract name from a Many2one tuple, or None."""
        val = record.get(field)
        return val[1] if isinstance(val, (list, tuple)) and len(val) > 1 else None

    result = {}
    for r in recs:
        code = r.get("default_code", "")
        if not code:
            continue
        attributes = [
            av_label_map[avid]
            for avid in (r.get("attribute_value_ids") or [])
            if avid in av_label_map
        ]
        result[code] = {
            "name":              r.get("name", ""),
            "default_code":      code,
            "template_name":     _m2o(r, "product_tmpl_id") or r.get("name", ""),
            "categ_name":        _m2o(r, "categ_id"),
            "brand_name":        _m2o(r, "brand_id"),
            "season_name":       _m2o(r, "season_id"),
            "barcode":           r.get("barcode", ""),
            "type":              r.get("type", "consu"),
            "standard_price":    float(r.get("standard_price") or 0.0),
            "list_price":        float(r.get("list_price") or 0.0),
            "compare_list_price": float(r.get("compare_list_price") or 0.0),
            "attributes":        attributes,   # e.g. ["Size: M", "Color: Black"]
        }
    return result


# =============================================================================
# create_product_in_target — variant-aware
# =============================================================================
def create_product_in_target(target_cfg, product_data):
    """
    Create a product in the target company using pre-fetched SWAG data.

    • If product_data has no 'attributes': uses the original simple creation path
      (creates product.product directly).
    • If 'attributes' is present: ensures attribute/value records exist, finds or
      creates a product.template with the right attribute lines, then locates or
      claims the auto-generated product.product variant.
    """
    uid = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid:
        raise Exception("Authentication failed for target company")

    categ_id  = get_or_create_category(target_cfg, product_data.get("categ_name"))  if product_data.get("categ_name")  else None
    brand_id  = get_or_create_brand(target_cfg, product_data.get("brand_name"))     if product_data.get("brand_name")  else None
    season_id = get_or_create_season(target_cfg, product_data.get("season_name"))   if product_data.get("season_name") else None

    base_vals = {
        "type":           product_data.get("type", "consu"),
        "standard_price": product_data.get("standard_price", 0.0),
        "list_price":     product_data.get("compare_list_price") or product_data.get("list_price") or 0.0,
    }
    if categ_id:  base_vals["categ_id"]  = categ_id
    if brand_id:  base_vals["brand_id"]  = brand_id
    if season_id: base_vals["season_id"] = season_id

    attributes = product_data.get("attributes", [])

    # ── Simple product (no variants) ────────────────────────────────────────
    if not attributes:
        vals = {
            "name":         product_data["name"],
            "default_code": product_data["default_code"],
            "barcode":      product_data.get("barcode", ""),
            **base_vals,
        }
        return call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.product", "create", [vals], {}
        )

    # ── Variant product ──────────────────────────────────────────────────────
    # Parse "Attribute: Value" strings
    attr_vals_map: dict[str, str] = {}
    for attr_str in attributes:
        if ": " in attr_str:
            a, v = attr_str.split(": ", 1)
            attr_vals_map[a.strip()] = v.strip()

    if not attr_vals_map:
        # Couldn't parse — fall back to simple creation
        vals = {
            "name":         product_data["name"],
            "default_code": product_data["default_code"],
            "barcode":      product_data.get("barcode", ""),
            **base_vals,
        }
        return call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.product", "create", [vals], {}
        )

    # Ensure attribute + value records exist in target (batch-friendly: one pair at a time)
    attr_id_map: dict[str, int] = {}
    val_id_map: dict[tuple, int] = {}

    for attr_name, val_name in attr_vals_map.items():
        attr_id = get_or_create_attribute(target_cfg, attr_name)
        if attr_id:
            attr_id_map[attr_name] = attr_id
            val_id = get_or_create_attribute_value(target_cfg, attr_id, val_name)
            if val_id:
                val_id_map[(attr_name, val_name)] = val_id

    target_pav_ids = set(val_id_map.values())
    template_name  = product_data.get("template_name") or product_data["name"]

    # ── Find or create the product.template ─────────────────────────────────
    existing_tmpls = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.template", "search_read",
        [[["name", "=", template_name]]],
        {"fields": ["id", "attribute_line_ids"], "limit": 1}
    )

    if existing_tmpls:
        tmpl_id = existing_tmpls[0]["id"]

        # If the variant already exists by default_code, return it immediately
        existing_variant = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.product", "search",
            [[["default_code", "=", product_data["default_code"]]]],
            {"limit": 1}
        )
        if existing_variant:
            return existing_variant[0]

        # Ensure the template has attribute lines for our values
        existing_line_ids = existing_tmpls[0].get("attribute_line_ids", [])
        existing_lines_data: dict[int, dict] = {}

        if existing_line_ids:
            lines = call_with_retry(
                _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
                "product.template.attribute.line", "read", [existing_line_ids],
                {"fields": ["attribute_id", "value_ids"]}
            )
            for line in (lines or []):
                aid = (
                    line["attribute_id"][0]
                    if isinstance(line["attribute_id"], (list, tuple))
                    else line["attribute_id"]
                )
                existing_lines_data[aid] = {
                    "line_id":   line["id"],
                    "value_ids": set(line.get("value_ids", [])),
                }

        write_cmds = []
        for attr_name, val_name in attr_vals_map.items():
            attr_id = attr_id_map.get(attr_name)
            val_id  = val_id_map.get((attr_name, val_name))
            if not attr_id or not val_id:
                continue
            if attr_id in existing_lines_data:
                if val_id not in existing_lines_data[attr_id]["value_ids"]:
                    write_cmds.append((1, existing_lines_data[attr_id]["line_id"], {"value_ids": [(4, val_id)]}))
            else:
                write_cmds.append((0, 0, {"attribute_id": attr_id, "value_ids": [(6, 0, [val_id])]}))

        if write_cmds:
            call_with_retry(
                _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
                "product.template", "write",
                [[tmpl_id], {"attribute_line_ids": write_cmds}], {}
            )

    else:
        # Create new template with attribute lines
        attr_line_cmds = [
            (0, 0, {"attribute_id": attr_id_map[a], "value_ids": [(6, 0, [val_id_map[(a, v)]])]})
            for a, v in attr_vals_map.items()
            if attr_id_map.get(a) and val_id_map.get((a, v))
        ]
        tmpl_vals = {"name": template_name, **base_vals}
        if attr_line_cmds:
            tmpl_vals["attribute_line_ids"] = attr_line_cmds

        tmpl_id = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.template", "create", [tmpl_vals], {}
        )

    # ── Locate the auto-generated variant matching our attribute values ───────
    variant_id = _find_variant_by_pav_ids(target_cfg, uid, tmpl_id, target_pav_ids)

    if variant_id:
        call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.product", "write",
            [[variant_id], {
                "default_code": product_data["default_code"],
                "barcode":      product_data.get("barcode", ""),
            }], {}
        )
        return variant_id

    # Fallback: claim any uncoded variant on this template
    uncoded = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.product", "search",
        [[["product_tmpl_id", "=", tmpl_id], ["default_code", "=", False]]],
        {"limit": 1}
    )
    if uncoded:
        vid = uncoded[0]
        call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
            "product.product", "write",
            [[vid], {
                "default_code": product_data["default_code"],
                "barcode":      product_data.get("barcode", ""),
            }], {}
        )
        return vid

    # Final fallback: direct product.product create
    vals = {
        "name":         product_data["name"],
        "default_code": product_data["default_code"],
        **base_vals,
    }
    return call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid, target_cfg["api_key"],
        "product.product", "create", [vals], {}
    )


# -----------------------------------------------------------------------------
# Smart error parser
# -----------------------------------------------------------------------------
def parse_odoo_error(e):
    error_str = str(e)
    if hasattr(e, "faultString"):
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
        return f"Incompatible or invalid field: '{field}'. Check related record exists."
    if "xmlrpc.client.Fault" in error_str:
        return f"XML-RPC Fault: {error_str[:300]}"
    return error_str[:500]


# -----------------------------------------------------------------------------
# Batch check (2 API calls total)
# -----------------------------------------------------------------------------
def batch_check_products(codes, target_cfg):
    """Check existence in target company and fetch SWAG product names in two API calls."""
    uid_target = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    existing_map = {code: False for code in codes}
    if uid_target:
        domain = [["default_code", "in", codes]]
        existing_products = call_with_retry(
            _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
            "product.product", "search_read", [domain],
            {"fields": ["default_code"], "limit": len(codes) + 50}
        )
        for p in (existing_products or []):
            code = p.get("default_code")
            if code:
                existing_map[code] = True

    swag_cfg = st.secrets["SWAG"]
    uid_swag  = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
    swag_exists   = {code: False for code in codes}
    product_names = {code: code for code in codes}
    if uid_swag:
        domain = [["default_code", "in", codes]]
        swag_products = call_with_retry(
            _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
            "product.product", "search_read", [domain],
            {"fields": ["default_code", "name"], "limit": len(codes) + 50}
        )
        for p in (swag_products or []):
            code = p.get("default_code")
            if code:
                swag_exists[code]   = True
                product_names[code] = p.get("name", code)

    results = []
    for code in codes:
        if not swag_exists[code]:
            status = "not_in_swag"
        elif existing_map[code]:
            status = "exists"
        else:
            status = "missing"
        results.append({"code": code, "name": product_names[code], "status": status})
    return results


# -----------------------------------------------------------------------------
# Full Scan (fetch all products from SWAG + target, return diff)
# -----------------------------------------------------------------------------
def full_scan(target_cfg):
    """
    Fetch all products from SWAG and the target company.
    Returns (missing_list, total_swag, total_target).

    Checks both product.template AND product.product in SWAG to catch
    variant-level default_codes.
    """
    swag_cfg = st.secrets["SWAG"]
    uid_swag   = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
    uid_target = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
    if not uid_swag or not uid_target:
        raise Exception("Authentication failed for SWAG or target company.")

    # SWAG — product.template
    swag_tmpl = call_with_retry(
        _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
        "product.template", "search_read",
        [[["default_code", "!=", False]]],
        {"fields": ["default_code", "name", "categ_id", "brand_id"], "limit": 5000, "order": "id asc"}
    ) or []

    # SWAG — product.product (captures variant-level codes that differ from template)
    swag_pp = call_with_retry(
        _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
        "product.product", "search_read",
        [[["default_code", "!=", False]]],
        {"fields": ["default_code", "name", "categ_id", "brand_id"], "limit": 5000, "order": "id asc"}
    ) or []

    swag_dict: dict[str, dict] = {}
    for p in swag_tmpl + swag_pp:
        code = p.get("default_code")
        if not code or code in swag_dict:
            continue
        categ_name = p["categ_id"][1] if isinstance(p.get("categ_id"), (list, tuple)) and len(p["categ_id"]) > 1 else None
        brand_name = p["brand_id"][1] if isinstance(p.get("brand_id"), (list, tuple)) and len(p["brand_id"]) > 1 else None
        swag_dict[code] = {
            "code":     code,
            "name":     p.get("name", code),
            "category": categ_name or "—",
            "brand":    brand_name or "—",
        }

    # Target — collect all existing codes
    target_all = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
        "product.template", "search_read",
        [[["default_code", "!=", False]]],
        {"fields": ["default_code"], "limit": 5000}
    ) or []
    target_pp = call_with_retry(
        _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
        "product.product", "search_read",
        [[["default_code", "!=", False]]],
        {"fields": ["default_code"], "limit": 5000}
    ) or []
    target_codes = {
        p.get("default_code")
        for p in target_all + target_pp
        if p.get("default_code")
    }

    missing = [data for code, data in swag_dict.items() if code not in target_codes]
    return missing, len(swag_dict), len(target_codes)


# =============================================================================
# === UI ANIMATIONS ENHANCEMENTS ===
# Helper snippets used after operations complete.
# =============================================================================

def _anim_check_complete_banner():
    """Fades in after 'Check Products' finishes."""
    st.markdown(
        """<div class="info-banner"
              style="animation: fadeInUp 0.5s ease forwards;">
            ✅ Check complete — scroll down to see results
        </div>""",
        unsafe_allow_html=True,
    )


def _anim_scan_result_banner(missing_count: int, company: str):
    """Slides in from the right after Full Scan completes."""
    if missing_count == 0:
        st.markdown(
            f"""<div class="ok-banner"
                  style="animation: slideInRight 0.5s ease forwards;">
                ✅ All SWAG products already exist in <strong>{company}</strong>!
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="alert-banner"
                  style="animation: slideInRight 0.5s ease forwards;">
                ⚠️ <strong>{missing_count}</strong> products are missing from
                <strong>{company}</strong>. Review below.
            </div>""",
            unsafe_allow_html=True,
        )


def _anim_creation_result_banner(errors: int):
    """Shows ok-banner (pulse) or alert-banner (shake) after creation."""
    if errors == 0:
        st.balloons()
        st.markdown(
            """<div class="ok-banner"
                  style="animation: pulse 2s infinite;">
                🎉 All products created successfully!
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="alert-banner"
                  style="animation: shake 0.6s ease; animation-fill-mode: both;">
                ⚠️ Completed with <strong>{errors} error(s)</strong>. See details above.
            </div>""",
            unsafe_allow_html=True,
        )


# =============================================================================
# MAIN UI
# =============================================================================

# Sidebar — Sync History
with st.sidebar:
    st.markdown("### 📜 Sync History")
    if st.session_state.sync_history:
        for entry in st.session_state.sync_history[-5:][::-1]:
            with st.expander(f"{entry['timestamp']} — {entry['company']}"):
                st.markdown(f"**Total:** {entry['total']}")
                st.markdown(f"✅ Created: {entry['created']}")
                st.markdown(f"⚠️ Skipped: {entry['skipped']}")
                st.markdown(f"❌ Failed: {entry['errors']}")
                if entry.get("retried"):
                    st.caption(f"🔄 Retried: {entry['retried']}")
    else:
        st.caption("No sync operations yet.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# FULL SCAN
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 🔍 FULL SCAN — Find all missing products")
st.markdown("Scan all products in SWAG and compare with the target company.")

full_scan_company_map = {
    "La Rouche":        "LAROUCHE",
    "Fashion Limits":   "FASHION_LIMITS",
    "Different Clothes": "DIFFC",
}
full_scan_selected_label = st.selectbox(
    "Target Company for Full Scan",
    list(full_scan_company_map.keys()),
    key="full_scan_company",
)
full_scan_target_key = full_scan_company_map[full_scan_selected_label]
full_scan_target_cfg = st.secrets.get(full_scan_target_key)

if st.button("🔍 Scan Now", type="primary", key="full_scan_button"):
    if not full_scan_target_cfg:
        st.error(f"❌ Secrets missing for {full_scan_selected_label}.")
    else:
        # Animated status card while scanning
        scan_placeholder = st.empty()
        scan_placeholder.markdown(
            f"""<div class="scan-status-card"
                  style="animation: slideInRight 0.4s ease forwards;">
                🔄 Scanning SWAG &amp; <strong>{full_scan_selected_label}</strong>…
                <br><small>Fetching product lists (up to 5 000 records each).</small>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.spinner(f"Comparing catalogues…"):
            try:
                missing_list, total_swag, total_target = full_scan(full_scan_target_cfg)
                st.session_state.full_scan_results = {
                    "missing":      missing_list,
                    "total_swag":   total_swag,
                    "total_target": total_target,
                    "company":      full_scan_selected_label,
                    "target_cfg":   full_scan_target_cfg,
                }
            except Exception as e:
                st.error(f"❌ Scan failed: {e}")
                st.session_state.full_scan_results = None
        scan_placeholder.empty()


if st.session_state.get("full_scan_results"):
    res          = st.session_state.full_scan_results
    missing      = res["missing"]
    total_swag   = res["total_swag"]
    total_target = res["total_target"]
    company      = res["company"]

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Total in SWAG",      total_swag)
    c2.metric(f"✅ Already in {company}", total_target)
    c3.metric("❌ Missing",             len(missing))

    # Animated result banner
    _anim_scan_result_banner(len(missing), company)

    if len(missing) > 0:
        st.markdown(f"#### 📋 Missing Products ({len(missing)} items)")
        show_missing = missing[:500]
        df_missing = pd.DataFrame(show_missing)
        if len(missing) > 500:
            st.info(f"Showing first 500 of {len(missing)}. Download CSV for full list.")
        st.dataframe(df_missing, use_container_width=True, hide_index=True)

        csv_full = pd.DataFrame(missing).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Download Missing List CSV", csv_full,
            f"missing_{company}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv", use_container_width=False,
        )

        if st.button("➕ Create All Missing", type="primary", key="full_scan_create"):
            to_create        = missing
            total_to_create  = len(to_create)

            progress_bar  = st.progress(0, text="Starting parallel creation…")
            batch_status  = st.empty()   # dynamic text above bar
            errors_cont   = st.container()
            results_created = []

            missing_codes    = [item["code"] for item in to_create]
            swag_bulk_data   = fetch_products_bulk_from_swag(missing_codes)

            completed = 0

            def _create_one_full(product_info):
                code      = product_info["code"]
                prod_data = swag_bulk_data.get(code)
                if not prod_data:
                    return {"code": code, "name": product_info["name"],
                            "status": "skipped", "reason": "Not found in SWAG",
                            "variant": "", "new_id": None}
                try:
                    new_id = create_product_in_target(res["target_cfg"], prod_data)
                    return {"code": code, "name": product_info["name"],
                            "status": "created", "reason": "",
                            "variant": ", ".join(prod_data.get("attributes", [])),
                            "new_id": new_id}
                except Exception as exc:
                    return {"code": code, "name": product_info["name"],
                            "status": "error", "reason": parse_odoo_error(exc),
                            "variant": ", ".join(prod_data.get("attributes", []) if prod_data else []),
                            "raw_error": str(exc), "new_id": None}

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(_create_one_full, info): info for info in to_create}
                for future in as_completed(futures):
                    result = future.result()
                    results_created.append(result)
                    completed += 1
                    pct = int(completed / total_to_create * 100)
                    progress_bar.progress(
                        completed / total_to_create,
                        text=f"⚡ Creating {completed} / {total_to_create} ({pct}%)…"
                    )
                    batch_status.markdown(
                        f"🔄 **{completed} / {total_to_create}** completed &nbsp;"
                        f"<small style='color:#888'>{pct}%</small>",
                        unsafe_allow_html=True,
                    )
                    if result["status"] == "error":
                        with errors_cont:
                            st.markdown(
                                f"<div class='error-card'>"
                                f"<strong>❌ {result['code']}</strong> — {result['name']}<br>"
                                f"<strong>Variant:</strong> {result['variant'] or '—'}<br>"
                                f"<strong>⚠️ Reason:</strong> {result['reason']}<br>"
                                f"<strong>🔍 Raw:</strong> {result.get('raw_error','')[:200]}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

            progress_bar.empty()
            batch_status.empty()

            created = sum(1 for r in results_created if r["status"] == "created")
            skipped = sum(1 for r in results_created if r["status"] == "skipped")
            errors  = sum(1 for r in results_created if r["status"] == "error")

            _anim_creation_result_banner(errors)

            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Created", created)
            c2.metric("⚠️ Skipped", skipped)
            c3.metric("❌ Failed",  errors)

            success_list = [
                {"Code": r["code"], "Name": r["name"], "Variant": r["variant"], "New ID": r["new_id"]}
                for r in results_created if r["status"] == "created"
            ]
            failed_list = [
                {"Code": r["code"], "Name": r["name"], "Variant": r["variant"], "Error Reason": r["reason"]}
                for r in results_created if r["status"] == "error"
            ]
            if success_list:
                st.download_button(
                    "⬇️ Download Success List (CSV)",
                    pd.DataFrame(success_list).to_csv(index=False).encode("utf-8-sig"),
                    f"success_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv",
                )
            if failed_list:
                st.download_button(
                    "⬇️ Download Failed List (CSV)",
                    pd.DataFrame(failed_list).to_csv(index=False).encode("utf-8-sig"),
                    f"failed_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv",
                )

            st.session_state.sync_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "company":   company,
                "total":     total_to_create,
                "created":   created,
                "skipped":   skipped,
                "errors":    errors,
                "retried":   0,
            })
            st.session_state.full_scan_results = None
            st.rerun()

st.markdown("---")
st.markdown("###  Manual Sync (Targeted Products)")
st.markdown("For specific product codes, use the manual method below.")

# ─────────────────────────────────────────────────────────────────────────────
# MANUAL SYNC
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="section-header"><span class="step-circle">1</span><h3>Target Company</h3></div>',
    unsafe_allow_html=True,
)
company_map = {
    "La Rouche":        "LAROUCHE",
    "Fashion Limits":   "FASHION_LIMITS",
    "Different Clothes": "DIFFC",
}
selected_company_label = st.selectbox(
    "🎯 Target Company", list(company_map.keys()), key="sync_company",
)
target_key = company_map[selected_company_label]
target_cfg = st.secrets.get(target_key)
if not target_cfg:
    st.error(f"❌ Secrets missing for {selected_company_label}.")
    st.stop()

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

st.markdown(
    '<div class="section-header"><span class="step-circle">2</span><h3>Product Codes Input</h3></div>',
    unsafe_allow_html=True,
)
input_method = st.radio(
    "Input method", ["Manual entry", "Upload PDF invoice"], horizontal=True, key="sync_method",
)

codes = []
if input_method == "Manual entry":
    raw_codes = st.text_area(
        "Enter product codes (one per line)", height=150,
        placeholder="XP6013\nRVT196\nABC123", key="sync_manual_codes",
    )
    codes = [c.strip() for c in raw_codes.splitlines() if c.strip()]
else:
    pdf_file = st.file_uploader("Upload PDF invoice", type=["pdf"], key="sync_pdf")
    if pdf_file:
        with st.spinner("Parsing PDF…"):
            parsed = parse_invoice_pdf_cached(pdf_file.read())
        if parsed:
            codes = list(dict.fromkeys([item["code"] for item in parsed]))
            st.success(f"✅ {len(codes)} unique codes extracted.")
        else:
            st.warning("No codes found in PDF.")

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# Step 3 — Check
if st.button("🔍 Check Products", type="primary", key="sync_check"):
    if not codes:
        st.warning("Please enter at least one product code.")
    else:
        with st.spinner("Checking codes in batch (2 API calls)…"):
            check_results = batch_check_products(codes, target_cfg)
            st.session_state.check_results = check_results

            missing_list = [r for r in check_results if r["status"] == "missing"]
            missing_products_data = []
            if missing_list:
                missing_codes = [r["code"] for r in missing_list]
                swag_bulk = fetch_products_bulk_from_swag(missing_codes)
                for r in missing_list:
                    prod = swag_bulk.get(r["code"], {})
                    attrs = prod.get("attributes", [])
                    missing_products_data.append({
                        "code":     r["code"],
                        "name":     r["name"],
                        "category": prod.get("categ_name") or "—",
                        "brand":    prod.get("brand_name") or "—",
                        "variant":  ", ".join(attrs) if attrs else "—",
                    })
            st.session_state.missing_products_data = missing_products_data

        # Animated completion banner
        _anim_check_complete_banner()


# Display check results
if st.session_state.check_results:
    results     = st.session_state.check_results
    total       = len(results)
    exists_ct   = sum(1 for r in results if r["status"] == "exists")
    missing_ct  = sum(1 for r in results if r["status"] == "missing")
    not_swag_ct = sum(1 for r in results if r["status"] == "not_in_swag")

    st.markdown("### 📊 Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total Codes",    total)
    c2.metric("✅ Already Exists", exists_ct)
    c3.metric("❌ Missing",        missing_ct)
    c4.metric("⚠️ Not in SWAG",   not_swag_ct)
    st.markdown("---")

    if missing_ct > 0 and st.session_state.missing_products_data:
        st.markdown("### 📋 Products to Create")
        df_missing = pd.DataFrame(st.session_state.missing_products_data)
        df_missing.insert(0, "Select", True)

        edited_df = st.data_editor(
            df_missing,
            column_config={
                "Select":   st.column_config.CheckboxColumn("Create?", default=True),
                "variant":  st.column_config.TextColumn("Variant", width="medium"),
            },
            disabled=["code", "name", "category", "brand", "variant"],
            hide_index=True,
            use_container_width=True,
        )
        selected_codes = edited_df[edited_df["Select"]]["code"].tolist()

        if st.button("➕ Create Selected Products", type="primary", key="create_selected"):
            if not selected_codes:
                st.warning("No products selected for creation.")
            else:
                to_create       = [r for r in st.session_state.missing_products_data if r["code"] in selected_codes]
                total_to_create = len(to_create)

                progress_bar    = st.progress(0, text="Starting parallel creation…")
                batch_status    = st.empty()
                errors_cont     = st.container()
                results_created = []

                swag_bulk_data  = fetch_products_bulk_from_swag([item["code"] for item in to_create])
                completed       = 0

                def _create_one_manual(product_info):
                    code      = product_info["code"]
                    prod_data = swag_bulk_data.get(code)
                    if not prod_data:
                        return {"code": code, "name": product_info["name"],
                                "status": "skipped", "reason": "Not found in SWAG",
                                "variant": product_info.get("variant", ""), "new_id": None}
                    try:
                        new_id = create_product_in_target(target_cfg, prod_data)
                        return {"code": code, "name": product_info["name"],
                                "status": "created", "reason": "",
                                "variant": ", ".join(prod_data.get("attributes", [])),
                                "new_id": new_id}
                    except Exception as exc:
                        return {"code": code, "name": product_info["name"],
                                "status": "error", "reason": parse_odoo_error(exc),
                                "variant": ", ".join(prod_data.get("attributes", []) if prod_data else []),
                                "raw_error": str(exc), "new_id": None}

                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {executor.submit(_create_one_manual, info): info for info in to_create}
                    for future in as_completed(futures):
                        result = future.result()
                        results_created.append(result)
                        completed += 1
                        pct = int(completed / total_to_create * 100)
                        progress_bar.progress(
                            completed / total_to_create,
                            text=f"⚡ Creating {completed} / {total_to_create} ({pct}%)…"
                        )
                        batch_status.markdown(
                            f"🔄 **{completed} / {total_to_create}** completed &nbsp;"
                            f"<small style='color:#888'>{pct}%</small>",
                            unsafe_allow_html=True,
                        )
                        if result["status"] == "error":
                            with errors_cont:
                                st.markdown(
                                    f"<div class='error-card'>"
                                    f"<strong>❌ {result['code']}</strong> — {result['name']}<br>"
                                    f"<strong>Variant:</strong> {result['variant'] or '—'}<br>"
                                    f"<strong>⚠️ Reason:</strong> {result['reason']}<br>"
                                    f"<strong>🔍 Raw:</strong> {result.get('raw_error','')[:200]}"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )

                progress_bar.empty()
                batch_status.empty()

                created = sum(1 for r in results_created if r["status"] == "created")
                skipped = sum(1 for r in results_created if r["status"] == "skipped")
                errors  = sum(1 for r in results_created if r["status"] == "error")

                _anim_creation_result_banner(errors)

                c1, c2, c3 = st.columns(3)
                c1.metric("✅ Created", created)
                c2.metric("⚠️ Skipped", skipped)
                c3.metric("❌ Failed",  errors)

                success_list = [
                    {"Code": r["code"], "Name": r["name"], "Variant": r["variant"], "New ID": r["new_id"]}
                    for r in results_created if r["status"] == "created"
                ]
                failed_list = [
                    {"Code": r["code"], "Name": r["name"], "Variant": r["variant"], "Error Reason": r["reason"]}
                    for r in results_created if r["status"] == "error"
                ]
                if success_list:
                    st.download_button(
                        "⬇️ Download Success List (CSV)",
                        pd.DataFrame(success_list).to_csv(index=False).encode("utf-8-sig"),
                        f"success_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv",
                    )
                if failed_list:
                    st.download_button(
                        "⬇️ Download Failed List (CSV)",
                        pd.DataFrame(failed_list).to_csv(index=False).encode("utf-8-sig"),
                        f"failed_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv",
                    )

                # Retry failed
                if errors > 0:
                    if st.button("🔄 Retry Failed", type="secondary", key="retry_failed"):
                        for r in results_created:
                            if r["status"] == "error":
                                st.session_state.retry_counts[r["code"]] = (
                                    st.session_state.retry_counts.get(r["code"], 0) + 1
                                )
                        to_retry = [
                            r for r in results_created
                            if r["status"] == "error"
                            and st.session_state.retry_counts.get(r["code"], 0) <= 2
                        ]
                        if not to_retry:
                            st.info("No products eligible for retry (max 2 attempts reached).")
                        else:
                            st.session_state.missing_products_data = [
                                {"code": r["code"], "name": r["name"],
                                 "category": "", "brand": "", "variant": r.get("variant", "")}
                                for r in to_retry
                            ]
                            st.rerun()

                st.session_state.sync_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "company":   selected_company_label,
                    "total":     total_to_create,
                    "created":   created,
                    "skipped":   skipped,
                    "errors":    errors,
                    "retried":   len([
                        r for r in results_created
                        if r["status"] == "error"
                        and st.session_state.retry_counts.get(r["code"], 0) > 0
                    ]),
                })

                st.session_state.check_results = None
                st.session_state.missing_products_data = None
                st.rerun()

    else:
        if missing_ct == 0:
            st.markdown(
                '<div class="empty-state">✨ All products already exist — no action needed.</div>',
                unsafe_allow_html=True,
            )
        elif not st.session_state.missing_products_data:
            st.info("No missing products found.")

elif (
    st.session_state.check_results
    and sum(1 for r in st.session_state.check_results if r["status"] == "missing") == 0
):
    st.markdown(
        '<div class="empty-state">✨ All products already exist — no action needed.</div>',
        unsafe_allow_html=True,
    )
