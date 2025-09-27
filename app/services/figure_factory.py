from __future__ import annotations
import pandas as pd
import plotly.express as px
from typing import Optional

class FigureFactory:
    """Pure figür oluşturma sınıfı; dosya yolu / I/O içermez.

    Responsibilities:
    - Girilen plot_type, x_col, y_col bilgisine göre uygun Plotly figürü üretmek.
    - Veri ön işleme / grouping (mean hesaplama) gibi mantığı merkezileştirmek.
    - State veya yan etki barındırmamak (kolay test edilebilirlik).
    """

    SUPPORTED = {"Bar", "Line", "Scatter", "Histogram"}

    def create(self, plot_type: str, df: pd.DataFrame, x_col: str, y_col: Optional[str]) -> 'px.Figure':  # type: ignore
        if plot_type not in self.SUPPORTED:
            raise ValueError(f"Geçersiz grafik tipi: {plot_type}")

        if plot_type in {"Bar", "Line", "Scatter"} and not y_col:
            raise ValueError(f"{plot_type} grafiği için Y ekseni gereklidir.")

        if plot_type == "Bar":
            numeric_df = df.select_dtypes(include='number')
            if x_col not in numeric_df.columns:
                numeric_df[x_col] = df[x_col]
            mean_series = numeric_df.groupby(x_col)[y_col].mean()
            grouped_df = mean_series.reset_index(name=f"{y_col}_mean")
            return px.bar(grouped_df, x=x_col, y=f"{y_col}_mean", title=f"Bar Chart of {x_col} vs {y_col} (Mean)")

        if plot_type == "Line":
            mean_series = df.groupby(x_col)[y_col].mean()
            grouped_df = mean_series.reset_index(name=f"{y_col}_mean")
            return px.line(grouped_df, x=x_col, y=f"{y_col}_mean", title=f"Line Chart of {x_col} vs {y_col} (Mean)")

        if plot_type == "Scatter":
            return px.scatter(df, x=x_col, y=y_col, title=f"Scatter Plot of {x_col} vs {y_col}")

        if plot_type == "Histogram":
            return px.histogram(df, x=x_col, title=f"Histogram of {x_col}")

        # Redundant safeguard
        raise ValueError(f"Geçersiz grafik tipi: {plot_type}")

__all__ = ["FigureFactory"]
