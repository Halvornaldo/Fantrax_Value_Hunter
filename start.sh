#!/bin/bash
# Production startup script for Railway deployment
set -e

echo "🚀 Starting Fantrax Value Hunter production server..."
echo "🐍 Starting Flask server..."
python src/app.py
