"""
Streamlit demo UI - styled to match Razorpay's visual identity
(navy #0C2451 / #072654, signature blue #3395FF, clean card-based layout).

This is a thin visual wrapper. All logic still lives in propose.py,
attack_discount.py, validate.py, execute.py, audit.py, red_team.py -
nothing here duplicates that logic, it only calls it and displays results.
"""

import streamlit as st
import time
import json
import os
from catalog import get_catalog, get_item
from propose import propose_upsell
from attack_discount import propose_upsell_attack
from validate import validate_proposal
from execute import execute_approved_upsell
from audit import log_decision, new_trace_id

st.set_page_config(
    page_title="Guarded Upsell Agent | Razorpay Buildathon",
    page_icon="🛡️",
    layout="wide",
)

# ---------------- Razorpay-style theming ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    .stApp {
        background-color: #F7F9FC;
    }

    .rzp-header {
        background: linear-gradient(90deg, #0C2451 0%, #14315E 100%);
        padding: 20px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .rzp-header h1 { color: white; font-size: 22px; font-weight: 700; margin: 0; }
    .rzp-header p { color: #A9C1E8; font-size: 13px; margin: 2px 0 0 0; }
    .rzp-badge {
        background: #3395FF; color: white; padding: 6px 14px;
        border-radius: 20px; font-size: 12px; font-weight: 600;
    }

    .rzp-card {
        background: white; border-radius: 12px; padding: 20px 24px;
        border: 1px solid #E5EAF2; box-shadow: 0 1px 3px rgba(12,36,81,0.06);
        margin-bottom: 16px;
    }
    .rzp-card h3 {
        color: #0C2451; font-size: 15px; font-weight: 700; margin: 0 0 12px 0;
        text-transform: uppercase; letter-spacing: 0.5px;
    }

    .pill-approved {
        background: #E6F7ED; color: #0F9D58; padding: 6px 14px;
        border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block;
    }
    .pill-blocked {
        background: #FDECEC; color: #D93025; padding: 6px 14px;
        border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block;
    }
    .pill-neutral {
        background: #EAF2FF; color: #3395FF; padding: 4px 12px;
        border-radius: 14px; font-weight: 600; font-size: 12px; display: inline-block;
    }

    .stage-box {
        background: #F7F9FC; border: 1px solid #E5EAF2; border-radius: 10px;
        padding: 14px 16px; margin-bottom: 10px;
    }
    .stage-box .stage-label {
        color: #6B7A99; font-size: 11px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .stage-box .stage-value { color: #0C2451; font-size: 14px; font-weight: 500; margin-top: 4px; }

    .stButton>button {
        background: #3395FF; color: white; border-radius: 8px; border: none;
        font-weight: 600; padding: 10px 20px;
    }
    .stButton>button:hover { background: #0C2451; color: white; }

    .metric-number { font-size: 28px; font-weight: 800; color: #0C2451; }
    .metric-label {
        font-size: 12px; color: #6B7A99; text-transform: uppercase;
        letter-spacing: 0.5px; font-weight: 600;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 600; color: #0C2451;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown("""
<div class="rzp-header">
    <div>
        <h1>🛡️ Guarded Upsell Agent</h1>
        <p>Propose → Validate → Execute → Audit | Razorpay AI Builder Buildathon 2026 · Track 01</p>
    </div>
    <div class="rzp-badge">TEST MODE</div>
</div>
""", unsafe_allow_html=True)

# ---------------- Session state: track only this session's runs ----------------
if "session_records" not in st.session_state:
    st.session_state.session_records = []

# ---------------- Main demo ----------------
with st.sidebar:
    st.markdown("### 🛒 Build a Cart")
    catalog = get_catalog()
    item_names = {item["id"]: f"{item['name']} (₹{item['sell_price']})" for item in catalog}
    selected_id = st.selectbox(
        "Item in customer's cart",
        options=list(item_names.keys()),
        format_func=lambda x: item_names[x],
        index=3,
    )

    st.markdown("---")
    st.markdown("### ⚙️ Agent Mode")
    mode = st.radio(
        "Choose how the agent behaves",
        options=["Normal", "Adversarial (attack)"],
        help="Normal: honest agent, no pressure. Adversarial: agent is pressured to offer a huge discount to close the sale, no matter the margin.",
    )

    run_button = st.button("▶ Run Pipeline", use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 Gate Rules")
    st.markdown("""
    <div class="stage-box">
        <div class="stage-label">Min Margin</div>
        <div class="stage-value">20%</div>
    </div>
    <div class="stage-box">
        <div class="stage-label">Max Discount</div>
        <div class="stage-value">30%</div>
    </div>
    """, unsafe_allow_html=True)

cart_items = [{"id": selected_id, "quantity": 1}]
use_attack = (mode == "Adversarial (attack)")

if run_button:
    trace_id = new_trace_id()
    t_start = time.perf_counter()

    with st.spinner("Agent is thinking..."):
        t0 = time.perf_counter()
        proposal = propose_upsell_attack(cart_items) if use_attack else propose_upsell(cart_items)
        t_propose = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    gate_result = validate_proposal(proposal, cart_items)
    t_validate = (time.perf_counter() - t0) * 1000

    exec_result = None
    t_execute = 0
    if gate_result["approved"]:
        with st.spinner("Creating Razorpay order..."):
            t0 = time.perf_counter()
            exec_result = execute_approved_upsell(gate_result)
            t_execute = (time.perf_counter() - t0) * 1000

    t_total = (time.perf_counter() - t_start) * 1000
    latency = {
        "propose_ms": round(t_propose, 1),
        "validate_ms": round(t_validate, 3),
        "execute_ms": round(t_execute, 1),
        "total": round(t_total, 1),
    }

    logged_record = log_decision(
        trace_id=trace_id, cart_items=cart_items, proposal=proposal,
        gate_result=gate_result, exec_result=exec_result,
        mode="attack" if use_attack else "normal", latency_ms=latency,
    )
    # Track this run in THIS session only (not the full historical file)
    st.session_state.session_records.append(logged_record)

    proposed_item_obj = get_item(proposal.get("proposed_item_id"))
    proposed_display_name = proposed_item_obj["name"] if proposed_item_obj else f"Unknown ({proposal.get('proposed_item_id','-')})"

    # ---- 4-stage pipeline cards ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="rzp-card"><h3>1. Propose</h3>
        <span class="pill-neutral">LLM · Groq</span>
        <p style="margin-top:10px; font-size:13px; color:#0C2451;">
        Item: <b>{proposed_display_name}</b><br>
        <span style="font-size:11px; color:#6B7A99;">({proposal.get('proposed_item_id','-')})</span><br>
        Discount: <b>{proposal.get('discount_percent',0)}%</b>
        </p>
        <p style="font-size:11px; color:#6B7A99;">LLM latency: {latency['propose_ms']/1000:.1f}s</p>
        </div>""", unsafe_allow_html=True)

    with col2:
        pill = "pill-approved" if gate_result["approved"] else "pill-blocked"
        label = "APPROVED" if gate_result["approved"] else "BLOCKED"
        st.markdown(f"""<div class="rzp-card"><h3>2. Validate</h3>
        <span class="{pill}">{label}</span>
        <p style="margin-top:10px; font-size:12px; color:#0C2451;">{gate_result['reason']}</p>
        <p style="font-size:11px; color:#6B7A99;">Policy evaluation: {latency['validate_ms']} ms</p>
        </div>""", unsafe_allow_html=True)

    with col3:
        if exec_result and exec_result["executed"]:
            st.markdown(f"""<div class="rzp-card"><h3>3. Execute</h3>
            <span class="pill-approved">ORDER CREATED</span>
            <p style="margin-top:10px; font-size:13px; color:#0C2451;">
            {gate_result['item']['name']}<br>
            <b>₹{gate_result['final_price']}</b>
            </p>
            <p style="font-size:11px; color:#6B7A99; word-break:break-all;">{exec_result['order']['id']}</p>
            <p style="font-size:11px; color:#6B7A99;">{latency['execute_ms']} ms</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="rzp-card"><h3>3. Execute</h3>
            <span class="pill-blocked">SKIPPED</span>
            <p style="margin-top:10px; font-size:12px; color:#6B7A99;">No order created — nothing reaches Razorpay unless the gate approves.</p>
            </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""<div class="rzp-card"><h3>4. Audit</h3>
        <span class="pill-neutral">LOGGED</span>
        <p style="margin-top:10px; font-size:12px; color:#0C2451; word-break:break-all;">trace: {trace_id}</p>
        <p style="font-size:11px; color:#6B7A99;">total: {latency['total']} ms</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---- Margin math breakdown (real numbers, re-derived from catalog) ----
    lookup = get_item(proposal.get("proposed_item_id"))
    if lookup:
        discount = proposal.get("discount_percent", 0) or 0
        try:
            discount = float(discount)
        except (TypeError, ValueError):
            discount = 0
        cost = lookup["cost_price"]
        sell = lookup["sell_price"]
        final_price = sell * (1 - discount / 100)
        margin_amount = final_price - cost
        margin_pct = (margin_amount / final_price) * 100 if final_price > 0 else -100
        passed = margin_pct >= 20

        st.markdown(f"""<div class="rzp-card"><h3>💰 Margin Check (re-derived from catalog, not from the LLM)</h3>
        <div style="display:flex; gap:32px; align-items:center; flex-wrap:wrap;">
            <div><span class="stage-label">Cost Price</span><br><span class="metric-number" style="font-size:18px;">₹{cost}</span></div>
            <div><span class="stage-label">List Price</span><br><span class="metric-number" style="font-size:18px;">₹{sell}</span></div>
            <div><span class="stage-label">Discount Applied</span><br><span class="metric-number" style="font-size:18px;">{discount}%</span></div>
            <div><span class="stage-label">Final Price</span><br><span class="metric-number" style="font-size:18px;">₹{final_price:.1f}</span></div>
            <div><span class="stage-label">Resulting Margin</span><br><span class="metric-number" style="font-size:18px; color:{'#0F9D58' if passed else '#D93025'};">{margin_pct:.1f}%</span></div>
            <div><span class="stage-label">Required</span><br><span class="metric-number" style="font-size:18px;">≥ 20%</span></div>
            <div><span class="{'pill-approved' if passed else 'pill-blocked'}">{'PASS' if passed else 'FAIL'}</span></div>
        </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="rzp-card"><h3>💰 Margin Check</h3>
        <p style="font-size:13px; color:#6B7A99;">Not applicable — proposed item does not exist in catalog (hallucination caught before pricing math even runs).</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---- Human-readable timeline ----
    st.markdown("#### 🕒 Run Timeline")
    discount_val = proposal.get('discount_percent', 0) or 0
    discount_ok = isinstance(discount_val, (int, float)) and 0 <= discount_val <= 30
    timeline_html = f"""
    <div class="rzp-card">
        <div style="font-family:monospace; font-size:13px; color:#0C2451; line-height:1.9;">
            <b>[1] PROPOSE</b> &nbsp; {proposed_display_name} &nbsp;·&nbsp; discount {discount_val}%<br>
            <b>[2] VALIDATE</b> &nbsp; {'✓' if lookup else '✗'} item exists
                &nbsp;·&nbsp; {'✓' if discount_ok else '✗'} discount ≤ 30%
                &nbsp;·&nbsp; {'✓' if gate_result['approved'] else '✗'} margin ≥ 20%<br>
            <b>[3] EXECUTE</b> &nbsp; {'⛔ SKIPPED — gate rejected proposal' if not gate_result['approved'] else ('✅ order created' if exec_result and exec_result['executed'] else '⚠️ execution failed')}<br>
            <b>[4] AUDIT</b> &nbsp; logged as <code>{trace_id}</code>
        </div>
    </div>
    """
    st.markdown(timeline_html, unsafe_allow_html=True)

    with st.expander("🔍 Raw JSON (proposal, gate decision, execution)"):
        st.json({"proposal": proposal, "gate_result": gate_result, "execution": exec_result})

# ---- Audit trail table (this session only) ----
st.markdown("### 📜 Audit Trail (this session)")
records = st.session_state.session_records
if records:
    display_records = []
    for r in reversed(records[-15:]):
        proposed = r.get("proposed", {}) or {}
        item_obj = get_item(proposed.get("proposed_item_id"))
        item_display = item_obj["name"] if item_obj else (proposed.get("proposed_item_id") or "-")
        display_records.append({
            "Trace": r.get("trace_id", "-")[:16],
            "Mode": r.get("mode", "-"),
            "Item": item_display,
            "Status": r.get("guardrail_status", "-"),
            "Reason": r.get("decision_reasoning", "-")[:60],
            "Order": r.get("order_id") or "-",
            "Total (ms)": r.get("latency_ms", {}).get("total", "-"),
        })
    st.dataframe(display_records, use_container_width=True, hide_index=True)
else:
    st.info("No runs logged yet. Click **Run Pipeline** in the sidebar to get started.")

st.markdown("""
<div style="text-align:center; color:#6B7A99; font-size:12px; margin-top:32px;">
    Guarded Upsell Agent · Razorpay AI Builder Internship 2026 Buildathon · Track 01: AI Growth & Agentic Commerce
</div>
""", unsafe_allow_html=True)