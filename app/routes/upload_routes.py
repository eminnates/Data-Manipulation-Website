from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
from app.utils.file_utils import allowed_file, Project
from python_scripts.getHead import GetHead

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/<projectName>', methods=['POST'])
def upload_file(projectName):
    # Safely get the file from request.files
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400

    # Check extension
    if allowed_file(file.filename):
        # Save file
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        _, ext = os.path.splitext(file.filename)
        extension = ext[1:].lower() if ext else ""

        # Update project info
        pr = Project()
        project_json = pr.project_json
        project_json['project_name'] = projectName
        project_json['file_name'] = file.filename
        project_json['extension'] = extension

        # Validate secim3
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

        # Store dropdown selections
        project_json['option'] = [
            request.form.get('secim1'),
            request.form.get('secim2'),
            request.form.get('secim3'),
            request.form.get('secim4')
        ]
        pr.project_json = project_json
        # Optionally save to JSON or perform other processing

        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully'
        }), 200

    # If the file extension is not allowed
    return jsonify({
        'status': 'error',
        'message': 'Invalid file format'
    }), 400

@upload_blueprint.route('/get-head-api', methods=['POST'])
def get_head_api():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400

    try:
        # Dosya uzantısını al
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()
        
        # Dosya tipine göre oku
        if ext == '.csv':
            df = pd.read_csv(file)
        elif ext in ['.xls', '.xlsx', '.xlsm']:
            df = pd.read_excel(file)
        elif ext == '.json':
            try:
                df = pd.read_json(file)
            except ValueError:
                file.seek(0)
                df = pd.read_json(file, lines=True)
            # Büyük dosya ise sadece ilk 1000 satırı al
            if hasattr(df, 'head'):
                df = df.head(1000)
        elif ext == '.txt':
            # Tab veya virgülle ayrılmış olabilir, otomatik tespit et
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            return jsonify({'status': 'error', 'message': f'Desteklenmeyen dosya türü: {ext}'}), 400

        # İlk 10 satırı JSON olarak döndür
        head_json = GetHead(df).get_head()
        return jsonify({'status': 'success', 'head': head_json}), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Veri okuma hatası: {str(e)}'}), 400

@upload_blueprint.route('/get-columns-api', methods=['POST'])
def get_columns_api():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400

    try:
        # Dosya uzantısını al
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()
        
        # Dosya tipine göre oku
        if ext == '.csv':
            df = pd.read_csv(file)
        elif ext in ['.xls', '.xlsx', '.xlsm']:
            df = pd.read_excel(file)
        elif ext == '.json':
            try:
                df = pd.read_json(file)
            except ValueError:
                file.seek(0)
                df = pd.read_json(file, lines=True)
            if hasattr(df, 'head'):
                df = df.head(1000)
        elif ext == '.txt':
            # Tab veya virgülle ayrılmış olabilir, otomatik tespit et
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            return jsonify({'status': 'error', 'message': f'Desteklenmeyen dosya türü: {ext}'}), 400

        # Sütunları liste olarak döndür
        from python_scripts.getColumns import GetColumns
        columns = GetColumns(df).get_columns()
        return jsonify({'status': 'success', 'columns': columns}), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Veri okuma hatası: {str(e)}'}), 400
