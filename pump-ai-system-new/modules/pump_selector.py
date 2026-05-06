# =============================================================================
# modules/pump_selector.py
# Smart Pump Selection Engine
# Reference: Karassik Pump Handbook Table 1.1 + HI Std selection charts
# =============================================================================

def select_pump(Q_m3s, H_m, rho, mu_pas, T_C=25, fluid="Water"):
    """
    Rule-based + scoring pump selection.
    Returns ranked list of (pump_type, score, reasons).
    """
    Q_lpm  = Q_m3s * 60_000
    Q_m3h  = Q_m3s * 3600
    mu_cP  = mu_pas * 1000
    results = {}

    # ── Centrifugal ───────────────────────────────────────────────────────────
    s, r = 100, []
    if Q_m3h > 5:
        s += 40; r.append("High flow suited ✓")
    if H_m < 400:
        s += 25; r.append("Head range OK ✓")
    if mu_cP < 100:
        s += 30; r.append("Low viscosity ✓")
    elif mu_cP < 500:
        s += 10; r.append("Moderate viscosity (derate)")
    else:
        s -= 40; r.append("High viscosity — unfavorable ✗")
    if H_m > 800:
        s -= 20; r.append("Very high head — use multistage")
    results["Centrifugal"] = (s, r)

    # ── Reciprocating ─────────────────────────────────────────────────────────
    s, r = 60, []
    if H_m > 200:
        s += 50; r.append("High pressure duty ✓")
    if Q_m3h < 50:
        s += 25; r.append("Low flow suited ✓")
    if mu_cP > 20:
        s += 15; r.append("Handles viscous fluids ✓")
    if Q_m3h > 300:
        s -= 30; r.append("Too high flow for reciprocating ✗")
    results["Reciprocating"] = (s, r)

    # ── Plunger ───────────────────────────────────────────────────────────────
    s, r = 65, []
    if H_m > 500:
        s += 50; r.append("Very high pressure ✓")
    if Q_m3h < 20:
        s += 25; r.append("Metering / low flow suited ✓")
    if "Acid" in fluid or "Chemical" in fluid:
        s += 20; r.append("Chemical service suited ✓")
    if Q_m3h > 200:
        s -= 30; r.append("Flow exceeds typical plunger range ✗")
    results["Plunger"] = (s, r)

    # ── Gear ──────────────────────────────────────────────────────────────────
    s, r = 50, []
    if mu_cP > 100:
        s += 60; r.append("High viscosity — ideal ✓")
    if mu_cP > 1000:
        s += 20; r.append("Very high viscosity — best choice ✓")
    if Q_m3h < 300:
        s += 15; r.append("Flow range suitable ✓")
    if H_m > 300:
        s -= 20; r.append("High head — unfavorable ✗")
    if rho > 1500:
        s -= 15; r.append("Very dense fluid — check gear loading ✗")
    results["Gear"] = (s, r)

    ranked = sorted(results.items(), key=lambda x: x[1][0], reverse=True)
    return [(pt, sc, reasons) for pt, (sc, reasons) in ranked]


PUMP_INFO = {
    "Centrifugal": {
        "icon":  "🔵",
        "desc":  "Kinetic-energy pump. Rotating impeller converts velocity to pressure. Most widely used industrial pump (>80% of global installations).",
        "apps":  "Water supply · HVAC · Process chemicals · Power plants · Desalination",
        "range": "Flow: 1–100,000 m³/h | Head: 2–1,500 m | Viscosity: <500 cP",
        "std":   "API 610 · ANSI/HI 1.1-1.6 · ISO 5199",
        "pros":  "Simple, reliable, low maintenance, wide range",
        "cons":  "Poor at high viscosity, cavitation risk",
        "color": "#4fc3f7",
    },
    "Reciprocating": {
        "icon":  "🟠",
        "desc":  "Positive-displacement piston pump. Delivers precise constant flow regardless of discharge pressure.",
        "apps":  "High-pressure injection · Hydraulic systems · Metering · Well services",
        "range": "Flow: 0.01–200 m³/h | Head: up to 5,000 m | Viscosity: 1–500 cP",
        "std":   "API 674 · ANSI/HI 6.1-6.5",
        "pros":  "High pressure, precise flow, handles viscous",
        "cons":  "Pulsating flow, high maintenance, noisy",
        "color": "#ffa726",
    },
    "Plunger": {
        "icon":  "🟣",
        "desc":  "High-pressure reciprocating pump with solid plunger instead of piston. Excellent seal life under extreme pressure.",
        "apps":  "Hydrotesting · Chemical injection · Descaling · HPLC · Paint spraying",
        "range": "Flow: 0.001–50 m³/h | Head: up to 10,000+ m | Viscosity: 1–200 cP",
        "std":   "API 674 · ANSI/HI 6.1-6.5",
        "pros":  "Extreme high pressure, good efficiency, precise metering",
        "cons":  "Pulsation, complex valves, low flow only",
        "color": "#ab47bc",
    },
    "Gear": {
        "icon":  "🟢",
        "desc":  "Rotary positive-displacement pump. Meshing gears trap and move fluid. Ideal for thick, lubricating fluids.",
        "apps":  "Lube oil · Fuel transfer · Polymers · Resins · Bitumen · Chocolate",
        "range": "Flow: 0.001–500 m³/h | Head: up to 200 m | Viscosity: 1–100,000 cP",
        "std":   "ANSI/HI 3.1-3.5 · ISO 2943 · API 676",
        "pros":  "Handles very high viscosity, self-priming, smooth flow",
        "cons":  "Not for abrasives, limited pressure range, gear wear",
        "color": "#66bb6a",
    },
}
