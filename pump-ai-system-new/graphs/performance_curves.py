# =============================================================================
# graphs/performance_curves.py
# Reciprocating, Plunger, Gear pump plots
# =============================================================================
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.reciprocating import flow_vs_time as recip_flow, pressure_pulsation
from modules.plunger import flow_vs_time as plunger_flow
from modules.gear import flow_vs_viscosity

def rgba(hex6, alpha):
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

# ── Reciprocating ─────────────────────────────────────────────────────────────
def recip_dashboard(Q_act, H_m, N_rpm, n_cyl, th):
    acc = th["accent"]; acc2 = th["accent2"]; acc3 = th["accent3"]
    t_f, Q_f = recip_flow(Q_act, N_rpm, n_cyl)
    t_p, P_p = pressure_pulsation(H_m, N_rpm, n_cyl)

    fig = make_subplots(rows=1, cols=2,
                         subplot_titles=("Flow vs Time (Pulsation)", "Pressure Pulsation"))
    fig.add_trace(go.Scatter(x=t_f, y=Q_f*1000, mode="lines", name="Q(t) L/s",
                              line=dict(color=acc, width=2.5),
                              fill="tozeroy", fillcolor=rgba(acc, 0.09)), row=1, col=1)
    fig.add_hline(y=Q_act*1000, line_dash="dot", line_color=acc2,
                  annotation_text="Mean Flow", row=1, col=1)
    fig.add_trace(go.Scatter(x=t_p, y=P_p, mode="lines", name="Pressure (m)",
                              line=dict(color=acc3, width=2.5)), row=1, col=2)
    fig.add_hline(y=H_m, line_dash="dot", line_color=acc,
                  annotation_text="Design Head", row=1, col=2)
    fig.update_layout(
        title=dict(text=f"Reciprocating Pump — Pulsation Analysis ({n_cyl} cyl)",
                   font=dict(size=15, color=acc)),
        template=th["plotly_tmpl"], height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    for ann in fig.layout.annotations:
        ann.font.color = th["accent"]
    return fig

# ── Plunger ───────────────────────────────────────────────────────────────────
def plunger_dashboard(Q_act, H_m, N_rpm, n_pl, th):
    acc = th["accent"]; acc2 = th["accent2"]
    t_f, Q_f = plunger_flow(Q_act, N_rpm, n_pl)
    # Pressure vs flow (PD characteristic — near vertical)
    dP_range = np.linspace(0, H_m * 1.4, 80)
    Q_pd     = Q_act * (1 - 0.03 * dP_range / (H_m + 1e-9))

    fig = make_subplots(rows=1, cols=2,
                         subplot_titles=("Flow vs Time", "P-Q Characteristic"))
    fig.add_trace(go.Scatter(x=t_f, y=Q_f*1000, mode="lines", name="Q(t) L/s",
                              line=dict(color=acc, width=2.5),
                              fill="tozeroy", fillcolor=rgba(acc, 0.09)), row=1, col=1)
    fig.add_trace(go.Scatter(x=Q_pd*1000, y=dP_range, mode="lines",
                              name="P-Q (PD pump)", line=dict(color=acc2, width=2.5)),
                  row=1, col=2)
    fig.update_layout(
        title=dict(text="Plunger Pump — Performance", font=dict(size=15, color=acc)),
        template=th["plotly_tmpl"], height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    for ann in fig.layout.annotations:
        ann.font.color = th["accent"]
    return fig

# ── Gear ──────────────────────────────────────────────────────────────────────
def gear_dashboard(Q_d, mu_pas, vol_eff, th):
    acc = th["accent"]; acc2 = th["accent2"]; acc3 = th["accent3"]
    mu_cP, Q_arr = flow_vs_viscosity(Q_d, vol_eff=vol_eff)

    # eff vs viscosity
    eta_arr = np.clip(vol_eff - 0.00005 * mu_cP**0.4, 0.5, vol_eff)

    fig = make_subplots(rows=1, cols=2,
                         subplot_titles=("Flow vs Viscosity", "Efficiency vs Viscosity"))
    fig.add_trace(go.Scatter(x=mu_cP, y=Q_arr*3600, mode="lines",
                              name="Flow (m³/h)",
                              line=dict(color=acc, width=2.5),
                              fill="tozeroy", fillcolor=rgba(acc, 0.09)), row=1, col=1)
    fig.add_vline(x=mu_pas*1000, line_dash="dot", line_color=acc3,
                  annotation_text="Design μ", row=1, col=1)
    fig.add_trace(go.Scatter(x=mu_cP, y=eta_arr*100, mode="lines",
                              name="Efficiency (%)",
                              line=dict(color=acc2, width=2.5)), row=1, col=2)
    fig.update_xaxes(type="log", title_text="Viscosity (cP)")
    fig.update_layout(
        title=dict(text="Gear Pump — Viscosity Performance Curves",
                   font=dict(size=15, color=acc)),
        template=th["plotly_tmpl"], height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    for ann in fig.layout.annotations:
        ann.font.color = th["accent"]
    return fig
