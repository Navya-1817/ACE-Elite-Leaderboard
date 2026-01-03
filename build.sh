#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

echo "Python version: $(python --version)"

# Upgrade pip and install setuptools
pip install --upgrade pip setuptools wheel

# Install dependencies (numpy first, then pandas)
pip install numpy==1.24.3
pip install pandas==1.5.3
pip install -r requirements.txt

# Initialize database
python init_db.py

echo "✅ Build completed successfully!"
