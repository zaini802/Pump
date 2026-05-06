# =============================================================================
# utils/fittings.py
# Pipe Fitting K-value Database — Crane Technical Paper No. 410
# Reference: Crane TP-410 (2013), Perry's Ch.6, Idelchik (1994)
# =============================================================================

# ── FITTING DATABASE ──────────────────────────────────────────────────────────
# Format: { category: { fitting_name: { K: float, desc: str, icon: str } } }
FITTINGS = {
    "🔵 Elbows & Bends": {
        "90° Elbow (Standard)":         {"K": 0.75,  "desc": "Standard radius R/D≈1, screwed or flanged"},
        "90° Elbow (Long Radius)":      {"K": 0.45,  "desc": "Long radius R/D≈1.5, lower loss"},
        "90° Elbow (Mitered 1 cut)":    {"K": 1.50,  "desc": "Sharp mitered 90° bend — 1 weld cut"},
        "45° Elbow (Standard)":         {"K": 0.35,  "desc": "Standard 45° bend"},
        "45° Elbow (Long Radius)":      {"K": 0.20,  "desc": "Long radius 45° bend"},
        "180° Return Bend (Close)":     {"K": 1.50,  "desc": "Close-pattern U-bend"},
        "180° Return Bend (Open)":      {"K": 0.75,  "desc": "Open-pattern return bend"},
    },
    "🟢 Tees & Branches": {
        "Tee — Flow Through Run":       {"K": 0.40,  "desc": "Flow straight through, branch closed"},
        "Tee — Flow Through Branch":    {"K": 1.00,  "desc": "Flow turned into branch"},
        "Tee — Converging (branch→run)":{"K": 0.80,  "desc": "Branch flow merging into run"},
        "Wye (45°) — Run":              {"K": 0.30,  "desc": "45° wye, flow through main run"},
        "Wye (45°) — Branch":           {"K": 0.50,  "desc": "45° wye, flow through branch"},
    },
    "🔴 Valves": {
        "Gate Valve (fully open)":      {"K": 0.08,  "desc": "Fully open gate valve — minimal resistance"},
        "Gate Valve (¾ open)":          {"K": 0.90,  "desc": "3/4 open gate valve"},
        "Gate Valve (½ open)":          {"K": 4.50,  "desc": "Half open gate valve — significant loss"},
        "Gate Valve (¼ open)":          {"K": 24.0,  "desc": "Quarter open gate valve — very high loss"},
        "Globe Valve (fully open)":     {"K": 6.00,  "desc": "Globe valve fully open (Crane TP-410)"},
        "Globe Valve (½ open)":         {"K": 9.50,  "desc": "Globe valve half open"},
        "Ball Valve (fully open)":      {"K": 0.05,  "desc": "Full-port ball valve, fully open"},
        "Ball Valve (½ open)":          {"K": 5.50,  "desc": "Ball valve half open"},
        "Butterfly Valve (open)":       {"K": 0.30,  "desc": "Butterfly valve fully open"},
        "Butterfly Valve (10° closed)": {"K": 0.52,  "desc": "Butterfly valve 10° from fully open"},
        "Angle Valve (fully open)":     {"K": 2.00,  "desc": "Angle valve fully open"},
        "Check Valve (Swing)":          {"K": 2.00,  "desc": "Swing check valve — full bore"},
        "Check Valve (Lift)":           {"K": 12.0,  "desc": "Lift (piston) check valve"},
        "Check Valve (Tilting Disc)":   {"K": 1.00,  "desc": "Tilting disc check valve"},
        "Foot Valve (with strainer)":   {"K": 5.00,  "desc": "Foot valve with strainer at pump inlet"},
        "Needle Valve (fully open)":    {"K": 6.00,  "desc": "Needle valve fully open"},
        "Plug Valve (fully open)":      {"K": 0.30,  "desc": "Straight-through plug valve"},
        "Pressure Relief Valve":        {"K": 6.00,  "desc": "Spring-loaded pressure relief valve"},
    },
    "🟡 Pipe Entries & Exits": {
        "Sharp-edged Pipe Entry":       {"K": 0.50,  "desc": "Flush pipe entry into vessel/tank"},
        "Rounded Pipe Entry":           {"K": 0.05,  "desc": "Well-rounded bellmouth entry"},
        "Re-entrant (Borda) Entry":     {"K": 1.00,  "desc": "Projecting pipe into vessel"},
        "Pipe Exit (into tank)":        {"K": 1.00,  "desc": "Pipe discharging into large vessel"},
        "Sudden Contraction (0.5)":     {"K": 0.30,  "desc": "Area ratio A2/A1 = 0.5"},
        "Sudden Expansion (0.5)":       {"K": 0.56,  "desc": "Area ratio A1/A2 = 0.5 (Borda-Carnot)"},
    },
    "🟣 Reducers & Increasers": {
        "Concentric Reducer (gradual)": {"K": 0.05,  "desc": "Gradual concentric reducer, θ<15°"},
        "Concentric Reducer (abrupt)":  {"K": 0.50,  "desc": "Abrupt / sudden contraction"},
        "Eccentric Reducer (flat top)": {"K": 0.10,  "desc": "Eccentric reducer, flat top (no air trap)"},
        "Pipe Enlarger (gradual)":      {"K": 0.10,  "desc": "Gradual expander θ<15°"},
        "Pipe Enlarger (abrupt)":       {"K": 0.60,  "desc": "Abrupt enlargement (Borda-Carnot)"},
    },
    "⚪ Strainers & Filters": {
        "Y-Strainer (clean)":           {"K": 0.80,  "desc": "Y-strainer, clean element (clean)"},
        "Y-Strainer (50% plugged)":     {"K": 2.50,  "desc": "Y-strainer, 50% element blockage"},
        "Basket Strainer (clean)":      {"K": 0.50,  "desc": "Basket strainer, clean"},
        "Basket Strainer (50% plugged)":{"K": 2.00,  "desc": "Basket strainer, 50% blockage"},
        "In-line Filter":               {"K": 1.50,  "desc": "In-line cartridge filter"},
    },
    "🔶 Flow Meters & Instruments": {
        "Orifice Plate (β=0.5)":        {"K": 6.00,  "desc": "Sharp-edged orifice plate, β = d/D = 0.5"},
        "Orifice Plate (β=0.7)":        {"K": 1.50,  "desc": "Sharp-edged orifice plate, β = 0.7"},
        "Venturi Meter":                {"K": 0.30,  "desc": "Venturi tube (overall)"},
        "Flow Nozzle":                  {"K": 0.50,  "desc": "ASME flow nozzle"},
        "Magnetic Flowmeter":           {"K": 0.10,  "desc": "Full-bore electromagnetic meter"},
        "Coriolis Meter":               {"K": 1.50,  "desc": "Coriolis mass flow meter"},
        "Rotameter (variable area)":    {"K": 2.00,  "desc": "In-line variable area meter"},
    },
    "🏭 Process Equipment": {
        "Heat Exchanger (shell&tube)":  {"K": 4.00,  "desc": "Shell-and-tube HX, typical"},
        "Heat Exchanger (plate type)":  {"K": 8.00,  "desc": "Plate heat exchanger, typical"},
        "Pressure Vessel Nozzle":       {"K": 0.50,  "desc": "Vessel nozzle (entry or exit)"},
        "Pump Suction Nozzle":          {"K": 0.50,  "desc": "Suction manifold / nozzle"},
    },
}

