# Database Schema

## Connection Details

**Database**: `fantrax_value_hunter`  
**Host**: `localhost`  
**Port**: `5433`  
**Username**: `fantrax_user`  
**Password**: `fantrax_password`

## Core Tables

### `players`
Primary player data table
- **Primary Key**: `id` (VARCHAR)
- **Core Columns**: `id`, `name`, `team`, `position`, `minutes`, `xg90`, `xa90`, `xgi90`
- **v2.0 Columns** (added 2025-08-21):
  - `true_value` (DECIMAL 8,2) - True point prediction (separate from price)
  - `roi` (DECIMAL 8,3) - Return on investment (true_value/price)
  - `formula_version` (VARCHAR 10, DEFAULT 'v2.0') - Formula version used
  - `exponential_form_score` (DECIMAL 5,3) - EWMA form calculation
  - `baseline_xgi` (DECIMAL 5,3) - Position-specific xGI baseline
  - `blended_ppg` (DECIMAL 5,2) - Dynamic blend of historical/current PPG
  - `current_season_weight` (DECIMAL 4,3) - Current season data weight
- **Description**: Contains basic player information, xG statistics, and v2.0 formula enhancements

### `player_metrics`
Player performance metrics by gameweek
- **Primary Key**: `(player_id, gameweek)`
- **Foreign Key**: `player_id` → `players.id`

**Core Columns**:
- `player_id` (VARCHAR) - References players.id
- `gameweek` (INTEGER) - Gameweek number
- `price` (DECIMAL) - Current Fantrax price
- `ppg` (DECIMAL) - Points per game
- `value_score` (DECIMAL) - PPG ÷ Price (PP$)
- `true_value` (DECIMAL) - Calculated true value
- `last_updated` (TIMESTAMP)

**Computed Fields** (calculated in queries):
- `games_total` - Sum of games_played + games_played_historical for sorting

**Multiplier Columns**:
- `form_multiplier` (DECIMAL 5,3, DEFAULT 1.0)
- `fixture_multiplier` (DECIMAL 5,3, DEFAULT 1.0)
- `starter_multiplier` (DECIMAL 5,3, DEFAULT 1.0)
- `xgi_multiplier` (DECIMAL 5,3, DEFAULT 1.0)

**Games Tracking Columns** (added via migration):
- `total_points` (DECIMAL 8,2, DEFAULT 0) - Current season total
- `games_played` (INTEGER, DEFAULT 0) - Current season games
- `total_points_historical` (DECIMAL 8,2, DEFAULT 0) - 2024-25 season total
- `games_played_historical` (INTEGER, DEFAULT 0) - 2024-25 season games
- `data_source` (VARCHAR 20, DEFAULT 'current') - Primary data source

### `player_games_data`
Separate table for detailed games tracking (created via create_games_table.py)
- **Primary Key**: `(player_id, gameweek)`
- **Owner**: `fantrax_user`

**Columns**:
- `player_id` (VARCHAR 50, NOT NULL) - Player identifier
- `gameweek` (INTEGER, NOT NULL) - Gameweek number  
- `total_points` (DECIMAL 8,2, DEFAULT 0) - Current season total
- `games_played` (INTEGER, DEFAULT 0) - Current season games
- `total_points_historical` (DECIMAL 8,2, DEFAULT 0) - 2024-25 total
- `games_played_historical` (INTEGER, DEFAULT 0) - 2024-25 games
- `data_source` (VARCHAR 20, DEFAULT 'current') - Data source
- `last_updated` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) - Update time

**Indexes**:
- `idx_player_games_player_id` - On player_id
- `idx_player_games_gameweek` - On gameweek
- `idx_player_games_data_source` - On data_source
- `idx_player_games_historical` - On games_played_historical

### `player_form`
Historical form data for calculations
- **Primary Key**: `(player_id, gameweek)`
- **Unique Constraint**: `(player_id, gameweek)`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `player_id` (VARCHAR 10) - References players.id
- `gameweek` (INTEGER, NOT NULL) - Gameweek number
- `points` (DECIMAL 5,2, NOT NULL) - Points scored that gameweek
- `timestamp` (TIMESTAMP, DEFAULT NOW()) - Data timestamp

### `team_fixtures`
Team fixture difficulty data from betting odds
- **Primary Key**: `id` (SERIAL)
- **Unique Constraint**: `(team_code, gameweek)`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `team_code` (VARCHAR 3, NOT NULL) - Team identifier
- `gameweek` (INTEGER, NOT NULL) - Gameweek number
- `opponent_code` (VARCHAR 3, NOT NULL) - Opponent team code
- `is_home` (BOOLEAN, NOT NULL) - Home/away indicator
- `difficulty_score` (DECIMAL 5,2, NOT NULL) - Calculated difficulty (-10 to +10)
- `created_at` (TIMESTAMP, DEFAULT NOW()) - Creation timestamp

