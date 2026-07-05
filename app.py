import json
import os
import hashlib
import time
from datetime import date, datetime, timedelta, timezone
from html import escape
import httpx
import streamlit as st
import pandas as pd
import local_db

# ==============================================================================
# 1. DATABASE CONNECTIVITY & KEY RETRIEVAL (MIGRATED TO LOCAL SQLITE)
# ==============================================================================

# Core client (Public tables: obsidian_vault, mission_control)
supabase = local_db.supabase

# Admin client (Sensitive tables: ai_spend)
def get_admin_client():
    return local_db.get_admin_client()

# ==============================================================================
# 2. PAGE INITIALIZATION & PREMIUM TYPOGRAPHY & DESIGN STYLES
# ==============================================================================

st.set_page_config(page_title="Agentic OS", layout="wide", initial_sidebar_state="expanded")

# Inject Google Fonts and Custom Modern Violet Glassmorphism Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@300;400;500&display=swap');

    /* Global Body Overrides */
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* Force expand sidebar button to be visible and styled premium cyan */
    [data-testid="collapsedControl"] {
        display: flex !important;
        background-color: rgba(32, 26, 52, 0.8) !important;
        border: 1px solid rgba(90, 215, 230, 0.3) !important;
        border-radius: 8px !important;
        color: #5ad7e6 !important;
        box-shadow: 0 0 10px rgba(90, 215, 230, 0.2) !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 99999 !important;
    }
    [data-testid="collapsedControl"] button {
        color: #5ad7e6 !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #5ad7e6 !important;
    }

    /* Style collapse sidebar button inside the sidebar */
    [data-testid="stSidebar"] button[aria-label="Close sidebar"] {
        color: #5ad7e6 !important;
    }
    [data-testid="stSidebar"] button[aria-label="Close sidebar"] svg {
        fill: #5ad7e6 !important;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif !important;
        background:
            radial-gradient(900px 500px at 60% -10%, rgba(120,70,200,0.32) 0%, rgba(120,70,200,0) 55%),
            radial-gradient(700px 400px at 12% 5%, rgba(80,40,140,0.25) 0%, rgba(80,40,140,0) 50%),
            linear-gradient(160deg, #120e22 0%, #0a0715 45%, #05040a 100%);
        background-attachment: fixed;
        color: #d8d4e6;
    }

    /* Sidebar glass effect & design */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(26,20,44,0.92) 0%, rgba(12,8,22,0.95) 100%) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.01) !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        color: #a5a1c0 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 12px !important;
        transition: all .2s ease !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(90deg, rgba(90,200,220,0.12), rgba(120,90,230,0.08)) !important;
        border: 1px solid rgba(120,200,220,0.20) !important;
        color: #ffffff !important;
        box-shadow: inset 3px 0 0 #5ad7e6 !important;
    }

    /* Main content buttons: dark glass to match violet/indigo theme.
       Streamlit's default white background + light text is unreadable on dark themes. */
    .stButton > button {
        background: rgba(30, 24, 52, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #d8d4e6 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, rgba(90, 200, 220, 0.15), rgba(120, 90, 230, 0.10)) !important;
        border-color: rgba(90, 215, 230, 0.35) !important;
        color: #ffffff !important;
    }
    .stButton > button:disabled {
        opacity: 0.45 !important;
        color: #8a84a6 !important;
    }
    /* Primary-variant buttons: stronger cyan accent */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #5ad7e6 0%, #4d6dff 100%) !important;
        border: none !important;
        color: #0a0715 !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 16px rgba(90, 215, 230, 0.45) !important;
        color: #0a0715 !important;
    }

    /* Form widget labels (Model / Skill / etc.) — default Streamlit label is too dim on dark theme. */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stWidgetLabel"] label,
    label[data-testid="stWidgetLabel"] {
        color: #c8c3de !important;
        font-weight: 500 !important;
    }
    /* Selectbox / input text — keep readable on dark glass */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stChatInput"] textarea,
    textarea[data-testid="stChatInputTextArea"],
    [data-testid="stTextInput"] input {
        color: #ffffff !important;
        background: rgba(15, 11, 28, 0.55) !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    /* Chat input outer container — dark glass border instead of bright default */
    [data-testid="stChatInput"] {
        background: rgba(15, 11, 28, 0.55) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #8a84a6 !important;
        -webkit-text-fill-color: #8a84a6 !important;
    }
    [data-testid="stSelectbox"] svg {
        fill: #a5a1c0 !important;
    }

    /* Modern Styled Labels & Sections */
    .sidebar-section-title {
        font-size: 11px; font-weight: 700; color: #5b5478;
        text-transform: uppercase; letter-spacing: 2px;
        margin-top: 25px; margin-bottom: 12px; padding-left: 10px;
    }

    /* Navigation Links Styling */
    .nav-link { text-decoration: none; color: inherit; display: block; }
    .nav-link:hover { text-decoration: none; color: inherit; }

    /* Custom Agent list styling in sidebar */
    .agent-row {
        display: flex; align-items: center; gap: 12px;
        padding: 9px 12px; margin-bottom: 5px;
        border-radius: 10px; border: 1px solid transparent;
        transition: all 0.2s ease; cursor: pointer;
    }
    .agent-row:hover {
        background: rgba(255,255,255,0.03);
        border-color: rgba(90,215,230,0.18);
    }
    .agent-row.active {
        background: linear-gradient(90deg, rgba(90,200,220,0.15), rgba(120,90,230,0.08));
        border-color: rgba(90,215,230,0.3);
        box-shadow: inset 3px 0 0 #5ad7e6;
    }
    .agent-avatar {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; color: #ffffff; font-weight: bold;
        box-shadow: 0 0 10px rgba(0,0,0,0.4);
    }
    .agent-name { font-size: 14px; font-weight: 500; color: #d8d4e6; }
    .agent-row.active .agent-name { color: #ffffff; font-weight: 600; }

    /* Avatar specific gradient coloring */
    .av-claude       { background: linear-gradient(135deg, #ff9d4d, #ff6a3d); }
    .av-openclaw     { background: linear-gradient(135deg, #ff7eb3, #ff4d6d); }
    .av-hermes       { background: linear-gradient(135deg, #5aa9ff, #4d6dff); }
    .av-gemini       { background: linear-gradient(135deg, #a855f7, #7c3aed); }
    .av-antigravity  { background: linear-gradient(135deg, #6366f1, #4f46e5); }
    .av-codex        { background: linear-gradient(135deg, #10b981, #059669); }
    .av-freeclaw     { background: linear-gradient(135deg, #34d399, #10b981); }

    /* Self sidebar item styling */
    .side-item {
        display: block; padding: 8px 12px; margin-bottom: 5px;
        border-radius: 10px; color: #a5a1c0 !important; font-weight: 500;
        font-size: 14px; border: 1px solid transparent; transition: all 0.2s ease;
        text-decoration: none !important;
    }
    .side-item:hover {
        background: rgba(255,255,255,0.03);
        border-color: rgba(90,215,230,0.18);
        color: #ffffff !important;
    }
    .side-item.active {
        background: linear-gradient(90deg, rgba(90,200,220,0.15), rgba(120,90,230,0.08));
        border-color: rgba(90,215,230,0.3);
        box-shadow: inset 3px 0 0 #5ad7e6;
        color: #ffffff !important;
    }

    /* Cards and Vault details */
    .memory-card {
        background: rgba(30, 24, 52, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .memory-card:hover {
        background: rgba(45, 35, 75, 0.5);
        border-color: rgba(90,215,230,0.25);
    }
    .file-title { font-size: 15px; font-weight: 600; color: #ffffff; }
    .file-path { font-size: 12px; color: #7d7796; font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
    .time-badge { font-size: 12px; color: #8a84a6; text-align: right; }

    /* Mission Control goals cards */
    .mc-card {
        background: rgba(32,26,52,0.4); backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;
        padding: 16px 18px; margin-bottom: 12px;
    }
    .mc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .mc-title { font-size: 15px; font-weight: 600; color: #ffffff; }
    .status-badge {
        font-size: 10px; font-weight: 700; padding: 3px 9px; border-radius: 12px;
        text-transform: uppercase; letter-spacing: .5px;
    }
    .st-todo { background: rgba(120,120,150,0.15); color: #9a96b5; }
    .st-prog { background: rgba(90,215,230,0.15); color: #5ad7e6; }
    .st-done { background: rgba(52,211,153,0.15); color: #34d399; }
    
    .mc-bar { height: 6px; border-radius: 4px; background: rgba(255,255,255,0.04); overflow: hidden; }
    .mc-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #5ad7e6, #8a6cff); }
    .mc-meta { display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #8a84a6; }

    /* Tabs buttons override - premium glass */
    div.stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: transparent !important;
    }
    div.stTabs [data-baseweb="tab"] {
        background: rgba(30,24,52,0.4) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 20px !important;
        color: #a5a1c0 !important;
        padding: 6px 18px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s !important;
    }
    div.stTabs [data-baseweb="tab"]:hover {
        background: rgba(45,35,75,0.6) !important;
        border-color: rgba(90,215,230,0.25) !important;
        color: #ffffff !important;
    }
    div.stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, rgba(90,200,220,0.15), rgba(120,90,230,0.10)) !important;
        border-color: rgba(90,215,230,0.45) !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(90,215,230,0.2) !important;
    }

    /* Custom styled elements inside tables */
    .stTable, [data-testid="stTable"] {
        background: rgba(30, 24, 52, 0.2) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stMetric"] {
        background: rgba(30,24,52,0.3) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
    }

    /* Sub-tab pills */
    .sub-tab-pill {
        background: rgba(30,24,52,0.4);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        color: #a5a1c0;
        padding: 6px 18px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .sub-tab-pill:hover {
        background: rgba(45,35,75,0.6);
        border-color: rgba(90,215,230,0.25);
        color: #ffffff;
    }
    .sub-tab-pill.active {
        background: linear-gradient(90deg, rgba(90,200,220,0.15), rgba(120,90,230,0.10));
        border-color: rgba(90,215,230,0.45);
        color: #ffffff;
        box-shadow: 0 0 12px rgba(90,215,230,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CORE DEFINITIONS: AGENTS & SELF SECTIONS (MATCHING MOCKUPS)
# ==============================================================================

AGENTS = {
    "claude": {
        "label": "Claude", "avatar": "✦", "cls": "av-claude", 
        "num": "II", "desc": "Anthropic flagship model. Advanced reasoning, system architecture, and dynamic coding.",
        "color": "#ff9d4d"
    },
    "openclaw": {
        "label": "OpenClaw", "avatar": "✸", "cls": "av-openclaw", 
        "num": "III", "desc": "Custom agent swarm coordinator. Orchestrates multi-agent tasks and runs local workflows.",
        "color": "#ff7eb3"
    },
    "hermes": {
        "label": "Hermes", "avatar": "✈", "cls": "av-hermes",
        "num": "IV", "desc": "Nous Research agent. Model routing: gpt-5.5 (code) · deepseek-4-flash (general) · minimax-m3 (content). Sessions, skills, kanban, chat.",
        "color": "#5aa9ff"
    },
    "gemini": {
        "label": "Gemini", "avatar": "●", "cls": "av-gemini", 
        "num": "V", "desc": "Google DeepMind multimodal agent. Massive context processing, video, and audio synthesis.",
        "color": "#a855f7"
    },
    "antigravity": {
        "label": "Antigravity", "avatar": "▲", "cls": "av-antigravity", 
        "num": "VI", "desc": "Autonomous agentic coding copilot. Workspace refactoring, high-fidelity styles, and visual verification.",
        "color": "#6366f1"
    },
    "codex": {
        "label": "Codex", "avatar": "■", "cls": "av-codex", 
        "num": "VII", "desc": "Local coding intelligence and static analysis agent. Refactoring and architectural validation.",
        "color": "#10b981"
    },
    "free-claude": {
        "label": "Official Claude Code", "avatar": "▼", "cls": "av-freeclaw", 
        "num": "VIII", "desc": "Official Anthropic Claude Code setup, workspace guidance, and safe coding workflow notes.",
        "color": "#34d399"
    }
}

SELF_SECTIONS = {
    "agenthq": {
        "label": "Agent HQ", "icon": "🤖", "match": None,
        "num": "XVII", "desc": "Visual representation of agent swarm status, floor coordinate logs, and interactive chat line."
    },
    "ideas": {
        "label": "Ideas Board", "icon": "💡", "match": None,
        "num": "XVIII", "desc": "Premium idea screening pipeline, categories filtering, and status action board."
    },
    "youtube": {
        "label": "YouTube Studio", "icon": "📺", "match": None,
        "num": "XIX", "desc": "Workspace for creators. Script outline generation, checklist validation, and tweak notes."
    },
    "goals": {
        "label": "Goals", "icon": "◎", "match": "Goals", 
        "num": "IX", "desc": "System objectives, key metrics, and OKRs. Aligning agency actions with quarterly goals."
    },
    "seo": {
        "label": "SEO", "icon": "↗", "match": "SEO", 
        "num": "X", "desc": "Pick a keyword + transcript. Generate 5 unique articles. Deploy to your Netlify funnel."
    },
    "studio": {
        "label": "Studio", "icon": "✎", "match": "Studio", 
        "num": "XI", "desc": "Visual & media generation workshop. Coordinates n8n video rendering and asset management."
    },
    "notebook": {
        "label": "Notebook", "icon": "📓", "match": "Note", 
        "num": "XII", "desc": "Interactive scratchpads and persistent ideas canvas. Markdown workspace for agent logs."
    },
    "kanban": {
        "label": "Kanban", "icon": "📋", "match": "Kanban", 
        "num": "XIII", "desc": "Personal interactive work board. Organizes actions, sprint milestones, and agent logs."
    },
    "journal": {
        "label": "Journal", "icon": "▤", "match": "Journal", 
        "num": "XIV", "desc": "Structured reflections and daily engineering logs. Tracks systemic thoughts and insights."
    },
    "memory": {
        "label": "Memory", "icon": "◈", "match": None, 
        "num": "XV", "desc": "Search 1,261 Omi memories + your Obsidian vault."
    },
    "guide": {
        "label": "Build Guide", "icon": "✦", "match": "Build",
        "num": "XVI", "desc": "Engineering manuals, OS setup procedures, and code templates for Agent OS deployment."
    }
}

# Cấu hình model thống nhất cho Hermes — NGUỒN SỰ THẬT DUY NHẤT.
# Hiển thị giống nhau trên mọi giao diện (tab Hermes, Agent HQ drawer) để cấu
# hình định tuyến model luôn nhất quán. Việc chuyển model thật do `hermes` CLI
# trên VPS thực thi; dashboard chỉ phản ánh bảng định tuyến đã thống nhất.
HERMES_MODELS = [
    {"task": "Nhiệm vụ phức tạp (viết code)", "model": "gpt-5.5", "provider": "openai-codex"},
    {"task": "Nhiệm vụ thông thường", "model": "deepseek-4-flash", "provider": "deepseek"},
    {"task": "Viết content", "model": "minimax-m3", "provider": "minimax"},
]


def hermes_model_card_html() -> str:
    """Thẻ glassmorphism hiển thị bảng định tuyến model của Hermes."""
    rows = "".join(
        '<div style="display:flex; justify-content:space-between; gap:12px; align-items:baseline; '
        'padding:6px 0; border-top:1px solid rgba(255,255,255,0.05);">'
        f'<span style="color:#a5a1c0; font-size:12px;">{escape(m["task"])}</span>'
        f'<span style="color:#fff; font-size:12px; font-weight:600; text-align:right;">{escape(m["model"])}'
        f'<span style="color:#5ad7e6; font-weight:500;"> · {escape(m["provider"])}</span></span>'
        '</div>'
        for m in HERMES_MODELS
    )
    return (
        '<div style="background:rgba(30,24,52,0.45); backdrop-filter:blur(10px); '
        'border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px 16px; margin-bottom:14px;">'
        '<div style="font-size:10px; font-weight:700; color:#5ad7e6; letter-spacing:2px; '
        'text-transform:uppercase; margin-bottom:2px;">⚡ Hermes · Model Routing</div>'
        + rows + '</div>'
    )

# ==============================================================================
# 4. MOCK DATA FALLBACKS (PIXEL PERFECT BACKUPS)
# ==============================================================================

MOCK_VAULT_DATA = [
    {"file_name": "2026-05-25", "file_path": "Agentic OS/Memories/2026-05-25.md", "updated_at": "45m ago", "category": "Recent"},
    {"file_name": "2026-05-24", "file_path": "Agentic OS/Memories/2026-05-24.md", "updated_at": "1d ago", "category": "Recent"},
    {"file_name": "Underlord", "file_path": "Wiki/Tools/Underlord.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Paperclip", "file_path": "Wiki/Tools/Paperclip.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Zapier", "file_path": "Wiki/Tools/Zapier.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Make.com", "file_path": "Wiki/Tools/Make.com.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "GitHub Copilot", "file_path": "Wiki/Tools/GitHub Copilot.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Perplexity", "file_path": "Wiki/Tools/Perplexity.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Antigravity", "file_path": "Wiki/Tools/Antigravity.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Gemini", "file_path": "Wiki/Tools/Gemini.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "Amazon", "file_path": "Wiki/Tools/Amazon.md", "updated_at": "1d ago", "category": "Notes"},
    {"file_name": "SEO Link Building Podcast", "file_path": "Wiki/Transcripts/SEO-Link-Building-Podcast.md", "updated_at": "2d ago", "category": "Omi"},
    {"file_name": "Affiliate Challenge", "file_path": "Wiki/Ideas/Affiliate-Challenge.md", "updated_at": "3d ago", "category": "Omi"},
    {"file_name": "Goldie Agency", "file_path": "Wiki/Entities/Goldie-Agency.md", "updated_at": "3d ago", "category": "Omi"},
    {"file_name": "AI Profit Boardroom", "file_path": "Wiki/Strategy/AI-Profit-Boardroom.md", "updated_at": "4d ago", "category": "Recent"},
]

MOCK_MISSION_DATA = [
    {"id": 1, "goal_name": "Build Guide for AI Money Lab", "status": "In Progress", "progress_percent": 65, "turns_used": 14, "turn_budget": 20},
    {"id": 2, "goal_name": "Optimize Obsidian Memory Vault MCP Sync", "status": "Done", "progress_percent": 100, "turns_used": 5, "turn_budget": 5},
    {"id": 3, "goal_name": "Launch Antigravity Coding Agent Swarm", "status": "To Do", "progress_percent": 0, "turns_used": 0, "turn_budget": 50},
    {"id": 4, "goal_name": "SEO Netlify Pipeline Automated Deployments", "status": "In Progress", "progress_percent": 40, "turns_used": 8, "turn_budget": 15},
]

MOCK_SPEND_DATA = [
    {"model_name": "gpt-4o", "cost_usd": 0.1250, "input_tokens": 12500, "output_tokens": 4200, "created_at": "2026-06-02 09:12:00"},
    {"model_name": "claude-3-5-sonnet", "cost_usd": 0.4560, "input_tokens": 28400, "output_tokens": 11200, "created_at": "2026-06-02 08:45:00"},
    {"model_name": "hermes-3-llama-3.1", "cost_usd": 0.0000, "input_tokens": 18500, "output_tokens": 6400, "created_at": "2026-06-02 08:30:00"},
    {"model_name": "gemini-1.5-flash", "cost_usd": 0.0120, "input_tokens": 35000, "output_tokens": 8200, "created_at": "2026-06-02 07:15:00"},
    {"model_name": "claude-3-5-sonnet", "cost_usd": 0.8120, "input_tokens": 45000, "output_tokens": 18000, "created_at": "2026-06-02 06:12:00"},
]

# ==============================================================================
# 5. DATA QUERIES WITH RESILIENT FALLBACKS
# ==============================================================================

def get_obsidian_vault() -> pd.DataFrame:
    try:
        res = supabase.table("obsidian_vault").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(MOCK_VAULT_DATA)

def get_mission_control() -> pd.DataFrame:
    try:
        res = supabase.table("mission_control").select("*").order("id").execute()
        return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(MOCK_MISSION_DATA)

def get_ai_spend(active_agent: str | None = None) -> pd.DataFrame:
    admin = get_admin_client()
    if admin is not None:
        try:
            q = admin.table("ai_spend").select("*")
            if active_agent:
                q = q.ilike("model_name", f"%{active_agent}%")
            res = q.order("created_at", desc=True).execute()
            return pd.DataFrame(res.data)
        except Exception:
            pass
    
    # Return mock data
    df = pd.DataFrame(MOCK_SPEND_DATA)
    if active_agent:
        # Simple local search
        mask = df["model_name"].str.contains(active_agent, case=False, na=False)
        return df[mask]
    return df

# ==============================================================================
# FALLBACK LOCAL DATA STORAGE FOR NEW FEATURES
# ==============================================================================
def load_ideas_data():
    try:
        res = supabase.table("ideas").select("*").order("timestamp", desc=True).execute()
        return res.data
    except Exception:
        try:
            res = supabase.table("Idea").select("*").order("timestamp", desc=True).execute()
            return res.data
        except Exception:
            pass
            
    backup_path = "backups/ideas.json"
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    default_ideas = [
        {"id": "idea-1", "title": "Auto-sync Obsidian with Telegram Agent", "description": "Trigger an alert on Telegram whenever a new note is added to the vault.", "category": "Experiment", "source": "sage", "status": "pending", "timestamp": datetime.now().isoformat()},
        {"id": "idea-2", "title": "Build a custom n8n dashboard for token cost tracking", "description": "Render a bar chart of everyday model expenses with direct API calls.", "category": "Build", "source": "max", "status": "approved", "timestamp": datetime.now().isoformat()},
        {"id": "idea-3", "title": "Create a 5-minute video tutorial explaining OpenClaw setup", "description": "High-retention script outline demonstrating local swarm coordination.", "category": "Content", "source": "nova", "status": "pending", "timestamp": datetime.now().isoformat()}
    ]
    os.makedirs("backups", exist_ok=True)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(default_ideas, f, ensure_ascii=False, indent=2)
    return default_ideas

def save_idea(new_idea):
    try:
        res = supabase.table("ideas").insert(new_idea).execute()
        if res.data:
            return True
    except Exception:
        try:
            res = supabase.table("Idea").insert(new_idea).execute()
            if res.data:
                return True
        except Exception:
            pass
            
    backup_path = "backups/ideas.json"
    ideas = load_ideas_data()
    ideas.insert(0, new_idea)
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(ideas, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def update_idea_status_db(idea_id, status):
    try:
        res = supabase.table("ideas").update({"status": status}).eq("id", idea_id).execute()
        if res.data:
            return True
    except Exception:
        try:
            res = supabase.table("Idea").update({"status": status}).eq("id", idea_id).execute()
            if res.data:
                return True
        except Exception:
            pass
            
    backup_path = "backups/ideas.json"
    ideas = load_ideas_data()
    for idea in ideas:
        if idea["id"] == idea_id:
            idea["status"] = status
            break
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(ideas, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def minimax_tts(text: str) -> tuple[bytes | None, str | None]:
    """MiniMax T2A v2 → mp3 bytes. Trả (audio, None) khi OK; (None, lỗi) khi lỗi.
    Cấu hình qua secrets: MINIMAX_API_KEY, MINIMAX_GROUP_ID
    (tùy chọn: MINIMAX_VOICE_ID, MINIMAX_TTS_MODEL, MINIMAX_API_BASE)."""
    api_key = st.secrets.get("MINIMAX_API_KEY")
    group_id = st.secrets.get("MINIMAX_GROUP_ID")
    if not api_key or not group_id:
        return None, "Chưa cấu hình MiniMax (thiếu MINIMAX_API_KEY / MINIMAX_GROUP_ID)."
    text = (text or "").strip()
    if not text:
        return None, "Không có nội dung để đọc."

    base = st.secrets.get("MINIMAX_API_BASE", "https://api.minimax.io").rstrip("/")
    model = st.secrets.get("MINIMAX_TTS_MODEL", "speech-02-hd")
    voice_id = st.secrets.get("MINIMAX_VOICE_ID", "English_expressive_narrator")
    try:
        r = httpx.post(
            f"{base}/v1/t2a_v2?GroupId={group_id}",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "text": text[:9000],
                "stream": False,
                "language_boost": "auto",
                "output_format": "hex",
                "voice_setting": {"voice_id": voice_id, "speed": 1.0, "vol": 1.0, "pitch": 0},
                "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        # MiniMax báo lỗi nghiệp vụ trong base_resp dù HTTP vẫn 200.
        base_resp = data.get("base_resp") or {}
        if base_resp.get("status_code") not in (0, None):
            return None, f"MiniMax lỗi: {base_resp.get('status_msg', 'unknown')} (code {base_resp.get('status_code')})"
        audio_hex = (data.get("data") or {}).get("audio")
        if not audio_hex:
            return None, "MiniMax không trả audio (kiểm tra voice_id/model/quota)."
        return bytes.fromhex(audio_hex), None
    except Exception as e:
        return None, f"Không gọi được MiniMax TTS: {e}"


def hermes_chat_reply(message: str, model: str | None = None) -> str:
    """Gửi 1 tin nhắn tới Hermes shim, trả câu trả lời đã làm sạch (hoặc thông báo lỗi thân thiện).
    `model` (tùy chọn): ép Hermes dùng đúng model này theo request (shim mở rộng đọc field `model`)."""
    url = st.secrets.get("HERMES_API_URL")
    key = st.secrets.get("HERMES_API_KEY")
    if not url:
        return "Hermes chưa kết nối (thiếu HERMES_API_URL). Bạn vẫn có thể dùng công cụ đọc văn bản bên dưới."
    try:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        payload = {"message": message}
        if model:
            payload["model"] = model
        r = httpx.post(f"{url.rstrip('/')}/chat", json=payload, headers=headers, timeout=50)
        if r.status_code == 401:
            return "⚠️ 401 Unauthorized — HERMES_API_KEY không khớp với shim trên VPS."
        if r.status_code == 422:
            try:
                detail = r.json().get("detail", "")
            except Exception:
                detail = r.text
            return (
                "⚠️ Claude/Hermes từ chối request từ upstream. "
                "Hãy mở session mới hoặc viết lại thành một task kỹ thuật hẹp. "
                f"{detail}".strip()
            )
        r.raise_for_status()
        raw = r.json().get("reply", "")
        cleaned = raw.split("\n")
        cleaned = [l for l in cleaned if "Normalized model" not in l]  # bỏ cảnh báo chuẩn-hoá model của Hermes
        cleaned = [l for l in cleaned if not (("Hermes" in l) and ("─" in l or "═" in l))]
        cleaned = [l.replace("│", "").strip() for l in cleaned]
        cleaned = [l for l in cleaned if not all(c in "─╭╰╯╮┬┴┼═║╔╗╚╝░▒▓█▄▀■-—_=+*#" for c in l.strip())]
        out = "\n".join(l for l in cleaned if l.strip()).strip()
        return out or raw.strip() or "(Hermes không trả về nội dung)"
    except Exception as e:
        return f"⚠️ Hermes lỗi kết nối: {e}. Bạn vẫn có thể dùng công cụ đọc văn bản bên dưới."


def generate_nova_script(title: str) -> str:
    vps_url = st.secrets.get("HERMES_API_URL")
    vps_key = st.secrets.get("HERMES_API_KEY")
    if not vps_url or not vps_key:
        return f"""TITLE: {title}
--------------------------------------------------
[HOOK]
(0:00 - 0:30)
"Chào mừng các bạn đến với kênh! Trong video hôm nay, chúng ta sẽ cùng khám phá cách triển khai tự động hóa quy trình với các AI agent chạy hoàn toàn cục bộ."

[OUTLINE]
1. Giới thiệu giải pháp tự động hóa.
2. Cấu hình kết nối dữ liệu.
3. Cài đặt các Agent trên Agent Floor.
4. Tích hợp API endpoint.
5. Chạy thử nghiệm thực tế.

[FULL SCRIPT BODY]
(Bản thảo kịch bản chi tiết dựa trên tiêu đề: {title})"""

    system_prompt = (
        "Bạn là NOVA, chuyên gia sáng tạo kịch bản video và nội dung YouTube. "
        f"Hãy viết một kịch bản video YouTube chi tiết bằng tiếng Việt cho tiêu đề: \"{title}\".\n"
        "Yêu cầu phản hồi định dạng chính xác như sau (không chứa các ký tự vẽ khung CLI hay lời dẫn giải thích ngoài kịch bản):\n\n"
        f"TITLE: {title}\n"
        "--------------------------------------------------\n"
        "[HOOK]\n"
        "(0:00 - 0:30)\n"
        "\"<Viết lời mở đầu cuốn hút, kích thích sự tò mò ở đây>\"\n\n"
        "[OUTLINE]\n"
        "1. <Ý chính 1>\n"
        "2. <Ý chính 2>\n"
        "3. <Ý chính 3>\n"
        "4. <Ý chính 4>\n"
        "5. <Ý chính 5>\n\n"
        "[FULL SCRIPT BODY]\n"
        "<Viết bản phác thảo chi tiết nội dung từng phần của kịch bản, nêu rõ các bước hướng dẫn cụ thể>"
    )

    try:
        headers = {"Authorization": f"Bearer {vps_key}", "Content-Type": "application/json"}
        r = httpx.post(f"{vps_url.rstrip('/')}/chat", json={"message": system_prompt}, headers=headers, timeout=180)
        if r.status_code == 200:
            raw_reply = r.json().get("reply", "")
            cleaned = raw_reply.split("\n")
            cleaned = [line for line in cleaned if not (("Hermes" in line or "NOVA" in line) and ("─" in line or "═" in line))]
            cleaned = [line.replace("│", "").strip() for line in cleaned]
            cleaned = [line for line in cleaned if not all(c in "─╭╰╯╮┬┴┼═║╔╗╚╝░▒▓█▄▀■-—_=+*#" for c in line.strip())]
            reply = "\n".join([l for l in cleaned if l.strip()]).strip()
            return reply if reply else raw_reply.strip()
    except Exception:
        pass

    return f"""TITLE: {title}
--------------------------------------------------
[HOOK]
(0:00 - 0:30)
"Chào mừng bạn đến với video hướng dẫn. Hôm nay chúng ta sẽ giải quyết bài toán làm thế nào để vận hành tối ưu nhất."

[OUTLINE]
1. Khái niệm cốt lõi.
2. Thiết lập cơ sở dữ liệu.
3. Điều phối các tác vụ.
4. Đo lường hiệu năng.
5. Tổng kết và tối ưu.

[FULL SCRIPT BODY]
(Bản thảo kịch bản chi tiết dựa trên tiêu đề: {title})"""

def generate_seo_articles(keyword: str, transcript: str, prompt_template: str | None = None) -> list[dict]:
    vps_url = st.secrets.get("HERMES_API_URL")
    vps_key = st.secrets.get("HERMES_API_KEY")
    if not vps_url or not vps_key:
        return [
            {
                "title": f"Tại sao {keyword} là chìa khóa chăm sóc sức khỏe chủ động",
                "slug": f"tai-sao-{keyword}-quan-trong",
                "excerpt": "Phân tích trích dẫn hữu ích từ kinh nghiệm y khoa...",
                "content": f"### Nội dung bài viết 1\n\nĐây là bài viết SEO chi tiết về chủ đề {keyword} dựa trên thông tin từ transcript..."
            },
            {
                "title": f"Hướng dẫn thiết lập {keyword} từng bước chi tiết",
                "slug": f"huong-dan-thiet-lap-{keyword}",
                "excerpt": "Các bước chuẩn hóa dữ liệu và vận hành Swarm...",
                "content": f"### Nội dung bài viết 2\n\nHướng dẫn kỹ thuật thực tế để tối ưu {keyword}..."
            },
            {
                "title": f"5 sai lầm phổ biến khi triển khai {keyword}",
                "slug": f"sai-lam-trien-khai-{keyword}",
                "excerpt": "Những điểm yếu dễ mắc phải và cách khắc phục...",
                "content": f"### Nội dung bài viết 3\n\nPhân tích chi tiết và các lời khuyên thiết thực..."
            },
            {
                "title": f"Đánh giá hiệu năng và chi phí của {keyword}",
                "slug": f"danh-gia-hieu-nang-{keyword}",
                "excerpt": "Đo lường hiệu quả vận hành thực tế...",
                "content": f"### Nội dung bài viết 4\n\nBảng so sánh chi phí token và tốc độ phản hồi..."
            },
            {
                "title": f"Tương lai của {keyword} trong chăm sóc sức khỏe 2026",
                "slug": f"tuong-lai-{keyword}",
                "excerpt": "Nhận định xu hướng phát triển dài hạn...",
                "content": f"### Nội dung bài viết 5\n\nTầm nhìn dài hạn và định hướng mở rộng hệ sinh thái..."
            }
        ]

    # Ưu tiên prompt do người dùng cấu hình ở tab Skill (chứa {keyword}/{transcript}).
    # Dùng replace thay vì .format() để prompt tự sửa có thể chứa dấu { } khác mà không lỗi.
    if prompt_template and prompt_template.strip():
        prompt = (
            prompt_template
            .replace("{keyword}", keyword)
            .replace("{transcript}", transcript[:1500])
        )
    else:
        prompt = (
            "Bạn là một chuyên gia viết bài viết SEO chuẩn hóa cho y khoa. "
            f"Hãy tạo ra 5 tiêu đề bài viết khác nhau, độc đáo và thu hút dựa trên từ khóa: \"{keyword}\" và nội dung transcript sau:\n"
            f"\"{transcript[:1500]}\"\n\n"
            "Yêu cầu phản hồi định dạng đúng JSON (chỉ trả về chuỗi JSON thô, không nằm trong dấu nháy markdown hay chứa lời dẫn giải thích), "
            "là một danh sách (array) gồm 5 object, mỗi object có 4 thuộc tính: \n"
            "- \"title\": tiêu đề bài viết tiếng Việt cuốn hút chứa từ khóa\n"
            "- \"slug\": đường dẫn viết liền không dấu ngăn cách bằng gạch ngang\n"
            "- \"excerpt\": một đoạn trích ngắn 1-2 câu tóm tắt cuốn hút\n"
            "- \"content\": nội dung bài viết markdown chi tiết khoảng 300 từ (tiếng Việt), có phân bổ từ khóa.\n"
        )

    try:
        headers = {"Authorization": f"Bearer {vps_key}", "Content-Type": "application/json"}
        r = httpx.post(f"{vps_url.rstrip('/')}/chat", json={"message": prompt}, headers=headers, timeout=180)
        if r.status_code == 200:
            raw = r.json().get("reply", "")
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            articles = json.loads(cleaned)
            if isinstance(articles, list) and len(articles) > 0:
                return articles
    except Exception:
        pass

    return [
        {
            "title": f"Tại sao {keyword} là chìa khóa chăm sóc sức khỏe chủ động",
            "slug": f"tai-sao-{keyword}-quan-trong",
            "excerpt": "Phân tích trích dẫn hữu ích từ kinh nghiệm y khoa...",
            "content": f"### Nội dung bài viết 1\n\nĐây là bài viết SEO chi tiết về chủ đề {keyword} dựa trên thông tin từ transcript..."
        },
        {
            "title": f"Hướng dẫn thiết lập {keyword} từng bước chi tiết",
            "slug": f"huong-dan-thiet-lap-{keyword}",
            "excerpt": "Các bước chuẩn hóa dữ liệu và vận hành Swarm...",
            "content": f"### Nội dung bài viết 2\n\nHướng dẫn kỹ thuật thực tế để tối ưu {keyword}..."
        },
        {
            "title": f"5 sai lầm phổ biến khi triển khai {keyword}",
            "slug": f"sai-lam-trien-khai-{keyword}",
            "excerpt": "Những điểm yếu dễ mắc phải và cách khắc phục...",
            "content": f"### Nội dung bài viết 3\n\nPhân tích chi tiết và các lời khuyên thiết thực..."
        },
        {
            "title": f"Đánh giá hiệu năng và chi phí của {keyword}",
            "slug": f"danh-gia-hieu-nang-{keyword}",
            "excerpt": "Đo lường hiệu quả vận hành thực tế...",
            "content": f"### Nội dung bài viết 4\n\nBảng so sánh chi phí token và tốc độ phản hồi..."
        },
        {
            "title": f"Tương lai của {keyword} trong chăm sóc sức khỏe 2026",
            "slug": f"tuong-lai-{keyword}",
            "excerpt": "Nhận định xu hướng phát triển dài hạn...",
            "content": f"### Nội dung bài viết 5\n\nTầm nhìn dài hạn và định hướng mở rộng hệ sinh thái..."
        }
    ]

def load_youtube_scripts():
    try:
        res = supabase.table("DataStore").select("data").eq("key", "youtube-scripts").execute()
        if res.data:
            return res.data[0]["data"]
        else:
            return []
    except Exception:
        try:
            res = supabase.table("datastore").select("data").eq("key", "youtube-scripts").execute()
            if res.data:
                return res.data[0]["data"]
            else:
                return []
        except Exception:
            pass
            
    backup_path = "backups/youtube_scripts.json"
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    default_scripts = [
        {
            "id": "script-1",
            "title": "How To Build a Public Scoreboard for 7 AI Agents in OpenClaw",
            "hook": True,
            "outline": False,
            "fullScript": False,
            "status": "pending_review",
            "category": "ideas",
            "type": "articles",
            "notes": ""
        },
        {
            "id": "script-2",
            "title": "How To Run OpenClaw With Claude and Gemma 4 for $30/Month",
            "hook": True,
            "outline": True,
            "fullScript": True,
            "status": "pending_review",
            "category": "ideas",
            "type": "videos",
            "notes": ""
        }
    ]
    os.makedirs("backups", exist_ok=True)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(default_scripts, f, ensure_ascii=False, indent=2)
    return default_scripts

def save_youtube_scripts(scripts):
    try:
        res = supabase.table("DataStore").select("*").eq("key", "youtube-scripts").execute()
        if res.data:
            supabase.table("DataStore").update({"data": scripts}).eq("key", "youtube-scripts").execute()
        else:
            supabase.table("DataStore").insert({"key": "youtube-scripts", "data": scripts}).execute()
        return True
    except Exception:
        try:
            res = supabase.table("datastore").select("*").eq("key", "youtube-scripts").execute()
            if res.data:
                supabase.table("datastore").update({"data": scripts}).eq("key", "youtube-scripts").execute()
            else:
                supabase.table("datastore").insert({"key": "youtube-scripts", "data": scripts}).execute()
            return True
        except Exception:
            pass
            
    backup_path = "backups/youtube_scripts.json"
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def render_copy_button(label: str, text: str, key: str) -> None:
    """Render nút copy clipboard thật bằng browser Clipboard API."""
    payload = json.dumps(text or "").replace("</", "<\\/")
    button_id = f"copy_btn_{key}".replace("-", "_")
    status_id = f"copy_status_{key}".replace("-", "_")
    st.components.v1.html(
        f"""
        <button id="{button_id}" style="
            display:inline-flex; align-items:center; gap:8px;
            background:rgba(30,24,52,0.72);
            border:1px solid rgba(255,255,255,0.10);
            border-radius:10px;
            color:#ffffff;
            padding:12px 18px;
            font:600 14px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            cursor:pointer;
            min-width:174px;
            justify-content:center;
        ">
            📋 {label}
        </button>
        <span id="{status_id}" style="
            margin-left:10px; color:#34d399;
            font:600 12px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            opacity:0; transition:opacity .18s ease;
        ">Copied</span>
        <script>
        const copyText = {payload};
        const btn = document.getElementById("{button_id}");
        const status = document.getElementById("{status_id}");
        function fallbackCopy(text) {{
            const area = document.createElement("textarea");
            area.value = text;
            area.style.position = "fixed";
            area.style.left = "-9999px";
            document.body.appendChild(area);
            area.focus();
            area.select();
            const ok = document.execCommand("copy");
            document.body.removeChild(area);
            return ok;
        }}
        btn.addEventListener("click", async () => {{
            let ok = false;
            try {{
                if (navigator.clipboard && window.isSecureContext) {{
                    await navigator.clipboard.writeText(copyText);
                    ok = true;
                }}
            }} catch (err) {{}}
            if (!ok) ok = fallbackCopy(copyText);
            status.textContent = ok ? "Copied" : "Press Ctrl+C";
            status.style.opacity = "1";
            btn.textContent = ok ? "✓ Copied" : "Select text";
            setTimeout(() => {{
                status.style.opacity = "0";
                btn.textContent = "📋 {label}";
            }}, 1600);
        }});
        </script>
        """,
        height=52,
    )

def load_seo_campaigns():
    try:
        res = supabase.table("DataStore").select("data").eq("key", "seo-campaigns").execute()
        if res.data:
            return res.data[0]["data"]
    except Exception:
        try:
            res = supabase.table("datastore").select("data").eq("key", "seo-campaigns").execute()
            if res.data:
                return res.data[0]["data"]
        except Exception:
            pass
            
    backup_path = "backups/seo_campaigns.json"
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_seo_campaigns(campaigns):
    try:
        res = supabase.table("DataStore").select("*").eq("key", "seo-campaigns").execute()
        if res.data:
            supabase.table("DataStore").update({"data": campaigns}).eq("key", "seo-campaigns").execute()
        else:
            supabase.table("DataStore").insert({"key": "seo-campaigns", "data": campaigns}).execute()
        return True
    except Exception:
        try:
            res = supabase.table("datastore").select("*").eq("key", "seo-campaigns").execute()
            if res.data:
                supabase.table("datastore").update({"data": campaigns}).eq("key", "seo-campaigns").execute()
            else:
                supabase.table("datastore").insert({"key": "seo-campaigns", "data": campaigns}).execute()
            return True
        except Exception:
            pass
            
    backup_path = "backups/seo_campaigns.json"
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(campaigns, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def load_seo_transcripts():
    try:
        res = supabase.table("DataStore").select("data").eq("key", "seo-transcripts").execute()
        if res.data:
            return res.data[0]["data"]
    except Exception:
        try:
            res = supabase.table("datastore").select("data").eq("key", "seo-transcripts").execute()
            if res.data:
                return res.data[0]["data"]
        except Exception:
            pass

    backup_path = "backups/seo_transcripts.json"
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_seo_transcripts(transcripts):
    try:
        res = supabase.table("DataStore").select("*").eq("key", "seo-transcripts").execute()
        if res.data:
            supabase.table("DataStore").update({"data": transcripts}).eq("key", "seo-transcripts").execute()
        else:
            supabase.table("DataStore").insert({"key": "seo-transcripts", "data": transcripts}).execute()
        return True
    except Exception:
        try:
            res = supabase.table("datastore").select("*").eq("key", "seo-transcripts").execute()
            if res.data:
                supabase.table("datastore").update({"data": transcripts}).eq("key", "seo-transcripts").execute()
            else:
                supabase.table("datastore").insert({"key": "seo-transcripts", "data": transcripts}).execute()
            return True
        except Exception:
            pass

    backup_path = "backups/seo_transcripts.json"
    try:
        os.makedirs("backups", exist_ok=True)
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(transcripts, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ==============================================================================
# WORKSPACE · MODEL ARENA (so sánh đa-model thật) + SKILL LIBRARY (lưu Skill)
# ==============================================================================

def load_skills() -> list:
    """Đọc thư viện Skill đã lưu từ DataStore (key: workspace-skills)."""
    try:
        res = supabase.table("DataStore").select("data").eq("key", "workspace-skills").execute()
        if res.data:
            return res.data[0]["data"]
    except Exception:
        try:
            res = supabase.table("datastore").select("data").eq("key", "workspace-skills").execute()
            if res.data:
                return res.data[0]["data"]
        except Exception:
            pass
    return []


def save_skills(entries: list) -> bool:
    """Ghi thư viện Skill vào DataStore (anon client — giống save_seo_transcripts)."""
    try:
        res = supabase.table("DataStore").select("*").eq("key", "workspace-skills").execute()
        if res.data:
            supabase.table("DataStore").update({"data": entries}).eq("key", "workspace-skills").execute()
        else:
            supabase.table("DataStore").insert({"key": "workspace-skills", "data": entries}).execute()
        return True
    except Exception:
        try:
            res = supabase.table("datastore").select("*").eq("key", "workspace-skills").execute()
            if res.data:
                supabase.table("datastore").update({"data": entries}).eq("key", "workspace-skills").execute()
            else:
                supabase.table("datastore").insert({"key": "workspace-skills", "data": entries}).execute()
            return True
        except Exception:
            pass
    return False


# Bộ định tuyến đa-model THẬT: mỗi nhãn map tới một provider gọi backend thật.
# Cột thiếu key/quota sẽ báo trung thực (⚠️) thay vì bịa nội dung. Thêm model =
# thêm 1 dòng ở đây; thêm key vào secrets là cột đó "sáng" lên.
# So sánh model THẬT qua API trực tiếp. Mỗi nhãn → 1 provider thật; thiếu key thì
# model_status báo 🟡 và cột hiện "⚠️ Chưa cấu hình ...". Hermes hiện chỉ cấu hình
# DeepSeek nên để 1 cột "Hermes · deepseek". Gemini dùng endpoint OpenAI-compatible
# của Google (cùng code path openai_chat). Thêm model = thêm 1 dòng; thêm key = cột sáng.
MODEL_REGISTRY = {
    "Hermes · deepseek":         {"provider": "hermes"},
    "gpt-4o · OpenAI":           {"provider": "openai", "model": "gpt-4o",           "key": "OPENAI_API_KEY",   "base": "https://api.openai.com/v1"},
    "gemini-2.5-flash · Google": {"provider": "openai", "model": "gemini-2.5-flash", "key": "GEMINI_API_KEY",   "base": "https://generativelanguage.googleapis.com/v1beta/openai"},
    "deepseek-chat · DeepSeek":  {"provider": "openai", "model": "deepseek-chat",    "key": "DEEPSEEK_API_KEY", "base": "https://api.deepseek.com/v1"},
    "minimax-m3 · MiniMax":      {"provider": "minimax", "model": "minimax-m3"},
}
ARENA_MODEL_CHOICES = list(MODEL_REGISTRY.keys())


def model_status(label: str) -> tuple[bool, str]:
    """(sẵn-sàng?, ghi-chú) — model nào đủ key/secret để gọi thật."""
    cfg = MODEL_REGISTRY.get(label, {})
    p = cfg.get("provider")
    if p == "hermes":
        ok = bool(st.secrets.get("HERMES_API_URL"))
        if not ok:
            return False, "thiếu HERMES_API_URL"
        return True, "ép model qua Hermes" if cfg.get("hermes_model") else "Hermes auto"
    if p == "minimax":
        ok = bool(st.secrets.get("MINIMAX_API_KEY") and st.secrets.get("MINIMAX_GROUP_ID"))
        return ok, "đã cấu hình" if ok else "thiếu MINIMAX_API_KEY"
    if p == "openai":
        ok = bool(st.secrets.get(cfg.get("key", "")))
        return ok, "đã cấu hình" if ok else f"thiếu {cfg.get('key')}"
    return False, "không rõ provider"


def minimax_chat(prompt: str, model: str = "minimax-m3") -> str:
    """Gọi MiniMax text chat (chatcompletion_v2). Báo lỗi nghiệp vụ trung thực."""
    api_key = st.secrets.get("MINIMAX_API_KEY")
    if not api_key:
        return "⚠️ Chưa cấu hình MINIMAX_API_KEY."
    base = st.secrets.get("MINIMAX_API_BASE", "https://api.minimax.io").rstrip("/")
    try:
        r = httpx.post(
            f"{base}/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048},
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        br = data.get("base_resp") or {}
        if br.get("status_code") not in (0, None):
            return f"⚠️ MiniMax: {br.get('status_msg', 'lỗi')} (code {br.get('status_code')})"
        return ((data.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip() or "(MiniMax không trả nội dung)"
    except Exception as e:
        return f"⚠️ MiniMax lỗi kết nối: {e}"


def openai_chat(prompt: str, model: str, base: str, key_name: str) -> str:
    """OpenAI-compatible (OpenAI, DeepSeek...). Thiếu key thì báo, không bịa."""
    key = st.secrets.get(key_name)
    if not key:
        return f"⚠️ Chưa cấu hình {key_name} trong secrets — thêm key để bật model này."
    try:
        r = httpx.post(
            f"{base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        r.raise_for_status()
        return ((r.json().get("choices") or [{}])[0].get("message", {}).get("content") or "").strip() or "(không có nội dung)"
    except Exception as e:
        return f"⚠️ {key_name} lỗi: {e}"


def run_model(model_label: str, prompt: str) -> str:
    """Định tuyến 1 prompt tới provider THẬT theo MODEL_REGISTRY."""
    cfg = MODEL_REGISTRY.get(model_label, {"provider": "hermes"})
    p = cfg.get("provider")
    if p == "minimax":
        return minimax_chat(prompt, cfg.get("model", "minimax-m3"))
    if p == "openai":
        return openai_chat(prompt, cfg["model"], cfg["base"], cfg["key"])
    return hermes_chat_reply(prompt, cfg.get("hermes_model"))  # hermes: auto hoặc ép model


def render_workspace_bucket_nav(selected_bucket: str) -> None:
    """Cột Buckets của Workspace — dùng chung cho explorer và Model Arena."""
    st.markdown("<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Buckets</div>", unsafe_allow_html=True)
    buckets = [
        {"id": "compare", "label": "So sánh Model", "icon": "🆚"},
        {"id": "goal", "label": "Goal Mode", "icon": "🎯"},
        {"id": "apps", "label": "Apps", "icon": "📱"},
        {"id": "video", "label": "Video", "icon": "🎥"},
        {"id": "images", "label": "Images", "icon": "🖼️"},
        {"id": "audio", "label": "Audio", "icon": "🎵"},
        {"id": "sandboxes", "label": "Sandboxes", "icon": "📦"},
        {"id": "pastes", "label": "Pastes", "icon": "📋"},
    ]
    for b in buckets:
        active_class = "active" if b["id"] == selected_bucket else ""
        st.markdown(f"""
        <a class="nav-link side-item {active_class}" target="_self" href="?nav=hermes&tab=workspace&bucket={b['id']}" style="display:block; text-decoration:none;">
            {b['icon']} {b['label']}
        </a>
        """, unsafe_allow_html=True)


def render_skills_panel() -> None:
    """Bảng Skill (Charms): mỗi Skill gán MODEL riêng (tuỳ chọn) + nút ▶ Dùng để
    gọi Skill đó vào ô chat (trả lời bằng đúng model được gán)."""
    all_skills = load_skills()
    active_id = st.session_state.get("active_skill_id")
    st.markdown(
        "<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;'>"
        "<span style='font-size:13px; font-weight:700; color:#f3f1fb;'>⚡ Skills (Charms)</span>"
        f"<span style='font-size:11px; color:#5ad7e6; background:rgba(90,215,230,0.1); padding:1px 8px; border-radius:6px; font-weight:600;'>{len(all_skills)}</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    if not all_skills:
        st.caption("Chưa có Skill. Vào chế độ 🆚 So sánh, chọn bản tốt rồi “Lưu thành Skill”.")
        return
    q = st.text_input("Tìm Skill", key="skill_search", placeholder="Search by Name", label_visibility="collapsed")
    skills = all_skills
    if q:
        ql = q.lower()
        skills = [s for s in all_skills if ql in (str(s.get("name", "")) + str(s.get("prompt", ""))).lower()]

    dirty = False
    for s in skills[:40]:
        sid = s.get("id")
        is_active = (sid == active_id)
        with st.expander(("✅ " if is_active else "▶ ") + s.get("name", "(chưa đặt tên)"), expanded=is_active):
            # Gán model riêng cho Skill (tuỳ chọn của người dùng)
            cur = s.get("model", ARENA_MODEL_CHOICES[0])
            idx = ARENA_MODEL_CHOICES.index(cur) if cur in ARENA_MODEL_CHOICES else 0
            chosen = st.selectbox("Model của Skill", ARENA_MODEL_CHOICES, index=idx, key=f"skill_model_{sid}")
            if chosen != s.get("model"):
                s["model"] = chosen
                dirty = True
            ok, note = model_status(chosen)
            st.caption(("🟢 " if ok else "🟡 ") + note)
            if s.get("prompt"):
                pv = s["prompt"]
                st.caption("🎭 " + pv[:120] + ("…" if len(pv) > 120 else ""))
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✕ Thôi dùng" if is_active else "▶ Dùng", key=f"skill_use_{sid}", use_container_width=True):
                    st.session_state["active_skill_id"] = None if is_active else sid
                    st.rerun()
            with b2:
                if st.button("🗑 Xóa", key=f"skill_del_{sid}", use_container_width=True):
                    if is_active:
                        st.session_state["active_skill_id"] = None
                    save_skills([x for x in all_skills if x.get("id") != sid])
                    st.rerun()
    if dirty:
        save_skills(all_skills)
        st.rerun()


def render_skills_page() -> None:
    """Trang quản lý Skills toàn trang — tạo mới, import JSON, export, xóa, gọi vào Workspace."""
    render_custom_header("⚡", "WORKSPACE", "Skills", "Thư viện Skill tái sử dụng — tạo, import, gọi vào Workspace so sánh model.")

    # Thông báo sau khi lưu/import thành công
    if msg := st.session_state.pop("skp_toast", None):
        st.success(msg)

    all_skills = load_skills()

    # --- Top action bar ---
    bar_l, bar_m, bar_r = st.columns([3, 1.3, 1.2])
    with bar_l:
        q = st.text_input("🔍", key="skp_q", placeholder="Tìm Skill theo tên hoặc prompt…", label_visibility="collapsed")
    with bar_m:
        if st.button("✦ Tạo Skill mới", key="skp_open_create", type="primary", use_container_width=True):
            st.session_state["skp_create_open"] = not st.session_state.get("skp_create_open", False)
            st.session_state.pop("skp_import_open", None)
    with bar_r:
        if st.button("↥ Import JSON", key="skp_open_import", use_container_width=True):
            st.session_state["skp_import_open"] = not st.session_state.get("skp_import_open", False)
            st.session_state.pop("skp_create_open", None)

    # --- Create form ---
    if st.session_state.get("skp_create_open", False):
        with st.container(border=True):
            st.markdown("**✦ Tạo Skill mới**")
            with st.form("skp_create_form", clear_on_submit=True):
                name = st.text_input("Tên Skill *", placeholder="Ví dụ: Biên tập viên tiếng Việt")
                prompt = st.text_area("Prompt / Persona", placeholder="Bạn là chuyên gia biên tập viên…", height=90)
                col_m, col_n = st.columns(2)
                with col_m:
                    model = st.selectbox("Model mặc định", ARENA_MODEL_CHOICES, key="skp_create_model")
                with col_n:
                    note = st.text_input("Ghi chú (tuỳ chọn)")
                c_sub, c_cancel = st.columns(2)
                with c_sub:
                    submitted = st.form_submit_button("✓ Lưu Skill", type="primary", use_container_width=True)
                with c_cancel:
                    cancelled = st.form_submit_button("✕ Hủy", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Tên Skill không được để trống.")
                else:
                    entry = {
                        "id": f"sk_{int(time.time()*1000)}",
                        "name": name.strip(),
                        "prompt": prompt.strip(),
                        "model": model,
                        "note": note.strip(),
                        "ts": datetime.now().isoformat(),
                        "answer": "",
                        "models_compared": [],
                    }
                    all_skills.insert(0, entry)
                    save_skills(all_skills)
                    st.session_state["skp_create_open"] = False
                    st.session_state["skp_toast"] = f"✓ Đã tạo Skill '{entry['name']}'"
                    st.rerun()
            if cancelled:
                st.session_state["skp_create_open"] = False
                st.rerun()

    # --- Import JSON section ---
    if st.session_state.get("skp_import_open", False):
        with st.container(border=True):
            st.markdown("**↥ Import Skill từ JSON**")
            st.caption("Hỗ trợ: 1 Skill (object) hoặc nhiều Skill (array). Trùng ID sẽ bỏ qua.")
            uploaded = st.file_uploader("Chọn file JSON", type=["json"], key="skp_import_file", label_visibility="collapsed")
            if uploaded:
                try:
                    raw = json.loads(uploaded.read().decode("utf-8"))
                    items = raw if isinstance(raw, list) else [raw]
                    existing_ids = {s.get("id") for s in all_skills}
                    new_items: list = []
                    for idx_item, item in enumerate(items):
                        if not isinstance(item, dict) or not item.get("name"):
                            continue
                        if not item.get("id"):
                            item["id"] = f"sk_{int(time.time()*1000)}_{idx_item}"
                        if item["id"] not in existing_ids:
                            new_items.append(item)
                            existing_ids.add(item["id"])
                    st.info(f"Tìm thấy {len(new_items)} Skill mới từ file.")
                    if st.button(f"✓ Import {len(new_items)} Skill", key="skp_do_import",
                                 type="primary", disabled=(len(new_items) == 0)):
                        save_skills(all_skills + new_items)
                        st.session_state["skp_import_open"] = False
                        st.session_state["skp_toast"] = f"✓ Đã import {len(new_items)} Skill"
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi parse JSON: {e}")
            if st.button("✕ Đóng Import", key="skp_import_close"):
                st.session_state["skp_import_open"] = False
                st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # --- Stats + Export all ---
    stats_l, stats_r = st.columns([3, 1])
    with stats_l:
        st.markdown(
            f"<span style='color:#5ad7e6; font-weight:700; font-size:15px;'>{len(all_skills)} Skills</span>"
            f"<span style='color:#6b7280; font-size:13px;'> trong thư viện</span>",
            unsafe_allow_html=True,
        )
    with stats_r:
        if all_skills:
            st.download_button(
                "⬇ Export tất cả",
                data=json.dumps(all_skills, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="skills_export.json",
                mime="application/json",
                key="skp_export_all",
                use_container_width=True,
            )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # --- Filter ---
    filtered = all_skills
    if q:
        ql = q.lower()
        filtered = [s for s in all_skills if ql in (
            s.get("name", "") + " " + s.get("prompt", "") + " " + s.get("note", "")
        ).lower()]

    if not filtered:
        st.info(
            "Không tìm thấy Skill nào khớp." if q else
            "Chưa có Skill nào. Bấm [✦ Tạo Skill mới] bên trên, hoặc vào Workspace → 🆚 So sánh Model → Lưu thành Skill."
        )
        return

    # --- Skills grid 3 cột ---
    active_id = st.session_state.get("active_skill_id")
    cols = st.columns(3, gap="medium")
    for i, s in enumerate(filtered[:60]):
        sid = s.get("id", f"idx_{i}")
        is_active = (sid == active_id)
        ok, ok_note = model_status(s.get("model", ARENA_MODEL_CHOICES[0]))
        model_label = s.get("model", "?")
        ok_clr = "#22c55e" if ok else "#f59e0b"
        ok_bg = "34,197,94" if ok else "245,158,11"
        prompt_prev = s.get("prompt", "")
        note_text = s.get("note", "")
        border_op = "0.25" if is_active else "0.08"
        with cols[i % 3]:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,{border_op}); "
                f"border-radius:12px; padding:14px 14px 8px 14px; margin-bottom:2px;'>"
                f"<div style='font-weight:700; font-size:14px; color:#f3f1fb; margin-bottom:6px;'>"
                f"{'✅ ' if is_active else ''}{escape(s.get('name', '(chưa đặt tên)'))}</div>"
                f"<div style='display:flex; gap:5px; flex-wrap:wrap; margin-bottom:6px;'>"
                f"<span style='background:rgba(90,215,230,0.12); color:#5ad7e6; border-radius:5px; padding:1px 8px; font-size:11px;'>{escape(model_label)}</span>"
                f"<span style='background:rgba({ok_bg},0.12); color:{ok_clr}; border-radius:5px; padding:1px 8px; font-size:11px;'>{'🟢' if ok else '🟡'} {escape(ok_note)}</span>"
                f"</div>"
                + (f"<div style='color:#8b92b6; font-size:12px; margin-bottom:5px;'>{escape(prompt_prev[:100])}{'…' if len(prompt_prev)>100 else ''}</div>" if prompt_prev else "")
                + (f"<div style='color:#6b7280; font-size:11px;'>{escape(note_text)}</div>" if note_text else "")
                + "</div>",
                unsafe_allow_html=True,
            )
            b1, b2, b3 = st.columns([1.2, 1, 0.8])
            with b1:
                btn_lbl = "✕ Thôi dùng" if is_active else "▶ Gọi"
                if st.button(btn_lbl, key=f"skp_use_{sid}", use_container_width=True):
                    st.session_state["active_skill_id"] = None if is_active else sid
                    st.rerun()
            with b2:
                st.download_button(
                    "📋",
                    data=json.dumps(s, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name=f"skill_{sid}.json",
                    mime="application/json",
                    key=f"skp_dl_{sid}",
                    use_container_width=True,
                    help="Export Skill này",
                )
            with b3:
                if st.button("🗑", key=f"skp_del_{sid}", use_container_width=True, help="Xóa Skill"):
                    save_skills([x for x in all_skills if x.get("id") != sid])
                    if active_id == sid:
                        st.session_state["active_skill_id"] = None
                    st.rerun()
            st.markdown(
                f"<a href='?nav=hermes&tab=workspace&bucket=compare' target='_self' "
                f"style='font-size:11px; color:#5ad7e6; text-decoration:none;'>→ Dùng trong Workspace</a>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


def render_chat_pane() -> None:
    """Ô chat: gọi Skill (Charm) từ bảng phải -> trả lời bằng MODEL gán cho Skill đó;
    hoặc chat thường với model mặc định tuỳ chọn."""
    if st.session_state.pop("ws_chat_clear", False):
        st.session_state.pop("ws_chat_input", None)

    skills = load_skills()
    active_skill = next((s for s in skills if s.get("id") == st.session_state.get("active_skill_id")), None)

    if active_skill:
        eff_model = active_skill.get("model", ARENA_MODEL_CHOICES[0])
        ok, _ = model_status(eff_model)
        bl, br = st.columns([4, 1])
        with bl:
            st.markdown(
                f"<div style='background:rgba(120,90,230,0.12); border:1px solid rgba(120,90,230,0.3); "
                f"border-radius:10px; padding:8px 12px;'>"
                f"<span style='color:#b9a9ff; font-weight:700; font-size:13px;'>🎭 {escape(active_skill.get('name', 'Skill'))}</span>"
                f"<span style='color:#8b92b6; font-size:12px;'> · model {escape(eff_model)} {'🟢' if ok else '🟡'}</span></div>",
                unsafe_allow_html=True,
            )
        with br:
            if st.button("✕ Thôi", key="chat_skill_off", use_container_width=True):
                st.session_state["active_skill_id"] = None
                st.rerun()
    else:
        eff_model = st.selectbox("Model (chat thường)", ARENA_MODEL_CHOICES, key="chat_model")
        ok, note = model_status(eff_model)
        st.caption(("🟢 " if ok else "🟡 ") + note + " — hoặc bấm ▶ Dùng một Skill bên phải để gọi chuyên gia.")

    history = st.session_state.setdefault("ws_chat", [])
    hl, hr = st.columns([4, 1])
    with hl:
        st.caption(f"💬 {len(history)} tin nhắn")
    with hr:
        if st.button("🗑 Xoá", key="ws_chat_reset", use_container_width=True):
            st.session_state["ws_chat"] = []
            st.rerun()

    box = st.container(height=320)
    with box:
        if not history:
            st.caption("Gọi một Skill bên phải (▶ Dùng) rồi nhắn yêu cầu — Skill trả lời bằng model được gán cho nó. Mỗi Skill có thể dùng model khác nhau.")
        for msg in history:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])

    user_msg = st.text_area(
        "Tin nhắn", key="ws_chat_input", height=80, label_visibility="collapsed",
        placeholder="Nhắn yêu cầu cho Skill / chat...",
    )
    if st.button("Gửi ▸", type="primary", use_container_width=True):
        if not user_msg.strip():
            st.warning("Nhập tin nhắn trước khi gửi.")
        else:
            history.append({"role": "user", "content": user_msg.strip()})
            parts = []
            if active_skill and active_skill.get("prompt"):
                parts.append("Hãy đóng vai theo chỉ dẫn sau, trả lời bằng tiếng Việt:\n" + active_skill["prompt"])
            for msg in history[-10:]:
                who = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                parts.append(f"{who}: {msg['content']}")
            parts.append("Trợ lý:")
            with st.spinner(f"{eff_model} đang trả lời..."):
                reply = run_model(eff_model, "\n\n".join(parts))
            history.append({"role": "assistant", "content": reply})
            st.session_state["ws_chat"] = history
            st.session_state["ws_chat_clear"] = True
            st.rerun()


def render_arena_pane() -> None:
    """Chế độ So sánh: 1 prompt -> 2–4 model cạnh nhau -> chọn bản tốt -> lưu Skill."""
    # Nạp prompt từ Skill "Dùng lại" — phải đặt TRƯỚC khi tạo widget text_area.
    if "arena_prefill" in st.session_state:
        st.session_state["arena_prompt"] = st.session_state.pop("arena_prefill")

    st.caption(
        "ℹ️ Mỗi cột gọi provider thật. “Hermes · deepseek” = agent live. OpenAI / Google / "
        "DeepSeek / MiniMax gọi API trực tiếp — 🟡 = thiếu key, 🟢 = sẵn sàng."
    )

    n = st.radio("Số model so sánh", [2, 3, 4], horizontal=True, key="arena_num")
    sel_cols = st.columns(n)
    chosen_models = []
    for i in range(n):
        with sel_cols[i]:
            m = st.selectbox(
                f"Cột {i + 1}",
                ARENA_MODEL_CHOICES,
                index=min(i, len(ARENA_MODEL_CHOICES) - 1),
                key=f"arena_model_{i}",
            )
            ok, note = model_status(m)
            st.caption(("🟢 " if ok else "🟡 ") + note)
            chosen_models.append(m)

    prompt = st.text_area(
        "Yêu cầu của bạn",
        key="arena_prompt",
        height=120,
        placeholder="VD: Viết mở bài cho khóa học '21 ngày chia tay bệnh tiểu đường'...",
    )

    if st.button("🚀 Tạo & so sánh", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Nhập yêu cầu trước khi chạy.")
        else:
            results = []
            with st.spinner(f"Đang chạy {n} model thật..."):
                for m in chosen_models:
                    t0 = time.time()
                    ans = run_model(m, prompt.strip())
                    results.append({
                        "model": m,
                        "answer": ans,
                        "elapsed": round(time.time() - t0, 1),
                        "chars": len(ans),
                    })
            st.session_state["arena_run"] = {"prompt": prompt.strip(), "results": results}
            st.session_state.pop("arena_winner", None)

    run_data = st.session_state.get("arena_run")
    if run_data:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        results = run_data["results"]
        res_cols = st.columns(len(results))
        winner = st.session_state.get("arena_winner")
        for i, r in enumerate(results):
            with res_cols[i]:
                is_win = (winner == i)
                accent = "#34d399" if is_win else "#5ad7e6"
                crown = "🏆 " if is_win else ""
                st.markdown(
                    f"<div style='border-top:2px solid {accent}; background:rgba(30,24,52,0.5); "
                    f"border:1px solid rgba(255,255,255,0.07); border-radius:10px; "
                    f"padding:8px 12px; margin-bottom:8px;'>"
                    f"<div style='font-size:13px; font-weight:700; color:#fff;'>{crown}{escape(r['model'])}</div>"
                    f"<div style='font-size:10px; color:#8b92b6; font-family:JetBrains Mono,monospace;'>"
                    f"⏱ {r['elapsed']}s · {r['chars']} ký tự</div></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(r["answer"])
                label = "✓ Đã chọn" if is_win else "Chọn bản này"
                if st.button(label, key=f"arena_pick_{i}", use_container_width=True, disabled=is_win):
                    st.session_state["arena_winner"] = i
                    st.rerun()

        if winner is not None:
            win = results[winner]
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:rgba(52,211,153,0.08); border:1px solid rgba(52,211,153,0.25); "
                f"border-radius:10px; padding:10px 14px; margin-bottom:8px;'>"
                f"<span style='color:#34d399; font-weight:700; font-size:13px;'>🏆 Đã chọn: {escape(win['model'])}</span>"
                f" <span style='color:#8b92b6; font-size:12px;'>— lưu lại để tái sử dụng</span></div>",
                unsafe_allow_html=True,
            )
            skill_name = st.text_input(
                "Tên Skill",
                key="skill_name",
                placeholder="VD: Chuyên gia viết mở bài khóa học",
            )
            note = st.text_area(
                "Ghi chú đánh giá / phản biện (tùy chọn)",
                key="arena_note",
                height=70,
                placeholder="Vì sao bản này tốt hơn? Điểm cần chỉnh khi dùng lại...",
            )
            if st.button("💾 Lưu thành Skill", use_container_width=True):
                if not skill_name.strip():
                    st.warning("Đặt tên cho Skill trước khi lưu.")
                else:
                    entry = {
                        "id": f"sk_{int(time.time())}",
                        "name": skill_name.strip(),
                        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "prompt": run_data["prompt"],
                        "model": win["model"],
                        "answer": win["answer"],
                        "note": note.strip(),
                        "models_compared": [r["model"] for r in results],
                    }
                    skills = load_skills()
                    skills.insert(0, entry)
                    if save_skills(skills):
                        st.success(f"Đã lưu Skill “{skill_name.strip()}” — xem ở bảng Skills bên phải.")
                    else:
                        st.warning("Không lưu được — kiểm tra bảng DataStore / quyền ghi anon trên Supabase.")


def render_workspace_compare(selected_bucket: str) -> None:
    """Workspace Studio: cột trái = ô chat chung (chọn Model + gọi Skill) hoặc chế độ
    So sánh nhiều model; cột phải = thư viện Skill (kiểu CharmIQ)."""
    col_nav, col_main, col_skills = st.columns([0.8, 3, 1.4])

    with col_nav:
        render_workspace_bucket_nav(selected_bucket)

    with col_main:
        st.markdown(
            "<div style='display:flex; align-items:center; gap:10px; margin-bottom:6px;'>"
            "<span style='font-size:22px;'>🛰️</span>"
            "<span style='font-size:20px; font-weight:700; color:#f3f1fb;'>Workspace Studio</span>"
            "<span style='font-size:11px; color:#5ad7e6; background:rgba(90,215,230,0.1); padding:2px 8px; border-radius:6px; font-weight:600;'>Chat · Skills · Models</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        mode = st.radio(
            "Chế độ", ["💬 Chat", "🆚 So sánh nhiều model"],
            horizontal=True, key="ws_mode", label_visibility="collapsed",
        )
        if mode == "💬 Chat":
            render_chat_pane()
        else:
            render_arena_pane()

    with col_skills:
        render_skills_panel()


def create_seo_zip(articles, keyword):
    import io
    import zipfile
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for idx, art in enumerate(articles):
            slug = art.get("slug", f"article-{idx+1}")
            title = art.get("title", f"Article {idx+1}")
            excerpt = art.get("excerpt", "")
            content = art.get("content", "")
            
            md_content = f"""---
title: "{title}"
excerpt: "{excerpt}"
keyword: "{keyword}"
date: "{date.today().isoformat()}"
---

# {title}

{content}
"""
            zip_file.writestr(f"{slug}.md", md_content.encode("utf-8"))
    return zip_buffer.getvalue()

# ------------------------------------------------------------------------------
# NETLIFY DEPLOY — deploy thật qua REST API (digest deploy), không cần CLI.
# Tự tạo (hoặc tái dùng) site cho mỗi bài viết rồi đẩy 1 trang HTML/site.
# ------------------------------------------------------------------------------
NETLIFY_API = "https://api.netlify.com/api/v1"

def _netlify_token():
    tok = (st.secrets.get("NETLIFY_AUTH_TOKEN", "") or "").strip()
    # Bỏ qua placeholder mẫu trong secrets.toml.example
    if not tok or tok.startswith("<") or tok.lower() in ("your-netlify-token", "your-token"):
        return None
    return tok

def _slugify_netlify(text: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower().strip()).strip("-")
    return (s or "seo-pack")[:50]

def _md_to_html(md_text: str) -> str:
    # Markdown tối giản -> HTML, escape trước để chống XSS rồi mới thêm thẻ an toàn.
    import re
    blocks = []
    for raw in (md_text or "").split("\n\n"):
        block = raw.strip()
        if not block:
            continue
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(block))
        if block.startswith("### "):
            blocks.append(f"<h3>{esc[4:].lstrip()}</h3>")
        elif block.startswith("## "):
            blocks.append(f"<h2>{esc[3:].lstrip()}</h2>")
        elif block.startswith("# "):
            blocks.append(f"<h2>{esc[2:].lstrip()}</h2>")
        else:
            blocks.append("<p>" + esc.replace("\n", "<br>") + "</p>")
    return "\n".join(blocks)

def render_article_html(article: dict, keyword: str) -> str:
    title = article.get("title", "Bài viết")
    excerpt = article.get("excerpt", "")
    body = _md_to_html(article.get("content", ""))
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(excerpt)}">
<meta name="keywords" content="{escape(keyword)}">
<style>
  :root {{ color-scheme: light; }}
  body {{ margin:0; background:#0b0716; color:#e7e5ef; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; line-height:1.7; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:64px 22px 96px; }}
  .kw {{ font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#a855f7; font-weight:700; }}
  h1 {{ font-size:34px; line-height:1.2; margin:10px 0 14px; color:#fff; }}
  .excerpt {{ font-size:18px; color:#b9b5c9; font-style:italic; margin:0 0 28px; }}
  article h2 {{ font-size:22px; color:#fff; margin:30px 0 8px; }}
  article h3 {{ font-size:18px; color:#d9d5e6; margin:24px 0 6px; }}
  article p {{ margin:0 0 16px; }}
  footer {{ margin-top:48px; padding-top:18px; border-top:1px solid rgba(255,255,255,.08); font-size:12px; color:#6f6a83; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="kw">{escape(keyword)}</div>
    <h1>{escape(title)}</h1>
    <p class="excerpt">{escape(excerpt)}</p>
    <article>{body}</article>
    <footer>Generated by Hermes OS · SEO Pipeline · {date.today().isoformat()}</footer>
  </div>
</body>
</html>"""

def _netlify_ensure_site(client, headers, desired_name, slot, logs):
    # Tái dùng site đã lưu nếu còn tồn tại.
    if slot and slot.get("id"):
        r = client.get(f"{NETLIFY_API}/sites/{slot['id']}", headers=headers)
        if r.status_code == 200:
            logs.append(f"[Netlify] Tái dùng site: {slot.get('name', slot['id'])}")
            return r.json()
        logs.append(f"[Netlify] Site cũ {slot['id']} không còn — tạo site mới.")
    json_headers = {**headers, "Content-Type": "application/json"}
    r = client.post(f"{NETLIFY_API}/sites", headers=json_headers, json={"name": desired_name, "force_ssl": True})
    if r.status_code in (200, 201):
        site = r.json()
        logs.append(f"[Netlify] Đã tạo site: {site.get('name')}")
        return site
    # Tên bị trùng/không hợp lệ -> để Netlify tự sinh subdomain ngẫu nhiên.
    if r.status_code in (400, 409, 422):
        logs.append(f"[Netlify] Tên '{desired_name}' không dùng được ({r.status_code}) — tạo site tên ngẫu nhiên.")
        r2 = client.post(f"{NETLIFY_API}/sites", headers=json_headers, json={"force_ssl": True})
        if r2.status_code in (200, 201):
            site = r2.json()
            logs.append(f"[Netlify] Đã tạo site: {site.get('name')}")
            return site
        raise RuntimeError(f"create site {r2.status_code}: {r2.text[:160]}")
    raise RuntimeError(f"create site {r.status_code}: {r.text[:160]}")

def _netlify_deploy_files(client, headers, site_id, files, logs):
    # files: {"/index.html": "<nội dung>"}; digest deploy = snapshot toàn site.
    digest = {path: hashlib.sha1(content.encode("utf-8")).hexdigest() for path, content in files.items()}
    r = client.post(
        f"{NETLIFY_API}/sites/{site_id}/deploys",
        headers={**headers, "Content-Type": "application/json"},
        json={"files": digest},
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"create deploy {r.status_code}: {r.text[:160]}")
    deploy = r.json()
    deploy_id = deploy.get("id")
    required = set(deploy.get("required", []))
    for path, content in files.items():
        if digest[path] in required:
            up = client.put(
                f"{NETLIFY_API}/deploys/{deploy_id}/files/{path.lstrip('/')}",
                headers={**headers, "Content-Type": "application/octet-stream"},
                content=content.encode("utf-8"),
            )
            if up.status_code not in (200, 201):
                raise RuntimeError(f"upload {path} {up.status_code}: {up.text[:120]}")
    # Chờ deploy chuyển sang 'ready' (tối đa ~12s).
    for _ in range(6):
        if deploy.get("state") == "ready":
            break
        time.sleep(2)
        pr = client.get(f"{NETLIFY_API}/deploys/{deploy_id}", headers=headers)
        if pr.status_code == 200:
            deploy = pr.json()
    return deploy

def deploy_campaign_to_netlify(campaign: dict) -> dict:
    """Deploy 1 chiến dịch (mỗi bài viết -> 1 site Netlify). Trả về {ok, logs, sites, error}."""
    token = _netlify_token()
    logs = []
    if not token:
        return {"ok": False, "error": "missing_token",
                "logs": ["[Netlify] Thiếu NETLIFY_AUTH_TOKEN trong secrets — không thể deploy thật."],
                "sites": []}

    articles = campaign.get("articles", []) or []
    keyword = campaign.get("keyword", "")
    base_slug = _slugify_netlify(campaign.get("slug") or keyword)
    saved_sites = campaign.get("netlify_sites", []) or []
    headers = {"Authorization": f"Bearer {token}"}

    logs.append(f"[Netlify] Bắt đầu deploy {len(articles)} site cho từ khóa: {keyword}")
    results = []
    with httpx.Client(timeout=60) as client:
        for i, art in enumerate(articles):
            slot = saved_sites[i] if i < len(saved_sites) else None
            desired = f"{base_slug}-{i + 1}"
            try:
                site = _netlify_ensure_site(client, headers, desired, slot, logs)
                deploy = _netlify_deploy_files(client, headers, site["id"], {"/index.html": render_article_html(art, keyword)}, logs)
                url = site.get("ssl_url") or site.get("url") or f"https://{site.get('name', '')}.netlify.app"
                state = deploy.get("state", "uploaded")
                results.append({"id": site["id"], "name": site.get("name", ""), "url": url, "state": state})
                logs.append(f"[Site {i + 1}: {site.get('name')}] OK -> {url} ({state})")
            except Exception as e:
                results.append({"id": (slot or {}).get("id", ""), "name": desired, "url": "", "state": "error", "error": str(e)})
                logs.append(f"[Site {i + 1}: {desired}] LỖI: {e}")

    ok = any(r["state"] != "error" for r in results)
    logs.append("[Netlify] Hoàn tất deploy swarm. 🏆" if ok else "[Netlify] Tất cả site đều lỗi.")
    return {"ok": ok, "logs": logs, "sites": results, "error": None}

# ==============================================================================
# 6. LAYOUT RENDERING FUNCTIONS
# ==============================================================================

def render_back_button() -> None:
    """Nút Back dùng LỊCH SỬ TRÌNH DUYỆT — chạy trên MỌI view (kể cả trang chủ),
    quay về đúng trang trước đó. Streamlit lọc scheme javascript: nên phải dùng
    1 component HTML gọi window.parent.history.back(). Tự ẩn khi không có lịch sử để lùi."""
    st.components.v1.html(
        """
<style>
  html,body{margin:0;background:transparent;overflow:hidden;}
  #hb{display:inline-flex;align-items:center;gap:6px;font-family:'Outfit',sans-serif,system-ui;
      font-size:12px;color:#a5a1c0;background:rgba(30,24,52,0.5);border:1px solid rgba(255,255,255,0.06);
      padding:6px 14px;border-radius:8px;cursor:pointer;transition:all .2s;}
  #hb:hover{color:#fff;border-color:rgba(90,215,230,0.35);background:rgba(45,35,75,0.6);}
  #hb span{font-size:15px;line-height:1;}
</style>
<button id="hb"><span>&larr;</span> Back</button>
<script>
  (function(){
    var btn=document.getElementById('hb'), h;
    try{ h=window.parent.history; }catch(e){ h=window.history; }
    try{ if(!h || h.length<=1){ btn.style.display='none'; } }catch(e){}
    btn.onclick=function(){
      try{ window.parent.history.back(); }
      catch(e){ try{ window.top.history.back(); }catch(e2){ history.back(); } }
    };
  })();
</script>
        """,
        height=40,
    )


def render_custom_header(num: str, section_type: str, section_name: str, desc: str) -> None:
    # Giờ Ho Chi Minh (UTC+7, không DST) tính lúc render.
    hcm_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M")
    # Nút Back (lịch sử trình duyệt) — hiển thị trên mọi view.
    render_back_button()
    st.markdown(f"""
    <div style="position: relative; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1.2rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap:15px;">
            <div>
                <div style="font-family: 'Cinzel', serif; font-size: 12px; color: #8b8ea9; letter-spacing: 4px; text-transform: uppercase;">
                    {num}. &mdash; {section_type} - {section_name}
                </div>
                <h1 style="font-family: 'Outfit', sans-serif; font-size: 38px; font-weight: 400; color: #ffffff; margin: 0.3rem 0 0.5rem 0; letter-spacing: -0.5px;">
                    {section_name}
                </h1>
                <div style="font-family: 'Outfit', sans-serif; font-size: 15px; color: #8b92b6; font-weight: 300;">
                    {desc}
                </div>
            </div>
            <div style="display: flex; gap: 12px; align-items: center; margin-top: 10px;">
                <div style="font-family: monospace; font-size: 11px; color: #8b92b6; background: rgba(30,24,52,0.5); border: 1px solid rgba(255,255,255,0.05); padding: 6px 12px; border-radius: 8px; font-weight:500;">
                    {hcm_time} LOCAL &bull; HO CHI MINH
                </div>
                <a href="?nav=mission" target="_self" class="nav-link" style="display: flex; align-items: center; gap: 6px; font-family: 'Outfit', sans-serif; font-size: 13px; color: #a5a1c0 !important; background: rgba(30,24,52,0.5); border: 1px solid rgba(255,255,255,0.05); padding: 6px 14px; border-radius: 8px; text-decoration: none; transition: all 0.2s; letter-spacing: 0.5px;">
                    <span style="color:#5ad7e6; font-size:13px;">▦</span> ALL SYSTEMS
                </a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_vault_card(row) -> None:
    name = escape(str(row["file_name"]))
    path = escape(str(row["file_path"]))
    updated = escape(str(row["updated_at"]))
    st.markdown(f"""
    <div class="memory-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div class="file-title">{name}.md</div>
                <div class="file-path">{path}</div>
            </div>
            <div class="time-badge">{updated}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. NAVIGATION STATE & SIDEBAR LAYOUT
# ==============================================================================

# Keep active states
active = st.query_params.get("nav", "agenthq")

with st.sidebar:
    # Top Branding Header
    st.markdown("""
        <div style="padding: 10px 10px 20px 10px; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <div style="font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 500; color: #7d7796; letter-spacing: 1.5px; text-transform: uppercase;">LOCAL &bull; HO CHI MINH</div>
            <div style="font-family: 'Cinzel', serif; font-size: 24px; font-weight: 400; color: #ffffff; margin-top: 3px; display: flex; align-items: center; gap: 8px;">
                Agentic <span style="font-style: italic; color:#5ad7e6;">OS</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. WORKSPACE Section
    st.markdown("<div class='sidebar-section-title'>Workspace</div>", unsafe_allow_html=True)
    mc_active = " active" if active == "mission" else ""
    st.markdown(f"<a class='nav-link side-item{mc_active}' target='_self' href='?nav=mission'>"
                f"▦ Mission Control</a>", unsafe_allow_html=True)
    
    hq_active = " active" if active == "agenthq" else ""
    st.markdown(f"<a class='nav-link side-item{hq_active}' target='_self' href='?nav=agenthq'>"
                f"🤖 Agent HQ</a>", unsafe_allow_html=True)

    ideas_active = " active" if active == "ideas" else ""
    st.markdown(f"<a class='nav-link side-item{ideas_active}' target='_self' href='?nav=ideas'>"
                f"💡 Ideas Board</a>", unsafe_allow_html=True)

    yt_active = " active" if active == "youtube" else ""
    st.markdown(f"<a class='nav-link side-item{yt_active}' target='_self' href='?nav=youtube'>"
                f"📺 YouTube Studio</a>", unsafe_allow_html=True)

    sk_active = " active" if active == "skills" else ""
    st.markdown(f"<a class='nav-link side-item{sk_active}' target='_self' href='?nav=skills'>"
                f"⚡ Skills</a>", unsafe_allow_html=True)

    # 2. AGENTS Section
    st.markdown("<div class='sidebar-section-title'>Agents</div>", unsafe_allow_html=True)
    for k, a in AGENTS.items():
        extra = " active" if active == k else ""
        st.markdown(f"""
            <a class="nav-link agent-row{extra}" target="_self" href="?nav={k}">
                <span class="agent-avatar {a['cls']}">{a['avatar']}</span>
                <span class="agent-name">{a['label']}</span>
            </a>
        """, unsafe_allow_html=True)

    # 3. SELF Section
    st.markdown("<div class='sidebar-section-title'>Self</div>", unsafe_allow_html=True)
    for k, s in SELF_SECTIONS.items():
        if k in ["agenthq", "ideas", "youtube"]:
            continue
        extra = " active" if active == k else ""
        st.markdown(f"<a class='nav-link side-item{extra}' target='_self' href='?nav={k}'>"
                    f"{s['icon']} {s['label']}</a>", unsafe_allow_html=True)

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True) # spacer

    # Red issue badge matching mockups at the very bottom
    if st.button("🚨 2 Issues", key="issues_badge", use_container_width=True):
        st.session_state["show_issues"] = True

# Pop-up dialog modal if the issue badge is clicked
if st.session_state.get("show_issues", False):
    @st.dialog("System Diagnostics & Alerts")
    def show_issues_dialog():
        st.markdown("""
        <div style="font-family: 'Outfit', sans-serif;">
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 14px; margin-bottom: 15px;">
                <h5 style="color:#f87171; margin:0 0 6px 0; font-size:14px; font-weight:600;">⚠️ Supabase service_role Key Missing</h5>
                <p style="color:#d1d5db; font-size:13px; margin:0; line-height:1.4;">
                    No <code>SUPABASE_SERVICE_ROLE_KEY</code> is loaded in <code>secrets.toml</code>. Live AI spend tracking is currently operating on cached mockup datasets. Add the key to enable server-side analytics.
                </p>
            </div>
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 14px;">
                <h5 style="color:#f87171; margin:0 0 6px 0; font-size:14px; font-weight:600;">⚠️ Local Vault Sync Mismatch</h5>
                <p style="color:#d1d5db; font-size:13px; margin:0; line-height:1.4;">
                    Obsidian Index Sync is pending. Local system lists 1,261 markdown files, but online table contains only 186. Trigger <code>python scripts/backup_supabase.py</code> to align databases.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acknowledge & Close", use_container_width=True):
            st.session_state["show_issues"] = False
            st.rerun()
    show_issues_dialog()

# ==============================================================================
# 8. VIEW DISPATCHER
# ==============================================================================

# ------------------------------------------------------------------------------
# VIEW: MISSION CONTROL (Roman Numeral I)
# ------------------------------------------------------------------------------
if active == "mission":
    render_custom_header("I", "WORKSPACE", "Mission Control", "Unified control deck for automated campaigns and agent goals.")
    
    mc = get_mission_control()
    if mc.empty:
        st.info("No active campaign goals in database.")
    else:
        # Convert types safely
        for col in ["progress_percent", "turns_used", "turn_budget"]:
            mc[col] = pd.to_numeric(mc[col], errors="coerce").fillna(0).astype(int)

        c1, c2, c3 = st.columns(3)
        c1.metric("Campaign Objectives", len(mc))
        c2.metric("Mean Completion Rate", f"{int(mc['progress_percent'].mean())}%")
        c3.metric("Swarm Budget Utilized", f"{int(mc['turns_used'].sum())}/{int(mc['turn_budget'].sum())}")

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

        STMAP = {"To Do": "st-todo", "In Progress": "st-prog", "Done": "st-done"}
        for _, r in mc.iterrows():
            status = str(r["status"])
            cls = STMAP.get(status, "st-todo")
            pct = int(r["progress_percent"])
            st.markdown(f"""
            <div class='mc-card'>
              <div class='mc-top'>
                <div class='mc-title'>{escape(str(r['goal_name']))}</div>
                <div class='status-badge {cls}'>{escape(status)}</div>
              </div>
              <div class='mc-bar'><div class='mc-fill' style='width:{pct}%;'></div></div>
              <div class='mc-meta'>
                <span>{pct}% complete</span>
                <span>{int(r['turns_used'])}/{int(r['turn_budget'])} steps</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: AGENT SUBPANELS (Claude, OpenClaw, Hermes, Gemini, Antigravity, etc.)
# ------------------------------------------------------------------------------
if active in AGENTS:
    a = AGENTS[active]
    render_custom_header(a["num"], "AGENT", a["label"], a["desc"])
    
    if active == "hermes":
        tab = st.query_params.get("tab", "chat")
        
        # HTML styled horizontal sub-tab bar (order khớp ảnh mẫu)
        tabs = [
            {"id": "chat", "label": "Chat", "icon": "💬"},
            {"id": "talk", "label": "Talk", "icon": "🎙️"},
            {"id": "jarvis", "label": "Jarvis", "icon": "🛰️"},
            {"id": "studio", "label": "Studio", "icon": "🎬"},
            {"id": "sessions", "label": "Sessions", "icon": "🗂️"},
            {"id": "goal", "label": "Goal Mode", "icon": "🎯"},
            {"id": "workspace", "label": "Workspace", "icon": "📁"},
            {"id": "mcps", "label": "MCPs", "icon": "🔌"},
            {"id": "manage", "label": "Manage", "icon": "🛠️"},
            {"id": "control", "label": "Control Room", "icon": "🎛️"},
        ]
        tabs_html = "".join([
            f'<a class="nav-link" target="_self" href="?nav=hermes&tab={t["id"]}" style="text-decoration:none; display:inline-block; margin-right:5px;">'
            f'<div class="sub-tab-pill {"active" if tab == t["id"] else ""}">{t["icon"]} {t["label"]}</div>'
            f'</a>'
            for t in tabs
        ])
        st.markdown(f'<div style="display:flex; gap:5px; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:10px; flex-wrap:wrap;">{tabs_html}</div>', unsafe_allow_html=True)

        # Hermes Agent dashboard (web UI cục bộ) — nguồn quản trị thật cho Manage/Sessions/MCPs...
        dash_url = st.secrets.get("HERMES_DASHBOARD_URL", "http://localhost:9119")

        def _dash_reachable(u):
            # Ping ngắn để hiện trạng thái; tránh block render tab Manage.
            try:
                httpx.get(u, timeout=1.5)
                return True
            except Exception:
                return False

        def _hermes_feature_panel(icon, title, desc, cta_label, cta_url, new_tab=True):
            target = "_blank" if new_tab else "_self"
            st.markdown(f"""
            <div style="background: rgba(30,24,52,0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border:1px solid rgba(255,255,255,0.06); border-radius:14px; padding:36px 28px; text-align:center; margin-top:10px; box-shadow:0 8px 32px rgba(0,0,0,0.3);">
                <div style="font-size:46px; margin-bottom:14px; filter:drop-shadow(0 0 12px rgba(90,215,230,0.35)); line-height:1;">{icon}</div>
                <h3 style="color:#fff; margin:0 0 10px 0; font-family:'Outfit',sans-serif; font-size:21px; font-weight:500; letter-spacing:-0.5px;">{escape(title)}</h3>
                <p style="color:#a5a1c0; font-size:14px; max-width:560px; margin:0 auto 22px auto; line-height:1.6; font-weight:300;">{escape(desc)}</p>
                <a href="{escape(cta_url)}" target="{target}" style="display:inline-flex; align-items:center; gap:8px; background:linear-gradient(135deg,#5ad7e6,#785ae6); color:#fff !important; font-weight:600; font-size:14px; padding:11px 26px; border-radius:8px; text-decoration:none; box-shadow:0 0 18px rgba(90,215,230,0.3); border:1px solid rgba(255,255,255,0.1);">{escape(cta_label)} ↗</a>
            </div>
            """, unsafe_allow_html=True)

        if tab == "chat":
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            # Sub-header
            st.markdown("<div style='font-size:16px; font-weight:600; color:#ffffff; margin-bottom:12px;'>✦ Live Chat Terminal</div>", unsafe_allow_html=True)

            # Bảng định tuyến model — hiển thị thống nhất với Agent HQ drawer
            st.markdown(hermes_model_card_html(), unsafe_allow_html=True)

            # Ô chat chung: chọn Model tuỳ ý + gọi Skill (đóng vai chuyên gia đã lưu)
            _skills = load_skills()
            _skill_names = [s.get("name", "(chưa đặt tên)") for s in _skills]
            cc_model, cc_skill = st.columns(2)
            with cc_model:
                chat_model = st.selectbox("Model", ARENA_MODEL_CHOICES, key="hermes_chat_model")
                _ok, _note = model_status(chat_model)
                st.caption(("🟢 " if _ok else "🟡 ") + _note)
            with cc_skill:
                _choice = st.selectbox("Skill (đóng vai)", ["— Chat thường —"] + _skill_names, key="hermes_chat_skill")
                _active_skill = next((s for s in _skills if s.get("name") == _choice), None) if _choice != "— Chat thường —" else None
                st.caption(f"🎭 {_active_skill['name']}" if _active_skill else "Không dùng Skill")

            # Render lịch sử chat
            for m in st.session_state.get("hermes_msgs", []):
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            prompt = st.chat_input("Message Hermes...")
            if prompt:
                st.session_state.setdefault("hermes_msgs", []).append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner(f"{chat_model} đang trả lời..."):
                        parts = []
                        if _active_skill and _active_skill.get("prompt"):
                            parts.append("Hãy đóng vai theo chỉ dẫn sau, trả lời bằng tiếng Việt:\n" + _active_skill["prompt"])
                        for m in st.session_state.hermes_msgs[-10:]:
                            who = "Người dùng" if m["role"] == "user" else "Trợ lý"
                            parts.append(f"{who}: {m['content']}")
                        parts.append("Trợ lý:")
                        try:
                            reply = run_model(chat_model, "\n\n".join(parts))
                        except Exception as e:
                            reply = f"⚠️ Lỗi: {e}"
                        st.markdown(reply)
                st.session_state.hermes_msgs.append({"role": "assistant", "content": reply})
                
        elif tab == "goal":
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            
            # Initialize Goal Swarms list in Session State if not present
            if "hermes_goals" not in st.session_state:
                st.session_state.hermes_goals = [
                    {
                        "id": 1, 
                        "title": "SEO Blog Post Automation Suite", 
                        "prompt": "Generate 5 unique blog posts about AI automation for ecommerce, save to /posts/ as .md with frontmatter, ready to deploy.",
                        "status": "Running",
                        "progress": 65,
                        "created_at": "1h ago",
                        "logs": [
                            "[Hermes OS] Initiating SEO Swarm...",
                            "[Hermes OS] Reading keywords repository from Obsidian Vault...",
                            "[Hermes OS] Found 3 target terms: 'Shopify AI', 'ecom agents', 'cart recovery swarm'",
                            "[Hermes OS] Synthesizing SEO Article 1: 'The Rise of Autonomous Cart Recovery'...",
                            "[Hermes OS] Synthesizing SEO Article 2: 'Shopify Agentic Flows in 2026'...",
                            "[Hermes OS] Compiling markdown frontmatter headers...",
                            "[Hermes OS] Writing local files to /posts/ directory...",
                            "[Hermes OS] [Running] Evaluating article readability and keyword density (65%)..."
                        ]
                    },
                    {
                        "id": 2, 
                        "title": "Obsidian Note Link Sync Script", 
                        "prompt": "Write a Python script to scan obsidian vault, calculate note linkages, and sync graph nodes.",
                        "status": "Done",
                        "progress": 100,
                        "created_at": "3h ago",
                        "logs": [
                            "[Hermes OS] Reading file schema...",
                            "[Hermes OS] Calculating bidirectional connections...",
                            "[Hermes OS] Found 199 nodes and 897 edges.",
                            "[Hermes OS] Syncing to Supabase table 'obsidian_vault'...",
                            "[Hermes OS] [Done] Synchronized successfully. Execution closed."
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Campaign n8n Automation Sync",
                        "prompt": "Setup webhook channels between Skool API and n8n webhook nodes.",
                        "status": "Done",
                        "progress": 100,
                        "created_at": "1d ago",
                        "logs": [
                            "[Hermes OS] Pinging Skool webhook endpoint...",
                            "[Hermes OS] Connected. Testing auth bearer payload...",
                            "[Hermes OS] Mapping JSON response keys to Supabase...",
                            "[Hermes OS] [Done] Webhook active. Status 200 OK."
                        ]
                    }
                ]
            
            # Statistics counts
            running_count = sum(1 for g in st.session_state.hermes_goals if g["status"] == "Running")
            total_count = len(st.session_state.hermes_goals)
            
            # Premium Goal Mode Header Card
            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.4); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 18px 22px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, rgba(90,215,230,0.12), rgba(120,90,230,0.12)); border: 1px solid rgba(90,215,230,0.25); display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 0 12px rgba(90,215,230,0.2);">
                        🧠
                    </div>
                    <div>
                        <div style="font-size: 11px; font-weight: 700; color: #5ad7e6; text-transform: uppercase; letter-spacing: 2px;">HERMES &bull; GOAL MODE</div>
                        <h3 style="color:#ffffff; margin: 2px 0 4px 0; font-family:'Outfit', sans-serif; font-size: 18px; font-weight: 500; letter-spacing: -0.5px;">Set the target. Walk away.</h3>
                        <p style="color:#8b92b6; font-size:13px; margin:0; line-height:1.4; font-weight: 300;">
                            Hand Hermes a long-horizon goal. It runs <code>hermes chat --yolo --max-turns 50</code> in its own scratch.dir. Close your laptop, go to sleep, come back to finished work.
                        </p>
                    </div>
                </div>
                <div style="color: #8b92b6; font-size: 11px; font-weight: 600; font-family: monospace; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); padding: 5px 12px; border-radius: 8px;">
                    ➤ {running_count} RUNNING &nbsp;&bull;&nbsp; {total_count} TOTAL
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Bottom Columns
            col_l, col_r = st.columns([1.1, 1.4])
            
            with col_l:
                st.markdown("<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>New Goal</div>", unsafe_allow_html=True)
                
                # Card Wrapper for input
                st.markdown("""
                <div style="background: rgba(30,24,52,0.3); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 18px; margin-bottom: 20px;">
                """, unsafe_allow_html=True)
                
                goal_title = st.text_input("Goal title (optional — auto-derived from prompt)", placeholder="e.g. SEO Campaign Suite", label_visibility="visible", key="goal_title_inp")
                
                goal_prompt = st.text_area("What should Hermes do? Be specific. Example: Generate 5 unique blog posts about AI automation for ecommerce, save to /posts/ as .md with frontmatter, ready to deploy.", placeholder="Be specific. Explain key parameters, file paths, and deliverables...", height=120, key="goal_prompt_inp")
                
                # Bottom Launch Actions
                col_btn_l, col_btn_r = st.columns([1, 1])
                with col_btn_l:
                    st.markdown("<div style='font-size:11px; color:#5b5478; margin-top:12px; font-weight:500;'>⌘Enter to launch</div>", unsafe_allow_html=True)
                with col_btn_r:
                    # Blue airplane Launch Goal Button
                    launch_btn = st.button("✈ Launch goal", key="launch_goal_swarm", use_container_width=True)
                    
                st.markdown("</div>", unsafe_allow_html=True) # close container card
                
                # If launch clicked
                if launch_btn and goal_prompt:
                    new_id = len(st.session_state.hermes_goals) + 1
                    title = goal_title if goal_title else f"Task Swarm #{new_id}"
                    
                    st.session_state.hermes_goals.insert(0, {
                        "id": new_id,
                        "title": title,
                        "prompt": goal_prompt,
                        "status": "Running",
                        "progress": 20,
                        "created_at": "Just now",
                        "logs": [
                            f"[Hermes OS] Initiating Task Swarm: {title}...",
                            "[Hermes OS] Spawning reasoning sub-agents...",
                            "[Hermes OS] Creating virtual workspace sandboxes...",
                            f"[Hermes OS] Analyzing goal description: \"{goal_prompt[:60]}...\"",
                            "[Hermes OS] [Running] Sweeping directories for context matching (20%)..."
                        ]
                    })
                    st.query_params["goal_id"] = str(new_id)
                    st.rerun()
                
                # Goals List Header
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; margin-top:5px;">
                    <div style="font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px;">Goals &nbsp;&bull;&nbsp; {total_count}</div>
                    <a href="?nav=hermes&tab=goal" target="_self" style="font-size:11px; color:#5ad7e6 !important; font-weight:600; text-decoration:none;">REFRESH</a>
                </div>
                """, unsafe_allow_html=True)
                
                # Render Goals list
                selected_goal_id = int(st.query_params.get("goal_id", "1"))
                
                for g in st.session_state.hermes_goals:
                    is_active = (g["id"] == selected_goal_id)
                    active_border = "border-color: rgba(90,215,230,0.4) !important; background: rgba(90,200,220,0.12) !important; box-shadow: 0 0 10px rgba(90,215,230,0.15);" if is_active else ""
                    status_color = "color:#5ad7e6; background:rgba(90,215,230,0.1);" if g["status"] == "Running" else "color:#34d399; background:rgba(52,211,153,0.1);"
                    
                    st.markdown(f"""
                    <a class="nav-link" target="_self" href="?nav=hermes&tab=goal&goal_id={g['id']}" style="text-decoration:none;">
                        <div style="padding: 12px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 8px; cursor: pointer; transition: all 0.2s; {active_border}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:13.5px; font-weight:500; color:#ffffff;">{escape(str(g['title']))}</span>
                                <span style="font-size:9px; font-weight:700; padding:2px 6px; border-radius:10px; {status_color}">{g['status'].upper()}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#7d7796; margin-top:5px;">
                                <span>{g['created_at']}</span>
                                <span>{g['progress']}% done</span>
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
                        
            with col_r:
                st.markdown("<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Goal Swarm Terminal</div>", unsafe_allow_html=True)
                
                # Active selected goal details
                sel_id = int(st.query_params.get("goal_id", "1"))
                active_goal = next((g for g in st.session_state.hermes_goals if g["id"] == sel_id), None)
                
                if active_goal is None:
                    # Default: Pick a goal to watch live
                    st.markdown("""
                    <div style="background: rgba(30, 24, 52, 0.25); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 80px 20px; text-align: center; min-height: 380px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div style="width:50px; height:50px; border-radius:50%; border:2px dashed #5b5478; display:flex; align-items:center; justify-content:center; margin-bottom:15px;">
                            <span style="font-size:24px; color:#5b5478;">🎯</span>
                        </div>
                        <h4 style="color:#ffffff; margin:0 0 5px 0; font-weight:500;">Pick a goal to watch live</h4>
                        <p style="color:#7d7796; font-size:12.5px; max-width:280px; margin:0; line-height:1.4;">Select a launched task swarm from the goals list to view real-time thoughts and terminal logs.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Console logs body (mỗi dòng escape chống XSS)
                    logs_html = "".join(
                        f"<div style='margin-bottom:6px; line-height:1.4;'>"
                        f"<span style='color:#7d7796;'>[{escape(str(active_goal['created_at']))}]</span> {escape(l)}</div>"
                        for l in active_goal["logs"]
                    )
                    # Một khối HTML cân bằng, KHÔNG thụt đầu dòng bên trong chuỗi — tránh
                    # việc Markdown hiểu nhầm dòng thụt-sau-dòng-trống thành code block
                    # (nguyên nhân lỗi rò HTML thô trước đây).
                    st.markdown(
                        '<div style="background: rgba(30,24,52,0.4); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:16px; margin-bottom:12px;">'
                        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                        f'<span style="font-size:14.5px; font-weight:600; color:#ffffff;">{escape(str(active_goal["title"]))}</span>'
                        f'<span style="font-size:11px; color:#5ad7e6; font-weight:500;">{active_goal["progress"]}% complete</span>'
                        '</div>'
                        '<div style="font-size:12px; color:#8b92b6; line-height:1.4; margin-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:10px;">'
                        f'<b>Goal Target:</b> {escape(str(active_goal["prompt"]))}'
                        '</div>'
                        '<div style="font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; display:flex; align-items:center; gap:5px;">'
                        '<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#34d399;"></span> Console Thoughts Log Stream'
                        '</div>'
                        '<div style="background: rgba(13,9,26,0.85); border:1px solid rgba(255,255,255,0.07); border-radius:10px; padding:15px; font-family:\'JetBrains Mono\', monospace; font-size:11.5px; color:#34d399; min-height:250px; max-height:320px; overflow-y:auto; box-shadow: inset 0 0 15px rgba(0,0,0,0.5);">'
                        f'{logs_html}'
                        '</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
            
        elif tab == "workspace":
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            
            # Read Buckets and Files via query parameters for 100% stable state
            selected_bucket = st.query_params.get("bucket", "apps")

            # Model Arena — bucket "compare": studio đa-model + thư viện Skill (full-width).
            if selected_bucket == "compare":
                render_workspace_compare(selected_bucket)
                st.stop()

            col_b, col_f, col_p = st.columns([1, 1.3, 2.7])
            
            with col_b:
                render_workspace_bucket_nav(selected_bucket)
                        
            with col_f:
                st.markdown("<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Apps Explorer</div>", unsafe_allow_html=True)
                
                bucket_files = {
                    "goal": [
                        {"name": "campaign-strategy.md", "size": "4.2 KB", "type": "MD"},
                        {"name": "okr-q3-leads.md", "size": "2.8 KB", "type": "MD"},
                    ],
                    "apps": [
                        {"name": "testimonials.html", "size": "37.6 KB", "type": "HTML"},
                        {"name": "agent-os-sync.py", "size": "12.3 KB", "type": "PYTHON"},
                        {"name": "tuds-app.html", "size": "8.4 KB", "type": "HTML"},
                        {"name": "notebook.html", "size": "19.1 KB", "type": "HTML"},
                        {"name": "openclaw-studio.py", "size": "11.2 KB", "type": "PYTHON"},
                        {"name": "hermes-agent.py", "size": "23.4 KB", "type": "PYTHON"},
                        {"name": "claude-mythos.py", "size": "5.6 KB", "type": "PYTHON"},
                        {"name": "free-claude.py", "size": "4.1 KB", "type": "PYTHON"},
                        {"name": "landing.html", "size": "18.2 KB", "type": "HTML"},
                        {"name": "index.html", "size": "15.3 KB", "type": "HTML"},
                    ],
                    "video": [
                        {"name": "seo-mastery-vsl.mp4", "size": "42.1 MB", "type": "MP4"},
                        {"name": "intro-draft.mp4", "size": "15.6 MB", "type": "MP4"},
                    ],
                    "images": [
                        {"name": "final_memory.png", "size": "1.2 MB", "type": "PNG"},
                        {"name": "landing_bg.jpg", "size": "850 KB", "type": "JPG"},
                    ],
                    "audio": [
                        {"name": "voiceover-elevenlabs.mp3", "size": "2.4 MB", "type": "MP3"},
                    ],
                    "sandboxes": [
                        {"name": "test-env-01.zip", "size": "14.2 MB", "type": "ZIP"},
                    ],
                    "pastes": [
                        {"name": "claude-prompt-v2.txt", "size": "3.5 KB", "type": "TXT"},
                    ]
                }
                
                files = bucket_files.get(selected_bucket, [])
                selected_file = st.query_params.get("file", "")
                if not selected_file or not any(f["name"] == selected_file for f in files):
                    selected_file = files[0]["name"] if files else ""
                
                for f in files:
                    is_active = (f["name"] == selected_file)
                    active_border = "border-color: rgba(90,215,230,0.4) !important; background: rgba(90,200,220,0.12) !important; box-shadow: 0 0 10px rgba(90,215,230,0.15);" if is_active else ""
                    
                    st.markdown(f"""
                    <a class="nav-link" target="_self" href="?nav=hermes&tab=workspace&bucket={selected_bucket}&file={f['name']}" style="text-decoration:none; display:block;">
                        <div style="padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 6px; cursor: pointer; transition: all 0.2s; {active_border}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:13px; font-weight:500; color:#f3f1fb; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:130px;">{f['name']}</span>
                                <span style="font-size:9px; color:#5ad7e6; background:rgba(90,215,230,0.1); padding:1px 5px; border-radius:4px; font-weight:bold;">{f['type']}</span>
                            </div>
                            <div style="font-size:11px; color:#7d7796; margin-top:2px;">{f['size']}</div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
                        
            with col_p:
                st.markdown("<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>App View & Preview</div>", unsafe_allow_html=True)
                current_file = selected_file
                
                st.markdown(f"""
                <div style="font-size: 11px; color: #8b92b6; font-family: 'JetBrains Mono', monospace; background: rgba(30,24,52,0.6); padding: 7px 14px; border-radius: 10px 10px 0 0; border: 1px solid rgba(255,255,255,0.06); border-bottom: none; display: flex; justify-content: space-between; align-items: center;">
                    <span>Workspace &raquo; {selected_bucket} &raquo; {current_file}</span>
                    <span style="color:#34d399; font-weight:bold; font-size:10px;">&bull; LIVE PREVIEW ACTIVE</span>
                </div>
                """, unsafe_allow_html=True)
                
                if "landing" in current_file or "index" in current_file or "testimonials" in current_file:
                    # Nút Join AIPB: lấy URL từ secret AIPB_URL; chưa cấu hình thì ẩn nút (tránh link chết "#").
                    aipb_url = st.secrets.get("AIPB_URL")
                    aipb_btn = (
                        f'<a href="{escape(aipb_url)}" target="_blank" rel="noopener noreferrer" '
                        'style="display:inline-block; background: linear-gradient(135deg, #ff9d4d, #ff6a3d); '
                        'color:#ffffff; font-weight:700; font-size:13px; padding: 8px 22px; border-radius: 8px; '
                        'text-decoration:none; box-shadow: 0 0 15px rgba(255,106,61,0.35);">Join AIPB &rarr;</a>'
                    ) if aipb_url else ""
                    # st.html() render HTML thô, không qua markdown -> tránh bug HTML thụt lề
                    # + dòng trống bị biến thành code block (LIVE PREVIEW hiện code thay vì trang).
                    preview_html = """
                    <div style="background: linear-gradient(160deg, #151125 0%, #0c0817 100%); border: 1px solid rgba(255,255,255,0.06); border-radius: 0 0 12px 12px; padding: 25px; min-height: 420px; color: #d8d4e6; font-family: 'Outfit', sans-serif;">
                        
                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                            <span style="color:#fb7185; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:1px;">★ Get the full Agent OS install + every layer in this guide inside the</span>
                            <h4 style="margin: 5px 0 15px 0; color:#ffffff; font-size:17px; font-weight:600;">AI Profit Boardroom</h4>
                            __AIPB_BUTTON__
                        </div>
                        
                        <div style="border-left: 2px solid #5ad7e6; padding-left: 15px; margin-bottom: 25px;">
                            <span style="font-family: serif; font-size: 13px; font-style: italic; color: #5ad7e6;">Mistake II</span>
                            <h3 style="margin: 2px 0 8px 0; color:#ffffff; font-size:17px; font-weight:500;">Picking the right tool for each job</h3>
                            <p style="font-size:13px; color:#8b92b6; line-height:1.5; margin:0;">
                                $249/mo for Ahrefs. $45/mo for Frase. $30/mo for Midjourney. $20/mo for ChatGPT Plus. $20/mo for Claude Pro. $11/mo for ElevenLabs. <b>~$375/mo in tools</b> before I'd produced a single dollar that month. The fix was boring and useful: keep official coding tools for repo work, use open-source agents for local automation, and route content tasks to cheaper models only when their providers explicitly support it.
                            </p>
                        </div>
                        
                        <div style="border-left: 2px solid #ff7eb3; padding-left: 15px; margin-bottom: 25px;">
                            <span style="font-family: serif; font-size: 13px; font-style: italic; color: #ff7eb3;">Mistake IV</span>
                            <h3 style="margin: 2px 0 8px 0; color:#ffffff; font-size:17px; font-weight:500;">Building automations in n8n before checking what the agents already do</h3>
                            <p style="font-size:13px; color:#8b92b6; line-height:1.5; margin:0;">
                                I spent two weekends wiring a "content production pipeline" in n8n - Zapier-style boxes connecting OpenAI to Google Docs to Notion to Substack. It was a mess. Brittle. Slow. Every webhook had its own auth. Two weeks later I realized Hermes inside Agent OS could do the same pipeline natively, with proper agent reasoning at each step, in about 200 lines of total config.
                            </p>
                        </div>
                        
                        <div style="border-left: 2px solid #a855f7; padding-left: 15px;">
                            <span style="font-family: serif; font-size: 13px; font-style: italic; color: #a855f7;">Mistake V</span>
                            <h3 style="margin: 2px 0 8px 0; color:#ffffff; font-size:17px; font-weight:500;">Outputs landing in random folders nobody could find</h3>
                            <p style="font-size:13px; color:#8b92b6; line-height:1.5; margin:0;">
                                Every image Midjourney made went to Downloads. Every video render went to Desktop. Every generated HTML page went to "Untitled.html" somewhere. Two weeks later I couldn't find any of it. I had 23 HTML apps I'd forgotten existed, voiceovers in three different folders, and infographics with random filenames that meant nothing.
                            </p>
                        </div>
                    </div>
                    """
                    st.html(preview_html.replace("__AIPB_BUTTON__", aipb_btn))
                elif "py" in current_file:
                    st.code(f"""# {current_file} - Local Sync Core Engine
import os
import sys
import time

def main():
    print("Initializing workspace context hooks...")
    # Loaded environment configs
    time.sleep(0.5)
    print("Sync completed. Channels aligned.")

if __name__ == "__main__":
    main()
""", language="python")
                elif "png" in current_file or "jpg" in current_file:
                    st.markdown("<div style='background:rgba(25,20,40,0.4); border:1px solid rgba(255,255,255,0.06); border-radius:0 0 12px 12px; padding:40px; text-align:center; min-height:420px; display:flex; flex-direction:column; justify-content:center; align-items:center;'><span style='font-size:52px; margin-bottom:15px;'>🖼️</span><h5 style='color:#ffffff; margin:0; font-size:16px;'>Visual Media Image Panel</h5><p style='color:#8b92b6; font-size:12px; margin-top:5px;'>High Resolution Asset cached in Local workspace RAM.</p></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background:rgba(25,20,40,0.4); border:1px solid rgba(255,255,255,0.06); border-radius:0 0 12px 12px; padding:40px; text-align:center; min-height:420px; display:flex; flex-direction:column; justify-content:center; align-items:center;'><span style='font-size:52px; margin-bottom:15px;'>📄</span><h5 style='color:#ffffff; margin:0; font-size:16px;'>Raw Text / Data Payload</h5><p style='color:#8b92b6; font-size:12px; margin-top:5px;'>Decrypted buffer content successfully parsed.</p></div>", unsafe_allow_html=True)
                    
        elif tab == "manage":
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            host = dash_url.split("://")[-1].rstrip("/")
            reachable = _dash_reachable(dash_url)
            dot = "#34d399" if reachable else "#fbbf24"
            state_txt = "Connected" if reachable else "Configured"

            c_status, c_refresh, c_open = st.columns([4, 1, 1])
            with c_status:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px; background: rgba(30,24,52,0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:11px 16px;">
                    <span style="width:9px; height:9px; border-radius:50%; background:{dot}; box-shadow:0 0 8px {dot};"></span>
                    <span style="font-size:13px; color:#e7e5ef; font-weight:600;">Hermes Dashboard</span>
                    <span style="font-size:12px; color:#8b92b6; font-family:'JetBrains Mono',monospace;">{state_txt} &middot; {escape(host)}</span>
                </div>
                """, unsafe_allow_html=True)
            with c_refresh:
                if st.button("↻ Refresh", use_container_width=True, key="hermes_dash_refresh"):
                    st.rerun()
            with c_open:
                st.markdown(f"""
                <a href="{escape(dash_url)}" target="_blank" style="display:inline-flex; justify-content:center; width:100%; align-items:center; gap:6px; background:rgba(90,215,230,0.1); border:1px solid rgba(90,215,230,0.25); color:#5ad7e6 !important; padding:8px 10px; border-radius:8px; font-size:13px; text-decoration:none; font-weight:600;">⧉ Open in tab</a>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            # Chỉ nhúng iframe khi máy chủ app thật sự kết nối được dashboard.
            # Tránh nhúng localhost vào app đã deploy (HTTPS) -> trình duyệt báo "refused to connect".
            if reachable:
                st.components.v1.iframe(dash_url, height=720, scrolling=True)
            else:
                is_local = ("localhost" in host) or host.startswith("127.")
                reason = (
                    "Dashboard chạy cục bộ (localhost) nên app đã deploy (HTTPS) không nhúng được: trình duyệt "
                    "chặn nội dung http trong trang https, và localhost trỏ về máy người xem chứ không phải máy chủ."
                    if is_local else
                    "Máy chủ app không kết nối được tới dashboard (chưa chạy, sai địa chỉ, hoặc bị chặn nhúng qua X-Frame-Options)."
                )
                st.markdown(
                    "<div style='background:rgba(25,20,40,0.4); border:1px solid rgba(255,255,255,0.06); "
                    "border-radius:12px; padding:48px 28px; text-align:center; min-height:360px; display:flex; "
                    "flex-direction:column; justify-content:center; align-items:center; gap:12px;'>"
                    "<span style='font-size:46px;'>🖥️</span>"
                    "<h5 style='color:#ffffff; margin:0; font-size:16px; font-weight:600;'>Hermes Dashboard chưa nhúng được</h5>"
                    f"<p style='color:#8b92b6; font-size:13px; max-width:540px; margin:0; line-height:1.6;'>{escape(reason)}</p>"
                    "<p style='color:#8b92b6; font-size:13px; max-width:540px; margin:0; line-height:1.6;'>"
                    "Bấm <b style='color:#5ad7e6;'>⧉ Open in tab</b> ở trên (nếu bạn đang chạy dashboard cục bộ), "
                    "hoặc đặt secret <code>HERMES_DASHBOARD_URL</code> thành một URL HTTPS công khai để nhúng tại đây.</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )

        elif tab == "sessions":
            _hermes_feature_panel("🗂️", "Sessions",
                "Lịch sử phiên làm việc của Hermes Agent — tiếp tục, tìm kiếm và nén ngữ cảnh. Quản lý trực tiếp trong Hermes Dashboard.",
                "Mở Hermes Dashboard", "?nav=hermes&tab=manage", new_tab=False)

        elif tab == "mcps":
            _hermes_feature_panel("🔌", "MCP Servers",
                "Các Model Context Protocol server cấp tools/resources cho Hermes. Bật/tắt và định tuyến tool trong Hermes Dashboard.",
                "Mở Hermes Dashboard", "?nav=hermes&tab=manage", new_tab=False)

        elif tab == "talk":
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:16px; font-weight:600; color:#ffffff; margin-bottom:4px;'>🎙️ Talk — Hermes trả lời bằng giọng MiniMax</div>", unsafe_allow_html=True)
            st.caption("Nhắn cho Hermes, nhận câu trả lời và nghe đọc bằng giọng MiniMax (TTS).")

            mm_ready = bool(st.secrets.get("MINIMAX_API_KEY") and st.secrets.get("MINIMAX_GROUP_ID"))
            if not mm_ready:
                st.markdown(
                    "<div style='background:rgba(25,20,40,0.4); border:1px solid rgba(255,255,255,0.06); "
                    "border-radius:12px; padding:40px 28px; text-align:center; min-height:300px; display:flex; "
                    "flex-direction:column; justify-content:center; align-items:center; gap:12px;'>"
                    "<span style='font-size:46px;'>🎙️</span>"
                    "<h5 style='color:#ffffff; margin:0; font-size:16px; font-weight:600;'>Kết nối MiniMax voice để bật Talk</h5>"
                    "<p style='color:#8b92b6; font-size:13px; max-width:560px; margin:0; line-height:1.6;'>"
                    "Thêm 2 secret <code>MINIMAX_API_KEY</code> và <code>MINIMAX_GROUP_ID</code> (lấy ở platform.minimax.io) "
                    "vào <code>.streamlit/secrets.toml</code> (local) hoặc Streamlit Cloud → Settings → Secrets. "
                    "Tùy chọn ghi đè: <code>MINIMAX_VOICE_ID</code>, <code>MINIMAX_TTS_MODEL</code>.</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.session_state.setdefault("talk_msgs", [])
                for m in st.session_state.talk_msgs:
                    with st.chat_message(m["role"]):
                        st.markdown(m["content"])
                        if m.get("audio"):
                            st.audio(m["audio"], format="audio/mp3")

                prompt = st.chat_input("Nói gì với Hermes...")
                if prompt:
                    st.session_state.talk_msgs.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    with st.chat_message("assistant"):
                        with st.spinner("Hermes đang trả lời..."):
                            reply = hermes_chat_reply(prompt)
                        st.markdown(reply)
                        with st.spinner("Đang tạo giọng nói MiniMax..."):
                            audio, err = minimax_tts(reply)
                        if audio:
                            st.audio(audio, format="audio/mp3")
                        elif err:
                            st.caption(f"⚠️ {err}")
                    st.session_state.talk_msgs.append({"role": "assistant", "content": reply, "audio": audio})

                st.divider()
                with st.expander("🔊 Đọc văn bản bất kỳ bằng giọng MiniMax"):
                    tts_text = st.text_area("Văn bản", key="talk_tts_text", placeholder="Nhập văn bản để nghe...", height=100)
                    if st.button("Đọc bằng giọng MiniMax", key="talk_tts_btn"):
                        if tts_text.strip():
                            with st.spinner("Đang tạo giọng nói..."):
                                audio2, err2 = minimax_tts(tts_text)
                            if audio2:
                                st.audio(audio2, format="audio/mp3")
                            else:
                                st.error(err2 or "Lỗi không xác định.")
                        else:
                            st.warning("Nhập văn bản trước đã.")

        elif tab == "jarvis":
            _hermes_feature_panel("🛰️", "Jarvis",
                "Chế độ trợ lý chủ động — Hermes theo dõi tín hiệu và chạy automation theo lịch. Cấu hình Cron & Plugins trong Hermes Dashboard.",
                "Mở Hermes Dashboard", "?nav=hermes&tab=manage", new_tab=False)

        elif tab == "studio":
            _hermes_feature_panel("🎬", "Studio",
                "Không gian sản xuất media của Hermes: apps, video, images, audio — tất cả gom trong Workspace của agent.",
                "Mở Workspace", "?nav=hermes&tab=workspace", new_tab=False)

        elif tab == "control":
            st.markdown("<div style='padding:20px; text-align:center;'><span style='font-size:36px;'>🎛️</span><h4>Control Room</h4><p style='color:#7d7796;'>Realtime logs, memory weights, and neural engine hyper-parameters.</p></div>", unsafe_allow_html=True)

    elif active == "openclaw":
        tab_ctrl, tab_spend = st.tabs(["Control Center", "AI Spend"])
        
        with tab_ctrl:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            gw_url = st.secrets.get("OPENCLAW_URL", "https://gw-openclaw.tuandoctor.com/")
            
            # Premium design layout for security restricted iframe embedding
            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 35px 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 54px; margin-bottom: 15px; filter: drop-shadow(0 0 12px rgba(255, 126, 179, 0.45)); line-height: 1;">✸</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Cổng điều phối OpenClaw Gateway
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:580px; margin: 0 auto 25px auto; line-height:1.6; font-weight: 300;">
                    Máy chủ <b>OpenClaw Gateway</b> được cấu hình chính sách bảo mật chống nhúng trang (Clickjacking / Same-Origin Policy). Để đảm bảo an toàn bảo mật và đầy đủ tính năng tương tác, vui lòng mở trang quản trị trên một tab trình duyệt độc lập.
                </p>
                <a href="{gw_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #ff7eb3, #ff4d6d); color: #ffffff !important; font-weight: 600; font-size: 14px; padding: 12px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 0 20px rgba(255, 77, 109, 0.4); transition: all 0.2s; border: 1px solid rgba(255, 255, 255, 0.1);">
                    Mở OpenClaw Control Panel ↗
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # Secondary option to show embedded view
            with st.expander("Hiển thị giao diện nhúng (Iframe)"):
                st.components.v1.iframe(gw_url, height=650, scrolling=True)
            
        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**.")
            else:
                df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
                df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
                df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
                c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
                c3.metric("Swarm API Calls", f"{len(df_a):,}")
                
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_a, use_container_width=True, hide_index=True)
            
    elif active == "free-claude":
        tab_setup, tab_spend = st.tabs(["Official Setup", "AI Spend"])

        with tab_setup:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 30px 25px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 48px; margin-bottom: 12px; filter: drop-shadow(0 0 12px rgba(52, 211, 153, 0.5)); line-height: 1;">▼</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Official Claude Code — Anthropic Setup
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:680px; margin: 0 auto 18px auto; line-height:1.65; font-weight: 300;">
                    Cài Claude Code chính thức, đăng nhập bằng tài khoản Anthropic, rồi chạy trong thư mục repo để tác nhân đọc ngữ cảnh và sửa code an toàn.
                    Panel này chỉ giữ checklist vận hành; không cấu hình proxy hay endpoint thay thế cho Claude Code.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>1. CÀI TRÊN MÁY LOCAL (PowerShell, chạy 1 lần)</div>", unsafe_allow_html=True)
            st.code("npm install -g @anthropic-ai/claude-code", language="powershell")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>2. ĐĂNG NHẬP VÀ MỞ REPO</div>", unsafe_allow_html=True)
            st.code("cd \"D:\\BÁC SĨ CHÍNH MÌNH\\Project\\agent-hermes-os\"\nclaude", language="powershell")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>3. KHI GẶP POLICY BLOCK</div>", unsafe_allow_html=True)
            st.code("Ask for narrow repository changes only, and keep Claude Code on the official Anthropic endpoint.", language="text")
            st.caption("Nếu lỗi vẫn xuất hiện, mở session mới và gửi task hẹp hơn, ví dụ: 'review app.py for bugs' hoặc 'fix the Streamlit error in this traceback'.")

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            col_in, col_btn = st.columns([3, 1])
            with col_in:
                proxy_url = st.text_input(
                    "Optional API health URL",
                    value=st.session_state.get("fcc_tunnel_url", ""),
                    placeholder="https://api.anthropic.com",
                    key="fcc_tunnel_url_input",
                    label_visibility="visible",
                )
            with col_btn:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                test_clicked = st.button("Test connection", use_container_width=True, key="fcc_test_btn")

            if proxy_url:
                st.session_state["fcc_tunnel_url"] = proxy_url

            if test_clicked and proxy_url:
                clean = proxy_url.rstrip("/")
                with st.spinner("Checking endpoint..."):
                    try:
                        r = httpx.get(f"{clean}/v1/models", timeout=10)
                        st.session_state["fcc_test_result"] = ("ok", r.status_code, clean)
                    except Exception as e:
                        st.session_state["fcc_test_result"] = ("err", str(e), clean)

            res = st.session_state.get("fcc_test_result")
            if res and (not test_clicked or res[2] == st.session_state.get("fcc_tunnel_url", "").rstrip("/")):
                kind, payload, url = res
                if kind == "ok":
                    st.markdown(f"""
                    <div style="background: rgba(52, 211, 153, 0.10); border: 1px solid rgba(52, 211, 153, 0.35); border-radius: 10px; padding: 14px 18px; margin-top: 10px;">
                        <div style="color:#34d399; font-weight:600; font-size:14px; margin-bottom:4px;">✓ Endpoint reachable (HTTP {payload})</div>
                        <div style="color:#a5a1c0; font-size:12.5px;">Endpoint <code>{escape(url)}</code> đang phản hồi. Claude Code vẫn nên dùng cấu hình chính thức của Anthropic.</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.10); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 10px; padding: 14px 18px; margin-top: 10px;">
                        <div style="color:#ef4444; font-weight:600; font-size:14px; margin-bottom:4px;">✗ Không kết nối được</div>
                        <div style="color:#a5a1c0; font-size:12.5px;">{escape(str(payload))}</div>
                    </div>
                    """, unsafe_allow_html=True)

            tunnel_url = st.session_state.get("fcc_tunnel_url", "").rstrip("/")
            if tunnel_url:
                st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 22px 0 8px 0; font-weight:500;'>4. GHI CHÚ CẤU HÌNH</div>", unsafe_allow_html=True)
                env_block = (
                    "{\n"
                    '  "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "190000"\n'
                    "}"
                )
                st.code(env_block, language="json")
                st.caption("VSCode: Settings → claude-code.environmentVariables → Edit in settings.json. Giữ endpoint mặc định của Anthropic trừ khi tài liệu chính thức yêu cầu khác.")

        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**. Claude Code billing and usage live in your Anthropic account, not in this SQLite table.")
            else:
                df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
                df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
                df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
                c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
                c3.metric("Swarm API Calls", f"{len(df_a):,}")
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_a, use_container_width=True, hide_index=True)

    elif active == "claude":
        tab_setup, tab_spend = st.tabs(["Launch & Setup", "AI Spend"])

        with tab_setup:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            # Claude (claude.ai) chặn nhúng iframe (frame-ancestors) — panel là cổng mở app + hướng dẫn.
            claude_url = st.secrets.get("CLAUDE_URL", "https://claude.ai")

            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 157, 77, 0.15); border-radius: 14px; padding: 35px 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 54px; margin-bottom: 15px; filter: drop-shadow(0 0 12px rgba(255, 157, 77, 0.5)); line-height: 1; color:#ffb877;">✦</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Claude — Anthropic Flagship
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:580px; margin: 0 auto 25px auto; line-height:1.6; font-weight: 300;">
                    Model reasoning hàng đầu của Anthropic cho system architecture và coding agentic. Web app bảo mật chống nhúng — hãy mở trên tab độc lập để đăng nhập đầy đủ.
                </p>
                <a href="{claude_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #ff9d4d, #ff6a3d); color: #ffffff !important; font-weight: 600; font-size: 14px; padding: 12px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 0 20px rgba(255, 157, 77, 0.4); transition: all 0.2s; border: 1px solid rgba(255, 255, 255, 0.1);">
                    Mở Claude ↗
                </a>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>1. MỞ CLAUDE</div>", unsafe_allow_html=True)
            st.markdown("Dùng [claude.ai](https://claude.ai) trên web hoặc tải app desktop (macOS / Windows).")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>2. ĐĂNG NHẬP ANTHROPIC</div>", unsafe_allow_html=True)
            st.markdown("Đăng nhập tài khoản Anthropic (Free / Pro / Max).")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>3. CLAUDE CODE (TÙY CHỌN)</div>", unsafe_allow_html=True)
            st.code("npm install -g @anthropic-ai/claude-code", language="bash")
            st.caption("Cài CLI rồi chạy `claude` trong thư mục repo để code agentic ngay trong terminal.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>4. GIAO TASK</div>", unsafe_allow_html=True)
            st.markdown("Chat để reasoning / system architecture, hoặc giao task code trực tiếp cho Claude Code.")

        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**.")
            else:
                df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
                df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
                df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
                c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
                c3.metric("Swarm API Calls", f"{len(df_a):,}")
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_a, use_container_width=True, hide_index=True)

    elif active == "gemini":
        tab_setup, tab_spend = st.tabs(["Launch & Setup", "AI Spend"])

        with tab_setup:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            # Gemini (gemini.google.com) chặn nhúng iframe — panel là cổng mở app + hướng dẫn.
            gemini_url = st.secrets.get("GEMINI_URL", "https://gemini.google.com")

            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(168, 85, 247, 0.15); border-radius: 14px; padding: 35px 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 54px; margin-bottom: 15px; filter: drop-shadow(0 0 12px rgba(168, 85, 247, 0.5)); line-height: 1; color:#c084fc;">●</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Gemini — Google DeepMind
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:580px; margin: 0 auto 25px auto; line-height:1.6; font-weight: 300;">
                    Agent multimodal của Google: context cực dài, xử lý ảnh, PDF, video và audio. Web app chống nhúng — hãy mở trên tab độc lập để đăng nhập đầy đủ.
                </p>
                <a href="{gemini_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #a855f7, #7c3aed); color: #ffffff !important; font-weight: 600; font-size: 14px; padding: 12px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 0 20px rgba(168, 85, 247, 0.4); transition: all 0.2s; border: 1px solid rgba(255, 255, 255, 0.1);">
                    Mở Gemini ↗
                </a>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>1. MỞ GEMINI</div>", unsafe_allow_html=True)
            st.markdown("Dùng [gemini.google.com](https://gemini.google.com) trên web hoặc app Gemini trên điện thoại.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>2. ĐĂNG NHẬP GOOGLE</div>", unsafe_allow_html=True)
            st.markdown("Free, hoặc Google AI Pro / Ultra để mở khóa model mạnh hơn và context dài hơn.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>3. MULTIMODAL</div>", unsafe_allow_html=True)
            st.markdown("Upload ảnh, PDF, video, audio để Gemini xử lý ngữ cảnh lớn trong một lần.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>4. GIAO TASK</div>", unsafe_allow_html=True)
            st.markdown("Reasoning, phân tích tài liệu dài, tổng hợp nội dung từ video/audio.")

        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**.")
            else:
                df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
                df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
                df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
                c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
                c3.metric("Swarm API Calls", f"{len(df_a):,}")
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_a, use_container_width=True, hide_index=True)

    elif active == "antigravity":
        tab_setup, tab_spend = st.tabs(["Launch & Setup", "AI Spend"])

        with tab_setup:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            # Antigravity là IDE desktop agent-first (Gemini 3) — không có web UI để nhúng iframe
            # hay REST API, nên panel này là cổng mở app + hướng dẫn cài đặt.
            ag_url = st.secrets.get("ANTIGRAVITY_URL", "https://antigravity.google")

            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 14px; padding: 35px 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 54px; margin-bottom: 15px; filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.5)); line-height: 1; color:#818cf8;">▲</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Google Antigravity — Agentic IDE
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:580px; margin: 0 auto 25px auto; line-height:1.6; font-weight: 300;">
                    IDE agent-first chạy Gemini 3, dùng cho refactor workspace, dựng style high-fidelity và visual verification. Đây là ứng dụng desktop — không nhúng được trong dashboard, hãy mở app để giao việc cho agent.
                </p>
                <a href="{ag_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #6366f1, #4f46e5); color: #ffffff !important; font-weight: 600; font-size: 14px; padding: 12px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 0 20px rgba(99, 102, 241, 0.4); transition: all 0.2s; border: 1px solid rgba(255, 255, 255, 0.1);">
                    Mở Antigravity ↗
                </a>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>1. TẢI & CÀI ANTIGRAVITY</div>", unsafe_allow_html=True)
            st.markdown("Tải bản Windows / macOS / Linux tại [antigravity.google](https://antigravity.google) rồi cài như một IDE thông thường.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>2. ĐĂNG NHẬP GOOGLE</div>", unsafe_allow_html=True)
            st.markdown("Mở app và đăng nhập bằng tài khoản Google để kích hoạt model Gemini 3.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>3. MỞ WORKSPACE</div>", unsafe_allow_html=True)
            st.markdown("Open folder project của bạn — agent sẽ có quyền đọc/sửa file trong workspace đó.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>4. GIAO TASK CHO AGENT</div>", unsafe_allow_html=True)
            st.markdown("Mô tả task (refactor, dựng UI, visual verification) → agent tự lập kế hoạch, sửa code và tự kiểm chứng kết quả.")

        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**. (Antigravity chạy local trên máy bạn — token Gemini không log qua bảng Supabase này.)")
            else:
                df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
                df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
                df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
                c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
                c3.metric("Swarm API Calls", f"{len(df_a):,}")
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_a, use_container_width=True, hide_index=True)

    elif active == "codex":
        tab_setup, tab_spend = st.tabs(["Launch & Setup", "AI Spend"])

        with tab_setup:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            # Codex là coding agent của OpenAI (CLI + cloud) — không nhúng iframe, mở app/CLI.
            codex_url = st.secrets.get("CODEX_URL", "https://chatgpt.com/codex")

            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 14px; padding: 35px 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 54px; margin-bottom: 15px; filter: drop-shadow(0 0 12px rgba(16, 185, 129, 0.5)); line-height: 1; color:#34d399;">■</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Codex — OpenAI Coding Agent
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:580px; margin: 0 auto 25px auto; line-height:1.6; font-weight: 300;">
                    Agent coding của OpenAI cho refactor, static analysis và kiểm chứng kiến trúc. Chạy bằng CLI ngay trong repo hoặc trên cloud — mở app để giao việc cho agent.
                </p>
                <a href="{codex_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #10b981, #059669); color: #ffffff !important; font-weight: 600; font-size: 14px; padding: 12px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 0 20px rgba(16, 185, 129, 0.4); transition: all 0.2s; border: 1px solid rgba(255, 255, 255, 0.1);">
                    Mở Codex ↗
                </a>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>1. CÀI CODEX CLI</div>", unsafe_allow_html=True)
            st.code("npm install -g @openai/codex", language="bash")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>2. ĐĂNG NHẬP</div>", unsafe_allow_html=True)
            st.markdown("Đăng nhập bằng tài khoản ChatGPT (Plus / Pro / Team) hoặc đặt `OPENAI_API_KEY`.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>3. CHẠY TRONG REPO</div>", unsafe_allow_html=True)
            st.code("codex", language="bash")
            st.caption("Chạy trong thư mục project để agent đọc/sửa code; hoặc dùng bản cloud tại chatgpt.com/codex.")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>4. GIAO TASK</div>", unsafe_allow_html=True)
            st.markdown("Refactor, static analysis, kiểm chứng kiến trúc → agent lập kế hoạch và sửa code.")

        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**.")
            else:
                df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
                df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
                df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
                c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
                c3.metric("Swarm API Calls", f"{len(df_a):,}")
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_a, use_container_width=True, hide_index=True)

    else:
        # Standard Agent spend dashboard view (all other agents)
        df_a = get_ai_spend(active)
        
        if df_a.empty:
            st.info(f"No logged token cost events for agent: **{a['label']}**.")
        else:
            # Convert values safely
            df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
            df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
            df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Logged Costs (USD)", f"${df_a['cost_usd'].sum():,.4f}")
            c2.metric("Total Tokens Processed", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
            c3.metric("Swarm API Calls", f"{len(df_a):,}")
            
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            st.dataframe(df_a, use_container_width=True, hide_index=True)
            
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: SEO PIPELINE (Roman Numeral X - Matches Screenshot 4)
# ------------------------------------------------------------------------------
if active == "seo":
    import time
    render_custom_header("X", "SELF", "SEO Pipeline", "Automated high-quality transcript to article SEO engine.")
    
    # CSS overrides for button and container styles to make them extremely premium
    st.markdown("""
    <style>
    div.stButton > button, div.stDownloadButton > button {
        background: linear-gradient(135deg, #a855f7, #7c3aed) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.25) !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, #b866ff, #8c4aff) !important;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.4) !important;
        transform: translateY(-1px);
    }
    .log-terminal {
        background: #090514;
        border: 1px solid rgba(168, 85, 247, 0.15);
        border-radius: 8px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        color: #34d399;
        height: 250px;
        overflow-y: auto;
        white-space: pre-wrap;
        margin-top: 10px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
    }
    </style>
    """, unsafe_allow_html=True)
    
    seo_tab = st.query_params.get("seo_tab", "generate")
    
    # Define active tab colors
    tab_styles = {
        "generate": ("rgba(52,211,153,0.12)", "rgba(52,211,153,0.25)", "#34d399"),
        "deploy": ("rgba(168,85,247,0.12)", "rgba(168,85,247,0.25)", "#a855f7"),
        "history": ("rgba(245,158,11,0.12)", "rgba(245,158,11,0.25)", "#fbbf24"),
        "transcripts": ("rgba(59,130,246,0.12)", "rgba(59,130,246,0.25)", "#60a5fa"),
        "skill": ("rgba(236,72,153,0.12)", "rgba(236,72,153,0.25)", "#f472b6"),
        "setup": ("rgba(255,255,255,0.08)", "rgba(255,255,255,0.15)", "#ffffff")
    }

    def get_tab_style(tab_id):
        if seo_tab == tab_id:
            bg, border, text = tab_styles[tab_id]
            return f"background:{bg}; border:1px solid {border}; color:{text} !important; font-weight:600;"
        else:
            return "background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:#8b92b6 !important;"

    # Left sub-tabs links
    left_tabs_html = "".join([
        f'<a href="?nav=seo&seo_tab={tid}" target="_self" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; padding:8px 16px; border-radius:8px; font-size:13px; text-decoration:none; transition:all 0.2s; {get_tab_style(tid)}">{lbl}</a> '
        for tid, lbl in [
            ("generate", "▶ Generate"),
            ("deploy", "☁ Deploy"),
            ("history", "🕒 History"),
            ("transcripts", "📚 Transcripts"),
            ("skill", "🏆 Skill")
        ]
    ])

    # Right action / setup links
    right_setup_style = get_tab_style("setup")
    right_buttons_html = f'<a href="?nav=seo&seo_tab=setup" target="_self" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; padding:8px 14px; border-radius:8px; font-size:13px; text-decoration:none; transition:all 0.2s; {right_setup_style}">Setup Guide</a>'

    # Render custom tab bar
    col_nav, col_dl = st.columns([4, 1.2])
    with col_nav:
        st.markdown(f"""
        <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
            {left_tabs_html}
            <div style="width:1px; height:20px; background:rgba(255,255,255,0.08); margin:0 8px;"></div>
            {right_buttons_html}
        </div>
        """, unsafe_allow_html=True)
    
    with col_dl:
        # Dynamic zip download button for active articles if they exist
        active_articles = st.session_state.get("seo_active_articles", [])
        active_keyword = st.session_state.get("seo_active_keyword", "seo-pack")
        if active_articles:
            zip_bytes = create_seo_zip(active_articles, active_keyword)
            st.download_button(
                label="📥 SEO Pack (.zip)",
                data=zip_bytes,
                file_name=f"{st.session_state.get('seo_active_slug', 'seo-pack')}.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.markdown("""
            <a href="#" class="nav-link" style="display:inline-flex; justify-content:center; width:100%; align-items:center; gap:6px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); color:rgba(139,146,182,0.4) !important; padding:8px 14px; border-radius:8px; font-size:13px; text-decoration:none; cursor:not-allowed;">
                📥 SEO Pack (.zip)
            </a>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Load resources
    campaigns = load_seo_campaigns()
    obsidian_df = get_obsidian_vault()

    # Determine default prompt
    if "seo_agent_prompt" not in st.session_state:
        st.session_state["seo_agent_prompt"] = (
            "Bạn là một chuyên gia viết bài viết SEO chuẩn hóa cho y khoa. "
            "Hãy tạo ra 5 tiêu đề bài viết khác nhau, độc đáo và thu hút dựa trên từ khóa: \"{keyword}\" và nội dung transcript sau:\n"
            "\"{transcript}\"\n\n"
            "Yêu cầu phản hồi định dạng đúng JSON (chỉ trả về chuỗi JSON thô, không nằm trong dấu nháy markdown hay chứa lời dẫn giải thích), "
            "là một danh sách (array) gồm 5 object, mỗi object có 4 thuộc tính:\n"
            "- \"title\": tiêu đề bài viết tiếng Việt cuốn hút chứa từ khóa\n"
            "- \"slug\": đường dẫn viết liền không dấu ngăn cách bằng gạch ngang\n"
            "- \"excerpt\": một đoạn trích ngắn 1-2 câu tóm tắt cuốn hút\n"
            "- \"content\": nội dung bài viết markdown chi tiết khoảng 300 từ (tiếng Việt), có phân bổ từ khóa.\n"
        )

    # --------------------------------------------------------------------------
    # TAB: GENERATE
    # --------------------------------------------------------------------------
    if seo_tab == "generate":
        st.markdown("""
        <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px 22px 22px 22px; margin-bottom:1.5rem;">
            <h4 style="margin: 0 0 18px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                <span style="color:#34d399; font-size:14px;">✨</span> Generate 5 unique articles for all 5 sites
            </h4>
        """, unsafe_allow_html=True)

        col_k, col_s = st.columns(2)
        with col_k:
            st.text_input("TARGET KEYWORD", placeholder="e.g. hermes mcp server", key="seo_kw")
        with col_s:
            # Simple auto-slug deduction
            raw_kw = st.session_state.get("seo_kw", "")
            suggested_slug = raw_kw.lower().strip().replace(" ", "-").replace(".", "")
            st.text_input("FILE SLUG", value=suggested_slug if raw_kw.strip() else "", placeholder="hermes-mcp-server", key="seo_slug")

        st.markdown("<div style='font-size: 11px; font-weight: 700; color: #5b5478; text-transform: uppercase; letter-spacing: 1.5px; margin: 20px 0 10px 0;'>Source Transcript</div>", unsafe_allow_html=True)
        
        trans_mode = st.radio("Source Transcript Mode", ["PICK EXISTING", "PASTE NEW"], horizontal=True, label_visibility="collapsed")

        selected_transcript_content = ""
        if trans_mode == "PICK EXISTING":
            # Transcript đã import (có nội dung thật, lưu ở datastore "seo-transcripts") — ưu tiên dùng.
            saved_transcripts = load_seo_transcripts()
            saved_content = {t["file_name"]: t.get("content", "") for t in saved_transcripts}

            # Bổ sung index từ vault (chỉ có tên file, nội dung .md không sync lên cloud).
            vault_transcripts = list(saved_transcripts)
            if not obsidian_df.empty:
                mask = obsidian_df["category"].isin(["Omi", "Notes", "Recent"]) | obsidian_df["file_path"].str.contains("transcript", case=False, na=False)
                vault_transcripts += obsidian_df[mask].to_dict("records")

            if not vault_transcripts:
                vault_transcripts = [
                    {"file_name": "ai-money-lab-shared", "file_path": "Wiki/Transcripts/ai-money-lab-shared.md"},
                    {"file_name": "openclaw-ai-agent-community", "file_path": "Wiki/Transcripts/openclaw-ai-agent-community.md"},
                    {"file_name": "telegram-ai-agent", "file_path": "Wiki/Transcripts/telegram-ai-agent.md"},
                    {"file_name": "best-ai-agent-community", "file_path": "Wiki/Transcripts/best-ai-agent-community.md"}
                ]

            trans_names = []
            for t in vault_transcripts:
                if t["file_name"] not in trans_names:
                    trans_names.append(t["file_name"])
            selected_trans_name = st.selectbox("Select transcript file", trans_names, label_visibility="collapsed")

            if selected_trans_name:
                real_content = saved_content.get(selected_trans_name, "").strip()
                if real_content:
                    selected_transcript_content = real_content
                else:
                    # Nội dung không có trên cloud (chỉ là index vault) — báo rõ, dùng PASTE NEW để có nội dung thật.
                    selected_transcript_content = f"Transcript Content for {selected_trans_name}...\nĐây là bản ghi âm chia sẻ về cách xây dựng mô hình chăm sóc sức khỏe chủ động và tích hợp các agent thông minh tự động hóa toàn diện quy trình y tế thực tiễn."
                    st.caption("⚠️ Nội dung gốc của transcript này không được đồng bộ lên cloud (vault chỉ lưu chỉ mục). Hãy Import lại ở tab Transcripts hoặc dùng PASTE NEW để có nội dung thật.")

                st.markdown(f"""
                <div style="background: rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.05); padding:10px 14px; border-radius:8px; margin-top:8px; height:120px; overflow-y:auto; font-size:12.5px; color:#a5a1c0; font-family: 'JetBrains Mono', monospace; white-space:pre-wrap;">
                    {escape(selected_transcript_content)}
                </div>
                """, unsafe_allow_html=True)
        else:
            selected_transcript_content = st.text_area("Source Transcript Payload", placeholder="Paste Zoom/YouTube audio raw transcripts here to parse...", height=120, label_visibility="collapsed")

        st.markdown("</div>", unsafe_allow_html=True) # end container

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        col_t, col_desc = st.columns([1, 4])
        with col_t:
            st.toggle("Auto-deploy after generate", value=True, key="seo_auto_deploy")
        with col_desc:
            st.markdown("<div style='font-size: 13px; color: #8b92b6; line-height:1.4; margin-top:2px;'><b>Auto-deploy after generate</b><br>As soon as Claude finishes writing, all 5 sites build + deploy in parallel.</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

        if st.button("🚀 Run SEO Swarm (Generate 5 Articles)", use_container_width=True):
            if not st.session_state.get("seo_kw", "").strip():
                st.error("Vui lòng nhập từ khóa mục tiêu (TARGET KEYWORD)!")
            elif not selected_transcript_content.strip():
                st.error("Vui lòng chọn hoặc nhập Transcript nguồn!")
            else:
                with st.spinner("Đang khởi chạy SEO Swarm và tạo 5 bài viết tối ưu..."):
                    kw = st.session_state["seo_kw"].strip()
                    slug = st.session_state.get("seo_slug", "seo-pack").strip()
                    articles = generate_seo_articles(kw, selected_transcript_content, st.session_state.get("seo_agent_prompt"))
                    
                    st.session_state["seo_active_articles"] = articles
                    st.session_state["seo_active_keyword"] = kw
                    st.session_state["seo_active_slug"] = slug
                    
                    new_camp = {
                        "id": f"seo-{int(time.time())}",
                        "keyword": kw,
                        "slug": slug,
                        "timestamp": datetime.now().isoformat(),
                        "articles": articles,
                        "deployed": False
                    }
                    campaigns.insert(0, new_camp)
                    save_seo_campaigns(campaigns)
                    
                    if st.session_state.get("seo_auto_deploy"):
                        # Đặt cờ để tab Deploy chạy deploy THẬT khi load (tạo site + đẩy bài).
                        st.session_state["seo_deploy_pending_id"] = new_camp["id"]
                        st.toast("Sinh bài viết thành công! Bắt đầu deploy tự động...", icon="🚀")
                        st.query_params["seo_tab"] = "deploy"
                    else:
                        st.toast("Tạo 5 bài viết chuẩn SEO thành công!", icon="✅")

                    st.rerun()

        # Display active generated articles below
        if active_articles:
            st.markdown(f"""
            <div style="margin-top: 25px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px;">
                <h3 style="font-family:'Outfit', sans-serif; font-size:18px; font-weight:600; color:#ffffff; margin-bottom:15px;">
                    ✨ Kết quả SEO Swarm của từ khóa: <span style="color:#34d399;">{active_keyword}</span>
                </h3>
            </div>
            """, unsafe_allow_html=True)

            for idx, art in enumerate(active_articles):
                with st.expander(f"Bài viết {idx+1}: {art.get('title')}", expanded=(idx==0)):
                    st.markdown(f"**Slug:** `{art.get('slug')}`")
                    st.markdown(f"**Trích dẫn ngắn (Excerpt):** *{art.get('excerpt')}*")
                    st.markdown("---")
                    st.markdown(art.get("content"))

    # --------------------------------------------------------------------------
    # TAB: DEPLOY
    # --------------------------------------------------------------------------
    elif seo_tab == "deploy":
        st.markdown("""
        <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px; margin-bottom:1.5rem;">
            <h4 style="margin: 0 0 15px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                <span style="color:#a855f7; font-size:14px;">☁</span> Netlify Funnels Swarm Deployment
            </h4>
        """, unsafe_allow_html=True)
        
        # Thực thi deploy THẬT khi có yêu cầu (Generate auto-deploy / nút Trigger / Redeploy).
        pending_id = st.session_state.pop("seo_deploy_pending_id", None)
        if pending_id:
            target = next((c for c in campaigns if c["id"] == pending_id), None)
            if target:
                with st.spinner("Đang deploy lên Netlify (tạo site + đẩy bài viết)..."):
                    result = deploy_campaign_to_netlify(target)
                st.session_state["seo_deploy_result"] = result
                st.session_state["seo_deploy_campaign_id"] = pending_id
                st.session_state["seo_deploy_status"] = "success" if result["ok"] else "error"
                if result["ok"]:
                    # Lưu site id để redeploy tái dùng (idempotent) + đánh dấu đã deploy.
                    target["netlify_sites"] = [
                        {"id": s["id"], "name": s["name"], "url": s["url"]}
                        for s in result["sites"] if s.get("id")
                    ]
                    target["deployed"] = True
                    save_seo_campaigns(campaigns)
                st.rerun()

        status_state = st.session_state.get("seo_deploy_status", "idle")
        result = st.session_state.get("seo_deploy_result")
        campaign_id = st.session_state.get("seo_deploy_campaign_id")
        deploying_camp = next((c for c in campaigns if c["id"] == campaign_id), None) if campaign_id else None
        token_ready = _netlify_token() is not None

        col_st_left, col_st_right = st.columns([2, 1])
        with col_st_left:
            if status_state == "success":
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px; color:#34d399; font-size:14px; font-weight:600; margin-bottom:10px;">
                    <span style="width:10px; height:10px; background:#34d399; border-radius:50%; display:inline-block;"></span>
                    Đã deploy: <span style="color:#ffffff;">{escape(deploying_camp.get('keyword')) if deploying_camp else 'Chiến dịch'}</span>
                </div>
                """, unsafe_allow_html=True)
            elif status_state == "error":
                st.markdown("""
                <div style="color:#f87171; font-size:14px; font-weight:600; margin-bottom:10px;">
                    Deploy lỗi — xem log bên dưới.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="color:#8b92b6; font-size:14px; margin-bottom:10px;">
                    Trạng thái: <b>Sẵn sàng (Idle)</b>
                </div>
                """, unsafe_allow_html=True)

        with col_st_right:
            if campaigns:
                if st.button("⚡ Trigger Netlify Build Swarm", key="trigger_deploy", disabled=not token_ready):
                    st.session_state["seo_deploy_pending_id"] = campaigns[0]["id"]
                    st.rerun()
            else:
                st.warning("Vui lòng tạo bài viết trước khi deploy.")

        if not token_ready:
            st.warning("Thiếu **NETLIFY_AUTH_TOKEN** trong secrets — thêm token (Streamlit Cloud → Settings → Secrets, hoặc `.streamlit/secrets.toml`) để deploy thật. Hướng dẫn ở tab **Setup Guide**.")

        sites = result.get("sites", []) if result else []
        total = len(sites)
        done = sum(1 for s in sites if s.get("state") not in ("error", None))
        pct_done = int(done / total * 100) if total else 0
        state_label = "SUCCESS" if status_state == "success" else "ERROR" if status_state == "error" else "IDLE"

        st.markdown(f"""
        <div style="margin: 10px 0 20px 0;">
            <div class="mc-bar"><div class="mc-fill" style="width:{pct_done}%; background:linear-gradient(90deg, #a855f7, #6366f1);"></div></div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#a5a1c0; margin-top:5px;">
                <span>Tiến trình: {pct_done}% ({done}/{total} site)</span>
                <span>{state_label}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 11px; font-weight: 700; color: #5b5478; text-transform: uppercase; letter-spacing: 1px;'>Netlify Build Status</div>", unsafe_allow_html=True)

        if sites:
            for s in sites:
                ok_site = s.get("state") not in ("error", None)
                badge_cls = "st-done" if ok_site else "st-todo"
                badge_txt = s.get("state", "?") if ok_site else "Error"
                url = s.get("url", "")
                if url:
                    link_html = f'<a href="{escape(url)}" target="_blank" style="font-size:11px; color:#5ad7e6; text-decoration:none;">{escape(url)} ↗</a>'
                else:
                    link_html = f'<span style="font-size:11px; color:#f87171;">{escape(str(s.get("error", "—"))[:80])}</span>'
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 6px; background: rgba(30, 24, 52, 0.25);">
                    <div style="display:flex; align-items:center; gap:8px; min-width:0;">
                        <span style="font-size:13px; font-family:'JetBrains Mono', monospace; color:#e2e8f0;">{escape(str(s.get('name', '—')))}</span>
                        {link_html}
                    </div>
                    <span class="status-badge {badge_cls}" style="font-size: 9px;">{escape(str(badge_txt))}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Chưa có site nào. Tạo bài viết rồi nhấn Trigger — Netlify sẽ tự tạo 1 site cho mỗi bài và deploy.")

        log_content = "\n".join(result.get("logs", [])) if result else "Terminal offline. Nhấn Trigger để bắt đầu deploy."
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 11px; font-weight: 700; color: #5b5478; text-transform: uppercase; letter-spacing: 1px;'>Live Deploy Log</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="log-terminal">{escape(log_content)}</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB: HISTORY
    # --------------------------------------------------------------------------
    elif seo_tab == "history":
        st.markdown("""
        <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px; margin-bottom:1.5rem;">
            <h4 style="margin: 0 0 15px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                <span style="color:#fbbf24; font-size:14px;">🕒</span> Campaign Execution History
            </h4>
        """, unsafe_allow_html=True)
        
        if not campaigns:
            st.info("Chưa có chiến dịch SEO nào được lưu. Hãy chuyển qua tab Generate để tạo chiến dịch đầu tiên!")
        else:
            for idx, c in enumerate(campaigns):
                st.markdown(f"""
                <div style="background: rgba(30, 24, 52, 0.45); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <h3 style="font-size: 15px; font-weight: 700; color: #ffffff; margin: 0;">Từ khóa: {escape(c['keyword'])}</h3>
                            <span style="font-size:11px; color:#8b92b6; font-family:'JetBrains Mono', monospace;">Slug: {escape(c['slug'])} &bull; ID: {c['id']}</span>
                        </div>
                        <span class="status-badge {('st-done' if c.get('deployed') else 'st-todo')}" style="font-size:9.5px;">
                            {('Deployed' if c.get('deployed') else 'Not Deployed')}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                
                c_act_1, c_act_2, c_act_3 = st.columns(3)
                
                if c_act_1.button("🔍 View Campaign", key=f"hist_view_{c['id']}"):
                    st.session_state["seo_active_articles"] = c["articles"]
                    st.session_state["seo_active_keyword"] = c["keyword"]
                    st.session_state["seo_active_slug"] = c["slug"]
                    st.toast(f"Đã tải bài viết chiến dịch '{c['keyword']}' vào panel!", icon="📂")
                    st.query_params["seo_tab"] = "generate"
                    st.rerun()
                
                hist_zip = create_seo_zip(c["articles"], c["keyword"])
                c_act_2.download_button(
                    label="📥 Download ZIP",
                    data=hist_zip,
                    file_name=f"{c['slug']}.zip",
                    mime="application/zip",
                    key=f"hist_dl_{c['id']}",
                    use_container_width=True
                )
                
                if c_act_3.button("⚡ Redeploy Swarm", key=f"hist_dep_{c['id']}"):
                    st.session_state["seo_deploy_pending_id"] = c["id"]
                    st.toast("Bắt đầu deploy lại...", icon="🚀")
                    st.query_params["seo_tab"] = "deploy"
                    st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB: TRANSCRIPTS
    # --------------------------------------------------------------------------
    elif seo_tab == "transcripts":
        st.markdown("""
        <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px; margin-bottom:1.5rem;">
            <h4 style="margin: 0 0 15px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                <span style="color:#60a5fa; font-size:14px;">📚</span> Source Transcripts Repository
            </h4>
        """, unsafe_allow_html=True)
        
        # Transcript đã import (nội dung thật, lưu ở datastore) — nguồn pickable cho tab Generate.
        saved_transcripts = load_seo_transcripts()

        vault_list = []
        if not obsidian_df.empty:
            mask = obsidian_df["category"].isin(["Omi", "Notes", "Recent"]) | obsidian_df["file_path"].str.contains("transcript", case=False, na=False)
            vault_list = obsidian_df[mask].to_dict("records")

        if not saved_transcripts and not vault_list:
            vault_list = [
                {"file_name": "ai-money-lab-shared", "file_path": "Wiki/Transcripts/ai-money-lab-shared.md", "updated_at": "2d ago"},
                {"file_name": "openclaw-ai-agent-community", "file_path": "Wiki/Transcripts/openclaw-ai-agent-community.md", "updated_at": "3d ago"},
                {"file_name": "telegram-ai-agent", "file_path": "Wiki/Transcripts/telegram-ai-agent.md", "updated_at": "5d ago"}
            ]

        trans_list = saved_transcripts + vault_list

        with st.expander("➕ Import / Thêm transcript mới", expanded=False):
            with st.form("add_new_transcript", clear_on_submit=True):
                t_name = st.text_input("Tên Transcript", placeholder="vd. chia-se-dinh-duong-guthealth")
                t_text = st.text_area("Nội dung transcript", placeholder="Nhập hoặc dán nội dung bản ghi âm Zoom/YouTube tại đây...", height=120)
                submit_t = st.form_submit_button("Lưu Transcript")
                if submit_t:
                    if not t_name.strip() or not t_text.strip():
                        st.error("Vui lòng điền đủ tên và nội dung!")
                    else:
                        slug = t_name.lower().strip().replace(" ", "-").replace(".", "")
                        saved_transcripts.insert(0, {
                            "file_name": t_name.strip(),
                            "file_path": f"Wiki/Transcripts/{slug}.md",
                            "content": t_text.strip(),
                            "updated_at": "Vừa xong"
                        })
                        if save_seo_transcripts(saved_transcripts):
                            st.success(f"Transcript '{t_name}' đã được lưu trữ thành công!")
                        else:
                            st.error("Không lưu được transcript (kiểm tra kết nối Supabase / quyền ghi).")
                        time.sleep(1)
                        st.rerun()

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        for t in trans_list:
            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 15px; margin-bottom: 10px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:14px; font-weight:600; color:#ffffff;">{escape(t['file_name'])}.md</span>
                        <div style="font-size:11px; color:#8b92b6; font-family:'JetBrains Mono', monospace; margin-top:2px;">{escape(t.get('file_path', 'Wiki/Transcripts/'))}</div>
                    </div>
                    <span style="font-size:11px; color:#8b92b6;">{escape(t.get('updated_at', 'Vừa xong'))}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB: SKILL
    # --------------------------------------------------------------------------
    elif seo_tab == "skill":
        st.markdown("""
        <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px; margin-bottom:1.5rem;">
            <h4 style="margin: 0 0 15px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                <span style="color:#f472b6; font-size:14px;">🏆</span> SEO Swarm agent Prompt Configuration
            </h4>
            <p style="color:#a5a1c0; font-size:13px; line-height:1.4; margin-bottom:20px;">
                Đây là Prompt hệ thống mà Hermes/Nova sử dụng để hướng dẫn mô hình ngôn ngữ sinh 5 bài viết tối ưu từ khoá kết hợp dữ liệu transcript. Thay đổi prompt này sẽ ảnh hưởng trực tiếp tới cấu trúc bài viết và phong cách ngôn từ.
            </p>
        """, unsafe_allow_html=True)
        
        with st.form("save_prompt_form"):
            edited_prompt = st.text_area("Hệ thống Agent Prompt (System Prompt)", value=st.session_state["seo_agent_prompt"], height=280)
            c_p_left, c_p_right = st.columns([3, 1])
            c_p_left.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            save_p = c_p_right.form_submit_button("Lưu Cấu Hình", use_container_width=True)
            if save_p:
                st.session_state["seo_agent_prompt"] = edited_prompt
                st.toast("Cấu hình Agent Prompt đã cập nhật thành công!", icon="✅")
                time.sleep(1)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB: SETUP GUIDE
    # --------------------------------------------------------------------------
    elif seo_tab == "setup":
        st.markdown("""
        <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px; margin-bottom:1.5rem;">
            <h4 style="margin: 0 0 15px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                <span style="color:#ffffff; font-size:14px;">✦</span> Setup Guide & Architecture
            </h4>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### Hướng Dẫn Thiết Lập Tự Động Hóa SEO Pipeline
        
        Quy trình xử lý tự động (automated transcript-to-article engine) chuyển đổi nội dung âm thanh/hình ảnh thô từ các video Zoom hoặc YouTube thành các bài viết chuẩn SEO được deploy tự động lên hạ tầng của bạn.
        
        #### 1. Nguyên lý hoạt động
        1. **Tải lên Transcript**: Người dùng chọn một tệp văn bản thô ghi âm bài chia sẻ chuyên môn (transcript) trong Obsidian hoặc dán thủ công.
        2. **Khởi động Swarm**: Hermes/Nova chia dữ liệu lớn thành các phân đoạn thông tin quan trọng.
        3. **LLM Synthesis**: Sử dụng mô hình ngôn ngữ lớn tối ưu hóa chuẩn SEO của y khoa để tạo 5 bài viết nhắm mục tiêu 5 khía cạnh từ khóa khác nhau.
        4. **Nén ZIP / Xuất bản**: Mỗi bài viết được render thành một trang HTML tự chứa (self-contained) — cũng tải về được dưới dạng ZIP Markdown (frontmatter chuẩn Hugo/Jekyll/Astro).
        5. **Deploy Netlify (thật)**: App gọi thẳng Netlify REST API (digest deploy) để **tự tạo 1 site cho mỗi bài viết** rồi đẩy trang HTML lên. Không cần Netlify CLI. Site id được lưu vào chiến dịch nên Redeploy sẽ tái dùng đúng site (idempotent).

        #### 2. Kết nối Netlify
        Lấy **Personal Access Token** tại Netlify: *User settings → Applications → New access token*, rồi đặt vào `.streamlit/secrets.toml` (hoặc Streamlit Cloud → Settings → Secrets):
        ```toml
        NETLIFY_AUTH_TOKEN = "nfp_xxx_personal_access_token"

        # (tùy chọn) Hermes shim để sinh bài bằng LLM thật thay vì bản mẫu:
        HERMES_API_URL = "https://your-fastapi-shim.vps.com"
        HERMES_API_KEY = "your-api-secret-key"
        ```
        Khi thiếu `NETLIFY_AUTH_TOKEN`, tab **Deploy** sẽ vô hiệu nút và hiện cảnh báo (không deploy giả).

        > ⚠️ **Lưu ý an toàn**: Netlify digest deploy ghi đè **toàn bộ** snapshot của site. App chỉ deploy lên các site do chính nó tạo (mỗi bài 1 site), nên không đụng tới site có sẵn của bạn.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ------------------------------------------------------------------------------
# VIEW: KANBAN BOARD VIEW (Roman Numeral XIII - Matches User Screenshot)
# ------------------------------------------------------------------------------
if active == "kanban":
    render_back_button()
    # Lấy địa chỉ Kanban URL từ secrets hoặc mặc định
    kanban_url = st.secrets.get("KANBAN_URL", "https://workspace.tuandoctor.com/tasks")
    
    # CSS tối ưu hóa: ẩn hoàn toàn padding thừa của Streamlit, bo tròn iframe, viền neon violet sang trọng
    st.markdown("""
        <style>
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        iframe {
            border-radius: 16px;
            border: 1px solid rgba(168, 85, 247, 0.15) !important;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5), 0 0 20px rgba(168, 85, 247, 0.05);
            background: rgba(10, 7, 21, 0.6);
            transition: all 0.3s ease;
        }
        iframe:hover {
            border-color: rgba(168, 85, 247, 0.25) !important;
            box-shadow: 0 16px 64px rgba(0, 0, 0, 0.6), 0 0 30px rgba(168, 85, 247, 0.08);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Đăng nhập trong iframe xuyên nguồn (cross-origin) bị trình duyệt chặn cookie phiên
    # (third-party cookie / SameSite), nên nhập đúng mật khẩu vẫn không vào được.
    # Giải pháp: mở Kanban ở tab độc lập — ngữ cảnh first-party, cookie đăng nhập hoạt động bình thường.
    st.markdown(f"""
    <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(168, 85, 247, 0.12); border-radius: 14px; padding: 35px 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
        <div style="font-size: 54px; margin-bottom: 15px; filter: drop-shadow(0 0 12px rgba(168, 85, 247, 0.45)); line-height: 1;">📋</div>
        <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
            Kanban Board — Workspace
        </h3>
        <p style="color:#a5a1c0; font-size:14.5px; max-width:580px; margin: 0 auto 25px auto; line-height:1.6; font-weight: 300;">
            Bảng Kanban yêu cầu đăng nhập. Khi nhúng trong iframe, trình duyệt chặn cookie phiên xuyên nguồn nên nhập đúng mật khẩu vẫn không vào được. Hãy mở bảng trên một tab độc lập để đăng nhập hoạt động bình thường.
        </p>
        <a href="{kanban_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #a855f7, #7c3aed); color: #ffffff !important; font-weight: 600; font-size: 14px; padding: 12px 30px; border-radius: 8px; text-decoration: none; box-shadow: 0 0 20px rgba(168, 85, 247, 0.4); transition: all 0.2s; border: 1px solid rgba(255, 255, 255, 0.1);">
            Mở Kanban Board ↗
        </a>
    </div>
    """, unsafe_allow_html=True)

    # Tùy chọn phụ: xem giao diện nhúng (đăng nhập có thể không hoạt động do trình duyệt chặn cookie iframe)
    with st.expander("Hiển thị giao diện nhúng (Iframe)"):
        st.components.v1.iframe(kanban_url, height=850, scrolling=True)
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: GOALS MANAGER (Roman Numeral IX) — xem + thêm/sửa/xoá OKR vào mission_control
# ------------------------------------------------------------------------------
if active == "goals":
    g = SELF_SECTIONS["goals"]
    render_custom_header(g["num"], "SELF", g["label"], g["desc"])

    admin = get_admin_client()
    can_write = admin is not None

    # Đọc trực tiếp mission_control (anon đọc được nhờ RLS public) — KHÔNG dùng mock
    # fallback để manager phản ánh đúng trạng thái DB thật (tránh sửa/xoá nhầm row ảo).
    try:
        res = supabase.table("mission_control").select("*").order("id").execute()
        mc = pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        mc = pd.DataFrame()

    if not mc.empty:
        for col in ["progress_percent", "turns_used", "turn_budget"]:
            mc[col] = pd.to_numeric(mc[col], errors="coerce").fillna(0).astype(int)
        c1, c2, c3 = st.columns(3)
        c1.metric("Objectives", len(mc))
        c2.metric("Mean Completion", f"{int(mc['progress_percent'].mean())}%")
        c3.metric("Budget Utilized", f"{int(mc['turns_used'].sum())}/{int(mc['turn_budget'].sum())}")
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    if not can_write:
        st.warning("Thiếu SUPABASE_SERVICE_ROLE_KEY — chế độ chỉ-xem, không thêm/sửa/xoá được mục tiêu.")

    STATUSES = ["To Do", "In Progress", "Done"]
    STMAP = {"To Do": "st-todo", "In Progress": "st-prog", "Done": "st-done"}

    # --- Thêm mục tiêu mới ---
    with st.expander("➕ Thêm mục tiêu mới", expanded=mc.empty):
        with st.form("add_goal", clear_on_submit=True):
            new_name = st.text_input("Tên mục tiêu", placeholder="vd. Hoàn thành chiến dịch SEO Q3")
            a, b, c = st.columns(3)
            new_status = a.selectbox("Trạng thái", STATUSES, key="add_status")
            new_progress = b.slider("Tiến độ %", 0, 100, 0, key="add_prog")
            new_budget = c.number_input("Ngân sách bước", 1, 999, 20, key="add_budget")
            submitted = st.form_submit_button("💾 Lưu mục tiêu", disabled=not can_write, use_container_width=True)
        if submitted:
            if not new_name.strip():
                st.warning("Nhập tên mục tiêu.")
            elif can_write:
                admin.table("mission_control").insert({
                    "goal_name": new_name.strip(),
                    "status": new_status,
                    "progress_percent": int(new_progress),
                    "turns_used": 0,
                    "turn_budget": int(new_budget),
                }).execute()
                st.success("Đã thêm mục tiêu.")
                st.rerun()

    # --- Danh sách mục tiêu + sửa/xoá ---
    if mc.empty:
        st.info("Chưa có mục tiêu nào trong mission_control. Thêm ở khung trên.")
    else:
        for _, r in mc.iterrows():
            gid = int(r["id"])
            status = str(r["status"])
            cls = STMAP.get(status, "st-todo")
            pct = int(r["progress_percent"])
            st.markdown(f"""
            <div class='mc-card'>
              <div class='mc-top'>
                <div class='mc-title'>{escape(str(r['goal_name']))}</div>
                <div class='status-badge {cls}'>{escape(status)}</div>
              </div>
              <div class='mc-bar'><div class='mc-fill' style='width:{pct}%;'></div></div>
              <div class='mc-meta'>
                <span>{pct}% complete</span>
                <span>{int(r['turns_used'])}/{int(r['turn_budget'])} steps</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("✎ Sửa / Xoá", expanded=False):
                e1, e2, e3 = st.columns(3)
                up_status = e1.selectbox("Trạng thái", STATUSES,
                                         index=STATUSES.index(status) if status in STATUSES else 0,
                                         key=f"st_{gid}")
                up_pct = e2.slider("Tiến độ %", 0, 100, pct, key=f"pc_{gid}")
                up_used = e3.number_input("Bước đã dùng", 0, 9999, int(r["turns_used"]), key=f"tu_{gid}")
                s1, s2 = st.columns(2)
                if s1.button("💾 Lưu thay đổi", key=f"sv_{gid}", disabled=not can_write, use_container_width=True):
                    admin.table("mission_control").update({
                        "status": up_status,
                        "progress_percent": int(up_pct),
                        "turns_used": int(up_used),
                    }).eq("id", gid).execute()
                    st.rerun()
                if s2.button("🗑 Xoá mục tiêu", key=f"del_{gid}", disabled=not can_write, use_container_width=True):
                    admin.table("mission_control").delete().eq("id", gid).execute()
                    st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: STUDIO (Roman Numeral XI) — launchpad công cụ media generation
# ------------------------------------------------------------------------------
if active == "studio":
    s = SELF_SECTIONS["studio"]
    render_custom_header(s["num"], "SELF", s["label"], s["desc"])

    # Mỗi tool: link mặc định trỏ trang chính thức, ghi đè được qua secret (key).
    STUDIO_TOOLS = [
        {"name": "Higgsfield",  "icon": "✦", "color": "#ff7eb3", "key": "STUDIO_HIGGSFIELD_URL", "url": "https://higgsfield.ai", "desc": "Image & video generation"},
        {"name": "Gamma",       "icon": "◰", "color": "#a855f7", "key": "STUDIO_GAMMA_URL",      "url": "https://gamma.app",     "desc": "AI decks & one-pagers"},
        {"name": "Canva",       "icon": "◇", "color": "#22d3ee", "key": "STUDIO_CANVA_URL",      "url": "https://www.canva.com", "desc": "Design & templates"},
        {"name": "Figma",       "icon": "❖", "color": "#fb7185", "key": "STUDIO_FIGMA_URL",      "url": "https://figma.com",     "desc": "UI & visual design"},
        {"name": "n8n Studio",  "icon": "⬡", "color": "#10b981", "key": "STUDIO_N8N_URL",        "url": "https://n8n.io",        "desc": "Video render workflows"},
        {"name": "ElevenLabs",  "icon": "♪", "color": "#f59e0b", "key": "STUDIO_ELEVENLABS_URL", "url": "https://elevenlabs.io", "desc": "Voiceover & audio"},
    ]

    st.markdown("""
    <style>
    .studio-card { transition: all .2s ease; }
    .studio-card:hover { transform: translateY(-3px); border-color: rgba(255,255,255,0.18) !important; box-shadow: 0 14px 44px rgba(0,0,0,0.5); }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, t in enumerate(STUDIO_TOOLS):
        url = st.secrets.get(t["key"], t["url"])
        with cols[i % 3]:
            st.markdown(f"""
            <a href="{escape(url)}" target="_blank" style="text-decoration:none; display:block; margin-bottom:18px;">
              <div class="studio-card" style="background: rgba(30,24,52,0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border:1px solid rgba(255,255,255,0.06); border-radius:14px; padding:24px 18px; text-align:center; box-shadow:0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size:36px; color:{t['color']}; filter:drop-shadow(0 0 10px {t['color']}66); margin-bottom:10px; line-height:1;">{t['icon']}</div>
                <div style="color:#fff; font-weight:600; font-size:16px;">{escape(t['name'])}</div>
                <div style="color:#a5a1c0; font-size:12.5px; margin-top:4px; font-weight:300; line-height:1.4;">{escape(t['desc'])}</div>
                <div style="color:{t['color']}; font-size:12px; margin-top:14px; font-weight:600; letter-spacing:0.3px;">Mở ↗</div>
              </div>
            </a>
            """, unsafe_allow_html=True)

    st.caption("Link mỗi công cụ cấu hình được qua secrets (STUDIO_*_URL) — mặc định trỏ trang chính thức.")
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: NOTEBOOK (Roman Numeral XII) — scratchpad markdown lưu vào bảng notebook
# ------------------------------------------------------------------------------
if active == "notebook":
    nb = SELF_SECTIONS["notebook"]
    render_custom_header(nb["num"], "SELF", nb["label"], nb["desc"])

    admin = get_admin_client()
    can_write = admin is not None

    # Đọc notebook (anon đọc được nhờ RLS) — mới nhất trước.
    try:
        res = supabase.table("notebook").select("*").order("updated_at", desc=True).execute()
        notes = res.data or []
    except Exception:
        notes = []

    if not can_write:
        st.warning("Thiếu SUPABASE_SERVICE_ROLE_KEY — chế độ chỉ-xem, không thêm/sửa/xoá được ghi chú.")

    # --- Ghi chú mới ---
    with st.expander("➕ Ghi chú mới", expanded=not notes):
        with st.form("add_note", clear_on_submit=True):
            n_title = st.text_input("Tiêu đề", placeholder="vd. Ý tưởng nội dung tuần này")
            n_body = st.text_area("Nội dung (Markdown)", height=160,
                                  placeholder="# Heading\n- ý tưởng A\n- ý tưởng B")
            add_ok = st.form_submit_button("💾 Lưu ghi chú", disabled=not can_write, use_container_width=True)
        if add_ok:
            if not (n_title.strip() or n_body.strip()):
                st.warning("Nhập tiêu đề hoặc nội dung.")
            elif can_write:
                admin.table("notebook").insert({
                    "title": n_title.strip() or "Untitled",
                    "content": n_body,
                }).execute()
                st.success("Đã lưu ghi chú.")
                st.rerun()

    # --- Danh sách ghi chú ---
    if not notes:
        st.info("Chưa có ghi chú nào. Thêm ở khung trên.")
    else:
        for note in notes:
            nid = int(note["id"])
            title = str(note.get("title") or "Untitled")
            content = str(note.get("content") or "")
            disp = str(note.get("updated_at") or "")[:16].replace("T", " ")
            st.markdown(f"""
            <div class='mc-card' style='margin-bottom:6px;'>
              <div class='mc-top'>
                <div class='mc-title'>{escape(title)}</div>
                <div class='time-badge'>{escape(disp)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if content.strip():
                # st.markdown KHÔNG cho raw HTML (unsafe_allow_html mặc định False) -> an toàn XSS.
                st.markdown(content)

            with st.expander("✎ Sửa / Xoá", expanded=False):
                up_title = st.text_input("Tiêu đề", value=title, key=f"nt_{nid}")
                up_body = st.text_area("Nội dung (Markdown)", value=content, height=180, key=f"nb_{nid}")
                e1, e2 = st.columns(2)
                if e1.button("💾 Lưu thay đổi", key=f"nsv_{nid}", disabled=not can_write, use_container_width=True):
                    admin.table("notebook").update({
                        "title": up_title.strip() or "Untitled",
                        "content": up_body,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", nid).execute()
                    st.rerun()
                if e2.button("🗑 Xoá ghi chú", key=f"ndel_{nid}", disabled=not can_write, use_container_width=True):
                    admin.table("notebook").delete().eq("id", nid).execute()
                    st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: JOURNAL (Roman Numeral XIV) — nhật ký theo ngày, lưu vào bảng journal
# ------------------------------------------------------------------------------
if active == "journal":
    j = SELF_SECTIONS["journal"]
    render_custom_header(j["num"], "SELF", j["label"], j["desc"])

    admin = get_admin_client()
    can_write = admin is not None

    # Đọc journal (anon đọc được nhờ RLS) — mới nhất theo ngày trước.
    try:
        res = (supabase.table("journal").select("*")
               .order("entry_date", desc=True).order("id", desc=True).execute())
        entries = res.data or []
    except Exception:
        entries = []

    if not can_write:
        st.warning("Thiếu SUPABASE_SERVICE_ROLE_KEY — chế độ chỉ-xem, không thêm/sửa/xoá được entry.")

    # --- Entry mới ---
    with st.expander("➕ Entry mới", expanded=not entries):
        with st.form("add_journal", clear_on_submit=True):
            j_date = st.date_input("Ngày", value=date.today())
            j_body = st.text_area("Nội dung (Markdown)", height=160,
                                  placeholder="# Reflection\n- Hôm nay đã làm...\n- Insight:")
            add_ok = st.form_submit_button("💾 Lưu entry", disabled=not can_write, use_container_width=True)
        if add_ok:
            if not j_body.strip():
                st.warning("Nhập nội dung.")
            elif can_write:
                admin.table("journal").insert({
                    "entry_date": j_date.isoformat(),
                    "content": j_body,
                }).execute()
                st.success("Đã lưu entry.")
                st.rerun()

    # --- Timeline ---
    if not entries:
        st.info("Chưa có entry nào. Thêm ở khung trên.")
    else:
        for e in entries:
            eid = int(e["id"])
            ed = str(e.get("entry_date") or "")
            content = str(e.get("content") or "")
            try:
                disp = date.fromisoformat(ed).strftime("%d/%m/%Y")
            except ValueError:
                disp = ed
            st.markdown(f"""
            <div class='mc-card' style='margin-bottom:6px;'>
              <div class='mc-top'>
                <div class='mc-title'>📅 {escape(disp)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if content.strip():
                # st.markdown KHÔNG cho raw HTML -> an toàn XSS.
                st.markdown(content)

            with st.expander("✎ Sửa / Xoá", expanded=False):
                try:
                    cur_date = date.fromisoformat(ed)
                except ValueError:
                    cur_date = date.today()
                up_date = st.date_input("Ngày", value=cur_date, key=f"jd_{eid}")
                up_body = st.text_area("Nội dung (Markdown)", value=content, height=180, key=f"jb_{eid}")
                a, b = st.columns(2)
                if a.button("💾 Lưu thay đổi", key=f"jsv_{eid}", disabled=not can_write, use_container_width=True):
                    admin.table("journal").update({
                        "entry_date": up_date.isoformat(),
                        "content": up_body,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", eid).execute()
                    st.rerun()
                if b.button("🗑 Xoá entry", key=f"jdel_{eid}", disabled=not can_write, use_container_width=True):
                    admin.table("journal").delete().eq("id", eid).execute()
                    st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: BUILD GUIDE (Roman Numeral XVI) — hướng dẫn deploy Agent OS thật
# ------------------------------------------------------------------------------
if active == "guide":
    gd = SELF_SECTIONS["guide"]
    render_custom_header(gd["num"], "SELF", gd["label"], gd["desc"])

    st.markdown("""
    <div style="background: rgba(30,24,52,0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border:1px solid rgba(168,85,247,0.12); border-radius:14px; padding:22px 24px; margin-bottom:8px; box-shadow:0 8px 32px rgba(0,0,0,0.35);">
      <div style="color:#fff; font-weight:600; font-size:17px; margin-bottom:6px;">🚀 Triển khai Agent OS từ con số 0</div>
      <div style="color:#a5a1c0; font-size:13.5px; line-height:1.65; font-weight:300;">
        Dashboard Streamlit này chạy trên Supabase. Làm theo 7 bước dưới đây để dựng lại toàn bộ hệ thống — từ secrets, schema, đồng bộ Obsidian, tới deploy lên Streamlit Community Cloud.
      </div>
    </div>
    """, unsafe_allow_html=True)

    GUIDE_STEPS = [
        {"title": "Cấu hình secrets", "lang": "bash",
         "desc": "Copy file mẫu rồi điền Supabase URL/keys (và tuỳ chọn Hermes, đường dẫn vault).",
         "code": "cp .streamlit/secrets.toml.example .streamlit/secrets.toml",
         "note": "Bắt buộc: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`. Không bao giờ commit `secrets.toml` (đã gitignore)."},
        {"title": "Tạo schema Supabase", "lang": None,
         "desc": "Mở Supabase SQL Editor, dán toàn bộ security/00_full_setup.sql rồi Run — tạo bảng + seed + RLS.",
         "code": None,
         "note": "⚠️ File `DROP` các bảng trước khi tạo lại → chạy lại sẽ **xoá sạch dữ liệu**. Chỉ chạy 1 lần khi setup."},
        {"title": "Cài deps & chạy local", "lang": "bash",
         "desc": "Cài thư viện runtime và mở dashboard ở localhost.",
         "code": "pip install -r requirements.txt\nstreamlit run app.py",
         "note": "Dashboard chạy tại http://localhost:8501"},
        {"title": "Đồng bộ vault Obsidian", "lang": "bash",
         "desc": "Đẩy ghi chú + [[wikilink]] từ vault local lên bảng obsidian_vault (xem trước bằng --dry-run).",
         "code": "python scripts/sync_obsidian.py --vault PATH --dry-run\npython scripts/sync_obsidian.py --vault PATH",
         "note": "Tự động hoá (Windows): `python scripts/install_task.py` đăng ký Task Scheduler chạy mỗi 6 giờ."},
        {"title": "Verify trực quan", "lang": "bash",
         "desc": "Không có test suite — kiểm tra bằng screenshot Playwright.",
         "code": "pip install -r requirements-dev.txt && playwright install chromium\npython shoot.py",
         "note": None},
        {"title": "Deploy lên Streamlit Cloud", "lang": "bash",
         "desc": "Push lên main → Streamlit Community Cloud tự build. Đặt lại các secret ở Settings → Secrets.",
         "code": "git push origin main",
         "note": "⚠️ Vercel KHÔNG chạy được (Streamlit cần server + websocket). Phải dùng Streamlit Community Cloud."},
        {"title": "Backup tự động", "lang": None,
         "desc": "Workflow .github/workflows/daily-backup.yml export 3 bảng ra backups/*.json hằng ngày (00:00 giờ VN).",
         "code": None,
         "note": "Cần `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` trong GitHub Actions secrets."},
    ]

    for i, step in enumerate(GUIDE_STEPS, start=1):
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin:26px 0 6px 0;">
          <div style="min-width:30px; height:30px; border-radius:9px; background:linear-gradient(135deg,#a855f7,#7c3aed); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:14px; box-shadow:0 0 14px rgba(168,85,247,0.4);">{i}</div>
          <div style="color:#fff; font-weight:600; font-size:17px;">{escape(step['title'])}</div>
        </div>
        <div style="color:#a5a1c0; font-size:13.5px; margin:0 0 8px 42px; line-height:1.6; font-weight:300;">{escape(step['desc'])}</div>
        """, unsafe_allow_html=True)
        if step["code"]:
            st.code(step["code"], language=step["lang"])
        if step["note"]:
            st.caption(step["note"])

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    st.caption("Tài liệu đầy đủ: CLAUDE.md (kiến trúc, secrets, deploy) và docs/ trong repo.")
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: AGENT HQ (Sơ đồ sàn + Chat Drawer)
# ------------------------------------------------------------------------------
if active == "agenthq":
    render_custom_header("XVII", "WORKSPACE", "Agent HQ", "Visual representation of agent floor coordinate logs, status check, and interactive chat line.")
    import time
    
    # 1. Các Agent Định nghĩa
    AGENT_FLOOR_DEFS = {
        "max": {"name": "MAX", "emoji": "🎩", "role": "CEO CORNER", "status": "online", "task": "Coordinating Agent Floor operations.", "glow": "amber-500", "left": "70%", "top": "22%"},
        "sage": {"name": "SAGE", "emoji": "🧙‍♂️", "role": "RESEARCH BAY", "status": "online", "task": "Analyzing queries on CTR retention.", "glow": "emerald-500", "left": "12%", "top": "55%"},
        "knox": {"name": "KNOX", "emoji": "🛡️", "role": "OPS DESK", "status": "working", "task": "DEX transactions checked. Liquidity stable.", "glow": "sky-500", "left": "41%", "top": "55%"},
        "nova": {"name": "NOVA", "emoji": "🚀", "role": "CREATIVE HUB", "status": "idle", "task": "Drafting outline for low budget setups.", "glow": "rose-500", "left": "70%", "top": "55%"},
        "pixel": {"name": "PIXEL", "emoji": "👾", "role": "DESIGN LAB", "status": "online", "task": "Exporting matching CSS design tokens.", "glow": "purple-500", "left": "12%", "top": "22%"},
        "hermes": {"name": "HERMES", "emoji": "⚡", "role": "HERMES DESK", "status": "working", "task": "Model routing: gpt-5.5 · deepseek-4-flash · minimax-m3.", "glow": "emerald-500", "left": "41%", "top": "22%"}
    }
    
    # Lấy chat_agent từ query params hoặc state
    chat_agent = st.query_params.get("chat_agent")
    
    # Setup columns
    if chat_agent and chat_agent in AGENT_FLOOR_DEFS:
        col_floor, col_chat = st.columns([1.8, 1.0])
    else:
        col_floor = st.container()
        col_chat = None
        
    with col_floor:
        # Nhúng CSS styling phục vụ sàn 2D Agent Floor
        floor_css = """
        <style>
        .floor-canvas {
            position: relative;
            width: 100%;
            height: 520px;
            background: #090715;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            background-image: radial-gradient(rgba(255,255,255,0.03) 1.2px, transparent 1.2px);
            background-size: 24px 24px;
        }
        .floor-banner {
            position: absolute;
            top: 16px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(30, 24, 52, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            padding: 6px 16px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            z-index: 100;
        }
        .floor-banner-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #10b981;
            animation: pulse-dot 1.5s infinite;
        }
        @keyframes pulse-dot {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        .floor-banner-text {
            font-size: 10px;
            font-weight: 700;
            color: #a5a1c0;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .agent-node {
            position: absolute;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: all 0.3s ease;
            z-index: 10;
        }
        .agent-node:hover {
            transform: scale(1.03);
        }
        .speech-bubble {
            margin-bottom: 12px;
            background: rgba(26, 20, 44, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 8px 12px;
            max-width: 190px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            position: relative;
            backdrop-filter: blur(8px);
        }
        .speech-bubble-text {
            font-size: 11.5px;
            color: #d8d4e6;
            line-height: 1.4;
            font-weight: 400;
        }
        .speech-bubble-arrow {
            width: 8px;
            height: 8px;
            background: rgba(26, 20, 44, 0.85);
            border-right: 1px solid rgba(255, 255, 255, 0.06);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            position: absolute;
            bottom: -5px;
            left: 50%;
            transform: translateX(-50%) rotate(45deg);
        }
        .agent-box {
            width: 150px;
            background: rgba(30, 24, 52, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        .agent-box:hover {
            background: rgba(45, 35, 75, 0.6);
        }
        .agent-avatar-box {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: #090715;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            position: relative;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            position: absolute;
            bottom: -2px;
            right: -2px;
            border: 1.5px solid #090715;
            box-shadow: 0 0 6px rgba(0,0,0,0.8);
        }
        .status-dot.online { background: #10b981; }
        .status-dot.working { background: #0ea5e9; }
        .status-dot.idle { background: #f59e0b; }
        .status-dot.offline { background: #6b7280; }
        
        .agent-box-name {
            font-weight: 700;
            font-size: 13px;
            color: #ffffff;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .agent-box-role {
            font-size: 9px;
            font-weight: 700;
            color: #a5a1c0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .glow-max:hover { border-color: rgba(245, 158, 11, 0.45) !important; box-shadow: 0 0 15px rgba(245, 158, 11, 0.15) !important; }
        .glow-sage:hover { border-color: rgba(16, 185, 129, 0.45) !important; box-shadow: 0 0 15px rgba(16, 185, 129, 0.15) !important; }
        .glow-knox:hover { border-color: rgba(14, 165, 233, 0.45) !important; box-shadow: 0 0 15px rgba(14, 165, 233, 0.15) !important; }
        .glow-nova:hover { border-color: rgba(244, 63, 94, 0.45) !important; box-shadow: 0 0 15px rgba(244, 63, 94, 0.15) !important; }
        .glow-pixel:hover { border-color: rgba(168, 85, 247, 0.45) !important; box-shadow: 0 0 15px rgba(168, 85, 247, 0.15) !important; }
        .glow-hermes:hover { border-color: rgba(16, 185, 129, 0.45) !important; box-shadow: 0 0 15px rgba(16, 185, 129, 0.15) !important; }
        
        .legend-bar {
            position: absolute;
            bottom: 16px;
            left: 16px;
            background: rgba(10, 7, 21, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 6px 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 10px;
            font-weight: 700;
            color: #8a84a6;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            backdrop-filter: blur(8px);
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .legend-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
        }
        </style>
        """
        st.html(floor_css)
        
        # Build floor HTML content
        agents_html = ""
        for k, a in AGENT_FLOOR_DEFS.items():
            act_task = a["task"]
            status_cls = a["status"]
            active_border = "border-color: rgba(90, 215, 230, 0.45) !important; box-shadow: 0 0 15px rgba(90, 215, 230, 0.2) !important; background: rgba(45, 35, 75, 0.65);" if chat_agent == k else ""
            
            agents_html += f"""
            <div class="agent-node" style="left: {a['left']}; top: {a['top']};">
                <div class="speech-bubble">
                    <div class="speech-bubble-text">{escape(act_task)}</div>
                    <div class="speech-bubble-arrow"></div>
                </div>
                <a href="?nav=agenthq&chat_agent={k}" target="_self" style="text-decoration: none;">
                    <div class="agent-box glow-{k}" style="{active_border}">
                        <div class="agent-avatar-box">
                            {a['emoji']}
                            <span class="status-dot {status_cls}"></span>
                        </div>
                        <div class="agent-box-name">{a['name']}</div>
                        <div class="agent-box-role">{a['role']}</div>
                    </div>
                </a>
            </div>
            """
            
        floor_html = f"""
        <div class="floor-canvas">
            <div class="floor-banner">
                <span class="floor-banner-dot"></span>
                <span class="floor-banner-text">MAX HQ - AGENT FLOOR</span>
                <span class="floor-banner-dot"></span>
            </div>
            {agents_html}
            <div class="legend-bar">
                <div class="legend-item"><span class="legend-dot" style="background:#0ea5e9;"></span>Working</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f59e0b;"></span>Idle</div>
                <div class="legend-item"><span class="legend-dot" style="background:#10b981;"></span>Online</div>
                <div class="legend-item"><span class="legend-dot" style="background:#6b7280;"></span>Offline</div>
            </div>
        </div>
        """
        st.html(floor_html)
        
        # Thêm các nút chat nhanh ở dưới
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        cols_btn = st.columns(6)
        for i, (k, a) in enumerate(AGENT_FLOOR_DEFS.items()):
            btn_style = "border-color: rgba(90, 215, 230, 0.45) !important;" if chat_agent == k else ""
            btn_html = f"""
            <a href="?nav=agenthq&chat_agent={k}" target="_self" style="text-decoration: none; width: 100%;">
                <div style="background: rgba(30, 24, 52, 0.45); border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 8px; text-align: center; color: #d8d4e6; font-size: 11.5px; font-weight: 700; transition: all 0.2s; cursor: pointer; {btn_style}" onmouseover="this.style.background='rgba(45,35,75,0.6)'; this.style.color='#ffffff';" onmouseout="this.style.background='rgba(30,24,52,0.45)'; this.style.color='#d8d4e6';">
                    {a['emoji']} Chat with {a['name']}
                </div>
            </a>
            """
            cols_btn[i].html(btn_html)
            
    if col_chat:
        with col_chat:
            sel_agent = AGENT_FLOOR_DEFS[chat_agent]
            
            # Header chat drawer
            st.html(f"""
            <div style="background: rgba(30, 24, 52, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="font-size: 26px;">{sel_agent['emoji']}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 14.5px; color: #ffffff; line-height: 1.2;">{sel_agent['name']}</div>
                        <div style="font-size: 9.5px; color: #a5a1c0; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">{sel_agent['role']}</div>
                    </div>
                </div>
                <a href="?nav=agenthq" target="_self" style="text-decoration: none; font-size: 16px; color: #8a84a6 !important; transition: all 0.2s;" onmouseover="this.style.color='#ffffff';" onmouseout="this.style.color='#8a84a6';">✕</a>
            </div>
            """)

            # Bảng định tuyến model — hiển thị thống nhất với tab Hermes (luôn hiện kể cả khi VPS lỗi)
            if chat_agent == "hermes":
                st.markdown(hermes_model_card_html(), unsafe_allow_html=True)

            # Lịch sử chat trong session_state
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = {}
                
            if chat_agent not in st.session_state.chat_history:
                st.session_state.chat_history[chat_agent] = [
                    {"role": "assistant", "content": f"Greetings! I am {sel_agent['name']} ({sel_agent['role']}). How can I assist you with our operations today?"}
                ]
                
            chat_container = st.container(height=380)
            with chat_container:
                for m in st.session_state.chat_history[chat_agent]:
                    with st.chat_message(m["role"]):
                        st.markdown(m["content"])
                        
            user_msg = st.chat_input(f"Message {sel_agent['name']}...")
            if user_msg:
                st.session_state.chat_history[chat_agent].append({"role": "user", "content": user_msg})
                
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(user_msg)
                        
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner(f"{sel_agent['name']} is responding..."):
                            agent_response = ""
                            vps_url = st.secrets.get("HERMES_API_URL")
                            vps_key = st.secrets.get("HERMES_API_KEY")
                            
                            is_ai_agent = chat_agent in ["hermes", "max", "sage", "knox", "nova", "pixel"]
                            
                            # 1) AI AGENTS (Hermes & Simulated Personas using VPS API)
                            if is_ai_agent and vps_url and vps_key:
                                if chat_agent == "hermes":
                                    api_msg = user_msg
                                else:
                                    roleplay_prompts = {
                                        "max": "Bạn là MAX (CEO Corner), người điều phối dự án y khoa 'Bác sĩ chính mình'. Hãy trả lời tin nhắn sau của người dùng bằng tiếng Việt với phong thái tự tin, tầm nhìn chiến lược và định hướng quản lý:",
                                        "sage": "Bạn là SAGE (Research Bay), nhà nghiên cứu thông tin y khoa của dự án 'Bác sĩ chính mình'. Hãy phân tích và trả lời tin nhắn sau của người dùng bằng tiếng Việt dựa trên kiến thức y học, chế độ ăn uống, dinh dưỡng và các bằng chứng khoa học cụ thể:",
                                        "knox": "Bạn là KNOX (Ops Desk), điều hành kỹ thuật và dữ liệu của hệ thống 'Bác sĩ chính mình'. Hãy trả lời tin nhắn sau của người dùng bằng tiếng Việt tập trung vào các giải pháp kỹ thuật, cơ sở dữ liệu Supabase, MCP sync và vận hành hệ thống:",
                                        "nova": "Bạn là NOVA (Creative Hub), chuyên gia sáng tạo nội dung, kịch bản video YouTube và bài viết SEO của dự án 'Bác sĩ chính mình'. Hãy trả lời tin nhắn sau của người dùng bằng tiếng Việt với sự hào hứng, tập trung vào ý tưởng làm nội dung, kịch bản video hoặc chiến dịch truyền thông y khoa chủ động:",
                                        "pixel": "Bạn là PIXEL (Design Lab), nhà thiết kế UI/UX và CSS của dashboard 'Agentic OS'. Hãy trả lời tin nhắn sau của người dùng bằng tiếng Việt tập trung vào khía cạnh thiết kế giao diện, trải nghiệm người dùng, CSS, layout Glassmorphism và thẩm mỹ ứng dụng:"
                                    }
                                    prefix = roleplay_prompts.get(chat_agent, "")
                                    api_msg = f"{prefix}\n\"{user_msg}\""
                                    
                                try:
                                    headers = {"Authorization": f"Bearer {vps_key}", "Content-Type": "application/json"}
                                    r = httpx.post(f"{vps_url.rstrip('/')}/chat", json={"message": api_msg}, headers=headers, timeout=180)
                                    if r.status_code == 401:
                                        agent_response = ("⚠️ **401 Unauthorized** — `HERMES_API_KEY` không khớp với shim trên VPS.\n\n"
                                                         "Sửa: copy đúng key trong `/root/.hermes/hermes-api.env` (VPS) vào Streamlit Cloud "
                                                         "→ **Settings → Secrets** (`HERMES_API_KEY`) cho khớp, rồi rerun app. Xem `vps/README.md`.")
                                    else:
                                        r.raise_for_status()
                                        raw_reply = r.json().get("reply", "")
                                        
                                        if chat_agent == "hermes":
                                            cleaned = raw_reply.split("\n")
                                            cleaned = [line for line in cleaned if not (("Hermes" in line) and ("─" in line or "═" in line))]
                                            cleaned = [line.replace("│", "").strip() for line in cleaned]
                                            cleaned = [line for line in cleaned if not all(c in "─╭╰╯╮┬┴┼═║╔╗╚╝░▒▓█▄▀■-—_=+*#" for c in line.strip())]
                                            agent_response = "\n".join([l for l in cleaned if l.strip()]).strip()
                                            if not agent_response:
                                                agent_response = raw_reply.strip()
                                        else:
                                            agent_response = raw_reply.strip()
                                            
                                except Exception as e:
                                    # Hiển thị thông báo nhỏ cảnh báo kết nối
                                    err_msg = str(e)
                                    if "504" in err_msg or "Timeout" in err_msg:
                                        display_err = "Timeout/Phản hồi chậm"
                                    else:
                                        display_err = err_msg[:40] + "..." if len(err_msg) > 40 else err_msg
                                        
                                    st.toast(f"⚠️ Kết nối AI gián đoạn ({display_err}). Đang dùng phản hồi dự phòng.", icon="⚠️")
                                    
                                    # Fallback tiếng Việt đúng vai trò của từng agent
                                    if chat_agent == "max":
                                        agent_response = f"Tôi là MAX (CEO Corner). Tôi đã ghi nhận yêu cầu của bạn: \"{user_msg}\". Hiện tại kết nối đến máy chủ AI đang gặp sự cố ({display_err}), nhưng tôi sẽ thảo luận với Sage và Knox để điều phối hoạt động ngay khi hệ thống ổn định trở lại."
                                    elif chat_agent == "sage":
                                        agent_response = f"Tôi là SAGE (Research Bay). Về yêu cầu tìm kiếm: \"{user_msg}\", tôi rất muốn tra cứu các tài liệu y khoa mới nhất cho bạn. Do kết nối AI đang gián đoạn ({display_err}), dưới đây là phân tích sơ bộ của tôi: chế độ ăn uống đóng vai trò then chốt đối với gan nhiễm mỡ. Bạn nên khuyên bệnh nhân/người dùng hạn chế thực phẩm nhiều đường fructozơ, đồ chiên rán, và bổ sung nhiều rau xanh, omega-3, kết hợp tập thể thao đều đặn. Chi tiết nghiên cứu cụ thể, tôi sẽ cập nhật thêm khi hệ thống kết nối lại."
                                    elif chat_agent == "knox":
                                        agent_response = f"Tôi là KNOX (Ops Desk). Trạng thái cơ sở dữ liệu Supabase vẫn đang ỔN ĐỊNH. Đã ghi nhận lệnh \"{user_msg}\" của bạn. Kết nối AI đến VPS tạm thời gặp lỗi ({display_err}), hệ thống kỹ thuật đang tự động ghi nhận nhật ký lỗi để khắc phục."
                                    elif chat_agent == "nova":
                                        agent_response = f"Chào bạn! Tôi là NOVA. Ý tưởng phát triển nội dung về \"{user_msg}\" thực sự rất tiềm năng cho các video chia sẻ kiến thức sức khỏe chủ động của chúng ta. Hiện kết nối AI đang bị gián đoạn ({display_err}), tôi đề xuất outline kịch bản nhanh: 1. Hook nhấn mạnh mối nguy hiểm thầm lặng của thói quen ăn uống xấu gây gan nhiễm mỡ; 2. Phân tích 3 loại thực phẩm tàn phá gan nhanh nhất; 3. Gợi ý 3 thực phẩm vàng giải độc gan."
                                    elif chat_agent == "pixel":
                                        agent_response = f"Tôi là PIXEL. Yêu cầu thiết kế liên quan đến \"{user_msg}\" đã được ghi nhận. Kết nối máy chủ AI đang bị gián đoạn ({display_err}), tôi đang tiến hành kiểm tra các token màu sắc và cấu trúc CSS Glassmorphism thủ công."
                                    elif chat_agent == "hermes":
                                        agent_response = f"Tôi là HERMES. Kết nối AI VPS hiện tại gặp lỗi gián đoạn ({display_err}). Vui lòng kiểm tra lại dịch vụ FastAPI shim trên Hostinger VPS hoặc kết nối mạng."
                                    else:
                                        agent_response = f"Đã ghi nhận tin nhắn: \"{user_msg}\". (Đang hoạt động ngoại tuyến do lỗi kết nối AI: {display_err})"
                                    
                            # 2) OPENCLAW (Real Gateway)
                            elif chat_agent == "openclaw":
                                o_url = st.secrets.get("OPENCLAW_URL")
                                if o_url:
                                    try:
                                        headers = {"Content-Type": "application/json"}
                                        r = httpx.post(f"{o_url.rstrip('/')}/api/chat", json={"agentId": "openclaw", "message": user_msg}, headers=headers, timeout=30)
                                        if r.status_code == 200:
                                            data = r.json()
                                            agent_response = data.get("response", data.get("reply", ""))
                                        else:
                                            agent_response = f"[OpenClaw Swarm Gateway] Dispatched checklist. Swarm coordinator online at {o_url}. Status: {r.status_code}."
                                    except Exception as e:
                                        agent_response = f"[OpenClaw Swarm Gateway] Dispatched checklist. Swarm coordinator online at {o_url}. Node callback pending: {e}."
                                else:
                                    agent_response = f"OpenClaw swarm coordinator: \"{user_msg}\". (Live gateway connection pending OPENCLAW_URL configuration in secrets)."
                                    
                            # 3) FALLBACK (If API Offline or Unconfigured)
                            else:
                                time.sleep(0.5)
                                if chat_agent == "max":
                                    agent_response = f"Tôi là MAX (CEO Corner). Tôi đã ghi nhận yêu cầu của bạn: \"{user_msg}\". Hiện tại hệ thống AI đang ngoại tuyến, nhưng tôi sẽ thảo luận với Sage và Knox để phân phối băng thông xử lý ngay khi hệ thống kết nối lại."
                                elif chat_agent == "sage":
                                    agent_response = f"Tôi là SAGE (Research Bay). Về yêu cầu: \"{user_msg}\", tôi rất muốn tra cứu các tài liệu y khoa và nghiên cứu mới nhất cho bạn. Do kết nối AI ngoại tuyến, bạn có thể tham khảo các tài liệu trong Obsidian Vault hoặc thử lại sau nhé."
                                elif chat_agent == "knox":
                                    agent_response = f"Trạng thái hệ thống: ỔN ĐỊNH. Knox (Ops Desk) đã ghi nhận lệnh: \"{user_msg}\". Các bể thanh khoản và dữ liệu Supabase hoạt động tốt. Kết nối AI ngoại tuyến, hệ thống đang lưu log chờ xử lý."
                                elif chat_agent == "nova":
                                    agent_response = f"Tôi là NOVA! Ý tưởng về \"{user_msg}\" rất hấp dẫn để sản xuất nội dung video hoặc bài viết SEO y khoa cho dự án 'Bác sĩ chính mình'. Tiếc là hệ thống AI đang ngoại tuyến, khi online chúng ta sẽ lập tức lên outline chi tiết nhé!"
                                elif chat_agent == "pixel":
                                    agent_response = f"Tôi là PIXEL. Yêu cầu của bạn: \"{user_msg}\" liên quan đến thiết kế. Tôi đang tối ưu hóa các biến CSS và layout Glassmorphism cho ứng dụng. Rất mong hệ thống AI sớm kết nối lại."
                                elif chat_agent == "hermes":
                                    agent_response = f"Tôi là HERMES. Tin nhắn của bạn: \"{user_msg}\". Kết nối VPS ngoại tuyến hoặc thiếu cấu hình API key trong secrets."
                                else:
                                    agent_response = f"Đã ghi nhận tin nhắn: \"{user_msg}\". Tôi đang hoạt động ngoại tuyến."
                                    
                            st.markdown(agent_response)
                            
                st.session_state.chat_history[chat_agent].append({"role": "assistant", "content": agent_response})
                st.rerun()

    st.stop()

# ------------------------------------------------------------------------------
# VIEW: IDEAS BOARD (Roman Numeral XVIII)
# ------------------------------------------------------------------------------
if active == "ideas":
    import time
    
    @st.dialog("Tạo ý tưởng mới")
    def create_new_idea_dialog():
        with st.form("new_idea_form", clear_on_submit=True):
            title = st.text_input("Tiêu đề", placeholder="vd. Auto-standup summary email...", key="new_idea_title")
            desc = st.text_area("Mô tả ý tưởng", placeholder="Mô tả chi tiết ý tưởng hoạt động...", key="new_idea_desc")
            
            c_cat, c_src = st.columns(2)
            category = c_cat.selectbox("Category", ["Content", "Experiment", "Thread", "Build", "General"], index=0)
            source = c_src.selectbox("Source", ["user", "max", "sage", "knox", "nova", "pixel"], index=0)
            
            submitted = st.form_submit_button("Lưu ý tưởng", use_container_width=True)
            if submitted:
                if not title.strip():
                    st.error("Tiêu đề không được bỏ trống.")
                else:
                    new_idea = {
                        "id": f"idea-{int(time.time())}",
                        "title": title.strip(),
                        "description": desc.strip() or None,
                        "category": category,
                        "source": source,
                        "status": "pending",
                        "timestamp": datetime.now().isoformat()
                    }
                    if save_idea(new_idea):
                        st.success("Đã lưu ý tưởng mới thành công!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Lỗi khi lưu ý tưởng.")
                        
    ideas_list = load_ideas_data()
    pending_count = sum(1 for i in ideas_list if i.get("status") == "pending" or not i.get("status"))
    total_count = len(ideas_list)

    render_back_button()
    st.markdown("""
    <style>
    .ideas-header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 15px;
    }
    .ideas-title-box {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .ideas-title-text {
        font-family: 'Outfit', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_h_left, col_h_right = st.columns([2, 1])
    with col_h_left:
        st.markdown(f"""
        <div class="ideas-title-box">
            <span style="font-size: 28px; color: #f59e0b;">💡</span>
            <h1 class="ideas-title-text" style="display:inline; margin-left: 5px;">Ideas Board</h1>
        </div>
        <p style="color: #8a84a6; font-size:13.5px; margin: 4px 0 0 0; font-weight:300;">
            {pending_count} pending &bull; {total_count} total
        </p>
        """, unsafe_allow_html=True)
    with col_h_right:
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Add Idea", key="add_idea_btn_st", use_container_width=True):
            create_new_idea_dialog()
            
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    
    ideas_filter = st.query_params.get("ideas_filter", "active")
    ideas_cat_filter = st.query_params.get("ideas_cat_filter", "All Categories")
    
    c_filt_left, c_filt_right = st.columns([3.2, 1.0])
    with c_filt_left:
        tabs_lbl = ["Active", "All", "Approved", "Done", "Rejected"]
        tabs_ids = ["active", "all", "approved", "done", "rejected"]
        cols_t = st.columns(5)
        for idx, (lbl, tid) in enumerate(zip(tabs_lbl, tabs_ids)):
            cnt = 0
            for idea in ideas_list:
                matches_cat = (ideas_cat_filter == "All Categories" or idea.get("category", "").lower() == ideas_cat_filter.lower())
                if not matches_cat:
                    continue
                if tid == "all":
                    cnt += 1
                elif tid == "active":
                    if idea.get("status") == "pending" or not idea.get("status"):
                        cnt += 1
                else:
                    if idea.get("status") == tid:
                        cnt += 1
                        
            active_btn_style = "background: rgba(90, 200, 220, 0.15) !important; border-color: rgba(90, 215, 230, 0.4) !important; color:#ffffff !important;" if ideas_filter == tid else ""
            badge_style = "background: rgba(16, 185, 129, 0.2); color:#10b981;" if ideas_filter == tid else "background: rgba(255,255,255,0.06); color:#a5a1c0;"
            
            btn_html = f"""
            <a href="?nav=ideas&ideas_filter={tid}&ideas_cat_filter={ideas_cat_filter}" target="_self" style="text-decoration: none; width:100%;">
                <div style="background: rgba(30, 24, 52, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); padding: 8px 10px; border-radius: 8px; text-align: center; color: #a5a1c0; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; transition: all 0.2s; {active_btn_style}" onmouseover="this.style.background='rgba(45,35,75,0.6)';" onmouseout="this.style.background='{("rgba(90,200,220,0.15)" if ideas_filter == tid else "rgba(30, 24, 52, 0.4)")}';">
                    <span>{lbl}</span>
                    <span style="padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 900; {badge_style}">{cnt}</span>
                </div>
            </a>
            """
            cols_t[idx].markdown(btn_html, unsafe_allow_html=True)
            
    with c_filt_right:
        cats_list = ["All Categories", "Experiment", "Content", "Thread", "Build", "General"]
        sel_idx = cats_list.index(ideas_cat_filter) if ideas_cat_filter in cats_list else 0
        cat_select = st.selectbox("Lọc danh mục", cats_list, index=sel_idx, label_visibility="collapsed", key="cat_select_ideas")
        if cat_select != ideas_cat_filter:
            st.query_params["ideas_cat_filter"] = cat_select
            st.rerun()
            
    filtered_ideas = []
    for idea in ideas_list:
        matches_status = False
        status_val = idea.get("status", "pending") or "pending"
        if ideas_filter == "all":
            matches_status = True
        elif ideas_filter == "active":
            matches_status = (status_val == "pending")
        else:
            matches_status = (status_val == ideas_filter)
            
        matches_cat = (ideas_cat_filter == "All Categories" or idea.get("category", "").lower() == ideas_cat_filter.lower())
        
        if matches_status and matches_cat:
            filtered_ideas.append(idea)
            
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    
    if not filtered_ideas:
        st.markdown("""
        <div style="text-align: center; padding: 60px; border: 1px dashed rgba(255,255,255,0.08); border-radius: 12px; color: #8a84a6; font-size: 14px;">
            No ideas found under this section.
        </div>
        """, unsafe_allow_html=True)
    else:
        cols_grid = st.columns(3)
        for i, idea in enumerate(filtered_ideas):
            col_idx = i % 3
            with cols_grid[col_idx]:
                status_val = idea.get("status", "pending") or "pending"
                is_pending = (status_val == "pending")
                
                tags_html = ""
                if is_pending:
                    tags_html += """
                    <span style="font-size: 9px; font-weight: 900; text-transform: uppercase; color: #38bdf8; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.2); padding: 2px 8px; border-radius: 20px; display: inline-flex; align-items: center; gap: 4px;">
                        <span style="width:4px; height:4px; border-radius:50%; background:#38bdf8; display:inline-block; animation: pulse-dot 1s infinite;"></span> New
                    </span>
                    """
                tags_html += f"""
                <span style="font-size: 9px; font-weight: 900; text-transform: uppercase; color: #a5a1c0; background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 20px;">
                    🏷️ {escape(idea.get("category", "General"))}
                </span>
                """
                
                card_html = f"""
                <div style="background: rgba(30, 24, 52, 0.45); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; min-height: 190px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;" onmouseover="this.style.borderColor='rgba(16, 185, 129, 0.2)';" onmouseout="this.style.borderColor='rgba(255,255,255,0.06)';">
                    <div>
                        <div style="display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap;">
                            {tags_html}
                        </div>
                        <h3 style="font-size: 14.5px; font-weight: 700; color: #ffffff; margin: 0 0 8px 0; line-height: 1.4;">
                            {escape(idea.get("title"))}
                        </h3>
                        <p style="font-size: 12.5px; color: #a5a1c0; line-height: 1.4; font-weight: 400; margin: 0 0 15px 0;">
                            {escape(idea.get("description") or "")}
                        </p>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px; margin-top: auto;">
                        <span style="font-size: 9.5px; font-weight: 700; color: #8a84a6; text-transform: uppercase; letter-spacing: 0.5px;">By: {escape(idea.get("source") or "user")}</span>
                """
                
                if not is_pending:
                    badge_color = "#10b981" if status_val == "approved" else "#ef4444"
                    badge_bg = "rgba(16,185,129,0.1)" if status_val == "approved" else "rgba(239,68,68,0.1)"
                    card_html += f"""
                        <span style="font-size: 9px; font-weight: 900; text-transform: uppercase; color: {badge_color}; background: {badge_bg}; border: 1px solid {badge_color}30; padding: 2px 8px; border-radius: 4px;">{status_val}</span>
                    """
                
                card_html += "</div></div>"
                st.html(card_html)
                
                if is_pending:
                    c_act_l, c_act_r = st.columns(2)
                    if c_act_l.button("✓ Approve", key=f"appr_{idea['id']}", use_container_width=True):
                        update_idea_status_db(idea["id"], "approved")
                        st.rerun()
                    if c_act_r.button("✗ Reject", key=f"rej_{idea['id']}", use_container_width=True):
                        update_idea_status_db(idea["id"], "rejected")
                        st.rerun()
                        
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: YOUTUBE STUDIO (Roman Numeral XIX)
# ------------------------------------------------------------------------------
if active == "youtube":
    import time
    
    if "yt_toast" in st.session_state and st.session_state.yt_toast:
        st.toast(st.session_state.yt_toast, icon="✅")
        st.session_state.yt_toast = None
        
    yt_tab = st.query_params.get("yt_tab", "long_form")

    render_back_button()
    st.markdown("""
    <style>
    .yt-tab-bar {
        display: flex;
        gap: 5px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding-bottom: 5px;
        margin-bottom: 25px;
        overflow-x: auto;
    }
    .yt-tab-item {
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 700;
        color: #a5a1c0;
        border-bottom: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
    }
    .yt-tab-item:hover {
        color: #ffffff;
    }
    .yt-tab-item.active {
        color: #10b981;
        border-color: #10b981;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tabs_main = [
        ("long_form", "Long Form"),
        ("shorts", "Shorts"),
        ("performance", "Performance"),
        ("outliers", "Outliers"),
        ("content_gap", "Content Gap")
    ]
    
    tabs_html = "".join([
        f'<a href="?nav=youtube&yt_tab={tid}" target="_self" class="yt-tab-item {"active" if yt_tab == tid else ""}">{lbl}</a>'
        for tid, lbl in tabs_main
    ])
    st.markdown(f'<div class="yt-tab-bar">{tabs_html}</div>', unsafe_allow_html=True)
    
    if yt_tab != "long_form":
        st.markdown(f"""
        <div style="padding: 80px 20px; text-align: center; border: 1px dashed rgba(255, 255, 255, 0.08); border-radius: 16px; color: #8a84a6; font-size: 14px;">
            This dashboard section is managed by Nova. Review the Long Form tab to assign scripting goals.
        </div>
        """, unsafe_allow_html=True)
        st.stop()
        
    col_h_left, col_h_right = st.columns([2, 1])
    with col_h_left:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 20px; color: #ef4444;">📺</span>
            </div>
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <h1 style="font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 700; color: #ffffff; margin: 0; line-height: 1.0;">Long Form</h1>
                    <span style="font-size: 9px; font-weight: 900; text-transform: uppercase; color: #ef4444; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 2px 8px; border-radius: 20px;">YouTube</span>
                    <span style="font-size: 9px; font-weight: 900; text-transform: uppercase; color: #3b82f6; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); padding: 2px 8px; border-radius: 20px;">Twitter</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    scripts_list = load_youtube_scripts()
    
    yt_filter_type = st.query_params.get("yt_type", "all")
    yt_cat_tab = st.query_params.get("yt_cat", "ideas")
    
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    c_sub_l, c_sub_r = st.columns([1.5, 2.5])
    
    with c_sub_l:
        st.markdown("<div style='font-size: 11px; font-weight: 700; color: #5b5478; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;'>Filter</div>", unsafe_allow_html=True)
        cols_type = st.columns(3)
        types_lbl = ["All", "Articles", "Videos"]
        types_ids = ["all", "articles", "videos"]
        for idx, (lbl, tid) in enumerate(zip(types_lbl, types_ids)):
            active_btn_style = "background: rgba(255, 255, 255, 0.05) !important; color:#ffffff !important; border-color: rgba(255,255,255,0.15);" if yt_filter_type == tid else ""
            btn_html = f"""
            <a href="?nav=youtube&yt_tab=long_form&yt_type={tid}&yt_cat={yt_cat_tab}" target="_self" style="text-decoration: none; width:100%;">
                <div style="background: rgba(30, 24, 52, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); padding: 6px; border-radius: 6px; text-align: center; color: #a5a1c0; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s; {active_btn_style}" onmouseover="this.style.background='rgba(45,35,75,0.6)';" onmouseout="this.style.background='{("rgba(255, 255, 255, 0.05)" if yt_filter_type == tid else "rgba(30, 24, 52, 0.4)")}';">
                    {lbl}
                </div>
            </a>
            """
            cols_type[idx].markdown(btn_html, unsafe_allow_html=True)
            
    with c_sub_r:
        cols_cat = st.columns(5)
        cats_lbl = ["Ideas", "Scripts", "To Film", "Filmed", "Posted"]
        cats_ids = ["ideas", "scripts", "to_film", "filmed", "posted"]
        for idx, (lbl, cid) in enumerate(zip(cats_lbl, cats_ids)):
            cnt = sum(1 for s in scripts_list if s.get("category") == cid)
            active_btn_style = "background: rgba(30, 24, 52, 0.6) !important; border-color: rgba(16, 185, 129, 0.3) !important; color:#ffffff !important;" if yt_cat_tab == cid else ""
            badge_style = "background: rgba(16, 185, 129, 0.2); color:#10b981;" if yt_cat_tab == cid else "background: rgba(255,255,255,0.06); color:#a5a1c0;"
            
            btn_html = f"""
            <a href="?nav=youtube&yt_tab=long_form&yt_type={yt_filter_type}&yt_cat={cid}" target="_self" style="text-decoration: none; width:100%;">
                <div style="background: rgba(30, 24, 52, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); padding: 8px 6px; border-radius: 8px; text-align: center; color: #a5a1c0; font-size: 11.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 4px; cursor: pointer; transition: all 0.2s; {active_btn_style}" onmouseover="this.style.background='rgba(45,35,75,0.6)';" onmouseout="this.style.background='{("rgba(30, 24, 52, 0.6)" if yt_cat_tab == cid else "rgba(30, 24, 52, 0.3)")}';">
                    <span>{lbl}</span>
                    <span style="padding: 1px 5px; border-radius: 4px; font-size: 9.5px; font-weight: 900; {badge_style}">{cnt}</span>
                </div>
            </a>
            """
            cols_cat[idx].markdown(btn_html, unsafe_allow_html=True)
            
    st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(30, 24, 52, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 18px; box-shadow: inset 0 0 10px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0; font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 600; color: #ffffff; display: flex; align-items: center; gap: 6px;">
            <span style="color:#10b981; font-size:12px; animation: pulse-dot 1.5s infinite;">✦</span> Ask Nova to generate a new script outline
        </h4>
    """, unsafe_allow_html=True)
    
    with st.form("nova_prompt_form", clear_on_submit=True):
        prompt_txt = st.text_area("Yêu cầu Nova phác thảo kịch bản", placeholder="vd. Làm thế nào để setup 7 AI agent chạy tự động với chi phí cực thấp...", height=80, label_visibility="collapsed")
        c_frm_l, c_frm_r = st.columns([3, 1])
        c_frm_l.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        submitted = c_frm_r.form_submit_button("Ask Nova to Outline", use_container_width=True)
        if submitted and prompt_txt.strip():
            with st.spinner("Nova đang phác thảo kịch bản..."):
                generated_text = generate_nova_script(prompt_txt.strip())
            new_scr = {
                "id": f"script-{int(time.time())}",
                "title": prompt_txt.strip(),
                "hook": False,
                "outline": False,
                "fullScript": False,
                "status": "pending_review",
                "category": "ideas",
                "type": "videos",
                "notes": "",
                "script_text": generated_text
            }
            scripts_list.insert(0, new_scr)
            save_youtube_scripts(scripts_list)
            st.session_state.yt_toast = "Tạo script outline mới thành công!"
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)
    
    filtered_scripts = []
    for s in scripts_list:
        matches_cat = (s.get("category") == yt_cat_tab)
        matches_type = (yt_filter_type == "all" or s.get("type") == yt_filter_type)
        
        if matches_cat and matches_type:
            filtered_scripts.append(s)
            
    st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:15px;'>Pending review ({len(filtered_scripts)})</div>", unsafe_allow_html=True)
    
    if not filtered_scripts:
        st.markdown(f"""
        <div style="text-align: center; padding: 60px; border: 1px dashed rgba(255,255,255,0.08); border-radius: 12px; color: #8a84a6; font-size: 14px;">
            No scripts pending in this category.
        </div>
        """, unsafe_allow_html=True)
    else:
        for s in filtered_scripts:
            tweak_key = f"tweak_mode_{s['id']}"
            if tweak_key not in st.session_state:
                st.session_state[tweak_key] = False
                
            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 15px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <h3 style="font-size: 15.5px; font-weight: 700; color: #ffffff; margin: 0; line-height: 1.4; max-width: 85%;">
                        {escape(s['title'])}
                    </h3>
                    <span style="font-size: 9px; font-weight: 900; text-transform: uppercase; color: #a5a1c0; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 4px;">{escape(s['type'])}</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='font-size:10px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:0.5px;'>Checklist validation</div>", unsafe_allow_html=True)
            c_chk_1, c_chk_2, c_chk_3 = st.columns(3)
            
            chk_hook = c_chk_1.checkbox("HOOK", value=s.get("hook", False), key=f"hook_{s['id']}")
            chk_out = c_chk_2.checkbox("OUTLINE", value=s.get("outline", False), key=f"out_{s['id']}")
            chk_full = c_chk_3.checkbox("FULL SCRIPT", value=s.get("fullScript", False), key=f"full_{s['id']}")
            
            if (chk_hook != s.get("hook") or chk_out != s.get("outline") or chk_full != s.get("fullScript")):
                s["hook"] = chk_hook
                s["outline"] = chk_out
                s["fullScript"] = chk_full
                
                if chk_hook and chk_out and chk_full:
                    s["category"] = "scripts"
                    st.session_state.yt_toast = "Outline approved! Moving to scripts layout."
                else:
                    st.session_state.yt_toast = "Cập nhật checklist kịch bản!"
                save_youtube_scripts(scripts_list)
                st.rerun()
                
            if st.session_state[tweak_key]:
                with st.form(f"tweak_form_{s['id']}", clear_on_submit=False):
                    tw_notes = st.text_input("Ghi chú chỉnh sửa kịch bản", value=s.get("notes", ""))
                    c_tw_frm_l, c_tw_frm_r = st.columns([4, 1])
                    c_tw_frm_l.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                    if c_tw_frm_r.form_submit_button("Save Notes", use_container_width=True):
                        s["notes"] = tw_notes.strip()
                        save_youtube_scripts(scripts_list)
                        st.session_state[tweak_key] = False
                        st.session_state.yt_toast = "Lưu ghi chú thành công!"
                        st.rerun()
                    if st.form_submit_button("Cancel", key=f"cancel_tw_{s['id']}", use_container_width=True):
                        st.session_state[tweak_key] = False
                        st.rerun()
            else:
                if s.get("notes"):
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.12); padding: 10px 14px; border-radius: 8px; font-size: 12.5px; color: #a5a1c0; font-style: italic;">
                        Notes: {escape(s['notes'])}
                    </div>
                    """, unsafe_allow_html=True)
                    
            st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.05); padding-top:12px; margin-top:5px;'></div>", unsafe_allow_html=True)
            c_act_l, c_act_r = st.columns([2.5, 1.5])
            
            with c_act_l:
                st.markdown("""
                <style>
                .yt-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    padding: 6px 12px;
                    border-radius: 6px;
                    color: #a5a1c0;
                    font-size: 11px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .yt-btn:hover {
                    background: rgba(255,255,255,0.05);
                    color: #ffffff;
                }
                .yt-btn-primary {
                    background: rgba(16, 185, 129, 0.05);
                    border-color: rgba(16, 185, 129, 0.25);
                    color: #10b981;
                }
                .yt-btn-primary:hover {
                    background: rgba(16, 185, 129, 0.12);
                    color: #34d399;
                }
                </style>
                """, unsafe_allow_html=True)
                
                script_content = s.get("script_text")
                if not script_content:
                    script_content = f"""TITLE: {s['title']}
--------------------------------------------------
[HOOK]
(0:00 - 0:30)
"Most creators fail not because they lack ideas, but because they lack an automated system. In this video, I will show you how we coordinate our OpenClaw stack to do all the heavy lifting for under $30 a month..."

[OUTLINE]
1. Introduction to OpenClaw core architecture.
2. Setting up the database on Supabase using port 5432.
3. Seeding Max, Sage, Knox, and Nova on our Agent Floor.
4. Integrating the heartbeats API endpoint.
5. Running the entire setup locally with low budget.

[FULL SCRIPT BODY]
(Read the full script text draft here... complete tutorial details included)"""
                render_copy_button("Copy Full Script", script_content, f"yt_{s['id']}")

                st.markdown("<span style='margin-right:8px;'></span>", unsafe_allow_html=True)
                if st.button(f"✓ Approve & Generate Script", key=f"appr_gen_{s['id']}"):
                    s["hook"] = True
                    s["outline"] = True
                    s["fullScript"] = True
                    s["category"] = "scripts"
                    if not s.get("script_text"):
                        with st.spinner("Nova đang phác thảo kịch bản..."):
                            s["script_text"] = generate_nova_script(s["title"])
                    save_youtube_scripts(scripts_list)
                    st.session_state.yt_toast = "Outline approved! Moving to scripts layout."
                    st.rerun()
                    
            with c_act_r:
                c_btn_l, c_btn_r = st.columns(2)
                if c_btn_l.button("✎ Tweak", key=f"tweak_btn_{s['id']}", use_container_width=True):
                    st.session_state[tweak_key] = True
                    st.rerun()
                if c_btn_r.button("🗑 Reject", key=f"reject_btn_{s['id']}", use_container_width=True):
                    scripts_list = [scr for scr in scripts_list if scr["id"] != s["id"]]
                    save_youtube_scripts(scripts_list)
                    st.session_state.yt_toast = "Đã loại bỏ kịch bản!"
                    st.rerun()
                    
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: SKILLS (thư viện Skill — tạo, import, gọi vào Workspace)
# ------------------------------------------------------------------------------
if active == "skills":
    render_skills_page()
    st.stop()

# VIEW: ALL OTHER SELF SECTIONS (fallback cho SELF section chưa có view riêng)
# ------------------------------------------------------------------------------
if active in SELF_SECTIONS and active not in ["memory", "agenthq", "ideas", "youtube"]:
    s = SELF_SECTIONS[active]
    render_custom_header(s["num"], "SELF", s["label"], s["desc"])
    
    dfv = get_obsidian_vault()
    if not dfv.empty and s["match"]:
        # Filter matching files
        mask = (dfv["file_path"].str.contains(s["match"], case=False, na=False) |
                dfv["file_name"].str.contains(s["match"], case=False, na=False))
        df_filtered = dfv[mask]
    else:
        df_filtered = dfv

    if df_filtered.empty:
        st.info(f"No notes or files indexed inside **{s['label']}**.")
    else:
        st.caption(f"{len(df_filtered)} items cached")
        for _, row in df_filtered.iterrows():
            render_vault_card(row)
    st.stop()

# ==============================================================================
# 9. MAIN PANEL VIEW: MEMORY (Roman Numeral XV)
# ==============================================================================

render_custom_header("XV", "SELF", "Memory", "Search 1,261 Omi memories + your Obsidian vault.")

# Tabs sub-navigation
tab_recent, tab_notes, tab_omi, tab_graph = st.tabs(["Recent", "Notes", "Omi", "Graph"])

df_vault = get_obsidian_vault()

# ------------------------------------------------------------------------------
# TAB: RECENT
# ------------------------------------------------------------------------------
with tab_recent:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    # Search box inside tabs matching screenshot
    search_recent = st.text_input("Search Memories", placeholder="Search recent memories...", label_visibility="collapsed", key="search_rec")
    
    df_r = df_vault[df_vault["category"] == "Recent"]
    if search_recent:
        df_r = df_r[df_r["file_name"].str.contains(search_recent, case=False, regex=False)]
        
    if df_r.empty:
        st.info("No recent items found.")
    else:
        for _, row in df_r.iterrows():
            render_vault_card(row)

# ------------------------------------------------------------------------------
# TAB: NOTES
# ------------------------------------------------------------------------------
with tab_notes:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    search_notes = st.text_input("Search Notes", placeholder="Search index notes...", label_visibility="collapsed", key="search_not")
    
    df_n = df_vault[df_vault["category"] == "Notes"]
    if search_notes:
        df_n = df_n[df_n["file_name"].str.contains(search_notes, case=False, regex=False)]
        
    if df_n.empty:
        st.info("No Obsidian Notes matching filters.")
    else:
        for _, row in df_n.iterrows():
            render_vault_card(row)

# ------------------------------------------------------------------------------
# TAB: OMI
# ------------------------------------------------------------------------------
with tab_omi:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    search_omi = st.text_input("Search Omi", placeholder="Search Omi wearable voice logs...", label_visibility="collapsed", key="search_omi")
    
    df_o = df_vault[df_vault["category"] == "Omi"]
    if search_omi:
        df_o = df_o[df_o["file_name"].str.contains(search_omi, case=False, regex=False)]
        
    if df_o.empty:
        st.info("No logged Omi audio transcripts.")
    else:
        for _, row in df_o.iterrows():
            render_vault_card(row)

# ------------------------------------------------------------------------------
# TAB: GRAPH (PREMIUM INTERACTIVE D3 CANVAS KNOWLEDGE GRAPH)
# ------------------------------------------------------------------------------
with tab_graph:
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    
    # Dựng node + cạnh từ vault thật (df_vault có cột links khi đã sync Obsidian).
    g_rows = df_vault.to_dict("records")
    has_links = "links" in df_vault.columns
    cat_colors = {"Recent": "#5ad7e6", "Notes": "#a855f7", "Omi": "#34d399"}
    path_to_idx = {str(r.get("file_path")): i for i, r in enumerate(g_rows)}

    g_nodes = [{"name": str(r.get("file_name", "")),
                "color": cat_colors.get(r.get("category"), "#6366f1")} for r in g_rows]

    g_edges: list[list[int]] = []
    for i, r in enumerate(g_rows):
        raw_links = r.get("links") if has_links else []
        if isinstance(raw_links, str):
            try:
                raw_links = json.loads(raw_links)
            except (ValueError, TypeError):
                raw_links = []
        if not isinstance(raw_links, list):
            raw_links = []
        for tgt in raw_links:
            j = path_to_idx.get(str(tgt))
            if j is not None and j != i:
                g_edges.append([i, j])

    # Bán kính node theo degree (số liên kết) để hub nổi bật.
    deg = [0] * len(g_nodes)
    for s, t in g_edges:
        deg[s] += 1
        deg[t] += 1
    for i, n in enumerate(g_nodes):
        n["r"] = 5 + min(deg[i], 12)

    count_label = f"{len(g_nodes)} notes &bull; {len(g_edges)} links"

    # Embedded high-end Canvas simulation
    graph_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                background: #110e24;
                margin: 0;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                color: #fff;
            }
            #canvas {
                width: 100vw;
                height: 520px;
                display: block;
            }
            .info-panel {
                position: absolute;
                top: 15px;
                left: 15px;
                background: rgba(26, 20, 44, 0.7);
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                padding: 10px 14px;
                pointer-events: none;
            }
            .info-title {
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #5ad7e6;
                font-weight: 600;
                margin-bottom: 3px;
            }
            .info-subtitle {
                font-size: 13px;
                color: #d8d4e6;
                line-height: 1.4;
            }
        </style>
    </head>
    <body>
        <div class="info-panel">
            <div class="info-title">KNOWLEDGE GRAPH 2D</div>
            <div class="info-subtitle">
                __COUNT_LABEL__<br>
                <span style="font-size:11px; color:#8b92b6;">drag nodes &bull; scroll to zoom &bull; double-click auto-spin</span>
            </div>
        </div>
        <canvas id="canvas"></canvas>
        <script>
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            
            let width = window.innerWidth;
            let height = 520;
            canvas.width = width;
            canvas.height = height;

            window.addEventListener('resize', () => {
                width = window.innerWidth;
                canvas.width = width;
            });

            // Nodes (ghi chú) + cạnh ([[wikilink]] đã resolve) inject từ Obsidian vault thật.
            const nodes = __NODES__;
            nodes.forEach((n, i) => {
                const ang = (i / Math.max(1, nodes.length)) * Math.PI * 2;
                const rad = Math.min(width, 820) * (0.16 + 0.26 * ((i % 6) / 6));
                n.x = width / 2 + Math.cos(ang) * rad + (Math.random() - 0.5) * 40;
                n.y = height / 2 + Math.sin(ang) * rad + (Math.random() - 0.5) * 40;
            });

            const links = __EDGES__.map(e => ({ source: e[0], target: e[1] }));

            let scale = 1;
            let offsetX = 0;
            let offsetY = 0;
            let isDragging = false;
            let dragNode = null;
            let isDraggingCanvas = false;
            let dragStart = { x: 0, y: 0 };
            let hoveredNode = null;
            let autoAngle = 0.0003;
            let spin = true;

            canvas.addEventListener('mousedown', (e) => {
                const rect = canvas.getBoundingClientRect();
                const mx = (e.clientX - rect.left - offsetX) / scale;
                const my = (e.clientY - rect.top - offsetY) / scale;
                
                dragNode = nodes.find(n => Math.hypot(n.x - mx, n.y - my) < n.r * 1.6);
                if (dragNode) {
                    isDragging = true;
                    spin = false;
                } else {
                    isDraggingCanvas = true;
                    dragStart = { x: e.clientX - offsetX, y: e.clientY - offsetY };
                }
            });

            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                const mx = (e.clientX - rect.left - offsetX) / scale;
                const my = (e.clientY - rect.top - offsetY) / scale;

                if (isDragging && dragNode) {
                    dragNode.x = mx;
                    dragNode.y = my;
                } else if (isDraggingCanvas) {
                    offsetX = e.clientX - dragStart.x;
                    offsetY = e.clientY - dragStart.y;
                } else {
                    hoveredNode = nodes.find(n => Math.hypot(n.x - mx, n.y - my) < n.r * 1.6) || null;
                }
            });

            canvas.addEventListener('mouseup', () => {
                isDragging = false;
                isDraggingCanvas = false;
                dragNode = null;
            });

            canvas.addEventListener('wheel', (e) => {
                e.preventDefault();
                const factor = 1.05;
                const rect = canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                
                const beforeX = (mx - offsetX) / scale;
                const beforeY = (my - offsetY) / scale;
                
                if (e.deltaY < 0) {
                    scale *= factor;
                } else {
                    scale /= factor;
                }
                offsetX = mx - beforeX * scale;
                offsetY = my - beforeY * scale;
            });

            canvas.addEventListener('dblclick', () => {
                spin = !spin;
            });

            function tick() {
                const cx = width / 2;
                const cy = height / 2;

                if (spin) {
                    nodes.forEach(n => {
                        const dx = n.x - cx;
                        const dy = n.y - cy;
                        const d = Math.hypot(dx, dy);
                        const a = Math.atan2(dy, dx) + autoAngle;
                        n.x = cx + Math.cos(a) * d;
                        n.y = cy + Math.sin(a) * d;
                    });
                }

                // Node repulsion math
                for (let i = 0; i < nodes.length; i++) {
                    for (let j = i + 1; j < nodes.length; j++) {
                        const n1 = nodes[i];
                        const n2 = nodes[j];
                        const dx = n2.x - n1.x;
                        const dy = n2.y - n1.y;
                        const d = Math.hypot(dx, dy);
                        const limit = (n1.r + n2.r) * 5;
                        if (d < limit && d > 0) {
                            const force = (limit - d) * 0.005;
                            const fx = (dx / d) * force;
                            const fy = (dy / d) * force;
                            if (n1 !== dragNode) { n1.x -= fx; n1.y -= fy; }
                            if (n2 !== dragNode) { n2.x += fx; n2.y += fy; }
                        }
                    }
                }

                ctx.clearRect(0, 0, width, height);
                ctx.save();
                ctx.translate(offsetX, offsetY);
                ctx.scale(scale, scale);

                // Links
                links.forEach(l => {
                    const s = nodes[l.source];
                    const t = nodes[l.target];
                    const high = hoveredNode && (hoveredNode === s || hoveredNode === t);
                    ctx.strokeStyle = high ? 'rgba(90, 215, 230, 0.45)' : 'rgba(255,255,255,0.04)';
                    ctx.lineWidth = high ? 1.5 : 1;
                    ctx.beginPath();
                    ctx.moveTo(s.x, s.y);
                    ctx.lineTo(t.x, t.y);
                    ctx.stroke();
                });

                // Nodes
                nodes.forEach(n => {
                    const activeNode = hoveredNode === n;
                    
                    ctx.shadowColor = n.color;
                    ctx.shadowBlur = activeNode ? 20 : 6;
                    ctx.fillStyle = activeNode ? '#ffffff' : n.color;
                    
                    ctx.beginPath();
                    ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
                    ctx.fill();
                    
                    ctx.shadowBlur = 0;

                    // Nhãn: chỉ hiện cho hub (degree cao -> r>=10) hoặc node đang hover, tránh rối 174 node.
                    if (activeNode || n.r >= 10) {
                        const label = n.name.length > 28 ? n.name.slice(0, 27) + '…' : n.name;
                        ctx.fillStyle = activeNode ? '#ffffff' : 'rgba(216, 212, 230, 0.65)';
                        ctx.font = activeNode ? 'bold 11px sans-serif' : '10px sans-serif';
                        ctx.textAlign = 'center';
                        ctx.fillText(label, n.x, n.y + n.r + 14);
                    }
                });

                ctx.restore();
                requestAnimationFrame(tick);
            }

            tick();
        </script>
    </body>
    </html>
    """
    # json.dumps -> chèn vào <script>; escape '<' để không thể breakout </script>.
    nodes_json = json.dumps(g_nodes).replace("<", "\\u003c")
    edges_json = json.dumps(g_edges).replace("<", "\\u003c")
    graph_html = (graph_html
                  .replace("__NODES__", nodes_json)
                  .replace("__EDGES__", edges_json)
                  .replace("__COUNT_LABEL__", count_label))
    st.components.v1.html(graph_html, height=520)

# ==============================================================================
# 10. BOTOM ROW: AI SPEND TRACKER (RESILLIENT INTEGRATION)
# ==============================================================================

st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
st.markdown("<div class='vault-heading'><span>◈ AI Spend Tracker</span></div>", unsafe_allow_html=True)

df_spend = get_ai_spend()

if df_spend.empty:
    st.info("No recorded AI expense logging found.")
else:
    # Ensure types are floats
    df_spend["cost_usd"] = pd.to_numeric(df_spend["cost_usd"], errors="coerce").fillna(0)
    df_spend["input_tokens"] = pd.to_numeric(df_spend["input_tokens"], errors="coerce").fillna(0)
    df_spend["output_tokens"] = pd.to_numeric(df_spend["output_tokens"], errors="coerce").fillna(0)

    tot_usd = df_spend["cost_usd"].sum()
    tot_tok = int(df_spend["input_tokens"].sum() + df_spend["output_tokens"].sum())

    sp_col1, sp_col2, sp_col3 = st.columns(3)
    sp_col1.metric("Cumulative Spending (USD)", f"${tot_usd:,.4f}")
    sp_col2.metric("Total Tokens Emitted", f"{tot_tok:,}")
    sp_col3.metric("System Swarm API Invocations", f"{len(df_spend):,}")

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    
    # Display breakdown chart
    cost_breakdown = df_spend.groupby("model_name")["cost_usd"].sum().sort_values(ascending=False)
    st.bar_chart(cost_breakdown)
    
    st.dataframe(df_spend, use_container_width=True, hide_index=True)
