from flask import Blueprint, send_from_directory, jsonify, request
import os
from app.utils.file_utils import Project

graph_blueprint = Blueprint('graph', __name__)

@graph_blueprint.route('/get-graph', methods=['GET'])
def get_graph():
    project_name = Project().project_json.get("project_name", "").strip()
    base_name = os.path.splitext(project_name)[0]
    graph_type = request.args.get("type", "raw")  # "raw" veya "refined"
    suffix = "_raw" if graph_type == "raw" else "_refined"
    filename = f"{base_name}{suffix}.html"
    outputs_dir = os.path.abspath(os.path.join('app', 'static', 'outputs'))
    
    full_path = os.path.join(outputs_dir, filename)
    print("Looking for file:", full_path)  # Debug log

    if os.path.exists(full_path):
        return send_from_directory(outputs_dir, filename)
    
    return jsonify({'error': 'Graph file not found'}), 404
