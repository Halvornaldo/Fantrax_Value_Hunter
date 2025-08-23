# V2.0 Enhanced Formula Reference Guide - Complete Mathematical Documentation
## Fantasy Football Value Hunter V2.0 Enhanced Formula System

### **System Status: V2.0 Production Formula**

This document provides complete mathematical documentation for the V2.0 Enhanced Formula system. The system has been consolidated to a single V2.0 engine with all legacy components removed.

**Formula Engine**: `calculation_engine_v2.py`  
**Current System**: V2.0 Enhanced Formula fully operational

---

## **V2.0 Enhanced Core Formula**

### **Separated Prediction and Value Model**
```
True Value = Blended_PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Player_Price
```

**Key V2.0 Innovations**:
- **Separated Metrics**: True Value (point prediction) distinct from ROI (value efficiency)
- **Dynamic Blending**: Smooth mathematical transition from historical to current season data
- **Exponential Form**: EWMA calculations with α=0.87 for responsive form tracking
- **Normalized xGI**: Ratio-based Expected Goals Involvement with baseline comparisons
- **Exponential Fixtures**: Advanced difficulty scaling using base^(-difficulty) formula

---

## **V2.0 Component Calculations**

### **1. Dynamic PPG Blending System**
**Purpose**: Seamlessly transitions from historical (2024-25) to current season data using mathematical blending

**V2.0 Implementation** (`calculation_engine_v2.py:_calculate_dynamic_blending`):
```python
def _calculate_dynamic_blending(self, player_data, current_gameweek):
    K = self.parameters.get('full_adaptation_gw', 16)  # Full adaptation gameweek
    
    # Calculate current season weight
    if current_gameweek > 1:
        w_current = min(1.0, (current_gameweek - 1) / (K - 1))
    else:
        w_current = 0.0
    
    w_historical = 1.0 - w_current
    
    # Extract data
    current_ppg = player_data.get('ppg', 0.0)
    historical_ppg = player_data.get('historical_ppg', 0.0)
    
    # Blend with fallback protection
    if historical_ppg > 0.1:
        blended_ppg = (w_current * current_ppg) + (w_historical * historical_ppg)
    else:
        blended_ppg = current_ppg if current_ppg > 0.1 else 5.0  # Fallback baseline
    
    return max(0.1, blended_ppg), w_current
```

**Mathematical Formula**:
- **Weight Calculation**: `w_current = min(1, (N-1)/(K-1))`
- **Blended PPG**: `(w_current × Current_PPG) + (w_historical × Historical_PPG)`
- **Smooth Transition**: No hard cutoffs, gradual weight progression

**Examples**:
```
Gameweek 2: w_current = min(1, (2-1)/(16-1)) = 0.067 (6.7% current + 93.3% historical)
Gameweek 8: w_current = min(1, (8-1)/(16-1)) = 0.467 (46.7% current + 53.3% historical)
Gameweek 16: w_current = min(1, (16-1)/(16-1)) = 1.000 (100% current)
```

### **2. EWMA Form Calculation**
**Purpose**: Advanced form tracking using Exponential Weighted Moving Average for responsive performance analysis

**V2.0 Implementation** (`calculation_engine_v2.py:_calculate_exponential_form`):
```python
def _calculate_exponential_form(self, recent_points, baseline_ppg, alpha):
    if not recent_points or len(recent_points) == 0:
        return 1.0  # Neutral multiplier for no data
    
    # Generate exponential decay weights: α^0, α^1, α^2, ...
    weights = [alpha ** i for i in range(len(recent_points))]
    total_weight = sum(weights)
    
    if total_weight == 0:
        return 1.0
    
    # Calculate EWMA score
    ewma_score = sum(points * (weights[i] / total_weight) 
                    for i, points in enumerate(recent_points))
    
    # Normalize against dynamic baseline
    if baseline_ppg > 0:
        form_multiplier = ewma_score / baseline_ppg
    else:
        form_multiplier = 1.0
    
    # Apply enhanced caps [0.5, 2.0]
    return max(0.5, min(2.0, form_multiplier))
```

**Technical Features**:
- **Algorithm**: EWMA with exponential decay (α^0, α^1, α^2 for recent games)
- **5-Game Half-Life**: α=0.87 provides optimal balance of responsiveness and stability
- **Baseline Normalization**: Compares to dynamic blended PPG, not static average
- **Enhanced Range**: 0.5-2.0x (more responsive than legacy 0.5-1.5x)

