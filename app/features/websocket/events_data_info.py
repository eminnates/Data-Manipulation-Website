from app.features.websocket.extensions import socketio
from flask_socketio import emit
from flask import current_app
from app.domain.models import ProjectContext

@socketio.on('get_column_names')
def handle_get_column_names(data):
    project_name = data.get('project_name')
    file_name = data.get('file_name')
    if not all([project_name, file_name]):
        emit('column_names_result', {'error': 'Proje veya dosya adı eksik.'})
        return
    current_app.logger.info(f"Column names request for project '{project_name}', file '{file_name}'")
    try:
        context = ProjectContext(project_name=project_name, file_name=file_name)
        data_df = context.get_data(use_cache=True)
        columns_info = []
        for col in data_df.columns:
            col_type = str(data_df[col].dtype)
            is_numeric = data_df[col].dtype in ['int64', 'float64', 'int32', 'float32']
            is_string = data_df[col].dtype == 'object'
            columns_info.append({
                'name': col,
                'type': col_type,
                'is_numeric': is_numeric,
                'is_string': is_string,
                'null_count': int(data_df[col].isnull().sum()),
                'unique_count': int(data_df[col].nunique())
            })
        emit('column_names_result', {
            'columns': columns_info,
            'total_rows': len(data_df),
            'project_name': project_name,
            'file_name': file_name
        })
    except FileNotFoundError:
        emit('column_names_result', {'error': f'Dosya bulunamadı: {file_name}'})
    except Exception as e:
        current_app.logger.error(f"Column names fetch failed: {e}", exc_info=True)
        emit('column_names_result', {'error': f'Sütun adları alınırken hata: {str(e)}'})

@socketio.on('request_data_analysis')
def handle_data_analysis_request(data):
    project_name = data.get('project_name')
    file_name = data.get('file_name')
    if not all([project_name, file_name]):
        emit('data_analysis_error', {'error': 'Proje veya dosya adı eksik.'})
        return
    emit('data_analysis_status', {
        'status': 'acknowledged',
        'message': f'Veri analizi talebi alındı: {project_name}/{file_name}'
    })

@socketio.on('get_analysis_status')
def handle_get_analysis_status(data):
    project_name = data.get('project_name')
    emit('analysis_status_response', {
        'project_name': project_name,
        'status': 'ready_for_query'
    })
