try:
    from flask import current_app  # type: ignore
except Exception:  # pragma: no cover
    current_app = None  # type: ignore
import pandas as pd
import plotly.express as px
import os
import traceback
import json  # YENİ: JSON işlemleri için import et
from typing import Optional

try:
    from app.services.path_builder import PathBuilder  # type: ignore
except Exception:  # pragma: no cover
    PathBuilder = None  # type: ignore

try:
    # LogSink interface optional import (service layer kullanıyorsa daha zengin log alır)
    from app.infrastructure.logging_sinks import LogSink  # type: ignore
except Exception:  # pragma: no cover - import fallback
    LogSink = object  # type: ignore


class GraphGenerator:
    """
    Verilen bir DataFrame ve parametrelerle bir grafik oluşturup HTML veya JSON olarak döndürür.
    Bu sınıf 'stateless'dir ve herhangi bir global duruma bağlı değildir.
    """
    def __init__(self, data_df: pd.DataFrame, project_name: str, plot_type: str, x_col: str, y_col: str = None, output_type: str = "raw", logger=None, output_dir: str | None = None, path_builder=None, figure_factory=None):
        """
        GraphGenerator'ı başlatır.

        Args:
            data_df (pd.DataFrame): Grafik için kullanılacak veri.
            project_name (str): Çıktı dosya adını oluşturmak için proje adı.
            plot_type (str): Grafik türü (örn: "Scatter", "Bar", "Line", "Histogram").
            x_col (str): X ekseni için kullanılacak sütun adı.
            y_col (str, optional): Y ekseni için kullanılacak sütun adı. Defaults to None.
            output_type (str, optional): Dosya adı son eki için ("raw" veya "refined"). Defaults to "raw".
        """
        if not isinstance(data_df, pd.DataFrame):
            raise TypeError("data_df bir pandas DataFrame olmalıdır.")
        if not all([project_name, plot_type, x_col]):
            raise ValueError("project_name, plot_type ve x_col boş olamaz.")

        self.data_df = data_df
        self.project_name = project_name
        self.plot_type = plot_type
        self.x_col = x_col
        self.y_col = y_col
        self.output_type = output_type
        # logger param optional (duck-typed LogSink)
        self._logger = logger
        # PathBuilder verilirse onunla yol üretilecek; aksi halde output_dir veya fallback
        self._path_builder = path_builder if path_builder is not None else None
        self._output_dir = output_dir or (self._path_builder.base_output if (self._path_builder and hasattr(self._path_builder, 'base_output')) else self._resolve_default_output_dir())
        # FigureFactory injection
        if figure_factory is not None:
            self._figure_factory = figure_factory
        else:
            try:
                from app.services.figure_factory import FigureFactory  # type: ignore
                self._figure_factory = FigureFactory()
            except Exception:
                self._figure_factory = None

    def _resolve_default_output_dir(self) -> str:
        # Önce DI param (None geldi), sonra Flask (varsa), en son cwd/outputs
        if current_app is not None:
            try:
                cfg_dir = current_app.config.get('OUTPUT_FOLDER')  # type: ignore[attr-defined]
                if cfg_dir:
                    return cfg_dir
            except Exception:
                pass
        fallback = os.path.join(os.getcwd(), 'outputs')
        try:
            os.makedirs(fallback, exist_ok=True)
        except Exception:
            pass
        if self._logger:
            self._logger.info("viz.output_dir.fallback", path=fallback)
        return fallback

    # YENİ: Dosya yolu oluşturma mantığını merkezileştiren yardımcı metot
    def _get_output_path(self, extension: str) -> str:
        """
        Verilen uzantıya göre çıktı dosyasının tam yolunu oluşturur.
        Örn: extension=".html" veya extension=".json"
        """
        if self._path_builder is not None:
            try:
                path = self._path_builder.visualization(self.project_name, self.output_type, extension)
                if self._logger:
                    self._logger.info("viz.output_path.built", path=path, via="path_builder")
                return path
            except Exception as e:  # pragma: no cover - PathBuilder failure fallback
                if self._logger:
                    self._logger.warning("viz.output_path.builder_failure", exc=e)
        # Fallback eski inline mantık
        suffix = "_raw" if self.output_type == "raw" else "_refined"
        safe_project_name = "".join(c if c.isalnum() else "_" for c in self.project_name)
        if not extension.startswith('.'):
            extension = '.' + extension
        output_filename = f"{safe_project_name}{suffix}{extension}"
        if self._logger:
            self._logger.info("viz.output_path.built", filename=output_filename, extension=extension, suffix=suffix, via="inline")
        return os.path.join(self._output_dir, output_filename)



    # Grafiği JSON formatında string olarak döndür (eski generate_and_save_json yerine servis yazımı kullanılıyor)
    def generate_as_json(self) -> str:
        """
        Grafiği oluşturur ve Plotly figürünü JSON formatında bir string olarak döndürür.
        Başarısız olursa None döndürür.
        """
        try:
            # YENİ: Grafik figürünü oluşturan özel metodu çağır
            fig = self._create_figure()
            if fig:
                # Figürü HTML yerine JSON olarak döndür
                return fig.to_json()
        except Exception as e:
            if self._logger:
                self._logger.error("viz.json.error", exc=e, plot_type=self.plot_type)
            else:
                traceback.print_exc()
            return None
        
        return None

    # YENİ: Kod tekrarını önlemek için figür oluşturma mantığını ayıran özel metot
    def _create_figure(self):
        """FigureFactory varsa onu kullan; yoksa ValueError fırlat."""
        if self._figure_factory is None:
            raise RuntimeError("FigureFactory kullanılamıyor (import başarısız)")
        fig = self._figure_factory.create(self.plot_type, self.data_df, self.x_col, self.y_col)
        if self._logger:
            try:
                self._logger.info(
                    "viz.figure.meta",
                    plot_type=self.plot_type,
                    x=self.x_col,
                    y=self.y_col,
                    figure_type=str(type(fig)),
                    traces=len(fig.data) if fig and getattr(fig, 'data', None) is not None else 0,
                )
            except Exception:
                pass
        return fig

    # --- Yeni saf API: servis katmanı dosya yazımını üstlensin ---
    def generate_figure(self):
        """Dosya yazmadan sadece figür oluşturur (servis dışa aktarır)."""
        return self._create_figure()

    def build_output_path(self, extension: str) -> str:
        """Dışardan kullanılabilir path hesaplama (servis için)."""
        return self._get_output_path(extension)






