from flask import Flask, jsonify
import os

def create_app(testing=False):
    app = Flask(__name__)
    if testing:
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.ProductionConfig')
    # Temp klasörünün varlığını kontrol et
    if not os.path.exists(app.config['TEMP_FOLDER']):
        os.makedirs(app.config['TEMP_FOLDER'])

    # Error Handling    
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({'error': 'Page not found'}), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    # Register Blueprints
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

    return app
