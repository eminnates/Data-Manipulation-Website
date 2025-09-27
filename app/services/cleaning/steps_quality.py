from __future__ import annotations
import pandas as pd
from typing import Iterable
from .pipeline import CleaningContext

# Outlier removal based on IQR fence: value < Q1 - k*IQR or > Q3 + k*IQR
class OutlierIQRStep:
    name = 'quality.outlier_iqr'
    def __init__(self, columns: Iterable[str] | None = None, k: float = 1.5, min_rows: int = 10):
        self.columns = columns
        self.k = k
        self.min_rows = min_rows

    def apply(self, df: pd.DataFrame, context: CleaningContext) -> pd.DataFrame:
        cols = self.columns or list(df.select_dtypes(include=['number']).columns)
        if len(df) < self.min_rows:
            context.logger.info('clean.outlier.skip.size', rows=len(df), min_rows=self.min_rows)
            return df
        initial_rows = len(df)
        mask = pd.Series([True] * len(df), index=df.index)
        for c in cols:
            try:
                series = df[c].dropna()
                if series.empty:
                    continue
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lower = q1 - self.k * iqr
                upper = q3 + self.k * iqr
                # Keep rows within fence or with NaN (NaNs not considered outliers here)
                col_mask = ((df[c] >= lower) & (df[c] <= upper)) | df[c].isna()
                mask &= col_mask
            except Exception as e:
                context.logger.warning('clean.outlier.column.skip', column=c, exc=str(e))
        removed = initial_rows - mask.sum()
        if removed > 0:
            context.logger.info('clean.outlier.removed', removed=removed, remaining=int(mask.sum()))
        return df.loc[mask].reset_index(drop=True)

# Drop columns whose null ratio exceeds threshold
class HighNullPruneStep:
    name = 'quality.high_null_prune'
    def __init__(self, threshold: float = 0.6, min_columns: int = 1):
        self.threshold = threshold
        self.min_columns = min_columns

    def apply(self, df: pd.DataFrame, context: CleaningContext) -> pd.DataFrame:
        if df.shape[1] <= self.min_columns:
            context.logger.info('clean.nullprune.skip.mincols', cols=df.shape[1], min_columns=self.min_columns)
            return df
        to_drop = []
        for c in df.columns:
            try:
                series = df[c]
                # Ensure Python None in object columns is treated as NaN
                if series.dtype == object:
                    series = series.where(~series.isin([None]), other=pd.NA)
                ratio = series.isna().mean()
                if ratio >= self.threshold and (df.shape[1] - len(to_drop) - 1) >= self.min_columns:
                    to_drop.append(c)
            except Exception as e:
                context.logger.warning('clean.nullprune.column.skip', column=c, exc=str(e))
        if to_drop:
            context.logger.info('clean.nullprune.drop', columns=to_drop, count=len(to_drop))
            df = df.drop(columns=to_drop)
        return df

# Drop columns that are constant (single unique non-null value) unless excluded
class ConstantColumnPruneStep:
    name = 'quality.constant_prune'
    def __init__(self, exclude: Iterable[str] | None = None, treat_empty_as_null: bool = True):
        self.exclude = set(exclude) if exclude else set()
        self.treat_empty_as_null = treat_empty_as_null

    def apply(self, df: pd.DataFrame, context: CleaningContext) -> pd.DataFrame:
        to_drop = []
        for c in df.columns:
            if c in self.exclude:
                continue
            try:
                series = df[c]
                if self.treat_empty_as_null and series.dtype == object:
                    series = series.replace({'': None, ' ': None})
                nunique = series.nunique(dropna=True)
                if nunique <= 1:
                    to_drop.append(c)
            except Exception as e:
                context.logger.warning('clean.constant.column.skip', column=c, exc=str(e))
        if to_drop:
            context.logger.info('clean.constant.drop', columns=to_drop, count=len(to_drop))
            df = df.drop(columns=to_drop)
        return df

__all__ = ['OutlierIQRStep','HighNullPruneStep','ConstantColumnPruneStep']
