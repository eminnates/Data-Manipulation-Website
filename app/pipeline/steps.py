from dataclasses import dataclass
from typing import Optional, Protocol, Any, Dict
import pandas as pd
from python_scripts.dataCleaning import Cleanse, Manipulation, Augmentation
"""Pipeline step implementations.

Registries tanımlarını buraya taşıyarak circular import önlenir.
"""

# --- Manual Process Registries (moved from state_machine) ---
# Cleaning
CLEANING_REGISTRY_SIMPLE = {
    'RemoveWhitespace': lambda cl, proc: cl.RemoveWhitespace(),
    'StripSpecialChars': lambda cl, proc: cl.StripSpecialChars(),
    'LowercaseColumns': lambda cl, proc: cl.LowercaseColumns(),
    'DeleteDupValues': lambda cl, proc: cl.DeleteDupValues(),
    'RemoveConstantColumns': lambda cl, proc: cl.RemoveConstantColumns(),
    'CleanEmails': lambda cl, proc: cl.CleanEmails(),
    'NormalizeColumnValues': lambda cl, proc: cl.NormalizeColumnValues(),
    'AutoRemoveDigitsFromStringColumns': lambda cl, proc: cl.AutoRemoveDigitsFromStringColumns(),
}

def _fix_numeric_column(cl, proc):
    col = proc.get('FixNumericColumn_param')
    if col: cl.FixNumericColumn(col)

def _fill_missing(cl, proc):
    column = proc.get('column')
    method = proc.get('method', 'mean')
    value_to_fill = proc.get('value')
    if column:
        if method == 'value' and value_to_fill is not None:
            cl.FillMissing(column, method=method, value=value_to_fill)
        elif method != 'value':
            cl.FillMissing(column, method=method)

def _remove_high_null(cl, proc):
    threshold = float(proc.get('RemoveHighNullColumns_param', 0.8))
    cl.RemoveHighNullColumns(threshold=threshold)

def _drop_column(cl, proc):
    col = proc.get('DropColumn_param')
    if col: cl.DropColumn(col)

CLEANING_REGISTRY_PARAM = {
    'FixNumericColumn': _fix_numeric_column,
    'FillMissing': _fill_missing,
    'RemoveHighNullColumns': _remove_high_null,
    'DropColumn': _drop_column,
}

# Manipulation
MANIPULATION_REGISTRY_SIMPLE = {
    'detectAndDeleteOutliers': lambda cl, proc: cl.detectAndDeleteOutliers(),
}

def _log_transform(cl, proc):
    column = proc.get('logTransform_param')
    if column: cl.logTransform(column)

MANIPULATION_REGISTRY_PARAM = {
    'logTransform': _log_transform,
}

# Augmentation
def _sort_values(cl, proc):
    col = proc.get('sortValues_param')
    if col: cl.sortValues(col)

def _add_noise(cl, proc):
    column = proc.get('column')
    noise_level = float(proc.get('noise_level', 0.1))
    if column: cl.addNoise(column, noise_level)

def _generate_synth(cl, proc):
    num = int(proc.get('generateSyntheticData_param', 10))
    cl.generateSyntheticData(num_samples=num)

def _categorical_to_numeric(cl, proc):
    col = proc.get('categoricalToNumeric_param')
    if col: cl.categoricalToNumeric(col)

AUGMENTATION_REGISTRY_SIMPLE = {
    'sortValues': _sort_values,
    'addNoise': _add_noise,
    'generateSyntheticData': _generate_synth,
    'categoricalToNumeric': _categorical_to_numeric,
}

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

@dataclass
class StepResult:
    data: Optional[pd.DataFrame] = None
    next_state: Optional[str] = None
    stop: bool = False
    meta: Dict[str, Any] = None

class BaseStep(Protocol):
    name: str
    def run(self, data: pd.DataFrame, *, mode: str, processes, logger: LoggerLike): ...

class CleaningStep:
    name = 'CLEANING'
    def run(self, data: pd.DataFrame, *, mode: str, processes, logger: LoggerLike):
        logger.info("CleaningStep started", mode=mode)
        cl = Cleanse(data)
        if mode == 'full_manual' and processes:
            for proc in processes:
                name = proc.get('name')
                if not name:
                    continue
                if name in CLEANING_REGISTRY_SIMPLE:
                    CLEANING_REGISTRY_SIMPLE[name](cl, proc); continue
                if name in CLEANING_REGISTRY_PARAM:
                    CLEANING_REGISTRY_PARAM[name](cl, proc); continue
                if name == 'FilterRows':
                    cond = proc.get('FilterRows_param')
                    if cond:
                        cl.FilterRows(cond)
                    continue
                if name == 'DynamicFilter':
                    cond = proc.get('DynamicFilter_param')
                    if cond:
                        parts = cond.split()
                        if len(parts) == 3:
                            cl.DynamicFilter({parts[0]: f"{parts[1]} {parts[2]}"})
                    continue
        else:
            cl.RemoveWhitespace()
            cl.StripSpecialChars()
            cl.LowercaseColumns()
            for col in cl.data.select_dtypes(include=['object']).columns:
                cl.FillMissing(col, method='mode')
            cl.RemoveHighNullColumns(threshold=0.8)
            cl.DeleteDupValues()
            cl.RemoveConstantColumns()
            cl.detectAndDeleteOutliers()
            cl.CleanEmails()
            cl.NormalizeColumnValues()
            cl.AutoRemoveDigitsFromStringColumns()
        return StepResult(data=cl.data)

