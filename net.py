"""
net.py — rete con freni.

Il punto debole di questi progetti sono i COSTI / rate limit. Qui c'e' un
rate limiter semplice (token-bucket per minuto) e retry con backoff, cosi'
nessun job puo' martellare un'API gratuita e farti bannare o farti pagare.
"""
import time
import threading
import requests
from config import LIMITS


class RateLimiter:
    """Massimo N chiamate al minuto, thread-safe. Se sfori, aspetta."""
    def __init__(self, calls_per_min):
        self.capacity = calls_per_min
        self.tokens = calls_per_min
        self.refill_rate = calls_per_min / 60.0
        self.last = time.time()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_rate)
            self.last = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.refill_rate
                time.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1


def get_json(url, limiter: RateLimiter, params=None):
    """GET con rate limit + retry/backoff. Ritorna dict o None."""
    headers = {"User-Agent": LIMITS["user_agent"]}
    for attempt in range(LIMITS["max_retries"]):
        if limiter:
            limiter.acquire()
        try:
            r = requests.get(url, params=params, headers=headers,
                             timeout=LIMITS["http_timeout"])
            if r.status_code == 429:          # rate limited dall'API
                time.sleep(2 ** attempt * 2)
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            time.sleep(2 ** attempt)
    return None
