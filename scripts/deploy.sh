#!/bin/bash

# This script sets up the environment for the AI backend unified dashboard.

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
pip install -r requirements.txt

# Deactivate the virtual environment
deactivate

echo "Deployment complete."
echo "To run the dashboard, activate the virtual environment and run the following command:"
echo "source .venv/bin/activate"
echo "python3 -m scripts.dashboard"
