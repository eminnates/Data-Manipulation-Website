from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.features.redis.redis_client import get_redis_client
from app.infrastructure.logging_sinks import LogSink


@dataclass(slots=True)
class StatusService:
    """Encapsulates transient status flag operations (Redis backed).

    Provides a thin abstraction so orchestration / state machine code does not
    directly import or handle redis errors. Failures are swallowed after
    logging; callers should treat flags as best-effort signalling only.
    """
    logger: LogSink | None = None
    prefix: str = "pipeline"  # default namespace; legacy state machine uses different key

    def _safe(self):
        try:
            return get_redis_client()
        except Exception as e:
            if self.logger:
                self.logger.error("StatusService redis unavailable", exc=e)
            return None

    def set_flag(self, name: str, value: str = "1", *, ttl_seconds: int = 60, prefix: Optional[str] = None) -> bool:
        client = self._safe()
        if client is None:
            return False
        key_prefix = prefix or self.prefix
        key = f"{key_prefix}:{name}"
        try:
            client.set(key, value, ex=ttl_seconds)
            if self.logger:
                self.logger.info("Status flag set", key=key, value=value, ttl=ttl_seconds)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error("Status flag error", key=key, exc=e)
            return False

    def get_flag(self, name: str, *, prefix: Optional[str] = None) -> Optional[str]:
        client = self._safe()
        if client is None:
            return None
        key_prefix = prefix or self.prefix
        key = f"{key_prefix}:{name}"
        try:
            return client.get(key)
        except Exception as e:
            if self.logger:
                self.logger.error("Status flag read error", key=key, exc=e)
            return None

__all__ = ["StatusService"]
