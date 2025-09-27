from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Protocol, Optional

class ConfigProviderLike(Protocol):
    def get(self, key: str, default=None): ...

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

@dataclass(frozen=True)
class PathBuilder:
    base_output: str
    base_temp: str
    base_upload: Optional[str] = None

    @classmethod
    def from_config(cls, config: ConfigProviderLike, ensure: bool = True):
        output = config.get('OUTPUT_FOLDER', os.path.join(os.getcwd(), 'app', 'static', 'outputs'))
        temp = config.get('TEMP_FOLDER', os.path.join(os.getcwd(), 'app', 'static', 'temp'))
        upload = config.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
        if ensure:
            for p in [output, temp, upload]:
                try:
                    os.makedirs(p, exist_ok=True)
                except Exception:
                    # Sessiz geç; üst seviye log mekanizması yakalayabilir
                    pass
        return cls(base_output=output, base_temp=temp, base_upload=upload)

    def processed_csv(self, file_name: str | None = None) -> str:
        if not file_name:
            file_name = 'processed_data.csv'
        return os.path.join(self.base_temp, file_name)

    def visualization(self, project_name: str, output_type: str, extension: str) -> str:
        suffix = '_raw' if output_type == 'raw' else '_refined'
        safe_project = ''.join(c if c.isalnum() else '_' for c in project_name)
        if not extension.startswith('.'):
            extension = '.' + extension
        file_name = f"{safe_project}{suffix}{extension}"
        return os.path.join(self.base_output, file_name)

    # --- Upload related paths ---
    def upload_project_dir(self, project_name: str, ensure: bool = True) -> str:
        if not self.base_upload:
            raise ValueError('Upload base directory not configured in PathBuilder')
        safe_project = ''.join(c if c.isalnum() else '_' for c in project_name)
        path = os.path.join(self.base_upload, safe_project)
        if ensure:
            os.makedirs(path, exist_ok=True)
        return path

    def upload_file(self, project_name: str, file_name: str) -> str:
        project_dir = self.upload_project_dir(project_name, ensure=True)
        return os.path.join(project_dir, file_name)

__all__ = ['PathBuilder']
