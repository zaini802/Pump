# =============================================================================
# calculations/power_calc.py
# Power, efficiency, motor sizing
# Reference: Perry's Ch.10, HI Standards
# =============================================================================
from config.settings import g, next_motor_size

def hydraulic_power(Q_m3s, H_m, rho):
    """P_hyd = ρ·g·Q·H  [W]"""
    return rho * g * Q_m3s * H_m

def shaft_power(P_hyd_W, eta_pump):
    """P_shaft = P_hyd / η_pump  [W]"""
    return P_hyd_W / max(eta_pump, 0.01)

def motor_input_power(P_shaft_W, eta_motor, SF=1.15):
    """P_motor = P_shaft × SF / η_motor  [W]"""
    return P_shaft_W * SF / max(eta_motor, 0.01)

def overall_efficiency(eta_pump, eta_motor):
    return eta_pump * eta_motor

def shaft_torque(P_shaft_W, N_rpm):
    """T = P / ω  [N·m]"""
    omega = 2 * 3.14159 * N_rpm / 60
    return P_shaft_W / max(omega, 0.01)

def specific_speed(N_rpm, Q_m3s, H_m):
    """Ns = N·√Q / H^(3/4)  — dimensionless SI form"""
    Q_lps = Q_m3s * 1000
    if H_m <= 0 or Q_lps <= 0:
        return 0
    return N_rpm * Q_lps**0.5 / H_m**0.75

def motor_size(P_motor_W):
    return next_motor_size(P_motor_W / 1000)

def annual_energy_cost(P_motor_W, hours_per_year=8000, tariff_per_kwh=0.10):
    return P_motor_W / 1000 * hours_per_year * tariff_per_kwh
