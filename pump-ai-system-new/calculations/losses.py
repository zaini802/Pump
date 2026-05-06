# =============================================================================
# calculations/losses.py
# Darcy-Weisbach + Colebrook-White (Moody 1944 / Crane TP-410)
# =============================================================================
import math
from config.settings import g

def pipe_area(D_m):
    return math.pi * D_m**2 / 4

def flow_velocity(Q_m3s, D_m):
    A = pipe_area(D_m)
    return Q_m3s / A if A > 0 else 0

def reynolds_number(rho, v, D_m, mu):
    return rho * v * D_m / mu if mu > 0 else 0

def friction_factor(Re, D_m, eps):
    """Colebrook-White iterative (Moody chart)."""
    if Re < 1:
        return 0.0
    if Re < 2300:
        return 64.0 / Re
    eps_D = eps / D_m
    f = 0.025
    for _ in range(80):
        arg = eps_D / 3.7 + 2.51 / (Re * math.sqrt(f) + 1e-20)
        if arg <= 0:
            break
        f_new = (1 / (-2.0 * math.log10(arg)))**2
        if abs(f_new - f) < 1e-11:
            break
        f = f_new
    return f

def major_loss(f, L, D_m, v):
    """Darcy-Weisbach major (friction) head loss (m)."""
    return f * (L / D_m) * v**2 / (2 * g)

def minor_loss(K_total, v):
    """Minor head loss from fittings & valves (m)."""
    return K_total * v**2 / (2 * g)

def total_friction_loss(f, L, D_m, v, K_total):
    return major_loss(f, L, D_m, v) + minor_loss(K_total, v)

def system_curve(Q_design, H_static, f, L, D_m, K_total, rho, n=60):
    """Generate system curve H = H_static + R·Q² over 0→1.5·Q_design."""
    import numpy as np
    Q_range = np.linspace(0, Q_design * 1.5, n)
    H_sys   = []
    for Q in Q_range:
        v  = flow_velocity(Q, D_m) if Q > 0 else 0
        hf = total_friction_loss(f, L, D_m, v, K_total) if Q > 0 else 0
        H_sys.append(H_static + hf)
    return Q_range, np.array(H_sys)
