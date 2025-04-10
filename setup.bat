@echo off
setlocal

echo Python ve pip kurulumu kontrol ediliyor...
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python bulunamadi, indiriliyor...
    curl -o python-installer.exe https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe
    echo Python yukleniyor...
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
)

echo Python PATH'e eklendi, pip guncelleniyor...
python -m ensurepip
python -m pip install --upgrade pip

echo Gerekli kutuphaneler yukleniyor...
pip install Flask pandas seaborn matplotlib jinja2 plotly

echo Kurulum tamamlandi!
python main.py
