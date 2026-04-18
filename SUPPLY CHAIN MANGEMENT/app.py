import io
import re
import math
import hashlib
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="SWAG Control Center",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG"]
PAGE_SIZE   = 50
PALETTE     = ["#3b82f6","#22c55e","#f97316","#a855f7","#0ea5e9","#f59e0b","#ef4444","#10b981"]

C_SYSTEM        = "System"
C_MODEL         = "Model Code"
C_PRODUCT       = "Product"
C_SALE_PRICE    = "Sale Price"
C_ON_HAND       = "On Hand"
C_BRANCH        = "Branch"
C_REFERENCE     = "Reference"
C_STATE         = "State"
C_FROM          = "From"
C_TO            = "To"
C_QTY           = "Qty"
C_SCHEDULED     = "Scheduled Date"
C_SOLD          = "Sold (30d)"
C_VEL           = "Daily Velocity"
C_DAYS_LEFT     = "Days Left"
C_SUGGEST       = "Suggested Order"
C_PRIORITY      = "Priority"
C_DATE          = "Date"
C_PO            = "PO"
C_SO            = "SO"
C_VENDOR        = "Vendor"
C_CUSTOMER      = "Customer"
C_CATEGORY      = "Category"
C_UNIT_PRICE    = "Unit Price"
C_SUBTOTAL      = "Subtotal"
C_QTY_PURCHASED = "Qty Purchased"
C_CURRENCY      = "Currency"

# New columns added to align with Colab script (purchase & product metadata)
C_BRAND         = "Brand"
C_MODEL_CAT     = "Model Category"
C_STOCK_ON_HAND = "Stock On Hand"      # product.qty_available
C_FREE_QTY      = "Free Qty"           # product.free_qty
C_FORECAST_QTY  = "Forecast Qty"       # product.virtual_available

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False, "user_email": "", "last_run": None,
    "total_df": None, "branch_df": None, "transfers_df": None, "reorder_df": None,
    "sys_stats": {}, "search_exact": False, "low_stock_thresh": 5,
    "show_transfers": True, "show_reorder": True, "reorder_mode": "days_cover",
    "reorder_target_days": 30, "reorder_max_level": 100, "reorder_point": 10,
    "po_analytics_df": None, "salesanalyticsdf": None, "analytics_view": "stock",
    "page_total": 0, "page_branch": 0, "page_transfers": 0,
    "page_reorder": 0, "page_po": 0, "page_sales": 0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
_TOKEN_SECRET = "swag_v29_prod_2025"

def _make_token(email):
    return hashlib.sha256(f"{_TOKEN_SECRET}::{email}".encode()).hexdigest()[:40]

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

def do_logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ODOO HELPERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def _proxy(url, ep):
    return xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/{ep}", allow_none=True)

@st.cache_data(ttl=3600, show_spinner=False)
def _auth(url, db, user, key):
    try:
        uid = _proxy(url, "common").authenticate(db, user, key, {})
        return uid if (uid and isinstance(uid, int) and uid > 0) else None
    except Exception:
        return None

def _x(url, db, uid, key, model, method, domain, kw=None):
    return _proxy(url, "object").execute_kw(db, uid, key, model, method, domain, kw or {})

def _domain(codes, exact):
    if not codes:
        return []
    if exact:
        return [("default_code", "in", codes)]
    clauses = [("default_code", "=ilike", f"{c}%") for c in codes]
    if len(clauses) == 1:
        return [clauses[0]]
    d = []
    for _ in range(len(clauses) - 1):
        d.append("|")
    d.extend(clauses)
    return d

def _get_conn(key):
    cfg     = st.secrets.get(key, {})
    url     = cfg.get("url", "").rstrip("/")
    db      = cfg.get("db", "")
    user    = cfg.get("user", "")
    api_key = cfg.get("api_key", "")
    if not all([url, db, user, api_key]):
        return None, None, None, None, key, f"[{key}] Missing config."
    uid = _auth(url, db, user, api_key)
    if not uid:
        return url, db, None, api_key, key, f"[{key}] Auth failed."
    return url, db, uid, api_key, cfg.get("name", key), None

def _to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)

# ─────────────────────────────────────────────────────────────────────────────
# PAGINATION HELPER — fetch all records beyond a single search_read limit
# ─────────────────────────────────────────────────────────────────────────────
def _search_read_all(url, db, uid, ak, model, domain, fields, batch=2000):
    """
    Paginate through search_read in batches of `batch` to avoid truncation.
    Returns a flat list of all records matching the domain.
    """
    records = []
    offset  = 0
    while True:
        batch_result = _x(url, db, uid, ak, model, "search_read",
                          [domain],
                          {"fields": fields, "limit": batch, "offset": offset})
        if not batch_result:
            break
        records.extend(batch_result)
        if len(batch_result) < batch:
            break
        offset += batch
    return records

# -----------------------------------------------------------------------------
# Helper to safely get a field value that may be a many2one tuple or a scalar
# -----------------------------------------------------------------------------
def _safe_val(val):
    if isinstance(val, (list, tuple)) and len(val) > 1:
        return val[1]
    return val

# -----------------------------------------------------------------------------
# Helper to extract brand from product (supports multiple possible field names)
# -----------------------------------------------------------------------------
def _get_brand(product):
    for f in ["brand_id", "product_brand_id", "x_brand"]:
        val = product.get(f)
        if val:
            return _safe_val(val)
    return ""

