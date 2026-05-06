# =============================================================================
# ai/prompts.py
# System + engineering prompts for Groq AI
# =============================================================================

SYSTEM_PROMPT = """You are a Senior Process & Mechanical Engineer with 25+ years of experience 
in industrial pump design, selection, and troubleshooting. You follow API, ISO, and HI standards.

Rules:
- Give concise, practical engineering advice (3-6 sentences max per point)
- Cite references when possible (Perry's, API, HI, Karassik)
- Flag safety concerns clearly
- Never replace physics calculations — only advise and explain
- Use bullet points for clarity
- Avoid repetition
"""

def selection_prompt(pump_type, Q_m3h, H_m, mu_cP, rho, fluid, ranking):
    top = ranking[0][0] if ranking else pump_type
    match = "✅ matches recommended" if pump_type == top else f"⚠️ differs from recommended ({top})"
    return f"""
Process conditions:
- Selected pump: {pump_type} ({match})
- Flow: {Q_m3h:.1f} m³/h | Head: {H_m:.1f} m
- Fluid: {fluid} | Viscosity: {mu_cP:.1f} cP | Density: {rho:.0f} kg/m³

Please:
1. Validate if this pump selection is correct for these conditions
2. Highlight any risks or limitations
3. Suggest improvements if needed
4. Mention relevant standard (API/HI/ISO)
"""

def cavitation_prompt(NPSHa, NPSHr, margin, pump_type):
    return f"""
NPSH Analysis for {pump_type}:
- NPSHa = {NPSHa:.2f} m
- NPSHr = {NPSHr:.2f} m  
- Margin = {margin:.2f} m

{"CAVITATION RISK DETECTED" if margin < 0.5 else "NPSH appears adequate"}.

Explain:
1. What this means physically
2. What will happen if cavitation occurs
3. How to fix it (3 specific solutions)
4. Reference the HI standard requirement
"""

def general_question_prompt(question, pump_type, Q_m3h, H_m):
    return f"""
Context: {pump_type} pump | Flow: {Q_m3h:.1f} m³/h | Head: {H_m:.1f} m

Engineer's question: {question}

Answer concisely as a senior pump engineer. Be specific and practical.
"""
