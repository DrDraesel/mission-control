@echo off
cd /d "%~dp0"
echo Circolo mirror display: LabFlow /mirror on the mirror (1080x1920 portrait)
echo The mirror's IP is DHCP - if it changed, run:  Start Mirror Display.cmd --ip 192.168.1.x
echo Keep this window open. Ctrl+C to stop watching.
".venv\Scripts\python.exe" -m labflow.mirror_display %*
if "%~1"=="" pause
