@echo off
REM Quick Start Script for Hybrid RAG System (Windows)

echo ========================================
echo HYBRID RAG SYSTEM - QUICK START
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from python.org
    pause
    exit /b 1
)

echo [OK] Python found

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
echo [OK] Dependencies installed

REM Download spaCy model
echo Downloading spaCy model...
python -m spacy download en_core_web_sm >nul 2>&1
echo [OK] spaCy model downloaded

REM Check for .env file
if not exist ".env" (
    echo.
    echo WARNING: No .env file found!
    echo.
    echo Please create a .env file with your Google API key:
    echo   1. Copy .env.example to .env
    echo   2. Add your API key: GOOGLE_API_KEY=your_key_here
    echo   3. Get API key from: https://makersuite.google.com/app/apikey
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo [OK] Environment configured
echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Quick start commands:
echo.
echo   1. Test the system:
echo      python test_system.py
echo.
echo   2. Run examples:
echo      python examples.py
echo.
echo   3. Ingest documents and start server:
echo      python main.py --ingest --server
echo.
echo   4. Interactive queries:
echo      python main.py --query
echo.
echo   5. API documentation (after starting server):
echo      http://localhost:8000/docs
echo.
echo ========================================
echo For more information, see:
echo   - README.md
echo   - PROJECT_SUMMARY.md
echo ========================================
echo.

pause
