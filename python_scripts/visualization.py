import pandas as pd
import plotly.express as px
import os
import traceback

# Proje başlatıldığında çıktı klasörünün var olduğundan emin ol.
os.makedirs("app/static/outputs", exist_ok=True)

class GraphGenerator:
    """
    Verilen bir DataFrame ve parametrelerle bir grafik oluşturup HTML olarak kaydeder.
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

    # DÜZELTME: Metod adını 'generate_and_save' olarak değiştir ve dosya yolunu döndür.
    def generate_and_save(self) -> str:
        """
        Grafiği oluşturur, HTML dosyası olarak kaydeder ve dosya yolunu döndürür.
        Başarısız olursa None döndürür.
        """
        # Dosya adı ve yolunu hazırla
        suffix = "_raw" if self.output_type == "raw" else "_refined"
        safe_project_name = "".join(c if c.isalnum() else "_" for c in self.project_name)
        output_filename = f"{safe_project_name}{suffix}.html"
        output_path = os.path.join("app/static/outputs", output_filename)

        fig = None
        try:
            if self.plot_type == "Bar":
                if not self.y_col: raise ValueError("Bar grafiği için Y ekseni gereklidir.")
                mean_series = self.data_df.groupby(self.x_col)[self.y_col].mean()
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
                print(f"Geçersiz grafik tipi: {self.plot_type}")
                return None

            if fig:
                fig.write_html(output_path)
                print(f"Grafik kaydedildi: {output_path}")
                return output_path # Başarı durumunda dosya yolunu döndür
        except Exception as e:
            print(f"Grafik oluşturulurken hata oluştu ({self.plot_type}): {e}")
            print(traceback.format_exc())
            return None # Hata durumunda None döndür

        return None # Herhangi bir figür oluşturulmazsa None döndür






