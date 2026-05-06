# =============================================================================
# app.py  —  AI-Assisted Pump Design & Selection Platform  v3.1
# FIXES: session_state AI buttons | Word/PDF/CSV export | developer header |
#         theme headings always visible
# Run:  streamlit run app.py
# =============================================================================
import streamlit as st
import numpy as np
import math, json, io
from datetime import datetime
import datetime as _dt_module

st.set_page_config(
    page_title="AI Pump Design Platform",
    page_icon="⚙️", layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local imports ─────────────────────────────────────────────────────────────
from config.settings import (THEMES, FLUID_DATA, PUMP_TYPES,
                              PIPE_ROUGHNESS, next_motor_size, g)
from utils.validators    import validate_inputs
from utils.unit_converter import flow_to_m3s, FLOW_TO_M3S
from utils.exporters     import build_csv, build_docx, build_pdf
from calculations.losses import (pipe_area, flow_velocity, reynolds_number,
                                  friction_factor, total_friction_loss,
                                  major_loss, minor_loss)
from calculations.power_calc import (hydraulic_power, shaft_power,
                                     motor_input_power, overall_efficiency,
                                     shaft_torque, specific_speed,
                                     motor_size, annual_energy_cost)
from calculations.npsh_calc  import npsh_available, npsh_required, cavitation_check
from modules.pump_selector   import select_pump, PUMP_INFO
import modules.centrifugal   as cent
import modules.reciprocating as recip
import modules.plunger       as plunger
import modules.gear          as gear
from graphs.centrifugal_plots  import (hq_with_system, efficiency_curve,
                                       power_curve, combined_dashboard)
from graphs.performance_curves import (recip_dashboard, plunger_dashboard,
                                       gear_dashboard)
from ai.groq_client import get_client
from ai.advisor     import get_selection_advice, get_cavitation_advice, ask_question
from ui.theme_manager import inject_theme
from ui.sidebar       import render_sidebar

# ── SESSION STATE INIT ────────────────────────────────────────────────────────
for key in ("ai_selection_text", "ai_question_text", "calc_done",
            "res_s", "sp", "inputs_d", "results_d", "sp_d",
            "Q_m3s","Q_m3h","H_tot","rho","mu","mu_cP","Pv","eta_p",
            "pump_type","N_rpm","f_D","hf","P_hyd","P_sh","P_mot",
            "eta_ov","torq","mot_kw","v","Re","D_m","z_static",
            "ranking","fluid","cfg","th"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
cfg = render_sidebar()
st.session_state["cfg"] = cfg
th  = cfg["th"]
st.session_state["th"] = th
inject_theme(th)
eps  = PIPE_ROUGHNESS[cfg["pipe_mat"]]
tmpl = "plotly_dark" if cfg["dark_graphs"] else "plotly_white"
th_plot = {**th, "plotly_tmpl": tmpl}
ai_client = get_client(cfg["groq_key"]) if cfg["groq_key"] else None

# =============================================================================
# HELPERS
# =============================================================================
def rgba(hex6, alpha):
    h = hex6.lstrip("#")
    r, gv, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{gv},{b},{alpha})"

def sec(label, color=None):
    c = color or th["accent"]
    st.markdown(f'<div class="sec-heading" style="color:{c};border-color:{c};">{label}</div>',
                unsafe_allow_html=True)

def divider():
    st.markdown('<div class="fancy-div"></div>', unsafe_allow_html=True)

def mcard(label, value, unit=""):
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
    </div>""", unsafe_allow_html=True)

def cbox(formula="", sub="", result="", params: dict = None, title: str = ""):
    """
    3-column calculation box.
    title:  WHAT is being calculated — shown as banner on top
    params: { "D (pipe diameter)": "0.1000 m" }  
            → Symbol bold yellow | (description) gray | = cyan | value white
    """
    if params:
        # Build parameter list HTML
        left_html = ""
        for sym, val in params.items():
            if "(" in sym:
                s_name = sym[:sym.index("(")].strip()
                s_desc = sym[sym.index("("):]  # includes brackets
            else:
                s_name = sym; s_desc = ""
            left_html += (
                f'<div style="margin-bottom:7px;line-height:1.4;">'
                f'<span style="color:#ffd740;font-weight:900;font-size:.93rem;">{s_name}</span>'
                f'<span style="color:#666;font-size:.76rem;font-style:italic;"> {s_desc}</span>'
                f'<br>'
                f'<span style="color:#8be9fd;font-weight:700;"> = </span>'
                f'<span style="color:#f8f8f2;font-weight:600;font-size:.91rem;">{val}</span>'
                f'</div>'
            )

        # Title banner (what is calculated)
        banner = (
            f'<div style="background:linear-gradient(90deg,rgba(255,215,64,0.18),'
            f'rgba(80,250,123,0.08));padding:7px 16px;'
            f'border-bottom:1px solid rgba(255,215,64,0.2);'
            f'font-size:.80rem;font-weight:900;color:#ffd740;'
            f'letter-spacing:.8px;text-transform:uppercase;">'
            f'🔢 Calculating: {title}</div>'
        ) if title else ""

        mid_html = (
            f'<span class="cf" style="font-size:.92rem;display:block;margin-bottom:8px;">{formula}</span>'
            f'<span class="cs" style="font-size:.88rem;display:block;">{sub}</span>'
        )

        st.markdown(f"""
<div class="calc-box" style="padding:0;margin:12px 0;">
  {banner}
  <div style="display:grid;grid-template-columns:1.15fr 2fr 1fr;min-height:90px;">
    <div style="padding:12px 14px;border-right:1px solid rgba(255,255,255,0.07);
                background:rgba(255,215,64,0.04);border-radius:{'0' if title else '8px'} 0 0 8px;">
      <div style="font-size:.66rem;color:#777;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:9px;font-weight:700;">📌 Parameters</div>
      {left_html}
    </div>
    <div style="padding:12px 15px;border-right:1px solid rgba(255,255,255,0.07);">
      <div style="font-size:.66rem;color:#777;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:9px;font-weight:700;">📐 Formula → Substitution</div>
      {mid_html}
    </div>
    <div style="padding:12px 13px;display:flex;flex-direction:column;
                justify-content:center;background:rgba(80,250,123,0.05);
                border-radius:0 {'0' if title else '8px'} 8px 0;">
      <div style="font-size:.66rem;color:#777;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:9px;font-weight:700;">✅ Result</div>
      <span class="cr" style="font-size:1.02rem;line-height:1.55;">{result}</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    else:
        # Simple 1-column box (fallback)
        banner = (
            f'<div style="font-size:.76rem;color:#ffd740;font-weight:900;'
            f'text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px;">'
            f'🔢 {title}</div>'
        ) if title else ""
        st.markdown(f"""<div class="calc-box">
            {banner}
            <span class="cf">{formula}</span><br>
            <span class="cs">{sub}</span><br>
            <span class="cr">{result}</span>
        </div>""", unsafe_allow_html=True)

def info_box(msg):
    st.markdown(f'<div class="info-box">ℹ️ {msg}</div>', unsafe_allow_html=True)
def warn_box(msg):
    st.markdown(f'<div class="warn-box">⚠️ {msg}</div>', unsafe_allow_html=True)
def success_box(msg):
    st.markdown(f'<div class="success-box">✅ {msg}</div>', unsafe_allow_html=True)
def danger_box(msg):
    st.markdown(f'<div class="danger-box">🚨 {msg}</div>', unsafe_allow_html=True)

# =============================================================================
# DEVELOPER HEADER BANNER
# =============================================================================
st.markdown(f"""
<div class="dev-banner">
    <div class="dev-developed-by">⚙️ &nbsp; Developed by &nbsp; ⚙️</div>
    <div class="dev-name">Zunair Shahzad</div>
    <div class="dev-dept">Chemical Engineering</div>
    <div class="dev-uni">UET Lahore (New Campus)</div>
    <div class="dev-batch">2022 – 2026</div>
</div>""", unsafe_allow_html=True)

# PLATFORM HEADER
st.markdown(f"""
<div style="text-align:center;padding:10px 0 10px 0;">
  <div style="font-size:2.6rem;font-weight:900;letter-spacing:2px;
       background:linear-gradient(90deg,{th['grad_a']},{th['grad_b']},{th['accent3']});
       -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
      ⚙️ AI-ASSISTED PUMP DESIGN PLATFORM
  </div>
  <div style="opacity:.7;font-size:.97rem;margin-top:6px;color:{th['text']};">
      Professional Engineering System &nbsp;|&nbsp;
      Centrifugal · Reciprocating · Plunger · Gear &nbsp;|&nbsp;
      Groq AI Advisory &nbsp;|&nbsp; API 610 · HI · Perry's
  </div>
</div>""", unsafe_allow_html=True)

# Workflow steps
steps = [("📥","Input"),("💡","Select"),("🔧","Params"),
         ("⚡","Calculate"),("📊","Results"),("📈","Graphs"),("🎛️","VFD"),("🤖","AI"),("📄","Export")]
cols = st.columns(9)
for col, (ic, lb) in zip(cols, steps):
    col.markdown(
        f'<div style="text-align:center;background:{th["card_bg"]};border-radius:8px;'
        f'padding:10px 2px;font-size:.75rem;color:{th["text"]};">'
        f'{ic}<br><b>{lb}</b></div>', unsafe_allow_html=True)
divider()

# =============================================================================
# SECTION 1 — PROCESS INPUT PARAMETERS
# =============================================================================
sec("📥  SECTION 1 — PROCESS INPUT PARAMETERS", th["accent"])
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("##### 🌊 Flow Conditions")
    Q_val  = st.number_input("Flow Rate Value", 0.1, 50000.0, 50.0, 1.0)
    Q_unit = st.selectbox("Flow Unit", list(FLOW_TO_M3S.keys()))
    H_user = st.number_input("Total Dynamic Head TDH (m)", 1.0, 10000.0, 30.0, 0.5)
    D_mm   = st.number_input("Pipe Internal Diameter (mm)", 10.0, 3000.0, 100.0, 5.0)

with c2:
    st.markdown("##### 🧪 Fluid Properties")
    fluid  = st.selectbox("Fluid Type", list(FLUID_DATA.keys()))
    T_C    = st.number_input("Temperature (°C)", -30.0, 400.0, 25.0, 5.0)
    rho_c = mu_c = None
    if fluid == "Custom":
        rho_c = st.number_input("Density ρ (kg/m³)", 400.0, 5000.0, 1000.0)
        mu_c  = st.number_input("Viscosity μ (mPa·s)", 0.01, 500000.0, 1.0)
    eta_p  = st.slider("Pump Efficiency η (%)", 40, 95, 75) / 100

with c3:
    st.markdown("##### 🔩 Pump Selection")
    pump_type = st.selectbox("Pump Type", PUMP_TYPES)
    N_rpm     = st.number_input("Pump Speed (RPM)", 100, 7200,
                                 1450 if pump_type == "Centrifugal" else 200, 50)
    z_static  = st.number_input("Static Head Component (m)", 0.0, 500.0,
                                  min(H_user * 0.4, H_user), 0.5)

# =============================================================================
# SECTION 1b — MINOR LOSSES / FITTING SELECTOR (Interactive Panel)
# =============================================================================
divider()
sec("🔩  SECTION 1b — PIPE FITTINGS & MINOR LOSSES", th["accent3"])
st.markdown(
    f"<div style='font-size:.88rem;color:{th['text']};margin-bottom:12px;'>"
    "Select your pipe fittings by category. K-values auto-calculated from "
    "<b>Crane Technical Paper No. 410</b> standard database. "
    "Use the <b>← Back</b> button to return and select from another category.</div>",
    unsafe_allow_html=True)

from utils.fittings import FITTINGS, ALL_FITTINGS, calc_K_total

# Session state for fitting selections and UI state
if "fitting_selections" not in st.session_state:
    st.session_state["fitting_selections"] = {}   # {fname: qty}
if "fitting_cat" not in st.session_state:
    st.session_state["fitting_cat"] = None        # currently open category

cat_names = list(FITTINGS.keys())

fit_left, fit_right = st.columns([1, 1.6])

with fit_left:
    # ── Category browser ──────────────────────────────────────────────────────
    st.markdown(f"<div style='font-size:.80rem;color:{th['accent2']};font-weight:700;"
                "text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;'>"
                "① Choose a Category</div>", unsafe_allow_html=True)

    if st.session_state["fitting_cat"] is None:
        # Show category list — styled buttons with icons
        CAT_ICONS = {
            "Elbows & Bends":           "↩️",
            "Tees & Branches":          "⑃",
            "Valves":                   "🔧",
            "Pipe Entries & Exits":     "⬡",
            "Reducers & Increasers":    "⊳",
            "Strainers & Filters":      "⊟",
            "Flow Meters & Instruments":"📡",
            "Process Equipment":        "🏭",
        }
        for cat in cat_names:
            count = sum(1 for fn in FITTINGS[cat]
                        if st.session_state["fitting_selections"].get(fn, 0) > 0)
            icon = CAT_ICONS.get(cat, "🔩")
            badge_html = (
                f"<span style='background:#50fa7b;color:#0d1117;border-radius:10px;"
                f"padding:1px 7px;font-size:.70rem;font-weight:900;"
                f"margin-left:6px;'>✓{count}</span>"
            ) if count > 0 else ""
            # Render label + button together
            st.markdown(
                f"<div style='background:{th['card_bg']};border:1px solid {th['border']};"
                f"border-radius:8px;padding:2px 4px;margin:4px 0;"
                f"transition:all .15s;'>",
                unsafe_allow_html=True
            )
            if st.button(
                f"{icon}  {cat}" + (f"  ✅{count}" if count > 0 else ""),
                key=f"cat_btn_{cat}",
                use_container_width=True,
            ):
                st.session_state["fitting_cat"] = cat
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Show fittings in selected category
        cat = st.session_state["fitting_cat"]
        st.markdown(f"<div style='background:{th['card_bg']};padding:8px 12px;"
                    f"border-radius:8px;margin-bottom:10px;color:{th['accent']};font-weight:700;'>"
                    f"{cat}</div>", unsafe_allow_html=True)

        if st.button("← Back to Categories", key="back_btn", use_container_width=True):
            st.session_state["fitting_cat"] = None
            st.rerun()

        st.markdown(f"<div style='font-size:.78rem;color:{th['metric_lbl']};margin:6px 0 10px 0;'>"
                    "② Click + to add each fitting:</div>", unsafe_allow_html=True)

        for fname, fdata in FITTINGS[cat].items():
            qty = st.session_state["fitting_selections"].get(fname, 0)
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.markdown(
                    f"<div style='font-size:.83rem;color:{th['text']};padding:6px 0;'>"
                    f"<b style='color:{th['accent']};'>K={fdata['K']}</b>  {fname}</div>",
                    unsafe_allow_html=True)
            with col_b:
                if st.button("➕", key=f"add_{fname}", help=fdata["desc"]):
                    st.session_state["fitting_selections"][fname] = qty + 1
                    st.rerun()
            with col_c:
                if qty > 0:
                    if st.button(f"✖ {qty}", key=f"rem_{fname}"):
                        if qty > 1:
                            st.session_state["fitting_selections"][fname] = qty - 1
                        else:
                            del st.session_state["fitting_selections"][fname]
                        st.rerun()

with fit_right:
    # ── Selected fittings table ───────────────────────────────────────────────
    st.markdown(f"<div style='font-size:.80rem;color:{th['accent2']};font-weight:700;"
                "text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;'>"
                "③ Selected Fittings & K Breakdown</div>", unsafe_allow_html=True)

    sel = {k: v for k, v in st.session_state["fitting_selections"].items() if v > 0}
    K_total_live, breakdown = calc_K_total(sel)

    # Update session state so sidebar can read it
    st.session_state["K_fit_total"] = K_total_live

    if breakdown:
        import pandas as pd
        rows_html = ""
        for row in breakdown:
            rows_html += (
                f"<tr>"
                f"<td style='padding:6px 10px;color:{th['text']};'>{row['Fitting']}</td>"
                f"<td style='padding:6px 10px;text-align:center;color:{th['accent2']};font-weight:700;'>{row['Qty']}</td>"
                f"<td style='padding:6px 10px;text-align:center;color:#ffd740;'>{row['K each (Crane TP-410)']}</td>"
                f"<td style='padding:6px 10px;text-align:center;color:#50fa7b;font-weight:700;'>{row['K subtotal']}</td>"
                f"</tr>"
            )

        st.markdown(f"""
<div style='background:{th["card_bg"]};border-radius:10px;overflow:hidden;
            border:1px solid {th["border"]};'>
  <table style='width:100%;border-collapse:collapse;font-size:.83rem;'>
    <thead>
      <tr style='background:{th["accent"]}22;'>
        <th style='padding:8px 10px;text-align:left;color:{th["accent"]};'>Fitting</th>
        <th style='padding:8px 10px;text-align:center;color:{th["accent"]};'>Qty</th>
        <th style='padding:8px 10px;text-align:center;color:{th["accent"]};'>K each</th>
        <th style='padding:8px 10px;text-align:center;color:{th["accent"]};'>K sub</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
    <tfoot>
      <tr style='background:{th["accent"]}33;border-top:2px solid {th["accent"]};'>
        <td colspan='3' style='padding:8px 10px;font-weight:800;color:{th["accent"]};'>
          Σ K TOTAL</td>
        <td style='padding:8px 10px;text-align:center;font-weight:900;
                   font-size:1.1rem;color:#50fa7b;'>{K_total_live:.3f}</td>
      </tr>
    </tfoot>
  </table>
</div>""", unsafe_allow_html=True)

        # Clear all button
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("🗑️ Clear All Fittings", use_container_width=True):
                st.session_state["fitting_selections"] = {}
                st.session_state["K_fit_total"] = 0.0
                st.rerun()
        with cc2:
            # Individual K detail toggle
            with st.expander("📋 View Full Details"):
                for row in breakdown:
                    st.markdown(
                        f"**{row['Fitting']}** (×{row['Qty']})  \n"
                        f"K each = `{row['K each (Crane TP-410)']}` → "
                        f"K sub = `{row['K subtotal']}`  \n"
                        f"_{row['Description']}_"
                    )
    else:
        st.markdown(f"""
<div style='background:{th["card_bg"]};border-radius:10px;padding:28px 20px;
            text-align:center;border:1px dashed {th["border"]};'>
  <div style='font-size:2rem;margin-bottom:10px;'>🔩</div>
  <div style='color:{th["text"]};font-size:.90rem;'>
    No fittings selected yet.<br>
    <span style='color:{th["metric_lbl"]};font-size:.82rem;'>
    Choose a category on the left → click ➕ to add fittings</span>
  </div>
  <div style='margin-top:14px;font-size:.80rem;color:{th["accent"]};font-weight:700;'>
    Σ K = 0.000
  </div>
</div>""", unsafe_allow_html=True)

# Use live K_total from fitting panel
K_fit_live = st.session_state.get("K_fit_total", cfg["K_fit"])

# ── Conversions & fluid props ─────────────────────────────────────────────────
Q_m3s = flow_to_m3s(Q_val, Q_unit); Q_m3h = Q_m3s * 3600; D_m = D_mm / 1000

if fluid == "Custom":
    rho = rho_c; mu = mu_c * 1e-3; Pv = 2337
else:
    fd  = FLUID_DATA[fluid]
    rho = fd["rho"] * (1 - 0.00065 * (T_C - 20))
    mu  = fd["mu"] * math.exp(-0.025 * max(T_C - 20, 0)) if fluid in (
        "Water","Hot Water (80°C)","Seawater") else fd["mu"]
    Pv  = fd["Pv"]
mu_cP = mu * 1000

errs, warns = validate_inputs(Q_m3s, H_user, rho, mu, D_m)
for e in errs: st.error(f"❌ {e}")
if errs: st.stop()
for w in warns: warn_box(w)

# Pre-calc
A_p   = pipe_area(D_m); v = flow_velocity(Q_m3s, D_m)
Re    = reynolds_number(rho, v, D_m, mu); f_D = friction_factor(Re, D_m, eps)
hf    = total_friction_loss(f_D, cfg["pipe_L"], D_m, v, K_fit_live)
H_tot = H_user
P_hyd = hydraulic_power(Q_m3s, H_tot, rho); P_sh = shaft_power(P_hyd, eta_p)
P_mot = motor_input_power(P_sh, cfg["eta_motor"], cfg["SF"])
eta_ov= overall_efficiency(eta_p, cfg["eta_motor"]); torq = shaft_torque(P_sh, N_rpm)
mot_kw= motor_size(P_mot)

# =============================================================================
# SECTION 2 — SMART PUMP SELECTION
# =============================================================================
divider()
sec("💡  SECTION 2 — SMART PUMP SELECTION ENGINE", th["accent2"])
ranking = select_pump(Q_m3s, H_tot, rho, mu, T_C, fluid)

card_cols = st.columns(4)
for i, (pt, sc, reasons) in enumerate(ranking):
    info = PUMP_INFO.get(pt, {})
    cls  = "pump-card top" if i == 0 else "pump-card"
    badge = "⭐ TOP REC — " if i == 0 else ""
    with card_cols[i]:
        st.markdown(f"""<div class="{cls}">
            <div class="pump-card-title">{info.get('icon','⚙️')} {pt}</div>
            <div style="font-size:.72rem;color:{th['metric_lbl']};margin-bottom:5px;">
                Score: {sc}/200</div>
            <div class="pump-card-desc">{badge}{info.get('desc','')[:110]}…</div>
            <div class="pump-card-meta"><b>Range:</b> {info.get('range','—')}</div>
            <div class="pump-card-meta"><b>Std:</b> {info.get('std','—')}</div>
            <div class="pump-card-meta" style="margin-top:5px;font-size:.75rem;">
                {', '.join(reasons[:3])}</div>
        </div>""", unsafe_allow_html=True)

top_rec = ranking[0][0]
if pump_type == top_rec:
    success_box(f"Selected pump <b>{pump_type}</b> matches the top recommendation.")
else:
    warn_box(f"Selected <b>{pump_type}</b> differs from recommended <b>{top_rec}</b>. "
             "Use AI Advisor below for guidance.")

# =============================================================================
# SECTION 3 — PUMP-SPECIFIC PARAMETERS
# =============================================================================
divider()
sec(f"🔧  SECTION 3 — {pump_type.upper()} SPECIFIC PARAMETERS", th["accent3"])

sp = {}
with st.expander(f"Configure {pump_type} Parameters", expanded=False):
    if pump_type == "Centrifugal":
        ca, cb = st.columns(2)
        with ca:
            sp["phi"]      = st.slider("Head Coefficient φ", 0.70, 0.95, 0.85, 0.01)
            sp["D_imp_mm"] = st.number_input("Impeller Dia. (mm, 0=auto)", 0.0, 2500.0, 0.0, 10.0)
        with cb:
            st.markdown(f"<span style='color:{th['text']};'>Affinity laws auto-calculated at 90% speed.</span>",
                        unsafe_allow_html=True)

    elif pump_type == "Reciprocating":
        ca, cb = st.columns(2)
        with ca:
            sp["piston_dia_mm"] = st.number_input("Piston Diameter (mm)", 10.0, 600.0, 80.0, 5.0)
            sp["stroke_mm"]     = st.number_input("Stroke Length (mm)", 10.0, 600.0, 120.0, 10.0)
        with cb:
            sp["n_cyl"]    = st.selectbox("Number of Cylinders", [1,2,3,4,5], index=2)
            sp["slip_pct"] = st.slider("Slip Factor (%)", 0.0, 15.0, 3.5, 0.5)

    elif pump_type == "Plunger":
        ca, cb = st.columns(2)
        with ca:
            sp["plunger_dia_mm"] = st.number_input("Plunger Diameter (mm)", 5.0, 300.0, 40.0, 5.0)
            sp["stroke_mm"]      = st.number_input("Stroke Length (mm)", 10.0, 600.0, 100.0, 10.0)
        with cb:
            sp["n_pl"]     = st.selectbox("Number of Plungers", [1,2,3,4,5], index=2)
            sp["slip_pct"] = st.slider("Slip Factor (%)", 0.0, 10.0, 2.0, 0.5)

    elif pump_type == "Gear":
        ca, cb = st.columns(2)
        with ca:
            sp["disp_cc_rev"] = st.number_input("Displacement (cc/rev)", 0.1, 10000.0, 80.0, 5.0)
            sp["vol_eff_pct"] = st.slider("Volumetric Efficiency (%)", 60, 98, 90, 1)
        with cb:
            st.markdown(f"<span style='color:{th['text']};'>Viscosity correction auto-applied for μ = {mu_cP:.1f} cP</span>",
                        unsafe_allow_html=True)

# =============================================================================
# CALCULATE BUTTON
# =============================================================================
divider()
_, btn_col, _ = st.columns([1,2,1])
with btn_col:
    calc_clicked = st.button("⚡  RUN FULL ENGINEERING CALCULATION",
                              use_container_width=True, type="primary")

if calc_clicked:
    st.session_state["calc_done"] = True
    # Run pump-specific calculations
    if pump_type == "Centrifugal":
        res_s = cent.design(Q_m3s, H_tot, rho, mu, N_rpm,
                            sp.get("phi", 0.85), sp.get("D_imp_mm") or None)
    elif pump_type == "Reciprocating":
        res_s = recip.design(Q_m3s, H_tot, rho,
                             sp["piston_dia_mm"], sp["stroke_mm"],
                             N_rpm, sp["n_cyl"], sp["slip_pct"])
    elif pump_type == "Plunger":
        res_s = plunger.design(Q_m3s, H_tot, rho,
                               sp["plunger_dia_mm"], sp["stroke_mm"],
                               N_rpm, sp["n_pl"], sp["slip_pct"])
    elif pump_type == "Gear":
        res_s = gear.design(Q_m3s, H_tot, rho, mu,
                             sp["disp_cc_rev"], sp["vol_eff_pct"], N_rpm)
    else:
        res_s = {}

    # Save everything to session_state
    st.session_state.update({
        "res_s": res_s, "sp": sp,
        "Q_m3s": Q_m3s, "Q_m3h": Q_m3h, "H_tot": H_tot,
        "rho": rho, "mu": mu, "mu_cP": mu_cP, "Pv": Pv,
        "eta_p": eta_p, "pump_type": pump_type, "N_rpm": N_rpm,
        "f_D": f_D, "hf": hf, "P_hyd": P_hyd, "P_sh": P_sh,
        "P_mot": P_mot, "eta_ov": eta_ov, "torq": torq, "mot_kw": mot_kw,
        "v": v, "Re": Re, "D_m": D_m, "z_static": z_static,
        "D_mm_input": D_mm,
        "ranking": ranking, "fluid": fluid,
        "inputs_d": {
            "Pump Type": pump_type, "Fluid": fluid,
            "Temperature (°C)": T_C, "Density (kg/m³)": f"{rho:.3f}",
            "Viscosity (mPa·s)": f"{mu_cP:.3f}",
            f"Flow Rate ({Q_unit})": Q_val, "Flow (m³/s)": f"{Q_m3s:.6f}",
            "TDH (m)": H_tot, "Pipe Dia (mm)": D_mm,
            "Pipe Length (m)": cfg["pipe_L"], "Pipe Material": cfg["pipe_mat"],
            "Pump η (%)": f"{eta_p*100:.1f}",
            "Motor η (%)": f"{cfg['eta_motor']*100:.1f}",
            "Safety Factor": cfg["SF"], "N (RPM)": N_rpm,
        },
        "results_d": {
            "P_hyd (kW)": f"{P_hyd/1000:.4f}", "P_shaft (kW)": f"{P_sh/1000:.4f}",
            "P_motor (kW)": f"{P_mot/1000:.4f}", "Motor std. (kW)": mot_kw,
            "η_overall (%)": f"{eta_ov*100:.2f}", "v (m/s)": f"{v:.4f}",
            "Re": f"{Re:,.0f}", "f": f"{f_D:.6f}", "h_f (m)": f"{hf:.4f}",
            "Torque (N·m)": f"{torq:.3f}",
        },
        "sp_d": {k: (f"{vv:.4f}" if isinstance(vv,float) else str(vv))
                 for k,vv in res_s.items()},
    })

if not st.session_state["calc_done"]:
    info_box("Configure all parameters above, then press <b>Run Full Engineering Calculation</b>.")
    st.stop()

# ── Restore from session state ─────────────────────────────────────────────────
res_s     = st.session_state["res_s"]
sp        = st.session_state["sp"]
Q_m3s     = st.session_state["Q_m3s"]
Q_m3h     = st.session_state["Q_m3h"]
H_tot     = st.session_state["H_tot"]
rho       = st.session_state["rho"]
mu        = st.session_state["mu"]
mu_cP     = st.session_state["mu_cP"]
Pv        = st.session_state["Pv"]
eta_p     = st.session_state["eta_p"]
pump_type = st.session_state["pump_type"]
N_rpm     = st.session_state["N_rpm"]
f_D       = st.session_state["f_D"]
hf        = st.session_state["hf"]
P_hyd     = st.session_state["P_hyd"]
P_sh      = st.session_state["P_sh"]
P_mot     = st.session_state["P_mot"]
eta_ov    = st.session_state["eta_ov"]
torq      = st.session_state["torq"]
mot_kw    = st.session_state["mot_kw"]
v         = st.session_state["v"]
Re        = st.session_state["Re"]
D_mm_input= st.session_state.get("D_mm_input", D_mm)
D_m_ss    = st.session_state["D_m"]
z_static  = st.session_state["z_static"]
ranking   = st.session_state["ranking"]
fluid     = st.session_state["fluid"]
inputs_d  = st.session_state["inputs_d"]
results_d = st.session_state["results_d"]
sp_d      = st.session_state["sp_d"]

# =============================================================================
# SECTION 4 — DETAILED CALCULATIONS
# =============================================================================
divider()
sec("⚡  SECTION 4 — DETAILED ENGINEERING CALCULATIONS", th["accent"])

with st.expander("📐 4.1  Hydraulic — Pipe Flow & Losses", expanded=False):
    from utils.fittings import calc_K_total
    hf_maj = major_loss(f_D, cfg["pipe_L"], D_m_ss, v)
    hf_min = minor_loss(K_fit_live, v)

    cbox(
        title="Pipe Cross-Sectional Area",
        formula="A = π · D² / 4",
        sub=f"A = π × ({D_m_ss:.4f})² / 4",
        result=f"A = {A_p:.6f} m²",
        params={"D (pipe internal diameter)": f"{D_m_ss:.4f} m",
                "π (pi constant)":            "3.14159"}
    )
    cbox(
        title="Flow Velocity",
        formula="v = Q / A",
        sub=f"v = {Q_m3s:.5f} / {A_p:.6f}",
        result=f"v = {v:.4f} m/s",
        params={"Q (volumetric flow rate)": f"{Q_m3s:.5f} m³/s",
                "A (pipe cross-section)":   f"{A_p:.6f} m²"}
    )
    if v > 4.0:
        warn_box(f"Velocity {v:.2f} m/s > 4 m/s — HI §1.3.4 recommends ≤ 4 m/s. Increase pipe diameter.")

    regime = "Turbulent" if Re > 4000 else ("Transitional" if Re > 2300 else "Laminar")
    cbox(
        title="Reynolds Number & Flow Regime",
        formula="Re = ρ · v · D / μ",
        sub=f"Re = {rho:.2f} × {v:.4f} × {D_m_ss:.4f} / {mu:.4e}",
        result=f"Re = {Re:,.0f}  →  {regime} flow",
        params={"ρ (fluid density)":       f"{rho:.2f} kg/m³",
                "v (flow velocity)":       f"{v:.4f} m/s",
                "D (pipe diameter)":       f"{D_m_ss:.4f} m",
                "μ (dynamic viscosity)":   f"{mu:.4e} Pa·s"}
    )

    eps_val = PIPE_ROUGHNESS[cfg["pipe_mat"]]
    cbox(
        title="Darcy-Weisbach Friction Factor",
        formula="1/√f = −2 log₁₀[ ε/(3.7D) + 2.51/(Re√f) ]  [Colebrook-White]",
        sub=f"ε/D = {eps_val/D_m_ss:.4e},  Re = {Re:,.0f}  → solved iteratively",
        result=f"f = {f_D:.6f}",
        params={"ε (pipe roughness)":    f"{eps_val:.2e} m  [{cfg['pipe_mat']}]",
                "D (pipe diameter)":     f"{D_m_ss:.4f} m",
                "ε/D (relative rough.)": f"{eps_val/D_m_ss:.4e}",
                "Re (Reynolds No.)":     f"{Re:,.0f}"}
    )
    cbox(
        title="Major Head Loss (Pipe Friction)",
        formula="h_f,major = f · (L/D) · v² / (2g)",
        sub=f"= {f_D:.5f} × ({cfg['pipe_L']:.1f} / {D_m_ss:.4f}) × {v:.4f}² / (2 × 9.81)",
        result=f"h_f,major = {hf_maj:.4f} m",
        params={"f (friction factor)":  f"{f_D:.6f}",
                "L (pipe length)":      f"{cfg['pipe_L']:.1f} m",
                "D (pipe diameter)":    f"{D_m_ss:.4f} m",
                "v (flow velocity)":    f"{v:.4f} m/s",
                "g (gravity)":          "9.81 m/s²"}
    )
    cbox(
        title="Minor Head Loss (Fittings & Valves)",
        formula="h_f,minor = Σ K · v² / (2g)",
        sub=f"= {K_fit_live:.4f} × {v:.4f}² / (2 × 9.81)",
        result=f"h_f,minor = {hf_min:.4f} m  |  Total h_f = {hf:.4f} m",
        params={"Σ K (sum of K-values)": f"{K_fit_live:.4f}  (from fittings panel)",
                "v (flow velocity)":     f"{v:.4f} m/s",
                "g (gravity)":           "9.81 m/s²"}
    )

    # Fitting breakdown inside Section 4
    sel = {k: v_ for k, v_ in st.session_state.get("fitting_selections", {}).items() if v_ > 0}
    _, breakdown = calc_K_total(sel)
    if breakdown:
        st.markdown(f"<div style='margin-top:10px;font-size:.80rem;color:{th['accent2']};"
                    "font-weight:700;margin-bottom:6px;'>📋 Fitting Breakdown used above (Crane TP-410)</div>",
                    unsafe_allow_html=True)
        rows_html = "".join(
            f"<tr>"
            f"<td style='padding:5px 10px;color:{th['text']};font-size:.82rem;'>{r['Fitting']}</td>"
            f"<td style='padding:5px 10px;text-align:center;color:{th['accent2']};font-weight:700;'>{r['Qty']}</td>"
            f"<td style='padding:5px 10px;text-align:center;color:#ffd740;'>{r['K each (Crane TP-410)']}</td>"
            f"<td style='padding:5px 10px;text-align:center;color:#50fa7b;font-weight:700;'>{r['K subtotal']}</td>"
            f"<td style='padding:5px 10px;color:{th['metric_lbl']};font-size:.75rem;'>{r['Description']}</td>"
            f"</tr>"
            for r in breakdown
        )
        st.markdown(f"""
<div style='background:{th["card_bg"]};border-radius:10px;overflow:hidden;
            border:1px solid {th["border"]};margin-bottom:8px;'>
  <table style='width:100%;border-collapse:collapse;font-size:.82rem;'>
    <thead>
      <tr style='background:{th["accent"]}22;'>
        <th style='padding:7px 10px;text-align:left;color:{th["accent"]};'>Fitting</th>
        <th style='padding:7px 10px;text-align:center;color:{th["accent"]};'>Qty</th>
        <th style='padding:7px 10px;text-align:center;color:{th["accent"]};'>K each</th>
        <th style='padding:7px 10px;text-align:center;color:{th["accent"]};'>K sub</th>
        <th style='padding:7px 10px;text-align:left;color:{th["accent"]};'>Description</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
    <tfoot>
      <tr style='background:{th["accent"]}25;border-top:2px solid {th["accent"]};'>
        <td colspan='3' style='padding:7px 10px;font-weight:800;color:{th["accent"]};'>
          Σ K TOTAL</td>
        <td style='padding:7px 10px;text-align:center;font-weight:900;
                   font-size:1.05rem;color:#50fa7b;'>{K_fit_live:.4f}</td>
        <td style='padding:7px 10px;color:{th["metric_lbl"]};font-size:.75rem;'>
          Crane TP-410 standard values</td>
      </tr>
    </tfoot>
  </table>
</div>""", unsafe_allow_html=True)

with st.expander("⚡ 4.2  Power Calculations"):
    cbox(
        title="Hydraulic Power",
        formula="P_hyd = ρ · g · Q · H",
        sub=f"= {rho:.2f} × 9.81 × {Q_m3s:.5f} × {H_tot:.2f}",
        result=f"P_hyd = {P_hyd/1000:.4f} kW",
        params={"ρ (fluid density)":   f"{rho:.2f} kg/m³",
                "g (gravity)":         "9.81 m/s²",
                "Q (flow rate)":       f"{Q_m3s:.5f} m³/s",
                "H (total head)":      f"{H_tot:.2f} m"}
    )
    cbox(
        title="Shaft Power",
        formula="P_shaft = P_hyd / η_pump",
        sub=f"= {P_hyd/1000:.4f} kW / {eta_p:.4f}",
        result=f"P_shaft = {P_sh/1000:.4f} kW",
        params={"P_hyd (hydraulic power)": f"{P_hyd/1000:.4f} kW",
                "η_pump (pump efficiency)": f"{eta_p:.4f}  ({eta_p*100:.1f}%)"}
    )
    cbox(
        title="Motor Input Power (with Safety Factor)",
        formula="P_motor = P_shaft × SF / η_motor",
        sub=f"= {P_sh/1000:.4f} × {cfg['SF']} / {cfg['eta_motor']:.4f}",
        result=f"P_motor = {P_mot/1000:.4f} kW  →  Select {mot_kw} kW standard motor",
        params={"P_shaft (shaft power)":     f"{P_sh/1000:.4f} kW",
                "SF (safety factor)":        f"{cfg['SF']}",
                "η_motor (motor effic.)":    f"{cfg['eta_motor']:.4f}  ({cfg['eta_motor']*100:.0f}%)"}
    )
    omega = 2*math.pi*N_rpm/60
    cbox(
        title="Shaft Torque",
        formula="T = P_shaft / ω     [ω = 2π·N/60]",
        sub=f"ω = 2π×{N_rpm}/60 = {omega:.4f} rad/s  |  T = {P_sh:.2f} / {omega:.4f}",
        result=f"T = {torq:.3f} N·m",
        params={"P_shaft (shaft power)": f"{P_sh:.2f} W",
                "N (pump speed)":        f"{N_rpm} RPM",
                "ω (angular velocity)":  f"{omega:.4f} rad/s"}
    )

with st.expander("📊 4.3  Efficiency & Specific Speed"):
    cbox(
        title="Overall System Efficiency",
        formula="η_overall = η_pump × η_motor",
        sub=f"= {eta_p:.4f} × {cfg['eta_motor']:.4f}",
        result=f"η_overall = {eta_ov*100:.2f}%",
        params={"η_pump (pump effic.)":  f"{eta_p:.4f}  ({eta_p*100:.1f}%)",
                "η_motor (motor effic.)": f"{cfg['eta_motor']:.4f}  ({cfg['eta_motor']*100:.0f}%)"}
    )
    if pump_type == "Centrifugal":
        Ns = specific_speed(N_rpm, Q_m3s, H_tot)
        Q_lps = Q_m3s * 1000
        cbox(
            title="Specific Speed (Ns) — Impeller Type Selector",
            formula="Ns = N · √Q_lps / H^(3/4)",
            sub=f"= {N_rpm} × √{Q_lps:.3f} / {H_tot:.2f}^0.75",
            result=f"Ns = {Ns:.2f}",
            params={"N (pump speed)":    f"{N_rpm} RPM",
                    "Q_lps (flow)":      f"{Q_lps:.3f} L/s",
                    "H (total head)":    f"{H_tot:.2f} m"}
        )
        info_box("Ns < 600 → Radial-flow impeller | 600–2500 → Mixed-flow | > 2500 → Axial/propeller  "
                 "(Karassik Pump Handbook, Table 2.1)")

with st.expander(f"🔬 4.4  {pump_type} — Specific Results", expanded=False):
    if not res_s:
        st.info("No specific results. Run a calculation first.")
    else:
        # Render without CSS class dependency — inline styles only
        for k, vv in res_s.items():
            val = f"{vv:.4f}" if isinstance(vv, float) else str(vv)
            st.markdown(
                f"""<div style="background:#0d1117;border-left:4px solid {th['accent']};
                    padding:11px 18px;border-radius:8px;margin:7px 0;
                    display:flex;justify-content:space-between;align-items:center;
                    box-shadow:0 2px 8px rgba(0,0,0,0.25);">
                    <span style="color:#ff79c6;font-family:'Cascadia Code','Courier New',monospace;
                                 font-size:.90rem;font-weight:600;">{k}</span>
                    <span style="color:#50fa7b;font-family:'Cascadia Code','Courier New',monospace;
                                 font-size:.95rem;font-weight:800;">{val}</span>
                </div>""",
                unsafe_allow_html=True
            )
    if pump_type == "Reciprocating":
        if res_s.get("Flow Error vs Target (%)", 0) > 12:
            warn_box(f"Flow deviation {res_s['Flow Error vs Target (%)']:.1f}% — resize piston or adjust RPM.")

if cfg["show_npsh"] and pump_type == "Centrifugal":
    with st.expander("🌊 4.5  NPSH & Cavitation Analysis"):
        hf_suc = hf_maj * 0.20
        NPSHa  = npsh_available(cfg["P_atm"], Pv, rho, cfg["h_suc"], hf_suc)
        NPSHr  = npsh_required(N_rpm, Q_m3s)
        status, margin, risk = cavitation_check(NPSHa, NPSHr)

        # NPSH calculation box — inline styles only
        st.markdown(f"""
<div style="background:#0d1117;border-left:4px solid {th['accent']};
     padding:0;border-radius:10px;margin:10px 0;
     box-shadow:0 2px 12px rgba(0,0,0,0.3);overflow:hidden;">
  <div style="background:linear-gradient(90deg,rgba(255,215,64,0.15),rgba(80,250,123,0.06));
              padding:8px 16px;border-bottom:1px solid rgba(255,215,64,0.18);">
    <span style="color:#ffd740;font-weight:900;font-size:.78rem;
                 text-transform:uppercase;letter-spacing:1px;">🔢 Calculating: NPSHa Available</span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 2fr 1fr;min-height:88px;">
    <div style="padding:12px 14px;border-right:1px solid rgba(255,255,255,0.07);
                background:rgba(255,215,64,0.03);">
      <div style="font-size:.64rem;color:#666;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:8px;font-weight:700;">📌 Parameters</div>
      <div style="margin-bottom:5px;">
        <span style="color:#ffd740;font-weight:900;">P_atm</span>
        <span style="color:#666;font-size:.74rem;font-style:italic;"> (atmospheric)</span><br>
        <span style="color:#8be9fd;font-weight:700;"> = </span>
        <span style="color:#f8f8f2;">{cfg['P_atm']} Pa</span>
      </div>
      <div style="margin-bottom:5px;">
        <span style="color:#ffd740;font-weight:900;">Pv</span>
        <span style="color:#666;font-size:.74rem;font-style:italic;"> (vapor pressure)</span><br>
        <span style="color:#8be9fd;font-weight:700;"> = </span>
        <span style="color:#f8f8f2;">{Pv} Pa</span>
      </div>
      <div style="margin-bottom:5px;">
        <span style="color:#ffd740;font-weight:900;">h_s</span>
        <span style="color:#666;font-size:.74rem;font-style:italic;"> (suction head)</span><br>
        <span style="color:#8be9fd;font-weight:700;"> = </span>
        <span style="color:#f8f8f2;">{cfg['h_suc']} m</span>
      </div>
      <div>
        <span style="color:#ffd740;font-weight:900;">h_f,suc</span>
        <span style="color:#666;font-size:.74rem;font-style:italic;"> (suction friction)</span><br>
        <span style="color:#8be9fd;font-weight:700;"> = </span>
        <span style="color:#f8f8f2;">{hf_suc:.4f} m</span>
      </div>
    </div>
    <div style="padding:12px 15px;border-right:1px solid rgba(255,255,255,0.07);">
      <div style="font-size:.64rem;color:#666;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:8px;font-weight:700;">📐 Formula → Substitution</div>
      <div style="color:#ff79c6;font-family:'Cascadia Code','Courier New',monospace;
                  font-size:.90rem;margin-bottom:6px;font-weight:600;">
          NPSHa = (P_atm − Pv) / (ρ·g) + h_s − h_f,suc</div>
      <div style="color:#8be9fd;font-family:'Cascadia Code','Courier New',monospace;font-size:.86rem;">
          = ({cfg['P_atm']} − {Pv}) / ({rho:.1f} × 9.81) + {cfg['h_suc']} − {hf_suc:.3f}</div>
    </div>
    <div style="padding:12px 13px;display:flex;flex-direction:column;
                justify-content:center;background:rgba(80,250,123,0.04);">
      <div style="font-size:.64rem;color:#666;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:8px;font-weight:700;">✅ Result</div>
      <div style="color:#50fa7b;font-family:'Cascadia Code','Courier New',monospace;
                  font-size:.95rem;font-weight:800;line-height:1.6;">
          NPSHa = {NPSHa:.3f} m<br>
          NPSHr = {NPSHr:.3f} m<br>
          Margin = {margin:.3f} m
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        if risk == "low":    success_box(f"{status} — Margin {margin:.2f} m ≥ 0.5 m (HI min.)")
        elif risk == "medium": warn_box(f"{status} — Margin {margin:.2f} m marginal.")
        else:               danger_box(f"{status} — Redesign required!")

        if ai_client and st.button("🤖 AI NPSH Analysis", key="btn_npsh"):
            with st.spinner("AI analysing NPSH…"):
                npsh_ai = get_cavitation_advice(ai_client, NPSHa, NPSHr, margin, pump_type)
            st.session_state["ai_selection_text"] = npsh_ai
        if st.session_state["ai_selection_text"] and pump_type == "Centrifugal":
            st.markdown(f'<div class="ai-response">🤖 {st.session_state["ai_selection_text"]}</div>',
                        unsafe_allow_html=True)

# =============================================================================
# SECTION 4.6 — IMPELLER DESIGN  (Centrifugal only)
# =============================================================================
if pump_type == "Centrifugal":
    divider()
    sec("🌀  SECTION 4.6 — IMPELLER DESIGN CALCULATIONS", th["accent2"])

    from modules.impeller import calc_impeller, impeller_style, pump_datasheet
    imp = calc_impeller(Q_m3s, H_tot, N_rpm, rho, eta_hyd=0.88,
                        phi=sp.get("phi", 0.85))
    st.session_state["imp"] = imp

    i_style, i_style_reason = impeller_style(fluid, rho*9.81*H_tot/1e5)

    # Impeller type banner
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{rgba(th['accent'],0.15)},{rgba(th['accent2'],0.1)});
     border-radius:12px;padding:16px 22px;margin:10px 0;
     border-left:5px solid {th['accent']};">
  <div style="font-size:.80rem;color:{th['metric_lbl']};text-transform:uppercase;
              letter-spacing:1px;margin-bottom:5px;">Impeller Classification</div>
  <div style="font-size:1.3rem;font-weight:800;color:{th['accent']};">
      {imp['Impeller Type']}</div>
  <div style="font-size:.88rem;color:{th['text']};margin-top:4px;">
      {imp['Impeller Description']}</div>
  <div style="font-size:.82rem;color:{th['accent3']};margin-top:6px;font-weight:600;">
      Style: {i_style} Impeller  —  {i_style_reason}</div>
</div>""", unsafe_allow_html=True)

    # Impeller calculations with cbox
    with st.expander("🔢 Impeller Geometry Calculations (Stepanoff / API 610)", expanded=False):
        Q_lps = Q_m3s * 1000
        Ns    = imp["Specific Speed Ns"]
        cbox(
            title="Specific Speed — Impeller Type Selection",
            formula="Ns = N · √Q_lps / H^(3/4)  [Karassik / HI]",
            sub=f"= {N_rpm} × √{Q_lps:.3f} / {H_tot:.2f}^0.75",
            result=f"Ns = {Ns}  →  {imp['Impeller Type']}",
            params={"N (pump speed)":    f"{N_rpm} RPM",
                    "Q_lps (flow)":      f"{Q_lps:.3f} L/s",
                    "H (total head)":    f"{H_tot:.2f} m"}
        )

        H_eu = imp["Euler Head H_eu (m)"]
        u2   = imp["Tip Speed u₂ (m/s)"]
        D2   = imp["Outlet Diameter D₂ (mm)"]
        cbox(
            title="Euler Head (Theoretical)",
            formula="H_eu = H / η_hydraulic",
            sub=f"= {H_tot:.2f} / 0.88",
            result=f"H_eu = {H_eu:.3f} m",
            params={"H (design head)":      f"{H_tot:.2f} m",
                    "η_hyd (hyd. effic.)":  "0.88 (typical API 610 §6.1)"}
        )
        cbox(
            title="Impeller Tip Speed (u₂)",
            formula="u₂ = φ · √(2·g·H_eu)",
            sub=f"= {sp.get('phi',0.85):.2f} × √(2 × 9.81 × {H_eu:.3f})",
            result=f"u₂ = {u2:.3f} m/s",
            params={"φ (head coefficient)":  f"{sp.get('phi',0.85):.2f}",
                    "g (gravity)":            "9.81 m/s²",
                    "H_eu (Euler head)":      f"{H_eu:.3f} m"}
        )
        cbox(
            title="Outlet Diameter D₂",
            formula="D₂ = 60 · u₂ / (π · N)",
            sub=f"= 60 × {u2:.3f} / (π × {N_rpm})",
            result=f"D₂ = {D2:.1f} mm",
            params={"u₂ (tip speed)":   f"{u2:.3f} m/s",
                    "N (speed)":         f"{N_rpm} RPM",
                    "π":                 "3.14159"}
        )

        D1  = imp["Inlet / Eye Diameter D₁ (mm)"]
        Dh  = imp["Hub Diameter Dₕ (mm)"]
        b2  = imp["Outlet Blade Width b₂ (mm)"]
        ds  = imp["Shaft Diameter (mm)"]
        cbox(
            title="Inlet / Eye Diameter D₁",
            formula="D₁ ≈ 0.45 · D₂  [Karassik empirical]",
            sub=f"= 0.45 × {D2:.1f}",
            result=f"D₁ = {D1:.1f} mm",
            params={"D₂ (outlet dia.)": f"{D2:.1f} mm",
                    "0.45 (ratio)":      "Karassik Table 2.3 — typical radial"}
        )
        cbox(
            title="Outlet Blade Width b₂",
            formula="b₂ = Q / (π · D₂ · Cm₂)  [continuity]",
            sub=f"Cm₂ = ψ·u₂ = 0.5×{u2:.3f} = {imp['Meridional Velocity Cm₂ (m/s)']:.3f} m/s",
            result=f"b₂ = {b2:.2f} mm",
            params={"Q (flow rate)":    f"{Q_m3s:.5f} m³/s",
                    "D₂ (outlet dia.)": f"{D2/1000:.4f} m",
                    "Cm₂ (merid. vel.)":f"{imp['Meridional Velocity Cm₂ (m/s)']:.3f} m/s"}
        )
        cbox(
            title="Blade Angles (Velocity Triangle — Stepanoff)",
            formula="β₁ = atan(Cm₁/u₁)   β₂ = atan(Wm₂/(u₂−Cu₂))",
            sub=f"β₁={imp['Blade Inlet Angle β₁ (°)']:.1f}°  →  β₂={imp['Blade Outlet Angle β₂ (°)']:.1f}°",
            result=f"β₁ = {imp['Blade Inlet Angle β₁ (°)']:.1f}°  |  β₂ = {imp['Blade Outlet Angle β₂ (°)']:.1f}°",
            params={"u₁ (inlet periph.)":   f"{imp['Inlet Peripheral Speed u₁ (m/s)']:.3f} m/s",
                    "u₂ (outlet periph.)":  f"{u2:.3f} m/s",
                    "Cu₂ (whirl comp.)":    f"{imp['Whirl Component Cu₂ (m/s)']:.3f} m/s",
                    "Cm₂ (merid. vel.)":    f"{imp['Meridional Velocity Cm₂ (m/s)']:.3f} m/s"}
        )
        cbox(
            title="Shaft Diameter (Torsional Stress)",
            formula="d_shaft = (16T / π·τ_allow)^(1/3)  [API 610 §6.3.1]",
            sub=f"τ_allow = 55 MPa (SS316),  T = {rho*9.81*Q_m3s*H_tot/(2*math.pi*N_rpm/60):.2f} N·m",
            result=f"d_shaft = {ds:.1f} mm",
            params={"τ_allow (shear)":  "55 MPa (SS316 / API 610)",
                    "N (speed)":         f"{N_rpm} RPM"}
        )

    # Advanced Impeller Dashboard Summary
    with st.expander("📋 Full Impeller Design Summary", expanded=False):
        # Group parameters into themed sections
        geo_keys   = ["Outlet Diameter D₂ (mm)", "Inlet / Eye Diameter D₁ (mm)",
                      "Hub Diameter Dₕ (mm)", "Shaft Diameter (mm)",
                      "Outlet Blade Width b₂ (mm)", "Inlet Blade Width b₁ (mm)"]
        blade_keys = ["Blade Inlet Angle β₁ (°)", "Blade Outlet Angle β₂ (°)",
                      "Number of Blades z", "Blade Type"]
        vel_keys   = ["Tip Speed u₂ (m/s)", "Inlet Peripheral Speed u₁ (m/s)",
                      "Meridional Velocity Cm₂ (m/s)", "Whirl Component Cu₂ (m/s)",
                      "Absolute Velocity C₂ (m/s)"]
        perf_keys  = ["Specific Speed Ns", "Euler Head H_eu (m)",
                      "Head Coefficient ψ", "Flow Coefficient φ",
                      "Slip Factor σ", "Material"]

        def _imp_card(keys, label, icon, acc_col):
            rows = ""
            for k in keys:
                v = imp.get(k)
                if v is None:
                    continue
                val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
                rows += (
                    f"<tr>"
                    f"<td style='padding:7px 14px;color:rgba(255,255,255,0.55);"
                    f"font-size:.80rem;border-bottom:1px solid rgba(255,255,255,0.04);"
                    f"width:58%;'>{k}</td>"
                    f"<td style='padding:7px 14px;color:#e6edf3;font-weight:700;"
                    f"font-family:JetBrains Mono,Cascadia Code,monospace;"
                    f"font-size:.88rem;border-bottom:1px solid rgba(255,255,255,0.04);'>"
                    f"<span style='color:{acc_col};'>{val_str}</span></td>"
                    f"</tr>"
                )
            if not rows:
                return ""
            return f"""
<div style="background:#0d1117;border-radius:10px;overflow:hidden;
            border:1px solid rgba(255,255,255,0.08);margin-bottom:14px;">
  <div style="background:linear-gradient(90deg,{acc_col}22,transparent);
              padding:9px 16px;border-bottom:1px solid {acc_col}33;">
    <span style="font-size:.80rem;font-weight:800;color:{acc_col};
                 text-transform:uppercase;letter-spacing:1px;">{icon} {label}</span>
  </div>
  <table style="width:100%;border-collapse:collapse;">
    <tbody>{rows}</tbody>
  </table>
</div>"""

        # Render in 2 columns
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(_imp_card(geo_keys,   "Geometry & Dimensions", "📐", "#ffd740"),
                        unsafe_allow_html=True)
            st.markdown(_imp_card(vel_keys,   "Velocity Components",   "⚡", "#8be9fd"),
                        unsafe_allow_html=True)
        with col_r:
            st.markdown(_imp_card(blade_keys, "Blade Design",          "🌀", "#ff79c6"),
                        unsafe_allow_html=True)
            st.markdown(_imp_card(perf_keys,  "Performance Numbers",   "📊", "#50fa7b"),
                        unsafe_allow_html=True)

        # API 610 compliance strip
        u2_v   = imp.get("Tip Speed u₂ (m/s)", 0)
        Ns_v   = imp.get("Specific Speed Ns", 0)
        D2_v   = imp.get("Outlet Diameter D₂ (mm)", 0)
        D1_v   = imp.get("Inlet / Eye Diameter D₁ (mm)", 1)
        ratio  = D2_v / max(D1_v, 1)

        checks = [
            ("u₂ ≤ 50 m/s", u2_v <= 50,
             f"{u2_v:.2f} m/s", "API 610 §6.3.1 tip speed limit"),
            ("D₂/D₁ 1.5–5.0", 1.5 <= ratio <= 5.0,
             f"{ratio:.2f}", "Karassik design ratio"),
            ("β₂ 15°–35°", 15 <= imp.get("Blade Outlet Angle β₂ (°)",22) <= 35,
             f"{imp.get('Blade Outlet Angle β₂ (°)',22):.1f}°", "Backward-curved blade range"),
            ("Ns range", 200 <= Ns_v <= 3000,
             f"{Ns_v:.0f}", "HI radial/mixed flow range"),
        ]

        checks_html = "".join([
            f"<div style='text-align:center;padding:10px 6px;'>"
            f"<div style='font-size:1.3rem;'>{'✅' if ok else '⚠️'}</div>"
            f"<div style='font-size:.70rem;color:{'#50fa7b' if ok else '#ffa726'};"
            f"font-weight:800;margin:3px 0;'>{name}</div>"
            f"<div style='font-size:.80rem;color:#e6edf3;font-weight:700;"
            f"font-family:JetBrains Mono,monospace;'>{val}</div>"
            f"<div style='font-size:.65rem;color:rgba(255,255,255,0.35);margin-top:2px;'>{note}</div>"
            f"</div>"
            for name, ok, val, note in checks
        ])

        st.markdown(f"""
<div style="background:linear-gradient(90deg,rgba(80,250,123,0.08),rgba(139,233,253,0.06));
     border:1px solid rgba(80,250,123,0.25);border-radius:10px;padding:10px 16px;
     margin-top:4px;">
  <div style="font-size:.74rem;color:#50fa7b;font-weight:800;text-transform:uppercase;
              letter-spacing:1px;margin-bottom:10px;">⚙️ API 610 Design Compliance Checks</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;">
    {checks_html}
  </div>
</div>""", unsafe_allow_html=True)

    # ── API 610 Advanced Pump Data Sheet ──────────────────────────────────────
    with st.expander("📄 API 610 Pump Data Sheet  —  Full Engineering Document", expanded=False):
        hf_suc_ds  = hf_maj * 0.20
        NPSHa_ds   = npsh_available(cfg["P_atm"], Pv, rho, cfg["h_suc"], hf_suc_ds)
        NPSHr_ds   = npsh_required(N_rpm, Q_m3s)
        ds_sections = pump_datasheet(
            pump_type, Q_m3h, H_tot, N_rpm, rho,
            P_sh/1000, P_mot/1000, mot_kw,
            eta_p, NPSHa_ds, NPSHr_ds, imp, fluid,
            # Pass all extended parameters
            mu_cP       = mu_cP,
            Pv_pa       = Pv,
            P_atm_pa    = cfg["P_atm"],
            pipe_L      = cfg["pipe_L"],
            pipe_D_mm   = D_mm_input,
            pipe_mat    = cfg["pipe_mat"],
            eps_m       = eps,
            K_fit       = K_fit_live,
            h_suc       = cfg["h_suc"],
            z_static    = z_static,
            hf_maj      = hf_maj,
            hf_min      = hf_min,
            Re          = Re,
            f_D         = f_D,
            v           = v,
            eta_motor   = cfg["eta_motor"],
            SF          = cfg["SF"],
            P_hyd_kw    = P_hyd/1000,
            eta_overall = eta_ov,
            torque_Nm   = torq,
            op_hours    = cfg.get("op_hours", 8000),
            tariff      = cfg.get("tariff", 0.10),
            project_name= "SmartPump Designer",
            service_desc= cfg.get("service_desc", "General Pumping Service"),
        )

        # ── Document Header ────────────────────────────────────────────────
        doc_date = _dt_module.date.today().strftime("%d %B %Y")
        st.markdown(f"""
<div style="background:linear-gradient(135deg,{th['accent']}18,{th['accent2']}10);
     border:2px solid {th['accent']}55;border-radius:14px;padding:20px 28px;margin-bottom:18px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
    <div>
      <div style="font-size:1.35rem;font-weight:900;color:{th['accent']};
                  letter-spacing:1.5px;font-family:'JetBrains Mono',monospace;">
        API 610 — CENTRIFUGAL PUMP DATA SHEET
      </div>
      <div style="font-size:.78rem;color:{th['metric_lbl']};margin-top:4px;letter-spacing:.5px;">
        INTERNATIONAL STANDARD  ·  12th EDITION  ·  ANNEX A FORMAT
      </div>
    </div>
    <div style="text-align:right;font-size:.75rem;color:{th['metric_lbl']};
                font-family:'JetBrains Mono',monospace;line-height:1.8;">
      <div><b style="color:{th['text']};">Document Date:</b>  {doc_date}</div>
      <div><b style="color:{th['text']};">Revision:</b>  R0 — Issued for Design</div>
      <div><b style="color:{th['text']};">Prepared by:</b>  Pump AI System</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Render each section ────────────────────────────────────────────
        # Save ds_sections for export use
        st.session_state["ds_sections"] = ds_sections

        # Section color map — each section gets distinct vivid color
        SEC_COLORS = {
            0: {"hdr":"#00b0ff", "param":"#90caf9", "val":"#e3f2fd", "note":"#64b5f6"},  # Blue
            1: {"hdr":"#00e676", "param":"#a5d6a7", "val":"#e8f5e9", "note":"#69f0ae"},  # Green
            2: {"hdr":"#ffd740", "param":"#ffe082", "val":"#fff8e1", "note":"#ffca28"},  # Yellow
            3: {"hdr":"#ff6e40", "param":"#ffab91", "val":"#fbe9e7", "note":"#ff7043"},  # Orange
            4: {"hdr":"#e040fb", "param":"#ce93d8", "val":"#f3e5f5", "note":"#ba68c8"},  # Purple
            5: {"hdr":"#00e5ff", "param":"#80deea", "val":"#e0f7fa", "note":"#4dd0e1"},  # Cyan
            6: {"hdr":"#ffa726", "param":"#ffcc80", "val":"#fff3e0", "note":"#fb8c00"},  # Amber
            7: {"hdr":"#76ff03", "param":"#ccff90", "val":"#f1f8e9", "note":"#64dd17"},  # Light Green
            8: {"hdr":"#ff4081", "param":"#f48fb1", "val":"#fce4ec", "note":"#f06292"},  # Pink
            9: {"hdr":"#40c4ff", "param":"#81d4fa", "val":"#e1f5fe", "note":"#29b6f6"},  # Light Blue
            10:{"hdr":"#b2ff59", "param":"#dce775", "val":"#f9fbe7", "note":"#c6ff00"},  # Lime
            11:{"hdr":"#ff6d00", "param":"#ffab40", "val":"#fff3e0", "note":"#ff9100"},  # Deep Orange
            12:{"hdr":"#ea80fc", "param":"#ce93d8", "val":"#f3e5f5", "note":"#ab47bc"},  # Purple2
            13:{"hdr":"#a7ffeb", "param":"#80cbc4", "val":"#e0f2f1", "note":"#26a69a"},  # Teal
        }

        for sec_idx, sec_data in enumerate(ds_sections):
            sec_title = sec_data["title"]
            sec_color = sec_data["color"]          # keep original for border
            sec_rows  = sec_data["rows"]
            sc = SEC_COLORS.get(sec_idx % len(SEC_COLORS), SEC_COLORS[0])

            rows_html = ""
            for i, row in enumerate(sec_rows):
                param = row[0]; val = str(row[1])
                note  = row[2] if len(row) > 2 else ""

                # Alternate row background
                row_bg = "rgba(255,255,255,0.04)" if i % 2 == 0 else "rgba(255,255,255,0.01)"

                # Smart value coloring
                if "✅" in val or "SAFE" in val.upper() or "PASS" in val.upper():
                    val_col = "#50fa7b"
                    val_weight = "800"
                elif "🚨" in val or "RISK" in val.upper() or "FAIL" in val.upper():
                    val_col = "#ff5555"
                    val_weight = "900"
                elif "⚠️" in val or "CHECK" in val.upper() or "MARGINAL" in val.upper():
                    val_col = "#ffa726"
                    val_weight = "800"
                elif any(kw in param.upper() for kw in
                         ["STATUS","CONCLUSION","SELECTED","CAVITATION","RECOMMENDATION",
                          "ENGINEERING CONCLUSION","COMPLIANCE"]):
                    val_col = "#ffd740"
                    val_weight = "800"
                else:
                    val_col = "#e6edf3"   # bright white — always visible
                    val_weight = "600"

                # Note html
                note_html = (
                    f"<div style='font-size:.70rem;color:{sc['note']};margin-top:4px;"
                    f"font-style:italic;font-weight:400;'>{note}</div>"
                ) if note else ""

                rows_html += (
                    f"<tr style='background:{row_bg};"
                    f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                    f"<td style='padding:9px 16px;"
                    f"color:{sc['param']};font-weight:700;"       # PARAM — colored, vivid
                    f"font-size:.84rem;width:36%;"
                    f"border-right:2px solid {sc['hdr']}44;'>{param}</td>"
                    f"<td style='padding:9px 16px;"
                    f"color:{val_col};"                            # VALUE — bright & readable
                    f"font-weight:{val_weight};"
                    f"font-size:.88rem;"
                    f"font-family:JetBrains Mono,Cascadia Code,monospace;'>"
                    f"{val}{note_html}</td>"
                    f"</tr>"
                )

            st.markdown(f"""
<div style="margin-bottom:22px;">
  <!-- Section heading bar -->
  <div style="background:linear-gradient(90deg,{sc['hdr']}40,{sc['hdr']}10);
       border-left:6px solid {sc['hdr']};border-radius:8px 8px 0 0;
       padding:11px 20px;display:flex;align-items:center;gap:12px;">
    <span style="font-size:1.05rem;font-weight:900;color:{sc['hdr']};
                 letter-spacing:2px;text-transform:uppercase;
                 font-family:'JetBrains Mono',monospace;">{sec_title}</span>
  </div>
  <!-- Table -->
  <div style="background:#0d1117;border-radius:0 0 10px 10px;overflow:hidden;
              border:1px solid {sc['hdr']}40;border-top:none;">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:{sc['hdr']}22;border-bottom:2px solid {sc['hdr']}60;">
          <th style="padding:8px 16px;text-align:left;color:{sc['hdr']};
                     font-size:.77rem;letter-spacing:1.2px;text-transform:uppercase;
                     font-weight:900;width:36%;">Parameter</th>
          <th style="padding:8px 16px;text-align:left;color:{sc['hdr']};
                     font-size:.77rem;letter-spacing:1.2px;text-transform:uppercase;
                     font-weight:900;">Specified Value</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Footer reference bar ────────────────────────────────────────────
        st.markdown(f"""
<div style="background:{th['card_bg']};border:1px solid {th['border']};border-radius:8px;
     padding:10px 18px;margin-top:6px;display:flex;justify-content:space-between;
     flex-wrap:wrap;gap:8px;">
  <span style="font-size:.70rem;color:{th['metric_lbl']};">
    📐 Ref: API 610 12th Ed. · API 682 4th Ed. · API 671 · HI 1.1-1.6 · HI 9.6.1 · ASME B16.20
  </span>
  <span style="font-size:.70rem;color:{th['metric_lbl']};">
    ⚠️ All values are design calculations — verify with vendor certified test curves before procurement.
  </span>
</div>""", unsafe_allow_html=True)

        # ── Quick Download Buttons inside Data Sheet ────────────────────────
        st.markdown(f"""
<div style="margin-top:20px;padding:14px 20px;
     background:linear-gradient(135deg,#00c85314,#00c85308);
     border:1px solid #00c85340;border-radius:10px;">
  <div style="font-size:.80rem;font-weight:900;color:#00c853;letter-spacing:1.5px;
              margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
    ⬇️  QUICK DOWNLOAD — DATA SHEET ONLY
  </div>
</div>""", unsafe_allow_html=True)

        _qdl1, _qdl2, _qdl3 = st.columns([1, 1, 2])
        _ds_now = datetime.now().strftime("%Y%m%d_%H%M")
        _ds_fname = f"API610_DataSheet_{pump_type}_{_ds_now}"

        with _qdl1:
            try:
                _ds_pdf = build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
                st.download_button(
                    "📄 Download Data Sheet (PDF)",
                    data=_ds_pdf,
                    file_name=f"{_ds_fname}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="ds_pdf_quick"
                )
            except Exception as _e:
                st.error(f"PDF: {_e}")

        with _qdl2:
            try:
                _ds_docx = build_docx(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
                st.download_button(
                    "📝 Download Data Sheet (Word)",
                    data=_ds_docx,
                    file_name=f"{_ds_fname}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="ds_docx_quick"
                )
            except Exception as _e:
                st.error(f"Word: {_e}")

        with _qdl3:
            st.info("💡 For full report with graphs & 3D model → use **Section 8 — Advanced Export Builder** below.")

# =============================================================================
# SECTION 4.7 — 3D PUMP VISUALIZATION + ANIMATED FLOW
# =============================================================================
divider()
sec("🔵  SECTION 4.7 — 3D PUMP VISUALIZATION & ANIMATED FLOW DIAGRAM", th["accent3"])

from graphs.pump_3d import pump_3d_view, animated_flow_diagram, velocity_triangle_plot

imp_data = st.session_state.get("imp", {})
D2_vis   = imp_data.get("Outlet Diameter D₂ (mm)", D_mm_input * 4) if pump_type=="Centrifugal" else D_mm_input*3
D1_vis   = imp_data.get("Inlet / Eye Diameter D₁ (mm)", D_mm_input*2)
b2_vis   = imp_data.get("Outlet Blade Width b₂ (mm)", D_mm_input*0.2)
ds_vis   = imp_data.get("Shaft Diameter (mm)", D_mm_input*0.3)

viz_tab1, viz_tab2, viz_tab3 = st.tabs(
    ["🔵 3D Pump Cross-Section", "🌊 Animated Flow Diagram", "📐 Velocity Triangles"])

with viz_tab1:
    st.markdown(f"""
<div style="font-size:.82rem;color:{th['metric_lbl']};margin-bottom:8px;">
    Interactive 3D view of pump internals scaled to your design parameters.
    <b>Drag to rotate</b> | <b>Scroll to zoom</b> | <b>Click legend</b> to show/hide parts.
</div>""", unsafe_allow_html=True)
    fig_3d = pump_3d_view(
        D2_mm=D2_vis, D1_mm=D1_vis, b2_mm=b2_vis,
        shaft_dia_mm=ds_vis, D_pipe_mm=D_mm_input,
        H_m=H_tot, Q_m3h=Q_m3h, N_rpm=N_rpm, th=th_plot,
        pump_type=pump_type
    )
    st.plotly_chart(fig_3d, use_container_width=True)
    info_box(
        f"All dimensions from your design: D₂={D2_vis:.0f}mm | D₁={D1_vis:.0f}mm | "
        f"b₂={b2_vis:.1f}mm | Shaft={ds_vis:.0f}mm | Pipe DN{D_mm_input:.0f}"
    )

with viz_tab2:
    st.markdown(f"""
<div style="font-size:.82rem;color:{th['metric_lbl']};margin-bottom:8px;">
    Press <b>▶ Play</b> to animate fluid particles flowing from reservoir → pump → discharge tank.
    All pipe dimensions match your actual design inputs.
</div>""", unsafe_allow_html=True)
    fig_anim = animated_flow_diagram(
        Q_m3h=Q_m3h, H_m=H_tot, D_pipe_mm=D_mm_input,
        L_suction_m=min(cfg["pipe_L"]*0.15, 20),
        L_discharge_m=cfg["pipe_L"]*0.85,
        z_suction_m=max(cfg["h_suc"], 0.5),
        z_discharge_m=H_tot * 0.6,
        th=th_plot,
        NPSHa=NPSHa, NPSHr=NPSHr,
        eta_p=eta_p, P_sh_kw=P_sh/1000,
        hf_maj=hf_maj, hf_min=hf_min,
    )
    st.plotly_chart(fig_anim, use_container_width=True)

with viz_tab3:
    if pump_type == "Centrifugal" and imp_data:
        st.markdown(f"<div style='font-size:.82rem;color:{th['metric_lbl']};margin-bottom:8px;'>"
                    "Velocity triangles at impeller inlet and outlet "
                    "(Euler / Stepanoff method — Karassik Ch.2)</div>", unsafe_allow_html=True)
        fig_vt = velocity_triangle_plot(
            u1=imp_data.get("Inlet Peripheral Speed u₁ (m/s)", 5),
            u2=imp_data.get("Tip Speed u₂ (m/s)", 15),
            Cm1=imp_data.get("Meridional Velocity Cm₂ (m/s)", 3)*1.2,
            Cm2=imp_data.get("Meridional Velocity Cm₂ (m/s)", 3),
            Cu2=imp_data.get("Whirl Component Cu₂ (m/s)", 10),
            beta1=imp_data.get("Blade Inlet Angle β₁ (°)", 25),
            beta2=imp_data.get("Blade Outlet Angle β₂ (°)", 25),
            th=th_plot
        )
        st.plotly_chart(fig_vt, use_container_width=True)
    else:
        info_box("Velocity triangles are specific to centrifugal pumps with rotating impeller.")

# =============================================================================
# SECTION 5 — RESULTS SUMMARY
# =============================================================================
divider()
sec("📊  SECTION 5 — DESIGN RESULTS SUMMARY", th["accent2"])
r1, r2, r3, r4 = st.columns(4)
with r1:
    mcard("Selected Pump",    pump_type)
    mcard("Flow Rate",        f"{Q_val:.2f}", Q_unit)
    mcard("Total Head",       f"{H_tot:.1f}", "m")
with r2:
    mcard("Hydraulic Power",  f"{P_hyd/1000:.3f}", "kW")
    mcard("Shaft Power",      f"{P_sh/1000:.3f}",  "kW")
    mcard("Motor Sized",      f"{mot_kw}",           "kW")
with r3:
    mcard("Pump Efficiency",  f"{eta_p*100:.1f}",    "%")
    mcard("Motor Efficiency", f"{cfg['eta_motor']*100:.1f}", "%")
    mcard("Overall η",        f"{eta_ov*100:.2f}",   "%")
with r4:
    mcard("Pipe Velocity",    f"{v:.3f}", "m/s")
    mcard("Reynolds No.",     f"{Re:,.0f}")
    mcard("Shaft Torque",     f"{torq:.2f}", "N·m")

if cfg["show_cost"]:
    divider()
    sec("💰  SECTION 5b — LIFE CYCLE COST ANALYSIS (API 686 / HI 9.6.4 Method)", th["accent3"])

    # ── Cost Calculation Engine ───────────────────────────────────────────────
    # Capital Cost — Lang Factor method (Peters & Timmerhaus)
    P_sh_kw    = P_sh / 1000
    P_mot_kw   = P_mot / 1000
    op_h       = cfg["op_hours"]
    tariff_kwh = cfg["tariff"]
    life_yr    = cfg.get("life_years", 20)

    # Equipment cost bases (Chemical Engineering Plant Cost Index, 2024 basis)
    # Centrifugal: $300–$1200/kW^0.65, Recip: $800+, Plunger: $1000+, Gear: $650+
    _equip_base = {"Centrifugal": 420, "Reciprocating": 950,
                   "Plunger": 1100, "Gear": 700}.get(pump_type, 500)
    c_pump_bare  = _equip_base * max(P_sh_kw, 0.5) ** 0.65   # Bare pump
    c_motor_bare = 280 * max(P_mot_kw, 0.5) ** 0.72           # Motor (IEC IE3)
    c_seal       = c_pump_bare * 0.12                          # Mechanical seal (API 682)
    c_coupling   = c_pump_bare * 0.04                          # Coupling (API 671)
    c_baseplate  = c_pump_bare * 0.06                          # Epoxy baseplate

    # Installed cost = bare cost × Lang factors
    # Lang factor for pumps: 4.74 (fluid processing) — Peters & Timmerhaus Table 6-3
    # Broken down:
    f_piping     = 0.45   # Piping & instrumentation
    f_civil      = 0.15   # Civil & structural
    f_electrical = 0.12   # Electrical installation
    f_insulation = 0.03   # Insulation
    f_painting   = 0.02   # Painting & coating
    f_indirect   = 0.25   # Engineering, procurement, construction management
    f_contingency= 0.10   # Contingency (10%)

    c_equip_total = c_pump_bare + c_motor_bare + c_seal + c_coupling + c_baseplate
    c_piping      = c_equip_total * f_piping
    c_civil       = c_equip_total * f_civil
    c_electrical  = c_equip_total * f_electrical
    c_insulation  = c_equip_total * f_insulation
    c_painting    = c_equip_total * f_painting
    c_direct      = c_equip_total + c_piping + c_civil + c_electrical + c_insulation + c_painting
    c_indirect    = c_direct * f_indirect
    c_subtotal    = c_direct + c_indirect
    c_contingency = c_subtotal * f_contingency
    c_tdc         = c_subtotal + c_contingency   # Total Direct + Indirect
    c_commission  = c_tdc * 0.03                 # Commissioning & startup
    c_capex       = c_tdc + c_commission         # Total CAPEX

    # Operating Cost (Annual) — HI 9.6.4 Lifecycle Cost
    c_energy_yr   = annual_energy_cost(P_mot, op_h, tariff_kwh)   # Energy
    c_maint_yr    = c_pump_bare * 0.03            # Maintenance (3% of pump cost/yr)
    c_seal_yr     = c_seal * 0.20                 # Seal replacement (20%/yr amortized)
    c_lube_yr     = max(200, c_pump_bare * 0.005) # Lubrication
    c_inspect_yr  = c_pump_bare * 0.015           # Inspection & monitoring
    c_overhead_yr = (c_maint_yr + c_seal_yr) * 0.10  # Overhead/admin
    c_opex_yr     = (c_energy_yr + c_maint_yr + c_seal_yr +
                     c_lube_yr + c_inspect_yr + c_overhead_yr)

    # Lifecycle totals
    c_energy_life = c_energy_yr  * life_yr
    c_opex_life   = c_opex_yr    * life_yr
    c_lcca        = c_capex + c_opex_life          # Total Life Cycle Cost
    c_payback_yr  = c_capex / max(c_opex_yr, 1)   # Simple payback (informational)

    # NPV of operating costs (discount rate 8%)
    r_disc = 0.08
    npv_factor = (1 - (1 + r_disc) ** (-life_yr)) / r_disc
    c_npv_opex = c_opex_yr * npv_factor

    # Efficiency impact: cost premium if η < 75%
    eta_penalty = max(0, (0.75 - eta_p) / 0.75) * c_energy_yr * life_yr

    # CO₂ emission estimate (0.233 kg CO₂/kWh — IEA world average grid)
    co2_per_kwh = 0.233
    co2_yr_kg   = P_mot_kw * op_h * co2_per_kwh
    co2_life_t  = co2_yr_kg * life_yr / 1000

    # Store for export
    _cost_data = {
        "pump_type": pump_type, "P_sh_kw": P_sh_kw, "P_mot_kw": P_mot_kw,
        "op_hours": op_h, "tariff": tariff_kwh, "life_years": life_yr,
        "c_pump_bare": c_pump_bare, "c_motor_bare": c_motor_bare,
        "c_seal": c_seal, "c_coupling": c_coupling, "c_baseplate": c_baseplate,
        "c_equip_total": c_equip_total, "c_piping": c_piping,
        "c_civil": c_civil, "c_electrical": c_electrical,
        "c_direct": c_direct, "c_indirect": c_indirect,
        "c_contingency": c_contingency, "c_capex": c_capex,
        "c_energy_yr": c_energy_yr, "c_maint_yr": c_maint_yr,
        "c_seal_yr": c_seal_yr, "c_lube_yr": c_lube_yr,
        "c_opex_yr": c_opex_yr, "c_lcca": c_lcca,
        "c_npv_opex": c_npv_opex, "c_energy_life": c_energy_life,
        "eta_penalty": eta_penalty, "co2_yr_kg": co2_yr_kg,
        "co2_life_t": co2_life_t, "Q_m3h": Q_m3h, "H_tot": H_tot,
        "eta_p": eta_p, "mot_kw": mot_kw, "fluid": fluid,
        "r_disc": r_disc, "npv_factor": npv_factor,
    }
    st.session_state["cost_data"] = _cost_data


    # ══════════════════════════════════════════════════════════════════════════
    # COST ANALYSIS — ADVANCED UI
    # ══════════════════════════════════════════════════════════════════════════

    # ── 6 KPI Cards ───────────────────────────────────────────────────────────
    energy_pct  = c_energy_life / c_lcca * 100
    capex_pct   = c_capex / c_lcca * 100
    maint_pct   = (c_opex_life - c_energy_life) / c_lcca * 100
    saving_1pct = c_energy_yr / max(eta_p, 0.01) * 0.01

    kpi_items = [
        ("🏭", "TOTAL CAPEX",           f"${c_capex:,.0f}",        "#58a6ff", "Equipment + Install + EPC"),
        ("⚡", "ENERGY / YEAR",         f"${c_energy_yr:,.0f}",    "#ffd740", f"{P_mot_kw:.1f} kW × {op_h} hr"),
        ("🔧", "TOTAL OPEX / YEAR",     f"${c_opex_yr:,.0f}",      "#3fb950", "Energy + Maint + Seal + More"),
        ("📅", f"LIFECYCLE {life_yr}yr", f"${c_lcca:,.0f}",        "#f78166", f"CAPEX + {life_yr}yr OPEX"),
        ("📈", "NPV OF OPEX",           f"${c_npv_opex:,.0f}",     "#d2a8ff", f"@ {r_disc*100:.0f}% discount rate"),
        ("🌿", "CO₂/YEAR",              f"{co2_yr_kg/1000:.2f} t", "#56d364", "IEA: 0.233 kg/kWh"),
    ]

    kpi_html = "".join([
        f"""<div style='background:linear-gradient(135deg,{col}25,{col}08);
            border:1px solid {col}60;border-radius:14px;padding:16px 10px;text-align:center;'>
          <div style='font-size:1.6rem;margin-bottom:4px;'>{icon}</div>
          <div style='font-size:.63rem;color:{col};text-transform:uppercase;
                      letter-spacing:1px;font-weight:800;margin-bottom:8px;'>{lbl}</div>
          <div style='font-size:1.20rem;font-weight:900;color:#ffffff;
                      font-family:JetBrains Mono,monospace;margin-bottom:5px;'>{val}</div>
          <div style='font-size:.63rem;color:#8b949e;'>{sub}</div>
        </div>"""
        for icon, lbl, val, col, sub in kpi_items
    ])

    st.markdown(f"""
<div style='display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:18px 0;'>
  {kpi_html}
</div>""", unsafe_allow_html=True)

    # ── Cost composition bar ──────────────────────────────────────────────────
    st.markdown(f"""
<div style='background:linear-gradient(135deg,#ffd74015,#ffd74005);
     border:1px solid #ffd74045;border-radius:12px;padding:14px 20px;margin-bottom:18px;'>
  <div style='font-size:.78rem;font-weight:800;color:#ffd740;letter-spacing:1px;margin-bottom:10px;'>
    ⚡ LIFECYCLE COST COMPOSITION — {life_yr} YEARS  |  Total: ${c_lcca:,.0f}
  </div>
  <div style='display:flex;height:22px;border-radius:8px;overflow:hidden;margin-bottom:10px;'>
    <div style='width:{capex_pct:.1f}%;background:#58a6ff;display:flex;align-items:center;
                justify-content:center;font-size:.65rem;color:#000;font-weight:800;'>
      {capex_pct:.0f}%</div>
    <div style='width:{energy_pct:.1f}%;background:#ffd740;display:flex;align-items:center;
                justify-content:center;font-size:.65rem;color:#000;font-weight:800;'>
      {energy_pct:.0f}%</div>
    <div style='width:{maint_pct:.1f}%;background:#3fb950;display:flex;align-items:center;
                justify-content:center;font-size:.65rem;color:#000;font-weight:800;'>
      {maint_pct:.0f}%</div>
  </div>
  <div style='display:flex;gap:24px;flex-wrap:wrap;align-items:center;'>
    <span style='font-size:.75rem;color:#58a6ff;font-weight:700;'>■ CAPEX {capex_pct:.1f}% (${c_capex:,.0f})</span>
    <span style='font-size:.75rem;color:#ffd740;font-weight:700;'>■ Energy {energy_pct:.1f}% (${c_energy_life:,.0f})</span>
    <span style='font-size:.75rem;color:#3fb950;font-weight:700;'>■ Maintenance {maint_pct:.1f}% (${c_opex_life-c_energy_life:,.0f})</span>
    <span style='font-size:.75rem;color:#ff7b72;margin-left:auto;font-weight:800;'>
      💡 Every +1% efficiency saves ${saving_1pct:,.0f}/yr</span>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Shared table renderer ─────────────────────────────────────────────────
    def _cost_table(hdr_color, icon, title, rows):
        rows_html = ""
        for i, (lbl, val, note) in enumerate(rows):
            is_total = lbl.startswith("★") or "TOTAL" in lbl.upper()
            row_bg   = (f"background:linear-gradient(90deg,{hdr_color}22,{hdr_color}08);"
                        if is_total else
                        ("background:rgba(255,255,255,0.05);" if i%2==0 else "background:transparent;"))
            lbl_col  = "#ffffff" if is_total else "#d0d7de"
            val_col  = hdr_color if is_total else "#e6edf3"
            fw       = "900" if is_total else "600"
            border   = (f"border-top:2px solid {hdr_color}60;border-bottom:2px solid {hdr_color}60;"
                        if is_total else "border-bottom:1px solid rgba(255,255,255,0.07);")
            rows_html += (
                f"<tr style='{row_bg}{border}'>"
                f"<td style='padding:10px 16px;color:{lbl_col};font-size:.85rem;"
                f"font-weight:{fw};width:36%;'>{lbl}</td>"
                f"<td style='padding:10px 16px;color:{val_col};"
                f"font-family:JetBrains Mono,monospace;font-size:.88rem;"
                f"font-weight:{fw};text-align:right;width:24%;'>{val}</td>"
                f"<td style='padding:10px 16px;color:#8b949e;font-size:.73rem;"
                f"font-style:italic;'>{note}</td></tr>"
            )
        return f"""
<div style='background:#0d1117;border-radius:12px;overflow:hidden;
     border:1px solid {hdr_color}45;margin-bottom:14px;'>
  <div style='background:linear-gradient(90deg,{hdr_color}35,{hdr_color}08);
       border-left:5px solid {hdr_color};padding:11px 18px;'>
    <span style='font-size:.88rem;font-weight:900;color:{hdr_color};
                 text-transform:uppercase;letter-spacing:1.5px;'>
      {icon} {title}</span>
  </div>
  <table style='width:100%;border-collapse:collapse;'>
    <thead><tr style='background:{hdr_color}22;'>
      <th style='padding:7px 16px;text-align:left;color:{hdr_color};font-size:.72rem;
                 text-transform:uppercase;letter-spacing:.8px;font-weight:700;width:36%;'>Item</th>
      <th style='padding:7px 16px;text-align:right;color:{hdr_color};font-size:.72rem;
                 text-transform:uppercase;letter-spacing:.8px;font-weight:700;width:24%;'>Amount (USD)</th>
      <th style='padding:7px 16px;text-align:left;color:{hdr_color};font-size:.72rem;
                 text-transform:uppercase;letter-spacing:.8px;font-weight:700;'>Basis / Reference</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""

    # ── CAPEX Tables ──────────────────────────────────────────────────────────
    with st.expander("🏗️ CAPEX — Capital Cost Breakdown (Lang Factor Method)", expanded=False):
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(_cost_table("#58a6ff", "🔩", "Equipment Costs (Bare — CEPCI 2024)", [
                ("Pump (bare)",       f"${c_pump_bare:,.0f}",   f"${_equip_base}/kW^0.65 × {P_sh_kw:.1f} kW"),
                ("Motor (IE3)",       f"${c_motor_bare:,.0f}",  f"$280/kW^0.72 × {P_mot_kw:.1f} kW"),
                ("Mechanical Seal",   f"${c_seal:,.0f}",        "12% of pump — API 682 4th Ed."),
                ("Flexible Coupling", f"${c_coupling:,.0f}",    "4% of pump — API 671"),
                ("Epoxy Baseplate",   f"${c_baseplate:,.0f}",   "6% of pump — API 610 §6.1.1"),
                ("★ Equipment Total", f"${c_equip_total:,.0f}", "Sum of all bare equipment"),
            ]), unsafe_allow_html=True)
        with cc2:
            st.markdown(_cost_table("#ffd740", "🏗️", "Installed Cost (Lang Factor — Peters & Timmerhaus)", [
                ("Equipment (bare)",    f"${c_equip_total:,.0f}", "Direct equipment"),
                ("Piping & Instr.",     f"${c_piping:,.0f}",      "45% of equip — Crane TP-410"),
                ("Civil & Structural",  f"${c_civil:,.0f}",       "15% of equip"),
                ("Electrical",          f"${c_electrical:,.0f}",  "12% of equip"),
                ("Insulation + Paint",  f"${c_insulation+c_painting:,.0f}", "5% of equip"),
                ("Direct Total",        f"${c_direct:,.0f}",      "All direct items"),
                ("Indirect — EPC Mgmt", f"${c_indirect:,.0f}",   "25% — Engg. + Procurement"),
                ("Contingency 10%",     f"${c_contingency:,.0f}", "Peters & Timmerhaus Table 6-3"),
                ("Commissioning 3%",    f"${c_commission:,.0f}",  "Startup & testing"),
                ("★ TOTAL CAPEX",       f"${c_capex:,.0f}",       "ROM ±40% accuracy (Pre-FEED)"),
            ]), unsafe_allow_html=True)

    # ── OPEX Tables ───────────────────────────────────────────────────────────
    with st.expander("⚡ OPEX — Annual Operating Cost & Lifecycle Analysis (HI 9.6.4)", expanded=False):
        oc1, oc2 = st.columns(2)
        with oc1:
            st.markdown(_cost_table("#3fb950", "📅", "Annual OPEX Breakdown", [
                ("Energy (electricity)", f"${c_energy_yr:,.0f}/yr",
                 f"P={P_mot_kw:.1f}kW × {op_h}h × ${tariff_kwh}/kWh"),
                ("Maintenance & Parts",  f"${c_maint_yr:,.0f}/yr",  "3% pump cost — HI 9.6.4"),
                ("Seal Replacement",     f"${c_seal_yr:,.0f}/yr",   "20% seal cost amortized/yr"),
                ("Lubrication",          f"${c_lube_yr:,.0f}/yr",   "0.5% pump cost/yr"),
                ("Inspection & Monit.",  f"${c_inspect_yr:,.0f}/yr","1.5% pump cost/yr"),
                ("Overhead / Admin",     f"${c_overhead_yr:,.0f}/yr","10% of maint. + seal"),
                ("★ TOTAL OPEX/Year",    f"${c_opex_yr:,.0f}/yr",   "Complete annual operating cost"),
            ]), unsafe_allow_html=True)
        with oc2:
            st.markdown(_cost_table("#f78166", "📊", f"{life_yr}-Year Lifecycle (NPV @ {r_disc*100:.0f}%)", [
                ("Total CAPEX",               f"${c_capex:,.0f}",        "Equipment + install"),
                (f"Energy ({life_yr}yr)",     f"${c_energy_life:,.0f}",  f"${c_energy_yr:,.0f}/yr × {life_yr}yr"),
                (f"Total OPEX ({life_yr}yr)", f"${c_opex_life:,.0f}",    f"${c_opex_yr:,.0f}/yr × {life_yr}yr"),
                ("NPV of OPEX",               f"${c_npv_opex:,.0f}",     f"Discount rate {r_disc*100:.0f}%"),
                ("★ LIFE CYCLE COST",         f"${c_lcca:,.0f}",         "CAPEX + Total OPEX"),
                ("Energy % of LCC",           f"{energy_pct:.1f}%",      "Dominant cost driver"),
                ("Efficiency Penalty",         f"${eta_penalty:,.0f}",    f"η={eta_p*100:.0f}% vs 75% BEP"),
                (f"CO₂ Emitted ({life_yr}yr)",f"{co2_life_t:.1f} t",    "@ 0.233 kg/kWh (IEA avg.)"),
            ]), unsafe_allow_html=True)

        # Plotly donut chart
        try:
            import plotly.graph_objects as go
            fig_pie = go.Figure(go.Pie(
                labels=["CAPEX", "Energy", "Maintenance", "Seal+Lube+Insp.", "Overhead"],
                values=[c_capex, c_energy_life,
                        c_maint_yr*life_yr,
                        (c_seal_yr+c_lube_yr+c_inspect_yr)*life_yr,
                        c_overhead_yr*life_yr],
                hole=0.58,
                marker=dict(
                    colors=["#58a6ff","#ffd740","#3fb950","#d2a8ff","#f78166"],
                    line=dict(color="#0d1117", width=3)
                ),
                textfont=dict(size=12, color="#ffffff"),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_pie.update_layout(
                title=dict(
                    text=f"<b>{life_yr}-Year Life Cycle Cost — ${c_lcca/1e6:.2f}M Total</b>",
                    font=dict(color="#ffffff", size=14), x=0.5
                ),
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font=dict(color="#c9d1d9"),
                legend=dict(font=dict(color="#c9d1d9",size=12), bgcolor="rgba(0,0,0,0)",
                            orientation="h", y=-0.1),
                annotations=[dict(
                    text=f"<b>${c_lcca/1e6:.2f}M</b><br>Total LCC",
                    font=dict(size=14, color="#ffffff"), showarrow=False
                )],
                margin=dict(t=50, b=40, l=10, r=10),
                height=360,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        except Exception:
            pass


    with st.expander("📋 Cost Report — Download PDF / Word", expanded=False):

        # Build cost report text for PDF/Word
        def _build_cost_report_data():
            return {
                "Project":              "SmartPump Designer",
                "Pump Type":            pump_type,
                "Flow Rate (m³/h)":     f"{Q_m3h:.2f}",
                "Total Head (m)":       f"{H_tot:.2f}",
                "Shaft Power (kW)":     f"{P_sh_kw:.2f}",
                "Motor Power (kW)":     f"{P_mot_kw:.2f}",
                "Pump Efficiency (%)":  f"{eta_p*100:.1f}",
                "Operating Hours/yr":   f"{op_h}",
                "Electricity ($/kWh)":  f"{tariff_kwh:.3f}",
                "Equipment Life (yr)":  f"{life_yr}",
                "Discount Rate (%)":    f"{r_disc*100:.0f}",
                "── CAPEX ──":          "──────────────────",
                "Pump (bare)":          f"${c_pump_bare:,.0f}",
                "Motor (IE3)":          f"${c_motor_bare:,.0f}",
                "Seal (API 682)":       f"${c_seal:,.0f}",
                "Coupling (API 671)":   f"${c_coupling:,.0f}",
                "Baseplate":            f"${c_baseplate:,.0f}",
                "Equipment Total":      f"${c_equip_total:,.0f}",
                "Piping & Instr.":      f"${c_piping:,.0f}",
                "Civil & Struct.":      f"${c_civil:,.0f}",
                "Electrical":           f"${c_electrical:,.0f}",
                "EPC Indirect":         f"${c_indirect:,.0f}",
                "Contingency (10%)":    f"${c_contingency:,.0f}",
                "Commissioning (3%)":   f"${c_commission:,.0f}",
                "TOTAL CAPEX":          f"${c_capex:,.0f}",
                "── ANNUAL OPEX ──":    "──────────────────",
                "Energy (Electricity)": f"${c_energy_yr:,.0f}/yr",
                "Maintenance":          f"${c_maint_yr:,.0f}/yr",
                "Seal Replacement":     f"${c_seal_yr:,.0f}/yr",
                "Lubrication":          f"${c_lube_yr:,.0f}/yr",
                "Inspection":           f"${c_inspect_yr:,.0f}/yr",
                "TOTAL OPEX/Year":      f"${c_opex_yr:,.0f}/yr",
                "── LIFECYCLE ──":      "──────────────────",
                f"Energy ({life_yr}yr)":f"${c_energy_life:,.0f}",
                f"OPEX ({life_yr}yr)":  f"${c_opex_life:,.0f}",
                "NPV of OPEX":          f"${c_npv_opex:,.0f}",
                "TOTAL LIFE CYCLE":     f"${c_lcca:,.0f}",
                "Energy % of LCC":      f"{c_energy_life/c_lcca*100:.1f}%",
                f"CO₂ ({life_yr}yr)":   f"{co2_life_t:.1f} tonnes",
                "── REFERENCE ──":      "──────────────────",
                "Cost Method":          "Lang Factor (Peters & Timmerhaus)",
                "OPEX Method":          "HI 9.6.4 Lifecycle Cost Analysis",
                "Accuracy":             "ROM ±40% — Pre-FEED stage estimate",
                "Standard":             "API 610 12th Ed. / API 686 / HI 9.6.4",
            }

        cost_dl1, cost_dl2, cost_dl3 = st.columns(3)

        with cost_dl1:
            try:
                _cost_pdf = build_pdf(
                    pump_type,
                    _build_cost_report_data(), {}, {},
                    ds_sections=None
                )
                st.download_button(
                    "📄 Cost Report (PDF)",
                    data=_cost_pdf,
                    file_name=f"cost_estimation_{pump_type.lower()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="cost_pdf_dl"
                )
            except Exception as _ce:
                st.error(f"PDF: {_ce}")

        with cost_dl2:
            try:
                _cost_docx = build_docx(
                    pump_type,
                    _build_cost_report_data(), {}, {},
                    ds_sections=None
                )
                st.download_button(
                    "📝 Cost Report (Word)",
                    data=_cost_docx,
                    file_name=f"cost_estimation_{pump_type.lower()}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="cost_docx_dl"
                )
            except Exception as _ce:
                st.error(f"Word: {_ce}")

        with cost_dl3:
            import csv, io as _io
            _cost_csv_buf = _io.StringIO()
            _cwr = csv.writer(_cost_csv_buf)
            _cwr.writerow(["Parameter", "Value"])
            for k, v in _build_cost_report_data().items():
                _cwr.writerow([k, v])
            st.download_button(
                "📊 Cost Report (CSV)",
                data=_cost_csv_buf.getvalue().encode("utf-8"),
                file_name=f"cost_estimation_{pump_type.lower()}.csv",
                mime="text/csv",
                use_container_width=True,
                key="cost_csv_dl"
            )

        info_box(
            f"Cost basis: Lang Factor method (Peters & Timmerhaus, 9th Ed.) · "
            f"OPEX: HI 9.6.4 Lifecycle Analysis · "
            f"Accuracy: ROM ±40% (Pre-FEED) · "
            f"Energy dominates LCC at <b>{c_energy_life/c_lcca*100:.0f}%</b> — "
            f"every 1% η improvement saves <b>${c_energy_yr/eta_p*0.01:,.0f}/yr</b>"
        )

# =============================================================================
# SECTION 6 — PERFORMANCE GRAPHS
# =============================================================================
divider()
sec("📈  SECTION 6 — PUMP PERFORMANCE GRAPHS", th["accent3"])

if pump_type == "Centrifugal":
    tab1,tab2,tab3,tab4 = st.tabs(
        ["🔵 H-Q + System","🟢 Efficiency","🟠 Power","🔴 Dashboard"])
    with tab1:
        fig_hq, op_Q, op_H = hq_with_system(
            Q_m3s, H_tot, z_static, f_D, cfg["pipe_L"], D_m_ss,
            cfg["K_fit"], eta_p, th_plot)
        st.plotly_chart(fig_hq, use_container_width=True)
        info_box(f"Operating Point: Q = {op_Q:.2f} m³/h  |  H = {op_H:.2f} m")
    with tab2:
        st.plotly_chart(efficiency_curve(Q_m3s, H_tot, eta_p, th_plot),
                        use_container_width=True)
    with tab3:
        st.plotly_chart(power_curve(Q_m3s, H_tot, eta_p, th_plot),
                        use_container_width=True)
    with tab4:
        st.plotly_chart(combined_dashboard(
            Q_m3s, H_tot, z_static, f_D, cfg["pipe_L"], D_m_ss,
            cfg["K_fit"], eta_p, th_plot), use_container_width=True)

elif pump_type == "Reciprocating":
    Q_act_r = res_s.get("Actual Flow (m³/s)", Q_m3s)
    st.plotly_chart(recip_dashboard(Q_act_r, H_tot, N_rpm,
                                     sp.get("n_cyl", 3), th_plot),
                    use_container_width=True)
elif pump_type == "Plunger":
    Q_act_p = res_s.get("Actual Flow (m³/s)", Q_m3s)
    st.plotly_chart(plunger_dashboard(Q_act_p, H_tot, N_rpm,
                                       sp.get("n_pl", 3), th_plot),
                    use_container_width=True)
elif pump_type == "Gear":
    st.plotly_chart(gear_dashboard(Q_m3s, mu, sp.get("vol_eff_pct",90)/100, th_plot),
                    use_container_width=True)

# =============================================================================
# SECTION 6b — VFD & AFFINITY LAWS SIMULATION
# =============================================================================
divider()
sec("🎛️  SECTION 6b — VFD & PERFORMANCE CONTROL  (Affinity Laws Simulation)", th["accent2"])

from modules.vfd_affinity import (
    affinity_laws, energy_savings_pct,
    plot_speed_vs_flow, plot_speed_vs_head,
    plot_speed_vs_power, plot_combined_vfd,
)

# ── VFD intro banner ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,{th['accent2']}18,{th['accent']}08);
     border:1px solid {th['accent2']}50;border-radius:14px;
     padding:16px 22px;margin-bottom:18px;">
  <div style="font-size:1.05rem;font-weight:900;color:{th['accent2']};
              letter-spacing:1px;margin-bottom:6px;">
    ⚡ Variable Frequency Drive (VFD) Simulation
  </div>
  <div style="font-size:.84rem;color:{th['text']};line-height:1.7;">
    Simulate real industrial pump behaviour under speed-controlled operation.
    Affinity Laws (HI&nbsp;1.3.4 / API&nbsp;610&nbsp;§5.3) define how <b>Flow, Head,
    and Power</b> scale with shaft speed — the foundation of VFD energy optimisation.<br>
    <span style="color:{th['metric_lbl']};font-size:.78rem;">
      Base values are taken directly from your design calculation above. No existing
      results are modified.
    </span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Affinity Law cards ────────────────────────────────────────────────────────
law_html = "".join([
    f"""<div style="background:{th['card_bg']};border:1px solid {th['border']};
         border-radius:12px;padding:14px 16px;text-align:center;">
      <div style="font-size:1.5rem;margin-bottom:6px;">{icon}</div>
      <div style="font-size:.72rem;color:{th['metric_lbl']};text-transform:uppercase;
                  letter-spacing:1px;margin-bottom:6px;font-weight:700;">{title}</div>
      <div style="font-size:1rem;font-weight:900;font-family:'JetBrains Mono',monospace;
                  color:{color};">{law}</div>
      <div style="font-size:.70rem;color:{th['metric_lbl']};margin-top:4px;">{note}</div>
    </div>"""
    for icon, title, law, color, note in [
        ("🌊", "Flow Law",  "Q ∝ N",  th["accent"],  "Linear with speed"),
        ("🔺", "Head Law",  "H ∝ N²", th["accent3"], "Square of speed ratio"),
        ("⚡", "Power Law", "P ∝ N³", "#50fa7b",     "Cube of speed ratio — key to energy saving"),
        ("💰", "Saving",    "1 − (N/N₀)³", "#ffd740","% energy saved vs throttle valve"),
    ]
])
st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;">
  {law_html}
</div>""", unsafe_allow_html=True)

# ── Speed control input ───────────────────────────────────────────────────────
vfd_c1, vfd_c2 = st.columns([2, 1])

with vfd_c1:
    st.markdown(f"<div style='font-size:.80rem;font-weight:700;color:{th['metric_lbl']};"
                "text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px;'>"
                "🎚️ Set VFD Speed Control</div>", unsafe_allow_html=True)

    vfd_mode = st.radio(
        "Speed input mode",
        ["% of Base Speed", "Absolute RPM"],
        horizontal=True,
        key="vfd_mode",
        label_visibility="collapsed",
    )

    if vfd_mode == "% of Base Speed":
        vfd_pct = st.slider(
            f"Speed (% of Base {N_rpm} RPM)",
            min_value=20, max_value=110, value=80, step=1,
            format="%d%%", key="vfd_pct_slider"
        )
        N_vfd = N_rpm * vfd_pct / 100
    else:
        N_vfd = st.number_input(
            "Speed (RPM)",
            min_value=int(N_rpm * 0.20),
            max_value=int(N_rpm * 1.10),
            value=int(N_rpm * 0.80),
            step=10,
            key="vfd_rpm_input",
        )
        vfd_pct = N_vfd / N_rpm * 100

    # Show live speed badge
    st.markdown(f"""
<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:8px;">
  <div style="background:{th['card_bg']};border:1px solid {th['border']};
       border-radius:8px;padding:8px 18px;text-align:center;">
    <div style="font-size:.65rem;color:{th['metric_lbl']};text-transform:uppercase;
                letter-spacing:.8px;">VFD Speed</div>
    <div style="font-size:1.3rem;font-weight:900;font-family:'JetBrains Mono',monospace;
                color:{th['accent2']};">{N_vfd:.0f} RPM</div>
  </div>
  <div style="background:{th['card_bg']};border:1px solid {th['border']};
       border-radius:8px;padding:8px 18px;text-align:center;">
    <div style="font-size:.65rem;color:{th['metric_lbl']};text-transform:uppercase;
                letter-spacing:.8px;">% of Base</div>
    <div style="font-size:1.3rem;font-weight:900;font-family:'JetBrains Mono',monospace;
                color:{th['accent2']};">{vfd_pct:.1f}%</div>
  </div>
  <div style="background:{th['card_bg']};border:1px solid {th['border']};
       border-radius:8px;padding:8px 18px;text-align:center;">
    <div style="font-size:.65rem;color:{th['metric_lbl']};text-transform:uppercase;
                letter-spacing:.8px;">Base Speed</div>
    <div style="font-size:1.3rem;font-weight:900;font-family:'JetBrains Mono',monospace;
                color:#ffd740;">{N_rpm:.0f} RPM</div>
  </div>
</div>""", unsafe_allow_html=True)

with vfd_c2:
    st.markdown(f"<div style='font-size:.80rem;font-weight:700;color:{th['metric_lbl']};"
                "text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px;'>"
                "📌 Base Design Values</div>", unsafe_allow_html=True)
    base_items = [
        ("Flow Q₀",  f"{Q_m3h:.3f} m³/h"),
        ("Head H₀",  f"{H_tot:.2f} m"),
        ("Power P₀", f"{P_sh/1000:.4f} kW"),
        ("Speed N₀", f"{N_rpm:.0f} RPM"),
    ]
    for lbl, val in base_items:
        st.markdown(f"""
<div style="background:{th['card_bg']};border:1px solid {th['border']};
     border-radius:8px;padding:8px 14px;margin-bottom:6px;
     display:flex;justify-content:space-between;align-items:center;">
  <span style="color:{th['metric_lbl']};font-size:.82rem;">{lbl}</span>
  <span style="color:{th['accent']};font-weight:800;font-family:'JetBrains Mono',monospace;
               font-size:.88rem;">{val}</span>
</div>""", unsafe_allow_html=True)

# ── Live affinity calculation ─────────────────────────────────────────────────
vfd_res  = affinity_laws(Q_m3h, H_tot, P_sh/1000, N_rpm, N_vfd)
vfd_save = energy_savings_pct(N_vfd, N_rpm)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:.80rem;font-weight:700;color:{th['metric_lbl']};"
            "text-transform:uppercase;letter-spacing:.8px;margin-bottom:12px;'>"
            "🔢 Real-Time Affinity Law Results</div>", unsafe_allow_html=True)

# Results KPI cards
kpi_vfd = [
    ("🌊", "Flow Q_new",  f"{vfd_res['Q_new']:.3f}", "m³/h",
     f"Q₀ × {vfd_res['ratio']:.3f}",          th["accent"]),
    ("🔺", "Head H_new",  f"{vfd_res['H_new']:.3f}", "m",
     f"H₀ × {vfd_res['ratio']**2:.4f}",       th["accent3"]),
    ("⚡", "Power P_new", f"{vfd_res['P_new']:.4f}", "kW",
     f"P₀ × {vfd_res['ratio']**3:.5f}",       "#50fa7b"),
    ("💰", "Energy Saved", f"{vfd_save:.1f}", "%",
     "vs throttle valve control",              "#ffd740"),
    ("📉", "Speed Ratio",  f"{vfd_res['ratio']:.4f}", "",
     f"N_vfd / N_base = {N_vfd:.0f}/{N_rpm:.0f}", th["accent2"]),
]

kpi_cols = st.columns(5)
for col, (icon, label, val, unit, sub, color) in zip(kpi_cols, kpi_vfd):
    col.markdown(f"""
<div style="background:linear-gradient(135deg,{color}22,{color}08);
     border:1px solid {color}55;border-radius:14px;padding:14px 10px;text-align:center;">
  <div style="font-size:1.5rem;">{icon}</div>
  <div style="font-size:.62rem;color:{color};text-transform:uppercase;
              letter-spacing:1px;font-weight:800;margin:5px 0;">{label}</div>
  <div style="font-size:1.25rem;font-weight:900;color:#ffffff;
              font-family:'JetBrains Mono',monospace;">{val}<span style="font-size:.75rem;
              color:{th['metric_lbl']};margin-left:3px;">{unit}</span></div>
  <div style="font-size:.63rem;color:{th['metric_lbl']};margin-top:4px;">{sub}</div>
</div>""", unsafe_allow_html=True)

# ── Calculation detail box ────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📐 Affinity Law Calculation Detail (HI 1.3.4 / Karassik 4th Ed. §2.4)", expanded=False):
    ratio = vfd_res["ratio"]
    cbox(
        title="Speed Ratio",
        formula="ratio = N_new / N_base",
        sub=f"= {N_vfd:.1f} / {N_rpm:.1f}",
        result=f"ratio = {ratio:.4f}  ({vfd_pct:.1f}% of base speed)",
        params={"N_new (VFD speed)": f"{N_vfd:.1f} RPM",
                "N_base (base speed)": f"{N_rpm:.1f} RPM"}
    )
    cbox(
        title="New Flow Rate  [Q ∝ N]",
        formula="Q_new = Q_base × (N_new / N_base)",
        sub=f"= {Q_m3h:.3f} × {ratio:.4f}",
        result=f"Q_new = {vfd_res['Q_new']:.3f} m³/h",
        params={"Q_base (base flow)": f"{Q_m3h:.3f} m³/h",
                "Speed ratio": f"{ratio:.4f}"}
    )
    cbox(
        title="New Total Head  [H ∝ N²]",
        formula="H_new = H_base × (N_new / N_base)²",
        sub=f"= {H_tot:.3f} × {ratio:.4f}² = {H_tot:.3f} × {ratio**2:.5f}",
        result=f"H_new = {vfd_res['H_new']:.3f} m",
        params={"H_base (base head)": f"{H_tot:.3f} m",
                "Speed ratio²": f"{ratio**2:.5f}"}
    )
    cbox(
        title="New Shaft Power  [P ∝ N³]",
        formula="P_new = P_base × (N_new / N_base)³",
        sub=f"= {P_sh/1000:.4f} × {ratio:.4f}³ = {P_sh/1000:.4f} × {ratio**3:.6f}",
        result=f"P_new = {vfd_res['P_new']:.4f} kW",
        params={"P_base (base shaft power)": f"{P_sh/1000:.4f} kW",
                "Speed ratio³": f"{ratio**3:.6f}"}
    )
    cbox(
        title="Energy Saving vs Throttle Valve",
        formula="Saving (%) = (1 − ratio³) × 100",
        sub=f"= (1 − {ratio:.4f}³) × 100 = (1 − {ratio**3:.5f}) × 100",
        result=f"Energy Saved = {vfd_save:.2f}%   vs. constant-power throttle control",
        params={"Speed ratio": f"{ratio:.4f}",
                "ratio³":      f"{ratio**3:.5f}",
                "Reference":   "HI 9.6.4 — VFD vs Throttle Valve Energy Analysis"}
    )

    # HI compliance note
    if N_vfd < N_rpm * 0.20:
        st.warning("⚠️ Speed below 20% of base — risk of overheating, bearing lubrication failure. "
                   "HI §1.3.4 recommends VFD minimum speed ≥ 20–25% of rated speed.")
    elif N_vfd > N_rpm * 1.05:
        st.warning("⚠️ Speed above 105% of base — verify motor, bearing, and shaft ratings "
                   "for overspeed condition (API 610 §5.3.5).")
    else:
        success_box(f"Operating at {vfd_pct:.1f}% of base speed — within HI recommended VFD range.")

# ── Performance graphs ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:.80rem;font-weight:700;color:{th['metric_lbl']};"
            "text-transform:uppercase;letter-spacing:.8px;margin-bottom:12px;'>"
            "📈 VFD Performance Graphs</div>", unsafe_allow_html=True)

vfd_tab1, vfd_tab2, vfd_tab3, vfd_tab4 = st.tabs([
    "🌊 Speed vs Flow",
    "🔺 Speed vs Head",
    "⚡ Speed vs Power",
    "📊 Combined Dashboard",
])

with vfd_tab1:
    st.plotly_chart(
        plot_speed_vs_flow(Q_m3h, H_tot, P_sh/1000, N_rpm, N_vfd, th_plot),
        use_container_width=True
    )
    info_box(f"At {N_vfd:.0f} RPM ({vfd_pct:.1f}%), flow changes from "
             f"<b>{Q_m3h:.3f}</b> → <b>{vfd_res['Q_new']:.3f} m³/h</b>  "
             f"(ratio: {vfd_res['ratio']:.4f})")

with vfd_tab2:
    st.plotly_chart(
        plot_speed_vs_head(Q_m3h, H_tot, P_sh/1000, N_rpm, N_vfd, th_plot),
        use_container_width=True
    )
    info_box(f"At {N_vfd:.0f} RPM ({vfd_pct:.1f}%), head changes from "
             f"<b>{H_tot:.3f}</b> → <b>{vfd_res['H_new']:.3f} m</b>  "
             f"(ratio²: {vfd_res['ratio']**2:.5f})")

with vfd_tab3:
    st.plotly_chart(
        plot_speed_vs_power(Q_m3h, H_tot, P_sh/1000, N_rpm, N_vfd, th_plot),
        use_container_width=True
    )
    if vfd_save > 0:
        success_box(f"VFD saves <b>{vfd_save:.1f}%</b> energy vs throttle valve at this speed. "
                    f"Power: <b>{P_sh/1000:.4f}</b> → <b>{vfd_res['P_new']:.4f} kW</b>.")
    else:
        warn_box("Operating above base speed — power consumption increases above rated.")

with vfd_tab4:
    st.plotly_chart(
        plot_combined_vfd(Q_m3h, H_tot, P_sh/1000, N_rpm, N_vfd, th_plot),
        use_container_width=True
    )
    info_box("Combined 4-panel dashboard: Flow, Head, Power curves + Affinity comparison bar chart. "
             "Green shaded area = energy saved by VFD vs constant-speed throttle control.")

# ── Industry context note ─────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{th['card_bg']};border:1px solid {th['border']};
     border-radius:10px;padding:14px 20px;margin-top:16px;">
  <div style="font-size:.78rem;font-weight:800;color:{th['accent']};
              margin-bottom:8px;letter-spacing:.5px;">
    📚 Engineering Reference — VFD Affinity Laws (HI 1.3.4 / API 610 §5.3)
  </div>
  <div style="font-size:.78rem;color:{th['text']};line-height:1.7;">
    • <b>HI Standard 1.3.4</b> defines Affinity Laws for centrifugal pump variable speed operation.<br>
    • <b>API 610 §5.3.5</b> — VFD operating range typically <b>70%–105%</b> of rated speed (verify with vendor).<br>
    • <b>Energy savings:</b> Reducing speed to 80% saves <b>~49%</b> power  |  70% → <b>~66%</b> saving  (cubic law).<br>
    • <b>Minimum speed:</b> HI recommends ≥ 20–25% to avoid bearing and lubrication issues.<br>
    • <b>Real-world use:</b> VFDs are standard in HVAC, water treatment, process plants for flow control.
  </div>
</div>""", unsafe_allow_html=True)

# =============================================================================
# SECTION 7 — AI ENGINEERING ADVISOR  (SESSION STATE FIX)
# =============================================================================
divider()
sec("🤖  SECTION 7 — AI ENGINEERING ADVISOR", th["accent4"])

if not cfg["groq_key"]:
    info_box("Enter your <b>Groq API key</b> in the sidebar to activate the AI advisor. "
             "Free key at <b>console.groq.com</b>")
else:
    c_ai1, c_ai2 = st.columns(2)

    with c_ai1:
        st.markdown(f"#### 📋 Auto — Pump Selection Analysis")
        if st.button("🤖 Analyse My Pump Selection", use_container_width=True, key="btn_sel"):
            with st.spinner("AI thinking…"):
                ai_txt = get_selection_advice(
                    ai_client, pump_type, Q_m3h, H_tot, mu_cP, rho, fluid, ranking)
            st.session_state["ai_selection_text"] = ai_txt

        if st.session_state.get("ai_selection_text"):
            st.markdown(
                f'<div class="ai-response">🤖 <b>AI Selection Analysis:</b><br>'
                f'{st.session_state["ai_selection_text"]}</div>',
                unsafe_allow_html=True)

    with c_ai2:
        st.markdown(f"#### 💬 Free — Ask Anything")
        q_input = st.text_area("Your engineering question:", height=90,
                                key="ai_q_input",
                                placeholder="e.g. Why is my pump cavitating? How to reduce vibration?")
        if st.button("💬 Ask AI", use_container_width=True, key="btn_ask"):
            if q_input.strip():
                with st.spinner("AI responding…"):
                    ans = ask_question(ai_client, q_input, pump_type, Q_m3h, H_tot)
                st.session_state["ai_question_text"] = ans
            else:
                st.warning("Please type a question first.")

        if st.session_state.get("ai_question_text"):
            st.markdown(
                f'<div class="ai-response">🤖 <b>AI Answer:</b><br>'
                f'{st.session_state["ai_question_text"]}</div>',
                unsafe_allow_html=True)

# =============================================================================
# SECTION 8 — EXPORT RESULTS
# =============================================================================
# SECTION 8 — ADVANCED EXPORT BUILDER
# =============================================================================
divider()
sec("📦  SECTION 8 — ADVANCED EXPORT BUILDER", th["accent"])

now_str    = datetime.now().strftime("%Y%m%d_%H%M")
fname_base = f"pump_{pump_type}_{now_str}"

st.markdown(f"""
<div style="background:linear-gradient(135deg,{th['accent']}12,{th['accent2']}08);
     border:1px solid {th['accent']}40;border-radius:12px;padding:16px 22px;margin-bottom:18px;">
  <div style="font-size:.90rem;font-weight:800;color:{th['accent']};margin-bottom:6px;">
    📋 Build Your Custom Report Package
  </div>
  <div style="font-size:.78rem;color:{th['metric_lbl']};">
    Select what to include → generate a single file or full ZIP package with all selected items.
  </div>
</div>""", unsafe_allow_html=True)

# ── Checkbox selection grid ───────────────────────────────────────────────────
st.markdown(f"<div style='font-size:.78rem;font-weight:700;color:{th['metric_lbl']};margin-bottom:8px;letter-spacing:.5px;'>SELECT EXPORT CONTENTS:</div>", unsafe_allow_html=True)

_ec1, _ec2, _ec3 = st.columns(3)
with _ec1:
    _inc_ds     = st.checkbox("📄 API 610 Data Sheet",         value=True,  key="exp_ds")
    _inc_calc   = st.checkbox("🔢 Full Calculations Report",   value=True,  key="exp_calc")
    _inc_csv    = st.checkbox("📊 CSV Data Table",              value=False, key="exp_csv")
with _ec2:
    _inc_json   = st.checkbox("🗂️ JSON Raw Data",               value=False, key="exp_json")
    _inc_word   = st.checkbox("📝 Word Document (.docx)",       value=False, key="exp_word")
    _inc_graphs = st.checkbox("📈 Performance Graphs (PNG)",    value=False, key="exp_graphs")
with _ec3:
    _inc_npsh   = st.checkbox("💧 NPSH Analysis Summary",       value=False, key="exp_npsh")
    _inc_imp    = st.checkbox("⚙️ Impeller Design Summary",     value=False, key="exp_imp")
    _inc_ai     = st.checkbox("🤖 AI Suggestions (if available)",value=False, key="exp_ai")

_any_selected = any([_inc_ds, _inc_calc, _inc_csv, _inc_json,
                     _inc_word, _inc_graphs, _inc_npsh, _inc_imp, _inc_ai])

_total_items = sum([_inc_ds, _inc_calc, _inc_csv, _inc_json,
                    _inc_word, _inc_graphs, _inc_npsh, _inc_imp, _inc_ai])

# ── Format chooser ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_fmt_col1, _fmt_col2 = st.columns([1, 3])
with _fmt_col1:
    if _total_items > 1:
        _export_format = "ZIP Package"
        st.markdown(f"""
<div style="background:{th['accent3']}20;border:1px solid {th['accent3']}50;
     border-radius:8px;padding:10px 14px;text-align:center;">
  <div style="font-size:1.4rem;">📦</div>
  <div style="font-size:.75rem;font-weight:800;color:{th['accent3']};margin-top:4px;">
    ZIP PACKAGE
  </div>
  <div style="font-size:.68rem;color:{th['metric_lbl']};margin-top:2px;">
    {_total_items} items selected
  </div>
</div>""", unsafe_allow_html=True)
    elif _total_items == 1:
        _export_format = "Single File"
        st.markdown(f"""
<div style="background:{th['accent2']}20;border:1px solid {th['accent2']}50;
     border-radius:8px;padding:10px 14px;text-align:center;">
  <div style="font-size:1.4rem;">📄</div>
  <div style="font-size:.75rem;font-weight:800;color:{th['accent2']};margin-top:4px;">
    SINGLE FILE
  </div>
  <div style="font-size:.68rem;color:{th['metric_lbl']};margin-top:2px;">
    1 item selected
  </div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:{th['card_bg']};border:1px dashed {th['border']};
     border-radius:8px;padding:10px 14px;text-align:center;">
  <div style="font-size:.75rem;color:{th['metric_lbl']};">Select items above</div>
</div>""", unsafe_allow_html=True)

with _fmt_col2:
    # Show what will be in the package
    _items_preview = []
    if _inc_ds:     _items_preview.append("📄 api610_datasheet.pdf")
    if _inc_calc:   _items_preview.append("📊 full_calculations.pdf")
    if _inc_word:   _items_preview.append("📝 report.docx")
    if _inc_csv:    _items_preview.append("📋 data_table.csv")
    if _inc_json:   _items_preview.append("🗂️ raw_data.json")
    if _inc_graphs: _items_preview.append("📁 /graphs  →  hq_curve.png · efficiency.png · power.png")
    if _inc_npsh:   _items_preview.append("💧 npsh_analysis.pdf")
    if _inc_imp:    _items_preview.append("⚙️ impeller_summary.pdf")
    if _inc_ai:     _items_preview.append("🤖 ai_suggestions.txt")

    if _items_preview:
        preview_html = "".join([
            f"<div style='font-size:.73rem;color:{th['text']};padding:2px 0;'>"
            f"<span style='color:{th['metric_lbl']};margin-right:8px;'>→</span>{item}</div>"
            for item in _items_preview
        ])
        st.markdown(f"""
<div style="background:{th['card_bg']};border:1px solid {th['border']};
     border-radius:8px;padding:12px 16px;">
  <div style="font-size:.72rem;font-weight:700;color:{th['metric_lbl']};
              margin-bottom:8px;letter-spacing:.5px;">PACKAGE CONTENTS PREVIEW:</div>
  {preview_html}
</div>""", unsafe_allow_html=True)

# ── Generate & Download Button ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_gen_col1, _gen_col2, _gen_col3 = st.columns([2, 1, 1])

with _gen_col1:
    _do_generate = st.button(
        f"{'📦 Generate ZIP Package' if _total_items > 1 else '📄 Generate & Download'}"
        f"  ({_total_items} item{'s' if _total_items != 1 else ''} selected)",
        disabled=not _any_selected,
        use_container_width=True,
        key="generate_export"
    )

with _gen_col2:
    # Always-available quick PDF
    try:
        _quick_pdf = build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
        st.download_button("📄 Quick PDF", data=_quick_pdf,
                           file_name=f"{fname_base}.pdf", mime="application/pdf",
                           use_container_width=True, key="sec8_quick_pdf")
    except Exception as _e:
        st.error(f"PDF: {_e}")

with _gen_col3:
    # Always-available quick CSV
    _quick_csv = build_csv(inputs_d, results_d, sp_d)
    st.download_button("📊 Quick CSV", data=_quick_csv,
                       file_name=f"{fname_base}.csv", mime="text/csv",
                       use_container_width=True, key="sec8_quick_csv")

# ── Generation logic ──────────────────────────────────────────────────────────
if _do_generate and _any_selected:
    import zipfile

    _progress = st.progress(0, text="Preparing export...")
    _step = 0
    _total_steps = _total_items + 1

    def _prog(msg):
        global _step
        _step += 1
        _progress.progress(min(_step / _total_steps, 1.0), text=msg)

    # ── Build NPSH summary text ───────────────────────────────────────────────
    def _build_npsh_txt():
        lines = [
            "=" * 60,
            "  NPSH & CAVITATION ANALYSIS SUMMARY",
            "  API 610 12th Ed. · HI 9.6.1",
            "=" * 60, "",
            f"  NPSHa (Available)    : {NPSHa:.3f} m",
            f"  NPSHr (Required)     : {NPSHr:.3f} m",
            f"  NPSH Margin          : {NPSHa - NPSHr:.3f} m",
            f"  Min. Required Margin : {max(0.5, 0.10*NPSHr):.3f} m  (HI 9.6.1)",
            f"  Vapor Pressure Pv    : {Pv:.0f} Pa",
            f"  Suction Head h_s     : {cfg['h_suc']:.2f} m",
            f"  Cavitation Status    : {'SAFE' if (NPSHa-NPSHr) >= max(0.5,0.10*NPSHr) else 'RISK'}",
            "",
            "  Formula: NPSHa = (P_atm - Pv) / (rho * g) + h_s - h_f,suc",
            "=" * 60,
        ]
        return "\n".join(lines).encode("utf-8")

    # ── Build impeller summary text ───────────────────────────────────────────
    def _build_imp_txt():
        lines = ["=" * 60, "  IMPELLER DESIGN SUMMARY", "  Karassik / Stepanoff Method", "=" * 60, ""]
        for k, v_ in imp.items():
            lines.append(f"  {str(k):<42} {str(v_)}")
        lines += ["", "=" * 60]
        return "\n".join(lines).encode("utf-8")

    # ── Build AI suggestions text ─────────────────────────────────────────────
    def _build_ai_txt():
        ai_hist = st.session_state.get("ai_history", [])
        if not ai_hist:
            return b"No AI suggestions were generated in this session."
        lines = ["=" * 60, "  AI SUGGESTIONS & ANALYSIS", "=" * 60, ""]
        for entry in ai_hist:
            lines.append(f"Q: {entry.get('q', '')}")
            lines.append(f"A: {entry.get('a', '')}")
            lines.append("-" * 60)
        return "\n".join(lines).encode("utf-8")

    # ── Generate graphs as PNG bytes ──────────────────────────────────────────
    def _build_graph_pngs():
        """
        Export graphs — tries PNG (kaleido), falls back to
        self-contained interactive HTML (zero extra deps).
        """
        graphs = {}
        try:
            from graphs.centrifugal_plots import efficiency_curve, power_curve, hq_with_system
            import plotly.io as pio

            figs_to_export = {}
            try:
                fig_hq, _, _ = hq_with_system(
                    Q_m3s, H_tot, z_static, f_D, cfg["pipe_L"],
                    D_m_ss, cfg["K_fit"], eta_p, th_plot)
                figs_to_export["hq_system_curve"] = fig_hq
            except Exception: pass
            try:
                figs_to_export["efficiency_curve"] = efficiency_curve(Q_m3s, H_tot, eta_p, th_plot)
            except Exception: pass
            try:
                figs_to_export["power_curve"] = power_curve(Q_m3s, H_tot, eta_p, th_plot)
            except Exception: pass

            first = True
            for name, fig in figs_to_export.items():
                try:
                    # Try kaleido PNG
                    graphs[f"{name}.png"] = pio.to_image(
                        fig, format="png", width=1100, height=650)
                except Exception:
                    # Fallback: interactive HTML (always works)
                    html_str = fig.to_html(
                        full_html=True,
                        include_plotlyjs="cdn" if first else True,
                        config={
                            "displayModeBar": True,
                            "toImageButtonOptions": {
                                "format": "png", "width": 1100, "height": 650,
                                "filename": name
                            }
                        }
                    )
                    graphs[f"{name}.html"] = html_str.encode("utf-8")
                    first = False

            # 3D pump model — always HTML (no kaleido for 3D)
            try:
                from graphs.pump_3d import pump_3d_view, animated_flow_diagram, velocity_triangle_plot

                D2_e = float(imp.get("Outlet Diameter D₂ (mm)", D_mm_input * 4))
                D1_e = float(imp.get("Inlet / Eye Diameter D₁ (mm)", D_mm_input * 2))
                b2_e = float(imp.get("Outlet Blade Width b₂ (mm)", D_mm_input * 0.2))
                ds_e = float(imp.get("Shaft Diameter (mm)", max(20, D_mm_input * 0.3)))
                z_bl = int(imp.get("Number of Blades (recommended)", 6))
                b2d  = float(imp.get("Blade Outlet Angle β₂ (°)", 25))

                plots_3d = []
                try:
                    plots_3d.append(("3D Pump Cross-Section",
                        pump_3d_view(D2_mm=D2_e, D1_mm=D1_e, b2_mm=b2_e,
                                     shaft_dia_mm=ds_e, D_pipe_mm=D_mm_input,
                                     n_vanes=z_bl, th=th_plot)))
                except Exception: pass
                try:
                    plots_3d.append(("Animated Flow Diagram",
                        animated_flow_diagram(
                            Q_m3h=Q_m3h, H_m=H_tot,
                            D_pipe_mm=D_mm_input, pipe_L=cfg["pipe_L"],
                            h_suc=cfg["h_suc"], z_dis=z_static,
                            v_ms=v, th=th_plot)))
                except Exception: pass
                try:
                    plots_3d.append(("Velocity Triangle",
                        velocity_triangle_plot(
                            D2_mm=D2_e, b2_mm=b2_e, N_rpm=N_rpm,
                            Q_m3s=Q_m3s, beta2_deg=b2d, th=th_plot)))
                except Exception: pass

                if plots_3d:
                    header_html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<title>SmartPump Designer — 3D Pump Visualizations</title>
<style>
  body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;
        margin:0;padding:24px;}}
  h1  {{color:#58a6ff;text-align:center;font-size:1.4rem;
        letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;}}
  .sub{{color:#8b949e;text-align:center;font-size:.84rem;margin-bottom:28px;}}
  .sh {{color:#3fb950;font-size:1rem;font-weight:700;
        border-left:5px solid #3fb950;padding:7px 14px;
        background:rgba(63,185,80,0.10);margin:22px 0 10px;
        border-radius:0 6px 6px 0;letter-spacing:1px;text-transform:uppercase;}}
  .pw {{background:#161b22;border:1px solid #30363d;
        border-radius:10px;padding:8px;margin-bottom:18px;}}
  .ft {{text-align:center;font-size:.74rem;color:#8b949e;
        border-top:1px solid #30363d;margin-top:28px;padding-top:14px;}}
</style></head><body>
<h1>⚙️ SmartPump Designer — 3D Pump Visualizations</h1>
<div class="sub">API 610 · {pump_type} · Q={Q_m3h:.1f} m³/h ·
H={H_tot:.1f} m · D₂={D2_e:.0f} mm ·
Generated: {datetime.now().strftime('%d %B %Y  %H:%M')}</div>
"""
                    body_html = ""
                    inc_cdn = True
                    for title, fig in plots_3d:
                        div = fig.to_html(
                            full_html=False,
                            include_plotlyjs="cdn" if inc_cdn else False,
                            config={"displayModeBar": True,
                                    "toImageButtonOptions": {
                                        "format":"png","width":1200,"height":700,
                                        "filename": title.replace(" ","_")}}
                        )
                        body_html += (f'<div class="sh">{title}</div>'
                                      f'<div class="pw">{div}</div>')
                        inc_cdn = False

                    footer_html = (
                        f'<div class="ft">SmartPump Designer · {DEVELOPER} · '
                        f'{DEGREE} · {UNI} · Batch {BATCH}<br>'
                        f'<i>Engineering estimates only. Verify with licensed P.Eng/PE.</i>'
                        f'</div></body></html>')

                    graphs["3d_pump_model.html"] = (
                        header_html + body_html + footer_html
                    ).encode("utf-8")

            except Exception as _3de:
                graphs["3d_pump_model_error.txt"] = (
                    f"3D export error: {_3de}").encode("utf-8")

        except Exception as _ge:
            graphs["graphs_error.txt"] = str(_ge).encode("utf-8")
        return graphs

    # ── Single-file shortcut ──────────────────────────────────────────────────
    if _total_items == 1:
        _prog("Building file...")
        try:
            if _inc_ds or _inc_calc:
                _bytes = build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
                _mime  = "application/pdf"
                _ext   = "pdf"
                _label = "📄 Download PDF"
            elif _inc_word:
                _bytes = build_docx(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
                _mime  = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                _ext   = "docx"
                _label = "📝 Download Word"
            elif _inc_csv:
                _bytes = build_csv(inputs_d, results_d, sp_d)
                _mime  = "text/csv"
                _ext   = "csv"
                _label = "📊 Download CSV"
            elif _inc_json:
                _bytes = json.dumps({"inputs": inputs_d, "results": results_d, "pump_specific": sp_d}, indent=2).encode()
                _mime  = "application/json"
                _ext   = "json"
                _label = "🗂️ Download JSON"
            elif _inc_npsh:
                _bytes = _build_npsh_txt()
                _mime  = "text/plain"
                _ext   = "txt"
                _label = "💧 Download NPSH"
            elif _inc_imp:
                _bytes = _build_imp_txt()
                _mime  = "text/plain"
                _ext   = "txt"
                _label = "⚙️ Download Impeller"
            elif _inc_ai:
                _bytes = _build_ai_txt()
                _mime  = "text/plain"
                _ext   = "txt"
                _label = "🤖 Download AI Notes"
            elif _inc_graphs:
                _prog("Rendering graphs...")
                _pngs = _build_graph_pngs()
                if _pngs:
                    _bytes = next(iter(_pngs.values()))
                    _mime  = "image/png"
                    _ext   = "png"
                    _label = "📈 Download Graph"
                else:
                    st.warning("Graph generation failed.")
                    _bytes = None

            _progress.progress(1.0, text="✅ Ready!")
            if _bytes:
                st.download_button(_label, data=_bytes,
                                   file_name=f"{fname_base}.{_ext}", mime=_mime,
                                   use_container_width=True, key="single_dl")
        except Exception as _ex:
            st.error(f"Export error: {_ex}")

    else:
        # ── Build ZIP ─────────────────────────────────────────────────────────
        _zip_buf = io.BytesIO()
        with zipfile.ZipFile(_zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as _zf:

            if _inc_ds:
                _prog("Building API 610 Data Sheet PDF...")
                try:
                    _zf.writestr("api610_datasheet.pdf",
                                 build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections")))
                except Exception as _ex:
                    _zf.writestr("api610_datasheet_ERROR.txt", str(_ex))

            if _inc_calc:
                _prog("Building Full Calculations PDF...")
                try:
                    _zf.writestr("full_calculations_report.pdf",
                                 build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections")))
                except Exception as _ex:
                    _zf.writestr("full_calculations_ERROR.txt", str(_ex))

            if _inc_word:
                _prog("Building Word Document...")
                try:
                    _zf.writestr("report.docx",
                                 build_docx(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections")))
                except Exception as _ex:
                    _zf.writestr("report_docx_ERROR.txt", str(_ex))

            if _inc_csv:
                _prog("Building CSV...")
                _zf.writestr("data_table.csv", build_csv(inputs_d, results_d, sp_d))

            if _inc_json:
                _prog("Building JSON...")
                _json_bytes = json.dumps({
                    "developer": "Zunair Shahzad | UET Lahore",
                    "generated": datetime.now().isoformat(),
                    "inputs":    inputs_d,
                    "results":   results_d,
                    "pump_specific": sp_d,
                    "impeller":  {str(k): str(v_) for k, v_ in imp.items()},
                }, indent=2).encode()
                _zf.writestr("raw_data.json", _json_bytes)

            if _inc_npsh:
                _prog("Building NPSH Analysis...")
                _zf.writestr("npsh_analysis.txt", _build_npsh_txt())

            if _inc_imp:
                _prog("Building Impeller Summary...")
                _zf.writestr("impeller_summary.txt", _build_imp_txt())

            if _inc_ai:
                _prog("Building AI Notes...")
                _zf.writestr("ai_suggestions.txt", _build_ai_txt())

            if _inc_graphs:
                _prog("Rendering Performance Graphs...")
                try:
                    _pngs = _build_graph_pngs()
                    for _gname, _gbytes in _pngs.items():
                        _zf.writestr(f"graphs/{_gname}", _gbytes)
                    if not _pngs:
                        _zf.writestr("graphs/README.txt",
                                     "Graph export requires kaleido: pip install kaleido")
                except Exception as _ex:
                    _zf.writestr("graphs/ERROR.txt", str(_ex))

            # Always add README
            _readme = "\n".join([
                "=" * 60,
                "  PUMP DESIGN EXPORT PACKAGE",
                f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"  Pump Type: {pump_type}",
                "  Standard:  API 610 12th Ed.",
                "  Developer: Zunair Shahzad | UET Lahore | 2022-2026",
                "=" * 60, "",
                "CONTENTS:",
                *[f"  → {item}" for item in _items_preview],
                "",
                "REFERENCES:",
                "  [1] API 610 12th Ed.  [2] API 682 4th Ed.",
                "  [3] HI 1.1-1.6        [4] Karassik Pump Handbook 4th Ed.",
                "  [5] Perry's 9th Ed.   [6] Crane TP-410",
                "",
                "DISCLAIMER: Engineering estimates only.",
                "Verify all results with a licensed P.Eng / PE before procurement.",
                "=" * 60,
            ])
            _zf.writestr("README.txt", _readme)

        _progress.progress(1.0, text="✅ ZIP Package ready!")
        _zip_buf.seek(0)

        st.success(f"✅ ZIP package built — {_total_items} items included.")
        st.download_button(
            f"📦 Download ZIP Package  ({_total_items} files)",
            data=_zip_buf.getvalue(),
            file_name=f"project_{fname_base}.zip",
            mime="application/zip",
            use_container_width=True,
            key="zip_dl"
        )

# ── Legacy quick buttons row ──────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:20px;margin-bottom:8px;font-size:.74rem;font-weight:700;
     color:{th['metric_lbl']};letter-spacing:.5px;">
  ⚡ LEGACY QUICK EXPORT:
</div>""", unsafe_allow_html=True)

_ldl1, _ldl2, _ldl3, _ldl4 = st.columns(4)
with _ldl1:
    try:
        _leg_docx = build_docx(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
        st.download_button("📝 Word (.docx)", data=_leg_docx,
                           file_name=f"{fname_base}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True, key="leg_docx")
    except ImportError:
        st.error("Needs python-docx")

with _ldl2:
    try:
        _leg_pdf = build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=st.session_state.get("ds_sections"))
        st.download_button("📄 PDF (.pdf)", data=_leg_pdf,
                           file_name=f"{fname_base}.pdf", mime="application/pdf",
                           use_container_width=True, key="leg_pdf")
    except ImportError:
        st.error("Needs reportlab")

with _ldl3:
    _leg_csv = build_csv(inputs_d, results_d, sp_d)
    st.download_button("📊 CSV (.csv)", data=_leg_csv,
                       file_name=f"{fname_base}.csv", mime="text/csv",
                       use_container_width=True, key="leg_csv")

with _ldl4:
    _leg_json = json.dumps({
        "developer": "Zunair Shahzad | Chemical Engineering | UET Lahore 2022-2026",
        "inputs": inputs_d, "results": results_d, "pump_specific": sp_d
    }, indent=2)
    st.download_button("🗂️ JSON", data=_leg_json.encode(),
                       file_name=f"{fname_base}.json", mime="application/json",
                       use_container_width=True, key="leg_json")

# =============================================================================
# FOOTER
# =============================================================================
divider()
st.markdown(f"""
<div style="text-align:center;padding:10px 0 22px 0;">
  <div style="font-size:.88rem;color:#66bb6a;font-weight:700;">
      Developed by Zunair Shahzad
  </div>
  <div style="font-size:.82rem;color:{th['text']};opacity:.7;margin-top:3px;">
      Chemical Engineering &nbsp;|&nbsp; UET Lahore (New Campus) &nbsp;|&nbsp; 2022 – 2026
  </div>
  <div style="font-size:.75rem;color:{th['text']};opacity:.45;margin-top:6px;">
      AI-Assisted Pump Design Platform v3.1 &nbsp;|&nbsp;
      Streamlit + Plotly + Groq AI &nbsp;|&nbsp;
      API 610/674/676 · HI 1.1-1.6 · ISO 5199 · Perry's 9th Ed.<br>
      ⚠️ Engineering estimates only — all designs must be reviewed by a licensed P.Eng / PE.
  </div>
</div>""", unsafe_allow_html=True)
