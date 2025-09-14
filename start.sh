#!/bin/bash
# Production startup script for Railway deployment
set -e

echo "🚀 Starting Fantrax Value Hunter production server..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start Flask server
echo "🐍 Starting Flask server..."
python src/app.py