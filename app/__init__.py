from flask import Flask
import os
import redis



redis_client = redis.Redis()

def create_app(testing=False):
    app = Flask(__name__)
    if testing:
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.ProductionConfig')

    # Gerekli dizinleri oluştur ve logla
    print("Dizinler oluşturuluyor...")
    for folder in ['TEMP_FOLDER', 'UPLOAD_FOLDER', 'OUTPUT_FOLDER', 'LOGS_FOLDER']:
        folder_path = app.config[folder]
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                print(f"Dizin oluşturuldu: {folder_path}")
            except Exception as e:
                print(f"Dizin oluşturma hatası ({folder_path}): {str(e)}")

    # Logger konfigürasyonu
    configure_logging(app)



    
    # Hata işleyicilerini kaydet
    from app.errors.handlers import register_error_handlers
    register_error_handlers(app)
    
    # Blueprint'leri kaydet
    register_blueprints(app)

    return app

def configure_logging(app):
    import logging
    import os
    from datetime import datetime
    
    # Temel loglama seviyesini ayarla
    if not app.debug:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

    if not app.logger.handlers:
        try:
            logs_folder = app.config['LOGS_FOLDER']
            
            # Logs dizini kontrolü
            if not os.path.exists(logs_folder):
                os.makedirs(logs_folder, exist_ok=True)
                print(f"Logs dizini oluşturuldu: {logs_folder}")
                
            # Doğru yol ayırıcı kullanımı
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            flask_log_file = os.path.join(logs_folder, f"flask_app_{timestamp}.log")
            
            # Test et
            try:
                with open(flask_log_file, 'a') as f:
                    f.write(f"Log testi: {datetime.now().isoformat()}\n")
                print(f"Log dosyası yazma testi başarılı: {flask_log_file}")
            except Exception as e:
                print(f"Log dosyası yazma testi başarısız: {str(e)}")
            
            file_handler = logging.FileHandler(flask_log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            
            # Test loglama
            app.logger.info("Flask logging başlatıldı")
            print(f"Flask logger dosyaya yapılandırıldı: {flask_log_file}")
        except Exception as e:
            print(f"Flask logger hatası: {str(e)}")
            # Konsola fallback ekle
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            app.logger.addHandler(console_handler)
            print("Flask logger konsola yapılandırıldı (fallback)")

def register_blueprints(app):
    """Tüm blueprint'leri uygulama ile kaydeder"""
    from app.routes.main_routes import main_blueprint
    from app.routes.upload_routes import upload_blueprint
    from app.routes.graph_routes import graph_blueprint
    from app.routes.state_routes import state_blueprint
    from app.routes.logs_api import logs_blueprint
    from app.routes.download_routes import download_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(upload_blueprint, url_prefix='/upload')
    app.register_blueprint(graph_blueprint, url_prefix='/graph')
    app.register_blueprint(state_blueprint, url_prefix='/state')
    app.register_blueprint(logs_blueprint, url_prefix='/logs')
    app.register_blueprint(download_blueprint, url_prefix='/download')
