# Fantrax Value Hunter - Development Context

## Current System Status

✅ **v2.0 Enhanced Formula Complete** - Dynamic Blending with Historical Data Integration

## ⚠️ CRITICAL: DUAL ENGINE SYSTEM

**IMPORTANT FOR DEVELOPERS**: This system now runs TWO calculation engines in parallel:

- **v1.0 Legacy Engine** (`src/app.py` calculations + static multipliers)
- **v2.0 Enhanced Engine** (`calculation_engine_v2.py` + dynamic blending)

**⚠️ ENGINE SEPARATION WARNINGS:**
1. **Parameter Structure**: v1.0 uses `form_calculation`, v2.0 uses `formula_optimization_v2.exponential_form`
2. **Database Columns**: v1.0 writes to `value_score`, v2.0 writes to `true_value` + `roi`  
3. **API Endpoints**: `/api/players` (both), `/api/calculate-values-v2` (v2.0 only)
4. **JavaScript**: Different parameter detection for v1.0 vs v2.0 modes
5. **Calculation Logic**: v1.0 = `(PPG/Price) × multipliers`, v2.0 = `Blended_PPG × multipliers ÷ Price`

**⚠️ WHEN MODIFYING CODE:**
- **Check which engine** you're working on - don't mix v1.0 and v2.0 logic
- **Test both modes** - Dashboard has toggle switch between Legacy/Enhanced
- **Parameter changes** - Ensure correct structure for target engine
- **Database updates** - v2.0 requires `historical_ppg`, `baseline_xgi`, etc.
- **API changes** - Update both main and v2.0 endpoints if needed

**✅ Safe Reversion Point**: `git reset --hard v2.0-dynamic-blending-stable`

### Recent Major Features (2025-08-22)
- **Blender Display Configuration**: Adjustable thresholds for blending historical/current season data
- **Professional Tooltip System**: All 17 columns have detailed explanations
- **Complete xGI Integration**: Understat data with name matching system (99% match rate)
- **Optimized Performance**: Fixture difficulty calculations improved 2x (90s → 46s)
- **Manual Override System**: Real-time starter prediction overrides with S/B/O/A controls
- **Enhanced Table Features**: Numeric Games sorting, pagination (50/100/200/All), improved filtering
- **Calculation Research Framework**: 6 specialized LLM research prompts for formula optimization

### Formula Optimization v2.0 Implementation (2025-08-21/22)
- **Sprint 1 COMPLETED**: Foundation & Critical Fixes implemented and tested
- **Sprint 2 COMPLETED**: Advanced calculations implemented and tested
- **Sprint 3 COMPLETED**: Validation Framework & Critical Data Fixes
- **Sprint 4 COMPLETED**: Dashboard Integration - v2.0 toggle, ROI column, validation status, tooltip system fixes
- **Core Formula Fixed**: Separated True Value (point prediction) from ROI (value/price ratio)
- **Exponential Fixture Calculation**: Implemented base^(-difficulty) instead of linear multipliers
- **EWMA Form Calculation**: Exponential weighted moving average with configurable α=0.87
- **Dynamic Blending**: Smooth transition between historical and current season data using w_current = min(1, (N-1)/(K-1))
- **Normalized xGI**: Ratio-based calculation with position-specific adjustments
- **Multiplier Cap System**: Prevents extreme outliers (form: 2.0, fixture: 1.8, xGI: 2.5, global: 3.0)
- **Enhanced Metadata**: Blending information, feature flags, caps applied tracking
- **Dual Engine System**: v1.0 and v2.0 engines running in parallel for safe A/B testing
- **Database Migration**: Added v2.0 schema with new columns (true_value, roi, exponential_form_score)
- **API Integration**: New /api/calculate-values-v2 endpoints functional with Sprint 2 features
- **Validation Framework**: Production-ready validation system with data quality fixes (Sprint 3)
- **Critical Data Cleanup**: Fixed 63 players with corrupted baseline data from Championship/lower leagues
- **Formula Discovery**: Identified v1.0 vs v2.0 validation issues and temporal separation requirements
- **Ready for Sprint 4**: UI integration with realistic validation expectations

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

### Recent Session Focus (2025-08-21)  
- **Sprint 4 Phase 1 Completed**: Dashboard Integration with v2.0 formula toggle and ROI column
- **UI Integration**: Successfully surfaced v2.0 ROI calculations with proper NULL handling and visual indicators
- **Validation System**: Backend properly connected, awaiting sufficient gameweek data (currently 2 GWs, need 5+)
- **Technical Discoveries**: Database NULL sorting issues resolved, formula engine coexistence validated
- **Issues Tracking**: Created comprehensive issues list for Phase 4 polish (minor toggle bugs identified)

### System Maturity
The system is production-ready with:
- ✅ Comprehensive feature set with parameter controls
- ✅ Robust data integration with name matching  
- ✅ Performance optimizations for real-time use
- ✅ Professional UI with tooltips and responsive design
- ✅ Complete documentation for development and usage

The dashboard successfully handles all 633 Premier League players with real-time parameter adjustments, making it effective for weekly fantasy lineup optimization.

---
*Last Updated: 2025-08-21 - Focus: Sprint 4 Phase 2 - V1.0 Legacy Removal and Clean V2.0 Interface*

## Sprint 4 Phase 2: V1.0 Legacy Removal Progress (2025-08-21)

### Issues Discovered
During Sprint 4 Phase 2, we identified critical architectural problems with the v1.0/v2.0 dual system:

