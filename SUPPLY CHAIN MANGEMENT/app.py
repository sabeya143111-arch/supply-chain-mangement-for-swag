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
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1a2e 0,#16213e 100%)!important}
.stTabs [data-baseweb="tab-list"]{background:linear-gradient(90deg,#1e1e3f,#2d2b55);border-radius:12px;padding:4px;gap:4px}
.stTabs [data-baseweb="tab"]{color:#a0aec0!important;border-radius:10px!important;font-weight:600!important}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#667eea,#764ba2)!important;color:white!important}
.stButton button[kind="primary"]{background:linear-gradient(90deg,#667eea,#764ba2,#f093fb)!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important}
.stButton button[kind="secondary"]{background:#1e1e3f!important;border:1px solid #667eea66!important;color:#c4b5fd!important;border-radius:10px!important}
h1,h2,h3,h4{color:#e8e8ff!important}
.stMarkdown p{color:#c4b5fd!important}
.info-banner{background:linear-gradient(135deg,#1e3a5f,#1e3a5f99);border-left:4px solid #3b82f6;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#93c5fd!important}
.ok-banner{background:linear-gradient(135deg,#0a3b1e,#0a3b1e99);border-left:4px solid #22c55e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#86efac!important}
.alert-banner{background:linear-gradient(135deg,#3b0a1e,#3b0a1e99);border-left:4px solid #f43f5e;border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:#fca5a5!important}
[data-testid="stFileUploader"]{background:linear-gradient(135deg,#1e1e3f,#2d2b55)!important;border:2px dashed #667eea66!important;border-radius:14px!important}
[data-testid="stProgressBar"] div{background:linear-gradient(90deg,#667eea,#f093fb)!important;border-radius:10px!important}
footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

# ── CONFIG ───────────────────────────────────────────────
COMPANIES = {
    "La Rouche": "LAROUCHE",
    "Fashion Limits": "FASHION_LIMITS",
    "Different Clothes": "DIFFC",
}

REBRACKET = re.compile(r'[A-Za-z0-9#\-]{3,30}')
RESRLINE  = re.compile(r'(?:[A-Z]{2,6})?[-]?(?:[A-Z]{0,6}[-])?[A-Z0-9]{1,10}[^\n]{0,80}?(?:SR)', re.MULTILINE)
REGENERAL = re.compile(r'[A-Z]{2,6}[-]?(?:[A-Z0-9]{1,4}[-]?){1,15}')
EXCLUDE   = frozenset(['SR','VAT','TAX','PCS','QTY','NO','REF','INV','PO','SO',
                       'DO','ID','EN','AR','PDF','AED','SAR','USD','KWD','OMR',
                       'BHD','JOD','EGP','TRY'])

# ── HELPERS ──────────────────────────────────────────────
@st.cache_resource
def proxy(url, ep):
    return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{ep}", allow_none=True)

def auth(url, db, user, key):
    try:
        uid = proxy(url, "common").authenticate(db, user, key, {})
        return uid or None
    except Exception:
        return None

def x(url, db, uid, key, model, method, domain, kw={}):
    return proxy(url, "object").execute_kw(db, uid, key, model, method, domain, kw)

def call_with_retry(fn, *args, retries=5, **kwargs):
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(4)
            else:
                raise e

def valid_code(c):
    code = c.strip().upper()
    return (bool(re.search(r'[A-Z]', code)) and
            bool(re.search(r'\d', code)) and
            4 <= len(code) <= 25 and
            code not in EXCLUDE)

@st.cache_data(show_spinner=False)
def parse_invoice_pdf(file_bytes):
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    text = ""
    for page in PdfReader(io.BytesIO(file_bytes)).pages:
        text += page.extract_text() or ""
    if not text.strip():
        return []
    raw = (REBRACKET.findall(text) +
           [m.group(1) for m in RESRLINE.finditer(text)] +
           REGENERAL.findall(text))
    seen, out = set(), []
    seq = 1
    for c in raw:
        u = c.strip().upper()
        if valid_code(u) and u not in seen:
            seen.add(u)
            out.append({"sequence": seq, "code": u})
            seq += 1
    return out

def get_or_create_category(cfg, uid, categ_name):
    parts = [p.strip() for p in categ_name.split("/")]
    parent_id = None
    for part in parts:
        domain = [["name", "=", part]]
        if parent_id:
            domain.append(["parent_id", "=", parent_id])
        res = call_with_retry(x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                              "product.category", "search_read", [domain],
                              {"fields": ["id"], "limit": 1})
        if res:
            parent_id = res[0]["id"]
        else:
            vals = {"name": part}
            if parent_id:
                vals["parent_id"] = parent_id
            parent_id = call_with_retry(x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                                        "product.category", "create", [vals])
    return parent_id

def get_or_create_brand(cfg, uid, brand_name):
    res = call_with_retry(x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                          "product.brand", "search_read",
                          [[["name", "=", brand_name]]],
                          {"fields": ["id"], "limit": 1})
    if res:
        return res[0]["id"]
    return call_with_retry(x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                           "product.brand", "create", [{"name": brand_name}])

def get_or_create_season(cfg, uid, season_name):
    res = call_with_retry(x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                          "product.season", "search_read",
                          [[["name", "=", season_name]]],
                          {"fields": ["id"], "limit": 1})
    if res:
        return res[0]["id"]
    return call_with_retry(x, cfg["url"], cfg["db"], uid, cfg["api_key"],
                           "product.season", "create", [{"name": season_name}])

# ── MAIN UI ──────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:20px 0 10px'>
  <div style='font-size:2.2rem;font-weight:700;background:linear-gradient(90deg,#667eea,#f093fb,#43e97b);
  background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent'>
  🔄 Product Sync</div>
  <div style='color:#a0aec0;font-size:0.95rem;margin-top:4px'>SWAG → La Rouche / Fashion Limits / Different Clothes</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="info-banner">SWAG se products copy karo target company me. Category, Brand, Season auto-create ho jaate hain agar missing ho.</div>', unsafe_allow_html=True)

# ── Company selector ──────────────────────────────────────
selected_label = st.selectbox("🏢 Target Company", list(COMPANIES.keys()), key="sync_company")
target_key = COMPANIES[selected_label]
target_cfg_raw = st.secrets.get(target_key)

if not target_cfg_raw:
    st.error(f"❌ Secrets missing for `{target_key}`. Check your secrets.toml.")
    st.stop()

target_cfg = dict(target_cfg_raw)

st.divider()

# ── Input method ─────────────────────────────────────────
input_method = st.radio("📋 Product codes input method", 
                         ["✏️ Manual entry", "📄 Upload PDF invoice"],
                         horizontal=True, key="sync_method")

codes = []

if "✏️" in input_method:
    raw_codes = st.text_area("Enter product codes (one per line)", height=150,
                              placeholder="XP6013\nRVT196\nABC123", key="sync_manual")
    codes = [c.strip() for c in raw_codes.splitlines() if c.strip()]
else:
    pdf_file = st.file_uploader("Upload PDF invoice", type="pdf", key="sync_pdf")
    if pdf_file:
        with st.spinner("Parsing PDF..."):
            fbytes = pdf_file.read()
            fhash  = hashlib.md5(fbytes).hexdigest()
            ck     = f"pdf_{fhash}"
            if ck not in st.session_state:
                st.session_state[ck] = parse_invoice_pdf(fbytes)
            parsed = st.session_state[ck]
        if parsed:
            codes = list(dict.fromkeys(item["code"] for item in parsed))
            st.success(f"✅ {len(codes)} unique codes extracted from PDF")
            with st.expander(f"Show {len(codes)} codes"):
                st.code(", ".join(codes))
        else:
            st.warning("⚠️ No codes found in PDF.")

st.divider()

# ── Check button ──────────────────────────────────────────
col1, col2 = st.columns([1, 3])
with col1:
    check_btn = st.button("🔍 Check", type="primary", 
                           use_container_width=True, key="sync_check",
                           disabled=len(codes) == 0)

if check_btn and codes:
    swag_cfg = st.secrets.get("SWAG")
    if not swag_cfg:
        st.error("❌ SWAG secrets missing.")
        st.stop()

    with st.spinner("Checking codes..."):
        uid_swag   = auth(swag_cfg["url"], swag_cfg["db"], swag_cfg["user"], swag_cfg["api_key"])
        uid_target = auth(target_cfg["url"], target_cfg["db"], target_cfg["user"], target_cfg["api_key"])

        if not uid_swag:
            st.error("❌ SWAG authentication failed.")
            st.stop()
        if not uid_target:
            st.error(f"❌ {selected_label} authentication failed.")
            st.stop()

        # Fetch from SWAG
        swag_recs = call_with_retry(
            x, swag_cfg["url"], swag_cfg["db"], uid_swag, swag_cfg["api_key"],
            "product.template", "search_read",
            [[["default_code", "in", codes]]],
            {"fields": ["id","name","default_code","categ_id","list_price",
                        "compare_list_price","standard_price","barcode",
                        "brand_id","season_id","type"], "limit": len(codes)+10}
        )
        swag_map = {r["default_code"]: r for r in swag_recs if r.get("default_code")}

        # Fetch from target
        target_recs = call_with_retry(
            x, target_cfg["url"], target_cfg["db"], uid_target, target_cfg["api_key"],
            "product.template", "search_read",
            [[["default_code", "in", codes]]],
            {"fields": ["default_code"], "limit": len(codes)+10}
        )
        target_codes = {r["default_code"] for r in target_recs if r.get("default_code")}

    # Build result table
    results = []
    for code in codes:
        in_swag   = code in swag_map
        in_target = code in target_codes
        name      = swag_map[code]["name"] if in_swag else "—"
        if not in_swag:
            status = "⚠️ Not in SWAG"
        elif in_target:
            status = "✅ Already exists"
        else:
            status = "❌ Missing"
        results.append({"Code": code, "Product Name": name,
                         f"Status in {selected_label}": status})

    st.session_state["sync_results"]    = results
    st.session_state["sync_swag_map"]   = swag_map
    st.session_state["sync_target_codes"] = target_codes
    st.session_state["sync_uid_swag"]   = uid_swag
    st.session_state["sync_uid_target"] = uid_target

# ── Results table 
