# app.py
# Streamlit Demo UI — LLM-CAPP Project
# Week 6 | LLM-CAPP Project

import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week5")))

from tokenizer import tokenize
from agents import time_agent, cost_agent, energy_agent, efficiency_agent
from nsga2 import run_nsga2, ROUTE_VARIANTS
from fsm_validator import validate_sequence
from error_detector import detect_errors
from self_corrector import self_correct

# ── Page Config ───────────────────────────────────
st.set_page_config(
    page_title="LLM-CAPP System",
    page_icon="🏭",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0d0f1a; }
    .stApp { background-color: #0d0f1a; color: #e2e5f0; }
    .metric-card {
        background: #181c30;
        border: 1px solid #252a45;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .success-box {
        background: rgba(52,211,153,0.1);
        border: 1px solid rgba(52,211,153,0.3);
        border-radius: 10px;
        padding: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────
st.title("🏭 LLM-Based Intelligent Process Planning System")
st.markdown("**Manufacturing AI · IIT Kharagpur SRIC · Prof. Sankha Deb**")
st.divider()

# ── Sidebar — Input ───────────────────────────────
st.sidebar.header("⚙️ Part Configuration")

material = st.sidebar.selectbox(
    "Material",
    ["Aluminum", "Steel", "Brass", "Copper", "Titanium", "Plastic", "Cast Iron"]
)

features = st.sidebar.multiselect(
    "Features (select 1-4)",
    ["Hole", "Slot", "Pocket", "Boss", "Thread", "Chamfer", "Fillet", "Groove", "Step", "Face"],
    default=["Hole", "Slot"]
)

tolerance = st.sidebar.selectbox(
    "Tolerance",
    ["0.005mm", "0.01mm", "0.02mm", "0.05mm", "0.1mm", "0.5mm"],
    index=2
)

batch_size = st.sidebar.number_input(
    "Batch Size",
    min_value=1, max_value=10000, value=500, step=50
)

run_btn = st.sidebar.button("🚀 Generate Process Plan", type="primary", use_container_width=True)

# ── Main Content ──────────────────────────────────
if not run_btn:
    st.info("👈 Configure your part in the sidebar and click **Generate Process Plan**")

    # Show project overview
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Weeks Complete", "6/6")
    with col2:
        st.metric("Tests Passing", "43/43")
    with col3:
        st.metric("Dataset Parts", "50")
    with col4:
        st.metric("Avg Efficiency", "76.13/100")
    with col5:
        st.metric("Pipeline Speed", "0.01s")

    st.divider()
    st.subheader("🏗 System Pipeline")
    st.markdown(""" Part Input → Tokenizer (W1) → LLM Planner (W2) → Multi-Agent Eval (W3)
           → NSGA-II + FSM (W4) → Self-Correction (W5) → Best Route ✅ """)

else:
    if not features:
        st.error("❌ Please select at least one feature!")
        st.stop()

    part = {
        "material": material,
        "features": features,
        "tolerance": tolerance,
        "batch_size": batch_size
    }

    with st.spinner("Running pipeline..."):

        # ── Step 1: Tokenize ──────────────────────
        st.subheader("Step 1 — Feature Tokenization")
        token_result = tokenize(part)

        if token_result["success"]:
            col1, col2 = st.columns(2)
            with col1:
                st.success("✅ Tokenization Successful")
                st.write("**Token Sequence:**", token_result["tokens"])
            with col2:
                st.write("**Token Labels:**")
                for tok, lab in zip(token_result["tokens"], token_result["token_labels"]):
                    st.write(f"  `{tok}` → {lab}")
        else:
            st.error(f"❌ Tokenization Failed: {token_result['errors']}")
            st.stop()

        st.divider()

        # ── Step 2: NSGA-II ───────────────────────
        st.subheader("Step 2 — NSGA-II Optimization")
        pareto = run_nsga2(material, batch_size)
        st.success(f"✅ Found **{len(pareto)}** Pareto-optimal route(s)")

        pareto_data = []
        for ind in pareto:
            t, c, e = ind.objectives
            pareto_data.append({
                "Route": ind.route_name,
                "Steps": " → ".join(ind.steps),
                "Time (min)": t,
                "Cost ($)": c,
                "Energy (kWh)": e
            })
        st.dataframe(pareto_data, use_container_width=True)

        st.divider()

        # ── Step 3: FSM + Self-Correction ─────────
        st.subheader("Step 3 — FSM Validation & Self-Correction")

        valid_routes = []
        for ind in pareto:
            fsm = validate_sequence(ind.steps)
            if fsm["valid"]:
                st.success(f"✅ {ind.route_name} → FSM Valid")
                valid_routes.append(ind)
            else:
                correction = self_correct(ind.steps, verbose=False)
                if correction["success"]:
                    st.warning(f"🔧 {ind.route_name} → Auto-corrected in {correction['attempts']} attempt(s)")
                    ind.steps = correction["corrected"]
                    valid_routes.append(ind)
                else:
                    st.error(f"❌ {ind.route_name} → Could not fix")

        st.divider()

        # ── Step 4: Agent Scoring ─────────────────
        st.subheader("Step 4 — Multi-Agent Evaluation")

        agent_data = []
        best = None
        best_eff = -1

        for ind in valid_routes:
            t = time_agent(ind.steps, material)
            c = cost_agent(ind.steps, material, batch_size)
            e = energy_agent(ind.steps, material)
            eff = efficiency_agent(t, c, e)

            agent_data.append({
                "Route": ind.route_name,
                "Time (min)": t,
                "Cost ($)": c,
                "Energy (kWh)": e,
                "Efficiency Score": eff
            })

            if eff > best_eff:
                best_eff = eff
                best = {"route": ind.route_name, "steps": ind.steps, "t": t, "c": c, "e": e, "eff": eff}

        st.dataframe(agent_data, use_container_width=True)

        st.divider()

        # ── Final Result ──────────────────────────
        st.subheader("🏆 Final Result — Best Process Plan")

        if best:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Best Route", best["route"])
            with col2:
                st.metric("Time", f"{best['t']} min")
            with col3:
                st.metric("Cost", f"${best['c']}")
            with col4:
                st.metric("Efficiency", f"{best['eff']}/100")

            st.success(f"**Process Steps:** {' → '.join(best['steps'])}")

            st.balloons()
