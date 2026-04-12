# app.py — SWAG Product Comparison Dashboard — Version 29.0
# Full production-ready implementation

import io
import re
import math
import hashlib
import time
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SWAG Product Comparison Dashboard",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: SYSTEM KEYS & CANONICAL COLUMN CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]

PAGE_SIZE = 50

# Canonical column names (internal use only — English)
C_SYSTEM       = "System"
C_MODEL        = "Model Code"
C_PRODUCT      = "Product"
C_SALE_PRICE   = "Sale Price"
C_ON_HAND      = "On Hand"
C_BRANCH       = "Branch"
C_LOCATION     = "Location"
C_REFERENCE    = "Reference"
C_TYPE         = "Type"
C_STATE        = "State"
C_FROM         = "From"
C_TO           = "To"
C_QTY          = "Qty"
C_SCHEDULED    = "Scheduled Date"
C_SOLD         = "Sold (30d)"
C_VEL          = "Daily Velocity"
C_DAYS_LEFT    = "Days Left"
C_SUGGEST      = "Suggested Order"
C_PRIORITY     = "Priority"
C_DATE         = "Date"
C_PO           = "PO"
C_SO           = "SO"
C_VENDOR       = "Vendor"
C_CUSTOMER     = "Customer"
C_BRAND_CAT    = "Brand/Category"
C_CATEGORY     = "Category"
C_UNIT_PRICE   = "Unit Price"
C_SUBTOTAL     = "Subtotal"
C_QTY_PURCHASED = "Qty Purchased"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: BILINGUAL SUPPORT
# ─────────────────────────────────────────────────────────────────────────────
def get_lang() -> str:
    return st.session_state.get("lang", "EN")

def t(en: str, ar: str) -> str:
    return ar if get_lang() == "AR" else en

def get_dir() -> str:
    return "rtl" if get_lang() == "AR" else "ltr"

# Canonical → display label map  {canonical: (EN label, AR label)}
_COL_LABELS = {
    C_SYSTEM:        ("System",           "النظام"),
    C_MODEL:         ("Model Code",       "رمز الموديل"),
    C_PRODUCT:       ("Product",          "المنتج"),
    C_SALE_PRICE:    ("Sale Price",       "سعر البيع"),
    C_ON_HAND:       ("On Hand",          "المتوفر"),
    C_BRANCH:        ("Branch",           "الفرع"),
    C_LOCATION:      ("Location",         "الموقع"),
    C_REFERENCE:     ("Reference",        "المرجع"),
    C_TYPE:          ("Type",             "النوع"),
    C_STATE:         ("State",            "الحالة"),
    C_FROM:          ("From",             "من"),
    C_TO:            ("To",               "إلى"),
    C_QTY:           ("Qty",              "الكمية"),
    C_SCHEDULED:     ("Scheduled Date",   "التاريخ المجدول"),
    C_SOLD:          ("Sold (30d)",       "مباع (30 يوم)"),
    C_VEL:           ("Daily Velocity",   "السرعة اليومية"),
    C_DAYS_LEFT:     ("Days Left",        "الأيام المتبقية"),
    C_SUGGEST:       ("Suggested Order",  "الطلب المقترح"),
    C_PRIORITY:      ("Priority",         "الأولوية"),
    C_DATE:          ("Date",             "التاريخ"),
    C_PO:            ("PO",               "أمر شراء"),
    C_SO:            ("SO",               "أمر بيع"),
    C_VENDOR:        ("Vendor",           "المورد"),
    C_CUSTOMER:      ("Customer",         "العميل"),
    C_BRAND_CAT:     ("Brand/Category",   "العلامة/الفئة"),
    C_CATEGORY:      ("Category",         "الفئة"),
    C_UNIT_PRICE:    ("Unit Price",       "سعر الوحدة"),
    C_SUBTOTAL:      ("Subtotal",         "المجموع الفرعي"),
    C_QTY_PURCHASED: ("Qty Purchased",    "الكمية المشتراة"),
}

def col_label(canonical: str) -> str:
    entry = _COL_LABELS.get(canonical)
    if entry:
        return entry[1] if get_lang() == "AR" else entry[0]
    return canonical

def df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Rename canonical columns to current-language labels for display only."""
    if df is None or df.empty:
        return df
    rename = {}
    for canonical, (en, ar) in _COL_LABELS.items():
        if canonical in df.columns:
            rename[canonical] = ar if get_lang() == "AR" else en
    return df.rename(columns=rename) if rename else df.copy()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False,
    "user_email": "",
    "lang": "EN",
    "last_run": None,
    "total_df": None,
    "branch_df": None,
    "transfers_df": None,
    "reorder_df": None,
    "sys_stats": {},
    "search_exact": False,
    "low_stock_thresh": 5,
    "price_history": {},
    "show_transfers": True,
    "show_reorder": True,
    "reorder_mode": "days_cover",
    "reorder_target_days": 30,
    "reorder_max_level": 100,
    "reorder_point": 10,
    "pdf_codes": [],
    "pdf_mode": False,
    "po_analytics_df": None,
    "pc_purch_df": None,
    "pc_stock_df": None,
    "pc_last_code": "",
    "salesanalyticsdf": None,
    "analytics_view": "stock",
    "page_total": 0,
    "page_branch": 0,
    "page_transfers": 0,
    "page_reorder": 0,
    "page_po": 0,
    "page_sales": 0,
}

for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: AUTH
# ─────────────────────────────────────────────────────────────────────────────
_TOKEN_SECRET = "swag_v29_prod_2025"

def _make_token(email: str) -> str:
    raw = f"{_TOKEN_SECRET}::{email}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]

def _verify_token(email: str, token: str) -> bool:
    return bool(email and token and token == _make_token(email))

def restore_session():
    if st.session_state.get("authenticated"):
        return
    try:
        params = st.query_params
        email = params.get("u", "")
        token = params.get("t", "")
        if email and token and _verify_token(email, token):
            st.session_state.authenticated = True
            st.session_state.user_email = email
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
# SECTION 5: ODOO XML-RPC HELPERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def _proxy(url: str, ep: str):
    return xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/{ep}", allow_none=True)

@st.cache_data(ttl=3600, show_spinner=False)
def _auth(url: str, db: str, user: str, key: str):
    try:
        uid = _proxy(url, "common").authenticate(db, user, key, {})
        return uid if (uid and isinstance(uid, int) and uid > 0) else None
    except Exception:
        return None

def _x(url, db, uid, key, model, method, domain, kw=None):
    if kw is None:
        kw = {}
    return _proxy(url, "object").execute_kw(db, uid, key, model, method, domain, kw)

def _domain(codes: list, exact: bool) -> list:
    if not codes:
        return []
    if exact:
        return [("default_code", "in", codes)]
    clauses = [("default_code", "=ilike", f"{c}%") for c in codes]
    if len(clauses) == 1:
        return [clauses[0]]
    domain = []
    for _ in range(len(clauses) - 1):
        domain.append("|")
    domain.extend(clauses)
    return domain

def _get_conn(key: str):
    cfg = st.secrets.get(key, {})
    url = cfg.get("url", "").rstrip("/")
    db = cfg.get("db", "")
    user = cfg.get("user", "")
    api_key = cfg.get("api_key", "")
    if not url or not db or not user or not api_key:
        return None, None, None, None, key, f"[{key}] Missing config."
    uid = _auth(url, db, user, api_key)
    if not uid:
        return url, db, None, api_key, key, f"[{key}] Auth failed."
    name_en = cfg.get("name", key)
    name_ar = cfg.get("name_ar", name_en)
    display_name = name_ar if get_lang() == "AR" else name_en
    return url, db, uid, api_key, display_name, None

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: NUMERIC HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)

def _safe_val(val):
    try:
        return float(val)
    except Exception:
        return 0.0

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: PDF INVOICE PARSING
# ─────────────────────────────────────────────────────────────────────────────
_EXCLUDE = {
    "SR", "VAT", "TAX", "PCS", "QTY", "NO", "REF", "INV", "PO", "SO",
    "DO", "ID", "EN", "AR", "PDF", "AED", "SAR", "USD", "KWD", "OMR",
    "BHD", "JOD", "EGP", "TRY",
}

_PDF_PATTERNS = [
    re.compile(r"\[([A-Z0-9][A-Z0-9\-]{2,})\]"),
    re.compile(r"^SR\s+([A-Z0-9][A-Z0-9\-]{2,})", re.MULTILINE),
    re.compile(r"\b([A-Z]{2,}[0-9]{2,}[A-Z0-9\-]*)\b"),
]

def parse_invoice_pdf_cached(file_bytes: bytes) -> list:
    """Parse PDF invoice bytes, return list of {sequence, code} dicts."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    except Exception:
        return []
    text = ""
    for page in reader.pages:
        try:
            text += (page.extract_text() or "") + "\n"
        except Exception:
            pass
    found = []
    seen = set()
    seq = 0
    for pat in _PDF_PATTERNS:
        for m in pat.finditer(text):
            code = m.group(1).strip().upper()
            if code in _EXCLUDE or len(code) < 3:
                continue
            if code not in seen:
                seen.add(code)
                found.append({"sequence": seq, "code": code})
                seq += 1
    return found

def extract_base_model(code: str) -> str:
    """Strip size suffixes like -XL, -M, -42, -38, etc."""
    cleaned = re.sub(r"[-_](XS|S|M|L|XL|XXL|2XL|3XL|XXXL|\d{2,3})$", "", code.upper().strip())
    return cleaned

