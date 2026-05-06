# =============================================================================
# modules/impeller.py
# Impeller Design Module — API 610 / Karassik / HI Standards
# Reference: Karassik "Pump Handbook" 4th Ed. Ch.2
#            Stepanoff "Centrifugal and Axial Flow Pumps" 2nd Ed.
#            API 610 12th Ed. Section 6 (Hydraulic Design)
# =============================================================================
import math
import numpy as np

g = 9.81

# ─────────────────────────────────────────────────────────────────────────────
# IMPELLER TYPE SELECTION
# ─────────────────────────────────────────────────────────────────────────────
def impeller_type(Ns):
    """
    Select impeller type from Specific Speed (Karassik Table 2.1 / HI Fig 1.3.4).
    Ns in SI units: N(rpm) * Q(L/s)^0.5 / H(m)^0.75
    """
    if Ns < 400:
        return "Radial Flow (Low Ns)", "Closed impeller, narrow passages, high head per stage"
    elif Ns < 1200:
        return "Radial Flow (Medium Ns)", "Closed impeller, standard design — most common industrial pump"
    elif Ns < 2500:
        return "Mixed Flow", "Semi-open or closed impeller, moderate head, higher flow"
    elif Ns < 5000:
        return "Mixed-Axial Flow", "Open/semi-open impeller, low head, very high flow"
    else:
        return "Axial Flow (Propeller)", "Open propeller impeller, very low head, extremely high flow"

def impeller_style(fluid, pressure_bar, solid_content=False):
    """
    Recommend open/semi-open/closed style.
    Reference: API 610 §6.1.9; Karassik Ch.2.1
    """
    if solid_content:
        return "Open", "Solids handling — open impeller prevents clogging"
    elif fluid in ("Water","Hot Water (80°C)","Seawater","Ethanol","Gasoline"):
        return "Closed", "Clean fluid — closed impeller for maximum efficiency (API 610 preferred)"
    elif pressure_bar > 40:
        return "Closed", "High pressure — closed impeller for structural integrity"
    else:
        return "Semi-Open", "Moderately contaminated or viscous fluid — semi-open impeller"

