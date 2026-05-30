from html import escape

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CẤU HÌNH KẾT NỐI — đọc bí mật từ st.secrets, KHÔNG hardcode.
#    Streamlit chạy server-side nên key không lộ ra trình duyệt.
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

# Dashboard chỉ ĐỌC dữ liệu công khai đã được RLS bảo vệ -> dùng anon key.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# Client service_role RIÊNG để đọc dữ liệu nhạy cảm (ai_spend) — bỏ qua RLS.
# CHỈ chạy server-side (Streamlit server). Không bao giờ lộ key ra browser.
# Tách hẳn khỏi client anon; chỉ khởi tạo khi có key.
@st.cache_resource
def get_admin_client() -> Client | None:
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key or key == "your-service-role-key":
        return None
    return create_client(SUPABASE_URL, key)

st.set_page_config(page_title="Hermes OS", layout="wide", initial_sidebar_state="expanded")

# 2. GIAO DIỆN — Glassmorphism tím/indigo + accent cyan (đồng bộ ảnh mẫu)
st.markdown("""
    <style>
    /* Nền: gradient tím-indigo + glow tím trên đỉnh */
    /* Ẩn header trắng + toolbar Streamlit để theme liền mạch */
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    .block-container { padding-top: 2.2rem; }

    .stApp {
        background:
            radial-gradient(900px 500px at 60% -10%, rgba(120,70,200,0.35) 0%, rgba(120,70,200,0) 55%),
            radial-gradient(700px 400px at 12% 5%, rgba(80,40,140,0.30) 0%, rgba(80,40,140,0) 50%),
            linear-gradient(160deg, #14101f 0%, #0d0a16 45%, #08060d 100%);
        background-attachment: fixed;
        color: #d8d4e6;
    }

    /* Sidebar: gradient tím trong, viền kính */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(30,22,52,0.85) 0%, rgba(16,11,28,0.85) 100%);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* Card ghi chú: kính mờ, viền sáng mảnh, bo góc lớn */
    .memory-card {
        background: rgba(32,26,52,0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 10px;
        transition: border-color .18s ease, background .18s ease;
    }
    .memory-card:hover {
        background: rgba(46,36,74,0.55);
        border-color: rgba(120,200,220,0.35);
    }
    .file-title { font-size: 15px; font-weight: 600; color: #f3f1fb; margin-bottom: 3px; }
    .file-path { font-size: 12px; color: #7d7796; font-family: monospace; }
    .time-badge { font-size: 12px; color: #7d7796; text-align: right; }
    .sidebar-section-title {
        font-size: 11px; font-weight: 700; color: #5b5478;
        text-transform: uppercase; letter-spacing: 2px;
        margin-top: 20px; margin-bottom: 8px; padding-left: 10px;
    }

    /* Heading gradient cyan -> tím + thanh accent trái */
    .vault-heading {
        display: flex; align-items: center; gap: 10px;
        font-size: 20px; font-weight: 600; margin: 4px 0 14px 0;
    }
    .vault-heading::before {
        content: ""; width: 3px; height: 22px; border-radius: 3px;
        background: linear-gradient(180deg, #5ad7e6, #8a6cff);
        box-shadow: 0 0 10px rgba(90,215,230,0.6);
    }
    .vault-heading span {
        background: linear-gradient(90deg, #6fe0ec 0%, #9b8cff 100%);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Nút sidebar: dạng kính, hover phát sáng cyan */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.02);
        border: 1px solid transparent;
        border-radius: 12px;
        color: #c9c4dc; font-weight: 500;
        text-align: left; justify-content: flex-start;
        transition: all .18s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(90deg, rgba(90,200,220,0.14), rgba(120,90,230,0.10));
        border: 1px solid rgba(120,200,220,0.30);
        color: #ffffff;
        box-shadow: inset 3px 0 0 #5ad7e6;
    }
    [data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: inset 3px 0 0 #5ad7e6; color: #ffffff;
    }

    /* Ô tìm kiếm: kính */
    [data-testid="stTextInput"] input {
        background: rgba(28,22,46,0.55) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        color: #e7e3f3 !important;
    }

    /* Tab Recent/Notes/Omi: pill kính tím */
    [data-testid="stRadio"] label {
        background: rgba(40,30,66,0.45);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px; padding: 6px 14px; margin-right: 6px;
    }

    /* Metric (AI Spend) trên nền kính */
    [data-testid="stMetric"] {
        background: rgba(32,26,52,0.40);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; padding: 14px 16px;
    }

    /* Hàng AGENT: avatar tròn gradient + tên */
    .agent-row {
        display: flex; align-items: center; gap: 12px;
        padding: 9px 10px; margin-bottom: 4px;
        border-radius: 12px; cursor: pointer;
        border: 1px solid transparent;
        transition: all .18s ease;
    }
    .agent-row:hover {
        background: rgba(255,255,255,0.04);
        border-color: rgba(120,200,220,0.25);
    }
    .agent-avatar {
        width: 30px; height: 30px; border-radius: 50%;
        flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; color: #ffffff;
        box-shadow: 0 0 12px rgba(0,0,0,0.4);
    }
    .agent-name { font-size: 15px; font-weight: 500; color: #d8d4e6 !important; }
    .nav-link:focus, .nav-link:focus-visible { outline: none; color: inherit !important; }
    .av-claude   { background: linear-gradient(135deg, #ff9d4d, #ff6a3d); box-shadow: 0 0 14px rgba(255,130,60,0.45); }
    .av-openclaw { background: linear-gradient(135deg, #ff7eb3, #ff4d6d); box-shadow: 0 0 14px rgba(255,90,130,0.45); }
    .av-hermes   { background: linear-gradient(135deg, #5aa9ff, #4d6dff); box-shadow: 0 0 14px rgba(80,130,255,0.45); }

    /* Link điều hướng agent: bỏ gạch chân, hàng active sáng cyan */
    .nav-link, .nav-link:hover, .nav-link:visited { text-decoration: none; color: inherit; }
    .agent-row.active {
        background: linear-gradient(90deg, rgba(90,200,220,0.16), rgba(120,90,230,0.10));
        border-color: rgba(120,200,220,0.40);
        box-shadow: inset 3px 0 0 #5ad7e6;
    }
    .agent-row.active .agent-name { color: #ffffff; font-weight: 600; }
    .back-link {
        display: block;
        font-size: 13px; color: #8fd9e6 !important; padding: 8px 10px; margin-top: 6px;
        border-radius: 10px; transition: background .18s ease;
    }
    .back-link:hover { background: rgba(90,200,220,0.10); }

    /* Mục sidebar dạng link (Mission Control) */
    .side-item {
        display: block; padding: 9px 12px; margin-bottom: 4px;
        border-radius: 12px; color: #c9c4dc; font-weight: 500;
        border: 1px solid transparent; transition: all .18s ease;
    }
    .side-item:hover {
        background: linear-gradient(90deg, rgba(90,200,220,0.14), rgba(120,90,230,0.10));
        border-color: rgba(120,200,220,0.30); color: #ffffff;
    }
    .side-item.active {
        background: linear-gradient(90deg, rgba(90,200,220,0.16), rgba(120,90,230,0.10));
        border-color: rgba(120,200,220,0.40); box-shadow: inset 3px 0 0 #5ad7e6; color: #ffffff;
    }

    /* Thẻ mục tiêu Mission Control */
    .mc-card {
        background: rgba(32,26,52,0.45); backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.07); border-radius: 14px;
        padding: 16px 18px; margin-bottom: 12px;
    }
    .mc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .mc-title { font-size: 16px; font-weight: 600; color: #f3f1fb; }
    .status-badge {
        font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px;
        text-transform: uppercase; letter-spacing: .5px;
    }
    .st-todo { background: rgba(120,120,150,0.18); color: #9a96b5; }
    .st-prog { background: rgba(90,200,220,0.16); color: #7fdcea; }
    .st-done { background: rgba(90,220,140,0.16); color: #74e0a0; }
    .mc-bar { height: 8px; border-radius: 6px; background: rgba(255,255,255,0.06); overflow: hidden; }
    .mc-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #5ad7e6, #8a6cff); }
    .mc-meta { display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #7d7796; }
    </style>
""", unsafe_allow_html=True)