**Examples**:
```
Recent games: [8.5, 7.2, 9.1, 6.8, 8.0]
Alpha = 0.87
Weights: [1.00, 0.87, 0.76, 0.66, 0.57] → Normalized: [0.28, 0.24, 0.21, 0.18, 0.16]
EWMA Score: 8.5×0.28 + 7.2×0.24 + 9.1×0.21 + 6.8×0.18 + 8.0×0.16 = 8.15
If baseline_ppg = 8.0: Form Multiplier = 8.15/8.0 = 1.019x
```

### **3. Exponential Fixture Difficulty**
**Purpose**: Advanced fixture difficulty using exponential scaling for more accurate impact assessment

**V2.0 Implementation** (`calculation_engine_v2.py:_calculate_exponential_fixtures`):
```python
def _calculate_exponential_fixtures(self, player_data):
    difficulty_score = float(player_data.get('fixture_difficulty', 0.0))
    position = player_data.get('position', 'M')
    
    # Get exponential base (configurable, default: 1.05)
    exponential_base = self.parameters.get('exponential_base', 1.05)
    
    # Position-specific impact weights
    position_weights = {
        'G': 1.1,   # Goalkeepers: 110% (save opportunities)
        'D': 1.2,   # Defenders: 120% (clean sheet dependency)
        'M': 1.0,   # Midfielders: 100% (baseline)
        'F': 1.05   # Forwards: 105% (scoring vs weaker defenses)
    }
    
    pos_weight = position_weights.get(position, 1.0)
    
    # Apply position weight and normalize
    adjusted_difficulty = difficulty_score * pos_weight
    
    # Exponential transformation: base^(-difficulty)
    fixture_multiplier = exponential_base ** (-adjusted_difficulty)
    
    # Apply caps [0.5, 1.8]
    return max(0.5, min(1.8, fixture_multiplier))
```

**Mathematical Formula**:
- **Base Transformation**: `multiplier = base^(-difficulty_score)`
- **21-Point Scale**: Converts betting odds to difficulty (-10 to +10)
- **Position Adjustments**: Role-appropriate impact scaling

**Examples**:
```
Easy Fixture (-8.0 difficulty): 1.05^(8.0) = 1.477x multiplier
Hard Fixture (+6.0 difficulty): 1.05^(-6.0) = 0.746x multiplier
Neutral Fixture (0.0 difficulty): 1.05^0 = 1.000x multiplier

Position Impact:
Defender vs Easy Fixture: (-8.0 × 1.2) = -9.6 → 1.05^9.6 = 1.604x
Midfielder vs Easy Fixture: (-8.0 × 1.0) = -8.0 → 1.05^8.0 = 1.477x
```

### **4. Normalized xGI Integration**
**Purpose**: Advanced Expected Goals Involvement using ratio-based comparisons with position-specific adjustments

**V2.0 Implementation** (`calculation_engine_v2.py:_calculate_normalized_xgi`):
```python
def _calculate_normalized_xgi(self, player_data):
    current_xgi = float(player_data.get('xgi90', 0.0) or 0.0)
    baseline_xgi = float(player_data.get('baseline_xgi', 0.0) or 0.0)
    position = player_data.get('position', 'M')
    
    # Position-specific logic
    if position == 'G':
        return 1.0  # Goalkeepers - xGI completely disabled
    
    # Calculate ratio-based multiplier
    if baseline_xgi > 0.1:
        xgi_ratio = current_xgi / baseline_xgi
    else:
        # Use position defaults for missing baseline
        position_defaults = {'D': 0.15, 'M': 0.8, 'F': 1.2}
        default_baseline = position_defaults.get(position, 0.8)
        xgi_ratio = current_xgi / default_baseline if default_baseline > 0 else 1.0
    
    # Position-specific impact adjustments
    if position == 'D' and baseline_xgi < 0.2:
        # Reduce impact for defenders when baseline is low (defensive role)
        xgi_ratio = 1.0 + (xgi_ratio - 1.0) * 0.7  # 30% impact reduction
    
    # Apply enhanced caps [0.5, 2.5]
    return max(0.5, min(2.5, xgi_ratio))
```

