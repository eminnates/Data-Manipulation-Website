import eventlet
import json
import time
import os
from app.features.redis.redis_client import get_redis_client
from app.features.websocket.events import send_log_to_clients

def start_redis_listener(app):
    """Start a green thread to listen Redis pub/sub for log channel.

    Enhancements:
      - Exponential backoff retry (configurable attempt cap)
      - Optional JSON log formatting (LOG_JSON=1)
      - Defensive parse with structured fallback
    """
    if not app.config.get('ENABLE_REDIS_LISTENER', True):
        app.logger.info('redis.listener.disabled')
        return

    channel = app.config.get('LOG_CHANNEL_NAME', 'log_channel')
    json_mode = (str(app.config.get('LOG_JSON', os.environ.get('LOG_JSON', '0'))).lower() in ('1','true','yes'))

    def _serialize(level: str, msg: str, **ctx):
        if not json_mode:
            if ctx:
                suffix = ' '.join(f"{k}={v}" for k, v in ctx.items())
                return f"{msg} {suffix}"
            return msg
        payload = {'level': level, 'message': msg, 'ctx': ctx or None}
        try:
            return json.dumps(payload, ensure_ascii=False)
        except Exception:
            return f"{msg} serialization_error=1"

    def _log(level: str, msg: str, **ctx):
        getattr(app.logger, level)(_serialize(level, msg, **ctx))

    def listener():
        def inner():
            max_attempts = int(os.environ.get('REDIS_LISTENER_MAX_ATTEMPTS', '6'))  # ~ up to ~127s with base 1s
            base_sleep = float(os.environ.get('REDIS_LISTENER_BACKOFF_BASE', '1.0'))
            attempt = 0
            while True:
                attempt += 1
                _log('info', 'redis.listener.starting', channel=channel, attempt=attempt)
                try:
                    redis_client = get_redis_client()
                    pubsub = redis_client.pubsub()
                    pubsub.subscribe(channel)
                    _log('info', 'redis.listener.subscribed', channel=channel)
                    for message in pubsub.listen():
                        if message.get('type') != 'message':
                            continue
                        raw = message.get('data')
                        if isinstance(raw, bytes):
                            raw_text = raw.decode('utf-8', errors='replace')
                        else:
                            raw_text = str(raw)
                        level = None
                        ctx = None
                        out_msg = raw_text
                        try:
                            parsed = json.loads(raw_text)
                            if isinstance(parsed, dict):
                                level = parsed.get('level')
                                out_msg = parsed.get('message', raw_text)
                                ctx = parsed.get('ctx')
                        except Exception:
                            pass
                        send_log_to_clients({'log': out_msg, 'level': level, 'ctx': ctx})
                except Exception as e:
                    _log('warning', 'redis.listener.error', channel=channel, error=str(e), attempt=attempt)
                    if attempt >= max_attempts:
                        _log('error', 'redis.listener.giveup', channel=channel, attempts=attempt)
                        break
                    sleep_for = base_sleep * (2 ** (attempt - 1))
                    sleep_for = min(sleep_for, 60.0)
                    _log('info', 'redis.listener.retrying', in_seconds=round(sleep_for,2))
                    eventlet.sleep(sleep_for)
                    continue
                else:
                    _log('warning', 'redis.listener.disconnected', channel=channel)
                    if attempt >= max_attempts:
                        _log('error', 'redis.listener.giveup', channel=channel, attempts=attempt)
                        break
                    eventlet.sleep(base_sleep)
                    continue
                break
        if hasattr(app, 'app_context'):
            with app.app_context():
                inner()
        else:
            inner()

    try:
        eventlet.spawn(listener)
        _log('info', 'redis.listener.spawned', channel=channel)
    except Exception as e:
        _log('error', 'redis.listener.spawn.fail', channel=channel, error=str(e))
