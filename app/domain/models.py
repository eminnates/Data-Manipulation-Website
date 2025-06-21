from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import pandas as pd
import os
from flask import current_app

@dataclass
class ProjectContext:
    """
    Represents the state and data for a single project/request.
    This object is intended to be created and used per-request, not shared globally.
    """
    project_name: str
    file_name: str
    
    # The actual DataFrame, loaded into memory
    dataframe: Optional[pd.DataFrame] = None
    
    # Path to the currently active data file (could be original or a processed version)
    active_file_path: Optional[str] = None

    def __post_init__(self):
        """Set the initial active file path after the object is created."""
        if self.active_file_path is None:
            self.active_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_name)

    @property
    def extension(self) -> str:
        """Returns the file extension without the dot."""
        _, ext = os.path.splitext(self.file_name)
        return ext.lstrip('.')

    # DÜZELTME: Metodun 'use_cache' parametresini kabul etmesini sağla
    def get_data(self, use_cache=True) -> pd.DataFrame:
        """
        Proje dosyasını okur ve bir pandas DataFrame olarak döndürür.
        use_cache=True ise ve veri daha önce okunmuşsa, diskten tekrar okumak yerine
        önbellekteki veriyi döndürür.
        """
        # 1. Önbelleği kullan ve önbellek dolu mu diye kontrol et
        if use_cache and self.dataframe is not None:
            current_app.logger.info(f"Önbellekten veri getiriliyor: {self.file_name}")
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
            current_app.logger.info(f"Disk'ten veri okunup önbelleğe alındı: {self.file_name}")
            
            return self.dataframe

        except Exception as e:
            current_app.logger.error(f"Dosya okunurken hata oluştu: {self.active_file_path} - Hata: {e}")
            raise

    def __repr__(self):
        return f"<ProjectContext project='{self.project_name}' file='{self.file_name}'>"