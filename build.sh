#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install Python dependencies (use only binary wheels, no source builds)
pip install --upgrade pip
pip install --only-binary=:all: -r requirements.txt || pip install -r requirements.txt

# Initialize database
python init_db.py

echo "✅ Build completed successfully!"
