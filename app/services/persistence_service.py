from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Protocol, Optional
import pandas as pd

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

@dataclass
class SaveResult:
    path: Optional[str]
    success: bool
    error: Optional[str] = None

class PersistenceService:
    """Responsible for persisting processed data outputs (currently CSV)."""
    def __init__(self, logger: LoggerLike):
        self.logger = logger

    def ensure_dir(self, path: str):
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def resolve_path(self, provided_path: str | None) -> str:
        if provided_path:
            return provided_path
        # fallback temp path
        temp_dir = os.path.join(os.getcwd(), 'app', 'static', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, 'processed_data.csv')

    def save_csv(self, df: pd.DataFrame, target_path: str | None) -> SaveResult:
        path = self.resolve_path(target_path)
        try:
            self.ensure_dir(path)
            df.to_csv(path, index=False)
            self.logger.info("Data persisted", path=path)
            return SaveResult(path=path, success=True)
        except Exception as e:
            self.logger.error("Persist error", exc=e, path=path)
            return SaveResult(path=None, success=False, error=str(e))

__all__ = ["PersistenceService", "SaveResult"]
