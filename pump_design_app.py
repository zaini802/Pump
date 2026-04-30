# =============================================================================
# PUMP DESIGN TOOL — Professional Engineering Application
# =============================================================================
# References:
#   [1] Hydraulic Institute Standards — ANSI/HI 1.1-1.6, 2.1-2.5, 3.1-3.5
#   [2] Perry's Chemical Engineers' Handbook, 9th Ed. (McGraw-Hill, 2018)
#   [3] McCabe, Smith & Harriott — Unit Operations of Chemical Engineering, 7th Ed.
#   [4] Crane Technical Paper No. 410 — Flow of Fluids (Crane Co., 2013)
#   [5] Karassik et al. — Pump Handbook, 4th Ed. (McGraw-Hill, 2008)
#   [6] ISO 5199 / ISO 9908 — Centrifugal Pump Specifications
#   [7] API 610 / API 674 — Petroleum Industry Pump Standards
#   [8] Moody (1944) — Friction Factors for Pipe Flow
#   [9] ISO 281 — Rolling Bearing Life Calculation
#   [10] Chilton (1949) — Six-tenths Cost Estimation Rule
#
# Install: pip install streamlit plotly pandas numpy
# Run:     streamlit run pump_design_app.py
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math
import io
import json
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pump Design Tool",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

    /* ── Section headings ── */
    .sec-title {
        font-size: 1.30rem; font-weight: 700; letter-spacing: .5px;
        padding: 6px 0 2px 0; margin-top: 18px;
    }
    .sec-title.blue   { color: #4fc3f7; border-bottom: 2px solid #4fc3f7; }
    .sec-title.green  { color: #66bb6a; border-bottom: 2px solid #66bb6a; }
    .sec-title.amber  { color: #ffa726; border-bottom: 2px solid #ffa726; }
    .sec-title.red    { color: #ef5350; border-bottom: 2px solid #ef5350; }
    .sec-title.teal   { color: #26c6da; border-bottom: 2px solid #26c6da; }
    .sec-title.violet { color: #ab47bc; border-bottom: 2px solid #ab47bc; }
    .sec-title.gray   { color: #90a4ae; border-bottom: 2px solid #90a4ae; }

    /* ── Metric cards ── */
    .metric-card {
        background: #1e2130; border-radius: 10px; padding: 14px 18px;
        margin: 5px 0; border-left: 4px solid;
    }
    .metric-card.blue   { border-color: #4fc3f7; }
    .metric-card.green  { border-color: #66bb6a; }
    .metric-card.amber  { border-color: #ffa726; }
    .metric-card.red    { border-color: #ef5350; }
    .metric-card.teal   { border-color: #26c6da; }
    .metric-card.violet { border-color: #ab47bc; }
    .metric-label { font-size: .75rem; color: #90a4ae; margin-bottom: 3px; }
    .metric-value { font-size: 1.45rem; font-weight: 700; color: #ffffff; }
    .metric-unit  { font-size: .82rem; color: #b0bec5; margin-left: 4px; }

    /* ── Pump suggestion cards ── */
    .pump-card {
        background: #1e2130; border-radius: 12px; padding: 16px 20px;
        margin-bottom: 12px; border: 1px solid #2a2f45;
    }
    .pump-card.recommended { border: 2px solid #66bb6a; }
    .pump-title { font-size: 1.05rem; font-weight: 700; color: #4fc3f7; }

    /* ── Calculation step boxes ── */
    .calc-box {
        background: #12151f; border-left: 3px solid #4fc3f7;
        padding: 10px 16px; border-radius: 6px; margin: 8px 0;
        font-family: 'Courier New', monospace; font-size: .90rem; color: #cfd8dc;
    }
    .formula      { color: #f48fb1; }
    .substitution { color: #80cbc4; }
    .result       { color: #a5d6a7; font-weight: 700; }

    /* ── Info / warning ── */
    .warn-box {
        background: #2d1f00; border-left: 4px solid #ffa726;
        padding: 10px 16px; border-radius: 6px; margin: 8px 0;
        color: #ffcc80; font-size: .87rem;
    }
    .info-box {
        background: #0d1f2d; border-left: 4px solid #4fc3f7;
        padding: 10px 16px; border-radius: 6px; margin: 8px 0;
        color: #b3e5fc; font-size: .87rem;
    }

    /* ── Fancy divider ── */
    .fancy-divider {
        height: 3px;
        background: linear-gradient(90deg,#4fc3f7,#66bb6a,#ffa726,#ef5350,#ab47bc);
        border-radius: 2px; margin: 26px 0;
    }

    /* ── Reference rows ── */
    .ref-row { padding: 5px 0; border-bottom: 1px solid #2a2f45; font-size: .86rem; }
    .ref-row:last-child { border-bottom: none; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #13161f; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FLUID DATABASE  (Perry's 9th Ed. + standard tables)
# ─────────────────────────────────────────────────────────────────────────────
FLUID_DATA = {
    "Water":           {"rho_20": 998.2,  "mu_20": 1.002e-3, "Pv_20": 2337},
    "Hot Water (80°C)":{"rho_20": 958.4,  "mu_20": 0.282e-3,  "Pv_20": 47360},
    "Seawater":        {"rho_20": 1025.0, "mu_20": 1.08e-3,   "Pv_20": 2200},
    "Crude Oil":       {"rho_20": 870.0,  "mu_20": 50e-3,     "Pv_20": 500},
    "Diesel":          {"rho_20": 840.0,  "mu_20": 3.5e-3,    "Pv_20": 200},
    "Gasoline":        {"rho_20": 740.0,  "mu_20": 0.6e-3,    "Pv_20": 13000},
    "Sulfuric Acid":   {"rho_20": 1840.0, "mu_20": 26e-3,     "Pv_20": 10},
    "Ethanol":         {"rho_20": 789.0,  "mu_20": 1.2e-3,    "Pv_20": 5867},
    "Glycol (EG)":     {"rho_20": 1113.0, "mu_20": 21e-3,     "Pv_20": 8},
    "Milk":            {"rho_20": 1030.0, "mu_20": 2.1e-3,    "Pv_20": 2300},
    "Slurry (light)":  {"rho_20": 1150.0, "mu_20": 10e-3,     "Pv_20": 1500},
    "Custom":          {"rho_20": None,   "mu_20": None,       "Pv_20": None},
}

PIPE_ROUGHNESS = {
    "Commercial Steel":  4.6e-5,
    "Galvanized Steel":  1.5e-4,
    "Cast Iron":         2.6e-4,
    "PVC / Plastic":     1.5e-6,
    "Stainless Steel":   1.5e-5,
    "Concrete":          3.0e-4,
}

# ─────────────────────────────────────────────────────────────────────────────
# ENGINEERING CALCULATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def density_at_T(rho_20, T_C):
    """Approximate density at T °C (Perry's linear approximation, kg/m³)."""
    return rho_20 * (1 - 0.00065 * (T_C - 20))

def viscosity_at_T(mu_20, T_C, fluid):
    """Exponential viscosity correction for water-like fluids (Pa·s)."""
    if fluid in ("Water", "Hot Water (80°C)", "Seawater", "Milk"):
        return mu_20 * math.exp(-0.025 * (T_C - 20))
    return mu_20  # conservative: no correction for non-aqueous

def reynolds(rho, v, D, mu):
    return rho * v * D / mu

def colebrook_white(Re, D, eps):
    """Colebrook-White friction factor (Moody chart, implicit, iterative)."""
    if Re < 2300:
        return 64.0 / Re   # Laminar: Hagen-Poiseuille
    eps_D = eps / D
    f = 0.025              # initial guess (turbulent)
    for _ in range(60):
        arg = eps_D / 3.7 + 2.51 / (Re * math.sqrt(f))
        if arg <= 0:
            break
        f_new = (1 / (-2.0 * math.log10(arg))) ** 2
        if abs(f_new - f) < 1e-10:
            break
        f = f_new
    return f

def darcy_head_loss(f, L, D, v, g=9.81):
    """Major (pipe friction) head loss via Darcy-Weisbach (m)."""
    return f * (L / D) * v**2 / (2 * g)

def minor_head_loss(K, v, g=9.81):
    """Minor (fitting) head loss (m)."""
    return K * v**2 / (2 * g)

def hydraulic_power_W(Q, H, rho, g=9.81):
    """Hydraulic power: P_hyd = ρ·g·Q·H  (W)."""
    return rho * g * Q * H

def shaft_power_W(P_hyd, eta):
    return P_hyd / eta

def motor_power_W(P_shaft, eta_motor):
    return P_shaft / eta_motor

def specific_speed_metric(N, Q_lps, H):
    """Ns = N·√Q / H^(3/4)  [rpm, L/s, m] — HI metric convention."""
    if H <= 0 or Q_lps <= 0:
        return 0.0
    return N * math.sqrt(Q_lps) / H**0.75

def estimate_rpm(Q_m3s, D_mm):
    """Rough RPM estimate based on flow & pipe diameter (empirical)."""
    Q_lpm = Q_m3s * 60_000
    D_m   = D_mm / 1000
    if D_m <= 0 or Q_lpm <= 0:
        return 1450
    rpm = min(3600, max(350, 200 * Q_lpm**0.2 / D_m**0.5))
    return int(round(rpm / 50) * 50)

def pump_curve(Q_design, H_design, n=80):
    """
    Synthetic pump performance curve using parabolic H-Q model.
    Shutoff head ≈ 1.25 × H_design  (typical centrifugal, HI Fig. 1.1-4).
    """
    Q_max = Q_design * 1.65
    Q = np.linspace(0, Q_max, n)
    H0 = H_design * 1.25
    a  = H0 / Q_max**2
    H  = np.clip(H0 - a * Q**2, 0, H0)
    # Efficiency: parabolic peak at design point
    eta_pk = 0.83
    eta = eta_pk * (1 - 3.8 * ((Q - Q_design) / Q_max)**2)
    eta = np.clip(eta, 0.04, eta_pk)
    # Shaft power (kW) — using water at 1000 kg/m³ for curve shape
    P_kw = np.where(eta > 0.01, 1000 * 9.81 * Q * H / eta / 1000, 0)
    return Q, H, eta, P_kw

def select_pump(Q_m3s, H_m, rho, mu):
    """
    Rule-based selection per HI Standards and Karassik Pump Handbook.
    Returns list of (type, score, reasoning) sorted best-first.
    """
    Q_lpm  = Q_m3s * 60_000
    mu_cP  = mu * 1000

    scores = {}
    notes  = {}

    # ── Centrifugal ──
    s = 100; n = []
    if Q_lpm > 20:      s += 30; n.append("Flow range suited ✓")
    if H_m < 400:       s += 20; n.append("Head range suited ✓")
    if mu_cP < 100:     s += 25; n.append("Low viscosity ✓")
    else:               s -= 30; n.append("High viscosity penalty ✗")
    if rho < 1500:      s += 10
    scores["Centrifugal"] = s;  notes["Centrifugal"] = ", ".join(n) or "General purpose"

    # ── Reciprocating (plunger/piston) ──
    s = 55; n = []
    if H_m > 150:       s += 40; n.append("High-pressure duty ✓")
    if Q_lpm < 100:     s += 20; n.append("Low flow suited ✓")
    if mu_cP > 30:      s += 15; n.append("Handles viscous fluids ✓")
    scores["Reciprocating"] = s; notes["Reciprocating"] = ", ".join(n) or "Metering/high-P"

    # ── Gear (rotary PD) ──
    s = 45; n = []
    if mu_cP > 100:     s += 50; n.append("Excellent viscous handling ✓")
    if Q_lpm < 300:     s += 20; n.append("Moderate flow range ✓")
    if H_m > 80:        s -= 10
    scores["Gear"] = s;  notes["Gear"] = ", ".join(n) or "Lubricating / viscous fluids"

    # ── Diaphragm ──
    s = 38; n = []
    if rho > 1150:      s += 25; n.append("Dense / slurry fluid ✓")
    if Q_lpm < 50:      s += 15; n.append("Low flow ✓")
    scores["Diaphragm"] = s; notes["Diaphragm"] = ", ".join(n) or "Chemical / abrasive"

    ranked = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [(t, scores[t], notes[t]) for t in ranked]

def rom_cost(P_kw, pump_type):
    """ROM capital cost (USD, 2024 basis, six-tenths rule — Chilton 1949)."""
    base = {"Centrifugal": 350, "Reciprocating": 900, "Gear": 700, "Diaphragm": 1100}
    return base.get(pump_type, 400) * max(P_kw, 0.1)**0.7

# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def sec(label, color="blue"):
    st.markdown(f'<div class="sec-title {color}">{label}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

def mcard(label, value, unit="", color="blue"):
    st.markdown(f"""<div class="metric-card {color}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
    </div>""", unsafe_allow_html=True)

def cbox(formula="", sub="", result=""):
    st.markdown(f"""<div class="calc-box">
        <span class="formula">{formula}</span><br>
        <span class="substitution">{sub}</span><br>
        <span class="result">{result}</span>
    </div>""", unsafe_allow_html=True)

def info_box(msg):
    st.markdown(f'<div class="info-box">ℹ️ {msg}</div>', unsafe_allow_html=True)

def warn_box(msg):
    st.markdown(f'<div class="warn-box">⚠️ {msg}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# REPORT / CSV BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_report(inputs, results, calcs):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    L = [
        "=" * 72,
        "  PUMP DESIGN ENGINEERING REPORT",
        f"  Generated : {now}",
        "=" * 72, "",
        "SECTION 1 — PROCESS INPUTS", "-" * 50,
        *[f"  {k:<35} {v}" for k, v in inputs.items()],
        "", "SECTION 2 — DESIGN RESULTS", "-" * 50,
        *[f"  {k:<35} {v}" for k, v in results.items()],
        "", "SECTION 3 — CALCULATION SUMMARY", "-" * 50,
        *[f"  {k:<45} {v}" for k, v in calcs.items()],
        "",
        "=" * 72,
        "REFERENCES",
        "-" * 50,
        "  [1] ANSI/HI 1.1-1.6, 2.1, 3.1-3.5, 6.1-6.5 — Hydraulic Institute Standards",
        "  [2] Perry's Chemical Engineers' Handbook, 9th Ed., McGraw-Hill (2018)",
        "  [3] McCabe, Smith & Harriott — Unit Operations, 7th Ed., McGraw-Hill (2005)",
        "  [4] Crane Technical Paper No. 410 — Flow of Fluids (2013)",
        "  [5] Karassik et al. — Pump Handbook, 4th Ed., McGraw-Hill (2008)",
        "  [6] ISO 5199 / ISO 9908 — Centrifugal Pump Specifications",
        "  [7] API 610 / API 674 — Petroleum Industry Pump Standards",
        "  [8] Moody, L.F. — ASME Trans. 66, 671-684 (1944)",
        "  [9] ISO 281 — Rolling Bearing Rating Life",
        " [10] Chilton, C.H. — Six-tenths Rule, Chem. Eng. (1949)",
        "=" * 72,
        "",
        "DISCLAIMER: Engineering estimates only. Verify with a licensed P.Eng / PE.",
    ]
    return "\n".join(L)

def build_csv(inputs, results, Q_arr, H_arr, eta_arr, P_arr):
    buf = io.StringIO()
    buf.write("# PUMP DESIGN DATA — " + datetime.now().strftime("%Y-%m-%d") + "\n")
    buf.write("# INPUTS & RESULTS\n")
    pd.DataFrame([{"Parameter": k, "Value": v}
                  for k, v in {**inputs, **results}.items()]).to_csv(buf, index=False)
    buf.write("\n# PERFORMANCE CURVE\n")
    pd.DataFrame({
        "Flow_m3s": np.round(Q_arr, 6),
        "Head_m":   np.round(H_arr, 3),
        "Efficiency": np.round(eta_arr, 4),
        "Power_kW": np.round(P_arr, 3),
    }).to_csv(buf, index=False)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    g = 9.81  # m/s²

    # ── HEADER ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:22px 0 10px 0;">
        <div style="font-size:2.5rem; font-weight:800; letter-spacing:2px;
             background:linear-gradient(90deg,#4fc3f7,#66bb6a,#ffa726);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            ⚙️  PUMP DESIGN TOOL
        </div>
        <div style="color:#78909c; font-size:.97rem; margin-top:6px;">
            Professional Engineering Platform &nbsp;|&nbsp;
            Centrifugal · Reciprocating · Gear · Diaphragm Pumps
        </div>
    </div>
    """, unsafe_allow_html=True)
    divider()

    # ── WORKFLOW BANNER ───────────────────────────────────────────────────────
    steps = [("📥","Input"),("💡","Suggest"),("📐","Params"),("⚡","Calculate"),
             ("📊","Results"),("📈","Graphs"),("📄","Download")]
    cols = st.columns(7)
    for col, (ic, lb) in zip(cols, steps):
        col.markdown(
            f'<div style="text-align:center;background:#1e2130;border-radius:8px;'
            f'padding:10px 2px;font-size:.78rem;color:#b0bec5;">{ic}<br><b>{lb}</b></div>',
            unsafe_allow_html=True)
    divider()

    # =========================================================================
    # SIDEBAR — ADVANCED
    # =========================================================================
    with st.sidebar:
        st.markdown("## ⚙️  Advanced Options")
        pipe_mat   = st.selectbox("Pipe Material", list(PIPE_ROUGHNESS.keys()))
        pipe_L     = st.number_input("Pipe Length (m)", 10.0, 5000.0, 100.0, 10.0)
        K_fit      = st.number_input("Fitting Loss Coeff. K_total", 0.0, 50.0, 5.0, 0.5,
                                      help="Sum of all minor-loss K-values")
        eta_motor  = st.slider("Motor Efficiency (%)", 80, 99, 95) / 100
        SF         = st.slider("Power Safety Factor", 1.05, 1.50, 1.15, 0.05,
                                help="Motor sizing multiplier above shaft power")
        h_suction  = st.number_input("Suction Head h_s (m)", -5.0, 10.0, 2.0, 0.5)
        P_atm      = st.number_input("Atmospheric Pressure (Pa)", 80000, 110000, 101325, 500)
        st.markdown("---")
        show_npsh  = st.checkbox("Show NPSH Analysis", True)
        show_cost  = st.checkbox("Show Cost Estimate",  True)
        dark_theme = st.checkbox("Dark Graph Theme",    True)

    tmpl = "plotly_dark" if dark_theme else "plotly_white"
    eps  = PIPE_ROUGHNESS[pipe_mat]

    # =========================================================================
    # SECTION 2 — INPUTS
    # =========================================================================
    sec("📥  SECTION 2 — PROCESS INPUT PARAMETERS", "blue")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("##### 🌊 Flow Conditions")
        Q_val  = st.number_input("Volumetric Flow Rate", 0.1, 10000.0, 50.0, 1.0)
        Q_unit = st.selectbox("Flow Unit", ["m³/h","L/s","L/min","m³/s","US GPM"])
        H_user = st.number_input("Total Dynamic Head, TDH (m)", 1.0, 2000.0, 30.0, 0.5)
        st.caption("TDH = static head + velocity head + all friction losses")

    with c2:
        st.markdown("##### 🧪 Fluid Properties")
        fluid  = st.selectbox("Fluid Type", list(FLUID_DATA.keys()))
        T_C    = st.number_input("Operating Temperature (°C)", -10.0, 300.0, 25.0, 5.0)
        if fluid == "Custom":
            rho_cust = st.number_input("Custom Density ρ (kg/m³)", 400.0, 3000.0, 1000.0)
            mu_cust  = st.number_input("Custom Viscosity μ (mPa·s)", 0.1, 100000.0, 1.0)
        else:
            rho_cust = mu_cust = None

    with c3:
        st.markdown("##### 🔧 Piping & Efficiency")
        D_mm   = st.number_input("Pipe Internal Diameter (mm)", 10.0, 2000.0, 100.0, 5.0)
        eta_p  = st.slider("Pump Efficiency η_pump (%)", 40, 95, 75,
                            help="Overall hydraulic + volumetric + mechanical efficiency") / 100
        prefer = st.selectbox("Preferred Pump Family",
                               ["Auto-Select","Centrifugal","Reciprocating","Gear","Diaphragm"])

    # ── Unit conversions ─────────────────────────────────────────────────────
    CONV = {"m³/h": 1/3600, "L/s": 1e-3, "L/min": 1/60000,
            "m³/s": 1.0, "US GPM": 6.309e-5}
    Q_m3s = Q_val * CONV[Q_unit]
    D_m   = D_mm / 1000

    # ── Fluid properties ─────────────────────────────────────────────────────
    if fluid == "Custom":
        rho = rho_cust;  mu = mu_cust * 1e-3;  Pv = 2337
    else:
        fd  = FLUID_DATA[fluid]
        rho = density_at_T(fd["rho_20"], T_C)
        mu  = viscosity_at_T(fd["mu_20"], T_C, fluid)
        Pv  = fd["Pv_20"]

    # ── Input validation ─────────────────────────────────────────────────────
    errs = []
    if Q_m3s <= 0:  errs.append("Flow rate must be > 0.")
    if H_user <= 0: errs.append("TDH must be > 0 m.")
    if D_m    <= 0: errs.append("Pipe diameter must be > 0 mm.")
    if rho    <= 0: errs.append("Density must be > 0 kg/m³.")
    if mu     <= 0: errs.append("Viscosity must be > 0 Pa·s.")
    if errs:
        for e in errs: st.error(f"❌ {e}")
        st.stop()

    # ── Pre-calculations for preview ─────────────────────────────────────────
    A_pipe = math.pi * D_m**2 / 4
    v_pipe = Q_m3s / A_pipe
    Re     = reynolds(rho, v_pipe, D_m, mu)
    f_D    = colebrook_white(Re, D_m, eps)
    hf_maj = darcy_head_loss(f_D, pipe_L, D_m, v_pipe)
    hf_min = minor_head_loss(K_fit, v_pipe)
    H_tot  = H_user
    P_hyd  = hydraulic_power_W(Q_m3s, H_tot, rho)
    P_sh   = shaft_power_W(P_hyd, eta_p)
    P_mot  = motor_power_W(P_sh * SF, eta_motor)
    N_rpm  = estimate_rpm(Q_m3s, D_mm)
    Q_lps  = Q_m3s * 1000
    Ns     = specific_speed_metric(N_rpm, Q_lps, H_tot)
    omega  = 2 * math.pi * N_rpm / 60
    torque = P_sh / omega

    # =========================================================================
    # SECTION 3 — PUMP SUGGESTIONS
    # =========================================================================
    divider()
    sec("💡  SECTION 3 — PUMP TYPE SELECTION & RECOMMENDATIONS", "green")

    ranking = select_pump(Q_m3s, H_tot, rho, mu)
    if prefer != "Auto-Select":
        ranking.sort(key=lambda x: (0 if x[0] == prefer else 1, -x[1]))

    PUMP_META = {
        "Centrifugal":  {
            "icon":"🔵","color":"blue",
            "desc": "Kinetic-energy pump; rotating impeller imparts velocity converted to pressure. "
                    "Most widely used industrial pump type globally (>80% of all pump installations).",
            "apps":["Water/wastewater","HVAC","Process chemicals","Power generation","Desalination"],
            "range":"Flow: 1–100,000 m³/h  |  Head: 2–1,500 m  |  Viscosity: <500 cP",
            "std":"ANSI/HI 1.1-1.6  |  ISO 5199  |  API 610",
        },
        "Reciprocating":{
            "icon":"🟠","color":"amber",
            "desc": "Positive-displacement pump using piston or plunger reciprocation. "
                    "Delivers precise flow independent of discharge pressure.",
            "apps":["High-pressure injection","Hydraulic systems","Metering","Well pumping","HPLC"],
            "range":"Flow: 0.001–200 m³/h  |  Head: up to 10,000 m  |  Viscosity: 1–200 cP",
            "std":"ANSI/HI 6.1-6.5  |  API 674",
        },
        "Gear":         {
            "icon":"🟢","color":"green",
            "desc": "Rotary positive-displacement pump with meshing spur or helical gears. "
                    "Excellent for viscous, lubricating fluids with near-pulse-free delivery.",
            "apps":["Lube oil systems","Fuel transfer","Polymers","Resin injection","Bitumen"],
            "range":"Flow: 0.001–500 m³/h  |  Head: up to 200 m  |  Viscosity: 1–100,000 cP",
            "std":"ANSI/HI 3.1-3.5  |  ISO 2943",
        },
        "Diaphragm":    {
            "icon":"🔴","color":"red",
            "desc": "Flexible diaphragm flexes to displace fluid. Seal-less design prevents "
                    "leakage; ideal for hazardous, corrosive, or abrasive slurries.",
            "apps":["Chemical dosing","Slurry mining","Wastewater","Pharmaceutical","Paints/inks"],
            "range":"Flow: 0.001–100 m³/h  |  Head: up to 150 m  |  Viscosity: 1–50,000 cP",
            "std":"ANSI/HI 7.1-7.5  |  ISO 9908",
        },
    }

    for i, (pt, sc, reason) in enumerate(ranking):
        m = PUMP_META[pt]
        rec = "recommended" if i == 0 else ""
        badge = "⭐ RECOMMENDED  —  " if i == 0 else ""
        apps_str = "  |  ".join(m["apps"])
        st.markdown(f"""
        <div class="pump-card {rec}">
            <div class="pump-title">{m['icon']} {pt} Pump
                <span style="font-size:.72rem;color:#78909c;"> — Suitability Score: {sc}</span>
            </div>
            <div style="color:#cfd8dc;margin:6px 0 4px 0;font-size:.88rem;">
                {badge}{m['desc']}
            </div>
            <div style="color:#78909c;font-size:.78rem;margin-bottom:3px;">
                <b>Applications:</b> {apps_str}
            </div>
            <div style="color:#78909c;font-size:.78rem;margin-bottom:3px;">
                <b>Typical Range:</b> {m['range']}
            </div>
            <div style="color:#546e7a;font-size:.76rem;">
                <b>Standard:</b> {m['std']} &nbsp;&nbsp;
                <b>Selection basis:</b> {reason}
            </div>
        </div>""", unsafe_allow_html=True)

    selected = ranking[0][0]
    info_box(f"Auto-selected: <b>{selected} Pump</b> — based on duty point and fluid properties.")

    # =========================================================================
    # SECTION 4 — DESIGN PARAMETERS PREVIEW
    # =========================================================================
    divider()
    sec("📐  SECTION 4 — PRELIMINARY DESIGN PARAMETERS", "amber")
    p1,p2,p3,p4 = st.columns(4)
    with p1:
        mcard("Hydraulic Power",  f"{P_hyd/1000:.2f}", "kW",    "blue")
        mcard("Pipe Velocity",    f"{v_pipe:.2f}",      "m/s",   "blue")
    with p2:
        mcard("Shaft Power",      f"{P_sh/1000:.2f}",   "kW",    "green")
        mcard("Reynolds Number",  f"{Re:,.0f}",          "",      "green")
    with p3:
        mcard("Motor Input Power",f"{P_mot/1000:.2f}",  "kW",    "amber")
        mcard("Friction Factor f",f"{f_D:.5f}",          "",      "amber")
    with p4:
        mcard("Specific Speed Ns",f"{Ns:.1f}",           "",      "teal")
        mcard("Estimated RPM",    f"{N_rpm}",             "rpm",   "teal")

    # =========================================================================
    # SECTION 5 — CALCULATE BUTTON
    # =========================================================================
    divider()
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        calc_btn = st.button("⚡  CALCULATE PUMP DESIGN", use_container_width=True, type="primary")

    if not calc_btn:
        info_box("Configure parameters above, then press <b>Calculate Pump Design</b>.")
        _show_refs()
        return

    # =========================================================================
    # SECTION 6 — DETAILED CALCULATIONS
    # =========================================================================
    divider()
    sec("🔢  SECTION 6 — DETAILED ENGINEERING CALCULATIONS", "violet")

    # ── 6.1 Hydraulic ────────────────────────────────────────────────────────
    with st.expander("📌 6.1  HYDRAULIC CALCULATIONS — Pipe Flow & Head Losses", expanded=True):
        st.markdown("#### 6.1.1  Cross-sectional Area & Flow Velocity")
        cbox("A = π·D² / 4",
             f"A = π × ({D_m:.4f})² / 4",
             f"A = {A_pipe:.6f} m²")
        cbox("v = Q / A",
             f"v = {Q_m3s:.5f} / {A_pipe:.6f}",
             f"v = {v_pipe:.4f} m/s")
        if v_pipe > 4.0:
            warn_box(f"Velocity {v_pipe:.2f} m/s exceeds recommended 3–4 m/s (HI Std § 1.3.4). "
                     "Consider increasing pipe diameter to reduce erosion and noise.")

        st.markdown("#### 6.1.2  Reynolds Number & Flow Regime")
        regime = "Turbulent" if Re > 4000 else ("Transitional" if Re > 2300 else "Laminar")
        cbox("Re = ρ · v · D / μ",
             f"Re = {rho:.2f} × {v_pipe:.4f} × {D_m:.4f} / {mu:.4e}",
             f"Re = {Re:,.0f}  →  {regime} flow")

        st.markdown("#### 6.1.3  Darcy-Weisbach Friction Factor (Colebrook-White)")
        cbox("1/√f = −2 log₁₀(ε/(3.7D) + 2.51/(Re√f))  [implicit, iterative]",
             f"ε = {eps:.2e} m,  ε/D = {eps/D_m:.2e},  Re = {Re:,.0f}",
             f"f = {f_D:.6f}  (Moody diagram, fully turbulent zone)")

        st.markdown("#### 6.1.4  Major Friction Head Loss")
        cbox("h_f = f · (L/D) · v²/(2g)",
             f"h_f = {f_D:.5f} × ({pipe_L:.0f}/{D_m:.4f}) × {v_pipe:.4f}²/(2×{g})",
             f"h_f = {hf_maj:.4f} m")

        st.markdown("#### 6.1.5  Minor (Fitting) Head Loss")
        cbox("h_m = K_total · v²/(2g)",
             f"h_m = {K_fit:.2f} × {v_pipe:.4f}²/(2×{g})",
             f"h_m = {hf_min:.4f} m")

        h_frict = hf_maj + hf_min
        cbox("h_friction,total = h_f + h_m",
             f"h_friction,total = {hf_maj:.4f} + {hf_min:.4f}",
             f"h_friction,total = {h_frict:.4f} m")

        st.markdown("#### 6.1.6  Velocity Head")
        h_vel = v_pipe**2 / (2*g)
        cbox("h_v = v²/(2g)",
             f"h_v = {v_pipe:.4f}²/(2×{g})",
             f"h_v = {h_vel:.5f} m")

        info_box("TDH as specified by user already incorporates static lift, velocity head, "
                 "and all friction contributions (Perry's §6-22).")

    # ── 6.2 Power ─────────────────────────────────────────────────────────────
    with st.expander("⚡ 6.2  POWER CALCULATIONS"):
        st.markdown("#### 6.2.1  Hydraulic (Water) Power")
        cbox("P_hyd = ρ · g · Q · H",
             f"P_hyd = {rho:.2f} × {g} × {Q_m3s:.5f} × {H_tot:.2f}",
             f"P_hyd = {P_hyd:.2f} W  =  {P_hyd/1000:.4f} kW")

        st.markdown("#### 6.2.2  Pump Shaft Power")
        cbox("P_shaft = P_hyd / η_pump",
             f"P_shaft = {P_hyd:.2f} / {eta_p:.4f}",
             f"P_shaft = {P_sh:.2f} W  =  {P_sh/1000:.4f} kW")

        st.markdown("#### 6.2.3  Motor Sizing Power (with Safety Factor)")
        P_mot_s = P_sh * SF / eta_motor
        cbox("P_motor = P_shaft × SF / η_motor",
             f"P_motor = {P_sh/1000:.4f} × {SF} / {eta_motor:.3f}",
             f"P_motor = {P_mot_s/1000:.4f} kW  →  Select next standard motor size")

        st.markdown("#### 6.2.4  Torque at Pump Shaft")
        cbox("T = P_shaft / ω,  where ω = 2π·N/60",
             f"ω = 2π×{N_rpm}/60 = {omega:.3f} rad/s",
             f"T = {P_sh:.2f} / {omega:.3f}  =  {torque:.3f} N·m")

    # ── 6.3 Efficiency ────────────────────────────────────────────────────────
    with st.expander("📊 6.3  EFFICIENCY ANALYSIS & SPECIFIC SPEED"):
        eta_ov = eta_p * eta_motor
        st.markdown("#### 6.3.1  Overall System Efficiency")
        cbox("η_overall = η_pump × η_motor",
             f"η_overall = {eta_p:.4f} × {eta_motor:.4f}",
             f"η_overall = {eta_ov:.4f}  =  {eta_ov*100:.2f}%")

        st.markdown("#### 6.3.2  Specific Speed (SI Metric — HI Std)")
        cbox("Ns = N · √Q_lps / H^(3/4)   [rpm, L/s, m]",
             f"Ns = {N_rpm} × √{Q_lps:.3f} / {H_tot:.2f}^0.75",
             f"Ns = {Ns:.2f}")
        pump_cls = ("Low Ns → Radial-flow / multi-stage" if Ns < 600
                    else "Mid Ns → Mixed-flow centrifugal" if Ns < 2500
                    else "High Ns → Axial/propeller flow")
        info_box(f"Specific Speed Class: <b>{pump_cls}</b>  (Karassik, Table 2.1)")

        st.markdown("#### 6.3.3  BEP Operating Window")
        st.markdown("""
        > Per **ANSI/HI 1.3**, centrifugal pumps must operate within **70–120 % of BEP flow**
        > to avoid excessive radial thrust, vibration, and premature bearing/seal failure.
        > Sustained operation at < 50 % BEP can reduce MTBF by > 50 %
        > (Karassik §2.3; McCabe §7.4).
        """)

    # ── 6.4 Mechanical ────────────────────────────────────────────────────────
    with st.expander("🔩 6.4  MECHANICAL DESIGN CONSIDERATIONS"):
        st.markdown("#### 6.4.1  Impeller Diameter Estimate")
        phi = 0.85   # head coefficient (typical radial-flow: 0.8–0.9)
        u2  = math.sqrt(2*g*H_tot) / phi
        D_imp_mm = 60 * u2 / (math.pi * N_rpm) * 1000
        cbox("u₂ = √(2gH)/φ  →  D₂ = 60·u₂/(π·N)",
             f"u₂ = √(2×{g}×{H_tot:.2f}) / {phi} = {u2:.3f} m/s",
             f"D₂ ≈ {D_imp_mm:.0f} mm  (preliminary; refine via hydraulic design)")

        st.markdown("#### 6.4.2  Minimum Shaft Diameter (ASME B106.1M)")
        tau_allow = 40e6   # Pa, allowable shear for carbon steel shaft
        d_sh_mm   = (16*torque / (math.pi*tau_allow))**(1/3) * 1000
        cbox("d_shaft = (16·T / (π·τ_allow))^(1/3)",
             f"d_shaft = (16×{torque:.3f} / (π×{tau_allow:.0e}))^(1/3)",
             f"d_shaft ≥ {d_sh_mm:.1f} mm  (add keyway derating factor ×1.15)")

        st.markdown("#### 6.4.3  Bearing L₁₀ Life Estimate (ISO 281)")
        C_dyn = 50000  # N (representative medium-duty bearing)
        F_rad = max(rho * g * Q_m3s, 50)   # N, approximate radial load
        L10_h = (1e6 / (60*N_rpm)) * (C_dyn / F_rad)**3
        cbox("L₁₀ = (10⁶/(60N)) · (C/P)³",
             f"L₁₀ = (10⁶/({60*N_rpm:.0f})) × ({C_dyn}/{F_rad:.0f})³",
             f"L₁₀ ≈ {min(L10_h,500000):,.0f} h  (indicative, bearing selection required)")

    # ── 6.5 Pressure Drop & NPSH ─────────────────────────────────────────────
    with st.expander("🔴 6.5  PRESSURE DROP & NPSH / CAVITATION ANALYSIS"):
        dP_maj = f_D * (pipe_L/D_m) * rho * v_pipe**2 / 2
        dP_min = K_fit * rho * v_pipe**2 / 2
        dP_tot = dP_maj + dP_min

        st.markdown("#### 6.5.1  Pressure Drop (Darcy-Weisbach)")
        cbox("ΔP_major = f·(L/D)·(ρv²/2)",
             f"ΔP_major = {f_D:.5f} × ({pipe_L}/{D_m:.4f}) × ({rho:.2f}×{v_pipe:.4f}²/2)",
             f"ΔP_major = {dP_maj:,.1f} Pa  =  {dP_maj/1e5:.4f} bar")
        cbox("ΔP_minor = K·(ρv²/2)",
             f"ΔP_minor = {K_fit} × ({rho:.2f}×{v_pipe:.4f}²/2)",
             f"ΔP_minor = {dP_min:,.1f} Pa  =  {dP_min/1e5:.4f} bar")
        cbox("ΔP_total = ΔP_major + ΔP_minor",
             "",
             f"ΔP_total = {dP_tot:,.1f} Pa  =  {dP_tot/1e5:.5f} bar")

        if show_npsh:
            st.markdown("#### 6.5.2  NPSH Analysis (HI 1.3 / Karassik Ch. 2)")
            hf_suc  = hf_maj * 0.25   # assume 25% of total friction on suction side
            NPSHa   = (P_atm - Pv) / (rho*g) + h_suction - hf_suc
            NPSHr   = max(0.5, 0.003 * (N_rpm * Q_m3s**0.5)**(4/3) / g)
            margin  = NPSHa - NPSHr
            cbox("NPSH_a = (P_atm − P_v)/(ρg) + h_s − h_f,suc",
                 f"NPSH_a = ({P_atm}−{Pv})/({rho:.1f}×{g}) + {h_suction} − {hf_suc:.3f}",
                 f"NPSH_a = {NPSHa:.3f} m")
            cbox("NPSH_r  (Karassik empirical correlation)",
                 f"N = {N_rpm} rpm,  Q = {Q_m3s:.5f} m³/s",
                 f"NPSH_r ≈ {NPSHr:.3f} m")
            cbox("NPSH Margin = NPSH_a − NPSH_r  (min 0.5 m per HI Std)",
                 "",
                 f"Margin = {margin:.3f} m")
            if margin < 0.5:
                warn_box(f"CAVITATION RISK — NPSH margin = {margin:.2f} m < 0.5 m (HI minimum). "
                         "Raise suction head, reduce suction losses, or de-rate pump speed.")
            else:
                st.success(f"✅  NPSH adequate — Margin = {margin:.2f} m (≥ 0.5 m required)")

    # ── 6.6 Cost Estimate ────────────────────────────────────────────────────
    if show_cost:
        with st.expander("💰 6.6  ROUGH-ORDER-OF-MAGNITUDE COST ESTIMATE"):
            P_kw_sh = P_sh / 1000
            c_pump  = rom_cost(P_kw_sh, selected)
            c_motor = c_pump * 0.35
            c_inst  = (c_pump + c_motor) * 0.50
            c_total = c_pump + c_motor + c_inst
            E_yr    = P_mot_s / 1000 * 8000 / 1000  # MWh/yr
            E_cost  = E_yr * 100                      # $0.10/kWh

            st.markdown("**ROM Capital Cost (±40% accuracy, 2024 USD, Chilton six-tenths rule)**")
            ca, cb, cc = st.columns(3)
            ca.metric("Pump Equipment",  f"${c_pump:,.0f}")
            cb.metric("Motor + Starter", f"${c_motor:,.0f}")
            cc.metric("Installation",    f"${c_inst:,.0f}")
            st.metric("Total Installed Cost", f"${c_total:,.0f}")
            st.metric("Annual Energy Cost (8,000 hr/yr, $0.10/kWh)", f"${E_cost:,.0f} / yr")
            info_box("Cost estimates are ROM (±40%). Actual costs depend on material class, "
                     "vendor quotes, site conditions, and applicable codes.")

    # =========================================================================
    # SECTION 7 — RESULTS SUMMARY
    # =========================================================================
    divider()
    sec("📊  SECTION 7 — RESULTS SUMMARY", "green")

    r1,r2,r3,r4 = st.columns(4)
    eta_ov = eta_p * eta_motor
    with r1:
        mcard("Selected Pump",    selected,             "",   "blue")
        mcard("Flow Rate",        f"{Q_val:.2f}",       Q_unit, "blue")
        mcard("Total Head",       f"{H_tot:.1f}",       "m",  "blue")
    with r2:
        mcard("Hydraulic Power",  f"{P_hyd/1000:.3f}",  "kW", "green")
        mcard("Shaft Power",      f"{P_sh/1000:.3f}",   "kW", "green")
        mcard("Motor Power",      f"{P_mot_s/1000:.3f}","kW", "green")
    with r3:
        mcard("Pump Efficiency",  f"{eta_p*100:.1f}",   "%",  "amber")
        mcard("Motor Efficiency", f"{eta_motor*100:.1f}","%", "amber")
        mcard("Overall Efficiency",f"{eta_ov*100:.2f}", "%",  "amber")
    with r4:
        mcard("Pipe Velocity",    f"{v_pipe:.3f}",      "m/s","teal")
        mcard("Reynolds No.",     f"{Re:,.0f}",          "",   "teal")
        mcard("Specific Speed",   f"{Ns:.1f}",           "",   "teal")

    # =========================================================================
    # SECTION 8 — GRAPHS
    # =========================================================================
    divider()
    sec("📈  SECTION 8 — PUMP PERFORMANCE GRAPHS", "red")

    Q_c, H_c, eta_c, P_c = pump_curve(Q_m3s, H_tot)
    Qlpm_c = Q_c * 60_000

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔵 H-Q Curve", "🟢 Efficiency", "🟠 Power", "🔴 Dashboard"
    ])

    # ── T1: H-Q ──────────────────────────────────────────────────────────────
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Qlpm_c, y=H_c, mode="lines", name="Pump Curve",
                                  line=dict(color="#4fc3f7", width=3),
                                  fill="tozeroy", fillcolor="rgba(79,195,247,0.07)"))
        # System curve
        Q_sys  = np.linspace(0, Q_m3s*1.5, 60)
        H_st   = H_tot * 0.40
        a_sys  = (H_tot - H_st) / Q_m3s**2
        H_sys  = H_st + a_sys * Q_sys**2
        fig.add_trace(go.Scatter(x=Q_sys*60000, y=H_sys, mode="lines", name="System Curve",
                                  line=dict(color="#ffa726", width=2, dash="dash")))
        fig.add_trace(go.Scatter(x=[Q_m3s*60000], y=[H_tot], mode="markers",
                                  name="Operating Point",
                                  marker=dict(color="#ef5350", size=14, symbol="star",
                                              line=dict(color="white", width=2))))
        fig.update_layout(template=tmpl, height=430,
                          title=dict(text="Pump H-Q Curve vs System Curve", font=dict(size=15)),
                          xaxis_title="Flow Rate (L/min)", yaxis_title="Head (m)",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#12151f",
                          font=dict(color="#b0bec5"))
        st.plotly_chart(fig, use_container_width=True)

    # ── T2: Efficiency ────────────────────────────────────────────────────────
    with tab2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Qlpm_c, y=eta_c*100, mode="lines", name="η (%)",
                                  line=dict(color="#66bb6a", width=3),
                                  fill="tozeroy", fillcolor="rgba(102,187,106,0.07)"))
        fig.add_hline(y=eta_p*100, line_dash="dot", line_color="#ab47bc",
                      annotation_text=f"Design η = {eta_p*100:.0f}%",
                      annotation_font_color="#ab47bc")
        fig.add_trace(go.Scatter(x=[Q_m3s*60000], y=[eta_p*100], mode="markers",
                                  name="Design Point",
                                  marker=dict(color="#ffa726", size=12, symbol="diamond",
                                              line=dict(color="white", width=2))))
        fig.update_layout(template=tmpl, height=430,
                          title=dict(text="Pump Efficiency vs Flow Rate", font=dict(size=15)),
                          xaxis_title="Flow Rate (L/min)", yaxis_title="Efficiency (%)",
                          yaxis_range=[0, 100],
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#12151f",
                          font=dict(color="#b0bec5"))
        st.plotly_chart(fig, use_container_width=True)

    # ── T3: Power ─────────────────────────────────────────────────────────────
    with tab3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Qlpm_c, y=P_c, mode="lines", name="Shaft Power (kW)",
                                  line=dict(color="#ffa726", width=3),
                                  fill="tozeroy", fillcolor="rgba(255,167,38,0.07)"))
        fig.add_trace(go.Scatter(x=[Q_m3s*60000], y=[P_sh/1000], mode="markers",
                                  name="Design Point",
                                  marker=dict(color="#ef5350", size=12, symbol="star",
                                              line=dict(color="white", width=2))))
        fig.update_layout(template=tmpl, height=430,
                          title=dict(text="Shaft Power vs Flow Rate", font=dict(size=15)),
                          xaxis_title="Flow Rate (L/min)", yaxis_title="Power (kW)",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#12151f",
                          font=dict(color="#b0bec5"))
        st.plotly_chart(fig, use_container_width=True)

    # ── T4: Dashboard ─────────────────────────────────────────────────────────
    with tab4:
        fig = make_subplots(rows=2, cols=2,
                            subplot_titles=("H-Q Curve","Efficiency vs Flow",
                                            "Power vs Flow","Pump Suitability Scores"),
                            vertical_spacing=0.16, horizontal_spacing=0.10)
        fig.add_trace(go.Scatter(x=Qlpm_c, y=H_c, mode="lines",
                                  line=dict(color="#4fc3f7", width=2), name="Head"), row=1, col=1)
        fig.add_trace(go.Scatter(x=[Q_m3s*60000], y=[H_tot], mode="markers",
                                  marker=dict(color="#ef5350", size=9), name="OP"), row=1, col=1)
        fig.add_trace(go.Scatter(x=Qlpm_c, y=eta_c*100, mode="lines",
                                  line=dict(color="#66bb6a", width=2), name="Efficiency"), row=1, col=2)
        fig.add_trace(go.Scatter(x=Qlpm_c, y=P_c, mode="lines",
                                  line=dict(color="#ffa726", width=2), name="Power"), row=2, col=1)
        fig.add_trace(go.Bar(x=[r[0] for r in ranking], y=[r[1] for r in ranking],
                              marker_color=["#66bb6a","#4fc3f7","#ffa726","#ef5350"],
                              name="Score"), row=2, col=2)
        fig.update_layout(template=tmpl, height=580, showlegend=False,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#12151f",
                          font=dict(color="#b0bec5"))
        for ann in fig.layout.annotations:
            ann.font.color = "#cfd8dc"
        st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # SECTION 9 — DOWNLOADS
    # =========================================================================
    divider()
    sec("📄  SECTION 9 — DOWNLOAD RESULTS", "gray")

    inputs_d = {
        "Fluid":               fluid,
        "Temperature (°C)":    T_C,
        "Density (kg/m³)":     f"{rho:.3f}",
        "Viscosity (Pa·s)":    f"{mu:.4e}",
        "Flow Rate":           f"{Q_val} {Q_unit}",
        "Flow Rate (m³/s)":    f"{Q_m3s:.6f}",
        "Total Head (m)":      H_tot,
        "Pipe Dia. (mm)":      D_mm,
        "Pipe Length (m)":     pipe_L,
        "Pipe Material":       pipe_mat,
        "Pump Efficiency (%)": f"{eta_p*100:.1f}",
        "Motor Efficiency (%)":f"{eta_motor*100:.1f}",
        "Safety Factor":       SF,
    }
    results_d = {
        "Selected Pump":          selected,
        "Hydraulic Power (kW)":   f"{P_hyd/1000:.4f}",
        "Shaft Power (kW)":       f"{P_sh/1000:.4f}",
        "Motor Sized Power (kW)": f"{P_mot_s/1000:.4f}",
        "Overall Efficiency (%)": f"{eta_ov*100:.2f}",
        "Pipe Velocity (m/s)":    f"{v_pipe:.4f}",
        "Reynolds Number":        f"{Re:,.0f}",
        "Friction Factor":        f"{f_D:.6f}",
        "Friction Head Loss (m)": f"{hf_maj+hf_min:.4f}",
        "Specific Speed Ns":      f"{Ns:.2f}",
        "Estimated RPM":          N_rpm,
        "Impeller Dia. (mm)":     f"{D_imp_mm:.0f}",
        "Shaft Dia. min (mm)":    f"{d_sh_mm:.1f}",
        "Torque (N·m)":           f"{torque:.3f}",
        "Total ΔP (Pa)":          f"{dP_tot:.1f}",
    }
    calcs_d = {
        "A_pipe = πD²/4 (m²)":            f"{A_pipe:.6f}",
        "v = Q/A (m/s)":                   f"{v_pipe:.5f}",
        "Re = ρvD/μ":                      f"{Re:.1f}",
        "f (Colebrook-White)":             f"{f_D:.6f}",
        "h_f,major (m)":                   f"{hf_maj:.5f}",
        "h_f,minor (m)":                   f"{hf_min:.5f}",
        "P_hyd = ρgQH (kW)":               f"{P_hyd/1000:.5f}",
        "P_shaft = P_hyd/η (kW)":          f"{P_sh/1000:.5f}",
        "P_motor,sized (kW)":              f"{P_mot_s/1000:.5f}",
        "η_overall = η_pump×η_motor":      f"{eta_ov:.5f}",
        "Ns = N√Q/H^0.75":                 f"{Ns:.3f}",
        "Torque (N·m)":                    f"{torque:.4f}",
        "Impeller D₂ (mm)":                f"{D_imp_mm:.1f}",
        "ΔP_total (Pa)":                   f"{dP_tot:.2f}",
    }

    report_txt = build_report(inputs_d, results_d, calcs_d)
    csv_data   = build_csv(inputs_d, results_d, Q_c, H_c, eta_c, P_c)
    json_data  = json.dumps({"inputs": inputs_d, "results": results_d,
                              "calculations": calcs_d}, indent=2)

    dl1, dl2, dl3 = st.columns(3)
    tstamp = datetime.now().strftime("%Y%m%d_%H%M")
    with dl1:
        st.download_button("📄 Download Report (.txt)", data=report_txt.encode(),
                            file_name=f"pump_report_{tstamp}.txt", mime="text/plain",
                            use_container_width=True)
    with dl2:
        st.download_button("📊 Download Data (.csv)", data=csv_data.encode(),
                            file_name=f"pump_data_{tstamp}.csv", mime="text/csv",
                            use_container_width=True)
    with dl3:
        st.download_button("🗂️ Download JSON", data=json_data.encode(),
                            file_name=f"pump_design_{tstamp}.json", mime="application/json",
                            use_container_width=True)

    _show_refs()


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCES SECTION
# ─────────────────────────────────────────────────────────────────────────────
def _show_refs():
    divider()
    sec("📚  ENGINEERING REFERENCES & STANDARDS", "gray")
    refs = [
        ("[1]", "Hydraulic Institute Standards",
         "ANSI/HI 1.1-1.6 (Centrifugal), 2.1-2.5, 3.1-3.5 (Gear), 6.1-6.5, 7.1-7.5",
         "HI, 2020"),
        ("[2]", "Perry's Chemical Engineers' Handbook",
         "§6 Fluid Dynamics, §10 Transport & Storage of Fluids",
         "McGraw-Hill, 9th Ed., 2018"),
        ("[3]", "McCabe, Smith & Harriott",
         "Unit Operations of Chemical Engineering — Chapter 7: Pumps & Compressors",
         "McGraw-Hill, 7th Ed., 2005"),
        ("[4]", "Crane Technical Paper No. 410",
         "Flow of Fluids Through Valves, Fittings and Pipe",
         "Crane Co., 2013"),
        ("[5]", "Karassik, Messina, Cooper & Heald",
         "Pump Handbook — Chapters 1–3: Types, Selection, Performance",
         "McGraw-Hill, 4th Ed., 2008"),
        ("[6]", "ISO 5199 / ISO 9908",
         "Technical Specifications for Centrifugal Pumps — Classes I, II, III",
         "ISO, 2002"),
        ("[7]", "API 610 / API 674",
         "Centrifugal Pumps & Positive Displacement Pumps for Petroleum Industry",
         "American Petroleum Institute, 12th Ed., 2021"),
        ("[8]", "Moody, L.F.",
         "Friction Factors for Pipe Flow — ASME Transactions Vol. 66, pp. 671-684",
         "ASME, 1944"),
        ("[9]", "ISO 281",
         "Rolling Bearings — Dynamic Load Ratings and Rating Life",
         "ISO, 2007"),
        ("[10]","Chilton, C.H.",
         "Six-tenths Factor for Cost Estimation",
         "Chemical Engineering, 1949"),
    ]
    for ref in refs:
        st.markdown(f"""
        <div class="ref-row">
            <b style="color:#4fc3f7;">{ref[0]}</b> &nbsp;
            <b style="color:#cfd8dc;">{ref[1]}</b> — {ref[2]}
            &nbsp;<span style="color:#546e7a;">({ref[3]})</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:20px;color:#546e7a;font-size:.80rem;text-align:center;">
        ⚠️ DISCLAIMER: This application provides engineering estimates only.
        All designs must be reviewed and stamped by a licensed Professional Engineer (P.Eng / PE).
        Results are not suitable as the sole basis for procurement, construction, or safety decisions.<br><br>
        Pump Design Tool v1.0 &nbsp;|&nbsp; Powered by Streamlit + Plotly
        &nbsp;|&nbsp; © 2024
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
