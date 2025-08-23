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
- `blended_ppg` (DECIMAL 5,2) - **Dynamic blend** of historical/current PPG
- `current_season_weight` (DECIMAL 4,3) - **Blending weight** for current season data
- `historical_ppg` (DECIMAL 5,2) - **2024-25 season** calculated PPG baseline
- `exponential_form_score` (DECIMAL 5,3) - **EWMA form multiplier** (α=0.87)
- `baseline_xgi` (DECIMAL 5,3) - **⚠️ REQUIRED** Historical 2024-25 xGI baseline for normalization
- `formula_version` (VARCHAR 10, DEFAULT 'v2.0') - Formula version used

**Expected Goals Data** (Understat integration):
- `xg90` (DECIMAL 5,3) - Expected goals per 90 minutes
- `xa90` (DECIMAL 5,3) - Expected assists per 90 minutes  
- `xgi90` (DECIMAL 5,3) - Expected goals involvement per 90 minutes

**Description**: Contains all player data for V2.0 Enhanced Formula calculations with separated True Value and ROI metrics.

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

**Last Updated**: 2025-08-22 - V2.0 Enhanced Formula Database Schema Complete

*This document reflects the current V2.0-only database structure with all legacy components removed. The database serves 647 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form calculations, and normalized xGI integration.*