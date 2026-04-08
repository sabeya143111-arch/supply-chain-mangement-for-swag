"""
Odoo Business Dashboard – Streamlit App
========================================
Single-file Streamlit dashboard connecting to multiple Odoo instances via XML-RPC.
Supports: Inventory, Sales, Purchase, POS, Insights tabs.
Languages: English / Arabic (RTL-friendly).
Themes: Dark Executive, Light Executive, Ocean Blue.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from xmlrpc.client import ServerProxy
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional, Tuple, List, Dict, Any

# ═══════════════════════════════════════════════════════════════
# THEMES + CSS
# ═══════════════════════════════════════════════════════════════

THEMES: Dict[str, Dict[str, Any]] = {
    "Dark Executive": {
        "bg": "#0f1117", "sidebar_bg": "#161b22", "card_bg": "#1c2333",
        "accent1": "#58a6ff", "accent2": "#3fb950", "text": "#e6edf3",
        "text_muted": "#8b949e", "border": "#30363d",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#58a6ff", "#3fb950", "#f0883e", "#bc8cff", "#ff7b72", "#79c0ff"],
    },
    "Light Executive": {
        "bg": "#ffffff", "sidebar_bg": "#f6f8fa", "card_bg": "#f0f3f6",
        "accent1": "#0969da", "accent2": "#1a7f37", "text": "#1f2328",
        "text_muted": "#656d76", "border": "#d0d7de",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#0969da", "#1a7f37", "#bf8700", "#8250df", "#cf222e", "#0550ae"],
    },
    "Ocean Blue": {
        "bg": "#0a192f", "sidebar_bg": "#112240", "card_bg": "#172a45",
        "accent1": "#64ffda", "accent2": "#ffd700", "text": "#ccd6f6",
        "text_muted": "#8892b0", "border": "#233554",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#64ffda", "#ffd700", "#ff6b6b", "#48dbfb", "#ff9ff3", "#54a0ff"],
    },
}


def get_theme() -> Dict[str, Any]:
    return THEMES.get(st.session_state.get("theme", "Dark Executive"), THEMES["Dark Executive"])


def inject_css():
    th = get_theme()
    lang = get_lang()
    direction = "rtl" if lang == "AR" else "ltr"
    text_align = "right" if lang == "AR" else "left"
    st.markdown(f"""
    <style>
    .main .block-container {{ max-width: 1200px; }}
    .stApp {{ background-color: {th['bg']}; color: {th['text']}; direction: {direction}; }}
    section[data-testid="stSidebar"] {{ background-color: {th['sidebar_bg']}; }}
    .metric-card {{
        background: {th['card_bg']}; border: 1px solid {th['border']};
        border-radius: 12px; padding: 20px; text-align: center;
        transition: transform 0.15s ease;
    }}
    .metric-card:hover {{ transform: translateY(-2px); }}
    .metric-card .value {{ font-size: 28px; font-weight: 700; color: {th['accent1']}; }}
    .metric-card .label {{ font-size: 13px; color: {th['text_muted']}; margin-top: 4px; }}
    .app-title {{ text-align: center; font-size: 32px; font-weight: 800; color: {th['text']}; margin-bottom: 0; }}
    .app-subtitle {{ text-align: center; font-size: 14px; color: {th['text_muted']}; margin-bottom: 20px; }}
    div[data-testid="stDataFrame"] {{ direction: ltr; }}
    th, td {{ text-align: {text_align}; }}
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# LANG / LOCALIZATION
# ═══════════════════════════════════════════════════════════════

def get_lang() -> str:
    return st.session_state.get("lang", "EN")


def t(en: str, ar: str) -> str:
    return ar if get_lang() == "AR" else en


_COL_MAP: Dict[str, Tuple[str, str]] = {
    "System": ("System", "النظام"),
    "Date": ("Date", "التاريخ"),
    "Model Code": ("Model Code", "رمز الموديل"),
    "Product": ("Product", "المنتج"),
    "Sale Price": ("Sale Price", "سعر البيع"),
    "On Hand": ("On Hand", "الكمية المتوفرة"),
    "Purchase Qty": ("Purchase Qty", "كمية الشراء"),
    "Branch": ("Branch", "الفرع"),
    "Location": ("Location", "الموقع"),
    "POS Order": ("POS Order", "طلب نقطة البيع"),
    "Customer": ("Customer", "العميل"),
    "Cashier": ("Cashier", "الكاشير"),
    "Category": ("Category", "الفئة"),
    "Qty": ("Qty", "الكمية"),
    "Unit Price": ("Unit Price", "سعر الوحدة"),
    "Subtotal": ("Subtotal", "المجموع الفرعي"),
    "Total Amount": ("Total Amount", "المبلغ الإجمالي"),
    "SO": ("SO", "أمر البيع"),
    "Vendor": ("Vendor", "المورد"),
    "Receipt Location": ("Receipt Location", "موقع الاستلام"),
    "PO": ("PO", "أمر الشراء"),
    "State": ("State", "الحالة"),
}


