import os
import tempfile
import logging
import pytest
from app import create_app
from app.routes.download_routes import get_processed_data_file, check_processed_file_logic

@pytest.fixture
def app():
    app = create_app(env="testing")
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class DummyLogger:
    def __init__(self):
        self.messages = []
    def warn(self, msg):
        self.messages.append(('warn', msg))
    def error(self, msg):
        self.messages.append(('error', msg))

def test_get_processed_data_file_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Sahte config ve logger
        config = {'TEMP_FOLDER': ''}
        logger = DummyLogger()
        root_path = temp_dir
        # Dosya oluştur
        file_path = os.path.join(temp_dir, 'processed_data.csv')
        with open(file_path, 'w') as f:
            f.write('test')
        result, error = get_processed_data_file(config, logger, root_path)
        assert result == file_path
        assert error is None

def test_get_processed_data_file_not_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {'TEMP_FOLDER': ''}
        logger = DummyLogger()
        root_path = temp_dir
        result, error = get_processed_data_file(config, logger, root_path)
        assert result is None
        assert "İşlenmiş veri bulunamadı" in error
        assert logger.messages and logger.messages[0][0] == 'warn'

def test_check_processed_file_logic_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {'TEMP_FOLDER': ''}
        logger = DummyLogger()
        root_path = temp_dir
        file_path = os.path.join(temp_dir, 'processed_data.csv')
        with open(file_path, 'w') as f:
            f.write('test')
        assert check_processed_file_logic(config, logger, root_path) is True

def test_check_processed_file_logic_not_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {'TEMP_FOLDER': ''}
        logger = DummyLogger()
        root_path = temp_dir
        assert check_processed_file_logic(config, logger, root_path) is False