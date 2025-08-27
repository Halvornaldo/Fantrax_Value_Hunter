# Database Schema - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter Database Structure

### **System Status: V2.0 Production Database**

This document describes the complete database schema for the V2.0 Enhanced Formula system. The system has been consolidated to a single V2.0 engine with all legacy components removed.

**Database Environment:**
- **Database**: `fantrax_value_hunter`  
- **Host**: `localhost`  
- **Port**: `5433`  
- **Username**: `fantrax_user`  
- **Password**: `fantrax_password`
- **Total Players**: 647 Premier League players

---

## **Raw Data Snapshot System**

### **Overview: Retrospective Trend Analysis Architecture**
The V2.0 Enhanced system includes a raw data snapshot system that captures weekly imported data without calculations. This enables "apples-to-apples" trend analysis by applying the same formula parameters retroactively to different gameweeks.

**Key Benefits:**
- Compare player performance across weeks using consistent V2.0 Enhanced parameters
- Analyze formula effectiveness over time
- Test different parameter sets against historical raw data
- Track weekly changes in prices, form, fixtures, and performance

### **`raw_player_snapshots`** - Weekly Player Performance Data
**Purpose**: Capture raw imported data (prices, FPts, xG stats) without any calculations for retrospective analysis

**Primary Key**: `(player_id, gameweek)`
**Owner**: `fantrax_user`

**Core Player Data**:
- `player_id` (VARCHAR(10) NOT NULL) - Player identifier
- `gameweek` (INTEGER NOT NULL) - Gameweek number
- `name` (VARCHAR(255)) - Player name at time of capture
- `team` (VARCHAR(3)) - Team code at time of capture
- `position` (VARCHAR(10)) - Playing position
- `price` (DECIMAL(5,2)) - Fantrax price for that gameweek
- `fpts` (DECIMAL(6,2)) - Fantrax points scored that gameweek
- `minutes_played` (INTEGER DEFAULT 0) - Minutes played that gameweek

**Expected Goals Data** (Understat raw weekly stats):
- `xg90` (DECIMAL(5,3)) - Expected goals per 90 minutes (cumulative)
- `xa90` (DECIMAL(5,3)) - Expected assists per 90 minutes (cumulative)  
- `xgi90` (DECIMAL(5,3)) - Expected goals involvement per 90 minutes (cumulative)
- `baseline_xgi` (DECIMAL(5,3)) - Historical 2024-25 baseline for normalization

**Fixture Context**:
- `opponent` (VARCHAR(3)) - Opponent team code
- `is_home` (BOOLEAN) - Home/away indicator
- `fixture_difficulty` (DECIMAL(5,2)) - Calculated difficulty score

**Starting Status** (FFS prediction data):
- `is_predicted_starter` (BOOLEAN) - Starting prediction
- `rotation_risk` (VARCHAR(10)) - Risk level ('low', 'medium', 'high', 'benched')

**Metadata**:
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Capture timestamp
- `fantrax_import` (BOOLEAN DEFAULT FALSE) - Data source flags
- `understat_import` (BOOLEAN DEFAULT FALSE)
- `ffs_import` (BOOLEAN DEFAULT FALSE)
- `odds_import` (BOOLEAN DEFAULT FALSE)

**Constraints**:
- `UNIQUE(player_id, gameweek)` - One record per player per gameweek
- `CHECK (gameweek > 0)` - Valid gameweek numbers

### **`raw_fixture_snapshots`** - Weekly Fixture and Odds Data
**Purpose**: Capture fixture difficulty and betting odds data for each gameweek

**Primary Key**: `(team_code, gameweek)`
**Owner**: `fantrax_user`

**Fixture Data**:
- `team_code` (VARCHAR(3) NOT NULL) - Team identifier
- `gameweek` (INTEGER NOT NULL) - Gameweek number
- `opponent_code` (VARCHAR(3) NOT NULL) - Opponent team code
- `is_home` (BOOLEAN NOT NULL) - Home/away indicator
- `difficulty_score` (DECIMAL(5,2)) - Calculated difficulty score

**Betting Odds** (raw odds for difficulty calculation):
- `home_odds` (DECIMAL(6,2)) - Home win odds
- `draw_odds` (DECIMAL(6,2)) - Draw odds
- `away_odds` (DECIMAL(6,2)) - Away win odds
- `implied_prob_home` (DECIMAL(5,4)) - Calculated home win probability
- `implied_prob_away` (DECIMAL(5,4)) - Calculated away win probability

**Metadata**:
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Capture timestamp
- `odds_source` (VARCHAR(50)) - Odds data source

