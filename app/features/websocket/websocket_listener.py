import eventlet
from app.features.redis.redis_client import get_redis_client
from app.features.websocket.events import send_log_to_clients

def start_redis_listener(app):
    def listener():
        with app.app_context():
            print("Redis listener started...")
            redis_client = get_redis_client()
            pubsub = redis_client.pubsub()
            pubsub.subscribe('log_channel')
            print("Subscribed to log_channel")
            for message in pubsub.listen():
                if message['type'] == 'message':
                    if isinstance(message['data'], bytes):
                        log_data = message['data'].decode('utf-8')
                    else:
                        log_data = str(message['data'])
                    print(f"Received message: {log_data}")
                    send_log_to_clients(log_data)
                    print(f"Emitted message via helper function: {log_data}")

    eventlet.spawn(listener)
