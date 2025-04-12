import sys
import json
import pandas as pd
import plotly.express as px
import os
from enum import Enum
os.makedirs("outputs", exist_ok=True)


class Project:
    
    def __init__(self, project_name, file_name, extension,option):       
        self.project_name = project_name
        self.file_name = file_name
        self.extension = extension
        self.option = option

    def get_filename(self):
        return f"{self.name}.{self.extension}"
    
    def visualize(self):
        data = pd.read_csv(os.path.join("uploads", self.file_name))
        column_name = data.columns[self.option]
        output_path = os.path.join("static/outputs", (self.project_name + ".html"))
        fig = px.histogram(data, x=column_name, nbins=30,title=f"Histogram of {column_name}")
        fig.write_html(output_path)

json_string = sys.argv[1]
with open(json_string, 'r') as f:
    project_data = json.load(f)
project = Project(project_data["project_name"],project_data["file_name"],project_data["extension"],project_data["option"])
project.visualize()


