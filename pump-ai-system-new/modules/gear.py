# =============================================================================
# modules/gear.py
# Gear Pump Model — ANSI/HI 3.1-3.5 / API 676
# =============================================================================
import numpy as np
import math
from config.settings import g

def design(Q_m3s, H_m, rho, mu_pas, displacement_cc_rev, vol_eff_pct, N_rpm):
    mu_cP   = mu_pas * 1000
    eta_v   = vol_eff_pct / 100
    disp_m3 = displacement_cc_rev * 1e-6

    Q_th    = disp_m3 * N_rpm / 60
    Q_act   = Q_th * eta_v

    # Viscosity correction factor (Merritt, Hydraulic Control Systems, 1967)
    visc_f  = min(1.0, max(0.55, 1.0 - 0.00035 * max(0, mu_cP - 50)**0.55))
    Q_visc  = Q_act * visc_f

    dP      = rho * g * H_m
    torque  = dP * disp_m3 / (2 * math.pi * max(eta_v, 0.01))
    slip    = Q_th - Q_act

    return {
        "Theoretical Flow (m³/s)":         Q_th,
        "Actual Flow (m³/s)":              Q_act,
        "Viscosity-Corrected Flow (m³/s)": Q_visc,
        "Internal Slip (m³/s)":            slip,
        "Volumetric Efficiency (%)":       eta_v * 100,
        "Viscosity Correction Factor":     visc_f,
        "Discharge Pressure (bar)":        dP / 1e5,
        "Required Torque (N·m)":           torque,
    }

def flow_vs_viscosity(Q_design, mu_range_cP=None, vol_eff=0.90, visc_ref_cP=100):
    """Flow vs viscosity curve for gear pump."""
    if mu_range_cP is None:
        mu_range_cP = np.logspace(0, 5, 80)   # 1 to 100,000 cP
    visc_f = np.clip(1.0 - 0.00035 * np.maximum(0, mu_range_cP - 50)**0.55, 0.55, 1.0)
    Q_arr  = Q_design * vol_eff * visc_f
    return mu_range_cP, Q_arr
