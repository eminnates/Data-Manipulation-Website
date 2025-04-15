class Config:
    UPLOAD_FOLDER = 'uploads/'
    OUTPUT_FOLDER = 'outputs/'
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False  # Disable debug mode in production
