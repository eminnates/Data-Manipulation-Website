"""Utility for emitting structured deprecation warnings only once per key.

Amaç:
    - Aynı deprecation mesajının log'ları spam etmesini önlemek.
    - LogSink arabirimi ile entegre (info/warning seviyesinde kullanıma uygun).

Kullanım:
    from app.infrastructure.deprecation import DeprecationEmitter
    DeprecationEmitter.emit('legacy.state_machine', sink, message='DataStateMachine deprecated')

İleriki aşamada:
    - İsteğe bağlı environment flag (örn. DISABLE_DEPRECATION=1) desteği eklenebilir.
    - Emisyon sayısı (metrik) tutulabilir.
"""
from __future__ import annotations
from typing import ClassVar, Set, Optional
import threading

from app.infrastructure.logging_sinks import LogSink


class DeprecationEmitter:
    _emitted: ClassVar[Set[str]] = set()
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def emit(cls, key: str, sink: Optional[LogSink], message: str, *, level: str = 'warning', extra: dict | None = None) -> bool:
        """Emit deprecation warning once.

        Returns True if emitted this call, False if it was previously emitted.
        """
        if sink is None:
            return False
        with cls._lock:
            if key in cls._emitted:
                return False
            cls._emitted.add(key)
        payload = extra or {}
        payload = {**payload, 'deprecation_key': key}
        try:
            if level == 'warning':
                sink.warning(message, **payload)
            elif level == 'info':
                sink.info(message, **payload)
            else:
                sink.warning(message, **payload)
            return True
        except Exception:
            return False

__all__ = ["DeprecationEmitter"]
