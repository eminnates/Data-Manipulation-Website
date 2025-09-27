from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Protocol, Dict, Any
import pandas as pd

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

from app.services.visualization_params import VisualizationParamsSchema
from app.services.path_builder import PathBuilder

@dataclass
class VisualizationResult:
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None

class VisualizationService:
    """GraphGenerator kullanımını soyutlar ve param/doğrulama sorumluluğunu merkezileştirir."""
    def __init__(self, logger: LoggerLike, generator_cls=None, path_builder: PathBuilder | None = None):
        self.logger = logger
        if generator_cls is None:
            from python_scripts.visualization import GraphGenerator  # local import to avoid heavy deps on import time
            self._generator_cls = GraphGenerator
        else:
            self._generator_cls = generator_cls
        self._path_builder = path_builder

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
                logger=self.logger,
                path_builder=self._path_builder,
            )
            # Yeni akış: figürü oluştur, json yaz (varsayılan output format JSON kalıyor)
            figure = gen.generate_figure()
            if figure is None:
                self.logger.warning('Visualization generation returned no figure')
                return VisualizationResult(success=False, error='No figure generated')
            out_path = gen.build_output_path('.json')
            try:
                figure.write_json(out_path)
                self.logger.info('Visualization saved', path=out_path, format='json')
            except Exception as io_exc:
                self.logger.error('Visualization write error', exc=str(io_exc), path=out_path)
                return VisualizationResult(success=False, error=str(io_exc))
            return VisualizationResult(success=True, path=out_path)
        except Exception as e:
            # Mirror old logging pattern so existing tests expecting specific error log pass
            import traceback
            self.logger.error('Visualization error details', exc=str(e))
            self.logger.error('Traceback', trace=traceback.format_exc())
            return VisualizationResult(success=False, error=str(e))

    # Ek gelecekte HTML desteği gerekiyorsa çıkarılmış saf metodlar
    def save_html(self, gen, figure) -> str:
        path = gen.build_output_path('.html')
        figure.write_html(path)
        self.logger.info('Visualization saved', path=path, format='html')
        return path

    def save_json(self, gen, figure) -> str:
        path = gen.build_output_path('.json')
        figure.write_json(path)
        self.logger.info('Visualization saved', path=path, format='json')
        return path

__all__ = ['VisualizationService', 'VisualizationResult']
