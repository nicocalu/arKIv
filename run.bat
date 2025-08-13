:: filepath: c:\Users\nicoc\OneDrive\Desktop\programming\arKIv\run_pipeline.bat
@echo off
cls

echo ===================================
echo  arKIv Full Processing Pipeline
echo ===================================
echo.

REM --- Pre-run Checks ---

REM Check for API key file
if not exist "api.key" (
    echo [ERROR] API key file 'api.key' not found.
    echo Please create this file, place your OpenAI API key inside it, and run again.
    pause
    exit /b 1
)

REM Check for virtual environment (recommended)
if not defined VIRTUAL_ENV (
    echo [WARNING] You are not running inside a Python virtual environment.
    echo It is highly recommended to use one to manage dependencies.
    echo To create one: python -m venv venv
    echo To activate:   .\venv\Scripts\activate
    echo.
    pause
)

REM --- Execution Pipeline ---

echo.
echo [Step 1/4] Running main.py to scrape papers and metadata...
python src/main.py
if %errorlevel% neq 0 (
    echo [ERROR] main.py failed. Halting pipeline.
    pause
    exit /b 1
)

echo.
echo [Step 2/4] Running data_extractor.py to create embeddings...
python src/data_extractor.py
if %errorlevel% neq 0 (
    echo [ERROR] data_extractor.py failed. Halting pipeline.
    pause
    exit /b 1
)

echo.
echo [Step 3/4] Running kg_builder.py to build the knowledge graph...
python src/kg_builder.py
if %errorlevel% neq 0 (
    echo [ERROR] kg_builder.py failed. Halting pipeline.
    pause
    exit /b 1
)

echo.
echo [Step 4/4] Running qa_system.py to start the question-answering interface...
python src/qa_system.py

echo.
echo ===================================
echo  Pipeline finished.
echo ===================================
pause