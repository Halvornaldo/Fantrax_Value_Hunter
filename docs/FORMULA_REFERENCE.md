# Formula Reference Guide

## Core Formula Overview

The Fantrax Value Hunter system uses Formula Optimization v2.0 with separate True Value and ROI calculations:

**Formula v2.0 (Current - 2025-08-21)**:
```
True Value = Blended PPG × Form Multiplier × Fixture Multiplier × Starter Multiplier × xGI Multiplier
ROI = True Value ÷ Player Price
```

**Sprint 2 Enhancements**:
- **EWMA Form**: Exponential weighted moving average with α=0.87
- **Dynamic Blending**: Smooth transition using w_current = min(1, (N-1)/(K-1))
- **Normalized xGI**: Ratio-based calculation (Recent_xGI/Historical_Baseline)

**Legacy Formula v1.0 (Deprecated)**:
```
Base Value = Points Per Game (PPG) ÷ Player Price  [MIXED PREDICTION WITH VALUE]
```

## Detailed Formula Breakdown

### 1. Dynamic PPG Blending (`calculation_engine_v2.py:_calculate_blended_ppg`)

**Sprint 2 Enhancement**: Replaces static PPG with dynamically blended historical and current season data.

```python
def _calculate_blended_ppg(self, player_data):
    K = 16  # Full adaptation gameweek
    w_current = min(1.0, (current_gameweek - 1) / (K - 1)) if current_gameweek > 1 else 0.0
    w_historical = 1.0 - w_current
    
    blended_ppg = (w_current * current_ppg) + (w_historical * historical_ppg)
    return max(0.1, blended_ppg), w_current
```

**Components:**
- **Current PPG**: Points per game this season
- **Historical PPG**: Points per game previous season  
- **K**: Full adaptation gameweek (default: 16)
- **Smooth Transition**: No hard cutoffs, gradual weight shift

**Legacy v1.0 (Deprecated):**
```python
base_value = ppg / price if price > 0 else 0  # Mixed prediction with value
```

### 2. EWMA Form Multiplier (`calculation_engine_v2.py:_calculate_exponential_form_multiplier`)

**Sprint 2 Enhancement**: Exponential Weighted Moving Average with configurable decay factor.

```python
def _calculate_exponential_form_multiplier(self, player_data):
    alpha = 0.87  # Exponential decay factor (5-game half-life)
    recent_games = player_data.get('recent_points', [])
    
    # Generate exponential decay weights: α^0, α^1, α^2, ...
    weights = [alpha ** i for i in range(len(recent_games))]
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    # Calculate weighted form score
    form_score = sum(points * weight for points, weight in zip(recent_games, normalized_weights))
    
    # Normalize against blended baseline
    blended_baseline, _ = self._calculate_blended_ppg(player_data)
    form_multiplier = form_score / blended_baseline if blended_baseline > 0 else 1.0
    
    return max(0.5, min(2.0, form_multiplier))  # Capped at [0.5, 2.0]
```

**Key Features:**
- **α = 0.87**: 5-game half-life (most recent games weighted highest)
- **Exponential Decay**: More sophisticated than linear weights
- **Dynamic Baseline**: Uses blended PPG instead of static baseline
- **Multiplier Caps**: Prevents extreme outliers [0.5, 2.0]

**Legacy v1.0 (Deprecated):**
```python
# Fixed weights: [0.4, 0.25, 0.2, 0.1, 0.05] for 5 games
weighted_form = sum(points[i] * weights[i] for i in range(len(points)))
```

### 3. Normalized xGI Multiplier (`calculation_engine_v2.py:_calculate_normalized_xgi_multiplier`)

**Sprint 2 Enhancement**: Ratio-based xGI comparison against historical baseline.

