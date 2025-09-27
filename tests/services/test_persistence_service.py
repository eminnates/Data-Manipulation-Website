import os
import io
import pandas as pd
import pytest
from app.services.persistence_service import PersistenceService

class DummyLogger:
    def __init__(self):
        self.records = []
    def info(self, msg, **ctx):
        self.records.append(("info", msg, ctx))
    def warning(self, msg, **ctx):
        self.records.append(("warning", msg, ctx))
    def error(self, msg, **ctx):
        self.records.append(("error", msg, ctx))

@pytest.fixture()
def df():
    return pd.DataFrame({"a": [1,2], "b": [3,4]})

@pytest.fixture()
def logger():
    return DummyLogger()

@pytest.fixture()
def service(logger):
    return PersistenceService(logger)


def test_save_csv_success(tmp_path, df, service, logger):
    target = tmp_path / "out.csv"
    result = service.save_csv(df, str(target))
    assert result.success
    assert result.path == str(target)
    assert os.path.exists(result.path)
    # ensure log captured
    assert any(r[0] == 'info' and 'Data persisted' in r[1] for r in logger.records)


def test_save_csv_default_path(df, service, logger, monkeypatch, tmp_path):
    # Force cwd to temp so default path resolves inside temp
    monkeypatch.chdir(tmp_path)
    result = service.save_csv(df, None)
    assert result.success
    assert result.path.endswith(os.path.join('app','static','temp','processed_data.csv'))
    assert os.path.exists(result.path)


def test_save_csv_failure(df, service, logger, monkeypatch):
    # Simulate failure by making to_csv raise
    def boom(*args, **kwargs):
        raise IOError("disk full")
    monkeypatch.setattr(df, 'to_csv', boom)
    result = service.save_csv(df, None)
    assert not result.success
    assert result.error == 'disk full'
    assert any(r[0] == 'error' for r in logger.records)
