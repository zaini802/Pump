# =============================================================================
# graphs/pump_3d.py
# 3D Pump Visualization + Animated Flow Diagram (Plotly)
# Pure Python — no CAD software needed
# =============================================================================
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

def rgba(hex6, alpha):
    h = hex6.lstrip("#")
    r, gv, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{gv},{b},{alpha})"

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Generate cylinder mesh
# ─────────────────────────────────────────────────────────────────────────────
def _cylinder(x_c, y_c, z_start, z_end, radius, n=40, color="lightblue", name=""):
    theta = np.linspace(0, 2*np.pi, n)
    x = x_c + radius * np.cos(theta)
    y = y_c + radius * np.sin(theta)
    vertices_x, vertices_y, vertices_z = [], [], []
    i_idx, j_idx, k_idx = [], [], []
    # Build side surface
    for ti in range(n-1):
        # bottom ring vertex ti, top ring vertex ti
        base = ti * 2
        vertices_x += [x[ti], x[ti], x[ti+1], x[ti+1]]
        vertices_y += [y[ti], y[ti], y[ti+1], y[ti+1]]
        vertices_z += [z_start, z_end, z_start, z_end]
    return dict(x=vertices_x, y=vertices_y, z=vertices_z, color=color, name=name)

def _torus_points(R, r, n_major=60, n_minor=20):
    """Torus for impeller casing cross-section."""
    u = np.linspace(0, 2*np.pi, n_major)
    v = np.linspace(0, 2*np.pi, n_minor)
    U, V = np.meshgrid(u, v)
    X = (R + r*np.cos(V)) * np.cos(U)
    Y = (R + r*np.cos(V)) * np.sin(U)
    Z = r * np.sin(V)
    return X, Y, Z