# Trạng thái điều hướng đọc từ URL query param (?nav=...)
AGENTS = {
    "claude":   {"label": "Claude",   "avatar": "✦", "cls": "av-claude",   "color": "#ff7a4d"},
    "openclaw": {"label": "OpenClaw", "avatar": "✸", "cls": "av-openclaw", "color": "#ff5a82"},
    "hermes":   {"label": "Hermes",   "avatar": "✈", "cls": "av-hermes",   "color": "#5a82ff"},
}
active = st.query_params.get("nav", "memory")


def agent_row_html(key: str) -> str:
    a = AGENTS[key]
    extra = " active" if active == key else ""
    # class dồn vào <a>; con là <span> (inline) để markdown không phá cấu trúc
    return (f"<a class='nav-link agent-row{extra}' target='_self' href='?nav={key}'>"
            f"<span class='agent-avatar {a['cls']}'>{a['avatar']}</span>"
            f"<span class='agent-name'>{a['label']}</span></a>")


# 3. SIDEBAR ĐIỀU HƯỚNG
with st.sidebar:
    st.markdown("<div style='padding: 10px 0px; font-weight:bold; color:#8b92b6;'>SELF</div>",
                unsafe_allow_html=True)
    mc_active = " active" if active == "mission" else ""
    st.markdown(f"<a class='nav-link side-item{mc_active}' target='_self' href='?nav=mission'>"
                f"▦ Mission Control</a>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section-title'>AGENTS</div>", unsafe_allow_html=True)
    st.markdown(agent_row_html("claude") + agent_row_html("openclaw") + agent_row_html("hermes"),
                unsafe_allow_html=True)
    if active != "memory":
        st.markdown("<a class='nav-link back-link' target='_self' href='?nav=memory'>"
                    "← Về Memory</a>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section-title'>SELF</div>", unsafe_allow_html=True)
    nav_goals = st.button("Goals", use_container_width=True)
    nav_seo = st.button("SEO", use_container_width=True)
    nav_studio = st.button("Studio", use_container_width=True)
    nav_journal = st.button("Journal", use_container_width=True)
    nav_memory = st.button("Memory", use_container_width=True)
    nav_guide = st.button("Build Guide", use_container_width=True)

