# Dashboard Features Guide - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter Dashboard Features

### **System Status: V2.0 Production Dashboard**

This document describes the complete dashboard features for the V2.0 Enhanced Formula system. The system has been consolidated to a single V2.0 engine with all legacy components removed.

**Dashboard URL**: `http://localhost:3000` (React Frontend)  
**API Backend**: `http://localhost:5001`  
**Current System**: V2.0 Enhanced Formula fully operational

---

## **Overview**

The V2.0 Enhanced Formula dashboard provides advanced analytics for Premier League fantasy football players, combining multiple data sources with sophisticated calculations to generate optimized "True Value" ratings and Return on Investment (ROI) metrics.

**Key V2.0 Innovations**:
- **Separated Predictions**: True Value (point prediction) distinct from ROI (value efficiency)
- **Dynamic Blending**: Smooth transition from historical to current season data
- **Exponential Form**: EWMA calculations with α=0.87 for responsive form tracking
- **Normalized xGI**: Ratio-based Expected Goals Involvement with baseline comparisons
- **Exponential Fixtures**: Advanced difficulty scaling using base^(-difficulty) formula

---

## **Trend Analysis System - Raw Data Snapshot Feature**

### **Overview: Retrospective Analysis Tool**
The V2.0 Enhanced system includes a comprehensive trend analysis system that captures weekly raw data for retrospective "apples-to-apples" analysis throughout the season.

**Key Benefits**:
- **Historical Comparison**: Apply current V2.0 parameters to past gameweeks
- **Formula Testing**: Test different parameter sets against historical raw data
- **Performance Tracking**: Track player trends using consistent calculation methods
- **Data Integrity**: Raw data capture without calculations for unbiased analysis

### **Raw Data Capture System**
**Automatic Weekly Capture**: The system automatically captures raw imported data during standard workflows:

1. **Fantrax Upload**: Captures player prices, FPts, team assignments
2. **Understat Sync**: Captures xG/xA stats and minutes played  
3. **FFP Lineup Import**: Captures starting predictions and confidence-based multipliers
4. **Odds CSV Import**: Captures fixture difficulty and home/away status
5. **Form Processing**: Captures weekly points and games played

**Data Types Captured**:
- **Player Performance**: Prices, FPts, minutes, xG stats, baseline data
- **Fixture Context**: Opponents, home/away, difficulty scores, betting odds
- **Form Progression**: Weekly points, games, season running totals
- **Starting Status**: Predicted lineups, rotation risk levels

### **Trend Analysis Interface** (Future Development)
**Dashboard Integration**: Planned integration with main dashboard for trend visualization

**Proposed Features**:
- **Parameter Comparison Tool**: Compare different V2.0 settings across gameweeks
- **Player Performance Charts**: Visual trend tracking with formula consistency
- **Gameweek Selection**: Choose specific weeks or ranges for analysis
- **Export Functionality**: Download trend data for external analysis

**API Access**: Available through `/api/trends/calculate` and `/api/trends/raw-data` endpoints

### **Technical Implementation**
**Database Tables**:
- `raw_player_snapshots` - Weekly player performance data
- `raw_fixture_snapshots` - Weekly fixture and odds data  
- `raw_form_snapshots` - Weekly form progression data

**Current Season Focus**: Uses current-season-only baselines for immediate Week 1 data capture

**Live Table Mode**: All data uploads update the single live table for immediate dashboard reflection

### **Usage Examples**
**Testing New Parameters**: Apply modified V2.0 parameters to GW1 data to predict performance
**Player Comparison**: Compare two players using identical formula settings across multiple weeks  
**Formula Validation**: Test accuracy of different multiplier caps or EWMA settings
**Seasonal Analysis**: Track how fixture difficulty impacts different positions over time

---

## **Weekly Archive System - Analysis State Management** ✅ *Added 2025-08-28*

### **Overview: Weekly Analysis Workflow**
The V2.0 Enhanced system includes a streamlined weekly analysis workflow that preserves complete analysis states for historical reference and trend comparison.

