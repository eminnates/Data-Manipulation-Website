import eventlet
eventlet.monkey_patch()

import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.features.websocket.extensions import socketio

# Ortam belirleme (default: production)
env = os.environ.get('APP_ENV', 'production')
app = create_app(env=env)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
