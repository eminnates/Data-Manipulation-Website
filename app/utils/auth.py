import time
import typing as t
from functools import wraps
from flask import current_app, request, jsonify, g

class AuthError(Exception):
    pass

def create_token(identity: str, claims: t.Optional[dict] = None, expires_in: int | None = None) -> str:
    """Create a JWT for given identity.

    This helper is mainly for tests or manual token seeding. In production you would
    have a proper login exchanging credentials for a token.
    """
    cfg = current_app.config if current_app else {}
    secret = cfg.get('JWT_SECRET', 'change-me-dev-secret')
    alg = cfg.get('JWT_ALG', 'HS256')
    exp_seconds = expires_in if expires_in is not None else cfg.get('JWT_EXP_SECONDS', 3600)
    now = int(time.time())
    payload = {
        'sub': identity,
        'iat': now,
        'exp': now + int(exp_seconds)
    }
    if claims:
        # Avoid overwriting reserved claims
        for k, v in claims.items():
            if k not in ('sub', 'iat', 'exp'):
                payload[k] = v
    import jwt  # lazy import
    token = jwt.encode(payload, secret, algorithm=alg)
    # PyJWT >=2 returns str
    return token

def decode_token(token: str) -> dict:
    cfg = current_app.config
    secret = cfg.get('JWT_SECRET')
    alg = cfg.get('JWT_ALG', 'HS256')
    try:
        import jwt  # lazy import
        data = jwt.decode(token, secret, algorithms=[alg])
        return data
    except jwt.ExpiredSignatureError as e:
        raise AuthError('Token expired') from e
    except jwt.InvalidTokenError as e:
        raise AuthError('Invalid token') from e

def extract_bearer_token() -> str | None:
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    if not auth_header.lower().startswith('bearer '):
        return None
    return auth_header.split(' ', 1)[1].strip()

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_app.config.get('WEBSOCKET_AUTH_ENABLED', True):
            return fn(*args, **kwargs)
        token = extract_bearer_token()
        if not token:
            return jsonify({'error': 'Missing bearer token'}), 401
        try:
            claims = decode_token(token)
        except AuthError as e:
            return jsonify({'error': str(e)}), 401
        # Attach identity for downstream usage
        g.identity = claims.get('sub')
        g.jwt_claims = claims
        return fn(*args, **kwargs)
    return wrapper

def build_rate_limit_key(identity: str, scope: str) -> str:
    return f"rl:{identity}:{scope}"
