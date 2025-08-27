# V2.0 Enhanced Formula Guide
## Fantasy Football Value Hunter - Complete Formula Documentation

### **System Status: V2.0 Production System**

The Fantasy Football Value Hunter uses a research-based V2.0 Enhanced Formula system that separates point prediction from value assessment for more accurate analysis.

**Core Architecture:**
- **Engine**: `calculation_engine_v2.py` (FormulaEngineV2 class)
- **Players**: 647 Premier League players
- **Performance**: Sub-second calculations, <500ms API response
- **Database**: PostgreSQL with V2.0 schema integration

---

## **Core V2.0 Formula**

### **Separated Prediction Model**
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Player_Price
```

**Key Innovation**: True Value predicts points independently, then ROI assesses value efficiency separately.

---

## **V2.0 Component Calculations**

### **1. Dynamic Blending System**
**Purpose**: Smooth transition from historical (2024-25) to current season data

**Formula**: 
- `w_current = min(1, (N-1)/(K-1))` where N=current gameweek, K=12
- `Blended_PPG = (w_current × Current_PPG) + (w_historical × Historical_PPG)`

**Examples**:
- GW2: 9.1% current + 90.9% historical
- GW7: 54.5% current + 45.5% historical  
- GW12: 100% current

**Display Format**: "38+2" (historical+current games)

### **2. EWMA Form Calculation**
**Purpose**: Responsive form tracking using Exponential Weighted Moving Average

**Algorithm**:
- Recent 5 games weighted exponentially: α^0, α^1, α^2, α^3, α^4
- Alpha (α) = 0.87 (5-game half-life)
- Normalized against dynamic baseline: `form_score ÷ blended_ppg`
- **Range**: 0.5x - 2.0x (enhanced from legacy 0.5x-1.5x)

**Implementation**: `calculation_engine_v2.py:_calculate_exponential_form_multiplier`

### **3. Exponential Fixture Difficulty**
**Purpose**: Advanced difficulty scaling using exponential transformation

**Formula**: `multiplier = base^(-difficulty_score × position_weight)`
- **Base**: 1.05 (configurable 1.02-1.10)
- **Position Weights**: G=1.1, D=1.2, M=1.0, F=1.05
- **Range**: 0.5x - 1.8x

**Examples**:
- Easy fixture (-8.0): 1.05^8.0 = 1.477x
- Hard fixture (+6.0): 1.05^(-6.0) = 0.746x
- Neutral (0.0): 1.000x

### **4. Normalized xGI Integration**
**Purpose**: Expected Goals Involvement using ratio-based comparisons

**Calculation**: `current_xgi90 ÷ baseline_xgi`
- **Baseline Source**: 2024-25 season averages (335 players have data)
- **Position Logic**: 
  - Goalkeepers: xGI disabled (1.0x)
  - Defenders: 30% reduced impact for low baselines
  - Midfielders/Forwards: Full impact
- **Range**: 0.5x - 2.5x

**Toggle**: User-controllable via `xgi_integration.enabled`

### **5. Starter Prediction System**
**Purpose**: Starting likelihood with manual override support

**Automatic Multipliers**:
- Starter: 1.0x
- Rotation: 0.9x
- Bench: 0.6x
- Out: 0.0x

**Manual Overrides**: Real-time dashboard controls (S/B/O/A) with instant recalculation

---

## **Multiplier Cap System**

**Enhanced V2.0 Caps**:
- **Form**: 0.5 - 2.0x
- **Fixture**: 0.5 - 1.8x
- **xGI**: 0.5 - 2.5x
- **Global**: 3.0x maximum (total product)

**Implementation**: Individual caps applied first, then global scaling if total exceeds 3.0x

---

## **System Configuration**

### **System Parameters** (`config/system_parameters.json`)

```json
{
  "xgi_integration": {
    "enabled": true,
    "description": "xGI integration toggle and statistics"
  },
  "starter_prediction": {
    "enabled": true,
    "manual_overrides": {}
  },
  "formula_optimization_v2": {
    "exponential_form": {
      "alpha": 0.87
    },
    "dynamic_blending": {
      "enabled": true,
      "full_adaptation_gw": 12
    },
    "normalized_xgi": {
      "enabled": true
    },
    "exponential_fixture": {
      "base": 1.05,
      "position_weights": {
        "G": 1.1, "D": 1.2, "M": 1.0, "F": 1.05
      }
    },
    "multiplier_caps": {
      "enabled": true,
      "form": 2.0,
      "fixture": 1.8,
      "xgi": 2.5,
      "global": 3.0
    }
  }
}
```

---

## **Database Schema (V2.0 Columns)**

```sql
-- Core V2.0 calculations
true_value DECIMAL(8,2)           -- Pure point prediction
roi DECIMAL(8,3)                  -- Return on investment

-- Enhanced data support
blended_ppg DECIMAL(5,2)          -- Dynamic blending result
current_season_weight DECIMAL(4,3) -- Blending weight
baseline_xgi DECIMAL(5,3)         -- Historical xGI baseline
historical_ppg DECIMAL(5,2)       -- Historical season PPG

