# =============================================================================
# modules/centrifugal.py
# Centrifugal Pump Model — HI / API 610 / Karassik
# =============================================================================
import numpy as np
import math
from config.settings import g

# ── Design Calculations ───────────────────────────────────────────────────────
def design(Q_m3s, H_m, rho, mu, N_rpm, phi=0.85, D_imp_user_mm=None):
    """
    Full centrifugal pump design.
    Returns dict of all design parameters.
    """
    Q_lps  = Q_m3s * 1000
    Ns     = N_rpm * math.sqrt(Q_lps) / H_m**0.75 if H_m > 0 and Q_lps > 0 else 0

    # Impeller tip speed from Euler equation
    u2     = math.sqrt(2 * g * H_m) / phi
    D_calc = 60 * u2 / (math.pi * N_rpm) * 1000  # mm
    D_imp  = D_imp_user_mm if D_imp_user_mm else D_calc

    # Viscosity correction (HI Std Fig 1.3.3.3)
    mu_cP  = mu * 1000
    Cv, CH, CE = 1.0, 1.0, 1.0  # default: no correction
    if mu_cP > 10:
        Cv = max(0.6,  1 - 0.00025 * mu_cP**0.5 * Q_m3s**0.1 * H_m**0.1)
        CH = max(0.8,  1 - 0.0003  * mu_cP**0.5)
        CE = max(0.4,  1 - 0.0006  * mu_cP**0.5)

    # Affinity laws at 90% speed
    Q_90 = Q_m3s * 0.9
    H_90 = H_m * 0.81
    P_90_ratio = 0.729

    # Pump class from Ns
    if Ns < 600:
        pump_class = "Radial-flow (Low Ns)"
    elif Ns < 2500:
        pump_class = "Mixed-flow (Medium Ns)"
    else:
        pump_class = "Axial/Propeller (High Ns)"

    return {
        "Specific Speed Ns":          Ns,
        "Pump Class":                 pump_class,
        "Impeller Dia. (mm)":         D_imp,
        "Tip Speed u₂ (m/s)":         u2,
        "Head Coefficient φ":         phi,
        "Visc. Flow Correction Cv":   Cv,
        "Visc. Head Correction CH":   CH,
        "Visc. Eff. Correction CE":   CE,
        "Affinity Q at 90% N (m³/s)": Q_90,
        "Affinity H at 90% N (m)":    H_90,
        "Affinity P ratio at 90% N":  P_90_ratio,
    }

# ── Performance Curves ────────────────────────────────────────────────────────
def performance_curves(Q_design, H_design, eta_design=0.78, n=80):
    """
    Returns Q, H, eta, P arrays for H-Q, efficiency, power curves.
    Parabolic H-Q model (standard for radial-flow centrifugal pumps).
    """
    Q_max = Q_design * 1.65
    Q     = np.linspace(0, Q_max, n)
    H0    = H_design * 1.25          # shutoff head
    a     = H0 / (Q_max**2 + 1e-20)
    H     = np.clip(H0 - a * Q**2, 0, H0)

    # Efficiency: bell-curve peaked at Q_design
    eta_pk = min(eta_design + 0.04, 0.88)
    eta    = eta_pk * (1 - 3.6 * ((Q - Q_design) / (Q_max + 1e-20))**2)
    eta    = np.clip(eta, 0.02, eta_pk)

    # Shaft power P = ρgQH/η  (rho=1000 kg/m³ for normalised curve)
    rho_n = 1000
    P_kw  = np.where(eta > 0.01,
                     rho_n * 9.81 * Q * H / eta / 1000, 0)
    return Q, H, eta, P_kw

def pulsation_analysis():
    """Centrifugal pumps have negligible pulsation — return placeholder."""
    return None
