"""
double_agent.py — chiama ALTRE AI (GPT-5, DeepSeek, Gemini) con un prompt e ne salva la risposta.

Serve al protocollo DOUBLE AGENT: Claude genera un prompt-bomba, lo manda a modelli di FAMIGLIE
diverse (per prospettiva vera, non la stessa di Claude), e legge le risposte. Tutto automatico.

CFO: ogni chiamata costa centesimi. Chiavi da .env (mai in codice).
"""
import os, json, urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _post(url, headers, body, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={**headers, "Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def ask_gpt5(prompt, max_tokens=6000, timeout=300):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    r = _post("https://api.openai.com/v1/chat/completions",
              {"Authorization": f"Bearer {key}"},
              {"model": "gpt-5", "messages": [{"role": "user", "content": prompt}],
               "max_completion_tokens": max_tokens}, timeout=timeout)
    return r["choices"][0]["message"]["content"]


def ask_deepseek(prompt, max_tokens=6000, timeout=300):
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        return None
    r = _post("https://api.deepseek.com/chat/completions",
              {"Authorization": f"Bearer {key}"},
              {"model": "deepseek-reasoner", "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens}, timeout=timeout)
    return r["choices"][0]["message"]["content"]


def ask_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    r = _post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
              {}, {"contents": [{"parts": [{"text": prompt}]}]})
    return r["candidates"][0]["content"]["parts"][0]["text"]


def ask_grok(prompt, max_tokens=2000, timeout=120, live_x=True):
    """Grok (xAI) — ha X/Twitter INTEGRATO in tempo reale e cerca su X da solo (agentico).
    E' la nostra fonte del segnale TREND/virale a costo basso. None se manca XAI_API_KEY.
    (live_x tenuto per compat; Grok-4 cerca comunque su X nativamente)."""
    key = os.getenv("XAI_API_KEY")
    if not key:
        return None
    body = {"model": os.getenv("GROK_MODEL", "grok-4-1-fast"),
            "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    r = _post("https://api.x.ai/v1/chat/completions",
              {"Authorization": f"Bearer {key}"}, body, timeout=timeout)
    return r["choices"][0]["message"]["content"]


MODELS = {"gpt5": ask_gpt5, "deepseek": ask_deepseek, "gemini": ask_gemini, "grok": ask_grok}


def consult(prompt, models=("gpt5", "deepseek")):
    """Manda il prompt ai modelli scelti. Ritorna {model: risposta}."""
    out = {}
    for m in models:
        try:
            print(f"[double-agent] chiamo {m}...")
            out[m] = MODELS[m](prompt)
            print(f"[double-agent] {m}: {len(out[m] or '')} char")
        except Exception as e:
            out[m] = None
            print(f"[double-agent] {m} errore: {str(e)[:150]}")
    return out
