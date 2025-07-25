from flask import Blueprint, request, jsonify, current_app, abort
import os
import pandas as pd
import threading
from python_scripts.state_machine import DataStateMachine
import json
import uuid 
from app.domain.models import ProjectContext

state_blueprint = Blueprint('state', __name__)

# DÜZELTME: Arka plan görevine 'visualization_params' parametresini ekle
def run_state_machine_background(app, file_name, ext, mode='full_auto', output_type='raw', process_list=None, project_title="default_project", visualization_params=None):
    with app.app_context():
        try:
            # 1. YARAT: Context nesnesini burada oluştur.
            project_context = ProjectContext(project_name=project_title, file_name=file_name)
            
            data_df = project_context.get_data()

            app.logger.info(f"Dosya başarıyla okundu: {project_context.active_file_path}")

            temp_dir = os.path.join(app.root_path, app.config['TEMP_FOLDER'])
            unique_filename = f"processed_{uuid.uuid4().hex}.csv"
            output_processed_file_path = os.path.join(temp_dir, unique_filename)

            # 2. TAŞI: Makineye sadece context nesnesini ve diğer parametreleri ver.
            machine = DataStateMachine(
                context=project_context, # data ve project_name yerine tek bir nesne
                mode=mode,
                output_type=output_type,
                processes=process_list,
                processed_data_save_path=output_processed_file_path,
                visualization_params=visualization_params # Grafik için yeni parametre
            )
            machine.process()
            
            app.logger.info(f"State machine işlemi tamamlandı. İşlenmiş veri şuraya kaydedildi: {output_processed_file_path}")

        except Exception as e:
            app.logger.error(f"State machine arka plan görevi sırasında hata: {e}", exc_info=True)


@state_blueprint.route('/run-state-machine', methods=['POST'])
def run_state_machine():
    file_name = request.form.get('file_name')
    project_title = request.form.get('project_name')
    
    if not file_name:
        abort(400, description='file_name parametresi eksik.')
    
    # Dosya adından uzantıyı al
    _, file_extension = os.path.splitext(file_name)

    # Dosyanın sunucuda var olduğunu kontrol et
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, file_name)

    if not os.path.exists(file_path):
        current_app.logger.error(f"Dosya bulunamadı: {file_path}")
        abort(404, description=f'Sunucuda dosya bulunamadı: {file_name}')
        
    # Diğer parametreleri al
    mode = request.form.get('mode', 'full_auto')
    output_type = request.form.get('output_type', 'raw')
    processes_json_str = request.form.get('processes')
    
    # DÜZELTME: Görselleştirme parametrelerini formdan al
    visualization_params = {
        "plot_type": request.form.get("secim1"),
        "x_col": request.form.get("secim2"),
        "y_col": request.form.get("secim3")
    }
    
    process_list = []
    if processes_json_str:
        try:
            process_list = json.loads(processes_json_str)
        except json.JSONDecodeError:
            abort(400, description='Gönderilen process listesi geçerli bir JSON değil.')

    if not project_title:
        project_title = os.path.splitext(file_name)[0]

    app_instance = current_app._get_current_object()
    
    thread = threading.Thread(
        target=run_state_machine_background,
        # DÜZELTME: Arka plan görevine yeni parametreleri de gönder
        args=(app_instance, file_name, file_extension, mode, output_type, process_list, project_title, visualization_params)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'State machine başarıyla başlatıldı.', 'processed_file': file_name}), 202