import os
import pandas as pd
import pytest
from app.services.persistence_service import PersistenceService

class DummyLogger:
    def __init__(self):
        self.events = []
    def info(self, msg, **ctx): self.events.append(('info', msg, ctx))
    def warning(self, msg, **ctx): self.events.append(('warning', msg, ctx))
    def error(self, msg, **ctx): self.events.append(('error', msg, ctx))

@pytest.fixture()
def df():
    return pd.DataFrame({'a':[1,2,3],'b':['x','y','z']})

@pytest.fixture()
def service():
    return PersistenceService(DummyLogger())

@pytest.mark.parametrize('fmt', ['csv','parquet'])
def test_save_data_formats(tmp_path, df, service, fmt):
    target = tmp_path / f'data_output.{fmt}'
    result = service.save_data(df, str(target), format=fmt)
    if fmt == 'parquet' and (not result.success):
        # Missing engine scenario -> skip
        if result.error and 'engine' in result.error.lower():
            pytest.skip(f"Parquet engine missing: {result.error}")
    assert result.success
    assert result.path and os.path.exists(result.path)
    if fmt == 'csv':
        loaded = pd.read_csv(result.path)
    else:
        loaded = pd.read_parquet(result.path)
    assert list(loaded.columns) == ['a','b']


def test_extension_auto_adjust(tmp_path, df, service):
    # Provide wrong extension; should auto-fix
    target = tmp_path / 'mydata.txt'
    result = service.save_data(df, str(target), format='parquet')
    if not result.success and 'engine' in (result.error or '').lower():
        pytest.skip('Parquet engine not installed')
    assert result.path.endswith('.parquet')


def test_parquet_failure(monkeypatch, tmp_path, df, service):
    # Force parquet write failure
    def boom(*args, **kwargs):
        raise RuntimeError('write fail')
    monkeypatch.setattr(pd.DataFrame, 'to_parquet', boom)
    res = service.save_data(df, tmp_path / 'file.parquet', format='parquet')
    assert not res.success
    assert 'write fail' in (res.error or '')
