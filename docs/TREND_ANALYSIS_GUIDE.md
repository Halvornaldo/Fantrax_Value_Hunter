# Trend Analysis System Guide - Raw Data Snapshot Tool
## Fantasy Football Value Hunter Trend Analysis Documentation

### **System Status: Production Ready**

This document provides comprehensive documentation for the Raw Data Snapshot System and Trend Analysis Tool, enabling retrospective "apples-to-apples" analysis throughout the fantasy football season.

**Version**: 1.0  
**Last Updated**: 2025-08-23  
**System**: V2.0 Enhanced Formula with Current Season Analytics

---

## **Overview**

The Trend Analysis System captures weekly raw imported data without calculations, enabling consistent parameter application across different gameweeks for unbiased performance analysis.

### **Key Benefits**

**Retrospective Analysis**: Apply current V2.0 Enhanced Formula parameters to past gameweeks for trend comparison

**Formula Testing**: Test different parameter sets against historical raw data to validate effectiveness

**Season-Long Tracking**: Monitor player performance trends using consistent calculation methods

**Data Integrity**: Raw data capture without calculations ensures unbiased analysis

**Current Season Focus**: Uses current-season-only baselines for immediate data availability

---

## **Raw Data Snapshot System**

### **Automatic Data Capture**

The system automatically captures raw data during standard weekly workflows:

1. **Fantrax Upload** → Captures player prices, FPts, team assignments → `raw_player_snapshots`
2. **Understat Sync** → Captures xG/xA stats, minutes played → `raw_player_snapshots`  
3. **FFS Lineup Import** → Captures starting predictions, rotation risk → `raw_player_snapshots`
4. **Odds CSV Import** → Captures fixture difficulty, home/away status → `raw_fixture_snapshots`
5. **Form Processing** → Captures weekly points, games played → `raw_form_snapshots`

### **Data Types Captured**

**Player Performance Data**:
- Prices, FPts, minutes played
- xG90, xA90, xGI90 stats
- Historical baseline data (2024-25)
- Team assignments and position data

**Fixture Context Data**:
- Opponent team codes
- Home/away indicators  
- Calculated difficulty scores (-10 to +10 scale)
- Raw betting odds (home/draw/away)

**Form Progression Data**:
- Weekly points scored
- Games played (0 or 1)
- Running season totals and PPG
- Historical data for comparisons

**Starting Status Data**:
- Predicted starter status (true/false)
- Rotation risk levels (low/medium/high/benched)
- FFS prediction confidence

---

## **Database Schema**

### **`raw_player_snapshots`**
**Purpose**: Weekly player performance data without calculations

**Primary Key**: `(player_id, gameweek)`

**Key Columns**:
```sql
player_id VARCHAR(10) NOT NULL     -- Player identifier
gameweek INTEGER NOT NULL          -- Gameweek number  
name VARCHAR(255)                  -- Player name
team VARCHAR(3)                    -- Team code
position VARCHAR(10)               -- Playing position
price DECIMAL(5,2)                 -- Fantrax price
fpts DECIMAL(6,2)                  -- Points scored
minutes_played INTEGER DEFAULT 0   -- Minutes played
xg90 DECIMAL(5,3)                  -- Expected goals per 90
xa90 DECIMAL(5,3)                  -- Expected assists per 90
xgi90 DECIMAL(5,3)                 -- Expected goals involvement per 90
baseline_xgi DECIMAL(5,3)          -- 2024-25 baseline for normalization
opponent VARCHAR(3)                -- Opponent team code
is_home BOOLEAN                    -- Home/away indicator
fixture_difficulty DECIMAL(5,2)    -- Calculated difficulty score
is_predicted_starter BOOLEAN       -- Starting prediction
rotation_risk VARCHAR(10)          -- Risk level assessment
```

### **`raw_fixture_snapshots`**
**Purpose**: Weekly fixture difficulty and betting odds

**Primary Key**: `(team_code, gameweek)`

**Key Columns**:
```sql
team_code VARCHAR(3) NOT NULL      -- Team identifier
gameweek INTEGER NOT NULL          -- Gameweek number
opponent_code VARCHAR(3) NOT NULL  -- Opponent team
is_home BOOLEAN NOT NULL           -- Home/away indicator
difficulty_score DECIMAL(5,2)      -- Calculated difficulty
home_odds DECIMAL(6,2)             -- Home win odds
draw_odds DECIMAL(6,2)             -- Draw odds  
away_odds DECIMAL(6,2)             -- Away win odds
```

