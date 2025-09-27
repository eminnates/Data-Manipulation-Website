from flask import Blueprint, send_file, jsonify, current_app, abort
import os

download_blueprint = Blueprint('download', __name__)

# İş mantığını bağımsız fonksiyona taşı
def get_processed_data_file(config, logger, root_path):
    temp_dir = os.path.join(root_path, config['TEMP_FOLDER'])
    processed_file_path = os.path.join(temp_dir, 'processed_data.csv')
    if os.path.exists(processed_file_path):
        return processed_file_path, None
    else:
        logger.warn(f"İndirilmek istenen işlenmiş veri dosyası bulunamadı: {processed_file_path}")
        return None, "İşlenmiş veri bulunamadı - state machine tamamlanmamış olabilir."

@download_blueprint.route('/processed-data', methods=['GET'])
def download_processed_data():
    """İşlenmiş veriyi CSV formatında indirir"""
    try:
        processed_file_path, error = get_processed_data_file(current_app.config, current_app.logger, current_app.root_path)
        if processed_file_path:
            return send_file(
                processed_file_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name="processed_data.csv"
            )
        else:
            return abort(404, error)
    except Exception as e:
        current_app.logger.error(f"İndirme hatası: {str(e)}")
        return abort(500, f"İndirme hatası: {str(e)}")

def check_processed_file_logic(config, logger, root_path):
    temp_dir = os.path.join(root_path, config['TEMP_FOLDER'])
    processed_file_path = os.path.join(temp_dir, 'processed_data.csv')
    exists = os.path.exists(processed_file_path)
    return exists

@download_blueprint.route('/check-file', methods=['GET'])
def check_processed_file():
    """İşlenmiş veri dosyasının varlığını kontrol eder"""
    try:
        exists = check_processed_file_logic(current_app.config, current_app.logger, current_app.root_path)
        return jsonify({
            "exists": exists,
            "message": "İşlenmiş veri mevcut" if exists else "İşlenmiş veri bulunamadı"
        })
    except Exception as e:
        current_app.logger.error(f"İşlenmiş dosya kontrol hatası: {str(e)}")
        return jsonify({
            "error": str(e),
            "exists": False
        }), 500