#!/bin/bash

# Store the script directory
SCRIPT_DIR="/home/yemoeaung1/ECHO-Pipeline/data-storer-production" # Update this path to your actual script directory

# Change to the script directory
cd "$SCRIPT_DIR" || {
    echo "ERROR: Failed to change to directory: $SCRIPT_DIR"
    exit 1
}

# Activate virtual environment
source "venv/bin/activate" || {
    echo "ERROR: Failed to activate virtual environment"
    exit 1
}

# Run the Python script
python savetolake.py
PYTHON_EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Exit with the same code as the Python script
exit $PYTHON_EXIT_CODE