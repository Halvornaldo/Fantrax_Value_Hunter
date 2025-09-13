# Dashboard Setup Guide

## Overview

The Fantrax Value Hunter uses a **React frontend** (port 3000) with a **Flask API backend** (port 5001). Both components must be running for the system to work properly.

## Quick Start

### Option 1: Automated Launcher (Recommended)
```bash
# Windows users
start_dashboard.bat
```
This script will:
1. Start the Flask backend on port 5001
2. Start the React frontend on port 3000  
3. Open the dashboard in your browser

### Option 2: Manual Startup
```bash
# Terminal 1: Start Flask backend
python src/app.py

# Terminal 2: Start React frontend  
cd frontend
npm start
```

## Access Points

- **Dashboard**: http://localhost:3000 (React Frontend)
- **API Backend**: http://localhost:5001 (Flask API)

## Architecture

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐
│  React Frontend │ ────────────────▶│   Flask Backend  │
│   Port 3000     │                 │    Port 5001     │
│                 │◀────────────────│                  │
└─────────────────┘    JSON Data    └──────────────────┘
         │                                     │
         │                                     │
         ▼                                     ▼
   Browser Display                    PostgreSQL Database
                                      localhost:5433
```

## Requirements

### Backend Requirements
- Python 3.8+
- PostgreSQL database running on port 5433
- Flask dependencies (see requirements.txt)

### Frontend Requirements  
- Node.js 14+
- NPM dependencies (automatically installed)

## Development Commands

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Backend Development
```bash
# Start Flask in debug mode
python src/app.py

# Check API health
curl http://localhost:5001/api/health

# View player data
curl http://localhost:5001/api/players?limit=5
```

## Troubleshooting

### Frontend Issues
- **Port 3000 in use**: Kill process or change port in package.json
- **API not connecting**: Check backend is running on port 5001
- **Build errors**: Run `npm install` to update dependencies

### Backend Issues
- **Database connection errors**: Verify PostgreSQL is running on port 5433
- **Port 5001 in use**: Kill Flask process or change port in src/app.py
- **Missing modules**: Run `pip install -r requirements.txt`

### Common Solutions
```bash
# Kill processes on ports
npx kill-port 3000
npx kill-port 5001

# Reset frontend
cd frontend && rm -rf node_modules && npm install

# Check database connection
python archive/setup_scripts/check_db_structure.py
```

## File Structure

```
frontend/
├── package.json          # React dependencies
├── public/               # Static assets
├── src/
│   ├── App.js           # Main React component
│   ├── components/      # React components
│   └── services/        # API service calls
└── build/               # Production build

src/
├── app.py              # Flask backend
├── db_manager.py       # Database operations
└── ...                 # Other backend modules
```

## Production Deployment

For production deployment:
1. Build React frontend: `cd frontend && npm run build`
2. Configure Flask to serve static files from `frontend/build`
3. Use production database settings
4. Set up proper SSL certificates

The system is designed to run both components locally for development and can be configured for production deployment with appropriate environment variables.