# ─────────────────────────────────────────────────────────────────────────────
# MAIN: 3D Centrifugal Pump Cross-Section View
# ─────────────────────────────────────────────────────────────────────────────
def pump_3d_view(D2_mm, D1_mm, b2_mm, shaft_dia_mm, D_pipe_mm,
                 H_m, Q_m3h, N_rpm, th, pump_type="Centrifugal"):
    """
    Interactive 3D pump visualization scaled to actual design parameters.
    Shows: casing (volute), impeller, shaft, suction/discharge nozzles.
    """
    # Scale everything relative to impeller diameter (in metres)
    D2    = D2_mm / 1000
    D1    = D1_mm / 1000
    b2    = b2_mm / 1000
    Ds    = shaft_dia_mm / 1000
    Dp    = D_pipe_mm / 1000
    R_cas = D2 * 0.62                   # casing inner radius (volute)
    R_cas_out = D2 * 0.75               # casing outer radius
    acc   = th["accent"]
    acc2  = th["accent2"]
    acc3  = th["accent3"]
    acc4  = th["accent4"]
    bg    = th["plot_bg"]
    text  = th["text"]

    fig = go.Figure()
    n = 80

    # ── 1. VOLUTE CASING (torus-like) ────────────────────────────────────────
    X_v, Y_v, Z_v = _torus_points(R_cas, (R_cas_out-R_cas)/2, n_major=80, n_minor=30)
    fig.add_trace(go.Surface(
        x=X_v, y=Y_v, z=Z_v,
        colorscale=[[0,"#2a3f5f"],[1,"#3d5a8a"]],
        opacity=0.55, showscale=False, name="Volute Casing",
        hovertemplate="Volute Casing<br>D_outer=%.0f mm" % (R_cas_out*2000)
    ))

    # ── 2. IMPELLER DISC (main disc) ─────────────────────────────────────────
    theta = np.linspace(0, 2*np.pi, n)
    r_imp = np.linspace(D1/2, D2/2, 20)
    T, R  = np.meshgrid(theta, r_imp)
    X_imp = R * np.cos(T)
    Y_imp = R * np.sin(T)
    Z_imp_b = np.zeros_like(X_imp) - b2/2   # bottom shroud
    Z_imp_t = np.zeros_like(X_imp) + b2/2   # top shroud

    for Z_imp, name_i in [(Z_imp_b,"Impeller Back Shroud"),(Z_imp_t,"Impeller Front Shroud")]:
        fig.add_trace(go.Surface(
            x=X_imp, y=Y_imp, z=Z_imp,
            colorscale=[[0,"#c0392b"],[0.5,"#e74c3c"],[1,"#ff6b6b"]],
            opacity=0.85, showscale=False, name=name_i,
            hovertemplate=f"{name_i}<br>D₂={D2_mm:.0f}mm<extra></extra>"
        ))

    # ── 3. IMPELLER BLADES (6 backward-curved blades) ────────────────────────
    n_blades = 6
    beta2_rad = math.radians(25)    # backward-swept outlet angle
    for k in range(n_blades):
        angle_offset = k * 2*math.pi / n_blades
        r_blade = np.linspace(D1/2, D2/2, 25)
        theta_blade = angle_offset + (r_blade - D1/2)/(D2/2 - D1/2) * 1.2
        x_bl = r_blade * np.cos(theta_blade)
        y_bl = r_blade * np.sin(theta_blade)
        z_bl_top =  np.ones_like(r_blade) * b2/2 * 0.9
        z_bl_bot = -np.ones_like(r_blade) * b2/2 * 0.9
        for z_bl in [z_bl_top, z_bl_bot]:
            fig.add_trace(go.Scatter3d(
                x=x_bl, y=y_bl, z=z_bl,
                mode="lines",
                line=dict(color="#ff9f43", width=4),
                name="Blade" if k==0 else "",
                showlegend=(k==0),
                hovertemplate=f"Impeller Blade {k+1}<br>β₂=25°<extra></extra>"
            ))
        # Blade surface fill (thin rectangle)
        x_surf = np.array([x_bl, x_bl])
        y_surf = np.array([y_bl, y_bl])
        z_surf = np.array([z_bl_top, z_bl_bot])
        fig.add_trace(go.Surface(
            x=x_surf, y=y_surf, z=z_surf,
            colorscale=[[0,"#ff9f43"],[1,"#ffd700"]],
            opacity=0.7, showscale=False,
            name="Blade Surface" if k==0 else "",
            showlegend=False,
        ))

    # ── 4. SHAFT ─────────────────────────────────────────────────────────────
    z_shaft = np.linspace(-D2*0.9, D2*0.9, 10)
    theta_s = np.linspace(0, 2*np.pi, 20)
    T_s, Z_s = np.meshgrid(theta_s, z_shaft)
    X_s = Ds/2 * np.cos(T_s)
    Y_s = Ds/2 * np.sin(T_s)
    fig.add_trace(go.Surface(
        x=X_s, y=Y_s, z=Z_s,
        colorscale=[[0,"#636e72"],[1,"#b2bec3"]],
        opacity=0.95, showscale=False, name="Shaft",
        hovertemplate=f"Shaft<br>d_shaft={shaft_dia_mm:.0f}mm<extra></extra>"
    ))

    # ── 5. SUCTION NOZZLE (horizontal pipe into eye) ─────────────────────────
    pipe_len = D2 * 1.8
    z_suc = np.linspace(-pipe_len, -D2*0.35, 15)
    theta_p = np.linspace(0, 2*np.pi, 20)
    T_p, Z_p = np.meshgrid(theta_p, z_suc)
    X_suc = Dp/2 * np.cos(T_p)
    Y_suc = Dp/2 * np.sin(T_p)
    fig.add_trace(go.Surface(
        x=X_suc, y=Y_suc, z=Z_p,
        colorscale=[[0,"#00b894"],[1,"#00cec9"]],
        opacity=0.7, showscale=False, name="Suction Nozzle",
        hovertemplate=f"Suction Nozzle<br>D_pipe={D_pipe_mm:.0f}mm<extra></extra>"
    ))

    # ── 6. DISCHARGE NOZZLE (vertical pipe out of volute top) ────────────────
    z_dis = np.linspace(R_cas_out, R_cas_out + pipe_len, 15)
    X_dis = Dp/2 * np.cos(T_p) + R_cas * 0.7
    Y_dis = Dp/2 * np.sin(T_p)
    fig.add_trace(go.Surface(
        x=X_dis, y=Y_dis, z=z_dis,
        colorscale=[[0,"#e17055"],[1,"#d63031"]],
        opacity=0.7, showscale=False, name="Discharge Nozzle",
        hovertemplate=f"Discharge Nozzle<br>D_pipe={D_pipe_mm:.0f}mm<extra></extra>"
    ))

    annotations = [
        dict(x=0, y=0, z=D2*0.82,
             text=f"Shaft d={shaft_dia_mm:.0f}mm",
             showarrow=False, font=dict(color=text, size=10)),
        dict(x=R_cas_out*0.7, y=R_cas_out*0.7, z=R_cas_out*0.5,
             text="Volute Casing", showarrow=False,
             font=dict(color=acc, size=10)),
    ]
    arrow_r = R_cas * 0.85
    for idx_a, ang in enumerate(np.linspace(0, 2*np.pi, 8, endpoint=False)):
        dx = -math.sin(ang) * 0.04
        dy =  math.cos(ang) * 0.04
        fig.add_trace(go.Cone(
            x=[arrow_r*math.cos(ang)], y=[arrow_r*math.sin(ang)], z=[0],
            u=[dx], v=[dy], w=[0],
            colorscale=[[0,"#74b9ff"],[1,"#0984e3"]],
            showscale=False, sizemode="absolute", sizeref=0.03,
            name="Flow" if idx_a == 0 else "",
            showlegend=bool(idx_a == 0),
            hovertemplate="Flow direction<extra></extra>"
        ))

    # ── 8. BEARING HOUSINGS (both sides of shaft) ────────────────────────────
    for z_brg in [-D2*0.65, D2*0.65]:
        theta_b = np.linspace(0, 2*np.pi, 20)
        r_brg   = Ds * 2.2
        X_brg   = r_brg * np.cos(theta_b)
        Y_brg   = r_brg * np.sin(theta_b)
        Z_brg_l = np.full_like(theta_b, z_brg)
        Z_brg_u = np.full_like(theta_b, z_brg + np.sign(z_brg)*D2*0.12)
        for xb, yb, za, zb in zip(X_brg[:-1], Y_brg[:-1], Z_brg_l[:-1], Z_brg_u[:-1]):
            pass  # simplified — just add as surface
        T_b, Z_b2 = np.meshgrid(theta_b, [z_brg, z_brg + np.sign(z_brg)*D2*0.12])
        X_b2 = r_brg * np.cos(T_b)
        Y_b2 = r_brg * np.sin(T_b)
        fig.add_trace(go.Surface(
            x=X_b2, y=Y_b2, z=Z_b2,
            colorscale=[[0,"#636e72"],[1,"#b2bec3"]],
            opacity=0.6, showscale=False,
            name="Bearing Housing" if z_brg < 0 else "",
            showlegend=(z_brg < 0),
        ))

    # ── 9. DIMENSION LINES (educational overlay) ─────────────────────────────
    # D2 line
    fig.add_trace(go.Scatter3d(
        x=[-D2/2, D2/2], y=[0,0], z=[b2/2+0.02, b2/2+0.02],
        mode="lines+text",
        line=dict(color=acc, width=3),
        text=["", f"D₂={D2_mm:.0f}mm"],
        textposition="top center",
        textfont=dict(color=acc, size=11),
        name="D₂ dimension", showlegend=False,
    ))
    # D1 line
    fig.add_trace(go.Scatter3d(
        x=[-D1/2, D1/2], y=[0,0], z=[b2/2+0.01, b2/2+0.01],
        mode="lines+text",
        line=dict(color=acc2, width=2, dash="dot"),
        text=["", f"D₁={D1_mm:.0f}mm"],
        textposition="top center",
        textfont=dict(color=acc2, size=10),
        name="D₁ dimension", showlegend=False,
    ))

    fig.update_layout(
        title=dict(
            text=f"🔵 {pump_type} Pump — 3D Cross-Section View<br>"
                 f"<sub>D₂={D2_mm:.0f}mm | Q={Q_m3h:.0f}m³/h | H={H_m:.0f}m | N={N_rpm}rpm</sub>",
            font=dict(size=15, color=acc), x=0.5
        ),
        scene=dict(
            xaxis=dict(title="X (m)", showgrid=True, gridcolor=rgba(acc,0.15),
                       backgroundcolor=bg, color=text),
            yaxis=dict(title="Y (m)", showgrid=True, gridcolor=rgba(acc,0.15),
                       backgroundcolor=bg, color=text),
            zaxis=dict(title="Z (m)", showgrid=True, gridcolor=rgba(acc,0.15),
                       backgroundcolor=bg, color=text),
            bgcolor=bg,
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.9)),
            aspectmode="cube",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        height=620,
        showlegend=True,
        legend=dict(font=dict(color=text), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0,r=0,t=70,b=0),
        # View buttons: Isometric / Front / Top / Side
        updatemenus=[dict(
            type="buttons",
            showactive=True,
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            bgcolor=rgba(acc, 0.15),
            bordercolor=acc,
            font=dict(color=text, size=11),
            buttons=[
                dict(label="⟳ Isometric",
                     method="relayout",
                     args=["scene.camera",
                           dict(eye=dict(x=1.6, y=1.6, z=0.9),
                                up=dict(x=0, y=0, z=1))]),
                dict(label="▶ Front View",
                     method="relayout",
                     args=["scene.camera",
                           dict(eye=dict(x=0, y=-2.5, z=0),
                                up=dict(x=0, y=0, z=1))]),
                dict(label="▲ Top View",
                     method="relayout",
                     args=["scene.camera",
                           dict(eye=dict(x=0, y=0, z=2.8),
                                up=dict(x=0, y=1, z=0))]),
                dict(label="◀ Side View",
                     method="relayout",
                     args=["scene.camera",
                           dict(eye=dict(x=2.5, y=0, z=0),
                                up=dict(x=0, y=0, z=1))]),
                dict(label="↗ Section Cut",
                     method="relayout",
                     args=["scene.camera",
                           dict(eye=dict(x=1.8, y=-1.2, z=1.2),
                                up=dict(x=0, y=0, z=1))]),
            ]
        )],
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ANIMATED FLOW DIAGRAM — Advanced Engineering System Layout
# Exact scaled measurements, animated particles, pressure indicators,
# dimension lines, velocity labels, NPSH zones, engineering annotations
# ─────────────────────────────────────────────────────────────────────────────
def animated_flow_diagram(Q_m3h, H_m, D_pipe_mm, L_suction_m, L_discharge_m,
                           z_suction_m, z_discharge_m, th,
                           NPSHa=None, NPSHr=None, eta_p=None,
                           P_sh_kw=None, hf_maj=None, hf_min=None):
    """
    Advanced animated engineering flow diagram.
    Shows: reservoir → suction pipe → pump → discharge pipe → tank
    All dimensions are proportional to actual design values.
    Includes: animated particles, dimension lines, elevation markers,
              pressure zones, velocity labels, NPSH zone, annotations.
    """
    acc  = th["accent"];  acc2 = th["accent2"]
    acc3 = th["accent3"]; acc4 = th.get("accent4", "#ff9f43")
    bg   = th["plot_bg"]; text = th["text"]
    card = th["card_bg"]

    # ── Layout constants (all in metres, diagram coordinates) ─────────────────
    # Reservoir left wall x=0, pump at x=12, discharge tank right x=22
    DATUM   = 0.0          # ground datum y=0
    RES_X0  = 0.0          # reservoir left
    RES_X1  = 3.0          # reservoir right
    RES_Y0  = DATUM - 1.0  # reservoir bottom (1m below datum)
    RES_Y1  = z_suction_m  # reservoir water surface (actual elevation)
    RES_W   = RES_X1 - RES_X0

    PUMP_X  = 12.0         # pump centre x
    PUMP_Y  = DATUM        # pump centre y (at datum level)
    PUMP_R  = 1.1          # pump visual radius

    DT_X0   = 20.0         # discharge tank left
    DT_X1   = 23.0         # discharge tank right
    DT_Y0   = DATUM - 1.0  # discharge tank bottom
    DT_Y1   = z_discharge_m  # discharge tank water surface

    PH      = max(0.18, D_pipe_mm / 1000 * 2.5)  # pipe half-height (visual)
    static_H = z_discharge_m - z_suction_m        # static head

    # Pipe routing:
    # Suction: from reservoir right wall → horizontal → up into pump suction
    SUC_START_X = RES_X1
    SUC_END_X   = PUMP_X - PUMP_R
    SUC_Y       = PUMP_Y   # horizontal suction at pump centreline

    # Discharge: from pump discharge → horizontal → vertical rise → into tank
    DIS_START_X = PUMP_X + PUMP_R
    DIS_RISE_X  = DT_X0 - 0.5   # x where pipe rises
    DIS_Y       = PUMP_Y         # horizontal part at datum
    DIS_Y_TOP   = DT_Y1          # pipe enters tank at water level

    # ── Helper ────────────────────────────────────────────────────────────────
    def rgba_local(hex6, alpha):
        h = hex6.lstrip("#")
        r, gv, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"rgba({r},{gv},{b},{alpha})"

    C_WATER   = "#4fc3f7"   # water blue
    C_PRES    = "#ef5350"   # high pressure red
    C_SUC     = "#26c6da"   # suction cyan
    C_PUMP    = acc
    C_DIM     = "#ffd740"   # dimension yellow
    C_NPSH    = "#ff7043"   # NPSH warning orange
    C_SAFE    = "#66bb6a"   # safe green

    # ── Particle path definition ──────────────────────────────────────────────
    # Path segments: (x_start, y_start, x_end, y_end, color)
    path_segments = [
        # 1. Through reservoir (vertical drop to suction opening)
        (RES_X1 - 0.3, RES_Y1, RES_X1 - 0.3, PUMP_Y, C_WATER),
        # 2. Suction pipe (horizontal)
        (SUC_START_X, SUC_Y, SUC_END_X, SUC_Y, C_SUC),
        # 3. Through pump
        (SUC_END_X, PUMP_Y, DIS_START_X, PUMP_Y, C_PUMP),
        # 4. Discharge pipe horizontal
        (DIS_START_X, DIS_Y, DIS_RISE_X, DIS_Y, C_PRES),
        # 5. Discharge pipe vertical rise
        (DIS_RISE_X, DIS_Y, DIS_RISE_X, DIS_Y_TOP, C_PRES),
        # 6. Into discharge tank
        (DIS_RISE_X, DIS_Y_TOP, DT_X0 + 0.5, DIS_Y_TOP, C_PRES),
    ]

    # Flatten path into (x, y, color) waypoints with cumulative length
    path_pts = []  # list of (x, y, color_idx)
    total_len = 0
    seg_cum = []
    for (x0,y0,x1,y1,col) in path_segments:
        seg_len = math.sqrt((x1-x0)**2 + (y1-y0)**2)
        seg_cum.append((total_len, total_len+seg_len, x0,y0,x1,y1,col))
        total_len += seg_len

    def path_point(s):
        """Given arc length s (0..total_len), return (x, y, color)."""
        s = s % total_len
        for (s0, s1, x0,y0,x1,y1,col) in seg_cum:
            if s0 <= s <= s1:
                frac = (s - s0) / max(s1-s0, 1e-9)
                return x0 + frac*(x1-x0), y0 + frac*(y1-y0), col
        return path_pts[-1] if path_pts else (0,0,"#fff")

    # ── Build animation frames ────────────────────────────────────────────────
    n_frames    = 50
    n_particles = 18
    speed       = total_len / n_frames * 1.5   # advance per frame

    # Particle colour zones: suction = blue, pump = accent, discharge = red
    def particle_color(x, y):
        if x < PUMP_X - PUMP_R:
            return C_SUC
        elif x <= PUMP_X + PUMP_R:
            return C_PUMP
        else:
            return C_PRES

    frames = []
    for fi in range(n_frames):
        pts_x, pts_y, pts_c, pts_sz = [], [], [], []
        for pi in range(n_particles):
            s = (fi * speed + pi * total_len / n_particles) % total_len
            px, py, pc = path_point(s)
            pts_x.append(px)
            pts_y.append(py)
            pts_c.append(particle_color(px, py))
            # Particles bigger inside pump
            in_pump = (PUMP_X - PUMP_R) <= px <= (PUMP_X + PUMP_R)
            pts_sz.append(14 if in_pump else 9)

        frames.append(go.Frame(
            data=[go.Scatter(
                x=pts_x, y=pts_y,
                mode="markers",
                marker=dict(
                    size=pts_sz,
                    color=pts_c,
                    line=dict(width=1.5, color="white"),
                    opacity=0.92,
                ),
                name="Fluid flow",
                hovertemplate="Flow particle<br>x=%.1f m, z=%.1f m<extra></extra>",
            )],
            name=str(fi),
        ))

    # ── Static shapes ─────────────────────────────────────────────────────────
    shapes = [
        # ── Ground / Datum line ──
        dict(type="line", x0=-0.5, x1=24, y0=DATUM-1.0, y1=DATUM-1.0,
             line=dict(color=rgba_local(text,0.25), width=1.5, dash="dot")),

        # ── Reservoir walls ──
        dict(type="rect",
             x0=RES_X0, x1=RES_X1, y0=RES_Y0, y1=RES_Y1+1.5,
             fillcolor=rgba_local(acc2, 0.08),
             line=dict(color=acc2, width=2.5)),

        # ── Reservoir water body ──
        dict(type="rect",
             x0=RES_X0+0.12, x1=RES_X1-0.12,
             y0=RES_Y0+0.1, y1=RES_Y1,
             fillcolor=rgba_local(C_WATER, 0.28),
             line=dict(color=C_WATER, width=1)),

        # ── Water surface wave line (reservoir) ──
        dict(type="line",
             x0=RES_X0+0.12, x1=RES_X1-0.12,
             y0=RES_Y1, y1=RES_Y1,
             line=dict(color=C_WATER, width=2.5, dash="solid")),

        # ── Suction pipe (horizontal) ──
        dict(type="rect",
             x0=SUC_START_X, x1=SUC_END_X,
             y0=SUC_Y-PH, y1=SUC_Y+PH,
             fillcolor=rgba_local(C_SUC, 0.22),
             line=dict(color=C_SUC, width=2)),

        # ── Pump body (outer casing) ──
        dict(type="circle",
             x0=PUMP_X-PUMP_R, x1=PUMP_X+PUMP_R,
             y0=PUMP_Y-PUMP_R, y1=PUMP_Y+PUMP_R,
             fillcolor=rgba_local(C_PUMP, 0.20),
             line=dict(color=C_PUMP, width=3.5)),

        # ── Pump inner (impeller area) ──
        dict(type="circle",
             x0=PUMP_X-PUMP_R*0.55, x1=PUMP_X+PUMP_R*0.55,
             y0=PUMP_Y-PUMP_R*0.55, y1=PUMP_Y+PUMP_R*0.55,
             fillcolor=rgba_local(acc4, 0.30),
             line=dict(color=acc4, width=2)),

        # ── Pump shaft (vertical line) ──
        dict(type="line",
             x0=PUMP_X, x1=PUMP_X,
             y0=PUMP_Y+PUMP_R, y1=PUMP_Y+PUMP_R+1.2,
             line=dict(color=rgba_local(text,0.6), width=4)),

        # ── Motor coupling box ──
        dict(type="rect",
             x0=PUMP_X-0.35, x1=PUMP_X+0.35,
             y0=PUMP_Y+PUMP_R+1.2, y1=PUMP_Y+PUMP_R+1.9,
             fillcolor=rgba_local(text, 0.12),
             line=dict(color=rgba_local(text, 0.5), width=2)),

        # ── Discharge pipe (horizontal) ──
        dict(type="rect",
             x0=DIS_START_X, x1=DIS_RISE_X,
             y0=DIS_Y-PH, y1=DIS_Y+PH,
             fillcolor=rgba_local(C_PRES, 0.22),
             line=dict(color=C_PRES, width=2)),

        # ── Discharge pipe (vertical rise) ──
        dict(type="rect",
             x0=DIS_RISE_X-PH, x1=DIS_RISE_X+PH,
             y0=DIS_Y, y1=DIS_Y_TOP,
             fillcolor=rgba_local(C_PRES, 0.22),
             line=dict(color=C_PRES, width=2)),

        # ── Discharge pipe top horizontal (into tank) ──
        dict(type="rect",
             x0=DIS_RISE_X, x1=DT_X0+0.5,
             y0=DIS_Y_TOP-PH, y1=DIS_Y_TOP+PH,
             fillcolor=rgba_local(C_PRES, 0.22),
             line=dict(color=C_PRES, width=2)),

        # ── Discharge tank walls ──
        dict(type="rect",
             x0=DT_X0, x1=DT_X1,
             y0=DT_Y0, y1=DT_Y1+1.5,
             fillcolor=rgba_local(acc3, 0.08),
             line=dict(color=acc3, width=2.5)),

        # ── Discharge tank water body ──
        dict(type="rect",
             x0=DT_X0+0.12, x1=DT_X1-0.12,
             y0=DT_Y0+0.1, y1=DT_Y1,
             fillcolor=rgba_local(C_PRES, 0.22),
             line=dict(color=C_PRES, width=1)),

        # ── Discharge tank water surface ──
        dict(type="line",
             x0=DT_X0+0.12, x1=DT_X1-0.12,
             y0=DT_Y1, y1=DT_Y1,
             line=dict(color=C_PRES, width=2.5)),

        # ── NPSH zone highlight on suction pipe ──
        dict(type="rect",
             x0=SUC_START_X+0.3, x1=SUC_END_X-0.1,
             y0=SUC_Y-PH*1.6, y1=SUC_Y+PH*1.6,
             fillcolor=rgba_local(C_NPSH, 0.07),
             line=dict(color=C_NPSH, width=1, dash="dot")),

        # ── Static head dimension line (vertical, right side) ──
        dict(type="line",
             x0=23.5, x1=23.5, y0=z_suction_m, y1=z_discharge_m,
             line=dict(color=C_DIM, width=2, dash="dash")),
        dict(type="line", x0=23.2, x1=23.8, y0=z_suction_m, y1=z_suction_m,
             line=dict(color=C_DIM, width=1.5)),
        dict(type="line", x0=23.2, x1=23.8, y0=z_discharge_m, y1=z_discharge_m,
             line=dict(color=C_DIM, width=1.5)),

        # ── Pump elevation arrows (suction head) ──
        dict(type="line",
             x0=-0.8, x1=-0.8, y0=DATUM-1.0, y1=z_suction_m,
             line=dict(color=C_SUC, width=2, dash="dash")),
        dict(type="line", x0=-1.1, x1=-0.5, y0=z_suction_m, y1=z_suction_m,
             line=dict(color=C_SUC, width=1.5)),
        dict(type="line", x0=-1.1, x1=-0.5, y0=DATUM-1.0, y1=DATUM-1.0,
             line=dict(color=C_SUC, width=1.5)),
    ]

    # ── Pipe centreline dashes ─────────────────────────────────────────────────
    shapes += [
        dict(type="line",
             x0=SUC_START_X, x1=SUC_END_X, y0=SUC_Y, y1=SUC_Y,
             line=dict(color=rgba_local(C_SUC, 0.5), width=1, dash="dot")),
        dict(type="line",
             x0=DIS_START_X, x1=DIS_RISE_X, y0=DIS_Y, y1=DIS_Y,
             line=dict(color=rgba_local(C_PRES, 0.5), width=1, dash="dot")),
    ]

    # ── Impeller blades (5 curved lines inside pump circle) ──────────────────
    for bi in range(5):
        ang = bi * 72
        ar  = math.radians(ang)
        x0b = PUMP_X + PUMP_R*0.22*math.cos(ar)
        y0b = PUMP_Y + PUMP_R*0.22*math.sin(ar)
        x1b = PUMP_X + PUMP_R*0.52*math.cos(ar + math.radians(38))
        y1b = PUMP_Y + PUMP_R*0.52*math.sin(ar + math.radians(38))
        shapes.append(dict(type="line", x0=x0b, x1=x1b, y0=y0b, y1=y1b,
                           line=dict(color=acc4, width=2.5)))

    # ── Pressure gradient color bar on discharge pipe ─────────────────────────
    # Gradient effect using multiple small rects
    n_grad = 12
    for gi in range(n_grad):
        alpha = 0.07 + 0.18 * gi/n_grad
        x0g = DIS_START_X + gi*(DIS_RISE_X-DIS_START_X)/n_grad
        x1g = DIS_START_X + (gi+1)*(DIS_RISE_X-DIS_START_X)/n_grad
        shapes.append(dict(type="rect", x0=x0g, x1=x1g,
                           y0=DIS_Y-PH, y1=DIS_Y+PH,
                           fillcolor=rgba_local(C_PRES, alpha),
                           line=dict(width=0)))

    # ── Annotations ───────────────────────────────────────────────────────────
    v_pipe = Q_m3h / 3600 / (math.pi*(D_pipe_mm/1000)**2/4)  # m/s

    annots = [
        # ── Reservoir label ──
        dict(x=RES_X0+RES_W/2, y=RES_Y1+1.0,
             text=f"<b>SUCTION RESERVOIR</b><br>z_s = {z_suction_m:.2f} m",
             showarrow=False, font=dict(color=acc2, size=11, family="JetBrains Mono"),
             bgcolor=rgba_local(card, 0.88), bordercolor=acc2, borderwidth=1,
             borderpad=4),

        # ── Water surface elevation (reservoir) ──
        dict(x=RES_X1+0.4, y=RES_Y1,
             text=f"▼ z = {z_suction_m:.2f} m",
             showarrow=False, font=dict(color=C_WATER, size=10),
             xanchor="left"),

        # ── Discharge tank label ──
        dict(x=DT_X0+(DT_X1-DT_X0)/2, y=DT_Y1+1.0,
             text=f"<b>DISCHARGE TANK</b><br>z_d = {z_discharge_m:.2f} m",
             showarrow=False, font=dict(color=acc3, size=11, family="JetBrains Mono"),
             bgcolor=rgba_local(card, 0.88), bordercolor=acc3, borderwidth=1,
             borderpad=4),

        # ── Discharge water surface elevation ──
        dict(x=DT_X0-0.4, y=DT_Y1,
             text=f"▼ z = {z_discharge_m:.2f} m",
             showarrow=False, font=dict(color=C_PRES, size=10),
             xanchor="right"),

        # ── Pump label (centre) ──
        dict(x=PUMP_X, y=PUMP_Y,
             text=f"<b>PUMP</b>",
             showarrow=False, font=dict(color=C_PUMP, size=12, family="JetBrains Mono")),

        # ── Pump specs box ──
        dict(x=PUMP_X, y=PUMP_Y - PUMP_R - 0.8,
             text=(f"Q = {Q_m3h:.1f} m³/h<br>"
                   f"H = {H_m:.2f} m<br>"
                   f"η = {(eta_p or 0)*100:.1f}%<br>"
                   f"P = {P_sh_kw:.2f} kW" if P_sh_kw else
                   f"Q = {Q_m3h:.1f} m³/h<br>H = {H_m:.2f} m"),
             showarrow=True, ax=0, ay=40,
             arrowhead=2, arrowcolor=C_PUMP, arrowwidth=1.5,
             font=dict(color=C_PUMP, size=10, family="JetBrains Mono"),
             bgcolor=rgba_local(card, 0.92), bordercolor=C_PUMP,
             borderwidth=1.5, borderpad=5),

        # ── Motor label ──
        dict(x=PUMP_X, y=PUMP_Y+PUMP_R+1.55,
             text="⚡ MOTOR",
             showarrow=False, font=dict(color=rgba_local(text,0.75), size=9),
             bgcolor=rgba_local(text, 0.10)),

        # ── Suction pipe label ──
        dict(x=(SUC_START_X+SUC_END_X)/2, y=SUC_Y-PH-0.45,
             text=f"← SUCTION PIPE  DN{D_pipe_mm:.0f}  L={L_suction_m:.1f}m  v={v_pipe:.2f}m/s →",
             showarrow=False, font=dict(color=C_SUC, size=9.5, family="JetBrains Mono")),

        # ── Discharge pipe label ──
        dict(x=(DIS_START_X+DIS_RISE_X)/2, y=DIS_Y-PH-0.45,
             text=f"→ DISCHARGE PIPE  DN{D_pipe_mm:.0f}  L={L_discharge_m:.1f}m  v={v_pipe:.2f}m/s →",
             showarrow=False, font=dict(color=C_PRES, size=9.5, family="JetBrains Mono")),

        # ── Static head dimension ──
        dict(x=23.8, y=(z_suction_m+z_discharge_m)/2,
             text=f"<b>H_static<br>= {static_H:.2f} m</b>",
             showarrow=False, font=dict(color=C_DIM, size=10, family="JetBrains Mono"),
             xanchor="left"),

        # ── TDH label ──
        dict(x=PUMP_X+PUMP_R+1.0, y=PUMP_Y+H_m*0.18,
             text=f"<b>TDH = {H_m:.2f} m</b>",
             showarrow=True, ax=-30, ay=-40,
             arrowhead=2, arrowcolor=C_DIM, arrowwidth=1.5,
             font=dict(color=C_DIM, size=11, family="JetBrains Mono"),
             bgcolor=rgba_local(card, 0.88), bordercolor=C_DIM, borderwidth=1.5),

        # ── Friction loss label ──
        dict(x=(SUC_START_X+DIS_RISE_X)/2, y=SUC_Y+PH+0.5,
             text=f"h_f = {(hf_maj or 0)+(hf_min or 0):.3f} m  (Major: {hf_maj or 0:.3f} + Minor: {hf_min or 0:.3f})",
             showarrow=False, font=dict(color=rgba_local(text,0.65), size=9)),

        # ── NPSH zone label ──
        dict(x=(SUC_START_X+SUC_END_X)/2, y=SUC_Y+PH+0.9,
             text=f"⚠ NPSH Zone  |  NPSHa={NPSHa:.2f}m  NPSHr={NPSHr:.2f}m" if NPSHa and NPSHr else "NPSH Zone",
             showarrow=False, font=dict(color=C_NPSH, size=9.5)),

        # ── Datum label ──
        dict(x=0, y=DATUM-1.15,
             text="──── DATUM z = 0 ────",
             showarrow=False, font=dict(color=rgba_local(text,0.4), size=9)),

        # ── Suction head dimension ──
        dict(x=-1.5, y=(DATUM-1.0 + z_suction_m)/2,
             text=f"h_s<br>={z_suction_m:.2f}m",
             showarrow=False, font=dict(color=C_SUC, size=9, family="JetBrains Mono"),
             xanchor="right"),

        # ── High pressure marker ──
        dict(x=DIS_RISE_X-0.5, y=DIS_Y+PH+0.9,
             text="🔴 HIGH PRESSURE",
             showarrow=False, font=dict(color=C_PRES, size=9.5)),

        # ── Low pressure marker ──
        dict(x=SUC_END_X-1.5, y=SUC_Y+PH+0.9,
             text="🔵 LOW PRESSURE",
             showarrow=False, font=dict(color=C_SUC, size=9.5)),
    ]

    # ── NPSH safety badge ─────────────────────────────────────────────────────
    if NPSHa and NPSHr:
        margin   = NPSHa - NPSHr
        npsh_ok  = margin >= 0.5
        npsh_col = C_SAFE if npsh_ok else C_NPSH
        npsh_sym = "✅" if npsh_ok else "⚠️"
        annots.append(dict(
            x=PUMP_X, y=PUMP_Y+PUMP_R+0.35,
            text=f"{npsh_sym} NPSHa-NPSHr = {margin:.2f} m",
            showarrow=False,
            font=dict(color=npsh_col, size=9.5, family="JetBrains Mono"),
            bgcolor=rgba_local(card, 0.85), bordercolor=npsh_col,
            borderwidth=1, borderpad=3,
        ))

    # ── Initial frame data (static frame 0) ───────────────────────────────────
    init_x, init_y, init_c = [], [], []
    for pi in range(n_particles):
        s  = pi * total_len / n_particles
        px, py, pc = path_point(s)
        init_x.append(px); init_y.append(py); init_c.append(pc)

    # ── Y-axis range ──────────────────────────────────────────────────────────
    y_min = min(RES_Y0, DT_Y0, DATUM-1.5)
    y_max = max(RES_Y1, DT_Y1, PUMP_Y+PUMP_R+2.5) + 1.5

    fig = go.Figure(
        data=[go.Scatter(
            x=init_x, y=init_y,
            mode="markers",
            marker=dict(size=9, color=init_c,
                        line=dict(width=1.5, color="white"), opacity=0.92),
            name="Fluid particles",
            hovertemplate="Flow particle<br>x=%.1f m  z=%.1f m<extra></extra>",
        )],
        frames=frames,
        layout=go.Layout(
            title=dict(
                text=(f"🌊 ANIMATED SYSTEM FLOW DIAGRAM — {Q_m3h:.1f} m³/h  |  "
                      f"TDH = {H_m:.2f} m  |  DN{D_pipe_mm:.0f}  |  "
                      f"H_static = {static_H:.2f} m  |  v = {v_pipe:.2f} m/s"),
                font=dict(size=13, color=acc, family="JetBrains Mono"), x=0.5,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=bg,
            height=600,
            shapes=shapes,
            annotations=annots,
            xaxis=dict(
                range=[-2.5, 25],
                title="Horizontal Distance (m)",
                showgrid=True, gridcolor=rgba_local(text, 0.07),
                color=text, zeroline=False,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                range=[y_min - 0.5, y_max],
                title="Elevation / Height (m)",
                color=text,
                showgrid=True, gridcolor=rgba_local(text, 0.07),
                tickfont=dict(size=10),
                zeroline=True, zerolinecolor=rgba_local(text, 0.2),
                zerolinewidth=1.5,
            ),
            font=dict(color=text, size=10),
            legend=dict(
                font=dict(color=text, size=10),
                bgcolor=rgba_local(card, 0.5),
                x=0.01, y=0.01,
            ),
            margin=dict(l=60, r=80, t=55, b=50),
            updatemenus=[dict(
                type="buttons", showactive=False,
                x=0.38, y=1.06, xanchor="left",
                bgcolor=rgba_local(acc, 0.15),
                bordercolor=acc, font=dict(color=text, size=11),
                buttons=[
                    dict(label="▶  Play",
                         method="animate",
                         args=[None, dict(
                             frame=dict(duration=60, redraw=True),
                             fromcurrent=True,
                             transition=dict(duration=0))]),
                    dict(label="⏸  Pause",
                         method="animate",
                         args=[[None], dict(
                             frame=dict(duration=0, redraw=False),
                             mode="immediate",
                             transition=dict(duration=0))]),
                ],
            )],
            sliders=[dict(
                steps=[dict(
                    args=[[f.name], dict(frame=dict(duration=0, redraw=True),
                                        mode="immediate")],
                    method="animate", label="",
                ) for f in frames],
                active=0,
                x=0.38, y=0.0, len=0.62,
                currentvalue=dict(prefix="", font=dict(color=rgba_local(text,0.5))),
                bgcolor=rgba_local(acc, 0.15),
                bordercolor=rgba_local(acc, 0.3),
                tickcolor=rgba_local(text, 0.3),
            )],
        ),
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# IMPELLER 2D VELOCITY TRIANGLE DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────
def velocity_triangle_plot(u1, u2, Cm1, Cm2, Cu2, beta1, beta2, th):
    """
    Velocity triangles at impeller inlet and outlet.
    Classic Karassik / Stepanoff representation.
    """
    acc  = th["accent"]; acc2 = th["accent2"]; acc3 = th["accent3"]
    bg   = th["plot_bg"]; text = th["text"]

    fig = make_subplots(rows=1, cols=2,
                         subplot_titles=("Inlet Velocity Triangle", "Outlet Velocity Triangle"))

    def add_triangle(row, u, Cm, Cu, beta_deg, label):
        # Absolute velocity V = sqrt(Cm^2 + Cu^2)
        V   = math.sqrt(Cm**2 + Cu**2)
        # Relative velocity W
        W   = math.sqrt(Cm**2 + (u - Cu)**2)
        # Origin at (0,0)
        # u vector: horizontal (peripheral speed)
        # V vector: absolute velocity
        # W vector: relative velocity

        vectors = [
            ("u (peripheral)", 0,0, u,0,      acc,  4),
            ("V (absolute)",   0,0, Cu,Cm,     acc2, 3),
            ("W (relative)",   Cu,Cm, u,0,     acc3, 3),  # W = u - V
            ("Cm (meridional)",0,0, 0,Cm,      "#ffd740", 2),
        ]
        for vname, x0,y0,x1,y1,color,width in vectors:
            fig.add_trace(go.Scatter(
                x=[x0,x1], y=[y0,y1], mode="lines+markers",
                line=dict(color=color, width=width),
                marker=dict(size=[4,8], color=color, symbol=["circle","arrow"]),
                name=vname if row==1 else "",
                showlegend=(row==1),
                hovertemplate=f"{vname}: {math.sqrt((x1-x0)**2+(y1-y0)**2):.2f} m/s<extra></extra>"
            ), row=1, col=row)

        # Labels
        fig.add_annotation(x=u/2, y=-0.3, text=f"u={u:.2f}m/s",
                           font=dict(color=acc,size=10), showarrow=False, row=1, col=row)
        fig.add_annotation(x=Cu/2-0.1, y=Cm/2, text=f"V={V:.2f}m/s",
                           font=dict(color=acc2,size=10), showarrow=False, row=1, col=row)
        fig.add_annotation(x=(Cu+u)/2, y=Cm/2, text=f"W={W:.2f}m/s\nβ={beta_deg:.1f}°",
                           font=dict(color=acc3,size=10), showarrow=False, row=1, col=row)

    add_triangle(1, u1, Cm1, 0,   beta1, "Inlet")
    add_triangle(2, u2, Cm2, Cu2, beta2, "Outlet")

    fig.update_layout(
        template="plotly_dark" if bg.startswith("#0") else "plotly_white",
        title=dict(text="Impeller Velocity Triangles (Euler / Stepanoff Method)",
                   font=dict(color=acc, size=14), x=0.5),
        height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=bg,
        font=dict(color=text),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=text)),
    )
    for ann in fig.layout.annotations:
        ann.font.color = acc
    return fig
