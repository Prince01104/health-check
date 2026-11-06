@echo off
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python -m uvicorn backend.main:app --port 8000
pause
