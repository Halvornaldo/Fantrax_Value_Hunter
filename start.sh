#!/bin/bash
set -e
echo "🚀 Starting Fantrax Value Hunter production server..."
echo "🐍 Starting Flask server..."
. venv/bin/activate && python src/app.py
