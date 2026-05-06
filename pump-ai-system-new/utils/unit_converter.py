# =============================================================================
# utils/unit_converter.py
# =============================================================================
FLOW_TO_M3S = {
    "m³/h":   1 / 3600,
    "L/s":    1e-3,
    "L/min":  1 / 60_000,
    "m³/s":   1.0,
    "US GPM": 6.30902e-5,
    "bbl/day":1.84e-6,
}
PRESSURE_TO_PA = {
    "Pa":    1.0,
    "kPa":   1e3,
    "bar":   1e5,
    "psi":   6894.76,
    "atm":   101325,
    "m H₂O": 9810.0,
}
def flow_to_m3s(val, unit): return val * FLOW_TO_M3S.get(unit, 1)
def pressure_to_pa(val, unit): return val * PRESSURE_TO_PA.get(unit, 1)
def m3s_to_unit(val, unit): return val / FLOW_TO_M3S.get(unit, 1)
def pa_to_unit(val, unit):  return val / PRESSURE_TO_PA.get(unit, 1)
