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
        cleanse_instance = Cleanse(data_df)    
        total_affected_rows = 0
        # 4. Frontend'den gelen her bir işlem için döngü başlat
        for process in processes:
            op_name = process.get("name")
            # Frontend'den gelen parametreleri al, yoksa boş bir sözlük kullan
            op_params = process.get("params", {})

            if not op_name:
                continue

            # 5. DetectChanges'i DOĞRU şekilde çağır
            #    Her işlem için o anki veri setinde ne kadar değişiklik olduğunu hesapla
            result = cleanse_instance.DetectChanges(operation_type=op_name, parameters=op_params)
            
            if result and 'affected_rows' in result:
                # Etkilenen satır sayısını toplam skora ekle
                total_affected_rows += result['affected_rows']

        # 6. Hesaplanan toplam skoru istemciye gönder
        emit('suitability_result', {'Total affected rows': total_affected_rows})

    except FileNotFoundError:
        emit('suitability_result', {'error': f'Dosya bulunamadı: {file_name}'})
    except Exception as e:
        current_app.logger.error(f"Suitability calculation failed: {e}", exc_info=True)
        emit('suitability_result', {'error': 'Hesaplama sırasında bir hata oluştu.'})