**Key Innovation**: Manual archive button in React dashboard for flexible weekly workflow management without rigid gameweek constraints.

### **Archive Workflow Integration**

**1. Complete Weekly Analysis**
- Upload new data to live table (Fantrax CSV, Understat sync, odds data)
- Run calculations and parameter optimizations  
- Review True Value and ROI rankings
- Optimize lineup selections and strategy

**2. Archive Analysis State** 
- Click **"Archive Week"** button in React dashboard
- System preserves complete analysis snapshot:
  - All player True Values and ROI calculations
  - Current system parameters and multiplier settings
  - Form data and fixture assessments  
  - Top performer analysis and rankings

**3. Prepare for Next Week**
- System ready for fresh data imports
- Previous analysis safely archived for comparison
- Historical trend analysis available through archived states

### **Archive System Benefits**

**Workflow Flexibility**: 
- No complex gameweek management - single live table approach
- Archive when analysis is complete, not on fixed schedule
- Maintain live analysis capability with continuous data updates

**Data Continuity**: 
- Complete preservation of analysis decisions and reasoning
- Historical comparison of parameter effectiveness
- Season-long performance tracking and validation

**Error Recovery**: 
- Safe rollback point if data imports encounter issues
- Protection against accidental overwrites during busy periods
- Backup of successful analysis states for reference

### **Dashboard Archive Controls**

**Archive Week Button**: 
- Location: React dashboard main interface
- Function: Creates comprehensive analysis snapshot
- Feedback: Displays archived player count and success confirmation
- Timing: Use after completing weekly analysis, before importing new data

**Archive Status Display**:
- Shows last archived gameweek information
- Displays archived player count and timestamp  
- Provides quick verification of archive completion
- Links to historical archive management (future development)

**Integration with Data Imports**:
- Suggested workflow: Archive → Import → Analyze → Archive
- Seamless transition between weekly analysis cycles
- Protection against data loss during import operations
- Maintains analysis consistency with live data updates

---

## **V2.0 Enhanced Parameter Controls Panel**

All V2.0 features are configured through the Parameter Controls panel with enhanced controls and real-time feedback.

### **Dynamic Blending System**
**Purpose**: Seamlessly transitions from historical (2024-25) to current season data using mathematical blending

**V2.0 Enhanced Controls**:
- **Enable Dynamic Blending**: Toggle for V2.0 blending system (always enabled)
- **Full Adaptation Gameweek**: When to reach current-only data (default: 16)
- **Blending Progress**: Visual indicator showing current weights
- **Transition Status**: Early season, transitioning, or current-only indicators

**Technical Implementation**:
- **Mathematical Formula**: `w_current = min(1, (N-1)/(K-1))`
- **Current Formula (GW2)**: 6.7% current + 93.3% historical
- **Smooth Transition**: No hard cutoffs, gradual weight progression
- **Database Integration**: Real-time calculation of `historical_ppg` from 2024-25 data

**Display Format**:
- **Early Season**: "27+1" (27 historical + 1 current games)
- **Mid Season**: Continues blended format with increasing current weight
- **Late Season**: Pure current season display

### **Progressive Form Calculation (EWMA) with Sample-Size Ranges** ✅ *Added 2025-08-28*
**Purpose**: Advanced form tracking using Exponential Weighted Moving Average with progressive multiplier ranges based on statistical confidence

**V2.0 Enhanced Controls**:
- **Enable Exponential Form**: Toggle for EWMA calculation (default: enabled)
- **Alpha Parameter**: Decay rate slider (0.70-0.995, default: 0.87)
- **Progressive Ranges**: Sample-size-aware multiplier boundaries (default: enabled)
- **Baseline Comparison**: Form relative to blended PPG instead of fixed baseline

**Progressive Form Ranges System**:
The system dynamically adjusts Form multiplier boundaries based on games played for statistical confidence:

