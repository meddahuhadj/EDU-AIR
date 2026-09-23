@echo off
rem EDU-AIR Web Bridge v1.1
rem Sert l'app en LOCAL (http://localhost:8080) + WebSocket (ws://localhost:8765)
rem Chrome autorise ws:// depuis http://, donc le mode REEL fonctionne !
setlocal
cd /d "%~dp0"
echo.
echo  ══════════════════════════════════════════════════════
echo   EDU-AIR  Mode Reel Web  —  v1.1
echo  ══════════════════════════════════════════════════════
echo   Apres le demarrage, ouvrez dans Chrome :
echo.
echo     http://localhost:8080
echo.
echo   Le badge passera de DEMO a  REEL automatiquement.
echo  ══════════════════════════════════════════════════════
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -m pip install websockets -q
    py -3.12 web_bridge.py %*
) else (
    python -m pip install websockets -q
    python web_bridge.py %*
)
pause
