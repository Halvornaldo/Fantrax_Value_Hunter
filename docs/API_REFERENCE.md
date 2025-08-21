# API Reference

## Base URL
`http://localhost:5000`

## Endpoints

### Dashboard & UI Routes

#### `GET /`
**Description**: Main dashboard page  
**Returns**: HTML dashboard interface

#### `GET /form-upload`
**Description**: Form upload page for CSV data  
**Returns**: HTML form interface

#### `GET /odds-upload`
**Description**: Odds upload page for fixture data  
**Returns**: HTML form interface

#### `GET /import-validation`
**Description**: Import validation page  
**Returns**: HTML validation interface

#### `GET /monitoring`
**Description**: System monitoring page  
**Returns**: HTML monitoring interface

### Player Data API

#### `GET /api/players`
**Description**: Get all players with filtering and sorting  
**Parameters**:
- `position` (string, optional): Filter by position (G, D, M, F)
- `min_price` (float, optional): Minimum price filter
- `max_price` (float, optional): Maximum price filter
- `team` (string, optional): Filter by team code
- `search` (string, optional): Search player names
- `gameweek` (int, optional, default=1): Gameweek data to retrieve
- `limit` (int, optional, default=100): Results per page (50, 100, 200, 1000)
- `offset` (int, optional, default=0): Pagination offset
- `sort_by` (string, optional, default='true_value'): Sort field (games_total supported for numeric Games sorting, roi supported with NULLS LAST handling)
- `sort_direction` (string, optional, default='desc'): Sort direction (asc/desc)

**Returns**: JSON object with pagination info and player array

