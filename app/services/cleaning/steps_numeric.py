from __future__ import annotations
import pandas as pd
from .pipeline import PipelineStep, CleaningContext

class NumericImputeStep:
    name = 'numeric.impute'
    def __init__(self, strategy: str = 'mean', columns=None):
        self.strategy = strategy
        self.columns = columns

    def apply(self, df: pd.DataFrame, context: CleaningContext) -> pd.DataFrame:
        cols = self.columns
        if cols is None:
            cols = [c for c in df.select_dtypes(include=['number']).columns]
        for c in cols:
            try:
                if self.strategy == 'mean':
                    val = df[c].mean()
                elif self.strategy == 'median':
                    val = df[c].median()
                elif self.strategy == 'zero':
                    val = 0
                else:
                    context.logger.warning('clean.numeric.strategy.unknown', column=c, strategy=self.strategy)
                    continue
                df[c] = df[c].fillna(val)
            except Exception as e:
                context.logger.warning('clean.numeric.skip', column=c, exc=str(e))
        return df

__all__ = ['NumericImputeStep']
