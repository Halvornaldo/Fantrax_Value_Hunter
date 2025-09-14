#!/bin/bash
# Fantrax Value Hunter - Railway Build Script
# Builds React frontend and prepares Flask backend for production

set -e  # Exit on any error

echo "🏗️  Starting Fantrax Value Hunter build process..."

# Check if we're in the correct directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    exit 1
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

# Build the React application
echo "⚛️  Building React frontend..."
npm run build

# Go back to root
cd ..

# Create static directory in src if it doesn't exist
echo "📁 Setting up Flask static directory..."
mkdir -p src/static

# Remove old build if exists
if [ -d "src/static/react-build" ]; then
    echo "🗑️  Removing old React build..."
    rm -rf src/static/react-build
fi

# Copy React build to Flask static directory
echo "📋 Copying React build to Flask static directory..."
cp -r frontend/build src/static/react-build

# Verify the build was successful
if [ -f "src/static/react-build/index.html" ]; then
    echo "✅ React build copied successfully!"
else
    echo "❌ Error: React build failed or index.html not found"
    exit 1
fi

echo "🚀 Build process completed successfully!"
echo "   - React frontend built and copied to src/static/react-build/"
echo "   - Flask backend ready to serve static files"
echo ""
echo "Next: Deploy to Railway and access full application at your Railway URL!"