```python
def _calculate_normalized_xgi_multiplier(self, player_data):
    current_xgi = float(player_data.get('xgi90', 0.0) or 0.0)
    baseline_xgi = float(player_data.get('baseline_xgi', 0.0) or 0.0)
    position = player_data.get('position', 'M')
    
    # Position-specific logic
    if position == 'G':
        return 1.0  # Goalkeepers - xGI not relevant
    
    # Calculate ratio-based multiplier
    if baseline_xgi > 0.1:
        xgi_ratio = current_xgi / baseline_xgi
    else:
        # Use position defaults for missing baseline
        xgi_ratio = 1.0
    
    # Position-specific impact adjustments
    if position == 'D':
        # Reduce impact for defenders (less xGI relevance)
        xgi_ratio = 1.0 + (xgi_ratio - 1.0) * 0.6
    
    return max(0.4, min(2.5, xgi_ratio))  # Capped at [0.4, 2.5]
```

**Key Features:**
- **Ratio Calculation**: `current_xGI90 / baseline_xGI90`
- **Historical Baseline**: 2024/25 season data from Understat
- **Position Awareness**: Reduced impact for defenders, disabled for goalkeepers
- **Multiplier Caps**: Prevents extreme outliers [0.4, 2.5]

**Data Sources:**
- **Current**: `xgi90` column (2025/26 season Expected Goals Involvement)
- **Baseline**: `baseline_xgi` column (2024/25 historical data)

**Legacy v1.0 (Deprecated):**
```python
# Fixed modes: direct, adjusted, capped (no normalization)
```

### 4. Exponential Fixture Multiplier (Enhanced in Sprint 1)

**Sprint 1 Enhancement**: Exponential transformation instead of linear adjustment.

```python
def _calculate_exponential_fixture_multiplier(self, player_data):
    difficulty_score = player_data.get('fixture_difficulty', 0)
    position = player_data.get('position', 'M')
    
    # Get exponential base (configurable, default: 1.05)
    exponential_base = 1.05
    
    # Position-specific impact weights
    position_weights = {
        'G': 1.1,   # Goalkeepers: 110%
        'D': 1.2,   # Defenders: 120% 
        'M': 1.0,   # Midfielders: 100% (baseline)
        'F': 1.05   # Forwards: 105%
    }
    
    pos_weight = position_weights.get(position, 1.0)
    adjusted_difficulty = difficulty_score * pos_weight / 10.0
    
    # Exponential transformation: base^(-difficulty)
    fixture_multiplier = exponential_base ** (-adjusted_difficulty)
    
    return max(0.5, min(1.8, fixture_multiplier))  # Capped at [0.5, 1.8]
```

**Key Features:**
- **Exponential Transformation**: `base^(-difficulty)` instead of linear
- **Configurable Base**: Default 1.05 (5% per difficulty point)
- **Position Weights**: Enhanced impact for goalkeepers and defenders
- **Multiplier Caps**: Prevents extreme outliers [0.5, 1.8]

**Examples:**
- **Easy fixture** (-5 difficulty): 1.05^(0.5) ≈ 1.25x (25% boost)
- **Hard fixture** (+5 difficulty): 1.05^(-0.5) ≈ 0.81x (19% penalty)

**Legacy v1.0 (Linear):**
```python
final_multiplier = 1.0 - (difficulty_score / 10.0) * 0.2
```

### 5. Starter Prediction Multiplier (`app.py:218-284`)

Adjusts value based on predicted starting likelihood with manual override support.

#### Base Calculation:
```python
if starter_status == 'starter':
    starter_multiplier = 1.0
elif starter_status == 'rotation':
    starter_multiplier = 0.9  # 10% penalty
elif starter_status == 'bench':
    starter_multiplier = 0.6  # 40% penalty
else:
    starter_multiplier = 1.0  # Unknown = no penalty
```

#### Manual Override System:
Manual overrides stored in JSON format take precedence:
```json
{
    "player_name": {
        "status": "starter|rotation|bench",
        "confidence": 0.8,
        "reason": "Confirmed in training"
    }
}
```

#### Override Logic:
```python
if manual_override_exists:
    return manual_override_multiplier
else:
    return calculated_starter_multiplier
```

**Note:** xGI multiplier calculation is covered in Section 3 (Normalized xGI Multiplier) above.

## Blender Display System

The games display format evolves throughout the season to reflect data transitions.

### Display Logic (`app.py:games_display`)

