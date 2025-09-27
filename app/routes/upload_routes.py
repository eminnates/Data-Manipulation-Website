from flask import Blueprint, request, jsonify, current_app
import pandas as pd
from flask_cors import cross_origin
from python_scripts.getHead import GetHead
from python_scripts.getColumns import GetColumns
from app.services.file_storage_service import FileStorageService
from app.services.path_builder import PathBuilder
from app.infrastructure.config_provider import FlaskConfigProvider

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/<projectName>', methods=['POST'])
@cross_origin()
def upload_file(projectName):
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    up_file = request.files['file']
    if not up_file or up_file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400

    # Config -> PathBuilder (upload desteği ile)
    config_provider = FlaskConfigProvider(current_app)
    path_builder = PathBuilder.from_config(config_provider, ensure=True)
    service = FileStorageService(logger=current_app.logger, path_builder=path_builder, base_upload_dir=path_builder.base_upload)
    result = service.save_uploaded(projectName, up_file)
    if not result.success:
        return jsonify({'status': 'error', 'message': result.error or 'Upload failed'}), 400

    return jsonify({
        'status': 'success',
        'message': 'File uploaded successfully. Data analysis can be started.',
        'file_name': result.original_name,
        'stored_name': result.stored_name,
        'project_name': result.project,
        'file_path': result.path,
        'analysis_started': False  # Future: async trigger
    }), 200


@upload_blueprint.route('/get-head-api', methods=['POST'])
def get_head_api():
    try:
        # JSON içindeki sample alanını al
        data = request.get_json()
        if not data or 'sample' not in data:
            return jsonify({'status': 'error', 'message': 'sample verisi eksik'}), 400
        
        sample_text = data['sample']
        
        # Pandas ile sample CSV'yi oku
        from io import StringIO
        sample_io = StringIO(sample_text)
        df = pd.read_csv(sample_io)

        # İlk 10 satır (zaten öyle geliyor ama yine de safe)
        head_json = GetHead(df.head(10)).get_head()
        return jsonify({'status': 'success', 'head': head_json}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Veri okuma hatası: {str(e)}'}), 400
    
@upload_blueprint.route('/get-columns-api', methods=['POST'])
def get_columns_api():
    try:
        # JSON içindeki sample alanını al
        data = request.get_json()
        if not data or 'sample' not in data:
            return jsonify({'status': 'error', 'message': 'sample verisi eksik'}), 400
        
        sample_text = data['sample']
        
        # CSV içeriğini DataFrame'e çevir
        from io import StringIO
        sample_io = StringIO(sample_text)
        df = pd.read_csv(sample_io)

        # Sütunları çıkar
        from python_scripts.getColumns import GetColumns
        columns = GetColumns(df).get_columns()
        return jsonify({'status': 'success', 'columns': columns}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Veri okuma hatası: {str(e)}'}), 400