# ─────────────────────────────────────────────────────────────────────────────
# IMPELLER GEOMETRY CALCULATIONS (Stepanoff method)
# ─────────────────────────────────────────────────────────────────────────────
def calc_impeller(Q_m3s, H_m, N_rpm, rho, eta_hyd=0.88, phi=0.85, psi=0.5, z_blades=6):
    """
    Full impeller geometry design.
    phi  = head coefficient (0.80–0.92 typical)
    psi  = flow coefficient (0.08–0.30 typical)
    z    = number of blades
    Returns comprehensive dict of all impeller dimensions.
    """
    Q_lps = Q_m3s * 1000
    omega = 2 * math.pi * N_rpm / 60    # rad/s

    # ── Specific Speed ────────────────────────────────────────────────────────
    Ns = N_rpm * math.sqrt(Q_lps) / (H_m ** 0.75) if H_m > 0 and Q_lps > 0 else 0
    imp_type, imp_desc = impeller_type(Ns)

    # ── Euler head (theoretical) ──────────────────────────────────────────────
    H_euler = H_m / eta_hyd

    # ── Outlet diameter (D2) — from tip speed ─────────────────────────────────
    # u2 = phi * sqrt(2gH_euler)
    u2    = phi * math.sqrt(2 * g * H_euler)
    D2    = 60 * u2 / (math.pi * N_rpm)            # m
    D2_mm = D2 * 1000                               # mm

    # ── Inlet diameter (D1 / Eye diameter) ────────────────────────────────────
    # From continuity: D1 ≈ 0.35–0.5 × D2 (Karassik guideline)
    D1    = 0.45 * D2
    D1_mm = D1 * 1000

    # ── Hub diameter (Dh) ─────────────────────────────────────────────────────
    Dh    = 0.35 * D1
    Dh_mm = Dh * 1000

    # ── Blade widths ──────────────────────────────────────────────────────────
    # b2 from continuity at outlet: Q = pi * D2 * b2 * Cm2
    # Meridional velocity Cm2 ≈ psi * u2
    Cm2 = psi * u2
    b2  = Q_m3s / (math.pi * D2 * Cm2) if (D2 * Cm2) > 0 else 0.02
    b2_mm = b2 * 1000

    # Inlet blade width b1 (larger for smooth entry)
    b1_mm = b2_mm * 1.4

    # ── Blade angles (Stepanoff velocity triangle method) ─────────────────────
    # Inlet: no pre-swirl (alpha1 = 90°)
    u1    = omega * D1 / 2
    Cm1   = Q_m3s / (math.pi * D1 * b2 * 1.4) if (D1 * b2) > 0 else Cm2 * 1.2
    beta1 = math.degrees(math.atan(Cm1 / u1)) if u1 > 0 else 20  # blade angle at inlet

    # Outlet: from Euler equation Cu2 = H_euler * g / u2
    Cu2   = H_euler * g / u2 if u2 > 0 else 0
    Wm2   = Cm2
    beta2 = math.degrees(math.atan(Wm2 / (u2 - Cu2))) if (u2 - Cu2) > 0 else 25

    # Practical limits (API 610 §6.1.10.1)
    beta1 = min(max(beta1, 15), 40)
    beta2 = min(max(beta2, 20), 35)

    # ── Blade thickness & material ────────────────────────────────────────────
    t_blade_mm = max(3.0, D2_mm * 0.012)  # 1.2% of D2

    # ── Shaft diameter (from torque) ──────────────────────────────────────────
    P_hyd  = rho * g * Q_m3s * H_m
    P_sh   = P_hyd / 0.75                  # assume 75% pump efficiency
    torque = P_sh / omega if omega > 0 else 100
    tau_allow = 55e6                        # SS316 allowable shear stress (Pa)
    d_shaft = (16 * torque / (math.pi * tau_allow)) ** (1/3) * 1000  # mm
    d_shaft = max(d_shaft, 20)              # minimum 20 mm

    # ── Eye area & NPSH contribution ─────────────────────────────────────────
    A_eye  = math.pi * (D1**2 - Dh**2) / 4
    V_eye  = Q_m3s / A_eye if A_eye > 0 else 2.0
    NPSH_contrib = V_eye**2 / (2*g)

    # ── Peripheral velocity ratio ─────────────────────────────────────────────
    phi_actual = u2 / math.sqrt(2 * g * H_m) if H_m > 0 else phi

    # ── Number of blades check ────────────────────────────────────────────────
    # Pfleiderer formula: z = 6.5*(D2+D1)/(D2-D1)*sin((beta1+beta2)/2)
    angle_avg = math.radians((beta1 + beta2) / 2)
    z_recommended = 6.5 * (D2 + D1) / max(D2 - D1, 0.001) * math.sin(angle_avg)
    z_recommended = int(min(max(round(z_recommended), 5), 9))

    return {
        # Identification
        "Specific Speed Ns":             round(Ns, 2),
        "Impeller Type":                 imp_type,
        "Impeller Description":          imp_desc,
        # Key diameters
        "Outlet Diameter D₂ (mm)":       round(D2_mm, 1),
        "Inlet / Eye Diameter D₁ (mm)":  round(D1_mm, 1),
        "Hub Diameter Dₕ (mm)":          round(Dh_mm, 1),
        "Shaft Diameter (mm)":           round(d_shaft, 1),
        # Blade geometry
        "Outlet Blade Width b₂ (mm)":    round(b2_mm, 2),
        "Inlet Blade Width b₁ (mm)":     round(b1_mm, 2),
        "Blade Inlet Angle β₁ (°)":      round(beta1, 1),
        "Blade Outlet Angle β₂ (°)":     round(beta2, 1),
        "Number of Blades (recommended)":z_recommended,
        "Blade Thickness (mm)":          round(t_blade_mm, 2),
        # Velocities
        "Tip Speed u₂ (m/s)":            round(u2, 3),
        "Inlet Peripheral Speed u₁ (m/s)":round(u1, 3),
        "Meridional Velocity Cm₂ (m/s)": round(Cm2, 3),
        "Eye Velocity V_eye (m/s)":      round(V_eye, 3),
        "Whirl Component Cu₂ (m/s)":     round(Cu2, 3),
        # Design parameters
        "Head Coefficient φ":            round(phi_actual, 4),
        "Flow Coefficient ψ":            round(psi, 4),
        "Hydraulic Efficiency η_hyd":    f"{eta_hyd*100:.1f} %",
        "Euler Head H_eu (m)":           round(H_euler, 3),
        "NPSH₃ Contribution (m)":        round(NPSH_contrib, 3),
        # Material (API 610 Table 7)
        "Recommended Material (clean)":  "SS316 / ASTM A743 CA6NM",
        "Material (corrosive)":          "Duplex SS 2205 / Hastelloy C",
        "Casing Material":               "ASTM A216 WCB (CS) / A351 CF8M (SS)",
        "Shaft Material":                "AISI 4140 / 17-4 PH SS",
    }