# -----------------------------------------------------------------------------
# Helper to extract model category (supports multiple possible field names)
# -----------------------------------------------------------------------------
def _get_model_category(product):
    for f in ["x_model_category", "x_studio_model_category"]:
        val = product.get(f)
        if val:
            return _safe_val(val)
    return ""

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING — STOCK (aligned with Odoo inventory valuation)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_stock_one(key, codes_tuple, exact, low_thresh, show_transfers, show_reorder,
                     reorder_mode, reorder_target_days, reorder_max_level, reorder_point):
    url, db, uid, ak, name, err = _get_conn(key)
    if err:
        return [], [], [], [], {"system": name, "level": "error", "msg": err}
    codes = list(codes_tuple)
    try:
        prod_domain = _domain(codes, exact) if codes else []

        # Paginate templates
        templates = _search_read_all(url, db, uid, ak, "product.template",
                                     prod_domain if prod_domain else [],
                                     ["id", "name", "default_code", "list_price", "categ_id"])
        if not templates:
            return [], [], [], [], {"system": name, "level": "ok", "msg": "No products found."}

        tmpl_map  = {t["id"]: t for t in templates}
        tmpl_ids  = list(tmpl_map.keys())

        # Fetch all variants for these templates
        variants  = _search_read_all(url, db, uid, ak, "product.product",
                                     [("product_tmpl_id", "in", tmpl_ids)],
                                     ["id", "product_tmpl_id"])
        var_to_tmpl = {}
        for v in variants:
            raw = v.get("product_tmpl_id")
            var_to_tmpl[v["id"]] = raw[0] if isinstance(raw, list) else raw
        var_ids = list(var_to_tmpl.keys())

        tmpl_qty, branch_rows = {}, []
        if var_ids:
            # Quant domain: internal locations only -> matches Odoo "On Hand" report
            quants = _search_read_all(url, db, uid, ak, "stock.quant",
                                      [("product_id", "in", var_ids),
                                       ("location_id.usage", "=", "internal")],
                                      ["product_id", "location_id", "quantity"])
            for q in quants:
                vid = (q["product_id"][0] if isinstance(q.get("product_id"), list) else q.get("product_id"))
                tid = var_to_tmpl.get(vid)
                if tid is None:
                    continue
                qty = float(q.get("quantity") or 0)
                tmpl_qty[tid] = tmpl_qty.get(tid, 0) + qty
                loc_raw  = q.get("location_id")
                loc_name = loc_raw[1] if isinstance(loc_raw, list) and len(loc_raw) > 1 else str(loc_raw or "")
                mc = (tmpl_map.get(tid, {}).get("default_code") or "").strip()
                if mc:
                    branch_rows.append({C_SYSTEM: name, C_BRANCH: loc_name, C_MODEL: mc, C_ON_HAND: qty})

        # Velocity: sales in last 30 days (state sale/done, date_order based)
        vel_map = {}
        if var_ids:
            try:
                date_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                so_lines = _search_read_all(url, db, uid, ak, "sale.order.line",
                                            [("product_id", "in", var_ids),
                                             ("order_id.date_order", ">=", f"{date_30} 00:00:00"),
                                             ("order_id.state", "in", ["sale", "done"])],
                                            ["product_id", "product_uom_qty"])
                for sl in so_lines:
                    vid = (sl["product_id"][0] if isinstance(sl.get("product_id"), list) else sl.get("product_id"))
                    tid = var_to_tmpl.get(vid)
                    if tid:
                        vel_map[tid] = vel_map.get(tid, 0) + float(sl.get("product_uom_qty") or 0)
            except Exception as e:
                return [], [], [], [], {"system": name, "level": "error",
                                        "msg": f"Velocity fetch error: {type(e).__name__}: {e}"}

        total_rows, reorder_rows, transfer_rows = [], [], []

        for tid, tmpl in tmpl_map.items():
            mc        = (tmpl.get("default_code") or "").strip()
            categ_raw = tmpl.get("categ_id")
            category  = categ_raw[1] if isinstance(categ_raw, list) and len(categ_raw) > 1 else ""
            on_hand   = tmpl_qty.get(tid, 0)
            sale_price= float(tmpl.get("list_price") or 0)
            sold_30   = vel_map.get(tid, 0)
            daily_vel = sold_30 / 30.0
            total_rows.append({
                C_SYSTEM:     name,
                C_MODEL:      mc,
                C_PRODUCT:    tmpl.get("name", ""),
                C_SALE_PRICE: sale_price,
                C_ON_HAND:    on_hand,
                C_SOLD:       sold_30,
                C_VEL:        round(daily_vel, 3),
                C_CATEGORY:   category,
            })

        if show_reorder:
            for tid, tmpl in tmpl_map.items():
                mc        = (tmpl.get("default_code") or "").strip()
                on_hand   = tmpl_qty.get(tid, 0)
                sold_30   = vel_map.get(tid, 0)
                daily_vel = sold_30 / 30.0
                if reorder_mode == "days_cover":
                    days_left = (on_hand / daily_vel) if daily_vel > 0 else 999
                    suggest   = max(0, round(daily_vel * reorder_target_days - on_hand))
                    priority  = "🔴 Critical" if days_left < 7 else ("🟡 Low" if days_left < 14 else "🟢 OK")
                else:
                    days_left = (on_hand / daily_vel) if daily_vel > 0 else 999
                    suggest   = max(0, reorder_max_level - on_hand) if on_hand <= reorder_point else 0
                    priority  = "🔴 Critical" if on_hand <= reorder_point else "🟢 OK"
                if suggest > 0 or on_hand <= low_thresh:
                    reorder_rows.append({
                        C_SYSTEM:   name,
                        C_MODEL:    mc,
                        C_PRODUCT:  tmpl.get("name", ""),
                        C_ON_HAND:  on_hand,
                        C_SOLD:     sold_30,
                        C_VEL:      round(daily_vel, 3),
                        C_DAYS_LEFT:round(days_left, 1) if days_left < 999 else "∞",
                        C_SUGGEST:  suggest,
                        C_PRIORITY: priority,
                    })

        if show_transfers and var_ids:
            try:
                moves = _search_read_all(url, db, uid, ak, "stock.move",
                                         [("product_id", "in", var_ids),
                                          ("state", "not in", ["cancel", "done"]),
                                          ("picking_id.picking_type_code", "=", "internal")],
                                         ["product_id", "product_uom_qty", "state",
                                          "location_id", "location_dest_id", "reference", "date"])
                for mv in moves:
                    vid      = (mv["product_id"][0] if isinstance(mv.get("product_id"), list) else mv.get("product_id"))
                    tid      = var_to_tmpl.get(vid)
                    mc       = (tmpl_map.get(tid, {}).get("default_code") or "").strip() if tid else ""
                    loc_from = mv.get("location_id")
                    loc_to   = mv.get("location_dest_id")
                    transfer_rows.append({
                        C_SYSTEM:    name,
                        C_MODEL:     mc,
                        C_PRODUCT:   tmpl_map.get(tid, {}).get("name", "") if tid else "",
                        C_QTY:       float(mv.get("product_uom_qty") or 0),
                        C_STATE:     mv.get("state", ""),
                        C_FROM:      loc_from[1] if isinstance(loc_from, list) and len(loc_from) > 1 else "",
                        C_TO:        loc_to[1]   if isinstance(loc_to,   list) and len(loc_to)   > 1 else "",
                        C_REFERENCE: mv.get("reference", ""),
                        C_SCHEDULED: str(mv.get("date", ""))[:10],
                    })
            except Exception:
                pass

        return total_rows, branch_rows, transfer_rows, reorder_rows, \
               {"system": name, "level": "ok", "msg": f"Loaded {len(total_rows)} products."}
    except Exception as e:
        return [], [], [], [], {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}


