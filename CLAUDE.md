# Fantrax Value Hunter - Development Context

## System Overview
V2.0 Enhanced Formula system for Premier League fantasy analysis using Python Flask backend with PostgreSQL database.

## Quick Start
```bash
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
start_dashboard.bat  # Starts backend (5001) + React dashboard (3000)
# OR manually: python src/app.py && cd frontend && npm start
```

## Core Architecture
- **Database**: `fantrax_value_hunter` on PostgreSQL (localhost:5433)
- **User**: `fantrax_user` / `fantrax_password`  
- **Backend**: Flask app (`src/app.py`) - Port 5001
- **Frontend**: React dashboard (`frontend/`) - Port 3000  
- **Engine**: V2.0 calculation engine (`calculation_engine_v2.py`)

## V2.0 Formula
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Player_Price
```

## Key Tables
- `players` - Core player data (647 players)
- `player_metrics` - Live performance data (single table, continuously updated)
- `player_games_data` - Games tracking for blending
- `name_mappings` - Cross-source player resolution
- `team_fixtures` - Fixture difficulty scores

## Documentation
- `docs/API_REFERENCE.md` - API endpoints
- `docs/DATABASE_SCHEMA.md` - Database structure  
- `docs/FEATURE_GUIDE.md` - Dashboard functionality
- `docs/DEVELOPMENT_SETUP.md` - Development setup

## Essential Commands
```bash
# Database verification
python archive/setup_scripts/check_db_structure.py

# System validation  
python archive/setup_scripts/fantasy_validation.py
```

## Archive Structure
- `archive/setup_scripts/` - One-time utility scripts
- `archive/old_docs/` - Historical documentation
- `archive/experimental/` - R scripts and API testing

## Current Status
Production-ready V2.0 system processing 647 Premier League players with advanced mathematical formulas for live fantasy optimization. Uses single live table approach for real-time data updates.