### **`raw_form_snapshots`**
**Purpose**: Weekly form tracking for EWMA calculations

**Primary Key**: `(player_id, gameweek)`

**Key Columns**:
```sql
player_id VARCHAR(10) NOT NULL     -- Player identifier
gameweek INTEGER NOT NULL          -- Gameweek number
points_scored DECIMAL(5,2) NOT NULL -- Points that gameweek
games_played INTEGER NOT NULL      -- Games played (0 or 1)
total_points_season DECIMAL(8,2)   -- Running season total
total_games_season INTEGER         -- Running season games
ppg_season DECIMAL(5,2)            -- Running season PPG
```

---

## **API Endpoints**

### **`GET /api/trends/calculate`**
**Description**: Apply V2.0 Enhanced Formula to raw data snapshots

**Parameters**:
- `gameweek_start` (int, required): Starting gameweek (inclusive)
- `gameweek_end` (int, required): Ending gameweek (inclusive)  
- `player_ids` (string, optional): Comma-separated player IDs
- `parameters` (JSON, optional): V2.0 Enhanced Formula parameters

**Usage Examples**:
```bash
# Analyze GW1-2 with default parameters
curl "http://localhost:5001/api/trends/calculate?gameweek_start=1&gameweek_end=2"

# Analyze specific players with custom parameters
curl -X GET "http://localhost:5001/api/trends/calculate" \
  -G -d "gameweek_start=1" \
  -d "gameweek_end=1" \
  -d "player_ids=ABC123,DEF456" \
  --data-urlencode 'parameters={"formula_optimization_v2":{"exponential_form":{"enabled":true,"ewma_alpha":0.9}}}'

# Test different EWMA alpha values
curl -X GET "http://localhost:5001/api/trends/calculate" \
  -G -d "gameweek_start=1" \
  -d "gameweek_end=1" \
  --data-urlencode 'parameters={"formula_optimization_v2":{"exponential_form":{"ewma_alpha":0.75}}}'
```

**Response Format**:
```json
{
  "trend_analysis": [
    {
      "player_id": "ABC123",
      "name": "Mo Salah", 
      "team": "LIV",
      "position": "M",
      "gameweek": 1,
      "price": 12.50,
      "fpts": 18.0,
      "season_ppg": 6.0,
      "current_season_weight": 1.0,
      "form_multiplier": 1.0,
      "fixture_multiplier": 1.05,
      "starter_multiplier": 1.0,
      "xgi_multiplier": 1.2,
      "true_value": 7.56,
      "roi": 0.605,
      "value_score": 0.605,
      "calculation_timestamp": "2025-08-23T14:30:00Z",
      "parameters_used": "current_season_only"
    }
  ],
  "metadata": {
    "gameweeks_analyzed": [1, 2],
    "total_data_points": 1244,
    "calculation_method": "current_season_baselines",
    "parameters_applied": "v2.0_enhanced_default", 
    "analysis_timestamp": "2025-08-23T14:30:00Z"
  }
}
```

### **`GET /api/trends/raw-data`**
**Description**: Access raw snapshot data without calculations

**Parameters**:
- `gameweek` (int, optional): Specific gameweek
- `gameweek_start` (int, optional): Starting gameweek range
- `gameweek_end` (int, optional): Ending gameweek range
- `player_ids` (string, optional): Comma-separated player IDs
- `data_types` (string, optional): Comma-separated types ('player', 'fixture', 'form')

**Usage Examples**:
```bash
# Get all raw data for GW1
curl "http://localhost:5001/api/trends/raw-data?gameweek=1"

# Get Salah's data across multiple gameweeks
curl "http://localhost:5001/api/trends/raw-data?gameweek_start=1&gameweek_end=3&player_ids=ABC123"

# Get only fixture data for analysis  
curl "http://localhost:5001/api/trends/raw-data?gameweek=1&data_types=fixture"

# Get form progression data
curl "http://localhost:5001/api/trends/raw-data?gameweek_start=1&gameweek_end=5&data_types=form"
```

---

## **Technical Implementation**

### **SimpleTrendAnalysisEngine**
**File**: `src/trend_analysis_engine_simple.py`

**Purpose**: Current-season-only trend analysis engine optimized for immediate Week 1 data capture

