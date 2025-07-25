from flask_socketio import SocketIO
import os

socketio = SocketIO(
    async_mode='eventlet',
    message_queue=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)
