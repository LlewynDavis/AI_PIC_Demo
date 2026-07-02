@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating Python virtual environment...
    py -3.11 -m venv .venv 2>nul || python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo [2/3] Installing verified dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Please confirm Python 3.11 and network access.
    pause
    exit /b 1
)

echo [3/3] Starting Streamlit demo at http://localhost:8501
echo If port 8501 is already in use, stop the old demo with Ctrl+C first.
python -m streamlit run app.py --server.port 8501

endlocal
