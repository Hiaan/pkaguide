@echo off
cd /d "%~dp0"
python build_items_db.py
python pka_overlay.py
pause
