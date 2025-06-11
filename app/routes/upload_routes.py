from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
from app.utils.file_utils import allowed_file, Project
from python_scripts.getHead import GetHead

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/<projectName>', methods=['POST'])
def upload_file(projectName):
    # request.files dan gelen dosyayı kontrol et
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400

    # uzantıyı kontrol et
    if allowed_file(file.filename):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        _, ext = os.path.splitext(file.filename)
        extension = ext[1:].lower() if ext else ""

        # proje bilgisini jsona yaz
        pr = Project()
        project_json = pr.project_json
        project_json['project_name'] = projectName
        project_json['file_name'] = file.filename
        project_json['extension'] = extension

        # dropdownlardaki seçimleri kontrol et
        secim3_value = request.form.get('secim3')
        secim4_value = request.form.get('secim4')
        if secim3_value is None or secim3_value == '':
            return jsonify({
                'status': 'error',
                'message': 'secim3 alanı eksik veya geçersiz!'
            }), 400
        if secim4_value is None or secim4_value == '':
            return jsonify({
                'status': 'error',
                'message': 'secim4 alanı eksik veya geçersiz!'
            }), 400

        # dropdown seçimlerini option başlığı adı altında jsona ekle
        project_json['option'] = [
            request.form.get('secim1'),
            request.form.get('secim2'),
            request.form.get('secim3'),
            request.form.get('secim4')
        ]
        pr.project_json = project_json

        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully'
        }), 200

    return jsonify({
        'status': 'error',
        'message': 'Invalid file format'
    }), 400

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