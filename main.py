import tempfile
from flask import Flask, json, redirect, request, send_file, render_template, jsonify, url_for
import os
import subprocess

app = Flask(__name__)

project_json = {
    "project_name": None,
    "file_name": None,
    "extension": None,
    "option": None
}
prn = ""
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['OUTPUT_FOLDER'] = 'static/outputs/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

def allowed_file(filename):
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    if extension == 'csv' or 'xlsx' or 'txt':
        project_json['file_name'] = filename
        project_json['extension'] = extension
        return True
    else:
        return False

@app.route('/upload/<projectName>', methods=['POST'])
def upload_file(projectName):
    if 'file' not in request.files:
        return 'Dosya bulunamadı'
    
    file = request.files['file']
    if file.filename == '':
        return 'Dosya adı boş'
    
    if file and allowed_file(file.filename):
        secim1 = request.form.get('secim1')
        secim2 = request.form.get('secim2')
        secim3 = request.form.get('secim3')
        project_json['project_name'] = projectName
        global prn
        prn = projectName
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        project_json['option'] = int(secim3)
        return 'Yükleme başarılı'
    return 'Geçersiz dosya formatı'

@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')

@app.route('/hakkimizda', methods=['GET'])
def hakkimizda_page():
    return render_template('hakkımızda.html')

@app.route('/Iletisim', methods=['GET'])
def iletisim_page():
    return render_template('Iletisim.html')

@app.route('/get-graph', methods=['GET'])
def get_graph():
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], prn + ".html")
    if os.path.exists(file_path):
        return send_file(file_path)
    return "File not found", 404

@app.route('/works', methods=['GET'])
def works():
    return render_template('works.html')



@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmpfile:
            json.dump(project_json, tmpfile)
            tmpfile_path = tmpfile.name

        result = subprocess.run(
            ["python", "python_scripts/visualition2.py", tmpfile_path],
            capture_output=True, text=True, check=False
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        if result.returncode != 0:
            return jsonify({"error": "Script error", "details": result.stderr}), 500

        os.remove(tmpfile_path)

        for key in project_json:
            project_json[key] = None

        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500

if __name__ == "__main__":    
    app.run(debug=True)
