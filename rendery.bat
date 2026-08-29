@echo off
REM RenderY launcher - PYTHONUTF8=1 BAT BUOC (bay encoding Windows, xem CLAUDE.md)
cd /d "%~dp0autoedit"
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m autoedit.cli %*
