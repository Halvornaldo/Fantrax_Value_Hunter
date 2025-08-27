# API Reference - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter API Documentation

### **System Status: V2.0 Production API + Enterprise Gameweek Management**

This document describes the complete API for the V2.0 Enhanced Formula system with unified gameweek management. The system has been consolidated to a single V2.0 engine with enterprise-grade gameweek consistency across all functions.

**Base URL**: `http://localhost:5001`  
**Server Status**: V2.0 Enhanced Formula + GameweekManager fully operational  
**Gameweek Management**: 100% unified detection with smart anomaly filtering

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
**Testing Status**: ✅ Verified working - file upload, validation, and unmatched player workflow functional

#### `GET /monitoring`
**Description**: V2.0 system monitoring interface  
**Returns**: HTML monitoring page with performance metrics

---

## **Gameweek Management API - Enterprise Monitoring System**

### **`GET /api/gameweek-status`** - Smart Upload System Status
**Description**: Current gameweek status for intelligent upload suggestions  
**Returns**: JSON with current gameweek, upload guidance, and system status

**Response Example**:
```json
{
  "success": true,
  "current_gameweek": 2,
  "next_gameweek": 3,
  "current_status": {
    "data_completeness": 647,
    "protection_status": "GW1_PROTECTED"
  },
  "system_message": "System currently at GW2. Upload GW2 to update or GW3 for new data."
}
```

**Use Cases**:
- Form upload page pre-fills current gameweek
- Smart validation preventing anomalous uploads
- Upload guidance for users

### **`GET /api/gameweek-consistency`** - Enterprise Health Monitoring ⭐ NEW
**Description**: Comprehensive gameweek consistency monitoring across all tables  
**Returns**: JSON health report with consistency analysis and anomaly detection

**Response Example**:
```json
{
  "timestamp": "2025-08-23T18:00:00.000Z",
  "gameweek_manager_detection": 2,
  "overall_status": "HEALTHY",
  "table_analysis": {
    "player_metrics": {
      "latest_gameweek": 2,
      "latest_record_count": 647,
      "latest_update": "2025-08-23T17:30:00.000Z",
      "gameweek_distribution": [
        {"gameweek": 2, "count": 647},
        {"gameweek": 1, "count": 647}
      ]
    }
  },
  "consistency_issues": [],
  "summary": {
    "total_issues": 0,
    "high_severity": 0,
    "tables_checked": 5,
    "healthy_tables": 5
  }
}
```

**Status Levels**:
- `HEALTHY`: All systems consistent
- `WARNING`: Minor inconsistencies detected
- `CRITICAL`: Major consistency issues requiring attention

**Use Cases**:
- Production monitoring dashboards
- Automated health checks
- Anomaly detection and alerting

---

## **Trend Analysis API - Raw Data Snapshot System**

### **`GET /api/trends/calculate`** - Apply V2.0 Formula to Historical Raw Data
**Description**: Retroactively apply V2.0 Enhanced Formula to raw data snapshots for trend analysis

**Purpose**: Enable "apples-to-apples" analysis by applying consistent formula parameters to different gameweeks using captured raw data without calculations.

**Parameters**:
- `gameweek_start` (int, required): Starting gameweek for analysis (inclusive)
- `gameweek_end` (int, required): Ending gameweek for analysis (inclusive)
- `player_ids` (string, optional): Comma-separated player IDs to analyze
- `parameters` (JSON, optional): V2.0 Enhanced Formula parameters to apply