**Constraints**:
- `UNIQUE(team_code, gameweek)` - One record per team per gameweek
- `CHECK (gameweek > 0)` - Valid gameweek numbers

### **`raw_form_snapshots`** - Weekly Form Tracking Data  
**Purpose**: Capture weekly form progression for EWMA calculations

**Primary Key**: `(player_id, gameweek)`
**Owner**: `fantrax_user`

**Form Tracking**:
- `player_id` (VARCHAR(10) NOT NULL) - Player identifier
- `gameweek` (INTEGER NOT NULL) - Gameweek number
- `points_scored` (DECIMAL(5,2) NOT NULL) - Points scored that gameweek
- `games_played` (INTEGER NOT NULL) - Games played that gameweek (0 or 1)

**Running Totals** (for season calculations):
- `total_points_season` (DECIMAL(8,2)) - Running season total
- `total_games_season` (INTEGER) - Running season games count
- `ppg_season` (DECIMAL(5,2)) - Running season PPG

**Metadata**:
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Capture timestamp

**Constraints**:
- `UNIQUE(player_id, gameweek)` - One record per player per gameweek
- `CHECK (gameweek > 0)` - Valid gameweek numbers
- `CHECK (games_played IN (0, 1))` - Valid games played values

### **Database Views for Raw Data Access**

#### **`raw_data_complete`** - Comprehensive Raw Data View
Complete view combining all raw snapshot data for trend analysis:
```sql
SELECT 
    rps.player_id, rps.gameweek, rps.name, rps.team, rps.position,
    rps.price, rps.fpts, rps.minutes_played,
    rps.xg90, rps.xa90, rps.xgi90, rps.baseline_xgi,
    rps.opponent, rps.is_home, rps.fixture_difficulty,
    rps.is_predicted_starter, rps.rotation_risk,
    rfs.points_scored, rfs.games_played,
    rfs.total_points_season, rfs.total_games_season, rfs.ppg_season
FROM raw_player_snapshots rps
LEFT JOIN raw_form_snapshots rfs 
    ON rps.player_id = rfs.player_id AND rps.gameweek = rfs.gameweek
ORDER BY rps.player_id, rps.gameweek
```

#### **`raw_form_history`** - Form Analysis View
Form progression view for EWMA calculations:
```sql
SELECT 
    player_id, gameweek, points_scored, games_played,
    ppg_season,
    LAG(points_scored, 1) OVER (PARTITION BY player_id ORDER BY gameweek) as prev_points,
    LAG(points_scored, 2) OVER (PARTITION BY player_id ORDER BY gameweek) as prev_2_points,
    AVG(points_scored) OVER (PARTITION BY player_id ORDER BY gameweek ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) as form_8gw
FROM raw_form_snapshots
ORDER BY player_id, gameweek
```

### **Gameweek Detection Pattern**
**🎯 CRITICAL**: All functions accessing raw data MUST use database-driven gameweek detection

**✅ CORRECT PATTERN:**
```sql
SELECT MAX(gameweek) FROM raw_player_snapshots WHERE gameweek IS NOT NULL
```

**❌ INCORRECT PATTERNS TO AVOID:**
- `gameweek = 1` (hardcoded values)
- Parameter-based gameweek without database validation
- Assumptions about current gameweek

### **Raw Data Import Integration**
**Data Flow**: Raw snapshots are populated during standard import processes:

1. **Fantrax Upload**: Captures player prices, FPts, team data → `raw_player_snapshots`
2. **Understat Sync**: Captures xG stats, minutes → `raw_player_snapshots` 
3. **FFS Lineup Upload**: Captures starting predictions → `raw_player_snapshots`
4. **Odds CSV Import**: Captures fixture difficulty → `raw_fixture_snapshots`
5. **Form Calculation**: Aggregates weekly points → `raw_form_snapshots`

### **🎯 NEW: Rolling Minutes-Based Games Detection (2025-08-26)**
**Purpose**: Intelligent games_played detection using minutes comparison across gameweeks

**Algorithm**:
```sql
-- Get current total minutes from Understat sync
SELECT COALESCE(minutes, 0) FROM players WHERE id = %s

-- Get previous gameweek snapshot minutes
SELECT COALESCE(minutes_played, 0) 
FROM raw_player_snapshots 
WHERE player_id = %s AND gameweek = %s-1

-- Determine if player played this gameweek
games_played = 1 IF current_total_minutes > previous_gameweek_minutes ELSE 0
```

**Rolling Pattern**: Uses `gameweek - 1` snapshot for dynamic comparison:
- **GW2 Upload**: Compares total minutes vs GW1 snapshot
- **GW3 Upload**: Compares total minutes vs GW2 snapshot  
- **GW4 Upload**: Compares total minutes vs GW3 snapshot

