from flask import Blueprint, send_file, jsonify, current_app, abort
import os
from app.infrastructure.config_provider import FlaskConfigProvider
from app.services.path_builder import PathBuilder

download_blueprint = Blueprint('download', __name__)

# İş mantığını bağımsız fonksiyona taşı
def get_processed_data_file(app_ctx_or_config, logger=None, root_path=None):
    """Backward compatible signature.

    Eski testler (config, logger, root_path) bekliyor; yeni kullanım current_app geçiriyor.
    Parametre sayısına göre ayrım yapıyoruz.
    """
    if hasattr(app_ctx_or_config, 'config'):
        app_ctx = app_ctx_or_config  # current_app benzeri
        cfg = FlaskConfigProvider(app_ctx.config)
        pb = PathBuilder.from_config(cfg, ensure=True)
        processed_file_path = pb.processed_csv()
    else:
        # Legacy yol: root_path + config['TEMP_FOLDER'] + processed_data.csv (TEMP_FOLDER boş ise root_path)
        config = app_ctx_or_config or {}
        temp_folder = config.get('TEMP_FOLDER', '')
        base = root_path if root_path else os.getcwd()
        temp_dir = os.path.join(base, temp_folder) if temp_folder else base
        processed_file_path = os.path.join(temp_dir, 'processed_data.csv')
        class _Shim:
            def __init__(self, logger):
                self.logger = logger
        app_ctx = _Shim(logger)
    if os.path.exists(processed_file_path):
        return processed_file_path, None
    else:
        # Legacy logger (tests) sadece warn içeriyor olabilir.
        if hasattr(app_ctx.logger, 'warn'):
            try:
                app_ctx.logger.warn("processed.csv.missing")
            except Exception:
                pass
        else:
            log_fn = getattr(app_ctx.logger, 'warning', None)
            if log_fn:
                try:
                    log_fn("processed.csv.missing", path=processed_file_path)
                except Exception:
                    pass
        return None, "İşlenmiş veri bulunamadı - state machine tamamlanmamış olabilir."

@download_blueprint.route('/processed-data', methods=['GET'])
def download_processed_data():
    """İşlenmiş veriyi CSV formatında indirir"""
    try:
        processed_file_path, error = get_processed_data_file(current_app)
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

def check_processed_file_logic(app_ctx_or_config, logger=None, root_path=None):
    if hasattr(app_ctx_or_config, 'config'):
        app_ctx = app_ctx_or_config
        cfg = FlaskConfigProvider(app_ctx.config)
        pb = PathBuilder.from_config(cfg, ensure=True)
        processed_file_path = pb.processed_csv()
        return os.path.exists(processed_file_path)
    else:
        config = app_ctx_or_config or {}
        temp_folder = config.get('TEMP_FOLDER', '')
        base = root_path if root_path else os.getcwd()
        temp_dir = os.path.join(base, temp_folder) if temp_folder else base
        processed_file_path = os.path.join(temp_dir, 'processed_data.csv')
        return os.path.exists(processed_file_path)

@download_blueprint.route('/check-file', methods=['GET'])
def check_processed_file():
    """İşlenmiş veri dosyasının varlığını kontrol eder"""
    try:
        exists = check_processed_file_logic(current_app)
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