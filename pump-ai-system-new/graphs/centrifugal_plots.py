# =============================================================================
# graphs/centrifugal_plots.py
# =============================================================================
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.centrifugal import performance_curves
from calculations.losses import system_curve

def rgba(hex6, alpha):
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def hq_with_system(Q_d, H_d, H_static, f, L, D_m, K_tot, eta_d, th):
    Q, H, eta, P_kw = performance_curves(Q_d, H_d, eta_d)
    Q_sys, H_sys    = system_curve(Q_d, H_static, f, L, D_m, K_tot, rho=1000)
    acc = th["accent"]; acc2 = th["accent2"]; acc3 = th["accent3"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Q*3600, y=H, mode="lines", name="Pump H-Q Curve",
        line=dict(color=acc, width=3),
        fill="tozeroy", fillcolor=rgba(acc, 0.07)
    ))
    fig.add_trace(go.Scatter(
        x=Q_sys*3600, y=H_sys, mode="lines", name="System Curve",
        line=dict(color=acc3, width=2.5, dash="dash")
    ))
    # Operating point intersection
    diff = np.abs(H - np.interp(Q, Q_sys, H_sys))
    idx  = int(np.argmin(diff))
    fig.add_trace(go.Scatter(
        x=[Q[idx]*3600], y=[H[idx]], mode="markers", name="Operating Point",
        marker=dict(color="#ef5350", size=16, symbol="star",
                    line=dict(color="white", width=2))
    ))
    fig.update_layout(
        title=dict(text="Head-Flow (H-Q) Curve with System Curve", font=dict(size=16, color=acc)),
        xaxis_title="Flow Rate (m³/h)",
        yaxis_title="Head (m)",
        template=th["plotly_tmpl"],
        height=440,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=th["text"])),
    )
    return fig, Q[idx]*3600, H[idx]

def efficiency_curve(Q_d, H_d, eta_d, th):
    Q, H, eta, P_kw = performance_curves(Q_d, H_d, eta_d)
    acc = th["accent2"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Q*3600, y=eta*100, mode="lines", name="Efficiency η (%)",
        line=dict(color=acc, width=3),
        fill="tozeroy", fillcolor=rgba(acc, 0.08)
    ))
    bep_idx = int(np.argmax(eta))
    fig.add_trace(go.Scatter(
        x=[Q[bep_idx]*3600], y=[eta[bep_idx]*100], mode="markers", name="BEP",
        marker=dict(color="#ffd740", size=14, symbol="diamond",
                    line=dict(color="white", width=2))
    ))
    fig.add_hline(y=eta_d*100, line_dash="dot", line_color=th["accent3"],
                  annotation_text=f"Design η = {eta_d*100:.0f}%",
                  annotation_font_color=th["accent3"])
    fig.update_layout(
        title=dict(text="Efficiency vs Flow Rate", font=dict(size=16, color=acc)),
        xaxis_title="Flow Rate (m³/h)", yaxis_title="Efficiency (%)",
        yaxis_range=[0, 100],
        template=th["plotly_tmpl"], height=400,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=th["text"])),
    )
    return fig

def power_curve(Q_d, H_d, eta_d, th):
    Q, H, eta, P_kw = performance_curves(Q_d, H_d, eta_d)
    acc = th["accent3"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Q*3600, y=P_kw, mode="lines", name="Shaft Power (kW)",
        line=dict(color=acc, width=3),
        fill="tozeroy", fillcolor=rgba(acc, 0.08)
    ))
    fig.update_layout(
        title=dict(text="Shaft Power vs Flow Rate", font=dict(size=16, color=acc)),
        xaxis_title="Flow Rate (m³/h)", yaxis_title="Power (kW)",
        template=th["plotly_tmpl"], height=400,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=th["text"])),
    )
    return fig

def combined_dashboard(Q_d, H_d, H_static, f, L, D_m, K_tot, eta_d, th):
    Q, H, eta, P_kw = performance_curves(Q_d, H_d, eta_d)
    Q_sys, H_sys    = system_curve(Q_d, H_static, f, L, D_m, K_tot, rho=1000)
    acc  = th["accent"]; acc2 = th["accent2"]; acc3 = th["accent3"]; acc4 = th["accent4"]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("H-Q & System Curve", "Efficiency vs Flow",
                        "Shaft Power", "Performance Envelope"),
        vertical_spacing=0.18, horizontal_spacing=0.14,
    )
    # Row 1 Col 1 — HQ
    fig.add_trace(go.Scatter(x=Q*3600, y=H, mode="lines", name="H-Q",
                              line=dict(color=acc, width=2.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=Q_sys*3600, y=H_sys, mode="lines", name="System",
                              line=dict(color=acc3, width=2, dash="dash")), row=1, col=1)
    # Row 1 Col 2 — Efficiency
    fig.add_trace(go.Scatter(x=Q*3600, y=eta*100, mode="lines", name="η(%)",
                              line=dict(color=acc2, width=2.5)), row=1, col=2)
    # Row 2 Col 1 — Power
    fig.add_trace(go.Scatter(x=Q*3600, y=P_kw, mode="lines", name="P(kW)",
                              line=dict(color=acc4, width=2.5)), row=2, col=1)
    # Row 2 Col 2 — Bar chart: performance scores
    cats   = ["Head", "Flow", "Efficiency", "Reliability", "Maintenance"]
    scores = [75, 90, int(eta_d*100), 92, 88]
    colors = [acc, acc2, acc3, acc4, "#4fc3f7"]
    fig.add_trace(go.Bar(x=cats, y=scores, marker_color=colors, name="Score"), row=2, col=2)

    fig.update_layout(
        template=th["plotly_tmpl"], height=620, showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=th["plot_bg"],
        font=dict(color=th["text"]),
    )
    for ann in fig.layout.annotations:
        ann.font.color = th["accent"]
        ann.font.size  = 13
    return fig
