@echo off
rem EDU-AIR Web Bridge — connects the Vercel web page to the local Python engine.
rem Launch this, then open https://edu-air-smart-surface.vercel.app
rem The page will auto-switch from DEMO to REEL.
setlocal
cd /d "%~dp0"
echo.
echo  ══════════════════════════════════════════════════
echo   EDU-AIR  Web Bridge  —  Mode Reel dans le navigateur
echo  ══════════════════════════════════════════════════
echo   1. Ce serveur va demarrer sur ws://localhost:8765
echo   2. Ouvrez  https://edu-air-smart-surface.vercel.app
echo   3. La page basculera automatiquement en MODE REEL
echo  ══════════════════════════════════════════════════
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
