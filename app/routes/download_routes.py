from flask import Blueprint, send_file, jsonify, current_app, abort
import os

download_blueprint = Blueprint('download', __name__)

@download_blueprint.route('/processed-data', methods=['GET'])
def download_processed_data():
    """İşlenmiş veriyi CSV formatında indirir"""
    try:
        # Kök dizini ve yapılandırmadan temp klasörünü al
        # root_dir = os.getcwd() # ESKİ YÖNTEM
        # temp_file_path = os.path.join(root_dir, 'app/static/temp', 'processed_data.csv') # ESKİ YÖNTEM

        # YENİ YÖNTEM: current_app ve config kullanarak yolu oluştur
        temp_dir = os.path.join(current_app.root_path, current_app.config['TEMP_FOLDER'])
        processed_file_path = os.path.join(temp_dir, 'processed_data.csv')
        
        if os.path.exists(processed_file_path):
            return send_file(
                processed_file_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name="processed_data.csv"
            )
        else:
            current_app.logger.warn(f"İndirilmek istenen işlenmiş veri dosyası bulunamadı: {processed_file_path}")
            return abort(404, "İşlenmiş veri bulunamadı - state machine tamamlanmamış olabilir.")
            
    except Exception as e:
        current_app.logger.error(f"İndirme hatası: {str(e)}")
        return abort(500, f"İndirme hatası: {str(e)}")

@download_blueprint.route('/check-file', methods=['GET'])
def check_processed_file():
    """İşlenmiş veri dosyasının varlığını kontrol eder"""
    try:
        # temp_file_path = os.path.join(os.getcwd(), 'app/static/temp', 'processed_data.csv') # ESKİ YÖNTEM

        # YENİ YÖNTEM: current_app ve config kullanarak yolu oluştur
        temp_dir = os.path.join(current_app.root_path, current_app.config['TEMP_FOLDER'])
        processed_file_path = os.path.join(temp_dir, 'processed_data.csv')
        
        exists = os.path.exists(processed_file_path)
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