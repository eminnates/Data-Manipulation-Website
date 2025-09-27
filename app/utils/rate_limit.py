import time
from flask import current_app
from app.features.redis.redis_client import get_redis_client


class RateLimitResult:
    __slots__ = ("allowed", "remaining", "reset", "limit")

    def __init__(self, allowed: bool, remaining: int, reset: int, limit: int):
        self.allowed = allowed
        self.remaining = remaining
        self.reset = reset
        self.limit = limit

    def to_headers(self):
        return {
            'X-RateLimit-Limit': str(self.limit),
            'X-RateLimit-Remaining': str(max(0, self.remaining)),
            'X-RateLimit-Reset': str(self.reset)
        }


def check_rate_limit(identity: str, scope: str) -> RateLimitResult:
    cfg = current_app.config
    if not cfg.get('RATE_LIMIT_ENABLED', True):
        # effectively unlimited
        return RateLimitResult(True, cfg.get('RATE_LIMIT_MAX', 0), int(time.time()), cfg.get('RATE_LIMIT_MAX', 0))

    limit = int(cfg.get('RATE_LIMIT_MAX', 60))
    window = int(cfg.get('RATE_LIMIT_WINDOW', 60))
    now = int(time.time())
    window_start = now - (now % window)
    key = f"rl:{identity}:{scope}:{window_start}"
    reset = window_start + window

    r = get_redis_client()
    try:
        pipe = r.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, window + 5)
        current = pipe.execute()[0]
    except Exception:
        # fail-open in case redis unavailable
        return RateLimitResult(True, limit, reset, limit)

    remaining = limit - current
    allowed = current <= limit
    return RateLimitResult(allowed, remaining, reset, limit)