- **Games 1-2**: ±5% range (0.95-1.05) - Tight early-season control
- **Games 3-4**: ±15% range (0.85-1.15) - Moderate expansion  
- **Games 5-6**: ±20% range (0.80-1.20) - Increased differentiation
- **Games 7-8**: ±25% range (0.75-1.25) - Strong sample confidence
- **Games 9-10**: ±30% range (0.70-1.30) - Full statistical confidence
- **Games 11+**: ±30% range maintained - Maximum differentiation allowed

**Technical Implementation**:
- **Algorithm**: EWMA with exponential decay (α^0, α^1, α^2 for recent games)
- **5-Game Half-Life**: α=0.87 provides optimal balance of responsiveness and stability
- **Progressive Boundaries**: `form_multiplier = max(form_min, min(form_max, raw_ewma))`
- **Baseline Normalization**: Compares to dynamic blended PPG, not static average
- **Real-time Updates**: Form scores update immediately with new game data

**Early Season Benefits**:
- **Volatility Control**: 50% reduction in early-season multiplier extremes (±5% vs ±10%)
- **Statistical Rigor**: Multiplier ranges expand as sample size increases reliability
- **Performance Balance**: Form impact scales appropriately relative to other multiplier systems
- **Neutral Defaults**: Similar early-season performance results in ~1.0x multipliers

**Examples**:
- **Early Season (2 games)**: Raw EWMA 0.85 → Capped at 0.95 (±5% limit)
- **Mid Season (6 games)**: Raw EWMA 0.85 → Applied as 0.85 (±20% allows full range)
- **Late Season (15 games)**: Raw EWMA 0.70 → Applied as 0.70 (±30% maximum range)
- **Neutral Form**: Form matches expectation = 1.0x multiplier regardless of games played

### **NPxG Fixture System**
**Purpose**: Team strength assessment using Non-Penalty Expected Goals data for fixture difficulty

**V2.0 Enhanced Controls**:
- **Enable NPxG Fixtures**: Toggle for NPxG-based difficulty (default: enabled)
- **NPxG Weight**: Repurposed "Fixture Base" slider controls strength (-20% to +20%)
- **Position-Specific Calculations**: Automatic attacking/defensive component weighting
- **Home/Away Adjustments**: Built-in location-based modifiers

**Technical Implementation**:
- **Attacking Component**: `(opponent_npxga / league_avg_npxga) × home_away_mult × weight`
- **Defensive Component**: `(league_avg_npxg / opponent_npxg) × home_away_mult × weight`
- **Position Mapping**:
  - **Goalkeepers/Defenders**: 100% defensive component
  - **Forwards**: 100% attacking component
  - **Midfielders**: 75% attacking + 25% defensive blend
- **Home/Away Adjustments**: Attacking (±10%), Defensive (±15%)
- **Team Alias Resolution**: Automatic BRF→BRE, NOT→NFO mapping

**Examples**:
- **vs Weak Defense (home)**: High NPxGA opponent + home boost = 1.2x multiplier
- **@ Strong Defense (away)**: Low NPxGA opponent + away penalty = 0.7x multiplier
- **Neutral Matchup**: Average team strength = 1.0x multiplier

### **Normalized xGI Integration**
**Purpose**: Advanced Expected Goals Involvement using ratio-based comparisons with position-specific adjustments

**V2.0 Enhanced Controls**:
- **Enable Normalized xGI**: Master toggle for xGI system (default: enabled)
- **Apply xGI to True Value**: User control toggle (default: disabled early season)
- **Position Adjustments**: Automatic adjustments for defenders/goalkeepers
- **xGI Caps**: Enhanced range 0.5-2.5x for controlled impact

**Technical Implementation**:
- **Calculation**: `current_xgi90 ÷ baseline_xgi` (ratio-based normalization)
- **Baseline Source**: 2024-25 season averages from Understat integration
- **Position Logic**:
  - **Goalkeepers**: xGI completely disabled (not relevant)
  - **Defenders**: 30% impact reduction when baseline < 0.2
  - **Midfielders/Forwards**: Full impact (100%)

