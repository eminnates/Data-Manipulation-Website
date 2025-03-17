from flask import Flask, request, redirect, url_for,render_template
import os

app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'txt'}
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'Dosya bulunamadı'
    file = request.files['file']
    if file.filename == '':
        return 'Dosya adı boş'
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return 'Dosya yüklendi'
    return 'Geçersiz dosya formatı'

if __name__ == "__main__":    
    app.run(debug=True)