**Key Features**:
- **No Historical Dependencies**: Uses current season baselines only
- **Database-Driven Gameweek Detection**: Eliminates hardcoded values
- **V2.0 Formula Integration**: Consistent with main calculation engine
- **Error Handling**: Graceful fallbacks for missing data

**Core Methods**:
```python
calculate_historical_trends(gameweek_start, gameweek_end, parameters, player_ids)
# Apply V2.0 formula to raw data snapshots

_fetch_raw_data(cursor, gameweek, player_ids)  
# Retrieve raw data for specific gameweek

_calculate_player_values_from_raw(cursor, player_data, current_gw, parameters)
# Calculate V2.0 values using raw data and current-season baselines
```

### **Gameweek Detection Pattern**
**Critical Implementation**: All trend analysis functions use database-driven detection

**✅ Correct Pattern**:
```sql
SELECT MAX(gameweek) FROM raw_player_snapshots WHERE gameweek IS NOT NULL
```

**❌ Incorrect Patterns to Avoid**:
- `gameweek = 1` (hardcoded values)
- Parameter-based gameweek without validation
- Assumptions about current gameweek

### **Current Season Baseline Calculations**

**Season PPG Calculation**:
```python
def _calculate_season_ppg(self, cursor, player_id: str, current_gw: int) -> float:
    cursor.execute("""
        SELECT 
            SUM(points_scored) as total_points,
            SUM(games_played) as total_games
        FROM raw_form_snapshots 
        WHERE player_id = %s AND gameweek <= %s
    """, [player_id, current_gw])
    
    result = cursor.fetchone()
    if result and result['total_games'] and result['total_games'] > 0:
        return float(result['total_points']) / float(result['total_games'])
    else:
        return 6.0  # Default for players with no data yet
```

**EWMA Form Calculation**:
```python
def _calculate_form_multiplier_from_raw(self, cursor, player_id: str, current_gw: int, parameters: Dict) -> float:
    # Get recent form data
    cursor.execute("""
        SELECT points_scored 
        FROM raw_form_snapshots 
        WHERE player_id = %s AND gameweek < %s 
        ORDER BY gameweek DESC 
        LIMIT %s
    """, [player_id, current_gw, lookback_games])
    
    # Calculate EWMA with α=0.87 (default)
    points = [float(row['points_scored']) for row in form_data]
    ewma_score = points[0]  # Most recent game
    for i in range(1, len(points)):
        ewma_score = alpha * ewma_score + (1 - alpha) * points[i]
```

---

## **Usage Scenarios**

### **Parameter Testing**
**Scenario**: Test different EWMA alpha values to find optimal form sensitivity

**Method**:
1. Capture GW1 raw data using standard upload workflow
2. Apply trend analysis with α=0.87 (default) to GW1 data  
3. Apply trend analysis with α=0.75 (more responsive) to same GW1 data
4. Compare True Value predictions against actual GW2 performance
5. Determine which alpha value provides better predictive accuracy

**Example**:
```bash
# Test default alpha (0.87)
curl -G "http://localhost:5001/api/trends/calculate" \
  -d "gameweek_start=1&gameweek_end=1" \
  --data-urlencode 'parameters={"formula_optimization_v2":{"exponential_form":{"ewma_alpha":0.87}}}'

# Test more responsive alpha (0.75)  
curl -G "http://localhost:5001/api/trends/calculate" \
  -d "gameweek_start=1&gameweek_end=1" \
  --data-urlencode 'parameters={"formula_optimization_v2":{"exponential_form":{"ewma_alpha":0.75}}}'
```

### **Player Comparison Analysis**
**Scenario**: Compare two similar players using identical formula settings

**Method**:
1. Identify players for comparison (e.g., two premium midfielders)
2. Extract raw data for both players across multiple gameweeks
3. Apply identical V2.0 parameters to ensure fair comparison
4. Analyze True Value, ROI, and individual multiplier contributions
5. Determine which player offers better value under current conditions

### **Fixture Difficulty Validation**
**Scenario**: Validate exponential fixture calculation accuracy

**Method**:
1. Extract raw fixture data showing betting odds and calculated difficulties
2. Apply trend analysis to players facing different fixture difficulties  
3. Compare predicted performance (True Value) with actual points scored
4. Adjust exponential base parameter (default 1.05) if needed for better accuracy

### **Seasonal Progress Tracking**
**Scenario**: Track how player values evolve as more current season data becomes available