**Early Season Strategy**:
- **Default State**: Disabled (xGI multiplier = 1.0x)
- **Rationale**: Limited 2025-26 sample sizes create volatile ratios
- **Activation**: User can enable when confident in current season data (~GW5+)
- **Examples**: Ben White (0.909x), Calafiori (2.500x capped) show early season volatility

### **V2.0 Progressive Multiplier Cap System**
**Purpose**: Prevents extreme outliers while allowing meaningful differentiation with sample-size awareness

**Enhanced Caps**:
- **Form Cap**: Progressive ranges (0.95-1.05 early → 0.70-1.30 late season) - Sample-size aware boundaries
- **Fixture Cap**: 0.5-1.8x (maintains reasonable difficulty impact)
- **xGI Cap**: 0.5-2.5x (allows significant xGI differentiation)
- **Global Cap**: 3.0x maximum (product of all multipliers)

**Visual Indicators**:
- Cap application shown in player tooltips
- Color coding indicates when caps are applied
- Metadata tracks which caps affected each player

---

## **V2.0 Enhanced Player Table**

### **Core V2.0 Columns**

**Enhanced Value Columns**:
- **True Value**: V2.0 point prediction (separate from price consideration)
- **ROI**: Return on Investment (True Value ÷ Price) with green gradient styling
- **Blended PPG**: Dynamic blend of historical/current season data
- **Games Display**: Shows blending format ("27+1", "38+2", "5")

**V2.0 Multiplier Columns**:
- **Form**: Progressive EWMA form multiplier with sample-size aware boundaries (±5% early → ±30% late season)
- **Fixture**: Exponential difficulty multiplier (base^(-difficulty))
- **Starter**: Rotation penalty multiplier (manual override capable)
- **xGI**: Normalized ratio multiplier (with enable/disable control)

**Enhanced Data Columns**:
- **Baseline xGI**: Historical 2024-25 xGI average for normalization
- **Historical PPG**: 2024-25 season PPG for blending calculations
- **Current Weight**: Dynamic blending weight (e.g., 0.067 for 6.7% current)

### **V2.0 Color Coding System**

**True Value Column**:
- **Deep Blue (>15.0)**: Elite players with high point predictions
- **Blue (10.0-15.0)**: Premium players with strong predictions
- **Green (7.5-10.0)**: Quality players with good predictions
- **Yellow (5.0-7.5)**: Average players with moderate predictions
- **Red (<5.0)**: Low-value players with poor predictions

**ROI Column** (V2.0 Feature):
- **Green Gradient**: Higher ROI values receive stronger green intensity
- **Threshold Indicators**: >2.0 (excellent), 1.5-2.0 (good), 1.0-1.5 (fair), <1.0 (poor)
- **NULL Handling**: Missing ROI values display appropriately

**Games Display Column**:
- **Color Intensity**: Based on total games (current + historical)
- **Format Indicators**: Visual cues for blending status
- **Sample Size Warning**: Red highlighting for insufficient data

### **V2.0 Enhanced Manual Override System**

**Purpose**: Real-time manual overrides with instant V2.0 recalculation

**Override Controls** (per player):
- **S (Starter)**: Force starter status (1.0x multiplier)
- **B (Bench)**: Force bench status (0.6x multiplier)
- **O (Out)**: Force unavailable (0.0x multiplier)
- **A (Auto)**: Use automatic prediction (system default)

**V2.0 Enhanced Features**:
- **Instant Recalculation**: True Value updates immediately using V2.0 engine
- **ROI Update**: ROI column reflects new True Value instantly
- **Visual Feedback**: Color coding shows override status
- **Multiplier Tracking**: All multipliers recalculated with V2.0 formula

**Example Override Impact**:
```
Erling Haaland Override: B → S
- Starter Multiplier: 0.6x → 1.0x
- True Value: 17.07 → 28.45 (+66.8% increase)
- ROI: 1.138 → 1.896 (+66.8% increase)
- Calculation Time: ~45ms with V2.0 engine
```

