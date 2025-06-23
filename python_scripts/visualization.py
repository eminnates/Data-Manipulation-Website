from flask import current_app
import pandas as pd
import plotly.express as px
import os
import traceback
import json # YENİ: JSON işlemleri için import et


class GraphGenerator:
    """
    Verilen bir DataFrame ve parametrelerle bir grafik oluşturup HTML veya JSON olarak döndürür.
    Bu sınıf 'stateless'dir ve herhangi bir global duruma bağlı değildir.
    """
    def __init__(self, data_df: pd.DataFrame, project_name: str, plot_type: str, x_col: str, y_col: str = None, output_type: str = "raw"):
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

    # YENİ: Dosya yolu oluşturma mantığını merkezileştiren yardımcı metot
    def _get_output_path(self, extension: str) -> str:
        """
        Verilen uzantıya göre çıktı dosyasının tam yolunu oluşturur.
        Örn: extension=".html" veya extension=".json"
        """
        suffix = "_raw" if self.output_type == "raw" else "_refined"
        safe_project_name = "".join(c if c.isalnum() else "_" for c in self.project_name)
        # Uzantının başında nokta olduğundan emin ol
        if not extension.startswith('.'):
            extension = '.' + extension
        output_filename = f"{safe_project_name}{suffix}{extension}"
        print(f"Çıktı dosyası adı: {output_filename}")
        print(f"suffix: {suffix}")
        print(f"extension: {extension}")
        print(f"output_filename: {output_filename}")
        print(f"full output path: {os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)}")
        return os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)

    def generate_and_save(self) -> str:
        """
        Grafiği oluşturur, HTML dosyası olarak kaydeder ve dosya yolunu döndürür.
        Başarısız olursa None döndürür.
        """
        output_path = self._get_output_path(".html")
        print(f"DEBUG: Attempting to save HTML to: {output_path}") # DEBUG

        try:
            fig = self._create_figure()
            print(f"DEBUG: _create_figure returned an object of type: {type(fig)}") # DEBUG

            if fig:
                print("DEBUG: 'if fig' was TRUE. Writing HTML file...") # DEBUG
                fig.write_html(output_path)
                print(f"Grafik kaydedildi: {output_path}")
                return output_path
            else:
                print("DEBUG: 'if fig' was FALSE. Skipping HTML file write.") # DEBUG

        except Exception as e:
            print(f"Grafik oluşturulurken hata oluştu ({self.plot_type}): {e}")
            print(traceback.format_exc())
        

    # YENİ: Grafiği JSON dosyası olarak kaydeden metot
    def generate_and_save_json(self) -> str:
        """
        Grafiği oluşturur, JSON dosyası olarak kaydeder ve dosya yolunu döndürür.
        Başarısız olursa None döndürür.
        """
        output_path = self._get_output_path(".json")
        print(f"DEBUG: Attempting to save JSON to: {output_path}") # DEBUG
        
        try:
            fig = self._create_figure()
            print(f"DEBUG: _create_figure returned an object of type: {type(fig)}") # DEBUG

            if fig:
                print("DEBUG: 'if fig' was TRUE. Writing JSON file...") # DEBUG
                fig.write_json(output_path)
                print(f"Grafik JSON olarak kaydedildi: {output_path}")
                return output_path
            else:
                print("DEBUG: 'if fig' was FALSE. Skipping JSON file write.") # DEBUG

        except Exception as e:
            print(f"Grafik JSON'u kaydedilirken hata oluştu ({self.plot_type}): {e}")
            print(traceback.format_exc())



    # YENİ: Grafiği JSON formatında döndüren metot
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
            print(f"Grafik JSON'u oluşturulurken hata oluştu ({self.plot_type}): {e}")
            print(traceback.format_exc())
            return None
        
        return None

    # YENİ: Kod tekrarını önlemek için figür oluşturma mantığını ayıran özel metot
    def _create_figure(self):
        """
        Sınıf niteliklerine göre bir Plotly figürü oluşturur ve döndürür.
        """
        fig = None
        if self.plot_type == "Bar":
            if not self.y_col: raise ValueError("Bar grafiği için Y ekseni gereklidir.")
            # Sayısal olmayan sütunları hariç tutarak gruplama yap
            numeric_df = self.data_df.select_dtypes(include='number')
            if self.x_col not in numeric_df.columns:
                numeric_df[self.x_col] = self.data_df[self.x_col]
            
            mean_series = numeric_df.groupby(self.x_col)[self.y_col].mean()
            grouped_df = mean_series.reset_index(name=f"{self.y_col}_mean")
            fig = px.bar(grouped_df, x=self.x_col, y=f"{self.y_col}_mean", title=f"Bar Chart of {self.x_col} vs {self.y_col} (Mean)")
        
        elif self.plot_type == "Line":
            if not self.y_col: raise ValueError("Line grafiği için Y ekseni gereklidir.")
            mean_series = self.data_df.groupby(self.x_col)[self.y_col].mean()
            grouped_df = mean_series.reset_index(name=f"{self.y_col}_mean")
            fig = px.line(grouped_df, x=self.x_col, y=f"{self.y_col}_mean", title=f"Line Chart of {self.x_col} vs {self.y_col} (Mean)")
        
        elif self.plot_type == "Scatter":
            if not self.y_col: raise ValueError("Scatter grafiği için Y ekseni gereklidir.")
            fig = px.scatter(self.data_df, x=self.x_col, y=self.y_col, title=f"Scatter Plot of {self.x_col} vs {self.y_col}")
        
        elif self.plot_type == "Histogram":
            fig = px.histogram(self.data_df, x=self.x_col, title=f"Histogram of {self.x_col}")
        
        else:
            raise ValueError(f"Geçersiz grafik tipi: {self.plot_type}")
        print(f"fig oluşturuldu: {self.plot_type} - {self.x_col} vs {self.y_col if self.y_col else 'N/A'}")
        print(f"fig tipi: {type(fig)}")
        print(f"fig veri tipi: {type(fig.data)}")
        print(f"fig: {fig}")

        return fig






