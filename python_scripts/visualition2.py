import pandas as pd
import plotly.express as px
import os

os.makedirs("outputs", exist_ok=True)


data = pd.read_csv(os.path.join("uploads", "read.csv"))


column_name = data.columns[1]


fig = px.histogram(data, x=column_name, nbins=30,title=f"Histogram of {column_name}")


output_path = os.path.join("static/outputs", "chart.html")
fig.write_html(output_path)
