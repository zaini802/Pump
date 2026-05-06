# =============================================================================
# ai/groq_client.py
# Groq API connection (FREE LLM — Llama-3 / Mixtral)
# Get free key: https://console.groq.com
# =============================================================================
import os
import ssl

# ── SSL FIX: SSL_CERT_FILE env var points to a missing file in some conda envs ──
# Remove it so httpx/Groq falls back to the system default SSL bundle.
_bad_ssl = os.environ.get("SSL_CERT_FILE", "")
if _bad_ssl and not os.path.isfile(_bad_ssl):
    del os.environ["SSL_CERT_FILE"]

# Same fix for REQUESTS_CA_BUNDLE if present
_bad_ca = os.environ.get("REQUESTS_CA_BUNDLE", "")
if _bad_ca and not os.path.isfile(_bad_ca):
    del os.environ["REQUESTS_CA_BUNDLE"]

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

def get_client(api_key: str = None):
    if not _GROQ_AVAILABLE:
        return None
    key = api_key or os.environ.get("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        return Groq(api_key=key)
    except FileNotFoundError:
        # Last resort: unset all SSL overrides and retry
        for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
            os.environ.pop(var, None)
        return Groq(api_key=key)

def ask(client, messages: list, model="llama-3.3-70b-versatile", max_tokens=700) -> str:
    """
    Call Groq LLM API.
    Default model: llama-3.3-70b-versatile (Groq recommended, 2025)
    Fallback chain: llama-3.3-70b-versatile → llama-3.1-8b-instant → gemma2-9b-it
    Ref: https://console.groq.com/docs/deprecations
    """
    if client is None:
        return "⚠️ AI unavailable — enter a Groq API key in the sidebar to enable AI advisor."

    FALLBACK_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
    ]

    # If caller passed an old decommissioned model, override with primary
    if model in ("llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"):
        model = FALLBACK_MODELS[0]

    last_err = None
    for attempt_model in [model] + [m for m in FALLBACK_MODELS if m != model]:
        try:
            resp = client.chat.completions.create(
                model=attempt_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            err_str = str(e)
            # Only fallback on model-related errors
            if "decommissioned" in err_str or "model_not_found" in err_str or "404" in err_str:
                continue
            # Other errors (auth, rate limit etc) — return immediately
            return f"⚠️ AI error: {e}"

    return f"⚠️ AI error (all models failed): {last_err}"
