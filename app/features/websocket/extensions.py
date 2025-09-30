from flask_socketio import SocketIO
import os

socketio = SocketIO(
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)
