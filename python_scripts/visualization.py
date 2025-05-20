import pandas as pd
import plotly.express as px
import os
# from app.utils.file_utils import Project, prn # 'Project' burada yeniden tanımlanıyor, 'prn' kullanılmıyor.
# 'FileProject' __init__ içinde lokal olarak import ediliyor.

os.makedirs("app/static/outputs", exist_ok=True)


class Project:
    def __init__(self, project_json=None, output_type="raw", data=None):
        if project_json is None:
            from app.utils.file_utils import Project as FileProject
            project_json = FileProject().project_json
        self.project_name = project_json['project_name']
        self.file_name = project_json['file_name']
        self.extension = project_json['extension']
        self.option = project_json['option'] # plot_type, x_axis, y_axis içerir
        self.output_type = output_type  # "raw" veya "refined"
        self.data = data  # refined için işlenmiş veri

    def visualize(self):
        # 1. DataFrame'i belirle
        data_df = None
        if self.data is not None and isinstance(self.data, pd.DataFrame):
            data_df = self.data
        else:
            extension = self.extension.lstrip('.')
            file_path = os.path.join("uploads", self.file_name)
            if not os.path.exists(file_path):
                print(f"Hata: Dosya bulunamadı - {file_path}")
                return False
            if extension.lower() == "csv":
                data_df = pd.read_csv(file_path)
            elif extension.lower() in ["xls", "xlsx", "xlsm"]:
                data_df = pd.read_excel(file_path)
            elif extension.lower() == "json":
                try:
                    data_df = pd.read_json(file_path)
                except ValueError:
                    data_df = pd.read_json(file_path, lines=True)
            elif extension.lower() == "xml":
                data_df = pd.read_xml(file_path)
            else:
                print(f"Desteklenmeyen dosya uzantısı: {extension}")
                return False

        if data_df is None:
            print("Veri yüklenemedi.")
            return False

        plot_type = self.option[0]
        x_col = self.option[1]
        y_col = self.option[2] if len(self.option) > 2 else None

        # Dosya adı ve yolunu hazırla
        suffix = "_raw" if self.output_type == "raw" else "_refined"
        safe_project_name = "".join(c if c.isalnum() else "_" for c in self.project_name)
        output_filename = f"{safe_project_name}{suffix}.html"
        output_path = os.path.join("app/static/outputs", output_filename)

        fig = None
        try:
            if plot_type == "Bar":
                mean_series = data_df.groupby(x_col)[y_col].mean()
                grouped_df = mean_series.reset_index(name=f"{y_col}_mean")
                fig = px.bar(grouped_df, x=x_col, y=f"{y_col}_mean", title=f"Bar Chart of {x_col} vs {y_col} (Mean)")
            elif plot_type == "Line":
                mean_series = data_df.groupby(x_col)[y_col].mean()
                grouped_df = mean_series.reset_index(name=f"{y_col}_mean")
                fig = px.line(grouped_df, x=x_col, y=f"{y_col}_mean", title=f"Line Chart of {x_col} vs {y_col} (Mean)")
            elif plot_type == "Scatter":
                fig = px.scatter(data_df, x=x_col, y=y_col, title=f"Scatter Plot of {x_col} vs {y_col}")
            elif plot_type == "Histogram":
                fig = px.histogram(data_df, x=x_col, title=f"Histogram of {x_col}")
            else:
                print(f"Geçersiz grafik tipi: {plot_type}")
                return False

            if fig:
                fig.write_html(output_path)
                print(f"Grafik kaydedildi: {output_path}")
                return True
        except Exception as e:
            print(f"Grafik oluşturulurken hata oluştu ({plot_type}): {e}")
            import traceback
            print(traceback.format_exc())
            return False

        return False