### **V2.0 Table Features**

**Enhanced Sorting**:
- **True Value**: Default sort by V2.0 point predictions
- **ROI**: V2.0 value efficiency with NULL handling
- **Numeric Games**: Proper numerical sorting of total games
- **Multiple Criteria**: Secondary sorts for tie-breaking

**Advanced Filtering**:
- **Position Logic**: Enhanced position-specific filtering
- **Value Ranges**: True Value and ROI range filters
- **Team Analysis**: Multi-team comparison capabilities
- **Search Enhancement**: Improved player name matching

**Performance Optimization**:
- **Efficient Pagination**: 50/100/200/All options with optimized queries
- **Real-time Updates**: Parameter changes reflected immediately
- **Export Enhancement**: CSV includes all V2.0 columns and metadata

---

## **V2.0 Data Import Workflows**

### **Enhanced Weekly Game Data Import**

**Process**:
1. Click "📊 Upload Weekly Game Data" button → ✅ Working (2025-08-23)
2. Data automatically goes to live table → ✅ Working
3. Upload Fantrax CSV export with enhanced validation → ✅ Working
4. **V2.0 Processing**:
   - Dynamic blending weights recalculated → ✅ Working
   - EWMA form scores updated → ✅ Working  
   - True Value and ROI refreshed → ✅ Working
   - CSV validation with error handling → ✅ Working
   - Success confirmation display → ✅ Working
   - Historical data integration confirmed

**V2.0 Enhancements**:
- **99% Match Rate**: Enhanced name matching with confidence scoring
- **Blending Integration**: Automatic historical data integration
- **Form Updates**: EWMA recalculation with new game data
- **Validation Feedback**: Real-time import statistics and quality metrics

### **FFP Lineup Import** ✅ *Working September 2025*

**🚨 IMPORTANT PATH**: Only use the dashboard football icon button for FFP imports:
- ✅ **WORKING**: Main dashboard → Football icon button → "Import lineup CSV" (hover text)
- ❌ **NOT WORKING**: Top menu "Upload & Sync" → "Import Lineup CSV"

**V2.0 Enhanced Process**:
1. Click **⚽ football icon** on main dashboard (with hover text "Import lineup CSV")
2. Upload Fantasy Football Pundit CSV file
3. **Enhanced Name Matching**:
   - UnifiedNameMatcher with source system consistency ('ffp')
   - FFP team names automatically converted to database codes
   - Confidence-based starter multiplier assignment using frontend parameters
4. **Validation Workflow**:
   - Unmatched players trigger manual validation interface at `localhost:5001/import-validation`
   - Manual confirmation creates persistent database mappings
   - Pre-validated players bypass validation on subsequent imports
5. **Automatic Multiplier Application**:
   - Confidence-based multipliers applied immediately after validation
   - Uses configurable system parameters from frontend adjustment panels
   - Triggers automatic true value recalculation

**Confidence-Based Multipliers** (configurable via frontend):
- **90-100% confidence** → 1.0x multiplier (definite starter)
- **70-89% confidence** → likely_starter_penalty parameter (~0.90)
- **50-69% confidence** → auto_rotation_penalty parameter (~0.75)
- **30-49% confidence** → unlikely_starter_penalty parameter (~0.50)
- **<30% confidence** → force_bench_penalty parameter (~0.35)

**Expected Performance**: Name mapping persistence ensures no repeated validations. Confidence parsing works correctly (90% CSV = 90% system = 1.0x multiplier).

### **NPxG Fixture Data Integration**

**Automatic Process**:
- NPxG fixture multipliers are calculated automatically using team metrics
- No manual CSV import required (replaced the old betting odds workflow)
- Team strength data is maintained in the database
- Automatic team code alias resolution ensures accurate mappings

### **Starter Predictions with V2.0 Integration**

