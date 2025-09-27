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
    app = current_app
    if app.config.get('WEBSOCKET_AUTH_ENABLED', True):
        # Token query=?token= or header Authorization
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.lower().startswith('bearer '):
                token = auth_header.split(' ',1)[1].strip()
        if not token:
            return False  # reject
        try:
            claims = decode_token(token)
            request.environ['ws.identity'] = claims.get('sub')
        except AuthError:
            return False
    print("Bir istemci WebSocket ile bağlandı.")

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

