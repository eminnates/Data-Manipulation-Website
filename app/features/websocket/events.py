from app.features.websocket.extensions import socketio
from flask import current_app, request
from flask_socketio import emit, disconnect
from app.utils.auth import decode_token, AuthError
from app.utils.rate_limit import check_rate_limit

# Alt event modüllerini import ederek handler kayıtlarını gerçekleştir.
from app.features.websocket import events_preview  # noqa: F401
from app.features.websocket import events_suitability  # noqa: F401
from app.features.websocket import events_data_info  # noqa: F401

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket client connections."""
    current_app.logger.info("Bir istemci WebSocket ile bağlandı.")
    emit('connection_confirmed', {'message': 'WebSocket connection established'})

@socketio.on('test_event')
def handle_test_event(data):
    emit('test_response', {'message': 'Test event received successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    print("[DEBUG] Client disconnected from WebSocket")

def send_log_to_clients(log_message):
    """Emit a log event to websocket clients.

    Accepts either plain string or dict with keys: log, level, ctx.
    """
    if isinstance(log_message, dict):
        payload = {
            'log': log_message.get('log'),
            'level': log_message.get('level'),
            'ctx': log_message.get('ctx')
        }
    else:
        payload = {'log': str(log_message), 'level': None, 'ctx': None}
    socketio.emit('log_message', payload)