class ManipulationStep:
    name = 'MANIPULATION'
    def run(self, data: pd.DataFrame, *, mode: str, processes, logger: LoggerLike):
        logger.info("ManipulationStep started", mode=mode)
        cl = Manipulation(data)
        if mode == 'full_manual' and processes:
            for proc in processes:
                name = proc.get('name')
                if not name:
                    continue
                if name in MANIPULATION_REGISTRY_SIMPLE:
                    MANIPULATION_REGISTRY_SIMPLE[name](cl, proc); continue
                if name == 'combineColumns':
                    columns_str = proc.get('combineColumns_param')
                    new_col = proc.get('combineColumns_new', 'combined')
                    if columns_str and hasattr(cl, 'combineColumns'):
                        columns = [c.strip() for c in columns_str.split(',')]
                        cl.combineColumns(columns, new_col)
        else:
            ops = Manipulation.choose_column_operations(cl.data)
            for col, actions in ops.items():
                if 'outlier' in actions:
                    cl.detectAndDeleteOutliers()
                if 'log' in actions:
                    cl.logTransform(col)
        return StepResult(data=cl.data)

class AugmentationStep:
    name = 'AUGMENTATION'
    def run(self, data: pd.DataFrame, *, mode: str, processes, logger: LoggerLike):
        logger.info("AugmentationStep started", mode=mode)
        cl = Augmentation(data)
        if mode == 'full_manual' and processes:
            for proc in processes:
                name = proc.get('name')
                if not name:
                    continue
                if name in AUGMENTATION_REGISTRY_SIMPLE:
                    AUGMENTATION_REGISTRY_SIMPLE[name](cl, proc); continue
                if name == 'combineColumns':
                    cols = proc.get('combineColumns_param')
                    new_col = proc.get('combineColumns_new')
                    if cols and new_col:
                        col_list = [c.strip() for c in cols.split(',')]
                        cl.combineColumns(col_list, new_col)
                if name == 'timeSeriesShift':
                    col = proc.get('timeSeriesShift_param')
                    period = int(proc.get('timeSeriesShift_period', 1))
                    if col: cl.timeSeriesShift(col, periods=period)
        else:
            ops = cl.suggest_operations()
            for col, actions in ops.items():
                if 'add_noise' in actions:
                    cl.addNoise(col)
                if 'categorical_to_numeric' in actions:
                    cl.categoricalToNumeric(col)
                if 'generate_synthetic_data' in actions:
                    cl.generateSyntheticData(num_samples=10)
        return StepResult(data=cl.data)

class VisualizationStep:
    name = 'VISUALIZATION'
    def __init__(self, project_name: str, visualization_params: dict, output_type: str):
        self.project_name = project_name
        self.params = visualization_params or {}
        self.output_type = output_type
        # Try import visualization service
        try:
            from app.services.visualization_service import VisualizationService  # type: ignore
            self._VisualizationService = VisualizationService
        except Exception:
            self._VisualizationService = None

    def run(self, data: pd.DataFrame, *, mode: str, processes, logger: LoggerLike):
        logger.info("VisualizationStep started", params=self.params)
        if self._VisualizationService is None:
            logger.warning("VisualizationService unavailable, skipping visualization")
            target = 'COMPLETE' if mode == 'visualize_only' else 'FINAL'
            return StepResult(data=data, next_state=target)
        service = self._VisualizationService(logger)
        result = service.generate(data, self.project_name, {**self.params, 'output_type': self.output_type})
        if result.success:
            logger.info("Visualization successful", path=result.path)
        else:
            logger.warning("Visualization skipped or failed", error=result.error)
        target = 'COMPLETE' if mode == 'visualize_only' else 'FINAL'
        return StepResult(data=data, next_state=target)

class FinalizationStep:
    name = 'FINAL'
    def __init__(self, save_path: str | None):
        self.save_path = save_path
        # Lazy import placeholder; actual service provided at runtime or imported here if needed
        try:
            from app.services.persistence_service import PersistenceService  # type: ignore
            self._PersistenceService = PersistenceService
        except Exception:  # pragma: no cover - fallback if import path changes
            self._PersistenceService = None

    def run(self, data: pd.DataFrame, *, mode: str, processes, logger: LoggerLike):
        logger.info("FinalizationStep started")
        if self._PersistenceService is None:
            logger.warning("PersistenceService unavailable, skipping persistence")
            return StepResult(data=data, next_state='COMPLETE')

        service = self._PersistenceService(logger)
        result = service.save_csv(data, self.save_path)
        if result.success:
            logger.info("Processed data saved", path=result.path)
        else:
            logger.error("Error saving processed data", error=result.error)
        return StepResult(data=data, next_state='COMPLETE')

__all__ = [
    'BaseStep', 'StepResult',
    'CleaningStep', 'ManipulationStep', 'AugmentationStep',
    'VisualizationStep', 'FinalizationStep'
]
