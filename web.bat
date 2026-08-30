@echo off
REM Bat bang dieu khien web RenderY
cd /d "%~dp0autoedit"
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m autoedit.cli web %*
