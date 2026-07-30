@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m opportunity_scout.main
) else (
  python -m opportunity_scout.main
)
pause
