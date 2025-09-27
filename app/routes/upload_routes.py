from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
import numpy as np
import threading
from app.utils.file_utils import allowed_file
from python_scripts.getHead import GetHead
from python_scripts.getColumns import GetColumns
from flask_cors import cross_origin
from app.features.websocket.extensions import socketio

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/<projectName>', methods=['POST'])
@cross_origin()
def upload_file(projectName):
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400
    
    if allowed_file(file.filename):
        project_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], projectName)
        os.makedirs(project_folder, exist_ok=True)

        filepath = os.path.join(project_folder, file.filename)
        file.save(filepath)

        # Eventlet Green Thread ile analiz başlat


        return jsonify({
            'status': 'success', 
            'message': 'File uploaded successfully. Data analysis started in background.', 
            'file_name': file.filename,
            'project_name': projectName,
            'file_path': filepath,
            'analysis_started': True
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400


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

