# app.py – PREMIUM EXECUTIVE DASHBOARD (FULLY FIXED VERSION)
# Multi-Company Odoo Operations Dashboard
# Board-of-Directors Level Analytics
# Features: Inventory, POS, Sales, Purchase, Premium Viz, Theme Switcher, AI Insights, Pagination
# BUGS FIXED:
#   1. Arabic mode crash — all column refs use t() variables
#   2. Inventory loading — session_state assignment verified
#   3. Sales tab null check & t() columns
#   4. Purchase tab null check & t() columns
#   5. to_excel_branch_matrix — return b""
#   6. Paginated table HTML — closing </tr> tag
#   7. get_purchase_summary_by_model — all SYSTEM_KEYS
#   8. Language cache — clear data on lang switch

import io
import re
import hashlib
import time
import math
import xmlrpc.client
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Swag",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Dark Executive": {
        "bg": "linear-gradient(135deg,#0f0c29,#302b63,#24243e)",
        "sidebar_bg": "linear-gradient(180deg,#1a1a2e 0%,#16213e 100%)",
        "card_bg": "linear-gradient(145deg,#1e1e3f,#2d2b55)",
        "card_bg_solid": "#1e1e3f",
        "accent1": "#667eea",
        "accent2": "#f093fb",
        "accent3": "#43e97b",
        "accent4": "#f6d365",
        "text": "#e8e8ff",
        "text_muted": "#a0aec0",
        "text_label": "#c4b5fd",
        "border": "#ffffff18",
        "input_bg": "#1e1e3f",
        "metric_gradient": "linear-gradient(90deg,#667eea,#f093fb)",
        "tab_active": "linear-gradient(90deg,#667eea,#764ba2)",
        "title_gradient": "linear-gradient(90deg,#667eea,#f093fb,#43e97b,#667eea)",
        "button_gradient": "linear-gradient(90deg,#667eea,#764ba2,#f093fb,#667eea)",
        "chat_bg": "rgba(26,26,46,0.95)",
        "chat_user_bg": "linear-gradient(135deg,#667eea,#764ba2)",
        "chat_bot_bg": "linear-gradient(135deg,#2d2b55,#1e1e3f)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#667eea","#f093fb","#43e97b","#f6d365","#fda085","#a18cd1","#96fbc4","#f093fb","#4facfe","#43e97b"],
        "danger": "#f43f5e",
        "warning": "#f59e0b",
        "success": "#22c55e",
    },
    "Light Executive": {
        "bg": "linear-gradient(135deg,#f0f4ff,#ffffff,#f8f0ff)",
        "sidebar_bg": "linear-gradient(180deg,#ffffff 0%,#f0f4ff 100%)",
        "card_bg": "linear-gradient(145deg,#ffffff,#f8f8ff)",
        "card_bg_solid": "#ffffff",
        "accent1": "#4f46e5",
        "accent2": "#9333ea",
        "accent3": "#16a34a",
        "accent4": "#d97706",
        "text": "#1e1b4b",
        "text_muted": "#6b7280",
        "text_label": "#4f46e5",
        "border": "#e5e7eb",
        "input_bg": "#ffffff",
        "metric_gradient": "linear-gradient(90deg,#4f46e5,#9333ea)",
        "tab_active": "linear-gradient(90deg,#4f46e5,#7c3aed)",
        "title_gradient": "linear-gradient(90deg,#4f46e5,#9333ea,#16a34a,#4f46e5)",
        "button_gradient": "linear-gradient(90deg,#4f46e5,#7c3aed,#9333ea,#4f46e5)",
        "chat_bg": "rgba(249,250,251,0.98)",
        "chat_user_bg": "linear-gradient(135deg,#4f46e5,#7c3aed)",
        "chat_bot_bg": "linear-gradient(135deg,#f3f4f6,#e5e7eb)",
        "plotly_template": "plotly_white",
        "plotly_colors": ["#4f46e5","#9333ea","#16a34a","#d97706","#dc2626","#0891b2","#7c3aed","#059669","#db2777","#2563eb"],
        "danger": "#dc2626",
        "warning": "#d97706",
        "success": "#16a34a",
    },
    "Luxury Gold": {
        "bg": "linear-gradient(135deg,#0a0800,#1a1400,#0d0a00)",
        "sidebar_bg": "linear-gradient(180deg,#0f0c00 0%,#1a1400 100%)",
        "card_bg": "linear-gradient(145deg,#1a1400,#2a2000)",
        "card_bg_solid": "#1a1400",
        "accent1": "#d4af37",
        "accent2": "#f5c842",
        "accent3": "#c8a415",
        "accent4": "#fff7d4",
        "text": "#f5e6c8",
        "text_muted": "#a89060",
        "text_label": "#d4af37",
        "border": "#d4af3722",
        "input_bg": "#1a1400",
        "metric_gradient": "linear-gradient(90deg,#d4af37,#f5c842)",
        "tab_active": "linear-gradient(90deg,#d4af37,#c8a415)",
        "title_gradient": "linear-gradient(90deg,#d4af37,#f5c842,#fff7d4,#d4af37)",
        "button_gradient": "linear-gradient(90deg,#d4af37,#c8a415,#f5c842,#d4af37)",
        "chat_bg": "rgba(10,8,0,0.97)",
        "chat_user_bg": "linear-gradient(135deg,#d4af37,#c8a415)",
        "chat_bot_bg": "linear-gradient(135deg,#2a2000,#1a1400)",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#d4af37","#f5c842","#c8a415","#fff7d4","#a89060","#8b7536","#f0e68c","#ffd700","#daa520","#b8860b"],
        "danger": "#ff6b6b",
        "warning": "#ffd700",
        "success": "#90ee90",
    },
    "Glass Premium": {
        "bg": "linear-gradient(135deg,#0a0a1a 0%,#1a0a2e 50%,#0a1a2e 100%)",
        "sidebar_bg": "linear-gradient(180deg,rgba(255,255,255,0.05) 0%,rgba(255,255,255,0.02) 100%)",
        "card_bg": "linear-gradient(145deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04))",
        "card_bg_solid": "rgba(255,255,255,0.06)",
        "accent1": "#00d4ff",
        "accent2": "#ff6b9d",
        "accent3": "#00ff88",
        "accent4": "#ffd700",
        "text": "#ffffff",
        "text_muted": "#aaaacc",
        "text_label": "#00d4ff",
        "border": "rgba(255,255,255,0.15)",
        "input_bg": "rgba(255,255,255,0.08)",
        "metric_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d)",
        "tab_active": "linear-gradient(90deg,rgba(0,212,255,0.3),rgba(255,107,157,0.3))",
        "title_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d,#00ff88,#00d4ff)",
        "button_gradient": "linear-gradient(90deg,#00d4ff,#ff6b9d,#00ff88,#00d4ff)",
        "chat_bg": "rgba(0,0,0,0.6)",
        "chat_user_bg": "linear-gradient(135deg,rgba(0,212,255,0.4),rgba(255,107,157,0.4))",
        "chat_bot_bg": "linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04))",
        "plotly_template": "plotly_dark",
        "plotly_colors": ["#00d4ff","#ff6b9d","#00ff88","#ffd700","#ff6b35","#a855f7","#34d399","#fb923c","#818cf8","#2dd4bf"],
        "danger": "#ff6b9d",
        "warning": "#ffd700",
        "success": "#00ff88",
    },
}

def get_theme():
    theme = st.session_state.get("theme", "Dark Executive")
    if theme not in THEMES:
        theme = "Dark Executive"
        st.session_state.theme = theme
    return theme

def th(key):
    return THEMES[get_theme()][key]

def build_css(t_dict):
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,html,body,[class*="css"]{{font-family:'IBM Plex Sans Arabic','Space Grotesk',sans-serif;box-sizing:border-box;}}
.stApp{{background:{t_dict["bg"]};min-height:100vh;}}
section[data-testid="stSidebar"]{{background:{t_dict["sidebar_bg"]}!important;border-right:1px solid {t_dict["border"]};backdrop-filter:blur(20px);}}
section[data-testid="stSidebar"] *,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] div{{color:{t_dict["text"]}!important;}}
section[data-testid="stSidebar"] input{{color:{t_dict["text"]}!important;}}

