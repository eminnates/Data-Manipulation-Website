import sys
import json
import pandas as pd
import plotly.express as px
import os
from enum import Enum
os.makedirs("app/static/outputs", exist_ok=True)


class Project:
    
    def __init__(self, project_name, file_name, extension, option):       
        self.project_name = project_name
        self.file_name = file_name
        self.extension = extension
        self.option = option

    def visualize(self):
        data = None
        if self.extension == "csv":
            data = pd.read_csv(os.path.join("uploads", self.file_name))
        elif self.extension == "xlsx":
            data = pd.read_excel(os.path.join("uploads", self.file_name))
        elif self.extension == "json":
            data = pd.read_json(os.path.join("uploads", self.file_name))
        elif self.extension == "xml":
            data = pd.read_xml(os.path.join("uploads", self.file_name))
        column_name = data.columns[self.option[2]]
        output_path = os.path.join("app/static/outputs", (self.project_name + ".html"))
        fig = px.histogram(data, x=column_name, nbins=30,title=f"Histogram of {column_name}")
        fig.write_html(output_path)

json_string = sys.argv[1]
with open(json_string, 'r') as f:
    project_data = json.load(f)
print(f"Project data loaded: {project_data}")
project = Project(project_data["project_name"],project_data["file_name"],project_data["extension"],project_data["option"])
project.visualize()


