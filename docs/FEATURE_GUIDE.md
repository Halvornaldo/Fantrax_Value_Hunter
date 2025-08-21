# Dashboard Features Guide

## Overview
The Fantrax Value Hunter dashboard provides configurable analytics for Premier League fantasy football players, combining multiple data sources to calculate optimized "True Value" ratings.

## Formula Optimization v2.0 Status (2025-08-21)

**Current Status**: Sprint 1 Complete - Foundation implemented but not yet live in dashboard
- ✅ **Core Formula Fixed**: True Value now separate from price (calculation engine only)
- ✅ **Exponential Fixture Calculation**: Implemented base^(-difficulty) transformation
- ✅ **Multiplier Cap System**: Prevents extreme outliers in calculations
- 🔄 **Dashboard Integration**: Will be added in Sprint 4
- 🔄 **Advanced Features**: EWMA form, dynamic blending pending Sprint 2

**Current Dashboard**: Still shows v1.0 calculations (mixed price/prediction formula)
**Testing**: v2.0 calculations available via API endpoints (`/api/calculate-values-v2`)

> **Note**: The dashboard features described below reflect the current v1.0 system. v2.0 improvements will be integrated into the dashboard in future sprints while maintaining backward compatibility.

## Parameter Controls Panel

All features can be configured through the Parameter Controls panel on the left side of the dashboard.

### Form Calculation

**Purpose**: Adjusts player values based on recent performance versus season average

**Controls**:
- **Enable/Disable**: Checkbox to toggle form calculation
- **Lookback Period**: 3 or 5 games (dropdown)
- **Minimum Games**: Minimum games required for form calculation (default: 3)
- **Baseline Switchover Gameweek**: When to switch from historical to current data (default: 10)
- **Form Strength**: How much form affects True Value (slider, default: 1.00x)

**Technical Implementation**:
- **Before GW10**: Uses 2024-25 season baseline + form adjustment
- **After GW10**: Uses current season average + form adjustment
- **Weighted Calculation**: Recent games weighted 0.5, 0.3, 0.2 for last 3 games
- **Constraints**: Multipliers capped between 0.5x and 1.5x
- **Minimum Threshold**: Requires 3+ games for calculation, otherwise returns 1.0x

**How It Works**:
- Calculates weighted average of recent games vs season performance
- Form data stored in `player_form` table with weekly Fantrax CSV uploads
- Earlier in season: Uses 2024-25 historical data as baseline
- Later in season: Uses current season form data
- Higher form strength = bigger impact on True Value

### Odds-Based Fixture Difficulty

**Purpose**: Adjusts player values based on upcoming fixture difficulty using real betting odds from OddsPortal.com

**Controls**:
- **Enable/Disable**: Checkbox to toggle fixture difficulty
- **Preset Levels**: Conservative (±10%), Balanced (±20%), Aggressive (±30%), or Custom
- **Multiplier Strength**: How much fixture difficulty affects True Value (0.1-0.5 range)
- **Position Weights**: Different impact by position
  - Goalkeepers: 110% (benefit more from easy fixtures - save opportunities)
  - Defenders: 120% (maximum impact - clean sheet dependency)
  - Midfielders: 100% (baseline - balanced offensive/defensive)
  - Forwards: 105% (slight bonus - scoring vs weaker defenses)

**Technical Implementation**:
- **21-Point Scale**: Converts betting odds to difficulty scores (-10 to +10)
- **Calculation**: difficulty = (opponent_win_probability - 0.5) × 20
- **Final Multiplier**: 1.0 + (difficulty/10) × strength × position_weight
- **Constraints**: Multipliers capped between 0.5x and 1.5x
- **Performance**: Optimized caching reduces calculation time from 90s to 46s

**Example**:
- Arsenal vs Leeds: Leeds has 7.50 odds (13% win probability)
- Arsenal difficulty vs Leeds: (0.13 - 0.5) × 20 = -7.4
- Arsenal defender multiplier: 1.0 + (-7.4/10) × 0.2 × 1.2 = 1.178x

### Starter Predictions

**Purpose**: Penalizes players unlikely to start based on predicted lineups

**Controls**:
- **Enable/Disable**: Checkbox to toggle starter predictions
- **Auto Rotation Penalty**: Penalty for rotation-risk players (default: 0.65x)
- **Force Bench Penalty**: Penalty for likely benched players (default: 0.60x)

**How It Works**:
- CSV import identifies predicted starters (receive 1.0x multiplier)
- Non-starters receive penalty multiplier based on slider values
- Manual overrides can force specific multiplier values
- Helps avoid players likely to be rested or benched

