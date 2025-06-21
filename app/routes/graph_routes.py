from flask import Blueprint, send_from_directory, jsonify, request, current_app, abort
import os

graph_blueprint = Blueprint('graph', __name__)

@graph_blueprint.route('/get-graph', methods=['GET'])
def get_graph():
    project_name = request.args.get("project_name")
    graph_type = request.args.get("type", "raw")  # "raw" veya "refined"

    if not project_name:
        abort(400, description="project_name parametresi eksik.")

    base_name = os.path.splitext(project_name)[0]
    suffix = "_raw" if graph_type == "raw" else "_refined"
    filename = f"{base_name}{suffix}.html"
    outputs_dir = os.path.join(current_app.root_path, 'static', 'outputs')
    
    full_path = os.path.join(outputs_dir, filename)
    current_app.logger.info(f"Aranan grafik dosyası: {full_path}")

    if os.path.exists(full_path):
        return send_from_directory(outputs_dir, filename)
    
    abort(404, description=f"Grafik dosyası bulunamadı: {filename}")