**Response Format**:
```json
{
  "players": [...],
  "total_count": 647,
  "filtered_count": 50,
  "filters_applied": {...},
  "pagination": {
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

#### `GET /api/players-by-team`
**Description**: Get players for a specific team  
**Parameters**:
- `team` (string, required): Team code

**Returns**: JSON array of player objects for team

#### `GET /api/teams`
**Description**: Get list of all teams  
**Returns**: JSON array of team objects

### Configuration API

#### `GET /api/config`
**Description**: Get current system configuration  
**Returns**: JSON configuration object

#### `POST /api/update-parameters`
**Description**: Update system parameters  
**Body**: JSON configuration object  
**Returns**: Success/error response

### Formula Optimization v2.0 API

#### `POST /api/calculate-values-v2`
**Description**: Calculate player values using Formula Optimization v2.0 (Sprint 1 & 2 features)  
**Sprint 2 Features**: EWMA form calculation, dynamic PPG blending, normalized xGI

**Body**: 
```json
{
  "formula_version": "v2.0|v1.0",
  "gameweek": "number",
  "player_ids": ["array", "optional"]
}
```

**Returns**: 
```json
{
  "success": true,
  "version": "v2.0",
  "players_calculated": 647,
  "sprint_features": {
    "ewma_form": true,
    "dynamic_blending": true,
    "normalized_xgi": true,
    "exponential_fixture": true
  },
  "sample_results": [
    {
      "player_id": "string",
      "name": "Erling Haaland",
      "true_value": 8.68,
      "roi": 1.021,
      "value_score": 1.021,
      "multipliers": {
        "form": 0.952,
        "fixture": 1.006,
        "starter": 1.000,
        "xgi": 0.895
      },
      "sprint2_data": {
        "blended_ppg": 8.45,
        "current_season_weight": 0.125,
        "exponential_form_score": 0.952,
        "normalized_xgi_ratio": 0.895,
        "baseline_xgi": 2.064
      },
      "metadata": {
        "formula_version": "v2.0",
        "caps_applied": {
          "form": false,
          "fixture": false,
          "xgi": false,
          "global": false
        },
        "blending_info": {
          "weight_current": 0.125,
          "weight_historical": 0.875,
          "adaptation_gameweek": 16
        }
      }
    }
  ]
}
```

#### `POST /api/toggle-formula-version`
**Description**: Toggle between v1.0 and v2.0 formulas (admin only)  
**Body**: 
```json
{
  "version": "v2.0|v1.0"
}
```
**Returns**: 
```json
{
  "success": true,
  "new_version": "v2.0",
  "message": "Formula switched to v2.0"
}
```

#### `GET /api/get-formula-version`
**Description**: Get current formula version  
**Returns**: 
```json
{
  "current_version": "v2.0",
  "v2_enabled": true,
  "legacy_support": true
}
```

### Data Import API

#### `POST /api/import-form-data`
**Description**: Import weekly form data from CSV  
**Parameters**:
- `gameweek` (string, required): Gameweek number
- `file` (file, required): CSV file upload

**Returns**: Success/error response with import statistics

#### `POST /api/import-lineups`
**Description**: Import lineup predictions from CSV  
**Body**: JSON with lineup data  
**Returns**: Success/error response

#### `POST /api/import-odds`
**Description**: Import fixture odds data from CSV  
**Parameters**:
- `file` (file, required): CSV file upload

**Returns**: Success/error response

### Data Validation API

#### `POST /api/validate-import`
**Description**: Validate CSV data before import  
**Body**: JSON with CSV data  
**Returns**: Validation results

#### `POST /api/apply-import`
**Description**: Apply validated import data  
**Body**: JSON with validated data  
**Returns**: Import results

### Player Management API

#### `POST /api/manual-override`
**Description**: Set manual starter override for individual players (applies immediately)
**Body**: 
```json
{
  "player_id": "string", 
  "override_type": "starter|bench|out|auto",
  "gameweek": "number"
}
```
**Returns**: 
```json
{
  "success": true,
  "player_name": "string",
  "new_multiplier": "number", 
  "new_true_value": "number"
}
```

#### `POST /api/get-player-suggestions`
**Description**: Get player name suggestions for mapping  
**Body**: JSON with search criteria  
**Returns**: Player suggestions

#### `POST /api/confirm-mapping`
**Description**: Confirm player name mapping  
**Body**: JSON with mapping confirmations  
**Returns**: Success/error response

### Understat Integration API

#### `POST /api/understat/sync`
**Description**: Sync data with Understat  
**Returns**: Sync results

#### `GET /api/understat/unmatched`
**Description**: Get unmatched Understat players  
**Returns**: List of unmatched players

#### `GET /api/understat/stats`
**Description**: Get Understat integration statistics  
**Returns**: Statistics object

#### `POST /api/understat/apply-mappings`
**Description**: Apply Understat player mappings  
**Body**: JSON with mapping data  
**Returns**: Success/error response

### Validation Framework API (Sprint 3)

#### `POST /api/run-validation`
**Description**: Execute validation backtesting against actual fantasy performance  
**Body**: 
```json
{
  "gameweeks": [1, 2, 3],
  "min_minutes": 90,
  "formula_version": "v2.0",
  "validation_type": "temporal|cross_validation"
}
```
**Returns**: 
```json
{
  "success": true,
  "validation_id": "string",
  "metrics": {
    "rmse": 0.305,
    "mae": 0.234,
    "correlation": 0.87,
    "r_squared": 0.76,
    "players_tested": 33
  },
  "limitations": [
    "Single gameweek testing",
    "Potential data leakage risk",
    "Small sample size (33 players)"
  ]
}
```

#### `POST /api/optimize-parameters`
**Description**: Run parameter optimization for multipliers  
**Body**: 
```json
{
  "parameters_to_optimize": ["form_strength", "fixture_strength"],
  "gameweeks": [1, 2, 3],
  "objective": "minimize_rmse"
}
```
**Returns**: Parameter optimization results

#### `POST /api/benchmark-versions`
**Description**: Compare v1.0 vs v2.0 formula performance  
**Body**: 
```json
{
  "gameweeks": [1],
  "min_minutes": 90
}
```
**Returns**: 
```json
{
  "v1_metrics": {
    "rmse": 2.277,
    "players_tested": 74,
    "bias": 1.7
  },
  "v2_metrics": {
    "rmse": 0.305,
    "players_tested": 33,
    "bias": 0.1
  },
  "improvement": "87% RMSE reduction"
}
```

#### `GET /api/validation-history`
**Description**: Get historical validation results  
**Returns**: Array of previous validation runs

#### `GET /api/validation-dashboard`
**Description**: Validation dashboard page  
**Returns**: HTML validation dashboard interface

### Utility API

#### `GET /api/export`
**Description**: Export player data as CSV  
**Parameters**: Same as `/api/players` endpoint  
**Returns**: CSV file download

#### `GET /api/health`
**Description**: Health check endpoint  
**Returns**: System status

#### `GET /api/monitoring/metrics`
**Description**: Get system monitoring metrics  
**Returns**: Metrics data

## Response Formats

### Player Object
```json
{
  "id": "string",
  "name": "string", 
  "team": "string",
  "position": "string",
  "price": "number",
  "ppg": "number",
  "value_score": "number",
  "true_value": "number",
  "roi": "number",
  "form_multiplier": "number",
  "fixture_multiplier": "number", 
  "starter_multiplier": "number",
  "xgi_multiplier": "number",
  "games_played": "number",
  "games_played_historical": "number",
  "games_total": "number",
  "games_display": "string",
  "data_source": "string",
  "xg90": "number",
  "xa90": "number", 
  "xgi90": "number",
  "minutes": "number",
  "last_updated": "timestamp"
}
```

### Configuration Object
```json
{
  "form_calculation": {
    "enabled": "boolean",
    "lookback_period": "number",
    "minimum_games": "number",
    "baseline_switchover_gameweek": "number",
    "form_strength": "number"
  },
  "fixture_difficulty": {
    "enabled": "boolean",
    "multiplier_strength": "number",
    "position_weights": {
      "goalkeeper": "number",
      "defender": "number", 
      "midfielder": "number",
      "forward": "number"
    }
  },
  "starter_prediction": {
    "enabled": "boolean",
    "auto_rotation_penalty": "number",
    "force_bench_penalty": "number"
  },
  "xgi_integration": {
    "enabled": "boolean",
    "multiplier_mode": "string",
    "multiplier_strength": "number"
  },
  "games_display": {
    "baseline_switchover_gameweek": "number",
    "transition_period_end": "number",
    "show_historical_data": "boolean"
  }
}
```

---

**Maintenance Note**: This document must be updated after each Formula Optimization sprint with new endpoints, response formats, and API changes. See `docs/DOCUMENTATION_MAINTENANCE.md` for complete update requirements.

## Sprint 4 Phase 1 Updates (2025-08-21)

### New UI Features
- **ROI Column**: Added to player table with proper NULL handling via `NULLS LAST` sorting
- **Formula Toggle**: Dashboard includes v1.0/v2.0 formula version switching  
- **Validation Status**: Indicators show validation system connectivity (awaiting sufficient data)
- **Visual Indicators**: v2.0 features marked with version badges and conditional CSS styling

### Database Considerations
- **NULL Handling**: ROI column may contain NULL values - API automatically applies `NULLS LAST` clause when sorting by ROI
- **Dual Engine**: v1.0 and v2.0 formulas run in parallel, switchable via toggle without data conflicts
- **Data Requirements**: Validation system requires 5+ gameweeks for meaningful backtesting (currently 2 GWs available)

### Frontend Integration
- **CSS Classes**: Body classes (`v2-enabled`, `v1-enabled`) control conditional styling for formula versions
- **State Management**: Formula toggle affects visual styling but maintains functional consistency
- **Performance**: New features add minimal overhead to existing API response times

*Last updated: 2025-08-21 - Post Sprint 4 Phase 1 completion (Dashboard Integration)*