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
- `sort_by` (string, optional, default='true_value'): Sort field (games_total supported for numeric Games sorting)
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