@echo off
REM Treatment — ban kich ban + kiem chung nguon (module cua RenderY, cong 9121).
REM Khac web.bat (9118 — day chuyen dung): hai tien trinh rieng, restart doc lap.
setlocal
cd /d %~dp0autoedit
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=.
if "%KICHBAN_DB%"=="" set KICHBAN_DB=F:\AutoEdit\kichban\kichban.db
echo Treatment -^> http://127.0.0.1:9121
.venv\Scripts\python.exe -m uvicorn autoedit.treatment.app:tao_app_mac_dinh --factory --host 0.0.0.0 --port 9121
endlocal
