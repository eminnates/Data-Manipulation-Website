from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Protocol, Optional

from app.services.path_builder import PathBuilder

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

@dataclass
class GraphLookupResult:
    exists: bool
    path: Optional[str]
    project: str
    output_type: str
    format: str  # 'html' or 'json'
    error: Optional[str] = None

class GraphQueryService:
    """Locates previously generated graph artifacts using PathBuilder.

    - Abstracts filename/suffix logic
    - Provides single point for existence check & logging
    - Prepares ground for caching or remote storage later
    """
    def __init__(self, path_builder: PathBuilder, logger: LoggerLike | None = None):
        self._pb = path_builder
        self._logger = logger

    def _build_path(self, project: str, output_type: str, format: str) -> str:
        ext = '.html' if format == 'html' else '.json'
        return self._pb.visualization(project, output_type, ext)

    def find(self, project: str, output_type: str = 'raw', format: str = 'html') -> GraphLookupResult:
        format = format.lower()
        if format not in ('html','json'):
            return GraphLookupResult(False, None, project, output_type, format, error='Unsupported format')
        path = self._build_path(project, output_type, format)
        exists = os.path.exists(path)
        if self._logger:
            self._logger.info('graph.lookup', project=project, output_type=output_type, format=format, exists=exists, path=path)
        if not exists:
            return GraphLookupResult(False, None, project, output_type, format, error='Not found')
        return GraphLookupResult(True, path, project, output_type, format)

__all__ = ['GraphQueryService','GraphLookupResult']