**Technical Features**:
- **Calculation**: `current_xgi90 ÷ baseline_xgi` (ratio-based normalization)
- **Baseline Source**: 2024-25 season averages from Understat integration
- **Position Logic**: Automatic adjustments for role-appropriate impact
- **Enhanced Range**: 0.5-2.5x (allows significant xGI differentiation)

**Examples**:
```
Ben White (Defender):
- current_xgi90: 0.099 (2025-26 limited data)
- baseline_xgi: 0.142 (2024-25 average)
- Raw ratio: 0.099/0.142 = 0.697
- Position adjustment: 1.0 + (0.697 - 1.0) × 0.7 = 0.788
- Final multiplier: 0.788x (defensive role, below baseline performance)

Erling Haaland (Forward):
- current_xgi90: 1.845 (2025-26 excellent form)
- baseline_xgi: 2.064 (2024-25 elite level)
- Raw ratio: 1.845/2.064 = 0.894
- Position adjustment: 100% impact (forward)
- Final multiplier: 0.894x (slightly below elite baseline)
```

### **5. Starter Prediction Multiplier**
**Purpose**: Adjusts value based on predicted starting likelihood with manual override support

**V2.0 Implementation** (`src/app.py:starter_multiplier_logic`):
```python
def calculate_starter_multiplier(player_data, manual_overrides=None):
    player_name = player_data.get('name', '')
    
    # Check for manual override first
    if manual_overrides and player_name in manual_overrides:
        override = manual_overrides[player_name]
        status = override.get('status', 'auto')
        
        if status == 'starter':
            return 1.0
        elif status == 'bench':
            return 0.6
        elif status == 'out':
            return 0.0
    
    # Use automatic prediction
    starter_status = player_data.get('starter_status', 'unknown')
    
    if starter_status == 'starter':
        return 1.0      # Full expected value
    elif starter_status == 'rotation':
        return 0.9      # 10% penalty for rotation risk
    elif starter_status == 'bench':
        return 0.6      # 40% penalty for bench role
    elif starter_status == 'out':
        return 0.0      # Unavailable
    else:
        return 1.0      # Unknown = no penalty (benefit of doubt)
```

**Manual Override System**:
- **Real-time Updates**: True Value recalculates instantly with V2.0 engine
- **Override Controls**: S (Starter), B (Bench), O (Out), A (Auto)
- **Visual Feedback**: Color coding shows override status in dashboard
- **Persistence**: Manual overrides stored and maintained between sessions

---

## **V2.0 Multiplier Cap System**

### **Enhanced Cap Framework**
**Purpose**: Prevents extreme outliers while allowing meaningful differentiation

**V2.0 Cap Implementation**:
```python
def apply_multiplier_caps(self, multipliers):
    caps = self.parameters.get('multiplier_caps', {
        'form': 2.0,
        'fixture': 1.8,
        'xgi': 2.5,
        'global': 3.0
    })
    
    # Apply individual caps
    form_capped = max(0.5, min(caps['form'], multipliers['form']))
    fixture_capped = max(0.5, min(caps['fixture'], multipliers['fixture']))
    xgi_capped = max(0.5, min(caps['xgi'], multipliers['xgi']))
    starter_capped = max(0.0, min(1.0, multipliers['starter']))
    
    # Calculate total multiplier
    total_multiplier = form_capped * fixture_capped * xgi_capped * starter_capped
    
    # Apply global cap
    if total_multiplier > caps['global']:
        scaling_factor = caps['global'] / total_multiplier
        form_capped *= scaling_factor
        fixture_capped *= scaling_factor
        xgi_capped *= scaling_factor
    
    return {
        'form': form_capped,
        'fixture': fixture_capped,
        'xgi': xgi_capped,
        'starter': starter_capped,
        'total': min(total_multiplier, caps['global'])
    }
```

**Enhanced V2.0 Caps**:
- **Form Cap**: 0.5-2.0x (expanded from legacy 0.5-1.5x)
- **Fixture Cap**: 0.5-1.8x (maintains reasonable difficulty impact)
- **xGI Cap**: 0.5-2.5x (allows significant xGI differentiation)
- **Global Cap**: 3.0x maximum (product of all multipliers)

---

