@echo off
REM Factcheck — ban kich ban + kiem chung nguon. Cong 9121.
REM venv: dung chung venv cua RenderY tren may chu; may khac thi doi PY o duoi.
setlocal
set PY=F:\RenderY\autoedit\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%~dp0;F:\RenderY\autoedit
if "%KICHBAN_DB%"=="" set KICHBAN_DB=F:\AutoEdit\kichban\kichban.db

echo Factcheck -^> http://127.0.0.1:9121
"%PY%" -m uvicorn factcheck.app:tao_app_mac_dinh --factory --host 0.0.0.0 --port 9121
endlocal
