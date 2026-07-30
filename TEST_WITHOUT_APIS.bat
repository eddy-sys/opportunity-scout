@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m opportunity_scout.main --sample --mock-scoring --dry-run
) else (
  python -m opportunity_scout.main --sample --mock-scoring --dry-run
)
pause
