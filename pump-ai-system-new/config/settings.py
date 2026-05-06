# =============================================================================
# config/settings.py
# Themes, constants, engineering limits
# =============================================================================

# ── PHYSICAL CONSTANTS ───────────────────────────────────────────────────────
g = 9.81          # gravitational acceleration (m/s²)
RHO_WATER = 998.2 # water density at 20°C (kg/m³)
MU_WATER  = 1.002e-3  # water dynamic viscosity at 20°C (Pa·s)

# ── STANDARD MOTOR SIZES (kW) ────────────────────────────────────────────────
STANDARD_MOTORS = [
    0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0,
    5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90,
    110, 132, 160, 200, 250, 315, 400, 500
]

# ── PIPE ROUGHNESS (m) ───────────────────────────────────────────────────────
PIPE_ROUGHNESS = {
    "Commercial Steel":  4.6e-5,
    "Galvanized Steel":  1.5e-4,
    "Cast Iron":         2.6e-4,
    "PVC / Plastic":     1.5e-6,
    "Stainless Steel":   1.5e-5,
    "Concrete (smooth)": 3.0e-4,
}

# ── FLUID DATABASE ───────────────────────────────────────────────────────────
FLUID_DATA = {
    "Water":              {"rho": 998.2,  "mu": 1.002e-3, "Pv": 2337},
    "Hot Water (80°C)":   {"rho": 958.4,  "mu": 0.282e-3, "Pv": 47360},
    "Seawater":           {"rho": 1025.0, "mu": 1.08e-3,  "Pv": 2200},
    "Crude Oil":          {"rho": 870.0,  "mu": 50e-3,    "Pv": 500},
    "Diesel":             {"rho": 840.0,  "mu": 3.5e-3,   "Pv": 200},
    "Gasoline":           {"rho": 740.0,  "mu": 0.6e-3,   "Pv": 13000},
    "Sulfuric Acid (98%)":{"rho": 1840.0, "mu": 26e-3,    "Pv": 10},
    "Ethanol":            {"rho": 789.0,  "mu": 1.2e-3,   "Pv": 5867},
    "Glycol (EG)":        {"rho": 1113.0, "mu": 21e-3,    "Pv": 8},
    "Lube Oil":           {"rho": 890.0,  "mu": 100e-3,   "Pv": 50},
    "Polymer Melt":       {"rho": 950.0,  "mu": 5000e-3,  "Pv": 5},
    "Custom":             {"rho": None,   "mu": None,      "Pv": None},
}

PUMP_TYPES = ["Centrifugal"]

