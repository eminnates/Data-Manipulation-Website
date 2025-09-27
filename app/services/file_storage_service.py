from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Protocol, Optional
from werkzeug.datastructures import FileStorage

try:
    from app.utils.file_utils import allowed_file  # type: ignore
except Exception:  # pragma: no cover
    def allowed_file(_):
        return False

class LoggerLike(Protocol):
    def info(self, msg: str, **ctx): ...
    def warning(self, msg: str, **ctx): ...
    def error(self, msg: str, **ctx): ...

@dataclass
class StoredFileResult:
    success: bool
    project: str
    original_name: Optional[str] = None
    stored_name: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None

class FileStorageService:
    """Uploads klasörü içinde proje bazlı dosya saklama sorumluluğu.

    Responsibilities:
    - Güvenli dosya adı üretimi (sanitize)
    - Geçerli uzantı doğrulaması
    - Proje alt klasörünün oluşturulması
    - Yazım hatalarının loglanması
    - Tek noktadan path oluşturma (gelecekte PathBuilder entegrasyonu için hook)
    """

    def __init__(self, base_upload_dir: str | None = None, logger: LoggerLike | None = None, path_builder = None):
        """base_upload_dir opsiyonel hale getirildi; PathBuilder sağlanırsa ondan okunur."""
        self.base_upload_dir = base_upload_dir
        self.logger = logger
        self.path_builder = path_builder

    _sanitize_pattern = re.compile(r"[^A-Za-z0-9_.-]+")

    def sanitize_filename(self, name: str) -> str:
        # Uzantıyı koru, adı normalize et
        name = name.strip()
        return self._sanitize_pattern.sub('_', name)

    def ensure_project_dir(self, project: str) -> str:
        if self.path_builder is not None:
            try:
                return self.path_builder.upload_project_dir(project)
            except Exception as e:
                if self.logger:
                    self.logger.warning('file.upload.path_builder_failed', project=project, exc=e)
        if not self.base_upload_dir:
            raise ValueError('No base upload directory configured')
        safe_project = self.sanitize_filename(project)
        project_dir = os.path.join(self.base_upload_dir, safe_project)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    def save_uploaded(self, project: str, file: FileStorage) -> StoredFileResult:
        if file is None or file.filename is None or file.filename == '':
            return StoredFileResult(success=False, project=project, error='Boş dosya adı')
        original = file.filename
        if not allowed_file(original):
            return StoredFileResult(success=False, project=project, original_name=original, error='Geçersiz uzantı')
        try:
            project_dir = self.ensure_project_dir(project)
            safe_name = self.sanitize_filename(original)
            full_path = os.path.join(project_dir, safe_name)
            file.save(full_path)
            if self.logger:
                self.logger.info('file.upload.saved', project=project, stored_name=safe_name, path=full_path)
            return StoredFileResult(success=True, project=project, original_name=original, stored_name=safe_name, path=full_path)
        except Exception as e:
            if self.logger:
                self.logger.error('file.upload.error', project=project, exc=e, original=original)
            return StoredFileResult(success=False, project=project, original_name=original, error=str(e))

__all__ = ['FileStorageService', 'StoredFileResult']
