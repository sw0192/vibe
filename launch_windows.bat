@echo off
setlocal

set "REPO_URL=https://github.com/sw0192/vibe.git"
set "APP_DIR=%USERPROFILE%\vibe-file-converter"
set "GIT_EXE=git"
set "PYTHON_CMD=python"

echo.
echo FILE CONVERTER launcher
echo =======================
echo.

where git >nul 2>nul
if errorlevel 1 (
  if exist "%ProgramFiles%\Git\cmd\git.exe" (
    set "GIT_EXE=%ProgramFiles%\Git\cmd\git.exe"
  ) else (
    echo Git was not found.
    echo Install Git for Windows from https://git-scm.com/download/win
    pause
    exit /b 1
  )
)

python --version >nul 2>nul
if errorlevel 1 (
  py -3 --version >nul 2>nul
  if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3 from https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )
  set "PYTHON_CMD=py -3"
)

if exist "%APP_DIR%\.git" (
  echo Updating the latest code...
  cd /d "%APP_DIR%" || exit /b 1
  "%GIT_EXE%" pull --ff-only
) else (
  if exist "%APP_DIR%" (
    echo "%APP_DIR%" already exists, but it is not a git repository.
    echo Rename or delete that folder, then run this launcher again.
    pause
    exit /b 1
  )

  echo Cloning the app from GitHub...
  "%GIT_EXE%" clone "%REPO_URL%" "%APP_DIR%"
  cd /d "%APP_DIR%" || exit /b 1
)

if errorlevel 1 (
  echo Failed to clone or update the app.
  pause
  exit /b 1
)

echo Preparing the Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
)

if errorlevel 1 (
  echo Failed to create the Python virtual environment.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Installing required libraries...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
  echo Failed to install required libraries.
  pause
  exit /b 1
)

echo Starting the converter. Your browser will open automatically.
python run_converter.py

echo.
echo The converter has stopped.
pause
