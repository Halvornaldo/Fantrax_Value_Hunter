# Fantrax Value Hunter - Project Context

## Overview
This is the **Fantrax Value Hunter V2.0 Enhanced Formula** system - a comprehensive fantasy football analytics platform that calculates player "true value" and ROI using advanced statistical modeling.

## Project Structure
```
c:/Users/halvo/.claude/Fantrax_Value_Hunter/
├── src/
│   ├── app.py                          # Main Flask application (5500+ lines)
│   ├── calculation_engine_v2.py        # V2.0 Enhanced Formula engine
│   ├── trend_analysis_engine_simple.py # Current-season trend analysis
│   ├── name_matcher.py                 # Player name matching system
│   └── scraperfc_integration.py        # Understat data integration
├── frontend/                           # React frontend (npm start)
├── templates/                          # Flask HTML templates
├── docs/                              # Documentation (TREND_ANALYSIS_GUIDE.md)
└── data/                              # CSV imports and exports
```

## Core Technologies
- **Backend**: Flask (Python) with PostgreSQL database
- **Frontend**: React (runs on separate npm server)
- **Data Sources**: Fantrax (CSV), Understat (ScraperFC), FFP lineups, betting odds
- **Analytics**: V2.0 Enhanced Formula with EWMA, xGI multipliers, fixture difficulty

## Key Features

### 1. V2.0 Enhanced Formula System
- **True Value Calculation**: Sophisticated algorithm combining multiple factors
- **ROI Analysis**: Return on investment based on player prices vs performance
- **Current Season Focus**: Uses 2024-25 baseline data for immediate accuracy
- **Multiple Multipliers**: Form (EWMA), fixture difficulty, starter probability, xGI performance

### 2. Data Integration Workflows
- **Weekly Fantrax Import**: Player prices, points, team assignments
- **Understat Sync**: xG90, xA90, xGI90 stats with minutes played
- **FFP Lineup Import**: Starting predictions and rotation risk assessment
- **Odds CSV Import**: Betting odds for fixture difficulty calculation
- **Game Scores Validation**: Understat participation verification

### 3. Trend Analysis System
- **Historical Analysis**: Apply current parameters to past gameweeks
- **Parameter Testing**: Compare different formula settings
- **API Endpoints**: `/api/trends/calculate`, `/api/trends/raw-data`

## Database Schema (PostgreSQL)
- **Core Tables**: `players`, `player_game_scores`, `team_fixtures`
- **Analytics**: `player_predictions`, `form_scores`, `validation_results`
- **Name Mapping**: `name_mappings`, `understat_name_mappings`, `verified_name_mappings`

## Development Environment
- **Platform**: Windows (MINGW64_NT-10.0-26100)
- **Working Directory**: `c:/Users/halvo/.claude/Fantrax_Value_Hunter/`
- **Services**: Flask backend + React frontend (dual servers)
- **Database**: PostgreSQL with connection via environment variables

## Common Commands
```bash
# Start backend
python src/app.py

# Start frontend
cd frontend && npm start

# Database queries
psql -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter

# Validation endpoint
curl -X POST http://localhost:5001/api/validate-game-scores \
  -H "Content-Type: application/json" \
  -d '{"game_number": 5, "leagues": ["EPL"]}'
```

## Development Notes
- **Multiple Running Processes**: Both Flask and React servers typically running
- **Route Registration**: Critical that validation endpoints come before catch-all routes
- **Current Season Data**: System optimized for 2024-25 season analytics
- **Git Usage**: Active repository with detailed commit messages

This project represents a sophisticated fantasy football analytics platform with real-time data integration, advanced statistical modeling, and comprehensive trend analysis capabilities.