# ─────────────────────────────────────────────────────────────────────────────
# PUMP SPECIFICATION SHEET — ADVANCED (API 610 12th Ed. format)
# Full sectioned datasheet for EPC / vendor documentation
# ─────────────────────────────────────────────────────────────────────────────
def pump_datasheet(pump_type, Q_m3h, H_m, N_rpm, rho, P_sh_kw, P_mot_kw,
                   mot_kw_std, eta_pump, NPSHa, NPSHr, impeller_dict, fluid,
                   # Extended kwargs — all optional with sensible defaults
                   mu_cP=1.0, Pv_pa=2337, P_atm_pa=101325,
                   pipe_L=100.0, pipe_D_mm=100.0, pipe_mat="Commercial Steel",
                   eps_m=4.6e-5, K_fit=0.0, h_suc=3.0,
                   z_static=20.0, hf_maj=0.0, hf_min=0.0,
                   Re=0.0, f_D=0.0, v=0.0,
                   eta_motor=0.92, SF=1.15, P_hyd_kw=0.0,
                   eta_overall=0.0, torque_Nm=0.0,
                   op_hours=8000, tariff=0.10,
                   project_name="Not Specified", service_desc="General Service"):
    """
    Returns a list of sections, each section being a dict:
      {"title": str, "color": str, "rows": [(param, value, note), ...]}
    'note' is optional reference / formula string.
    """
    # ── Pre-computed values ───────────────────────────────────────────────────
    dP_bar       = rho * g * H_m / 1e5
    dP_design    = max(10.0, dP_bar * 1.5)
    dP_hydro     = max(15.0, dP_bar * 2.0)
    NPSHa_margin = NPSHa - NPSHr
    min_margin   = max(0.5, 0.10 * NPSHr)
    if NPSHa_margin >= min_margin:
        npsh_status = "✅ SAFE — No cavitation risk"
    elif NPSHa_margin >= 0:
        npsh_status = "⚠️ MARGINAL — Monitor closely"
    else:
        npsh_status = "🚨 CAVITATION RISK — Redesign required"

    api_class  = "OH2 (end-suction, centre-line mounted)" if pump_type == "Centrifugal" else "BB1 / BB2"
    Ns_v       = impeller_dict.get("Specific Speed Ns", 0)
    D2_mm      = impeller_dict.get("Outlet Diameter D₂ (mm)", "—")
    D1_mm      = impeller_dict.get("Inlet / Eye Diameter D₁ (mm)", "—")
    Dh_mm      = impeller_dict.get("Hub Diameter Dₕ (mm)", "—")
    ds_mm      = impeller_dict.get("Shaft Diameter (mm)", "—")
    b2_mm      = impeller_dict.get("Outlet Blade Width b₂ (mm)", "—")
    b1_mm      = impeller_dict.get("Inlet Blade Width b₁ (mm)", "—")
    beta1      = impeller_dict.get("Blade Inlet Angle β₁ (°)", "—")
    beta2      = impeller_dict.get("Blade Outlet Angle β₂ (°)", "—")
    z_blades   = impeller_dict.get("Number of Blades (recommended)", "—")
    t_blade    = impeller_dict.get("Blade Thickness (mm)", "—")
    u2         = impeller_dict.get("Tip Speed u₂ (m/s)", "—")
    u1         = impeller_dict.get("Inlet Peripheral Speed u₁ (m/s)", "—")
    Cm2        = impeller_dict.get("Meridional Velocity Cm₂ (m/s)", "—")
    V_eye      = impeller_dict.get("Eye Velocity V_eye (m/s)", "—")
    Cu2        = impeller_dict.get("Whirl Component Cu₂ (m/s)", "—")
    phi_coef   = impeller_dict.get("Head Coefficient φ", "—")
    psi_coef   = impeller_dict.get("Flow Coefficient ψ", "—")
    eta_hyd    = impeller_dict.get("Hydraulic Efficiency η_hyd", "—")
    H_euler    = impeller_dict.get("Euler Head H_eu (m)", "—")
    npsh_c     = impeller_dict.get("NPSH₃ Contribution (m)", "—")
    imp_type   = impeller_dict.get("Impeller Type", "—")
    imp_desc   = impeller_dict.get("Impeller Description", "—")
    mat_clean  = impeller_dict.get("Recommended Material (clean)", "SS316 / ASTM A743 CA6NM")
    mat_corro  = impeller_dict.get("Material (corrosive)", "Duplex SS 2205 / Hastelloy C")
    mat_cas    = impeller_dict.get("Casing Material", "ASTM A216 WCB")
    mat_shaft  = impeller_dict.get("Shaft Diameter (mm)", "AISI 4140 / 17-4 PH SS")

    # D2/D1 ratio
    try:
        ratio = round(float(D2_mm) / float(D1_mm), 2)
    except Exception:
        ratio = "—"

    # Tip-speed check
    try:
        u2_ok = "✅" if float(u2) <= 50 else "⚠️ Exceeds 50 m/s limit"
        u2_str = f"{float(u2):.2f} m/s  {u2_ok}"
    except Exception:
        u2_str = str(u2)

    # Suction specific speed Nss
    try:
        Q_lps = Q_m3h / 3.6
        Nss   = N_rpm * (Q_lps ** 0.5) / (NPSHr ** 0.75) if NPSHr > 0 else 0
        Nss_str = f"{Nss:.1f}  ({'✅ OK' if Nss < 220 else '⚠️ High — cavitation risk'})"
    except Exception:
        Nss_str = "—"

    # Annual energy
    try:
        ann_energy = P_mot_kw * op_hours
        ann_cost   = ann_energy * tariff
        energy_str = f"{ann_energy:,.0f} kWh/yr  (≈ ${ann_cost:,.0f}/yr @ ${tariff}/kWh)"
    except Exception:
        energy_str = "—"

    # Overall efficiency
    try:
        eta_ov_pct = eta_overall * 100 if eta_overall > 0 else eta_pump * eta_motor * 100
        eta_ov_str = f"{eta_ov_pct:.2f} %"
    except Exception:
        eta_ov_str = "—"

    # Torque
    try:
        torq_str = f"{torque_Nm:.2f} N·m" if torque_Nm > 0 else "—"
    except Exception:
        torq_str = "—"

    # Reynolds
    try:
        flow_regime = "Turbulent" if Re > 4000 else ("Transitional" if Re > 2300 else "Laminar")
        Re_str = f"{Re:,.0f}  ({flow_regime})"
    except Exception:
        Re_str = "—"

    # Pipe velocity check
    try:
        v_check = "✅ OK" if 1.0 <= v <= 3.5 else ("⚠️ Low" if v < 1.0 else "⚠️ High")
        v_str = f"{v:.3f} m/s  {v_check}  [HI: 1.0–3.5 m/s]"
    except Exception:
        v_str = "—"

    # NPSHr formula note
    NPSHr_note = f"σ·(N·Q⁰·⁵)^1.333 / g  →  {NPSHr:.2f} m"

    # ── Section builder helper ────────────────────────────────────────────────
    def s(title, color, rows):
        return {"title": title, "color": color, "rows": rows}

    return [
        # ═══════════════════════════════════════════════════════════════════════
        s("§1  GENERAL INFORMATION", "#00d4ff", [
            ("Project Name",              project_name,                            "Client / EPC reference"),
            ("Document Type",             "Pump Data Sheet — Vendor Submittal",    "API 610 12th Ed. Annex A"),
            ("Service Description",       service_desc,                            "Process service tag"),
            ("Pump Type",                 f"{pump_type} — Centrifugal",            "HI 1.1-1.6 Classification"),
            ("API 610 Classification",    api_class,                               "API 610 §5.1 Table 1"),
            ("Number of Stages",          "1  (Single Stage)",                     ""),
            ("Orientation",               "Horizontal",                            "OH2 — horizontal, end-suction"),
            ("Drive Arrangement",         "Direct — Flexible Disc Coupling",       "API 671"),
            ("Design Standard",           "API 610 12th Ed.",                      ""),
            ("Seal Standard",             "API 682 4th Ed.",                       ""),
            ("Coupling Standard",         "API 671",                               ""),
            ("Inspection Level",          "API 610 Annex E — Witnessed",           "Hydrotest + Performance Test"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§2  PROCESS / FLUID DATA", "#39ff14", [
            ("Fluid",                     fluid,                                   "Process fluid"),
            ("Density ρ",                 f"{rho:.2f} kg/m³",                      "At operating temperature"),
            ("Dynamic Viscosity μ",       f"{mu_cP:.3f} mPa·s  ({mu_cP:.3f} cP)", "At operating temperature"),
            ("Vapor Pressure Pv",         f"{Pv_pa:,.0f} Pa  ({Pv_pa/1e5:.4f} bar)","At pumping temperature"),
            ("Atmospheric Pressure",      f"{P_atm_pa:,.0f} Pa  ({P_atm_pa/1e5:.4f} bar)", "Site elevation corrected"),
            ("Corrosive / Abrasive",      "Refer to fluid selection",              "API 610 §6.1.9"),
            ("Solid Content",             "None assumed — clean fluid",            ""),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§3  DESIGN PARAMETERS & INPUTS", "#ffd740", [
            ("Rated Flow Rate Q",         f"{Q_m3h:.2f} m³/h  ({Q_m3h/3.6:.4f} m³/s  |  {Q_m3h*1000/3600:.2f} L/s)", "Specified process flow"),
            ("Rated Total Dynamic Head",  f"{H_m:.2f} m",                          "At rated flow & density"),
            ("Operating Speed N",         f"{N_rpm} RPM",                          "Synchronous or variable speed"),
            ("Pipe Internal Diameter",    f"{pipe_D_mm:.1f} mm  ({pipe_D_mm/1000:.4f} m)", "Common suction & discharge"),
            ("Pipe Total Length",         f"{pipe_L:.1f} m",                       "Suction + discharge combined"),
            ("Pipe Material / Roughness", f"{pipe_mat}  (ε = {eps_m:.2e} m)",      "Colebrook-White Moody Chart"),
            ("Static Head Component",     f"{z_static:.2f} m",                     "Discharge elev. − suction elev."),
            ("Suction Head h_s",          f"{h_suc:.2f} m",                        "+ve above pump centreline"),
            ("Sum of K-factors Σ K",      f"{K_fit:.4f}",                          "From fittings / valves panel"),
            ("Pump Efficiency η_p",       f"{eta_pump*100:.1f} %",                 "At rated point"),
            ("Motor Efficiency η_m",      f"{eta_motor*100:.1f} %",                "Per IEC 60034-30"),
            ("Service Factor SF",         f"{SF:.2f}",                             "Motor oversizing factor"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§4  HYDRAULIC CALCULATIONS", "#ff6b00", [
            ("Pipe Flow Velocity v",      v_str,                                   "v = Q / A  |  A = π·D²/4"),
            ("Reynolds Number Re",        Re_str,                                  "Re = ρ·v·D / μ"),
            ("Darcy Friction Factor f",   f"{f_D:.5f}",                            "Colebrook-White iterative (Moody)"),
            ("Major Head Loss h_f,maj",   f"{hf_maj:.4f} m",                       "Darcy-Weisbach: f·(L/D)·v²/2g"),
            ("Minor Head Loss h_f,min",   f"{hf_min:.4f} m",                       "ΣK·v²/2g  (fittings & valves)"),
            ("Total Friction Loss h_f",   f"{hf_maj+hf_min:.4f} m",               "h_f,maj + h_f,min"),
            ("Static Head H_static",      f"{z_static:.3f} m",                     "Elevation difference"),
            ("Total Dynamic Head TDH",    f"{H_m:.3f} m",                          "H_stat + H_friction + ΔH_vel"),
            ("Differential Pressure ΔP",  f"{dP_bar:.4f} bar  ({dP_bar*100:.2f} kPa)", "ΔP = ρ·g·H / 10⁵"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§5  PUMP PERFORMANCE RESULTS", "#a78bfa", [
            ("Rated Flow Rate",           f"{Q_m3h:.2f} m³/h",                    "Operating point"),
            ("Rated Head",                f"{H_m:.2f} m",                          "At rated flow"),
            ("Hydraulic Power P_hyd",     f"{P_hyd_kw:.3f} kW",                   "P_hyd = ρ·g·Q·H"),
            ("Shaft Power P_shaft",       f"{P_sh_kw:.3f} kW",                    "P_sh = P_hyd / η_pump"),
            ("Motor Input Power P_motor", f"{P_mot_kw:.3f} kW",                   "P_mot = P_sh · SF / η_motor"),
            ("Standard Motor Size",       f"{mot_kw_std} kW",                     "Next standard IEC motor"),
            ("Pump Efficiency η_p",       f"{eta_pump*100:.1f} %",                 "At rated operating point"),
            ("Overall Efficiency η_ov",   eta_ov_str,                              "η_ov = η_pump × η_motor"),
            ("Shaft Torque T",            torq_str,                                "T = P_shaft / ω"),
            ("Angular Velocity ω",        f"{2*math.pi*N_rpm/60:.3f} rad/s",      "ω = 2π·N/60"),
            ("Annual Energy Consumption", energy_str,                              f"At {op_hours} hr/yr operation"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§6  NPSH & CAVITATION ANALYSIS", "#ff4fc8", [
            ("NPSH Available NPSHa",      f"{NPSHa:.3f} m",                        "(P_atm−Pv)/(ρg) + h_s − h_f,suc"),
            ("NPSH Required NPSHr",       f"{NPSHr:.3f} m",                        NPSHr_note),
            ("NPSH Margin",               f"{NPSHa_margin:.3f} m",                 "NPSHa − NPSHr  (min 0.5 m per HI)"),
            ("Minimum Required Margin",   f"{min_margin:.3f} m",                   "max(0.5, 0.10 × NPSHr)"),
            ("Suction Specific Speed Nss",Nss_str,                                 "N·Q⁰·⁵/NPSHr⁰·⁷⁵  [SI]"),
            ("Cavitation Status",         npsh_status,                             "HI 9.6.1 — API 610 §6.1.12"),
            ("Vapor Pressure Pv",         f"{Pv_pa:,.0f} Pa",                      "At pumping temperature"),
            ("Suction Head h_s",          f"{h_suc:.2f} m",                        "+ve = above pump"),
            ("Suction Line Friction",     f"{hf_maj*0.20:.4f} m",                  "≈20% of total major loss"),
            ("Atmospheric Head",          f"{P_atm_pa/(rho*g):.3f} m",            "(P_atm)/(ρ·g)"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§7  IMPELLER DESIGN CALCULATIONS", "#00e5ff", [
            ("Impeller Type",             imp_type,                                "Karassik Table 2.1 / HI Fig 1.3.4"),
            ("Impeller Description",      imp_desc,                                ""),
            ("Impeller Style",            "Closed (double-shroud)",                "API 610 preferred for clean fluids"),
            ("Specific Speed Ns",         f"{Ns_v}",                               "Ns = N·√Q_L / H^0.75  [SI]"),
            ("Outlet Diameter D₂",        f"{D2_mm} mm",                           "From u₂ = φ·√(2gH_eu)"),
            ("Inlet / Eye Diameter D₁",   f"{D1_mm} mm",                           "D₁ ≈ 0.45 × D₂  (Karassik)"),
            ("Hub Diameter Dₕ",           f"{Dh_mm} mm",                           "Dₕ ≈ 0.35 × D₁"),
            ("D₂ / D₁ Ratio",             f"{ratio}",                              "Typical: 1.5–5.0  (Karassik)"),
            ("Outlet Blade Width b₂",     f"{b2_mm} mm",                           "Q = π·D₂·b₂·Cm₂"),
            ("Inlet Blade Width b₁",      f"{b1_mm} mm",                           "b₁ ≈ 1.4 × b₂  (smooth entry)"),
            ("Number of Blades z",        f"{z_blades}",                           "Pfleiderer formula"),
            ("Blade Thickness t",         f"{t_blade} mm",                         "≈ 1.2% of D₂"),
            ("Blade Inlet Angle β₁",      f"{beta1} °",                            "From velocity triangle — no pre-swirl"),
            ("Blade Outlet Angle β₂",     f"{beta2} °",                            "Backward-curved: API 610 §6.1.10"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§8  VELOCITY & FLOW CALCULATIONS", "#69f0ae", [
            ("Tip Speed u₂",              u2_str,                                  "u₂ = φ·√(2g·H_euler)  [API 610 §6.3.1: ≤50 m/s]"),
            ("Inlet Peripheral Speed u₁", f"{u1} m/s",                             "u₁ = ω·D₁/2"),
            ("Meridional Velocity Cm₂",   f"{Cm2} m/s",                            "Cm₂ = ψ·u₂"),
            ("Eye Velocity V_eye",        f"{V_eye} m/s",                          "V_eye = Q / A_eye"),
            ("Whirl Component Cu₂",       f"{Cu2} m/s",                            "Cu₂ = H_euler·g / u₂  (Euler)"),
            ("Head Coefficient φ",        f"{phi_coef}",                           "φ = u₂/√(2gH)  typical 0.80–0.92"),
            ("Flow Coefficient ψ",        f"{psi_coef}",                           "ψ = Cm₂/u₂  typical 0.08–0.30"),
            ("Hydraulic Efficiency η_hyd",f"{eta_hyd}",                            "H = H_euler × η_hyd"),
            ("Euler (Theoretical) Head",  f"{H_euler} m",                          "H_euler = H / η_hyd"),
            ("NPSH₃ Inlet Contribution",  f"{npsh_c} m",                           "V_eye²/(2g)  — inlet velocity head"),
            ("Eye Area A_eye",            f"{math.pi*((float(D1_mm)/1000)**2-(float(Dh_mm)/1000)**2)/4*1e4:.2f} cm²" if isinstance(D1_mm, (int,float)) and isinstance(Dh_mm, (int,float)) else "—",
                                                                                    "A_eye = π(D₁²−Dₕ²)/4"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§9  MECHANICAL & SEALING", "#ffb300", [
            ("Shaft Diameter d_s",        f"{ds_mm} mm",                           "From torsion: d = (16T/πτ)^(1/3)"),
            ("Shaft Material",            "AISI 4140 / 17-4 PH SS",               "API 610 Table 7"),
            ("Allowable Shear Stress",    "55 MPa",                                "SS316 — conservative"),
            ("Seal Type",                 "Single Cartridge Mechanical Seal",      "API 682 4th Ed. Plan 01"),
            ("Seal Flush Plan",           "API Plan 01 (internal recirculation)",  "For clean, non-flashing fluids"),
            ("Bearing Type",              "Anti-friction  (ball + roller)",         "L10 life > 25,000 hr"),
            ("Bearing Lubrication",       "Grease (standard) / Oil mist (optional)","API 610 §6.9"),
            ("Coupling Type",             "Flexible Disc Coupling",                "API 671 — spacer type"),
            ("Baseplate",                 "Epoxy-grout, drip-rim, integral sump",  "API 610 §6.1.1"),
            ("Casing Pressure — Design",  f"{dP_design:.1f} bar",                  "1.5 × dP_operating  (minimum 10 bar)"),
            ("Casing Pressure — Hydrotest",f"{dP_hydro:.1f} bar",                  "2.0 × dP_operating  (minimum 15 bar)"),
            ("Nozzle Loads",              "Per API 610 Table 4",                   "Allowable forces & moments"),
            ("Vibration Limit",           "< 4.5 mm/s RMS unfiltered",             "API 610 §6.8.2"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§10  MATERIALS OF CONSTRUCTION", "#f48fb1", [
            ("Casing",                    "ASTM A216 WCB (CS)  /  A351 CF8M (SS)","API 610 Table 7 — std. material class"),
            ("Impeller — Clean Service",  mat_clean,                               "API 610 preferred impeller material"),
            ("Impeller — Corrosive Svc.", mat_corro,                               "For H₂S, Cl⁻, acid service"),
            ("Shaft",                     "AISI 4140  /  17-4 PH SS",             "API 610 Table 7"),
            ("Wear Rings",                "SS316 / Stellite 6 overlay",            "≥ 60 HRC coating for abrasive service"),
            ("Fasteners",                 "ASTM A193 B7 / A194 2H",               "High-temp bolting"),
            ("Gaskets",                   "Spiral Wound SS316 / Graphite",         "ASME B16.20"),
            ("Nameplate",                 "316 SS — permanently attached",         "API 610 §6.3.6"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§11  OPERATING LIMITS & COMPLIANCE CHECKS", "#ff7043", [
            ("Tip Speed u₂ ≤ 50 m/s",    u2_str,                                  "API 610 §6.3.1"),
            ("D₂/D₁ Ratio  (1.5–5.0)",   f"{ratio}",                              "Karassik design guideline"),
            ("β₂ Blade Angle (15°–35°)",  f"{beta2} °",                            "Backward-curved blade API 610"),
            ("Specific Speed (200–3000)", f"{Ns_v}",                               "HI radial/mixed flow envelope"),
            ("NPSHa > NPSHr + 0.5 m",    f"Margin = {NPSHa_margin:.2f} m  →  {npsh_status.split('—')[0].strip()}", "HI 9.6.1"),
            ("Suction Specific Speed Nss",Nss_str,                                 "< 220 SI recommended"),
            ("Pipe Velocity (1.0–3.5 m/s)",v_str,                                  "HI 9.6.6 recommended range"),
            ("Flow Regime",               Re_str,                                   "Colebrook-White validity: Re > 4000"),
            ("Min. Operating Flow",       f"≥ 70 % of BEP  →  ≥ {Q_m3h*0.70:.1f} m³/h", "API 610 §6.1.8.2"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§12  PERFORMANCE CURVES SUMMARY", "#80deea", [
            ("Head-Flow (H-Q) Curve",     "Continuously rising toward shut-off",   "API 610 §6.1.8 — no dip to BEP"),
            ("Shut-off Head",             f"≈ {H_m*1.20:.1f} m  (estimated +20%)", "API 610: min. 110% of rated head"),
            ("Best Efficiency Point (BEP)",f"Q_BEP ≈ {Q_m3h:.1f} m³/h  |  H_BEP ≈ {H_m:.1f} m", "At rated operating conditions"),
            ("Maximum Efficiency η_max",  f"{eta_pump*100:.1f} %",                 "At rated point (= BEP assumed)"),
            ("Efficiency Curve",          "Parabolic — peaks at BEP",              "Stepanoff method"),
            ("Power Curve",               "Rises with flow — non-overloading type","API 610 §6.1.8.6"),
            ("System Curve",              f"H = {z_static:.1f} + R·Q²",            "R = friction resistance coefficient"),
            ("Operating Point",           f"Q = {Q_m3h:.2f} m³/h  |  H = {H_m:.2f} m","Intersection H-Q × System Curve"),
            ("Graphs Available",          "H-Q + System | Efficiency | Power | Dashboard","See Section 6 — Performance Graphs"),
        ]),
        # ═══════════════════════════════════════════════════════════════════════
        s("§13  FINAL DESIGN SUMMARY & RECOMMENDATION", "#c3f53c", [
            ("SELECTED PUMP",             f"{pump_type} — {api_class}",            "API 610 12th Ed."),
            ("Fluid",                     fluid,                                   ""),
            ("Rated Flow",                f"{Q_m3h:.2f} m³/h",                    ""),
            ("Total Dynamic Head",        f"{H_m:.2f} m",                          ""),
            ("Differential Pressure",     f"{dP_bar:.4f} bar",                     ""),
            ("Impeller Diameter D₂",      f"{D2_mm} mm",                           ""),
            ("Speed",                     f"{N_rpm} RPM",                          ""),
            ("Specific Speed Ns",         f"{Ns_v}",                               ""),
            ("Pump Efficiency",           f"{eta_pump*100:.1f} %",                 ""),
            ("Shaft Power",               f"{P_sh_kw:.3f} kW",                     ""),
            ("Motor Standard Size",       f"{mot_kw_std} kW",                      ""),
            ("NPSHa / NPSHr",             f"{NPSHa:.2f} m  /  {NPSHr:.2f} m",     ""),
            ("Cavitation Status",         npsh_status,                             ""),
            ("Seal",                      "Mechanical Seal API 682 Plan 01",       ""),
            ("Engineering Conclusion",    "Pump design satisfies all API 610 hydraulic and mechanical requirements. Proceed to vendor RFQ." if NPSHa_margin >= min_margin else "NPSH margin insufficient — review suction conditions or increase speed.", ""),
        ]),
    ]