### `fixture_odds`
Raw betting odds data for CSV imports
- **Primary Key**: `id` (SERIAL)
- **Unique Constraint**: `(gameweek, home_team, away_team)`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `gameweek` (INTEGER, NOT NULL) - Gameweek number
- `home_team` (VARCHAR 3, NOT NULL) - Home team code
- `away_team` (VARCHAR 3, NOT NULL) - Away team code
- `home_odds` (DECIMAL 6,2) - Home win odds
- `draw_odds` (DECIMAL 6,2) - Draw odds
- `away_odds` (DECIMAL 6,2) - Away win odds
- `imported_at` (TIMESTAMP, DEFAULT NOW()) - Import timestamp

## v2.0 Formula Optimization Tables

### `player_predictions` 
Validation tracking for formula accuracy (added 2025-08-21)
- **Primary Key**: `(player_id, gameweek)`
- **Foreign Key**: `player_id` → `players.id`

**Columns**:
- `player_id` (VARCHAR 50) - References players.id
- `gameweek` (INTEGER) - Gameweek number
- `predicted_value` (DECIMAL 8,2) - v2.0 true value prediction
- `actual_points` (DECIMAL 5,2) - Actual points scored
- `prediction_error` (DECIMAL 6,2) - Absolute prediction error
- `formula_version` (VARCHAR 10) - Formula version ('v1.0', 'v2.0')
- `created_at` (TIMESTAMP, DEFAULT NOW()) - Prediction timestamp

### `formula_validation_results`
Backtesting and validation metrics (added 2025-08-21)
- **Primary Key**: `id` (SERIAL)

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `test_name` (VARCHAR 100) - Test identifier
- `formula_version` (VARCHAR 10) - Version tested
- `gameweek_range` (VARCHAR 20) - GW range tested
- `sample_size` (INTEGER) - Number of predictions
- `rmse` (DECIMAL 6,3) - Root Mean Square Error
- `mae` (DECIMAL 6,3) - Mean Absolute Error
- `spearman_correlation` (DECIMAL 5,3) - Rank correlation
- `precision_at_20` (DECIMAL 5,3) - Top 20 precision
- `test_date` (TIMESTAMP, DEFAULT NOW()) - Test execution date
- `notes` (TEXT) - Additional test notes

## Name Mapping System

### `name_mappings`
Master table for external data source name mapping
- **Primary Key**: `id` (SERIAL)
- **Unique Constraint**: `(source_system, source_name)`
- **Foreign Key**: `fantrax_id` → `players.id`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `source_system` (VARCHAR 50) - External source ('ffs', 'understat', etc.)
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

**Indexes**:
- `idx_name_mappings_source` - On (source_system, source_name)
- `idx_name_mappings_fantrax` - On fantrax_id
- `idx_name_mappings_verified` - On verified
- `idx_name_mappings_team_pos` - On (team, position)
- `idx_name_mappings_confidence` - On confidence_score DESC

### `name_mapping_history`
Audit trail for name mapping changes
- **Primary Key**: `id` (SERIAL)
- **Foreign Key**: `mapping_id` → `name_mappings.id` (ON DELETE SET NULL)

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

## Database Views

### `verified_name_mappings`
Pre-filtered view of verified name mappings
```sql
SELECT source_system, source_name, fantrax_id, fantrax_name, team, position, 
       confidence_score, match_type, verification_date, verified_by, 
       usage_count, last_used, created_at
FROM name_mappings 
WHERE verified = TRUE
ORDER BY source_system, source_name
```

### `name_mapping_stats`
Statistics view for mapping system performance
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

## Database Functions

### `update_name_mappings_timestamp()`
Automatically updates `updated_at` timestamp on name_mappings updates

### `log_name_mapping_changes()`
Automatically logs all changes to name_mappings in the audit history table

## Data Flow

1. **Player Data**: Core player info stored in `players` table
2. **Weekly Metrics**: Performance data stored in `player_metrics` by gameweek
3. **Games Tracking**: Games played data in both `player_metrics` and `player_games_data`
4. **External Data**: Name mappings handle external data source integration
5. **Form Calculation**: Historical points stored in `player_form` for form multipliers
6. **Fixture Data**: Odds-based difficulty stored in `fixture_difficulty`

## Recent Data Fixes

**Player Data Corrections** (applied to database):
- Fixed Leandro Trossard incorrect xGI/minutes data (set to 0)
- Updated 50 players with 0 games but >0 minutes to set games_played=1
- Added name mappings for Rodrigo Muniz and Rodrigo Gomes (correct team associations)

## Key Relationships

- `players.id` ← `player_metrics.player_id` (1:many)
- `players.id` ← `player_games_data.player_id` (1:many)  
- `players.id` ← `name_mappings.fantrax_id` (1:many)
- `players.id` ← `player_form.player_id` (1:many)

## Performance Indexes

All tables include appropriate indexes for:
- Primary key lookups
- Foreign key relationships  
- Common query patterns (gameweek, team, position)
- Time-based queries (created_at, updated_at)
- Games tracking queries