# Flat list for easy lookup
ALL_FITTINGS = {}
for cat, items in FITTINGS.items():
    for name, data in items.items():
        ALL_FITTINGS[name] = {**data, "category": cat}

def calc_K_total(selected_fittings: dict) -> tuple:
    """
    selected_fittings: {fitting_name: quantity}
    Returns (K_total, breakdown_list)
    breakdown_list: [ {name, qty, K_each, K_sub} ]
    """
    K_total   = 0.0
    breakdown = []
    for name, qty in selected_fittings.items():
        if qty > 0 and name in ALL_FITTINGS:
            K_each = ALL_FITTINGS[name]["K"]
            K_sub  = K_each * qty
            K_total += K_sub
            breakdown.append({
                "Fitting": name,
                "Category": ALL_FITTINGS[name]["category"],
                "Qty": qty,
                "K each (Crane TP-410)": K_each,
                "K subtotal": round(K_sub, 3),
                "Description": ALL_FITTINGS[name]["desc"],
            })
    return round(K_total, 4), breakdown


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT FITTING SELECTOR WIDGET
# Call this from app.py; it manages its own session_state internally.
# Returns (K_total, selected_list)
# ─────────────────────────────────────────────────────────────────────────────
def fitting_selector_widget(th):
    import streamlit as st

    acc   = th["accent"]
    acc2  = th["accent2"]
    acc3  = th["accent3"]
    card  = th["card_bg"]
    text  = th["text"]
    mlbl  = th["metric_lbl"]
    bg    = th["bg"]

    # ── session state init ────────────────────────────────────────────────────
    if "fitting_list" not in st.session_state:
        st.session_state["fitting_list"] = []   # list of {name, K, qty, desc, cat}

    # ── Layout: left selector | right basket ─────────────────────────────────
    col_sel, col_basket = st.columns([1, 1], gap="large")

    # ══════════════════════════════════════════════════════════════════════════
    # LEFT — Category → Item selector
    # ══════════════════════════════════════════════════════════════════════════
    with col_sel:
        st.markdown(
            f'<div style="font-size:.85rem;font-weight:700;color:{acc};'
            f'margin-bottom:8px;">🗂️ Select Category</div>',
            unsafe_allow_html=True)

        categories = list(FITTINGS.keys())
        chosen_cat = st.radio("Category", categories,
                               label_visibility="collapsed", key="fit_cat_radio")

        st.markdown(
            f'<div style="font-size:.82rem;font-weight:700;color:{acc2};'
            f'margin:10px 0 6px 0;">📦 Items in {chosen_cat}</div>',
            unsafe_allow_html=True)

        items_in_cat = FITTINGS[chosen_cat]

        chosen_item = st.selectbox(
            "Select fitting", list(items_in_cat.keys()),
            label_visibility="collapsed", key="fit_item_sel")

        chosen_data = items_in_cat[chosen_item]
        st.markdown(
            f'<div style="background:{card};border-left:3px solid {acc};'
            f'padding:8px 12px;border-radius:6px;margin:6px 0;">'
            f'<span style="color:{acc};font-weight:700;">K = {chosen_data["K"]}</span>'
            f'<br><span style="color:{text};font-size:.80rem;">{chosen_data["desc"]}</span>'
            f'</div>', unsafe_allow_html=True)

        qty = st.number_input("Quantity", min_value=1, max_value=30,
                               value=1, step=1, key="fit_qty")

        if st.button("➕  Add to List", use_container_width=True, key="fit_add_btn"):
            # Check if already in list — update qty
            existing = [x for x in st.session_state["fitting_list"]
                        if x["name"] == chosen_item]
            if existing:
                existing[0]["qty"] += qty
                existing[0]["K_sub"] = round(existing[0]["K_each"] * existing[0]["qty"], 4)
            else:
                st.session_state["fitting_list"].append({
                    "name": chosen_item,
                    "cat":  chosen_cat,
                    "K_each": chosen_data["K"],
                    "qty":  qty,
                    "K_sub": round(chosen_data["K"] * qty, 4),
                    "desc": chosen_data["desc"],
                })
            st.rerun()

        if st.button("🗑️  Clear All Fittings", use_container_width=True,
                     key="fit_clear_btn", type="secondary"):
            st.session_state["fitting_list"] = []
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # RIGHT — Selected fittings basket
    # ══════════════════════════════════════════════════════════════════════════
    with col_basket:
        fl = st.session_state["fitting_list"]
        K_total = round(sum(x["K_sub"] for x in fl), 4)

        st.markdown(
            f'<div style="font-size:.85rem;font-weight:700;color:{acc};'
            f'margin-bottom:6px;">🧺 Selected Fittings</div>',
            unsafe_allow_html=True)

        if not fl:
            st.markdown(
                f'<div style="background:{card};border-radius:8px;padding:18px;'
                f'text-align:center;color:{mlbl};font-size:.85rem;">'
                f'No fittings added yet.<br>Select from the left and press ➕ Add.</div>',
                unsafe_allow_html=True)
        else:
            # Basket table
            rows_html = ""
            for i, item in enumerate(fl):
                remove_key = f"rm_{i}_{item['name']}"
                rows_html += (
                    f'<tr>'
                    f'<td style="padding:5px 8px;color:{text};font-size:.82rem;">'
                    f'{item["name"]}</td>'
                    f'<td style="padding:5px 8px;text-align:center;color:{acc2};'
                    f'font-weight:700;">{item["qty"]}</td>'
                    f'<td style="padding:5px 8px;text-align:center;color:{mlbl};">'
                    f'{item["K_each"]}</td>'
                    f'<td style="padding:5px 8px;text-align:center;color:{acc};'
                    f'font-weight:700;">{item["K_sub"]}</td>'
                    f'</tr>'
                )
            total_row = (
                f'<tr style="border-top:2px solid {acc};">'
                f'<td colspan="3" style="padding:6px 8px;color:{acc};font-weight:800;'
                f'font-size:.88rem;">Σ K TOTAL</td>'
                f'<td style="padding:6px 8px;text-align:center;color:{acc};'
                f'font-weight:900;font-size:1.05rem;">{K_total}</td>'
                f'</tr>'
            )
            st.markdown(f"""
<div style="background:{card};border-radius:10px;overflow:hidden;
            border:1px solid {acc}33;">
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr style="background:{acc}22;">
        <th style="padding:7px 8px;text-align:left;color:{acc};
                   font-size:.78rem;">Fitting</th>
        <th style="padding:7px 8px;text-align:center;color:{acc};
                   font-size:.78rem;">Qty</th>
        <th style="padding:7px 8px;text-align:center;color:{acc};
                   font-size:.78rem;">K each</th>
        <th style="padding:7px 8px;text-align:center;color:{acc};
                   font-size:.78rem;">K sub</th>
      </tr>
    </thead>
    <tbody>{rows_html}{total_row}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

            # Per-item remove buttons
            st.markdown("<div style='margin-top:6px;'>", unsafe_allow_html=True)
            remove_cols = st.columns(min(len(fl), 3))
            for i, item in enumerate(fl):
                with remove_cols[i % min(len(fl), 3)]:
                    label = item["name"][:20] + "…" if len(item["name"]) > 20 else item["name"]
                    if st.button(f"✕ {label}", key=f"rm_{i}", use_container_width=True):
                        st.session_state["fitting_list"].pop(i)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            # K detail toggle
            with st.expander("📋 View Individual K-values (Crane TP-410)", expanded=False):
                for item in fl:
                    st.markdown(
                        f"**{item['name']}** — `K = {item['K_each']}` × {item['qty']} = "
                        f"`{item['K_sub']}`  \n"
                        f"<span style='color:{mlbl};font-size:.78rem;'>"
                        f"{item['cat']} | {item['desc']}</span>",
                        unsafe_allow_html=True)

        # Save to session_state for sidebar + calculations
        st.session_state["K_fit_total"] = K_total

    return K_total, st.session_state["fitting_list"]
