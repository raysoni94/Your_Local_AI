@echo off
REM run_app.bat
REM Double-click this to launch the local knowledge base UI in your browser.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    echo Activating venv...
    call venv\Scripts\activate.bat
) else (
    echo No venv found in this folder - using system Python.
)

echo.
echo Checking for streamlit...
python -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo.
    echo streamlit is not installed in this Python environment.
    echo Installing dependencies now...
    python -m pip install -r requirements.txt
)

echo.
echo Launching app...
python -m streamlit run app.py

pause