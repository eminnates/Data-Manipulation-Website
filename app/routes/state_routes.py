from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
import threading
from python_scripts.state_machine import DataState, DataStateMachine
from app.utils.file_utils import Project
import json  # json importu eklendi

state_blueprint = Blueprint('state', __name__)

# run_state_machine_background fonksiyonu artık 'app' parametresini alacak
def run_state_machine_background(app, file_path, ext, mode='full_auto', output_type='raw', process_list=None, project_title="default_project"):
    with app.app_context():  # current_app yerine doğrudan app nesnesini kullan
        try:
            # YENİ YÖNTEM: app ve config kullanarak yolu oluştur
            temp_dir = os.path.join(app.root_path, app.config['TEMP_FOLDER'])
            processed_file_path_to_delete = os.path.join(temp_dir, 'processed_data.csv')

            if os.path.exists(processed_file_path_to_delete):
                try:
                    os.remove(processed_file_path_to_delete)
                    app.logger.info(f"Eski işlenmiş dosya başarıyla silindi: {processed_file_path_to_delete}")
                except OSError as e:
                    app.logger.error(f"Eski işlenmiş dosya silinirken hata oluştu {processed_file_path_to_delete}: {e}")
            else:
                app.logger.info(f"Silinecek eski işlenmiş dosya bulunamadı: {processed_file_path_to_delete}")
            
            # Uzantıyı düzgün formata getir (nokta ekleyerek)
            if not ext.startswith('.'):
                ext = '.' + ext
            
            # Dosya uzantısına göre farklı okuma yöntemleri kullan
            data_df = None  # data_df olarak yeniden adlandırıldı
            if ext.lower() == '.csv':
                data_df = pd.read_csv(file_path)
            elif ext.lower() in ['.xls', '.xlsx', '.xlsm']:
                data_df = pd.read_excel(file_path)
            elif ext.lower() == '.json':
                try:
                    data_df = pd.read_json(file_path)
                except ValueError:  # Eğer dosya satır satır JSON ise
                    data_df = pd.read_json(file_path, lines=True)
                app.logger.info(f"JSON dosyası başarıyla okundu: {file_path}")
            elif ext.lower() == '.txt':
                data_df = pd.read_csv(file_path, sep=None, engine='python')  # Otomatik ayırıcı tespiti
            else:
                app.logger.warning(f"Uzantı {ext} tanınmadı. CSV olarak okuma deneniyor.")
                try:
                    data_df = pd.read_csv(file_path)
                except Exception as read_err:
                    app.logger.error(f"Dosya {file_path} CSV olarak da okunamadı: {read_err}")
                    return

            if data_df is None:
                app.logger.error(f"Veri yüklenemedi: {file_path}")
                return

            app.logger.info(f"Dosya başarıyla okundu: {file_path} (format: {ext})")
            
            # State machine çalıştır
            output_processed_file_path = os.path.join(temp_dir, 'processed_data.csv')

            machine = DataStateMachine(
                data=data_df,
                mode=mode,
                output_type=output_type,
                processes=process_list,
                processed_data_save_path=output_processed_file_path,
                # project_name=project_title # Eğer DataStateMachine __init__ project_name alıyorsa
            )
            machine.process()  # State machine'i çalıştır
            
            app.logger.info(f"State machine işlemi tamamlandı. İşlenmiş veri şuraya kaydedilmeli: {output_processed_file_path}")

        except Exception as e:
            app.logger.error(f"State machine arka plan görevi sırasında hata: {e}")
            import traceback
            app.logger.error(traceback.format_exc())

@state_blueprint.route('/run-state-machine', methods=['POST'])
def run_state_machine():
    # file_utils.Project() her çağrıldığında project.json'ı yeniden okur.
    # Bu, dosya seçimi değiştiğinde güncel bilgiyi almasını sağlar.
    project_helper = Project() 
    file_name = project_helper.project_json.get('file_name', '')
    
    if not file_name:
        # Eğer file_utils.Project ile dosya adı alınamadıysa, doğrudan request'ten almayı dene
        # Bu genellikle ilk dosya yükleme senaryosu için geçerli olabilir.
        if 'file' in request.files:
             file = request.files['file']
             if file.filename == '':
                 return jsonify({'error': 'No file selected in form'}), 400
             file_name = file.filename  # Yüklenen dosyanın adını kullan
             # Dosyayı kaydet (eğer ilk yükleme ise)
             upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
             if not os.path.exists(upload_folder):
                 os.makedirs(upload_folder)
             file_path_for_save = os.path.join(upload_folder, file_name)
             file.save(file_path_for_save)
             current_app.logger.info(f"File uploaded and saved via form: {file_path_for_save}")
             # project.json'ı bu yeni dosya ile güncelle
             project_helper.update_project_json(project_name=os.path.splitext(file_name)[0], file_name=file_name, extension=os.path.splitext(file_name)[1])
        else:
            return jsonify({'error': 'No file provided or found in project context'}), 400
        
    project_extension = project_helper.project_json.get('extension', '')
    # Uzantı kontrolü ve düzeltme
    if project_extension and not project_extension.startswith('.'):
        project_extension = '.' + project_extension
    
    # UPLOAD_FOLDER'ı config'den al, yoksa varsayılan kullan
    upload_folder_path = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
    file_path = os.path.join(upload_folder_path, file_name)
    file_path = os.path.abspath(file_path)  # Tam yolu al
    
    current_app.logger.info(f"Attempting to process file: {file_path} with extension: {project_extension}")
    
    # Dosyanın varlığını kontrol et
    if not os.path.exists(file_path):
        current_app.logger.error(f"File not found at path: {file_path}")
        return jsonify({'error': f'File not found: {file_path}'}), 400
        
    # İstek parametrelerini al
    mode = request.form.get('mode', 'full_auto')
    output_type = request.form.get('output_type', 'raw')
    processes_json_str = request.form.get('processes')  # processes_json_str olarak adlandırdım
    project_title = project_helper.project_json.get('project_name', os.path.splitext(file_name)[0])

    process_list = []
    if processes_json_str:
        try:
            process_list = json.loads(processes_json_str)
            current_app.logger.info(f"Received processes: {process_list}")
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON Decode Error for processes: {e}")
            return jsonify({'error': f'Process list is not valid JSON: {e}'}), 400
    
    # Gerçek app nesnesini al
    app_instance = current_app._get_current_object()

    # State machine'i arka planda başlat
    thread = threading.Thread(
        target=run_state_machine_background,
        args=(app_instance, file_path, project_extension, mode, output_type, process_list, project_title)  # project_title eklendi
    )
    thread.daemon = True  # Ana thread sonlandığında bu thread'in de sonlanmasını sağlar
    thread.start()
    
    # Başarı yanıtı döndür
    return jsonify({'message': 'State machine başlatıldı', 'filename_processed': file_name}), 202