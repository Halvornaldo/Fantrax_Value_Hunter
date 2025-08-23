# API Reference - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter API Documentation

### **System Status: V2.0 Production API**

This document describes the complete API for the V2.0 Enhanced Formula system. The system has been consolidated to a single V2.0 engine with all legacy components removed.

**Base URL**: `http://localhost:5001`  
**Server Status**: V2.0 Enhanced Formula fully operational

---

## **Core API Endpoints**

### **Dashboard & UI Routes**

#### `GET /`
**Description**: V2.0 Enhanced dashboard interface  
**Returns**: HTML dashboard with V2.0 Enhanced Formula controls
**Features**: True Value/ROI columns, dynamic blending display, exponential controls

#### `GET /form-upload`
**Description**: Weekly game data upload interface  
**Returns**: HTML form for CSV uploads with name validation
**Button Label**: "Upload Weekly Game Data"

#### `GET /odds-upload`
**Description**: Fixture odds upload interface  
**Returns**: HTML form for betting odds CSV imports

#### `GET /import-validation`
**Description**: Data import validation interface  
**Returns**: HTML validation page with 99% match rate system

#### `GET /monitoring`
**Description**: V2.0 system monitoring interface  
**Returns**: HTML monitoring page with performance metrics

---

## **Player Data API - V2.0 Enhanced**

### **`GET /api/players`** - Primary Player Data Endpoint
**Description**: Get all players with V2.0 Enhanced Formula calculations

**Parameters**:
- `position` (string, optional): Filter by position (G, D, M, F)
- `min_price` (float, optional): Minimum price filter
- `max_price` (float, optional): Maximum price filter
- `team` (string, optional): Filter by team code
- `search` (string, optional): Search player names
- `gameweek` (int, optional, default=current): Gameweek data to retrieve
- `limit` (int, optional, default=100): Results per page (50, 100, 200, 1000)
- `offset` (int, optional, default=0): Pagination offset
- `sort_by` (string, optional, default='true_value'): Sort field
  - `true_value` - V2.0 point predictions
  - `roi` - Return on investment (with NULLS LAST)
  - `games_total` - Total games (current + historical)
- `sort_direction` (string, optional, default='desc'): Sort direction (asc/desc)

**V2.0 Response Format**:
```json
{
  "players": [
    {
      "id": "string",
      "name": "Erling Haaland",
      "team": "MCI",
      "position": "F",
      "price": 15.00,
      "true_value": 28.45,
      "roi": 1.896,
      "blended_ppg": 8.45,
      "historical_ppg": 8.0,
      "current_season_weight": 0.067,
      "exponential_form_score": 0.952,
      "baseline_xgi": 2.064,
      "xgi90": 1.845,
      "multipliers": {
        "form": 0.952,
        "fixture": 1.006,
        "starter": 1.000,
        "xgi": 0.895
      },
      "games_played": 1,
      "games_played_historical": 27,
      "games_total": 28,
      "games_display": "27+1",
      "v2_calculation": true,
      "formula_version": "v2.0",
      "last_updated": "2025-08-22T10:30:00Z"
    }
  ],
  "total_count": 647,
  "filtered_count": 100,
  "filters_applied": {
    "position": null,
    "team": null,
    "price_range": null
  },
  "pagination": {
    "limit": 100,
    "offset": 0,
    "has_more": true
  },
  "metadata": {
    "formula_version": "v2.0",
    "calculation_engine": "enhanced",
    "features_active": {
      "dynamic_blending": true,
      "exponential_form": true,
      "normalized_xgi": true,
      "exponential_fixtures": true
    }
  }
}
```

**⚠️ CRITICAL SQL Requirements for V2.0**:
```sql
-- REQUIRED columns for V2.0 functionality
SELECT p.baseline_xgi, p.true_value, p.roi, p.blended_ppg,
       p.current_season_weight, p.exponential_form_score,
       -- Historical PPG calculation for Dynamic Blending
       CASE 
           WHEN COALESCE(pgd.games_played_historical, 0) > 0 
           THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
           ELSE pm.ppg 
       END as historical_ppg
FROM players p
WHERE ...
```

### **`GET /api/players-by-team`**
**Description**: Get V2.0 calculated players for specific team  
**Parameters**:
- `team` (string, required): Team code

