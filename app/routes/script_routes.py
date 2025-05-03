import os
from flask import Blueprint, jsonify
import subprocess
import tempfile
import json
from app.utils.file_utils import project_json
os.makedirs("logs", exist_ok=True)
script_blueprint = Blueprint('script', __name__)
@script_blueprint.route('run-script', methods=['POST'])
def run_script():
    try:
        # Write project data to a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmpfile:
            json.dump(project_json, tmpfile)
            tmpfile_path = tmpfile.name

        with open("logs/visualition_stdout.log", "w") as out, open("logs/visualition_stderr.log", "w") as err:
            process = subprocess.Popen(
            ["python", "python_scripts/visualition2.py", tmpfile_path],
            stdout=out,
            stderr=err,
            text=True
            )

        # You could choose to log the process PID, store it for later reference, etc.
        return jsonify({
            'message': 'Script started in the background',
            'pid': process.pid,
            'temp_file': tmpfile_path
        }), 202
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
