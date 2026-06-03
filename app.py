import json
import os
from datetime import date, datetime, timezone
from html import escape
import httpx
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==============================================================================
# 1. DATABASE CONNECTIVITY & KEY RETRIEVAL
# ==============================================================================

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", "your-anon-key")

# Core client (Public tables: obsidian_vault, mission_control)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client (Sensitive tables: ai_spend)
@st.cache_resource
def get_admin_client() -> Client | None:
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key or key == "your-service-role-key" or key == "<service_role key>":
        return None
    try:
        return create_client(SUPABASE_URL, key)
    except Exception:
        return None

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
        "num": "IV", "desc": "Nous Research agent. Sessions, skills, kanban — and a chat line.",
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
        "label": "Free Claude Code", "avatar": "▼", "cls": "av-freeclaw", 
        "num": "VIII", "desc": "Zero per-token cost local Claude harness. Routing proxied intelligence with no operational overhead.",
        "color": "#34d399"
    }
}

SELF_SECTIONS = {
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
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(MOCK_VAULT_DATA)

def get_mission_control() -> pd.DataFrame:
    try:
        res = supabase.table("mission_control").select("*").order("id").execute()
        if res.data:
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
            if res.data:
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
# 6. LAYOUT RENDERING FUNCTIONS
# ==============================================================================

def render_custom_header(num: str, section_type: str, section_name: str, desc: str) -> None:
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
                    13:10 LOCAL &bull; BANGKOK
                </div>
                <a href="#" class="nav-link" style="display: flex; align-items: center; gap: 6px; font-family: 'Outfit', sans-serif; font-size: 13px; color: #a5a1c0 !important; background: rgba(30,24,52,0.5); border: 1px solid rgba(255,255,255,0.05); padding: 6px 14px; border-radius: 8px; text-decoration: none; transition: all 0.2s;">
                    <span style="font-size: 11px; background:rgba(255,255,255,0.08); padding:1px 5px; border-radius:4px; margin-right:2px;">⌘K</span> Command palette
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
active = st.query_params.get("nav", "memory")

with st.sidebar:
    # Top Branding Header
    st.markdown("""
        <div style="padding: 10px 10px 20px 10px; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <div style="font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 500; color: #7d7796; letter-spacing: 1.5px; text-transform: uppercase;">LOCAL &bull; BANGKOK</div>
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
        
        # HTML styled horizontal sub-tab bar
        tabs = [
            {"id": "chat", "label": "Chat", "icon": "💬"},
            {"id": "goal", "label": "Goal Mode", "icon": "🎯"},
            {"id": "workspace", "label": "Workspace", "icon": "📁"},
            {"id": "control", "label": "Control Room", "icon": "🎛️"},
        ]
        tabs_html = "".join([
            f'<a class="nav-link" target="_self" href="?nav=hermes&tab={t["id"]}" style="text-decoration:none; display:inline-block; margin-right:5px;">'
            f'<div class="sub-tab-pill {"active" if tab == t["id"] else ""}">{t["icon"]} {t["label"]}</div>'
            f'</a>'
            for t in tabs
        ])
        st.markdown(f'<div style="display:flex; gap:5px; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:10px; flex-wrap:wrap;">{tabs_html}</div>', unsafe_allow_html=True)
        
        if tab == "chat":
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            url = st.secrets.get("HERMES_API_URL")
            key = st.secrets.get("HERMES_API_KEY")
            
            # Sub-header
            st.markdown("<div style='font-size:16px; font-weight:600; color:#ffffff; margin-bottom:12px;'>✦ Live Chat Terminal</div>", unsafe_allow_html=True)
            
            if not url:
                # Provide gorgeous preview messages inside chat if no API is available
                if "hermes_msgs" not in st.session_state:
                    st.session_state.hermes_msgs = [
                        {"role": "assistant", "content": "### Suggested Long-Tail Phrases for YouTube/SEO Content\n- \"AI Profit Boardroom worth it\"\n- \"how I built a $100k MRR AI community on Skool\"\n- \"n8n automations inside AI Profit Boardroom\"\n- \"Hermes Agent setup for AIPB members\"\n- \"daily AI coaching community\"\n- \"free AI Money Lab to paid AIPB\"\n\nThese directly mirror the language, value props, funnel mechanics, and tech stack documented in your AIPB Operations, AIPB Growth, and Funnel Strategy notes.\nFocus on the freemium path (YouTube -> AI Money Lab -> AIPB) and the specific value stack (n8n vault, Daily QA, live calls, guarantees) for the strongest alignment with what you're already tracking in the vault."}
                    ]
            
            # Render chat
            for m in st.session_state.get("hermes_msgs", []):
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
            
            prompt = st.chat_input("Message Hermes...")
            if prompt:
                st.session_state.setdefault("hermes_msgs", []).append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Hermes is reasoning..."):
                        if url:
                            try:
                                headers = {"Authorization": f"Bearer {key}"} if key else {}
                                r = httpx.post(f"{url.rstrip('/')}/chat", json={"message": prompt}, headers=headers, timeout=180)
                                r.raise_for_status()
                                reply = r.json().get("reply", "(empty)")
                            except Exception as e:
                                reply = f"⚠️ Hermes API error: {e}"
                        else:
                            reply = f"Hermes processing query: \"{prompt}\". (Live VPS shim connection pending API configuration in secrets)."
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
                                <span style="font-size:13.5px; font-weight:500; color:#ffffff;">{g['title']}</span>
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
                    # Renders active logs stream
                    st.markdown(f"""
                    <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="font-size:14.5px; font-weight:600; color:#ffffff;">{active_goal['title']}</span>
                            <span style="font-size:11px; color:#5ad7e6; font-weight:500;">{active_goal['progress']}% complete</span>
                        </div>
                        <div style="font-size:12px; color:#8b92b6; line-height:1.4; margin-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:10px;">
                            <b>Goal Target:</b> {active_goal['prompt']}
                        </div>
                        
                        <div style="font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; display:flex; align-items:center; gap:5px;">
                            <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#34d399;"></span> Console Thoughts Log Stream
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Console logs body
                    logs_html = "".join([f"<div style='margin-bottom:6px; line-height:1.4;'><span style='color:#7d7796;'>[{active_goal['created_at']}]</span> {escape(l)}</div>" for l in active_goal["logs"]])
                    
                    st.markdown(f"""
                    <div style="background: rgba(13,9,26,0.85); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 15px; font-family: 'JetBrains Mono', monospace; font-size: 11.5px; color: #34d399; min-height: 250px; max-height: 320px; overflow-y: auto; box-shadow: inset 0 0 15px rgba(0,0,0,0.5);">
                        {logs_html}
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
            
        elif tab == "workspace":
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            
            # Read Buckets and Files via query parameters for 100% stable state
            selected_bucket = st.query_params.get("bucket", "apps")
            
            col_b, col_f, col_p = st.columns([1, 1.3, 2.7])
            
            with col_b:
                st.markdown("<div style='font-size:11px; font-weight:700; color:#5b5478; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Buckets</div>", unsafe_allow_html=True)
                buckets = [
                    {"id": "goal", "label": "Goal Mode", "icon": "🎯"},
                    {"id": "apps", "label": "Apps", "icon": "📱"},
                    {"id": "video", "label": "Video", "icon": "🎥"},
                    {"id": "images", "label": "Images", "icon": "🖼️"},
                    {"id": "audio", "label": "Audio", "icon": "🎵"},
                    {"id": "sandboxes", "label": "Sandboxes", "icon": "📦"},
                    {"id": "pastes", "label": "Pastes", "icon": "📋"},
                ]
                
                for b in buckets:
                    is_active = (b["id"] == selected_bucket)
                    active_class = "active" if is_active else ""
                    st.markdown(f"""
                    <a class="nav-link side-item {active_class}" target="_self" href="?nav=hermes&tab=workspace&bucket={b['id']}" style="display:block; text-decoration:none;">
                        {b['icon']} {b['label']}
                    </a>
                    """, unsafe_allow_html=True)
                        
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
                    st.markdown("""
                    <div style="background: linear-gradient(160deg, #151125 0%, #0c0817 100%); border: 1px solid rgba(255,255,255,0.06); border-radius: 0 0 12px 12px; padding: 25px; min-height: 420px; color: #d8d4e6; font-family: 'Outfit', sans-serif;">
                        
                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                            <span style="color:#fb7185; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:1px;">★ Get the full Agent OS install + every layer in this guide inside the</span>
                            <h4 style="margin: 5px 0 15px 0; color:#ffffff; font-size:17px; font-weight:600;">AI Profit Boardroom</h4>
                            <a href="#" style="display:inline-block; background: linear-gradient(135deg, #ff9d4d, #ff6a3d); color:#ffffff; font-weight:700; font-size:13px; padding: 8px 22px; border-radius: 8px; text-decoration:none; box-shadow: 0 0 15px rgba(255,106,61,0.35);">
                                Join AIPB →
                            </a>
                        </div>
                        
                        <div style="border-left: 2px solid #5ad7e6; padding-left: 15px; margin-bottom: 25px;">
                            <span style="font-family: serif; font-size: 13px; font-style: italic; color: #5ad7e6;">Mistake II</span>
                            <h3 style="margin: 2px 0 8px 0; color:#ffffff; font-size:17px; font-weight:500;">Paying for everything before exploring free</h3>
                            <p style="font-size:13px; color:#8b92b6; line-height:1.5; margin:0;">
                                $249/mo for Ahrefs. $45/mo for Frase. $30/mo for Midjourney. $20/mo for ChatGPT Plus. $20/mo for Claude Pro. $11/mo for ElevenLabs. <b>~$375/mo in tools</b> before I'd produced a single dollar that month. Then Owl Alpha showed up free on OpenRouter, Hermes was open-source from day one, and Free Claude Code routed the same Claude harness through whatever model I wanted at zero per-token cost.
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
                    """, unsafe_allow_html=True)
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
        tab_setup, tab_spend = st.tabs(["Setup & Tunnel", "AI Spend"])

        with tab_setup:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: rgba(30, 24, 52, 0.45); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 30px 25px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
                <div style="font-size: 48px; margin-bottom: 12px; filter: drop-shadow(0 0 12px rgba(52, 211, 153, 0.5)); line-height: 1;">▼</div>
                <h3 style="color:#ffffff; margin: 0 0 10px 0; font-family:'Outfit', sans-serif; font-size: 22px; font-weight: 500; letter-spacing: -0.5px;">
                    Free Claude Code — Local Proxy
                </h3>
                <p style="color:#a5a1c0; font-size:14.5px; max-width:680px; margin: 0 auto 18px auto; line-height:1.65; font-weight: 300;">
                    Routes Claude Code traffic qua 17 backend miễn phí (NVIDIA NIM, OpenRouter, Gemini, DeepSeek, Groq, Ollama…).
                    <b>Chạy local trên máy bạn</b>, không host trên cloud — dùng <code>cloudflared</code> để tunnel ra public URL rồi dán vào đây để app này xác minh kết nối.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>1. CÀI TRÊN MÁY LOCAL (PowerShell, chạy 1 lần)</div>", unsafe_allow_html=True)
            st.code("irm https://github.com/Alishahryar1/free-claude-code/blob/main/scripts/install.ps1?raw=1 | iex", language="powershell")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>2. KHỞI ĐỘNG PROXY (port 8082, để chạy nền)</div>", unsafe_allow_html=True)
            st.code("fcc-server", language="powershell")

            st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 18px 0 8px 0; font-weight:500;'>3. MỞ TUNNEL RA PUBLIC (Quick Tunnel — không cần tài khoản Cloudflare)</div>", unsafe_allow_html=True)
            st.code("cloudflared tunnel --url http://127.0.0.1:8082", language="powershell")
            st.caption("Sao chép URL `https://<...>.trycloudflare.com` xuất hiện trong output rồi dán vào ô bên dưới.")

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            col_in, col_btn = st.columns([3, 1])
            with col_in:
                proxy_url = st.text_input(
                    "Public tunnel URL",
                    value=st.session_state.get("fcc_tunnel_url", ""),
                    placeholder="https://<random>.trycloudflare.com",
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
                with st.spinner("Pinging proxy..."):
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
                        <div style="color:#34d399; font-weight:600; font-size:14px; margin-bottom:4px;">✓ Tunnel reachable (HTTP {payload})</div>
                        <div style="color:#a5a1c0; font-size:12.5px;">Proxy tại <code>{escape(url)}</code> đang phản hồi. Copy env vars bên dưới vào VSCode/Claude Code để bắt đầu route traffic.</div>
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
                st.markdown("<div style='font-size:13px; color:#a5a1c0; letter-spacing:0.5px; margin: 22px 0 8px 0; font-weight:500;'>4. DÁN VÀO CLAUDE CODE / VSCODE</div>", unsafe_allow_html=True)
                env_block = (
                    "{\n"
                    f'  "ANTHROPIC_BASE_URL": "{tunnel_url}",\n'
                    '  "ANTHROPIC_AUTH_TOKEN": "freecc",\n'
                    '  "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",\n'
                    '  "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "190000"\n'
                    "}"
                )
                st.code(env_block, language="json")
                st.caption("VSCode: Settings → claude-code.environmentVariables → Edit in settings.json. Claude CLI: chạy `fcc-claude`.")

        with tab_spend:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            df_a = get_ai_spend(active)
            if df_a.empty:
                st.info(f"No logged token cost events for agent: **{a['label']}**. (Free Claude Code là local proxy — chi phí được track ở Admin UI của proxy, không qua bảng Supabase này.)")
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
    render_custom_header("X", "SELF", "SEO Pipeline", "Automated high-quality transcript to article SEO engine.")
    
    # Custom HTML header action buttons bar
    st.markdown("""
    <div style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:1.5rem; justify-content:space-between; align-items:center;">
        <div style="display:flex; gap:8px;">
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; font-weight:600; background:rgba(52,211,153,0.12); border:1px solid rgba(52,211,153,0.25); color:#34d399 !important; padding:8px 16px; border-radius:8px; font-size:13px; text-decoration:none;">
                ▶ Generate
            </a>
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:#8b92b6 !important; padding:8px 16px; border-radius:8px; font-size:13px; text-decoration:none;">
                ☁ Deploy
            </a>
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:#8b92b6 !important; padding:8px 16px; border-radius:8px; font-size:13px; text-decoration:none;">
                🕒 History
            </a>
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:#8b92b6 !important; padding:8px 16px; border-radius:8px; font-size:13px; text-decoration:none;">
                📚 Transcripts
            </a>
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:#8b92b6 !important; padding:8px 16px; border-radius:8px; font-size:13px; text-decoration:none;">
                🏆 Skill
            </a>
        </div>
        <div style="display:flex; gap:8px;">
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:#a5a1c0 !important; padding:8px 14px; border-radius:8px; font-size:13px; text-decoration:none;">
                Setup Guide
            </a>
            <a href="#" class="nav-link" style="display:inline-flex; align-items:center; gap:6px; background:rgba(90,215,230,0.12); border:1px solid rgba(90,215,230,0.25); color:#5ad7e6 !important; padding:8px 14px; border-radius:8px; font-size:13px; text-decoration:none;">
                📥 SEO Pack (.zip)
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(30,24,52,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px 22px 5px 22px; margin-bottom:1.5rem;">
        <h4 style="margin: 0 0 18px 0; font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; display: flex; align-items: center; gap: 8px;">
            <span style="color:#5ad7e6; font-size:14px;">✨</span> Generate 5 unique articles for all 5 sites
        </h4>
    """, unsafe_allow_html=True)
    
    col_k, col_s = st.columns(2)
    with col_k:
        st.text_input("TARGET KEYWORD", value="e.g. hermes mcp server", key="seo_kw")
    with col_s:
        st.text_input("FILE SLUG", value="hermes-mcp-server", key="seo_slug")
        
    st.markdown("<div style='font-size: 11px; font-weight: 700; color: #5b5478; text-transform: uppercase; letter-spacing: 1.5px; margin: 20px 0 10px 0;'>Source Transcript</div>", unsafe_allow_html=True)
    
    trans_tab = st.radio("Source Transcript Mode", ["PICK EXISTING", "PASTE NEW"], horizontal=True, label_visibility="collapsed")
    
    if trans_tab == "PICK EXISTING":
        transcripts = [
            {"name": "ai-money-lab-shared", "size": "3.1 KB"},
            {"name": "openclaw-ai-agent-community", "size": "2.8 KB"},
            {"name": "telegram-ai-agent", "size": "2.5 KB"},
            {"name": "best-ai-agent-community", "size": "1.9 KB"},
            {"name": "how-to-make-money-building-ai-agent", "size": "2.5 KB"},
            {"name": "how-to-make-money-with-artificial-intelligence", "size": "2.3 KB"},
            {"name": "openclaw-computer-use", "size": "2.7 KB"}
        ]
        
        selected_trans = st.session_state.get("selected_transcript", "ai-money-lab-shared")
        
        # Grid select list
        for t in transcripts:
            is_active = (t["name"] == selected_trans)
            row_bg = "background: rgba(90,215,230,0.12); border-color: rgba(90,215,230,0.3);" if is_active else ""
            
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 6px; {row_bg}">
                <span style="font-size:13px; font-family:'JetBrains Mono', monospace; color:#e2e8f0;">{t['name']}</span>
                <span style="font-size:11px; color:#8b92b6;">{t['size']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Pick " + t["name"], key=f"pick_{t['name']}", use_container_width=True):
                st.session_state["selected_transcript"] = t["name"]
                st.rerun()
    else:
        st.text_area("Source Transcript Payload", placeholder="Paste Zoom/YouTube audio raw transcripts here to parse...")
        
    st.markdown("</div>", unsafe_allow_html=True) # end container
    
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    
    # Bottom toggle block
    col_t, col_desc = st.columns([1, 4])
    with col_t:
        st.toggle("Auto-deploy after generate", value=True, key="seo_auto_deploy")
    with col_desc:
        st.markdown("<div style='font-size: 13px; color: #8b92b6; line-height:1.4; margin-top:2px;'><b>Auto-deploy after generate</b><br>As soon as Claude finishes writing, all 5 sites build + deploy in parallel.</div>", unsafe_allow_html=True)
        
    st.stop()

# ------------------------------------------------------------------------------
# VIEW: KANBAN BOARD VIEW (Roman Numeral XIII - Matches User Screenshot)
# ------------------------------------------------------------------------------
if active == "kanban":
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
# VIEW: ALL OTHER SELF SECTIONS (fallback cho SELF section chưa có view riêng)
# ------------------------------------------------------------------------------
if active in SELF_SECTIONS and active != "memory":
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