# ── 10 PROFESSIONAL THEMES ───────────────────────────────────────────────────
THEMES = {
    # 1
    "Light Engineering": {
        "bg":          "#f4f6fa",
        "sidebar_bg":  "#e8ecf4",
        "card_bg":     "#ffffff",
        "text":        "#1a2340",
        "accent":      "#1565c0",
        "accent2":     "#00897b",
        "accent3":     "#e65100",
        "accent4":     "#6a1b9a",
        "border":      "#1565c033",
        "plot_bg":     "#ffffff",
        "plotly_tmpl": "plotly_white",
        "metric_lbl":  "#546e8a",
        "grad_a":      "#1565c0",
        "grad_b":      "#00897b",
        "btn_bg":      "#1565c0",
        "btn_text":    "#ffffff",
    },
    # 2
    "Dark Industrial": {
        "bg":          "#0a0f1a",
        "sidebar_bg":  "#111827",
        "card_bg":     "#1c2333",
        "text":        "#dce8f5",
        "accent":      "#00d4ff",
        "accent2":     "#39ff14",
        "accent3":     "#ff6b00",
        "accent4":     "#bf5af2",
        "border":      "#00d4ff33",
        "plot_bg":     "#0d1526",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#7da3c0",
        "grad_a":      "#00d4ff",
        "grad_b":      "#39ff14",
        "btn_bg":      "#00d4ff",
        "btn_text":    "#000000",
    },
    # 3
    "Blue Process Plant": {
        "bg":          "#001b44",
        "sidebar_bg":  "#002a6e",
        "card_bg":     "#00347a",
        "text":        "#cce4ff",
        "accent":      "#4fc3f7",
        "accent2":     "#80deea",
        "accent3":     "#ffcc02",
        "accent4":     "#e040fb",
        "border":      "#4fc3f744",
        "plot_bg":     "#001535",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#7ab8e0",
        "grad_a":      "#4fc3f7",
        "grad_b":      "#80deea",
        "btn_bg":      "#4fc3f7",
        "btn_text":    "#001b44",
    },
    # 4
    "Green Chemical Plant": {
        "bg":          "#071a0f",
        "sidebar_bg":  "#0d2b18",
        "card_bg":     "#123320",
        "text":        "#ccf0d8",
        "accent":      "#00e676",
        "accent2":     "#69f0ae",
        "accent3":     "#ffeb3b",
        "accent4":     "#40c4ff",
        "border":      "#00e67633",
        "plot_bg":     "#071a0f",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#60a870",
        "grad_a":      "#00e676",
        "grad_b":      "#69f0ae",
        "btn_bg":      "#00e676",
        "btn_text":    "#071a0f",
    },
    # 5
    "Minimal White": {
        "bg":          "#ffffff",
        "sidebar_bg":  "#f8f9fc",
        "card_bg":     "#f1f3f8",
        "text":        "#212121",
        "accent":      "#3949ab",
        "accent2":     "#00acc1",
        "accent3":     "#e53935",
        "accent4":     "#7b1fa2",
        "border":      "#3949ab22",
        "plot_bg":     "#ffffff",
        "plotly_tmpl": "plotly_white",
        "metric_lbl":  "#666666",
        "grad_a":      "#3949ab",
        "grad_b":      "#00acc1",
        "btn_bg":      "#3949ab",
        "btn_text":    "#ffffff",
    },
    # 6
    "High Contrast Black": {
        "bg":          "#000000",
        "sidebar_bg":  "#0d0d0d",
        "card_bg":     "#1a1a1a",
        "text":        "#ffffff",
        "accent":      "#ffffff",
        "accent2":     "#ffff00",
        "accent3":     "#ff4444",
        "accent4":     "#44ffff",
        "border":      "#ffffff44",
        "plot_bg":     "#050505",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#bbbbbb",
        "grad_a":      "#ffffff",
        "grad_b":      "#ffff00",
        "btn_bg":      "#ffffff",
        "btn_text":    "#000000",
    },
    # 7
    "Ocean Blue": {
        "bg":          "#001f3f",
        "sidebar_bg":  "#003366",
        "card_bg":     "#004080",
        "text":        "#cce8ff",
        "accent":      "#7fdbff",
        "accent2":     "#01ff70",
        "accent3":     "#ff851b",
        "accent4":     "#f012be",
        "border":      "#7fdbff33",
        "plot_bg":     "#001530",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#6090b0",
        "grad_a":      "#7fdbff",
        "grad_b":      "#01ff70",
        "btn_bg":      "#7fdbff",
        "btn_text":    "#001f3f",
    },
    # 8
    "Solar Orange": {
        "bg":          "#1a0a00",
        "sidebar_bg":  "#2d1400",
        "card_bg":     "#3d1f00",
        "text":        "#ffe0b2",
        "accent":      "#ff9100",
        "accent2":     "#ffd740",
        "accent3":     "#ff1744",
        "accent4":     "#40c4ff",
        "border":      "#ff910033",
        "plot_bg":     "#120700",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#c07030",
        "grad_a":      "#ff9100",
        "grad_b":      "#ffd740",
        "btn_bg":      "#ff9100",
        "btn_text":    "#1a0a00",
    },
    # 9
    "MATLAB Scientific": {
        "bg":          "#f5f5f5",
        "sidebar_bg":  "#e8e8e8",
        "card_bg":     "#ffffff",
        "text":        "#222222",
        "accent":      "#0066cc",
        "accent2":     "#cc0000",
        "accent3":     "#007700",
        "accent4":     "#8800cc",
        "border":      "#0066cc33",
        "plot_bg":     "#ffffff",
        "plotly_tmpl": "plotly_white",
        "metric_lbl":  "#555555",
        "grad_a":      "#0066cc",
        "grad_b":      "#cc0000",
        "btn_bg":      "#0066cc",
        "btn_text":    "#ffffff",
    },
    # 10
    "Gradient Glass": {
        "bg":          "#0f0c29",
        "sidebar_bg":  "#1a1560",
        "card_bg":     "#1e1a70",
        "text":        "#e8e0ff",
        "accent":      "#a78bfa",
        "accent2":     "#34d399",
        "accent3":     "#f87171",
        "accent4":     "#fbbf24",
        "border":      "#a78bfa33",
        "plot_bg":     "#0d0a22",
        "plotly_tmpl": "plotly_dark",
        "metric_lbl":  "#9080c0",
        "grad_a":      "#a78bfa",
        "grad_b":      "#34d399",
        "btn_bg":      "linear-gradient(135deg,#a78bfa,#34d399)",
        "btn_text":    "#0f0c29",
    },
}

def next_motor_size(P_kw):
    for m in STANDARD_MOTORS:
        if m >= P_kw:
            return m
    return STANDARD_MOTORS[-1]
