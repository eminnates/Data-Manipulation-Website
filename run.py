import eventlet
eventlet.monkey_patch()

from app import create_app
from app.features.websocket.extensions import socketio  # socketio objesi buradaysa

app = create_app(testing=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