**Workflow Integration**:
1. **Sync Understat Data** → Updates `players.minutes` with current total
2. **Upload CSV** → Uses minutes comparison for accurate `games_played` detection
3. **Create New Snapshot** → Captures current gameweek data for next comparison

### **🎯 PPG CALCULATION ENHANCEMENT (2025-08-26)**
**Purpose**: Fixed critical PPG calculation discrepancy in V2.0 True Value formula

**Problem Identified**: 
- Display PPG was correctly calculated using MAX(points) from cumulative form data
- V2.0 calculations used stale stored PPG values instead of fresh calculations
- Form imports triggered PPG recalculation but not V2.0 True Value updates

**Enhanced PPG Query Pattern**:
```sql
-- Correct PPG calculation using MAX(points) from player_form
CASE 
    WHEN COALESCE(pgd.games_played, 0) > 0 
    THEN COALESCE(pf_max.total_points, 0) / pgd.games_played
    ELSE 0 
END as ppg,

-- With form data aggregation
LEFT JOIN (
    SELECT player_id, MAX(points) as total_points
    FROM player_form
    GROUP BY player_id
) pf_max ON p.id = pf_max.player_id
```

**Auto-Trigger V2.0 Recalculation**:
```python
# Added to form import workflow in app.py lines 2134-2200
print(f"Triggering V2.0 True Value recalculation...")
try:
    from calculation_engine_v2 import FormulaEngineV2
    parameters = load_system_parameters()
    engine = FormulaEngineV2(DB_CONFIG, parameters)
    results = engine.calculate_all_players()
    
    # Store results with corrected PPG
    store_v2_calculations(results, parameters, gameweek_num)
```

**PPG Storage Integration**:
```sql
-- Enhanced store_v2_calculations to include PPG (app.py lines 3657-3671)
UPDATE player_metrics 
SET 
    true_value = %s,
    value_score = %s,
    ppg = %s,  -- Added corrected PPG storage
    last_updated = NOW()
WHERE player_id = %s AND gameweek = %s
```

**Complete Workflow (2025-08-26)**:
1. **Understat Sync** → Updates `players.minutes` with current total minutes
2. **Form Upload** → PPG recalculation using correct MAX(points) aggregation
3. **Auto V2.0 Trigger** → V2.0 True Value recalculation with fresh PPG data
4. **PPG Storage** → Store corrected PPG alongside True Value and ROI
5. **Verification** → New `/api/verify-ppg` endpoint for ongoing consistency monitoring

**Testing Requirements:**
- Verify raw data capture during weekly imports (Fantrax, Understat, odds)
- Test trend analysis endpoints with historical gameweek data  
- Confirm V2.0 parameter consistency across trend calculations
- Validate gameweek detection in all time-based functionality

---

## **Core Data Tables**

### **`players`** - Primary Player Data
**Purpose**: Central player registry with V2.0 Enhanced Formula calculations

**Primary Key**: `id` (VARCHAR) - Fantrax player identifier

**Core Player Information**:
- `id` (VARCHAR) - Unique player identifier
- `name` (VARCHAR) - Player name
- `team` (VARCHAR) - Team code (3-letter)
- `position` (VARCHAR) - Playing position
- `minutes` (INTEGER) - Total minutes played
- `price` (DECIMAL 5,2) - Current Fantrax price

**V2.0 Enhanced Formula Columns**:
- `true_value` (DECIMAL 8,2) - **Pure point prediction** (separate from price)
- `roi` (DECIMAL 8,3) - **Return on investment** (true_value ÷ price)
- `blended_ppg` (DECIMAL 5,2) - **✅ NEW: Dynamic blend** of historical/current season PPG using adaptation formula
- `current_season_weight` (DECIMAL 4,3) - **✅ NEW: Blending weight** for current season data (0-1 scale)
- `historical_ppg` (DECIMAL 5,2) - **2024-25 season** calculated PPG baseline
- `exponential_form_score` (DECIMAL 5,3) - **EWMA form multiplier** (α=0.87)
- `baseline_xgi` (DECIMAL 5,3) - **⚠️ REQUIRED** Historical 2024-25 xGI baseline for normalization
- `formula_version` (VARCHAR 10, DEFAULT 'v2.0') - Formula version used

**Expected Goals Data** (Understat integration):
- `xg90` (DECIMAL 5,3) - Expected goals per 90 minutes
- `xa90` (DECIMAL 5,3) - Expected assists per 90 minutes  
- `xgi90` (DECIMAL 5,3) - Expected goals involvement per 90 minutes