**Multiplier Values**:
- **Starter**: 1.0x (predicted to start)
- **Rotation Risk**: Uses "Auto Rotation Penalty" slider value (default: 0.65x)
- **Bench**: Uses "Force Bench Penalty" slider value (default: 0.60x)  
- **Out**: 0.0x (injured/suspended)

### xGI Integration (Understat)

**Purpose**: Incorporates Expected Goals Involvement (xG + xA) data from Understat

**Controls**:
- **Enable/Disable**: Checkbox to toggle xGI integration
- **Multiplier Mode**: How xGI affects True Value
  - Direct: xGI90 × strength
  - Adjusted: 1 + (xGI90 × strength)  
  - Capped: Limited range (0.5 - 1.5)
- **Multiplier Strength**: xGI impact factor (default: 1.0)
- **Sync Button**: Manually sync with Understat data

**How It Works**:
- Higher xGI90 values = higher multipliers
- Accounts for underlying performance metrics
- Helps identify undervalued attacking players

### Blender Display

**Purpose**: Configures how games played data is displayed and when to switch between historical/current data

**Controls**:
- **Enable/Disable**: Always enabled (checkbox for future use)
- **Baseline Switchover Gameweek**: When to start blending historical + current data (default: 10)
- **Transition Period End**: When to switch from blended to current-only (default: 15)  
- **Show Historical Data**: Whether to display 2024-25 season data (default: checked)

**How It Works**:
- **Gameweeks 1-10**: Shows "38 (24-25)" format (historical data only)
  - Baseline = Previous Season PPG
  - Form = Recent Games / Historical Baseline
- **Gameweeks 11-15**: Shows "38+2" format (historical + current games)
  - Progressive Blending: Weighted Average(Historical PPG, Current Season PPG)
  - Weighting transitions from 100% historical to 0% historical linearly
  - Example GW13: ~60% historical + 40% current season baseline
- **Gameweeks 16+**: Shows "5" format (current season only)
  - Baseline = Current Season PPG only
  - Form = Recent Games / Current Season Baseline
- Provides context for sample size reliability and calculation methodology

## Player Table

### Columns Explained

- **Name**: Player name with tooltip information
- **Team**: Three-letter team code
- **Pos**: Position (G/D/M/F)
- **Price**: Current Fantrax price
- **PPG**: Points per game (current or blended based on gameweek)
- **PP$**: Points per dollar (PPG ÷ Price) - value indicator
- **Games**: Games played with format indicating data source
- **True Value**: Final calculated rating incorporating all multipliers
- **Form**: Form calculation multiplier (1.00x = neutral)
- **Fixture**: Fixture difficulty multiplier (>1.00x = easy fixture)
- **Starter**: Starter prediction multiplier (1.00x = predicted starter)
- **xGI**: xGI multiplier based on Understat data
- **Starter Override**: Manual override controls (S/B/O/A radio buttons)
- **xG90/xA90/xGI90**: Understat expected stats per 90 minutes
- **Min**: Minutes played

### Color Coding

**PP$ Column**:
- Green (≥0.7): Excellent value
- Blue (0.5-0.7): Good value  
- Yellow (0.3-0.5): Average value
- Red (<0.3): Poor value

**Games Column**:
- Green (≥10 games): Reliable sample size
- Yellow (5-9 games): Moderate sample size
- Red (<5 games): Small sample size

### Manual Override System

**Purpose**: Override automatic starter predictions for specific players

**Controls**:
- **S (Starter)**: Force player as starter (1.0x multiplier)
- **B (Bench)**: Force player as bench player (~0.6x multiplier)
- **O (Out)**: Force player as out (0.0x multiplier)
- **A (Auto)**: Use automatic prediction (default)

**How It Works**:
- Overrides apply immediately without needing to "Apply Changes"
- Updates True Value calculation in real-time
- Visual feedback shows updated multipliers with color coding
- Useful for insider knowledge about lineups or disagreeing with predictions

**Current Manual Overrides in System**:
```json
"manual_overrides": {
  "05tqx": {"type": "bench", "multiplier": 0.6},
  "04fk6": {"type": "bench", "multiplier": 0.6}, 
  "068n8": {"type": "out", "multiplier": 0.0},
  "06rf9": {"type": "out", "multiplier": 0.0}
}
```
- Overrides persist until manually reset to "Auto"
- Dashboard shows override status with color indicators
- System tracks all manual adjustments for audit trail

### Table Features

**Sorting**: Click any column header to sort (Games column now sorts numerically)
**Pagination**: 
- Page size options: 50, 100, 200, All
- Previous/Next navigation
- "All" option loads all ~647 players (may impact performance)
**Filtering**:
- Position checkboxes (G/D/M/F)
- Price range sliders
- Team dropdown (multi-select)
- Player name search
**Export**: CSV export with current filters and sorting applied