## **V2.0 Blender Display System**

### **Dynamic Display Logic**
**Purpose**: Visual representation of data blending throughout the season

**V2.0 Display Implementation** (`src/app.py:games_display_v2`):
```python
def calculate_games_display_v2(player_data, current_gameweek):
    games_current = int(player_data.get('games_played', 0))
    games_historical = int(player_data.get('games_played_historical', 0))
    
    # Configuration parameters
    baseline_switchover = 10
    transition_end = 16
    
    # Display format based on season progression
    if current_gameweek <= baseline_switchover:
        # Early season - show historical basis
        if games_current > 0 and games_historical > 0:
            return f"{games_historical}+{games_current}"  # "38+2"
        elif games_historical > 0:
            return f"{games_historical} (24-25)"          # "38 (24-25)"
        else:
            return str(games_current) if games_current > 0 else "0"
            
    elif current_gameweek <= transition_end:
        # Transition period - blend display
        if games_current > 0 and games_historical > 0:
            return f"{games_historical}+{games_current}"  # "38+8"
        else:
            return str(games_current) if games_current > 0 else "0"
            
    else:
        # Late season - current data focus
        if games_current > 0:
            return str(games_current)                      # "15"
        elif games_historical > 0:
            return f"{games_historical} (24-25)"          # "38 (24-25)"
        else:
            return "0"
```

**Display Evolution**:
- **Early Season (GW1-10)**: "38+2" (historical foundation)
- **Transition (GW11-16)**: "38+8" (blending phase)
- **Late Season (GW17+)**: "15" (current focus)

---

## **V2.0 Parameter Configuration**

### **System Parameters Structure**
**File**: `config/system_parameters.json`

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
  }
}
```

### **V2.0 Parameter Ranges**

**Dynamic Blending Parameters**:
- **Full Adaptation GW**: 10-20 games (default: 16)
- **Current Weight Formula**: `min(1, (N-1)/(K-1))`
- **Minimum Baseline**: Historical PPG > 0.1

**EWMA Form Parameters**:
- **Alpha (α)**: 0.70-0.995 (default: 0.87)
  - 0.70: Highly reactive (2-game focus)
  - 0.87: 5-game half-life (recommended)
  - 0.95: Sticky form (10-game influence)
- **Multiplier Caps**: [0.5, 2.0]

**Exponential Fixture Parameters**:
- **Base**: 1.01-1.10 (default: 1.05)
- **Position Weights**: G=1.1, D=1.2, M=1.0, F=1.05
- **Multiplier Caps**: [0.5, 1.8]

**Normalized xGI Parameters**:
- **Position Impact**: D=70%, M/F=100%, G=disabled
- **Minimum Baseline**: 0.1 xGI90
- **Multiplier Caps**: [0.5, 2.5]

---

## **V2.0 Error Handling and Fallbacks**

### **Robust Data Validation**
```python
# Dynamic blending fallback
def safe_dynamic_blending(player_data, current_gameweek):
    historical_ppg = float(player_data.get('historical_ppg', 0.0) or 0.0)
    current_ppg = float(player_data.get('ppg', 0.0) or 0.0)
    
    if historical_ppg <= 0.1:
        return current_ppg if current_ppg > 0.1 else 5.0, 1.0
    
    return calculate_blended_ppg(player_data, current_gameweek)

# EWMA form fallback
def safe_ewma_calculation(recent_games, baseline_ppg, alpha):
    if not recent_games or len(recent_games) == 0:
        return 1.0  # Neutral multiplier
    
    if baseline_ppg <= 0:
        baseline_ppg = 5.0  # Reasonable default
    
    return calculate_ewma_form(recent_games, baseline_ppg, alpha)

# Normalized xGI fallback
def safe_xgi_calculation(player_data):
    baseline_xgi = float(player_data.get('baseline_xgi', 0.0) or 0.0)
    
    if baseline_xgi <= 0.1:
        # Use position-specific defaults
        position = player_data.get('position', 'M')
        position_defaults = {'D': 0.15, 'M': 0.8, 'F': 1.2, 'G': 0.0}
        baseline_xgi = position_defaults.get(position, 0.8)
    
    return calculate_normalized_xgi(player_data, baseline_xgi)
