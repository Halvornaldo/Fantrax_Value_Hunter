# V2.0 Enhanced Formula Guide
## Fantasy Football Value Hunter - Complete Formula Documentation

### **System Status: V2.0 Production System**

The Fantasy Football Value Hunter uses a research-based V2.0 Enhanced Formula system that separates point prediction from value assessment for more accurate analysis.

**Core Architecture:**
- **Engine**: `calculation_engine_v2.py` (FormulaEngineV2 class)
- **Players**: 714 Premier League players
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
n#### **⚠️ CRITICAL: Games Count Data Sources**
The system uses **TWO** different sources for games count:
1. **`players.games_current_season`** - From Understat sync, **ACCURATE** game counts ✅
2. **`player_games_data` (SUM)** - May have incorrect aggregations ⚠️

**ALWAYS use `p.games_current_season` for:**
- PPG calculations in recalculation
- Dynamic blending `games_current` parameter
- Frontend display (25-26 column)
n#### **Enhanced MAX Formula Implementation** ✅ *Updated 2025-09-17*

**For players WITH historical data:**
1. **Weight_A** = `games_current / (games_current + games_historical)` (games-based ratio)
2. **Weight_B** = `MIN(1.0, games_current / transition_period)` (transition-based, default 12 games)
3. **Final weight** = `MAX(Weight_A, Weight_B)` - Ensures fair weighting for limited historical data
4. **Blended PPG** = `(weight × current_PPG) + ((1-weight) × historical_PPG)`

**For players WITHOUT historical data:**
- Use **100% current season PPG**
- Orange/amber visual indicator in frontend
- No blending applied


**Purpose**: Smooth transition from historical (2024-25) to current season data


**Games-Based Formula**: The system uses games played instead of calendar gameweeks for weighting. This ensures:
- Sustainable operation regardless of when data is uploaded
- Adaptation based on actual player performance data
- Consistency across different upload schedules

**Formula**: 
- `w_current = min(1, (games_played - 1) / 15)` where games_played is actual games data
- `Blended_PPG = (w_current × Current_PPG) + (w_historical × Historical_PPG)`

**Examples**:
- GW2: 6.7% current + 93.3% historical
- GW8: 46.7% current + 53.3% historical  
- GW16: 100% current

**Display Format**: "38+2" (historical+current games)

### **2. Progressive Form Calculation (EWMA)** ✅ *Enhanced 2025-08-28*
**Purpose**: Responsive form tracking using Exponential Weighted Moving Average with sample-size aware boundaries

**Algorithm**:
- Recent 5 games weighted exponentially: α^0, α^1, α^2, α^3, α^4
- Alpha (α) = 0.87 (5-game half-life)
- Normalized against dynamic baseline: `form_score ÷ blended_ppg`

**Progressive Range System** ✅ *New Feature*:
Progressive multiplier boundaries based on statistical confidence of sample size:
- **Games 1-2**: ±5% range (0.95-1.05) - Tight early-season control  
- **Games 3-4**: ±15% range (0.85-1.15) - Moderate expansion
- **Games 5-6**: ±20% range (0.80-1.20) - Increased differentiation
- **Games 7-8**: ±25% range (0.75-1.25) - Strong sample confidence
- **Games 9-10**: ±30% range (0.70-1.30) - Full statistical confidence
- **Games 11+**: ±30% range maintained - Maximum differentiation allowed

**Benefits**:
- **Early Season Volatility Control**: 50% reduction in multiplier extremes (±5% vs ±10%)
- **Statistical Rigor**: Ranges expand as sample size increases reliability
- **Balance**: Form impact scales appropriately relative to other multipliers

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
- **Form**: Progressive ranges (0.95-1.05 early → 0.70-1.30 late season) - Sample-size aware
- **Fixture**: 0.5 - 1.8x
- **xGI**: 0.5 - 2.5x
- **Global**: 3.0x maximum (total product)

**Implementation**: Individual caps applied first, then global scaling if total exceeds 3.0x

---

## **Progressive Form Ranges System** ✅ *Added 2025-08-28*

### **Statistical Foundation**
The progressive Form ranges system addresses a critical issue in early-season fantasy football analysis: small sample sizes create unreliable performance metrics that lead to volatile multiplier values.

### **Implementation Strategy**
Instead of applying fixed multiplier boundaries (e.g., 0.5x-2.0x) regardless of data reliability, the system uses **sample-size aware boundaries** that expand as statistical confidence increases:

**Progressive Boundary Schedule**:
```
Games Played  │ Range        │ Statistical Confidence
──────────────┼──────────────┼─────────────────────
1-2 games     │ ±5%  (0.95-1.05) │ Low confidence
3-4 games     │ ±15% (0.85-1.15) │ Moderate confidence  
5-6 games     │ ±20% (0.80-1.20) │ Growing confidence
7-8 games     │ ±25% (0.75-1.25) │ Strong confidence
9-10 games    │ ±30% (0.70-1.30) │ Full confidence
11+ games     │ ±30% (0.70-1.30) │ Maximum range
```

### **Mathematical Benefits**
1. **Early Season Stability**: ±5% boundaries prevent extreme multipliers from limited data
2. **Progressive Expansion**: Boundaries expand as sample reliability increases
3. **Statistical Rigor**: Aligns multiplier impact with confidence level of underlying data
4. **System Balance**: Form impact scales relative to other V2.0 multipliers (Fixture: ±80%, xGI: ±150%)

### **Business Impact**
- **50% Volatility Reduction**: Early season multipliers reduced from ±10% to ±5%
- **Improved Predictions**: More stable True Value calculations with limited data
- **Better User Experience**: Fewer dramatic swings in player recommendations
- **Enhanced Reliability**: Multiplier ranges match statistical confidence of performance data

### **Configuration**
Progressive ranges are enabled via `config/system_parameters.json`:
```json
"progressive_form_ranges": {
  "enabled": true,
  "ranges_by_games": [
    {"games": 2, "min": 0.95, "max": 1.05},
    {"games": 4, "min": 0.85, "max": 1.15},
    {"games": 6, "min": 0.80, "max": 1.20},
    {"games": 8, "min": 0.75, "max": 1.25},
    {"games": 10, "min": 0.70, "max": 1.30}
  ]
}
```

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
      "full_adaptation_gw": 16
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
   - Weight: 6.7% current + 93.3% historical
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
- **Full Recalculation**: <1 second for 714 players

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
- **xGI Coverage**: 335/714 players with baseline data
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

*This guide documents the complete V2.0 Enhanced Formula system serving 714 Premier League players with advanced mathematical calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form tracking, and normalized xGI integration.*