"""
SWAG Product Sync — Standalone App (Light Theme)
Copy products from SWAG to any target company (La Rouche, Fashion Limits, Different Clothes)
"""

import io
import re
import hashlib
import time
import xmlrpc.client
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SWAG Product Sync",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CSS (Light Theme – clean white/indigo)
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
@keyframes bounceIn{0%{transform:scale(0.2) rotate(-10deg);opacity:0}60%{transform:scale(1.2) rotate(5deg);opacity:1}80%{transform:scale(0.9)}100%{transform:scale(1);opacity:1}}
@keyframes shimmer{0%{background-position:-400% center}100%{background-position:400% center}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 #6366f144}50%{box-shadow:0 0 20px 8px #8b5cf622}}
@keyframes glow{0%,100%{text-shadow:0 0 10px #6366f188}50%{text-shadow:0 0 30px #8b5cf6cc,0 0 60px #6366f188}}
@keyframes slideInLeft{from{opacity:0;transform:translateX(-40px)}to{opacity:1;transform:translateX(0)}}
@keyframes slideInRight{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes btnShine{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes borderGlow{0%,100%{border-color:#6366f1;box-shadow:0 0 5px #6366f144}50%{border-color:#8b5cf6;box-shadow:0 0 15px #8b5cf666}}
@keyframes countUp{from{opacity:0;transform:scale(0.5)}to{opacity:1;transform:scale(1)}}
.login-orb{width:120px;height:120px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6,#a78bfa);display:flex;align-items:center;justify-content:center;font-size:3rem;margin:0 auto 20px;animation:float 3s ease-in-out infinite,bounceIn 1s ease forwards;box-shadow:0 8px 40px #6366f166,0 0 60px #a78bfa33;}
.login-title{font-size:2.4rem;font-weight:700;background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1);background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s linear infinite,fadeInDown 0.8s ease forwards;text-align:center;margin-bottom:6px;}
.login-subtitle{color:#4b5563!important;font-size:0.95rem;text-align:center;animation:fadeInUp 1s ease forwards;margin-bottom:28px;}
.login-card{background:#ffffff;border:1px solid #e0e7ff;border-radius:20px;padding:32px 36px;width:100%;animation:fadeInUp 0.9s ease forwards,pulse 3s infinite;}
.welcome-banner{background:#eef2ff;border:1px solid #c7d2fe;border-radius:12px;padding:14px 20px;text-align:center;margin-bottom:20px;font-size:0.95rem;color:#4f46e5!important;animation:fadeInDown 0.7s ease forwards,borderGlow 3s infinite;}
.stTextInput input,.stNumberInput input,.stTextArea textarea{background:#ffffff!important;border:1px solid #c7d2fe!important;border-radius:10px!important;color:#1e1b4b!important;caret-color:#6366f1!important;transition:all 0.3s ease!important;}
.stTextInput input::placeholder,.stNumberInput input::placeholder,.stTextArea textarea::placeholder{color:#9ca3af!important;}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:#6366f1!important;box-shadow:0 0 0 3px #6366f133!important;background:#ffffff!important;}
.stTextInput label,.stNumberInput label,.stTextArea label{color:#374151!important;font-weight:600!important;}
.stFormSubmitButton button,.stButton button[kind="primary"]{background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1)!important;background-size:300% auto!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important;font-size:1rem!important;padding:12px!important;animation:btnShine 3s linear infinite!important;transition:transform 0.2s,box-shadow 0.2s!important;box-shadow:0 4px 20px #6366f155!important;}
.stFormSubmitButton button:hover,.stButton button[kind="primary"]:hover{transform:translateY(-2px) scale(1.02)!important;box-shadow:0 8px 30px #8b5cf699!important;}
.stButton button[kind="secondary"]{background:#ffffff!important;border:1px solid #c7d2fe!important;color:#4f46e5!important;border-radius:10px!important;}
.stButton button[kind="secondary"]:hover{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;}
.stButton button{color:#4f46e5!important;}
.stDownloadButton button{background:#ffffff!important;border:1px solid #c7d2fe!important;border-radius:10px!important;color:#4f46e5!important;font-size:0.78rem!important;font-weight:600!important;padding:6px 14px!important;transition:all 0.25s ease!important;box-shadow:0 2px 8px #00000022!important;}
.stDownloadButton button:hover{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;border-color:transparent!important;transform:translateY(-2px) scale(1.04)!important;box-shadow:0 6px 20px #6366f155!important;}
.dash-header{text-align:center;padding:16px 0 24px;animation:fadeInDown 0.6s ease forwards;}
.dash-title{font-size:2.4rem;font-weight:700;background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1);background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 4s linear infinite,glow 3s ease-in-out infinite;}
.dash-subtitle{color:#6b7280;font-size:0.95rem;margin-top:-4px;}
[data-testid="stMetric"]{background:#ffffff!important;border:1px solid #e0e7ff!important;border-radius:16px!important;padding:16px 20px!important;animation:countUp 0.6s ease forwards;transition:transform 0.2s,box-shadow 0.2s;}
[data-testid="stMetric"]:hover{transform:translateY(-4px);box-shadow:0 8px 30px #6366f144;}
[data-testid="stMetricLabel"]{color:#6b7280!important;font-size:0.82rem!important;}
[data-testid="stMetricValue"]{font-size:1.7rem!important;font-weight:700!important;background:linear-gradient(90deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.stTabs [data-baseweb="tab-list"]{background:#ffffff;border-radius:12px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{color:#6b7280!important;border-radius:10px!important;font-size:0.83rem!important;font-weight:600!important;padding:8px 16px!important;transition:all 0.2s ease!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#6366f1,#8b5cf6)!important;color:white!important;box-shadow:0 4px 12px #6366f155!important;}
.info-banner{background:#eef2ff;border-left:4px solid #6366f1;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#1e3a8a!important;animation:slideInLeft 0.4s ease;}
.warn-banner{background:#fffbeb;border-left:4px solid #f59e0b;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#92400e!important;}
.alert-banner{background:#fef2f2;border-left:4px solid #f43f5e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#991b1b!important;animation:pulse 2s infinite;}
.ok-banner{background:#ecfdf5;border-left:4px solid #22c55e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#065f46!important;}
.snap-card{background:#ffffff;border:1px solid #e0e7ff;border-radius:14px;padding:16px 20px;font-size:0.87rem;color:#1e1b4b!important;line-height:2;animation:slideInRight 0.5s ease;box-shadow:0 4px 20px #00000022;}
.snap-card b{color:#4f46e5!important;}
.sys-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
.sys-row span{color:#1e1b4b!important;}
.badge-ok{background:#ecfdf5;color:#065f46!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}
.badge-off{background:#fef2f2;color:#991b1b!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}
.badge-err{background:#fffbeb;color:#92400e!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;}
.stRadio label,.stRadio div[role="radiogroup"] label span,[data-testid="stToggle"] label,.stCheckbox label{color:#1e1b4b!important;}
div[data-testid="stRadio"] p{color:#1e1b4b!important;}
h1,h2,h3,h4,h5,h6{color:#1e1b4b!important;}
.stMarkdown p,.stMarkdown li{color:#374151!important;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#9ca3af!important;}
.stAlert p{color:#1e1b4b!important;font-weight:600;}
[data-testid="stExpander"]{background:#ffffff!important;border:1px solid #e0e7ff!important;border-radius:12px!important;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:#1e1b4b!important;}
[data-testid="stFileUploader"]{background:#ffffff!important;border:2px dashed #c7d2fe!important;border-radius:14px!important;}
[data-testid="stFileUploader"] p,[data-testid="stFileUploader"] span{color:#4b5563!important;}
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,#c7d2fe,transparent)!important;margin:16px 0!important;}
[data-testid="stProgressBar"]>div{background:linear-gradient(90deg,#6366f1,#8b5cf6)!important;border-radius:10px!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#f0f2f6;}
::-webkit-scrollbar-thumb{background:#c7d2fe;border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:#8b5cf6;}
.stNumberInput button{color:#4f46e5!important;background:#ffffff!important;}
.mono{font-family:'IBM Plex Mono',monospace;font-size:0.82rem;color:#4b5563;}
footer{visibility:hidden;}
[data-baseweb="tag"]{background:#e0e7ff!important;color:#4f46e5!important;}
[data-baseweb="select"] div{background:#ffffff!important;color:#1e1b4b!important;border-color:#c7d2fe!important;}
</style>
""", unsafe_allow_html=True)


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
# Main UI
# -----------------------------------------------------------------------------
st.markdown("""
<div class='dash-header'>
    <div class='dash-title'>🔄 Product Sync</div>
    <div class='dash-subtitle'>Copy products from SWAG to any target company</div>
</div>
""", unsafe_allow_html=True)
st.divider()

# Step 1: Company selector
company_map = {
    "La Rouche": "LAROUCHE",
    "Fashion Limits": "FASHION_LIMITS",
    "Different Clothes": "DIFFC"
}
selected_company_label = st.selectbox(
    "🎯 Target Company",
    list(company_map.keys()),
    key="sync_company"
)
target_key = company_map[selected_company_label]
target_cfg = st.secrets.get(target_key)
if not target_cfg:
    st.error(f"❌ Secrets missing for {selected_company_label}. Check your secrets.toml file.")
    st.stop()

# Step 2: Input method
input_method = st.radio(
    "📝 Product codes input",
    ["Manual entry", "Upload PDF invoice"],
    horizontal=True,
    key="sync_method"
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
        key="sync_pdf"
    )
    if pdf_file:
        with st.spinner("Parsing PDF..."):
            parsed = parse_invoice_pdf_cached(pdf_file.read())
        if parsed:
            codes = list(dict.fromkeys([item["code"] for item in parsed]))
            st.success(f"✅ {len(codes)} unique codes extracted.")
        else:
            st.warning("No codes found in PDF.")

# Step 3: Check button
if st.button("🔍 Check Products", type="primary", use_container_width=False, key="sync_check"):
    if not codes:
        st.warning("Please enter at least one product code.")
    else:
        with st.spinner("Checking codes in target company..."):
            uid_target = _auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])
            if not uid_target:
                st.error("Authentication failed for target company.")
            else:
                # Determine existing products in target
                existing_map = {}
                for code in codes:
                    domain = [["default_code", "=", code]]
                    ids = call_with_retry(
                        _x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
                        "product.product", "search", [domain], {"limit": 1}
                    )
                    existing_map[code] = len(ids) > 0

                # Fetch product names and SWAG existence
                swag_cfg = st.secrets["SWAG"]
                uid_swag = _auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
                swag_exists = {}
                product_names = {}
                if uid_swag:
                    for code in codes:
                        prod = call_with_retry(
                            _x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
                            "product.product", "search_read", [[["default_code", "=", code]]],
                            {"fields": ["name"], "limit": 1}
                        )
                        if prod:
                            swag_exists[code] = True
                            product_names[code] = prod[0].get("name", code)
                        else:
                            swag_exists[code] = False
                            product_names[code] = code
                else:
                    # fallback: assume all codes exist in SWAG? safer to treat as unknown
                    for code in codes:
                        swag_exists[code] = True
                        product_names[code] = code

                # Build results table
                result_rows = []
                for code in codes:
                    if not swag_exists.get(code, False):
                        status = "⚠️ Not in SWAG"
                        badge_class = "badge-err"
                    elif existing_map.get(code, False):
                        status = "✅ Already exists"
                        badge_class = "badge-ok"
                    else:
                        status = "❌ Missing"
                        badge_class = "badge-off"
                    result_rows.append({
                        "Code": code,
                        "Product Name": product_names.get(code, code),
                        "Status": f'<span class="{badge_class}">{status}</span>'
                    })

                df_result = pd.DataFrame(result_rows)
                st.markdown("#### 📋 Check Result")
                st.write(
                    df_result.to_html(escape=False, index=False),
                    unsafe_allow_html=True
                )

                # Store in session state for creation step
                missing_codes = [code for code in codes if swag_exists.get(code, False) and not existing_map.get(code, False)]
                st.session_state["sync_missing_codes"] = missing_codes
                st.session_state["sync_result_df"] = df_result

# Step 4: Create Missing button (only if missing products exist)
if "sync_missing_codes" in st.session_state and st.session_state["sync_missing_codes"]:
    missing_codes = st.session_state["sync_missing_codes"]
    st.markdown(f"<div class='info-banner'>📌 {len(missing_codes)} product(s) are missing in the target company.</div>", unsafe_allow_html=True)
    if st.button("➕ Create Missing", type="primary", key="sync_create"):
        progress_bar = st.progress(0, text="Creating products...")
        created = 0
        skipped = 0
        errors = 0
        total = len(missing_codes)
        for i, code in enumerate(missing_codes):
            try:
                swag_prod = fetch_product_from_swag(code)
                if not swag_prod:
                    st.warning(f"⚠️ Could not fetch product {code} from SWAG. Skipped.")
                    skipped += 1
                else:
                    create_product_in_target(target_cfg, swag_prod)
                    created += 1
            except Exception as e:
                st.error(f"❌ Failed to create {code}: {e}")
                errors += 1
            time.sleep(0.5)
            progress_bar.progress((i + 1) / total, text=f"Creating products... ({i+1}/{total})")
        progress_bar.empty()
        st.success(f"✅ Done. Created: {created}, Skipped: {skipped}, Errors: {errors}")
        # clear session state so the button disappears after creation
        del st.session_state["sync_missing_codes"]
        st.rerun()
