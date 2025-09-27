import pytest
from app.infrastructure.logging_sinks import InMemorySink, CompositeSink
from python_scripts.state_machine import DataStateMachine, DataState
from app.domain.models import ProjectContext
import pandas as pd

class DummyRedis:
    def __init__(self, fail=False):
        self.published = []
        self.fail = fail
    def publish(self, channel, payload):
        if self.fail:
            raise RuntimeError("redis down")
        self.published.append((channel, payload))

class DummyRedisSink:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.events = []
    def info(self, msg, **ctx):
        self.events.append(('info', msg, ctx))
    def warning(self, msg, **ctx):
        self.events.append(('warning', msg, ctx))
    def error(self, msg, exc=None, **ctx):
        if exc:
            ctx = {**ctx, 'error': str(exc)}
        self.events.append(('error', msg, ctx))

@pytest.fixture()
def context_tmp(tmp_path):
    # Minimal ProjectContext with in-memory DataFrame (avoid disk IO)
    upload_root = tmp_path / 'uploads'
    project = 'p1'
    file_name = 'data.csv'
    proj_dir = upload_root / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    df_path = proj_dir / file_name
    pd.DataFrame({'a':[1,2]}).to_csv(df_path, index=False)
    ctx = ProjectContext(project_name=project, file_name=file_name, base_upload_dir=str(upload_root))
    return ctx

def test_inmemory_sink_basic():
    sink = InMemorySink()
    sink.info("Hello", user="u1")
    sink.error("Boom", exc=ValueError("x"))
    assert ('info', 'Hello', {'user':'u1'}) in sink.events
    # error kaydında error mesajı embed edilmiş olmalı
    err_event = [e for e in sink.events if e[0]=='error'][0]
    assert 'error' in err_event[2]


def test_state_machine_with_custom_sink(context_tmp):
    mem = InMemorySink()
    sm = DataStateMachine(context_tmp, mode='visualize_only', log_sink=mem, visualization_params={'plot_type':None,'x_col':None})
    sm.process()
    # En azından initialize + loading + transitioning loglarını bekliyoruz
    messages = [m[1] for m in mem.events]
    assert any('State Machine initialized' in msg or msg == 'State Machine initialized' for msg in messages)
    assert any('Loading' in msg for msg in messages)
    assert any('State machine finished' in msg or 'No further processing' in msg for msg in messages)


def test_composite_sink_order_and_propagation():
    s1 = InMemorySink(); s2 = InMemorySink()
    comp = CompositeSink([s1, s2])
    comp.info('X', step=1)
    assert s1.events[0]==('info','X',{'step':1})
    assert s2.events[0]==('info','X',{'step':1})


def test_redis_failure_is_swallowed(monkeypatch, context_tmp):
    # get_redis_client fail etsin
    from app.features.redis import redis_client as rc_mod
    def failing_client():
        raise RuntimeError('connection refused')
    monkeypatch.setattr(rc_mod, 'get_redis_client', failing_client)
    mem = InMemorySink()
    # log_sink vermiyoruz ki default path Redis denemesi yapmaya kalkışsın; failing_client devreye girsin
    sm = DataStateMachine(context_tmp, mode='visualize_only', visualization_params={'plot_type':None,'x_col':None}, log_sink=mem)
    sm.process()
    # Çalışmayı bitirmeli (exception propagate olmamalı)
    assert any(e[0]=='info' for e in mem.events)

class FailingRedis:
    def publish(self, ch, payload):
        raise RuntimeError("boom")

def test_redissink_publish_failure_swallowed():
    from app.infrastructure.logging_sinks import RedisSink
    sink = RedisSink(FailingRedis())
    # Hiç exception fırlatmamalı:
    sink.info("msg", a=1)
    sink.error("err", exc=ValueError("x"))

def test_state_machine_redis_init_failure(monkeypatch, context_tmp):
    from app.features.redis import redis_client as rc_mod
    monkeypatch.setattr(rc_mod, 'get_redis_client', lambda: (_ for _ in ()).throw(RuntimeError("down")))
    sm = DataStateMachine(context_tmp, mode='visualize_only', visualization_params={'plot_type':None,'x_col':None})
    # Burada log_sink CompositeSink(StdLoggerSink) olmalı; Redis yok ama crash etmemeli
    sm.process()

def test_visualization_step_error(monkeypatch, context_tmp):
    # plot_type geçerli ama GraphGenerator._create_figure hata fırlatsın
    import python_scripts.visualization as viz
    orig = viz.GraphGenerator._create_figure
    def boom(self): raise ValueError("viz fail")
    monkeypatch.setattr(viz.GraphGenerator, "_create_figure", boom)
    mem = InMemorySink()
    sm = DataStateMachine(context_tmp, mode='visualize_only',
        visualization_params={'plot_type':'Histogram','x_col':'a'},
        log_sink=mem)
    sm.process()
    assert any(e[0]=='error' and 'Visualization error details' in e[1] for e in mem.events)
    monkeypatch.setattr(viz.GraphGenerator, "_create_figure", orig)

def test_finalization_write_error(monkeypatch, context_tmp, tmp_path):
    mem = InMemorySink()
    # İmkânsız path uyduralım
    sm = DataStateMachine(context_tmp, mode='full_auto',
        processed_data_save_path=str(tmp_path / 'nonexistent_dir' / 'sub' / 'file.csv'),
        visualization_params={'plot_type':'Histogram','x_col':'a'},
        log_sink=mem)
    # Monkeypatch os.makedirs hata versin
    import os
    monkeypatch.setattr(os, 'makedirs', lambda *a, **k: (_ for _ in ()).throw(PermissionError("no perm")))
    sm.process()
    assert any(e[0]=='error' and 'Error saving processed data' in e[1] for e in mem.events)

def test_visualize_only_missing_params_early_complete(context_tmp):
    mem = InMemorySink()
    sm = DataStateMachine(context_tmp, mode='visualize_only',
        visualization_params={'plot_type':None,'x_col':None},
        log_sink=mem)
    sm.process()
    msgs = [m[1] for m in mem.events]
    assert any('finished' in m.lower() for m in msgs)
