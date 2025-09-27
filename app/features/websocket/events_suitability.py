from app.features.websocket.extensions import socketio
from flask_socketio import emit
from flask import current_app
from app.domain.models import ProjectContext
from python_scripts.dataCleaning import Cleanse

@socketio.on('calculate_suitability')
def handle_suitability_check(data):
    processes = data.get('processes', [])
    project_name = data.get('project_name')
    file_name = data.get('file_name')

    if not all([project_name, file_name]):
        emit('suitability_result', {'error': 'Proje veya dosya adı eksik.'})
        return

    current_app.logger.info(f"Suitability check for project '{project_name}' with processes: {processes}")

    try:
        context = ProjectContext(project_name=project_name, file_name=file_name)
        data_df = context.get_data(use_cache=True).copy()
        total_affected_rows = 0
        for process in processes:
            op_name = process.get("name")
            op_params = process.get("params", {})
            if not op_name:
                continue
            current_app.logger.info(f"Processing operation: {op_name} with params: {op_params}")
            cleanse_instance = Cleanse(data_df.copy())
            result = cleanse_instance.DetectChanges(operation_type=op_name, parameters=op_params)
            if result and 'affected_rows' in result:
                total_affected_rows += result['affected_rows']
                current_app.logger.info(f"Operation '{op_name}' affected {result['affected_rows']} rows")
            else:
                current_app.logger.warning(f"Operation '{op_name}' returned no valid result: {result}")
        emit('suitability_result', {'Total affected rows': total_affected_rows})
    except FileNotFoundError:
        emit('suitability_result', {'error': f'Dosya bulunamadı: {file_name}'})
    except Exception as e:
        current_app.logger.error(f"Suitability calculation failed: {e}", exc_info=True)
        emit('suitability_result', {'error': f'Hesaplama sırasında hata: {str(e)}'})
