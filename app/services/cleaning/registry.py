import importlib
import pkgutil
from typing import Dict, Callable, Any, Type
from pathlib import Path

# Basit discovery: Step sınıfları 'name' attribute içeriyor ve apply(df, ctx) metoduna sahip.
# Dosya adları steps_*.py pattern'i ile filtrelenir.

_STEP_CACHE: Dict[str, Type] = {}
_DISCOVERED = False


def discover_steps(force: bool = False):
    global _DISCOVERED
    if _DISCOVERED and not force:
        return
    package = 'app.services.cleaning'
    package_path = Path(__file__).parent
    for m in pkgutil.iter_modules([str(package_path)]):
        if not m.name.startswith('steps_'):
            continue
        full_name = f'{package}.{m.name}'
        try:
            mod = importlib.import_module(full_name)
        except Exception:
            continue
        for attr in dir(mod):
            if attr.startswith('_'):
                continue
            obj = getattr(mod, attr)
            if isinstance(obj, type):
                if hasattr(obj, 'name') and hasattr(obj, 'apply'):
                    step_name = getattr(obj, 'name', None)
                    if isinstance(step_name, str):
                        _STEP_CACHE[step_name] = obj
    _DISCOVERED = True


def get_step_factory(step_name: str) -> Callable[[dict], Any] | None:
    if not _DISCOVERED:
        discover_steps()
    cls = _STEP_CACHE.get(step_name)
    if not cls:
        return None
    def factory(params: dict):
        return cls(**params)  # Paramlar doğrudan __init__ ile eşleşmeli.
    return factory


def list_registered_steps():
    if not _DISCOVERED:
        discover_steps()
    return sorted(_STEP_CACHE.keys())
