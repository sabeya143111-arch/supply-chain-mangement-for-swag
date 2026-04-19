"""
SWAG Product Sync — Streamlit app
Sync products from SWAG (source Odoo) to target companies via XML-RPC.
"""
import io
import re
import time
import xmlrpc.client
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
from pypdf import PdfReader

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SWAG Product Sync",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Premium CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f8f9fa;
  --surface:#ffffff;
  --sidebar:#0f172a;
  --sidebar-fg:#e2e8f0;
  --primary:#6366f1;
  --primary-600:#4f46e5;
  --text:#0f172a;
  --muted:#64748b;
  --border:#e2e8f0;
  --success:#10b981;
  --danger:#ef4444;
  --warning:#f59e0b;
}
html,body,[class*="css"]{font-family:'Inter',sans-serif;color:var(--text);}
h1,h2,h3,h4,h5,h6,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{
  font-family:'Space Grotesk',sans-serif!important;letter-spacing:-0.02em;
}
.stApp{background:var(--bg);}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}

/* Sidebar */
section[data-testid="stSidebar"]{background:var(--sidebar)!important;}
section[data-testid="stSidebar"] *{color:var(--sidebar-fg)!important;}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3{color:#fff!important;}

/* Buttons */
.stButton>button, .stDownloadButton>button{
  background:var(--primary);color:#fff;border:none;border-radius:10px;
  padding:.6rem 1.2rem;font-weight:600;font-family:'Inter',sans-serif;
  transition:all .2s ease;box-shadow:0 1px 2px rgba(15,23,42,.08);
}
.stButton>button:hover, .stDownloadButton>button:hover{
  background:var(--primary-600);transform:translateY(-1px);
  box-shadow:0 6px 18px rgba(99,102,241,.35);
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"]>div{
  background:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:10px!important;
}

/* Cards */
.card{
  background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(15,23,42,.05);
  margin-bottom:1rem;
}
.metric-card{
  background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:1.25rem;box-shadow:0 1px 3px rgba(15,23,42,.05);
}
.metric-label{color:var(--muted);font-size:.8rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.05em;}
.metric-value{font-family:'Space Grotesk',sans-serif;font-size:2rem;
  font-weight:700;color:var(--text);margin-top:.25rem;}

/* Badges */
.badge{display:inline-block;padding:.25rem .65rem;border-radius:999px;
  font-size:.75rem;font-weight:600;}
.badge-ok{background:#d1fae5;color:#065f46;}
.badge-miss{background:#fee2e2;color:#991b1b;}
.badge-warn{background:#fef3c7;color:#92400e;}
.badge-var{background:#ede9fe;color:#5b21b6;}

/* Status dots */
.dot{display:inline-block;width:.6rem;height:.6rem;border-radius:50%;
  margin-right:.5rem;vertical-align:middle;}
.dot-ok{background:#10b981;box-shadow:0 0 0 3px rgba(16,185,129,.2);}
.dot-bad{background:#ef4444;box-shadow:0 0 0 3px rgba(239,68,68,.2);}

/* Progress */
.stProgress>div>div>div>div{background:linear-gradient(90deg,#6366f1,#8b5cf6)!important;}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:.5rem;}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:10px;
  padding:.5rem 1rem;font-weight:600;}
.stTabs [aria-selected="true"]{background:var(--primary)!important;color:#fff!important;}

/* DataFrame */
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden;}

.sidebar-item{padding:.5rem 0;border-bottom:1px solid #1e293b;font-size:.85rem;}
.sidebar-item:last-child{border-bottom:none;}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Targets
# ──────────────────────────────────────────────────────────────────────────────
TARGETS = {
    "La Rouche": "LAROUCHE",
    "Fashion Limits": "FASHION_LIMITS",
    "Different Clothes": "DIFFC",
}

# ──────────────────────────────────────────────────────────────────────────────
# XML-RPC helpers
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def proxy(url, ep):
    return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{ep}", allow_none=True)


def auth(url, db, user, key):
    try:
        uid = proxy(url, "common").authenticate(db, user, key, {})
        return uid or None
    except Exception:
        return None


def odoo_call(cfg, uid, model, method, args, kwargs=None, retries=5):
    if kwargs is None:
        kwargs = {}
    last = None
    for attempt in range(retries):
        try:
            return proxy(cfg["url"], "object").execute_kw(
                cfg["db"], uid, cfg["api_key"], model, method, args, kwargs
            )
        except Exception as e:
            last = e
            if attempt < retries - 1:
                time.sleep(3)
            else:
                raise last


def get_cfg(key):
    s = st.secrets[key]
    return {"url": s["url"], "db": s["db"], "user": s["user"], "api_key": s["api_key"]}


# ──────────────────────────────────────────────────────────────────────────────
# PDF parsing
# ──────────────────────────────────────────────────────────────────────────────
EXCLUDE = {
    "SR", "VAT", "TAX", "PCS", "QTY", "NO", "REF", "INV", "PDF", "SAR",
    "USD", "EUR", "AED", "TOTAL", "SUB", "DISC", "AMT", "ITEM", "DESC",
    "PRICE", "CODE", "DATE", "PAGE",
}


def parse_pdf_codes(file_bytes: bytes):
    text = ""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text += "\n" + (page.extract_text() or "")
    except Exception as e:
        st.error(f"PDF read error: {e}")
        return []

    pattern = re.compile(r"\b[A-Z0-9][A-Z0-9\-]{3,24}\b")
    raw = pattern.findall(text.upper())
    seen, out = set(), []
    for c in raw:
        if c in EXCLUDE or c in seen:
            continue
        if not (4 <= len(c) <= 25):
            continue
        has_a = any(ch.isalpha() for ch in c)
        has_n = any(ch.isdigit() for ch in c)
        if not (has_a and has_n):
            continue
        seen.add(c)
        out.append(c)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# get_or_create
# ──────────────────────────────────────────────────────────────────────────────
def get_or_create(cfg, uid, model, name, extra=None):
    if not name:
        return False
    ids = odoo_call(cfg, uid, model, "search", [[["name", "=", name]]], {"limit": 1})
    if ids:
        return ids[0]
    vals = {"name": name}
    if extra:
        vals.update(extra)
    try:
        return odoo_call(cfg, uid, model, "create", [vals])
    except Exception:
        ids = odoo_call(cfg, uid, model, "search", [[["name", "=", name]]], {"limit": 1})
        return ids[0] if ids else False


# ──────────────────────────────────────────────────────────────────────────────
# Bulk fetchers
# ──────────────────────────────────────────────────────────────────────────────
PROD_FIELDS = [
    "name", "default_code", "categ_id", "barcode", "type",
    "standard_price", "list_price", "attribute_line_ids",
]
OPTIONAL_FIELDS = ["brand_id", "season_id", "compare_list_price"]


def fetch_swag_products(cfg, uid, codes=None, limit=5000):
    domain = [("default_code", "!=", False)]
    if codes:
        domain = [("default_code", "in", list(codes))]
    fields = PROD_FIELDS + OPTIONAL_FIELDS
    try:
        return odoo_call(
            cfg, uid, "product.template", "search_read",
            [domain], {"fields": fields, "limit": limit},
        )
    except Exception:
        return odoo_call(
            cfg, uid, "product.template", "search_read",
            [domain], {"fields": PROD_FIELDS, "limit": limit},
        )


def fetch_existing_codes(cfg, uid, codes=None, limit=5000):
    domain = [("default_code", "!=", False)]
    if codes:
        domain = [("default_code", "in", list(codes))]
    rows = odoo_call(
        cfg, uid, "product.template", "search_read",
        [domain], {"fields": ["default_code"], "limit": limit},
    )
    return {r["default_code"] for r in rows if r.get("default_code")}


# ──────────────────────────────────────────────────────────────────────────────
# Variant handling
# ──────────────────────────────────────────────────────────────────────────────
def build_variant_attribute_lines(swag_cfg, swag_uid, tgt_cfg, tgt_uid, attr_line_ids):
    if not attr_line_ids:
        return []
    lines = odoo_call(
        swag_cfg, swag_uid, "product.template.attribute.line",
        "read", [attr_line_ids], {"fields": ["attribute_id", "value_ids"]},
    )
    out = []
    for ln in lines:
        attr_id = ln["attribute_id"][0] if ln.get("attribute_id") else False
        if not attr_id:
            continue
        attr = odoo_call(swag_cfg, swag_uid, "product.attribute", "read",
                         [[attr_id]], {"fields": ["name", "create_variant"]})[0]
        vals = odoo_call(swag_cfg, swag_uid, "product.attribute.value", "read",
                         [ln["value_ids"]], {"fields": ["name"]}) if ln.get("value_ids") else []

        tgt_attr = get_or_create(tgt_cfg, tgt_uid, "product.attribute", attr["name"],
                                 {"create_variant": attr.get("create_variant") or "always"})
        tgt_value_ids = []
        for v in vals:
            vid = odoo_call(tgt_cfg, tgt_uid, "product.attribute.value", "search",
                            [[["name", "=", v["name"]], ["attribute_id", "=", tgt_attr]]],
                            {"limit": 1})
            if vid:
                tgt_value_ids.append(vid[0])
            else:
                new_v = odoo_call(tgt_cfg, tgt_uid, "product.attribute.value", "create",
                                  [{"name": v["name"], "attribute_id": tgt_attr}])
                tgt_value_ids.append(new_v)

        out.append((0, 0, {"attribute_id": tgt_attr, "value_ids": [(6, 0, tgt_value_ids)]}))
    return out


def sync_variant_codes(swag_cfg, swag_uid, tgt_cfg, tgt_uid,
                       swag_template_id, tgt_template_id):
    """Match SWAG variants to target variants by attribute values, copy default_code."""
    try:
        swag_variants = odoo_call(
            swag_cfg, swag_uid, "product.product", "search_read",
            [[["product_tmpl_id", "=", swag_template_id]]],
            {"fields": ["default_code", "product_template_attribute_value_ids"]},
        )
        tgt_variants = odoo_call(
            tgt_cfg, tgt_uid, "product.product", "search_read",
            [[["product_tmpl_id", "=", tgt_template_id]]],
            {"fields": ["default_code", "product_template_attribute_value_ids"]},
        )

        def names_for(cfg, uid, ptav_ids):
            if not ptav_ids:
                return frozenset()
            rows = odoo_call(cfg, uid, "product.template.attribute.value", "read",
                             [ptav_ids], {"fields": ["name"]})
            return frozenset((r.get("name") or "").strip().lower() for r in rows)

        tgt_map = {names_for(tgt_cfg, tgt_uid, v["product_template_attribute_value_ids"]): v["id"]
                   for v in tgt_variants}

        matched = 0
        for sv in swag_variants:
            if not sv.get("default_code"):
                continue
            key = names_for(swag_cfg, swag_uid, sv["product_template_attribute_value_ids"])
            if key in tgt_map:
                odoo_call(tgt_cfg, tgt_uid, "product.product", "write",
                          [[tgt_map[key]], {"default_code": sv["default_code"]}])
                matched += 1
        return matched
    except Exception:
        return 0


# ──────────────────────────────────────────────────────────────────────────────
# Create product
# ──────────────────────────────────────────────────────────────────────────────
def humanize_error(err: str) -> str:
    s = (err or "").lower()
    if "access denied" in s or "access" in s and "denied" in s:
        return "No permission (Access Denied)"
    if "unique" in s and "constraint" in s:
        return "Already exists (unique constraint)"
    m = re.search(r"required field[^:]*:?\s*([a-z0-9_\.]+)", s)
    if m:
        return f"Missing required field: {m.group(1)}"
    if "required" in s:
        return "Missing required field"
    if "invalid field" in s:
        return "Invalid field for this model"
    return "Unknown error"


def create_product(swag_cfg, swag_uid, tgt_cfg, tgt_uid, prod):
    """Create one product in target. Returns dict result."""
    code = prod.get("default_code") or ""
    try:
        cat_name = prod["categ_id"][1] if prod.get("categ_id") else False
        brand_name = prod["brand_id"][1] if prod.get("brand_id") else False
        season_name = prod["season_id"][1] if prod.get("season_id") else False

        cat_id = get_or_create(tgt_cfg, tgt_uid, "product.category", cat_name) if cat_name else False
        brand_id = get_or_create(tgt_cfg, tgt_uid, "product.brand", brand_name) if brand_name else False
        season_id = get_or_create(tgt_cfg, tgt_uid, "product.season", season_name) if season_name else False

        sale_price = prod.get("compare_list_price") or prod.get("list_price") or 0.0

        vals = {
            "name": prod.get("name") or code,
            "default_code": code,
            "type": prod.get("type") or "product",
            "list_price": sale_price,
            "standard_price": prod.get("standard_price") or 0.0,
        }
        if prod.get("barcode"):
            vals["barcode"] = prod["barcode"]
        if cat_id:
            vals["categ_id"] = cat_id

        # optional fields — set only if target accepts them
        optional = {}
        if brand_id:
            optional["brand_id"] = brand_id
        if season_id:
            optional["season_id"] = season_id

        attr_line_ids = prod.get("attribute_line_ids") or []
        has_variants = bool(attr_line_ids)

        if has_variants:
            try:
                lines = build_variant_attribute_lines(
                    swag_cfg, swag_uid, tgt_cfg, tgt_uid, attr_line_ids
                )
                vals_with_var = {**vals, **optional}
                if lines:
                    vals_with_var["attribute_line_ids"] = lines
                try:
                    new_id = odoo_call(tgt_cfg, tgt_uid, "product.template", "create",
                                       [vals_with_var])
                except Exception:
                    # retry without optional fields
                    vals_with_var2 = {**vals}
                    if lines:
                        vals_with_var2["attribute_line_ids"] = lines
                    new_id = odoo_call(tgt_cfg, tgt_uid, "product.template", "create",
                                       [vals_with_var2])

                matched = sync_variant_codes(swag_cfg, swag_uid, tgt_cfg, tgt_uid,
                                             prod["id"], new_id)
                return {"code": code, "ok": True, "id": new_id,
                        "msg": f"Created with {matched} variant codes synced"}
            except Exception as ve:
                # fallback simple
                try:
                    simple_vals = {**vals, **optional}
                    new_id = odoo_call(tgt_cfg, tgt_uid, "product.template", "create", [simple_vals])
                    return {"code": code, "ok": True, "id": new_id,
                            "msg": f"Variant create failed, created as simple ({humanize_error(str(ve))})"}
                except Exception as se:
                    new_id = odoo_call(tgt_cfg, tgt_uid, "product.template", "create", [vals])
                    return {"code": code, "ok": True, "id": new_id,
                            "msg": f"Created minimal (variant fallback): {humanize_error(str(se))}"}
        else:
            try:
                vals_full = {**vals, **optional}
                new_id = odoo_call(tgt_cfg, tgt_uid, "product.template", "create", [vals_full])
            except Exception:
                new_id = odoo_call(tgt_cfg, tgt_uid, "product.template", "create", [vals])
            return {"code": code, "ok": True, "id": new_id, "msg": "Created"}

    except Exception as e:
        return {"code": code, "ok": False, "msg": humanize_error(str(e)), "raw": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Parallel create
# ──────────────────────────────────────────────────────────────────────────────
def parallel_create(swag_cfg, swag_uid, tgt_cfg, tgt_uid, products, progress_cb=None):
    results = []
    total = len(products)
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(create_product, swag_cfg, swag_uid, tgt_cfg, tgt_uid, p): p
                   for p in products}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            if progress_cb:
                progress_cb(done, total, res)
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "last_sync" not in st.session_state:
    st.session_state.last_sync = None


def log_history(action, company, summary):
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action, "company": company, "summary": summary,
    })
    st.session_state.history = st.session_state.history[:5]
    st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ SWAG Sync")
    st.markdown("###### Premium product sync console")
    st.markdown("---")
    st.markdown("**Last sync**")
    st.markdown(f"<div class='sidebar-item'>{st.session_state.last_sync or '—'}</div>",
                unsafe_allow_html=True)

    st.markdown("**Connection status**")
    statuses_html = ""
    for name, key in [("SWAG", "SWAG"), *TARGETS.items()]:
        try:
            cfg = get_cfg(key)
            uid = auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
            ok = bool(uid)
        except Exception:
            ok = False
        dot = "dot-ok" if ok else "dot-bad"
        statuses_html += f"<div class='sidebar-item'><span class='dot {dot}'></span>{name}</div>"
    st.markdown(statuses_html, unsafe_allow_html=True)

    st.markdown("**Recent activity**")
    if not st.session_state.history:
        st.markdown("<div class='sidebar-item'>No activity yet</div>", unsafe_allow_html=True)
    else:
        for h in st.session_state.history:
            st.markdown(
                f"<div class='sidebar-item'><b>{h['time']}</b> · {h['action']}<br>"
                f"<span style='opacity:.7'>{h['company']} — {h['summary']}</span></div>",
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("# SWAG Product Sync")
st.markdown(
    "<p style='color:var(--muted);margin-top:-.5rem;'>Sync products from SWAG to your target companies — fast, reliable, parallelized.</p>",
    unsafe_allow_html=True,
)

tab_scan, tab_manual = st.tabs(["🔎 Full Scan", "✏️ Manual Sync"])


# ──────────────────────────────────────────────────────────────────────────────
# Helpers for UI
# ──────────────────────────────────────────────────────────────────────────────
def status_badge(label):
    if label == "✅ Already exists":
        return f"<span class='badge badge-ok'>{label}</span>"
    if label == "❌ Missing":
        return f"<span class='badge badge-miss'>{label}</span>"
    return f"<span class='badge badge-warn'>{label}</span>"


def metric_card(col, label, value, color="var(--text)"):
    col.markdown(
        f"<div class='metric-card'><div class='metric-label'>{label}</div>"
        f"<div class='metric-value' style='color:{color};'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def df_from_products(products, status_map):
    rows = []
    for p in products:
        code = p.get("default_code") or ""
        rows.append({
            "Code": code,
            "Product Name": p.get("name") or "",
            "Category": p["categ_id"][1] if p.get("categ_id") else "",
            "Brand": p["brand_id"][1] if p.get("brand_id") else "",
            "Type": ("🔀 Has Variants (%d)" % len(p.get("attribute_line_ids") or []))
                    if p.get("attribute_line_ids") else (p.get("type") or ""),
            "Status": status_map.get(code, "❌ Missing"),
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Tab: Full Scan
# ──────────────────────────────────────────────────────────────────────────────
with tab_scan:
    st.markdown("### Full Catalog Scan")
    st.markdown(
        "<p style='color:var(--muted)'>Compare all SWAG products against the target company and find what's missing.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        company = st.selectbox("Target company", list(TARGETS.keys()), key="scan_company")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🔎 Scan Now", use_container_width=True, key="scan_btn")

    if scan_btn:
        try:
            swag_cfg = get_cfg("SWAG")
            tgt_cfg = get_cfg(TARGETS[company])
            with st.spinner("Authenticating…"):
                swag_uid = auth(**swag_cfg)
                tgt_uid = auth(**tgt_cfg)
            if not swag_uid or not tgt_uid:
                st.error("Authentication failed. Check credentials in secrets.toml.")
            else:
                with st.spinner("Fetching SWAG catalog…"):
                    swag_products = fetch_swag_products(swag_cfg, swag_uid, limit=5000)
                with st.spinner(f"Fetching {company} catalog…"):
                    existing = fetch_existing_codes(tgt_cfg, tgt_uid, limit=5000)

                swag_codes = {p["default_code"] for p in swag_products if p.get("default_code")}
                missing_codes = swag_codes - existing
                missing_products = [p for p in swag_products
                                    if p.get("default_code") in missing_codes]

                m1, m2, m3 = st.columns(3)
                metric_card(m1, "Total in SWAG", len(swag_codes))
                metric_card(m2, "Already in target", len(swag_codes & existing), "var(--success)")
                metric_card(m3, "Missing", len(missing_codes), "var(--danger)")

                st.session_state["scan_missing"] = missing_products
                st.session_state["scan_company"] = company
                log_history("Full Scan", company,
                            f"{len(missing_codes)} missing of {len(swag_codes)}")
        except Exception as e:
            st.error(f"Scan failed: {e}")

    if st.session_state.get("scan_missing"):
        missing = st.session_state["scan_missing"]
        st.markdown("#### Missing products")
        df = df_from_products(missing, {})
        st.dataframe(df, use_container_width=True, height=420)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name=f"missing_{st.session_state['scan_company'].replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c2:
            if st.button("🚀 Create All Missing", use_container_width=True, key="create_all_missing"):
                swag_cfg = get_cfg("SWAG")
                tgt_cfg = get_cfg(TARGETS[st.session_state["scan_company"]])
                swag_uid = auth(**swag_cfg)
                tgt_uid = auth(**tgt_cfg)

                progress = st.progress(0.0, text="Starting…")
                status = st.empty()

                def cb(done, total, res):
                    progress.progress(done / total,
                                      text=f"{done}/{total} — {res['code']} ({'✓' if res['ok'] else '✗'})")

                results = parallel_create(swag_cfg, swag_uid, tgt_cfg, tgt_uid,
                                          missing, progress_cb=cb)
                ok = [r for r in results if r["ok"]]
                fail = [r for r in results if not r["ok"]]
                status.success(f"Done — Created: {len(ok)} · Failed: {len(fail)}")
                if fail:
                    st.dataframe(pd.DataFrame(fail), use_container_width=True)
                log_history("Bulk Create", st.session_state["scan_company"],
                            f"{len(ok)} created, {len(fail)} failed")


# ──────────────────────────────────────────────────────────────────────────────
# Tab: Manual Sync
# ──────────────────────────────────────────────────────────────────────────────
with tab_manual:
    st.markdown("### Manual Product Sync")
    st.markdown(
        "<p style='color:var(--muted)'>Paste codes or upload a PDF invoice — we'll check and sync the missing ones.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        m_company = st.selectbox("Target company", list(TARGETS.keys()), key="m_company")
    with c2:
        method = st.radio("Input method", ["Manual", "PDF"], horizontal=True, key="m_method")

    codes_input = []
    if method == "Manual":
        txt = st.text_area("Product codes (one per line, comma or space separated)",
                           height=140, key="m_text")
        if txt:
            codes_input = re.split(r"[\s,;\n]+", txt.strip().upper())
            codes_input = [c for c in codes_input if c]
    else:
        up = st.file_uploader("Upload PDF invoice", type=["pdf"], key="m_pdf")
        if up:
            codes_input = parse_pdf_codes(up.read())
            st.info(f"Extracted {len(codes_input)} candidate codes from PDF.")

    if st.button("🔍 Check Products", use_container_width=True, key="m_check"):
        if not codes_input:
            st.warning("No codes provided.")
        else:
            try:
                swag_cfg = get_cfg("SWAG")
                tgt_cfg = get_cfg(TARGETS[m_company])
                swag_uid = auth(**swag_cfg)
                tgt_uid = auth(**tgt_cfg)
                if not swag_uid or not tgt_uid:
                    st.error("Authentication failed.")
                else:
                    with st.spinner("Fetching from SWAG…"):
                        swag_products = fetch_swag_products(swag_cfg, swag_uid,
                                                            codes=codes_input)
                    with st.spinner(f"Checking {m_company}…"):
                        existing = fetch_existing_codes(tgt_cfg, tgt_uid, codes=codes_input)

                    swag_by_code = {p["default_code"]: p for p in swag_products
                                    if p.get("default_code")}
                    status_map = {}
                    rows = []
                    for code in codes_input:
                        if code in existing:
                            status_map[code] = "✅ Already exists"
                        elif code in swag_by_code:
                            status_map[code] = "❌ Missing"
                        else:
                            status_map[code] = "⚠️ Not in SWAG"

                    # Build the table from union (so unknown codes also show)
                    all_rows = []
                    for code in codes_input:
                        p = swag_by_code.get(code, {"default_code": code, "name": "—"})
                        all_rows.append({
                            "Code": code,
                            "Product Name": p.get("name") or "—",
                            "Category": p["categ_id"][1] if p.get("categ_id") else "",
                            "Brand": p["brand_id"][1] if p.get("brand_id") else "",
                            "Type": ("🔀 Has Variants (%d)" % len(p.get("attribute_line_ids") or []))
                                    if p.get("attribute_line_ids") else (p.get("type") or ""),
                            "Status": status_map[code],
                        })
                    df = pd.DataFrame(all_rows)
                    st.session_state["m_df"] = df
                    st.session_state["m_to_create"] = [
                        swag_by_code[c] for c in codes_input
                        if status_map[c] == "❌ Missing"
                    ]
                    st.session_state["m_company_used"] = m_company
            except Exception as e:
                st.error(f"Check failed: {e}")

    if "m_df" in st.session_state:
        df = st.session_state["m_df"]
        st.markdown("#### Results")
        st.dataframe(df, use_container_width=True, height=380)
        to_create = st.session_state.get("m_to_create", [])
        st.markdown(f"**{len(to_create)}** products ready to create.")

        if to_create and st.button("🚀 Create Missing", use_container_width=True, key="m_create"):
            swag_cfg = get_cfg("SWAG")
            tgt_cfg = get_cfg(TARGETS[st.session_state["m_company_used"]])
            swag_uid = auth(**swag_cfg)
            tgt_uid = auth(**tgt_cfg)

            progress = st.progress(0.0, text="Starting…")

            def cb(done, total, res):
                progress.progress(done / total,
                                  text=f"{done}/{total} — {res['code']} ({'✓' if res['ok'] else '✗'})")

            results = parallel_create(swag_cfg, swag_uid, tgt_cfg, tgt_uid,
                                      to_create, progress_cb=cb)

            ok = [r for r in results if r["ok"]]
            fail = [r for r in results if not r["ok"]]
            skipped = 0  # we only attempted missing ones

            c1, c2, c3 = st.columns(3)
            metric_card(c1, "Created", len(ok), "var(--success)")
            metric_card(c2, "Skipped", skipped, "var(--muted)")
            metric_card(c3, "Errors", len(fail), "var(--danger)")

            if ok:
                st.markdown("##### ✅ Created")
                ok_df = pd.DataFrame(ok)
                st.dataframe(ok_df, use_container_width=True)
                st.download_button("⬇️ Download success CSV",
                                   ok_df.to_csv(index=False).encode("utf-8"),
                                   file_name="created.csv", mime="text/csv")
            if fail:
                st.markdown("##### ❌ Errors")
                fail_df = pd.DataFrame(fail)
                st.dataframe(fail_df, use_container_width=True)
                st.download_button("⬇️ Download errors CSV",
                                   fail_df.to_csv(index=False).encode("utf-8"),
                                   file_name="errors.csv", mime="text/csv")

            log_history("Manual Sync", st.session_state["m_company_used"],
                        f"{len(ok)} ok, {len(fail)} err")
