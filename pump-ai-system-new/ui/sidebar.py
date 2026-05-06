# =============================================================================
# ui/sidebar.py  —  Clean sidebar (fitting selector moved to main area)
# =============================================================================
import streamlit as st
from config.settings import THEMES, PIPE_ROUGHNESS, FLUID_DATA, PUMP_TYPES
from theory.pump_theory import THEORY

def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Control Panel")

        # ── Theme ─────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🎨 Dashboard Theme")
        theme_name = st.selectbox("Select Theme", list(THEMES.keys()),
                                   index=1, label_visibility="collapsed")
        th = THEMES[theme_name]

        # ── AI Key ────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🤖 AI Advisor")
        groq_key = st.text_input("Groq API Key", type="password",
                                  placeholder="gsk_xxxx  (free at console.groq.com)",
                                  help="Get a free key at https://console.groq.com")
        ai_model = st.selectbox("AI Model", ["llama3-8b-8192", "mixtral-8x7b-32768"],
                                 label_visibility="collapsed")

        # ── Pipeline Settings ─────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🔧 Pipeline Settings")
        pipe_mat  = st.selectbox("Pipe Material", list(PIPE_ROUGHNESS.keys()))
        pipe_L    = st.number_input("Pipe Length (m)", 10.0, 5000.0, 120.0, 10.0)

        # Show computed K total (from main area fitting panel via session_state)
        K_fit = st.session_state.get("K_fit_total", 0.0)
        st.markdown(
            f"**🔩 Minor Loss Σ K = `{K_fit:.4f}`**  "
            f"<span style='font-size:.76rem;opacity:.65;'>(set in Section 1b below)</span>",
            unsafe_allow_html=True)

        eta_motor = st.slider("Motor Efficiency (%)", 80, 99, 95) / 100
        SF        = st.slider("Motor Safety Factor", 1.05, 1.50, 1.15, 0.05)
        h_suc     = st.number_input("Suction Head h_s (m)", -6.0, 12.0, 2.5, 0.5)
        P_atm     = st.number_input("Atm. Pressure (Pa)", 80000, 110000, 101325, 500)
        op_hours  = st.number_input("Operating Hours/Year", 1000, 8760, 8000, 200)
        tariff    = st.number_input("Electricity ($/kWh)", 0.02, 0.50, 0.10, 0.01)

        # ── Display Options ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📊 Display Options")
        show_npsh    = st.checkbox("NPSH Analysis",   True)
        show_cost    = st.checkbox("Cost Estimate",    True)
        show_compare = st.checkbox("Pump Comparison",  False)
        show_theory  = st.checkbox("Theory Sidebar",   True)
        dark_graphs  = st.checkbox("Dark Graph Theme", True)

        # ── Theory mini-textbook ───────────────────────────────────────────────
        if show_theory:
            st.markdown("---")
            st.markdown("### 📚 Engineering Theory")
            topic = st.selectbox("Topic", list(THEORY.keys()),
                                  label_visibility="collapsed")
            entry = THEORY[topic]
            st.markdown(f"**{entry['icon']} {topic}**")
            st.markdown(entry["content"])

    return {
        "theme_name":  theme_name,
        "th":          th,
        "groq_key":    groq_key,
        "ai_model":    ai_model,
        "pipe_mat":    pipe_mat,
        "pipe_L":      pipe_L,
        "K_fit":       K_fit,
        "eta_motor":   eta_motor,
        "SF":          SF,
        "h_suc":       h_suc,
        "P_atm":       P_atm,
        "op_hours":    op_hours,
        "tariff":      tariff,
        "show_npsh":   show_npsh,
        "show_cost":   show_cost,
        "show_compare":show_compare,
        "show_theory": show_theory,
        "dark_graphs": dark_graphs,
    }