```

### **V2.0 Validation Constraints**
- **Division Protection**: All ratios checked for zero denominators
- **Range Validation**: All multipliers constrained to valid ranges
- **Type Safety**: Explicit float conversion with fallback defaults
- **Position Validation**: All position codes validated against known values

---

## **V2.0 Performance Specifications**

### **Processing Targets**
- **Player Dataset**: 647 Premier League players
- **Calculation Engine**: V2.0 Enhanced Formula system
- **API Response Time**: <500ms for player data endpoint
- **Parameter Updates**: <300ms for configuration changes
- **Full Recalculation**: <1 second for complete dataset
- **Memory Usage**: <200MB peak during calculation

### **V2.0 Data Dependencies**
- **Current Season**: 2025-26 performance data (PPG, recent games)
- **Historical Baseline**: 2024-25 season data (PPG, xGI baselines)
- **Fixture Odds**: Real-time betting odds for difficulty calculation
- **Starter Predictions**: Rotation status and manual overrides

### **Integration Quality Metrics**
- **Name Matching**: 99% success rate across all data sources
- **xGI Baseline Coverage**: 335 players with 2024-25 baseline data
- **Form Data Coverage**: 100% player coverage with graceful missing data handling
- **Fixture Integration**: Real-time odds processing with 2x performance improvement

---

## **V2.0 Complete Calculation Example**

### **Detailed V2.0 Example: Erling Haaland**
```
Player: Erling Haaland (Manchester City)
Price: £15.00
Current Gameweek: 2

V2.0 Component Calculations:

1. Dynamic Blending:
   - Current PPG: 7.5 (1 game this season)
   - Historical PPG: 8.45 (2024-25 season average)
   - Current Weight: min(1, (2-1)/(16-1)) = 0.067 (6.7%)
   - Blended PPG: (0.067 × 7.5) + (0.933 × 8.45) = 8.39

2. EWMA Form (α=0.87):
   - Recent Games: [7.5] (single game)
   - EWMA Score: 7.5 (only one game)
   - Form Multiplier: 7.5 ÷ 8.39 = 0.894

3. Exponential Fixture:
   - Difficulty Score: +1.2 (slightly difficult)
   - Position Weight: 1.05 (Forward)
   - Adjusted Difficulty: 1.2 × 1.05 = 1.26
   - Fixture Multiplier: 1.05^(-1.26) = 0.937

4. Starter Prediction:
   - Status: Predicted starter
   - Starter Multiplier: 1.000

5. Normalized xGI:
   - Current xGI90: 1.845 (excellent early form)
   - Baseline xGI: 2.064 (2024-25 elite level)
   - xGI Ratio: 1.845 ÷ 2.064 = 0.894
   - xGI Multiplier: 0.894 (no position adjustment for forwards)

V2.0 Final Calculation:
True Value = 8.39 × 0.894 × 0.937 × 1.000 × 0.894 = 6.26
ROI = 6.26 ÷ 15.00 = 0.417

Result: Moderate True Value prediction with below-average ROI due to premium pricing
```

---

## **V2.0 Dashboard Integration**

### **Real-time Parameter Controls**
- **Apply Changes**: Save V2.0 parameters with instant recalculation
- **Reset to V2.0 Defaults**: Restore optimal V2.0 parameter values
- **Real-time Preview**: Parameter changes show immediate effect estimates
- **Configuration Persistence**: V2.0 settings saved to system_parameters.json

### **Enhanced Visual Feedback**
- **V2.0 Indicators**: Clear badges highlighting V2.0-specific features
- **Color Schemes**: Enhanced gradients for True Value and ROI columns
- **Tooltip System**: Professional explanations for all calculation components
- **Progress Tracking**: Visual feedback for parameter updates and calculations

### **Professional Interface Features**
- **Dashboard Layout**: Clean parameter controls and enhanced data table
- **Export Capabilities**: CSV exports include all V2.0 metadata
- **Mobile Compatibility**: Responsive design across device types
- **Performance Monitoring**: Real-time calculation status and timing

---

**Last Updated**: 2025-08-22 - V2.0 Enhanced Formula Mathematical Documentation Complete

*This document provides complete mathematical documentation for the V2.0 Enhanced Formula system with all legacy components removed. The formulas serve 647 Premier League players with optimized V2.0 calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form tracking, and normalized xGI integration.*