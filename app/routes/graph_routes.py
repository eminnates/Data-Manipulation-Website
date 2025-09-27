from flask import Blueprint, send_file, request, current_app, abort
import os
from app.services.path_builder import PathBuilder
from app.infrastructure.config_provider import FlaskConfigProvider
from app.services.graph_query_service import GraphQueryService

graph_blueprint = Blueprint('graph', __name__)

@graph_blueprint.route('/get-graph', methods=['GET'])
def get_graph():
    project_name = request.args.get("project_name")
    output_type = request.args.get("type", "raw")
    if not project_name:
        abort(400, description="project_name parametresi eksik.")
    # Deprecation: legacy endpoint (gelecekte /graph/v2 veya service-driven API önerilebilir)
    try:
        from app.infrastructure.deprecation import DeprecationEmitter  # type: ignore
        DeprecationEmitter.emit(
            key="route.graph.get_graph.legacy",
            sink=current_app.logger,
            message="/graph/get-graph legacy endpoint; prefer consolidated visualization query service (future /api/visualizations)",
            level='info',
            extra={"route":"get_graph"}
        )
    except Exception:
        pass
    cfg = FlaskConfigProvider(current_app.config)
    pb = PathBuilder.from_config(cfg)  # Protocol uyumlu
    svc = GraphQueryService(pb, current_app.logger)
    res = svc.find(project_name, output_type=output_type, format='html')
    if not res.exists or not res.path:
        abort(404, description=f"Grafik dosyası bulunamadı: {project_name} ({output_type})")
    return send_file(res.path)

@graph_blueprint.route('/get-graph-json', methods=['GET'])
def get_graph_json():
    """
    Önceden oluşturulmuş bir grafik JSON dosyasını arar ve varsa gönderir.
    Dosya bulunamazsa 404 hatası döndürür.
    """
    project_name = request.args.get("project_name")
    output_type = request.args.get("type", "raw")
    if not project_name:
        abort(400, description="project_name parametresi eksik.")
    try:
        from app.infrastructure.deprecation import DeprecationEmitter  # type: ignore
        DeprecationEmitter.emit(
            key="route.graph.get_graph_json.legacy",
            sink=current_app.logger,
            message="/graph/get-graph-json legacy endpoint; prefer unified JSON visualization service (future /api/visualizations)",
            level='info',
            extra={"route":"get_graph_json"}
        )
    except Exception:
        pass
    cfg = FlaskConfigProvider(current_app.config)
    pb = PathBuilder.from_config(cfg)
    svc = GraphQueryService(pb, current_app.logger)
    res = svc.find(project_name, output_type=output_type, format='json')
    if not res.exists or not res.path:
        abort(404, description=f"JSON Grafik dosyası bulunamadı: {project_name} ({output_type})")
    # JSON dosya için send_file content-type otomatik belirler
    return send_file(res.path)