-- Metadata
v2_calculation BOOLEAN            -- V2.0 calculation flag
last_updated TIMESTAMP            -- Calculation timestamp
```

---

## **API Integration**

### **Primary Endpoints**
- **`/api/players`** - V2.0 player data with calculations
- **`/api/config`** - System parameters
- **`/api/update-parameters`** - Real-time parameter updates
- **`/api/calculate-values-v2`** - V2.0 calculation engine

### **Response Structure**
```json
{
  "player_id": "061vq",
  "name": "Erling Haaland",
  "true_value": 36.32,
  "roi": 0.891,
  "blended_ppg": 12.11,
  "current_season_weight": 0.067,
  "v2_calculation": true,
  "multipliers": {
    "form": 1.57,
    "fixture": 1.038,
    "starter": 1.0,
    "xgi": 2.288
  },
  "metadata": {
    "formula_version": "2.0",
    "gameweek": 2
  }
}
```

---

## **Complete Calculation Example**

**Player**: Erling Haaland (GW2)
**Price**: £22.12

**V2.0 Calculation**:
1. **Dynamic Blending**:
   - Current PPG: 19.0, Historical PPG: 11.61
   - Weight: 9.1% current + 90.9% historical
   - Blended PPG: 12.11

2. **EWMA Form** (α=0.87):
   - Recent games weighted exponentially
   - Form Multiplier: 1.57x

3. **Exponential Fixture**:
   - Difficulty: -7.2 (easy fixture)
   - Position weight: 1.05 (Forward)
   - Fixture Multiplier: 1.038x

4. **Starter Prediction**: 1.0x (predicted starter)

5. **Normalized xGI**:
   - Current xGI90: 2.064, Baseline: 0.902
   - xGI Multiplier: 2.288x

**Final Result**:
- **True Value**: 12.11 × 1.57 × 1.038 × 1.0 × 2.288 = **36.32**
- **ROI**: 36.32 ÷ 22.12 = **0.891**

---

## **Development History**

### **Evolution from V1.0 to V2.0**
The system evolved through research-driven sprint development:

**Sprint 1 (Foundation)**: Fixed core formula by separating True Value from price, added exponential fixture calculation and multiplier caps.

**Sprint 2 (Advanced Features)**: Implemented EWMA form tracking, dynamic blending system, and normalized xGI integration.

**System Consolidation**: Removed legacy V1.0 engine, achieving single V2.0-only architecture for production deployment.

### **Research Foundation**
V2.0 improvements based on comprehensive analysis in `calculation-research/Fantasy Football Model Analysis & Optimization.md`:
- Validated multiplicative approach
- Identified exponential decay benefits
- Confirmed need for prediction/value separation

---

## **Dashboard Integration**

### **Enhanced Features**
- **Real-time Controls**: Parameter updates with instant recalculation
- **Visual Indicators**: True Value and ROI highlighted columns
- **Professional Tooltips**: Detailed explanations for all components
- **xGI Toggle**: User-controllable integration enable/disable
- **Manual Overrides**: Starter prediction controls with visual feedback

### **Performance Monitoring**
- **Calculation Status**: Real-time progress tracking
- **Parameter Updates**: <300ms configuration changes
- **Full Recalculation**: <1 second for 647 players

---

## **System Maintenance**

### **Regular Monitoring**
```bash
# Health check
curl http://localhost:5001/api/health

# Verify V2.0 calculations
curl "http://localhost:5001/api/players?limit=1" | grep v2_calculation

# Parameter validation
curl http://localhost:5001/api/config
```

### **Data Quality Metrics**
- **Name Matching**: 96.95% accuracy across data sources
- **xGI Coverage**: 335/647 players with baseline data
- **Form Coverage**: 100% with graceful fallbacks
- **Calculation Reliability**: Robust error handling and validation

### **Performance Specifications**
- **Response Time**: <500ms for player data endpoint
- **Memory Usage**: <200MB peak during calculations  
- **Database Load**: Optimized queries with proper indexing
- **Concurrent Users**: Tested for multiple simultaneous requests

---

## **Future Enhancements**

### **Planned Improvements**
- **Team Style Multiplier**: PPDA and tactical metrics integration
- **Position-Specific Models**: Specialized calculations for each position
- **Advanced Analytics**: Season-long projections and trend analysis
- **Automated Optimization**: Parameter tuning using backtesting

### **Research Integration**
- **Validation Framework**: RMSE/MAE tracking for accuracy monitoring
- **A/B Testing**: Parameter optimization through systematic testing
- **External Data**: Enhanced data source integration capabilities

---

**Last Updated**: 2025-08-23 - V2.0 Enhanced Formula Production System

*This guide documents the complete V2.0 Enhanced Formula system serving 647 Premier League players with advanced mathematical calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form tracking, and normalized xGI integration.*