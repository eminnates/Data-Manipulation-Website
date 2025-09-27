from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Protocol, Optional, Literal
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
    """Responsible for persisting processed data outputs (csv / parquet)."""
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

    def save_data(self, df: pd.DataFrame, target_path: str | None, *, format: Literal['csv','parquet']='csv', parquet_engine: str | None = None) -> SaveResult:
        # Normalize to str in case a Path object was passed
        if target_path is not None and not isinstance(target_path, str):
            target_path = str(target_path)
        path = self.resolve_path(target_path)
        # Adjust extension if mismatch
        if format == 'parquet' and not path.lower().endswith('.parquet'):
            base, _ = os.path.splitext(path)
            path = base + '.parquet'
        if format == 'csv' and not path.lower().endswith('.csv'):
            base, _ = os.path.splitext(path)
            path = base + '.csv'
        try:
            self.ensure_dir(path)
            if format == 'csv':
                df.to_csv(path, index=False)
            else:
                # Lazy import pyarrow / fastparquet not enforced; rely on pandas
                try:
                    df.to_parquet(path, engine=parquet_engine if parquet_engine else 'auto', index=False)
                except Exception as pe:
                    # Engine missing or write error
                    self.logger.error("Parquet persist error", exc=pe, path=path)
                    return SaveResult(path=None, success=False, error=str(pe))
            self.logger.info("Data persisted", path=path, format=format)
            return SaveResult(path=path, success=True)
        except Exception as e:
            self.logger.error("Persist error", exc=e, path=path, format=format)
            return SaveResult(path=None, success=False, error=str(e))

    # Backward compatibility wrapper
    def save_csv(self, df: pd.DataFrame, target_path: str | None) -> SaveResult:
        return self.save_data(df, target_path, format='csv')

__all__ = ["PersistenceService", "SaveResult"]
