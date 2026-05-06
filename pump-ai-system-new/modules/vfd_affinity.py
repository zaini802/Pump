# =============================================================================
# modules/vfd_affinity.py
# VFD (Variable Frequency Drive) & Affinity Laws Simulation Module
# Author  : Zunair Shahzad | Chemical Engineering | UET Lahore 2022-2026
# Standard: HI 1.3.4 | API 610 §5.3 | IEC 61800 (VFD)
# =============================================================================

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _hex_to_rgba(hex_color, alpha=0.08):
    """Convert #RRGGBB hex to proper 'rgba(r,g,b,a)' string for Plotly fillcolor."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(88,166,255,{alpha})"


# =============================================================================
# AFFINITY LAW CALCULATIONS
# =============================================================================

def affinity_laws(Q_base, H_base, P_base, N_base, N_new):
    """
    Apply Pump Affinity Laws for speed change.

    Laws (HI 1.3.4 / Karassik 4th Ed. §2.4):
        Q ∝ N        →  Q_new = Q_base × (N_new / N_base)
        H ∝ N²       →  H_new = H_base × (N_new / N_base)²
        P ∝ N³       →  P_new = P_base × (N_new / N_base)³

    Parameters
    ----------
    Q_base  : float  Base flow rate (m³/h or any consistent unit)
    H_base  : float  Base total dynamic head (m)
    P_base  : float  Base shaft power (kW)
    N_base  : float  Base speed (RPM)
    N_new   : float  New (VFD-controlled) speed (RPM)

    Returns
    -------
    dict with Q_new, H_new, P_new and ratio
    """
    ratio = N_new / N_base
    return {
        "ratio":  ratio,
        "Q_new":  Q_base * ratio,
        "H_new":  H_base * ratio ** 2,
        "P_new":  P_base * ratio ** 3,
    }


def affinity_curves(Q_base, H_base, P_base, N_base, n_points=60):
    """
    Generate Speed vs (Flow, Head, Power) sweep curves.
    Speed range: 20% → 110% of base speed.
    """
    speeds = np.linspace(N_base * 0.20, N_base * 1.10, n_points)
    ratios = speeds / N_base
    flows   = Q_base * ratios
    heads   = H_base * ratios ** 2
    powers  = P_base * ratios ** 3
    pct     = ratios * 100          # percentage of base speed
    return speeds, pct, flows, heads, powers


def energy_savings_pct(N_new, N_base):
    """
    Energy saving vs throttling (valve) control.
    VFD power ratio = (N_new/N_base)^3  vs  throttle = ~constant power.
    Saving % = (1 - ratio³) × 100
    """
    ratio = min(N_new / N_base, 1.0)
    return (1 - ratio ** 3) * 100


# =============================================================================
# PLOTLY VISUALIZATIONS
# =============================================================================

def _theme_layout(fig, th, title, height=480):
    """Apply consistent dark/light theme to a plotly figure."""
    tmpl  = th.get("plotly_tmpl", "plotly_white")
    bg    = "#0d1117" if "dark" in tmpl else "#ffffff"
    paper = "#0d1117" if "dark" in tmpl else "#f8f9fa"
    fc    = "#c9d1d9" if "dark" in tmpl else "#24292e"
    gc    = "rgba(255,255,255,0.06)" if "dark" in tmpl else "rgba(0,0,0,0.06)"

    fig.update_layout(
        template      = tmpl,
        paper_bgcolor = paper,
        plot_bgcolor  = bg,
        font          = dict(family="'Segoe UI', Arial, sans-serif", color=fc, size=12),
        title         = dict(text=title, font=dict(size=14, color=th.get("accent","#58a6ff")),
                             x=0.5, xanchor="center"),
        height        = height,
        margin        = dict(l=60, r=40, t=60, b=50),
        legend        = dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=fc)),
        xaxis         = dict(gridcolor=gc, zerolinecolor=gc),
        yaxis         = dict(gridcolor=gc, zerolinecolor=gc),
        hoverlabel    = dict(bgcolor="#1c2128", font_size=12,
                             font_family="'Segoe UI', Arial"),
    )
    return fig


def plot_speed_vs_flow(Q_base, H_base, P_base, N_base, N_new, th):
    """Speed vs Flow — with operating point marker."""
    speeds, pct, flows, _, _ = affinity_curves(Q_base, H_base, P_base, N_base)
    res   = affinity_laws(Q_base, H_base, P_base, N_base, N_new)
    acc   = th.get("accent",  "#58a6ff")
    acc2  = th.get("accent2", "#3fb950")

    fig = go.Figure()

    # Curve
    fig.add_trace(go.Scatter(
        x=pct, y=flows,
        mode="lines",
        name="Q vs Speed",
        line=dict(color=acc, width=3),
        fill="tozeroy",
        fillcolor=_hex_to_rgba(acc, 0.08),
        hovertemplate="<b>Speed: %{x:.1f}%</b><br>Flow: %{y:.3f} m³/h<extra></extra>",
    ))

    # Base operating point
    fig.add_trace(go.Scatter(
        x=[100], y=[Q_base],
        mode="markers", name=f"Base  ({N_base:.0f} RPM)",
        marker=dict(size=14, color="#ffd740", symbol="star",
                    line=dict(width=2, color="#0d1117")),
        hovertemplate=f"Base Point<br>Speed: {N_base:.0f} RPM (100%)<br>Q = {Q_base:.3f} m³/h<extra></extra>",
    ))

    # New VFD point
    pct_new = N_new / N_base * 100
    fig.add_trace(go.Scatter(
        x=[pct_new], y=[res["Q_new"]],
        mode="markers", name=f"VFD Point  ({N_new:.0f} RPM)",
        marker=dict(size=14, color=acc2, symbol="circle",
                    line=dict(width=2, color="#0d1117")),
        hovertemplate=f"VFD Point<br>Speed: {N_new:.0f} RPM ({pct_new:.1f}%)<br>Q = {res['Q_new']:.3f} m³/h<extra></extra>",
    ))

    # Vertical dashed line at new speed
    fig.add_vline(x=pct_new, line=dict(color=acc2, dash="dash", width=1.5),
                  annotation_text=f"{N_new:.0f} RPM", annotation_font_color=acc2)

    fig.update_xaxes(title_text="Speed (% of Base Speed)", range=[15, 115])
    fig.update_yaxes(title_text="Flow Rate Q (m³/h)")
    return _theme_layout(fig, th, "⚡ Speed vs Flow Rate  [Q ∝ N]")


def plot_speed_vs_head(Q_base, H_base, P_base, N_base, N_new, th):
    """Speed vs Head — with operating point marker."""
    speeds, pct, _, heads, _ = affinity_curves(Q_base, H_base, P_base, N_base)
    res   = affinity_laws(Q_base, H_base, P_base, N_base, N_new)
    acc   = th.get("accent3", "#ff79c6")
    acc2  = th.get("accent2", "#3fb950")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=pct, y=heads,
        mode="lines",
        name="H vs Speed",
        line=dict(color=acc, width=3),
        fill="tozeroy",
        fillcolor="rgba(255,121,198,0.08)",
        hovertemplate="Speed: %{x:.1f}%<br>H: %{y:.2f} m<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[100], y=[H_base],
        mode="markers", name=f"Base  ({N_base:.0f} RPM)",
        marker=dict(size=14, color="#ffd740", symbol="star",
                    line=dict(width=2, color="#0d1117")),
        hovertemplate=f"Base Point<br>Speed: {N_base:.0f} RPM (100%)<br>H = {H_base:.2f} m<extra></extra>",
    ))

    pct_new = N_new / N_base * 100
    fig.add_trace(go.Scatter(
        x=[pct_new], y=[res["H_new"]],
        mode="markers", name=f"VFD Point  ({N_new:.0f} RPM)",
        marker=dict(size=14, color=acc2, symbol="circle",
                    line=dict(width=2, color="#0d1117")),
        hovertemplate=f"VFD Point<br>Speed: {N_new:.0f} RPM ({pct_new:.1f}%)<br>H = {res['H_new']:.2f} m<extra></extra>",
    ))

    fig.add_vline(x=pct_new, line=dict(color=acc2, dash="dash", width=1.5),
                  annotation_text=f"{N_new:.0f} RPM", annotation_font_color=acc2)

    fig.update_xaxes(title_text="Speed (% of Base Speed)", range=[15, 115])
    fig.update_yaxes(title_text="Total Dynamic Head H (m)")
    return _theme_layout(fig, th, "⚡ Speed vs Head  [H ∝ N²]")


def plot_speed_vs_power(Q_base, H_base, P_base, N_base, N_new, th):
    """Speed vs Power — cubic relationship with energy saving annotation."""
    speeds, pct, _, _, powers = affinity_curves(Q_base, H_base, P_base, N_base)
    res     = affinity_laws(Q_base, H_base, P_base, N_base, N_new)
    saving  = energy_savings_pct(N_new, N_base)
    acc     = th.get("accent4",  "#50fa7b")
    acc2    = th.get("accent2",  "#3fb950")

    # Throttle comparison — constant power (simplified)
    throttle_powers = np.full_like(pct, P_base)   # valve throttling ≈ constant motor draw

    fig = go.Figure()

    # Throttle/valve reference
    fig.add_trace(go.Scatter(
        x=pct, y=throttle_powers,
        mode="lines",
        name="Throttle Valve (no VFD)",
        line=dict(color="#ff5555", width=2, dash="dot"),
        hovertemplate="<b>Speed: %{x:.1f}%</b><br>Power (throttle): %{y:.3f} kW<extra></extra>",
    ))

    # VFD power curve
    fig.add_trace(go.Scatter(
        x=pct, y=powers,
        mode="lines",
        name="VFD Control",
        line=dict(color=acc, width=3),
        fill="tozeroy",
        fillcolor="rgba(80,250,123,0.08)",
        hovertemplate="<b>Speed: %{x:.1f}%</b><br>Power (VFD): %{y:.3f} kW<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[100], y=[P_base],
        mode="markers", name=f"Base  ({N_base:.0f} RPM)",
        marker=dict(size=14, color="#ffd740", symbol="star",
                    line=dict(width=2, color="#0d1117")),
    ))

    pct_new = N_new / N_base * 100
    fig.add_trace(go.Scatter(
        x=[pct_new], y=[res["P_new"]],
        mode="markers", name=f"VFD Point  ({N_new:.0f} RPM)  —  Save {saving:.1f}%",
        marker=dict(size=14, color=acc2, symbol="circle",
                    line=dict(width=2, color="#0d1117")),
        hovertemplate=f"VFD Point<br>Speed: {N_new:.0f} RPM ({pct_new:.1f}%)<br>P = {res['P_new']:.3f} kW<br>Saving: {saving:.1f}%<extra></extra>",
    ))

    # Shaded energy saving region
    fig.add_trace(go.Scatter(
        x=pct, y=throttle_powers,
        mode="none", showlegend=False,
        fill=None,
    ))
    fig.add_trace(go.Scatter(
        x=pct, y=powers,
        mode="none", name=f"Energy Saved (VFD vs Throttle)",
        fill="tonexty",
        fillcolor="rgba(80,250,123,0.15)",
        showlegend=True,
    ))

    fig.add_vline(x=pct_new, line=dict(color=acc2, dash="dash", width=1.5),
                  annotation_text=f"{N_new:.0f} RPM", annotation_font_color=acc2)

    # Energy saving annotation
    fig.add_annotation(
        x=pct_new, y=res["P_new"] + P_base * 0.08,
        text=f"💡 {saving:.1f}% saved",
        showarrow=True, arrowhead=2, arrowcolor=acc2,
        font=dict(color=acc2, size=12, family="'Segoe UI', Arial"),
        bgcolor="rgba(0,0,0,0.5)", bordercolor=acc2,
        borderwidth=1, borderpad=4,
    )

    fig.update_xaxes(title_text="Speed (% of Base Speed)", range=[15, 115])
    fig.update_yaxes(title_text="Shaft Power P (kW)")
    return _theme_layout(fig, th, "⚡ Speed vs Power  [P ∝ N³]  |  VFD vs Throttle Valve")


def plot_combined_vfd(Q_base, H_base, P_base, N_base, N_new, th):
    """
    4-panel combined VFD dashboard:
    Top-left:  Speed vs Flow
    Top-right: Speed vs Head
    Bottom-left: Speed vs Power (with throttle comparison)
    Bottom-right: Affinity ratio summary bar chart
    """
    speeds, pct, flows, heads, powers = affinity_curves(Q_base, H_base, P_base, N_base)
    res    = affinity_laws(Q_base, H_base, P_base, N_base, N_new)
    saving = energy_savings_pct(N_new, N_base)
    pct_new = N_new / N_base * 100

    tmpl   = th.get("plotly_tmpl", "plotly_white")
    bg     = "#0d1117" if "dark" in tmpl else "#ffffff"
    paper  = "#0d1117" if "dark" in tmpl else "#f8f9fa"
    fc     = "#c9d1d9" if "dark" in tmpl else "#24292e"
    gc     = "rgba(255,255,255,0.06)" if "dark" in tmpl else "rgba(0,0,0,0.06)"

    acc_q  = th.get("accent",  "#58a6ff")
    acc_h  = th.get("accent3", "#ff79c6")
    acc_p  = "#50fa7b"
    acc2   = th.get("accent2", "#3fb950")

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Flow Rate  Q ∝ N",
            "Total Head  H ∝ N²",
            "Shaft Power  P ∝ N³  (VFD vs Throttle)",
            "Affinity Summary at Selected Speed"
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # ── Panel 1: Flow ──
    fig.add_trace(go.Scatter(x=pct, y=flows, mode="lines", name="Q",
                             line=dict(color=acc_q, width=2.5),
                             fill="tozeroy", fillcolor="rgba(88,166,255,0.07)",
                             hovertemplate="Speed: %{x:.1f}%<br>Q: %{y:.3f} m³/h<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=[100], y=[Q_base], mode="markers", name="Base Q",
                             marker=dict(size=12, color="#ffd740", symbol="star"),
                             showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=[pct_new], y=[res["Q_new"]], mode="markers", name="VFD Q",
                             marker=dict(size=12, color=acc2, symbol="circle"),
                             showlegend=False,
                             hovertemplate=f"VFD: {N_new:.0f} RPM<br>Q = {res['Q_new']:.3f} m³/h<extra></extra>"),
                  row=1, col=1)

    # ── Panel 2: Head ──
    fig.add_trace(go.Scatter(x=pct, y=heads, mode="lines", name="H",
                             line=dict(color=acc_h, width=2.5),
                             fill="tozeroy", fillcolor="rgba(255,121,198,0.07)",
                             hovertemplate="Speed: %{x:.1f}%<br>H: %{y:.2f} m<extra></extra>"),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=[100], y=[H_base], mode="markers", name="Base H",
                             marker=dict(size=12, color="#ffd740", symbol="star"),
                             showlegend=False),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=[pct_new], y=[res["H_new"]], mode="markers", name="VFD H",
                             marker=dict(size=12, color=acc2, symbol="circle"),
                             showlegend=False,
                             hovertemplate=f"VFD: {N_new:.0f} RPM<br>H = {res['H_new']:.2f} m<extra></extra>"),
                  row=1, col=2)

    # ── Panel 3: Power ──
    throttle_p = np.full_like(pct, P_base)
    fig.add_trace(go.Scatter(x=pct, y=throttle_p, mode="lines", name="Throttle Valve",
                             line=dict(color="#ff5555", width=1.8, dash="dot"),
                             hovertemplate="Speed: %{x:.1f}%<br>P (throttle): %{y:.3f} kW<extra></extra>"),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=pct, y=powers, mode="lines", name="VFD Power",
                             line=dict(color=acc_p, width=2.5),
                             fill="tozeroy", fillcolor="rgba(80,250,123,0.07)",
                             hovertemplate="Speed: %{x:.1f}%<br>P (VFD): %{y:.3f} kW<extra></extra>"),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=[100], y=[P_base], mode="markers", name="Base P",
                             marker=dict(size=12, color="#ffd740", symbol="star"),
                             showlegend=False),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=[pct_new], y=[res["P_new"]], mode="markers", name="VFD P",
                             marker=dict(size=12, color=acc2, symbol="circle"),
                             showlegend=False,
                             hovertemplate=f"VFD: {N_new:.0f} RPM<br>P = {res['P_new']:.3f} kW<br>Save {saving:.1f}%<extra></extra>"),
                  row=2, col=1)

    # ── Panel 4: Summary bar chart ──
    cats      = ["Flow Q", "Head H", "Power P"]
    base_vals = [Q_base, H_base, P_base]
    new_vals  = [res["Q_new"], res["H_new"], res["P_new"]]
    bar_colors = [acc_q, acc_h, acc_p]

    fig.add_trace(go.Bar(name="Base Speed", x=cats, y=base_vals,
                         marker_color="#ffd740", opacity=0.7,
                         hovertemplate="%{x} Base: %{y:.3f}<extra></extra>"),
                  row=2, col=2)
    fig.add_trace(go.Bar(name=f"VFD ({N_new:.0f} RPM)", x=cats, y=new_vals,
                         marker_color=bar_colors, opacity=0.9,
                         hovertemplate="%{x} VFD: %{y:.3f}<extra></extra>"),
                  row=2, col=2)

    # Axis labels
    fig.update_xaxes(title_text="Speed (% of Base)", row=1, col=1, gridcolor=gc, zerolinecolor=gc)
    fig.update_yaxes(title_text="Q (m³/h)",           row=1, col=1, gridcolor=gc, zerolinecolor=gc)
    fig.update_xaxes(title_text="Speed (% of Base)", row=1, col=2, gridcolor=gc, zerolinecolor=gc)
    fig.update_yaxes(title_text="H (m)",               row=1, col=2, gridcolor=gc, zerolinecolor=gc)
    fig.update_xaxes(title_text="Speed (% of Base)", row=2, col=1, gridcolor=gc, zerolinecolor=gc)
    fig.update_yaxes(title_text="P (kW)",              row=2, col=1, gridcolor=gc, zerolinecolor=gc)
    fig.update_xaxes(title_text="Parameter",           row=2, col=2, gridcolor=gc, zerolinecolor=gc)
    fig.update_yaxes(title_text="Value",               row=2, col=2, gridcolor=gc, zerolinecolor=gc)

    # Vlines on panels 1-3
    for r, c in [(1,1),(1,2),(2,1)]:
        fig.add_vline(x=pct_new, line=dict(color=acc2, dash="dash", width=1.2),
                      row=r, col=c)

    fig.update_layout(
        template=tmpl, paper_bgcolor=paper, plot_bgcolor=bg,
        font=dict(family="'Segoe UI', Arial, sans-serif", color=fc, size=11),
        height=700,
        title=dict(
            text=f"⚡ VFD & Affinity Laws — Combined Dashboard  |  Base: {N_base:.0f} RPM  →  VFD: {N_new:.0f} RPM  ({pct_new:.1f}%)",
            font=dict(size=14, color=th.get("accent","#58a6ff")), x=0.5, xanchor="center"
        ),
        margin=dict(l=60, r=40, t=70, b=50),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=fc),
                    orientation="h", y=-0.06, x=0.5, xanchor="center"),
        barmode="group",
        hoverlabel=dict(bgcolor="#1c2128", font_size=11),
    )
    # Update subplot title colors
    for ann in fig.layout.annotations:
        ann.font.color = th.get("accent", "#58a6ff")
        ann.font.size  = 12

    return fig
