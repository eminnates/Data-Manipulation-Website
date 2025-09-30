from dataclasses import dataclass
from typing import Optional
import pandas as pd
import os

@dataclass
class ProjectContext:
    """Framework bağımsız proje veri konteksi.

    Flask `current_app` bağımlılığı kaldırıldı. Gerekli bağımlılıklar
    (base_upload_dir, logger) DI ile sağlanır. Testlerde sade mock
    logger ve temp dizin ile kolayca üretilebilir.
    """
    project_name: str
    file_name: str
    base_upload_dir: str
    logger: Optional[object] = None
    dataframe: Optional[pd.DataFrame] = None
    active_file_path: Optional[str] = None

    def __post_init__(self):
        if self.active_file_path is None:
            project_folder = os.path.join(self.base_upload_dir, self.project_name)
            self.active_file_path = os.path.join(project_folder, self.file_name)
        # Lazy log
        if self.logger:
            try:
                self.logger.info(f"ProjectContext initialized: {self.active_file_path}")
            except Exception:
                pass

    @property
    def extension(self) -> str:
        """Returns the file extension without the dot."""
        _, ext = os.path.splitext(self.file_name)
        return ext.lstrip('.')
    
    def get_data_path(self) -> str:
        """Returns the full path to the data file."""
        return self.active_file_path

    # DÜZELTME: Metodun 'use_cache' parametresini kabul etmesini sağla
    def get_data(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Proje dosyasını okur ve bir pandas DataFrame olarak döndürür.
        use_cache=True ise ve veri daha önce okunmuşsa, diskten tekrar okumak yerine
        önbellekteki veriyi döndürür.
        """
        # 1. Önbelleği kullan ve önbellek dolu mu diye kontrol et
        if use_cache and self.dataframe is not None:
            if self.logger:
                self.logger.info(f"Önbellekten veri getiriliyor: {self.file_name}")
            return self.dataframe

        # 2. Dosyanın var olup olmadığını kontrol et
        if not os.path.exists(self.active_file_path):
            raise FileNotFoundError(f"Veri dosyası bulunamadı: {self.active_file_path}")

        # 3. Dosyayı uzantısına göre oku
        _, file_extension = os.path.splitext(self.file_name)
        try:
            if file_extension.lower() == '.csv':
                self.dataframe = pd.read_csv(self.active_file_path)
            elif file_extension.lower() in ['.xls', '.xlsx']:
                self.dataframe = pd.read_excel(self.active_file_path)
            else:
                raise ValueError(f"Desteklenmeyen dosya uzantısı: {file_extension}")
            
            # 4. Okunan veriyi önbelleğe al
            if self.logger:
                self.logger.info(f"Disk'ten veri okunup önbelleğe alındı: {self.file_name}")
            
            return self.dataframe

        except Exception as e:
            if self.logger:
                self.logger.error(f"Dosya okunurken hata oluştu: {self.active_file_path} - Hata: {e}")
            raise

    def __repr__(self):
        return f"<ProjectContext project='{self.project_name}' file='{self.file_name}'>"

    # Factory method for backwards compatibility with Flask code paths
    @classmethod
    def from_flask(cls, project_name: str, file_name: str, flask_app):
        base_upload_dir = flask_app.config['UPLOAD_FOLDER']
        logger = flask_app.logger if hasattr(flask_app, 'logger') else None
        return cls(project_name=project_name, file_name=file_name, base_upload_dir=base_upload_dir, logger=logger)