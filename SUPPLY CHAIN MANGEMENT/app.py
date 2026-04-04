"""
Luxury Multi-Company Sales & Purchase Analytics
Version 1.2 — Paginated Tables + Premium KPI Cards

Changes:
- KPI card numbers now use smaller font (1.4rem) with adjusted padding to prevent overflow
- Full luxury theme refresh: matte black background, gold/champagne accents, soft ivory text
- Tables now have pagination controls (rows per page, page navigation) while preserving export functionality
- Pagination applied to both Sales and Purchase detail tables
- No changes to charts, filters, or data fetching logic
"""

import io
import hashlib
import time
import xmlrpc.client
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

st.set_page_config(
    page_title="SWAG ODOO 4 COMPANY ANOTHER CONNECTED TO EACH OTHER — Multi-Company",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# LUXURY CSS — Updated with better KPI card sizing and refined aesthetics
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    box-sizing: border-box;
}

/* ── App Background – deep matte black ── */
.stApp {
    background: #0a0a0c;
    min-height: 100vh;
}

/* ── Sidebar – dark charcoal ── */
section[data-testid="stSidebar"] {
    background: #111114 !important;
    border-right: 1px solid #2a2a2e !important;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {
    color: #d4c5a9 !important;
}
section[data-testid="stSidebar"] input {
    color: #0a0a0c !important;
}

