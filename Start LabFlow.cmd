@echo off
cd /d "%~dp0"
echo LabFlow patient flow: http://127.0.0.1:8790
echo Keep this window open. Press Ctrl+C to stop.
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8790"
".venv\Scripts\python.exe" -m uvicorn labflow.app:app --host 127.0.0.1 --port 8790 --workers 1
pause
