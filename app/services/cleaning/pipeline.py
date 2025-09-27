from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, List, Dict, Any, Optional
import pandas as pd
import time

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

class PipelineStep(Protocol):
    name: str
    def apply(self, df: pd.DataFrame, context: 'CleaningContext') -> pd.DataFrame: ...

@dataclass
class CleaningContext:
    logger: LoggerLike
    params: Dict[str, Any]

@dataclass
class StepReport:
    name: str
    ms: float
    rows_before: int
    rows_after: int
    cols_before: int
    cols_after: int

@dataclass
class PipelineResult:
    df: pd.DataFrame
    steps: List[StepReport]

class DataCleaningPipeline:
    def __init__(self, steps: List[PipelineStep], logger: LoggerLike):
        self.steps = steps
        self.logger = logger

    def run(self, df: pd.DataFrame, params: Optional[Dict[str, Any]] = None) -> PipelineResult:
        ctx = CleaningContext(logger=self.logger, params=params or {})
        reports: List[StepReport] = []
        for step in self.steps:
            start = time.time()
            rows_before, cols_before = df.shape
            try:
                result_df = step.apply(df, ctx)
                if result_df is not None:
                    df = result_df
            except Exception as e:
                self.logger.error('clean.step.error', step=step.name, exc=str(e))
                # continue pipeline despite error
            rows_after, cols_after = df.shape
            dur = (time.time() - start) * 1000.0
            self.logger.info('clean.step.done', step=step.name, ms=round(dur,2), rows=rows_after, cols=cols_after)
            reports.append(StepReport(step.name, dur, rows_before, rows_after, cols_before, cols_after))
        return PipelineResult(df=df, steps=reports)

__all__ = ['PipelineStep','CleaningContext','DataCleaningPipeline','PipelineResult','StepReport']
