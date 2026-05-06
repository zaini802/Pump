# =============================================================================
# theory/pump_theory.py
# Engineering Theory Knowledge Base (sidebar mini-textbook)
# =============================================================================

THEORY = {
    "What is a Pump?": {
        "icon": "🔵",
        "content": """
A **pump** is a mechanical device that adds energy to a fluid, raising it from a lower energy state to a higher one.
It converts **mechanical energy (shaft work)** into **fluid energy** (pressure + velocity + elevation).

**Basic energy equation (Bernoulli + shaft work):**
> H_pump = (P₂-P₁)/(ρg) + (V₂²-V₁²)/(2g) + (z₂-z₁) + h_f

**Reference:** Perry's Chemical Engineers' Handbook §10.1; McCabe & Smith §7.1
"""
    },
    "Pump Classification": {
        "icon": "🗂️",
        "content": """
**Kinetic (Dynamic) Pumps** — impart velocity, convert to pressure:
- Centrifugal (radial, mixed, axial flow)
- Regenerative turbine
- Special effect (jet, electromagnetic)

**Positive Displacement (PD) Pumps** — trap & displace fluid:
- Reciprocating: piston, plunger, diaphragm
- Rotary: gear, screw, vane, lobe, peristaltic

**Selection Rule of Thumb (Karassik, Table 1.1):**
- High flow + moderate head → Centrifugal
- High pressure + low flow → Reciprocating / Plunger
- High viscosity → Gear / Screw
"""
    },
    "Total Dynamic Head (TDH)": {
        "icon": "📐",
        "content": """
**TDH** = total energy the pump must supply per unit weight of fluid.

```
TDH = H_static + H_pressure + H_velocity + H_friction
```

Where:
- **H_static** = elevation difference (m)
- **H_pressure** = (P_discharge - P_suction) / (ρg) (m)
- **H_velocity** = (v²d - v²s) / 2g ≈ 0 for same pipe diameter
- **H_friction** = major + minor losses (m)

**Reference:** Crane TP-410, Perry's §10.4
"""
    },
    "Pump Power & Efficiency": {
        "icon": "⚡",
        "content": """
**Hydraulic Power:**
> P_hyd = ρ · g · Q · H  [Watts]

**Shaft Power:**
> P_shaft = P_hyd / η_pump

**Motor Input Power:**
> P_motor = P_shaft · SF / η_motor

Typical efficiencies:
| Pump Type | η_pump |
|-----------|--------|
| Large centrifugal | 85-92% |
| Small centrifugal | 50-75% |
| Reciprocating | 75-90% |
| Gear pump | 80-92% |

**Reference:** HI 1.1-1.6, API 610 §6.1
"""
    },
    "NPSH & Cavitation": {
        "icon": "🌊",
        "content": """
**NPSH Available:**
> NPSHa = (P_atm - P_v)/(ρg) + h_suction - h_f,suction

**NPSHr** is given by the pump manufacturer.

**Cavitation** occurs when local pressure drops below vapor pressure:
- Vapor bubbles form → collapse violently → impeller damage
- Symptoms: noise, vibration, erosion, flow loss

**HI Safety Rule:**
> NPSHa ≥ NPSHr + 0.5 m (minimum margin)

**Solutions:**
1. Lower pump (increase suction head)
2. Increase suction pipe diameter
3. Cool the fluid (reduce Pv)
4. Use pump with lower NPSHr (inducer)

**Reference:** HI 1.1-1.6 §9; Karassik Ch.8
"""
    },
    "System Curve": {
        "icon": "📈",
        "content": """
The **system curve** represents the head required by the piping system at each flow rate:

> H_system = H_static + R · Q²

Where R = friction resistance (combines Darcy-Weisbach losses).

**Operating Point** = intersection of pump curve and system curve.

Changes in system:
- Opening valve → curve shifts down → flow ↑
- Adding resistance → curve shifts up → flow ↓
- Speed change (VFD) → pump curve shifts → operating point moves

**Reference:** Perry's §10.5; Karassik Ch.12
"""
    },
    "Best Efficiency Point (BEP)": {
        "icon": "🎯",
        "content": """
**BEP** = point on the pump curve where efficiency is maximum.

Operating away from BEP causes:
- Radial thrust (shaft bending)
- Cavitation risk
- Bearing overload
- Vibration and noise

**Allowable range** (API 610):
> 70% BEP ≤ Q_operating ≤ 110% BEP

**Reference:** API 610 §5.1.2; HI 1.1-1.6 §1.3
"""
    },
    "Affinity Laws": {
        "icon": "🔄",
        "content": """
For centrifugal pumps with speed change:

| Parameter | Formula |
|-----------|---------|
| Flow | Q₂/Q₁ = N₂/N₁ |
| Head | H₂/H₁ = (N₂/N₁)² |
| Power | P₂/P₁ = (N₂/N₁)³ |

For impeller trim (diameter change):

| Parameter | Formula |
|-----------|---------|
| Flow | Q₂/Q₁ = D₂/D₁ |
| Head | H₂/H₁ = (D₂/D₁)² |
| Power | P₂/P₁ = (D₂/D₁)³ |

**VFD Advantage:** Reducing speed by 20% cuts power by 49%!

**Reference:** HI 1.1-1.6 §14; Karassik Ch.13
"""
    },
    "Pipe Friction (Darcy-Weisbach)": {
        "icon": "🔧",
        "content": """
**Darcy-Weisbach equation:**
> h_f = f · (L/D) · v²/(2g)

**Colebrook-White** (friction factor, turbulent flow):
> 1/√f = −2 log₁₀(ε/(3.7D) + 2.51/(Re√f))

Flow regimes:
| Re | Regime | f |
|----|--------|---|
| < 2300 | Laminar | 64/Re |
| 2300–4000 | Transitional | interpolate |
| > 4000 | Turbulent | Colebrook-White |

Recommended velocity:
- Suction pipe: 0.6 – 1.5 m/s
- Discharge pipe: 1.0 – 3.5 m/s

**Reference:** Moody (1944) ASME Trans.; Crane TP-410
"""
    },
    "Industrial Standards": {
        "icon": "📋",
        "content": """
| Standard | Scope |
|----------|-------|
| **API 610** | Centrifugal pumps — petroleum industry |
| **API 674** | Reciprocating (positive displacement) pumps |
| **API 676** | Rotary pumps (gear, screw, vane) |
| **ANSI/HI 1.1-1.6** | Centrifugal pump design & testing |
| **ANSI/HI 6.1-6.5** | Reciprocating pump standards |
| **ANSI/HI 3.1-3.5** | Rotary pump standards |
| **ISO 5199** | Centrifugal pump specifications |
| **ISO 9908** | Technical specifications (Classes I-III) |

**Key Perry's sections:** §10.1 (fundamentals), §10.4 (head), §10.5 (system curve)
"""
    },
}
