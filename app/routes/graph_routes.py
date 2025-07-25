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

@graph_blueprint.route('/get-graph-json', methods=['GET'])
def get_graph_json():
    """
    Önceden oluşturulmuş bir grafik JSON dosyasını arar ve varsa gönderir.
    Dosya bulunamazsa 404 hatası döndürür.
    """
    project_name = request.args.get("project_name")
    graph_type = request.args.get("type", "raw")  # "raw" veya "refined"

    if not project_name:
        abort(400, description="project_name parametresi eksik.")

    # Güvenlik ve tutarlılık için proje adını temizle
    safe_project_name = "".join(c if c.isalnum() else "_" for c in project_name)
    suffix = "_raw" if graph_type == "raw" else "_refined"
    filename = f"{safe_project_name}{suffix}.json" # DİKKAT: Uzantı .json
    outputs_dir = os.path.join(current_app.root_path, 'static', 'outputs')
    
    full_path = os.path.join(outputs_dir, filename)
    current_app.logger.info(f"Aranan JSON grafik dosyası: {full_path}")

    if os.path.exists(full_path):
        # send_from_directory, dosya uzantısına göre doğru Content-Type'ı (application/json) ayarlar.
        return send_from_directory(outputs_dir, filename)
    
    # Dosya bulunamadıysa 404 (Not Found) hatası döndür.
    abort(404, description=f"JSON Grafik dosyası bulunamadı: {filename}")