**Description**: Contains all player data for V2.0 Enhanced Formula calculations with separated True Value and ROI metrics.

**⚠️ Name Matching Integration**: 
- All player imports utilize the UnifiedNameMatcher system
- Players with <85% confidence are flagged for manual verification
- Recent testing: 98.0% match rate (298/304 players matched automatically)
- Unmatched players stored in `/temp/understat_unmatched.json` for validation UI

### **`player_metrics`** - Weekly Performance Data
**Purpose**: Gameweek-by-gameweek player performance tracking with V2.0 multipliers

**Primary Key**: `(player_id, gameweek)`
**Foreign Key**: `player_id` → `players.id`

**Core Metrics**:
- `player_id` (VARCHAR) - References players.id
- `gameweek` (INTEGER) - Gameweek number
- `price` (DECIMAL) - Fantrax price for that gameweek
- `ppg` (DECIMAL) - Points per game
- `true_value` (DECIMAL) - **V2.0 True Value** calculation result
- `last_updated` (TIMESTAMP) - Last calculation time

**V2.0 Multiplier System**:
- `form_multiplier` (DECIMAL 5,3, DEFAULT 1.0) - EWMA form calculation
- `fixture_multiplier` (DECIMAL 5,3, DEFAULT 1.0) - Exponential fixture difficulty
- `starter_multiplier` (DECIMAL 5,3, DEFAULT 1.0) - Rotation penalty
- `xgi_multiplier` (DECIMAL 5,3, DEFAULT 1.0) - Normalized xGI ratio

**Games Tracking** (V2.0 Dynamic Blending):
- `total_points` (DECIMAL 8,2, DEFAULT 0) - Current season total points
- `games_played` (INTEGER, DEFAULT 0) - Current season games
- `total_points_historical` (DECIMAL 8,2, DEFAULT 0) - 2024-25 season total
- `games_played_historical` (INTEGER, DEFAULT 0) - 2024-25 season games
- `data_source` (VARCHAR 20, DEFAULT 'current') - Primary data source

**Computed Fields** (calculated in queries):
- `games_total` - Sum of `games_played + games_played_historical` for sorting

### **`player_games_data`** - Detailed Games Tracking
**Purpose**: Separate table for comprehensive games and points tracking across seasons

**Primary Key**: `(player_id, gameweek)`
**Owner**: `fantrax_user`

**Columns**:
- `player_id` (VARCHAR 50, NOT NULL) - Player identifier
- `gameweek` (INTEGER, NOT NULL) - Gameweek number  
- `total_points` (DECIMAL 8,2, DEFAULT 0) - Current season running total
- `games_played` (INTEGER, DEFAULT 0) - Current season games count
- `total_points_historical` (DECIMAL 8,2, DEFAULT 0) - 2024-25 season total
- `games_played_historical` (INTEGER, DEFAULT 0) - 2024-25 season games
- `data_source` (VARCHAR 20, DEFAULT 'current') - Data source identifier
- `last_updated` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) - Update timestamp

**Performance Indexes**:
- `idx_player_games_player_id` - Player lookup
- `idx_player_games_gameweek` - Gameweek filtering
- `idx_player_games_data_source` - Source filtering
- `idx_player_games_historical` - Historical data queries

### **`player_form`** - Historical Form Data
**Purpose**: Point-by-point form history for EWMA calculations

**Primary Key**: `(player_id, gameweek)`
**Unique Constraint**: `(player_id, gameweek)`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `player_id` (VARCHAR 10) - References players.id
- `gameweek` (INTEGER, NOT NULL) - Gameweek number
- `points` (DECIMAL 5,2, NOT NULL) - Points scored that gameweek
- `timestamp` (TIMESTAMP, DEFAULT NOW()) - Data timestamp

**Purpose**: Provides historical point data for exponential weighted moving average (EWMA) form calculations with α=0.87 parameter.

---

## **Fixture & Team Data**

### **`team_fixtures`** - Fixture Difficulty System
**Purpose**: Odds-based fixture difficulty calculations for V2.0 exponential multipliers

**Primary Key**: `id` (SERIAL)
**Unique Constraint**: `(team_code, gameweek)`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `team_code` (VARCHAR 3, NOT NULL) - Team identifier
- `gameweek` (INTEGER, NOT NULL) - Gameweek number
- `opponent_code` (VARCHAR 3, NOT NULL) - Opponent team code
- `is_home` (BOOLEAN, NOT NULL) - Home/away indicator
- `difficulty_score` (DECIMAL 5,2, NOT NULL) - **Calculated difficulty** (-10 to +10 scale)
- `created_at` (TIMESTAMP, DEFAULT NOW()) - Creation timestamp

