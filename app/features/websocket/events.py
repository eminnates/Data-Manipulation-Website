from app.features.websocket.extensions import socketio
from flask import current_app
from flask_socketio import emit
# DÜZELTME: ProjectContext'i import et
from app.domain.models import ProjectContext
# DÜZELTME: Uygunluk hesaplama mantığını import et (varsayımsal)
from python_scripts.dataCleaning import Cleanse

@socketio.on('connect')
def handle_connect():
    print("Bir istemci WebSocket ile bağlandı.")

def send_log_to_clients(log_message):
    socketio.emit('log_message', {'log': log_message})

@socketio.on('calculate_suitability')
def handle_suitability_check(data):
    """
    Frontend'den gelen işlem listesine ve proje bilgilerine göre bir
    uygunluk skoru (toplam etkilenen satır sayısı) hesaplar.
    """
    processes = data.get('processes', [])
    project_name = data.get('project_name')
    file_name = data.get('file_name')

    if not all([project_name, file_name]):
        emit('suitability_result', {'error': 'Proje veya dosya adı eksik.'})
        return

    current_app.logger.info(f"Suitability check for project '{project_name}' with processes: {processes}")

    try:
        # 1. Bu işleme özel bir ProjectContext YARAT
        context = ProjectContext(project_name=project_name, file_name=file_name)
        data_df = context.get_data(use_cache=True).copy()
        
        total_affected_rows = 0
        # 4. Frontend'den gelen her bir işlem için döngü başlat
        for process in processes:
            op_name = process.get("name")
            # Frontend'den gelen parametreleri al, yoksa boş bir sözlük kullan
            op_params = process.get("params", {})

            if not op_name:
                continue

            # Debug bilgisi ekle
            current_app.logger.info(f"Processing operation: {op_name} with params: {op_params}")

            # 5. Her işlem için temiz bir kopya oluştur
            # Bu sayede her işlem orijinal veriyi temel alır
            cleanse_instance = Cleanse(data_df.copy())
            
            # DetectChanges'i DOĞRU şekilde çağır
            # Her işlem için o anki veri setinde ne kadar değişiklik olduğunu hesapla
            result = cleanse_instance.DetectChanges(operation_type=op_name, parameters=op_params)
            
            if result and 'affected_rows' in result:
                # Etkilenen satır sayısını toplam skora ekle
                total_affected_rows += result['affected_rows']
                current_app.logger.info(f"Operation '{op_name}' affected {result['affected_rows']} rows")
            else:
                current_app.logger.warning(f"Operation '{op_name}' returned no valid result: {result}")

        # 6. Hesaplanan toplam skoru istemciye gönder
        emit('suitability_result', {'Total affected rows': total_affected_rows})

    except FileNotFoundError as e:
        current_app.logger.error(f"File not found: {e}")
        emit('suitability_result', {'error': f'Dosya bulunamadı: {file_name}'})
    except Exception as e:
        current_app.logger.error(f"Suitability calculation failed: {e}", exc_info=True)
        emit('suitability_result', {'error': f'Hesaplama sırasında bir hata oluştu: {str(e)}'})

@socketio.on('request_data_analysis')
def handle_data_analysis_request(data):
    """
    Frontend'den gelen veri analizi talebi
    """
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
    """
    Analiz durumunu sorgula
    """
    project_name = data.get('project_name')
    emit('analysis_status_response', {
        'project_name': project_name,
        'status': 'ready_for_query'
    })

@socketio.on('get_column_names')
def handle_get_column_names(data):
    """
    Belirtilen proje ve dosya için sütun adlarını getir
    """
    project_name = data.get('project_name')
    file_name = data.get('file_name')
    
    if not all([project_name, file_name]):
        emit('column_names_result', {'error': 'Proje veya dosya adı eksik.'})
        return
    
    current_app.logger.info(f"Column names request for project '{project_name}', file '{file_name}'")
    
    try:
        # ProjectContext ile veri dosyasını oku
        context = ProjectContext(project_name=project_name, file_name=file_name)
        data_df = context.get_data(use_cache=True)
        
        # Sütun adlarını ve tiplerini al
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
        
        current_app.logger.info(f"Found {len(columns_info)} columns for project '{project_name}'")
        
        emit('column_names_result', {
            'columns': columns_info,
            'total_rows': len(data_df),
            'project_name': project_name,
            'file_name': file_name
        })
        
    except FileNotFoundError as e:
        current_app.logger.error(f"File not found: {e}")
        emit('column_names_result', {'error': f'Dosya bulunamadı: {file_name}'})
    except Exception as e:
        current_app.logger.error(f"Column names fetch failed: {e}", exc_info=True)
        emit('column_names_result', {'error': f'Sütun adları alınırken hata oluştu: {str(e)}'})

from app.features.analysis.analyze_helpers import (
    analyze_data_background_main
)

from app.features.analysis.large_file_helpers import analyze_large_file_main

def register_analysis_events(socketio, app_instance):
    @socketio.on('start_data_analysis')
    def handle_data_analysis_event(data):
        filepath = data.get('filepath')
        project_name = data.get('project_name')
        file_name = data.get('file_name')
        if not filepath or not project_name or not file_name:
            emit('data_analysis_error', {
                'status': 'error',
                'message': 'Eksik parametre!',
                'error_type': 'argument',
                'project_name': project_name,
                'file_name': file_name
            })
            return
        analyze_data_background_main(filepath, project_name, file_name, app_instance)