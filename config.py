import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024 * 8  # 800MB

    # Redis URL for Flask-SocketIO, Celery, or direct usage
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

class DevelopmentConfig(Config):
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(Config.BASE_DIR, 'uploads'))
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(Config.BASE_DIR, 'app/static/outputs'))
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', os.path.join(Config.BASE_DIR, 'app/static/temp'))
    LOGS_FOLDER = os.environ.get('LOGS_FOLDER', os.path.join(Config.BASE_DIR, 'logs'))
    DEBUG = True

    # Redis config breakdown if needed for direct Redis client connections
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

class ProductionConfig(Config):
    DEBUG = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/app/uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', '/tmp/app/outputs')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', '/tmp/app/temp')
    LOGS_FOLDER = os.environ.get('LOGS_FOLDER', '/tmp/app/logs')

    # Redis config breakdown for production if needed
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
