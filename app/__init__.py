from flask import Flask, jsonify
from flasgger import Swagger
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')  # Adjust the path as needed if config.py is not in the same directory
 
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
    from app.routes.script_routes import script_blueprint
    from app.routes.state_routes import state_blueprint



    app.register_blueprint(main_blueprint)
    app.register_blueprint(upload_blueprint, url_prefix='/upload')
    app.register_blueprint(graph_blueprint, url_prefix='/graph')
    app.register_blueprint(script_blueprint, url_prefix='/run')
    app.register_blueprint(state_blueprint, url_prefix='/state')

    return app
