# =============================================================================
# utils/validators.py
# =============================================================================
def validate_inputs(Q_m3s, H, rho, mu, D_m):
    errors = []
    warnings = []
    if Q_m3s <= 0:
        errors.append("Flow rate must be > 0.")
    if H <= 0:
        errors.append("Total head must be > 0 m.")
    if rho <= 0 or rho > 20000:
        errors.append("Density out of range (0–20,000 kg/m³).")
    if mu <= 0:
        errors.append("Viscosity must be > 0 Pa·s.")
    if D_m <= 0.005:
        errors.append("Pipe diameter too small (< 5 mm).")
    v = Q_m3s / (3.14159 * D_m**2 / 4)
    if v > 5.0:
        warnings.append(f"Pipe velocity {v:.2f} m/s > 5 m/s — consider larger pipe (HI Std §1.3.4).")
    if v < 0.3:
        warnings.append(f"Pipe velocity {v:.2f} m/s < 0.3 m/s — risk of sedimentation.")
    return errors, warnings