**Enhanced Processing**:
- Manual override system integrated with V2.0 calculations
- Real-time True Value and ROI updates
- Position-aware penalty applications
- Instant visual feedback in dashboard

---

## **V2.0 True Value Calculation Formula**

### **Enhanced V2.0 Formula**
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Price
```

### **Detailed V2.0 Example**
```
Player: Erling Haaland (Manchester City)
Price: £15.00

Components:
- Blended PPG: 8.45 (6.7% current + 93.3% historical)
- Form Multiplier: 0.952 (EWMA below baseline)
- NPxG Fixture Multiplier: 0.866 (away vs Brentford)
- Starter Multiplier: 1.000 (predicted starter)
- xGI Multiplier: 0.895 (normalized xGI ratio)

Calculation:
True Value = 8.45 × 0.952 × 0.866 × 1.000 × 0.895 = 6.24

ROI = 6.24 ÷ 15.00 = 0.416

Result: Moderate True Value with below-average ROI due to premium pricing and difficult away fixture
```

### **V2.0 Calculation Features**
- **Separated Metrics**: True Value (prediction) vs ROI (efficiency)
- **Dynamic Baseline**: Blended PPG adapts throughout season
- **Exponential Scaling**: More accurate multiplier calculations
- **Position Awareness**: Role-appropriate adjustments
- **Cap Management**: Prevents unrealistic extreme values

---

## **V2.0 Configuration Management**

### **Enhanced Parameter Controls**
- **Apply Changes**: Save V2.0 parameters with instant recalculation
- **Reset to V2.0 Defaults**: Restore optimal V2.0 parameter values
- **Real-time Preview**: Parameter changes show immediate effect estimates
- **Configuration Persistence**: V2.0 settings saved to `config/system_parameters.json`

### **V2.0 Parameter Structure**
```json
{
  "formula_optimization_v2": {
    "exponential_form": {
      "enabled": true,
      "alpha": 0.87
    },
    "dynamic_blending": {
      "enabled": true,
      "full_adaptation_gw": 16
    },
    "normalized_xgi": {
      "enabled": true,
      "enable_xgi": false
    },
    "exponential_fixtures": {
      "enabled": true,
      "base": 1.05
    }
  },
  "multiplier_caps": {
    "form": 2.0,
    "fixture": 1.8,
    "xgi": 2.5,
    "global": 3.0
  }
}
```

---

## **V2.0 Data Integration Systems**

### **Enhanced Name Matching System** ✅ VERIFIED (2025-08-23)
**V2.0 Improvements**:
- **98%+ Success Rate**: 298/304 players automatically matched in testing
- **Multi-Source Integration**: Fantrax, Understat, FFS, manual overrides → ✅ Working
- **Confidence Scoring**: Advanced AI-powered matching with reliability metrics → ✅ Working
- **Learning System**: Persistent database builds from user confirmations → ✅ Working
- **Manual Verification Workflow**: Unmatched players properly flagged for review → ✅ Working

**Performance Metrics**:
- **Understat Integration**: 335 players with baseline xGI data
- **Form Data**: 100% player coverage with graceful missing data handling
- **Fixture Odds**: Real-time integration with 2x performance improvement

### **V2.0 Understat Integration**
**Enhanced Features**:
- **Baseline Data**: 335 players with 2024-25 season xGI baselines
- **Normalized Calculations**: Ratio-based comparisons for accurate relative performance
- **Position Logic**: Automatic adjustments for role-appropriate xGI impact
- **Real-time Sync**: "Sync Understat Data" with progress tracking

**Data Quality**:
- **Coverage**: All major attacking players across 20 Premier League teams
- **Accuracy**: High confidence exact matches with manual review for edge cases
- **Integration**: Seamless V2.0 calculation pipeline with normalized ratios

---

## **V2.0 System Performance Metrics**

### **Calculation Performance**
- **647 Players**: Complete V2.0 recalculation in <1 second
- **Real-time Updates**: Parameter changes apply instantly across all players
- **Database Optimization**: Sub-second API response times for full dataset
- **Memory Efficiency**: <200MB peak usage during complex calculations

### **V2.0 Enhanced Accuracy**
- **Dynamic Blending**: Smooth mathematical transitions eliminate hard cutoffs
- **EWMA Form**: 5-game half-life provides optimal responsiveness
- **Exponential Fixtures**: More accurate difficulty scaling than linear multipliers
- **Normalized xGI**: Proper baseline comparisons account for positional differences

### **Data Integration Quality**
- **Match Rates**: 99% success across all data sources
- **Missing Data Handling**: Graceful fallbacks maintain calculation integrity
- **Real-time Validation**: Instant feedback on data quality and completeness
- **Audit Trail**: Complete tracking of all calculations and data sources

---

## **V2.0 User Experience Features**

### **Enhanced Visual Design**
- **V2.0 Indicators**: Clear badges and highlighting for V2.0-specific features
- **Color Schemes**: Enhanced gradients for True Value and ROI columns
- **Responsive Design**: Optimized layout for parameter controls and data display
- **Tooltip System**: Professional explanations for all 17+ columns

### **Performance Feedback**
- **Calculation Status**: Real-time indicators during parameter updates
- **Progress Tracking**: Visual feedback for data imports and calculations
- **Error Handling**: Clear messages for any V2.0 calculation issues
- **Success Confirmation**: Immediate feedback on successful operations

### **Professional Interface**
- **Dashboard Layout**: Clean two-panel design with parameter controls and data table
- **Navigation**: Intuitive workflow for data imports and parameter adjustments
- **Export Capabilities**: Enhanced CSV exports with all V2.0 metadata
- **Mobile Compatibility**: Responsive design works across device types

---

## **Lineup Optimizer** ✅ *Added 2026-01-04*

### **Overview: ILP-Based Team Optimization**
The Lineup Optimizer uses Integer Linear Programming (ILP) with PuLP to find mathematically optimal lineups based on True Value scores, budget constraints, and formation requirements.

**Dashboard Access**: Navigate to the "Lineup Optimizer" tab in the React dashboard

### **Core Features**

**1. Roster Import**
- Import your current Fantrax team roster via CSV export
- Automatic matching of players to database records with True Value data
- Budget calculation based on purchase prices from CSV

**2. Pitch Visualization**
- Interactive football pitch display showing your current lineup
- Players grouped by position (GK, DEF, MID, FWD)
- Formation badge displays current formation (e.g., 3-5-2, 3-4-3)

**3. Player Actions (Icon Buttons)**
- **Lock Icon (top right)**: Lock/unlock players to keep them in optimized lineups
- **Replace Icon (top left)**: Swap any player with another from the full database
  - Search by name with position filtering
  - Replaced players are automatically locked
  - Budget and True Value totals update automatically

**4. Lock Discounted Button**
- One-click button to lock all players where purchase price < current market value
- Shows count of discounted players (players that appreciated in value)
- Protects value gains when optimizing

### **Optimization Engine**

**ILP Formulation**:
```
Maximize: Σ(x_i × true_value_i)
Subject to:
  - Budget: Σ(x_i × price_i) ≤ remaining_budget
  - Total: Σ(x_i) = 11 players
  - Positions: 1 GK, 3-5 DEF, 3-5 MID, 1-3 FWD
  - Locked: x_i = 1 for locked players
