# =============================================================================
# calculations/head_calc.py
# Total Dynamic Head (Perry's / Crane TP-410)
# =============================================================================
import math
from config.settings import g

def velocity_head(v):
    return v**2 / (2 * g)

def static_head(z_d, z_s):
    """z_d = discharge elevation, z_s = suction elevation (m)"""
    return z_d - z_s

def pressure_head(P_d, P_s, rho):
    """Convert pressure difference to head (m)"""
    return (P_d - P_s) / (rho * g)

def total_dynamic_head(H_static, H_press, H_vel, H_loss_total):
    return H_static + H_press + H_vel + H_loss_total
