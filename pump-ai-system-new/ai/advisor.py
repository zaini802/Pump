# =============================================================================
# ai/advisor.py
# AI Engineering Advisor — orchestrates Groq calls
# =============================================================================
from ai.groq_client import ask
from ai.prompts import (SYSTEM_PROMPT, selection_prompt,
                        cavitation_prompt, general_question_prompt)

def get_selection_advice(client, pump_type, Q_m3h, H_m, mu_cP, rho, fluid, ranking):
    user_msg = selection_prompt(pump_type, Q_m3h, H_m, mu_cP, rho, fluid, ranking)
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": user_msg},
    ]
    return ask(client, messages)

def get_cavitation_advice(client, NPSHa, NPSHr, margin, pump_type):
    user_msg = cavitation_prompt(NPSHa, NPSHr, margin, pump_type)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]
    return ask(client, messages)

def ask_question(client, question, pump_type, Q_m3h, H_m):
    user_msg = general_question_prompt(question, pump_type, Q_m3h, H_m)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]
    return ask(client, messages)