# 3a. PANEL MISSION CONTROL — điều phối mục tiêu chiến dịch.
if active == "mission":
    st.markdown("<div class='vault-heading'><span>▦ Mission Control</span></div>",
                unsafe_allow_html=True)
    try:
        mc = pd.DataFrame(supabase.table("mission_control").select("*").order("id").execute().data)
    except Exception:
        mc = pd.DataFrame()

    if mc.empty:
        st.info("Chưa có mục tiêu nào trong Mission Control.")
    else:
        for col in ["progress_percent", "turns_used", "turn_budget"]:
            mc[col] = pd.to_numeric(mc[col], errors="coerce").fillna(0).astype(int)

        c1, c2, c3 = st.columns(3)
        c1.metric("Mục tiêu", len(mc))
        c2.metric("Tiến độ TB", f"{int(mc['progress_percent'].mean())}%")
        c3.metric("Turn đã dùng", f"{int(mc['turns_used'].sum())}/{int(mc['turn_budget'].sum())}")

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
                <span>{pct}% hoàn thành</span>
                <span>{int(r['turns_used'])}/{int(r['turn_budget'])} turns</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# 3b. PANEL AGENT — hiển thị khi chọn 1 agent, rồi dừng (không render vault).
if active in AGENTS:
    a = AGENTS[active]
    st.markdown(
        f"<div class='vault-heading'>"
        f"<div class='agent-avatar {a['cls']}' style='width:34px;height:34px;'>{a['avatar']}</div>"
        f"<span>{a['label']} — Agent</span></div>",
        unsafe_allow_html=True,
    )
    # Chi phí riêng của agent này (đọc bằng service_role, lọc theo model_name)
    admin = get_admin_client()
    if admin is None:
        st.warning("Chưa cấu hình SUPABASE_SERVICE_ROLE_KEY -> không đọc được chi phí agent.")
    else:
        try:
            resp = admin.table("ai_spend").select("*").ilike("model_name", f"%{active}%").execute()
            df_a = pd.DataFrame(resp.data)
        except Exception:
            df_a = pd.DataFrame()

        if df_a.empty:
            st.info(f"Chưa có dữ liệu chi phí cho agent **{a['label']}**.")
        else:
            df_a["cost_usd"] = pd.to_numeric(df_a["cost_usd"], errors="coerce").fillna(0)
            df_a["input_tokens"] = pd.to_numeric(df_a["input_tokens"], errors="coerce").fillna(0)
            df_a["output_tokens"] = pd.to_numeric(df_a["output_tokens"], errors="coerce").fillna(0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Chi phí (USD)", f"${df_a['cost_usd'].sum():,.4f}")
            c2.metric("Token", f"{int(df_a['input_tokens'].sum() + df_a['output_tokens'].sum()):,}")
            c3.metric("Lần gọi", f"{len(df_a):,}")
            st.dataframe(df_a, use_container_width=True, hide_index=True)
    st.stop()

# 4. MAIN PANEL
st.markdown("<div class='vault-heading'><span>◈ Memory — Obsidian Vault</span></div>",
            unsafe_allow_html=True)
search_query = st.text_input("Search", placeholder="Search 1,261 memories • 186 notes...",
                             label_visibility="collapsed")
tab_filter = st.radio("", ["Recent 12", "Notes", "Omi"], horizontal=True,
                      label_visibility="collapsed")

# 5. ĐỌC DỮ LIỆU + RENDER THẺ
try:
    response = supabase.table("obsidian_vault").select("*").execute()
    df_vault = pd.DataFrame(response.data)
except Exception:
    df_vault = pd.DataFrame()

if not df_vault.empty:
    current_category = "Recent" if "Recent" in tab_filter else ("Notes" if "Notes" in tab_filter else "Omi")
    df_filtered = df_vault[df_vault["category"] == current_category]

    if search_query:
        df_filtered = df_filtered[df_filtered["file_name"].str.contains(search_query, case=False, regex=False)]

    for _, row in df_filtered.iterrows():
        # escape giá trị tệp trước khi nhúng vào HTML (chống XSS)
        name = escape(str(row["file_name"]))
        path = escape(str(row["file_path"]))
        updated = escape(str(row["updated_at"]))
        card_html = f"""
        <div class="memory-card">
            <table style="width:100%; background:none; border:none; margin:0; padding:0;">
                <tr style="background:none; border:none;">
                    <td style="border:none; padding:0; text-align:left;">
                        <div class="file-title">{name}.md</div>
                        <div class="file-path">{path}</div>
                    </td>
                    <td style="border:none; padding:0; text-align:right; width:100px; vertical-align:top;">
                        <div class="time-badge">{updated}</div>
                    </td>
                </tr>
            </table>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("Hệ thống đang chờ tệp dữ liệu đồng bộ...")

# 6. PANEL CHI PHÍ AI — đọc ai_spend bằng service_role (KHÔNG dùng anon).
st.markdown("<div class='vault-heading'><span>◈ AI Spend</span></div>", unsafe_allow_html=True)

admin = get_admin_client()
if admin is None:
    st.warning("Chưa cấu hình SUPABASE_SERVICE_ROLE_KEY -> không đọc được chi phí. "
               "Thêm key vào .streamlit/secrets.toml (server-side).")
else:
    try:
        spend_resp = admin.table("ai_spend").select("*").order("created_at", desc=True).execute()
        df_spend = pd.DataFrame(spend_resp.data)
    except Exception:
        df_spend = pd.DataFrame()

    if df_spend.empty:
        st.info("Chưa có dữ liệu chi phí.")
    else:
        df_spend["cost_usd"] = pd.to_numeric(df_spend["cost_usd"], errors="coerce").fillna(0)
        df_spend["input_tokens"] = pd.to_numeric(df_spend["input_tokens"], errors="coerce").fillna(0)
        df_spend["output_tokens"] = pd.to_numeric(df_spend["output_tokens"], errors="coerce").fillna(0)

        total_cost = df_spend["cost_usd"].sum()
        total_tokens = int(df_spend["input_tokens"].sum() + df_spend["output_tokens"].sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng chi phí (USD)", f"${total_cost:,.4f}")
        c2.metric("Tổng token", f"{total_tokens:,}")
        c3.metric("Số lần gọi", f"{len(df_spend):,}")

        by_model = (df_spend.groupby("model_name")["cost_usd"].sum()
                    .sort_values(ascending=False))
        st.bar_chart(by_model)
        st.dataframe(df_spend, use_container_width=True, hide_index=True)