## Data Import Workflows

### Weekly Form Data Import

1. Click "📊 Upload Weekly Game Data" button
2. Enter gameweek number (e.g., "2" for Week 2)
3. Upload Fantrax CSV export
4. System processes points and updates metrics
5. True Values recalculated automatically

### Lineup Predictions Import

1. Click "Import Lineups CSV" 
2. Upload CSV with predicted starters
3. System applies starter/rotation penalties

### Fixture Odds Import

1. Click "⚽ Upload Fixture Odds"
2. Upload betting odds CSV  
3. System calculates fixture difficulty multipliers

## True Value Calculation

**Base Formula**: 
```
True Value = PPG × Form Multiplier × Fixture Multiplier × Starter Multiplier × xGI Multiplier
```

**Example**:
- Player PPG: 8.0
- Form Multiplier: 1.2x (good recent form)
- Fixture Multiplier: 1.1x (easy fixture)
- Starter Multiplier: 1.0x (predicted starter)
- xGI Multiplier: 1.3x (high xGI)
- **True Value**: 8.0 × 1.2 × 1.1 × 1.0 × 1.3 = **13.73**

## Configuration Management

**Apply Changes**: Save current parameter settings to system  
**Reset to Defaults**: Restore all parameters to default values  
**Parameter Persistence**: Settings saved to `config/system_parameters.json`

All parameter changes are tracked and require "Apply Changes" to take effect.

## Data Integration Systems

### Global Name Matching System

**Purpose**: Resolves player name discrepancies across multiple data sources (FFS CSV, Understat, etc.)

**Key Features**:
- **100% Visibility**: No silent failures - every player gets matched or flagged
- **Smart Suggestions**: AI-powered recommendations with confidence scoring
- **Learning System**: Builds persistent mapping database through user confirmations
- **Multi-Strategy Matching**: 6 different algorithms (exact, fuzzy, component, etc.)
- **HTML Entity Support**: Handles encoded characters from web sources

**Performance**:
- **FFS CSV Import**: 71.4% automatic match rate with 95%+ confidence
- **Understat Integration**: 16.7% automatic, 91.7% reviewable
- **Database**: 50+ verified mappings across multiple source systems

**Usage**:
- Import validation occurs automatically during CSV uploads
- Manual review interface at `/import-validation` for problematic players
- System learns from user confirmations to improve future matches

### Understat Integration

**Purpose**: Incorporates Expected Goals Involvement (xG + xA) data from Understat.com

**Integration Features**:
- **Automatic Data Sync**: "Sync Understat Data" button in xGI controls
- **Name Matching**: Uses Global Name Matching System for player resolution
- **Data Processing**: Converts Understat player names to Fantrax IDs
- **Statistics**: Real-time sync progress and match statistics

**Data Quality**:
- **155+ Players Matched**: Covers major attacking players across all teams
- **Match Confidence**: High accuracy for exact name matches
- **Manual Review**: Flagged players can be resolved via validation interface

---

## System Performance Metrics

### Efficient Processing
- **633 Players**: Complete recalculation in reasonable time for weekly analysis
- **Parameter Updates**: Dashboard changes apply efficiently across all players
- **Memory Optimization**: Caching significantly improves fixture difficulty calculation performance

### Data Integration Accuracy
- **xGI Matching**: 296/299 players matched (99% success rate)
- **Name Matching**: 6-algorithm system with confidence scoring
- **Form Calculation**: Handles missing games gracefully with fallback multipliers

### Parameter Validation Ranges
**Fixture Difficulty Multipliers**:
- 5-Tier Very Easy: 1.2-1.5x range
- 5-Tier Very Hard: 0.6-0.8x range
- 3-Tier Easy: 1.1-1.4x range
- 3-Tier Hard: 0.7-0.9x range

**Starter Prediction Penalties**:
- Auto Rotation Penalty: 0.5-0.8x range (default: 0.7x)
- Force Bench Penalty: 0.4-0.8x range (default: 0.6x)

**xGI Integration**:
- Multiplier Strength: 0.0-2.0x range (default: 0.7x)
- Capped Mode Range: 0.5-1.5x (prevents extreme multipliers)

---

**Maintenance Note**: This document must be updated after each Formula Optimization sprint with new dashboard features, UI changes, and parameter controls. See `docs/DOCUMENTATION_MAINTENANCE.md` for complete update requirements.

*Last updated: 2025-08-21 - Post Formula Optimization v2.0 Sprint 1 completion*