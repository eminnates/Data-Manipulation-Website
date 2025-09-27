import pytest
import pandas as pd
from app.routes.state_routes import run_state_machine_background, run_state_machine_logic

class DummyLogger:
    def __init__(self):
        self.messages = []
    def info(self, msg):
        self.messages.append(('info', msg))
    def error(self, msg, **kwargs):
        self.messages.append(('error', msg))

class DummyProjectContext:
    def __init__(self, project_name, file_name):
        self.project_name = project_name
        self.file_name = file_name
        self.active_file_path = 'dummy.csv'
    def get_data(self):
        return pd.DataFrame({'a': [1, 2], 'b': [3, 4]})

def test_run_state_machine_logic_success(tmp_path):
    config = {'TEMP_FOLDER': ''}
    logger = DummyLogger()
    root_path = str(tmp_path)
    file_name = 'test.csv'
    ext = '.csv'
    ext2 = '.json'
    ext3 = '.xlsx'
    mode = 'full_auto'
    output_type = 'raw'
    process_list = []
    project_title = 'test_project'
    visualization_params = {}

    # Fonksiyonu çağır (hata atmamalı, logger'a info yazmalı)
    run_state_machine_logic(
        config, logger, root_path, file_name, ext, mode, output_type, process_list, project_title, visualization_params, project_context_cls=DummyProjectContext
    )
    assert any(m[0] == 'info' for m in logger.messages)
    run_state_machine_logic(
        config, logger, root_path, file_name, ext2, mode, output_type, process_list, project_title, visualization_params, project_context_cls=DummyProjectContext
    )
    assert any(m[0] == 'info' for m in logger.messages)
    run_state_machine_logic(
        config, logger, root_path, file_name, ext3, mode, output_type, process_list, project_title, visualization_params, project_context_cls=DummyProjectContext
    )
    assert any(m[0] == 'info' for m in logger.messages)