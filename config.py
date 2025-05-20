class Config:
    UPLOAD_FOLDER = 'uploads/'
    OUTPUT_FOLDER = 'app/static/outputs'
    TEMP_FOLDER = 'static/temp/'  # İşlenmiş verilerin geçici saklanacağı klasör
    DEBUG = True
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB maksimum dosya boyutu

class ProductionConfig(Config):
    DEBUG = False  # Disable debug mode in production
    # Üretim ortamı için daha güvenli bir temp klasörü


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True
