import types
import pytest

class DummyApp:
    def __init__(self):
        self.config = {
            'ENABLE_REDIS_LISTENER': True,
            'LOG_CHANNEL_NAME': 'test_channel'
        }
        self.extensions = {}
        self._logs = []
    class Logger:
        def __init__(self, outer):
            self.outer = outer
        def info(self, msg, **ctx):
            self.outer._logs.append(('info', msg, ctx))
        def warning(self, msg, **ctx):
            self.outer._logs.append(('warning', msg, ctx))
        def error(self, msg, **ctx):
            self.outer._logs.append(('error', msg, ctx))
    @property
    def logger(self):
        return self._logger
    @logger.setter
    def logger(self, v):
        self._logger = v

@pytest.fixture
def failing_app(monkeypatch):
    from app.features.websocket import websocket_listener as wl
    app = DummyApp()
    app.logger = DummyApp.Logger(app)

    # get_redis_client her çağrıda hata fırlatsın
    def fail(): raise RuntimeError('redis down')
    # Patch both original redis client path and already imported symbol in listener module
    monkeypatch.setattr('app.features.redis.redis_client.get_redis_client', fail, raising=True)
    monkeypatch.setattr(wl, 'get_redis_client', fail, raising=True)

    # eventlet.spawn yerine senkron çağrı yakalayacağız
    class DummyEventlet:
        @staticmethod
        def spawn(fn):
            # Fonksiyonu bir defa çağır (içinde sonsuz while, ilk hata sonrası sleep öncesi çıkıyoruz)
            try:
                gen = fn()
            except Exception:
                pass
    monkeypatch.setattr(wl, 'eventlet', DummyEventlet)
    return app


def test_redis_listener_graceful_failure(failing_app):
    from app.features.websocket.websocket_listener import start_redis_listener
    # Hata yutulmalı ve warning loglanmalı
    start_redis_listener(failing_app)
    warnings = [e for e in failing_app._logs if e[0] in ('warning','error','info')]
    assert any(
        'redis.listener.error' in w[1] or 'redis.listener.spawn.fail' in w[1]
        for w in warnings
    ), failing_app._logs
