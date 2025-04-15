from flask import Blueprint, request, jsonify, current_app
import os
from app.utils.file_utils import allowed_file, project_json, prn

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/<projectName>', methods=['POST'])
def upload_file(projectName):
    if 'file' not in request.files:
        return jsonify({'error': 'File not found'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Filename is empty'}), 400
    
    if file and allowed_file(file.filename):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        _, ext = os.path.splitext(file.filename)
        extension = ext[1:].lower() if ext else ""
        # Update project details
        global prn
        prn = file.filename
        project_json['project_name'] = projectName
        project_json['file_name'] = file.filename
        project_json['extension'] = extension
        project_json['option'] = [
            request.form.get('secim1'),
            request.form.get('secim2'),
            int(request.form.get('secim3'))
        ]

        return jsonify({'message': 'File uploaded successfully'}), 200

    return jsonify({'error': 'Invalid file format'}), 400
