@echo off
REM 141 test. PYTHONUTF8 la BAT BUOC: thieu no la chet UnicodeDecodeError.
setlocal
set PY=F:\RenderY\autoedit\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%~dp0;F:\RenderY\autoedit
"%PY%" -m pytest "%~dp0tests" -q
endlocal
