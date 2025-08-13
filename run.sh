#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

clear

echo "==================================="
echo " arKIv Full Processing Pipeline"
echo "==================================="
echo

# --- Pre-run Checks ---

# Check for API key file
if [ ! -f "api.key" ]; then
    echo "[ERROR] API key file 'api.key' not found."
    echo "Please create this file, place your OpenAI API key inside it, and run again."
    exit 1
fi

# Check for virtual environment (recommended)
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[WARNING] You are not running inside a Python virtual environment."
    echo "It is highly recommended to use one to manage dependencies."
    echo "To create one: python3 -m venv venv"
    echo "To activate:   source venv/bin/activate"
    echo
    read -p "Press Enter to continue without a virtual environment..."
fi

# --- Execution Pipeline ---

echo
echo "[Step 1/4] Running main.py to scrape papers and metadata..."
python3 src/main.py

echo
echo "[Step 2/4] Running data_extractor.py to create embeddings..."
python3 src/data_extractor.py

echo
echo "[Step 3/4] Running kg_builder.py to build the knowledge graph..."
python3 src/kg_builder.py

echo
echo "[Step 4/4] Running qa_system.py to start the question-answering interface..."
python3 src/qa_system.py

echo
echo "==================================="
echo " Pipeline finished successfully."
echo "==================================="