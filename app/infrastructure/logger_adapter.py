from __future__ import annotations
import logging
from typing import Any

class StructuredLoggerWrapper:
    """Wraps a standard logging.Logger to accept arbitrary **ctx and formats them inline.

    Example output:
        viz.output_path.built path=/tmp/file via=path_builder
    """
    def __init__(self, base: logging.Logger, separator: str = ' '):
        self._base = base
        self._sep = separator

    def _fmt(self, msg: str, ctx: dict[str, Any]) -> str:
        if not ctx:
            return msg
        parts = []
        for k, v in ctx.items():
            try:
                val = repr(v) if isinstance(v, (list, dict, tuple)) else v
            except Exception:
                val = '<unrepr>'
            parts.append(f"{k}={val}")
        return msg + self._sep + ' '.join(parts)

    # Common levels
    def info(self, msg: str, **ctx):
        self._base.info(self._fmt(msg, ctx))
    def warning(self, msg: str, **ctx):
        self._base.warning(self._fmt(msg, ctx))
    def error(self, msg: str, **ctx):
        self._base.error(self._fmt(msg, ctx))
    def debug(self, msg: str, **ctx):
        self._base.debug(self._fmt(msg, ctx))

    # Provide original logger access if needed
    @property
    def underlying(self):
        return self._base

    def __getattr__(self, item: str):  # delegate everything else
        return getattr(self._base, item)

__all__ = ["StructuredLoggerWrapper"]