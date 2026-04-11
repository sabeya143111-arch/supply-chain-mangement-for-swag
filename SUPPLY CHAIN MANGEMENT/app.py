# app.py — SWAG EXECUTIVE DASHBOARD — PROFESSIONAL EDITION (STABLE)
import io
import re
import hashlib
import math
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="SWAG Executive Dashboard", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------------------------
# Helper: Color
# ------------------------------------------------------------------------------
def hex_to_rgba(hex_color, alpha=0.15):
    try:
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6:
            return f"rgba(100,100,100,{alpha})"
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except:
        return f"rgba(100,100,100,{alpha})"

# ------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------
THEMES = {
    "Modern Corporate": {
        "bg": "#f8fafc", "sidebar_bg": "#ffffff", "card_bg": "#ffffff",
        "accent1": "#0f3b5e", "accent2": "#1e6f5c", "accent3": "#289672",
        "text": "#1e293b", "text_muted": "#64748b", "border": "#e2e8f0",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#0f3b5e", "#1e6f5c", "#289672", "#f4a261", "#e76f51", "#2a9d8f"],
    },
    "Dark Executive": {
        "bg": "#0a0c10", "sidebar_bg": "#111827", "card_bg": "#1f2937",
        "accent1": "#60a5fa", "accent2": "#34d399", "accent3": "#fbbf24",
        "text": "#f3f4f6", "text_muted": "#9ca3af", "border": "#374151",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#60a5fa", "#34d399", "#fbbf24", "#f87171", "#a78bfa"],
    },
}
def get_theme(): return st.session_state.get("theme", "Modern Corporate")
def th(key): return THEMES[get_theme()].get(key, "")
def th_color(key, fallback="#0f3b5e"):
    v = THEMES[get_theme()].get(key, fallback)
    return v if isinstance(v, str) and v.startswith("#") else fallback

