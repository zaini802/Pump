# =============================================================================
# modules/reciprocating.py
# Reciprocating (Piston) Pump Model — API 674 / HI 6.1-6.5
# =============================================================================
import numpy as np
import math
from config.settings import g

def design(Q_m3s, H_m, rho, piston_dia_mm, stroke_mm, N_rpm, n_cyl, slip_pct):
    d    = piston_dia_mm / 1000
    L    = stroke_mm / 1000
    slip = slip_pct / 100
    A    = math.pi * d**2 / 4

    Q_th_cyl = A * L                            # m³/stroke/cyl
    Q_th     = Q_th_cyl * n_cyl * N_rpm / 60   # theoretical total m³/s
    Q_act    = Q_th * (1 - slip)

    dP       = rho * g * H_m
    F_piston = dP * A                           # force per piston (N)
    P_hyd    = rho * g * Q_m3s * H_m

    # Pulsation: 1 = 100%, 2 = 40%, 3 = 7%, 4 = 5%, 5 = 2%
    PULSE = {1: 100, 2: 40, 3: 7, 4: 5, 5: 2}
    pulsation = PULSE.get(n_cyl, 7)

    return {
        "Piston Area (m²)":           A,
        "Theoretical Flow/Cyl (L/s)": Q_th_cyl * 1000,
        "Theoretical Flow (m³/s)":    Q_th,
        "Actual Flow (m³/s)":         Q_act,
        "Flow Error vs Target (%)":   abs(Q_act - Q_m3s) / max(Q_m3s, 1e-9) * 100,
        "Discharge Pressure (bar)":   dP / 1e5,
        "Piston Force (N)":           F_piston,
        "Pulsation (% of mean)":      pulsation,
        "Dampener Required":          "MANDATORY" if n_cyl <= 2 else "RECOMMENDED",
    }

def flow_vs_time(Q_act, N_rpm, n_cyl, t_max_s=0.5):
    """Pulsating flow waveform for reciprocating pump."""
    t    = np.linspace(0, t_max_s, 500)
    freq = N_rpm / 60
    flow = np.zeros_like(t)
    for c in range(n_cyl):
        phase = 2 * math.pi * c / n_cyl
        flow += np.clip(Q_act * np.sin(2 * math.pi * freq * t + phase), 0, None)
    flow = flow / n_cyl + Q_act * 0.05
    return t, flow

def pressure_pulsation(H_m, N_rpm, n_cyl, t_max_s=0.5):
    t    = np.linspace(0, t_max_s, 500)
    freq = N_rpm / 60
    amp  = H_m * {1: 0.5, 2: 0.25, 3: 0.08, 4: 0.05}.get(n_cyl, 0.08)
    P    = H_m + amp * np.sin(2 * math.pi * freq * n_cyl * t)
    return t, P
