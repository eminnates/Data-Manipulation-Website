from flask import Blueprint, jsonify, current_app, g
from app.infrastructure import metrics
from app.utils.auth import jwt_required
from app.utils.rate_limit import check_rate_limit

status_blueprint = Blueprint('status', __name__)

@status_blueprint.get('/health')
def health():
    app = current_app
    channel = app.config.get('LOG_CHANNEL_NAME')
    redis_ok = False
    redis_error = None
    if app.config.get('ENABLE_REDIS_LISTENER', True):
        try:
            # Lazy import to avoid circular
            from app.features.redis.redis_client import get_redis_client
            r = get_redis_client()
            pong = r.ping()
            redis_ok = bool(pong)
        except Exception as e:
            redis_error = str(e)
    socketio_enabled = 'socketio' in app.extensions
    return jsonify({
        'status': 'ok',
        'redis': {'enabled': app.config.get('ENABLE_REDIS_LISTENER', True), 'alive': redis_ok, 'error': redis_error},
        'socketio': {'enabled': socketio_enabled},
        'log_channel': channel
    })

@status_blueprint.get('/metrics')
@jwt_required
def metrics_endpoint():
    """Basit JSON metrics çıktısı.

    Not: Üretimde Prometheus formatına çevirmek için ayrı adapter gerekebilir.
    """
    identity = getattr(g, 'identity', 'anon')
    rl = check_rate_limit(identity, 'http_metrics')
    if not rl.allowed:
        resp = jsonify({'error': 'rate_limit_exceeded', 'reset': rl.reset})
        for k, v in rl.to_headers().items():
            resp.headers[k] = v
        return resp, 429
    snap = metrics.snapshot()
    resp = jsonify(snap)
    for k, v in rl.to_headers().items():
        resp.headers[k] = v
    return resp
