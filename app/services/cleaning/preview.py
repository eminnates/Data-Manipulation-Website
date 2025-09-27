from __future__ import annotations
import time
import pandas as pd
from typing import Callable, Dict, Any, List, Optional, Iterable
from .pipeline import CleaningContext
from .registry import get_step_factory, list_registered_steps
from .steps_text import TextNormalizeStep
from .steps_numeric import NumericImputeStep
from .steps_quality import OutlierIQRStep, HighNullPruneStep, ConstantColumnPruneStep

# Minimal logger placeholder (avoids coupling to app logger inside runner core)
class _NoopLogger:
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass

class PreviewPipelineRunner:
    """Executes cleaning steps in 'preview' mode and streams per-step metrics via a callback.

    Steps list item format:
        {"name": "text.normalize", "params": {"mode": "lower"}}

    Callback signature:
        callback(event_name: str, payload: dict)
    """
    def __init__(self, step_registry: Dict[str, Callable[[Dict[str, Any]], Any]] | None = None,
                 max_changed_columns: int = 40):
        self._cancelled = False
        self._max_changed_columns = max_changed_columns
        self._registry = step_registry or self._default_registry()

    def cancel(self):
        self._cancelled = True

    def _default_registry(self) -> Dict[str, Callable[[Dict[str, Any]], Any]]:
        return {
            'text.normalize': lambda p: TextNormalizeStep(columns=p.get('columns'), mode=p.get('mode','lower'), strip=p.get('strip', True)),
            'numeric.impute': lambda p: NumericImputeStep(strategy=p.get('strategy','mean'), columns=p.get('columns')),
            'quality.outlier_iqr': lambda p: OutlierIQRStep(columns=p.get('columns'), k=p.get('k',1.5), min_rows=p.get('min_rows',10)),
            'quality.high_null_prune': lambda p: HighNullPruneStep(threshold=p.get('threshold',0.6), min_columns=p.get('min_columns',1)),
            'quality.constant_prune': lambda p: ConstantColumnPruneStep(exclude=p.get('exclude'), treat_empty_as_null=p.get('treat_empty_as_null', True)),
        }

    def run(self, df: pd.DataFrame, steps: List[Dict[str, Any]], callback: Callable[[str, Dict[str, Any]], None],
            session_id: str, sample_limit: Optional[int] = None) -> Dict[str, Any]:
        work_df = df.head(sample_limit).copy() if sample_limit else df.copy()
        total_start = time.time()
        overall: List[Dict[str, Any]] = []
        prev_nulls = work_df.isna().sum()

        for idx, spec in enumerate(steps):
            if self._cancelled:
                callback('preview_cancelled', {'session_id': session_id, 'at_step': idx})
                break
            name = spec.get('name')
            params = spec.get('params', {})
            callback('preview_step_started', {'session_id': session_id, 'step': name, 'index': idx})
            factory = self._registry.get(name)
            if not factory:
                # Dynamic discovery fallback
                dyn = get_step_factory(name)
                if dyn:
                    factory = dyn
                    self._registry[name] = dyn  # cache locally for this runner
            if not factory:
                callback('preview_warning', {'session_id': session_id, 'step': name, 'index': idx, 'issue': 'unknown_step'})
                continue
            step_obj = factory(params)
            before_df = work_df.copy()
            rows_before, cols_before = work_df.shape
            t0 = time.time()
            try:
                # Use CleaningContext but with noop logger for isolation
                ctx = CleaningContext(logger=_NoopLogger(), params=params)
                result_df = step_obj.apply(work_df, ctx)
                if result_df is not None:
                    work_df = result_df
            except Exception as e:
                callback('preview_error', {'session_id': session_id, 'step': name, 'index': idx, 'error': str(e)})
                continue
            ms = (time.time() - t0)*1000.0
            rows_after, cols_after = work_df.shape
            diff = self._compute_diff(before_df, work_df, prev_nulls)
            prev_nulls = work_df.isna().sum()
            payload = {
                'session_id': session_id,
                'step': name,
                'index': idx,
                'ms': round(ms,2),
                'rows_before': rows_before,
                'rows_after': rows_after,
                'rows_delta': rows_after - rows_before,
                'cols_before': cols_before,
                'cols_after': cols_after,
                'cols_delta': cols_after - cols_before,
                **diff
            }
            overall.append(payload)
            callback('preview_step_done', payload)
        total_ms = (time.time() - total_start)*1000.0
        callback('preview_complete', {
            'session_id': session_id,
            'total_ms': round(total_ms,2),
            'steps': overall,
            'final_rows': int(work_df.shape[0]),
            'final_cols': int(work_df.shape[1])
        })
        return {'df': work_df, 'steps': overall}

    def _compute_diff(self, before: pd.DataFrame, after: pd.DataFrame, prev_nulls):
        rows_before, cols_before = before.shape
        rows_after, cols_after = after.shape
        # affected_rows logic
        if rows_before != rows_after:
            affected_rows = abs(rows_after - rows_before)
        else:
            # Content diff
            changed_mask_rows = None
            changed_columns = []
            for c in before.columns.intersection(after.columns):
                bcol = before[c]
                acol = after[c]
                try:
                    equal = bcol.equals(acol)
                except Exception:
                    equal = False
                if not equal:
                    changed_columns.append(c)
                    if changed_mask_rows is None:
                        changed_mask_rows = (bcol.fillna('__NA__') != acol.fillna('__NA__'))
                    else:
                        changed_mask_rows = changed_mask_rows | (bcol.fillna('__NA__') != acol.fillna('__NA__'))
            affected_rows = int(changed_mask_rows.sum()) if changed_mask_rows is not None else 0
        # changed_columns (limit)
        changed_columns_limited = []
        for c in before.columns.intersection(after.columns):
            if len(changed_columns_limited) >= self._max_changed_columns:
                break
            try:
                if not before[c].equals(after[c]):
                    changed_columns_limited.append(c)
            except Exception:
                changed_columns_limited.append(c)
        # null delta
        after_nulls = after.isna().sum()
        null_delta = {}
        for c in changed_columns_limited:
            try:
                delta = int(after_nulls.get(c,0) - prev_nulls.get(c,0))
                if delta != 0:
                    null_delta[c] = delta
            except Exception:
                continue
        return {
            'affected_rows': affected_rows,
            'changed_columns': changed_columns_limited,
            'null_delta': null_delta
        }

__all__ = ['PreviewPipelineRunner']
