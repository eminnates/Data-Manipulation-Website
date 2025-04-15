from flask import Blueprint, send_from_directory, jsonify
import os
from app.utils.file_utils import project_json

graph_blueprint = Blueprint('graph', __name__)

@graph_blueprint.route('/get-graph', methods=['GET'])
def get_graph():
    project_name = project_json.get("project_name", "").strip()
    base_name = os.path.splitext(project_name)[0]
    filename = base_name + '.html'
    outputs_dir = os.path.abspath(os.path.join('app', 'static', 'outputs'))
    
    full_path = os.path.join(outputs_dir, filename)
    print("Looking for file:", full_path)  # Debug log

    if os.path.exists(full_path):
        return send_from_directory(outputs_dir, filename)
    
    return jsonify({'error': 'Graph file not found'}), 404
