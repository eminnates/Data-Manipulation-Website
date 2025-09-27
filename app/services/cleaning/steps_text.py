from __future__ import annotations
import pandas as pd
from typing import Iterable
from .pipeline import PipelineStep, CleaningContext

class TextNormalizeStep:
    name = 'text.normalize'
    def __init__(self, columns: Iterable[str] | None = None, mode: str = 'lower', strip: bool = True):
        self.columns = columns
        self.mode = mode
        self.strip = strip

    def apply(self, df: pd.DataFrame, context: CleaningContext) -> pd.DataFrame:
        cols = self.columns
        if cols is None:
            cols = [c for c in df.columns if df[c].dtype == object]
        for c in cols:
            try:
                series = df[c].astype(str)
                if self.strip:
                    series = series.str.strip()
                if self.mode == 'lower':
                    series = series.str.lower()
                elif self.mode == 'upper':
                    series = series.str.upper()
                elif self.mode == 'title':
                    series = series.str.title()
                df[c] = series
            except Exception:
                context.logger.warning('clean.text.skip', column=c)
        return df

__all__ = ['TextNormalizeStep']