**Configuration Parameters:**
```python
baseline_switchover_gameweek = 10
transition_period_end = 15  
show_historical_data = True
```

**Display Format Rules:**

**Early Season (GW 1-10):**
```python
if games_current > 0:
    display = f"{games_historical}+{games_current}"  # "38+2"
elif games_historical > 0:
    display = f"{games_historical} (24-25)"         # "38 (24-25)"
else:
    display = "0"
```

**Transition Period (GW 11-15):**
```python
if games_historical > 0 and games_current > 0:
    display = f"{games_historical}+{games_current}"  # "38+5"
elif games_historical > 0:
    display = f"{games_historical} (24-25)"         # "38 (24-25)"
else:
    display = str(games_current)                     # "5"
```

**Late Season (GW 16+):**
```python
if games_current > 0:
    display = str(games_current)                     # "15"
elif games_historical > 0:
    display = f"{games_historical} (24-25)"         # "38 (24-25)"
else:
    display = "0"
```

## Sprint 2 Parameter Validation Ranges

### Dynamic Blending Parameters:
- **Full Adaptation GW**: 10-20 games (default: 16)
- **Current Weight Formula**: `min(1, (N-1)/(K-1))`
- **Minimum Baseline**: Historical PPG > 0.1

### EWMA Form Parameters:
- **Alpha (α)**: 0.70-0.995 (default: 0.87)
  - 0.70: Highly reactive (2-game focus)
  - 0.87: 5-game half-life (recommended)  
  - 0.95: Sticky form (10-game influence)
- **Multiplier Caps**: [0.5, 2.0]

### Exponential Fixture Parameters:
- **Base**: 1.01-1.10 (default: 1.05)
- **Position Weights**: G=1.1, D=1.2, M=1.0, F=1.05
- **Multiplier Caps**: [0.5, 1.8]

### Normalized xGI Parameters:
- **Position Impact**: D=60%, M/F=100%, G=disabled
- **Minimum Baseline**: 0.1 xGI90
- **Multiplier Caps**: [0.4, 2.5]

### Legacy v1.0 Parameters (Deprecated):
- **Fixed Form Weights**: [0.4, 0.25, 0.2, 0.1, 0.05]
- **Linear Fixture**: 20% base strength
- **xGI Modes**: Direct/Adjusted/Capped (no normalization)

## Sprint 2 Performance Specifications

### Processing Targets:
- **Player Count**: 647+ Premier League players
- **Calculation Engine**: v2.0 dual-engine system (v1.0 + v2.0)
- **API Endpoints**: `/api/calculate-values-v2` with Sprint 2 features
- **Response Time**: ~2-3 seconds for parameter changes
- **Data Integration**: 335 historical baselines from Understat 2024/25

### Sprint 2 Data Dependencies:
- **Current Season**: 2025/26 xGI data (xgi90 column)
- **Historical Baseline**: 2024/25 xGI data (baseline_xgi column) 
- **Dynamic Blending**: Historical + current PPG data
- **EWMA Form**: Recent points array for exponential calculation

## Sprint 2 Error Handling

### Missing Data Fallbacks:
```python
# Dynamic blending
if historical_ppg == 0:
    return current_ppg, 1.0  # Use current only

# EWMA form calculation
if not recent_games:
    return 1.0  # Neutral multiplier

# Normalized xGI  
if baseline_xgi < 0.1:
    baseline_xgi = position_default  # Use position average

# Exponential fixture
if difficulty_score is None:
    return 1.0  # Neutral multiplier
```

### Sprint 2 Validation Constraints:
- **Form Multiplier**: [0.5, 2.0] with exponential decay
- **Fixture Multiplier**: [0.5, 1.8] with exponential transformation  
- **xGI Multiplier**: [0.4, 2.5] with position-specific adjustments
- **Division Protection**: All ratios checked for zero denominators
- **Global Cap**: 3.0 maximum total multiplier (configurable)

## Sprint 3 Validation Framework Findings

### Critical Data Quality Discovery (Sprint 3)

