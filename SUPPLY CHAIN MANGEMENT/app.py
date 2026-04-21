"""
SO → PO Sync — Standalone App (Light Theme)
Create Purchase Orders in target Odoo (vendors) from Sale Orders in source Odoo.
Source = SWAG (ya koi bhi sales DB)
Target = La Rouche / kisi bhi purchase company
"""

import time
import xmlrpc.client
from datetime import datetime

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# BASIC PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SO → PO Sync",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CSS — same editorial style (black/white/red, Space Grotesk + Inter)
# -----------------------------------------------------------------------------
st.markdown(
    """
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

/* Banners */
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

hr { border: none !important; height: 1px !important; background: #e0e0e0 !important; margin: 24px 0 !important; }

.step-circle {
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; background: #1a1a1a; color: white;
    border-radius: 50%; font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; margin-right: 12px;
}
.section-header { display: flex; align-items: center; margin: 20px 0 16px; }
.section-header h3 { margin: 0; font-weight: 800; }

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# SIMPLE LOGO / TITLE
# -----------------------------------------------------------------------------
st.markdown(
    "<div style='text-align:center;font-size:1.8rem;font-weight:800;"
    "font-family:Space Grotesk;color:#1a1a1a;'>🔄 SO → PO Sync</div>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# GENERIC XML-RPC HELPERS
# -----------------------------------------------------------------------------
def od_proxy(url, ep):
    return xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/{ep}", allow_none=True)

def od_auth(url, db, user, key):
    try:
        common = od_proxy(url, "common")
        uid = common.authenticate(db, user, key, {})
        return uid or None
    except Exception:
        return None

def od_x(url, db, uid, key, model, method, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    obj = od_proxy(url, "object")
    return obj.execute_kw(db, uid, key, model, method, args, kwargs)

def od_call_with_retry(func, *func_args, retries=3, delay=2, **func_kwargs):
    last_error = None
    for attempt in range(retries):
        try:
            return func(*func_args, **func_kwargs)
        except Exception as e:
            last_error = e
            if attempt == retries - 1:
                raise
            time.sleep(delay)
    if last_error:
        raise last_error

# -----------------------------------------------------------------------------
# CONFIG WRAPPER
# -----------------------------------------------------------------------------
class OdooCfg:
    def __init__(self, name, data):
        self.name = name
        self.url = data.get("url", "").rstrip("/")
        self.db = data.get("db", "")
        self.user = data.get("user", "")
        self.apikey = data.get("apikey", "") or data.get("api_key", "")
        self.partner_code_field = data.get("partner_code_field", "company_code")
        self.company_id = data.get("company_id", None)
        self.has_brand_model = bool(data.get("has_brand_model", True))
        self.has_season_model = bool(data.get("has_season_model", True))

    def auth(self):
        return od_auth(self.url, self.db, self.user, self.apikey)

# -----------------------------------------------------------------------------
# SYNC CLASS (SO -> PO)
# -----------------------------------------------------------------------------
class SOtoPOSync:
    def __init__(self, source_cfg: OdooCfg, target_cfg: OdooCfg, logger=None):
        self.source = source_cfg
        self.target = target_cfg
        self.log = logger or (lambda m: None)

    # ----- helpers -----
    def _get_so_and_lines(self, so_name):
        cfg = self.source
        uid = cfg.auth()
        if not uid:
            raise Exception("Source auth failed")

        ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "sale.order", "search",
            args=[[("name", "=", so_name)]],
            kwargs={"limit": 1},
        )
        if not ids:
            raise Exception(f"Sale Order {so_name} not found in source")

        so = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "sale.order", "read",
            args=[ids],
            kwargs={"fields": ["name", "partner_id", "order_line", "date_order"]},
        )[0]

        line_ids = so.get("order_line") or []
        if not line_ids:
            return so, []

        lines = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "sale.order.line", "read",
            args=[line_ids],
            kwargs={"fields": ["product_id", "product_uom_qty", "price_unit", "name"]},
        )
        return so, lines

    def _get_customer_company_code(self, partner_id):
        cfg = self.source
        uid = cfg.auth()
        if not uid:
            raise Exception("Source auth failed")

        partner = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "res.partner", "read",
            args=[[partner_id]],
            kwargs={"fields": [cfg.partner_code_field, "name"]},
        )[0]
        code = (partner.get(cfg.partner_code_field) or "").strip()
        if not code:
            raise Exception(f"No company code on SO customer {partner.get('name')}")
        self.log(f"Customer '{partner.get('name')}' company code: {code}")
        return code

    def _get_product_data(self, prod_id):
        cfg = self.source
        uid = cfg.auth()
        if not uid:
            raise Exception("Source auth failed")

        prod = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "product.product", "read",
            args=[[prod_id]],
            kwargs={"fields": [
                "name", "default_code", "barcode", "type",
                "standard_price", "lst_price",
                "categ_id", "brand_id", "season_id",
            ]},
        )[0]

        def m2o(val):
            if isinstance(val, list) and len(val) == 2:
                return val[1]
            return None

        return {
            "name": prod.get("name") or prod.get("default_code") or "",
            "default_code": prod.get("default_code"),
            "barcode": prod.get("barcode") or "",
            "type": prod.get("type") or "consu",
            "standard_price": float(prod.get("standard_price") or 0.0),
            "list_price": float(prod.get("lst_price") or 0.0),
            "categ_name": m2o(prod.get("categ_id")),
            "brand_name": m2o(prod.get("brand_id")),
            "season_name": m2o(prod.get("season_id")),
        }

    def _get_or_create_category(self, name):
        if not name:
            return None
        cfg = self.target
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")

        # sirf search, create skip — no error
        ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "product.category", "search",
            args=[[("name", "=", name)]],
            kwargs={"limit": 1},
        )
        if ids:
            return ids[0]

        self.log(f"Category not found in target, skipping create for '{name}'")
        return None

    def _get_or_create_brand(self, name):
        cfg = self.target
        if not cfg.has_brand_model or not name:
            return None
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")
        ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "product.brand", "search",
            args=[[("name", "=", name)]],
            kwargs={"limit": 1},
        )
        if ids:
            return ids[0]
        try:
            return od_x(
                cfg.url, cfg.db, uid, cfg.apikey,
                "product.brand", "create",
                args=[[{"name": name}]],
                kwargs={},
            )
        except Exception as e:
            self.log(f"Brand create skipped for '{name}': {e}")
            return None

    def _get_or_create_season(self, name):
        cfg = self.target
        if not cfg.has_season_model or not name:
            return None
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")
        ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "product.season", "search",
            args=[[("name", "=", name)]],
            kwargs={"limit": 1},
        )
        if ids:
            return ids[0]
        try:
            return od_x(
                cfg.url, cfg.db, uid, cfg.apikey,
                "product.season", "create",
                args=[[{"name": name}]],
                kwargs={},
            )
        except Exception as e:
            self.log(f"Season create skipped for '{name}': {e}")
            return None

    def _ensure_product(self, prod_data):
        cfg = self.target
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")

        default_code = prod_data.get("default_code")
        if not default_code:
            raise Exception("No default_code on source product")

        ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "product.product", "search",
            args=[[("default_code", "=", default_code)]],
            kwargs={"limit": 1},
        )
        if ids:
            self.log(f"Product {default_code} exists in target: {ids[0]}")
            return ids[0]

        categ_id = self._get_or_create_category(prod_data.get("categ_name"))
        brand_id = self._get_or_create_brand(prod_data.get("brand_name"))
        season_id = self._get_or_create_season(prod_data.get("season_name"))

        vals = {
            "name": prod_data.get("name") or default_code,
            "default_code": default_code,
            "barcode": prod_data.get("barcode") or "",
            "type": prod_data.get("type") or "consu",
            "standard_price": prod_data.get("standard_price", 0.0),
            "list_price": prod_data.get("list_price", 0.0),
        }
        if categ_id:
            vals["categ_id"] = categ_id
        if brand_id:
            vals["brand_id"] = brand_id
        if season_id:
            vals["season_id"] = season_id
        if cfg.company_id:
            vals["company_id"] = cfg.company_id

        new_id = od_x(
            cfg.url, cfg.db, uid, cfg.apikey,
            "product.product", "create",
            args=[[vals]],
            kwargs={},
        )
        self.log(f"Created product {default_code} in target with ID {new_id}")
        return new_id

    def _find_supplier(self, company_code):
        cfg = self.target
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")
        ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "res.partner", "search",
            args=[[(
                cfg.partner_code_field, "=", company_code
            ), ("supplier_rank", ">", 0)]],
            kwargs={"limit": 1},
        )
        if not ids:
            raise Exception(f"No supplier found with company code {company_code}")
        self.log(f"Supplier ID {ids[0]} for company code {company_code}")
        return ids[0]

    def _cleanup_empty_po(self, origin):
        cfg = self.target
        uid = cfg.auth()
        if not uid:
            return
        po_ids = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "purchase.order", "search",
            args=[[("origin", "=", origin)]],
            kwargs={},
        )
        if not po_ids:
            return
        pos = od_call_with_retry(
            od_x, cfg.url, cfg.db, uid, cfg.apikey,
            "purchase.order", "read",
            args=[po_ids],
            kwargs={"fields": ["order_line", "state", "name", "origin"]},
        )
        for po in pos:
            if not po.get("order_line") and po.get("state") in ("draft", "sent", "to approve"):
                try:
                    od_x(
                        cfg.url, cfg.db, uid, cfg.apikey,
                        "purchase.order", "unlink",
                        args=[[po["id"]]],
                        kwargs={},
                    )
                    self.log(f"Deleted empty PO {po.get('name')} / ID {po['id']}")
                except Exception as e:
                    self.log(f"Could not delete empty PO {po['id']}: {e}")

    # ----- public API -----
    def create_po_from_so(self, so_name):
        self.log(f"SO {so_name}: start")
        so, lines = self._get_so_and_lines(so_name)
        if not lines:
            self.log("No lines on SO, skip.")
            return None

        cust = so.get("partner_id")
        customer_id = cust[0] if isinstance(cust, list) else cust
        if not customer_id:
            raise Exception("No customer on SO")

        code = self._get_customer_company_code(customer_id)
        supplier_id = self._find_supplier(code)

        cfg = self.target
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")

        po_vals = {
            "partner_id": supplier_id,
            "origin": so["name"],
            "date_order": so.get("date_order") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if cfg.company_id:
            po_vals["company_id"] = cfg.company_id

        po_id = od_x(
            cfg.url, cfg.db, uid, cfg.apikey,
            "purchase.order", "create",
            args=[[po_vals]],
            kwargs={},
        )
        self.log(f"PO header created: {po_id}")

        line_cmds = []
        for idx, line in enumerate(lines, start=1):
            pid = line["product_id"][0] if line.get("product_id") else None
            if not pid:
                self.log(f"Line {idx}: no product, skip")
                continue
            pdata = self._get_product_data(pid)
            target_pid = self._ensure_product(pdata)
            line_cmds.append((0, 0, {
                "product_id": target_pid,
                "name": line.get("name") or pdata.get("name") or "",
                "product_qty": line.get("product_uom_qty") or 0.0,
                "price_unit": line.get("price_unit") or 0.0,
                "date_planned": so.get("date_order") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }))

        if not line_cmds:
            self.log("No valid lines, delete PO")
            od_x(
                cfg.url, cfg.db, uid, cfg.apikey,
                "purchase.order", "unlink",
                args=[[po_id]],
                kwargs={},
            )
            return None

        od_x(
            cfg.url, cfg.db, uid, cfg.apikey,
            "purchase.order", "write",
            args=[[po_id, {"order_line": line_cmds}]],
            kwargs={},
        )
        self.log(f"PO {po_id} created for SO {so_name}")
        return po_id

    def sync_batch(self, so_list, dry_run=False):
        cfg = self.target
        uid = cfg.auth()
        if not uid:
            raise Exception("Target auth failed")

        created, skipped, failed = [], [], []
        for name in so_list:
            name = name.strip()
            if not name:
                continue
            self.log("────────────")
            self.log(f"Processing SO {name}")

            self._cleanup_empty_po(name)

            existing = od_call_with_retry(
                od_x, cfg.url, cfg.db, uid, cfg.apikey,
                "purchase.order", "search",
                args=[[("origin", "=", name)]],
                kwargs={"limit": 1},
            )
            if existing:
                self.log(f"PO already exists: {existing[0]} (skip)")
                skipped.append((name, existing[0]))
                continue

            if dry_run:
                self.log("Dry run: passed checks")
                created.append((name, "DRY-RUN"))
                continue

            try:
                po_id = self.create_po_from_so(name)
                if po_id:
                    created.append((name, po_id))
                else:
                    failed.append((name, "No PO created"))
            except Exception as e:
                self.log(f"ERROR: {e}")
                failed.append((name, str(e)))

        return {"created": created, "skipped": skipped, "failed": failed}

# -----------------------------------------------------------------------------
# SESSION LOG
# -----------------------------------------------------------------------------
if "so_po_logs" not in st.session_state:
    st.session_state["so_po_logs"] = []

def ui_logger(msg: str):
    st.session_state["so_po_logs"].append(msg)

# -----------------------------------------------------------------------------
# MAIN UI
# -----------------------------------------------------------------------------
st.markdown(
    "<div class='section-header'><span class='step-circle'>1</span><h3>Select Companies</h3></div>",
    unsafe_allow_html=True,
)

all_secrets = st.secrets.to_dict() if hasattr(st, "secrets") else {}
source_keys = [k for k in all_secrets.keys() if k.startswith("source_")]
target_keys = [k for k in all_secrets.keys() if k.startswith("target_")]

if not source_keys or not target_keys:
    st.markdown(
        "<div class='warn-banner'>Please define at least one [source_*] and one [target_*] "
        "section in .streamlit/secrets.toml.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

c1, c2 = st.columns(2)
with c1:
    src_name = st.selectbox("Source company (Sales)", source_keys)
with c2:
    tgt_name = st.selectbox("Target company (Purchase)", target_keys)

src_cfg = OdooCfg(src_name, all_secrets[src_name])
tgt_cfg = OdooCfg(tgt_name, all_secrets[tgt_name])

st.markdown(
    f"""
<div class='info-banner' style='animation: fadeInUp 0.4s ease;'>
<b>Source:</b> {src_cfg.name} → {src_cfg.url} (DB: {src_cfg.db})<br>
<b>Target:</b> {tgt_cfg.name} → {tgt_cfg.url} (DB: {tgt_cfg.db})<br>
<small>Partner code field: <code>{src_cfg.partner_code_field}</code> → <code>{tgt_cfg.partner_code_field}</code></small>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='section-header'><span class='step-circle'>2</span><h3>Sale Orders</h3></div>",
    unsafe_allow_html=True,
)

