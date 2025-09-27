import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app(env="testing")
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200


def test_hakkimizda_route(client):
    response = client.get('/hakkimizda')
    assert response.status_code == 200


def test_iletisim_route(client):
    response = client.get('/iletisim')
    assert response.status_code == 200

