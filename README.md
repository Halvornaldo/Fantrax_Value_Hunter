# Fantrax Value Hunter

A fantasy football analytics tool for Premier League players in Fantrax competitions. Uses advanced mathematical formulas to calculate player value and return on investment.

## Quick Start

1. **Start the application:**
   ```bash
   # Option 1: Use the launcher (Windows)
   start_dashboard.bat
   
   # Option 2: Start manually
   python src/app.py           # Backend (port 5001)
   cd frontend && npm start    # Frontend (port 3000)
   ```

2. **Access dashboard:**
   - Open browser to `http://localhost:3000` (React Dashboard)
   - View player rankings, values, and analytics

## Features

- **V2.0 Enhanced Formula**: Advanced player valuation using multiple factors
- **Dynamic Blending**: Combines historical and current season data
- **Interactive Dashboard**: Real-time parameter adjustments
- **Export Functionality**: CSV exports for analysis
- **Trend Analysis**: Historical performance tracking
- **Live Table Mode**: Real-time data updates without gameweek management

## System Requirements

- Python 3.8+
- PostgreSQL 
- Flask application server

## Database Connection

- **Host**: localhost:5433
- **Database**: fantrax_value_hunter
- **User**: fantrax_user
- **Password**: fantrax_password

## Documentation

- `docs/DASHBOARD_SETUP.md` - Dashboard startup and troubleshooting
- `docs/API_REFERENCE.md` - REST API endpoints
- `docs/DATABASE_SCHEMA.md` - Database structure
- `docs/FEATURE_GUIDE.md` - User interface guide
- `docs/DEVELOPMENT_SETUP.md` - Development environment setup

## Architecture

The system calculates player value using:
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Player_Price
```

Where:
- **Blended_PPG**: Historical + current season points per game
- **Form**: Recent performance trend (EWMA)
- **Fixture**: Upcoming match difficulty
- **Starter**: Playing time probability
- **xGI**: Expected goals involvement

## Data Model

The system uses a **live table approach** where:
- All data uploads update a single live table (gameweek 1)
- No complex gameweek management required
- Immediate dashboard reflection of new data
- Simplified workflow for continuous updates

## File Structure

```
src/                    # Core application
templates/              # HTML templates  
static/                 # CSS/JS assets
config/                 # Configuration
docs/                   # Documentation
archive/                # Historical files
```

Built for the 2025-26 Premier League season with live table data model for real-time updates.# Railway deployment trigger