**V2.0 Integration**: Used for exponential fixture multipliers with formula `base^(-difficulty_score)` where base=1.05.

### **`fixture_odds`** - Raw Betting Odds Data
**Purpose**: Source data for fixture difficulty calculations

**Primary Key**: `id` (SERIAL)
**Unique Constraint**: `(gameweek, home_team, away_team)`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `gameweek` (INTEGER, NOT NULL) - Gameweek number
- `home_team` (VARCHAR 3, NOT NULL) - Home team code
- `away_team` (VARCHAR 3, NOT NULL) - Away team code
- `home_odds` (DECIMAL 6,2) - Home win odds
- `draw_odds` (DECIMAL 6,2) - Draw odds
- `away_odds` (DECIMAL 6,2) - Away win odds
- `imported_at` (TIMESTAMP, DEFAULT NOW()) - Import timestamp

---

## **V2.0 Validation & Optimization Tables**

### **`player_predictions`** - Prediction Tracking
**Purpose**: V2.0 formula accuracy validation and backtesting

**Primary Key**: `(player_id, gameweek, model_version)`
**Foreign Key**: `player_id` → `players.id`

**Columns**:
- `player_id` (VARCHAR 50) - References players.id
- `gameweek` (INTEGER) - Gameweek number
- `predicted_value` (DECIMAL 8,2) - **V2.0 True Value prediction**
- `actual_points` (DECIMAL 5,2) - Actual points scored
- `model_version` (VARCHAR 50) - Model version identifier ('v2.0')
- `error_abs` (DECIMAL 8,2) GENERATED - Absolute prediction error |predicted - actual|
- `error_signed` (DECIMAL 8,2) GENERATED - Signed prediction error (predicted - actual)
- `created_at` (TIMESTAMP, DEFAULT NOW()) - Prediction timestamp

### **`validation_results`** - Model Performance Metrics
**Purpose**: Statistical validation of V2.0 formula accuracy

**Primary Key**: `id` (SERIAL)

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `model_version` (VARCHAR 50) - Model version tested ('v2.0')
- `season` (VARCHAR 10) - Season tested ('2025-26')
- `rmse` (DECIMAL 5,3) - Root Mean Square Error
- `mae` (DECIMAL 5,3) - Mean Absolute Error
- `spearman_correlation` (DECIMAL 5,3) - Rank correlation coefficient
- `spearman_p_value` (DECIMAL 6,4) - Statistical significance
- `precision_at_20` (DECIMAL 5,3) - Top 20 prediction precision
- `r_squared` (DECIMAL 5,3) - Coefficient of determination
- `n_predictions` (INTEGER) - Number of predictions in test
- `test_date` (TIMESTAMP, DEFAULT NOW()) - Test execution date
- `parameters` (JSONB) - Model parameters used
- `notes` (TEXT) - Additional test notes

### **`parameter_optimization`** - V2.0 Parameter Tuning
**Purpose**: Track parameter optimization results for V2.0 formula components

**Primary Key**: `id` (SERIAL)

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `test_date` (TIMESTAMP, DEFAULT NOW()) - Test execution date
- `parameters` (JSONB) - Parameter configuration tested
- `rmse` (DECIMAL 5,3) - Resulting RMSE
- `mae` (DECIMAL 5,3) - Resulting MAE
- `spearman_correlation` (DECIMAL 5,3) - Resulting correlation
- `fitness_score` (DECIMAL 6,3) - Combined fitness metric
- `notes` (TEXT) - Optimization notes

---

## **Name Mapping System**

### **`name_mappings`** - External Data Integration
**Purpose**: Cross-platform player name resolution for data imports

**Primary Key**: `id` (SERIAL)
**Unique Constraint**: `(source_system, source_name)`
**Foreign Key**: `fantrax_id` → `players.id`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `source_system` (VARCHAR 50) - External source ('understat', 'ffs', etc.)
- `source_name` (VARCHAR 255) - Original external name
- `fantrax_id` (VARCHAR 50) - Our canonical player ID
- `fantrax_name` (VARCHAR 255) - Current Fantrax name
- `team` (VARCHAR 10) - Team code for validation
- `position` (VARCHAR 10) - Position for validation
- `confidence_score` (FLOAT, DEFAULT 0) - Match confidence 0-100
- `match_type` (VARCHAR 50) - Match type ('exact', 'normalized', 'fuzzy', 'manual')
- `verified` (BOOLEAN, DEFAULT FALSE) - Human verification status
- `verification_date` (TIMESTAMP) - When verified
- `verified_by` (VARCHAR 100) - Who verified
- `last_used` (TIMESTAMP) - Last usage timestamp
- `usage_count` (INTEGER, DEFAULT 0) - Usage frequency
- `notes` (TEXT) - Optional notes
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

