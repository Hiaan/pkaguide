@echo off
REM Gera dist\PKA Guide Overlay.exe (executavel unico, instala sozinho na primeira execucao)
cd /d "%~dp0"
python build_items_db.py
pyinstaller --noconfirm --clean --onefile --windowed --name "PKA Guide Overlay" --icon logo.ico ^
  --add-data "items_db.json;." --add-data "logo.ico;." --add-data "logo_small.png;." ^
  --collect-all rapidocr_onnxruntime --hidden-import pynput.mouse._win32 pka_overlay.py
echo.
echo Pronto: dist\PKA Guide Overlay.exe
