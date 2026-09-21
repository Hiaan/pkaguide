@echo off
REM Gera dist\PKA GUIDE Setup.exe  (instalador unico que instala o app em pasta, sem extrair em Temp a cada abertura)
cd /d "%~dp0"
python build_items_db.py
python build_hub_db.py
rmdir /s /q build dist 2>nul
echo === 1/3 compilando o app (pasta)
pyinstaller --noconfirm --clean --onedir --windowed --name "PKA GUIDE" --icon logo.ico ^
  --add-data "items_db.json;." --add-data "tasks_db.json;." --add-data "hub_db.json;." --add-data "videos_db.json;." --add-data "logo.ico;." --add-data "logo_small.png;." ^
  --collect-all rapidocr_onnxruntime --hidden-import pynput.mouse._win32 --hidden-import pynput.keyboard._win32 pka_overlay.py
echo === 2/3 compactando
python -c "import shutil; shutil.make_archive('app','zip','dist/PKA GUIDE')"
echo === 3/3 compilando o instalador
pyinstaller --noconfirm --clean --onefile --windowed --name "PKA GUIDE Setup" --icon logo.ico ^
  --add-data "app.zip;." --add-data "logo.ico;." --add-data "logo_small.png;." installer.py
del app.zip
echo.
echo Pronto: dist\PKA GUIDE Setup.exe