**Method**:
1. Apply trend analysis to GW1 data (100% current season weight)
2. Apply trend analysis to GW5 data (still 100% current season)
3. Compare how True Values change as more performance data accumulates
4. Identify players whose values improve or decline with larger sample sizes

---

## **Data Quality Assurance**

### **Validation Procedures**

**Raw Data Completeness Check**:
```sql
-- Verify GW1 data capture completeness
SELECT 
    COUNT(*) as total_players,
    COUNT(*) FILTER (WHERE fantrax_import = TRUE) as fantrax_captured,
    COUNT(*) FILTER (WHERE understat_import = TRUE) as understat_captured,
    COUNT(*) FILTER (WHERE ffs_import = TRUE) as ffs_captured,
    COUNT(*) FILTER (WHERE odds_import = TRUE) as odds_captured
FROM raw_player_snapshots 
WHERE gameweek = 1;
```

**Fixture Data Integrity Check**:
```sql
-- Verify all teams have fixture data
SELECT 
    COUNT(DISTINCT team_code) as teams_with_fixtures,
    COUNT(*) as total_fixtures
FROM raw_fixture_snapshots 
WHERE gameweek = 1;
-- Expected: 20 teams, 10 fixtures
```

**Form Data Consistency Check**:
```sql
-- Verify form data matches player snapshots
SELECT 
    rps.gameweek,
    COUNT(rps.player_id) as players_with_performance,
    COUNT(rfs.player_id) as players_with_form
FROM raw_player_snapshots rps
LEFT JOIN raw_form_snapshots rfs 
    ON rps.player_id = rfs.player_id AND rps.gameweek = rfs.gameweek
WHERE rps.gameweek = 1
GROUP BY rps.gameweek;
```

### **Error Handling**

**Missing Data Scenarios**:
- **No form data**: Default to 1.0x form multiplier
- **Missing xGI baseline**: Default to 1.0x xGI multiplier  
- **No fixture data**: Default to 1.0x fixture multiplier
- **Missing rotation data**: Assume starter (1.0x starter multiplier)

**Data Type Conversions**:
- All price values converted to float to avoid Decimal/float conflicts
- NULL rotation_risk handled with `(player_data.get('rotation_risk') or '').lower()`
- Division by zero protection in all PPG calculations

---

## **Performance Specifications**

### **System Requirements**
- **Database**: PostgreSQL 12+ with sufficient storage for weekly snapshots
- **Memory**: <100MB for trend analysis calculations  
- **Processing**: <5 seconds for full gameweek analysis (622 players)
- **Storage**: ~1MB per gameweek of raw data (estimated)

### **Scalability Metrics**
- **Current Capacity**: Handles 622 players with complete data capture
- **Response Times**: <3 seconds for single gameweek analysis
- **Concurrent Usage**: Supports multiple simultaneous trend analysis requests
- **Data Growth**: ~38 gameweeks × 1MB = ~40MB additional storage per season

---

## **Future Enhancements**

### **Dashboard Integration** (Planned)
- **Visual Trend Charts**: Player performance tracking with interactive graphs
- **Parameter Comparison Tool**: Side-by-side analysis with different settings
- **Export Functionality**: CSV downloads for external analysis
- **Historical Comparison**: Multi-season trend analysis when data available

### **Advanced Analytics** (Planned)  
- **Regression Analysis**: Statistical validation of formula accuracy
- **Monte Carlo Simulation**: Risk assessment for player selections
- **Machine Learning Integration**: Pattern recognition in player performance
- **Automated Parameter Optimization**: Data-driven parameter tuning

### **Data Sources Integration** (Planned)
- **Weather Data**: Weather impact on player performance
- **Injury Data**: Automatic rotation risk updates
- **Team News**: Real-time lineup prediction improvements
- **Historical Seasons**: Multi-year baseline development when available

---

## **Troubleshooting**

### **Common Issues**

**"No raw data found for gameweek X"**
- **Cause**: Data not captured during weekly upload workflow
- **Solution**: Re-run standard data imports (Fantrax, Understat, FFS, odds)
- **Prevention**: Verify data capture completion after each weekly upload

**"Database connection error in trend analysis"**
- **Cause**: PostgreSQL connection issues or table missing
- **Solution**: Verify database is running and raw snapshot tables exist
- **Check**: `psql -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter`

