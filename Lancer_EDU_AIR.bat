@echo off
rem EDU-AIR launcher — starts the contactless classroom in real mode.
rem Use the second launcher (Lancer_EDU_AIR_Demo.bat) to preview without hardware.
setlocal
cd /d "%~dp0"

rem Prefer Python 3.12 if available (MediaPipe) else fall back to py default.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 edu_air_main.py %*
) else (
    python edu_air_main.py %*
)