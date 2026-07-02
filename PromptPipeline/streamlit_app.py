"""Streamlit UI — Prompt Pipeline (Customer Support Ticket).

Layout mirrors the reference design:
  • Top header bar with app name + subtitle
  • Horizontal stage stepper (Understand → Reason → Produce)
  • Two-column body:
      LEFT  — PIPELINE panel: dropdown, current stage card, prompt preview, Run stage button
      RIGHT — STAGE OUTPUTS panel: completed stage cards + live output viewer
"""

import json
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Prompt Pipeline",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset / base ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 2rem !important; max-width: 1200px; }

/* ── Top header bar ── */
.top-bar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.85rem 0 0.6rem;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 1.2rem;
}
.top-bar-left  { display:flex; align-items:center; gap:0.55rem; }
.top-bar-logo  {
    background:#fbbf24; border-radius:50%;
    width:28px; height:28px; display:inline-flex;
    align-items:center; justify-content:center;
    font-size:0.9rem; font-weight:900; color:#78350f;
}
.top-bar-title { font-size:1.05rem; font-weight:700; color:#0f172a; }
.top-bar-right { font-size:0.78rem; color:#94a3b8; }

/* ── Stage stepper ── */
.stepper {
    display:flex; align-items:center; gap:0;
    margin-bottom: 1.6rem;
}
.step-item { display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }
.step-circle {
    width:32px; height:32px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:0.8rem; font-weight:700; z-index:1;
}
.step-done   { background:#22c55e; color:white; }
.step-active { background:#3b82f6; color:white; box-shadow:0 0 0 3px #bfdbfe; }
.step-future { background:#e2e8f0; color:#94a3b8; }
.step-label  { font-size:0.72rem; font-weight:600; margin-top:0.3rem; color:#64748b; }
.step-label.active { color:#1d4ed8; }
.step-line {
    position:absolute; top:16px; left:calc(50% + 16px);
    width:calc(100% - 32px); height:2px; background:#e2e8f0; z-index:0;
}
.step-line.done { background:#22c55e; }

/* ── Panel headers ── */
.panel-header {
    font-size:0.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.1em; color:#94a3b8; margin-bottom:0.75rem;
}

/* ── Pipeline selector ── */
.pipeline-select-label {
    font-size:0.75rem; color:#64748b; font-weight:600; margin-bottom:0.3rem;
}

/* ── Stage card (left panel) ── */
.stage-card {
    border:1px solid #e2e8f0; border-radius:10px;
    padding:1rem 1.1rem; margin-bottom:0.9rem;
    background:white;
}
.stage-card-title {
    font-size:0.78rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.07em; color:#6366f1; margin-bottom:0.15rem;
}
.stage-card-desc { font-size:0.92rem; font-weight:700; color:#0f172a; margin-bottom:0.75rem; }

.input-label {
    font-size:0.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.08em; color:#94a3b8; margin-bottom:0.35rem;
}
.json-block {
    background:#f1f5f9; border-radius:7px; padding:0.6rem 0.8rem;
    font-family:'Courier New', monospace; font-size:0.78rem;
    color:#334155; white-space:pre-wrap; margin-bottom:0.75rem;
    border:1px solid #e2e8f0; max-height:140px; overflow-y:auto;
}
.prompt-block {
    background:#f8fafc; border-radius:7px; padding:0.75rem 0.9rem;
    font-size:0.84rem; color:#475569; line-height:1.6;
    border:1px solid #e2e8f0; white-space:pre-wrap;
    max-height:180px; overflow-y:auto; margin-bottom:0.9rem;
}

/* ── Output cards (right panel) ── */
.output-card {
    border:1px solid #e2e8f0; border-radius:10px;
    padding:0.75rem 1rem; margin-bottom:0.6rem;
    background:white; display:flex; align-items:center; gap:0.75rem;
}
.output-card.active-card { border-color:#3b82f6; background:#eff6ff; }
.output-card.complete-card { border-color:#22c55e; }
.output-icon {
    width:32px; height:32px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    font-size:0.85rem; font-weight:700;
}
.icon-done   { background:#dcfce7; color:#16a34a; }
.icon-active { background:#dbeafe; color:#2563eb; }
.icon-future { background:#f1f5f9; color:#94a3b8; }
.output-card-title { font-size:0.88rem; font-weight:700; color:#0f172a; }
.output-card-sub   { font-size:0.74rem; color:#94a3b8; }

/* ── Live output box ── */
.live-header {
    font-size:0.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.09em; color:#94a3b8; margin:1rem 0 0.4rem;
}
.live-label {
    display:inline-block; background:#fef9c3; color:#854d0e;
    border-radius:4px; padding:0.1rem 0.5rem;
    font-size:0.7rem; font-weight:700; margin-bottom:0.5rem;
}
.live-label.green { background:#dcfce7; color:#166534; }
.live-box {
    background:#0f172a; border-radius:8px;
    padding:1rem 1.1rem; font-family:'Courier New',monospace;
    font-size:0.8rem; color:#94a3b8; white-space:pre-wrap;
    max-height:260px; overflow-y:auto; line-height:1.6;
}
.live-box .key   { color:#7dd3fc; }
.live-box .str   { color:#86efac; }
.live-box .num   { color:#fca5a5; }

/* ── Reply box ── */
.reply-box {
    background:#f0fdf4; border:1px solid #bbf7d0;
    border-radius:9px; padding:1rem 1.2rem;
    font-size:0.92rem; line-height:1.75; color:#14532d;
    white-space:pre-wrap;
}

/* ── Status pill ── */
.status-pill {
    display:inline-block; border-radius:6px;
    padding:0.3rem 0.9rem; font-size:0.78rem; font-weight:700;
    float:right; margin-top:-2px;
}
.pill-running  { background:#fef3c7; color:#b45309; }
.pill-complete { background:#dcfce7; color:#166534; }
.pill-idle     { background:#f1f5f9; color:#64748b; }

/* ── Run button override ── */
div[data-testid="stButton"] > button {
    border-radius: 7px !important;
}

/* ── Divider ── */
.h-rule { border:none; border-top:1px solid #e2e8f0; margin:0.6rem 0 1rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("stage1_output", None),
    ("stage2_output", None),
    ("stage3_output", None),   # plain string
    ("active_stage", 1),       # 1, 2, or 3 — which stage is shown / next to run
    ("pipeline_status", "idle"),  # idle | running | complete
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# Top bar
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <div class="top-bar-left">
    <span class="top-bar-logo">⚡</span>
    <span class="top-bar-title">Prompt Pipeline</span>
  </div>
  <div class="top-bar-right">GenAI Lab · Customer Support Pipeline</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Stage stepper
# ─────────────────────────────────────────────────────────────────────────────
stages = ["Understand", "Reason", "Produce"]
active = st.session_state.active_stage  # 1-indexed

def _circle_cls(i):
    if i < active:   return "step-done"
    if i == active:  return "step-active"
    return "step-future"

def _label_cls(i):
    return "active" if i == active else ""

def _line_cls(i):
    return "done" if i < active else ""

stepper_html = '<div class="stepper">'
for idx, name in enumerate(stages, start=1):
    line = f'<div class="step-line {_line_cls(idx)}"></div>' if idx < len(stages) else ""
    stepper_html += f"""
    <div class="step-item">
      <div class="step-circle {_circle_cls(idx)}">{idx}</div>
      <div class="step-label {_label_cls(idx)}">{name}</div>
      {line}
    </div>"""
stepper_html += "</div>"
st.markdown(stepper_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
STAGE_META = {
    1: {
        "tag":   "STAGE 1 · UNDERSTAND — STRUCTURED EXTRACTION",
        "title": "Extract ticket fields as JSON.",
        "prompt_preview": (
            "You are a customer support data specialist.\n"
            "Read the ticket carefully. Extract ONLY factual information.\n"
            "Return valid JSON with:\n"
            "{ customer, order_id, issue, days_waiting, sentiment }"
        ),
    },
    2: {
        "tag":   "STAGE 2 · REASON — CHAIN-OF-THOUGHT",
        "title": "Decide priority & who handles it.",
        "prompt_preview": (
            "Think step by step. From the facts below,\n"
            "decide priority (P1–P3) and which team\n"
            "handles it, then return JSON:\n"
            "{ priority, route, why }"
        ),
    },
    3: {
        "tag":   "STAGE 3 · PRODUCE — GOAL + CONSTRAINTS",
        "title": "Draft the customer reply.",
        "prompt_preview": (
            "Write a reply that fixes the issue. Warm,\n"
            "under 120 words, no promises we can't\n"
            "keep. Acknowledge the delay and\n"
            "give a next step."
        ),
    },
}

def _input_for_stage(stage_num):
    """Return the input dict/string shown in the INPUT FROM STAGE N block."""
    if stage_num == 1:
        return None   # raw ticket — shown separately
    if stage_num == 2:
        return st.session_state.stage1_output
    if stage_num == 3:
        s1 = st.session_state.stage1_output or {}
        s2 = st.session_state.stage2_output or {}
        merged = {**s1, **s2}
        return merged
    return None

def _completed(stage_num):
    return {
        1: st.session_state.stage1_output is not None,
        2: st.session_state.stage2_output is not None,
        3: st.session_state.stage3_output is not None,
    }.get(stage_num, False)

def _output_for_stage(stage_num):
    if stage_num == 1: return st.session_state.stage1_output
    if stage_num == 2: return st.session_state.stage2_output
    if stage_num == 3: return st.session_state.stage3_output
    return None

def _format_json_html(obj):
    """Simple colour-coded JSON for the live box."""
    text = json.dumps(obj, indent=2) if isinstance(obj, dict) else str(obj)
    return text

# ─────────────────────────────────────────────────────────────────────────────
# Main body — two columns
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

# ══════════════════════════════════════════════════════════════
# LEFT — PIPELINE panel
# ══════════════════════════════════════════════════════════════
with col_left:
    st.markdown('<div class="panel-header">PIPELINE</div>', unsafe_allow_html=True)

    # Pipeline selector (decorative — always "Support ticket triage")
    st.selectbox(
        "Pipeline",
        ["Support ticket triage"],
        label_visibility="collapsed",
        key="pipeline_select",
    )

    st.markdown("<hr class='h-rule'>", unsafe_allow_html=True)

    cur = st.session_state.active_stage
    meta = STAGE_META[cur]

    # ── Stage card ──
    st.markdown(f"""
    <div class="stage-card">
      <div class="stage-card-title">{meta['tag']}</div>
      <div class="stage-card-desc">{meta['title']}</div>
    """, unsafe_allow_html=True)

    # Input block
    inp = _input_for_stage(cur)
    if cur == 1:
        st.markdown('<div class="input-label">INPUT — SUPPORT TICKET</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="input-label">INPUT FROM STAGE {cur-1}</div>', unsafe_allow_html=True)

    if inp is not None:
        inp_text = json.dumps(inp, indent=2)
        # Truncate for display
        if len(inp_text) > 300:
            inp_text = inp_text[:300] + "\n  ..."
        st.markdown(f'<div class="json-block">{inp_text}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="json-block"><em style="color:#94a3b8">Ticket text will be loaded from the input box below</em></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close stage-card

    # Prompt preview card
    st.markdown('<div class="input-label">YOUR PROMPT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="prompt-block">{meta["prompt_preview"]}</div>', unsafe_allow_html=True)

    # ── Ticket input (only shown for stage 1 or if no ticket loaded yet) ──
    ticket_placeholder = st.session_state.get("ticket_text", "")
    if cur == 1 or not ticket_placeholder:
        ticket_input = st.text_area(
            "Support ticket",
            value=ticket_placeholder,
            height=120,
            placeholder="Paste the customer support ticket here…",
            key="ticket_textarea",
            label_visibility="collapsed",
        )
        st.session_state["ticket_text"] = ticket_input

        # Load sample shortcut
        sample_path = os.path.join("inputs", "sample_ticket.txt")
        if st.button("📄 Load sample ticket", use_container_width=False):
            if os.path.exists(sample_path):
                with open(sample_path, encoding="utf-8") as f:
                    st.session_state["ticket_text"] = f.read()
                st.rerun()

    # ── Run stage button ──
    api_ok = bool(os.getenv("OPENROUTER_API_KEY"))
    ticket_ok = bool(st.session_state.get("ticket_text", "").strip())

    btn_disabled = (not api_ok) or (not ticket_ok) or (st.session_state.pipeline_status == "running")
    btn_label = {1: "▶ Run stage", 2: "▶ Run stage", 3: "▶ Run pipeline"}.get(cur, "▶ Run stage")

    if not api_ok:
        st.warning("⚠️ Set `OPENROUTER_API_KEY` in your `.env` file to run.")

    run_clicked = st.button(btn_label, type="primary", use_container_width=True, disabled=btn_disabled)

    if run_clicked:
        st.session_state.pipeline_status = "running"
        os.environ["MODEL"] = os.getenv("MODEL", "openai/gpt-4o-mini")

        from app.stage1_understand import stage1_understand
        from app.stage2_reason import stage2_reason
        from app.stage3_produce import stage3_produce
        from app.utils import save_output

        ticket = st.session_state.get("ticket_text", "")

        if cur == 1:
            with st.spinner("🔍 Extracting ticket fields…"):
                try:
                    st.session_state.stage1_output = stage1_understand(ticket)
                    st.session_state.active_stage = 2
                    st.session_state.pipeline_status = "idle"
                except Exception as e:
                    st.error(f"Stage 1 failed: {e}")
                    st.session_state.pipeline_status = "idle"

        elif cur == 2:
            with st.spinner("🧠 Reasoning about priority & routing…"):
                try:
                    st.session_state.stage2_output = stage2_reason(st.session_state.stage1_output)
                    st.session_state.active_stage = 3
                    st.session_state.pipeline_status = "idle"
                except Exception as e:
                    st.error(f"Stage 2 failed: {e}")
                    st.session_state.pipeline_status = "idle"

        elif cur == 3:
            with st.spinner("✍️ Drafting customer reply…"):
                try:
                    reply = stage3_produce(
                        st.session_state.stage1_output,
                        st.session_state.stage2_output,
                    )
                    st.session_state.stage3_output = reply
                    st.session_state.pipeline_status = "complete"

                    # Save result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_output(f"result_{timestamp}.json", {
                        "ticket_fields":    st.session_state.stage1_output,
                        "priority_routing": st.session_state.stage2_output,
                        "drafted_reply":    reply,
                    })
                except Exception as e:
                    st.error(f"Stage 3 failed: {e}")
                    st.session_state.pipeline_status = "idle"

        st.rerun()

    # Reset button (small, below run)
    if st.session_state.stage1_output is not None:
        if st.button("↺ Reset pipeline", use_container_width=False):
            for k in ["stage1_output","stage2_output","stage3_output","ticket_text"]:
                st.session_state[k] = None
            st.session_state.active_stage = 1
            st.session_state.pipeline_status = "idle"
            st.rerun()


# ══════════════════════════════════════════════════════════════
# RIGHT — STAGE OUTPUTS panel
# ══════════════════════════════════════════════════════════════
with col_right:

    # Status pill top-right
    status = st.session_state.pipeline_status
    pill_cls  = {"idle":"pill-idle","running":"pill-running","complete":"pill-complete"}.get(status,"pill-idle")
    pill_text = {"idle":"IDLE","running":"RUNNING…","complete":"COMPLETE"}.get(status,"IDLE")
    st.markdown(
        f'<div class="panel-header">STAGE OUTPUTS'
        f'<span class="status-pill {pill_cls}">{pill_text}</span></div>',
        unsafe_allow_html=True,
    )

    # ── Stage result cards ──
    STAGE_CARDS = [
        (1, "Stage 1 · Understand", "Fields extracted as valid JSON."),
        (2, "Stage 2 · Reason",     "Priority & routing decided."),
        (3, "Stage 3 · Produce",    "Reply drafted on-brand."),
    ]

    for snum, stitle, ssub in STAGE_CARDS:
        done = _completed(snum)
        is_active_card = (snum == st.session_state.active_stage) and not done

        if done:
            icon_cls = "icon-done";   card_cls = "complete-card"; icon = "✓"
        elif is_active_card:
            icon_cls = "icon-active"; card_cls = "active-card";   icon = str(snum)
        else:
            icon_cls = "icon-future"; card_cls = "";               icon = str(snum)

        sub_text = "Reasoning step by step." if snum == 2 and done else ssub

        st.markdown(f"""
        <div class="output-card {card_cls}">
          <div class="output-icon {icon_cls}">{icon}</div>
          <div>
            <div class="output-card-title">{stitle}</div>
            <div class="output-card-sub">{sub_text}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Live output section ──
    st.markdown('<div class="live-header">LIVE OUTPUT</div>', unsafe_allow_html=True)

    cur_out = _output_for_stage(st.session_state.active_stage - 1)  # last completed stage

    if st.session_state.stage3_output is not None:
        # Pipeline complete — show final reply
        st.markdown(
            '<span class="live-label green">✓ Pipeline complete — messy ticket → finished reply</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="live-header">LIVE OUTPUT · FINAL REPLY</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="reply-box">{st.session_state.stage3_output}</div>',
            unsafe_allow_html=True,
        )
        word_count = len(st.session_state.stage3_output.split())
        st.caption(f"{'🟢' if word_count <= 120 else '🔴'} {word_count} words")

        # Download
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        full = {
            "ticket_fields":    st.session_state.stage1_output,
            "priority_routing": st.session_state.stage2_output,
            "drafted_reply":    st.session_state.stage3_output,
        }
        st.download_button(
            "⬇️ Download full report (JSON)",
            data=json.dumps(full, indent=2),
            file_name=f"result_{ts}.json",
            mime="application/json",
            use_container_width=True,
        )

    elif st.session_state.stage2_output is not None:
        # Stage 2 done — show stage 2 output + reasoning bullets
        s2 = st.session_state.stage2_output
        label_text = f"LIVE OUTPUT · STAGE 2 · RUN ON STAGE 1 JSON"
        st.markdown(f'<span class="live-label">↳ {label_text}</span>', unsafe_allow_html=True)

        why_text = s2.get("why", "")
        reasoning_lines = [l.strip() for l in why_text.replace(". ", ".\n").splitlines() if l.strip()]

        st.markdown("**Reasoning:**")
        for line in reasoning_lines[:4]:
            st.markdown(f"• {line}")

        st.code(json.dumps({
            "priority": s2.get("priority"),
            "route":    s2.get("route"),
            "why":      s2.get("why","")[:80] + ("…" if len(s2.get("why","")) > 80 else ""),
        }, indent=2), language="json")

    elif st.session_state.stage1_output is not None:
        # Stage 1 done — show stage 1 JSON
        s1 = st.session_state.stage1_output
        st.markdown('<span class="live-label">↳ LIVE OUTPUT · STAGE 1 OUTPUT</span>', unsafe_allow_html=True)
        st.code(json.dumps(s1, indent=2), language="json")

    else:
        # Nothing run yet
        st.markdown(
            '<div class="live-box" style="color:#475569;font-family:inherit;font-size:0.88rem;">'
            'Run Stage 1 to see live output here.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── All-stages JSON expander (after pipeline complete) ──
    if st.session_state.stage3_output is not None:
        with st.expander("🗂️ All stage outputs (JSON)", expanded=False):
            st.code(json.dumps({
                "stage1_ticket_fields":    st.session_state.stage1_output,
                "stage2_priority_routing": st.session_state.stage2_output,
                "stage3_drafted_reply":    st.session_state.stage3_output,
            }, indent=2), language="json")