**Returns**: JSON array of player objects with V2.0 calculations

### **`GET /api/teams`**
**Description**: Get list of all Premier League teams  
**Returns**: JSON array of 20 team objects

---

## **V2.0 Formula Calculation API**

### **`POST /api/calculate-values-v2`** - V2.0 Enhanced Calculation Engine
**Description**: Execute V2.0 Enhanced Formula calculations with all advanced features

**Request Body**:
```json
{
  "formula_version": "v2.0",
  "gameweek": 2,
  "player_ids": ["optional", "array"],
  "parameters": {
    "dynamic_blending": {
      "enabled": true,
      "full_adaptation_gw": 16
    },
    "exponential_form": {
      "enabled": true,
      "alpha": 0.87
    },
    "normalized_xgi": {
      "enabled": true,
      "enable_xgi": false
    },
    "exponential_fixtures": {
      "enabled": true,
      "base": 1.05
    }
  }
}
```

**V2.0 Response**:
```json
{
  "success": true,
  "formula_version": "v2.0",
  "calculation_engine": "enhanced",
  "players_calculated": 647,
  "features_active": {
    "dynamic_blending": true,
    "exponential_form": true,
    "normalized_xgi": true,
    "exponential_fixtures": true
  },
  "performance_metrics": {
    "calculation_time_ms": 450,
    "database_queries": 8,
    "memory_usage_mb": 125
  },
  "sample_calculations": [
    {
      "player_id": "haaland_e",
      "name": "Erling Haaland",
      "true_value": 28.45,
      "roi": 1.896,
      "blended_ppg": 8.45,
      "multipliers": {
        "form": 0.952,
        "fixture": 1.006,
        "starter": 1.000,
        "xgi": 0.895
      },
      "v2_enhancements": {
        "dynamic_blending": {
          "current_weight": 0.067,
          "historical_weight": 0.933,
          "transition_status": "early_season"
        },
        "exponential_form": {
          "ewma_score": 0.952,
          "alpha_parameter": 0.87,
          "baseline_comparison": 8.45
        },
        "normalized_xgi": {
          "current_ratio": 0.895,
          "baseline_xgi": 2.064,
          "position_adjustment": "none"
        },
        "caps_applied": {
          "form": false,
          "fixture": false,
          "xgi": false,
          "global": false
        }
      }
    }
  ],
  "validation_status": {
    "data_quality": "excellent",
    "missing_baselines": 0,
    "calculation_warnings": []
  }
}
```

### **`POST /api/recalculate`** - Parameter Updates
**Description**: Update V2.0 system parameters and recalculate  
**Body**: JSON configuration with V2.0 parameter structure  
**Returns**: Updated calculations with performance metrics

---

## **Configuration API - V2.0 Enhanced**

### **`GET /api/config`**
**Description**: Get V2.0 Enhanced system configuration