**Performance Indexes**:
- `idx_name_mappings_source` - On (source_system, source_name)
- `idx_name_mappings_fantrax` - On fantrax_id
- `idx_name_mappings_verified` - On verified
- `idx_name_mappings_team_pos` - On (team, position)
- `idx_name_mappings_confidence` - On confidence_score DESC

### **`name_mapping_history`** - Change Audit Trail
**Purpose**: Track all changes to name mappings for accountability

**Primary Key**: `id` (SERIAL)
**Foreign Key**: `mapping_id` → `name_mappings.id` (ON DELETE SET NULL)

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `mapping_id` (INTEGER) - References name_mappings.id
- `action` (VARCHAR 50) - Action type ('created', 'verified', 'updated', 'deleted')
- `old_values` (JSONB) - Previous values
- `new_values` (JSONB) - New values
- `user_id` (VARCHAR 100) - User who made change
- `user_ip` (VARCHAR 45) - IP address
- `user_agent` (TEXT) - Browser/client info
- `session_id` (VARCHAR 100) - Session identifier
- `notes` (TEXT) - Optional notes
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

---

## **Database Views & Functions**

### **Views for Data Access**

#### **`verified_name_mappings`**
Pre-filtered view of verified name mappings for production use:
```sql
SELECT source_system, source_name, fantrax_id, fantrax_name, team, position, 
       confidence_score, match_type, verification_date, verified_by, 
       usage_count, last_used, created_at
FROM name_mappings 
WHERE verified = TRUE
ORDER BY source_system, source_name
```

#### **`name_mapping_stats`**
Statistics view for mapping system performance monitoring:
```sql
SELECT source_system, 
       COUNT(*) as total_mappings,
       COUNT(*) FILTER (WHERE verified = TRUE) as verified_mappings,
       COUNT(*) FILTER (WHERE confidence_score >= 95) as high_confidence,
       COUNT(*) FILTER (WHERE confidence_score BETWEEN 85 AND 94) as medium_confidence,
       COUNT(*) FILTER (WHERE confidence_score < 85) as low_confidence,
       AVG(confidence_score) as avg_confidence,
       MAX(usage_count) as max_usage,
       SUM(usage_count) as total_usage
FROM name_mappings 
GROUP BY source_system
ORDER BY total_mappings DESC
```

### **Database Functions**

#### **`update_name_mappings_timestamp()`**
Automatically updates `updated_at` timestamp on name_mappings table modifications.

#### **`log_name_mapping_changes()`**
Automatically logs all changes to name_mappings in the audit history table for accountability.

---

## **V2.0 Data Flow Architecture**

### **Primary Data Pipeline**
1. **Player Registration**: Core player info stored in `players` table with V2.0 columns
2. **Weekly Updates**: Performance data stored in `player_metrics` by gameweek
3. **Games Tracking**: Current/historical data in both `player_metrics` and `player_games_data`
4. **External Integration**: Understat xGI data via `name_mappings` system (99% success rate)
5. **Form Calculation**: Point history in `player_form` for EWMA calculations
6. **Fixture Integration**: Odds-based difficulty in `team_fixtures` for exponential multipliers

### **V2.0 Calculation Dependencies**
**⚠️ CRITICAL: All V2.0 API endpoints MUST include baseline_xgi in queries**

```sql
-- REQUIRED for V2.0 functionality
SELECT p.id, p.name, p.baseline_xgi, p.true_value, p.roi, p.blended_ppg
FROM players p 
WHERE ...
```

**Column Dependencies by Engine**:
- **V2.0 Enhanced Engine**: Writes to `true_value` + `roi`, REQUIRES `baseline_xgi`
- **Dynamic Blending**: Uses `blended_ppg`, `current_season_weight`, `historical_ppg`
- **EWMA Form**: Uses `exponential_form_score` with α=0.87 parameter
- **Normalized xGI**: Uses `baseline_xgi` for ratio calculations with position adjustments

---

## **Recent Data Quality Fixes**

### **Player Data Corrections** (Applied to production database)
- **Leandro Trossard**: Fixed incorrect xGI/minutes data (reset to 0 for clean calculation)
- **Games Played Fix**: Updated 50 players with 0 games but >0 minutes to set games_played=1
- **Name Mappings**: Added Rodrigo Muniz and Rodrigo Gomes with correct team associations
- **Baseline Data**: Cleaned 63 players with corrupted baseline data from Championship/lower leagues

