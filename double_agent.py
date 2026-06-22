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


def ask_grok(prompt, max_tokens=3000, timeout=240, live_x=True):
    """Grok (xAI) con RICERCA LIVE su X. Usa /v1/responses + tool x_search (il vecchio
    search_parameters e' stato ritirato -> 410). Con live_x Grok cerca DAVVERO su X in tempo
    reale (non dalla memoria di training). E' la nostra fonte del segnale virale. None se manca la key."""
    key = os.getenv("XAI_API_KEY")
    if not key:
        return None
    body = {"model": os.getenv("GROK_MODEL", "grok-4.3"),
            "input": [{"role": "user", "content": prompt}],
            "max_output_tokens": max_tokens}
    if live_x:
        body["tools"] = [{"type": "x_search"}]      # ricerca live su X (server-side, agentica)
    r = _post("https://api.x.ai/v1/responses",
              {"Authorization": f"Bearer {key}"}, body, timeout=timeout)
    for item in reversed(r.get("output", [])):       # il messaggio finale e' l'ultimo 'message'
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("text"):
                    return c["text"]
    return None


def ask_glm(prompt, max_tokens=6000, timeout=300):
    """GLM (Zhipu AI, modello cinese) — molto forte e a basso costo. OpenAI-compatibile.
    Key da GLM_API_KEY. Model ed endpoint configurabili (GLM_MODEL, GLM_BASE_URL) cosi' si setta
    l'ID esatto senza toccare il codice. None se manca la key."""
    key = os.getenv("GLM_API_KEY") or os.getenv("COMETAPI_API_KEY")
    if not key:
        return None
    base = os.getenv("GLM_BASE_URL", "https://api.cometapi.com/v1/chat/completions")
    r = _post(base,
              {"Authorization": f"Bearer {key}"},
              {"model": os.getenv("GLM_MODEL", "glm-5.2"), "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens}, timeout=timeout)
    return r["choices"][0]["message"]["content"]


MODELS = {"gpt5": ask_gpt5, "deepseek": ask_deepseek, "gemini": ask_gemini, "grok": ask_grok, "glm": ask_glm}


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
