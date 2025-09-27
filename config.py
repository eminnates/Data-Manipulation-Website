import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024 * 8  # 800MB

    # Redis URL for Flask-SocketIO, Celery, or direct usage
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    # Unified log channel (Redis pub/sub + websocket forwarding)
    LOG_CHANNEL_NAME = os.environ.get('LOG_CHANNEL_NAME', 'log_channel')
    # Feature flags for redis/websocket streaming
    ENABLE_REDIS_LOG_STREAM = os.environ.get('ENABLE_REDIS_LOG_STREAM', '1') == '1'
    ENABLE_REDIS_LISTENER = os.environ.get('ENABLE_REDIS_LISTENER', '1') == '1'

    # --- Auth / Security ---
    # JWT settings
    JWT_SECRET = os.environ.get('JWT_SECRET', 'change-me-dev-secret')  # In production override via env
    JWT_ALG = os.environ.get('JWT_ALG', 'HS256')
    JWT_EXP_SECONDS = int(os.environ.get('JWT_EXP_SECONDS', '3600'))  # Default 1 hour tokens
    WEBSOCKET_AUTH_ENABLED = os.environ.get('WEBSOCKET_AUTH_ENABLED', '1') == '1'

    # Rate limiting (simple fixed window per identity + scope)
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', '1') == '1'
    RATE_LIMIT_MAX = int(os.environ.get('RATE_LIMIT_MAX', '60'))  # requests per window
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '60'))  # seconds

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