**Championship Contamination Issue:**
- **Problem**: 63 players had `baseline_xgi` values from Championship/lower leagues
- **Impact**: Created false validation results and biased predictions
- **Teams Affected**: Leeds (promoted), Burnley, Southampton, plus new signings
- **Resolution**: Cleaned to 303 Premier League-only players for accurate validation

**Validation Results with Clean Data:**
```python
# Before cleanup: 366 players with baseline data
# After cleanup: 303 players with valid Premier League baseline
# Players removed: 63 with Championship/lower league contamination
```

### Formula Version Validation Issues

**v1.0 vs v2.0 Testing Problem:**
- **v1.0 Formula Issue**: `true_value = (ppg / price) * multipliers` → 0.0 when ppg=0 (early season)  
- **v2.0 Formula Correct**: `true_value = blended_ppg * multipliers` → Uses historical baseline properly

**Validation Comparison:**
```python
# v1.0 Results (Deprecated):
# - 74 players tested
# - RMSE: 2.277 (poor accuracy)
# - Bias: +1.7 points (massive under-prediction)

# v2.0 Results (Limited Data):
# - 33 players tested (90+ minutes filter)
# - RMSE: 0.305 (excellent accuracy)
# - Bias: +0.1 points (minimal error)
# - WARNING: Single gameweek, potential data leakage
```

### Validation Framework Limitations

**Critical Limitations Identified:**
1. **Data Leakage Risk**: Current validation tests against potentially seen data
2. **Small Sample Size**: Only 33 players with complete v2.0 data and 90+ minutes
3. **Single Gameweek**: No consistency testing across multiple gameweeks
4. **Temporal Separation**: Need future gameweek data for proper validation

**Validation Quality Assessment:**
- **Formula Architecture**: ✅ EXCELLENT - Proper prediction/value separation
- **Data Integration**: ✅ EXCELLENT - 99% name matching, clean historical data
- **Validation Results**: ⚠️ LIMITED but PROMISING - Need temporal separation for conclusive testing

### Production-Ready Validation Pipeline

**Created for Sprint 3:**
- `validation_pipeline.py` - Production-ready framework for future validation
- `fantasy_validation_simple.py` - Clean validation execution with limited data
- `verify_baseline_cleanup.py` - Data integrity verification system
- Comprehensive error analysis and prediction failure tracking

**Framework Capabilities:**
- Cross-validation across multiple gameweeks
- Temporal separation for proper backtesting
- Position-specific performance analysis
- Robustness testing for fixture difficulty and form variations
- Statistical framework with RMSE, MAE, correlation, R², precision@K metrics

### Sprint 3 Validation Requirements for Future Use

**For Proper Validation (Awaiting Data):**
1. **Temporal Separation**: Test on GW2+ data when available
2. **Historical Backtesting**: Use 2023-24 season data with ScraperFC
3. **Cross-Validation**: Test consistency across multiple gameweeks
4. **Larger Sample Size**: Expand beyond 33 players when more v2.0 data available

**Framework Status:**
- ✅ **Data Quality**: Championship contamination detection and cleanup system operational
- ✅ **Validation Infrastructure**: Production-ready pipeline created and tested
- ✅ **Error Analysis**: Comprehensive prediction failure tracking implemented
- ⏳ **Temporal Validation**: Framework ready, awaiting proper temporal data separation

## Integration with Dashboard

### Real-time Updates:
- Parameter changes trigger immediate recalculation
- Toggle switches provide instant enable/disable functionality
- Visual indicators show data quality and matching status

### User Controls:
- Slider controls for strength parameters
- Dropdown selects for calculation modes
- Manual override JSON editor for starter predictions
- Display toggles for showing/hiding statistical components

### Sprint 3 Validation Dashboard (Ready for Deployment):
- Backend API: 5 new validation endpoints in `src/app.py`
- Frontend: Complete HTML dashboard (`templates/validation_dashboard.html`)
- Real-time metrics display with historical trend charts
- Interactive parameter controls and target achievement indicators

This reference provides the complete mathematical foundation for the Fantrax Value Hunter system, including critical Sprint 3 validation framework findings and data quality discoveries.