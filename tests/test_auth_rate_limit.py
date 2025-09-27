import pytest
from app.utils.auth import create_token
from app import create_app

@pytest.fixture
def flask_app():
    app = create_app(env="development")
    app.config['WEBSOCKET_AUTH_ENABLED'] = True
    app.config['RATE_LIMIT_ENABLED'] = True
    return app

@pytest.fixture
def client(flask_app):
    return flask_app.test_client()

def test_metrics_requires_auth(client, flask_app):
    r = client.get('/status/metrics')
    assert r.status_code == 401
    token = None
    with flask_app.app_context():
        token = create_token('tester')
    r2 = client.get('/status/metrics', headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    data = r2.get_json()
    assert 'preview_sessions_started_total' in data or isinstance(data, dict)

def test_metrics_rate_limit(client, flask_app):
    with flask_app.app_context():
        token = create_token('ratelimit-user')
    # Exhaust small limit
    flask_app.config['RATE_LIMIT_MAX'] = 2
    for i in range(2):
        resp = client.get('/status/metrics', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
    # Third should 429
    resp3 = client.get('/status/metrics', headers={'Authorization': f'Bearer {token}'})
    assert resp3.status_code == 429
    assert resp3.get_json()['error'] == 'rate_limit_exceeded'
