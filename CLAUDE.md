# Fantrax Value Hunter - Development Context

## Current System Status

✅ **Production Ready Dashboard** with comprehensive parameter controls and player analytics

### Recent Major Features (2025-08-20)
- **Blender Display Configuration**: Adjustable thresholds for blending historical/current season data
- **Professional Tooltip System**: All 17 columns have detailed explanations
- **Complete xGI Integration**: Understat data with name matching system
- **Optimized Performance**: Fixture difficulty calculations improved 2x (90s → 46s)
- **Manual Override System**: Real-time starter prediction overrides with S/B/O/A controls
- **Enhanced Table Features**: Numeric Games sorting, pagination (50/100/200/All), improved filtering

## Core Architecture

### Database System
**Database**: `fantrax_value_hunter` on PostgreSQL (localhost:5433)
**User**: `fantrax_user` / `fantrax_password`
**Key Tables**:
- `players` (633 players) - Core player data
- `player_metrics` - Weekly performance data with multipliers  
- `player_games_data` - Games tracking (historical vs current)
- `name_mappings` - Cross-source player name resolution
- `team_fixtures` - Odds-based fixture difficulty scores

### Application Stack
- **Backend**: Flask app (`src/app.py`) with 25+ API endpoints
- **Frontend**: Two-panel dashboard (Parameter Controls + Player Table)
- **Configuration**: `config/system_parameters.json` with all adjustable parameters

## Feature Systems

### True Value Calculation
```
True Value = PPG × Form × Fixture × Starter × xGI Multipliers
```

**Multiplier Systems**:
1. **Form**: Weighted recent performance vs baseline (configurable lookback/weights)
2. **Fixture**: Odds-based difficulty on 21-point scale (-10 to +10)
3. **Starter**: Rotation penalties based on predicted lineups
4. **xGI**: Expected Goals Involvement from Understat data

### Blender Display Logic
**Configurable Thresholds** (new dashboard feature):
- **Baseline Switchover**: When to start blending historical+current (default: GW10)
- **Transition End**: When to switch to current-only (default: GW15)

**Display Formats**:
- GW 1-10: "38 (24-25)" (historical only)
- GW 11-15: "38+2" (blended)  
- GW 16+: "5" (current only)

### Data Integration
**Global Name Matching System**:
- 6 matching algorithms with confidence scoring
- 100% visibility (no silent failures)
- Learning system builds persistent mappings
- Manual review interface at `/import-validation`

**CSV Upload Workflows**:
- Weekly game data via `/form-upload` ("Upload Weekly Game Data" button)
- Fixture odds via `/odds-upload`
- Lineup predictions with auto-matching

## Development Information

### Quick Start
```bash
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
python src/app.py  # Starts on localhost:5000
```

### Documentation Structure
- `docs/API_REFERENCE.md` - Complete endpoint documentation
- `docs/DATABASE_SCHEMA.md` - Full database structure with credentials
- `docs/FEATURE_GUIDE.md` - Dashboard functionality guide  
- `docs/DEVELOPMENT_SETUP.md` - Setup instructions

### Essential Files
```
src/app.py                    # Main Flask application (2500+ lines)
templates/dashboard.html      # Two-panel UI
static/js/dashboard.js        # Parameter controls & table logic
config/system_parameters.json # All configurable parameters
```

### Performance Notes
- **Database**: Handles 633 players efficiently with optimized queries
- **Caching**: Fixture difficulty uses memory cache to avoid 644 DB queries
- **Batch Operations**: Multiplier updates use batch processing
- **Response Time**: Parameter changes recalculate all 633 players in ~2-3 seconds

## Known Issues & Status

### Resolved Issues ✅
- Week 1 import fixes: Games played logic corrected (252 actual vs 622 incorrect)
- JavaScript variable conflicts: Fixed `baselineSwitchover` naming collision
- Performance optimization: Fixture calculations improved 2x speed

### Recent Bug Fixes ✅ (2025-08-20)
- **Games Column Sorting**: Fixed to sort numerically using `games_total` backend field
- **Player Data Corrections**: Fixed Leandro Trossard xGI/minutes data, updated 50 players with incorrect games count
- **Name Mappings**: Added Rodrigo Muniz/Gomes mappings for correct team associations (Wolves/Fulham swap)
- **Pagination**: Fixed Previous/Next buttons to use proper filtered count instead of page data length
- **UI Terminology**: Updated "Games Display" → "Blender Display" and "Upload Form Data" → "Upload Weekly Game Data"

### Active Development Areas
- Configuration refinement based on weekly usage
- Performance monitoring and optimization
- Feature polish and UX improvements

## Command Reference

### Essential Commands
```bash
# Start application
python src/app.py

# Database verification  
python check_db_structure.py
python check_games.py

# Migration management
python run_migration.py
```

### Database Access
```python
# Quick connection test
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5433, 
    user='fantrax_user', password='fantrax_password',
    database='fantrax_value_hunter'
)
```

## Development Context

### Recent Session Focus (2025-08-20)
- Implemented comprehensive bug fixes for 5 reported issues and 2 enhancements
- Enhanced table functionality: numeric Games sorting, pagination improvements, "All" page size option
- Updated UI terminology for better clarity ("Blender Display", "Upload Weekly Game Data")
- Comprehensive documentation review and enhancement across 4 key documentation files
- Fixed critical player data issues (Trossard, games counting, name mappings)

### System Maturity
The system is production-ready with:
- ✅ Comprehensive feature set with parameter controls
- ✅ Robust data integration with name matching  
- ✅ Performance optimizations for real-time use
- ✅ Professional UI with tooltips and responsive design
- ✅ Complete documentation for development and usage

The dashboard successfully handles all 633 Premier League players with real-time parameter adjustments, making it effective for weekly fantasy lineup optimization.

---
*Last Updated: 2025-08-20 - Focus: Bug fixes, table enhancements, and comprehensive documentation review*