@keyframes fadeInUp{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInDown{{from{{opacity:0;transform:translateY(-30px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes bounceIn{{0%{{transform:scale(0.2) rotate(-10deg);opacity:0}}60%{{transform:scale(1.2) rotate(5deg);opacity:1}}80%{{transform:scale(0.9)}}100%{{transform:scale(1);opacity:1}}}}
@keyframes shimmer{{0%{{background-position:-400% center}}100%{{background-position:400% center}}}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 {t_dict["accent1"]}44}}50%{{box-shadow:0 0 20px 8px {t_dict["accent1"]}22}}}}
@keyframes glow{{0%,100%{{text-shadow:0 0 10px {t_dict["accent1"]}88}}50%{{text-shadow:0 0 30px {t_dict["accent2"]}cc,0 0 60px {t_dict["accent1"]}88}}}}
@keyframes slideInLeft{{from{{opacity:0;transform:translateX(-40px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes slideInRight{{from{{opacity:0;transform:translateX(40px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
@keyframes btnShine{{0%{{background-position:-200% center}}100%{{background-position:200% center}}}}
@keyframes countUp{{from{{opacity:0;transform:scale(0.5)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes chatSlideIn{{from{{opacity:0;transform:translateX(20px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes cardEntrance{{from{{opacity:0;transform:translateY(20px) scale(0.96)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
@keyframes insightPulse{{0%,100%{{border-color:{t_dict["accent1"]}33}}50%{{border-color:{t_dict["accent1"]}88}}}}

.login-orb{{width:120px;height:120px;border-radius:50%;background:{t_dict["button_gradient"]};display:flex;align-items:center;justify-content:center;font-size:3rem;margin:0 auto 20px;animation:float 3s ease-in-out infinite,bounceIn 1s ease forwards;box-shadow:0 8px 40px {t_dict["accent1"]}66,0 0 60px {t_dict["accent2"]}33;}}
.login-title{{font-size:2.4rem;font-weight:700;background:{t_dict["title_gradient"]};background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s linear infinite,fadeInDown 0.8s ease forwards;text-align:center;margin-bottom:6px;}}
.login-subtitle{{color:{t_dict["text_label"]}!important;font-size:0.95rem;text-align:center;animation:fadeInUp 1s ease forwards;margin-bottom:28px;}}
.login-card{{background:{t_dict["card_bg"]};border:1px solid {t_dict["border"]};border-radius:20px;padding:32px 36px;width:100%;animation:fadeInUp 0.9s ease forwards,pulse 3s infinite;backdrop-filter:blur(20px);}}

.stTextInput input,.stNumberInput input,.stTextArea textarea{{background:{t_dict["input_bg"]}!important;border:1px solid {t_dict["accent1"]}66!important;border-radius:10px!important;color:{t_dict["text"]}!important;caret-color:{t_dict["text_label"]}!important;transition:all 0.3s ease!important;}}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{{border-color:{t_dict["accent1"]}!important;box-shadow:0 0 0 3px {t_dict["accent1"]}33!important;}}
.stTextInput label,.stNumberInput label,.stTextArea label{{color:{t_dict["text_label"]}!important;font-weight:600!important;}}

.stFormSubmitButton button,.stButton button[kind="primary"]{{background:{t_dict["button_gradient"]}!important;background-size:300% auto!important;border:none!important;border-radius:12px!important;color:white!important;font-weight:700!important;font-size:1rem!important;padding:12px!important;animation:btnShine 3s linear infinite!important;transition:transform 0.2s,box-shadow 0.2s!important;box-shadow:0 4px 20px {t_dict["accent1"]}55!important;}}
.stFormSubmitButton button:hover,.stButton button[kind="primary"]:hover{{transform:translateY(-2px) scale(1.02)!important;box-shadow:0 8px 30px {t_dict["accent1"]}99!important;}}
.stButton button[kind="secondary"]{{background:{t_dict["card_bg"]}!important;border:1px solid {t_dict["accent1"]}66!important;color:{t_dict["text_label"]}!important;border-radius:10px!important;}}
.stButton button[kind="secondary"]:hover{{background:{t_dict["tab_active"]}!important;color:white!important;}}
.stButton button{{color:{t_dict["text_label"]}!important;}}
.stDownloadButton button{{background:{t_dict["card_bg"]}!important;border:1px solid {t_dict["accent1"]}66!important;border-radius:10px!important;color:{t_dict["text_label"]}!important;font-size:0.78rem!important;font-weight:600!important;padding:6px 14px!important;transition:all 0.25s ease!important;}}
.stDownloadButton button:hover{{background:{t_dict["tab_active"]}!important;color:white!important;border-color:transparent!important;transform:translateY(-2px) scale(1.04)!important;}}

.dash-header{{text-align:center;padding:16px 0 24px;animation:fadeInDown 0.6s ease forwards;}}
.dash-title{{font-size:2.6rem;font-weight:700;background:{t_dict["title_gradient"]};background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 4s linear infinite,glow 3s ease-in-out infinite;}}
.dash-subtitle{{color:{t_dict["text_muted"]};font-size:0.95rem;margin-top:-4px;}}

[data-testid="stMetric"]{{background:{t_dict["card_bg"]}!important;border:1px solid {t_dict["border"]}!important;border-radius:16px!important;padding:16px 20px!important;animation:cardEntrance 0.6s ease forwards;transition:transform 0.2s,box-shadow 0.2s;backdrop-filter:blur(10px);}}
[data-testid="stMetric"]:hover{{transform:translateY(-4px);box-shadow:0 8px 30px {t_dict["accent1"]}44;}}
[data-testid="stMetricLabel"]{{color:{t_dict["text_muted"]}!important;font-size:0.82rem!important;}}
[data-testid="stMetricValue"]{{font-size:1.7rem!important;font-weight:700!important;background:{t_dict["metric_gradient"]};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
[data-testid="stMetricDelta"]{{font-size:0.85rem!important;}}

.stTabs [data-baseweb="tab-list"]{{background:{t_dict["card_bg"]};border-radius:12px;padding:4px;gap:4px;border:1px solid {t_dict["border"]};}}
.stTabs [data-baseweb="tab"]{{color:{t_dict["text_muted"]}!important;border-radius:10px!important;font-size:0.83rem!important;font-weight:600!important;padding:8px 16px!important;transition:all 0.2s ease!important;}}
.stTabs [aria-selected="true"]{{background:{t_dict["tab_active"]}!important;color:white!important;box-shadow:0 4px 12px {t_dict["accent1"]}55!important;}}

.info-banner{{background:linear-gradient(135deg,{t_dict["accent1"]}22,{t_dict["accent1"]}11);border-left:4px solid {t_dict["accent1"]};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{t_dict["text"]}!important;animation:slideInLeft 0.4s ease;}}
.warn-banner{{background:linear-gradient(135deg,{t_dict["warning"]}22,{t_dict["warning"]}11);border-left:4px solid {t_dict["warning"]};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{t_dict["text"]}!important;}}
.alert-banner{{background:linear-gradient(135deg,{t_dict["danger"]}22,{t_dict["danger"]}11);border-left:4px solid {t_dict["danger"]};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{t_dict["text"]}!important;animation:insightPulse 2s infinite;}}
.ok-banner{{background:linear-gradient(135deg,{t_dict["success"]}22,{t_dict["success"]}11);border-left:4px solid {t_dict["success"]};border-radius:10px;padding:11px 16px;margin:8px 0 16px;font-size:0.85rem;color:{t_dict["text"]}!important;}}

.exec-card{{background:{t_dict["card_bg"]};border:1px solid {t_dict["border"]};border-radius:16px;padding:20px 24px;font-size:0.88rem;color:{t_dict["text"]}!important;line-height:1.9;animation:cardEntrance 0.5s ease;box-shadow:0 4px 20px #00000055;backdrop-filter:blur(10px);transition:all 0.3s ease;}}
.exec-card:hover{{transform:translateY(-3px);box-shadow:0 8px 32px {t_dict["accent1"]}33;border-color:{t_dict["accent1"]}44;}}
.exec-card b,.exec-card strong{{color:{t_dict["text_label"]}!important;}}

.insight-card{{background:{t_dict["card_bg"]};border:1px solid {t_dict["accent1"]}33;border-radius:14px;padding:16px 20px;margin:8px 0;animation:cardEntrance 0.4s ease,insightPulse 4s infinite;backdrop-filter:blur(10px);}}
.insight-title{{font-size:0.78rem;font-weight:700;color:{t_dict["text_muted"]};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;}}
.insight-value{{font-size:1.5rem;font-weight:700;background:{t_dict["metric_gradient"]};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.insight-sub{{font-size:0.82rem;color:{t_dict["text_muted"]};margin-top:3px;}}

.badge-ok{{background:linear-gradient(90deg,#065f46,#047857);color:#d1fae5!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;display:inline-block;}}
.badge-off{{background:linear-gradient(90deg,#991b1b,#b91c1c);color:#fee2e2!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;display:inline-block;}}
.badge-warn{{background:linear-gradient(90deg,#92400e,#b45309);color:#fef3c7!important;border-radius:20px;padding:3px 12px;font-size:0.76rem;font-weight:700;display:inline-block;}}

.stRadio label,.stRadio div[role="radiogroup"] label span,[data-testid="stToggle"] label,.stCheckbox label{{color:{t_dict["text"]}!important;}}
div[data-testid="stRadio"] p{{color:{t_dict["text"]}!important;}}
h1,h2,h3,h4,h5,h6{{color:{t_dict["text"]}!important;}}
.stMarkdown p,.stMarkdown li{{color:{t_dict["text_label"]}!important;}}
.stCaption,[data-testid="stCaptionContainer"] p{{color:{t_dict["text_muted"]}!important;}}
.stAlert p{{color:#1a1a2e!important;font-weight:600;}}
[data-testid="stExpander"]{{background:{t_dict["card_bg"]}!important;border:1px solid {t_dict["border"]}!important;border-radius:12px!important;}}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{{color:{t_dict["text_label"]}!important;}}
hr{{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,{t_dict["accent1"]}66,transparent)!important;margin:16px 0!important;}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:{t_dict["card_bg_solid"]};}}
::-webkit-scrollbar-thumb{{background:{t_dict["tab_active"]};border-radius:10px;}}
.stNumberInput button{{color:{t_dict["text_label"]}!important;background:{t_dict["card_bg"]}!important;}}
footer{{visibility:hidden;}}
[data-baseweb="tag"]{{background:{t_dict["accent1"]}33!important;color:{t_dict["text_label"]}!important;}}
[data-baseweb="select"] div{{background:{t_dict["input_bg"]}!important;color:{t_dict["text"]}!important;border-color:{t_dict["accent1"]}55!important;}}
[data-baseweb="select"] li{{background:{t_dict["card_bg_solid"]}!important;color:{t_dict["text"]}!important;}}

.dataframe-wrap table{{font-family:'IBM Plex Sans Arabic',sans-serif;border-collapse:collapse;width:100%;background:{t_dict["card_bg_solid"]};color:{t_dict["text"]};border-radius:12px;overflow:hidden;font-size:0.84rem;}}
.dataframe-wrap th{{background:{t_dict["tab_active"]};color:white;padding:10px 14px;text-align:center;font-weight:600;white-space:nowrap;}}
.dataframe-wrap td{{padding:8px 14px;text-align:center;border-bottom:1px solid {t_dict["border"]};white-space:nowrap;}}
.dataframe-wrap tr:hover{{background:{t_dict["accent1"]}11;}}

.kpi-tile{{background:{t_dict["card_bg"]};border:1px solid {t_dict["border"]};border-radius:16px;padding:22px;text-align:center;animation:cardEntrance 0.6s ease forwards;transition:all 0.3s ease;backdrop-filter:blur(10px);}}
.kpi-tile:hover{{transform:translateY(-6px);box-shadow:0 12px 40px {t_dict["accent1"]}44;border-color:{t_dict["accent1"]}66;}}
.kpi-tile .kpi-value{{font-size:2rem;font-weight:700;background:{t_dict["metric_gradient"]};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.kpi-tile .kpi-label{{font-size:0.8rem;color:{t_dict["text_muted"]};margin-top:6px;}}
.kpi-tile .kpi-icon{{font-size:2rem;margin-bottom:10px;}}
.kpi-tile .kpi-change{{font-size:0.78rem;margin-top:6px;}}

.viz-selector{{background:{t_dict["card_bg"]};border:1px solid {t_dict["border"]};border-radius:12px;padding:12px 16px;margin-bottom:16px;}}

.chat-panel{{background:{t_dict["chat_bg"]};border:1px solid {t_dict["border"]};border-radius:20px;overflow:hidden;backdrop-filter:blur(20px);box-shadow:0 20px 60px #00000066;}}
.chat-header{{background:{t_dict["tab_active"]};padding:16px 20px;display:flex;align-items:center;gap:12px;}}
.chat-header-avatar{{width:44px;height:44px;border-radius:50%;background:{t_dict["button_gradient"]};display:flex;align-items:center;justify-content:center;font-size:1.4rem;box-shadow:0 4px 12px {t_dict["accent1"]}55;}}
.chat-header-info .chat-name{{font-size:1rem;font-weight:700;color:white;}}
.chat-header-info .chat-status{{font-size:0.74rem;color:rgba(255,255,255,0.75);}}
.chat-messages{{padding:16px;max-height:440px;overflow-y:auto;}}
.chat-msg-user{{background:{t_dict["chat_user_bg"]};color:white;border-radius:18px 18px 4px 18px;padding:12px 16px;margin:6px 0 6px 60px;font-size:0.87rem;animation:chatSlideIn 0.3s ease;box-shadow:0 4px 12px {t_dict["accent1"]}33;line-height:1.6;}}
.chat-msg-bot{{background:{t_dict["chat_bot_bg"]};color:{t_dict["text"]};border:1px solid {t_dict["border"]};border-radius:18px 18px 18px 4px;padding:12px 16px;margin:6px 60px 6px 0;font-size:0.87rem;animation:chatSlideIn 0.3s ease;line-height:1.6;}}
.chat-label-user{{text-align:right;font-size:0.71rem;color:{t_dict["text_muted"]};margin-bottom:2px;padding-right:4px;}}
.chat-label-bot{{text-align:left;font-size:0.71rem;color:{t_dict["text_muted"]};margin-bottom:2px;padding-left:4px;}}
.chat-insight-block{{background:{t_dict["accent1"]}18;border:1px solid {t_dict["accent1"]}44;border-radius:12px;padding:12px 14px;margin:8px 0;font-size:0.84rem;}}
.chat-insight-row{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid {t_dict["border"]};}}
.chat-insight-row:last-child{{border-bottom:none;}}
.chat-insight-key{{color:{t_dict["text_muted"]};}}
.chat-insight-val{{color:{t_dict["text_label"]};font-weight:700;}}
.chat-input-area{{padding:12px 16px;border-top:1px solid {t_dict["border"]};background:{t_dict["card_bg"]};}}
.chip-row{{display:flex;flex-wrap:wrap;gap:6px;padding:10px 16px 0;}}
.chip{{background:{t_dict["accent1"]}22;border:1px solid {t_dict["accent1"]}44;border-radius:20px;padding:5px 12px;font-size:0.76rem;color:{t_dict["text_label"]};cursor:pointer;transition:all 0.2s;display:inline-block;}}
.chip:hover{{background:{t_dict["tab_active"]};color:white;border-color:transparent;}}

.exec-summary-bar{{background:{t_dict["card_bg"]};border:1px solid {t_dict["border"]};border-radius:14px;padding:14px 20px;margin:12px 0;display:flex;align-items:center;justify-content:space-between;animation:slideInLeft 0.4s ease;}}
.trend-up{{color:{t_dict["success"]};font-weight:700;}}
.trend-down{{color:{t_dict["danger"]};font-weight:700;}}
.trend-neutral{{color:{t_dict["text_muted"]};font-weight:700;}}

.pagination-bar{{display:flex;align-items:center;justify-content:center;gap:12px;padding:12px 0;margin-top:8px;}}
.page-info{{color:{t_dict["text_muted"]};font-size:0.84rem;background:{t_dict["card_bg"]};padding:6px 16px;border-radius:20px;border:1px solid {t_dict["border"]};}}

.section-header{{font-size:1.05rem;font-weight:700;color:{t_dict["text_label"]};margin:20px 0 12px;display:flex;align-items:center;gap:8px;padding-bottom:8px;border-bottom:1px solid {t_dict["border"]};}}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_KEYS = ["SWAG", "LAROUCHE", "DIFFC", "FASHION_LIMITS"]
ROWS_PER_PAGE = 30

VIZ_MODES = [
    "📋 List View", "🏆 KPI Tiles", "📊 Column Chart", "📊 Stacked Column",
    "📉 Horizontal Bar", "📈 Line Chart", "📉 Area Chart",
    "🍕 Pie Chart", "🍩 Donut Chart", "🔘 Scatter Chart",
    "🗂️ Funnel Chart", "📡 Radar Chart", "🔺 Pyramid",
]

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_lang():
    return st.session_state.get("lang", "EN")

def t(en, ar):
    return ar if get_lang() == "AR" else en

def get_system_name(key):
    cfg = st.secrets.get(key, {})
    return cfg.get("name_ar", cfg.get("name", key)) if get_lang() == "AR" else cfg.get("name", key)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
_DEF = {
    "authenticated": False,
    "user_email": "",
    "lang": "EN",
    "theme": "Dark Executive",
    "inventory_df": None,
    "inventory_branch_df": None,
    "pos_df": None,
    "sales_df": None,
    "purchase_df": None,
    "chat_history": [],
    "inv_viz_mode": "📋 List View",
    "pos_viz_mode": "📋 List View",
    "sales_viz_mode": "📋 List View",
    "pur_viz_mode": "📋 List View",
    "inv_page": 0,
    "pos_page": 0,
    "sales_page": 0,
    "pur_page": 0,
    "inv_last_refresh": None,
    "pos_last_refresh": None,
    "sales_last_refresh": None,
    "pur_last_refresh": None,
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# SESSION LOGIN RESTORE
# ─────────────────────────────────────────────────────────────────────────────
_COOKIE_SECRET = "swag_exec_2025"

def _make_token(email):
    return hashlib.sha256(f"{_COOKIE_SECRET}_{email}".encode()).hexdigest()[:32]

def _verify_token(email, token):
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

# ─────────────────────────────────────────────────────────────────────────────
# XML-RPC HELPERS
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def localize_columns(df):
    """Rename English column names to current language. Always maps FROM English TO t()."""
    if df is None or df.empty:
        return df
    rename_map = {
        "System": t("System", "النظام"),
        "Model Code": t("Model Code", "رمز الموديل"),
        "Product": t("Product", "المنتج"),
        "Sale Price": t("Sale Price", "سعر البيع"),
        "On Hand": t("On Hand", "متوفر"),
        "Branch": t("Branch", "الفرع"),
        "Location": t("Location", "الموقع"),
        "Date": t("Date", "التاريخ"),
        "POS Order": t("POS Order", "طلب نقطة بيع"),
        "Customer": t("Customer", "العميل"),
        "Cashier": t("Cashier", "الكاشير"),
        "Category": t("Category", "الفئة"),
        "Qty": t("Qty", "الكمية"),
        "Unit Price": t("Unit Price", "سعر الوحدة"),
        "Subtotal": t("Subtotal", "المجموع الفرعي"),
        "SO": t("SO", "أمر بيع"),
        "Vendor": t("Vendor", "المورد"),
        "Receipt Location": t("Receipt Location", "موقع الاستلام"),
        "Purchase Qty": t("Purchase Qty", "كمية الشراء"),
        "Order ID": t("Order ID", "رقم الطلب"),
        "Total Amount": t("Total Amount", "المبلغ الإجمالي"),
        "Bill Number": t("Bill Number", "رقم الفاتورة"),
        "State": t("State", "الحالة"),
        "PO": t("PO", "أمر شراء"),
    }
    # Only rename keys that exist in the dataframe (safe for already-localized dfs)
    to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
    return df.rename(columns=to_rename)

def prepare_df(df):
    """Apply localization and numeric coercion. Returns None-safe result."""
    if df is None or df.empty:
        return df
    df = localize_columns(df)
    if "_status" in df.columns:
        df = df.drop(columns=["_status"])
    # Build numeric cols list for BOTH english and localized names (safe either way)
    numeric_cols = [
        "On Hand", "Sale Price", "Qty", "Unit Price", "Subtotal", "Purchase Qty",
        t("On Hand", "متوفر"), t("Sale Price", "سعر البيع"),
        t("Qty", "الكمية"), t("Unit Price", "سعر الوحدة"),
        t("Subtotal", "المجموع الفرعي"), "Total Amount", t("Total Amount", "المبلغ الإجمالي"),
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def fmt_number(n, prefix="", suffix=""):
    if abs(n) >= 1_000_000:
        return f"{prefix}{n/1_000_000:.2f}M{suffix}"
    if abs(n) >= 1_000:
        return f"{prefix}{n/1_000:.1f}K{suffix}"
    return f"{prefix}{n:,.2f}{suffix}"

def delta_arrow(val, positive_is_good=True):
    if val > 0:
        color = th("success") if positive_is_good else th("danger")
        return f'<span style="color:{color}">▲ {val:+.1f}%</span>'
    elif val < 0:
        color = th("danger") if positive_is_good else th("success")
        return f'<span style="color:{color}">▼ {val:.1f}%</span>'
    return f'<span style="color:{th("text_muted")}">─ 0.0%</span>'

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        try:
            from openpyxl.styles import Font, Alignment, PatternFill
            ws = writer.sheets["Data"]
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
        except Exception:
            pass
    return output.getvalue()

def to_excel_branch_matrix(branch_df):
    """
    BUG FIX #5: was returning undefined `b` — now correctly returns b"" on failure.
    Columns are already localized; use t() variables consistently.
    """
    if branch_df is None or branch_df.empty:
        return b""  # FIX: was `return b` (undefined) → `return b""`

    # branch_df may already be localized; localize_columns is idempotent for that case
    branch_df = localize_columns(branch_df)

    branch_col = t("Branch", "الفرع")
    model_col  = t("Model Code", "رمز الموديل")
    qty_col    = t("On Hand", "متوفر")

    if branch_col not in branch_df.columns or model_col not in branch_df.columns:
        return b""  # FIX: safe fallback

    pivot = branch_df.pivot_table(
        index=model_col, columns=branch_col, values=qty_col,
        aggfunc="sum", fill_value=0,
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pivot.to_excel(writer, sheet_name="Branch_Matrix")
        try:
            from openpyxl.styles import Font, Alignment, PatternFill
            ws = writer.sheets["Branch_Matrix"]
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
        except Exception:
            pass
    return output.getvalue()

def dl_name(prefix, ext):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

# ─────────────────────────────────────────────────────────────────────────────
# PAGINATED TABLE  (BUG FIX #6: closing </tr> tag)
# ─────────────────────────────────────────────────────────────────────────────
def render_paginated_table(df, page_key, rows_per_page=ROWS_PER_PAGE):
    if df is None or df.empty:
        st.markdown(
            f"<div class='info-banner'>ℹ️ {t('No data to display.','لا توجد بيانات للعرض.')}</div>",
            unsafe_allow_html=True,
        )
        return

    if len(df.columns) == 0:
        st.markdown(
            f"<div class='info-banner'>ℹ️ {t('Data has no columns.','البيانات ليس لها أعمدة.')}</div>",
            unsafe_allow_html=True,
        )
        return

    total_rows = len(df)
    total_pages = max(1, math.ceil(total_rows / rows_per_page))
    current_page = st.session_state.get(page_key, 0)
    current_page = min(current_page, total_pages - 1)
    st.session_state[page_key] = current_page

    start = current_page * rows_per_page
    end   = min(start + rows_per_page, total_rows)
    page_df = df.iloc[start:end]

    # Build HTML table — BUG FIX #6: was `"</table>"` at end → must be `"</tr>"`
    table_html = (
        "<div class='dataframe-wrap'><table>"
        "<thead><tr>"
        + "".join(f"<th>{c}</th>" for c in page_df.columns)
        + "</thead><tbody>"
    )
    for _, row in page_df.iterrows():
        table_html += (
            "<tr>"
            + "".join(f"<td>{v}</td>" for v in row.values)
            + "</tr>"   # FIX: was `+ "<tr>"` (duplicate open tag)
        )
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

    # Pagination info
    st.markdown(
        f"<div class='pagination-bar'>"
        f"<span class='page-info'>"
        f"{t('Showing','عرض')} {start+1}–{end} {t('of','من')} {total_rows} {t('records','سجل')}"
        f" &nbsp;|&nbsp; {t('Page','صفحة')} {current_page+1}/{total_pages}"
        f"</span></div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    with col1:
        if st.button(f"⏮ {t('First','أولى')}", key=f"{page_key}_first", use_container_width=True):
            st.session_state[page_key] = 0
            st.rerun()
    with col2:
        if st.button(f"◀ {t('Prev','سابق')}", key=f"{page_key}_prev", use_container_width=True):
            st.session_state[page_key] = max(0, current_page - 1)
            st.rerun()
    with col3:
        st.markdown(
            f"<div style='text-align:center;color:{th('text_muted')};padding:8px 0;font-size:0.83rem;'>"
            f"{current_page+1} / {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with col4:
        if st.button(f"▶ {t('Next','تالي')}", key=f"{page_key}_next", use_container_width=True):
            st.session_state[page_key] = min(total_pages - 1, current_page + 1)
            st.rerun()
    with col5:
        if st.button(f"⏭ {t('Last','أخيرة')}", key=f"{page_key}_last", use_container_width=True):
            st.session_state[page_key] = total_pages - 1
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def apply_plotly_theme(fig):
    if fig is None:
        return
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=th("text"), family="IBM Plex Sans Arabic, Space Grotesk"),
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=th("border")),
    )
    fig.update_xaxes(gridcolor=f"{th('border')}", linecolor=th("border"))
    fig.update_yaxes(gridcolor=f"{th('border')}", linecolor=th("border"))
    return fig

def render_visualization(df, viz_mode, x_col, y_col, label=None, color_col=None):
    if df is None or df.empty:
        st.markdown(
            f"<div class='info-banner'>ℹ️ {t('No data available for visualization.','لا توجد بيانات متاحة للتصور.')}</div>",
            unsafe_allow_html=True,
        )
        return

    colors = th("plotly_colors")
    tmpl   = th("plotly_template")

    if x_col not in df.columns or y_col not in df.columns:
        st.warning(f"Columns not found: {x_col}, {y_col}")
        return

    df_plot = df.copy()
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce").fillna(0)

    if viz_mode == "📋 List View":
        unique_key = f"viz_table_{abs(hash(label or x_col)) % (10**9)}"
        render_paginated_table(df, unique_key)
        return

    df_agg = df_plot.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False)

    if viz_mode == "🏆 KPI Tiles":
        top_n = df_agg.head(8)
        icons = ["📦", "🏆", "⭐", "💎", "🔥", "📈", "🎯", "✅"]
        cols = st.columns(min(4, len(top_n)))
        for i, (_, row) in enumerate(top_n.iterrows()):
            with cols[i % 4]:
                val  = row[y_col]
                name = str(row[x_col])[:22]
                icon = icons[i % len(icons)]
                st.markdown(
                    f"<div class='kpi-tile'>"
                    f"<div class='kpi-icon'>{icon}</div>"
                    f"<div class='kpi-value'>{val:,.0f}</div>"
                    f"<div class='kpi-label'>{name}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        return

    elif viz_mode == "📊 Column Chart":
        fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label or "",
                     color=y_col, color_continuous_scale=[colors[0], colors[1]],
                     template=tmpl, text_auto=".2s")
        fig.update_traces(marker_line_width=0, opacity=0.9)

    elif viz_mode == "📊 Stacked Column":
        sys_col = t("System", "النظام")
        stack_by = color_col if (color_col and color_col in df_plot.columns) else (sys_col if sys_col in df_plot.columns else None)
        if stack_by:
            df_stack = df_plot.groupby([x_col, stack_by])[y_col].sum().reset_index()
            fig = px.bar(df_stack, x=x_col, y=y_col, color=stack_by,
                         title=label or "", barmode="stack", template=tmpl,
                         color_discrete_sequence=colors)
        else:
            fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label or "",
                         template=tmpl, color_discrete_sequence=colors, text_auto=".2s")

    elif viz_mode == "📉 Horizontal Bar":
        fig = px.bar(df_agg.head(15), x=y_col, y=x_col, orientation="h",
                     title=label or "", template=tmpl,
                     color=y_col, color_continuous_scale=[colors[0], colors[1]],
                     text_auto=".2s")
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))

    elif viz_mode == "📈 Line Chart":
        fig = px.line(df_agg.head(30), x=x_col, y=y_col, title=label or "",
                      markers=True, template=tmpl, color_discrete_sequence=[colors[0]])
        fig.update_traces(line_width=3, marker_size=8,
                          line_color=th("accent1"), marker_color=th("accent2"))

    elif viz_mode == "📉 Area Chart":
        fig = px.area(df_agg.head(30), x=x_col, y=y_col, title=label or "",
                      template=tmpl, color_discrete_sequence=[th("accent1")])
        fig.update_traces(fillcolor=f"{th('accent1')}33", line_color=th("accent1"), line_width=2.5)

    elif viz_mode == "🍕 Pie Chart":
        top_n = df_agg.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, title=label or "",
                     color_discrete_sequence=colors, template=tmpl, hole=0)
        fig.update_traces(textposition="inside", textinfo="percent+label")

    elif viz_mode == "🍩 Donut Chart":
        top_n = df_agg.head(10)
        fig = px.pie(top_n, names=x_col, values=y_col, hole=0.55,
                     title=label or "", color_discrete_sequence=colors, template=tmpl)
        fig.update_traces(textposition="inside", textinfo="percent+label")

    elif viz_mode == "🔘 Scatter Chart":
        fig = px.scatter(df_agg.head(30), x=x_col, y=y_col, title=label or "",
                         size=y_col, color=y_col,
                         color_continuous_scale=[colors[0], colors[1]], template=tmpl,
                         size_max=50)

    elif viz_mode == "🗂️ Funnel Chart":
        top_n = df_agg.head(10)
        fig = go.Figure(go.Funnel(
            y=top_n[x_col].astype(str),
            x=top_n[y_col],
            textinfo="value+percent initial",
            marker_color=colors[:len(top_n)],
        ))
        fig.update_layout(title=label or "")

    elif viz_mode == "📡 Radar Chart":
        top_n = df_agg.head(8)
        cats = top_n[x_col].astype(str).tolist()
        vals = top_n[y_col].tolist()
        if len(cats) < 3:
            st.info(t("Radar chart needs at least 3 data points.", "يحتاج مخطط الرادار إلى 3 نقاط بيانات على الأقل."))
            return
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=cats + [cats[0]],
            fill="toself",
            fillcolor=f"{th('accent1')}33",
            line_color=th("accent1"),
            line_width=2,
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, gridcolor=th("border")),
                angularaxis=dict(gridcolor=th("border")),
            ),
            title=label or "",
        )

    elif viz_mode == "🔺 Pyramid":
        top_n = df_agg.head(10).sort_values(y_col)
        fig = px.bar(top_n, x=y_col, y=x_col, orientation="h",
                     title=label or "", template=tmpl,
                     color=y_col, color_continuous_scale=[colors[0], colors[1]],
                     text_auto=".2s")
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))

    else:
        fig = px.bar(df_agg.head(20), x=x_col, y=y_col, title=label or "",
                     template=tmpl, color_discrete_sequence=colors)

    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# VIZ MODE SELECTOR
# ─────────────────────────────────────────────────────────────────────────────
def viz_mode_selector(key):
    st.markdown("<div class='viz-selector'>", unsafe_allow_html=True)
    mode = st.selectbox(
        f"📊 {t('Visualization Mode','نمط العرض')}",
        VIZ_MODES,
        index=VIZ_MODES.index(st.session_state.get(key, "📋 List View")),
        key=key,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return mode

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE INSIGHT BLOCKS
# ─────────────────────────────────────────────────────────────────────────────
def render_exec_summary(df, value_col, label_col, section_title, top_n=5, bottom_n=3):
    if df is None or df.empty or value_col not in df.columns or label_col not in df.columns:
        return

    df_c = df.copy()
    df_c[value_col] = pd.to_numeric(df_c[value_col], errors="coerce").fillna(0)
    agg = df_c.groupby(label_col)[value_col].sum().reset_index().sort_values(value_col, ascending=False)

    st.markdown(f"<div class='section-header'>💡 {section_title}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**🏆 {t('Top Performers','أفضل الأداء')}**")
        top = agg.head(top_n)
        top_html = "<div class='exec-card'>"
        for i, (_, row) in enumerate(top.iterrows()):
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            medal  = medals[i] if i < len(medals) else f"{i+1}."
            top_html += (
                f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                f"border-bottom:1px solid {th('border')};'>"
                f"<span>{medal} {str(row[label_col])[:28]}</span>"
                f"<b style='color:{th('accent1')}'>{row[value_col]:,.0f}</b></div>"
            )
        top_html += "</div>"
        st.markdown(top_html, unsafe_allow_html=True)

    with col2:
        if len(agg) > top_n:
            st.markdown(f"**⚠️ {t('Needs Attention','يحتاج اهتماماً')}**")
            bottom   = agg.tail(bottom_n).sort_values(value_col)
            bot_html = "<div class='exec-card'>"
            for _, row in bottom.iterrows():
                bot_html += (
                    f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
                    f"border-bottom:1px solid {th('border')};'>"
                    f"<span>⚠️ {str(row[label_col])[:28]}</span>"
                    f"<b style='color:{th('danger')}'>{row[value_col]:,.0f}</b></div>"
                )
            bot_html += "</div>"
            st.markdown(bot_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_inventory_cached(codestuple=(), exact=False, lang=None):
    all_rows        = []
    all_branch_rows = []

    for key in SYSTEM_KEYS:
        cfg = st.secrets.get(key)
        if not cfg:
            continue
        uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
        if not uid:
            continue

        u, db, ak  = cfg["url"], cfg["db"], cfg["api_key"]
        system_name = get_system_name(key)

        try:
            prod_domain = []
            if codestuple:
                if exact:
                    prod_domain = [("default_code", "in", list(codestuple))]
                else:
                    clauses = [("default_code", "=ilike", f"{c}%") for c in codestuple]
                    prod_domain = (
                        [clauses[0]] if len(clauses) == 1
                        else ["|"] * (len(clauses) - 1) + clauses
                    )

            products = _x(
                u, db, uid, ak, "product.template", "search_read",
                [prod_domain] if prod_domain else [[]],
                {"fields": ["id", "name", "default_code", "list_price", "categ_id"], "limit": 5000},
            )
            if not products:
                continue

            prod_ids       = [p["id"] for p in products]
            tmpl_to_model  = {p["id"]: (p.get("default_code") or "").strip() for p in products}
            tmpl_to_name   = {p["id"]: p.get("name", "") for p in products}
            tmpl_to_price  = {p["id"]: float(p.get("list_price") or 0) for p in products}

            quants = _x(
                u, db, uid, ak, "stock.quant", "search_read",
                [[
                    ("product_id.product_tmpl_id", "in", prod_ids),
                    ("location_id.usage", "=", "internal"),
                ]],
                {"fields": ["product_id", "location_id", "quantity", "product_id.product_tmpl_id"],
                 "limit": 50000},
            )

            tmpl_qty: dict = {}
            for q in quants:
                tmpl_id_raw = q.get("product_id.product_tmpl_id")
                if isinstance(tmpl_id_raw, list):
                    tmpl_id = tmpl_id_raw[0]
                else:
                    pid_raw  = q.get("product_id")
                    tmpl_id  = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
                qty = float(q.get("quantity") or 0)
                tmpl_qty[tmpl_id] = tmpl_qty.get(tmpl_id, 0) + qty

                loc      = q.get("location_id")
                loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc or "")
                model_code = tmpl_to_model.get(tmpl_id, "")
                if model_code:
                    all_branch_rows.append({
                        "System":     system_name,
                        "Branch":     loc_name,
                        "Model Code": model_code,
                        "On Hand":    qty,
                    })

            for tmpl_id in prod_ids:
                all_rows.append({
                    "System":     system_name,
                    "Model Code": tmpl_to_model.get(tmpl_id, ""),
                    "Product":    tmpl_to_name.get(tmpl_id, ""),
                    "Sale Price": tmpl_to_price.get(tmpl_id, 0),
                    "On Hand":    tmpl_qty.get(tmpl_id, 0),
                    "_status":    "OK",
                })
        except Exception:
            continue

    total_df = (
        pd.DataFrame(all_rows) if all_rows
        else pd.DataFrame(columns=["System", "Model Code", "Product", "Sale Price", "On Hand", "_status"])
    )
    branch_df = (
        pd.DataFrame(all_branch_rows)[["System", "Branch", "Model Code", "On Hand"]]
        if all_branch_rows
        else pd.DataFrame(columns=["System", "Branch", "Model Code", "On Hand"])
    )
    return total_df, branch_df

def fetch_inventory_data(codestuple=(), exact=False, lang=None):
    return fetch_inventory_cached(codestuple=codestuple, exact=exact, lang=lang)

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE SUMMARY — BUG FIX #7: loop through ALL SYSTEM_KEYS, not just SWAG
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_purchase_summary_by_model(model_codes_tuple, date_from, date_to, lang=None):
    """
    BUG FIX #7: Previously only queried SWAG.
    Now loops through all SYSTEM_KEYS and combines results.
    """
    if not model_codes_tuple:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])

    all_results = []

    for sys_key in SYSTEM_KEYS:
        cfg = st.secrets.get(sys_key)
        if not cfg:
            continue
        uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
        if not uid:
            continue
        try:
            domain = [
                ["order_id.date_approve", ">=", f"{date_from} 00:00:00"],
                ["order_id.date_approve", "<=", f"{date_to} 23:59:59"],
                ["order_id.state", "in", ["purchase", "done"]],
                ["product_id.default_code", "in", list(model_codes_tuple)],
            ]
            lines = _x(
                cfg["url"], cfg["db"], uid, cfg["api_key"],
                "purchase.order.line", "search_read", [domain],
                {"fields": ["product_id", "product_qty"], "limit": 10000},
            )
            if not lines:
                continue

            prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
            if not prod_ids:
                continue

            products = _x(
                cfg["url"], cfg["db"], uid, cfg["api_key"],
                "product.product", "search_read",
                [[["id", "in", prod_ids]]],
                {"fields": ["id", "default_code"], "limit": len(prod_ids) + 10},
            )
            prod_map = {p["id"]: p.get("default_code", "") for p in products}

            for line in lines:
                pid   = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
                model = prod_map.get(pid, "")
                if model:
                    all_results.append({
                        "Model Code": model,
                        "qty": float(line.get("product_qty") or 0),
                    })
        except Exception:
            continue

    if not all_results:
        return pd.DataFrame(columns=["Model Code", "Purchase Qty"])

    df = pd.DataFrame(all_results)
    summary = df.groupby("Model Code")["qty"].sum().reset_index()
    summary.columns = ["Model Code", "Purchase Qty"]
    return summary

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_purchase_for_system(system_key, model_code, date_from, date_to, lang=None):
    _empty_cols = [
        "Date", "PO", "Vendor", "Receipt Location", "Category",
        "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "System",
    ]
    empty_df = pd.DataFrame(columns=_empty_cols)

    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak   = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        po_domain = [
            ["date_approve", ">=", f"{date_from} 00:00:00"],
            ["date_approve", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["purchase", "done"]],
        ]
        pos_list = _x(u, db, uid, ak, "purchase.order", "search_read", [po_domain],
                      {"fields": ["id", "name", "partner_id", "date_approve", "state"], "limit": 2000})
        if not pos_list:
            return empty_df

        po_ids = [p["id"] for p in pos_list]
        po_map = {p["id"]: p for p in pos_list}

        lines = _x(u, db, uid, ak, "purchase.order.line", "search_read",
                   [[["order_id", "in", po_ids]]],
                   {"fields": ["order_id", "product_id", "product_qty", "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = _x(u, db, uid, ak, "product.product", "search_read",
                      [[["id", "in", prod_ids]]],
                      {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 10})
        prod_map = {p["id"]: p for p in products}

        pickings = _x(u, db, uid, ak, "stock.picking", "search_read",
                      [[["origin", "in", [p["name"] for p in pos_list]],
                        ["picking_type_code", "=", "incoming"]]],
                      {"fields": ["origin", "location_dest_id"], "limit": 2000})
        receipt_map: dict = {}
        for pick in pickings:
            loc      = pick.get("location_dest_id")
            loc_name = loc[1] if isinstance(loc, list) and len(loc) > 1 else str(loc) if loc else ""
            receipt_map[pick.get("origin", "")] = loc_name

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else None
            po  = po_map.get(oid, {})
            if not po:
                continue
            pid           = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod          = prod_map.get(pid, {})
            model_code_val = (prod.get("default_code") or "").strip()
            if model_code and model_code_val:
                if not model_code_val.upper().startswith(model_code.upper()):
                    continue
            receipt_loc  = receipt_map.get(po.get("name", ""), "")
            categ_obj    = prod.get("categ_id")
            category     = categ_obj[1] if isinstance(categ_obj, list) and len(categ_obj) > 1 else ""
            partner_obj  = po.get("partner_id")
            vendor       = partner_obj[1] if isinstance(partner_obj, list) and len(partner_obj) > 1 else ""
            rows.append({
                "System":           system_name,
                "Date":             str(po.get("date_approve", ""))[:10],
                "PO":               po.get("name", ""),
                "Vendor":           vendor,
                "Receipt Location": receipt_loc,
                "Category":         category,
                "Model Code":       model_code_val,
                "Product":          prod.get("name", ""),
                "Qty":              float(line.get("product_qty") or 0),
                "Unit Price":       float(line.get("price_unit") or 0),
                "Subtotal":         float(line.get("price_subtotal") or 0),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_purchase_multi(selected_keys, model_code, date_from, date_to, lang=None):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(fetch_purchase_for_system, k, model_code, date_from, date_to, lang): k
            for k in selected_keys
        }
        for f in as_completed(futs):
            try:
                df = f.result()
                if df is not None and not df.empty:
                    results.append(df)
            except Exception:
                continue
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# POS FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_pos_for_system(system_key, date_from, date_to, branch_filter, model_filter, lang=None):
    empty_df = pd.DataFrame(columns=[
        "System", "Date", "POS Order", "Branch", "Customer", "Cashier",
        "Model Code", "Product", "Qty", "Unit Price", "Subtotal", "Total Amount",
    ])
    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak   = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        order_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["paid", "done", "invoiced"]],
        ]
        orders = _x(u, db, uid, ak, "pos.order", "search_read", [order_domain],
                    {"fields": ["id", "name", "date_order", "amount_total", "user_id",
                                "session_id", "partner_id", "lines"],
                     "limit": 5000})
        if not orders:
            return empty_df

        session_ids = list({o["session_id"][0] for o in orders if o.get("session_id")})
        branch_map  = {}
        if session_ids:
            sessions   = _x(u, db, uid, ak, "pos.session", "search_read",
                            [[["id", "in", session_ids]]],
                            {"fields": ["id", "config_id"], "limit": len(session_ids) + 10})
            config_ids = list({s["config_id"][0] for s in sessions if s.get("config_id")})
            if config_ids:
                configs      = _x(u, db, uid, ak, "pos.config", "search_read",
                                  [[["id", "in", config_ids]]],
                                  {"fields": ["id", "name"], "limit": len(config_ids) + 10})
                config_name  = {c["id"]: c["name"] for c in configs}
                for s in sessions:
                    branch_map[s["id"]] = config_name.get(
                        s["config_id"][0] if isinstance(s.get("config_id"), list) else s.get("config_id"),
                        "Unknown",
                    )

        line_ids = []
        for o in orders:
            if o.get("lines"):
                line_ids.extend(o["lines"])
        if not line_ids:
            return empty_df

        lines = _x(u, db, uid, ak, "pos.order.line", "search_read",
                   [[["id", "in", line_ids]]],
                   {"fields": ["order_id", "product_id", "qty", "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        order_map = {o["id"]: o for o in orders}
        prod_ids  = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products  = (
            _x(u, db, uid, ak, "product.product", "search_read",
               [[["id", "in", prod_ids]]],
               {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 20})
            if prod_ids else []
        )
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid = line["order_id"][0] if isinstance(line.get("order_id"), list) else line.get("order_id")
            order = order_map.get(oid)
            if not order:
                continue

            sess_id    = order.get("session_id")
            sess_id    = sess_id[0] if isinstance(sess_id, list) else sess_id
            branch_name = branch_map.get(sess_id, "Unknown")
            if branch_filter and branch_filter.strip():
                if branch_filter.lower() not in branch_name.lower():
                    continue

            pid        = line["product_id"][0] if isinstance(line.get("product_id"), list) else None
            prod       = prod_map.get(pid, {})
            model_code = (prod.get("default_code") or "").strip()
            if model_filter and model_filter.strip():
                if not model_code.upper().startswith(model_filter.upper()):
                    continue

            partner  = order.get("partner_id")
            customer = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            user     = order.get("user_id")
            cashier  = user[1] if isinstance(user, list) and len(user) > 1 else ""

            rows.append({
                "System":       system_name,
                "Date":         str(order.get("date_order", ""))[:10],
                "POS Order":    order.get("name", ""),
                "Branch":       branch_name,
                "Customer":     customer,
                "Cashier":      cashier,
                "Model Code":   model_code,
                "Product":      prod.get("name", ""),
                "Qty":          float(line.get("qty") or 0),
                "Unit Price":   float(line.get("price_unit") or 0),
                "Subtotal":     float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_pos_multi(selected_keys, date_from, date_to, branch_filter, model_filter, lang=None):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(fetch_pos_for_system, k, date_from, date_to, branch_filter, model_filter, lang): k
            for k in selected_keys
        }
        for f in as_completed(futs):
            try:
                df = f.result()
                if df is not None and not df.empty:
                    results.append(df)
            except Exception:
                continue
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# SALES FETCH
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sales_for_system(system_key, date_from, date_to, model_filter, lang=None):
    empty_df = pd.DataFrame(columns=[
        "System", "Date", "SO", "Customer", "Model Code", "Product",
        "Qty", "Unit Price", "Subtotal", "Total Amount", "State",
    ])
    cfg = st.secrets.get(system_key)
    if not cfg:
        return empty_df
    uid = _auth(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"])
    if not uid:
        return empty_df

    u, db, ak   = cfg["url"], cfg["db"], cfg["api_key"]
    system_name = get_system_name(system_key)

    try:
        so_domain = [
            ["date_order", ">=", f"{date_from} 00:00:00"],
            ["date_order", "<=", f"{date_to} 23:59:59"],
            ["state", "in", ["sale", "done"]],
        ]
        orders = _x(u, db, uid, ak, "sale.order", "search_read", [so_domain],
                    {"fields": ["id", "name", "date_order", "amount_total",
                                "partner_id", "state", "order_line"],
                     "limit": 5000})
        if not orders:
            return empty_df

        order_map = {o["id"]: o for o in orders}
        line_ids  = []
        for o in orders:
            if o.get("order_line"):
                line_ids.extend(o["order_line"])
        if not line_ids:
            return empty_df

        lines = _x(u, db, uid, ak, "sale.order.line", "search_read",
                   [[["id", "in", line_ids]]],
                   {"fields": ["order_id", "product_id", "product_uom_qty",
                               "price_unit", "price_subtotal"],
                    "limit": 20000})
        if not lines:
            return empty_df

        prod_ids = list({l["product_id"][0] for l in lines if isinstance(l.get("product_id"), list)})
        products = (
            _x(u, db, uid, ak, "product.product", "search_read",
               [[["id", "in", prod_ids]]],
               {"fields": ["id", "default_code", "name", "categ_id"], "limit": len(prod_ids) + 20})
            if prod_ids else []
        )
        prod_map = {p["id"]: p for p in products}

        rows = []
        for line in lines:
            oid_raw = line.get("order_id")
            oid     = oid_raw[0] if isinstance(oid_raw, list) else oid_raw
            order   = order_map.get(oid)
            if not order:
                continue

            pid_raw    = line.get("product_id")
            pid        = pid_raw[0] if isinstance(pid_raw, list) else pid_raw
            prod       = prod_map.get(pid, {})
            model_code = (prod.get("default_code") or "").strip()

            if model_filter and model_filter.strip():
                if not model_code.upper().startswith(model_filter.upper()):
                    continue

            partner  = order.get("partner_id")
            customer = partner[1] if isinstance(partner, list) and len(partner) > 1 else ""
            date_raw = order.get("date_order", "")
            date_str = str(date_raw)[:10] if date_raw else ""

            rows.append({
                "System":       system_name,
                "Date":         date_str,
                "SO":           order.get("name", ""),
                "Customer":     customer,
                "Model Code":   model_code,
                "Product":      prod.get("name", ""),
                "Qty":          float(line.get("product_uom_qty") or 0),
                "Unit Price":   float(line.get("price_unit") or 0),
                "Subtotal":     float(line.get("price_subtotal") or 0),
                "Total Amount": float(order.get("amount_total") or 0),
                "State":        order.get("state", ""),
            })

        if not rows:
            return empty_df
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False).reset_index(drop=True)
    except Exception:
        return empty_df

def fetch_sales_multi(selected_keys, date_from, date_to, model_filter, lang=None):
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(fetch_sales_for_system, k, date_from, date_to, model_filter, lang): k
            for k in selected_keys
        }
        for f in as_completed(futs):
            try:
                df = f.result()
                if df is not None and not df.empty:
                    results.append(df)
            except Exception:
                continue
    if not results:
        return pd.DataFrame()
    combined = pd.concat(results, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined.sort_values("Date", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# AI INSIGHTS PANEL
# ─────────────────────────────────────────────────────────────────────────────
def _build_insight_block(rows_data):
    html = "<div class='chat-insight-block'>"
    for key, val in rows_data:
        html += (
            f"<div class='chat-insight-row'>"
            f"<span class='chat-insight-key'>{key}</span>"
            f"<span class='chat-insight-val'>{val}</span>"
            f"</div>"
        )
    html += "</div>"
    return html

def get_ai_response(user_msg: str) -> tuple:
    msg = user_msg.lower().strip()

    inv_df   = st.session_state.get("inventory_df")
    pos_df   = st.session_state.get("pos_df")
    sales_df = st.session_state.get("sales_df")
    pur_df   = st.session_state.get("purchase_df")

    # Column name vars — always use t() so they match the prepared DFs
    qc          = t("On Hand",        "متوفر")
    sp          = t("Sale Price",      "سعر البيع")
    mc          = t("Model Code",      "رمز الموديل")
    qty_col     = t("Qty",             "الكمية")
    sub_col     = t("Subtotal",        "المجموع الفرعي")
    total_col   = t("Total Amount",    "المبلغ الإجمالي")
    so_col      = t("SO",              "أمر بيع")
    branch_col  = t("Branch",         "الفرع")
    vendor_col  = t("Vendor",         "المورد")
    customer_col = t("Customer",      "العميل")
    cashier_col = t("Cashier",        "الكاشير")
    pos_order_col = t("POS Order",    "طلب نقطة بيع")

    # ── INVENTORY ────────────────────────────────────────────────────────────
    if any(k in msg for k in ["inventory", "stock", "مخزون", "متوفر", "zero", "low stock", "top 10 product", "top product", "fast", "slow"]):
        if inv_df is None or inv_df.empty:
            return (t("📦 No inventory data loaded yet. Please refresh the Inventory tab first.",
                      "📦 لم يتم تحميل بيانات المخزون. يرجى تحديث تبويب المخزون أولاً."), None)

        qty_s   = pd.to_numeric(inv_df.get(qc, pd.Series(dtype=float)), errors="coerce").fillna(0)
        price_s = pd.to_numeric(inv_df.get(sp, pd.Series(dtype=float)), errors="coerce").fillna(0)
        total_qty   = int(qty_s.sum())
        total_value = float((qty_s * price_s).sum())
        zero_count  = int((qty_s == 0).sum())
        low_count   = int(((qty_s > 0) & (qty_s <= 5)).sum())
        models      = inv_df[mc].nunique() if mc in inv_df.columns else 0

        if any(k in msg for k in ["zero", "صفر"]):
            zero_items = inv_df[qty_s == 0][mc].dropna().head(8).tolist() if mc in inv_df.columns else []
            insight = _build_insight_block([
                (t("Zero Stock Models", "موديلات بدون مخزون"), str(zero_count)),
                (t("Examples", "أمثلة"), ", ".join(str(x) for x in zero_items[:4])),
                (t("Action Required", "إجراء مطلوب"), t("Urgent Reorder", "إعادة طلب عاجل")),
            ])
            return (t(f"🔴 Critical Alert: {zero_count} products have zero stock. Immediate restocking recommended.",
                      f"🔴 تنبيه حرج: {zero_count} منتج بدون مخزون. يُنصح بإعادة الطلب الفوري."), insight)

        if any(k in msg for k in ["low", "منخفض", "low stock"]):
            insight = _build_insight_block([
                (t("Low Stock (≤5 units)", "مخزون منخفض (≤5)"), str(low_count)),
                (t("Zero Stock", "مخزون صفر"), str(zero_count)),
                (t("Risk Level", "مستوى الخطر"),
                 t("⚠️ Monitor Closely", "⚠️ مراقبة دقيقة") if low_count > 10 else t("✅ Manageable", "✅ قابل للإدارة")),
            ])
            return (t(f"⚠️ Stock Risk Report: {low_count} products are running low (≤5 units), {zero_count} are completely out of stock.",
                      f"⚠️ تقرير مخاطر المخزون: {low_count} منتج منخفض (≤5 وحدات)، {zero_count} بدون مخزون."), insight)

        if any(k in msg for k in ["top", "أعلى", "fast", "سريع", "best"]):
            if mc in inv_df.columns and qc in inv_df.columns:
                top = inv_df.groupby(mc)[qc].sum().sort_values(ascending=False).head(8)
                rows_data = [(str(k)[:30], f"{int(v):,}") for k, v in top.items()]
                insight = _build_insight_block(rows_data)
                return (t("🏆 Top 8 models by stock quantity:", "🏆 أعلى 8 موديلات من حيث الكمية:"), insight)

        if any(k in msg for k in ["slow", "بطيء", "dead", "راكد"]):
            if mc in inv_df.columns and qc in inv_df.columns:
                slow = inv_df[(qty_s > 0) & (qty_s <= 5)].groupby(mc)[qc].sum().sort_values().head(8)
                rows_data = [(str(k)[:30], f"{int(v):,}") for k, v in slow.items()]
                insight = _build_insight_block(rows_data) if rows_data else None
                return (t("🐌 Slow/dead stock identified — models with ≤5 units in hand:",
                          "🐌 مخزون راكد أو بطيء — موديلات بـ≤5 وحدات:"), insight)

        insight = _build_insight_block([
            (t("Total Stock Qty", "إجمالي الكمية"), f"{total_qty:,}"),
            (t("Total Value (SAR)", "القيمة الإجمالية (ر.س)"), f"{total_value:,.0f}"),
            (t("Distinct Models", "عدد الموديلات"), f"{models:,}"),
            (t("Zero Stock Items", "عناصر بدون مخزون"), f"{zero_count:,} {'⚠️' if zero_count > 20 else '✅'}"),
            (t("Low Stock (≤5)", "مخزون منخفض (≤5)"), f"{low_count:,} {'🔴' if low_count > 50 else '🟡'}"),
        ])
        risk = (t("High Risk", "خطر عالٍ") if zero_count > 50
                else t("Moderate", "معتدل") if zero_count > 20
                else t("Low Risk", "خطر منخفض"))
        return (t(f"📦 Inventory Executive Summary — Stock risk level: {risk}",
                  f"📦 ملخص المخزون التنفيذي — مستوى الخطر: {risk}"), insight)

    # ── POS ──────────────────────────────────────────────────────────────────
    if any(k in msg for k in ["pos", "cashier", "كاشير", "نقطة بيع", "bill", "فاتورة", "branch", "فرع", "pos summary"]):
        if pos_df is None or pos_df.empty:
            return (t("🛒 No POS data loaded. Please refresh the POS tab first.",
                      "🛒 لا توجد بيانات نقاط البيع. يرجى تحديث التبويب أولاً."), None)

        unique_orders = pos_df.drop_duplicates(subset=[pos_order_col]) if pos_order_col in pos_df.columns else pos_df
        total_amt     = float(unique_orders[total_col].sum()) if total_col in unique_orders.columns else 0
        bills         = len(unique_orders)
        avg           = total_amt / bills if bills > 0 else 0
        total_qty_v   = float(pos_df[qty_col].sum()) if qty_col in pos_df.columns else 0

        if any(k in msg for k in ["cashier", "كاشير"]):
            if cashier_col in unique_orders.columns and total_col in unique_orders.columns:
                top = unique_orders.groupby(cashier_col)[total_col].sum().sort_values(ascending=False).head(6)
                rows_data = [(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()]
                insight   = _build_insight_block(rows_data)
                return (t("👤 Cashier Performance Leaderboard — ranked by total sales value:",
                          "👤 ترتيب أداء الكاشيرين حسب إجمالي المبيعات:"), insight)

        if any(k in msg for k in ["branch", "فرع"]):
            if branch_col in unique_orders.columns and total_col in unique_orders.columns:
                top = unique_orders.groupby(branch_col)[total_col].sum().sort_values(ascending=False)
                rows_data = [(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()]
                insight   = _build_insight_block(rows_data)
                best  = rows_data[0][0] if rows_data else "N/A"
                worst = rows_data[-1][0] if len(rows_data) > 1 else "N/A"
                return (t(f"🏪 Branch POS Performance: Best performing — {best}, Needs attention — {worst}",
                          f"🏪 أداء فروع نقاط البيع: الأفضل — {best}، يحتاج اهتماماً — {worst}"), insight)

        insight = _build_insight_block([
            (t("Total POS Revenue (SAR)", "إجمالي إيرادات POS (ر.س)"), f"{total_amt:,.0f}"),
            (t("Total Bills", "إجمالي الفواتير"), f"{bills:,}"),
            (t("Average Bill Value (SAR)", "متوسط قيمة الفاتورة (ر.س)"), f"{avg:,.2f}"),
            (t("Total Units Sold", "إجمالي الوحدات المباعة"), f"{total_qty_v:,.0f}"),
        ])
        return (t(f"🛒 POS Executive Summary — {bills:,} bills processed totaling SAR {total_amt:,.0f}",
                  f"🛒 ملخص POS التنفيذي — {bills:,} فاتورة بإجمالي {total_amt:,.0f} ر.س"), insight)

    # ── SALES ─────────────────────────────────────────────────────────────────
    if any(k in msg for k in ["sale", "مبيعات", "order", "طلب", "customer", "عميل", "sales summary", "revenue"]):
        if sales_df is None or sales_df.empty:
            return (t("🛍️ No sales data loaded. Please refresh the Sales tab first.",
                      "🛍️ لا توجد بيانات مبيعات. يرجى تحديث التبويب أولاً."), None)

        unique_so   = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
        total_sales = float(unique_so[total_col].sum()) if total_col in unique_so.columns else 0
        total_orders = int(unique_so[so_col].nunique()) if so_col in unique_so.columns else len(unique_so)
        total_qty_v  = float(sales_df[qty_col].sum()) if qty_col in sales_df.columns else 0
        avg_ord      = total_sales / total_orders if total_orders > 0 else 0

        if any(k in msg for k in ["customer", "عميل", "top customer"]):
            if customer_col in unique_so.columns and total_col in unique_so.columns:
                top = unique_so.groupby(customer_col)[total_col].sum().sort_values(ascending=False).head(8)
                rows_data = [(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()]
                insight   = _build_insight_block(rows_data)
                return (t("👥 Top Customers by Revenue — key accounts driving your sales:",
                          "👥 أفضل العملاء حسب الإيراد — الحسابات الرئيسية:"), insight)

        if any(k in msg for k in ["top product", "top 10", "أعلى منتج"]):
            if mc in sales_df.columns and qty_col in sales_df.columns:
                top = sales_df.groupby(mc)[qty_col].sum().sort_values(ascending=False).head(10)
                rows_data = [(str(k)[:30], f"{int(v):,} units") for k, v in top.items()]
                insight   = _build_insight_block(rows_data)
                return (t("🏆 Top 10 Products by Quantity Sold:", "🏆 أفضل 10 منتجات حسب الكمية المباعة:"), insight)

        insight = _build_insight_block([
            (t("Total Revenue (SAR)", "إجمالي الإيرادات (ر.س)"), f"{total_sales:,.0f}"),
            (t("Total Orders", "إجمالي الطلبات"), f"{total_orders:,}"),
            (t("Total Units Sold", "إجمالي الوحدات المباعة"), f"{total_qty_v:,.0f}"),
            (t("Average Order Value (SAR)", "متوسط قيمة الطلب (ر.س)"), f"{avg_ord:,.2f}"),
        ])
        return (t(f"🛍️ Sales Executive Summary — SAR {total_sales:,.0f} across {total_orders:,} orders",
                  f"🛍️ ملخص المبيعات التنفيذي — {total_sales:,.0f} ر.س من {total_orders:,} طلب"), insight)

    # ── PURCHASE ──────────────────────────────────────────────────────────────
    if any(k in msg for k in ["purchase", "مشتريات", "vendor", "مورد", "po", "buy", "purchase summary"]):
        if pur_df is None or pur_df.empty:
            return (t("🔖 No purchase data loaded. Please refresh the Purchase tab first.",
                      "🔖 لا توجد بيانات مشتريات. يرجى تحديث التبويب أولاً."), None)

        total_qty_v = float(pd.to_numeric(pur_df.get(qty_col, pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        total_val   = float(pd.to_numeric(pur_df.get(sub_col, pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        vendors     = int(pur_df[vendor_col].nunique()) if vendor_col in pur_df.columns else 0

        if any(k in msg for k in ["vendor", "مورد", "supplier"]):
            if vendor_col in pur_df.columns and sub_col in pur_df.columns:
                top = pur_df.groupby(vendor_col)[sub_col].sum().sort_values(ascending=False).head(8)
                rows_data = [(str(k)[:28], f"SAR {v:,.0f}") for k, v in top.items()]
                insight   = _build_insight_block(rows_data)
                return (t("🏭 Top Vendors by Purchase Value — your key supply chain partners:",
                          "🏭 أفضل الموردين حسب قيمة الشراء:"), insight)

        insight = _build_insight_block([
            (t("Total Purchase Value (SAR)", "إجمالي قيمة الشراء (ر.س)"), f"{total_val:,.0f}"),
            (t("Total Units Purchased", "إجمالي الوحدات المشتراة"), f"{total_qty_v:,.0f}"),
            (t("Active Vendors", "الموردون النشطون"), f"{vendors:,}"),
        ])
        return (t(f"🔖 Purchase Executive Summary — SAR {total_val:,.0f} spent across {vendors:,} vendors",
                  f"🔖 ملخص المشتريات التنفيذي — {total_val:,.0f} ر.س من {vendors:,} مورد"), insight)

    # ── DASHBOARD OVERVIEW ───────────────────────────────────────────────────
    if any(k in msg for k in ["overview", "dashboard", "all", "كل", "ملخص كامل", "executive"]):
        insight_data = []
        if inv_df is not None and not inv_df.empty:
            qty_s = pd.to_numeric(inv_df.get(qc, pd.Series(dtype=float)), errors="coerce").fillna(0)
            insight_data.append((t("📦 Inventory Total Qty", "📦 إجمالي المخزون"), f"{int(qty_s.sum()):,}"))
        if sales_df is not None and not sales_df.empty:
            unique_so = sales_df.drop_duplicates(subset=[so_col]) if so_col in sales_df.columns else sales_df
            s_amt = float(unique_so[total_col].sum()) if total_col in unique_so.columns else 0
            insight_data.append((t("🛍️ Sales Revenue (SAR)", "🛍️ إيرادات المبيعات (ر.س)"), f"{s_amt:,.0f}"))
        if pos_df is not None and not pos_df.empty:
            unique_pos = pos_df.drop_duplicates(subset=[pos_order_col]) if pos_order_col in pos_df.columns else pos_df
            p_amt = float(unique_pos[total_col].sum()) if total_col in unique_pos.columns else 0
            insight_data.append((t("🛒 POS Revenue (SAR)", "🛒 إيرادات POS (ر.س)"), f"{p_amt:,.0f}"))
        if pur_df is not None and not pur_df.empty:
            pur_val = float(pd.to_numeric(pur_df.get(sub_col, pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
            insight_data.append((t("🔖 Purchase Spend (SAR)", "🔖 قيمة المشتريات (ر.س)"), f"{pur_val:,.0f}"))

        insight = _build_insight_block(insight_data) if insight_data else None
        loaded  = [x[0] for x in insight_data]
        return (t(f"💎 Executive Dashboard Overview — {len(loaded)} modules loaded: {', '.join(loaded)}",
                  f"💎 نظرة عامة تنفيذية — {len(loaded)} وحدات محملة"), insight)

    # ── HELP ──────────────────────────────────────────────────────────────────
    if any(k in msg for k in ["help", "مساعدة", "what", "ماذا", "how", "كيف"]):
        insight = _build_insight_block([
            (t("📦 Inventory", "📦 المخزون"),
             t("stock summary, zero stock, low stock, top products", "ملخص المخزون، صفر، منخفض، أفضل منتجات")),
            (t("🛒 POS", "🛒 نقاط البيع"),
             t("branch sales, cashier ranking, bills", "مبيعات الفروع، الكاشير، الفواتير")),
            (t("🛍️ Sales", "🛍️ المبيعات"),
             t("revenue, top customers, order summary", "الإيراد، العملاء، ملخص الطلبات")),
            (t("🔖 Purchase", "🔖 المشتريات"),
             t("vendor ranking, spend summary", "ترتيب الموردين، ملخص الإنفاق")),
            (t("💎 Overview", "💎 نظرة عامة"),
             t("executive dashboard overview", "نظرة تنفيذية شاملة")),
        ])
        return (t("💡 Here's what I can analyze from your loaded data:",
                  "💡 إليك ما يمكنني تحليله من بياناتك المحملة:"), insight)

    return (t(
        "🤖 I can analyze your loaded dashboard data. Try: 'inventory summary', 'top customers', 'POS branch sales', 'vendor ranking', or 'executive overview'.",
        "🤖 يمكنني تحليل بياناتك. جرب: 'ملخص المخزون'، 'أفضل العملاء'، 'مبيعات فروع POS'، 'أفضل الموردين'، أو 'نظرة عامة'.",
    ), None)

def show_chat_panel():
    st.markdown("<div class='chat-panel'>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='chat-header'>
      <div class='chat-header-avatar'>🤖</div>
      <div class='chat-header-info'>
        <div class='chat-name'>{t('Executive AI Insights','المساعد الذكي التنفيذي')}</div>
        <div class='chat-status'>● {t('Analyzing loaded dashboard data','يحلل بيانات اللوحة المحملة')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    chips = [
        t("💎 Executive Overview", "💎 نظرة تنفيذية"),
        t("📦 Inventory Summary", "📦 ملخص المخزون"),
        t("🔴 Zero Stock Alert", "🔴 تنبيه مخزون صفر"),
        t("🛒 POS Branch Sales", "🛒 مبيعات فروع POS"),
        t("👥 Top Customers", "👥 أفضل العملاء"),
        t("🏭 Top Vendors", "🏭 أفضل الموردين"),
        t("🏆 Top Products", "🏆 أفضل المنتجات"),
        t("⚠️ Low Stock", "⚠️ مخزون منخفض"),
        t("💡 Help", "💡 مساعدة"),
    ]
    chips_html = "<div class='chip-row'>" + "".join(f"<span class='chip'>{c}</span>" for c in chips) + "</div>"
    st.markdown(chips_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    history_html = "<div class='chat-messages'>"
    if not st.session_state.chat_history:
        history_html += f"""
        <div style='text-align:center;padding:30px 20px;'>
          <div style='font-size:2.5rem;margin-bottom:12px;'>💎</div>
          <div style='color:{th("text")};font-size:1rem;font-weight:600;margin-bottom:8px;'>
            {t('Welcome to Executive AI Insights','مرحباً في المساعد الذكي التنفيذي')}
          </div>
          <div style='color:{th("text_muted")};font-size:0.85rem;'>
            {t('Click a chip above or type your question below','انقر على أحد الاختصارات أعلاه أو اكتب سؤالك')}
          </div>
        </div>"""
    for msg in st.session_state.chat_history[-30:]:
        if msg["role"] == "user":
            history_html += f"<div class='chat-label-user'>{t('You','أنت')}</div>"
            history_html += f"<div class='chat-msg-user'>{msg['content']}</div>"
        else:
            history_html += f"<div class='chat-label-bot'>🤖 {t('AI Insight','تحليل ذكي')}</div>"
            history_html += f"<div class='chat-msg-bot'>{msg['content'].replace(chr(10),'<br>')}</div>"
            if msg.get("insight_html"):
                history_html += msg["insight_html"]
    history_html += "</div>"
    st.markdown(history_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**{t('Quick Insights:','تحليلات سريعة:')}**")
    chip_cols = st.columns(3)
    chip_actions = [
        (t("💎 Overview", "💎 نظرة عامة"),    t("executive overview", "نظرة تنفيذية")),
        (t("📦 Inventory", "📦 المخزون"),      t("inventory summary", "ملخص المخزون")),
        (t("🔴 Zero Stock", "🔴 مخزون صفر"),   t("zero stock", "مخزون صفر")),
        (t("🛒 POS Branches", "🛒 فروع POS"),  t("POS branch sales", "مبيعات فروع POS")),
        (t("👥 Customers", "👥 العملاء"),       t("top customers", "أفضل العملاء")),
        (t("🏭 Vendors", "🏭 الموردون"),        t("top vendors", "أفضل الموردين")),
    ]
    for i, (label, query) in enumerate(chip_actions):
        with chip_cols[i % 3]:
            if st.button(label, key=f"chip_btn_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": label})
                text, insight_html = get_ai_response(query)
                st.session_state.chat_history.append({"role": "bot", "content": text, "insight_html": insight_html or ""})
                st.rerun()

    col_in, col_send, col_clear = st.columns([5, 1, 1])
    with col_in:
        user_input = st.text_input(
            t("Ask the AI...", "اسأل الذكاء الاصطناعي..."),
            key="chat_input",
            label_visibility="collapsed",
            placeholder=t(
                "e.g. Show me low stock alerts, top customers, branch performance...",
                "مثال: أظهر المخزون المنخفض، أفضل العملاء، أداء الفروع...",
            ),
        )
    with col_send:
        if st.button(t("Send", "إرسال"), type="primary", use_container_width=True, key="chat_send"):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                text, insight_html = get_ai_response(user_input)
                st.session_state.chat_history.append({"role": "bot", "content": text, "insight_html": insight_html or ""})
                st.rerun()
    with col_clear:
        if st.button("🗑️", use_container_width=True, key="chat_clear"):
            st.session_state.chat_history = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown(build_css(THEMES[get_theme()]), unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-orb'>💎</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>Executive Operations</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-subtitle'>Multi-Company Analytics · Board-Level Dashboard</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            email     = st.text_input("Email", placeholder="user@company.com")
            password  = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
            if submitted:
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user_email    = email
                    token = _make_token(email)
                    st.query_params.update({"u": email, "t": token})
                    st.rerun()
                else:
                    st.error("Please enter your credentials.")
        st.markdown("</div>", unsafe_allow_html=True)

def do_logout():
    st.session_state.authenticated = False
    st.session_state.user_email    = ""
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def show_dashboard():
    theme = get_theme()
    if theme not in THEMES:
        theme = "Dark Executive"
        st.session_state.theme = theme
    t_dict = THEMES[theme]
    st.markdown(build_css(t_dict), unsafe_allow_html=True)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style='background:{t_dict["card_bg"]};border:1px solid {t_dict["border"]};border-radius:14px;padding:14px;margin-bottom:16px;text-align:center;'>
          <div style='font-size:2rem;margin-bottom:4px;'>💎</div>
          <div style='font-size:0.9rem;font-weight:700;color:{t_dict["text"]};'>Executive Dashboard</div>
          <div style='font-size:0.72rem;color:{t_dict["text_muted"]};margin-top:2px;'>{st.session_state.user_email}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**🎨 {t('Theme','المظهر')}**")
        new_theme = st.selectbox(
            t("Select Theme", "اختر المظهر"),
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(theme),
            key="theme_select",
            label_visibility="collapsed",
        )
        if new_theme != theme:
            st.session_state.theme = new_theme
            st.rerun()

        st.divider()

        # BUG FIX #8: clear all data DFs when language changes so cached column names refresh
        lc = st.radio(t("🌐 Language", "🌐 اللغة"), ["EN", "AR"],
                      index=0 if get_lang() == "EN" else 1, horizontal=True)
        if lc != get_lang():
            st.session_state.lang                  = lc
            # Clear all data — column names are baked into the DFs at prepare_df() time
            st.session_state.inventory_df          = None
            st.session_state.inventory_branch_df   = None
            st.session_state.pos_df                = None
            st.session_state.sales_df              = None
            st.session_state.purchase_df           = None
            st.rerun()

        st.divider()

        st.markdown(f"**🏢 {t('Connected Systems','الأنظمة المتصلة')}**")
        for key in SYSTEM_KEYS:
            cfg    = st.secrets.get(key, {})
            name   = get_system_name(key)
            badge  = "badge-ok" if cfg else "badge-off"
            status = "✓" if cfg else "✗"
            st.markdown(f"<div style='margin:4px 0;'><span class='{badge}'>{status} {name}</span></div>", unsafe_allow_html=True)

        st.divider()

        st.markdown(f"**📊 {t('Loaded Data','البيانات المحملة')}**")
        modules = [
            ("📦", t("Inventory", "المخزون"),   st.session_state.get("inventory_df"), "inv_last_refresh"),
            ("🛒", t("POS", "نقاط البيع"),       st.session_state.get("pos_df"),       "pos_last_refresh"),
            ("🛍️", t("Sales", "المبيعات"),       st.session_state.get("sales_df"),     "sales_last_refresh"),
            ("🔖", t("Purchase", "المشتريات"),   st.session_state.get("purchase_df"),  "pur_last_refresh"),
        ]
        for icon, name, df, ts_key in modules:
            if df is not None and not df.empty:
                ts     = st.session_state.get(ts_key)
                ts_str = f" ({ts.strftime('%H:%M')})" if ts else ""
                st.markdown(f"<span class='badge-ok'>{icon} {name} ({len(df):,}){ts_str}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='badge-warn'>{icon} {name} —</span>", unsafe_allow_html=True)

        st.divider()
        if st.button(f"🚪 {t('Logout','تسجيل الخروج')}", use_container_width=True):
            do_logout()

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='dash-header'>
        <div class='dash-title'>SWAG - MULTI DASHBOARD</div>
        <div class='dash-subtitle'>{t('Multi-Company · Inventory · POS · Sales · Purchase · AI Insights','متعدد الشركات · المخزون · نقاط البيع · المبيعات · المشتريات · تحليلات ذكية')}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    # ── MAIN TABS ─────────────────────────────────────────────────────────────
    tab_inv, tab_pos, tab_sales, tab_pur, tab_chat = st.tabs([
        f"📦 {t('Inventory','المخزون')}",
        f"🛒 {t('POS','نقاط البيع')}",
        f"🛍️ {t('Sales','المبيعات')}",
        f"🔖 {t('Purchase','المشتريات')}",
        f"🤖 {t('AI Insights','تحليلات ذكية')}",
    ])

    # =========================================================================
    # INVENTORY TAB
    # =========================================================================
    with tab_inv:
        st.markdown(f"<div class='section-header'>📦 {t('Inventory Overview','نظرة عامة على المخزون')}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='exec-summary-bar'>💡 {t('Monitor stock levels, identify slow movers, and manage replenishment across all branches.','مراقبة مستويات المخزون، تحديد المنتجات بطيئة الحركة، وإدارة إعادة التموين عبر جميع الفروع.')}</div>",
            unsafe_allow_html=True,
        )

        co1, co2, co3 = st.columns([2, 2, 1])
        with co1:
            company_options  = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
            selected_company = st.selectbox(t("Select Company", "اختر الشركة"), options=company_options, index=0, key="inv_company")
            inv_keys = (SYSTEM_KEYS if selected_company == t("All Companies", "جميع الشركات")
                        else [k for k in SYSTEM_KEYS if get_system_name(k) == selected_company])
        with co2:
            low_thresh = st.number_input(t("Low stock threshold", "حد المخزون المنخفض"),
                                         min_value=0, max_value=1000, value=5, step=1, key="inv_low_thresh")
        with co3:
            exact_match = st.toggle(t("Exact match", "تطابق تام"), value=False, key="inv_exact")

        fc1, fc2 = st.columns([3, 1])
        with fc1:
            model_filter = st.text_input(t("Model Code filter (optional)", "فلتر رمز الموديل (اختياري)"), key="inv_model_filter").strip()
        with fc2:
            if st.button(t("Reset Filters", "إعادة تعيين"), key="inv_reset_filters"):
                st.session_state.inv_model_filter = ""
                st.session_state.inv_company      = t("All Companies", "جميع الشركات")
                st.session_state.inv_low_thresh   = 5
                st.session_state.inv_exact        = False
                st.rerun()

        inv_viz_mode = viz_mode_selector("inv_viz_mode")

        if st.button(f"🔄 {t('Refresh Inventory','تحديث المخزون')}", type="primary"):
            with st.spinner(t("Fetching inventory data...", "جاري جلب بيانات المخزون...")):
                codes = tuple([model_filter]) if model_filter else ()
                raw_total_df, raw_branch_df = fetch_inventory_data(
                    codestuple=codes, exact=exact_match, lang=st.session_state.lang
                )

                # ── company filter (on raw english-col DF) ─────────────────
                if raw_total_df is not None and not raw_total_df.empty:
                    if selected_company != t("All Companies", "جميع الشركات"):
                        allowed = {get_system_name(k) for k in inv_keys}
                        if "System" in raw_total_df.columns:
                            raw_total_df = raw_total_df[raw_total_df["System"].isin(allowed)]

                    # Purchase qty overlay — all companies (BUG FIX #7 already in function)
                    if "System" in raw_total_df.columns and "Model Code" in raw_total_df.columns and not raw_total_df.empty:
                        mc_vals = raw_total_df["Model Code"].dropna().unique().tolist()
                        if mc_vals:
                            end_d   = datetime.now().date()
                            start_d = end_d - timedelta(days=365)
                            pur_sum = get_purchase_summary_by_model(
                                tuple(mc_vals),
                                start_d.strftime("%Y-%m-%d"),
                                end_d.strftime("%Y-%m-%d"),
                                lang=st.session_state.lang,
                            )
                            if pur_sum is not None and not pur_sum.empty:
                                raw_total_df = raw_total_df.merge(pur_sum, on="Model Code", how="left")
                                raw_total_df["Purchase Qty"] = raw_total_df["Purchase Qty"].fillna(0).astype(int)
                            else:
                                raw_total_df["Purchase Qty"] = 0
                        else:
                            raw_total_df["Purchase Qty"] = 0
                    else:
                        if raw_total_df is not None and not raw_total_df.empty:
                            raw_total_df["Purchase Qty"] = 0

                # ── branch df company filter ────────────────────────────────
                if raw_branch_df is not None and not raw_branch_df.empty:
                    if selected_company != t("All Companies", "جميع الشركات"):
                        allowed = {get_system_name(k) for k in inv_keys}
                        if "System" in raw_branch_df.columns:
                            raw_branch_df = raw_branch_df[raw_branch_df["System"].isin(allowed)]

                # BUG FIX #2: always persist to session_state
                st.session_state.inventory_df        = prepare_df(raw_total_df)
                st.session_state.inventory_branch_df = prepare_df(raw_branch_df)
                st.session_state.inv_page            = 0
                st.session_state.inv_last_refresh    = datetime.now()

        total_df  = st.session_state.get("inventory_df")
        branch_df = st.session_state.get("inventory_branch_df")

        if total_df is None or total_df.empty:
            st.markdown(
                f"<div class='info-banner'>ℹ️ {t('Click Refresh Inventory to load data.','اضغط تحديث المخزون لتحميل البيانات.')}</div>",
                unsafe_allow_html=True,
            )
        else:
            # All column refs use t() — safe in both EN and AR
            qc    = t("On Hand",    "متوفر")
            sp    = t("Sale Price", "سعر البيع")
            mc    = t("Model Code", "رمز الموديل")
            br_c  = t("Branch",    "الفرع")
            sys_c = t("System",    "النظام")
            pur_c = t("Purchase Qty", "كمية الشراء")

            qty_s   = pd.to_numeric(total_df.get(qc,  pd.Series(dtype=float)), errors="coerce").fillna(0)
            price_s = pd.to_numeric(total_df.get(sp,  pd.Series(dtype=float)), errors="coerce").fillna(0)
            total_qty       = int(qty_s.sum())
            total_value     = float((qty_s * price_s).sum())
            distinct_models = int(total_df[mc].nunique()) if mc in total_df.columns else 0
            distinct_branches = (
                int(branch_df[br_c].nunique())
                if (branch_df is not None and not branch_df.empty and br_c in branch_df.columns)
                else 0
            )
            zero_count = int((qty_s == 0).sum())
            low_count  = int(((qty_s > 0) & (qty_s <= low_thresh)).sum())

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric(t("Total Qty", "إجمالي الكمية"),        f"{total_qty:,}")
            c2.metric(t("Inventory Value", "قيمة المخزون"),    f"SAR {total_value:,.0f}")
            c3.metric(t("Models", "الموديلات"),                f"{distinct_models:,}")
            c4.metric(t("Branches", "الفروع"),                 f"{distinct_branches:,}")
            c5.metric(t("Zero Stock", "صفر مخزون"), f"{zero_count:,}",
                      delta=f"-{zero_count}" if zero_count > 0 else None, delta_color="inverse")
            c6.metric(t(f"Low ≤{low_thresh}", f"منخفض ≤{low_thresh}"), f"{low_count:,}",
                      delta=f"-{low_count}" if low_count > 0 else None, delta_color="inverse")
            st.divider()

            if zero_count > 0:
                st.markdown(
                    f"<div class='alert-banner'>🔴 {zero_count} {t('products have zero stock — immediate action required','منتج بدون مخزون — إجراء فوري مطلوب')}</div>",
                    unsafe_allow_html=True,
                )
            if low_count > 0:
                st.markdown(
                    f"<div class='warn-banner'>⚠️ {low_count} {t(f'products have low stock (≤{low_thresh} units)',f'منتج مخزون منخفض (≤{low_thresh} وحدة)')}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(f"<div class='section-header'>📊 {t('Inventory Visualization','تصور المخزون')}</div>", unsafe_allow_html=True)
            if mc in total_df.columns and qc in total_df.columns:
                render_visualization(total_df, inv_viz_mode, mc, qc, t("Stock Quantity by Model", "الكمية حسب الموديل"))
            st.divider()

            if mc in total_df.columns and qc in total_df.columns:
                render_exec_summary(total_df, qc, mc, t("Stock Performance Analysis", "تحليل أداء المخزون"))
                st.divider()

            if branch_df is not None and not branch_df.empty and br_c in branch_df.columns and qc in branch_df.columns:
                st.markdown(f"<div class='section-header'>🏪 {t('Branch-wise Stock Distribution','توزيع المخزون حسب الفرع')}</div>", unsafe_allow_html=True)
                branch_agg = branch_df.groupby(br_c)[qc].sum().reset_index().sort_values(qc, ascending=False)
                fig_branch = px.bar(branch_agg, x=br_c, y=qc,
                                    color=qc, color_continuous_scale=[th("accent1"), th("accent2")],
                                    template=th("plotly_template"), text_auto=".2s")
                st.plotly_chart(apply_plotly_theme(fig_branch), use_container_width=True)
                st.divider()

            st.markdown(f"<div class='section-header'>📋 {t('Inventory Detail (Filtered to Low Stock)','تفاصيل المخزون (مفلتر للمنخفض)')}</div>", unsafe_allow_html=True)
            display_df_filtered = total_df[qty_s <= low_thresh].copy() if low_thresh is not None else total_df.copy()
            render_paginated_table(display_df_filtered, "inv_page")
            st.markdown("<br>", unsafe_allow_html=True)

            with st.expander(f"📋 {t('Show Full Inventory Table','عرض جدول المخزون الكامل')}"):
                render_paginated_table(total_df, "inv_full_page")

            st.markdown("<br>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button("⬇️ CSV", to_csv(total_df), dl_name("inventory", "csv"), "text/csv", use_container_width=True)
            with d2:
                st.download_button("⬇️ Excel", to_excel(total_df), dl_name("inventory", "xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with d3:
                if branch_df is not None and not branch_df.empty:
                    mc_col = t("Model Code", "رمز الموديل")
                    bdf_f  = (branch_df[branch_df[mc_col].str.contains(model_filter, case=False, na=False)]
                              if (model_filter and mc_col in branch_df.columns) else branch_df)
                    st.download_button(
                        f"📊 {t('Branch Matrix Excel','Excel مصفوفة الفروع')}",
                        to_excel_branch_matrix(bdf_f),
                        dl_name("branch_matrix", "xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    # =========================================================================
    # POS TAB
    # =========================================================================
    with tab_pos:
        st.markdown(f"<div class='section-header'>🛒 {t('POS Sales Analytics','تحليلات مبيعات نقاط البيع')}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='exec-summary-bar'>💡 {t('Real-time POS performance by branch, cashier, and product. Monitor daily revenue and customer behavior.','أداء نقاط البيع في الوقت الفعلي حسب الفرع والكاشير والمنتج. مراقبة الإيرادات اليومية وسلوك العملاء.')}</div>",
            unsafe_allow_html=True,
        )

        pos_co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
        pos_co = st.selectbox(t("Select Company", "اختر الشركة"), options=pos_co_opts, index=0, key="pos_company")
        pos_keys = (SYSTEM_KEYS if pos_co == t("All Companies", "جميع الشركات")
                    else [k for k in SYSTEM_KEYS if get_system_name(k) == pos_co])

        pdc1, pdc2 = st.columns(2)
        with pdc1:
            pos_date_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=30), key="pos_date_from")
        with pdc2:
            pos_date_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="pos_date_to")

        pfc1, pfc2 = st.columns(2)
        with pfc1:
            pos_branch_filter = st.text_input(t("Branch filter (optional)", "فلتر الفرع (اختياري)"), key="pos_branch_filter").strip()
        with pfc2:
            pos_model_filter = st.text_input(t("Model Code (optional)", "رمز الموديل (اختياري)"), key="pos_model_filter").strip()

        if st.button(t("Reset Filters", "إعادة تعيين"), key="pos_reset_filters"):
            st.session_state.pos_branch_filter = ""
            st.session_state.pos_model_filter  = ""
            st.session_state.pos_company        = t("All Companies", "جميع الشركات")
            st.rerun()

        pos_viz_mode = viz_mode_selector("pos_viz_mode")

        if st.button(f"🔄 {t('Refresh POS Data','تحديث بيانات نقاط البيع')}", type="primary"):
            with st.spinner(t("Fetching POS data...", "جاري جلب بيانات نقاط البيع...")):
                raw_pos = fetch_pos_multi(
                    pos_keys,
                    pos_date_from.strftime("%Y-%m-%d"),
                    pos_date_to.strftime("%Y-%m-%d"),
                    pos_branch_filter, pos_model_filter,
                    lang=st.session_state.lang,
                )
                # BUG FIX #3: null check before filtering
                if raw_pos is not None and not raw_pos.empty and pos_co != t("All Companies", "جميع الشركات"):
                    allowed = {get_system_name(k) for k in pos_keys}
                    if "System" in raw_pos.columns:
                        raw_pos = raw_pos[raw_pos["System"].isin(allowed)]

                st.session_state.pos_df          = prepare_df(raw_pos) if raw_pos is not None else None
                st.session_state.pos_page        = 0
                st.session_state.pos_last_refresh = datetime.now()

        pos_df = st.session_state.get("pos_df")

        if pos_df is None or pos_df.empty:
            st.markdown(
                f"<div class='info-banner'>ℹ️ {t('Click Refresh POS Data to load.','اضغط تحديث بيانات نقاط البيع لتحميل البيانات.')}</div>",
                unsafe_allow_html=True,
            )
        else:
            # BUG FIX #1/#3: always use t() for column names
            qty_col       = t("Qty",          "الكمية")
            total_col     = t("Total Amount", "المبلغ الإجمالي")
            branch_col    = t("Branch",       "الفرع")
            cashier_col   = t("Cashier",      "الكاشير")
            mc            = t("Model Code",   "رمز الموديل")
            date_col      = t("Date",         "التاريخ")
            pos_order_col = t("POS Order",    "طلب نقطة بيع")

            unique_orders   = pos_df.drop_duplicates(subset=[pos_order_col]) if pos_order_col in pos_df.columns else pos_df
            total_sales_amt = float(unique_orders[total_col].sum()) if total_col in unique_orders.columns else 0
            total_qty_v     = float(pos_df[qty_col].sum()) if qty_col in pos_df.columns else 0
            total_bills     = len(unique_orders)
            avg_bill        = total_sales_amt / total_bills if total_bills > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("Total Revenue (SAR)", "إجمالي الإيرادات (ر.س)"), f"{total_sales_amt:,.0f}")
            m2.metric(t("Total Units Sold", "إجمالي الوحدات"),             f"{total_qty_v:,.0f}")
            m3.metric(t("Total Bills", "عدد الفواتير"),                    f"{total_bills:,}")
            m4.metric(t("Avg Bill (SAR)", "متوسط الفاتورة (ر.س)"),         f"{avg_bill:,.2f}")
            st.divider()

            if pos_co != t("All Companies", "جميع الشركات"):
                st.markdown(
                    f"<div class='ok-banner'>✅ {t('Showing data for','عرض بيانات')} <b>{pos_co}</b> {t('only','فقط')}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(f"<div class='section-header'>📊 {t('POS Visualization','تصور نقاط البيع')}</div>", unsafe_allow_html=True)
            if branch_col in unique_orders.columns and total_col in unique_orders.columns:
                render_visualization(unique_orders, pos_viz_mode, branch_col, total_col,
                                     t("Revenue by Branch", "الإيرادات حسب الفرع"))
            elif mc in pos_df.columns and qty_col in pos_df.columns:
                render_visualization(pos_df, pos_viz_mode, mc, qty_col,
                                     t("Qty Sold by Model", "الكمية حسب الموديل"))
            st.divider()

            if branch_col in unique_orders.columns and total_col in unique_orders.columns:
                render_exec_summary(unique_orders, total_col, branch_col,
                                    t("Branch Performance Analysis", "تحليل أداء الفروع"))
                st.divider()

                branch_agg = unique_orders.groupby(branch_col).agg(
                    Revenue=(total_col, "sum"),
                    Bills=(pos_order_col if pos_order_col in unique_orders.columns else total_col, "count"),
                ).reset_index().sort_values("Revenue", ascending=False)
                branch_agg.columns = [branch_col, t("Revenue (SAR)", "الإيرادات (ر.س)"), t("Bills", "الفواتير")]
                st.markdown(f"<div class='section-header'>🏪 {t('Branch Summary','ملخص الفروع')}</div>", unsafe_allow_html=True)
                render_paginated_table(branch_agg, "pos_branch_page")
                st.divider()

            if cashier_col in unique_orders.columns and total_col in unique_orders.columns:
                cashier_agg = unique_orders.groupby(cashier_col)[total_col].sum().reset_index().sort_values(total_col, ascending=False)
                st.markdown(f"<div class='section-header'>👤 {t('Cashier Performance','أداء الكاشير')}</div>", unsafe_allow_html=True)
                fig_cash = px.bar(cashier_agg.head(10), x=cashier_col, y=total_col,
                                  color=total_col, color_continuous_scale=[th("accent1"), th("accent2")],
                                  template=th("plotly_template"), text_auto=".2s")
                st.plotly_chart(apply_plotly_theme(fig_cash), use_container_width=True)
                render_paginated_table(cashier_agg, "pos_cashier_page")
                st.divider()

            if mc in pos_df.columns and qty_col in pos_df.columns:
                top_prods = pos_df.groupby(mc)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False).head(10)
                st.markdown(f"<div class='section-header'>🏆 {t('Top 10 Products','أفضل 10 منتجات')}</div>", unsafe_allow_html=True)
                fig_prod = px.bar(top_prods, x=mc, y=qty_col,
                                  color=qty_col, color_continuous_scale=[th("accent1"), th("accent2")],
                                  template=th("plotly_template"), text_auto=".2s")
                st.plotly_chart(apply_plotly_theme(fig_prod), use_container_width=True)
                st.divider()

            if date_col in unique_orders.columns and total_col in unique_orders.columns:
                daily = unique_orders.copy()
                daily[date_col] = pd.to_datetime(daily[date_col], errors="coerce").dt.date
                daily_trend = daily.groupby(date_col)[total_col].sum().reset_index().sort_values(date_col)
                st.markdown(f"<div class='section-header'>📈 {t('Daily Revenue Trend','الاتجاه اليومي للإيرادات')}</div>", unsafe_allow_html=True)
                fig_trend = px.area(daily_trend, x=date_col, y=total_col,
                                    template=th("plotly_template"), color_discrete_sequence=[th("accent1")])
                fig_trend.update_traces(fillcolor=f"{th('accent1')}33", line_color=th("accent1"), line_width=2.5)
                st.plotly_chart(apply_plotly_theme(fig_trend), use_container_width=True)
                st.divider()

            st.markdown(f"<div class='section-header'>📋 {t('Detailed POS Transactions','تفاصيل معاملات نقاط البيع')}</div>", unsafe_allow_html=True)
            render_paginated_table(pos_df, "pos_page")

            st.markdown("<br>", unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                st.download_button("⬇️ CSV", to_csv(pos_df), dl_name("pos", "csv"), "text/csv", use_container_width=True)
            with p2:
                st.download_button("⬇️ Excel", to_excel(pos_df), dl_name("pos", "xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # SALES TAB  (BUG FIX #3)
    # =========================================================================
    with tab_sales:
        st.markdown(f"<div class='section-header'>🛍️ {t('Sales Orders Analytics','تحليلات أوامر البيع')}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='exec-summary-bar'>💡 {t('Track revenue, top customers, product performance, and order trends. Identify growth opportunities.','تتبع الإيرادات، أفضل العملاء، أداء المنتجات، واتجاهات الطلبات. تحديد فرص النمو.')}</div>",
            unsafe_allow_html=True,
        )

        sales_co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
        sales_co = st.selectbox(t("Select Company", "اختر الشركة"), options=sales_co_opts, index=0, key="sales_company")
        sales_keys = (SYSTEM_KEYS if sales_co == t("All Companies", "جميع الشركات")
                      else [k for k in SYSTEM_KEYS if get_system_name(k) == sales_co])

        sc1, sc2 = st.columns(2)
        with sc1:
            sales_date_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=30), key="sales_date_from")
        with sc2:
            sales_date_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="sales_date_to")

        sales_model_filter = st.text_input(t("Model Code filter (optional)", "فلتر رمز الموديل (اختياري)"), key="sales_model_filter").strip()

        if st.button(t("Reset Filters", "إعادة تعيين"), key="sales_reset_filters"):
            st.session_state.sales_model_filter = ""
            st.session_state.sales_company      = t("All Companies", "جميع الشركات")
            st.rerun()

        sales_viz_mode = viz_mode_selector("sales_viz_mode")

        if st.button(f"🔄 {t('Refresh Sales Data','تحديث بيانات المبيعات')}", type="primary"):
            with st.spinner(t("Fetching sales data...", "جاري جلب بيانات المبيعات...")):
                raw_sales = fetch_sales_multi(
                    sales_keys,
                    sales_date_from.strftime("%Y-%m-%d"),
                    sales_date_to.strftime("%Y-%m-%d"),
                    sales_model_filter,
                    lang=st.session_state.lang,
                )
                # BUG FIX #3: null check before filtering
                if raw_sales is not None and not raw_sales.empty and sales_co != t("All Companies", "جميع الشركات"):
                    allowed = {get_system_name(k) for k in sales_keys}
                    if "System" in raw_sales.columns:
                        raw_sales = raw_sales[raw_sales["System"].isin(allowed)]

                st.session_state.sales_df          = prepare_df(raw_sales) if raw_sales is not None else None
                st.session_state.sales_page        = 0
                st.session_state.sales_last_refresh = datetime.now()

        sales_df = st.session_state.get("sales_df")

        if sales_df is None or sales_df.empty:
            st.markdown(
                f"<div class='info-banner'>ℹ️ {t('Click Refresh Sales Data to load.','اضغط تحديث بيانات المبيعات لتحميل البيانات.')}</div>",
                unsafe_allow_html=True,
            )
        else:
            # BUG FIX #1/#3: all column refs via t()
            qty_col      = t("Qty",          "الكمية")
            total_col    = t("Total Amount", "المبلغ الإجمالي")
            customer_col = t("Customer",     "العميل")
            mc           = t("Model Code",   "رمز الموديل")
            date_col     = t("Date",         "التاريخ")
            so_col       = t("SO",           "أمر بيع")
            sub_col      = t("Subtotal",     "المجموع الفرعي")

            # Defensive: verify SO column exists
            if so_col not in sales_df.columns:
                st.warning(t(f"Expected column '{so_col}' not found. Please re-fetch data.",
                             f"العمود المتوقع '{so_col}' غير موجود. يرجى إعادة جلب البيانات."))
            else:
                unique_so    = sales_df.drop_duplicates(subset=[so_col])
                total_sales_amt = float(unique_so[total_col].sum()) if total_col in unique_so.columns else 0
                total_orders    = int(unique_so[so_col].nunique())
                total_qty_v     = float(sales_df[qty_col].sum()) if qty_col in sales_df.columns else 0
                avg_order       = total_sales_amt / total_orders if total_orders > 0 else 0

                sm1, sm2, sm3, sm4 = st.columns(4)
                sm1.metric(t("Total Revenue (SAR)", "إجمالي الإيرادات (ر.س)"), f"{total_sales_amt:,.0f}")
                sm2.metric(t("Total Units Sold", "إجمالي الوحدات"),             f"{total_qty_v:,.0f}")
                sm3.metric(t("Total Orders", "عدد الطلبات"),                    f"{total_orders:,}")
                sm4.metric(t("Avg Order (SAR)", "متوسط الطلب (ر.س)"),           f"{avg_order:,.2f}")
                st.divider()

                st.markdown(f"<div class='section-header'>📊 {t('Sales Visualization','تصور المبيعات')}</div>", unsafe_allow_html=True)
                if mc in sales_df.columns and qty_col in sales_df.columns:
                    render_visualization(sales_df, sales_viz_mode, mc, qty_col,
                                         t("Units Sold by Model", "الوحدات المباعة حسب الموديل"))
                st.divider()

                if customer_col in unique_so.columns and total_col in unique_so.columns:
                    render_exec_summary(unique_so, total_col, customer_col,
                                        t("Customer Revenue Analysis", "تحليل إيرادات العملاء"))
                    st.divider()

                    st.markdown(f"<div class='section-header'>👥 {t('Customer Leaderboard','ترتيب العملاء')}</div>", unsafe_allow_html=True)
                    cust_agg = unique_so.groupby(customer_col).agg(
                        Revenue=(total_col, "sum"),
                        Orders=(so_col, "count"),
                    ).reset_index().sort_values("Revenue", ascending=False)
                    cust_agg.columns = [customer_col, t("Revenue (SAR)", "الإيراد (ر.س)"), t("Orders", "الطلبات")]
                    render_paginated_table(cust_agg, "sales_cust_page")
                    st.divider()

                if mc in sales_df.columns and qty_col in sales_df.columns:
                    top_prods = sales_df.groupby(mc)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False).head(10)
                    st.markdown(f"<div class='section-header'>🏆 {t('Top 10 Products by Qty Sold','أفضل 10 منتجات حسب الكمية')}</div>", unsafe_allow_html=True)
                    fig_sp = px.bar(top_prods, x=mc, y=qty_col,
                                    color=qty_col, color_continuous_scale=[th("accent1"), th("accent2")],
                                    template=th("plotly_template"), text_auto=".2s")
                    st.plotly_chart(apply_plotly_theme(fig_sp), use_container_width=True)
                    st.divider()

                if date_col in unique_so.columns and total_col in unique_so.columns:
                    daily = unique_so.copy()
                    daily[date_col] = pd.to_datetime(daily[date_col], errors="coerce").dt.date
                    daily_trend = daily.groupby(date_col)[total_col].sum().reset_index().sort_values(date_col)
                    st.markdown(f"<div class='section-header'>📈 {t('Daily Revenue Trend','الاتجاه اليومي للإيرادات')}</div>", unsafe_allow_html=True)
                    fig_st = px.area(daily_trend, x=date_col, y=total_col,
                                     template=th("plotly_template"), color_discrete_sequence=[th("accent2")])
                    fig_st.update_traces(fillcolor=f"{th('accent2')}33", line_color=th("accent2"), line_width=2.5)
                    st.plotly_chart(apply_plotly_theme(fig_st), use_container_width=True)
                    st.divider()

                st.markdown(f"<div class='section-header'>📋 {t('Detailed Sales Lines','تفاصيل بنود المبيعات')}</div>", unsafe_allow_html=True)
                render_paginated_table(sales_df, "sales_page")

                st.markdown("<br>", unsafe_allow_html=True)
                s1, s2 = st.columns(2)
                with s1:
                    st.download_button("⬇️ CSV", to_csv(sales_df), dl_name("sales", "csv"), "text/csv", use_container_width=True)
                with s2:
                    st.download_button("⬇️ Excel", to_excel(sales_df), dl_name("sales", "xlsx"),
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # PURCHASE TAB  (BUG FIX #4)
    # =========================================================================
    with tab_pur:
        st.markdown(f"<div class='section-header'>🔖 {t('Purchase Analytics','تحليلات المشتريات')}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='exec-summary-bar'>💡 {t('Analyze vendor spending, receipt locations, and purchase trends. Optimize procurement costs.','تحليل إنفاق الموردين، مواقع الاستلام، واتجاهات الشراء. تحسين تكاليف التوريد.')}</div>",
            unsafe_allow_html=True,
        )

        pur_co_opts = [t("All Companies", "جميع الشركات")] + [get_system_name(k) for k in SYSTEM_KEYS]
        pur_co = st.selectbox(t("Select Company", "اختر الشركة"), options=pur_co_opts, index=0, key="pur_company")
        pur_keys = (SYSTEM_KEYS if pur_co == t("All Companies", "جميع الشركات")
                    else [k for k in SYSTEM_KEYS if get_system_name(k) == pur_co])

        pur_model = st.text_input(t("Model Code filter (optional)", "فلتر رمز الموديل (اختياري)"), key="pur_model").strip()

        if st.button(t("Reset Filters", "إعادة تعيين"), key="pur_reset_filters"):
            st.session_state.pur_model   = ""
            st.session_state.pur_company = t("All Companies", "جميع الشركات")
            st.rerun()

        pc1, pc2 = st.columns(2)
        with pc1:
            pur_date_from = st.date_input(t("From", "من"), value=datetime.now().date() - timedelta(days=90), key="pur_date_from")
        with pc2:
            pur_date_to = st.date_input(t("To", "إلى"), value=datetime.now().date(), key="pur_date_to")

        pur_viz_mode = viz_mode_selector("pur_viz_mode")

        if st.button(f"🔄 {t('Refresh Purchase Data','تحديث بيانات المشتريات')}", type="primary"):
            with st.spinner(t("Fetching purchase data...", "جاري جلب بيانات المشتريات...")):
                raw_pur = fetch_purchase_multi(
                    pur_keys, pur_model,
                    pur_date_from.strftime("%Y-%m-%d"),
                    pur_date_to.strftime("%Y-%m-%d"),
                    lang=st.session_state.lang,
                )
                # BUG FIX #4: null check before filtering
                if raw_pur is not None and not raw_pur.empty and pur_co != t("All Companies", "جميع الشركات"):
                    allowed = {get_system_name(k) for k in pur_keys}
                    if "System" in raw_pur.columns:
                        raw_pur = raw_pur[raw_pur["System"].isin(allowed)]

                st.session_state.purchase_df       = prepare_df(raw_pur) if raw_pur is not None else None
                st.session_state.pur_page          = 0
                st.session_state.pur_last_refresh  = datetime.now()

        pur_df = st.session_state.get("purchase_df")

        if pur_df is None or pur_df.empty:
            st.markdown(
                f"<div class='info-banner'>ℹ️ {t('Click Refresh Purchase Data to load.','اضغط تحديث بيانات المشتريات لتحميل البيانات.')}</div>",
                unsafe_allow_html=True,
            )
        else:
            # BUG FIX #1/#4: all column refs via t()
            qty_col_pur = t("Qty",              "الكمية")
            sub_col_pur = t("Subtotal",         "المجموع الفرعي")
            vendor_col  = t("Vendor",           "المورد")
            mc          = t("Model Code",       "رمز الموديل")
            date_col    = t("Date",             "التاريخ")
            loc_col     = t("Receipt Location", "موقع الاستلام")
            po_col      = t("PO",               "أمر شراء")

            # Defensive coercions
            if qty_col_pur not in pur_df.columns:
                pur_df[qty_col_pur] = 0
            if sub_col_pur not in pur_df.columns:
                pur_df[sub_col_pur] = 0

            total_p_qty = int(pd.to_numeric(pur_df[qty_col_pur], errors="coerce").fillna(0).sum())
            total_p_val = float(pd.to_numeric(pur_df[sub_col_pur], errors="coerce").fillna(0).sum())
            total_vendors = int(pur_df[vendor_col].nunique()) if vendor_col in pur_df.columns else 0
            total_pos_n   = int(pur_df[po_col].nunique())    if po_col     in pur_df.columns else 0

            pm1, pm2, pm3, pm4 = st.columns(4)
            pm1.metric(t("Total Purchase Value (SAR)", "إجمالي قيمة الشراء (ر.س)"), f"{total_p_val:,.0f}")
            pm2.metric(t("Total Qty Purchased", "إجمالي الكمية المشتراة"),            f"{total_p_qty:,}")
            pm3.metric(t("Active Vendors", "الموردون النشطون"),                       f"{total_vendors:,}")
            pm4.metric(t("Purchase Orders", "أوامر الشراء"),                          f"{total_pos_n:,}")
            st.divider()

            st.markdown(f"<div class='section-header'>📊 {t('Purchase Visualization','تصور المشتريات')}</div>", unsafe_allow_html=True)
            if vendor_col in pur_df.columns and sub_col_pur in pur_df.columns:
                render_visualization(pur_df, pur_viz_mode, vendor_col, sub_col_pur,
                                     t("Purchase Value by Vendor", "قيمة الشراء حسب المورد"))
            elif mc in pur_df.columns and qty_col_pur in pur_df.columns:
                render_visualization(pur_df, pur_viz_mode, mc, qty_col_pur,
                                     t("Qty by Model", "الكمية حسب الموديل"))
            st.divider()

            if vendor_col in pur_df.columns and sub_col_pur in pur_df.columns:
                render_exec_summary(pur_df, sub_col_pur, vendor_col,
                                    t("Vendor Spend Analysis", "تحليل إنفاق الموردين"))
                st.divider()

                vendor_agg = pur_df.groupby(vendor_col).agg(
                    Spend=(sub_col_pur, "sum"),
                    Qty=(qty_col_pur, "sum"),
                ).reset_index().sort_values("Spend", ascending=False)
                vendor_agg.columns = [vendor_col, t("Spend (SAR)", "الإنفاق (ر.س)"), t("Qty", "الكمية")]
                st.markdown(f"<div class='section-header'>🏭 {t('Vendor Leaderboard','ترتيب الموردين')}</div>", unsafe_allow_html=True)
                render_paginated_table(vendor_agg, "pur_vendor_page")
                st.divider()

            if loc_col in pur_df.columns and qty_col_pur in pur_df.columns:
                loc_agg = pur_df.groupby(loc_col)[qty_col_pur].sum().reset_index().sort_values(qty_col_pur, ascending=False)
                st.markdown(f"<div class='section-header'>📍 {t('Receipt Location Summary','ملخص مواقع الاستلام')}</div>", unsafe_allow_html=True)
                fig_loc = px.pie(loc_agg.head(10), names=loc_col, values=qty_col_pur,
                                 color_discrete_sequence=th("plotly_colors"),
                                 template=th("plotly_template"), hole=0.5)
                fig_loc.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(apply_plotly_theme(fig_loc), use_container_width=True)
                st.divider()

            if date_col in pur_df.columns and sub_col_pur in pur_df.columns:
                daily_pur = pur_df.copy()
                daily_pur[date_col] = pd.to_datetime(daily_pur[date_col], errors="coerce").dt.date
                daily_pur_trend = daily_pur.groupby(date_col)[sub_col_pur].sum().reset_index().sort_values(date_col)
                st.markdown(f"<div class='section-header'>📈 {t('Daily Purchase Trend','الاتجاه اليومي للمشتريات')}</div>", unsafe_allow_html=True)
                fig_ptrend = px.area(daily_pur_trend, x=date_col, y=sub_col_pur,
                                     template=th("plotly_template"), color_discrete_sequence=[th("accent3")])
                fig_ptrend.update_traces(fillcolor=f"{th('accent3')}33", line_color=th("accent3"), line_width=2.5)
                st.plotly_chart(apply_plotly_theme(fig_ptrend), use_container_width=True)
                st.divider()

            st.markdown(f"<div class='section-header'>📋 {t('Detailed Purchase History','تفاصيل تاريخ المشتريات')}</div>", unsafe_allow_html=True)
            render_paginated_table(pur_df, "pur_page")

            st.markdown("<br>", unsafe_allow_html=True)
            pd1, pd2 = st.columns(2)
            with pd1:
                st.download_button("⬇️ CSV", to_csv(pur_df), dl_name("purchase", "csv"), "text/csv", use_container_width=True)
            with pd2:
                st.download_button("⬇️ Excel", to_excel(pur_df), dl_name("purchase", "xlsx"),
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # =========================================================================
    # AI INSIGHTS TAB
    # =========================================================================
    with tab_chat:
        show_chat_panel()

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
restore_session()

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