def get_unique_base_models(raw: list) -> list:
    """Deduplicate by base model code."""
    seen = set()
    result = []
    for item in raw:
        base = extract_base_model(item["code"])
        if base not in seen:
            seen.add(base)
            result.append(base)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: DATA FETCHING — INVENTORY & TRANSFERS & REORDER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_stock_one(key: str, codes_tuple: tuple, exact: bool, low_thresh: int,
                     show_transfers: bool, show_reorder: bool, reorder_mode: str,
                     reorder_target_days: int, reorder_max_level: int, reorder_point: int):
    url, db, uid, ak, name, err = _get_conn(key)
    if err:
        return [], [], [], [], {"system": name, "level": "error", "msg": err}

    codes = list(codes_tuple)
    try:
        # ── Products ──────────────────────────────────────────────────────────
        prod_domain = _domain(codes, exact) if codes else []
        templates = _x(url, db, uid, ak, "product.template", "search_read",
                        [prod_domain if prod_domain else []],
                        {"fields": ["id", "name", "default_code", "list_price", "categ_id"], "limit": 5000})
        if not templates:
            return [], [], [], [], {"system": name, "level": "ok", "msg": "No products found."}

        tmpl_map = {t["id"]: t for t in templates}
        tmpl_ids = list(tmpl_map.keys())

        # Variants
        variants = _x(url, db, uid, ak, "product.product", "search_read",
                       [[("product_tmpl_id", "in", tmpl_ids)]],
                       {"fields": ["id", "product_tmpl_id"], "limit": 50000})
        var_to_tmpl = {}
        for v in variants:
            raw = v.get("product_tmpl_id")
            tid = raw[0] if isinstance(raw, list) else raw
            var_to_tmpl[v["id"]] = tid
        var_ids = list(var_to_tmpl.keys())

        # Quants
        tmpl_qty = {}
        branch_rows = []
        if var_ids:
            quants = _x(url, db, uid, ak, "stock.quant", "search_read",
                         [[("product_id", "in", var_ids), ("location_id.usage", "=", "internal")]],
                         {"fields": ["product_id", "location_id", "quantity"], "limit": 50000})
            for q in quants:
                pid_raw = q.get("product_id")
                vid = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
                tid = var_to_tmpl.get(vid)
                if tid is None:
                    continue
                qty = float(q.get("quantity") or 0)
                tmpl_qty[tid] = tmpl_qty.get(tid, 0) + qty
                loc_raw = q.get("location_id")
                loc_name = loc_raw[1] if isinstance(loc_raw, list) and len(loc_raw) > 1 else str(loc_raw or "")
                mc = (tmpl_map.get(tid, {}).get("default_code") or "").strip()
                if mc:
                    branch_rows.append({C_SYSTEM: name, C_BRANCH: loc_name, C_MODEL: mc, C_ON_HAND: qty})

        # ── 30-day sales velocity ─────────────────────────────────────────────
        date_30_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        vel_map = {}
        if var_ids and (show_reorder or True):
            try:
                so_lines = _x(url, db, uid, ak, "sale.order.line", "search_read",
                               [[("product_id", "in", var_ids),
                                 ("order_id.date_order", ">=", f"{date_30_ago} 00:00:00"),
                                 ("order_id.state", "in", ["sale", "done"])]],
                               {"fields": ["product_id", "product_uom_qty"], "limit": 50000})
                for sl in so_lines:
                    pid_raw = sl.get("product_id")
                    vid = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
                    tid = var_to_tmpl.get(vid)
                    if tid:
                        vel_map[tid] = vel_map.get(tid, 0) + float(sl.get("product_uom_qty") or 0)
            except Exception:
                pass

        # ── Build total rows ──────────────────────────────────────────────────
        total_rows = []
        for tid, tmpl in tmpl_map.items():
            mc = (tmpl.get("default_code") or "").strip()
            categ_raw = tmpl.get("categ_id")
            category = categ_raw[1] if isinstance(categ_raw, list) and len(categ_raw) > 1 else ""
            on_hand = tmpl_qty.get(tid, 0)
            sale_price = float(tmpl.get("list_price") or 0)
            sold_30 = vel_map.get(tid, 0)
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

        # ── Reorder ───────────────────────────────────────────────────────────
        reorder_rows = []
        if show_reorder:
            for tid, tmpl in tmpl_map.items():
                mc = (tmpl.get("default_code") or "").strip()
                on_hand = tmpl_qty.get(tid, 0)
                sold_30 = vel_map.get(tid, 0)
                daily_vel = sold_30 / 30.0

                if reorder_mode == "days_cover":
                    days_left = (on_hand / daily_vel) if daily_vel > 0 else 999
                    suggest = max(0, round(daily_vel * reorder_target_days - on_hand))
                    priority = (
                        "🔴 Critical" if days_left < 7
                        else "🟡 Low" if days_left < 14
                        else "🟢 OK"
                    )
                else:  # reorder_point
                    days_left = (on_hand / daily_vel) if daily_vel > 0 else 999
                    suggest = max(0, reorder_max_level - on_hand) if on_hand <= reorder_point else 0
                    priority = "🔴 Critical" if on_hand <= reorder_point else "🟢 OK"

                if suggest > 0 or on_hand <= low_thresh:
                    reorder_rows.append({
                        C_SYSTEM:   name,
                        C_MODEL:    mc,
                        C_PRODUCT:  tmpl.get("name", ""),
                        C_ON_HAND:  on_hand,
                        C_SOLD:     sold_30,
                        C_VEL:      round(daily_vel, 3),
                        C_DAYS_LEFT: round(days_left, 1) if days_left < 999 else "∞",
                        C_SUGGEST:  suggest,
                        C_PRIORITY: priority,
                    })

        # ── Internal transfers ────────────────────────────────────────────────
        transfer_rows = []
        if show_transfers and var_ids:
            try:
                moves = _x(url, db, uid, ak, "stock.move", "search_read",
                            [[("product_id", "in", var_ids),
                              ("state", "not in", ["cancel", "done"]),
                              ("picking_id.picking_type_code", "=", "internal")]],
                            {"fields": ["product_id", "product_uom_qty", "state",
                                        "location_id", "location_dest_id", "reference",
                                        "date", "picking_id"], "limit": 5000})
                for mv in moves:
                    pid_raw = mv.get("product_id")
                    vid = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
                    tid = var_to_tmpl.get(vid)
                    mc = (tmpl_map.get(tid, {}).get("default_code") or "").strip() if tid else ""
                    loc_from = mv.get("location_id")
                    loc_to = mv.get("location_dest_id")
                    transfer_rows.append({
                        C_SYSTEM:    name,
                        C_MODEL:     mc,
                        C_PRODUCT:   tmpl_map.get(tid, {}).get("name", "") if tid else "",
                        C_QTY:       float(mv.get("product_uom_qty") or 0),
                        C_STATE:     mv.get("state", ""),
                        C_FROM:      loc_from[1] if isinstance(loc_from, list) and len(loc_from) > 1 else "",
                        C_TO:        loc_to[1] if isinstance(loc_to, list) and len(loc_to) > 1 else "",
                        C_REFERENCE: mv.get("reference", ""),
                        C_SCHEDULED: str(mv.get("date", ""))[:10],
                    })
            except Exception:
                pass

        msg = f"Loaded {len(total_rows)} products."
        return total_rows, branch_rows, transfer_rows, reorder_rows, {"system": name, "level": "ok", "msg": msg}

    except Exception as e:
        return [], [], [], [], {"system": name, "level": "error", "msg": f"{type(e).__name__}: {e}"}


