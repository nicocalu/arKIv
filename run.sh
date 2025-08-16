#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

clear

echo "==================================="
echo " arKIv Full Processing Pipeline"
echo "==================================="
echo

# --- Pre-run Checks ---

# 1. Check for Ollama Server
echo "Checking for local Ollama server..."
if ! curl -s -f http://localhost:11434/ > /dev/null; then
    echo "[ERROR] Local Ollama server is not running or not reachable at http://localhost:11434/"
    echo "Please start Ollama and ensure it's accessible, then run this script again."
    exit 1
fi
echo "Ollama server found."
echo

# 2. Check for API key file (for the final QA system)
if [ ! -f "api.key" ]; then
    echo "[ERROR] API key file 'api.key' not found."
    echo "This key is still required for the final QA system step (qa_system.py)."
    echo "Please create this file, place your OpenAI-compatible API key inside it, and run again."
    exit 1
fi

# 3. Check for virtual environment (recommended)
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
python3 src/oai_down.py

echo
echo "[Step 2/4] Running data_extractor.py to create embeddings..."
python3 src/data_extractor.py

echo
echo "[Step 3/4] Running kg_builder.py to build the knowledge graph (using local Ollama)..."
python3 src/kg_builder.py

echo
echo "[Step 4/4] Running qa_system.py to start the question-answering interface (using API key)..."
python3 src/qa_system.py

echo
echo "==================================="
echo " Pipeline finished successfully."
echo "==================================="