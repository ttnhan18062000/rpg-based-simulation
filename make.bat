@echo off
setlocal

:: RPG Simulation Engine - Task Runner (Windows)
:: Usage: make [command]

if "%~1"=="" goto help
if "%~1"=="help" goto help
if "%~1"=="install" goto install
if "%~1"=="install-py" goto install-py
if "%~1"=="install-fe" goto install-fe
if "%~1"=="build" goto build
if "%~1"=="dev" goto dev
if "%~1"=="dev-backend" goto dev-backend
if "%~1"=="dev-frontend" goto dev-frontend
if "%~1"=="serve" goto serve
if "%~1"=="serve-only" goto serve-only
if "%~1"=="cli" goto cli
if "%~1"=="lint" goto lint
if "%~1"=="typecheck" goto typecheck
if "%~1"=="clean" goto clean

echo Unknown command: %~1
echo Run 'make help' to see available commands.
exit /b 1

:help
echo.
echo   RPG Simulation Engine - Task Runner
echo   =====================================
echo.
echo   install          Install all dependencies (Python + Node)
echo   install-py       Install Python dependencies
echo   install-fe       Install frontend Node dependencies
echo   build            Build frontend for production
echo   dev              Start backend + frontend dev server (hot reload)
echo   dev-backend      Start only the backend server
echo   dev-frontend     Start only the frontend dev server
echo   serve            Build frontend + start production server
echo   serve-only       Start production server (assumes frontend already built)
echo   cli              Run headless simulation (200 ticks)
echo   lint             Run linters (frontend)
echo   typecheck        Run TypeScript type checking
echo   clean            Remove build artifacts
echo.
exit /b 0

:install
call :install-py
if errorlevel 1 exit /b 1
call :install-fe
exit /b %errorlevel%

:install-py
echo Installing Python dependencies...
pip install -r requirements.txt
exit /b %errorlevel%

:install-fe
echo Installing frontend dependencies...
pushd frontend
call npm install
popd
exit /b %errorlevel%

:build
echo Building frontend for production...
pushd frontend
call npm run build
popd
exit /b %errorlevel%

:dev
echo Starting backend on :8000 and frontend dev server on :5173...
echo Press Ctrl+C to stop.
echo.
start "RPG-Backend" cmd /c "python -m src serve --port 8000"
pushd frontend
call npm run dev
popd
taskkill /FI "WINDOWTITLE eq RPG-Backend*" /F >nul 2>&1
exit /b 0

:dev-backend
echo Starting backend server...
python -m src serve --port 8000
exit /b %errorlevel%

:dev-frontend
echo Starting frontend dev server...
pushd frontend
call npm run dev
popd
exit /b %errorlevel%

:serve
call :build
if errorlevel 1 exit /b 1
echo Starting production server...
python -m src serve --port 8000
exit /b %errorlevel%

:serve-only
echo Starting production server...
python -m src serve --port 8000
exit /b %errorlevel%

:cli
python -m src cli --ticks 200 --seed 42
exit /b %errorlevel%

:lint
pushd frontend
call npm run lint
popd
exit /b %errorlevel%

:typecheck
pushd frontend
call npx tsc --noEmit
popd
exit /b %errorlevel%

:clean
echo Cleaning build artifacts...
if exist frontend\dist rmdir /s /q frontend\dist
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Done.
exit /b 0