so_text = st.text_area(
    "Sale Order numbers",
    value="S02668",
    height=140,
    help="Comma separated ya ek per line: S02668, S02670, S02671",
)

def parse_so(text: str):
    vals = []
    for line in text.replace(",", "\n").splitlines():
        v = line.strip()
        if v:
            vals.append(v)
    return vals

so_list = parse_so(so_text)
dry_run = st.checkbox("Dry-run only (sirf check, PO create nahi)", value=False)
st.caption(f"Detected {len(so_list)} SO(s) from input.")

st.markdown(
    "<div class='section-header'><span class='step-circle'>3</span><h3>Run Sync</h3></div>",
    unsafe_allow_html=True,
)

colA, colB, colC = st.columns(3)
colA.metric("SO Count", len(so_list))
colB.metric("Source", src_cfg.name)
colC.metric("Target", tgt_cfg.name)

if st.button("Run SO → PO Sync", type="primary"):
    st.session_state["so_po_logs"] = []
    if not so_list:
        st.warning("Please enter at least one Sale Order.")
    else:
        try:
            sync = SOtoPOSync(src_cfg, tgt_cfg, logger=ui_logger)
            with st.spinner("Sync in progress..."):
                result = sync.sync_batch(so_list, dry_run=dry_run)

            st.success("Sync completed.")

            c1, c2, c3 = st.columns(3)
            c1.metric("Created", len(result["created"]))
            c2.metric("Skipped", len(result["skipped"]))
            c3.metric("Failed", len(result["failed"]))

            st.markdown("#### Created")
            if result["created"]:
                df_c = pd.DataFrame(result["created"], columns=["Sale Order", "PO ID / Status"])
                st.dataframe(df_c, use_container_width=True)
            else:
                st.info("No created POs.")

            st.markdown("#### Skipped")
            if result["skipped"]:
                df_s = pd.DataFrame(result["skipped"], columns=["Sale Order", "Existing PO ID"])
                st.dataframe(df_s, use_container_width=True)
            else:
                st.info("No skipped SOs.")

            st.markdown("#### Failed")
            if result["failed"]:
                df_f = pd.DataFrame(result["failed"], columns=["Sale Order", "Error"])
                st.dataframe(df_f, use_container_width=True)
            else:
                st.info("No failures.")

        except Exception as e:
            st.error(f"Sync error: {e}")

st.markdown("#### Logs")
log_text = "\n".join(st.session_state.get("so_po_logs", [])[-300:]) or "No logs yet"
st.text_area("Execution logs", value=log_text, height=260)