### **Database Performance Optimizations**
- **Fixture Calculation**: Improved 2x speed (90s → 46s) through query optimization
- **Index Strategy**: All tables include appropriate indexes for V2.0 query patterns
- **Data Types**: Optimized DECIMAL precision for calculation accuracy vs storage efficiency

---

## **Key Relationships & Constraints**

### **Foreign Key Relationships**
- `players.id` ← `player_metrics.player_id` (1:many) - Weekly performance data
- `players.id` ← `player_games_data.player_id` (1:many) - Games tracking
- `players.id` ← `name_mappings.fantrax_id` (1:many) - External source mapping
- `players.id` ← `player_form.player_id` (1:many) - Form history
- `players.id` ← `player_predictions.player_id` (1:many) - Validation tracking

### **Data Integrity Constraints**
- **Unique Constraints**: Prevent duplicate gameweek data per player
- **Check Constraints**: Ensure multipliers stay within reasonable ranges
- **Foreign Key Constraints**: Maintain referential integrity across related tables
- **Generated Columns**: Automatic error calculations in validation tables

---

## **V2.0 Performance Metrics**

### **Current System Performance**
- **Total Players**: 647 Premier League players
- **Database Size**: Optimized for efficient queries
- **API Response Time**: Sub-second response times
- **Calculation Speed**: All 647 players recalculated efficiently
- **Name Matching**: 99% success rate for external data integration
- **Data Freshness**: Real-time updates via weekly upload workflows

### **V2.0 Formula Validation**
```
Example Calculations (Validated):
Danny Ballard: True Value = 29.81 = 30.0 × 1.0 × 0.994 × 1.0 × 1.0 ✅
Chris Wood: Blended PPG = 8.8 (6.7% current + 93.3% historical) ✅
Calafiori: xGI Multiplier = 2.500x (capped from 9.64x) ✅
```

---

## **V2.0 Enhanced System Configuration**

### **Starter Prediction System Parameters**

The V2.0 Enhanced Formula includes an advanced starter prediction system with adjustable penalty multipliers and manual override capabilities. Configuration is managed through the `config/system_parameters.json` file.

**Configuration Structure**:
```json
{
  "starter_prediction": {
    "enabled": true,
    "manual_overrides": {},
    "auto_rotation_penalty": 0.75,
    "force_bench_penalty": 0.6,
    "force_out_penalty": 0.0,
    "description": "Starter prediction system with manual overrides and penalty settings"
  }
}
```

**Parameter Details**:
- **`auto_rotation_penalty`** (0.75): Multiplier for players at rotation risk
- **`force_bench_penalty`** (0.6): Multiplier for likely bench players  
- **`force_out_penalty`** (0.0): Multiplier for players definitely out
- **Starter multiplier**: 1.0 (implicit default, no configuration needed)

**Manual Override System**:
The `manual_overrides` object stores player-specific starter status overrides:
```json
{
  "manual_overrides": {
    "player_123": {
      "type": "rotation",
      "applied_gameweek": 8,
      "timestamp": "2025-08-26T10:30:00Z"
    }
  }
}
```

**Override Types**:
- **`starter`**: 1.0x multiplier (guaranteed starter)
- **`rotation`**: Uses `auto_rotation_penalty` value (rotation risk)  
- **`bench`**: Uses `force_bench_penalty` value (likely bench)
- **`out`**: Uses `force_out_penalty` value (definitely out)
- **`auto`**: Removes override, uses CSV prediction data

**Database Storage**:
Starter multipliers are stored in the `player_metrics` table:
```sql
-- Updated during manual overrides and CSV imports
UPDATE player_metrics 
SET starter_multiplier = 0.75 
WHERE player_id = 'player_123' AND gameweek = 8;
```

**V2.0 Enhanced Formula Integration**:
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
```
Where Starter multiplier directly affects the final True Value calculation.

### **Formula Toggle System Parameters**

The V2.0 Enhanced Formula supports individual component toggles for testing and optimization:

**Configuration Structure**:
```json
{
  "formula_optimization_v2": {
    "formula_toggles": {
      "form_enabled": true,
      "fixture_enabled": true, 
      "starter_enabled": true,
      "xgi_enabled": true
    }
  }
}
```

**Toggle Effects**:
- **Disabled components**: Default to 1.0x multiplier (no effect)
- **Enabled components**: Calculate and apply respective multipliers
- **Real-time updates**: Changes trigger immediate V2.0 recalculation

**Database Impact**:
When formula components are toggled off, the calculation engine applies 1.0x multipliers:
```python
# From calculation_engine_v2.py
form_mult = self._calculate_form_multiplier(player_data) if formula_toggles.get('form_enabled', True) else 1.0
starter_mult = player_data.get('starter_multiplier', 1.0) if formula_toggles.get('starter_enabled', True) else 1.0
```

---

## **Maintenance & Monitoring**

### **Database Health Checks**
```sql
-- Verify V2.0 data completeness
SELECT 
    COUNT(*) as total_players,
    COUNT(true_value) as with_true_value,
    COUNT(roi) as with_roi,
    COUNT(blended_ppg) as with_blending,
    COUNT(baseline_xgi) as with_baseline_xgi
