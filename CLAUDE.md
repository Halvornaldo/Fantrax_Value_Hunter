# Fantrax Value Hunter - Development Context

## Current System Status

✅ **Production Ready Dashboard** with comprehensive parameter controls and player analytics

### Recent Major Features (2025-08-20)
- **Blender Display Configuration**: Adjustable thresholds for blending historical/current season data
- **Professional Tooltip System**: All 17 columns have detailed explanations
- **Complete xGI Integration**: Understat data with name matching system (99% match rate)
- **Optimized Performance**: Fixture difficulty calculations improved 2x (90s → 46s)
- **Manual Override System**: Real-time starter prediction overrides with S/B/O/A controls
- **Enhanced Table Features**: Numeric Games sorting, pagination (50/100/200/All), improved filtering
- **Calculation Research Framework**: 6 specialized LLM research prompts for formula optimization

### Formula Optimization v2.0 Implementation (2025-08-21)
- **Sprint 1 COMPLETED**: Foundation & Critical Fixes implemented and tested
- **Core Formula Fixed**: Separated True Value (point prediction) from ROI (value/price ratio)
- **Exponential Fixture Calculation**: Implemented base^(-difficulty) instead of linear multipliers
- **Multiplier Cap System**: Prevents extreme outliers (form: 2.0, fixture: 1.8, xGI: 2.5, global: 3.0)
- **Dual Engine System**: v1.0 and v2.0 engines running in parallel for safe A/B testing
- **Database Migration**: Added v2.0 schema with new columns (true_value, roi, exponential_form_score)
- **API Integration**: New /api/calculate-values-v2 endpoints functional
- **Ready for Sprint 2**: EWMA form calculation, dynamic blending, normalized xGI

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
- `calculation-research/` - LLM research prompts for formula optimization

### Essential Files
```
src/app.py                    # Main Flask application (2500+ lines)
templates/dashboard.html      # Two-panel UI
static/js/dashboard.js        # Parameter controls & table logic
config/system_parameters.json # All configurable parameters
```

### Performance Benchmarks
- **Efficient Processing**: 633 players recalculated efficiently for weekly analysis workflow
- **Database Optimization**: Well-optimized queries for large player dataset
- **Memory Caching**: Significant fixture difficulty performance improvements through optimization
- **Data Integration**: 99% xGI name matching success rate (296/299 players)
- **Batch Processing**: Reliable multiplier updates across entire player dataset
- **Dashboard Responsiveness**: Parameter changes apply smoothly with visual feedback

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
- **Formula Optimization**: Using calculation-research/ prompts for LLM analysis
- **Parameter Validation**: Statistical validation of multiplier effectiveness
- **Performance Monitoring**: Ongoing optimization for efficient weekly analysis workflow
- **User Experience**: Feature polish and dashboard improvements

## Formula Optimization v2.0

### Research-Based Enhancement Plan
Following comprehensive mathematical research analysis, the system is ready for major formula optimization:

**Key Findings:**
- Current multiplicative approach validated and strong
- Critical issue: Price mixed with prediction (needs separation)
- Exponential decay superior to fixed weights for form
- Dynamic blending better than hard cutoffs
- xGI needs normalization around 1.0

### Implementation Documentation
Located in `docs/` folder:
1. **FORMULA_OPTIMIZATION_SPRINTS.md** - Complete 5-sprint implementation plan
2. **GEMINI_INTEGRATION_PLAN.md** - AI-powered insights strategy  
3. **FORMULA_MIGRATION_GUIDE.md** - Technical migration from v1.0 → v2.0

### Sprint Overview
- **Sprint 1**: Foundation fixes (separate True Value from ROI, exponential fixture)
- **Sprint 2**: Advanced calculations (EWMA form, dynamic blending, xGI normalization)
- **Sprint 3**: Validation framework (backtesting, RMSE/MAE metrics)
- **Sprint 4**: UI integration (new columns, parameter controls)
- **Sprint 5**: Future features (team style, position-specific models)

### Expected Improvements
- **Accuracy**: 10-15% better predictions (RMSE < 2.85, Spearman > 0.30)
- **User Experience**: Enhanced controls, AI insights, visual indicators
- **Mathematical Rigor**: Research-validated formulas with proper scaling

## Calculation Research Framework

### Research Prompts Available
Located in `calculation-research/` folder:
1. **01_Overall_Formula_Analysis.md** - Comprehensive system validation
2. **02_Form_Component_Analysis.md** - Form multiplier optimization  
3. **03_Blender_Display_Analysis.md** - Historical-to-current transition strategy
4. **04_Fixture_Difficulty_Analysis.md** - Odds-based difficulty system
5. **05_Starter_Prediction_Analysis.md** - Rotation penalty framework
6. **06_xGI_Integration_Analysis.md** - Expected Goals Involvement optimization
7. **Fantasy Football Model Analysis & Optimization.md** - Deep research analysis results

### Usage Strategy
- **Start with #1** for overall formula validation and system architecture review
- **Use #2-6** for deep dives into specific multiplier components  
- **Reference #7** for comprehensive research findings and mathematical validation
- Each prompt includes current parameter values, technical constraints, and performance requirements
- Designed for deep research LLMs to provide mathematical validation and optimization recommendations

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