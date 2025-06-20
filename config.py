import os

class Config:
        MAX_CONTENT_LENGTH = 100 * 1024 * 1024
class DevelopmentConfig(Config):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(BASE_DIR, 'app/static/outputs'))
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', os.path.join(BASE_DIR, 'app/static/temp'))
    LOGS_FOLDER = os.environ.get('LOGS_FOLDER', os.path.join(BASE_DIR, 'logs'))
    DEBUG = True
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

    # Redis config
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

class ProductionConfig(Config):
    DEBUG = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/app/uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', '/tmp/app/outputs')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', '/tmp/app/temp')
    LOGS_FOLDER = os.environ.get('LOGS_FOLDER', '/tmp/app/logs')