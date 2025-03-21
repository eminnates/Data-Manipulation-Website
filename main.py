from flask import Flask, request, send_file, render_template, jsonify
import os
import subprocess

app = Flask(__name__)


app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['OUTPUT_FOLDER'] = 'outputs/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'txt', 'json'}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'Dosya bulunamadı'
    
    file = request.files['file']
    if file.filename == '':
        return 'Dosya adı boş'
    
    if file and allowed_file(file.filename):
        file.filename = 'read.csv'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'read.csv')
        file.save(filepath)
        return f'Dosya yüklendi: {file.filename}'
    
    return 'Geçersiz dosya formatı'
@app.route('/get-graph', methods=['GET'])
def get_graph():
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output.png')
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/png')
    return "File not found", 404




@app.route('/run-script', methods=['POST'])
def run_script():
    get_graph()
    try:
       
        result = subprocess.run(
            ["python", "python_scripts/visualition2.py"],
            capture_output=True, text=True, check=True,
        )

        return jsonify({"image_url": f"/get-graph"})
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500

if __name__ == "__main__":    
    app.run(debug=True)
