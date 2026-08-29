@echo off
REM Chay bo test RenderY
cd /d "%~dp0autoedit"
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m pytest tests -q --no-header %*