FROM players;
-- Expected: 647 players with all V2.0 columns populated
```

### **Performance Monitoring**
```sql
-- Check calculation freshness
SELECT 
    MAX(last_updated) as latest_calculation,
    COUNT(*) as calculated_players
FROM player_metrics
WHERE gameweek = (SELECT MAX(gameweek) FROM player_metrics);
```

### **Data Quality Validation**
```sql
-- Verify multiplier ranges
SELECT 
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE form_multiplier BETWEEN 0.5 AND 2.0) as valid_form,
    COUNT(*) FILTER (WHERE fixture_multiplier BETWEEN 0.5 AND 1.8) as valid_fixture,
    COUNT(*) FILTER (WHERE xgi_multiplier BETWEEN 0.5 AND 2.5) as valid_xgi
FROM player_metrics
WHERE gameweek = (SELECT MAX(gameweek) FROM player_metrics);
```

---

## **Technical Specifications**

### **Database Engine Requirements**
- **PostgreSQL Version**: 12+ recommended
- **Character Set**: UTF8
- **Collation**: English locale support
- **Extensions**: None required (pure SQL implementation)

### **Connection Pooling**
- **Max Connections**: Configured for Flask application load
- **Connection Timeout**: Optimized for web application usage
- **Query Timeout**: Set for complex calculation queries

### **Backup Strategy**
- **Schema Backup**: Regular structure exports
- **Data Backup**: Player data and calculations preserved
- **Point-in-Time Recovery**: Available for data corruption scenarios

---

---

## **🎯 NEW: Dynamic Blending Implementation (2025-08-27)**

### **Enhanced `blended_ppg` and `current_season_weight` Columns**

**Purpose**: Transparent dynamic blending of historical (2024-25) and current season PPG data using configurable adaptation parameter.

**Implementation Details**:
- **`blended_ppg`** (DECIMAL 5,2) - The actual PPG value used in V2.0 True Value calculations
- **`current_season_weight`** (DECIMAL 4,3) - Weight applied to current season data (0-1 scale)
- **Adaptation Formula**: `w_current = min(1, (N-1)/(K-1))` where N=current gameweek, K=adaptation gameweek
- **Configuration**: `full_adaptation_gw: 12` (changed from 16 - faster transition to current season data)

**Database Integration**:
```sql
-- Enhanced API query includes blended PPG data
SELECT 
    p.id, p.name, p.true_value, p.roi,
    p.blended_ppg,           -- ✅ NEW: Dynamic PPG used in calculations
    p.current_season_weight, -- ✅ NEW: Blending transparency
    p.historical_ppg         -- Historical 2024-25 baseline
FROM players p
```

**Example Blending (GW3)**:
- **Current Season Weight**: 18.2% (2 games played, adapts by GW12)
- **Historical Weight**: 81.8% (2024-25 season baseline)
- **Blended PPG**: (0.182 × 15.0) + (0.818 × 11.0) = 11.7 points

**API Response Enhancement**:
```json
{
  "id": "123456",
  "name": "Test Player",
  "true_value": 14.5,
  "roi": 1.21,
  "blended_ppg": 11.7,
  "current_season_weight": 0.182,
  "historical_ppg": 11.0
}
```

**CSV Export Integration**:
The Export CSV feature now includes blended PPG data:
- `blended_ppg` - Dynamic PPG used in True Value calculations
- `current_season_weight` - Transparency into current/historical blend
- `roi` - Return on investment calculation
- `xgi_multiplier` - Normalized xGI impact factor

---

**Last Updated**: 2025-08-27 - Added Dynamic Blending columns and adaptation parameter documentation

*This document reflects the current V2.0-only database structure with enhanced dynamic blending transparency. The database serves 647 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending (GW12 adaptation), EWMA form calculations, and normalized xGI integration. The raw data snapshot system enables retrospective trend analysis by capturing weekly imported data without calculations.*