# ------------------------------------------------------------------------------
# CSS
# ------------------------------------------------------------------------------
def build_css():
    bg = th("bg"); sbg = th("sidebar_bg"); card = th("card_bg"); text = th("text")
    muted = th("text_muted"); border = th("border"); a1 = th_color("accent1"); a2 = th_color("accent2")
    shadow = "0 4px 12px rgba(0,0,0,0.05)"
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ font-family: 'Inter', sans-serif; }}
        body, .stApp {{ background: {bg}; }}
        section[data-testid="stSidebar"] {{ background: {sbg} !important; border-right: 1px solid {border}; }}
        .stButton>button {{ border-radius: 10px; font-weight: 500; background: {card}; border: 1px solid {border}; transition:0.2s; }}
        .stButton>button:hover {{ transform: translateY(-1px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); }}
        .stButton>button[kind="primary"] {{ background: linear-gradient(135deg, {a1}, {a2}); color: white; border: none; }}
        [data-testid="stMetric"] {{ background: {card}; border: 1px solid {border}; border-radius: 20px; padding: 1.2rem; box-shadow: {shadow}; }}
        [data-testid="stMetricLabel"] {{ color: {muted}; font-size: 0.7rem; text-transform: uppercase; letter-spacing:0.05em; }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem; font-weight: 700; color: {text}; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; border-bottom: 1px solid {border}; }}
        .stTabs [data-baseweb="tab"] {{ border-radius: 12px 12px 0 0; padding: 0.5rem 1.2rem; font-weight: 500; color: {muted}; }}
        .stTabs [aria-selected="true"] {{ color: {a1}; border-bottom: 3px solid {a1}; }}
        .info-banner, .warn-banner, .alert-banner, .ok-banner {{ padding: 0.8rem 1.2rem; border-radius: 12px; margin: 1rem 0; }}
        .info-banner {{ background: {hex_to_rgba(a1,0.1)}; border-left: 4px solid {a1}; }}
        .warn-banner {{ background: {hex_to_rgba("#f59e0b",0.1)}; border-left: 4px solid #f59e0b; }}
        .alert-banner {{ background: {hex_to_rgba("#dc2626",0.1)}; border-left: 4px solid #dc2626; }}
        .ok-banner {{ background: {hex_to_rgba("#10b981",0.1)}; border-left: 4px solid #10b981; }}
        .section-header {{ font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 1rem; display: flex; align-items: center; gap: 8px; color: {text}; }}
        .dataframe-wrap {{ overflow-x: auto; }}
        .dataframe-wrap table {{ width:100%; border-collapse:collapse; background:{card}; border-radius:16px; overflow:hidden; box-shadow:{shadow}; }}
        .dataframe-wrap th {{ background:{hex_to_rgba(a1,0.05)}; padding:0.8rem 1rem; text-align:left; font-weight:600; color:{text}; border-bottom:1px solid {border}; }}
        .dataframe-wrap td {{ padding:0.7rem 1rem; border-bottom:1px solid {border}; color:{text}; }}
        .dataframe-wrap tr:hover td {{ background:{hex_to_rgba(a1,0.03)}; }}
        .pagination-bar {{ display:flex; justify-content:center; gap:8px; margin-top:1rem; }}
        .page-info {{ background:{card}; border:1px solid {border}; border-radius:20px; padding:0.3rem 1rem; font-size:0.8rem; }}
        footer {{ visibility: hidden; }}
    </style>
    """

# ------------------------------------------------------------------------------
# Language
# ------------------------------------------------------------------------------
def get_lang(): return st.session_state.get("lang", "EN")
def t(en, ar): return ar if get_lang() == "AR" else en
_COL_MAP = {
    "System": ("System","النظام"), "Model Code": ("Model Code","رمز الموديل"), "Product": ("Product","المنتج"),
    "Sale Price": ("Sale Price","سعر البيع"), "On Hand": ("On Hand","متوفر"), "Purchase Qty": ("Purchase Qty","كمية الشراء"),
    "Branch": ("Branch","الفرع"), "Date": ("Date","التاريخ"), "POS Order": ("POS Order","طلب POS"),
    "Customer": ("Customer","العميل"), "Cashier": ("Cashier","الكاشير"), "Qty": ("Qty","الكمية"),
    "Unit Price": ("Unit Price","سعر الوحدة"), "Subtotal": ("Subtotal","المجموع"), "Total Amount": ("Total Amount","الإجمالي"),
    "SO": ("SO","أمر بيع"), "Vendor": ("Vendor","المورد"), "PO": ("PO","أمر شراء"),
    "Stock Value": ("Stock Value","قيمة المخزون"), "Estimated Sold": ("Estimated Sold","مقدر مبيع"),
    "Sell Through %": ("Sell Through %","نسبة البيع"), "Stock Status": ("Stock Status","الحالة"),
}
def col(raw): return _COL_MAP[raw][1 if get_lang()=="AR" else 0] if raw in _COL_MAP else raw
def localize_df(df):
    if df is None or df.empty: return df
    rename = {raw: col(raw) for raw in _COL_MAP if raw in df.columns}
    return df.rename(columns=rename)
def get_system_name(key):
    cfg = st.secrets.get(key, {})
    return cfg.get("name_ar", cfg.get("name", key)) if get_lang()=="AR" else cfg.get("name", key)

# ------------------------------------------------------------------------------
# Session State
# ------------------------------------------------------------------------------
for k, v in {
    "authenticated":False, "user_email":"", "lang":"EN", "theme":"Modern Corporate",
    "inventory_df":None, "inventory_branch_df":None, "pos_df":None, "sales_df":None, "purchase_df":None,
    "inv_diag":[], "pos_diag":[], "sales_diag":[], "pur_diag":[],
    "inv_last_refresh":None, "pos_last_refresh":None, "sales_last_refresh":None, "pur_last_refresh":None,
    "inv_page":0, "pos_page":0, "sales_page":0, "pur_page":0, "chat_history":[],
}.items():
    if k not in st.session_state: st.session_state[k] = v

# ------------------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------------------
_SECRET = "swag_exec_2025"
def _make_token(email): return hashlib.sha256(f"{_SECRET}_{email}".encode()).hexdigest()[:32]
def restore_session():
    if st.session_state.get("authenticated"): return
    try:
        p = st.query_params
        if p.get("u") and p.get("t") and p["t"] == _make_token(p["u"]):
            st.session_state.authenticated = True
            st.session_state.user_email = p["u"]
    except: pass
def attempt_login(email, pwd):
    if not email or not pwd: return False, "Enter email and password"
    candidates = []
    if "LOGIN" in st.secrets: candidates.append(("LOGIN", st.secrets["LOGIN"]))
    for key in ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]:
        cfg = st.secrets.get(key)
        if cfg and cfg.get("url") and cfg.get("db"): candidates.append((key, cfg))
    for src, cfg in candidates:
        url = cfg["url"].rstrip("/"); db = cfg["db"]
        try:
            uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common").authenticate(db, email, pwd, {})
            if uid and isinstance(uid, int) and uid > 0: return True, ""
        except: continue
    return False, "Invalid credentials"
def do_logout():
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.query_params.clear(); st.rerun()

# ------------------------------------------------------------------------------
# Odoo Helpers
# ------------------------------------------------------------------------------
@st.cache_resource
def _proxy(url, endpoint): return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/{endpoint}", allow_none=True)
@st.cache_data(ttl=28800)
def _odoo_auth(url, db, user, key):
    try: return _proxy(url, "common").authenticate(db, user, key, {})
    except: return None
def _odoo_call(url, db, uid, key, model, method, domain, kwargs):
    return _proxy(url, "object").execute_kw(db, uid, key, model, method, domain, kwargs)
def _get_conn(key):
    cfg = st.secrets.get(key)
    if not cfg: return None,None,None,None,key,"Not configured"
    url = cfg.get("url","").rstrip("/"); db = cfg.get("db",""); user = cfg.get("user",""); api = cfg.get("api_key","")
    name = get_system_name(key)
    if not url or not db or not user or not api: return None,None,None,None,name,"Missing credentials"
    uid = _odoo_auth(url, db, user, api)
    if not uid: return url,db,None,api,name,"Auth failed"
    return url,db,uid,api,name,None

# ------------------------------------------------------------------------------
# Data Utilities
# ------------------------------------------------------------------------------
def safe_get_col(df, raw):
    if df is None or df.empty: return pd.Series(dtype=float)
    if raw in df.columns: return pd.to_numeric(df[raw], errors="coerce").fillna(0)
    l = col(raw)
    if l in df.columns: return pd.to_numeric(df[l], errors="coerce").fillna(0)
    return pd.Series([0.0]*len(df))
def has_col(df, raw): return df is not None and not df.empty and (raw in df.columns or col(raw) in df.columns)
def get_display_col(df, raw):
    if df is None: return raw
    if raw in df.columns: return raw
    l = col(raw)
    return l if l in df.columns else raw
def to_csv(df): return df.to_csv(index=False).encode("utf-8-sig")
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Data", index=False)
    out.seek(0)
    return out.getvalue()
def dl_name(prefix): return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
def render_paginated_table(df, page_key, rows=30):
    if df is None or df.empty: st.info("No data"); return
    total = len(df); pages = max(1, math.ceil(total / rows))
    cur = min(st.session_state.get(page_key, 0), pages-1)
    st.session_state[page_key] = cur
    start = cur * rows; end = min(start+rows, total)
    display = localize_df(df.iloc[start:end])
    st.dataframe(display, use_container_width=True)
    c1,c2,_,c4,c5 = st.columns([1,1,2,1,1])
    if c1.button("⏮", key=f"{page_key}_first"): st.session_state[page_key]=0; st.rerun()
    if c2.button("◀", key=f"{page_key}_prev"): st.session_state[page_key]=max(0,cur-1); st.rerun()
    if c4.button("▶", key=f"{page_key}_next"): st.session_state[page_key]=min(pages-1,cur+1); st.rerun()
    if c5.button("⏭", key=f"{page_key}_last"): st.session_state[page_key]=pages-1; st.rerun()
    st.caption(f"Showing {start+1}-{end} of {total} | Page {cur+1}/{pages}")
def apply_plotly_theme(fig):
    if fig is None: return fig
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=th("text"), size=12), margin=dict(l=20,r=20,t=50,b=30),
                      legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=th("border")))
    fig.update_xaxes(gridcolor=th("border"), linecolor=th("border"))
    fig.update_yaxes(gridcolor=th("border"), linecolor=th("border"))
    return fig
def show_diag(diag):
    if not diag: return
    err = [d for d in diag if d.get("level")=="error"]
    if err:
        with st.expander("⚠️ Load errors"):
            for e in err: st.warning(f"[{e.get('system','')}] {e.get('msg','')}")
    else:
        with st.expander("✅ Load info"):
            for d in diag: st.caption(f"✅ {d.get('system','')}: {d.get('msg','')}")

# ------------------------------------------------------------------------------
# Inventory Fetch (Fixed)
# ------------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def _fetch_inventory_one(key, codes, exact):
    url,db,uid,ak,name,err = _get_conn(key)
    if err: return [],[],{"system":name,"level":"error","msg":err}
    try:
        domain = []
        if codes:
            if exact: domain = [("default_code","in",list(codes))]
            else:
                clauses = [("default_code","=ilike",f"{c}%") for c in codes]
                domain = [clauses[0]] if len(clauses)==1 else ["|"]*(len(clauses)-1)+clauses
        tmpls = _odoo_call(url,db,uid,ak,"product.template","search_read",
                           [domain], {"fields":["id","name","default_code","list_price"],"limit":5000})
        if not tmpls: return [],[],{"system":name,"level":"ok","msg":"No products"}
        tmpl_map = {t["id"]:t for t in tmpls}
        tmpl_ids = list(tmpl_map.keys())
        variants = _odoo_call(url,db,uid,ak,"product.product","search_read",
                              [[("product_tmpl_id","in",tmpl_ids)]],
                              {"fields":["id","product_tmpl_id"],"limit":50000})
        v2t = {}
        for v in variants:
            vid = v["id"]
            pt = v["product_tmpl_id"]
            ptid = pt[0] if isinstance(pt,list) else pt
            v2t[vid] = ptid
        vids = list(v2t.keys())
        if not vids:
            total = [{"System":name, "Model Code":(t.get("default_code") or "").strip(),
                      "Product":t.get("name",""), "Sale Price":float(t.get("list_price") or 0), "On Hand":0}
                     for t in tmpl_map.values()]
            return total,[],{"system":name,"level":"ok","msg":f"No variants, {len(total)} zero stock"}
        quants = _odoo_call(url,db,uid,ak,"stock.quant","search_read",
                            [[("product_id","in",vids), ("location_id.usage","=","internal")]],
                            {"fields":["product_id","location_id","quantity"],"limit":50000})
        tmpl_qty = {}
        branch_rows = []
        for q in quants:
            pid = q["product_id"][0] if isinstance(q["product_id"],list) else q["product_id"]
            tid = v2t.get(pid)
            if tid is None: continue
            qty = float(q.get("quantity") or 0)
            tmpl_qty[tid] = tmpl_qty.get(tid,0)+qty
            loc = q.get("location_id")
            loc_name = loc[1] if isinstance(loc,list) and len(loc)>1 else str(loc or "")
            mc = (tmpl_map.get(tid,{}).get("default_code") or "").strip()
            if mc:
                branch_rows.append({"System":name, "Branch":loc_name, "Model Code":mc, "On Hand":qty})
        total_rows = []
        for tid,t in tmpl_map.items():
            total_rows.append({
                "System":name, "Model Code":(t.get("default_code") or "").strip(),
                "Product":t.get("name",""), "Sale Price":float(t.get("list_price") or 0),
                "On Hand":tmpl_qty.get(tid,0)
            })
        return total_rows, branch_rows, {"system":name,"level":"ok","msg":f"{len(total_rows)} products"}
    except Exception as e:
        return [],[],{"system":name,"level":"error","msg":str(e)}
def fetch_inventory(keys, codes=(), exact=False):
    total, branch, diag = [], [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_inventory_one, k, codes, exact):k for k in keys}
        for f in as_completed(futs):
            t,b,d = f.result()
            total.extend(t); branch.extend(b); diag.append(d)
    total_df = pd.DataFrame(total) if total else pd.DataFrame(columns=["System","Model Code","Product","Sale Price","On Hand"])
    branch_df = pd.DataFrame(branch) if branch else pd.DataFrame(columns=["System","Branch","Model Code","On Hand"])
    return total_df, branch_df, diag

@st.cache_data(ttl=3600)
def _fetch_purchase_summary_one(key, codes, dfrom, dto):
    url,db,uid,ak,name,err = _get_conn(key)
    if err: return pd.DataFrame()
    try:
        lines = _odoo_call(url,db,uid,ak,"purchase.order.line","search_read",
                           [[("order_id.date_approve",">=",f"{dfrom} 00:00:00"),
                             ("order_id.date_approve","<=",f"{dto} 23:59:59"),
                             ("order_id.state","in",["purchase","done"]),
                             ("product_id.default_code","in",list(codes))]],
                           {"fields":["product_id","product_qty"],"limit":10000})
        if not lines: return pd.DataFrame()
        pids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"),list)})
        prods = _odoo_call(url,db,uid,ak,"product.product","search_read",
                           [[["id","in",pids]]], {"fields":["id","default_code"],"limit":len(pids)+10})
        pmap = {p["id"]:p.get("default_code","") for p in prods}
        rows = []
        for l in lines:
            pid = l["product_id"][0] if isinstance(l.get("product_id"),list) else None
            code = pmap.get(pid,"")
            if code: rows.append({"Model Code":code, "qty":float(l.get("product_qty") or 0)})
        if not rows: return pd.DataFrame()
        df = pd.DataFrame(rows).groupby("Model Code")["qty"].sum().reset_index()
        df.columns = ["Model Code","Purchase Qty"]
        return df
    except: return pd.DataFrame()
def fetch_purchase_summary(keys, codes, dfrom, dto):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(_fetch_purchase_summary_one, k, codes, dfrom, dto) for k in keys]
        for f in as_completed(futs):
            df = f.result()
            if not df.empty: results.append(df)
    if not results: return pd.DataFrame(columns=["Model Code","Purchase Qty"])
    return pd.concat(results).groupby("Model Code")["Purchase Qty"].sum().reset_index()

# ------------------------------------------------------------------------------
# POS, Sales, Purchase (simplified but working)
# ------------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def _fetch_pos_one(key, dfrom, dto, branch, model):
    empty = pd.DataFrame(columns=["System","Date","POS Order","Branch","Customer","Cashier","Model Code","Product","Qty","Unit Price","Subtotal","Total Amount"])
    url,db,uid,ak,name,err = _get_conn(key)
    if err: return empty, {"system":name,"level":"error","msg":err}
    try:
        orders = _odoo_call(url,db,uid,ak,"pos.order","search_read",
                            [[("date_order",">=",f"{dfrom} 00:00:00"),("date_order","<=",f"{dto} 23:59:59"),("state","in",["paid","done"])]],
                            {"fields":["id","name","date_order","amount_total","user_id","session_id","partner_id","lines"],"limit":5000})
        if not orders: return empty, {"system":name,"level":"ok","msg":"No orders"}
        sess_ids = list({o["session_id"][0] for o in orders if o.get("session_id")})
        branch_map = {}
        if sess_ids:
            sess = _odoo_call(url,db,uid,ak,"pos.session","search_read",[[["id","in",sess_ids]]],{"fields":["id","config_id"]})
            cfg_ids = list({s["config_id"][0] for s in sess if s.get("config_id")})
            if cfg_ids:
                cfgs = _odoo_call(url,db,uid,ak,"pos.config","search_read",[[["id","in",cfg_ids]]],{"fields":["id","name"]})
                cname = {c["id"]:c["name"] for c in cfgs}
                for s in sess:
                    cid = s["config_id"][0] if isinstance(s.get("config_id"),list) else s.get("config_id")
                    branch_map[s["id"]] = cname.get(cid,"Unknown")
        line_ids = []
        for o in orders:
            if o.get("lines"): line_ids.extend(o["lines"])
        if not line_ids: return empty, {"system":name,"level":"ok","msg":"No lines"}
        lines = _odoo_call(url,db,uid,ak,"pos.order.line","search_read",[[["id","in",line_ids]]],
                           {"fields":["order_id","product_id","qty","price_unit","price_subtotal"]})
        order_map = {o["id"]:o for o in orders}
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"),list)})
        prods = _odoo_call(url,db,uid,ak,"product.product","search_read",[[["id","in",prod_ids]]],
                           {"fields":["id","default_code","name"]}) if prod_ids else []
        prod_map = {p["id"]:p for p in prods}
        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"),list) else line.get("order_id")
            order = order_map.get(oid)
            if not order: continue
            sid = order.get("session_id")
            sid = sid[0] if isinstance(sid,list) else sid
            bname = branch_map.get(sid,"Unknown")
            if branch and branch.lower() not in bname.lower(): continue
            pid = line["product_id"][0] if isinstance(line.get("product_id"),list) else None
            prod = prod_map.get(pid,{})
            code = (prod.get("default_code") or "").strip()
            if model and not code.upper().startswith(model.upper()): continue
            partner = order.get("partner_id")
            cust = partner[1] if isinstance(partner,list) else ""
            user = order.get("user_id")
            cash = user[1] if isinstance(user,list) else ""
            rows.append({
                "System":name, "Date":str(order.get("date_order",""))[:10], "POS Order":order.get("name",""),
                "Branch":bname, "Customer":cust, "Cashier":cash, "Model Code":code, "Product":prod.get("name",""),
                "Qty":float(line.get("qty") or 0), "Unit Price":float(line.get("price_unit") or 0),
                "Subtotal":float(line.get("price_subtotal") or 0), "Total Amount":float(order.get("amount_total") or 0),
            })
        if not rows: return empty, {"system":name,"level":"ok","msg":"No rows after filters"}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df, {"system":name,"level":"ok","msg":f"{len(df)} rows"}
    except Exception as e:
        return empty, {"system":name,"level":"error","msg":str(e)}
def fetch_pos(keys, dfrom, dto, branch, model):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_pos_one, k, dfrom, dto, branch, model):k for k in keys}
        for f in as_completed(futs):
            df, d = f.result()
            diag.append(d)
            if not df.empty: results.append(df)
    if not results: return pd.DataFrame(), diag
    return pd.concat(results), diag

@st.cache_data(ttl=1800)
def _fetch_sales_one(key, dfrom, dto, model):
    empty = pd.DataFrame(columns=["System","Date","SO","Customer","Model Code","Product","Qty","Unit Price","Subtotal","Total Amount","State"])
    url,db,uid,ak,name,err = _get_conn(key)
    if err: return empty, {"system":name,"level":"error","msg":err}
    try:
        orders = _odoo_call(url,db,uid,ak,"sale.order","search_read",
                            [[("date_order",">=",f"{dfrom} 00:00:00"),("date_order","<=",f"{dto} 23:59:59"),("state","in",["sale","done"])]],
                            {"fields":["id","name","date_order","amount_total","partner_id","state","order_line"],"limit":5000})
        if not orders: return empty, {"system":name,"level":"ok","msg":"No orders"}
        order_map = {o["id"]:o for o in orders}
        line_ids = []
        for o in orders:
            if o.get("order_line"): line_ids.extend(o["order_line"])
        if not line_ids: return empty, {"system":name,"level":"ok","msg":"No lines"}
        lines = _odoo_call(url,db,uid,ak,"sale.order.line","search_read",[[["id","in",line_ids]]],
                           {"fields":["order_id","product_id","product_uom_qty","price_unit","price_subtotal"]})
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"),list)})
        prods = _odoo_call(url,db,uid,ak,"product.product","search_read",[[["id","in",prod_ids]]],
                           {"fields":["id","default_code","name"]}) if prod_ids else []
        prod_map = {p["id"]:p for p in prods}
        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"),list) else line.get("order_id")
            order = order_map.get(oid)
            if not order: continue
            pid = line["product_id"][0] if isinstance(line.get("product_id"),list) else None
            prod = prod_map.get(pid,{})
            code = (prod.get("default_code") or "").strip()
            if model and not code.upper().startswith(model.upper()): continue
            partner = order.get("partner_id")
            cust = partner[1] if isinstance(partner,list) else ""
            rows.append({
                "System":name, "Date":str(order.get("date_order",""))[:10], "SO":order.get("name",""),
                "Customer":cust, "Model Code":code, "Product":prod.get("name",""),
                "Qty":float(line.get("product_uom_qty") or 0), "Unit Price":float(line.get("price_unit") or 0),
                "Subtotal":float(line.get("price_subtotal") or 0), "Total Amount":float(order.get("amount_total") or 0),
                "State":order.get("state",""),
            })
        if not rows: return empty, {"system":name,"level":"ok","msg":"No rows"}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df, {"system":name,"level":"ok","msg":f"{len(df)} rows"}
    except Exception as e:
        return empty, {"system":name,"level":"error","msg":str(e)}
def fetch_sales(keys, dfrom, dto, model):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_sales_one, k, dfrom, dto, model):k for k in keys}
        for f in as_completed(futs):
            df, d = f.result()
            diag.append(d)
            if not df.empty: results.append(df)
    if not results: return pd.DataFrame(), diag
    return pd.concat(results), diag

@st.cache_data(ttl=1800)
def _fetch_purchase_one(key, model, dfrom, dto):
    empty = pd.DataFrame(columns=["System","Date","PO","Vendor","Receipt Location","Category","Model Code","Product","Qty","Unit Price","Subtotal"])
    url,db,uid,ak,name,err = _get_conn(key)
    if err: return empty, {"system":name,"level":"error","msg":err}
    try:
        pos = _odoo_call(url,db,uid,ak,"purchase.order","search_read",
                         [[("date_approve",">=",f"{dfrom} 00:00:00"),("date_approve","<=",f"{dto} 23:59:59"),("state","in",["purchase","done"])]],
                         {"fields":["id","name","partner_id","date_approve"],"limit":2000})
        if not pos: return empty, {"system":name,"level":"ok","msg":"No POs"}
        po_map = {p["id"]:p for p in pos}
        po_ids = list(po_map.keys())
        lines = _odoo_call(url,db,uid,ak,"purchase.order.line","search_read",[[["order_id","in",po_ids]]],
                           {"fields":["order_id","product_id","product_qty","price_unit","price_subtotal"],"limit":20000})
        if not lines: return empty, {"system":name,"level":"ok","msg":"No lines"}
        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"),list)})
        prods = _odoo_call(url,db,uid,ak,"product.product","search_read",[[["id","in",prod_ids]]],
                           {"fields":["id","default_code","name","categ_id"]}) if prod_ids else []
        prod_map = {p["id"]:p for p in prods}
        pickings = _odoo_call(url,db,uid,ak,"stock.picking","search_read",
                              [[["origin","in",[p["name"] for p in pos]],["picking_type_code","=","incoming"]]],
                              {"fields":["origin","location_dest_id"],"limit":2000})
        rec_map = {}
        for pick in pickings:
            loc = pick.get("location_dest_id")
            loc_name = loc[1] if isinstance(loc,list) and len(loc)>1 else str(loc or "")
            rec_map[pick.get("origin","")] = loc_name
        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"),list) else line.get("order_id")
            po = po_map.get(oid)
            if not po: continue
            pid = line["product_id"][0] if isinstance(line.get("product_id"),list) else None
            prod = prod_map.get(pid,{})
            code = (prod.get("default_code") or "").strip()
            if model and not code.upper().startswith(model.upper()): continue
            categ = prod.get("categ_id")
            cat = categ[1] if isinstance(categ,list) and len(categ)>1 else ""
            partner = po.get("partner_id")
            vendor = partner[1] if isinstance(partner,list) else ""
            rows.append({
                "System":name, "Date":str(po.get("date_approve",""))[:10], "PO":po.get("name",""),
                "Vendor":vendor, "Receipt Location":rec_map.get(po.get("name",""),""), "Category":cat,
                "Model Code":code, "Product":prod.get("name",""),
                "Qty":float(line.get("product_qty") or 0), "Unit Price":float(line.get("price_unit") or 0),
                "Subtotal":float(line.get("price_subtotal") or 0),
            })
        if not rows: return empty, {"system":name,"level":"ok","msg":"No rows"}
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df, {"system":name,"level":"ok","msg":f"{len(df)} rows"}
    except Exception as e:
        return empty, {"system":name,"level":"error","msg":str(e)}
def fetch_purchase(keys, model, dfrom, dto):
    results, diag = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_purchase_one, k, model, dfrom, dto):k for k in keys}
        for f in as_completed(futs):
            df, d = f.result()
            diag.append(d)
            if not df.empty: results.append(df)
    if not results: return pd.DataFrame(), diag
    return pd.concat(results), diag

# ------------------------------------------------------------------------------
# AI Chat (Simplified)
# ------------------------------------------------------------------------------
def get_ai_response(msg):
    inv = st.session_state.get("inventory_df")
    if inv is not None and not inv.empty:
        if "zero" in msg.lower():
            zero = len(inv[inv["On Hand"]==0])
            return f"🔴 {zero} products have zero stock.", None
        if "total" in msg.lower():
            total_qty = int(inv["On Hand"].sum())
            total_val = float((inv["On Hand"]*inv["Sale Price"]).sum())
            return f"📦 Total stock: {total_qty} units, value SAR {total_val:,.0f}", None
    return "🤖 Ask: inventory summary, zero stock, POS revenue, top customers, etc.", None
def show_chat():
    st.markdown("<div class='section-header'>🤖 AI Executive Assistant</div>", unsafe_allow_html=True)
    for m in st.session_state.chat_history[-20:]:
        if m["role"]=="user":
            st.markdown(f"<div style='background:{th_color("accent1")}20; padding:10px; border-radius:15px; margin:5px 0;'><b>You</b><br>{m['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:{th("card_bg")}; border:1px solid {th("border")}; padding:10px; border-radius:15px; margin:5px 0;'><b>🤖 AI</b><br>{m['content']}</div>", unsafe_allow_html=True)
    with st.form("chat_form"):
        q = st.text_input("Ask something...")
        if st.form_submit_button("Send"):
            if q.strip():
                st.session_state.chat_history.append({"role":"user","content":q})
                ans, _ = get_ai_response(q)
                st.session_state.chat_history.append({"role":"bot","content":ans})
                st.rerun()
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# ------------------------------------------------------------------------------
# Login Page
# ------------------------------------------------------------------------------
def show_login():
    st.markdown(build_css(), unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image("https://via.placeholder.com/150x50?text=SWAG", width=150)  # replace with your logo
        st.markdown(f"<h2 style='text-align:center;'>SWAG Executive</h2>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                ok, err = attempt_login(email.strip(), pwd)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email.strip()
                    token = _make_token(email.strip())
                    st.query_params.update({"u": email.strip(), "t": token})
                    st.rerun()
                else:
                    st.error(err)

# ------------------------------------------------------------------------------
# Main Dashboard
# ------------------------------------------------------------------------------
def show_dashboard():
    st.markdown(build_css(), unsafe_allow_html=True)
    # Sidebar
    with st.sidebar:
        st.markdown(f"<div style='padding:1rem 0; text-align:center;'><h3>💎 SWAG</h3><p>{st.session_state.user_email}</p></div>", unsafe_allow_html=True)
        new_theme = st.selectbox("Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(get_theme()))
        if new_theme != get_theme():
            st.session_state.theme = new_theme
            st.rerun()
        new_lang = st.radio("Language", ["EN","AR"], index=0 if get_lang()=="EN" else 1, horizontal=True)
        if new_lang != get_lang():
            st.session_state.lang = new_lang
            st.rerun()
        st.divider()
        st.markdown("**Connected Systems**")
        for key in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"]:
            cfg = st.secrets.get(key, {})
            icon = "✅" if cfg.get("url") else "❌"
            st.markdown(f"{icon} {get_system_name(key)}")
        st.divider()
        if st.button("Logout", use_container_width=True):
            do_logout()
    # Header
    st.markdown(f"<h1 style='font-size:2rem;'>SWAG Executive Operations</h1><p style='color:{th("text_muted")};'>Multi-Company · Inventory · POS · Sales · Purchasing · AI Insights</p>", unsafe_allow_html=True)
    tabs = st.tabs(["📦 Inventory", "🛒 POS", "🛍️ Sales", "🔖 Purchase", "🤖 AI Chat"])
    # ---------- Inventory Tab ----------
    with tabs[0]:
        st.markdown("<div class='section-header'>📦 Inventory Executive Dashboard</div>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([2,1,1,1])
        with col1:
            co_opts = ["All Companies"] + [get_system_name(k) for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"]]
            inv_co = st.selectbox("Company", co_opts, key="inv_co")
            inv_keys = ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if inv_co=="All Companies" else [k for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if get_system_name(k)==inv_co]
        with col2:
            low_thresh = st.number_input("Low Stock Threshold", min_value=0, value=5, step=1, key="inv_low")
        with col3:
            model_filter = st.text_input("Model Filter", key="inv_model").strip()
        with col4:
            exact = st.checkbox("Exact Match", key="inv_exact")
        if st.button("🔄 Refresh Inventory", type="primary"):
            with st.spinner("Loading..."):
                codes = tuple([model_filter]) if model_filter else ()
                total, branch, diag = fetch_inventory(inv_keys, codes, exact)
                if not total.empty and "Model Code" in total.columns:
                    codes_list = total["Model Code"].dropna().unique().tolist()
                    if codes_list:
                        end = datetime.now().date()
                        start = end - timedelta(days=365)
                        pur = fetch_purchase_summary(inv_keys, tuple(codes_list), start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                        if not pur.empty:
                            total = total.merge(pur, on="Model Code", how="left")
                            total["Purchase Qty"] = total["Purchase Qty"].fillna(0).astype(int)
                        else:
                            total["Purchase Qty"] = 0
                    else:
                        total["Purchase Qty"] = 0
                st.session_state.inventory_df = total
                st.session_state.inventory_branch_df = branch
                st.session_state.inv_diag = diag
                st.session_state.inv_last_refresh = datetime.now()
                st.rerun()
        show_diag(st.session_state.get("inv_diag", []))
        df = st.session_state.get("inventory_df")
        if df is None or df.empty:
            st.info("Click Refresh to load data")
        else:
            # Derived fields
            df["Stock Value"] = df["On Hand"] * df["Sale Price"]
            if "Purchase Qty" not in df.columns:
                df["Purchase Qty"] = 0
            df["Estimated Sold"] = (df["Purchase Qty"] - df["On Hand"]).clip(lower=0)
            df["Sell Through %"] = df.apply(lambda r: (r["Estimated Sold"]/r["Purchase Qty"]*100) if r["Purchase Qty"]>0 else 0, axis=1)
            def status(r):
                oh = r["On Hand"]
                if oh == 0: return "Zero"
                elif oh <= low_thresh: return "Low"
                elif oh <= low_thresh*3: return "Medium"
                else: return "Healthy"
            df["Stock Status"] = df.apply(status, axis=1)
            # KPIs
            k1,k2,k3,k4,k5,k6 = st.columns(6)
            k1.metric("Total On Hand", f"{int(df['On Hand'].sum()):,}")
            k2.metric("Stock Value (SAR)", f"{df['Stock Value'].sum():,.0f}")
            k3.metric("Purchase Qty", f"{int(df['Purchase Qty'].sum()):,}")
            k4.metric("Estimated Sold", f"{int(df['Estimated Sold'].sum()):,}")
            k5.metric("Avg Sell Through %", f"{df['Sell Through %'].mean():.1f}%")
            k6.metric("Low/Zero Count", f"{len(df[df['Stock Status'].isin(['Zero','Low'])]):,}")
            # Charts
            st.markdown("<div class='section-header'>📊 Stock Intelligence</div>", unsafe_allow_html=True)
            # Branch chart
            branch_df = st.session_state.get("inventory_branch_df")
            if branch_df is not None and not branch_df.empty and "Model Code" in branch_df.columns:
                price_map = df.set_index("Model Code")["Sale Price"].to_dict()
                branch_df["Sale Price"] = branch_df["Model Code"].map(price_map).fillna(0)
                branch_df["Stock Value"] = branch_df["On Hand"] * branch_df["Sale Price"]
                branch_val = branch_df.groupby("Branch")["Stock Value"].sum().reset_index().sort_values("Stock Value", ascending=False).head(10)
                fig = px.bar(branch_val, x="Branch", y="Stock Value", title="Branch Stock Value (SAR)", color="Stock Value", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            # Top models
            top = df.nlargest(10, "Stock Value")[["Model Code","Stock Value"]]
            fig2 = px.bar(top, x="Model Code", y="Stock Value", title="Top 10 Models by Stock Value", color="Stock Value", color_continuous_scale=[th_color("accent1"), th_color("accent2")])
            st.plotly_chart(apply_plotly_theme(fig2), use_container_width=True)
            # Health donut
            status_counts = df["Stock Status"].value_counts().reset_index()
            status_counts.columns = ["Status","Count"]
            fig3 = px.pie(status_counts, names="Status", values="Count", hole=0.55, title="Stock Health")
            st.plotly_chart(apply_plotly_theme(fig3), use_container_width=True)
            # Action tables
            st.markdown("<div class='section-header'>⚡ Actionable Insights</div>", unsafe_allow_html=True)
            reorder = df[(df["On Hand"]>0) & (df["On Hand"]<=low_thresh)].copy()
            if not reorder.empty:
                reorder = reorder.sort_values(["On Hand","Stock Value"], ascending=[True,False])
                st.subheader("Reorder Priority")
                render_paginated_table(reorder[["Model Code","Product","On Hand","Stock Value","Sell Through %"]], "inv_reorder")
            dead = df[(df["On Hand"]>low_thresh) & (df["Sell Through %"]<=20)].copy()
            if not dead.empty:
                dead = dead.sort_values("Stock Value", ascending=False)
                st.subheader("Dead / Slow Stock")
                render_paginated_table(dead[["Model Code","Product","On Hand","Stock Value","Purchase Qty","Estimated Sold","Sell Through %"]], "inv_dead")
            st.subheader("Full Inventory Detail")
            render_paginated_table(df[["System","Model Code","Product","Sale Price","On Hand","Purchase Qty","Estimated Sold","Sell Through %","Stock Value","Stock Status"]], "inv_full")
            # Exports
            col_csv, col_xls, col_branch = st.columns(3)
            with col_csv:
                st.download_button("⬇️ CSV", to_csv(localize_df(df)), dl_name("inventory_csv"), "text/csv")
            with col_xls:
                st.download_button("⬇️ Excel", to_excel(localize_df(df)), dl_name("inventory_xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col_branch:
                if branch_df is not None and not branch_df.empty:
                    bdf = branch_df[branch_df["Model Code"].str.contains(model_filter, case=False, na=False)] if model_filter else branch_df
                    # simple branch matrix
                    if not bdf.empty:
                        mat = bdf.pivot_table(index="Model Code", columns="Branch", values="On Hand", aggfunc="sum", fill_value=0)
                        out = io.BytesIO()
                        with pd.ExcelWriter(out, engine="openpyxl") as w:
                            mat.to_excel(w, sheet_name="Branch_Matrix")
                        out.seek(0)
                        st.download_button("📊 Branch Matrix", out, dl_name("branch_matrix"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    # ---------- POS Tab ----------
    with tabs[1]:
        st.markdown("<div class='section-header'>🛒 POS Analytics</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            pos_co = st.selectbox("Company", ["All Companies"]+[get_system_name(k) for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"]], key="pos_co")
            pos_keys = ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if pos_co=="All Companies" else [k for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if get_system_name(k)==pos_co]
        with col2:
            pos_viz = st.selectbox("Visualization", VIZ_MODES, key="pos_viz")
        d1,d2 = st.columns(2)
        with d1: pos_from = st.date_input("From", datetime.now()-timedelta(30), key="pos_from")
        with d2: pos_to = st.date_input("To", datetime.now(), key="pos_to")
        f1,f2 = st.columns(2)
        with f1: pos_branch = st.text_input("Branch filter", key="pos_branch").strip()
        with f2: pos_model = st.text_input("Model filter", key="pos_model").strip()
        if st.button("🔄 Refresh POS", type="primary"):
            with st.spinner("Loading..."):
                df, diag = fetch_pos(pos_keys, pos_from.strftime("%Y-%m-%d"), pos_to.strftime("%Y-%m-%d"), pos_branch, pos_model)
                st.session_state.pos_df = df
                st.session_state.pos_diag = diag
                st.session_state.pos_last_refresh = datetime.now()
                st.rerun()
        show_diag(st.session_state.get("pos_diag", []))
        pos_df = st.session_state.get("pos_df")
        if pos_df is None or pos_df.empty:
            st.info("Click Refresh to load data")
        else:
            unique = pos_df.drop_duplicates(subset=["POS Order"]) if "POS Order" in pos_df.columns else pos_df
            rev = safe_get_col(unique, "Total Amount").sum()
            bills = len(unique)
            qty = safe_get_col(pos_df, "Qty").sum()
            st.metric("Revenue (SAR)", f"{rev:,.0f}")
            st.metric("Bills", f"{bills:,}")
            st.metric("Units Sold", f"{qty:,.0f}")
            st.markdown("<div class='section-header'>📊 POS Performance</div>", unsafe_allow_html=True)
            if has_col(unique, "Branch") and has_col(unique, "Total Amount"):
                agg = unique.groupby("Branch")["Total Amount"].sum().reset_index().sort_values("Total Amount", ascending=False)
                fig = px.bar(agg.head(10), x="Branch", y="Total Amount", title="Revenue by Branch")
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            st.subheader("POS Transactions")
            render_paginated_table(pos_df, "pos_page")
            st.download_button("⬇️ Export POS", to_csv(localize_df(pos_df)), dl_name("pos_csv"), "text/csv")
    # ---------- Sales Tab ----------
    with tabs[2]:
        st.markdown("<div class='section-header'>🛍️ Sales Analytics</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            s_co = st.selectbox("Company", ["All Companies"]+[get_system_name(k) for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"]], key="s_co")
            s_keys = ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if s_co=="All Companies" else [k for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if get_system_name(k)==s_co]
        with col2:
            s_viz = st.selectbox("Visualization", VIZ_MODES, key="s_viz")
        d1,d2 = st.columns(2)
        with d1: s_from = st.date_input("From", datetime.now()-timedelta(30), key="s_from")
        with d2: s_to = st.date_input("To", datetime.now(), key="s_to")
        s_model = st.text_input("Model filter", key="s_model").strip()
        if st.button("🔄 Refresh Sales", type="primary"):
            with st.spinner("Loading..."):
                df, diag = fetch_sales(s_keys, s_from.strftime("%Y-%m-%d"), s_to.strftime("%Y-%m-%d"), s_model)
                st.session_state.sales_df = df
                st.session_state.sales_diag = diag
                st.session_state.sales_last_refresh = datetime.now()
                st.rerun()
        show_diag(st.session_state.get("sales_diag", []))
        sales_df = st.session_state.get("sales_df")
        if sales_df is None or sales_df.empty:
            st.info("Click Refresh")
        else:
            unique = sales_df.drop_duplicates(subset=["SO"]) if "SO" in sales_df.columns else sales_df
            rev = safe_get_col(unique, "Total Amount").sum()
            orders = len(unique)
            st.metric("Revenue (SAR)", f"{rev:,.0f}")
            st.metric("Orders", f"{orders:,}")
            if has_col(unique, "Customer"):
                top_cust = unique.groupby("Customer")["Total Amount"].sum().reset_index().sort_values("Total Amount", ascending=False).head(10)
                fig = px.bar(top_cust, x="Customer", y="Total Amount", title="Top Customers")
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            st.subheader("Sales Details")
            render_paginated_table(sales_df, "sales_page")
            st.download_button("⬇️ Export Sales", to_csv(localize_df(sales_df)), dl_name("sales_csv"), "text/csv")
    # ---------- Purchase Tab ----------
    with tabs[3]:
        st.markdown("<div class='section-header'>🔖 Purchase Analytics</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            p_co = st.selectbox("Company", ["All Companies"]+[get_system_name(k) for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"]], key="p_co")
            p_keys = ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if p_co=="All Companies" else [k for k in ["SWAG","LAROUCHE","DIFFC","FASHION_LIMITS"] if get_system_name(k)==p_co]
        with col2:
            p_viz = st.selectbox("Visualization", VIZ_MODES, key="p_viz")
        d1,d2 = st.columns(2)
        with d1: p_from = st.date_input("From", datetime.now()-timedelta(90), key="p_from")
        with d2: p_to = st.date_input("To", datetime.now(), key="p_to")
        p_model = st.text_input("Model filter", key="p_model").strip()
        if st.button("🔄 Refresh Purchase", type="primary"):
            with st.spinner("Loading..."):
                df, diag = fetch_purchase(p_keys, p_model, p_from.strftime("%Y-%m-%d"), p_to.strftime("%Y-%m-%d"))
                st.session_state.purchase_df = df
                st.session_state.pur_diag = diag
                st.session_state.pur_last_refresh = datetime.now()
                st.rerun()
        show_diag(st.session_state.get("pur_diag", []))
        pur_df = st.session_state.get("purchase_df")
        if pur_df is None or pur_df.empty:
            st.info("Click Refresh")
        else:
            spend = safe_get_col(pur_df, "Subtotal").sum()
            st.metric("Total Spend (SAR)", f"{spend:,.0f}")
            if has_col(pur_df, "Vendor"):
                top_vend = pur_df.groupby("Vendor")["Subtotal"].sum().reset_index().sort_values("Subtotal", ascending=False).head(10)
                fig = px.bar(top_vend, x="Vendor", y="Subtotal", title="Top Vendors")
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
            st.subheader("Purchase History")
            render_paginated_table(pur_df, "pur_page")
            st.download_button("⬇️ Export Purchase", to_csv(localize_df(pur_df)), dl_name("purchase_csv"), "text/csv")
    # ---------- AI Chat ----------
    with tabs[4]:
        show_chat()

# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------
restore_session()
if not st.session_state.get("authenticated"):
    show_login()
else:
    show_dashboard()