**V2.0 Configuration Response**:
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
  },
  "system_metadata": {
    "formula_version": "v2.0",
    "total_players": 647,
    "current_gameweek": 2,
    "calculation_engine": "enhanced"
  }
}
```

### **`POST /api/update-parameters`**
**Description**: Update V2.0 Enhanced system parameters  
**Body**: V2.0 configuration object with enhanced parameters  
**Returns**: Success confirmation with updated parameter values

---

## **Data Import API - V2.0 Enhanced**

### **`POST /api/import-form-data`**
**Description**: Import weekly game data with V2.0 name matching system

**Parameters**:
- `gameweek` (string, required): Gameweek number
- `file` (file, required): CSV file upload

**V2.0 Enhanced Response**:
```json
{
  "success": true,
  "import_statistics": {
    "total_rows": 300,
    "successful_matches": 297,
    "failed_matches": 3,
    "match_rate": "99%"
  },
  "name_matching": {
    "exact_matches": 250,
    "fuzzy_matches": 47,
    "manual_review_required": 3
  },
  "data_integration": {
    "historical_data_updated": true,
    "blending_weights_recalculated": true,
    "form_scores_updated": true
  }
}
```

### **`POST /api/import-odds`**
**Description**: Import fixture odds for V2.0 exponential difficulty calculation  
**Returns**: Import results with exponential multiplier updates

### **`POST /api/import-lineups`**
**Description**: Import lineup predictions for starter multipliers  
**Returns**: Lineup processing results with starter penalty applications

---

## **Player Management API - V2.0 Enhanced**

### **`POST /api/manual-override`**
**Description**: Real-time manual overrides with V2.0 instant recalculation

**Request Body**:
```json
{
  "player_id": "haaland_e", 
  "override_type": "starter|bench|out|auto",
  "gameweek": 2
}
```

**V2.0 Response**:
```json
{
  "success": true,
  "player_name": "Erling Haaland",
  "override_applied": "starter",
  "updated_calculations": {
    "old_starter_multiplier": 0.8,
    "new_starter_multiplier": 1.0,
    "old_true_value": 22.76,
    "new_true_value": 28.45,
    "impact": "+25% True Value increase"
  },
  "v2_recalculation": true,
  "calculation_time_ms": 45
}
```

---

## **Understat Integration API - V2.0 Enhanced**

### **`POST /api/understat/sync`**
**Description**: Sync xGI data for V2.0 normalized calculations

**V2.0 Enhanced Response**:
```json
{
  "success": true,
  "sync_results": {
    "players_updated": 299,
    "baseline_xgi_updated": 299,
    "match_rate": "99%",
    "failed_matches": ["Player Name 1", "Player Name 2"]
  },
  "v2_integration": {
    "normalized_calculations_ready": true,
    "baseline_data_quality": "excellent",
    "position_adjustments_applied": true
  }
}
```

### **`GET /api/understat/stats`**
**Description**: V2.0 xGI integration statistics

**Returns**: Enhanced statistics with baseline quality metrics

---

## **V2.0 Validation Framework API**

### **`POST /api/run-validation`**
**Description**: Execute V2.0 formula validation and backtesting

**Request Body**:
```json
{
  "gameweeks": [1, 2],
  "min_minutes": 90,
  "formula_version": "v2.0",
  "validation_type": "temporal",
  "features_to_test": [
    "dynamic_blending",
    "exponential_form", 
    "normalized_xgi",
    "exponential_fixtures"
  ]
}
```

**V2.0 Validation Response**:
```json
{
  "success": true,
  "validation_id": "v2_validation_20250822_001",
  "formula_version": "v2.0",
  "features_tested": {
    "dynamic_blending": true,
    "exponential_form": true,
    "normalized_xgi": true,
    "exponential_fixtures": true
  },
  "performance_metrics": {
    "rmse": 0.305,
    "mae": 0.234,
    "spearman_correlation": 0.87,
    "r_squared": 0.76,
    "precision_at_20": 0.85
  },
  "test_details": {
    "players_tested": 33,
    "gameweeks_tested": 2,
    "predictions_made": 66,
    "data_completeness": "excellent"
  },
  "v2_specific_metrics": {
    "blending_accuracy": 0.92,
    "form_prediction_accuracy": 0.89,
    "xgi_normalization_quality": 0.94
  }
}
```

### **`GET /api/validation-history`**
**Description**: Historical V2.0 validation results  
**Returns**: Array of V2.0 validation runs with trend analysis

---

## **Utility API - V2.0 Enhanced**

### **`GET /api/export`**
**Description**: Export V2.0 player data as CSV with all enhanced columns

**Enhanced Export Columns**:
- All standard player data
- `true_value` - V2.0 point predictions
- `roi` - Return on investment ratios
- `blended_ppg` - Dynamic blending results
- `exponential_form_score` - EWMA form scores
- `baseline_xgi` - Historical xGI baselines
- V2.0 multiplier breakdown

### **`GET /api/health`**
**Description**: V2.0 Enhanced system health check

**V2.0 Health Response**:
```json
{
  "status": "healthy",
  "formula_version": "v2.0",
  "system_info": {
    "total_players": 647,
    "database_status": "connected",
    "calculation_engine": "enhanced",
    "last_calculation": "2025-08-22T10:30:00Z"
  },
  "v2_features_status": {
    "dynamic_blending": "operational",
    "exponential_form": "operational", 
    "normalized_xgi": "operational",
    "exponential_fixtures": "operational"
  },
  "performance_metrics": {
    "avg_response_time_ms": 250,
    "calculation_success_rate": "100%",
    "memory_usage": "normal"
  }
}
```

---

## **V2.0 Data Structures**

### **Enhanced Player Object - V2.0**
```json
{
  "id": "string",
  "name": "string",
  "team": "string", 
  "position": "string",
  "price": "number",
  "true_value": "number",
  "roi": "number",
  "blended_ppg": "number",
  "historical_ppg": "number",
  "current_season_weight": "number",
  "exponential_form_score": "number",
  "baseline_xgi": "number",
  "xgi90": "number",
  "multipliers": {
    "form": "number",
    "fixture": "number", 
    "starter": "number",
    "xgi": "number"
  },
  "games_played": "number",
  "games_played_historical": "number",
  "games_total": "number",
  "games_display": "string",
  "v2_calculation": true,
  "formula_version": "v2.0",
  "minutes": "number",
  "last_updated": "timestamp",
  "v2_metadata": {
    "caps_applied": {
      "form": "boolean",
      "fixture": "boolean",
      "xgi": "boolean",
      "global": "boolean"
    },
    "blending_info": {
      "weight_current": "number",
      "weight_historical": "number",
      "transition_status": "string"
    }
  }
}
```

### **V2.0 Configuration Object**
```json
{
  "formula_optimization_v2": {
    "exponential_form": {
      "enabled": "boolean",
      "alpha": "number"
    },
    "dynamic_blending": {
      "enabled": "boolean", 
      "full_adaptation_gw": "number"
    },
    "normalized_xgi": {
      "enabled": "boolean",
      "enable_xgi": "boolean"
    },
    "exponential_fixtures": {
      "enabled": "boolean",
      "base": "number"
    }
  },
  "multiplier_caps": {
    "form": "number",
    "fixture": "number",
    "xgi": "number", 
    "global": "number"
  }
}
```

---

## **V2.0 Formula Implementation Details**

### **Core V2.0 Formula**
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Price
```