/* ── Typography – soft ivory ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Cormorant Garamond', serif !important;
    color: #f5efe6 !important;
    letter-spacing: 0.02em;
}

/* ── Main Header ── */
.lux-header {
    text-align: center;
    padding: 32px 0 28px;
    border-bottom: 1px solid #2a2a2e;
    margin-bottom: 32px;
}
.lux-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.6rem;
    font-weight: 600;
    color: #d4af6a;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.lux-subtitle {
    font-size: 0.85rem;
    color: #6e6e78;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    font-weight: 400;
}
.lux-company-badge {
    display: inline-block;
    margin-top: 12px;
    background: linear-gradient(135deg, #d4af6a22, #a07a4022);
    border: 1px solid #d4af6a44;
    border-radius: 4px;
    padding: 5px 18px;
    font-size: 0.75rem;
    color: #d4af6a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-weight: 600;
}

/* ── KPI Cards – improved number fitting ── */
[data-testid="stMetric"] {
    background: #16161a !important;
    border: 1px solid #2a2a2e !important;
    border-radius: 8px !important;
    padding: 12px 18px !important;          /* reduced vertical padding */
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    border-color: #d4af6a55 !important;
    box-shadow: 0 4px 24px #d4af6a11;
}
[data-testid="stMetricLabel"] {
    color: #6e6e78 !important;
    font-size: 0.68rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.4rem !important;           /* reduced from 2rem to fit large numbers */
    font-weight: 600 !important;
    color: #d4af6a !important;
    line-height: 1.2 !important;
    word-break: break-word !important;
    white-space: normal !important;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #2a2a2e;
}
.section-header-text {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: #f5efe6;
    letter-spacing: 0.04em;
}
.section-accent {
    width: 3px;
    height: 20px;
    background: linear-gradient(180deg, #d4af6a, #6b8f71);
    border-radius: 2px;
}

/* ── Buttons ── */
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #d4af6a, #a07a40) !important;
    border: none !important;
    border-radius: 4px !important;
    color: #0a0a0c !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    transition: opacity 0.2s !important;
}
.stButton button[kind="primary"]:hover {
    opacity: 0.88 !important;
}
.stButton button[kind="secondary"] {
    background: #16161a !important;
    border: 1px solid #2a2a2e !important;
    border-radius: 4px !important;
    color: #d4c5a9 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
}
.stButton button[kind="secondary"]:hover {
    border-color: #d4af6a66 !important;
    color: #d4af6a !important;
}

/* ── Download Buttons ── */
.stDownloadButton button {
    background: #16161a !important;
    border: 1px solid #2a2a2e !important;
    border-radius: 4px !important;
    color: #d4c5a9 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    padding: 7px 16px !important;
    transition: border-color 0.2s, color 0.2s !important;
}
.stDownloadButton button:hover {
    border-color: #d4af6a66 !important;
    color: #d4af6a !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: #16161a !important;
    border: 1px solid #2a2a2e !important;
    border-radius: 4px !important;
    color: #f5efe6 !important;
    caret-color: #d4af6a !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #d4af6a66 !important;
    box-shadow: 0 0 0 2px #d4af6a1a !important;
}
.stTextInput label, .stTextArea label, .stNumberInput label,
.stDateInput label, .stSelectbox label, .stMultiSelect label {
    color: #6e6e78 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
}

/* ── Select / Multiselect ── */
[data-baseweb="select"] div {
    background: #16161a !important;
    color: #f5efe6 !important;
    border-color: #2a2a2e !important;
}
[data-baseweb="tag"] {
    background: #d4af6a22 !important;
    color: #d4af6a !important;
    border: 1px solid #d4af6a44 !important;
}

/* ── Radio ── */
.stRadio label, div[data-testid="stRadio"] p {
    color: #d4c5a9 !important;
}

/* ── Banners ── */
.info-banner {
    background: #16161a;
    border-left: 3px solid #4a7c5e;
    border-radius: 4px;
    padding: 10px 16px;
    margin: 8px 0 16px;
    font-size: 0.83rem;
    color: #8ab49a !important;
}
.warn-banner {
    background: #16161a;
    border-left: 3px solid #b8963e;
    border-radius: 4px;
    padding: 10px 16px;
    margin: 8px 0 16px;
    font-size: 0.83rem;
    color: #d4af6a !important;
}
.alert-banner {
    background: #1a1216;
    border-left: 3px solid #8b4a5a;
    border-radius: 4px;
    padding: 10px 16px;
    margin: 8px 0 16px;
    font-size: 0.83rem;
    color: #c4848f !important;
}

/* ── Paginated Table Styling (luxury, sticky header effect) ── */
.lux-wrap {
    width: 100%;
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid #2a2a2e;
    margin-bottom: 12px;
}
.lux-tbl {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
}
.lux-tbl thead tr {
    background: #1a1a1e;
    border-bottom: 1px solid #d4af6a33;
}
.lux-tbl thead th {
    color: #6e6e78;
    font-weight: 600;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 12px 14px;
    text-align: left;
    white-space: nowrap;
    position: sticky;
    top: 0;
    background: #1a1a1e;
    z-index: 10;
}
.lux-tbl thead th:first-child { border-radius: 8px 0 0 0; }
.lux-tbl thead th:last-child  { border-radius: 0 8px 0 0; }
.lux-tbl tbody tr { transition: background 0.1s; }
.lux-tbl tbody tr:nth-child(odd)  { background: #111114; }
.lux-tbl tbody tr:nth-child(even) { background: #13131a; }
.lux-tbl tbody td {
    padding: 9px 14px;
    color: #c8c0b4;
    border-bottom: 1px solid #1e1e22;
    text-align: left;
}
.lux-tbl tbody td.lux-key {
    color: #d4af6a;
    font-weight: 600;
    font-size: 0.8rem;
}
.lux-tbl tbody tr:hover td { background: #1e1a12 !important; color: #f5efe6 !important; }
.lux-tbl tbody tr:hover td.lux-key { color: #e0c080 !important; }

/* Pagination controls container */
.pagination-container {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 16px;
    margin-top: 12px;
    flex-wrap: wrap;
}
.pagination-control {
    display: flex;
    gap: 8px;
    align-items: center;
}

/* ── Login Card ── */
.lux-login-card {
    background: #111114;
    border: 1px solid #2a2a2e;
    border-radius: 8px;
    padding: 36px 40px;
    width: 100%;
}
.lux-login-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 600;
    color: #d4af6a;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 4px;
}
.lux-login-sub {
    font-size: 0.75rem;
    color: #4e4e58;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 28px;
}

/* ── Sidebar Nav ── */
.nav-company-label {
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4e4e58 !important;
    margin-bottom: 6px;
    display: block;
}
.active-indicator {
    background: #1e1a12;
    border: 1px solid #d4af6a33;
    border-left: 3px solid #d4af6a;
    border-radius: 4px;
    padding: 7px 12px;
    font-size: 0.78rem;
    color: #d4af6a !important;
    margin-top: 6px;
    letter-spacing: 0.06em;
}

/* ── Divider ── */
hr {
    border: none !important;
    height: 1px !important;
    background: #2a2a2e !important;
    margin: 20px 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0a0a0c; }
::-webkit-scrollbar-thumb { background: #2a2a2e; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #d4af6a44; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #111114 !important;
    border: 1px solid #2a2a2e !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p { color: #d4c5a9 !important; }

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #4e4e58 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.06em;
}

/* ── Progress ── */
[data-testid="stProgressBar"] > div {
    background: linear-gradient(90deg, #d4af6a, #6b8f71) !important;
}

footer { visibility: hidden; }
.mono { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: #d4af6a; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]

COMPANY_DISPLAY = {
    "SWAG"          : "SWAG",
    "LAROUCHE"      : "LAROUCHE",
    "DIFFC"         : "DIFFC",
    "FASHION_LIMITS": "FASHION LIMITS",
}

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    return ar if get_lang() == "AR" else en

def get_system_name(key):
    cfg = st.secrets.get(key, {})
    if get_lang() == "AR":
        return cfg.get("name_ar", cfg.get("name", COMPANY_DISPLAY.get(key, key)))
    return cfg.get("name", COMPANY_DISPLAY.get(key, key))

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated"    : False,
    "user_email"       : "",
    "lang"             : "EN",
    "analytics_view"   : "sales",       # "sales" | "purchase"
    "selected_company" : "SWAG",
    "sales_df"         : None,
    "purchase_df"      : None,
    "sales_company"    : None,
    "purchase_company" : None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# SESSION LOGIN
# ─────────────────────────────────────────────────────────────────────────────
_COOKIE_SECRET = "luxury_analytics_2025"

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
def _proxy(url, endpoint):
    return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{endpoint}", allow_none=True)

@st.cache_data(ttl=28800, show_spinner=False)
def _auth(url, db, user, key):
    try:
        uid = _proxy(url, "common").authenticate(db, user, key, {})
        return uid or None
    except Exception:
        return None

def _rpc(url, db, uid, key, model, method, domain, kwargs):
    return _proxy(url, "object").execute_kw(db, uid, key, model, method, domain, kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# GENERIC FETCH: SALES HISTORY
# ─────────────────────────────────────────────────────────────────────────────

_SALE_STATES     = ["draft", "sent", "sale", "done"]
_PURCHASE_STATES = ["draft", "sent", "to approve", "purchase", "done"]


@st.cache_data(ttl=900, show_spinner=False)
def fetch_sales_history(system_key: str, model_code: str, date_from: str, date_to: str) -> pd.DataFrame:
    """
    Fetch sales order lines from any configured system.

    Args:
        system_key : one of SYSTEM_KEYS — key into st.secrets
        model_code : product default_code exact filter, or '' / None for all
        date_from  : 'YYYY-MM-DD'
        date_to    : 'YYYY-MM-DD'

    Returns:
        DataFrame with columns:
        Date, SO, Customer, Brand Category, Category,
        Model Code, Product, Qty, Unit Price, Subtotal
    """
    cols  = ["Date", "SO", "Customer", "Brand Category", "Category",
             "Model Code", "Product", "Qty", "Unit Price", "Subtotal"]
    empty = pd.DataFrame(columns=cols)

    # ── 1. Secrets check ────────────────────────────────────────────────────
    cfg = st.secrets.get(system_key)
    if not cfg:
        st.error(
            f"❌ **[{system_key}]** section is missing from `secrets.toml`. "
            f"Add `[{system_key}]` with url / db / user / api_key."
        )
        return empty

    for required_key in ("url", "db", "user", "api_key"):
        if required_key not in cfg:
            st.error(f"❌ `secrets.toml [{system_key}]` is missing the key `{required_key}`.")
            return empty

    # ── 2. Authentication ────────────────────────────────────────────────────
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        st.error(
            f"❌ Authentication failed for **{system_key}** "
            f"(`{cfg['db']}` @ `{cfg['url']}`). "
            "Check your Odoo user credentials in secrets.toml."
        )
        return empty

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]

    # ── 3. Build domain ──────────────────────────────────────────────────────
    mc_clean = str(model_code).strip().upper() if model_code else ""

    domain = [
        ["order_id.state", "in", _SALE_STATES],
        ["order_id.date_order", ">=", f"{date_from} 00:00:00"],
        ["order_id.date_order", "<=", f"{date_to} 23:59:59"],
    ]
    if mc_clean:
        domain.append(["product_id.default_code", "=", mc_clean])

    # ── 4. Fetch order lines ─────────────────────────────────────────────────
    try:
        lines = _rpc(u, db, uid, ak, "sale.order.line", "search_read",
                     [domain],
                     {"fields": ["order_id", "product_id", "product_uom_qty", "price_unit"],
                      "limit": 20000,
                      "order": "order_id desc"})
    except Exception as exc:
        st.error(f"❌ RPC error fetching `sale.order.line` for **{system_key}**: `{exc}`")
        st.code(f"Domain used:\n{domain}", language="python")
        return empty

    if not lines:
        # Diagnostic: try without state filter to see if records exist at all
        try:
            domain_no_state = [c for c in domain if c[0] != "order_id.state"]
            fallback = _rpc(u, db, uid, ak, "sale.order.line", "search_read",
                            [domain_no_state],
                            {"fields": ["order_id"], "limit": 5})
            fallback_count = len(fallback)
        except Exception:
            fallback_count = -1

        if fallback_count > 0:
            st.warning(
                f"⚠️ **{system_key}** — The state filter `{_SALE_STATES}` returned 0 lines "
                f"but **{fallback_count}** lines exist for this date range with other states. "
                "Your orders may be in a state not covered by the filter. "
                "Check the `order_id.state` values in your Odoo instance."
            )
            st.code(f"Domain used:\n{domain}", language="python")
        elif fallback_count == 0:
            st.info(
                f"ℹ️ **{system_key}** — No `sale.order.line` records found for "
                f"{date_from} → {date_to}"
                + (f" with model `{mc_clean}`." if mc_clean else ".")
            )
            st.code(f"Domain used:\n{domain}", language="python")
        return empty

    # ── 5. Fetch related orders and products ─────────────────────────────────
    try:
        order_ids   = list({l["order_id"][0] for l in lines if isinstance(l.get("order_id"), list)})
        product_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})

        orders = _rpc(u, db, uid, ak, "sale.order", "search_read",
                      [[["id", "in", order_ids]]],
                      {"fields": ["id", "name", "partner_id", "date_order"],
                       "limit": len(order_ids) + 10})
        order_map = {o["id"]: o for o in orders}

        products = _rpc(u, db, uid, ak, "product.product", "search_read",
                        [[["id", "in", product_ids]]],
                        {"fields": ["id", "default_code", "display_name",
                                    "categ_id", "product_tmpl_id"],
                         "limit": len(product_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        tmpl_ids = list({p["product_tmpl_id"][0] for p in products
                         if isinstance(p.get("product_tmpl_id"), list)})
        tmpl_map = {}
        if tmpl_ids:
            try:
                tmpls = _rpc(u, db, uid, ak, "product.template", "search_read",
                             [[["id", "in", tmpl_ids]]],
                             {"fields": ["id", "x_brand_category_id"],
                              "limit": len(tmpl_ids) + 10})
                tmpl_map = {tmpl_["id"]: tmpl_ for tmpl_ in tmpls}
            except Exception as exc:
                st.warning(
                    f"⚠️ Could not fetch `x_brand_category_id` for **{system_key}** "
                    f"(field may not exist): `{exc}`. Brand Category will be empty."
                )
                tmpl_map = {}

    except Exception as exc:
        st.error(f"❌ RPC error fetching orders/products for **{system_key}**: `{exc}`")
        return empty

    # ── 6. Build rows ────────────────────────────────────────────────────────
    rows = []
    for line in lines:
        oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
        pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
        order = order_map.get(oid, {})
        prod  = prod_map.get(pid, {})

        raw_date = order.get("date_order") or ""
        try:
            date_str = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        except Exception:
            date_str = raw_date[:10] if raw_date else ""

        partner  = order.get("partner_id")
        customer = (str(partner[1]) if isinstance(partner, list) and len(partner) > 1
                    else str(partner or ""))

        categ    = prod.get("categ_id")
        category = (str(categ[1]) if isinstance(categ, list) and len(categ) > 1
                    else str(categ or ""))

        brand_category = ""
        tmpl_ref = prod.get("product_tmpl_id")
        if isinstance(tmpl_ref, list) and tmpl_ref:
            tmpl_ = tmpl_map.get(tmpl_ref[0], {})
            bc    = tmpl_.get("x_brand_category_id")
            brand_category = (str(bc[1]) if isinstance(bc, list) and len(bc) > 1
                              else (str(bc) if bc else ""))

        qty        = float(line.get("product_uom_qty") or 0)
        unit_price = float(line.get("price_unit") or 0)

        rows.append({
            "Date"          : date_str,
            "SO"            : str(order.get("name") or ""),
            "Customer"      : customer,
            "Brand Category": brand_category,
            "Category"      : category,
            "Model Code"    : str(prod.get("default_code") or ""),
            "Product"       : str(prod.get("display_name") or ""),
            "Qty"           : qty,
            "Unit Price"    : unit_price,
            "Subtotal"      : round(qty * unit_price, 2),
        })

    if not rows:
        st.info(
            f"ℹ️ **{system_key}** — Lines were fetched but produced no processable rows. "
            "This is unexpected — check the RPC field mappings."
        )
        return empty

    df = pd.DataFrame(rows)
    for col in ["Customer", "Brand Category", "Category", "Model Code", "Product", "SO", "Date"]:
        df[col] = df[col].fillna("").astype(str)
    return df.sort_values("Date", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# GENERIC FETCH: PURCHASE HISTORY
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def fetch_purchase_history(system_key: str, model_code: str, date_from: str, date_to: str) -> pd.DataFrame:
    """
    Fetch purchase order lines from any configured system.

    Args:
        system_key : one of SYSTEM_KEYS — key into st.secrets
        model_code : product default_code exact filter, or '' / None for all
        date_from  : 'YYYY-MM-DD'
        date_to    : 'YYYY-MM-DD'

    Returns:
        DataFrame with columns:
        Date, PO, Vendor, Brand Category, Category,
        Model Code, Product, Qty, Unit Price, Subtotal
    """
    cols  = ["Date", "PO", "Vendor", "Brand Category", "Category",
             "Model Code", "Product", "Qty", "Unit Price", "Subtotal"]
    empty = pd.DataFrame(columns=cols)

    # ── 1. Secrets check ────────────────────────────────────────────────────
    cfg = st.secrets.get(system_key)
    if not cfg:
        st.error(
            f"❌ **[{system_key}]** section is missing from `secrets.toml`. "
            f"Add `[{system_key}]` with url / db / user / api_key."
        )
        return empty

    for required_key in ("url", "db", "user", "api_key"):
        if required_key not in cfg:
            st.error(f"❌ `secrets.toml [{system_key}]` is missing the key `{required_key}`.")
            return empty

    # ── 2. Authentication ────────────────────────────────────────────────────
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        st.error(
            f"❌ Authentication failed for **{system_key}** "
            f"(`{cfg['db']}` @ `{cfg['url']}`). "
            "Check your Odoo user credentials in secrets.toml."
        )
        return empty

    u, db, ak = cfg["url"], cfg["db"], cfg["api_key"]

    # ── 3. Build domain ──────────────────────────────────────────────────────
    mc_clean = str(model_code).strip().upper() if model_code else ""

    domain = [
        ["order_id.state", "in", _PURCHASE_STATES],
        ["order_id.date_order", ">=", f"{date_from} 00:00:00"],
        ["order_id.date_order", "<=", f"{date_to} 23:59:59"],
    ]
    if mc_clean:
        domain.append(["product_id.default_code", "=", mc_clean])

    # ── 4. Fetch order lines ─────────────────────────────────────────────────
    try:
        lines = _rpc(u, db, uid, ak, "purchase.order.line", "search_read",
                     [domain],
                     {"fields": ["order_id", "product_id", "product_qty", "price_unit"],
                      "limit": 10000,
                      "order": "order_id desc"})
    except Exception as exc:
        st.error(f"❌ RPC error fetching `purchase.order.line` for **{system_key}**: `{exc}`")
        st.code(f"Domain used:\n{domain}", language="python")
        return empty

    if not lines:
        try:
            domain_no_state = [c for c in domain if c[0] != "order_id.state"]
            fallback = _rpc(u, db, uid, ak, "purchase.order.line", "search_read",
                            [domain_no_state],
                            {"fields": ["order_id"], "limit": 5})
            fallback_count = len(fallback)
        except Exception:
            fallback_count = -1

        if fallback_count > 0:
            st.warning(
                f"⚠️ **{system_key}** — The state filter `{_PURCHASE_STATES}` returned 0 lines "
                f"but **{fallback_count}** lines exist for this date range with other states. "
                "Your purchase orders may be in a state not included in the filter. "
                "Check the `order_id.state` values in your Odoo instance — common values are "
                "`draft`, `sent`, `to approve`, `purchase`, `done`."
            )
            st.code(f"Domain used:\n{domain}", language="python")
        elif fallback_count == 0:
            st.info(
                f"ℹ️ **{system_key}** — No `purchase.order.line` records found for "
                f"{date_from} → {date_to}"
                + (f" with model `{mc_clean}`." if mc_clean else ".")
            )
            st.code(f"Domain used:\n{domain}", language="python")
        return empty

    # ── 5. Fetch related orders and products ─────────────────────────────────
    try:
        order_ids   = list({l["order_id"][0] for l in lines if isinstance(l.get("order_id"), list)})
        product_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})

        orders = _rpc(u, db, uid, ak, "purchase.order", "search_read",
                      [[["id", "in", order_ids]]],
                      {"fields": ["id", "name", "partner_id", "date_order"],
                       "limit": len(order_ids) + 10})
        order_map = {o["id"]: o for o in orders}

        products = _rpc(u, db, uid, ak, "product.product", "search_read",
                        [[["id", "in", product_ids]]],
                        {"fields": ["id", "default_code", "display_name",
                                    "categ_id", "product_tmpl_id"],
                         "limit": len(product_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        tmpl_ids = list({p["product_tmpl_id"][0] for p in products
                         if isinstance(p.get("product_tmpl_id"), list)})
        tmpl_map = {}
        if tmpl_ids:
            try:
                tmpls = _rpc(u, db, uid, ak, "product.template", "search_read",
                             [[["id", "in", tmpl_ids]]],
                             {"fields": ["id", "x_brand_category_id"],
                              "limit": len(tmpl_ids) + 10})
                tmpl_map = {tmpl_["id"]: tmpl_ for tmpl_ in tmpls}
            except Exception as exc:
                st.warning(
                    f"⚠️ Could not fetch `x_brand_category_id` for **{system_key}** "
                    f"(field may not exist): `{exc}`. Brand Category will be empty."
                )
                tmpl_map = {}

    except Exception as exc:
        st.error(f"❌ RPC error fetching orders/products for **{system_key}**: `{exc}`")
        return empty

    # ── 6. Build rows ────────────────────────────────────────────────────────
    rows = []
    for line in lines:
        oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
        pid = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
        order = order_map.get(oid, {})
        prod  = prod_map.get(pid, {})

        raw_date = order.get("date_order") or ""
        try:
            date_str = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        except Exception:
            date_str = raw_date[:10] if raw_date else ""

        partner = order.get("partner_id")
        vendor  = (str(partner[1]) if isinstance(partner, list) and len(partner) > 1
                   else str(partner or ""))

        categ    = prod.get("categ_id")
        category = (str(categ[1]) if isinstance(categ, list) and len(categ) > 1
                    else str(categ or ""))

        brand_category = ""
        tmpl_ref = prod.get("product_tmpl_id")
        if isinstance(tmpl_ref, list) and tmpl_ref:
            tmpl_ = tmpl_map.get(tmpl_ref[0], {})
            bc    = tmpl_.get("x_brand_category_id")
            brand_category = (str(bc[1]) if isinstance(bc, list) and len(bc) > 1
                              else (str(bc) if bc else ""))

        qty        = float(line.get("product_qty") or 0)
        unit_price = float(line.get("price_unit") or 0)

        rows.append({
            "Date"          : date_str,
            "PO"            : str(order.get("name") or ""),
            "Vendor"        : vendor,
            "Brand Category": brand_category,
            "Category"      : category,
            "Model Code"    : str(prod.get("default_code") or ""),
            "Product"       : str(prod.get("display_name") or ""),
            "Qty"           : qty,
            "Unit Price"    : unit_price,
            "Subtotal"      : round(qty * unit_price, 2),
        })

    if not rows:
        st.info(
            f"ℹ️ **{system_key}** — Lines were fetched but produced no processable rows. "
            "This is unexpected — check the RPC field mappings."
        )
        return empty

    df = pd.DataFrame(rows)
    for col in ["Vendor", "Brand Category", "Category", "Model Code", "Product", "PO", "Date"]:
        df[col] = df[col].fillna("").astype(str)
    return df.sort_values("Date", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _styled_excel(df: pd.DataFrame, sheet_name: str, accent_hex: str = "D4AF6A") -> bytes:
    """Create a styled Excel workbook from a DataFrame."""
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        ws = writer.sheets[sheet_name[:31]]

        hdr_fill    = PatternFill("solid", fgColor="1A1A1E")
        hdr_font    = Font(bold=True, color=accent_hex, size=10, name="Calibri")
        hdr_align   = Alignment(horizontal="center", vertical="center")
        thin        = Side(border_style="thin", color="2A2A2E")
        border      = Border(left=thin, right=thin, top=thin, bottom=thin)
        alt_fill    = PatternFill("solid", fgColor="13131A")
        main_fill   = PatternFill("solid", fgColor="111114")
        normal_font = Font(name="Calibri", size=10, color="C8C0B4")
        key_font    = Font(name="Calibri", size=10, color=accent_hex, bold=True)
        num_align   = Alignment(horizontal="right", vertical="center")
        ctr_align   = Alignment(horizontal="center", vertical="center")
        total_fill  = PatternFill("solid", fgColor="1A1A12")
        total_font  = Font(bold=True, name="Calibri", color=accent_hex)

        max_row = ws.max_row
        max_col = ws.max_column

        ws.row_dimensions[1].height = 26
        for col_num in range(1, max_col + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = hdr_fill; cell.font = hdr_font
            cell.alignment = hdr_align; cell.border = border

        col_names = [ws.cell(row=1, column=c).value for c in range(1, max_col + 1)]
        num_cols  = {"Qty", "Unit Price", "Subtotal"}

        for row in ws.iter_rows(min_row=2, max_row=max_row):
            for cell in row:
                cell.border = border
                col_name = col_names[cell.column - 1] if cell.column <= len(col_names) else ""
                is_num   = col_name in num_cols
                cell.font      = key_font if cell.column == 1 else normal_font
                cell.fill      = alt_fill if cell.row % 2 == 0 else main_fill
                cell.alignment = num_align if is_num else ctr_align
            ws.row_dimensions[row[0].row].height = 17

        for col_num in range(1, max_col + 1):
            col_letter = get_column_letter(col_num)
            max_len = max(
                (len(str(ws.cell(row=r, column=col_num).value or ""))
                 for r in range(1, max_row + 1)), default=8)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 48)

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(max_col)}{max_row}"

        total_row = max_row + 1
        ws.cell(row=total_row, column=1, value="TOTAL").font      = total_font
        ws.cell(row=total_row, column=1).fill      = total_fill
        ws.cell(row=total_row, column=1).alignment = Alignment(horizontal="center")

        for summary_col in ("Qty", "Subtotal"):
            if summary_col in col_names:
                ci = col_names.index(summary_col) + 1
                cl = get_column_letter(ci)
                ws.cell(row=total_row, column=ci, value=f"=SUM({cl}2:{cl}{max_row})")
                ws.cell(row=total_row, column=ci).font      = total_font
                ws.cell(row=total_row, column=ci).fill      = total_fill
                ws.cell(row=total_row, column=ci).alignment = Alignment(horizontal="center")

        ws.row_dimensions[total_row].height = 20
        ws.sheet_properties.tabColor = accent_hex

        footer_row = total_row + 2
        ws.cell(row=footer_row, column=1,
                value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Luxury Analytics")
        ws.cell(row=footer_row, column=1).font = Font(
            italic=True, color="4E4E58", size=8, name="Calibri")

        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToPage   = True
        ws.page_setup.fitToWidth  = 1
        ws.print_title_rows       = "1:1"
        ws.sheet_view.zoomScale   = 85

    return buf.getvalue()


def dl_filename(company: str, view: str, ext: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{company}_{view}_{ts}.{ext}"


# ─────────────────────────────────────────────────────────────────────────────
# ALTAIR CONFIG (luxury dark theme)
# ─────────────────────────────────────────────────────────────────────────────
_ALT_CFG = {
    "background"  : "transparent",
    "view"        : {"stroke": "transparent"},
    "axis"        : {
        "labelColor" : "#6e6e78",
        "titleColor" : "#6e6e78",
        "gridColor"  : "#1e1e22",
        "domainColor": "#2a2a2e",
        "tickColor"  : "#2a2a2e",
        "labelFont"  : "Inter",
        "titleFont"  : "Inter",
        "labelFontSize": 10,
    },
    "legend"      : {
        "labelColor": "#c8c0b4",
        "titleColor": "#6e6e78",
        "labelFont" : "Inter",
        "titleFont" : "Inter",
    },
    "title"       : {"color": "#f5efe6", "font": "Cormorant Garamond"},
}

_PALETTE = ["#d4af6a", "#6b8f71", "#7a8faf", "#b87c5a",
            "#9a7ab8", "#6aafaf", "#af8a6a", "#7a9a6a"]


def _bar_chart(df, x_field, y_field, color="#d4af6a", height=300, fmt=",.0f", angle=-35):
    tooltip_label = f"{y_field}_fmt"
    plot_df = df.copy()
    plot_df[tooltip_label] = plot_df[y_field].map(lambda v: f"{v:{fmt}}")

    return (
        alt.Chart(plot_df)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, opacity=0.85)
        .encode(
            x=alt.X(f"{x_field}:N", sort="-y",
                    axis=alt.Axis(labelAngle=angle, labelLimit=110), title=None),
            y=alt.Y(f"{y_field}:Q", title=y_field,
                    axis=alt.Axis(format="~s")),
            color=alt.condition(
                alt.datum[y_field] == plot_df[y_field].max(),
                alt.value("#e0c080"),
                alt.value(color),
            ),
            tooltip=[
                alt.Tooltip(f"{x_field}:N", title=x_field),
                alt.Tooltip(f"{tooltip_label}:N", title=y_field),
            ],
        )
        .properties(height=height)
        .configure(**_ALT_CFG)
        .interactive()
    )


def _line_chart(df, x_field, y_field, color="#d4af6a", height=260):
    line = (
        alt.Chart(df)
        .mark_line(color=color, strokeWidth=2, interpolate="monotone")
        .encode(
            x=alt.X(f"{x_field}:T", title=None,
                    axis=alt.Axis(format="%b %Y", labelAngle=-30)),
            y=alt.Y(f"{y_field}:Q", title=y_field,
                    axis=alt.Axis(format="~s")),
            tooltip=[
                alt.Tooltip(f"{x_field}:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip(f"{y_field}:Q", title=y_field, format=",.0f"),
            ],
        )
    )
    area = (
        alt.Chart(df)
        .mark_area(color=color, opacity=0.07, interpolate="monotone")
        .encode(
            x=alt.X(f"{x_field}:T"),
            y=alt.Y(f"{y_field}:Q"),
        )
    )
    points = (
        alt.Chart(df)
        .mark_circle(color=color, size=48, opacity=0.75)
        .encode(
            x=alt.X(f"{x_field}:T"),
            y=alt.Y(f"{y_field}:Q"),
            tooltip=[
                alt.Tooltip(f"{x_field}:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip(f"{y_field}:Q", title=y_field, format=",.0f"),
            ],
        )
    )
    return (
        (area + line + points)
        .properties(height=height)
        .configure(**_ALT_CFG)
        .interactive()
    )


def _donut_chart(labels, values, title="", height=340):
    if not _HAS_PLOTLY:
        st.info("Install plotly for donut charts.")
        return

    colors = ["#d4af6a", "#6b8f71", "#7a8faf", "#b87c5a",
              "#9a7ab8", "#6aafaf", "#af8a6a", "#7a9a6a",
              "#a07a40", "#4a7c5e", "#5a6f8f", "#8f5e4a"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.56,
        marker=dict(colors=colors[:len(labels)],
                    line=dict(color="#0a0a0c", width=2)),
        textinfo="percent+label",
        textfont=dict(color="#c8c0b4", size=11, family="Inter"),
        hovertemplate="<b>%{label}</b><br>Value: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
    )])
    fig.update_layout(
        title=dict(text=title, font=dict(color="#6e6e78", size=11,
                   family="Inter"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        height=height,
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(
            font=dict(color="#c8c0b4", size=10, family="Inter"),
            bgcolor="rgba(17,17,20,0.8)",
            bordercolor="#2a2a2e",
            borderwidth=1,
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGINATED TABLE RENDERER (replaces old _render_table)
# ─────────────────────────────────────────────────────────────────────────────
_TBL_CSS = """<style>
.lux-wrap{width:100%;overflow-x:auto;border-radius:8px;border:1px solid #2a2a2e;margin-bottom:4px;}
.lux-tbl{width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:.82rem;}
.lux-tbl thead tr{background:#1a1a1e;border-bottom:1px solid #d4af6a33;}
.lux-tbl thead th{color:#6e6e78;font-weight:600;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;padding:11px 14px;text-align:left;white-space:nowrap;}
.lux-tbl tbody tr:nth-child(odd){background:#111114;}
.lux-tbl tbody tr:nth-child(even){background:#13131a;}
.lux-tbl tbody td{padding:8px 14px;color:#c8c0b4;border-bottom:1px solid #1e1e22;text-align:left;}
.lux-tbl tbody td.lux-key{color:#d4af6a;font-weight:600;font-size:.8rem;}
.lux-tbl tbody tr:hover td{background:#1e1a12!important;color:#f5efe6!important;}
.lux-tbl tbody tr:hover td.lux-key{color:#e0c080!important;}
</style>"""

def _render_paginated_table(df: pd.DataFrame, key_suffix: str = ""):
    """
    Render a DataFrame with pagination controls (rows per page, page navigation).
    """
    if df is None or df.empty:
        st.info(t("No data available.", "لا توجد بيانات."))
        return

    total_rows = len(df)
    
    # Pagination state – use session state to persist per table instance
    page_key = f"table_page_{key_suffix}"
    per_page_key = f"table_per_page_{key_suffix}"
    
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    if per_page_key not in st.session_state:
        st.session_state[per_page_key] = 25  # default rows per page
    
    per_page = st.session_state[per_page_key]
    total_pages = (total_rows + per_page - 1) // per_page
    current_page = st.session_state[page_key]
    
    # Ensure current page is valid
    if current_page >= total_pages:
        current_page = total_pages - 1 if total_pages > 0 else 0
        st.session_state[page_key] = current_page
    
    start_idx = current_page * per_page
    end_idx = min(start_idx + per_page, total_rows)
    
    # Slice the DataFrame
    df_page = df.iloc[start_idx:end_idx].copy()
    
    # Render table HTML
    cols = df_page.columns.tolist()
    thead = "".join(f"<th>{c}</th>" for c in cols)
    tbody = "".join(
        "<tr>" + "".join(
            f'<td class="lux-key">{v}</td>' if ci == 0 else f"<td>{v}</td>"
            for ci, v in enumerate(row)
        ) + "</tr>"
        for _, row in df_page.iterrows()
    )
    st.markdown(
        f'{_TBL_CSS}<div class="lux-wrap">'
        f'<table class="lux-tbl"><thead><tr>{thead}</tr></thead>'
        f'<tbody>{tbody}</tbody></table></div>',
        unsafe_allow_html=True
    )
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Rows per page selector
        per_page_options = [10, 25, 50, 100]
        selected_per_page = st.selectbox(
            t("Rows per page", "صفوف لكل صفحة"),
            options=per_page_options,
            index=per_page_options.index(per_page) if per_page in per_page_options else 1,
            key=f"per_page_sel_{key_suffix}",
            label_visibility="collapsed"
        )
        if selected_per_page != per_page:
            st.session_state[per_page_key] = selected_per_page
            st.session_state[page_key] = 0
            st.rerun()
    
    with col2:
        # Page navigation
        if total_pages > 1:
            page_cols = st.columns([1, 2, 1, 2, 1])
            with page_cols[0]:
                if st.button("◀", key=f"prev_{key_suffix}", use_container_width=True):
                    if current_page > 0:
                        st.session_state[page_key] = current_page - 1
                        st.rerun()
            with page_cols[1]:
                st.markdown(
                    f"<div style='text-align:center; padding-top:8px; color:#c8c0b4;'>"
                    f"{t('Page', 'صفحة')} {current_page + 1} / {total_pages}</div>",
                    unsafe_allow_html=True
                )
            with page_cols[2]:
                if st.button("▶", key=f"next_{key_suffix}", use_container_width=True):
                    if current_page + 1 < total_pages:
                        st.session_state[page_key] = current_page + 1
                        st.rerun()
            with page_cols[3]:
                # Jump to page
                page_num = st.number_input(
                    t("Go to", "انتقل إلى"),
                    min_value=1, max_value=total_pages, value=current_page + 1,
                    step=1, key=f"goto_{key_suffix}", label_visibility="collapsed"
                )
                if page_num != current_page + 1:
                    st.session_state[page_key] = page_num - 1
                    st.rerun()
    
    with col3:
        st.caption(f"{total_rows} {t('rows total', 'إجمالي الصفوف')}")
    
    # Small info about current range
    st.caption(f"{t('Showing', 'عرض')} {start_idx + 1} – {end_idx} {t('of', 'من')} {total_rows}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION HEADER HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _section(title: str):
    st.markdown(
        f"<div class='section-header'>"
        f"<div class='section-accent'></div>"
        f"<div class='section-header-text'>{title}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# TOP-10 BAR + TABLE (still uses old _render_table for small tables, but we keep it as is)
# ─────────────────────────────────────────────────────────────────────────────
def _top10_block(title: str, group_col: str, value_col: str, df: pd.DataFrame,
                 color: str = "#d4af6a", fmt: str = ",.0f"):
    _section(title)
    if df is None or df.empty:
        st.info(t("No data.", "لا توجد بيانات.")); return

    placeholder = f"({group_col} N/A)"
    grp = (
        df.assign(**{group_col: df[group_col].replace("", placeholder).fillna(placeholder)})
        .groupby(group_col, as_index=False)[value_col].sum()
        .sort_values(value_col, ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    if grp.empty:
        st.info(t("No data.", "لا توجد بيانات.")); return

    display_col = "Total Qty" if value_col == "Qty" else "Total (SAR)"
    grp[display_col] = grp[value_col].map(lambda v: f"{v:{fmt}}")

    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.altair_chart(_bar_chart(grp, group_col, value_col, color=color, fmt=fmt),
                        use_container_width=True)
    with c2:
        # Use the simple non-paginated render for top-10 (small tables)
        cols = grp.columns.tolist()
        thead = "".join(f"<th>{c}</th>" for c in cols)
        tbody = "".join(
            "<tr>" + "".join(
                f'<td class="lux-key">{v}</td>' if ci == 0 else f"<td>{v}</td>"
                for ci, v in enumerate(row)
            ) + "</tr>"
            for _, row in grp.iterrows()
        )
        st.markdown(
            f'{_TBL_CSS}<div class="lux-wrap">'
            f'<table class="lux-tbl"><thead><tr>{thead}</table></thead>'
            f'<tbody>{tbody}</tbody></table></div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────────────────
# KPI ROWS (updated with better formatting)
# ─────────────────────────────────────────────────────────────────────────────
def _kpi_sales(df: pd.DataFrame):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("Total Sales", "إجمالي المبيعات"),        f"{df['Subtotal'].sum():,.0f} SAR")
    c2.metric(t("Qty Sold", "الكمية المباعة"),             f"{df['Qty'].sum():,.0f}")
    c3.metric(t("Orders", "الطلبات"),                     f"{df['SO'].nunique():,}")
    c4.metric(t("Unique Customers", "عملاء فريدون"),       f"{df['Customer'].nunique():,}")
    avg = df.loc[df["Unit Price"] > 0, "Unit Price"].mean()
    c5.metric(t("Avg Unit Price", "متوسط سعر الوحدة"),    f"{avg:,.2f} SAR" if pd.notna(avg) else "—")


def _kpi_purchase(df: pd.DataFrame):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("Total Purchases", "إجمالي المشتريات"),   f"{df['Subtotal'].sum():,.0f} SAR")
    c2.metric(t("Qty Purchased", "الكمية المشتراة"),       f"{df['Qty'].sum():,.0f}")
    c3.metric(t("Purchase Orders", "أوامر الشراء"),        f"{df['PO'].nunique():,}")
    c4.metric(t("Unique Vendors", "موردون فريدون"),        f"{df['Vendor'].nunique():,}")
    avg = df.loc[df["Unit Price"] > 0, "Unit Price"].mean()
    c5.metric(t("Avg Unit Price", "متوسط سعر الوحدة"),    f"{avg:,.2f} SAR" if pd.notna(avg) else "—")


# ─────────────────────────────────────────────────────────────────────────────
# SALES ANALYTICS VIEW (uses paginated table)
# ─────────────────────────────────────────────────────────────────────────────
def show_sales_analytics(company: str):
    display_name = COMPANY_DISPLAY.get(company, company)
    st.markdown(
        f"<div class='info-banner'>"
        f"Sales orders from <strong>{display_name}</strong> (state: sale / done)"
        f"</div>", unsafe_allow_html=True
    )

    # ── Filters ──
    default_from = datetime.now().date() - timedelta(days=365)
    default_to   = datetime.now().date()

    f1, f2, f3, f4 = st.columns([1.4, 1, 1, 1.4])
    with f1:
        model_input = st.text_input(
            t("MODEL CODE (OPTIONAL)", "رمز الموديل (اختياري)"),
            placeholder=t("e.g. RVT196 — blank = all", "مثال: RVT196"),
            key=f"sales_model_{company}"
        ).strip()
    with f2:
        date_from = st.date_input(t("FROM", "من"), value=default_from, key=f"sales_from_{company}")
    with f3:
        date_to   = st.date_input(t("TO", "إلى"), value=default_to,   key=f"sales_to_{company}")
    with f4:
        cached = st.session_state.get("sales_df")
        cust_opts = []
        if cached is not None and not cached.empty and "Customer" in cached.columns:
            if st.session_state.get("sales_company") == company:
                cust_opts = sorted(cached["Customer"].dropna().unique().tolist())
        customer_sel = st.multiselect(
            t("CUSTOMER", "العميل"), options=cust_opts,
            placeholder=t("All customers", "كل العملاء"),
            key=f"sales_cust_{company}"
        )

    if st.button(
        t("◆  Fetch Sales Data", "◆  جلب بيانات المبيعات"),
        type="primary", key=f"fetch_sales_{company}"
    ):
        fetch_sales_history.clear()
        with st.spinner(t("Retrieving data…", "جارٍ جلب البيانات…")):
            fetched = fetch_sales_history(
                system_key=company,
                model_code=model_input,
                date_from=date_from.strftime("%Y-%m-%d"),
                date_to=date_to.strftime("%Y-%m-%d"),
            )
        st.session_state.sales_df      = fetched
        st.session_state.sales_company = company
        st.rerun()

    df_full = st.session_state.get("sales_df")
    if df_full is None or st.session_state.get("sales_company") != company:
        st.info(t(
            "Set your filters and click **Fetch Sales Data** to load.",
            "حدد الفلاتر واضغط **جلب بيانات المبيعات**."
        )); return

    if df_full.empty:
        st.info(t("No sales found for this period.", "لا توجد مبيعات لهذه الفترة.")); return

    # ── Apply filters locally ──────────────────────────────────────────────
    df = df_full.copy()
    if customer_sel:
        df = df[df["Customer"].isin(customer_sel)]

    # Strict model filtering — no fallback to full dataset
    if model_input:
        mc_norm  = model_input.strip().upper()
        df_model = df[df["Model Code"].str.strip().str.upper() == mc_norm].copy()
        working  = df_model          # strict: stays empty if no match
    else:
        df_model = None
        working  = df

    # ── KPIs (always from full filtered df, not model-narrowed) ───────────
    st.divider()
    _section(t("Key Performance Indicators", "مؤشرات الأداء الرئيسية"))
    _kpi_sales(df)

    # ── Top 10 Products by Qty ──
    st.divider()
    _top10_block(
        t("Top 10 Products — Quantity Sold", "أعلى 10 منتجات — الكمية المباعة"),
        "Model Code", "Qty", df, color="#d4af6a"
    )

    # ── Top 10 Products by Amount ──
    st.divider()
    _top10_block(
        t("Top 10 Products — Sales Amount", "أعلى 10 منتجات — المبلغ"),
        "Model Code", "Subtotal", df, color="#6b8f71", fmt=",.0f"
    )

    # ── Top 10 Customers ──
    st.divider()
    _top10_block(
        t("Top 10 Customers — Sales Amount", "أعلى 10 عملاء — المبلغ"),
        "Customer", "Subtotal", df, color="#7a8faf", fmt=",.0f"
    )

    # ── Top 10 Brand Categories ──
    st.divider()
    _top10_block(
        t("Top 10 Brand Categories — Qty", "أعلى 10 فئات علامة — الكمية"),
        "Brand Category", "Qty", df, color="#b87c5a"
    )

    # ── Top 10 Categories ──
    st.divider()
    _top10_block(
        t("Top 10 Categories — Qty", "أعلى 10 فئات — الكمية"),
        "Category", "Qty", df, color="#9a7ab8"
    )

    # ── Share Donuts ──
    st.divider()
    _section(t("Share Analysis", "تحليل الحصص"))
    d1, d2, d3 = st.columns(3)

    def _prep_donut(src_df, group_col, value_col, na_label):
        grp = (
            src_df.assign(**{group_col: src_df[group_col].replace("", na_label).fillna(na_label)})
            .groupby(group_col, as_index=False)[value_col].sum()
            .sort_values(value_col, ascending=False)
        )
        top = grp.head(10)
        others = float(grp.iloc[10:][value_col].sum()) if len(grp) > 10 else 0
        labels = top[group_col].tolist()
        vals   = top[value_col].tolist()
        if others > 0:
            labels.append(t("Others", "أخرى")); vals.append(others)
        return labels, vals

    with d1:
        lbl, val = _prep_donut(df, "Brand Category", "Subtotal", "(No Brand)")
        _donut_chart(lbl, val, title=t("Brand Category Share", "حصة الفئة التجارية"))
    with d2:
        lbl, val = _prep_donut(df, "Category", "Subtotal", "(No Category)")
        _donut_chart(lbl, val, title=t("Category Share", "حصة الفئة"))
    with d3:
        lbl, val = _prep_donut(df, "Customer", "Subtotal", "(No Customer)")
        _donut_chart(lbl, val, title=t("Customer Share (Top 10)", "حصة العملاء"))

    # ── Time-series Trends ──
    st.divider()
    _section(t("Sales Trends Over Time", "اتجاهات المبيعات عبر الزمن"))
    ts1, ts2 = st.columns(2)

    def _ts(src_df, value_col, color):
        ts = (
            src_df.assign(Date=pd.to_datetime(src_df["Date"], errors="coerce"))
            .dropna(subset=["Date"])
            .groupby("Date", as_index=False)[value_col].sum()
            .sort_values("Date")
        )
        if not ts.empty:
            st.altair_chart(_line_chart(ts, "Date", value_col, color=color), use_container_width=True)
        else:
            st.info(t("No time data.", "لا توجد بيانات زمنية."))

    with ts1:
        st.markdown(
            f"<p style='color:#6e6e78;font-size:.72rem;letter-spacing:.1em;"
            f"text-transform:uppercase;margin-bottom:6px'>"
            f"{t('QTY SOLD OVER TIME', 'الكمية المباعة عبر الزمن')}</p>",
            unsafe_allow_html=True
        )
        _ts(df, "Qty", "#d4af6a")
    with ts2:
        st.markdown(
            f"<p style='color:#6e6e78;font-size:.72rem;letter-spacing:.1em;"
            f"text-transform:uppercase;margin-bottom:6px'>"
            f"{t('SALES AMOUNT OVER TIME', 'مبلغ المبيعات عبر الزمن')}</p>",
            unsafe_allow_html=True
        )
        _ts(df, "Subtotal", "#6b8f71")

    # ── Single Model Detail ────────────────────────────────────────────────
    st.divider()
    _section(t("Single Model Detail", "تفاصيل موديل واحد"))

    if not model_input:
        st.markdown(
            "<div class='info-banner'>"
            + t(
                "Enter a Model Code in the filter above to see single-model analytics.",
                "أدخل رمز الموديل في الفلتر أعلاه لعرض تحليلات الموديل."
            )
            + "</div>",
            unsafe_allow_html=True
        )
    elif df_model is not None and df_model.empty:
        st.markdown(
            f"<div class='warn-banner'>"
            + t(
                f"No data found for model: <strong>{model_input.strip().upper()}</strong>",
                f"لا توجد بيانات للموديل: <strong>{model_input.strip().upper()}</strong>"
            )
            + "</div>",
            unsafe_allow_html=True
        )
    else:
        mk1, mk2, mk3, _ = st.columns(4)
        mk1.metric(t("Qty (this model)", "الكمية (الموديل)"), f"{df_model['Qty'].sum():,.0f}")
        mk2.metric(t("Sales (SAR)", "المبيعات (ر.س)"),        f"{df_model['Subtotal'].sum():,.0f}")
        mk3.metric(t("Customers", "العملاء"),                  f"{df_model['Customer'].nunique():,}")

        m_ts_df = (
            df_model.assign(Date=pd.to_datetime(df_model["Date"], errors="coerce"))
            .dropna(subset=["Date"])
            .groupby("Date", as_index=False)["Qty"].sum()
            .sort_values("Date")
        )
        if not m_ts_df.empty:
            st.altair_chart(_line_chart(m_ts_df, "Date", "Qty"), use_container_width=True)

        _top10_block(
            t("Top Customers for this Model", "أعلى العملاء لهذا الموديل"),
            "Customer", "Qty", df_model, color="#9a7ab8"
        )

    # ── Full Detail Table + Downloads (with pagination) ───────────────────
    st.divider()
    _section(t("Full Detail Table", "جدول التفاصيل الكاملة"))

    if model_input and working.empty:
        st.markdown(
            f"<div class='warn-banner'>"
            + t(
                f"No records to display — model <strong>{model_input.strip().upper()}</strong> "
                f"was not found in this dataset.",
                f"لا توجد سجلات للعرض — الموديل <strong>{model_input.strip().upper()}</strong> "
                f"غير موجود في هذه البيانات."
            )
            + "</div>",
            unsafe_allow_html=True
        )
    else:
        tag        = f"_{model_input.strip().upper()}" if model_input else ""
        export_df  = working.copy()
        display_df = export_df.copy()
        display_df["Unit Price"] = display_df["Unit Price"].map(lambda v: f"{v:,.2f}")
        display_df["Subtotal"]   = display_df["Subtotal"].map(lambda v: f"{v:,.2f}")
        display_df["Qty"]        = display_df["Qty"].map(lambda v: f"{v:,.0f}")
        
        # Use paginated table renderer
        _render_paginated_table(display_df, key_suffix=f"sales_{company}{tag}")

        st.markdown("<br>", unsafe_allow_html=True)
        dl1, dl2, _ = st.columns([1, 1, 2])
        dl1.download_button(
            t("⬇  CSV Export", "⬇  تصدير CSV"),
            export_df.to_csv(index=False).encode("utf-8-sig"),
            dl_filename(company, f"sales{tag}", "csv"),
            "text/csv", use_container_width=True,
            key=f"dl_sales_csv_{company}{tag}"
        )
        dl2.download_button(
            t("⬇  Excel Export", "⬇  تصدير Excel"),
            _styled_excel(export_df, "Sales Data"),
            dl_filename(company, f"sales{tag}", "xlsx"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"dl_sales_xlsx_{company}{tag}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE ANALYTICS VIEW (uses paginated table)
# ─────────────────────────────────────────────────────────────────────────────
def show_purchase_analytics(company: str):
    display_name = COMPANY_DISPLAY.get(company, company)
    st.markdown(
        f"<div class='info-banner'>"
        f"Purchase orders from <strong>{display_name}</strong> (state: purchase / done)"
        f"</div>", unsafe_allow_html=True
    )

    # ── Filters ──
    default_from = datetime.now().date() - timedelta(days=365)
    default_to   = datetime.now().date()

    f1, f2, f3, f4 = st.columns([1.4, 1, 1, 1.4])
    with f1:
        model_input = st.text_input(
            t("MODEL CODE (OPTIONAL)", "رمز الموديل (اختياري)"),
            placeholder=t("e.g. RVT196 — blank = all", "مثال: RVT196"),
            key=f"purch_model_{company}"
        ).strip()
    with f2:
        date_from = st.date_input(t("FROM", "من"), value=default_from, key=f"purch_from_{company}")
    with f3:
        date_to   = st.date_input(t("TO", "إلى"), value=default_to,   key=f"purch_to_{company}")
    with f4:
        cached = st.session_state.get("purchase_df")
        vendor_opts = []
        if cached is not None and not cached.empty and "Vendor" in cached.columns:
            if st.session_state.get("purchase_company") == company:
                vendor_opts = sorted(cached["Vendor"].dropna().unique().tolist())
        vendor_sel = st.multiselect(
            t("VENDOR", "المورد"), options=vendor_opts,
            placeholder=t("All vendors", "كل الموردين"),
            key=f"purch_vend_{company}"
        )

    if st.button(
        t("◆  Fetch Purchase Data", "◆  جلب بيانات المشتريات"),
        type="primary", key=f"fetch_purch_{company}"
    ):
        fetch_purchase_history.clear()
        with st.spinner(t("Retrieving data…", "جارٍ جلب البيانات…")):
            fetched = fetch_purchase_history(
                system_key=company,
                model_code=model_input,
                date_from=date_from.strftime("%Y-%m-%d"),
                date_to=date_to.strftime("%Y-%m-%d"),
            )
        st.session_state.purchase_df      = fetched
        st.session_state.purchase_company = company
        st.rerun()

    df_full = st.session_state.get("purchase_df")
    if df_full is None or st.session_state.get("purchase_company") != company:
        st.info(t(
            "Set your filters and click **Fetch Purchase Data** to load.",
            "حدد الفلاتر واضغط **جلب بيانات المشتريات**."
        )); return

    if df_full.empty:
        st.info(t("No purchases found for this period.", "لا توجد مشتريات لهذه الفترة.")); return

    # ── Apply filters locally ──────────────────────────────────────────────
    df = df_full.copy()
    if vendor_sel:
        df = df[df["Vendor"].isin(vendor_sel)]

    # Strict model filtering — no fallback to full dataset
    if model_input:
        mc_norm  = model_input.strip().upper()
        df_model = df[df["Model Code"].str.strip().str.upper() == mc_norm].copy()
        working  = df_model          # strict: stays empty if no match
    else:
        df_model = None
        working  = df

    # ── KPIs (always from full filtered df, not model-narrowed) ───────────
    st.divider()
    _section(t("Key Performance Indicators", "مؤشرات الأداء الرئيسية"))
    _kpi_purchase(df)

    # ── Top 10 Products by Qty ──
    st.divider()
    _top10_block(
        t("Top 10 Products — Qty Purchased", "أعلى 10 منتجات — الكمية المشتراة"),
        "Model Code", "Qty", df, color="#d4af6a"
    )

    # ── Top 10 Products by Amount ──
    st.divider()
    _top10_block(
        t("Top 10 Products — Purchase Amount", "أعلى 10 منتجات — مبلغ الشراء"),
        "Model Code", "Subtotal", df, color="#6b8f71", fmt=",.0f"
    )

    # ── Top 10 Vendors ──
    st.divider()
    _top10_block(
        t("Top 10 Vendors — Purchase Amount", "أعلى 10 موردين — المبلغ"),
        "Vendor", "Subtotal", df, color="#7a8faf", fmt=",.0f"
    )

    # ── Top 10 Brand Categories ──
    st.divider()
    _top10_block(
        t("Top 10 Brand Categories — Qty", "أعلى 10 فئات علامة — الكمية"),
        "Brand Category", "Qty", df, color="#b87c5a"
    )

    # ── Top 10 Categories ──
    st.divider()
    _top10_block(
        t("Top 10 Categories — Qty", "أعلى 10 فئات — الكمية"),
        "Category", "Qty", df, color="#9a7ab8"
    )

    # ── Share Donuts ──
    st.divider()
    _section(t("Share Analysis", "تحليل الحصص"))
    d1, d2, d3 = st.columns(3)

    def _prep_donut(src_df, group_col, value_col, na_label):
        grp = (
            src_df.assign(**{group_col: src_df[group_col].replace("", na_label).fillna(na_label)})
            .groupby(group_col, as_index=False)[value_col].sum()
            .sort_values(value_col, ascending=False)
        )
        top    = grp.head(10)
        others = float(grp.iloc[10:][value_col].sum()) if len(grp) > 10 else 0
        labels = top[group_col].tolist()
        vals   = top[value_col].tolist()
        if others > 0:
            labels.append(t("Others", "أخرى")); vals.append(others)
        return labels, vals

    with d1:
        lbl, val = _prep_donut(df, "Brand Category", "Subtotal", "(No Brand)")
        _donut_chart(lbl, val, title=t("Brand Category Share", "حصة الفئة التجارية"))
    with d2:
        lbl, val = _prep_donut(df, "Category", "Subtotal", "(No Category)")
        _donut_chart(lbl, val, title=t("Category Share", "حصة الفئة"))
    with d3:
        lbl, val = _prep_donut(df, "Vendor", "Subtotal", "(No Vendor)")
        _donut_chart(lbl, val, title=t("Vendor Share (Top 10)", "حصة الموردين"))

    # ── Time-series Trends ──
    st.divider()
    _section(t("Purchase Trends Over Time", "اتجاهات المشتريات عبر الزمن"))
    ts1, ts2 = st.columns(2)

    def _ts(src_df, value_col, color):
        ts = (
            src_df.assign(Date=pd.to_datetime(src_df["Date"], errors="coerce"))
            .dropna(subset=["Date"])
            .groupby("Date", as_index=False)[value_col].sum()
            .sort_values("Date")
        )
        if not ts.empty:
            st.altair_chart(_line_chart(ts, "Date", value_col, color=color), use_container_width=True)
        else:
            st.info(t("No time data.", "لا توجد بيانات زمنية."))

    with ts1:
        st.markdown(
            f"<p style='color:#6e6e78;font-size:.72rem;letter-spacing:.1em;"
            f"text-transform:uppercase;margin-bottom:6px'>"
            f"{t('QTY PURCHASED OVER TIME', 'الكمية المشتراة عبر الزمن')}</p>",
            unsafe_allow_html=True
        )
        _ts(df, "Qty", "#d4af6a")
    with ts2:
        st.markdown(
            f"<p style='color:#6e6e78;font-size:.72rem;letter-spacing:.1em;"
            f"text-transform:uppercase;margin-bottom:6px'>"
            f"{t('PURCHASE AMOUNT OVER TIME', 'مبلغ المشتريات عبر الزمن')}</p>",
            unsafe_allow_html=True
        )
        _ts(df, "Subtotal", "#6b8f71")

    # ── Single Model Detail ────────────────────────────────────────────────
    st.divider()
    _section(t("Single Model Detail", "تفاصيل موديل واحد"))

    if not model_input:
        st.markdown(
            "<div class='info-banner'>"
            + t(
                "Enter a Model Code in the filter above to see single-model analytics.",
                "أدخل رمز الموديل في الفلتر أعلاه لعرض تحليلات الموديل."
            )
            + "</div>",
            unsafe_allow_html=True
        )
    elif df_model is not None and df_model.empty:
        st.markdown(
            f"<div class='warn-banner'>"
            + t(
                f"No data found for model: <strong>{model_input.strip().upper()}</strong>",
                f"لا توجد بيانات للموديل: <strong>{model_input.strip().upper()}</strong>"
            )
            + "</div>",
            unsafe_allow_html=True
        )
    else:
        mk1, mk2, mk3, _ = st.columns(4)
        mk1.metric(t("Qty (this model)", "الكمية (الموديل)"), f"{df_model['Qty'].sum():,.0f}")
        mk2.metric(t("Amount (SAR)", "المبلغ (ر.س)"),         f"{df_model['Subtotal'].sum():,.0f}")
        mk3.metric(t("Vendors", "الموردون"),                   f"{df_model['Vendor'].nunique():,}")

        m_ts_df = (
            df_model.assign(Date=pd.to_datetime(df_model["Date"], errors="coerce"))
            .dropna(subset=["Date"])
            .groupby("Date", as_index=False)["Qty"].sum()
            .sort_values("Date")
        )
        if not m_ts_df.empty:
            st.altair_chart(_line_chart(m_ts_df, "Date", "Qty"), use_container_width=True)

        _top10_block(
            t("Top Vendors for this Model", "أعلى الموردين لهذا الموديل"),
            "Vendor", "Qty", df_model, color="#7a8faf"
        )

    # ── Full Detail Table + Downloads (with pagination) ───────────────────
    st.divider()
    _section(t("Full Detail Table", "جدول التفاصيل الكاملة"))

    if model_input and working.empty:
        st.markdown(
            f"<div class='warn-banner'>"
            + t(
                f"No records to display — model <strong>{model_input.strip().upper()}</strong> "
                f"was not found in this dataset.",
                f"لا توجد سجلات للعرض — الموديل <strong>{model_input.strip().upper()}</strong> "
                f"غير موجود في هذه البيانات."
            )
            + "</div>",
            unsafe_allow_html=True
        )
    else:
        tag        = f"_{model_input.strip().upper()}" if model_input else ""
        export_df  = working.copy()
        display_df = export_df.copy()
        display_df["Unit Price"] = display_df["Unit Price"].map(lambda v: f"{v:,.2f}")
        display_df["Subtotal"]   = display_df["Subtotal"].map(lambda v: f"{v:,.2f}")
        display_df["Qty"]        = display_df["Qty"].map(lambda v: f"{v:,.0f}")
        
        # Use paginated table renderer
        _render_paginated_table(display_df, key_suffix=f"purchase_{company}{tag}")

        st.markdown("<br>", unsafe_allow_html=True)
        dl1, dl2, _ = st.columns([1, 1, 2])
        dl1.download_button(
            t("⬇  CSV Export", "⬇  تصدير CSV"),
            export_df.to_csv(index=False).encode("utf-8-sig"),
            dl_filename(company, f"purchase{tag}", "csv"),
            "text/csv", use_container_width=True,
            key=f"dl_purch_csv_{company}{tag}"
        )
        dl2.download_button(
            t("⬇  Excel Export", "⬇  تصدير Excel"),
            _styled_excel(export_df, "Purchase Data"),
            dl_filename(company, f"purchase{tag}", "xlsx"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"dl_purch_xlsx_{company}{tag}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    # Language toggle top-right
    _, _, lc = st.columns([3, 1, 0.6])
    with lc:
        lg = st.radio("", ["EN", "AR"], horizontal=True,
                      index=0 if get_lang() == "EN" else 1,
                      label_visibility="collapsed", key="login_lang")
        if lg != get_lang():
            st.session_state.lang = lg
            st.rerun()

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:40px 0 20px;'>
            <div style='font-size:2.8rem;margin-bottom:16px;opacity:0.85'>◆</div>
            <div class='lux-login-title'>Luxury Analytics</div>
            <div class='lux-login-sub'>Multi-Company · Sales & Purchase Intelligence</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='lux-login-card'>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                t("EMAIL ADDRESS", "البريد الإلكتروني"),
                placeholder="you@company.com"
            )
            password = st.text_input(
                t("PASSWORD", "كلمة المرور"),
                type="password", placeholder="••••••••"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                t("◆  Sign In", "◆  تسجيل الدخول"),
                use_container_width=True, type="primary"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            if not email or not password:
                st.error(t("Please fill in all fields.", "يرجى ملء جميع الحقول."))
                return
            if "LOGIN" not in st.secrets:
                st.error("❌ [LOGIN] section missing in secrets.toml")
                return
            cfg = st.secrets["LOGIN"]
            with st.spinner(t("Authenticating…", "جارٍ التحقق…")):
                try:
                    proxy = xmlrpc.client.ServerProxy(
                        f"{cfg['url']}/xmlrpc/2/common", allow_none=True)
                    uid = proxy.authenticate(cfg["db"], email, password, {})
                    if uid:
                        token = _make_token(email)
                        st.query_params["u"] = email
                        st.query_params["t"] = token
                        st.session_state.authenticated = True
                        st.session_state.user_email    = email
                        time.sleep(0.2)
                        st.rerun()
                    else:
                        st.error(t("Invalid credentials.", "بيانات الاعتماد غير صحيحة."))
                except Exception as e:
                    st.error(f"Connection error: {e}")

        st.markdown("""
        <p style='text-align:center;color:#2a2a2e;font-size:.72rem;margin-top:24px;
        letter-spacing:.08em;text-transform:uppercase;'>
        © 2025 Luxury Analytics · Powered by Odoo</p>""",
                    unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────
def do_logout():
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.session_state.authenticated = False
    st.session_state.user_email    = ""
    st.session_state.sales_df      = None
    st.session_state.purchase_df   = None
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    company = st.session_state.get("selected_company", "SWAG")
    view    = st.session_state.get("analytics_view", "sales")

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        # Language
        st.markdown("<span class='nav-company-label'>INTERFACE LANGUAGE</span>",
                    unsafe_allow_html=True)
        lg = st.radio("", ["EN", "AR"], horizontal=True,
                      index=0 if get_lang() == "EN" else 1,
                      label_visibility="collapsed", key="dash_lang")
        if lg != get_lang():
            st.session_state.lang = lg
            st.rerun()

        st.divider()

        # Company Selector
        st.markdown(f"<span class='nav-company-label'>{t('COMPANY', 'الشركة')}</span>",
                    unsafe_allow_html=True)
        company_labels = {k: COMPANY_DISPLAY[k] for k in SYSTEM_KEYS}
        selected = st.selectbox(
            "", options=list(company_labels.keys()),
            format_func=lambda k: company_labels[k],
            index=SYSTEM_KEYS.index(company),
            label_visibility="collapsed",
            key="company_selector"
        )
        if selected != company:
            st.session_state.selected_company = selected
            st.session_state.sales_df         = None
            st.session_state.purchase_df      = None
            st.rerun()

        st.divider()

        # View Selector
        st.markdown(f"<span class='nav-company-label'>{t('ANALYTICS TYPE', 'نوع التحليل')}</span>",
                    unsafe_allow_html=True)
        s_type = "primary" if view == "sales"    else "secondary"
        p_type = "primary" if view == "purchase" else "secondary"

        v1, v2 = st.columns(2)
        with v1:
            if st.button(t("Sales", "المبيعات"), type=s_type,
                         use_container_width=True, key="nav_sales"):
                st.session_state.analytics_view = "sales"
                st.rerun()
        with v2:
            if st.button(t("Purchase", "المشتريات"), type=p_type,
                         use_container_width=True, key="nav_purchase"):
                st.session_state.analytics_view = "purchase"
                st.rerun()

        # Active indicator
        indicator_text = (
            f"◆ {company_labels[selected]} — {t('Sales', 'المبيعات')}"
            if view == "sales"
            else f"◆ {company_labels[selected]} — {t('Purchase', 'المشتريات')}"
        )
        st.markdown(f"<div class='active-indicator'>{indicator_text}</div>",
                    unsafe_allow_html=True)

        st.divider()

        # User + Logout
        st.markdown(f"<span class='nav-company-label'>{t('SIGNED IN AS', 'مسجل دخول كـ')}</span>",
                    unsafe_allow_html=True)
        st.markdown(f"<p style='color:#d4c5a9;font-size:.82rem;margin:4px 0 12px;'>"
                    f"{st.session_state.user_email}</p>", unsafe_allow_html=True)
        if st.button(t("Sign Out", "تسجيل الخروج"), use_container_width=True, key="logout_btn"):
            do_logout()

    # ── MAIN HEADER ──────────────────────────────────────────────────────────
    view_label = t("Sales Analytics", "تحليلات المبيعات") if view == "sales" \
        else t("Purchase Analytics", "تحليلات المشتريات")

    st.markdown(f"""
    <div class='lux-header'>
        <div class='lux-title'>SWAG MULTI DASBOARD WITH 4 COMPANY </div>
        <div class='lux-subtitle'>{t('Sales & Purchase Intelligence · 4 Companies', 'ذكاء المبيعات والمشتريات · 4 شركات')}</div>
        <div>
            <span class='lux-company-badge'>{COMPANY_DISPLAY.get(company, company)}</span>
            <span class='lux-company-badge' style='margin-left:6px;border-color:#6b8f7144;background:linear-gradient(135deg,#6b8f7122,#4a7c5e22);color:#8ab49a;'>{view_label}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── ROUTE VIEW ───────────────────────────────────────────────────────────
    if view == "sales":
        show_sales_analytics(company)
    else:
        show_purchase_analytics(company)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
