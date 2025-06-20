from app.features.websocket.extensions import socketio
@socketio.on('connect')
def handle_connect():
    print("Bir istemci WebSocket ile bağlandı.")

def send_log_to_clients(log_message):
    socketio.emit('log_message', {'log': log_message})