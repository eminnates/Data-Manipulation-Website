from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

ALLOWED_PLOT_TYPES: List[str] = ['Bar', 'Line', 'Scatter', 'Histogram']
ALLOWED_OUTPUT_TYPES: List[str] = ['raw', 'refined']

@dataclass(frozen=True)
class VisualizationParamsSchema:
    plot_type: str
    x_col: str
    y_col: Optional[str]
    output_type: str

    @classmethod
    def validate(cls, raw: Dict[str, Any]):
        if raw is None:
            raise ValueError('Params dict required')
        plot_type = raw.get('plot_type')
        x_col = raw.get('x_col')
        y_col = raw.get('y_col')
        output_type = raw.get('output_type', 'raw')
        errors = []
        if not plot_type:
            errors.append('plot_type is required')
        elif plot_type not in ALLOWED_PLOT_TYPES:
            errors.append(f'plot_type must be one of {ALLOWED_PLOT_TYPES}')
        if not x_col:
            errors.append('x_col is required')
        if plot_type in ('Bar','Line','Scatter') and not raw.get('y_col'):
            errors.append('y_col required for Bar/Line/Scatter')
        if output_type not in ALLOWED_OUTPUT_TYPES:
            errors.append(f'output_type must be one of {ALLOWED_OUTPUT_TYPES}')
        if errors:
            raise ValueError('; '.join(errors))
        return cls(plot_type=plot_type, x_col=x_col, y_col=y_col, output_type=output_type)

__all__ = ['VisualizationParamsSchema','ALLOWED_PLOT_TYPES','ALLOWED_OUTPUT_TYPES']