def fetch_all_data(codes, exact, low_stock_thresh, show_transfers, show_reorder,
                   reorder_mode, reorder_target_days, reorder_max_level, reorder_point):
    codes_tuple = tuple(sorted(set(codes))) if codes else ()
    all_total, all_branch, all_transfers, all_reorder, sys_stats = [], [], [], [], {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_stock_one, k, codes_tuple, exact, low_stock_thresh,
                          show_transfers, show_reorder, reorder_mode,
                          reorder_target_days, reorder_max_level, reorder_point): k for k in SYSTEM_KEYS}
        for f in as_completed(futs):
            k = futs[f]
            tr, br, tf, ro, stat = f.result()
            all_total.extend(tr); all_branch.extend(br)
            all_transfers.extend(tf); all_reorder.extend(ro)
            sys_stats[k] = stat

    def _df(rows, cols):
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)

    total_df = _df(all_total, [C_SYSTEM, C_MODEL, C_PRODUCT, C_SALE_PRICE, C_ON_HAND, C_SOLD, C_VEL, C_CATEGORY])
    for c in [C_SALE_PRICE, C_ON_HAND, C_SOLD, C_VEL]:
        if c in total_df.columns: total_df[c] = _to_num(total_df[c])

    branch_df = _df(all_branch, [C_SYSTEM, C_BRANCH, C_MODEL, C_ON_HAND])
    if C_ON_HAND in branch_df.columns: branch_df[C_ON_HAND] = _to_num(branch_df[C_ON_HAND])

    transfers_df = _df(all_transfers, [C_SYSTEM, C_MODEL, C_PRODUCT, C_QTY, C_STATE, C_FROM, C_TO, C_REFERENCE, C_SCHEDULED])
    if C_QTY in transfers_df.columns: transfers_df[C_QTY] = _to_num(transfers_df[C_QTY])

    reorder_df = _df(all_reorder, [C_SYSTEM, C_MODEL, C_PRODUCT, C_ON_HAND, C_SOLD, C_VEL, C_DAYS_LEFT, C_SUGGEST, C_PRIORITY])
    return total_df, branch_df, transfers_df, reorder_df, sys_stats


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING — PURCHASE (ALIGNED WITH COLAB SCRIPT)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_history_for_system(system_key, model_codes, date_from, date_to):
    """
    Fetches purchase order lines with product metadata including brand, model category,
    and stock quantities (qty_available, free_qty, virtual_available).
    Aligned with Colab script:
        - state = 'purchase' (confirmed POs only)
        - date_order (Order Date) instead of date_approve
        - product fields: default_code, name, categ_id, brand fields, model category fields,
          qty_available, free_qty, virtual_available
    """
    url, db, uid, ak, name, err = _get_conn(system_key)
    _empty = pd.DataFrame(columns=[C_SYSTEM, C_DATE, C_PO, C_VENDOR, C_CURRENCY,
                                    C_PRODUCT, C_MODEL, C_CATEGORY, C_QTY_PURCHASED,
                                    C_UNIT_PRICE, C_SUBTOTAL, C_STATE,
                                    C_BRAND, C_MODEL_CAT, C_STOCK_ON_HAND, C_FREE_QTY, C_FORECAST_QTY])
    if err:
        return _empty
    try:
        # CHANGED: state = 'purchase' only (matches Colab)
        # CHANGED: use date_order (Order Date) to align with Odoo Purchase Analysis
        po_domain = [
            ("date_order", ">=", f"{date_from} 00:00:00"),
            ("date_order", "<=", f"{date_to} 23:59:59"),
            ("state", "=", "purchase"),
        ]
        pos_list = _search_read_all(url, db, uid, ak, "purchase.order",
                                    po_domain,
                                    ["id", "name", "partner_id", "date_order", "state", "currency_id"])
        if not pos_list:
            return _empty
        po_ids  = [p["id"] for p in pos_list]
        po_map  = {p["id"]: p for p in pos_list}

        line_domain = [("order_id", "in", po_ids)]
        if model_codes:
            line_domain.append(("product_id.default_code", "in", list(model_codes)))

        lines = _search_read_all(url, db, uid, ak, "purchase.order.line",
                                 line_domain,
                                 ["order_id", "product_id", "product_qty",
                                  "price_unit", "price_subtotal"])

        if not lines:
            return _empty

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})

        # CHANGED: fetch additional product fields required by Colab
        product_fields = [
            "id", "default_code", "name", "categ_id",
            "brand_id", "product_brand_id", "x_brand",
            "x_model_category", "x_studio_model_category",
            "qty_available", "free_qty", "virtual_available"
        ]
        products = _search_read_all(url, db, uid, ak, "product.product",
                                    [("id", "in", prod_ids)],
                                    product_fields)
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid  = (line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id"))
            po   = po_map.get(oid, {})
            pid  = (line["product_id"][0] if isinstance(line.get("product_id"), list) else line.get("product_id"))
            prod = prod_map.get(pid, {})

            mc = (prod.get("default_code") or "").strip()
            categ_raw    = prod.get("categ_id")
            partner_raw  = po.get("partner_id")
            currency_raw = po.get("currency_id")

            # Extract brand and model category using helpers
            brand = _get_brand(prod)
            model_cat = _get_model_category(prod)

            # Stock quantities (as of now, may be computed by Odoo)
            qty_available = float(prod.get("qty_available") or 0)
            free_qty      = float(prod.get("free_qty") or 0)
            virtual_avail = float(prod.get("virtual_available") or 0)

            rows.append({
                C_SYSTEM:   name,
                C_DATE:     str(po.get("date_order", ""))[:10],          # date_order
                C_PO:       po.get("name", ""),
                C_VENDOR:   partner_raw[1] if isinstance(partner_raw, list) and len(partner_raw) > 1 else "",
                C_CURRENCY: currency_raw[1] if isinstance(currency_raw, list) and len(currency_raw) > 1 else "SAR",
                C_PRODUCT:  prod.get("name", ""),
                C_MODEL:    mc,
                C_CATEGORY: categ_raw[1] if isinstance(categ_raw, list) and len(categ_raw) > 1 else "",
                C_QTY_PURCHASED: _to_num(pd.Series([line.get("product_qty", 0)]))[0],
                C_UNIT_PRICE:    _to_num(pd.Series([line.get("price_unit", 0)]))[0],
                C_SUBTOTAL:      _to_num(pd.Series([line.get("price_subtotal", 0)]))[0],
                C_STATE:    po.get("state", ""),
                # New columns
                C_BRAND:         brand,
                C_MODEL_CAT:     model_cat,
                C_STOCK_ON_HAND: qty_available,
                C_FREE_QTY:      free_qty,
                C_FORECAST_QTY:  virtual_avail,
            })

        if not rows:
            return _empty

        df = pd.DataFrame(rows)
        df[C_DATE] = pd.to_datetime(df[C_DATE], errors="coerce")
        numeric_cols = [C_QTY_PURCHASED, C_UNIT_PRICE, C_SUBTOTAL, C_STOCK_ON_HAND, C_FREE_QTY, C_FORECAST_QTY]
        for c in numeric_cols:
            if c in df.columns:
                df[c] = _to_num(df[c])
        return df.sort_values(C_DATE, ascending=False).reset_index(drop=True)

    except Exception as e:
        st.warning(f"[{system_key}] Purchase fetch error: {type(e).__name__}: {e}")
        return _empty


def fetch_all_purchase_history(model_codes, date_from, date_to):
    codes_tuple = tuple(sorted(set(model_codes))) if model_codes else ()
    results = [fetch_purchase_history_for_system(k, codes_tuple, date_from, date_to) for k in SYSTEM_KEYS]
    results = [r for r in results if r is not None and not r.empty]
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined[C_DATE] = pd.to_datetime(combined[C_DATE], errors="coerce")
    return combined.sort_values(C_DATE, ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING — SALES (ALIGNED WITH ODOO SALES ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sales_history_for_system(system_key, model_codes, date_from, date_to):
    url, db, uid, ak, name, err = _get_conn(system_key)
    _empty = pd.DataFrame(columns=[C_SYSTEM, C_DATE, C_SO, C_CUSTOMER, C_PRODUCT,
                                    C_MODEL, C_CATEGORY, C_QTY, C_UNIT_PRICE, C_SUBTOTAL, C_STATE])
    if err:
        return _empty
    try:
        # Odoo Sales Analysis: state in ('sale','done') = confirmed + locked
        so_domain = [
            ("date_order", ">=", f"{date_from} 00:00:00"),
            ("date_order", "<=", f"{date_to} 23:59:59"),
            ("state", "in", ["sale", "done"]),
        ]
        orders = _search_read_all(url, db, uid, ak, "sale.order",
                                  so_domain,
                                  ["id", "name", "date_order", "partner_id", "state", "order_line"])
        if not orders:
            return _empty

        order_map = {o["id"]: o for o in orders}
        order_ids = list(order_map.keys())

        line_domain = [("order_id", "in", order_ids)]
        if model_codes:
            line_domain.append(("product_id.default_code", "in", list(model_codes)))

        lines = _search_read_all(url, db, uid, ak, "sale.order.line",
                                 line_domain,
                                 ["order_id", "product_id", "product_uom_qty",
                                  "price_unit", "price_subtotal"])
        if not lines:
            return _empty

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _search_read_all(url, db, uid, ak, "product.product",
                                    [("id", "in", prod_ids)],
                                    ["id", "default_code", "name", "categ_id"])
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid     = (line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id"))
            order   = order_map.get(oid, {})
            pid     = (line["product_id"][0] if isinstance(line.get("product_id"), list) else line.get("product_id"))
            prod    = prod_map.get(pid, {})
            categ_raw   = prod.get("categ_id")
            partner_raw = order.get("partner_id")

            rows.append({
                C_SYSTEM:   name,
                C_DATE:     str(order.get("date_order", ""))[:10],
                C_SO:       order.get("name", ""),
                C_CUSTOMER: partner_raw[1] if isinstance(partner_raw, list) and len(partner_raw) > 1 else "",
                C_PRODUCT:  prod.get("name", ""),
                C_MODEL:    (prod.get("default_code") or "").strip(),
                C_CATEGORY: categ_raw[1] if isinstance(categ_raw, list) and len(categ_raw) > 1 else "",
                C_QTY:        _to_num(pd.Series([line.get("product_uom_qty", 0)]))[0],
                C_UNIT_PRICE: _to_num(pd.Series([line.get("price_unit", 0)]))[0],
                C_SUBTOTAL:   _to_num(pd.Series([line.get("price_subtotal", 0)]))[0],
                C_STATE:    order.get("state", ""),
            })

        if not rows:
            return _empty

        df = pd.DataFrame(rows)
        df[C_DATE] = pd.to_datetime(df[C_DATE], errors="coerce")
        for c in [C_QTY, C_UNIT_PRICE, C_SUBTOTAL]:
            df[c] = _to_num(df[c])
        return df.sort_values(C_DATE, ascending=False).reset_index(drop=True)

    except Exception as e:
        st.warning(f"[{system_key}] Sales fetch error: {type(e).__name__}: {e}")
        return _empty


def fetch_all_sales_history(model_codes, date_from, date_to):
    codes_tuple = tuple(sorted(set(model_codes))) if model_codes else ()
    results = [fetch_sales_history_for_system(k, codes_tuple, date_from, date_to) for k in SYSTEM_KEYS]
    results = [r for r in results if r is not None and not r.empty]
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined[C_DATE] = pd.to_datetime(combined[C_DATE], errors="coerce")
    return combined.sort_values(C_DATE, ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        (df if df is not None and not df.empty else pd.DataFrame({"Message": ["No data"]})).to_excel(w, index=False)
    out.seek(0)
    return out.getvalue()

def dl_name(prefix, ext):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# PAGINATION
# ─────────────────────────────────────────────────────────────────────────────
def paginate_df(df, page_key, page_size=PAGE_SIZE):
    if df is None or df.empty:
        return df, 1, 0
    total       = len(df)
    total_pages = max(1, math.ceil(total / page_size))
    current     = min(st.session_state.get(page_key, 0), total_pages - 1)
    st.session_state[page_key] = current
    start, end  = current * page_size, min(current * page_size + page_size, total)
    st.markdown(
        f"<div style='text-align:center;margin:6px 0;font-size:0.78rem;color:#6b7280;'>"
        f"Showing {start+1}–{end} of {total} &nbsp;|&nbsp;"
        f"<span style='background:#f0f9ff;border:1px solid #bae6fd;padding:2px 10px;"
        f"border-radius:12px;color:#0369a1;font-weight:600;'>Page {current+1}/{total_pages}</span></div>",
        unsafe_allow_html=True)
    c1, c2, _, c3, c4 = st.columns([1, 1, 3, 1, 1])
    if c1.button("⏮", key=f"{page_key}_first", use_container_width=True):
        st.session_state[page_key] = 0; st.rerun()
    if c2.button("◀", key=f"{page_key}_prev", use_container_width=True):
        st.session_state[page_key] = max(0, current - 1); st.rerun()
    if c3.button("▶", key=f"{page_key}_next", use_container_width=True):
        st.session_state[page_key] = min(total_pages - 1, current + 1); st.rerun()
    if c4.button("⏭", key=f"{page_key}_last", use_container_width=True):
        st.session_state[page_key] = total_pages - 1; st.rerun()
    return df.iloc[start:end].copy(), total_pages, current

# ─────────────────────────────────────────────────────────────────────────────
# CSS  (matches HTML dashboard design)
# ─────────────────────────────────────────────────────────────────────────────
def _css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box}

.stApp{
  background:
    radial-gradient(circle at 0% 0%,rgba(59,130,246,.18) 0,transparent 45%),
    radial-gradient(circle at 100% 100%,rgba(45,212,191,.18) 0,transparent 45%),
    #f3f5fb !important;
  color:#111827;font-family:'Inter',system-ui,sans-serif !important}

section[data-testid="stSidebar"]{background:#fff !important;border-right:1px solid #e5e7eb !important}
section[data-testid="stSidebar"] *{color:#374151 !important;font-family:'Inter',sans-serif !important}

.stTextInput input,.stNumberInput input,.stTextArea textarea{
  background:#f9fafb !important;border:1px solid #e5e7eb !important;
  border-radius:10px !important;color:#111827 !important;font-size:.875rem !important}
label{color:#6b7280 !important;font-size:.78rem !important;font-weight:500 !important}

.stButton>button{border-radius:10px !important;border:1px solid #e5e7eb !important;
  background:#fff !important;color:#374151 !important;font-weight:500 !important;
  font-size:.82rem !important;transition:all .16s ease !important}
.stButton>button:hover{background:#f9fafb !important;border-color:#0ea5e9 !important;color:#0ea5e9 !important;transform:translateY(-1px)}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#0ea5e9,#2563eb) !important;
  color:#fff !important;border:none !important;box-shadow:0 10px 24px rgba(37,99,235,.45) !important}
.stButton>button[kind="primary"]:hover{box-shadow:0 14px 30px rgba(37,99,235,.65) !important;transform:translateY(-1px)}
.stDownloadButton>button{background:#f9fafb !important;border:1px solid #e5e7eb !important;
  color:#374151 !important;border-radius:10px !important;font-size:.78rem !important}
.stDownloadButton>button:hover{background:linear-gradient(135deg,#0ea5e9,#2563eb) !important;
  color:#fff !important;border-color:transparent !important}

.stTabs [data-baseweb="tab-list"]{background:transparent;border-bottom:1px solid #e5e7eb;gap:2px}
.stTabs [data-baseweb="tab"]{background:#f9fafb !important;color:#6b7280 !important;
  border:1px solid #e5e7eb !important;border-radius:8px 8px 0 0 !important;
  padding:.5rem 1.1rem !important;font-weight:500 !important;font-size:.82rem !important}
.stTabs [aria-selected="true"]{background:#fff !important;color:#0ea5e9 !important;
  border-bottom:3px solid #0ea5e9 !important;font-weight:600 !important}

[data-testid="stMetric"]{background:#fff;border:1px solid #e5e7eb;border-radius:16px;
  padding:1rem 1.2rem;box-shadow:0 4px 16px rgba(15,23,42,.06)}
[data-testid="stMetricLabel"]{color:#6b7280 !important;font-size:.72rem !important;text-transform:uppercase;letter-spacing:.05em}
[data-testid="stMetricValue"]{font-size:1.4rem !important;font-weight:700 !important;color:#111827 !important}

::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:#f9fafb}
::-webkit-scrollbar-thumb{background:#d1d5db;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#0ea5e9}

/* KPI */
.kpi-row{display:grid;gap:.75rem;margin:.8rem 0}
.kpi-card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:.8rem .9rem;
  box-shadow:0 14px 40px rgba(15,23,42,.12);transition:all .18s ease}
.kpi-card:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(15,23,42,.10)}
.kpi-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:#9ca3af}
.kpi-value{margin-top:.35rem;font-size:1.15rem;font-weight:700;color:#0f172a}
.kpi-meta{margin-top:.12rem;font-size:.72rem;color:#6b7280}

/* HERO */
.hero-banner{background:#e8f3ff;border:1px solid #dbeafe;border-radius:18px;
  padding:1.1rem 1.3rem;margin-bottom:.8rem;box-shadow:0 14px 40px rgba(15,23,42,.12);
  display:flex;justify-content:space-between;gap:1rem;position:relative;overflow:hidden}
.hero-heading{font-size:1.1rem;font-weight:700;color:#0f172a}
.hero-sub{margin-top:.25rem;font-size:.8rem;color:#6b7280}
.hero-tags{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.6rem}
.hero-tag{font-size:.68rem;padding:.22rem .55rem;border-radius:999px;
  border:1px solid #dbeafe;background:#eff6ff;color:#1d4ed8}
.hero-status{display:inline-flex;align-items:center;gap:.35rem;padding:.3rem .6rem;
  border-radius:999px;background:#ecfdf3;border:1px solid #bbf7d0;font-size:.7rem;color:#166534;font-weight:600}
.hero-dot{width:8px;height:8px;border-radius:999px;background:#22c55e;display:inline-block}
.hero-center-title{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  pointer-events:none;font-size:1.5rem;letter-spacing:.30em;text-transform:uppercase;
  color:rgba(15,23,42,.55);font-weight:900;text-shadow:0 0 22px rgba(15,23,42,.35);
  white-space:nowrap;animation:pulseTitle 2.8s ease-in-out infinite}
@keyframes pulseTitle{
  0%,100%{transform:translate(-50%,-50%) scale(1);opacity:.7}
  50%{transform:translate(-50%,-50%) scale(1.06);opacity:1}}

/* PANEL */
.panel{background:#fff;border:1px solid #e5e7eb;border-radius:16px;
  padding:.85rem 1rem;box-shadow:0 14px 40px rgba(15,23,42,.12);margin:.5rem 0}
.panel-title{font-size:.85rem;font-weight:600;color:#0f172a}
.panel-sub{font-size:.72rem;color:#6b7280;margin-top:.1rem;margin-bottom:.4rem}

/* TABLE */
.table-wrap{max-height:380px;overflow:auto;border-radius:12px;
  border:1px solid #e5e7eb;margin:.5rem 0;box-shadow:0 2px 8px rgba(15,23,42,.04)}
table{width:100%;border-collapse:collapse;font-size:.75rem;background:#fff}
th{background:#f9fafb;text-align:left;font-size:.7rem;letter-spacing:.08em;
  text-transform:uppercase;color:#6b7280;padding:.55rem .7rem;
  border-bottom:1px solid #e5e7eb;font-weight:600;position:sticky;top:0;z-index:1}
td{padding:.48rem .7rem;border-bottom:1px solid #f3f4f6;color:#374151;font-size:.78rem}
tr.row-even td{background:#f9fafb}
tr.row-odd  td{background:#fff}
tr.row-zero td{background:#fee2e2 !important;color:#7f1d1d}
tr:hover    td{background:#eff6ff !important}

/* PILLS */
.pill-danger {font-size:.7rem;padding:.16rem .5rem;border-radius:999px;border:1px solid rgba(220,38,38,.8);background:#fee2e2;color:#b91c1c;font-weight:500}
.pill-warning{font-size:.7rem;padding:.16rem .5rem;border-radius:999px;border:1px solid rgba(245,158,11,.8);background:#fef3c7;color:#92400e;font-weight:500}
.pill-ok     {font-size:.7rem;padding:.16rem .5rem;border-radius:999px;border:1px solid rgba(34,197,94,.8);background:#dcfce7;color:#166534;font-weight:500}
.pill-soft   {font-size:.7rem;padding:.16rem .5rem;border-radius:999px;border:1px solid #e5e7eb;background:#f9fafb;color:#6b7280}
.pill-currency{font-size:.7rem;padding:.16rem .5rem;border-radius:999px;border:1px solid #bae6fd;background:#e0f2fe;color:#0369a1;font-weight:600}

/* MINI CARDS */
.mini-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem;margin-top:.35rem}
.mini-card{border-radius:12px;background:#f9fafb;border:1px solid #e5e7eb;padding:.6rem .65rem}
.mini-label{color:#9ca3af;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em}
.mini-value{margin-top:.2rem;font-size:.9rem;font-weight:600;color:#0f172a}
.mini-meta {margin-top:.15rem;font-size:.68rem;color:#6b7280}

/* MISC */
.empty-state{text-align:center;padding:2rem 1rem;color:#9ca3af;font-size:.85rem;
  background:#f9fafb;border-radius:12px;border:1px dashed #e5e7eb}
.swag-divider{border:none;border-top:1px solid #e5e7eb;margin:1rem 0}
.sys-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;
  border-radius:20px;font-size:.7rem;font-weight:600;border:1px solid transparent;margin:2px}
.sys-badge-ok {background:#ecfdf3;border-color:#bbf7d0;color:#166534}
.sys-badge-err{background:#fee2e2;border-color:#fecaca;color:#b91c1c}
.sys-badge-off{background:#f9fafb;border-color:#e5e7eb;color:#9ca3af}
footer{visibility:hidden}#MainMenu{visibility:hidden}.stDeployButton{display:none}
</style>"""

# ─────────────────────────────────────────────────────────────────────────────
# HTML COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def render_kpis(cards):
    cols = min(len(cards), 4)
    html = f"<div class='kpi-row' style='grid-template-columns:repeat({cols},1fr);'>"
    for label, value, meta in cards:
        html += (f"<div class='kpi-card'>"
                 f"<div class='kpi-label'>{label}</div>"
                 f"<div class='kpi-value'>{value}</div>"
                 f"<div class='kpi-meta'>{meta}</div></div>")
    st.markdown(html + "</div>", unsafe_allow_html=True)


def mini_grid(cards):
    html = "<div class='mini-grid'>"
    for label, value, meta in cards:
        html += (f"<div class='mini-card'>"
                 f"<div class='mini-label'>{label}</div>"
                 f"<div class='mini-value'>{value}</div>"
                 f"<div class='mini-meta'>{meta}</div></div>")
    st.markdown(html + "</div>", unsafe_allow_html=True)


def _days_pill(val):
    try:
        if str(val) == "∞" or val is None:
            return "<span class='pill-soft'>∞ days</span>"
        d = float(val)
        if d < 7:  return f"<span class='pill-danger'>🔴 {d:.0f}d left</span>"
        if d < 14: return f"<span class='pill-warning'>🟡 {d:.0f}d left</span>"
        return f"<span class='pill-ok'>🟢 {d:.0f}d left</span>"
    except Exception:
        return f"<span class='pill-soft'>{val}</span>"


def _priority_pill(val):
    v = str(val)
    if "Critical" in v: return f"<span class='pill-danger'>{v}</span>"
    if "Low"      in v: return f"<span class='pill-warning'>{v}</span>"
    return f"<span class='pill-ok'>{v}</span>"


def render_table(df):
    if df is None or df.empty:
        st.markdown("<div class='empty-state'>ℹ️ No data to display.</div>", unsafe_allow_html=True)
        return
    header = "".join(f"<th>{c}</th>" for c in df.columns)
    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        try:    oh = float(row.get(C_ON_HAND, 1))
        except: oh = 1
        cls = "row-zero" if oh == 0 else ("row-even" if i % 2 == 0 else "row-odd")
        cells = ""
        for col, val in zip(df.columns, row.values):
            if   col == C_DAYS_LEFT: content = _days_pill(val)
            elif col == C_PRIORITY:  content = _priority_pill(val)
            elif col == C_CURRENCY:  content = f"<span class='pill-currency'>{val or 'SAR'}</span>"
            elif col == C_ON_HAND:
                try:
                    v = float(val)
                    content = f"<strong style='color:{'#dc2626' if v==0 else '#111827'};'>{int(v)}</strong>"
                except: content = str(val) if val is not None else ""
            else: content = str(val) if val is not None else ""
            cells += f"<td>{content}</td>"
        rows_html += f"<tr class='{cls}'>{cells}</tr>"
    st.markdown(
        f"<div class='table-wrap'><table>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table></div>",
        unsafe_allow_html=True)


def display_df(df, table_key=None):
    if df is None or df.empty:
        render_table(df)
        return
    key = table_key or f"tbl_{abs(hash(str(df.columns.tolist()))) % 10**8}"
    page_df, _, _ = paginate_df(df, key)
    render_table(page_df)

# ─────────────────────────────────────────────────────────────────────────────
# CHART THEME
# ─────────────────────────────────────────────────────────────────────────────
def _light(fig):
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0)", plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#374151", family="Inter, sans-serif", size=11),
        margin=dict(l=20, r=20, t=36, b=20),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e5e7eb", borderwidth=1),
        title_font=dict(size=13, color="#111827"))
    fig.update_xaxes(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(size=10, color="#6b7280"))
    fig.update_yaxes(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(size=10, color="#9ca3af"))
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown(_css(), unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#eff6ff,#ecfdf5);border:1px solid #bfdbfe;
            border-radius:20px;padding:2.5rem;min-height:460px;
            display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:3rem;margin-bottom:1rem;">🏷️</div>
          <div style="font-size:2rem;font-weight:800;
              background:linear-gradient(135deg,#0ea5e9,#22c55e);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;
              margin-bottom:.4rem;">SWAG Control</div>
          <div style="color:#6b7280;font-size:.9rem;margin-bottom:1.5rem;">Inventory Intelligence Dashboard</div>
          <div style="display:flex;flex-wrap:wrap;gap:.35rem;">
            <span class="hero-tag">SWAG ERP</span>
            <span class="hero-tag">Real-time</span>
            <span class="hero-tag">Purchase Analytics</span>
            <span class="hero-tag">Sales Analytics</span>
          </div>
          <div style="margin-top:1.5rem;border-top:1px solid #e5e7eb;padding-top:1rem;">
            <div style="font-size:.7rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">Connected System</div>
            <span class="sys-badge sys-badge-ok">● SWAG</span>
          </div>
        </div>""", unsafe_allow_html=True)
    with right:
        st.markdown("""
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:20px;
            padding:2.5rem;box-shadow:0 8px 30px rgba(15,23,42,.08);">
          <div style="font-size:1.5rem;font-weight:700;color:#0f172a;margin-bottom:.3rem;">Sign In</div>
          <div style="color:#6b7280;font-size:.85rem;margin-bottom:1.5rem;">Access your SWAG control center</div>
        </div>""", unsafe_allow_html=True)
        if st.session_state.get("_login_err"):
            st.error(st.session_state._login_err)
        with st.form("login_form"):
            email    = st.text_input("Email", placeholder="user@company.com")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("🚀 Sign In", type="primary", use_container_width=True):
                if not email.strip() or not password:
                    st.session_state._login_err = "Please enter email and password."
                    st.rerun()
                with st.spinner("Authenticating…"):
                    ok, err_msg = _attempt_login(email.strip(), password)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.user_email    = email.strip()
                    st.session_state._login_err    = ""
                    try: st.query_params.update({"u": email.strip(), "t": _make_token(email.strip())})
                    except: pass
                    st.balloons(); st.rerun()
                else:
                    st.session_state._login_err = err_msg; st.rerun()


def _attempt_login(email, password):
    cfg = st.secrets.get("SWAG", {})
    url = cfg.get("url", "").rstrip("/")
    db  = cfg.get("db", "")
    if not url or not db:
        return False, "SWAG connection not configured."
    try:
        uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True).authenticate(db, email, password, {})
        return (True, "") if (uid and isinstance(uid, int) and uid > 0) else (False, f"Login failed on {db}.")
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        email  = st.session_state.get("user_email", "")
        avatar = email[0].upper() if email else "S"
        reorder_df  = st.session_state.get("reorder_df")
        reorder_cnt = len(reorder_df) if reorder_df is not None and not reorder_df.empty else 0
        crit_cnt    = (len(reorder_df[reorder_df[C_PRIORITY].str.contains("Critical", na=False)])
                       if reorder_df is not None and not reorder_df.empty and C_PRIORITY in reorder_df.columns else 0)

        st.markdown(f"""
        <div style="padding:.8rem 0 1rem;border-bottom:1px solid #e5e7eb;margin-bottom:1rem;">
          <div style="display:flex;align-items:center;gap:.6rem;">
            <div style="width:36px;height:36px;border-radius:12px;
                background:linear-gradient(135deg,#0ea5e9,#22c55e);
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-weight:700;font-size:.9rem;box-shadow:0 0 18px rgba(14,165,233,.35);">S</div>
            <div>
              <div style="font-size:.95rem;font-weight:700;color:#111827;">SWAG Control</div>
              <div style="font-size:.72rem;color:#9ca3af;">Inventory Intelligence</div>
            </div>
          </div>
        </div>
        <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;
            padding:.55rem .75rem;margin-bottom:1rem;display:flex;align-items:center;gap:.6rem;">
          <div style="width:28px;height:28px;border-radius:999px;
              background:linear-gradient(135deg,#0ea5e9,#22c55e);
              display:flex;align-items:center;justify-content:center;
              font-weight:700;font-size:.8rem;color:#fff;">{avatar}</div>
          <div>
            <div style="font-size:.75rem;color:#111827;font-weight:500;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px;">{email}</div>
            <div style="font-size:.63rem;color:#22c55e;font-weight:600;">● Online</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='font-size:.68rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>Workspaces</div>", unsafe_allow_html=True)
        current_view = st.session_state.get("analytics_view", "stock")
        for key, (label, _meta) in {
            "stock":    ("📊 Stock Overview",    "SWAG"),
            "purchase": ("🛒 Purchase Analytics", "PO"),
            "sales":    ("📈 Sales Analytics",    "SO"),
        }.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                         type="primary" if current_view == key else "secondary"):
                st.session_state.analytics_view = key; st.rerun()

        st.markdown("<hr style='border-color:#e5e7eb;margin:.8rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.68rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>Snapshots</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;padding:.65rem .75rem;margin-bottom:.5rem;font-size:.72rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;color:#111827;font-weight:600;">
            <span>Stock trend</span><span style="color:#16a34a;">+12%</span></div>
          <div style="font-size:.68rem;color:#9ca3af;">Last 30 days</div>
          <div style="display:flex;gap:3px;margin-top:.4rem;align-items:flex-end;">
            {''.join(f'<div style="width:6px;height:{h}px;border-radius:3px 3px 0 0;background:{c};"></div>' for h,c in [(18,'#bfdbfe'),(26,'#60a5fa'),(14,'#bfdbfe'),(28,'#0ea5e9'),(20,'#bfdbfe'),(24,'#22c55e')])}
          </div>
        </div>
        <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;padding:.65rem .75rem;margin-bottom:.5rem;font-size:.72rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;color:#111827;font-weight:600;">
            <span>Reorder risk</span><span style="color:#dc2626;">{reorder_cnt} items</span></div>
          <div style="font-size:.68rem;color:#9ca3af;">Below threshold</div>
          <div style="display:flex;gap:4px;margin-top:.45rem;flex-wrap:wrap;">
            <span class="pill-danger">Critical {crit_cnt}</span>
            <span class="pill-warning">Low</span><span class="pill-ok">OK</span>
          </div>
        </div>
        <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;padding:.65rem .75rem;margin-bottom:.5rem;font-size:.72rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;color:#111827;font-weight:600;">
            <span>Sales vs stock</span><span style="color:#16a34a;">72%</span></div>
          <div style="font-size:.68rem;color:#9ca3af;">Sell-through</div>
          <div style="width:100%;height:8px;border-radius:999px;background:#e5e7eb;margin-top:.5rem;overflow:hidden;">
            <div style="width:72%;height:100%;background:linear-gradient(90deg,#22c55e,#0ea5e9);"></div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#e5e7eb;margin:.8rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.68rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>Search Settings</div>", unsafe_allow_html=True)
        st.session_state.low_stock_thresh = st.slider("Low Stock Threshold", 0, 50, st.session_state.low_stock_thresh)
        st.session_state.search_exact     = st.checkbox("Exact Match",    value=st.session_state.search_exact)
        st.session_state.show_transfers   = st.checkbox("Show Transfers", value=st.session_state.show_transfers)
        st.session_state.show_reorder     = st.checkbox("Show Reorder",   value=st.session_state.show_reorder)
        with st.expander("⚙️ Reorder Settings"):
            st.session_state.reorder_mode        = st.selectbox("Mode", ["days_cover", "reorder_point"],
                                                     index=0 if st.session_state.reorder_mode == "days_cover" else 1)
            st.session_state.reorder_target_days = st.number_input("Target Days",   min_value=1,  max_value=365, value=st.session_state.reorder_target_days)
            st.session_state.reorder_max_level   = st.number_input("Max Level",     min_value=0,                 value=st.session_state.reorder_max_level)
            st.session_state.reorder_point       = st.number_input("Reorder Point", min_value=0,                 value=st.session_state.reorder_point)

        st.markdown("<hr style='border-color:#e5e7eb;margin:.8rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.68rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>System Status</div>", unsafe_allow_html=True)
        stat  = st.session_state.get("sys_stats", {}).get("SWAG", {})
        cfg   = st.secrets.get("SWAG", {})
        level = stat.get("level", "off") if stat else ("ok" if cfg.get("url") else "off")
        icon  = "✅" if level == "ok" else ("❌" if level == "error" else "⚫")
        cls   = "ok" if level == "ok" else ("err" if level == "error" else "off")
        msg   = stat.get("msg", "") if stat else ""
        st.markdown(f"<span class='sys-badge sys-badge-{cls}'>{icon} {cfg.get('name','SWAG')}</span>", unsafe_allow_html=True)
        if level == "error" and msg:
            st.markdown(f"<div style='font-size:.68rem;color:#b91c1c;margin-top:4px;'>{msg}</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#e5e7eb;margin:.8rem 0;'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            do_logout()
        st.markdown("""
        <div style="margin-top:1rem;padding:.7rem .75rem;border-radius:14px;
            background:#eff6ff;border:1px solid #dbeafe;font-size:.74rem;color:#6b7280;">
          <div style="font-size:.78rem;font-weight:600;color:#0f172a;margin-bottom:.25rem;">SWAG connected</div>
          Dashboard wired to SWAG Odoo backend.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STOCK VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_stock():
    today_str = datetime.now().strftime("%d %b %Y  %H:%M")
    c1, c2 = st.columns([2, 1])
    with c1: st.markdown("<div style='font-size:.78rem;letter-spacing:.15em;text-transform:uppercase;color:#9ca3af;margin-bottom:.4rem;'>Executive overview</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div style='text-align:right;font-size:.72rem;color:#9ca3af;'>{today_str}</div>", unsafe_allow_html=True)

    total_df    = st.session_state.get("total_df")
    total_units = int(_to_num(total_df[C_ON_HAND]).sum()) if total_df is not None and not total_df.empty else 0
    models_found= total_df[C_MODEL].nunique() if total_df is not None and not total_df.empty else 0

    st.markdown(f"""
    <div class="hero-banner">
      <div style="max-width:60%;">
        <div class="hero-heading">SWAG stock overview</div>
        <div class="hero-sub">Live picture of SWAG inventory health and low stock.</div>
        <div class="hero-tags">
          <span class="hero-tag">SWAG ERP</span>
          <span class="hero-tag">Inventory</span>
          <span class="hero-tag">Real-time</span>
        </div>
      </div>
      <div style="text-align:right;min-width:200px;">
        <div class="hero-status"><span class="hero-dot"></span> SWAG connected</div>
        <div style="margin-top:.7rem;display:flex;gap:.9rem;justify-content:flex-end;font-size:.75rem;color:#6b7280;">
          <div><div style="font-size:.95rem;font-weight:600;color:#0f172a;">{total_units:,}</div><div>Units</div></div>
          <div><div style="font-size:.95rem;font-weight:600;color:#0f172a;">{models_found:,}</div><div>Models</div></div>
        </div>
      </div>
      <div class="hero-center-title">SWAG DASHBOARD</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='panel'><div class='panel-title'>Product search and filters</div><div class='panel-sub'>Search SWAG models and review stock / reorder.</div>", unsafe_allow_html=True)
    code_input = st.text_area("Model codes (comma or newline separated)", height=70,
                               placeholder="e.g. ABC-001, DEF-002", key="code_input_area")
    col_btn, col_low, col_exact = st.columns([2, 1, 1])
    with col_btn:   search_clicked = st.button("🔍 Run Search", type="primary", use_container_width=True, key="search_btn")
    with col_low:   st.session_state.low_stock_thresh = st.number_input("Low stock ≤", min_value=0, value=st.session_state.low_stock_thresh, key="low_inp")
    with col_exact: st.session_state.search_exact     = st.checkbox("Exact match", value=st.session_state.search_exact, key="exact_cb")
    st.markdown("</div>", unsafe_allow_html=True)

    if search_clicked:
        codes = list(dict.fromkeys([c.strip().upper() for c in re.split(r"[,\n;]+", code_input) if c.strip()]))
        with st.spinner("Fetching data from SWAG…"):
            total_df, branch_df, transfers_df, reorder_df, sys_stats = fetch_all_data(
                codes, st.session_state.search_exact, st.session_state.low_stock_thresh,
                st.session_state.show_transfers, st.session_state.show_reorder,
                st.session_state.reorder_mode, st.session_state.reorder_target_days,
                st.session_state.reorder_max_level, st.session_state.reorder_point)
        st.session_state.total_df     = total_df
        st.session_state.branch_df    = branch_df
        st.session_state.transfers_df = transfers_df
        st.session_state.reorder_df   = reorder_df
        st.session_state.sys_stats    = sys_stats
        st.session_state.last_run     = datetime.now()
        for pk in ["page_total", "page_branch", "page_transfers", "page_reorder"]:
            st.session_state[pk] = 0
        st.rerun()

    total_df = st.session_state.get("total_df")
    if total_df is None or total_df.empty:
        if st.session_state.get("last_run"):
            st.markdown("<div class='empty-state'>ℹ️ No data returned.</div>", unsafe_allow_html=True)
        return

    st.markdown("<hr class='swag-divider'>", unsafe_allow_html=True)
    branch_df    = st.session_state.get("branch_df")
    transfers_df = st.session_state.get("transfers_df")
    reorder_df   = st.session_state.get("reorder_df")

    total_qty = int(_to_num(total_df[C_ON_HAND]).sum())
    total_val = (_to_num(total_df[C_ON_HAND]) * _to_num(total_df[C_SALE_PRICE])).sum()
    zero_cnt  = int((_to_num(total_df[C_ON_HAND]) == 0).sum())
    render_kpis([
        ("Total on hand", f"{total_qty:,}",        "SWAG inventory"),
        ("Stock value",   f"SAR {total_val:,.0f}", "Qty × price"),
        ("Zero stock",    str(zero_cnt),            "Models at 0 qty"),
        ("Unique models", str(total_df[C_MODEL].nunique()), "In SWAG"),
    ])

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("<div class='panel'><div class='panel-title'>Category wise stock</div><div class='panel-sub'>On-hand quantity by category.</div>", unsafe_allow_html=True)
        if C_CATEGORY in total_df.columns:
            agg = total_df.groupby(C_CATEGORY)[C_ON_HAND].sum().reset_index().nlargest(8, C_ON_HAND)
            fig = px.bar(agg, x=C_CATEGORY, y=C_ON_HAND,
                         color_discrete_sequence=["#60a5fa","#34d399","#fbbf24","#f97316"], template="plotly_white")
            fig.update_traces(marker_cornerradius=6, marker_line_width=0, width=0.6)
            st.plotly_chart(_light(fig), use_container_width=True, key="c1")
        st.markdown("</div>", unsafe_allow_html=True)

    with cc2:
        st.markdown("<div class='panel'><div class='panel-title'>Brand share</div><div class='panel-sub'>Stock distribution by system.</div>", unsafe_allow_html=True)
        agg2 = total_df.groupby(C_SYSTEM)[C_ON_HAND].sum().reset_index()
        fig2 = px.pie(agg2, names=C_SYSTEM, values=C_ON_HAND, hole=0.58,
                      color_discrete_sequence=PALETTE, template="plotly_white")
        fig2.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color="#fff", width=2)))
        st.plotly_chart(_light(fig2), use_container_width=True, key="c2")
        st.markdown("</div>", unsafe_allow_html=True)

    cc3, cc4 = st.columns(2)
    with cc3:
        st.markdown("<div class='panel'><div class='panel-title'>Branch coverage</div><div class='panel-sub'>Total stock by branch.</div>", unsafe_allow_html=True)
        if branch_df is not None and not branch_df.empty:
            agg3 = branch_df.groupby(C_BRANCH)[C_ON_HAND].sum().reset_index().nlargest(10, C_ON_HAND)
            fig3 = px.bar(agg3, x=C_BRANCH, y=C_ON_HAND,
                          color_discrete_sequence=["#0ea5e9"], template="plotly_white")
            fig3.update_traces(marker_cornerradius=6, marker_line_width=0)
            st.plotly_chart(_light(fig3), use_container_width=True, key="c3")
        else:
            st.markdown("<div class='empty-state'>No branch data.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with cc4:
        st.markdown("<div class='panel'><div class='panel-title'>Days left by category</div><div class='panel-sub'>Avg days remaining per category.</div>", unsafe_allow_html=True)
        if C_CATEGORY in total_df.columns and C_VEL in total_df.columns:
            dl = total_df.copy()
            dl["_vel"]  = _to_num(dl[C_VEL]); dl["_oh"] = _to_num(dl[C_ON_HAND])
            dl["_days"] = dl.apply(lambda r: r["_oh"]/r["_vel"] if r["_vel"] > 0 else None, axis=1)
            bd = dl.groupby(C_CATEGORY)["_days"].mean().dropna().reset_index()
            bd.columns = [C_CATEGORY, "Avg Days"]; bd = bd.sort_values("Avg Days")
            colors4 = ["#ef4444" if v < 7 else "#f59e0b" if v < 14 else "#22c55e" for v in bd["Avg Days"]]
            fig4 = px.bar(bd, x=C_CATEGORY, y="Avg Days", template="plotly_white")
            fig4.update_traces(marker_cornerradius=6, marker_line_width=0, marker_color=colors4)
            st.plotly_chart(_light(fig4), use_container_width=True, key="c4")
        else:
            st.markdown("<div class='empty-state'>No days-left data.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='swag-divider'>", unsafe_allow_html=True)
    tab_labels = ["📊 Total Stock", "🏪 By Branch"]
    if st.session_state.show_transfers: tab_labels.append("🔄 Transfers")
    if st.session_state.show_reorder:   tab_labels.append("🔔 Reorder Risk")
    tabs = st.tabs(tab_labels); ti = 0

    with tabs[ti]:
        ti += 1
        st.markdown(f"<div style='font-size:.72rem;color:#6b7280;margin-bottom:4px;'>Loaded {len(total_df)} SWAG product rows.</div>", unsafe_allow_html=True)
        mini_grid([("Zero-stock models", str(zero_cnt), "Need purchase / transfer"),
                   ("Tracked models", str(total_df[C_MODEL].nunique()), "In current view")])
        display_df(total_df, "page_total")
        dc1, dc2 = st.columns(2)
        with dc1: st.download_button("⬇️ Export CSV",   to_csv(total_df),   dl_name("total_stock","csv"),  "text/csv", use_container_width=True)
        with dc2: st.download_button("⬇️ Export Excel", to_excel(total_df), dl_name("total_stock","xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with tabs[ti]:
        ti += 1
        if branch_df is None or branch_df.empty:
            st.markdown("<div class='empty-state'>ℹ️ No branch data.</div>", unsafe_allow_html=True)
        else:
            pb = branch_df.groupby(C_BRANCH)[C_ON_HAND].sum().reset_index().sort_values(C_ON_HAND, ascending=False)
            mini_grid([("Top branch", str(pb.iloc[0][C_BRANCH]), f"Qty {int(pb.iloc[0][C_ON_HAND])}"),
                       ("Branches", str(len(pb)), "Active in result")])
            display_df(branch_df, "page_branch")
            bc1, bc2 = st.columns(2)
            with bc1: st.download_button("⬇️ CSV",   to_csv(branch_df),   dl_name("branch","csv"),  "text/csv", use_container_width=True)
            with bc2: st.download_button("⬇️ Excel", to_excel(branch_df), dl_name("branch","xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    if st.session_state.show_transfers and ti < len(tabs):
        with tabs[ti]:
            ti += 1
            if transfers_df is None or transfers_df.empty:
                st.markdown("<div class='empty-state'>ℹ️ No pending transfers.</div>", unsafe_allow_html=True)
            else:
                tf_total = int(_to_num(transfers_df[C_QTY]).sum()) if C_QTY in transfers_df.columns else 0
                mini_grid([("Transfer Lines", f"{len(transfers_df):,}", "Pending"),
                           ("Total Qty Moving", f"{tf_total:,}", "In transit")])
                display_df(transfers_df, "page_transfers")

    if st.session_state.show_reorder and ti < len(tabs):
        with tabs[ti]:
            if reorder_df is None or reorder_df.empty:
                st.markdown("<div style='text-align:center;padding:1.5rem;'><span class='pill-ok'>✅ No reorder needed.</span></div>", unsafe_allow_html=True)
            else:
                crit = len(reorder_df[reorder_df[C_PRIORITY].str.contains("Critical", na=False)]) if C_PRIORITY in reorder_df.columns else 0
                mini_grid([("Items to reorder", f"{len(reorder_df):,}", "Based on current rule"),
                           ("Critical priority", str(crit), "Immediate PO suggestion")])
                display_df(reorder_df, "page_reorder")
                rc1, rc2 = st.columns(2)
                with rc1: st.download_button("⬇️ CSV",   to_csv(reorder_df),   dl_name("reorder","csv"),  "text/csv", use_container_width=True)
                with rc2: st.download_button("⬇️ Excel", to_excel(reorder_df), dl_name("reorder","xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_purchase():
    today_str = datetime.now().strftime("%d %b %Y  %H:%M")
    st.markdown(f"<div style='font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:#9ca3af;margin-bottom:.4rem;'>Executive overview &nbsp;|&nbsp; {today_str}</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-banner">
      <div>
        <div class="hero-heading">🛒 SWAG purchase analytics</div>
        <div class="hero-sub">See how much you're buying, from whom, and days of coverage per PO.</div>
        <div class="hero-tags">
          <span class="hero-tag">Purchase Orders</span>
          <span class="hero-tag">Vendor Analysis</span>
          <span class="hero-tag">Days Cover</span>
          <span class="hero-tag">Currency</span>
        </div>
      </div>
      <div style="text-align:right;"><div class="hero-status"><span class="hero-dot"></span> SWAG connected</div></div>
      <div class="hero-center-title">SWAG DASHBOARD</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    d1, d2, mc_col = st.columns([1, 1, 2])
    with d1:     date_from = st.date_input("From Date", value=datetime.now()-timedelta(days=30), key="po_from")
    with d2:     date_to   = st.date_input("To Date",   value=datetime.now(),                   key="po_to")
    with mc_col: mc_input  = st.text_input("Model Code Filter (optional)", placeholder="e.g. ABC-001", key="po_mc")
    if st.button("🔍 Fetch Purchase Data", type="primary", use_container_width=True, key="po_fetch"):
        mc_list = [c.strip().upper() for c in re.split(r"[,\n;]+", mc_input) if c.strip()] if mc_input.strip() else []
        with st.spinner("Fetching purchase history…"):
            po_df = fetch_all_purchase_history(mc_list, str(date_from), str(date_to))
        st.session_state.po_analytics_df = po_df; st.session_state.page_po = 0; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    po_df = st.session_state.get("po_analytics_df")
    if po_df is None or po_df.empty:
        if st.session_state.po_analytics_df is not None:
            st.markdown("<div class='empty-state'>ℹ️ No purchase data found.</div>", unsafe_allow_html=True)
        return

    st.markdown("<hr class='swag-divider'>", unsafe_allow_html=True)
    total_spend = _to_num(po_df[C_SUBTOTAL]).sum()
    total_qty_p = _to_num(po_df[C_QTY_PURCHASED]).sum()
    vendor_cnt  = po_df[C_VENDOR].nunique()
    currencies  = list(po_df[C_CURRENCY].dropna().unique()) if C_CURRENCY in po_df.columns else ["SAR"]
    render_kpis([
        ("PO spend (orig. currency)", f"{total_spend:,.0f}", "Mixed currencies — see table"),
        ("Units bought",  f"{total_qty_p:,.0f}", "All PO lines"),
        ("Vendors",       str(vendor_cnt),        "Active vendors"),
        ("Currencies",    ", ".join(currencies),  f"{len(currencies)} currency type(s)"),
    ])

    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown("<div class='panel'><div class='panel-title'>Top vendors</div><div class='panel-sub'>Purchase subtotal by vendor.</div>", unsafe_allow_html=True)
        va = po_df.groupby(C_VENDOR)[C_SUBTOTAL].sum().reset_index().nlargest(6, C_SUBTOTAL)
        fig = px.bar(va, x=C_SUBTOTAL, y=C_VENDOR, orientation="h",
                     color_discrete_sequence=PALETTE, template="plotly_white")
        fig.update_traces(marker_cornerradius=6, marker_line_width=0)
        st.plotly_chart(_light(fig), use_container_width=True, key="poc1")
        st.markdown("</div>", unsafe_allow_html=True)

    with pc2:
        st.markdown("<div class='panel'><div class='panel-title'>Purchase by category</div><div class='panel-sub'>Quantity by category.</div>", unsafe_allow_html=True)
        ca = po_df.groupby(C_CATEGORY)[C_QTY_PURCHASED].sum().reset_index().nlargest(6, C_QTY_PURCHASED)
        fig2 = px.pie(ca, names=C_CATEGORY, values=C_QTY_PURCHASED, hole=0.58,
                      color_discrete_sequence=PALETTE, template="plotly_white")
        fig2.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color="#fff", width=2)))
        st.plotly_chart(_light(fig2), use_container_width=True, key="poc2")
        st.markdown("</div>", unsafe_allow_html=True)

    pc3, pc4 = st.columns(2)
    with pc3:
        st.markdown("<div class='panel'><div class='panel-title'>Daily purchase spend</div><div class='panel-sub'>Date wise purchase amount.</div>", unsafe_allow_html=True)
        daily = po_df.copy(); daily["_d"] = pd.to_datetime(daily[C_DATE], errors="coerce").dt.date
        da = daily.groupby("_d")[C_SUBTOTAL].sum().reset_index(); da.columns = ["Date", "Spend"]
        if not da.empty:
            fig3 = px.area(da, x="Date", y="Spend",
                           color_discrete_sequence=["#10b981"], template="plotly_white")
            fig3.update_traces(fill="tozeroy", fillcolor="rgba(16,185,129,.14)")
            st.plotly_chart(_light(fig3), use_container_width=True, key="poc3")
        st.markdown("</div>", unsafe_allow_html=True)

    with pc4:
        st.markdown("<div class='panel'><div class='panel-title'>Top vendors by volume</div><div class='panel-sub'>Units purchased per vendor.</div>", unsafe_allow_html=True)
        vv = po_df.groupby(C_VENDOR)[C_QTY_PURCHASED].sum().reset_index().nlargest(8, C_QTY_PURCHASED)
        fig4 = px.bar(vv, x=C_VENDOR, y=C_QTY_PURCHASED,
                      color_discrete_sequence=PALETTE, template="plotly_white")
        fig4.update_traces(marker_cornerradius=6, marker_line_width=0)
        st.plotly_chart(_light(fig4), use_container_width=True, key="poc4")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='swag-divider'><div class='panel-title'>Purchase detail</div><div class='panel-sub' style='margin-bottom:8px;'>PO data with currency via SWAG backend.</div>", unsafe_allow_html=True)
    display_df(po_df, "page_po")
    ec1, ec2 = st.columns(2)
    with ec1: st.download_button("⬇️ Export CSV",   to_csv(po_df),   dl_name("purchase","csv"),  "text/csv", use_container_width=True)
    with ec2: st.download_button("⬇️ Export Excel", to_excel(po_df), dl_name("purchase","xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SALES VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_sales():
    today_str = datetime.now().strftime("%d %b %Y  %H:%M")
    st.markdown(f"<div style='font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:#9ca3af;margin-bottom:.4rem;'>Executive overview &nbsp;|&nbsp; {today_str}</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-banner" style="border-color:#bbf7d0;background:linear-gradient(135deg,#ecfdf5,#eff6ff);">
      <div>
        <div class="hero-heading">📈 SWAG sales analytics</div>
        <div class="hero-sub">Understand which models drive revenue and how many days of stock remain.</div>
        <div class="hero-tags">
          <span class="hero-tag" style="background:#ecfdf3;border-color:#bbf7d0;color:#166534;">Sales Orders</span>
          <span class="hero-tag" style="background:#ecfdf3;border-color:#bbf7d0;color:#166534;">Revenue</span>
          <span class="hero-tag" style="background:#ecfdf3;border-color:#bbf7d0;color:#166534;">Customer Mix</span>
        </div>
      </div>
      <div style="text-align:right;"><div class="hero-status"><span class="hero-dot"></span> SWAG connected</div></div>
      <div class="hero-center-title">SWAG DASHBOARD</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    d1, d2, mc_col = st.columns([1, 1, 2])
    with d1:     date_from = st.date_input("From Date", value=datetime.now()-timedelta(days=30), key="sa_from")
    with d2:     date_to   = st.date_input("To Date",   value=datetime.now(),                   key="sa_to")
    with mc_col: mc_input  = st.text_input("Model Code Filter (optional)", placeholder="e.g. ABC-001", key="sa_mc")
    if st.button("🔍 Fetch Sales Data", type="primary", use_container_width=True, key="sa_fetch"):
        mc_list = [c.strip().upper() for c in re.split(r"[,\n;]+", mc_input) if c.strip()] if mc_input.strip() else []
        with st.spinner("Fetching sales history…"):
            sa_df = fetch_all_sales_history(mc_list, str(date_from), str(date_to))
        st.session_state.salesanalyticsdf = sa_df; st.session_state.page_sales = 0; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    sa_df = st.session_state.get("salesanalyticsdf")
    if sa_df is None or sa_df.empty:
        if st.session_state.salesanalyticsdf is not None:
            st.markdown("<div class='empty-state'>ℹ️ No sales data found.</div>", unsafe_allow_html=True)
        return

    st.markdown("<hr class='swag-divider'>", unsafe_allow_html=True)
    total_rev   = _to_num(sa_df[C_SUBTOTAL]).sum()
    total_qty_s = _to_num(sa_df[C_QTY]).sum()
    cust_cnt    = sa_df[C_CUSTOMER].nunique()
    so_cnt      = sa_df[C_SO].nunique() if C_SO in sa_df.columns else len(sa_df)
    render_kpis([
        ("Revenue",    f"SAR {total_rev:,.0f}", "Selected period"),
        ("Units sold", f"{total_qty_s:,.0f}",   "All SO lines"),
        ("Customers",  str(cust_cnt),            "Unique customers"),
        ("SO lines",   str(so_cnt),              "Sales orders"),
    ])

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("<div class='panel'><div class='panel-title'>Top models by sales</div><div class='panel-sub'>Qty sold per model.</div>", unsafe_allow_html=True)
        ma = sa_df.groupby(C_MODEL)[C_QTY].sum().reset_index().nlargest(10, C_QTY)
        fig = px.bar(ma, x=C_MODEL, y=C_QTY,
                     color_discrete_sequence=["#f97316","#22c55e"], template="plotly_white")
        fig.update_traces(marker_cornerradius=6, marker_line_width=0)
        st.plotly_chart(_light(fig), use_container_width=True, key="sc1")
        st.markdown("</div>", unsafe_allow_html=True)

    with sc2:
        st.markdown("<div class='panel'><div class='panel-title'>Sales by day</div><div class='panel-sub'>Daily revenue line chart.</div>", unsafe_allow_html=True)
        daily = sa_df.copy(); daily["_d"] = pd.to_datetime(daily[C_DATE], errors="coerce").dt.date
        da = daily.groupby("_d")[C_SUBTOTAL].sum().reset_index(); da.columns = ["Date", "Revenue"]
        if not da.empty:
            fig2 = px.area(da, x="Date", y="Revenue",
                           color_discrete_sequence=["#22c55e"], template="plotly_white")
            fig2.update_traces(fill="tozeroy", fillcolor="rgba(34,197,94,.15)")
            st.plotly_chart(_light(fig2), use_container_width=True, key="sc2")
        st.markdown("</div>", unsafe_allow_html=True)

    sc3, sc4 = st.columns(2)
    with sc3:
        st.markdown("<div class='panel'><div class='panel-title'>Customer mix</div><div class='panel-sub'>Revenue by customer.</div>", unsafe_allow_html=True)
        ca = sa_df.groupby(C_CUSTOMER)[C_SUBTOTAL].sum().reset_index().nlargest(8, C_SUBTOTAL)
        fig3 = px.pie(ca, names=C_CUSTOMER, values=C_SUBTOTAL, hole=0.58,
                      color_discrete_sequence=PALETTE, template="plotly_white")
        fig3.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color="#fff", width=2)))
        st.plotly_chart(_light(fig3), use_container_width=True, key="sc3")
        st.markdown("</div>", unsafe_allow_html=True)

    with sc4:
        st.markdown("<div class='panel'><div class='panel-title'>Top customers by volume</div><div class='panel-sub'>Units sold per customer.</div>", unsafe_allow_html=True)
        cv = sa_df.groupby(C_CUSTOMER)[C_QTY].sum().reset_index().nlargest(8, C_QTY)
        fig4 = px.bar(cv, x=C_CUSTOMER, y=C_QTY,
                      color_discrete_sequence=PALETTE, template="plotly_white")
        fig4.update_traces(marker_cornerradius=6, marker_line_width=0)
        st.plotly_chart(_light(fig4), use_container_width=True, key="sc4")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='swag-divider'><div class='panel-title'>Sales detail</div><div class='panel-sub' style='margin-bottom:8px;'>SO data with stock estimates via SWAG backend.</div>", unsafe_allow_html=True)
    display_df(sa_df, "page_sales")
    es1, es2 = st.columns(2)
    with es1: st.download_button("⬇️ Export CSV",   to_csv(sa_df),   dl_name("sales","csv"),  "text/csv", use_container_width=True)
    with es2: st.download_button("⬇️ Export Excel", to_excel(sa_df), dl_name("sales","xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    st.markdown(_css(), unsafe_allow_html=True)
    render_sidebar()
    view = st.session_state.get("analytics_view", "stock")
    if   view == "purchase": show_purchase()
    elif view == "sales":    show_sales()
    else:                    show_stock()


def main():
    restore_session()
    if not st.session_state.authenticated:
        show_login()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
