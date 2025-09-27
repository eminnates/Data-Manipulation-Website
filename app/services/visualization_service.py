from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Protocol, Dict, Any
import pandas as pd

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

from app.services.visualization_params import VisualizationParamsSchema

@dataclass
class VisualizationResult:
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None

class VisualizationService:
    """GraphGenerator kullanımını soyutlar ve param/doğrulama sorumluluğunu merkezileştirir."""
    def __init__(self, logger: LoggerLike, generator_cls=None):
        self.logger = logger
        if generator_cls is None:
            from python_scripts.visualization import GraphGenerator  # local import to avoid heavy deps on import time
            self._generator_cls = GraphGenerator
        else:
            self._generator_cls = generator_cls

    def validate(self, params_dict: Dict[str, Any]) -> VisualizationParamsSchema:
        try:
            params = VisualizationParamsSchema.validate(params_dict)
            return params
        except Exception as e:
            self.logger.warning('Visualization params invalid', error=str(e), raw=params_dict)
            raise

    def generate(self, df: pd.DataFrame, project_name: str, params_dict: Dict[str, Any]) -> VisualizationResult:
        try:
            params = self.validate(params_dict)
        except Exception as e:
            return VisualizationResult(success=False, error=str(e))
        try:
            gen = self._generator_cls(
                data_df=df,
                project_name=project_name,
                plot_type=params.plot_type,
                x_col=params.x_col,
                y_col=params.y_col,
                output_type=params.output_type,
            )
            path = gen.generate_and_save_json()
            if not path:
                self.logger.warning('Visualization generation returned no path')
                return VisualizationResult(success=False, error='No path generated')
            self.logger.info('Visualization generated', path=path, plot_type=params.plot_type)
            return VisualizationResult(success=True, path=path)
        except Exception as e:
            # Mirror old logging pattern so existing tests expecting specific error log pass
            import traceback
            self.logger.error('Visualization error details', exc=str(e))
            self.logger.error('Traceback', trace=traceback.format_exc())
            return VisualizationResult(success=False, error=str(e))

__all__ = ['VisualizationService', 'VisualizationResult']
