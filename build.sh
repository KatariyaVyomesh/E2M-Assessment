#!/bin/bash

# Build the project
echo "Building the project..."
python3 -m pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Build complete."