**Default Parameters Applied**:
```json
{
  "formula_optimization_v2": {
    "exponential_form": {
      "enabled": true,
      "lookback_games": 8,
      "ewma_alpha": 0.87,
      "min_multiplier": 0.5,
      "max_multiplier": 2.0
    },
    "exponential_fixture": {
      "enabled": true,
      "exponential_base": 1.05,
      "position_weights": {"G": 1.10, "D": 1.20, "M": 1.00, "F": 1.05},
      "min_multiplier": 0.5,
      "max_multiplier": 1.8
    },
    "normalized_xgi": {
      "enabled": true,
      "position_adjustments": {"G": 0.5, "D": 0.8, "M": 1.0, "F": 1.2},
      "min_multiplier": 0.5,
      "max_multiplier": 2.5
    },
    "multiplier_caps": {
      "form": 2.0,
      "fixture": 1.8,
      "xgi": 2.5,
      "global": 3.0
    }
  }
}
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

### **`GET /api/trends/raw-data`** - Access Raw Snapshot Data
**Description**: Retrieve raw weekly data without any calculations applied

**Parameters**:
- `gameweek` (int, optional): Specific gameweek to retrieve
- `gameweek_start` (int, optional): Starting gameweek range
- `gameweek_end` (int, optional): Ending gameweek range  
- `player_ids` (string, optional): Comma-separated player IDs
- `data_types` (string, optional): Comma-separated data types ('player', 'fixture', 'form')

**Response Format**:
```json
{
  "raw_data": {
    "player_snapshots": [
      {
        "player_id": "ABC123",
        "gameweek": 1,
        "name": "Mo Salah",
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
        "player_id": "ABC123",
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

**Usage Examples**:
```bash
# Get raw data for GW1
curl "http://localhost:5001/api/trends/raw-data?gameweek=1"

# Get Salah's raw data across multiple gameweeks
curl "http://localhost:5001/api/trends/raw-data?gameweek_start=1&gameweek_end=3&player_ids=ABC123"

# Get only fixture data for analysis
curl "http://localhost:5001/api/trends/raw-data?gameweek=1&data_types=fixture"
```

### **Historical Data Integration Requirements**
**🎯 CRITICAL**: All trend analysis endpoints MUST include historical_ppg calculation for dynamic blending

**Required SQL Pattern for Player Queries**:
```sql
SELECT 
    p.id, p.name, p.team, p.position, p.price,
    -- Historical PPG calculation for dynamic blending
    CASE 
        WHEN COALESCE(pgd.games_played_historical, 0) > 0 
        THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
        ELSE pm.ppg 
    END as historical_ppg,
    -- Other V2.0 calculations...
FROM players p
LEFT JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = %s
LEFT JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = %s
WHERE ...
```

### **Gameweek Detection Integration**
All trend analysis endpoints use database-driven gameweek detection:

**Current Gameweek Detection**:
```sql
SELECT MAX(gameweek) FROM raw_player_snapshots WHERE gameweek IS NOT NULL
```

**Available Gameweeks Query**:
```sql
SELECT DISTINCT gameweek 
FROM raw_player_snapshots 
WHERE gameweek IS NOT NULL 
ORDER BY gameweek
```

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
      "current_season_weight": 0.067,
      "historical_ppg": 8.0,
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
  },
  "gameweek_info": {
    "current_gameweek": 2,
    "detection_method": "GameweekManager",
    "data_source": "unified_detection",
    "emergency_protection_active": true,
    "data_freshness": {
      "gameweek": 2,
      "last_updated": {
        "player_metrics": "2025-08-23T17:30:00.000Z",
        "player_form": "2025-08-23T16:45:00.000Z",
        "raw_snapshots": "2025-08-23T18:00:00.000Z"
      },
      "record_counts": {
        "player_metrics": 647,
        "player_form": 647,
        "raw_snapshots": 647
      },
      "data_completeness": {
        "player_metrics": 100.0,
        "player_form": 100.0,
        "raw_snapshots": 100.0
      }
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
      "full_adaptation_gw": 12
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
**Description**: Get V2.0 Enhanced system configuration (legacy endpoint)

### **`GET /api/system/config`**  
**Description**: Get V2.0 Enhanced system configuration (React dashboard endpoint)  
**Returns**: Configuration object directly (not wrapped in success response)

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
      "full_adaptation_gw": 12
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
**Description**: Update V2.0 Enhanced system parameters (legacy endpoint)  
**Body**: V2.0 configuration object with enhanced parameters  
**Returns**: Success confirmation with updated parameter values

### **`POST /api/system/update-parameters`**
**Description**: Update V2.0 Enhanced system parameters (React dashboard endpoint)  
**Body**: V2.0 configuration object with enhanced parameters and deep merge support  
**Returns**: Success confirmation with updated configuration object

**Request Body Example**:
```json
{
  "formula_optimization_v2": {
    "formula_toggles": {
      "form_enabled": false,
      "fixture_enabled": true,
      "starter_enabled": true,
      "xgi_enabled": true
    },
    "ewma_form": {
      "alpha": 0.87
    },
    "multiplier_caps": {
      "form": 2.0,
      "fixture": 1.8,
      "xgi": 2.5,
      "global": 3.0
    }
  },
  "starter_prediction": {
    "auto_rotation_penalty": 0.75,
    "force_bench_penalty": 0.6,
    "force_out_penalty": 0.0
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "message": "Parameters updated successfully",
  "updated_config": {
    "formula_optimization_v2": {
      "formula_toggles": {
        "form_enabled": false,
        "fixture_enabled": true,
        "starter_enabled": true,
        "xgi_enabled": true
      }
    }
  }
}
```

---

## **Data Import API - V2.0 Enhanced**

### **`POST /api/import-form-data`**
**Description**: Import weekly game data with V2.0 name matching system and rolling minutes-based games detection

**Parameters**:
- `gameweek` (string, required): Gameweek number
- `file` (file, required): CSV file upload

**🎯 NEW: Rolling Minutes-Based Games Detection (2025-08-26)**:
The system now uses intelligent minutes comparison to detect which players actually played:
- **Compares**: Current total minutes (from Understat sync) vs previous gameweek snapshot minutes
- **Logic**: `games_played = 1` if `total_minutes > previous_gameweek_minutes`, otherwise `0`
- **Rolling Pattern**: Uses `gameweek - 1` snapshot for dynamic comparison across all gameweeks
- **Workflow**: Sync Understat data FIRST, then upload CSV for accurate games detection

**Prerequisites**:
1. **Sync Understat Data** - Updates player total minutes before upload
2. **Raw Snapshot Available** - Previous gameweek snapshot must exist for comparison

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
  "override_type": "starter|rotation|bench|out|auto",
  "gameweek": 2
}
```

**Override Types**:
- **`starter`**: 1.0x multiplier (guaranteed starter)
- **`rotation`**: 0.75x multiplier (rotation risk)  
- **`bench`**: 0.6x multiplier (likely bench player)
- **`out`**: 0.0x multiplier (definitely out)
- **`auto`**: Remove override, use CSV prediction data

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
**Testing Status**: ✅ Verified working - 98.0% match rate (298/304 players), unmatched players properly flagged

**V2.0 Enhanced Response**:
```json
{
  "success": true,
  "sync_results": {
    "players_updated": 298,
    "baseline_xgi_updated": 298,
    "match_rate": 98.02631578947368,
    "unmatched_players": 6,
    "total_understat_players": 304
  },
  "name_matching": {
    "exact_matches": 250,
    "fuzzy_matches": 48,
    "needs_manual_review": 6,
    "unmatched_saved_to": "/temp/understat_unmatched.json"
  },
  "v2_integration": {
    "normalized_calculations_ready": true,
    "baseline_data_quality": "excellent",
    "position_adjustments_applied": true
  }
}
```

### **`GET /api/understat/get-unmatched-data`**
**Description**: Retrieve unmatched players for manual verification UI
**Testing Status**: ✅ Verified working - returns structured validation data with original names, suggestions

**Response**:
```json
{
  "status": "success",
  "data": {
    "total_players": 6,
    "unmatched_count": 6,
    "unmatched_details": [
      {
        "original_name": "Tosin Adarabioyo",
        "original_team": "CHE",
        "original_position": "Unknown",
        "needs_review": true,
        "match_result": {
          "confidence": 0,
          "fantrax_name": null,
          "suggested_matches": []
        },
        "original_data": {
          "player_name": "Tosin Adarabioyo",
          "team": "Chelsea",
          "xG90": 0.0,
          "xA90": 0.0
        }
      }
    ],
    "summary": {
      "total": 6,
      "matched": 0,
      "needs_review": 6,
      "match_rate": 0.0
    }
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

**✅ Enhanced Export Columns (2025-08-27)**:
- All standard player data (name, team, position, price)
- `true_value` - V2.0 point predictions  
- `roi` - Return on investment ratios
- `blended_ppg` - **NEW:** Dynamic blending results used in calculations
- `current_season_weight` - **NEW:** Blending transparency (0-1 scale)
- `xgi_multiplier` - **NEW:** Normalized xGI impact factor  
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

### **`GET /api/verify-ppg`** - PPG Calculation Verification ⭐ NEW
**Description**: Diagnostic endpoint to verify PPG calculation consistency between stored and calculated values
**Added**: 2025-08-26 (PPG Calculation Fix)

**Purpose**: Identify discrepancies between stored `player_metrics.ppg` and fresh calculations using `MAX(points)/games_played`

**Response Structure**:
```json
{
  "gameweek": 3,
  "summary": {
    "total_players_checked": 50,
    "players_with_discrepancies": 12,
    "accuracy_rate": 76.0
  },
  "top_discrepancies": [
    {
      "name": "Antoine Semenyo",
      "team": "BOU", 
      "stored_ppg": "25.00",
      "calculated_ppg": "14.0000000000000000",
      "difference": "11.00",
      "total_points": "28.00",
      "games_played": 2,
      "true_value": "25.210",
      "roi": "1.845"
    }
  ],
  "message": "PPG verification completed for gameweek 3"
}
```

**Key Features**:
- **Real-time Verification**: Compares stored vs calculated PPG values
- **Discrepancy Detection**: Identifies players with PPG calculation issues  
- **Summary Statistics**: Shows overall system accuracy rate
- **Production Safe**: Excludes test players (`team != 'TST'`)
- **V2.0 Integration**: Uses same MAX(points) aggregation logic as V2.0 calculations

**Usage Examples**:
```bash
# Check current PPG consistency
curl "http://localhost:5001/api/verify-ppg"

# Use for monitoring system health after form imports
curl "http://localhost:5001/api/verify-ppg" | jq '.summary.accuracy_rate'
```

**Troubleshooting**:
- **High discrepancies**: May indicate form import issues or stale V2.0 calculations
- **0% accuracy rate**: Suggests systematic PPG calculation problems
- **Individual discrepancies**: Can help identify specific players needing attention

### **`GET /api/verify-starter-status`** - Starter System Validation ⭐ NEW
**Description**: Comprehensive starter system health monitoring and validation
**Added**: 2025-08-26 (Starter System Enhancement)

**Purpose**: Validate starter multiplier distribution, identify unusual values, and monitor manual override system health

**Response Structure**:
```json
{
  "success": true,
  "gameweek": 8,
  "health_status": "HEALTHY",
  "issues": [],
  "statistics": {
    "total_players": 647,
    "starters": 340,
    "rotation_risks": 180,
    "bench_players": 85,
    "out_players": 42,
    "missing_data": 0
  },
  "multiplier_distribution": [
    {
      "multiplier": 1.0,
      "count": 340,
      "players": ["Player A", "Player B", "Player C", "..."]
    },
    {
      "multiplier": 0.75,
      "count": 180,
      "players": ["Player D", "Player E", "Player F", "..."]
    },
    {
      "multiplier": 0.6,
      "count": 85,
      "players": ["Player G", "Player H", "..."]
    },
    {
      "multiplier": 0.0,
      "count": 42,
      "players": ["Player I", "Player J", "..."]
    }
  ],
  "unusual_multipliers": [
    {
      "player_name": "Test Player",
      "multiplier": 0.42,
      "team": "TST",
      "position": "M"
    }
  ],
  "validation_timestamp": "2025-08-26T15:30:00.123Z"
}
```

**Health Status Levels**:
- **`HEALTHY`**: All multipliers within standard ranges, minimal missing data
- **`WARNING`**: Non-standard multipliers detected or moderate missing data  
- **`CRITICAL`**: Significant data issues requiring immediate attention

**Standard Multiplier Values**:
- **1.0**: Guaranteed starters
- **0.75**: Rotation risk players (configurable via `auto_rotation_penalty`)
- **0.6**: Likely bench players (configurable via `force_bench_penalty`)
- **0.0**: Players definitely out (configurable via `force_out_penalty`)

**Key Features**:
- **Distribution Analysis**: Shows how many players in each starter category
- **Anomaly Detection**: Identifies non-standard multiplier values
- **Missing Data Monitoring**: Tracks players without starter multiplier data
- **GameweekManager Integration**: Uses unified gameweek detection for consistency

**Usage Examples**:
```bash
# Monitor starter system health
curl "http://localhost:5001/api/verify-starter-status"

# Check for system issues after lineup imports
curl "http://localhost:5001/api/verify-starter-status" | jq '.health_status'

# Review multiplier distribution
curl "http://localhost:5001/api/verify-starter-status" | jq '.multiplier_distribution'
```

**Integration Notes**:
- **Configurable Penalties**: Reads current values from `system_parameters.json`
- **Manual Override Support**: Monitors health of 5-option override system (S/R/B/O/A)
- **V2.0 Formula Impact**: Validates data feeding into True Value calculations

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
- **Transition**: Smooth progression to current-only by GW12 (updated 2025-08-27)

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

---

## **🎯 NEW: Dynamic Blending API Enhancement (2025-08-27)**

### **Enhanced Player Response Format**

**Purpose**: Added transparent dynamic blending fields to all player API endpoints for full visibility into V2.0 Enhanced Formula calculations.

**New Response Fields**:
```json
{
  "blended_ppg": 11.7,
  "current_season_weight": 0.182,
  "historical_ppg": 11.0
}
```

**Integration Notes**:
- **`blended_ppg`**: The actual PPG value used in V2.0 True Value calculations
- **`current_season_weight`**: Shows current season data influence (0-1 scale)
- **`historical_ppg`**: 2024-25 season baseline for comparison
- **Adaptation Parameter**: Changed from GW16 to GW12 for faster transition to current season data

**Export CSV Enhancement**:
The Export CSV endpoint now includes all blending data:
- `blended_ppg`, `current_season_weight`, `roi`, `xgi_multiplier` columns added
- Full transparency into V2.0 Enhanced Formula components
- Fixed endpoint URL from `/api/export/players-csv` to `/api/export`

**Configuration Update**:
All dynamic blending configuration examples updated to reflect GW12 adaptation:
```json
{
  "dynamic_blending": {
    "enabled": true,
    "full_adaptation_gw": 12
  }
}
```

---

**Last Updated**: 2025-08-27 - Dynamic Blending API Enhancement with GW12 adaptation parameter

*This document reflects the current V2.0-only API structure with enhanced dynamic blending transparency. The API serves 647 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending (GW12 adaptation), EWMA form calculations, and normalized xGI integration. The trend analysis system enables retrospective analysis using captured raw data snapshots.*