### **Dynamic Blending System**
- **Formula**: `w_current = min(1, (N-1)/(K-1))`  
- **Early Season (GW2)**: 6.7% current + 93.3% historical
- **Transition**: Smooth progression to current-only by GW16

### **Exponential Form (EWMA)**
- **Algorithm**: Exponential Weighted Moving Average
- **Alpha Parameter**: 0.87 (configurable)
- **Baseline**: Compared to blended PPG

### **Normalized xGI System**
- **Calculation**: `current_xgi90 ÷ baseline_xgi`
- **Position Adjustments**: Defenders 30% reduced impact
- **Toggle Control**: User can enable/disable

### **Exponential Fixtures**
- **Formula**: `multiplier = base^(-difficulty_score)`
- **Base**: 1.05 (configurable)
- **Position Adjustments**: Defenders +20% impact

---

## **Error Handling - V2.0 Enhanced**

### **Standard Error Response**
```json
{
  "success": false,
  "error": "error_code",
  "message": "Human readable error message",
  "formula_version": "v2.0",
  "context": {
    "endpoint": "/api/calculate-values-v2",
    "timestamp": "2025-08-22T10:30:00Z",
    "request_id": "req_12345"
  },
  "v2_specific": {
    "missing_baselines": ["player_id_1", "player_id_2"],
    "calculation_warnings": [],
    "feature_status": {
      "dynamic_blending": "operational",
      "exponential_form": "operational"
    }
  }
}
```

### **Common V2.0 Error Codes**
- `missing_baseline_xgi` - Required baseline_xgi data missing
- `invalid_v2_parameters` - V2.0 parameter validation failed
- `calculation_engine_error` - V2.0 engine processing error
- `insufficient_data` - Not enough data for V2.0 calculations

---

## **Performance Specifications - V2.0**

### **Response Time Targets**
- **Player Data API**: < 500ms for 647 players
- **V2.0 Calculations**: < 1000ms for full recalculation  
- **Parameter Updates**: < 300ms for configuration changes
- **Data Import**: < 5000ms for 300 player CSV

### **Scalability Metrics**
- **Concurrent Users**: 10+ simultaneous dashboard users
- **Database Performance**: Sub-second query response
- **Memory Usage**: < 200MB peak during calculations
- **Calculation Throughput**: 647 players/second

---

**Last Updated**: 2025-08-22 - V2.0 Enhanced Formula API Complete

*This document reflects the current V2.0-only API structure with all legacy endpoints removed. The API serves 647 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form calculations, and normalized xGI integration.*