**"Calculation errors for player X"**
- **Cause**: Missing baseline data or corrupted raw data
- **Solution**: Check `raw_player_snapshots` for data completeness
- **Fallback**: System uses default values (1.0x multipliers) for missing data

**"Gameweek detection returning wrong values"**
- **Cause**: Raw data tables empty or NULL gameweek values
- **Solution**: Verify data capture and check for proper gameweek assignment
- **Debug**: `SELECT DISTINCT gameweek FROM raw_player_snapshots ORDER BY gameweek`

### **Performance Issues**

**Slow trend analysis response times**
- **Check**: Database indexes on `(player_id, gameweek)` columns
- **Optimize**: Add database indexes if missing
- **Monitor**: Use `EXPLAIN ANALYZE` on trend analysis queries

**Memory usage spikes during analysis**
- **Cause**: Large result sets loaded into memory
- **Solution**: Implement pagination for large gameweek ranges
- **Limit**: Use `player_ids` parameter to reduce dataset size

---

## **API Response Examples**

### **Successful Trend Analysis**
```json
{
  "trend_analysis": [
    {
      "player_id": "13045",
      "name": "Mohamed Salah",
      "team": "LIV", 
      "position": "M",
      "gameweek": 1,
      "price": 12.50,
      "fpts": 18.0,
      "season_ppg": 18.0,
      "current_season_weight": 1.0,
      "form_multiplier": 1.0,
      "fixture_multiplier": 1.047,
      "starter_multiplier": 1.0,
      "xgi_multiplier": 1.096,
      "true_value": 20.74,
      "roi": 1.659,
      "value_score": 1.659,
      "calculation_timestamp": "2025-08-23T14:30:00Z",
      "parameters_used": "current_season_only"
    }
  ],
  "metadata": {
    "gameweeks_analyzed": [1],
    "total_data_points": 1,
    "calculation_method": "current_season_baselines",
    "parameters_applied": "v2.0_enhanced_default",
    "analysis_timestamp": "2025-08-23T14:30:00Z"
  }
}
```

### **Raw Data Response**
```json
{
  "raw_data": {
    "player_snapshots": [
      {
        "player_id": "13045",
        "gameweek": 1,
        "name": "Mohamed Salah",
        "team": "LIV",
        "position": "M", 
        "price": 12.50,
        "fpts": 18.0,
        "minutes_played": 90,
        "xg90": 0.45,
        "xa90": 0.12,
        "xgi90": 0.57,
        "baseline_xgi": 0.52,
        "opponent": "IPO",
        "is_home": true,
        "fixture_difficulty": -2.1,
        "is_predicted_starter": true,
        "rotation_risk": "low",
        "created_at": "2025-08-17T12:00:00Z"
      }
    ],
    "fixture_snapshots": [
      {
        "team_code": "LIV",
        "gameweek": 1,
        "opponent_code": "IPO", 
        "is_home": true,
        "difficulty_score": -2.1,
        "home_odds": 1.35,
        "draw_odds": 5.20,
        "away_odds": 8.50,
        "created_at": "2025-08-17T10:00:00Z"
      }
    ],
    "form_snapshots": [
      {
        "player_id": "13045",
        "gameweek": 1,
        "points_scored": 18.0,
        "games_played": 1,
        "total_points_season": 18.0,
        "total_games_season": 1,
        "ppg_season": 18.0,
        "created_at": "2025-08-17T18:00:00Z"
      }
    ]
  },
  "metadata": {
    "gameweeks_included": [1],
    "players_included": 622,
    "data_capture_complete": true,
    "last_updated": "2025-08-17T18:00:00Z"
  }
}
```

### **Error Response**
```json
{
  "success": false,
  "error": "missing_raw_data",
  "message": "No raw data found for specified gameweek range",
  "context": {
    "endpoint": "/api/trends/calculate",
    "gameweek_start": 5,
    "gameweek_end": 5,
    "available_gameweeks": [1, 2],
    "timestamp": "2025-08-23T14:30:00Z"
  },
  "suggestions": [
    "Check available gameweeks using /api/trends/raw-data",
    "Verify data capture completed for requested gameweek",
    "Use gameweeks 1-2 which have captured data"
  ]
}
```

---

**This comprehensive guide provides complete documentation for implementing and using the Raw Data Snapshot System for trend analysis in the Fantasy Football Value Hunter V2.0 Enhanced Formula system.**