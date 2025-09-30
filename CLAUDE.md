# Fantrax Value Hunter - Development Context

## System Overview
V2.0 Enhanced Formula system for Premier League fantasy analysis using Python Flask backend with PostgreSQL database.

## Quick Start
```bash
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
start_dashboard_safe.bat  # RECOMMENDED: Starts backend (5001) + React dashboard (3000) with safe file editing
# Alternative: start_dashboard.bat (original, may cause file locks during intensive editing)
# Manual: python src/app.py && cd frontend && npm start
```

## Core Architecture
- **Database**: `fantrax_value_hunter` on PostgreSQL (localhost:5433)
- **User**: `fantrax_user` / `fantrax_password`
- **Backend**: Flask app (`src/app.py`) - Port 5001
- **Frontend**: React dashboard (`frontend/`) - Port 3000
- **Engine**: V2.0 calculation engine (`calculation_engine_v2.py`)

## V2.0 Formula
```
True Value = Blended_PPG × Form × NPxG_Fixture × Starter × xGI
ROI = True Value ÷ Player_Price
```

## Key Tables
- `players` - Core player data (714 players)
- `player_metrics` - Live performance data with opponent info (includes next_opponent, is_home columns)
- `player_games_data` - Games tracking for blending
- `name_mappings` - Cross-source player resolution
- `team_metrics` - NPxG team strength data for fixture multipliers

## Documentation
- `docs/API_REFERENCE.md` - API endpoints
- `docs/DATABASE_SCHEMA.md` - Database structure
- `docs/FEATURE_GUIDE.md` - Dashboard functionality
- `docs/DEVELOPMENT_SETUP.md` - Development setup
- `docs/RAILWAY_DEPLOYMENT_PLAN.md` - Railway deployment strategy
- `docs/RAILWAY_DATABASE_CONNECTION.md` - Railway database configuration

## Essential Commands
```bash
# Database verification
python archive/setup_scripts/check_db_structure.py

# System validation
python archive/setup_scripts/fantasy_validation.py

# Check current database state
python check_current_state.py
```

## Data Sources
- **Fantrax**: Player data, pricing, and next opponent information
- **Understat**: xG/xA statistics
- **FFP (Fantasy Football Pundit)**: Starter predictions (replaced FFS)
- **NPxG Database**: Team strength metrics for fixture difficulty (replaced betting odds)

## NPxG Fixture System (September 2025)
### NPxG Replaces Betting Odds
- **Migration**: Replaced betting odds-based fixture difficulty with NPxG team strength analysis
- **Weight Control**: Repurposed "Fixture Base" slider to control NPxG weight (-20% to +20% range)
- **Position-Specific**: Attacking/defensive components based on player position
- **Team Aliases**: Automatic resolution of team code mismatches (BRF→BRE, NOT→NFO)
- **Home/Away Adjustments**: Built-in location modifiers (±10% attacking, ±15% defensive)

### Implementation Benefits
- **No Manual Import**: Eliminates need for weekly betting odds CSV uploads
- **Real-Time**: Fixture multipliers calculated automatically using database team metrics
- **Accurate Mapping**: Team alias system ensures proper opponent matching
- **User Control**: NPxG Weight slider provides fine-tuning control over fixture impact

## Recent Enhancements (September 2024)
### Next Opponent Column
- **Source**: Fantrax CSV "Opponent" column (format: "BUR Sat 4:00PM" or "@EVE Mon 9:00PM")
- **Display**: Shows as "vs BUR" (home) or "@ EVE" (away) in compact 60px column
- **Performance**: Stored directly in `player_metrics` table for fast retrieval
- **Auto-Update**: Refreshes automatically with each Fantrax CSV import

### Enhanced Color Coding
- **Fixed Scale**: Colors based on full dataset, not filtered subset
- **Consistent Reference**: Same player always shows same color intensity
- **Better Comparisons**: Meaningful color comparison across different filters
- **Affected Columns**: Minutes, Games Played, Total FPts, PPG, Price, ROI

### Performance Optimization
- **Query Speed**: Eliminated expensive `fixture_odds` JOIN
- **Table Navigation**: Restored original fast performance (0.67s for 100 players)
- **Data Storage**: Opponent data now stored directly in main table

## FFP CSV Import (Working)
**IMPORTANT**: Only use the dashboard import button for FFP CSV imports:
- ✅ **Working**: Main dashboard → Football icon button → "Import lineup CSV" (hover text)
- ❌ **Not Working**: Top menu "Upload & Sync" → "Import Lineup CSV"
- **Process**: Upload CSV → Validate unmatched players → Apply → Multipliers applied automatically
- **Features**:
  - Confidence-based multipliers (90-100% → 1.0x, 70-89% → configurable, etc.)
  - Name mapping persistence (no repeated validations)
  - Uses system parameters from frontend adjustment panels
  - Triggers automatic true value recalculation

## Archive Structure
- `archive/setup_scripts/` - One-time utility scripts
- `archive/old_docs/` - Historical documentation
- `archive/experimental/` - R scripts and API testing

## Railway Deployment
- **Purpose**: Read-only mirror for friends to access dashboard online
- **Strategy**: Weekly sync from local master database
- **Database**: PostgreSQL at `centerbeam.proxy.rlwy.net:16207`
- **Features**: Full data access with parameter adjustments disabled for stability

### 🚨 CRITICAL Railway Setting
**Environment Variable**: `NO_CACHE=1` **MUST BE ENABLED**
- **Location**: Railway Dashboard → Service → Variables
- **Purpose**: Disables Railway's build cache to ensure weekly updates deploy
- **Without this**: New data won't update due to aggressive caching
- **Status**: ✅ Currently enabled (September 2025)

## File Editing and Process Management
✅ **File modification issues have been resolved** (September 2025)

### Recommended Startup Methods
```bash
start_dashboard_safe.bat  # RECOMMENDED: Safe mode prevents file lock issues
start_dev_no_reload_corrected.bat  # Backend only, no auto-reload
emergency_recovery.bat  # For recovery if services get stuck
```

### Issue Resolution Summary
- **Root Cause**: Multiple `cmd.exe` processes holding directory handles
- **Solution**: Use safe startup scripts with `FLASK_NO_RELOAD=true`
- **Status**: Parameter updates now work without CSV re-import
- **Fixes Applied**: Cache clearing bug, cursor closure bug, UI cleanup

### Environment Variables (Current Working Setup)
- `FLASK_ENV=development` - Enables development mode features
- `FLASK_NO_RELOAD=true` - Prevents file watcher conflicts with Claude Code
- ❌ **Do NOT use**: `WERKZEUG_RUN_MAIN=true` (causes KeyError)

### VS Code Configuration
- `.vscode/settings.json` - Excludes unnecessary directories from file watching
- Background processes are managed automatically by safe startup scripts

## Current Status
Production-ready V2.0 system processing 714 Premier League players with advanced mathematical formulas for live fantasy optimization. Uses single live table approach for real-time data updates. No snapshot tables needed - all data is live and continuously updated.