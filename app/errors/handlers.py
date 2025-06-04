import traceback
import logging
from flask import jsonify, request, current_app
from app.errors.APIError import APIError

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({'error': 'Page not found'}), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"""
        Error: {str(e)}
        Path: {request.path}
        Method: {request.method}
        IP: {request.remote_addr}
        Traceback: {traceback.format_exc()}
        """)
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
        
    # Ek hata işleyiciler eklenebilir