from __future__ import annotations
from typing import Protocol, Any, Mapping

class ConfigProvider(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...

class DictConfigProvider:
    """Simple config provider over a plain dict (useful for tests/CLI)."""
    def __init__(self, data: Mapping[str, Any]):
        self._data = data
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

class FlaskConfigProvider:
    """Adapter that wraps a Flask application's config object."""
    def __init__(self, flask_config):
        self._cfg = flask_config
    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self._cfg.get(key, default)
        except Exception:
            return default

__all__ = ["ConfigProvider", "DictConfigProvider", "FlaskConfigProvider"]