```

**Multi-Position Handling**: Players with dual positions (e.g., "M,F") are expanded into separate variables with mutual exclusion constraints.

### **Lineup Generation**

**Per Formation Output** (18 total lineups):
- **6 Optimal Lineups**: Best True Value combinations with variation constraints
- **3 Differential Lineups**: Exclude top 8 performers to surface alternative picks

**Formation Support**:
- 3-5-2: 3 defenders, 5 midfielders, 2 forwards
- 3-4-3: 3 defenders, 4 midfielders, 3 forwards

### **Player Exclusion System**

**From Players Table**:
- Checkbox column to exclude specific players from optimization
- "Reset Exclusions" button to clear all exclusions
- Filter dropdown to view only excluded players
- Excluded players won't appear in any generated lineups

### **Usage Workflow**

1. **Import Roster**: Export your team from Fantrax → Import CSV in Lineup Optimizer
2. **Lock Key Players**: Click lock icon or use "Lock Discounted" button
3. **Replace if Needed**: Click replace icon to swap in different players
4. **Exclude Unwanted**: Use Players table checkbox to exclude specific players
5. **Generate Lineups**: Click "GENERATE LINEUPS" button (prominent button in Team Stats panel)
6. **Review Options**: Browse 9 lineups per formation (6 optimal + 3 differential)
7. **Select Lineup**: Click any lineup card to view it on the pitch
8. **Reset to Original**: Use "Reset to Original" button to restore your imported CSV lineup

### **Visual Indicators**
- **Gold Border**: Locked players (protected from optimization)
- **Cyan Border**: New players suggested by optimizer (not in your original CSV)

### **Built-in Help Section**
The optimizer includes a "How to Use" panel explaining all features:
- Lock Players, Lock Discounted, Replace Players
- Optimal vs Differential lineup types
- Exclude Players from main dashboard
- Cyan border meaning for new players

### **Technical Implementation**

**Dependencies**: `pulp>=2.7.0` (added to requirements.txt)

**API Endpoints**:
- `POST /api/lineup/import` - Import roster CSV
- `POST /api/lineup/optimize` - Generate optimized lineups
- `POST /api/players/<id>/toggle-exclude` - Toggle player exclusion
- `POST /api/players/reset-exclusions` - Reset all exclusions
- `GET /api/players?search=<term>` - Search players for replacement

**Frontend Components**:
- `LineupOptimizer.js` - Main optimizer interface
- `PitchView.js` - Football pitch visualization
- `PlayerSearchDialog.js` - Player replacement search modal
- `InspirationLineups.js` - Inspiration lineup viewer

---

## **Inspiration Lineups** ✅ *Added 2026-01-06*

### **Overview: View-Only Best XI by Metric**
The Inspiration Lineups feature displays the top players by various metrics in a read-only pitch view. This helps users discover high-performing players they might want to target.

**Visibility**: Appears below the main Lineup Optimizer after importing a roster CSV

### **Metric Options**
Select from 6 different metrics via dropdown:
- **Projected Points**: Best True Value scores (default)
- **Best Form**: Highest form multipliers
- **XG90+XA90**: Best xGI multiplier scores
- **Points per game**: Highest PPG
- **Points per 90**: Highest PP90 (calculated from total points / minutes × 90)
- **Value (ROI)**: Best return on investment

### **Formation & Bench**
- **Formation**: Fixed 3-4-3 (1 GK, 3 DEF, 4 MID, 3 FWD)
- **Bench**: 7 players (1 GK, 2 DEF, 2 MID, 2 FWD)

### **Filters**
- **Minimum Minutes**: Only players with 135+ minutes played are eligible
- **Likely Starters Toggle**: Optional filter to only show players with starter_multiplier ≥ 0.8

### **Display Features**
- **Pitch View**: Football pitch layout matching the main optimizer
- **Stats Panel**: Shows total metric value, team cost, formation, and player counts
- **Player Cards**: Compact cards showing name, team, price, and selected metric value
- **Tooltips**: Hover for full player details (price, minutes, projected, PPG, form)

### **Use Cases**
- Discover undervalued players with high ROI
- Find in-form players to target for transfers
- Compare best possible XIs across different metrics
- Identify likely starters with strong projections

---

**Last Updated**: 2026-01-06 - V2.0 Enhanced Formula Dashboard with Lineup Optimizer and Inspiration Lineups

*This document reflects the current V2.0-only dashboard features with all legacy components removed. The dashboard serves 714 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form calculations, and normalized xGI integration. The trend analysis system enables retrospective analysis using captured raw data snapshots for season-long performance tracking.*