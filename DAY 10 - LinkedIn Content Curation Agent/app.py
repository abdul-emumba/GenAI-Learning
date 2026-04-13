"""
LinkedIn Content Curation System — Streamlit UI (v3)
Two-step flow: POST /plan → show plan → POST /execute → show results
"""

import base64
import json
import time

import httpx
import streamlit as st

st.set_page_config(
    page_title="LinkedIn Content Curation Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BACKEND_URL = "http://localhost:8000"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

:root {
  --ink: #09090B;
  --groq: #F55036;
  --li-blue: #0077B5;
  --li-light: #E8F4FD;
  --surface: #FFFFFF;
  --muted: #71717A;
  --border: #E4E4E7;
  --bg: #FAFAFA;
  --parallel-bg: #FFF7ED;
  --parallel-fg: #9A3412;
  --seq-bg: #EFF6FF;
  --seq-fg: #1D4ED8;
  --success-bg: #F0FDF4;
  --success-fg: #15803D;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--ink);
}

/* ── Hero ── */
.hero {
  background: linear-gradient(135deg, #09090B 0%, #18181B 60%, #27272A 100%);
  border: 1px solid #3F3F46;
  padding: 2.5rem 2.5rem 2rem;
  border-radius: 16px;
  margin-bottom: 1.75rem;
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: '';
  position: absolute;
  bottom: -60px; right: -60px;
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(245,80,54,0.25) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.hero-label {
  font-family: 'Syne', sans-serif;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--groq);
  margin-bottom: 0.6rem;
}
.hero h1 {
  font-family: 'Syne', sans-serif;
  font-size: 2rem;
  font-weight: 800;
  color: #FAFAFA;
  margin: 0 0 0.5rem;
  line-height: 1.2;
}
.hero p {
  color: #A1A1AA;
  font-size: 0.9rem;
  margin: 0;
  max-width: 520px;
}

/* ── Cards ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

/* ── Plan step row ── */
.plan-step {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  margin-bottom: 0.5rem;
  transition: box-shadow 0.15s;
}
.plan-step:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.step-circle {
  width: 30px; height: 30px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Syne', sans-serif;
  font-size: 0.78rem; font-weight: 700;
  flex-shrink: 0; color: white;
  background: var(--ink);
}
.step-circle.parallel { background: var(--groq); }
.step-circle.sequential { background: var(--li-blue); }
.step-tool { font-weight: 600; font-size: 0.9rem; color: var(--ink); }
.step-meta { font-size: 0.78rem; color: var(--muted); margin-top: 0.15rem; }
.badge {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  margin-left: 0.5rem;
}
.badge-parallel { background: var(--parallel-bg); color: var(--parallel-fg); }
.badge-sequential { background: var(--seq-bg); color: var(--seq-fg); }
.badge-done { background: var(--success-bg); color: var(--success-fg); }

/* ── Exec log ── */
.exec-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
}
.exec-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--success-bg); color: var(--success-fg);
  font-size: 0.7rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.exec-tool { font-weight: 600; flex: 1; }
.exec-ms { font-size: 0.75rem; color: var(--muted); white-space: nowrap; }

