import os
import json
import pandas as pd
import pytest
from types import SimpleNamespace

from app.services.visualization_service import VisualizationService
from app.services.path_builder import PathBuilder

class DummyLogger:
    def __init__(self):
        self.events = []
    def info(self, msg, **ctx):
        self.events.append(('info', msg, ctx))
    def warning(self, msg, **ctx):
        self.events.append(('warning', msg, ctx))
    def error(self, msg, **ctx):
        self.events.append(('error', msg, ctx))

class DummyFigure:
    def __init__(self):
        self.json_written = False
        self.html_written = False
    def write_json(self, path):
        # Simulate write by creating file with simple JSON
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'dummy': True}, f)
        self.json_written = True
    def write_html(self, path):  # not used but present for completeness
        with open(path, 'w', encoding='utf-8') as f:
            f.write('<html></html>')
        self.html_written = True

class DummyGenerator:
    def __init__(self, data_df, project_name, plot_type, x_col, y_col=None, output_type='raw', logger=None, path_builder=None):
        self._figure = DummyFigure()
        self._project = project_name
        self._output_type = output_type
        self._logger = logger
        self._path_builder = path_builder
    def generate_figure(self):
        return self._figure
    def build_output_path(self, extension: str):
        return self._path_builder.visualization(self._project, self._output_type, extension)

@pytest.fixture
def temp_path_builder(tmp_path):
    output = tmp_path / 'outputs'
    temp = tmp_path / 'temp'
    upload = tmp_path / 'uploads'
    output.mkdir(); temp.mkdir(); upload.mkdir()
    return PathBuilder(base_output=str(output), base_temp=str(temp), base_upload=str(upload))

@pytest.fixture
def logger():
    return DummyLogger()

@pytest.fixture
def service(logger, temp_path_builder):
    # Inject DummyGenerator via generator_cls param
    return VisualizationService(logger=logger, generator_cls=DummyGenerator, path_builder=temp_path_builder)

@pytest.fixture
def sample_df():
    return pd.DataFrame({'a':[1,2,3], 'b':[4,5,6]})


def test_generate_success_creates_json_file(service, sample_df, temp_path_builder, logger):
    params = {
        'plot_type': 'Bar',
        'x_col': 'a',
        'y_col': 'b',
        'output_type': 'raw'
    }
    result = service.generate(sample_df, 'projX', params)
    assert result.success is True
    assert result.path is not None
    assert os.path.exists(result.path)
    # File content sanity
    with open(result.path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data.get('dummy') is True
    # Logger captured save event
    assert any(evt for evt in logger.events if evt[0]=='info' and 'Visualization saved' in evt[1])


def test_generate_validation_failure(service, sample_df):
    # Missing plot_type -> validation should fail
    bad_params = {'x_col':'a'}
    result = service.generate(sample_df, 'projX', bad_params)
    assert result.success is False
    assert 'plot_type' in (result.error or '')


def test_generate_write_error(monkeypatch, service, sample_df, logger):
    params = {'plot_type':'Bar','x_col':'a','y_col':'b','output_type':'raw'}
    # Force write_json to raise
    def boom(path):
        raise IOError('disk full')
    dummy_gen = service._generator_cls(sample_df, 'projX', 'Bar', 'a', 'b', 'raw', logger, service._path_builder)
    fig = dummy_gen.generate_figure()
    monkeypatch.setattr(fig, 'write_json', boom)
    # Monkeypatch service to return our prepared generator
    original_cls = service._generator_cls
    service._generator_cls = lambda *a, **k: dummy_gen
    try:
        result = service.generate(sample_df, 'projX', params)
    finally:
        service._generator_cls = original_cls
    assert result.success is False
    assert 'disk full' in (result.error or '')
    assert any(evt for evt in logger.events if evt[0]=='error' and 'Visualization write error' in evt[1])
