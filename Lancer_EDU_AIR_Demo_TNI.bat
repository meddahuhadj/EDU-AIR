@echo off
rem EDU-AIR interactive-whiteboard (TNI) demo launcher.
rem Plays the scripted board lesson live: pages, strokes, grid background,
rem undo and page delete are all visible in the window.
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 edu_air_main.py --demo --demo-board %*
) else (
    python edu_air_main.py --demo --demo-board %*
)