/* ── LinkedIn post card ── */
.li-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.75rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}
.li-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; }
.li-avatar {
  width: 46px; height: 46px; border-radius: 50%;
  background: linear-gradient(135deg, #0077B5, #00A0DC);
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 800; font-size: 1rem;
  font-family: 'Syne', sans-serif; flex-shrink: 0;
}
.li-name { font-weight: 600; font-size: 0.88rem; }
.li-sub { font-size: 0.75rem; color: var(--muted); }
.li-headline {
  font-family: 'Syne', sans-serif;
  font-size: 1.15rem; font-weight: 700;
  color: var(--ink); margin-bottom: 1rem; line-height: 1.4;
}
.li-body { color: #3F3F46; line-height: 1.8; font-size: 0.9rem; white-space: pre-line; }
.li-cta { margin-top: 0.9rem; color: var(--li-blue); font-weight: 500; font-size: 0.9rem; }
.li-tags { margin-top: 0.9rem; display: flex; flex-wrap: wrap; gap: 0.35rem; }
.li-tag {
  background: var(--li-light); color: var(--li-blue);
  padding: 0.2rem 0.65rem; border-radius: 999px;
  font-size: 0.78rem; font-weight: 500;
}

/* ── Metrics row ── */
.metrics { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }
.metric {
  flex: 1; background: var(--surface);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 0.9rem; text-align: center;
}
.metric-val {
  font-family: 'Syne', sans-serif;
  font-size: 1.5rem; font-weight: 800; color: var(--groq);
}
.metric-label { font-size: 0.72rem; color: var(--muted); margin-top: 0.2rem; }

/* ── Status banner ── */
.status-planning {
  background: #FFF7ED; border: 1px solid #FED7AA;
  border-radius: 10px; padding: 1rem 1.25rem;
  color: #9A3412; font-weight: 500; font-size: 0.88rem;
  margin-bottom: 1rem;
}
.status-executing {
  background: var(--seq-bg); border: 1px solid #BFDBFE;
  border-radius: 10px; padding: 1rem 1.25rem;
  color: var(--seq-fg); font-weight: 500; font-size: 0.88rem;
  margin-bottom: 1rem;
}

/* ── Section headers ── */
.section-title {
  font-family: 'Syne', sans-serif;
  font-size: 0.8rem; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--muted); margin: 1.5rem 0 0.75rem;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

def call_backend(method: str, path: str, payload: dict, timeout: int = 120) -> dict:
    url = f"{BACKEND_URL}{path}"
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.request(method, url, json=payload)
        if r.status_code != 200:
            st.error(f"Backend error {r.status_code} on {path}: {r.text[:400]}")
            st.stop()
        return r.json()
    except httpx.ConnectError:
        st.error(
            "❌ Cannot reach the backend. Start it with:\n\n"
            "```bash\ncd backend && uvicorn main:app --reload --port 8000\n```"
        )
        st.stop()

def render_plan(plan: dict, phase: str = "plan"):
    """Render the planner output with parallel/sequential badges."""
    steps = plan.get("steps", [])
    parallel_step_ids = {s["step"] for s in steps if not s.get("depends_on")}

    st.markdown('<div class="section-title">Execution Plan</div>', unsafe_allow_html=True)
    for s in steps:
        is_parallel = s["step"] in parallel_step_ids
        circle_class = "parallel" if is_parallel else "sequential"
        badge_class = "badge-parallel" if is_parallel else "badge-sequential"
        badge_label = "⚡ PARALLEL" if is_parallel else "🔗 SEQUENTIAL"
        deps_str = (
            f"depends on step{'s' if len(s['depends_on']) > 1 else ''} {', '.join(map(str, s['depends_on']))}"
            if s.get("depends_on") else "no dependencies"
        )
        st.markdown(f"""
        <div class="plan-step">
          <div class="step-circle {circle_class}">{s['step']}</div>
          <div style="flex:1">
            <div class="step-tool">
              {s['tool']}
              <span class="badge {badge_class}">{badge_label}</span>
            </div>
            <div class="step-meta">{deps_str}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)


def render_execution_log(execution_log: list[dict]):
    """Render per-node execution results with timing."""
    st.markdown('<div class="section-title">Tools Executed</div>', unsafe_allow_html=True)
    for entry in execution_log:
        tool_name = entry.get("tool", entry.get("node", "unknown"))
        duration = entry.get("duration_ms", 0)
        meta = entry.get("metadata", {})
        detail_parts = []
        if "result_count" in meta:
            detail_parts.append(f"{meta['result_count']} results")
        if "bullet_count" in meta:
            detail_parts.append(f"{meta['bullet_count']} bullets")
        if "headline" in meta:
            detail_parts.append(f'"{meta["headline"][:50]}…"')
        detail = " · ".join(detail_parts) if detail_parts else "completed"

        st.markdown(f"""
        <div class="exec-row">
          <div class="exec-num">✓</div>
          <div class="exec-tool">{tool_name}</div>
          <div style="font-size:0.8rem;color:#71717A;flex:2">{detail}</div>
          <div class="exec-ms">{duration}ms</div>
        </div>
        """, unsafe_allow_html=True)


def render_post(post: dict):
    """Render a LinkedIn-style post card."""
    hashtags_html = "".join(
        f'<span class="li-tag">#{h.lstrip("#")}</span>'
        for h in post.get("hashtags", [])
    )
    body = post.get("body", "").replace("<", "&lt;").replace(">", "&gt;")
    headline = post.get("headline", "").replace("<", "&lt;").replace(">", "&gt;")
    cta = post.get("call_to_action", "").replace("<", "&lt;").replace(">", "&gt;")

    st.markdown(f"""
    <div class="li-card">
      <div class="li-header">
        <div class="li-avatar">LI</div>
        <div>
          <div class="li-name">Your Name &nbsp;·&nbsp; <span style="color:#71717A">1st</span></div>
          <div class="li-sub">AI-generated draft · Just now</div>
        </div>
      </div>
      <div class="li-headline">{headline}</div>
      <div class="li-body">{body}</div>
      <div class="li-cta">{cta}</div>
      <div class="li-tags">{hashtags_html}</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("""
<div class="hero">
  <div class="hero-label">⚡ Powered by Groq · LangChain · LangGraph</div>
  <h1>LinkedIn Content Agent</h1>
  <p>Planner-driven, agentic content curation — two-step: plan first, execute second.</p>
</div>
""", unsafe_allow_html=True)


col_topic, col_opts = st.columns([3, 1])
with col_topic:
    topic = st.text_area(
        "What do you want to post about?",
        placeholder="e.g. Recent trends in GenAI agents for backend engineers",
        height=100,
        key="topic_input",
    )
with col_opts:
    audience = st.selectbox(
        "Audience",
        ["backend engineers", "product managers", "founders", "data scientists", "general tech"],
    )
    tone = st.selectbox(
        "Tone",
        ["professional yet engaging", "thought leadership", "conversational", "educational"],
    )

col_plan_btn, col_exec_btn = st.columns(2)
with col_plan_btn:
    plan_clicked = st.button("🧠 Step 1 — Generate Plan", use_container_width=True)
with col_exec_btn:
    exec_clicked = st.button(
        "⚡ Step 2 — Execute Plan",
        use_container_width=True,
        type="primary",
        disabled="plan_data" not in st.session_state,
    )

if plan_clicked:
    if not topic.strip():
        st.warning("Please enter a topic first.")
        st.stop()

    # Clear any previous results
    for key in ("plan_data", "execute_data"):
        st.session_state.pop(key, None)

    with st.spinner("🧠 Planner Agent is analysing your topic…"):
        st.markdown(
            '<div class="status-planning">🧠 Calling POST /plan — Groq Planner Agent thinking…</div>',
            unsafe_allow_html=True,
        )
        plan_resp = call_backend("POST", "/plan", {
            "topic": topic, "audience": audience, "tone": tone
        }, timeout=60)

    st.session_state["plan_data"] = plan_resp
    st.session_state["topic"] = topic
    st.session_state["audience"] = audience
    st.session_state["tone"] = tone
    st.rerun()


if "plan_data" in st.session_state and "execute_data" not in st.session_state:
    plan_data = st.session_state["plan_data"]
    st.divider()
    col_info, col_meta = st.columns([3, 1])
    with col_info:
        st.markdown(f"### 🗺️ Plan ready — Job `{plan_data['job_id']}`")
        st.caption(
            f"Topic: **{plan_data['topic']}** · "
            f"Audience: {plan_data['audience']} · "
            f"Planner took: {plan_data['duration_ms']}ms"
        )
    render_plan(plan_data["plan"])
    st.info("✅ Plan generated. Hit **Step 2 — Execute Plan** to run it.", icon="ℹ️")


if exec_clicked and "plan_data" in st.session_state:
    plan_data = st.session_state["plan_data"]

    with st.spinner("⚡ Executing plan — search, summarise, generate, edit, image…"):
        st.markdown(
            '<div class="status-executing">⚡ Calling POST /execute — LangGraph pipeline running…</div>',
            unsafe_allow_html=True,
        )
        exec_resp = call_backend("POST", "/execute", {
            "job_id": plan_data["job_id"],
            "topic": plan_data["topic"],
            "audience": plan_data["audience"],
            "tone": plan_data["tone"],
            "plan": plan_data["plan"],
        }, timeout=180)

    st.session_state["execute_data"] = exec_resp
    st.rerun()

if "execute_data" in st.session_state:
    data = st.session_state["execute_data"]
    plan_data = st.session_state.get("plan_data", {})

    post = data.get("post", {})
    image_b64 = data.get("image_base64")
    image_url = data.get("image_url")
    exec_log = data.get("execution_log", [])
    total_ms = data.get("total_duration_ms", 0)

    st.divider()

    tab_post, tab_image, tab_debug = st.tabs([
        "📝 LinkedIn Post",
        "🖼️ Generated Image",
        "🔍 Debug Panel",
    ])

    with tab_post:
        st.markdown(f"""
        <div class="metrics">
          <div class="metric">
            <div class="metric-val">{len(exec_log)}</div>
            <div class="metric-label">Nodes Run</div>
          </div>
          <div class="metric">
            <div class="metric-val">{total_ms // 1000}s</div>
            <div class="metric-label">Total Time</div>
          </div>
          <div class="metric">
            <div class="metric-val">{len(post.get('hashtags', []))}</div>
            <div class="metric-label">Hashtags</div>
          </div>
          <div class="metric">
            <div class="metric-val">{len(post.get('body', '').split())}</div>
            <div class="metric-label">Words</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        render_post(post)

        full_text = (
            f"{post.get('headline', '')}\n\n"
            f"{post.get('body', '')}\n\n"
            f"{post.get('call_to_action', '')}\n\n"
            + " ".join(f"#{h}" for h in post.get("hashtags", []))
        )
        st.download_button(
            "📋 Download Post as .txt",
            data=full_text,
            file_name="linkedin_post.txt",
            mime="text/plain",
        )

    with tab_image:
        if image_b64:
            img_bytes = base64.b64decode(image_b64)
            st.image(img_bytes, caption=f"Generated banner for: {data.get('topic', '')}", use_container_width=True)
            st.download_button(
                "⬇️ Download Banner (PNG)",
                data=img_bytes,
                file_name="linkedin_banner.png",
                mime="image/png",
            )
        elif image_url:
            st.image(image_url, caption=f"Generated banner for: {data.get('topic', '')}", use_container_width=True)
        else:
            st.info("Image generation was unavailable. Check Pollinations.ai connectivity.")

    with tab_debug:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 🗺️ Planner Output")
            st.caption(
                f"Job `{data['job_id']}` · "
                f"Planned in {plan_data.get('duration_ms', '?')}ms via POST /plan"
            )
            render_plan(data["plan"])

        with col_right:
            st.markdown("#### ⚙️ Execution Log")
            st.caption(f"Ran via POST /execute · Total: {total_ms}ms")
            render_execution_log(exec_log)

            # Parallel vs sequential summary
            plan_steps = data["plan"].get("steps", [])
            parallel_count = sum(1 for s in plan_steps if not s.get("depends_on"))
            sequential_count = len(plan_steps) - parallel_count
            st.markdown(f"""
            <div style="margin-top:1rem;padding:0.75rem 1rem;background:#F4F4F5;
                        border-radius:8px;font-size:0.82rem;color:#52525B">
              <strong>Execution order summary:</strong><br>
              <span style="color:var(--groq)">⚡ {parallel_count} parallel</span>
              steps ran first (no dependencies) ·
              <span style="color:#1D4ED8">🔗 {sequential_count} sequential</span>
              steps waited for upstream results
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        with st.expander("📦 Raw /plan response", expanded=False):
            st.json(plan_data)
        with st.expander("📦 Raw /execute response (no image bytes)", expanded=False):
            st.json({k: v for k, v in data.items() if k != "image_base64"})

    if st.button("🔄 Start Over", use_container_width=True):
        for key in ("plan_data", "execute_data", "topic", "audience", "tone"):
            st.session_state.pop(key, None)
        st.rerun()

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#A1A1AA;font-size:0.75rem'>"
    "LinkedIn Content Agent v3 &nbsp;·&nbsp; "
    "Groq llama-3.3-70b &nbsp;·&nbsp; LangChain LCEL &nbsp;·&nbsp; "
    "LangGraph StateGraph &nbsp;·&nbsp; FastAPI /plan + /execute &nbsp;·&nbsp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)