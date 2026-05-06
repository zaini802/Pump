# =============================================================================
# modules/plunger.py
# Plunger Pump Model — API 674 / HI 6.1-6.5
# =============================================================================
import numpy as np
import math
from config.settings import g

def design(Q_m3s, H_m, rho, plunger_dia_mm, stroke_mm, N_rpm, n_plungers, slip_pct):
    d    = plunger_dia_mm / 1000
    L    = stroke_mm / 1000
    slip = slip_pct / 100
    A    = math.pi * d**2 / 4

    Q_th_pl  = A * L
    Q_th     = Q_th_pl * n_plungers * N_rpm / 60
    Q_act    = Q_th * (1 - slip)
    dP       = rho * g * H_m
    F_plunger = dP * A
    rod_load = F_plunger / 1000   # kN

    # Peak pressure during stroke
    P_peak = dP * 1.15  # 15% inertia over-pressure

    MATERIAL_P_LIMIT = {
        "Duplex SS": 700e5, "Hastelloy C": 500e5,
        "AISI 316L": 350e5, "Carbon Steel": 250e5
    }

    return {
        "Plunger Area (m²)":          A,
        "Theoretical Flow/Plunger (L/s)": Q_th_pl * 1000,
        "Actual Flow (m³/s)":         Q_act,
        "Flow Error vs Target (%)":   abs(Q_act - Q_m3s) / max(Q_m3s, 1e-9) * 100,
        "Discharge Pressure (bar)":   dP / 1e5,
        "Peak Pressure (bar)":        P_peak / 1e5,
        "Plunger Force (N)":          F_plunger,
        "Rod Load (kN)":              rod_load,
        "Pulsation":                  "Triplex: ±2%  Duplex: ±6%  Simplex: ±25%",
        "Dampener":                   "MANDATORY for simplex/duplex",
    }

def flow_vs_time(Q_act, N_rpm, n_pl, t_max_s=0.5):
    t    = np.linspace(0, t_max_s, 500)
    freq = N_rpm / 60
    flow = np.zeros_like(t)
    for c in range(n_pl):
        phase = 2 * math.pi * c / n_pl
        flow += np.clip(Q_act * np.sin(2 * math.pi * freq * t + phase), 0, None)
    flow = flow / n_pl + Q_act * 0.03
    return t, flow