def fetch_all_data(codes, exact, low_stock_thresh, show_transfers,
                   show_reorder, reorder_mode, reorder_target_days,
                   reorder_max_level, reorder_point):
    codes_tuple = tuple(sorted(set(codes))) if codes else ()
    all_total, all_branch, all_transfers, all_reorder, sys_stats = [], [], [], [], {}

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(_fetch_stock_one, k, codes_tuple, exact, low_stock_thresh,
                      show_transfers, show_reorder, reorder_mode,
                      reorder_target_days, reorder_max_level, reorder_point): k
            for k in SYSTEM_KEYS
        }
        for f in as_completed(futs):
            key = futs[f]
            tr, br, tf, ro, stat = f.result()
            all_total.extend(tr)
            all_branch.extend(br)
            all_transfers.extend(tf)
            all_reorder.extend(ro)
            sys_stats[key] = stat

    num_cols_total = [C_SALE_PRICE, C_ON_HAND, C_SOLD, C_VEL]
    total_df = pd.DataFrame(all_total) if all_total else pd.DataFrame(
        columns=[C_SYSTEM, C_MODEL, C_PRODUCT, C_SALE_PRICE, C_ON_HAND, C_SOLD, C_VEL, C_CATEGORY])
    for c in num_cols_total:
        if c in total_df.columns:
            total_df[c] = _to_num(total_df[c])

    branch_df = pd.DataFrame(all_branch) if all_branch else pd.DataFrame(
        columns=[C_SYSTEM, C_BRANCH, C_MODEL, C_ON_HAND])
    if C_ON_HAND in branch_df.columns:
        branch_df[C_ON_HAND] = _to_num(branch_df[C_ON_HAND])

    transfers_df = pd.DataFrame(all_transfers) if all_transfers else pd.DataFrame(
        columns=[C_SYSTEM, C_MODEL, C_PRODUCT, C_QTY, C_STATE, C_FROM, C_TO, C_REFERENCE, C_SCHEDULED])
    if C_QTY in transfers_df.columns:
        transfers_df[C_QTY] = _to_num(transfers_df[C_QTY])

    reorder_df = pd.DataFrame(all_reorder) if all_reorder else pd.DataFrame(
        columns=[C_SYSTEM, C_MODEL, C_PRODUCT, C_ON_HAND, C_SOLD, C_VEL, C_DAYS_LEFT, C_SUGGEST, C_PRIORITY])

    return total_df, branch_df, transfers_df, reorder_df, sys_stats

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: PURCHASE HISTORY FETCHING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_history_for_system(system_key: str, model_codes: tuple, date_from: str, date_to: str) -> pd.DataFrame:
    url, db, uid, ak, name, err = _get_conn(system_key)
    _empty = pd.DataFrame(columns=[C_SYSTEM, C_DATE, C_PO, C_VENDOR, C_PRODUCT, C_MODEL,
                                    C_CATEGORY, C_BRAND_CAT, C_QTY_PURCHASED, C_UNIT_PRICE, C_SUBTOTAL, C_STATE])
    if err:
        return _empty
    try:
        po_domain = [
            ("date_approve", ">=", f"{date_from} 00:00:00"),
            ("date_approve", "<=", f"{date_to} 23:59:59"),
            ("state", "in", ["purchase", "done"]),
        ]
        pos_list = _x(url, db, uid, ak, "purchase.order", "search_read",
                       [po_domain], {"fields": ["id", "name", "partner_id", "date_approve", "state"], "limit": 2000})
        if not pos_list:
            return _empty
        po_ids = [p["id"] for p in pos_list]
        po_map = {p["id"]: p for p in pos_list}

        line_domain = [("order_id", "in", po_ids)]
        if model_codes:
            line_domain.append(("product_id.default_code", "in", list(model_codes)))

        lines = _x(url, db, uid, ak, "purchase.order.line", "search_read",
                    [line_domain],
                    {"fields": ["order_id", "product_id", "product_qty", "price_unit", "price_subtotal"], "limit": 20000})
        if not lines:
            return _empty

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _x(url, db, uid, ak, "product.product", "search_read",
                       [[("id", "in", prod_ids)]],
                       {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid_raw = line.get("order_id")
            oid = oid_raw[0] if isinstance(oid_raw, list) else oid_raw
            po = po_map.get(oid, {})
            pid_raw = line.get("product_id")
            pid = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
            prod = prod_map.get(pid, {})
            mc = (prod.get("default_code") or "").strip()
            categ_raw = prod.get("categ_id")
            category = categ_raw[1] if isinstance(categ_raw, list) and len(categ_raw) > 1 else ""
            partner_raw = po.get("partner_id")
            vendor = partner_raw[1] if isinstance(partner_raw, list) and len(partner_raw) > 1 else ""
            rows.append({
                C_SYSTEM:        name,
                C_DATE:          str(po.get("date_approve", ""))[:10],
                C_PO:            po.get("name", ""),
                C_VENDOR:        vendor,
                C_PRODUCT:       prod.get("name", ""),
                C_MODEL:         mc,
                C_CATEGORY:      category,
                C_BRAND_CAT:     category,
                C_QTY_PURCHASED: float(line.get("product_qty") or 0),
                C_UNIT_PRICE:    float(line.get("price_unit") or 0),
                C_SUBTOTAL:      float(line.get("price_subtotal") or 0),
                C_STATE:         po.get("state", ""),
            })
        if not rows:
            return _empty
        df = pd.DataFrame(rows)
        df[C_DATE] = pd.to_datetime(df[C_DATE], errors="coerce")
        for c in [C_QTY_PURCHASED, C_UNIT_PRICE, C_SUBTOTAL]:
            df[c] = _to_num(df[c])
        return df.sort_values(C_DATE, ascending=False).reset_index(drop=True)
    except Exception as e:
        return _empty

def fetch_all_systems_purchase_history(model_codes: list, date_from: str, date_to: str) -> pd.DataFrame:
    codes_tuple = tuple(sorted(set(model_codes))) if model_codes else ()
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(fetch_purchase_history_for_system, k, codes_tuple, date_from, date_to)
                for k in SYSTEM_KEYS]
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined[C_DATE] = pd.to_datetime(combined[C_DATE], errors="coerce")
    return combined.sort_values(C_DATE, ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: SALES HISTORY FETCHING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sales_history_for_system(system_key: str, model_codes: tuple, date_from: str, date_to: str) -> pd.DataFrame:
    url, db, uid, ak, name, err = _get_conn(system_key)
    _empty = pd.DataFrame(columns=[C_SYSTEM, C_DATE, C_SO, C_CUSTOMER, C_PRODUCT, C_MODEL,
                                    C_CATEGORY, C_BRAND_CAT, C_QTY, C_UNIT_PRICE, C_SUBTOTAL, C_STATE])
    if err:
        return _empty
    try:
        so_domain = [
            ("date_order", ">=", f"{date_from} 00:00:00"),
            ("date_order", "<=", f"{date_to} 23:59:59"),
            ("state", "in", ["sale", "done"]),
        ]
        orders = _x(url, db, uid, ak, "sale.order", "search_read",
                     [so_domain],
                     {"fields": ["id", "name", "date_order", "partner_id", "state", "order_line"], "limit": 5000})
        if not orders:
            return _empty
        order_map = {o["id"]: o for o in orders}
        line_ids = []
        for o in orders:
            if o.get("order_line"):
                line_ids.extend(o["order_line"])
        if not line_ids:
            return _empty

        line_domain = [("id", "in", line_ids)]
        if model_codes:
            line_domain.append(("product_id.default_code", "in", list(model_codes)))

        lines = _x(url, db, uid, ak, "sale.order.line", "search_read",
                    [line_domain],
                    {"fields": ["order_id", "product_id", "product_uom_qty", "price_unit", "price_subtotal"], "limit": 20000})
        if not lines:
            return _empty

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _x(url, db, uid, ak, "product.product", "search_read",
                       [[("id", "in", prod_ids)]],
                       {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid_raw = line.get("order_id")
            oid = oid_raw[0] if isinstance(oid_raw, list) else oid_raw
            order = order_map.get(oid, {})
            pid_raw = line.get("product_id")
            pid = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
            prod = prod_map.get(pid, {})
            mc = (prod.get("default_code") or "").strip()
            categ_raw = prod.get("categ_id")
            category = categ_raw[1] if isinstance(categ_raw, list) and len(categ_raw) > 1 else ""
            partner_raw = order.get("partner_id")
            customer = partner_raw[1] if isinstance(partner_raw, list) and len(partner_raw) > 1 else ""
            rows.append({
                C_SYSTEM:   name,
                C_DATE:     str(order.get("date_order", ""))[:10],
                C_SO:       order.get("name", ""),
                C_CUSTOMER: customer,
                C_PRODUCT:  prod.get("name", ""),
                C_MODEL:    mc,
                C_CATEGORY: category,
                C_BRAND_CAT: category,
                C_QTY:      float(line.get("product_uom_qty") or 0),
                C_UNIT_PRICE: float(line.get("price_unit") or 0),
                C_SUBTOTAL: float(line.get("price_subtotal") or 0),
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
        return _empty

def fetch_all_systems_sales_history(model_codes: list, date_from: str, date_to: str) -> pd.DataFrame:
    codes_tuple = tuple(sorted(set(model_codes))) if model_codes else ()
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(fetch_sales_history_for_system, k, codes_tuple, date_from, date_to)
                for k in SYSTEM_KEYS]
        for f in as_completed(futs):
            df = f.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined[C_DATE] = pd.to_datetime(combined[C_DATE], errors="coerce")
    return combined.sort_values(C_DATE, ascending=False).reset_index(drop=True)

def fetch_swag_sales_history(model_code: str, date_from: str, date_to: str) -> pd.DataFrame:
    return fetch_sales_history_for_system("SWAG", (model_code,) if model_code else (), date_from, date_to)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11: EXCEL / CSV EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def _style_worksheet(ws, df_clean: pd.DataFrame, lang: str = "EN"):
    """Apply dark-theme styling to an openpyxl worksheet."""
    try:
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.formatting.rule import DataBarRule, ColorScaleRule, CellIsRule
        from openpyxl.styles import Color as OpColor

        header_fill = PatternFill("solid", fgColor="2C3E50")
        alt_fill    = PatternFill("solid", fgColor="1A1E24")
        zero_fill   = PatternFill("solid", fgColor="5C1E1E")
        total_fill  = PatternFill("solid", fgColor="1A3A5C")
        header_font = Font(bold=True, color="FFFFFF", size=10)
        total_font  = Font(bold=True, color="FFFFFF", size=10)
        thin = Border(
            left=Side(style="thin", color="2C3E50"),
            right=Side(style="thin", color="2C3E50"),
            top=Side(style="thin", color="2C3E50"),
            bottom=Side(style="thin", color="2C3E50"),
        )
        if lang == "AR":
            ws.sheet_view.rightToLeft = True

        # Headers
        for col_idx, col_name in enumerate(df_clean.columns, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = col_name
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max(12, min(35, len(str(col_name)) + 4))

        # Data rows
        total_cols = list(df_clean.columns)
        on_hand_col_idx = None
        sale_price_col_idx = None
        if C_ON_HAND in total_cols:
            on_hand_col_idx = total_cols.index(C_ON_HAND) + 1
        if C_SALE_PRICE in total_cols:
            sale_price_col_idx = total_cols.index(C_SALE_PRICE) + 1

        totals = {}
        for row_idx, (_, row) in enumerate(df_clean.iterrows(), 2):
            on_hand_val = 0
            for col_idx, val in enumerate(row.values, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                if isinstance(val, float) and val != val:
                    cell.value = ""
                else:
                    cell.value = val
                if col_idx == on_hand_col_idx:
                    on_hand_val = float(val) if val and val == val else 0
                if row_idx % 2 == 0:
                    cell.fill = alt_fill
                cell.border = thin
                cell.font = Font(color="E0E0E0", size=9)
                cell.alignment = Alignment(horizontal="right" if lang == "AR" else "left", vertical="center")
                # Accumulate totals for numeric cols
                try:
                    numeric_val = float(val)
                    totals[col_idx] = totals.get(col_idx, 0) + numeric_val
                except (TypeError, ValueError):
                    pass
            if on_hand_val == 0:
                for col_idx2 in range(1, len(total_cols) + 1):
                    ws.cell(row=row_idx, column=col_idx2).fill = zero_fill

        # TOTAL row
        total_row = ws.max_row + 1
        ws.cell(row=total_row, column=1).value = "TOTAL"
        ws.cell(row=total_row, column=1).fill = total_fill
        ws.cell(row=total_row, column=1).font = total_font
        for col_idx in range(1, len(total_cols) + 1):
            cell = ws.cell(row=total_row, column=col_idx)
            cell.fill = total_fill
            cell.font = total_font
            cell.border = thin
            if col_idx in totals:
                cell.value = round(totals[col_idx], 2)

        # Freeze & filter
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        # Conditional formatting
        data_range = f"A2:{ws.cell(row=ws.max_row-1, column=len(total_cols)).coordinate}"
        if on_hand_col_idx:
            col_letter = ws.cell(row=2, column=on_hand_col_idx).column_letter
            oh_range = f"{col_letter}2:{col_letter}{ws.max_row - 1}"
            ws.conditional_formatting.add(oh_range, DataBarRule(
                start_type="min", end_type="max",
                color="4472C4", showValue=True,
            ))
            ws.conditional_formatting.add(oh_range, CellIsRule(
                operator="lessThanOrEqual", formula=["3"],
                fill=PatternFill("solid", fgColor="FFE57F"),
            ))
        if sale_price_col_idx:
            sp_letter = ws.cell(row=2, column=sale_price_col_idx).column_letter
            sp_range = f"{sp_letter}2:{sp_letter}{ws.max_row - 1}"
            ws.conditional_formatting.add(sp_range, ColorScaleRule(
                start_type="min", start_color="63BE7B",
                mid_type="percentile", mid_value=50, mid_color="FFEB84",
                end_type="max", end_color="F8696B",
            ))
    except Exception:
        pass  # Styling is best-effort

def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

def to_excel(df: pd.DataFrame) -> bytes:
    if df is None or df.empty:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as w:
            pd.DataFrame({"Message": ["No data"]}).to_excel(w, sheet_name="Data", index=False)
        out.seek(0)
        return out.getvalue()
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Data", index=False)
        ws = w.sheets["Data"]
        _style_worksheet(ws, df, get_lang())
    out.seek(0)
    return out.getvalue()

def to_excel_bulk(dfs_dict: dict) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        for sheet_name, df in dfs_dict.items():
            safe_name = re.sub(r"[:\\/?*\[\]]", "_", str(sheet_name))[:31]
            if df is not None and not df.empty:
                df.to_excel(w, sheet_name=safe_name, index=False)
                ws = w.sheets[safe_name]
                _style_worksheet(ws, df, get_lang())
            else:
                pd.DataFrame({"Message": ["No data"]}).to_excel(w, sheet_name=safe_name, index=False)
    out.seek(0)
    return out.getvalue()

def to_excel_purchase(df: pd.DataFrame) -> bytes:
    return to_excel(df)

def to_excel_sales(df: pd.DataFrame) -> bytes:
    return to_excel(df)

def dl_name(prefix: str, ext: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12: PAGINATION
# ─────────────────────────────────────────────────────────────────────────────
def paginate_df(df: pd.DataFrame, page_key: str, page_size: int = PAGE_SIZE):
    if df is None or df.empty:
        return df, 1, 0
    total = len(df)
    total_pages = max(1, math.ceil(total / page_size))
    current = min(st.session_state.get(page_key, 0), total_pages - 1)
    st.session_state[page_key] = current
    start = current * page_size
    end = min(start + page_size, total)
    page_df = df.iloc[start:end].copy()

    # Render pagination controls
    info_html = (
        f"<div style='text-align:center;margin:6px 0;font-size:0.8rem;color:#8899aa;'>"
        f"{t('Showing','عرض')} {start+1}–{end} {t('of','من')} {total} &nbsp;|&nbsp; "
        f"<span style='background:#1e2d3d;padding:2px 10px;border-radius:12px;'>"
        f"{t('Page','صفحة')} {current+1}/{total_pages}</span></div>"
    )
    st.markdown(info_html, unsafe_allow_html=True)
    c1, c2, _, c3, c4 = st.columns([1, 1, 3, 1, 1])
    if c1.button("⏮", key=f"{page_key}_first", use_container_width=True):
        st.session_state[page_key] = 0; st.rerun()
    if c2.button("◀", key=f"{page_key}_prev", use_container_width=True):
        st.session_state[page_key] = max(0, current - 1); st.rerun()
    if c3.button("▶", key=f"{page_key}_next", use_container_width=True):
        st.session_state[page_key] = min(total_pages - 1, current + 1); st.rerun()
    if c4.button("⏭", key=f"{page_key}_last", use_container_width=True):
        st.session_state[page_key] = total_pages - 1; st.rerun()

    return page_df, total_pages, current

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13: TABLE RENDERING
# ─────────────────────────────────────────────────────────────────────────────
def render_premium_table(df: pd.DataFrame, thresh: int = 0, accent_cols: list = None):
    if df is None or df.empty:
        st.markdown(
            f"<div style='text-align:center;padding:24px;color:#8899aa;'>"
            f"ℹ️ {t('No data to display.','لا توجد بيانات للعرض.')}</div>",
            unsafe_allow_html=True,
        )
        return
    if accent_cols is None:
        accent_cols = []
    is_rtl = get_lang() == "AR"
    dir_attr = 'dir="rtl"' if is_rtl else ''
    text_align = "right" if is_rtl else "left"

    header_html = "".join(
        f"<th style='padding:8px 12px;background:#2C3E50;color:#fff;font-size:0.75rem;"
        f"font-weight:600;text-transform:uppercase;letter-spacing:0.04em;text-align:{text_align};'>{c}</th>"
        for c in df.columns
    )

    rows_html = ""
    on_hand_col = col_label(C_ON_HAND)
    for i, (_, row) in enumerate(df.iterrows()):
        try:
            oh_val = float(row.get(on_hand_col, row.get(C_ON_HAND, 1))) if (on_hand_col in df.columns or C_ON_HAND in df.columns) else 1
        except Exception:
            oh_val = 1
        row_bg = "#5C1E1E" if oh_val == 0 else ("#1A1E24" if i % 2 == 0 else "#151A22")
        cells = ""
        for col_name, val in zip(df.columns, row.values):
            if col_name in accent_cols:
                cell_style = f"color:#4fa3e8;font-weight:700;font-size:0.82rem;text-align:{text_align};"
            else:
                cell_style = f"color:#c8d0dc;font-size:0.82rem;text-align:{text_align};"
            cells += f"<td style='padding:6px 12px;border-bottom:1px solid #1e2d3d;{cell_style}'>{val}</td>"
        rows_html += f"<tr style='background:{row_bg};'>{cells}</tr>"

    table_html = (
        f"<div style='overflow-x:auto;border-radius:10px;border:1px solid #1e2d3d;margin:8px 0;' {dir_attr}>"
        f"<table style='width:100%;border-collapse:collapse;background:#0d1520;'>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

def display_df(df: pd.DataFrame, thresh: int = 0, table_key: str = None):
    if df is None or df.empty:
        render_premium_table(df, thresh)
        return
    key = table_key or f"tbl_{abs(hash(str(df.columns.tolist()))) % 10**8}"
    page_df, _, _ = paginate_df(df, key)
    display = df_for_display(page_df)
    render_premium_table(display, thresh)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 14: UI COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _premium_kpi_card(icon: str, value: str, label: str, trend: str = None) -> str:
    trend_html = ""
    if trend:
        color = "#4ade80" if "+" in trend else "#f87171"
        trend_html = f"<div style='font-size:0.75rem;color:{color};margin-top:4px;'>{trend}</div>"
    return (
        f"<div style='background:rgba(12,16,24,0.8);border:1px solid #1e2d3d;border-radius:16px;"
        f"padding:1.2rem 1rem;text-align:center;border-top:3px solid #3b6fd4;"
        f"transition:all 0.2s;'>"
        f"<div style='font-size:1.8rem;margin-bottom:6px;'>{icon}</div>"
        f"<div style='font-size:1.4rem;font-weight:700;color:#e2e8f0;'>{value}</div>"
        f"<div style='font-size:0.72rem;color:#8899aa;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;'>{label}</div>"
        f"{trend_html}</div>"
    )

def _render_kpi_grid(cards: list):
    n = len(cards)
    cols_count = min(n, 4)
    html = f"<div style='display:grid;grid-template-columns:repeat({cols_count},1fr);gap:1rem;margin:1rem 0;'>"
    html += "".join(cards)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def _section_header(title: str, icon: str, subtitle: str = ""):
    sub = f"<div style='font-size:0.78rem;color:#8899aa;margin-top:2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"<div style='margin:1.5rem 0 0.8rem;'>"
        f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
        f"<span style='font-size:1.3rem;'>{icon}</span>"
        f"<span style='font-size:1rem;font-weight:700;color:#c8d0dc;'>{title}</span>"
        f"</div>{sub}</div>",
        unsafe_allow_html=True,
    )

def _chart_card_open(title: str, icon: str):
    st.markdown(
        f"<div style='background:rgba(8,11,18,0.8);border:1px solid #1e2d3d;border-radius:14px;"
        f"padding:1rem 1.2rem;margin:0.5rem 0;'>"
        f"<div style='font-size:0.85rem;font-weight:600;color:#a0b0c8;margin-bottom:0.8rem;'>"
        f"{icon} {title}</div>",
        unsafe_allow_html=True,
    )

def _chart_card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def _divider():
    st.markdown(
        "<hr style='border:none;border-top:1px solid;border-image:linear-gradient(to right,transparent,#3b6fd4,transparent) 1;margin:1.5rem 0;'>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15: CHART HELPERS (Altair + Plotly)
# ─────────────────────────────────────────────────────────────────────────────
_PLOTLY_COLORS = ["#3b6fd4", "#4ade80", "#f59e0b", "#f87171", "#a78bfa", "#34d399", "#fb923c", "#60a5fa"]

def _apply_plotly_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8d0dc", family="Inter, sans-serif", size=11),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2d3d"),
        title_font=dict(size=13, color="#a0b0c8"),
    )
    fig.update_xaxes(gridcolor="#1e2d3d", linecolor="#1e2d3d", tickfont=dict(size=10))
    fig.update_yaxes(gridcolor="#1e2d3d", linecolor="#1e2d3d", tickfont=dict(size=10))
    return fig

def _alt_bar_chart(df, x, y, color, title, tooltip):
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(x, sort="-y"),
            y=alt.Y(y),
            color=alt.Color(color, scale=alt.Scale(scheme="blues")),
            tooltip=tooltip,
        )
        .properties(title=title, height=300)
        .configure_axis(gridColor="#1e2d3d", domainColor="#1e2d3d", labelColor="#8899aa", titleColor="#a0b0c8")
        .configure_title(color="#c8d0dc")
        .configure_view(strokeOpacity=0)
    )
    return chart

def _alt_line_chart(df, x, y, color, title, tooltip):
    chart = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X(x),
            y=alt.Y(y),
            color=alt.Color(color, scale=alt.Scale(scheme="blues")),
            tooltip=tooltip,
        )
        .properties(title=title, height=300)
        .configure_axis(gridColor="#1e2d3d", domainColor="#1e2d3d", labelColor="#8899aa", titleColor="#a0b0c8")
        .configure_title(color="#c8d0dc")
        .configure_view(strokeOpacity=0)
    )
    return chart

def _top10_altair(df: pd.DataFrame, col_name: str, val_col: str, title: str, color: str = "#3b6fd4"):
    if df is None or df.empty or col_name not in df.columns or val_col not in df.columns:
        return None
    agg = df.groupby(col_name)[val_col].sum().reset_index().nlargest(10, val_col)
    agg[col_name] = agg[col_name].astype(str).str[:28]
    chart = (
        alt.Chart(agg)
        .mark_bar(color=color, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(val_col, title=val_col),
            y=alt.Y(col_name, sort="-x", title=""),
            tooltip=[col_name, val_col],
        )
        .properties(title=title, height=300)
        .configure_axis(gridColor="#1e2d3d", domainColor="#1e2d3d", labelColor="#8899aa")
        .configure_title(color="#c8d0dc")
        .configure_view(strokeOpacity=0)
    )
    return chart

def _plotly_donut(df: pd.DataFrame, names_col: str, values_col: str, title: str, colors: list = None):
    if df is None or df.empty:
        return None
    if colors is None:
        colors = _PLOTLY_COLORS
    fig = px.pie(df, names=names_col, values=values_col, hole=0.55, title=title,
                 color_discrete_sequence=colors)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply_plotly_theme(fig)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 16: DARK THEME CSS
# ─────────────────────────────────────────────────────────────────────────────
def _build_css() -> str:
    is_rtl = get_lang() == "AR"
    body_dir = "rtl" if is_rtl else "ltr"
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {{ font-family: 'Inter', sans-serif; box-sizing: border-box; }}
html, body {{ direction: {body_dir}; }}

/* ── Global background ── */
.stApp {{
    background: radial-gradient(ellipse at 20% 0%, rgba(30,60,120,0.18) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 100%, rgba(20,100,80,0.12) 0%, transparent 60%),
                #05070d;
    color: #c8d0dc;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #080b12 0%, #0d1117 100%) !important;
    border-right: 1px solid #1e2d3d !important;
}}
section[data-testid="stSidebar"] * {{ color: #c8d0dc !important; }}
section[data-testid="stSidebar"] .stSelectbox > div > div {{ background: #111827 !important; border-color: #1e2d3d !important; }}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: #0d1117 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.875rem !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: #3b6fd4 !important;
    box-shadow: 0 0 0 2px rgba(59,111,212,0.15) !important;
}}
label {{ color: #8899aa !important; font-size: 0.8rem !important; font-weight: 500 !important; }}

/* ── Buttons ── */
.stButton > button {{
    border-radius: 8px !important;
    border: 1px solid #1e2d3d !important;
    background: rgba(14,20,30,0.9) !important;
    color: #c8d0dc !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: #1e2d3d !important;
    border-color: #3b6fd4 !important;
    transform: translateY(-1px);
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #1e3a8a 0%, #3b6fd4 100%) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(59,111,212,0.3) !important;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 8px 20px rgba(59,111,212,0.5) !important;
    transform: translateY(-2px);
}}
.stDownloadButton > button {{
    background: rgba(14,20,30,0.9) !important;
    border: 1px solid #1e2d3d !important;
    color: #c8d0dc !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
}}
.stDownloadButton > button:hover {{
    background: linear-gradient(135deg, #1e3a8a 0%, #3b6fd4 100%) !important;
    color: #fff !important;
    border-color: transparent !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent;
    border-bottom: 1px solid #1e2d3d;
    gap: 2px;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: #8899aa !important;
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}}
.stTabs [aria-selected="true"] {{
    color: #4fa3e8 !important;
    border-bottom: 3px solid #3b6fd4 !important;
    font-weight: 600 !important;
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background: rgba(12,16,24,0.8);
    border: 1px solid #1e2d3d;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    transition: all 0.2s;
}}
[data-testid="stMetric"]:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
[data-testid="stMetricLabel"] {{ color: #8899aa !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.04em; }}
[data-testid="stMetricValue"] {{ font-size: 1.5rem !important; font-weight: 700 !important; color: #e2e8f0 !important; }}

/* ── Selectbox / Multiselect ── */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {{
    background: #0d1117 !important;
    border-color: #1e2d3d !important;
    color: #c8d0dc !important;
    border-radius: 8px !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background: rgba(14,20,30,0.8) !important;
    border-radius: 8px !important;
    color: #c8d0dc !important;
    border: 1px solid #1e2d3d !important;
}}

/* ── Slider ── */
.stSlider [data-testid="stThumb"] {{ background: #3b6fd4 !important; }}
.stSlider [data-testid="stTrack"] > div:first-child {{ background: #3b6fd4 !important; }}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {{
    background: rgba(14,20,30,0.5) !important;
    border: 2px dashed #1e2d3d !important;
    border-radius: 12px !important;
    color: #8899aa !important;
}}
[data-testid="stFileUploadDropzone"]:hover {{ border-color: #3b6fd4 !important; }}

/* ── Checkbox ── */
.stCheckbox [data-testid="stWidgetLabel"] {{ color: #c8d0dc !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: #0d1117; }}
::-webkit-scrollbar-thumb {{ background: #1e2d3d; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #3b6fd4; }}

/* ── Animations ── */
@keyframes fadeInUp {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
@keyframes fadeInLeft {{ from {{ opacity:0; transform:translateX(-20px); }} to {{ opacity:1; transform:translateX(0); }} }}
@keyframes shimmer {{ 0% {{ background-position:-200% 0; }} 100% {{ background-position:200% 0; }} }}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.6; }} }}
@keyframes glow {{ 0%,100% {{ box-shadow:0 0 10px rgba(59,111,212,0.3); }} 50% {{ box-shadow:0 0 25px rgba(59,111,212,0.7); }} }}
@keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-6px); }} }}

/* ── Hero banner ── */
.hero-banner {{
    background: linear-gradient(135deg, rgba(30,58,138,0.6) 0%, rgba(15,23,42,0.9) 100%);
    border: 1px solid #1e2d3d;
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    animation: fadeInUp 0.5s ease;
}}

/* ── System badge ── */
.sys-badge {{
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em;
    border: 1px solid transparent;
}}
.sys-badge-ok {{ background: rgba(74,222,128,0.15); border-color: rgba(74,222,128,0.4); color: #4ade80; }}
.sys-badge-err {{ background: rgba(248,113,113,0.15); border-color: rgba(248,113,113,0.4); color: #f87171; }}
.sys-badge-off {{ background: rgba(100,116,139,0.15); border-color: rgba(100,116,139,0.4); color: #64748b; }}

/* ── Mobile ── */
@media (max-width: 768px) {{
    .hero-banner {{ padding: 1.2rem; }}
    [data-testid="stMetricValue"] {{ font-size: 1.1rem !important; }}
}}

/* ── RTL ── */
{"[dir='rtl'] table th, [dir='rtl'] table td { text-align: right; }" if is_rtl else ""}

footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 17: LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown(_build_css(), unsafe_allow_html=True)
    # Left hero + right form layout using columns
    left, right = st.columns([1, 1])

    with left:
        st.markdown(f"""
        <div class="hero-banner" style="min-height:500px;display:flex;flex-direction:column;justify-content:center;animation:fadeInLeft 0.6s ease;">
            <div style="font-size:3.5rem;margin-bottom:1rem;animation:float 3s ease-in-out infinite;">👑</div>
            <div style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#60a5fa,#34d399);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.5rem;">
                SWAG Dashboard
            </div>
            <div style="color:#8899aa;font-size:0.9rem;margin-bottom:2rem;">
                {t('Product Comparison & Analytics v29','مقارنة المنتجات والتحليلات v29')}
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:1.5rem;">
                {"".join(f"<span style='background:rgba(59,111,212,0.15);border:1px solid rgba(59,111,212,0.3);border-radius:20px;padding:4px 12px;font-size:0.72rem;color:#60a5fa;'>{chip}</span>"
                  for chip in [t("Multi-System","متعدد الأنظمة"),t("Real-time","فوري"),t("Bilingual","ثنائي اللغة"),t("PDF Import","استيراد PDF"),t("Purchase Analytics","تحليل المشتريات"),t("Sales Analytics","تحليل المبيعات")])}
            </div>
            <div style="border-top:1px solid #1e2d3d;padding-top:1rem;margin-top:1rem;">
                <div style="font-size:0.75rem;color:#8899aa;margin-bottom:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">
                    {t('Connected Systems','الأنظمة المتصلة')}
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:8px;">
                    {"".join(f"<span class='sys-badge sys-badge-{'ok' if st.secrets.get(k,{}).get('url') else 'off'}'>"
                             f"{'●' if st.secrets.get(k,{}).get('url') else '○'} {st.secrets.get(k,{}).get('name',k)}</span>"
                             for k in SYSTEM_KEYS)}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div style="min-height:500px;display:flex;flex-direction:column;justify-content:center;
                    animation:fadeInUp 0.6s ease;">
            <div style="max-width:380px;margin:0 auto;width:100%;
                        background:rgba(12,16,24,0.85);border:1px solid #1e2d3d;
                        border-radius:20px;padding:2.5rem;">
                <div style="font-size:1.6rem;font-weight:700;color:#e2e8f0;margin-bottom:0.4rem;">
                    {t('Sign In','تسجيل الدخول')}
                </div>
                <div style="color:#8899aa;font-size:0.85rem;margin-bottom:1.8rem;">
                    {t('Access your executive dashboard','الوصول إلى لوحة التحكم التنفيذية')}
                </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("_login_err"):
            st.markdown(f"<div style='background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.4);border-radius:8px;padding:10px 14px;color:#f87171;font-size:0.82rem;margin-bottom:1rem;'>❌ {st.session_state._login_err}</div>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(t("Email", "البريد الإلكتروني"), placeholder="user@company.com")
            password = st.text_input(t("Password", "كلمة المرور"), type="password")
            submitted = st.form_submit_button(f"🚀 {t('Sign In','تسجيل الدخول')}", type="primary", use_container_width=True)
            if submitted:
                if not email.strip() or not password:
                    st.session_state._login_err = t("Please enter email and password.", "يرجى إدخال البريد الإلكتروني وكلمة المرور.")
                    st.rerun()
                else:
                    with st.spinner(t("Authenticating…", "جاري التحقق…")):
                        ok, err_msg = _attempt_login(email.strip(), password)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.user_email = email.strip()
                        st.session_state._login_err = ""
                        try:
                            st.query_params.update({"u": email.strip(), "t": _make_token(email.strip())})
                        except Exception:
                            pass
                        st.balloons()
                        st.rerun()
                    else:
                        st.session_state._login_err = err_msg
                        st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)

def _attempt_login(email: str, password: str):
    candidates = []
    if "LOGIN" in st.secrets:
        candidates.append(("LOGIN", st.secrets["LOGIN"]))
    for k in SYSTEM_KEYS:
        cfg = st.secrets.get(k, {})
        if cfg.get("url") and cfg.get("db"):
            candidates.append((k, cfg))
    if not candidates:
        return False, t("No Odoo connections configured.", "لا توجد اتصالات Odoo مُكوَّنة.")
    last_err = ""
    for src, cfg in candidates:
        url = cfg.get("url", "").rstrip("/")
        db = cfg.get("db", "")
        if not url or not db:
            continue
        try:
            proxy = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid = proxy.authenticate(db, email, password, {})
            if uid and isinstance(uid, int) and uid > 0:
                return True, ""
            last_err = t(f"Login failed on {db}.", f"فشل تسجيل الدخول على {db}.")
        except Exception as e:
            last_err = f"[{src}] {type(e).__name__}: {e}"
    return False, last_err

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 18: SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def _render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown(f"""
        <div style="padding:1.2rem 0.5rem 1rem;border-bottom:1px solid #1e2d3d;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:0.7rem;">
                <span style="font-size:2rem;animation:glow 2s ease-in-out infinite;">👑</span>
                <div>
                    <div style="font-size:1rem;font-weight:700;background:linear-gradient(135deg,#60a5fa,#34d399);
                                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                        SWAG v29
                    </div>
                    <div style="font-size:0.68rem;color:#4a6080;">Product Dashboard</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User card
        email = st.session_state.get("user_email", "")
        avatar_letter = email[0].upper() if email else "U"
        st.markdown(f"""
        <div style="background:rgba(14,20,30,0.8);border:1px solid #1e2d3d;border-radius:10px;
                    padding:0.7rem 0.9rem;margin-bottom:1rem;display:flex;align-items:center;gap:0.7rem;">
            <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#1e3a8a,#3b6fd4);
                        display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;color:#fff;">
                {avatar_letter}
            </div>
            <div style="overflow:hidden;">
                <div style="font-size:0.78rem;color:#c8d0dc;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {email}
                </div>
                <div style="font-size:0.65rem;color:#4ade80;">● {t('Online','متصل')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown(f"<div style='font-size:0.7rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;'>{t('Navigation','التنقل')}</div>", unsafe_allow_html=True)
        nav_options = {
            "stock":    f"📊 {t('Stock Comparison','مقارنة المخزون')}",
            "purchase": f"🛒 {t('Purchase Analytics','تحليل المشتريات')}",
            "sales":    f"📈 {t('Sales Analytics','تحليل المبيعات')}",
        }
        current_view = st.session_state.get("analytics_view", "stock")
        for key, label in nav_options.items():
            active = current_view == key
            btn_style = "primary" if active else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_style if active else "secondary"):
                st.session_state.analytics_view = key
                st.rerun()

        st.markdown("<hr style='border-color:#1e2d3d;margin:0.8rem 0;'>", unsafe_allow_html=True)

        # Filters
        st.markdown(f"<div style='font-size:0.7rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;'>{t('Search Settings','إعدادات البحث')}</div>", unsafe_allow_html=True)
        st.session_state.low_stock_thresh = st.slider(
            t("Low Stock Threshold", "حد المخزون المنخفض"),
            min_value=0, max_value=50, value=st.session_state.low_stock_thresh,
        )
        st.session_state.search_exact = st.checkbox(
            t("Exact Match", "تطابق تام"), value=st.session_state.search_exact,
        )
        st.session_state.show_transfers = st.checkbox(
            t("Show Transfers", "عرض التحويلات"), value=st.session_state.show_transfers,
        )
        st.session_state.show_reorder = st.checkbox(
            t("Show Reorder", "عرض قائمة الطلب"), value=st.session_state.show_reorder,
        )

        # Reorder settings
        with st.expander(f"⚙️ {t('Reorder Settings','إعدادات إعادة الطلب')}"):
            st.session_state.reorder_mode = st.selectbox(
                t("Mode", "النمط"),
                ["days_cover", "reorder_point"],
                index=0 if st.session_state.reorder_mode == "days_cover" else 1,
            )
            st.session_state.reorder_target_days = st.number_input(
                t("Target Days Cover", "أيام التغطية المستهدفة"), min_value=1, max_value=365,
                value=st.session_state.reorder_target_days,
            )
            st.session_state.reorder_max_level = st.number_input(
                t("Max Level", "الحد الأقصى"), min_value=0, value=st.session_state.reorder_max_level,
            )
            st.session_state.reorder_point = st.number_input(
                t("Reorder Point", "نقطة إعادة الطلب"), min_value=0, value=st.session_state.reorder_point,
            )

        st.markdown("<hr style='border-color:#1e2d3d;margin:0.8rem 0;'>", unsafe_allow_html=True)

        # System status
        st.markdown(f"<div style='font-size:0.7rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;'>{t('System Status','حالة الأنظمة')}</div>", unsafe_allow_html=True)
        sys_stats = st.session_state.get("sys_stats", {})
        for k in SYSTEM_KEYS:
            cfg = st.secrets.get(k, {})
            name = cfg.get("name_ar" if get_lang() == "AR" else "name", k)
            stat = sys_stats.get(k, {})
            level = stat.get("level", "off") if stat else ("ok" if cfg.get("url") else "off")
            icon = "✅" if level == "ok" else ("❌" if level == "error" else "⚫")
            cls = "ok" if level == "ok" else ("err" if level == "error" else "off")
            st.markdown(f"<span class='sys-badge sys-badge-{cls}'>{icon} {name}</span><br>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1e2d3d;margin:0.8rem 0;'>", unsafe_allow_html=True)

        # Language toggle
        lang_options = ["EN", "AR"]
        new_lang = st.radio(f"🌐 {t('Language','اللغة')}", lang_options,
                            index=lang_options.index(get_lang()), horizontal=True)
        if new_lang != get_lang():
            st.session_state.lang = new_lang
            st.rerun()

        # Logout
        if st.button(f"🚪 {t('Logout','تسجيل الخروج')}", use_container_width=True):
            do_logout()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 19: STOCK COMPARISON VIEW (main tab)
# ─────────────────────────────────────────────────────────────────────────────
def show_stock_comparison():
    # ── Hero banner ────────────────────────────────────────────────────────────
    total_df = st.session_state.get("total_df")
    branch_df = st.session_state.get("branch_df")
    sys_stats = st.session_state.get("sys_stats", {})
    systems_online = sum(1 for v in sys_stats.values() if v.get("level") == "ok")
    total_units = int(_to_num(total_df[C_ON_HAND]).sum()) if total_df is not None and not total_df.empty and C_ON_HAND in total_df.columns else 0
    models_found = total_df[C_MODEL].nunique() if total_df is not None and not total_df.empty else 0

    sys_badges = "".join(
        f"<span class='sys-badge sys-badge-{'ok' if v.get('level')=='ok' else 'err'}'>"
        f"{'✅' if v.get('level')=='ok' else '❌'} {v.get('system', k)}</span> "
        for k, v in sys_stats.items()
    ) if sys_stats else "<span style='color:#8899aa;font-size:0.8rem;'>—</span>"

    st.markdown(f"""
    <div class="hero-banner">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
            <div>
                <div style="font-size:1.4rem;font-weight:700;color:#e2e8f0;margin-bottom:0.3rem;">
                    📊 {t('Stock Comparison Dashboard','لوحة مقارنة المخزون')}
                </div>
                <div style="color:#8899aa;font-size:0.82rem;margin-bottom:0.8rem;">
                    {t('Multi-system inventory analysis across all branches','تحليل المخزون متعدد الأنظمة عبر جميع الفروع')}
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">{sys_badges}</div>
            </div>
            <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
                <div style="text-align:center;">
                    <div style="font-size:1.6rem;font-weight:700;color:#60a5fa;">{total_units:,}</div>
                    <div style="font-size:0.7rem;color:#8899aa;text-transform:uppercase;">{t('Total Units','إجمالي الوحدات')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:1.6rem;font-weight:700;color:#34d399;">{models_found:,}</div>
                    <div style="font-size:0.7rem;color:#8899aa;text-transform:uppercase;">{t('Models Found','الموديلات')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:1.6rem;font-weight:700;color:#f59e0b;">{systems_online}/4</div>
                    <div style="font-size:0.7rem;color:#8899aa;text-transform:uppercase;">{t('Systems Online','أنظمة متصلة')}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PDF Upload ─────────────────────────────────────────────────────────────
    _section_header(t("Import Product Codes", "استيراد رموز المنتجات"), "📄",
                    t("Upload a PDF invoice to extract model codes automatically", "ارفع فاتورة PDF لاستخراج رموز الموديلات تلقائياً"))

    with st.expander(t("📄 PDF Invoice Upload", "📄 رفع فاتورة PDF"), expanded=st.session_state.get("pdf_mode", False)):
        uploaded = st.file_uploader(t("Upload PDF Invoice", "رفع فاتورة PDF"), type=["pdf"], key="pdf_uploader")
        if uploaded:
            with st.spinner(t("Parsing invoice…", "جاري تحليل الفاتورة…")):
                raw = parse_invoice_pdf_cached(uploaded.read())
            base_models = get_unique_base_models(raw)
            if base_models:
                st.success(t(f"Found {len(base_models)} unique base models.", f"تم العثور على {len(base_models)} موديل فريد."))
                st.session_state.pdf_codes = base_models
                st.session_state.pdf_mode = True
                with st.expander(t("Preview Extracted Codes", "معاينة الرموز المستخرجة")):
                    st.code(", ".join(base_models))
            else:
                st.warning(t("No model codes found in PDF.", "لم يتم العثور على رموز موديلات في PDF."))
        if st.session_state.get("pdf_codes"):
            st.markdown(f"<div style='color:#4ade80;font-size:0.82rem;'>✅ {len(st.session_state.pdf_codes)} {t('codes loaded from PDF','رمز محمل من PDF')}</div>", unsafe_allow_html=True)
            if st.button(t("Clear PDF Codes", "مسح رموز PDF"), key="clear_pdf"):
                st.session_state.pdf_codes = []
                st.session_state.pdf_mode = False
                st.rerun()

    # ── Manual code input ──────────────────────────────────────────────────────
    _section_header(t("Search Products", "بحث المنتجات"), "🔍")
    pdf_pre = ", ".join(st.session_state.get("pdf_codes", []))
    code_input = st.text_area(
        t("Enter model codes (comma or newline separated)", "أدخل رموز الموديلات (مفصولة بفاصلة أو سطر جديد)"),
        value=pdf_pre,
        height=80,
        placeholder="e.g. ABC-001, DEF-002, GHI-003",
        key="code_input_area",
    )

    col_btn, col_opt = st.columns([2, 1])
    with col_btn:
        search_clicked = st.button(
            f"🔍 {t('Search All Systems','البحث في جميع الأنظمة')}",
            type="primary", use_container_width=True, key="search_btn",
        )
    with col_opt:
        st.session_state.search_exact = st.checkbox(
            t("Exact Match", "تطابق تام"), value=st.session_state.search_exact, key="exact_cb"
        )

    if search_clicked:
        raw_codes = [c.strip().upper() for c in re.split(r"[,\n;]+", code_input) if c.strip()]
        codes = list(dict.fromkeys(raw_codes))  # dedupe preserving order
        with st.spinner(t("Fetching data from all systems…", "جاري جلب البيانات من جميع الأنظمة…")):
            total_df, branch_df, transfers_df, reorder_df, sys_stats = fetch_all_data(
                codes, st.session_state.search_exact, st.session_state.low_stock_thresh,
                st.session_state.show_transfers, st.session_state.show_reorder,
                st.session_state.reorder_mode, st.session_state.reorder_target_days,
                st.session_state.reorder_max_level, st.session_state.reorder_point,
            )
        st.session_state.total_df = total_df
        st.session_state.branch_df = branch_df
        st.session_state.transfers_df = transfers_df
        st.session_state.reorder_df = reorder_df
        st.session_state.sys_stats = sys_stats
        st.session_state.last_run = datetime.now()
        # Build price history from total_df
        if total_df is not None and not total_df.empty:
            price_history = {}
            for _, row in total_df.iterrows():
                mc = row.get(C_MODEL, "")
                sys = row.get(C_SYSTEM, "")
                price = float(row.get(C_SALE_PRICE, 0) or 0)
                if mc and sys:
                    if mc not in price_history:
                        price_history[mc] = {}
                    price_history[mc][sys] = price
            st.session_state.price_history = price_history
        # Reset page counters
        for pk in ["page_total", "page_branch", "page_transfers", "page_reorder"]:
            st.session_state[pk] = 0
        st.rerun()

    # ── Results ────────────────────────────────────────────────────────────────
    total_df = st.session_state.get("total_df")
    if total_df is None or total_df.empty:
        if st.session_state.get("last_run") is not None:
            st.markdown(f"<div style='text-align:center;padding:2rem;color:#8899aa;'>ℹ️ {t('No data returned. Check your codes or system connections.','لا توجد بيانات. تحقق من الرموز أو اتصالات الأنظمة.')}</div>", unsafe_allow_html=True)
        return

    _divider()
    branch_df = st.session_state.get("branch_df")
    transfers_df = st.session_state.get("transfers_df")
    reorder_df = st.session_state.get("reorder_df")

    # ── KPI row ────────────────────────────────────────────────────────────────
    total_qty = int(_to_num(total_df[C_ON_HAND]).sum())
    total_val = (_to_num(total_df[C_ON_HAND]) * _to_num(total_df[C_SALE_PRICE])).sum()
    zero_cnt = int((_to_num(total_df[C_ON_HAND]) == 0).sum())
    low_cnt  = int(((_to_num(total_df[C_ON_HAND]) > 0) & (_to_num(total_df[C_ON_HAND]) <= st.session_state.low_stock_thresh)).sum())
    systems_list = total_df[C_SYSTEM].unique().tolist() if C_SYSTEM in total_df.columns else []

    _render_kpi_grid([
        _premium_kpi_card("📦", f"{total_qty:,}", t("Total On Hand","إجمالي المتوفر")),
        _premium_kpi_card("💰", f"SAR {total_val:,.0f}", t("Stock Value","قيمة المخزون")),
        _premium_kpi_card("🔴", f"{zero_cnt:,}", t("Zero Stock","صفر مخزون")),
        _premium_kpi_card("⚠️", f"{low_cnt:,}", t("Low Stock","مخزون منخفض")),
    ])

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_labels = [
        f"📊 {t('Total Stock','إجمالي المخزون')}",
        f"🏪 {t('Branch Stock','مخزون الفروع')}",
    ]
    if st.session_state.show_transfers:
        tab_labels.append(f"🔄 {t('Transfers','التحويلات')}")
    if st.session_state.show_reorder:
        tab_labels.append(f"🔔 {t('Reorder','قائمة الطلب')}")

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    # Total Stock tab
    with tabs[tab_idx]:
        tab_idx += 1
        _section_header(t("Total Stock Across All Systems","إجمالي المخزون عبر جميع الأنظمة"), "📊")
        c1, c2 = st.columns(2)
        with c1:
            chart = _top10_altair(total_df, C_MODEL, C_ON_HAND, t("Top 10 Models by Qty","أعلى 10 موديلات بالكمية"))
            if chart:
                st.altair_chart(chart, use_container_width=True)
        with c2:
            if C_SYSTEM in total_df.columns and C_ON_HAND in total_df.columns:
                sys_agg = total_df.groupby(C_SYSTEM)[C_ON_HAND].sum().reset_index()
                fig = _plotly_donut(sys_agg, C_SYSTEM, C_ON_HAND, t("Stock by System","المخزون حسب النظام"))
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        display_df(total_df, st.session_state.low_stock_thresh, "total_main")
        ec1, ec2 = st.columns(2)
        with ec1:
            st.download_button(f"⬇️ {t('Export CSV','تصدير CSV')}", to_csv(df_for_display(total_df)), dl_name("total_stock", "csv"), "text/csv")
        with ec2:
            st.download_button(f"⬇️ {t('Export Excel','تصدير Excel')}", to_excel(df_for_display(total_df)), dl_name("total_stock", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Price history chart
        price_history = st.session_state.get("price_history", {})
        if price_history:
            _section_header(t("Price Comparison by System","مقارنة الأسعار حسب النظام"), "💰")
            price_rows = []
            for mc, sys_prices in price_history.items():
                for sys, price in sys_prices.items():
                    price_rows.append({C_MODEL: mc, C_SYSTEM: sys, C_SALE_PRICE: price})
            if price_rows:
                price_df = pd.DataFrame(price_rows)
                if not price_df.empty:
                    try:
                        chart_p = (
                            alt.Chart(price_df)
                            .mark_line(point=True, strokeWidth=2)
                            .encode(
                                x=alt.X(C_MODEL, title=col_label(C_MODEL)),
                                y=alt.Y(C_SALE_PRICE, title=col_label(C_SALE_PRICE)),
                                color=alt.Color(C_SYSTEM, scale=alt.Scale(scheme="tableau10")),
                                tooltip=[C_MODEL, C_SYSTEM, C_SALE_PRICE],
                            )
                            .properties(height=280)
                            .configure_axis(gridColor="#1e2d3d", domainColor="#1e2d3d", labelColor="#8899aa")
                            .configure_view(strokeOpacity=0)
                        )
                        st.altair_chart(chart_p, use_container_width=True)
                    except Exception:
                        pass

    # Branch Stock tab
    with tabs[tab_idx]:
        tab_idx += 1
        _section_header(t("Stock by Branch","المخزون حسب الفرع"), "🏪")
        if branch_df is None or branch_df.empty:
            st.info(t("No branch data available.", "لا توجد بيانات فروع."))
        else:
            br_agg = branch_df.groupby(C_BRANCH)[C_ON_HAND].sum().reset_index().nlargest(15, C_ON_HAND)
            fig_br = px.bar(br_agg, x=C_BRANCH, y=C_ON_HAND,
                            title=t("On Hand by Branch","المتوفر حسب الفرع"),
                            color=C_ON_HAND, color_continuous_scale=["#1e3a8a", "#3b6fd4", "#60a5fa"],
                            template="plotly_dark")
            st.plotly_chart(_apply_plotly_theme(fig_br), use_container_width=True)
            display_df(branch_df, st.session_state.low_stock_thresh, "branch_main")
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                st.download_button(f"⬇️ {t('CSV','CSV')}", to_csv(df_for_display(branch_df)), dl_name("branch_stock", "csv"), "text/csv")
            with bc2:
                st.download_button(f"⬇️ {t('Excel','Excel')}", to_excel(df_for_display(branch_df)), dl_name("branch_stock", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with bc3:
                # Branch matrix
                try:
                    pivot = branch_df.pivot_table(index=C_MODEL, columns=C_BRANCH, values=C_ON_HAND, aggfunc="sum", fill_value=0)
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine="openpyxl") as w:
                        pivot.to_excel(w, sheet_name="Branch_Matrix")
                    out.seek(0)
                    st.download_button(f"📊 {t('Branch Matrix','مصفوفة الفروع')}", out, dl_name("branch_matrix", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception:
                    pass

    # Transfers tab
    if st.session_state.show_transfers and tab_idx < len(tabs):
        with tabs[tab_idx]:
            tab_idx += 1
            _section_header(t("Internal Transfers","التحويلات الداخلية"), "🔄")
            if transfers_df is None or transfers_df.empty:
                st.info(t("No pending transfers found.", "لا توجد تحويلات معلقة."))
            else:
                tf_total = int(_to_num(transfers_df[C_QTY]).sum()) if C_QTY in transfers_df.columns else 0
                tf_count = len(transfers_df)
                _render_kpi_grid([
                    _premium_kpi_card("🔄", f"{tf_count:,}", t("Transfer Lines","سطور التحويل")),
                    _premium_kpi_card("📦", f"{tf_total:,}", t("Total Qty Moving","الكمية المتحركة")),
                ])
                display_df(transfers_df, 0, "transfers_main")
                st.download_button(f"⬇️ {t('Export CSV','تصدير CSV')}", to_csv(df_for_display(transfers_df)), dl_name("transfers", "csv"), "text/csv")

    # Reorder tab
    if st.session_state.show_reorder and tab_idx < len(tabs):
        with tabs[tab_idx]:
            _section_header(t("Reorder Suggestions","اقتراحات إعادة الطلب"), "🔔")
            if reorder_df is None or reorder_df.empty:
                st.success(t("✅ No reorder needed based on current thresholds.", "✅ لا حاجة لإعادة الطلب بناءً على الحدود الحالية."))
            else:
                crit_cnt = len(reorder_df[reorder_df[C_PRIORITY].str.contains("Critical", na=False)]) if C_PRIORITY in reorder_df.columns else 0
                _render_kpi_grid([
                    _premium_kpi_card("🔔", f"{len(reorder_df):,}", t("Items to Reorder","عناصر للطلب")),
                    _premium_kpi_card("🔴", f"{crit_cnt:,}", t("Critical Priority","أولوية حرجة")),
                ])
                if C_PRIORITY in reorder_df.columns:
                    crit_df = reorder_df[reorder_df[C_PRIORITY].str.contains("Critical", na=False)]
                    if not crit_df.empty:
                        st.markdown(f"<div style='color:#f87171;font-size:0.82rem;font-weight:600;margin-bottom:8px;'>🔴 {t('Critical Items — Action Required','عناصر حرجة — إجراء مطلوب')}</div>", unsafe_allow_html=True)
                        display_df(crit_df, 0, "reorder_crit")
                display_df(reorder_df, 0, "reorder_main")
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.download_button(f"⬇️ {t('Export CSV','تصدير CSV')}", to_csv(df_for_display(reorder_df)), dl_name("reorder", "csv"), "text/csv")
                with rc2:
                    st.download_button(f"⬇️ {t('Export Excel','تصدير Excel')}", to_excel(df_for_display(reorder_df)), dl_name("reorder", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 20: PURCHASE ANALYTICS VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_purchase_analytics():
    # Hero
    st.markdown(f"""
    <div class="hero-banner">
        <div style="font-size:1.4rem;font-weight:700;color:#e2e8f0;margin-bottom:0.3rem;">
            🛒 {t('Purchase Analytics','تحليل المشتريات')}
        </div>
        <div style="color:#8899aa;font-size:0.82rem;">
            {t('Multi-system purchase order analysis','تحليل أوامر الشراء متعدد الأنظمة')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    _section_header(t("Filters","الفلاتر"), "⚙️")
    col_d1, col_d2, col_mc = st.columns([1, 1, 2])
    with col_d1:
        date_from = st.date_input(t("From Date","من تاريخ"), value=datetime.now() - timedelta(days=30), key="po_from")
    with col_d2:
        date_to = st.date_input(t("To Date","إلى تاريخ"), value=datetime.now(), key="po_to")
    with col_mc:
        mc_input = st.text_input(t("Model Code Filter (optional)","فلتر رمز الموديل (اختياري)"), placeholder="e.g. ABC-001, DEF", key="po_mc_filter")

    if st.button(f"🔍 {t('Fetch Purchase Data','جلب بيانات المشتريات')}", type="primary", key="po_fetch"):
        mc_list = [c.strip().upper() for c in re.split(r"[,\n;]+", mc_input) if c.strip()] if mc_input.strip() else []
        with st.spinner(t("Fetching purchase history from all systems…","جاري جلب سجل المشتريات…")):
            po_df = fetch_all_systems_purchase_history(mc_list, str(date_from), str(date_to))
        st.session_state.po_analytics_df = po_df
        st.session_state.page_po = 0
        st.rerun()

    po_df = st.session_state.get("po_analytics_df")
    if po_df is None or po_df.empty:
        if st.session_state.po_analytics_df is not None:
            st.info(t("No purchase data found for the selected filters.","لا توجد بيانات مشتريات للفلاتر المحددة."))
        return

    _divider()

    # KPIs
    total_spend = _to_num(po_df[C_SUBTOTAL]).sum() if C_SUBTOTAL in po_df.columns else 0
    total_qty_p = _to_num(po_df[C_QTY_PURCHASED]).sum() if C_QTY_PURCHASED in po_df.columns else 0
    unique_pos = po_df[C_PO].nunique() if C_PO in po_df.columns else 0
    top_vendor = po_df.groupby(C_VENDOR)[C_SUBTOTAL].sum().idxmax() if C_VENDOR in po_df.columns and not po_df.empty else "—"
    avg_po = total_spend / unique_pos if unique_pos > 0 else 0

    _render_kpi_grid([
        _premium_kpi_card("💰", f"SAR {total_spend:,.0f}", t("Total Spend","إجمالي الإنفاق")),
        _premium_kpi_card("📦", f"{total_qty_p:,.0f}", t("Total Qty","إجمالي الكمية")),
        _premium_kpi_card("📋", f"{unique_pos:,}", t("Purchase Orders","أوامر الشراء")),
        _premium_kpi_card("🏭", str(top_vendor)[:18], t("Top Vendor","أفضل مورد")),
    ])

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        _chart_card_open(t("Spend by System","الإنفاق حسب النظام"), "💰")
        if C_SYSTEM in po_df.columns:
            sys_spend = po_df.groupby(C_SYSTEM)[C_SUBTOTAL].sum().reset_index()
            fig = px.bar(sys_spend, x=C_SYSTEM, y=C_SUBTOTAL,
                         title=t("Spend by System","الإنفاق حسب النظام"),
                         color=C_SUBTOTAL, color_continuous_scale=["#1e3a8a", "#60a5fa"],
                         template="plotly_dark")
            st.plotly_chart(_apply_plotly_theme(fig), use_container_width=True)
        _chart_card_close()

    with c2:
        _chart_card_open(t("Daily Spend Trend","اتجاه الإنفاق اليومي"), "📈")
        if C_DATE in po_df.columns:
            daily = po_df.copy()
            daily["_date"] = pd.to_datetime(daily[C_DATE], errors="coerce").dt.date
            daily_agg = daily.groupby("_date")[C_SUBTOTAL].sum().reset_index()
            daily_agg.columns = ["Date", "Spend"]
            if not daily_agg.empty:
                fig2 = px.area(daily_agg, x="Date", y="Spend",
                               title=t("Daily Spend","الإنفاق اليومي"),
                               color_discrete_sequence=["#3b6fd4"], template="plotly_dark")
                st.plotly_chart(_apply_plotly_theme(fig2), use_container_width=True)
        _chart_card_close()

    c3, c4 = st.columns(2)
    with c3:
        chart_top = _top10_altair(po_df, C_MODEL, C_SUBTOTAL, t("Top 10 Products by Spend","أعلى 10 منتجات بالإنفاق"))
        if chart_top:
            st.altair_chart(chart_top, use_container_width=True)
    with c4:
        if C_CATEGORY in po_df.columns:
            cat_agg = po_df.groupby(C_CATEGORY)[C_SUBTOTAL].sum().reset_index().nlargest(8, C_SUBTOTAL)
            fig_cat = _plotly_donut(cat_agg, C_CATEGORY, C_SUBTOTAL, t("Spend by Category","الإنفاق حسب الفئة"))
            if fig_cat:
                st.plotly_chart(fig_cat, use_container_width=True)

    # Top vendors bar
    if C_VENDOR in po_df.columns:
        vendor_agg = po_df.groupby(C_VENDOR)[C_SUBTOTAL].sum().reset_index().nlargest(10, C_SUBTOTAL)
        chart_v = _top10_altair(vendor_agg, C_VENDOR, C_SUBTOTAL, t("Top Vendors","أفضل الموردين"), "#34d399")
        if chart_v:
            st.altair_chart(chart_v, use_container_width=True)

    # Full table
    _section_header(t("Purchase Detail","تفاصيل المشتريات"), "📋")
    display_df(po_df, 0, "po_table")
    pc1, pc2 = st.columns(2)
    with pc1:
        st.download_button(f"⬇️ {t('Export CSV','تصدير CSV')}", to_csv(df_for_display(po_df)), dl_name("purchase_analytics", "csv"), "text/csv")
    with pc2:
        st.download_button(f"⬇️ {t('Export Excel','تصدير Excel')}", to_excel_purchase(df_for_display(po_df)), dl_name("purchase_analytics", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Per-code detail
    _section_header(t("Per-Code Analysis","تحليل لكل رمز"), "🔎")
    codes_in_df = sorted(po_df[C_MODEL].dropna().unique().tolist()) if C_MODEL in po_df.columns else []
    if codes_in_df:
        selected_code = st.selectbox(t("Select Model Code","اختر رمز الموديل"), codes_in_df, key="po_code_select")
        if selected_code:
            code_po = po_df[po_df[C_MODEL] == selected_code]
            total_df_cur = st.session_state.get("total_df")
            code_stock = total_df_cur[total_df_cur[C_MODEL] == selected_code] if total_df_cur is not None else None
            dc1, dc2 = st.columns(2)
            with dc1:
                _section_header(t("Purchase History","سجل المشتريات"), "📋")
                render_premium_table(df_for_display(code_po))
            with dc2:
                _section_header(t("Current Stock","المخزون الحالي"), "📦")
                if code_stock is not None and not code_stock.empty:
                    render_premium_table(df_for_display(code_stock[[C_SYSTEM, C_PRODUCT, C_ON_HAND, C_SALE_PRICE]]))
                else:
                    st.info(t("No stock data. Run a stock search first.", "لا توجد بيانات مخزون. قم بالبحث أولاً."))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 21: SALES ANALYTICS VIEW
# ─────────────────────────────────────────────────────────────────────────────
def show_sales_analytics():
    # Hero
    st.markdown(f"""
    <div class="hero-banner">
        <div style="font-size:1.4rem;font-weight:700;color:#e2e8f0;margin-bottom:0.3rem;">
            📈 {t('Sales Analytics','تحليل المبيعات')}
        </div>
        <div style="color:#8899aa;font-size:0.82rem;">
            {t('Multi-system sales order analysis across all companies','تحليل أوامر المبيعات متعدد الأنظمة')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    _section_header(t("Filters","الفلاتر"), "⚙️")
    col_d1, col_d2, col_mc = st.columns([1, 1, 2])
    with col_d1:
        date_from = st.date_input(t("From Date","من تاريخ"), value=datetime.now() - timedelta(days=30), key="sa_from")
    with col_d2:
        date_to = st.date_input(t("To Date","إلى تاريخ"), value=datetime.now(), key="sa_to")
    with col_mc:
        mc_input = st.text_input(t("Model Code Filter (optional)","فلتر رمز الموديل (اختياري)"), placeholder="e.g. ABC-001", key="sa_mc_filter")

    if st.button(f"🔍 {t('Fetch Sales Data','جلب بيانات المبيعات')}", type="primary", key="sa_fetch"):
        mc_list = [c.strip().upper() for c in re.split(r"[,\n;]+", mc_input) if c.strip()] if mc_input.strip() else []
        with st.spinner(t("Fetching sales history from all systems…","جاري جلب سجل المبيعات…")):
            sa_df = fetch_all_systems_sales_history(mc_list, str(date_from), str(date_to))
        st.session_state.salesanalyticsdf = sa_df
        st.session_state.page_sales = 0
        st.rerun()

    sa_df = st.session_state.get("salesanalyticsdf")
    if sa_df is None or sa_df.empty:
        if st.session_state.salesanalyticsdf is not None:
            st.info(t("No sales data found for the selected filters.","لا توجد بيانات مبيعات للفلاتر المحددة."))
        return

    _divider()

    # KPIs
    total_rev = _to_num(sa_df[C_SUBTOTAL]).sum() if C_SUBTOTAL in sa_df.columns else 0
    total_qty_s = _to_num(sa_df[C_QTY]).sum() if C_QTY in sa_df.columns else 0
    unique_sos = sa_df[C_SO].nunique() if C_SO in sa_df.columns else 0
    avg_order = total_rev / unique_sos if unique_sos > 0 else 0
    top_system = sa_df.groupby(C_SYSTEM)[C_SUBTOTAL].sum().idxmax() if C_SYSTEM in sa_df.columns and not sa_df.empty else "—"

    _render_kpi_grid([
        _premium_kpi_card("💰", f"SAR {total_rev:,.0f}", t("Total Revenue","إجمالي الإيرادات")),
        _premium_kpi_card("📦", f"{total_qty_s:,.0f}", t("Total Qty Sold","إجمالي الكمية المباعة")),
        _premium_kpi_card("📋", f"{unique_sos:,}", t("Sales Orders","أوامر البيع")),
        _premium_kpi_card("🏆", str(top_system)[:16], t("Top System","أفضل نظام")),
    ])

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        _chart_card_open(t("Revenue by System","الإيرادات حسب النظام"), "💰")
        if C_SYSTEM in sa_df.columns:
            sys_rev = sa_df.groupby(C_SYSTEM)[C_SUBTOTAL].sum().reset_index()
            fig = px.bar(sys_rev, x=C_SYSTEM, y=C_SUBTOTAL,
                         title=t("Revenue by System","الإيرادات حسب النظام"),
                         color=C_SUBTOTAL, color_continuous_scale=["#064e3b", "#34d399"],
                         template="plotly_dark")
            st.plotly_chart(_apply_plotly_theme(fig), use_container_width=True)
        _chart_card_close()

    with c2:
        _chart_card_open(t("Daily Revenue Trend","اتجاه الإيرادات اليومية"), "📈")
        if C_DATE in sa_df.columns:
            daily = sa_df.copy()
            daily["_date"] = pd.to_datetime(daily[C_DATE], errors="coerce").dt.date
            daily_agg = daily.groupby("_date")[C_SUBTOTAL].sum().reset_index()
            daily_agg.columns = ["Date", "Revenue"]
            if not daily_agg.empty:
                fig2 = px.area(daily_agg, x="Date", y="Revenue",
                               title=t("Daily Revenue","الإيرادات اليومية"),
                               color_discrete_sequence=["#34d399"], template="plotly_dark")
                st.plotly_chart(_apply_plotly_theme(fig2), use_container_width=True)
        _chart_card_close()

    c3, c4 = st.columns(2)
    with c3:
        chart_top = _top10_altair(sa_df, C_MODEL, C_SUBTOTAL, t("Top 10 Products by Revenue","أعلى 10 منتجات بالإيرادات"), "#34d399")
        if chart_top:
            st.altair_chart(chart_top, use_container_width=True)
    with c4:
        if C_CATEGORY in sa_df.columns:
            cat_agg = sa_df.groupby(C_CATEGORY)[C_SUBTOTAL].sum().reset_index().nlargest(8, C_SUBTOTAL)
            fig_cat = _plotly_donut(cat_agg, C_CATEGORY, C_SUBTOTAL, t("Revenue by Category","الإيرادات حسب الفئة"), ["#34d399","#059669","#3b6fd4","#f59e0b","#f87171","#a78bfa","#fb923c","#60a5fa"])
            if fig_cat:
                st.plotly_chart(fig_cat, use_container_width=True)

    # Top customers
    if C_CUSTOMER in sa_df.columns:
        cust_agg = sa_df.groupby(C_CUSTOMER)[C_SUBTOTAL].sum().reset_index().nlargest(10, C_SUBTOTAL)
        chart_c = _top10_altair(cust_agg, C_CUSTOMER, C_SUBTOTAL, t("Top Customers","أفضل العملاء"), "#f59e0b")
        if chart_c:
            st.altair_chart(chart_c, use_container_width=True)

    # Full table
    _section_header(t("Sales Detail","تفاصيل المبيعات"), "📋")
    display_df(sa_df, 0, "sa_table")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.download_button(f"⬇️ {t('Export CSV','تصدير CSV')}", to_csv(df_for_display(sa_df)), dl_name("sales_analytics", "csv"), "text/csv")
    with sc2:
        st.download_button(f"⬇️ {t('Export Excel','تصدير Excel')}", to_excel_sales(df_for_display(sa_df)), dl_name("sales_analytics", "xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Per-code detail
    _section_header(t("Per-Code Analysis","تحليل لكل رمز"), "🔎")
    codes_in_df = sorted(sa_df[C_MODEL].dropna().unique().tolist()) if C_MODEL in sa_df.columns else []
    if codes_in_df:
        selected_code = st.selectbox(t("Select Model Code","اختر رمز الموديل"), codes_in_df, key="sa_code_select")
        if selected_code:
            code_sales = sa_df[sa_df[C_MODEL] == selected_code]
            total_df_cur = st.session_state.get("total_df")
            code_stock = total_df_cur[total_df_cur[C_MODEL] == selected_code] if total_df_cur is not None else None
            dc1, dc2 = st.columns(2)
            with dc1:
                _section_header(t("Sales History","سجل المبيعات"), "📈")
                render_premium_table(df_for_display(code_sales))
            with dc2:
                _section_header(t("Current Stock","المخزون الحالي"), "📦")
                if code_stock is not None and not code_stock.empty:
                    render_premium_table(df_for_display(code_stock[[C_SYSTEM, C_PRODUCT, C_ON_HAND, C_SALE_PRICE]]))
                else:
                    st.info(t("No stock data. Run a stock search first.", "لا توجد بيانات مخزون. قم بالبحث أولاً."))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 22: MAIN DASHBOARD ROUTER
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    st.markdown(_build_css(), unsafe_allow_html=True)
    _render_sidebar()

    view = st.session_state.get("analytics_view", "stock")
    if view == "stock":
        show_stock_comparison()
    elif view == "purchase":
        show_purchase_analytics()
    elif view == "sales":
        show_sales_analytics()
    else:
        show_stock_comparison()

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()
if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
