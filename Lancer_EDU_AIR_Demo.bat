@echo off
rem EDU-AIR demo launcher — runs entirely on synthetic input.
rem No webcam, no microphone and no OS interaction: ideal for previews,
rem trainings and hardware-free testing.
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 edu_air_main.py --demo %*
) else (
    python edu_air_main.py --demo %*
)