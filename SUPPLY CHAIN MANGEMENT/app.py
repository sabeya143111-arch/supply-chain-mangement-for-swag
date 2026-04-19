import io
import re
import hashlib
import time
import xmlrpc.client
import streamlit as st

st.set_page_config(page_title="Product Sync", page_icon="🔄", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');
html,body{font-family:'IBM Plex Sans Arabic',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);min-height:100vh}
.stTabs [data-baseweb="tab-list"]{background:linear-gradient(90deg,#1e1e3f,#2d2b55);border-radius:12px;padding:4px;gap:4px}
.stTabs [data-baseweb="tab"]{color:#a0aec0!important;border-radius:10px!important;font-weight:600!important}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#667eea,#764ba2)!important;color:white!important}
.stButton button[kind="primary"]{background:linear-gradient(90deg,#667eea,#764ba2,#f093fb)!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important}
.stButton button[kind="secondary"]{background:#1e1e3f!important;border:1px solid #667eea66!important;color:#c4b5fd!important;border-radius:10px!important}
h1,h2,h3,h4{color:#e8e8ff!important}
p,.stMarkdown p{color:#c4b5fd!important}
.info-banner{background:linear-gradient(135deg,#1e3a5f,#1e3a5f99);border-left:4px solid #3b82f6;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#93c5fd!important}
.ok-banner{background:linear-gradient(135deg,#0a3b1e,#0a3b1e99);border-left:4px solid #22c55e;border-radius:10px;padding:14px 18px;margin:8px 0 16px;color:#86efac!important;font-size:0.9rem}
.alert-banner{background:linear-gradient(135deg,#3b0a1e,#3b0a1e99);border-left:4px solid #f43f5e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;color:#fca5a5!important}
.warn-banner{background:linear-gradient(135deg,#3b2a0a,#3b2a0a99);border-left:4px solid #f59e0b;border-radius:10px;padding:11px 16px;margin:8px 0 16px;color:#fcd34d!important}
[data-testid="stFileUploader"]{background:linear-gradient(135deg,#1e1e3f,#2d2b55)!important;border:2px dashed #667eea66!important;border-radius:14px!important}
[data-testid="stProgressBar"] div{background:linear-gradient(90deg,#667eea,#f093fb)!important;border-radius:10px!important}
.rtable{width:100%;border-collapse:collapse;font-size:0.88rem;margin-top:8px}
.rtable th{background:#2d2b55;color:#c4b5fd;padding:10px 14px;text-align:left;border-bottom:1px solid #667eea44}
.rtable td{padding:9px 14px;border-bottom:1px solid #ffffff10;color:#e8e8ff}
.rtable tr:hover td{background:#ffffff08}
.badge-ok{background:#065f46;color:#d1fae5;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;white-space:nowrap}
.badge-miss{background:#991b1b;color:#fee2e2;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;white-space:nowrap}
.badge-warn{background:#78350f;color:#fef3c7;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;white-space:nowrap}
footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
COMPANIES = {
    "La Rouche":         "LAROUCHE",
    "Fashion Limits":    "FASHION_LIMITS",
    "Different Clothes": "DIFFC",
}

REBRACKET = re.compile(r'[A-Za-z0-9#\-]{3,30}')
REGENERAL = re.compile(r'[A-Z]{2,6}[-]?(?:[A-Z0-9]{1,4}[-]?){1,15}')
EXCLUDE   = frozenset(['SR','VAT','TAX','PCS','QTY','NO','REF','INV','PO','SO',
                       'DO','ID','EN','AR','PDF','AED','SAR','USD','KWD','OMR',
                       'BHD','JOD','EGP','TRY'])

for k, v in {
    "sync_results": None,
    "sync_swag_map": {},
    "sync_target_codes": set(),
    "sync_uid_swag": None,
    "sync_uid_target": None,
    "sync_swag_cfg": None,
    "sync_company_checked": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════
@st.cache_resource
def get_proxy(url, ep):
    return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{ep}", allow_none=True)

def odoo_auth(cfg):
    try:
        uid = get_proxy(cfg["url"], "common").authenticate(
            cfg["db"], cfg["user"], cfg["api_key"], {})
        return uid or None
    except Exception:
        return None

def odoo_call(cfg, uid, model, method, args, kwargs={}, retries=5):
    for attempt in range(retries):
        try:
            return get_proxy(cfg["url"], "object").execute_kw(
                cfg["db"], uid, cfg["api_key"], model, method, args, kwargs)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                raise e

def valid_code(c):
    code = c.strip().upper()
    return (bool(re.search(r'[A-Z]', code)) and
            bool(re.search(r'\d', code)) and
            4 <= len(code) <= 25 and
            code not in EXCLUDE)

@st.cache_data(show_spinner=False)
def parse_pdf(file_bytes):
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    text = ""
    for page in PdfReader(io.BytesIO(file_bytes)).pages:
        text += page.extract_text() or ""
    raw = REBRACKET.findall(text) + REGENERAL.findall(text)
    seen, out = set(), []
    for c in raw:
        u = c.strip().upper()
        if valid_code(u) and u not in seen:
            seen.add(u)
            out.append(u)
    return out

def get_or_create_category(cfg, uid, categ_name):
    parts = [p.strip() for p in categ_name.split("/")]
    parent_id = None
    for part in parts:
        domain = [["name", "=", part]]
        if parent_id:
            domain.append(["parent_id", "=", parent_id])
        res = odoo_call(cfg, uid, "product.category", "search_read",
                        [domain], {"fields": ["id"], "limit": 1})
        if res:
            parent_id = res[0]["id"]
        else:
            vals = {"name": part}
            if parent_id:
                vals["parent_id"] = parent_id
            parent_id = odoo_call(cfg, uid, "product.category", "create", [vals])
    return parent_id

def get_or_create_brand(cfg, uid, brand_name):
    try:
        res = odoo_call(cfg, uid, "product.brand", "search_read",
                        [[["name", "=", brand_name]]], {"fields": ["id"], "limit": 1})
        if res:
            return res[0]["id"]
        return odoo_call(cfg, uid, "product.brand", "create", [{"name": brand_name}])
    except Exception:
        return None

def get_or_create_season(cfg, uid, season_name):
    try:
        res = odoo_call(cfg, uid, "product.season", "search_read",
                        [[["name", "=", season_name]]], {"fields": ["id"], "limit": 1})
        if res:
            return res[0]["id"]
        return odoo_call(cfg, uid, "product.season", "create", [{"name": season_name}])
    except Exception:
        return None

def create_product(target_cfg, uid_target, prod):
    categ_id  = None
    brand_id  = None
    season_id = None

    if prod.get("categ_id"):
        cname = prod["categ_id"][1] if isinstance(prod["categ_id"], (list,tuple)) else str(prod["categ_id"])
        try:
            categ_id = get_or_create_category(target_cfg, uid_target, cname)
        except Exception:
            pass

    if prod.get("brand_id"):
        bname = prod["brand_id"][1] if isinstance(prod["brand_id"], (list,tuple)) else str(prod["brand_id"])
        brand_id = get_or_create_brand(target_cfg, uid_target, bname)

    if prod.get("season_id"):
        sname = prod["season_id"][1] if isinstance(prod["season_id"], (list,tuple)) else str(prod["season_id"])
        season_id = get_or_create_season(target_cfg, uid_target, sname)

    vals = {
        "name":           prod.get("name", ""),
        "default_code":   prod.get("default_code", ""),
        "type":           prod.get("type", "consu"),
        "list_price":     float(prod.get("compare_list_price") or prod.get("list_price") or 0.0),
        "standard_price": float(prod.get("standard_price") or 0.0),
    }
    if categ_id:              vals["categ_id"]  = categ_id
    if brand_id:              vals["brand_id"]  = brand_id
    if season_id:             vals["season_id"] = season_id
    if prod.get("barcode"):   vals["barcode"]   = prod["barcode"]

    return odoo_call(target_cfg, uid_target, "product.template", "create", [vals])

# ══════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center;padding:24px 0 12px'>
  <div style='font-size:2.4rem;font-weight:700;
    background:linear-gradient(90deg,#667eea,#f093fb,#43e97b);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
    🔄 Product Sync
  </div>
  <div style='color:#a0aec0;font-size:0.95rem;margin-top:6px'>
    SWAG → La Rouche &nbsp;/&nbsp; Fashion Limits &nbsp;/&nbsp; Different Clothes
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="info-banner">📌 SWAG se products check karo aur missing ones ko target company me create karo. Category, Brand, Season automatically ban jaate hain.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# STEP 1 — Company
# ══════════════════════════════════════════════════════════
st.markdown("### 🏢 Step 1 — Target Company select karo")
selected_label = st.selectbox("", list(COMPANIES.keys()),
                               key="sync_company", label_visibility="collapsed")
target_key     = COMPANIES[selected_label]
target_cfg_raw = st.secrets.get(target_key)

if not target_cfg_raw:
    st.error(f"❌ Secrets missing for `{target_key}`. Check secrets.toml.")
    st.stop()

target_cfg = dict(target_cfg_raw)

if st.session_state.sync_company_checked != selected_label:
    st.session_state.sync_results         = None
    st.session_state.sync_swag_map        = {}
    st.session_state.sync_target_codes    = set()
    st.session_state.sync_uid_swag        = None
    st.session_state.sync_uid_target      = None
    st.session_state.sync_company_checked = selected_label

st.divider()

# ══════════════════════════════════════════════════════════
# STEP 2 — Input
# ══════════════════════════════════════════════════════════
st.markdown("### 📋 Step 2 — Product codes daalo")

input_method = st.radio("", ["✏️ Manual entry", "📄 Upload PDF invoice"],
                         horizontal=True, key="sync_method",
                         label_visibility="collapsed")
codes = []

if "✏️" in input_method:
    raw_codes = st.text_area("Product codes (ek line me ek code)",
                              height=160,
                              placeholder="XP6013\nRVT196\nABC123\n5606#",
                              key="sync_manual")
    codes = [c.strip() for c in raw_codes.splitlines() if c.strip()]
    if codes:
        st.caption(f"📌 {len(codes)} codes ready")
else:
    pdf_file = st.file_uploader("PDF invoice upload karo", type="pdf", key="sync_pdf")
    if pdf_file:
        with st.spinner("📄 Parsing PDF..."):
            fbytes = pdf_file.read()
            ck     = f"pdf_{hashlib.md5(fbytes).
