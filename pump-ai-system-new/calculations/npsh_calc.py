# =============================================================================
# calculations/npsh_calc.py
# NPSH Available vs Required + Cavitation Risk
# Reference: HI Std 1.1-1.6, Karassik Pump Handbook Ch.8
# =============================================================================
import math
from config.settings import g

def npsh_available(P_atm_pa, Pv_pa, rho, h_suction_m, hf_suction_m):
    """
    NPSHa = (P_atm - Pv)/(ρg) + h_s - h_f,suc
    P_atm: absolute atmospheric pressure (Pa)
    Pv:    fluid vapor pressure (Pa)
    h_suction: suction head (positive = above pump, negative = below)
    hf_suction: friction loss in suction line (m)
    """
    return (P_atm_pa - Pv_pa) / (rho * g) + h_suction_m - hf_suction_m

def npsh_required(N_rpm, Q_m3s, sigma_ref=0.003):
    """
    Empirical NPSHr from Karassik (dimensionless suction specific speed method).
    sigma_ref ≈ 0.003 for most centrifugal pumps.
    """
    NPSHr = sigma_ref * (N_rpm * Q_m3s**0.5)**1.333 / g
    return max(0.3, NPSHr)

def cavitation_check(NPSHa, NPSHr):
    """
    Returns: status string, margin (m), risk level
    HI minimum safety margin = 0.5 m (or 10% of NPSHr, whichever is greater)
    """
    margin = NPSHa - NPSHr
    min_margin = max(0.5, 0.10 * NPSHr)
    if margin >= min_margin:
        return "✅ Safe", margin, "low"
    elif margin >= 0:
        return "⚠️ Marginal", margin, "medium"
    else:
        return "🚨 CAVITATION RISK", margin, "high"
