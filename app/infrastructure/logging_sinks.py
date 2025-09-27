import json
from typing import Any, Dict, List, Optional
import logging

class LogSink:
    """Abstract sink interface (duck-typed)."""
    def info(self, msg: str, **ctx): ...  # pragma: no cover
    def warning(self, msg: str, **ctx): ...  # pragma: no cover
    def error(self, msg: str, exc: Exception | None = None, **ctx): ...  # pragma: no cover

class StdLoggerSink(LogSink):
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    def info(self, msg: str, **ctx):
        self._logger.info(self._fmt(msg, ctx))
    def warning(self, msg: str, **ctx):
        self._logger.warning(self._fmt(msg, ctx))
    def error(self, msg: str, exc: Exception | None = None, **ctx):
        if exc:
            ctx = {**ctx, 'error': str(exc)}
        self._logger.error(self._fmt(msg, ctx))
    def _fmt(self, msg: str, ctx: Dict[str, Any]):
        return msg if not ctx else f"{msg} | {ctx}"

class RedisSink(LogSink):
    def __init__(self, redis_client, channel: str = 'log_channel'):
        self._redis = redis_client
        self._channel = channel
    def info(self, msg: str, **ctx): self._publish('INFO', msg, ctx)
    def warning(self, msg: str, **ctx): self._publish('WARN', msg, ctx)
    def error(self, msg: str, exc: Exception | None = None, **ctx):
        if exc:
            ctx = {**ctx, 'error': str(exc)}
        self._publish('ERROR', msg, ctx)
    def _publish(self, level: str, msg: str, ctx: Dict[str, Any]):
        try:
            payload = json.dumps({'level': level, 'message': msg, 'ctx': ctx})
            self._redis.publish(self._channel, payload)
        except Exception:
            # Sessiz geç (graceful degradation)
            pass

class CompositeSink(LogSink):
    def __init__(self, sinks: List[LogSink]):
        self._sinks = sinks
    def info(self, msg: str, **ctx):
        for s in self._sinks: s.info(msg, **ctx)
    def warning(self, msg: str, **ctx):
        for s in self._sinks: s.warning(msg, **ctx)
    def error(self, msg: str, exc: Exception | None = None, **ctx):
        for s in self._sinks: s.error(msg, exc=exc, **ctx)

class InMemorySink(LogSink):
    """Testing yardımcı sınıf - log olaylarını hafızada toplar."""
    def __init__(self):
        self.events: List[tuple] = []
    def info(self, msg: str, **ctx): self.events.append(('info', msg, ctx))
    def warning(self, msg: str, **ctx): self.events.append(('warning', msg, ctx))
    def error(self, msg: str, exc: Exception | None = None, **ctx):
        if exc:
            ctx = {**ctx, 'error': str(exc)}
        self.events.append(('error', msg, ctx))

__all__ = [
    'LogSink', 'StdLoggerSink', 'RedisSink', 'CompositeSink', 'InMemorySink'
]
