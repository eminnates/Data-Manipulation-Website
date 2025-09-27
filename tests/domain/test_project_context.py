import os
import pandas as pd
import pytest
from app.domain.models import ProjectContext

class DummyLogger:
    def __init__(self):
        self.infos = []
        self.errors = []
    def info(self, msg):
        self.infos.append(msg)
    def error(self, msg):
        self.errors.append(msg)

@pytest.fixture()
def temp_upload_dir(tmp_path):
    # Simule edilmiş UPLOAD_FOLDER
    return tmp_path

@pytest.fixture()
def sample_csv_file(temp_upload_dir):
    project = "projA"
    file_name = "data.csv"
    project_dir = temp_upload_dir / project
    project_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"a": [1,2,3], "b": ["x","y","z"]})
    file_path = project_dir / file_name
    df.to_csv(file_path, index=False)
    return project, file_name, file_path

@pytest.fixture()
def sample_xlsx_file(temp_upload_dir):
    project = "projB"
    file_name = "data.xlsx"
    project_dir = temp_upload_dir / project
    project_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"c": [10,20], "d": [0.1, 0.2]})
    file_path = project_dir / file_name
    df.to_excel(file_path, index=False)
    return project, file_name, file_path

def test_path_construction(sample_csv_file, temp_upload_dir):
    project, file_name, file_path = sample_csv_file
    ctx = ProjectContext(project_name=project, file_name=file_name, base_upload_dir=str(temp_upload_dir))
    assert ctx.active_file_path == str(file_path)
    assert ctx.extension == 'csv'

def test_cache_behavior(sample_csv_file, temp_upload_dir):
    project, file_name, file_path = sample_csv_file
    logger = DummyLogger()
    ctx = ProjectContext(project_name=project, file_name=file_name, base_upload_dir=str(temp_upload_dir), logger=logger)
    df1 = ctx.get_data()  # first read -> disk
    df2 = ctx.get_data()  # second read -> cache
    assert df1 is df2
    # logger kayıtlarında iki mesaj bekleriz: init + disk okuma + cache mesajı
    assert any("Disk'ten veri okunup" in m for m in logger.infos)
    assert any("Önbellekten" in m for m in logger.infos)

def test_use_cache_false_forces_reload(sample_csv_file, temp_upload_dir):
    project, file_name, file_path = sample_csv_file
    ctx = ProjectContext(project_name=project, file_name=file_name, base_upload_dir=str(temp_upload_dir))
    first = ctx.get_data()
    # küçük modifikasyon (cache ile karşılaştırma için) - DataFrame objesi değişmeyecek reload yapılırsa farklı id gerekir
    second = ctx.get_data(use_cache=False)
    assert first is not second  # yeniden okuma

def test_missing_file_raises(temp_upload_dir):
    ctx = ProjectContext(project_name="projX", file_name="missing.csv", base_upload_dir=str(temp_upload_dir))
    with pytest.raises(FileNotFoundError):
        ctx.get_data()

def test_xlsx_read(sample_xlsx_file, temp_upload_dir):
    project, file_name, file_path = sample_xlsx_file
    ctx = ProjectContext(project_name=project, file_name=file_name, base_upload_dir=str(temp_upload_dir))
    df = ctx.get_data()
    assert 'c' in df.columns and 'd' in df.columns

def test_unsupported_extension(temp_upload_dir):
    project = "projC"
    file_name = "data.txt"  # desteklenmeyen
    project_dir = os.path.join(str(temp_upload_dir), project)
    os.makedirs(project_dir, exist_ok=True)
    full_path = os.path.join(project_dir, file_name)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write("a|b|c\n1|2|3")
    ctx = ProjectContext(project_name=project, file_name=file_name, base_upload_dir=str(temp_upload_dir))
    with pytest.raises(ValueError):
        ctx.get_data()