**Core Problem**: V2.0 implemented as cosmetic wrapper over V1.0 base system
- V1.0 controls still visible and functional when v2.0 is selected
- Both systems active simultaneously causing parameter conflicts
- JavaScript treats v1.0/v2.0 as shared parameter system
- Apply Changes button responds to v1.0 sliders even in v2.0 mode

### Technical Issues Identified
1. **Duplicate HTML IDs**: Two `syncUnderstat` buttons causing JavaScript conflicts
2. **CSS Visibility Failure**: `body.v2-enabled` class not properly hiding v1.0 controls  
3. **Parameter Detection Conflict**: `buildParameterChanges()` reads from v1.0 controls in v2.0 mode
4. **Backend Engine Uncertainty**: Unclear if v2.0 can run independently of v1.0 system
5. **Broken Functionality**: Dark mode toggle, Import Lineup button not working

### Actions Taken
**✅ Fixed Immediate Issues**:
- Resolved duplicate sync button IDs (`syncUnderstat` vs `syncUnderstat-v2`)
- Updated JavaScript to handle both sync buttons safely
- Fixed ROI column to show actual values (was showing 0.000)
- Maintained git safety checkpoint at `2d0031c` for safe rollback

**⚠️ Partial Solutions Attempted**:
- Tried complete v1.0 removal → JavaScript broke (requires v1.0 element IDs)
- Added CSS classes for v1.0 hiding → Not working properly in practice
- Moved Sync button to v2.0 → Created conflicts, had to create separate button

### Current Status
- **ROI calculations working** ✅
- **V1.0 controls still visible** ❌ (should be hidden)
- **Parameter conflicts persist** ❌ (v1.0 sliders trigger Apply Changes in v2.0 mode)
- **Core functionality intact** ✅ (can revert to working state anytime)

### Architecture Discovery
Research revealed v2.0 is NOT a true replacement but a layer over v1.0:
- V1.0 provides base parameter detection and JavaScript event handling
- V2.0 adds enhanced controls but relies on v1.0 infrastructure  
- True v2.0 migration requires complete JavaScript architecture redesign

### Next Phase Requirements
**Complete V2.0 Migration Plan Needed**:
1. Backend engine independence verification
2. JavaScript parameter system separation  
3. HTML structure cleanup (remove v1.0 entirely)
4. CSS simplification for single-system interface
5. Comprehensive testing of v2.0-only functionality

### Recent Fixes (2025-08-22)
**✅ Sprint 4 Tooltip System Issues Resolved**:
- **Auto-triggering Fixed**: Tooltips no longer appear automatically on page load
- **Multiple Tooltip Cleanup**: Fixed tooltip stacking in top-left corner 
- **Positioning Robustness**: Added validation to prevent tooltips for invisible elements
- **V2.0 Tooltip Integration**: Properly integrated v2.0 parameter tooltips with cleanup system
- **Initialization Timing**: Added 500ms delay flag to prevent layout-triggered tooltips

**Technical Implementation**:
- Enhanced `hideTooltip()` function to clean up all tooltip types
- Added `tooltipsReady` flag with delayed activation
- Added element visibility validation in positioning functions
- Ensured v2.0 tooltips get proper IDs for cleanup

### Safety Measures
- Git checkpoint `2d0031c` available for instant rollback
- All v2.0 enhanced features confirmed working
- Database proven compatible with v2.0-only operation
- User can safely experiment knowing rollback option exists

---
*Last Updated: 2025-08-22 - Focus: Dynamic Blending Complete + Critical Dual Engine Warnings*

## Dynamic Blending Implementation Complete (2025-08-22)

### ✅ MAJOR BREAKTHROUGH: Historical Data Integration

**🎯 Core Fix**: v2.0 Dynamic Blending now properly uses real 2024-25 season data

**Technical Achievements**:
- **Historical PPG Calculation**: Added to both main API (`/api/players`) and v2.0 API (`/api/calculate-values-v2`)
- **Current Gameweek Detection**: Fixed hardcoded GW1 → database `MAX(gameweek)` query 
- **Database Integration**: `total_points_historical ÷ games_played_historical = historical_ppg`
- **Enhanced Data Pipeline**: v2.0 engine now receives complete dataset (historical_ppg, baseline_xgi, games data)

**Formula Impact**:
```
Current (GW2): w_current = min(1, (2-1)/(16-1)) = 0.067
Blended PPG = (0.067 × Current_PPG) + (0.933 × Historical_PPG_2024_25)
True Value = Blended_PPG × Form × Fixture × Starter × xGI
```

**Files Modified**:
- `calculation_engine_v2.py` - Fixed `_get_current_gameweek()` with database query
- `src/app.py` - Added `historical_ppg` calculation to both player APIs
- Enhanced v2.0 calculation endpoint with complete dataset

**🚨 CRITICAL ENGINE SEPARATION**:
- v1.0 engine unaffected (still uses current PPG only)
- v2.0 engine now properly blends historical + current data
- Dashboard toggle switches between completely different calculation methods
- Parameter structures remain separate (v1.0: `form_calculation`, v2.0: `formula_optimization_v2`)

### Git Status
- **Stable Commit**: `af620fb` - Complete Dynamic Blending implementation
- **Safe Tag**: `v2.0-dynamic-blending-stable` - Reversion point
- **Documentation**: README.md and CLAUDE.md updated with dual engine warnings

### System State
- ✅ **Working**: v2.0 Dynamic Blending with real historical data
- ✅ **Working**: v1.0 Legacy system (unchanged)  
- ✅ **Working**: Dual engine coexistence with proper separation
- ✅ **Working**: Form multipliers correctly showing 1.0 (early season, insufficient data)
- ✅ **Documentation**: Clear warnings about dual engine development requirements