def col(raw: str) -> str:
    """Return display column name based on current language."""
    pair = _COL_MAP.get(raw)
    if not pair:
        return raw
    return pair[1] if get_lang() == "AR" else pair[0]


def localize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with column names localized for display."""
    rename = {}
    for c in df.columns:
        if c in _COL_MAP:
            rename[c] = col(c)
    return df.rename(columns=rename) if rename else df.copy()


# ═══════════════════════════════════════════════════════════════
# AUTH (Odoo login)
# ═══════════════════════════════════════════════════════════════

SYSTEM_KEYS: List[str] = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]


def _odoo_auth(url: str, db: str, user: str, password: str) -> Tuple[Optional[int], Optional[str]]:
    """Authenticate with Odoo XML-RPC. Returns (uid, error)."""
    try:
        common = ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, user, password, {})
        if uid:
            return uid, None
        return None, t("Invalid credentials", "بيانات اعتماد غير صالحة")
    except Exception as e:
        return None, str(e)


def attempt_login(email: str, password: str) -> bool:
    """Try logging in via LOGIN secrets block or first available system."""
    try:
        cfg = st.secrets.get("LOGIN", None)
        if cfg:
            url = cfg["url"].rstrip("/xmlrpc/2").rstrip("/")
            uid, err = _odoo_auth(url + "/xmlrpc/2", cfg["db"], email, password)
            if uid:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                return True
            st.error(err or t("Login failed", "فشل تسجيل الدخول"))
            return False
    except Exception:
        pass
    # Fallback: try first system key
    for key in SYSTEM_KEYS:
        cfg = st.secrets.get(key, None)
        if cfg:
            url = cfg["url"].rstrip("/xmlrpc/2").rstrip("/")
            uid, err = _odoo_auth(url + "/xmlrpc/2", cfg["db"], email, password)
            if uid:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                return True
    st.error(t("Could not authenticate with any system", "تعذر المصادقة مع أي نظام"))
    return False


def _get_system_conn(key: str):
    """Return (url, db, uid, api_key, display_name, error)."""
    cfg = st.secrets.get(key, None)
    if not cfg:
        return None, None, None, None, key, f"No config for {key}"
    url = cfg.get("url", "").rstrip("/")
    db = cfg.get("db", "")
    user = cfg.get("user", "")
    api_key = cfg.get("api_key", cfg.get("password", ""))
    uid, err = _odoo_auth(url, db, user, api_key)
    if err:
        return url, db, None, None, key, err
    return url, db, uid, api_key, key, None


def _odoo_call(url: str, db: str, uid: int, api_key: str,
               model: str, method: str, domain: list, fields: list,
               limit: int = 0) -> list:
    """Execute an Odoo XML-RPC call."""
    models = ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    kwargs: Dict[str, Any] = {"fields": fields}
    if limit:
        kwargs["limit"] = limit
    return models.execute_kw(db, uid, api_key, model, method, [domain], kwargs)


# ═══════════════════════════════════════════════════════════════
# DATA UTILITIES
# ═══════════════════════════════════════════════════════════════

_NUMERIC_COLS = {"Sale Price", "On Hand", "Qty", "Unit Price", "Subtotal",
                 "Total Amount", "Purchase Qty"}


def coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    for c in _NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def has_col(df: pd.DataFrame, raw: str) -> bool:
    return raw in df.columns or col(raw) in df.columns


def get_display_col(df: pd.DataFrame, raw: str) -> Optional[str]:
    if raw in df.columns:
        return raw
    loc = col(raw)
    if loc in df.columns:
        return loc
    return None


def safe_get_col(df: pd.DataFrame, raw: str) -> pd.Series:
    c = get_display_col(df, raw)
    if c is None:
        return pd.Series(0, index=df.index)
    return pd.to_numeric(df[c], errors="coerce").fillna(0)


def to_csv(df: pd.DataFrame) -> bytes:
    return localize_df(df).to_csv(index=False).encode("utf-8-sig")


def to_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    localize_df(df).to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _empty_df(columns: List[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


# ═══════════════════════════════════════════════════════════════
# DATA FETCHERS
# ═══════════════════════════════════════════════════════════════

_INV_COLS = ["System", "Model Code", "Product", "Sale Price", "On Hand"]
_INV_BRANCH_COLS = ["System", "Branch", "Model Code", "On Hand"]
_SALES_COLS = ["System", "Date", "SO", "Customer", "Cashier", "Model Code",
               "Product", "Qty", "Unit Price", "Subtotal", "Total Amount", "Branch"]
_PURCHASE_COLS = ["System", "Date", "PO", "Vendor", "Model Code", "Product",
                  "Qty", "Unit Price", "Subtotal", "Receipt Location"]
_POS_COLS = ["System", "Date", "POS Order", "Customer", "Cashier",
             "Qty", "Subtotal", "Total Amount", "Branch"]


@st.cache_data(ttl=3 * 3600, show_spinner=False)
def fetch_inventory() -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
    """Fetch inventory data from all systems."""
    rows, branch_rows, diags = [], [], []
    for key in SYSTEM_KEYS:
        url, db, uid, api_key, name, err = _get_system_conn(key)
        if err:
            diags.append({"system": name, "level": "error", "msg": err})
            continue
        try:
            products = _odoo_call(url, db, uid, api_key, "product.product", "search_read",
                                  [("detailed_type", "=", "product"), ("active", "=", True)],
                                  ["id", "default_code", "name", "list_price"])
            if not products:
                continue
            pid_map = {p["id"]: p for p in products}
            pids = list(pid_map.keys())
            quants = _odoo_call(url, db, uid, api_key, "stock.quant", "search_read",
                                [("product_id", "in", pids), ("location_id.usage", "=", "internal")],
                                ["product_id", "location_id", "quantity"])
            # Aggregate per product
            agg: Dict[int, float] = {}
            branch_agg: Dict[Tuple[int, str], float] = {}
            for q in quants:
                pid = q["product_id"][0] if isinstance(q["product_id"], (list, tuple)) else q["product_id"]
                qty = q.get("quantity", 0) or 0
                agg[pid] = agg.get(pid, 0) + qty
                loc_name = q["location_id"][1] if isinstance(q["location_id"], (list, tuple)) else str(q["location_id"])
                branch = loc_name.split("/")[0].strip() if "/" in loc_name else loc_name
                branch_agg[(pid, branch)] = branch_agg.get((pid, branch), 0) + qty
            for pid, qty in agg.items():
                p = pid_map.get(pid)
                if not p:
                    continue
                rows.append({
                    "System": name,
                    "Model Code": p.get("default_code") or "",
                    "Product": p.get("name") or "",
                    "Sale Price": p.get("list_price", 0),
                    "On Hand": qty,
                })
            for (pid, branch), qty in branch_agg.items():
                p = pid_map.get(pid)
                if not p:
                    continue
                branch_rows.append({
                    "System": name,
                    "Branch": branch,
                    "Model Code": p.get("default_code") or "",
                    "On Hand": qty,
                })
        except Exception as e:
            diags.append({"system": name, "level": "error", "msg": str(e)})
    inv_df = pd.DataFrame(rows, columns=_INV_COLS) if rows else _empty_df(_INV_COLS)
    br_df = pd.DataFrame(branch_rows, columns=_INV_BRANCH_COLS) if branch_rows else _empty_df(_INV_BRANCH_COLS)
    return coerce_numerics(inv_df), coerce_numerics(br_df), diags


@st.cache_data(ttl=2 * 3600, show_spinner=False)
def fetch_sales(date_from: str = "", date_to: str = "") -> Tuple[pd.DataFrame, List[Dict]]:
    """Fetch sales data from POS orders across all systems."""
    rows, diags = [], []
    for key in SYSTEM_KEYS:
        url, db, uid, api_key, name, err = _get_system_conn(key)
        if err:
            diags.append({"system": name, "level": "error", "msg": err})
            continue
        try:
            domain: list = [("state", "in", ["paid", "done", "invoiced"])]
            if date_from:
                domain.append(("date_order", ">=", date_from))
            if date_to:
                domain.append(("date_order", "<=", date_to))
            orders = _odoo_call(url, db, uid, api_key, "pos.order", "search_read",
                                domain,
                                ["id", "name", "date_order", "partner_id", "user_id", "amount_total"])
            if not orders:
                continue
            oids = [o["id"] for o in orders]
            lines = _odoo_call(url, db, uid, api_key, "pos.order.line", "search_read",
                               [("order_id", "in", oids)],
                               ["order_id", "product_id", "qty", "price_unit", "price_subtotal"])
            order_map = {o["id"]: o for o in orders}
            for ln in lines:
                oid = ln["order_id"][0] if isinstance(ln["order_id"], (list, tuple)) else ln["order_id"]
                o = order_map.get(oid, {})
                prod_name = ln["product_id"][1] if isinstance(ln["product_id"], (list, tuple)) else ""
                code = ""
                if "[" in prod_name and "]" in prod_name:
                    code = prod_name.split("]")[0].replace("[", "").strip()
                    prod_name = prod_name.split("]")[-1].strip()
                rows.append({
                    "System": name,
                    "Date": str(o.get("date_order", ""))[:10],
                    "SO": o.get("name", ""),
                    "Customer": o.get("partner_id", [0, ""])[1] if isinstance(o.get("partner_id"), (list, tuple)) else "",
                    "Cashier": o.get("user_id", [0, ""])[1] if isinstance(o.get("user_id"), (list, tuple)) else "",
                    "Model Code": code,
                    "Product": prod_name,
                    "Qty": ln.get("qty", 0),
                    "Unit Price": ln.get("price_unit", 0),
                    "Subtotal": ln.get("price_subtotal", 0),
                    "Total Amount": o.get("amount_total", 0),
                    "Branch": name,
                })
        except Exception as e:
            diags.append({"system": name, "level": "error", "msg": str(e)})
    df = pd.DataFrame(rows, columns=_SALES_COLS) if rows else _empty_df(_SALES_COLS)
    df = coerce_numerics(df)
    if "Date" in df.columns and len(df):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df, diags


@st.cache_data(ttl=2 * 3600, show_spinner=False)
def fetch_purchase(date_from: str = "", date_to: str = "") -> Tuple[pd.DataFrame, List[Dict]]:
    """Fetch purchase orders from all systems."""
    rows, diags = [], []
    for key in SYSTEM_KEYS:
        url, db, uid, api_key, name, err = _get_system_conn(key)
        if err:
            diags.append({"system": name, "level": "error", "msg": err})
            continue
        try:
            domain: list = [("state", "in", ["purchase", "done"])]
            if date_from:
                domain.append(("date_order", ">=", date_from))
            if date_to:
                domain.append(("date_order", "<=", date_to))
            orders = _odoo_call(url, db, uid, api_key, "purchase.order", "search_read",
                                domain,
                                ["id", "name", "date_order", "partner_id", "amount_total"])
            if not orders:
                continue
            oids = [o["id"] for o in orders]
            lines = _odoo_call(url, db, uid, api_key, "purchase.order.line", "search_read",
                               [("order_id", "in", oids)],
                               ["order_id", "product_id", "product_qty", "price_unit", "price_subtotal"])
            order_map = {o["id"]: o for o in orders}
            for ln in lines:
                oid = ln["order_id"][0] if isinstance(ln["order_id"], (list, tuple)) else ln["order_id"]
                o = order_map.get(oid, {})
                prod_name = ln["product_id"][1] if isinstance(ln["product_id"], (list, tuple)) else ""
                code = ""
                if "[" in prod_name and "]" in prod_name:
                    code = prod_name.split("]")[0].replace("[", "").strip()
                    prod_name = prod_name.split("]")[-1].strip()
                rows.append({
                    "System": name,
                    "Date": str(o.get("date_order", ""))[:10],
                    "PO": o.get("name", ""),
                    "Vendor": o.get("partner_id", [0, ""])[1] if isinstance(o.get("partner_id"), (list, tuple)) else "",
                    "Model Code": code,
                    "Product": prod_name,
                    "Qty": ln.get("product_qty", 0),
                    "Unit Price": ln.get("price_unit", 0),
                    "Subtotal": ln.get("price_subtotal", 0),
                    "Receipt Location": name,
                })
        except Exception as e:
            diags.append({"system": name, "level": "error", "msg": str(e)})
    df = pd.DataFrame(rows, columns=_PURCHASE_COLS) if rows else _empty_df(_PURCHASE_COLS)
    df = coerce_numerics(df)
    if "Date" in df.columns and len(df):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df, diags


@st.cache_data(ttl=2 * 3600, show_spinner=False)
def fetch_pos(date_from: str = "", date_to: str = "") -> Tuple[pd.DataFrame, List[Dict]]:
    """Fetch POS orders from all systems."""
    rows, diags = [], []
    for key in SYSTEM_KEYS:
        url, db, uid, api_key, name, err = _get_system_conn(key)
        if err:
            diags.append({"system": name, "level": "error", "msg": err})
            continue
        try:
            domain: list = [("state", "in", ["paid", "done", "invoiced"])]
            if date_from:
                domain.append(("date_order", ">=", date_from))
            if date_to:
                domain.append(("date_order", "<=", date_to))
            orders = _odoo_call(url, db, uid, api_key, "pos.order", "search_read",
                                domain,
                                ["id", "name", "date_order", "partner_id", "user_id", "amount_total"])
            if not orders:
                continue
            oids = [o["id"] for o in orders]
            lines = _odoo_call(url, db, uid, api_key, "pos.order.line", "search_read",
                               [("order_id", "in", oids)],
                               ["order_id", "qty", "price_subtotal_incl"])
            order_map = {o["id"]: o for o in orders}
            for ln in lines:
                oid = ln["order_id"][0] if isinstance(ln["order_id"], (list, tuple)) else ln["order_id"]
                o = order_map.get(oid, {})
                rows.append({
                    "System": name,
                    "Date": str(o.get("date_order", ""))[:10],
                    "POS Order": o.get("name", ""),
                    "Customer": o.get("partner_id", [0, ""])[1] if isinstance(o.get("partner_id"), (list, tuple)) else "",
                    "Cashier": o.get("user_id", [0, ""])[1] if isinstance(o.get("user_id"), (list, tuple)) else "",
                    "Qty": ln.get("qty", 0),
                    "Subtotal": ln.get("price_subtotal_incl", 0),
                    "Total Amount": o.get("amount_total", 0),
                    "Branch": name,
                })
        except Exception as e:
            diags.append({"system": name, "level": "error", "msg": str(e)})
    df = pd.DataFrame(rows, columns=_POS_COLS) if rows else _empty_df(_POS_COLS)
    df = coerce_numerics(df)
    if "Date" in df.columns and len(df):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df, diags


# ═══════════════════════════════════════════════════════════════
# VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════

VIZ_MODES = [
    "List View", "KPI Tiles", "Column Chart", "Horizontal Bar",
    "Line Chart", "Area Chart", "Pie / Donut", "Stacked Bar", "Scatter",
]


def apply_plotly_theme(fig):
    th = get_theme()
    fig.update_layout(
        template=th["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=th["text"],
        colorway=th["plotly_colors"],
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def render_metric_cards(metrics: List[Tuple[str, str]]):
    """Render a row of metric cards. Each tuple: (label, value)."""
    cols = st.columns(len(metrics))
    for c, (label, value) in zip(cols, metrics):
        c.markdown(f"""
        <div class="metric-card">
            <div class="value">{value}</div>
            <div class="label">{label}</div>
        </div>
        """, unsafe_allow_html=True)


def render_visualization(df: pd.DataFrame, viz_mode: str, x_raw: str, y_raw: str,
                         label: str = "", color_raw: Optional[str] = None):
    """Generic visualization renderer."""
    if df is None or df.empty:
        st.info(t("No data to display", "لا توجد بيانات للعرض"))
        return
    x_col = get_display_col(df, x_raw) or x_raw
    y_col = get_display_col(df, y_raw) or y_raw
    if x_col not in df.columns or y_col not in df.columns:
        st.warning(t(f"Missing columns: {x_raw}, {y_raw}", f"أعمدة مفقودة: {x_raw}, {y_raw}"))
        return
    color_col = get_display_col(df, color_raw) if color_raw else None
    title = label or f"{col(y_raw)} by {col(x_raw)}"
    try:
        if viz_mode == "List View":
            render_paginated_table(df, f"viz_{x_raw}_{y_raw}")
            return
        if viz_mode == "KPI Tiles":
            top = df.groupby(x_col)[y_col].sum().nlargest(6).reset_index()
            metrics = [(str(r[x_col]), f"{r[y_col]:,.0f}") for _, r in top.iterrows()]
            render_metric_cards(metrics)
            return
        df_agg = df.groupby(x_col, as_index=False)[y_col].sum().sort_values(y_col, ascending=False)
        if viz_mode == "Column Chart":
            fig = px.bar(df_agg, x=x_col, y=y_col, title=title)
        elif viz_mode == "Horizontal Bar":
            fig = px.bar(df_agg, x=y_col, y=x_col, orientation="h", title=title)
        elif viz_mode == "Line Chart":
            fig = px.line(df_agg.sort_values(x_col), x=x_col, y=y_col, title=title, markers=True)
        elif viz_mode == "Area Chart":
            fig = px.area(df_agg.sort_values(x_col), x=x_col, y=y_col, title=title)
        elif viz_mode == "Pie / Donut":
            fig = px.pie(df_agg.head(10), names=x_col, values=y_col, title=title, hole=0.4)
        elif viz_mode == "Stacked Bar":
            if color_col and color_col in df.columns:
                df_s = df.groupby([x_col, color_col], as_index=False)[y_col].sum()
                fig = px.bar(df_s, x=x_col, y=y_col, color=color_col, title=title)
            else:
                fig = px.bar(df_agg, x=x_col, y=y_col, title=title)
        elif viz_mode == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=title, size=y_col if pd.api.types.is_numeric_dtype(df[y_col]) else None)
        else:
            fig = px.bar(df_agg, x=x_col, y=y_col, title=title)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(t(f"Chart error: {e}", f"خطأ في الرسم: {e}"))


def render_daily_trend_chart(df: pd.DataFrame, date_raw: str, value_raw: str,
                             title: str, chart_type: str = "area"):
    """Render a daily trend area/line chart."""
    if df is None or df.empty:
        st.info(t("No trend data", "لا توجد بيانات اتجاه"))
        return
    dc = get_display_col(df, date_raw)
    vc = get_display_col(df, value_raw)
    if not dc or not vc:
        st.info(t("Missing date/value columns", "أعمدة مفقودة"))
        return
    try:
        tmp = df[[dc, vc]].copy()
        tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
        tmp = tmp.dropna(subset=[dc])
        tmp[vc] = pd.to_numeric(tmp[vc], errors="coerce").fillna(0)
        daily = tmp.groupby(tmp[dc].dt.date, as_index=False)[vc].sum()
        daily.columns = ["Date", vc]
        daily = daily.sort_values("Date")
        if chart_type == "line":
            fig = px.line(daily, x="Date", y=vc, title=title, markers=True)
        else:
            fig = px.area(daily, x="Date", y=vc, title=title)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(t(f"Trend error: {e}", f"خطأ في الاتجاه: {e}"))


def render_paginated_table(df: pd.DataFrame, page_key: str, page_size: int = 25):
    """Paginated table with localized headers."""
    if df is None or df.empty:
        st.info(t("No data", "لا توجد بيانات"))
        return
    total = len(df)
    pages = max(1, (total + page_size - 1) // page_size)
    if f"pg_{page_key}" not in st.session_state:
        st.session_state[f"pg_{page_key}"] = 0
    pg = st.session_state[f"pg_{page_key}"]
    pg = min(pg, pages - 1)
    start = pg * page_size
    end = min(start + page_size, total)
    display = localize_df(df.iloc[start:end].reset_index(drop=True))
    st.dataframe(display, use_container_width=True, hide_index=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button(t("◀ Prev", "◀ السابق"), key=f"prev_{page_key}", disabled=pg == 0):
            st.session_state[f"pg_{page_key}"] = pg - 1
            st.rerun()
    with c2:
        st.caption(f"{t('Page', 'صفحة')} {pg + 1} / {pages}  ({total} {t('rows', 'صف')})")
    with c3:
        if st.button(t("Next ▶", "التالي ▶"), key=f"next_{page_key}", disabled=pg >= pages - 1):
            st.session_state[f"pg_{page_key}"] = pg + 1
            st.rerun()


def download_buttons(df: pd.DataFrame, key_prefix: str):
    """CSV and Excel download buttons."""
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(t("📥 CSV", "📥 CSV"), to_csv(df), f"{key_prefix}.csv",
                           "text/csv", key=f"dl_csv_{key_prefix}")
    with c2:
        st.download_button(t("📥 Excel", "📥 إكسل"), to_excel(df), f"{key_prefix}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"dl_xl_{key_prefix}")


# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════

def tab_inventory():
    with st.spinner(t("Loading inventory…", "جاري تحميل المخزون…")):
        inv_df, branch_df, diags = fetch_inventory()
    for d in diags:
        st.warning(f"⚠ {d['system']}: {d['msg']}")

    # Filters
    systems = ["All"] + sorted(inv_df["System"].unique().tolist()) if len(inv_df) else ["All"]
    sel_sys = st.selectbox(t("Company", "الشركة"), systems, key="inv_sys")
    df = inv_df if sel_sys == "All" else inv_df[inv_df["System"] == sel_sys]

    if has_col(branch_df, "Branch") and len(branch_df):
        bdf = branch_df if sel_sys == "All" else branch_df[branch_df["System"] == sel_sys]
        branches = ["All"] + sorted(bdf["Branch"].unique().tolist())
        sel_br = st.selectbox(t("Branch", "الفرع"), branches, key="inv_br")
        if sel_br != "All":
            codes = bdf[bdf["Branch"] == sel_br]["Model Code"].unique()
            df = df[df["Model Code"].isin(codes)]

    # KPIs
    total_oh = safe_get_col(df, "On Hand").sum()
    stock_val = (safe_get_col(df, "On Hand") * safe_get_col(df, "Sale Price")).sum()
    zero = int((safe_get_col(df, "On Hand") == 0).sum())
    render_metric_cards([
        (t("Total On Hand", "إجمالي المتوفر"), f"{total_oh:,.0f}"),
        (t("Stock Value", "قيمة المخزون"), f"{stock_val:,.0f}"),
        (t("Zero Stock", "مخزون صفري"), f"{zero:,}"),
    ])

    # Viz
    st.markdown("---")
    vm = st.selectbox(t("Visualization", "نوع العرض"), VIZ_MODES, key="inv_viz")
    render_visualization(df, vm, "Model Code", "On Hand", t("Inventory", "المخزون"))

    # Table
    st.markdown("---")
    render_paginated_table(df, "inv_table")
    download_buttons(df, "inventory")


def tab_sales():
    c1, c2 = st.columns(2)
    with c1:
        d_from = st.date_input(t("From", "من"), value=datetime.today() - timedelta(days=30), key="s_from")
    with c2:
        d_to = st.date_input(t("To", "إلى"), value=datetime.today(), key="s_to")
    with st.spinner(t("Loading sales…", "جاري تحميل المبيعات…")):
        sales_df, diags = fetch_sales(str(d_from), str(d_to))
    for d in diags:
        st.warning(f"⚠ {d['system']}: {d['msg']}")

    systems = ["All"] + sorted(sales_df["System"].unique().tolist()) if len(sales_df) else ["All"]
    sel = st.selectbox(t("Company", "الشركة"), systems, key="s_sys")
    df = sales_df if sel == "All" else sales_df[sales_df["System"] == sel]

    # KPIs
    rev = safe_get_col(df, "Total Amount").sum()
    orders = df["SO"].nunique() if "SO" in df.columns else 0
    avg_o = rev / orders if orders else 0
    custs = df["Customer"].nunique() if "Customer" in df.columns else 0
    render_metric_cards([
        (t("Revenue", "الإيرادات"), f"{rev:,.0f}"),
        (t("Orders", "الطلبات"), f"{orders:,}"),
        (t("Avg Order", "متوسط الطلب"), f"{avg_o:,.0f}"),
        (t("Customers", "العملاء"), f"{custs:,}"),
    ])

    st.markdown("---")
    render_daily_trend_chart(df, "Date", "Total Amount",
                             t("Daily Revenue", "الإيرادات اليومية"))

    st.markdown("---")
    vm = st.selectbox(t("Visualization", "نوع العرض"), VIZ_MODES, key="s_viz")
    render_visualization(df, vm, "Branch", "Total Amount",
                         t("Sales by Branch", "المبيعات حسب الفرع"))

    st.markdown("---")
    render_paginated_table(df, "sales_table")
    download_buttons(df, "sales")


def tab_purchase():
    c1, c2 = st.columns(2)
    with c1:
        d_from = st.date_input(t("From", "من"), value=datetime.today() - timedelta(days=30), key="p_from")
    with c2:
        d_to = st.date_input(t("To", "إلى"), value=datetime.today(), key="p_to")
    with st.spinner(t("Loading purchases…", "جاري تحميل المشتريات…")):
        purchase_df, diags = fetch_purchase(str(d_from), str(d_to))
    for d in diags:
        st.warning(f"⚠ {d['system']}: {d['msg']}")

    systems = ["All"] + sorted(purchase_df["System"].unique().tolist()) if len(purchase_df) else ["All"]
    sel = st.selectbox(t("Company", "الشركة"), systems, key="p_sys")
    df = purchase_df if sel == "All" else purchase_df[purchase_df["System"] == sel]

    # KPIs
    spend = safe_get_col(df, "Subtotal").sum()
    po_count = df["PO"].nunique() if "PO" in df.columns else 0
    vendors = df["Vendor"].nunique() if "Vendor" in df.columns else 0
    render_metric_cards([
        (t("Total Spend", "إجمالي الإنفاق"), f"{spend:,.0f}"),
        (t("PO Count", "عدد أوامر الشراء"), f"{po_count:,}"),
        (t("Vendors", "الموردون"), f"{vendors:,}"),
    ])

    st.markdown("---")
    render_daily_trend_chart(df, "Date", "Subtotal",
                             t("Daily Spend", "الإنفاق اليومي"))

    st.markdown("---")
    vm = st.selectbox(t("Visualization", "نوع العرض"), VIZ_MODES, key="p_viz")
    render_visualization(df, vm, "Vendor", "Subtotal",
                         t("Top Vendors", "أعلى الموردين"))

    st.markdown("---")
    render_paginated_table(df, "purchase_table")
    download_buttons(df, "purchase")


def tab_pos():
    c1, c2 = st.columns(2)
    with c1:
        d_from = st.date_input(t("From", "من"), value=datetime.today() - timedelta(days=30), key="pos_from")
    with c2:
        d_to = st.date_input(t("To", "إلى"), value=datetime.today(), key="pos_to")
    with st.spinner(t("Loading POS…", "جاري تحميل نقاط البيع…")):
        pos_df, diags = fetch_pos(str(d_from), str(d_to))
    for d in diags:
        st.warning(f"⚠ {d['system']}: {d['msg']}")

    systems = ["All"] + sorted(pos_df["System"].unique().tolist()) if len(pos_df) else ["All"]
    sel = st.selectbox(t("Company", "الشركة"), systems, key="pos_sys")
    df = pos_df if sel == "All" else pos_df[pos_df["System"] == sel]

    rev = safe_get_col(df, "Total Amount").sum()
    orders = df["POS Order"].nunique() if "POS Order" in df.columns else 0
    cashiers = df["Cashier"].nunique() if "Cashier" in df.columns else 0
    render_metric_cards([
        (t("POS Revenue", "إيرادات نقاط البيع"), f"{rev:,.0f}"),
        (t("Orders", "الطلبات"), f"{orders:,}"),
        (t("Cashiers", "الكاشير"), f"{cashiers:,}"),
    ])

    st.markdown("---")
    vm = st.selectbox(t("Visualization", "نوع العرض"), VIZ_MODES, key="pos_viz")
    render_visualization(df, vm, "Cashier", "Total Amount",
                         t("Cashier Performance", "أداء الكاشير"))

    st.markdown("---")
    render_visualization(df, "Column Chart", "Branch", "Total Amount",
                         t("Branch Performance", "أداء الفروع"))

    st.markdown("---")
    render_paginated_table(df, "pos_table")
    download_buttons(df, "pos")


def tab_insights():
    st.subheader(t("📊 Business Insights", "📊 رؤى الأعمال"))
    st.markdown("---")
    try:
        inv_df, _, _ = fetch_inventory()
        sales_df, _ = fetch_sales()
        purchase_df, _ = fetch_purchase()
        pos_df, _ = fetch_pos()

        total_stock = safe_get_col(inv_df, "On Hand").sum()
        total_sales = safe_get_col(sales_df, "Total Amount").sum()
        total_purchase = safe_get_col(purchase_df, "Subtotal").sum()
        total_pos = safe_get_col(pos_df, "Total Amount").sum()

        render_metric_cards([
            (t("Total Stock Units", "إجمالي وحدات المخزون"), f"{total_stock:,.0f}"),
            (t("Sales Revenue", "إيرادات المبيعات"), f"{total_sales:,.0f}"),
            (t("Purchase Spend", "إنفاق المشتريات"), f"{total_purchase:,.0f}"),
            (t("POS Revenue", "إيرادات نقاط البيع"), f"{total_pos:,.0f}"),
        ])

        st.markdown("---")
        st.markdown(t(
            "### Summary\\n"
            f"- **Inventory**: {total_stock:,.0f} units across all branches.\\n"
            f"- **Sales**: {total_sales:,.0f} total revenue.\\n"
            f"- **Purchases**: {total_purchase:,.0f} total spend.\\n"
            f"- **POS**: {total_pos:,.0f} total POS revenue.\\n"
            f"- **Margin Indicator**: Revenue vs. Spend ratio = "
            f"{(total_sales / total_purchase * 100) if total_purchase else 0:.1f}%",
            "### ملخص\\n"
            f"- **المخزون**: {total_stock:,.0f} وحدة عبر جميع الفروع.\\n"
            f"- **المبيعات**: {total_sales:,.0f} إجمالي الإيرادات.\\n"
            f"- **المشتريات**: {total_purchase:,.0f} إجمالي الإنفاق.\\n"
            f"- **نقاط البيع**: {total_pos:,.0f} إجمالي إيرادات نقاط البيع.\\n"
            f"- **مؤشر الهامش**: نسبة الإيرادات إلى الإنفاق = "
            f"{(total_sales / total_purchase * 100) if total_purchase else 0:.1f}%"
        ))
    except Exception as e:
        st.error(t(f"Insights error: {e}", f"خطأ في الرؤى: {e}"))


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY
# ═══════════════════════════════════════════════════════════════

def login_page():
    st.markdown(f'<h1 class="app-title">{t("Business Dashboard", "لوحة الأعمال")}</h1>',
                unsafe_allow_html=True)
    st.markdown(f'<p class="app-subtitle">{t("Sign in to continue", "سجل الدخول للمتابعة")}</p>',
                unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input(t("Email", "البريد الإلكتروني"))
        password = st.text_input(t("Password", "كلمة المرور"), type="password")
        if st.form_submit_button(t("Login", "دخول")):
            if email and password:
                attempt_login(email, password)
            else:
                st.warning(t("Please fill all fields", "يرجى ملء جميع الحقول"))


def main():
    st.set_page_config(
        page_title="Business Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar: Language + Theme
    with st.sidebar:
        lang = st.radio("🌐", ["English", "عربي"], horizontal=True, key="lang_radio")
        st.session_state.lang = "AR" if lang == "عربي" else "EN"

        theme_name = st.selectbox(
            t("Theme", "المظهر"),
            list(THEMES.keys()),
            key="theme",
        )

    inject_css()

    if not st.session_state.get("authenticated"):
        login_page()
        return

    # Sidebar info
    with st.sidebar:
        st.success(f"✅ {st.session_state.get('user_email', '')}")
        if st.button(t("Logout", "تسجيل خروج")):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # Title
    st.markdown(f'<h1 class="app-title">{t("Business Dashboard", "لوحة الأعمال")}</h1>',
                unsafe_allow_html=True)
    st.markdown(f'<p class="app-subtitle">{t("Multi-Company Analytics", "تحليلات متعددة الشركات")}</p>',
                unsafe_allow_html=True)

    # Tabs
    tab_labels = [
        t("📦 Inventory", "📦 المخزون"),
        t("💰 Sales", "💰 المبيعات"),
        t("🛒 Purchase", "🛒 المشتريات"),
        t("🏪 POS", "🏪 نقاط البيع"),
        t("🔍 Insights", "🔍 الرؤى"),
    ]
    tabs = st.tabs(tab_labels)
    with tabs[0]:
        tab_inventory()
    with tabs[1]:
        tab_sales()
    with tabs[2]:
        tab_purchase()
    with tabs[3]:
        tab_pos()
    with tabs[4]:
        tab_insights()


if __name__ == "__main__":
    main()
