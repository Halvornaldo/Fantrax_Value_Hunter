# Formula Optimization Sprint Plan
## Research-Driven Enhancement to Fantasy Football Value Hunter

### **Overview**

This document outlines a 5-sprint implementation plan to optimize the Fantrax Value Hunter formula based on deep research analysis. The research validated our multiplicative approach while identifying critical improvements including exponential decay models, dynamic data blending, and separation of prediction from value metrics.

**Research Source**: `calculation-research/Fantasy Football Model Analysis & Optimization.md`
**Formula Version**: Upgrading from v1.0 → v2.0
**Expected Improvement**: 10-15% better prediction accuracy (RMSE < 2.85, Spearman > 0.30)

---

## **SPRINT 1: Foundation & Critical Fixes** ✅ COMPLETED
*Duration: 1 session (2-3 hours)*
*Priority: CRITICAL - Fixes fundamental calculation issues*
*Completion Date: 2025-08-21*

### **Objectives** 
1. ✅ **COMPLETED**: Fix the core formula (remove price from prediction)
2. ✅ **COMPLETED**: Implement exponential fixture calculation  
3. ✅ **COMPLETED**: Add multiplier caps for stability
4. ⏸️ **DEFERRED**: Gemini API integration (moved to Sprint 5)

### **Implementation Results**
- **Core Formula Fixed**: Created FormulaEngineV2 with proper True Value/ROI separation
- **Exponential Fixtures**: Implemented base^(-difficulty) transformation (base=1.05)
- **Multiplier Caps**: All caps active (form: 2.0, fixture: 1.8, xGI: 2.5, global: 3.0)
- **Database Migration**: Added v2.0 schema with new columns
- **Data Type Fixes**: Resolved Decimal/float compatibility issues
- **Testing**: v2.0 API integration test passing with real data
- **Dual Engine**: v1.0 and v2.0 running in parallel for safe comparison

### **Current Problem Analysis**

**Critical Issue**: The current formula mixes prediction with value assessment:
```python
# INCORRECT (current):
base_value = ppg / price  # Conflates "how many points?" with "is it worth the cost?"
true_value = base_value × multipliers

# This means expensive players are penalized in the prediction itself
# Haaland (£15m) gets artificially low True Value even if he'll score most points
```

**Research Finding**: The formula should predict points independently, then assess value separately.

### **Tasks**

#### **1.1 Fix Core Formula Architecture**

**File**: `src/app.py` (around line 301)

**BEFORE**:
```python
def calculate_base_value(ppg, price):
    return ppg / price if price > 0 else 0
```

**AFTER**:
```python
def calculate_true_value_components(player_data, params):
    """
    Calculate True Value as pure point prediction
    """
    # Get baseline PPG (will be enhanced in Sprint 2 with blending)
    ppg = player_data.get('ppg', 0)
    
    # Calculate all multipliers
    form_mult = calculate_form_multiplier(player_data, params)
    fixture_mult = calculate_fixture_multiplier(player_data, params)  # Will be exponential
    starter_mult = player_data.get('starter_multiplier', 1.0)
    xgi_mult = calculate_xgi_multiplier(player_data, params)
    
    # Pure prediction (no price involved)
    true_value = ppg * form_mult * fixture_mult * starter_mult * xgi_mult
    
    # Apply global cap to prevent extreme outliers
    max_allowed = ppg * params.get('global_multiplier_cap', 3.0)
    true_value = min(true_value, max_allowed)
    
    # Calculate ROI separately
    price = player_data.get('price', 1.0)
    roi = true_value / price if price > 0 else 0
    
    return {
        'true_value': round(true_value, 2),
        'roi': round(roi, 2),
        'multipliers': {
            'form': round(form_mult, 3),
            'fixture': round(fixture_mult, 3),
            'starter': round(starter_mult, 3),
            'xgi': round(xgi_mult, 3)
        }
    }
```

#### **1.2 Exponential Fixture Calculation**

**Research Formula**: `Fixture_Multiplier = base^(-S_diff)`
- Base = 1.05 (configurable 1.02-1.10)
- S_diff = difficulty score (-10 to +10)
- Negative because: negative difficulty = easier fixture = higher multiplier

**File**: `src/app.py` (fixture multiplier function)

**BEFORE**:
```python
def calculate_fixture_multiplier(difficulty_score, position, params):
    base_strength = 0.2
    position_weight = position_weights.get(position, 1.0)
    multiplier_adjustment = (difficulty_score / 10.0) * base_strength * position_weight
    final_multiplier = 1.0 - multiplier_adjustment
    return max(0.5, min(1.5, final_multiplier))
```

**AFTER**:
```python
def calculate_fixture_multiplier(player_data, params):
    """
    Exponential fixture difficulty transformation
    Research: base^(-difficulty_score) where base=1.05
    """
    difficulty_score = player_data.get('fixture_difficulty', 0)
    position = player_data.get('position', 'M')
    
    # Get configurable base (default 1.05)
    base = params.get('fixture_exponential', {}).get('base', 1.05)
    
    # Position-specific adjustments to the impact
    position_weights = {
        'G': 1.1,   # Goalkeepers: more saves vs stronger teams
        'D': 1.2,   # Defenders: clean sheets vs weaker teams critical
        'M': 1.0,   # Midfielders: baseline
        'F': 1.05   # Forwards: goals vs weaker teams
    }
    
    pos_weight = position_weights.get(position, 1.0)
    
    # Exponential transformation
    # Note: We use -difficulty_score because:
    # - Negative difficulty = easier fixture = higher multiplier
    # - Positive difficulty = harder fixture = lower multiplier
    adjusted_score = (-difficulty_score * pos_weight) / 10.0
    fixture_multiplier = base ** adjusted_score
    
    # Apply caps
    cap = params.get('multiplier_caps', {}).get('fixture', 1.8)
    return max(0.5, min(cap, fixture_multiplier))

# Example outputs with base=1.05:
# Easy fixture (difficulty=-5): 1.05^(5/10) = 1.05^0.5 ≈ 1.25
# Hard fixture (difficulty=+5): 1.05^(-5/10) = 1.05^-0.5 ≈ 0.80
# Neutral fixture (difficulty=0): 1.05^0 = 1.00
```

#### **1.3 Add Multiplier Cap System**

**File**: `config/system_parameters.json`

```json
{
  "multiplier_caps": {
    "description": "Prevent extreme outlier multipliers from breaking calculations",
    "form": 2.0,
    "fixture": 1.8,
    "starter": 1.0,
    "xgi": 2.5,
    "global": 3.0
  },
  "fixture_exponential": {
    "description": "Exponential fixture transformation parameters",
    "enabled": true,
    "base": 1.05,
    "base_range": [1.02, 1.10]
  }
}
```

#### **1.4 Database Schema Updates**

**File**: Create `migrations/sprint1_formula_fix.sql`

```sql
-- Add new columns for separated prediction and value
ALTER TABLE players ADD COLUMN IF NOT EXISTS true_value DECIMAL(8,2);
ALTER TABLE players ADD COLUMN IF NOT EXISTS roi DECIMAL(8,3);

-- Add column to track which formula version was used
ALTER TABLE players ADD COLUMN IF NOT EXISTS formula_version VARCHAR(10) DEFAULT 'v2.0';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_players_roi ON players(roi DESC);
CREATE INDEX IF NOT EXISTS idx_players_true_value ON players(true_value DESC);

-- Comments for clarity
COMMENT ON COLUMN players.true_value IS 'Pure point prediction (no price factor)';
COMMENT ON COLUMN players.roi IS 'Return on Investment: true_value / price';
```

#### **1.5 Gemini API Setup**

**File**: `config/api_keys.json`

```json
{
  "fantrax_session": "existing_key",
  "gemini_api_key": "your_key_here",
  "gemini_config": {
    "model": "gemini-1.5-pro",
    "max_tokens": 500,
    "temperature": 0.7
  }
}
```

**File**: Create `src/gemini_integration.py`

```python
"""
Gemini API integration for enhanced player analysis
"""
import google.generativeai as genai
import json
import os
from typing import Dict, List, Optional

class GeminiAnalyzer:
    def __init__(self):
        self.api_key = self._load_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.enabled = True
        else:
            self.enabled = False
            print("Gemini API key not found - AI features disabled")
    
    def _load_api_key(self) -> Optional[str]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_keys.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get('gemini_api_key')
        except Exception as e:
            print(f"Error loading Gemini API key: {e}")
            return None
    
    def generate_player_insight(self, player_data: Dict) -> Optional[str]:
        """Generate 1-2 sentence insight about player's current value"""
        if not self.enabled:
            return None
            
        try:
            prompt = f"""
            Player: {player_data.get('name', 'Unknown')}
            Position: {player_data.get('position', 'Unknown')}
            True Value: {player_data.get('true_value', 0):.1f} points
            ROI: {player_data.get('roi', 0):.2f} points per £1M
            Form Multiplier: {player_data.get('form_multiplier', 1.0):.2f}
            Recent Games: {player_data.get('recent_points', [])}
            
            Generate exactly 1-2 sentences explaining this player's current fantasy value.
            Focus on: form trend, value for money, and key factors affecting their score.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return None

# Usage in main app
def add_ai_insights(player_data):
    """Add Gemini insights to player data if available"""
    analyzer = GeminiAnalyzer()
    insight = analyzer.generate_player_insight(player_data)
    if insight:
        player_data['ai_insight'] = insight
    return player_data
```

### **Dashboard Updates Required**

**File**: `templates/dashboard.html`

Add new columns to player table:
```html
<!-- Add after existing columns -->
<th data-column="true_value" class="sortable">
    True Value
    <span class="tooltip">Pure point prediction (no price factor)</span>
</th>
<th data-column="roi" class="sortable">
    ROI
    <span class="tooltip">Points per £1M spent</span>
</th>
```

### **Testing & Validation**

**Create**: `test_sprint1_changes.py`

```python
def test_formula_separation():
    """Test that True Value and ROI are correctly separated"""
    # Test case: Expensive player with high prediction
    haaland = {
        'ppg': 8.5,
        'price': 15.0,
        'form_multiplier': 1.2,
        'fixture_multiplier': 1.1,
        'starter_multiplier': 1.0,
        'xgi_multiplier': 1.3
    }
    
    result = calculate_true_value_components(haaland, default_params)
    
    # True Value should be high (good prediction)
    assert result['true_value'] > 10.0
    
    # ROI should be lower due to high price
    assert result['roi'] < 1.0
    
    print("✅ Formula separation working correctly")

def test_exponential_fixture():
    """Test exponential fixture calculation"""
    test_cases = [
        {'difficulty': -5, 'expected_range': (1.2, 1.3)},  # Easy fixture
        {'difficulty': 0, 'expected_range': (0.95, 1.05)}, # Neutral
        {'difficulty': 5, 'expected_range': (0.7, 0.85)}   # Hard fixture
    ]
    
    for case in test_cases:
        result = calculate_fixture_multiplier(
            {'fixture_difficulty': case['difficulty'], 'position': 'M'},
            {'fixture_exponential': {'base': 1.05}}
        )
        assert case['expected_range'][0] <= result <= case['expected_range'][1]
    
    print("✅ Exponential fixture calculation working correctly")
```

### **Success Metrics**
- [ ] True Value calculated without price factor
- [ ] ROI displayed as separate metric
- [ ] Fixture multiplier uses exponential transformation
- [ ] All multipliers respect caps
- [ ] Gemini API integration functional
- [ ] Dashboard displays new columns
- [ ] Tests pass for core changes

### **Sprint 1 Completion Checklist**
- [ ] `src/app.py` updated with new calculation logic
- [ ] Database migration script created and run
- [ ] Configuration parameters added
- [ ] Gemini integration setup
- [ ] Dashboard HTML updated
- [ ] Test suite created and passing
- [ ] Documentation updated

---

## **SPRINT 2: Advanced Calculations**
*Duration: 1 session (3-4 hours)*
*Priority: HIGH - Major accuracy improvements*

### **Objectives**
1. ✅ Implement exponential decay form model (EWMA)
2. ✅ Add dynamic data blending system
3. ✅ Normalize xGI multiplier around 1.0
4. ⏸️ **DEFERRED**: Enhance Gemini with pattern recognition (moved to Sprint 5)

### **Implementation Results**
- **EWMA Form Calculation**: Implemented exponential weighted moving average with configurable α=0.87
- **Dynamic Blending**: Smooth transition formula w_current = min(1, (N-1)/(K-1)) with K=16 default
- **Normalized xGI**: Ratio-based calculation (Recent_xGI/Historical_Baseline) with position adjustments
- **Enhanced Metadata**: Added blending_info, feature_flags, and caps_applied tracking
- **Sprint 2 Features**: All three core objectives implemented in FormulaEngineV2
- **API Integration**: v2.0 endpoints functional with Sprint 2 features
- **Testing**: calculation_engine_v2.py test passing with new features
- **Foundation for Sprint 3**: Validation framework ready to build on Sprint 2 enhancements

### **Research Foundation**

**Exponential Decay Formula**: `F_N = α × F_(N-1) + (1-α) × P_(N-1)`
- α = 0.87 for 5-game half-life
- More recent games weighted exponentially higher
- Theoretically superior to fixed weights

**Dynamic Blending Formula**: `w_current = min(1, (N-1)/(K-1))`
- Smooth transition from historical to current season data
- No more hard cutoffs at GW10/GW15
- K = 16 for full adaptation gameweek

### **Tasks**

#### **2.1 Exponential Decay Form Model**

**Research Reference**: Section 2.1 - "Implementing an Exponential Decay Model"

**File**: `src/app.py` - Replace existing form calculation

**Current Implementation**:
```python
def calculate_form_multiplier(player_id, current_gameweek, lookback_period=3):
    # Fixed weights: [0.5, 0.3, 0.2] for 3 games or [0.4, 0.25, 0.2, 0.1, 0.05] for 5
```

**New Implementation**:
```python
def calculate_exponential_form_multiplier(player_data, params):
    """
    Exponential Weighted Moving Average (EWMA) form calculation
    Research formula: F_N = α × F_(N-1) + (1-α) × P_(N-1)
    """
    recent_games = player_data.get('recent_points', [])
    alpha = params.get('exponential_decay', {}).get('alpha', 0.87)
    
    if not recent_games:
        return 1.0
    
    # Method 1: Direct weight calculation (easier to understand)
    def calculate_ewma_weights(num_games, alpha):
        """Generate exponential decay weights"""
        weights = [alpha ** i for i in range(num_games)]
        # Normalize so weights sum to 1
        total = sum(weights)
        return [w / total for w in weights]
    
    # Calculate weighted average
    weights = calculate_ewma_weights(len(recent_games), alpha)
    form_score = sum(points * weight for points, weight in zip(recent_games, weights))
    
    # Get baseline for normalization (will be enhanced with blending)
    baseline_ppg = get_baseline_ppg(player_data['player_id'], params)
    
    if baseline_ppg > 0:
        form_multiplier = form_score / baseline_ppg
    else:
        form_multiplier = 1.0
    
    # Apply cap
    cap = params.get('multiplier_caps', {}).get('form', 2.0)
    return max(0.5, min(cap, form_multiplier))

def calculate_recursive_form(player_id, new_points, params):
    """
    Alternative: Recursive EWMA (more efficient for ongoing tracking)
    F_N = α × F_(N-1) + (1-α) × P_(N-1)
    """
    alpha = params.get('exponential_decay', {}).get('alpha', 0.87)
    
    # Get previous form score from database
    previous_form = get_stored_form_score(player_id)
    
    if previous_form is None:
        # First calculation
        return new_points
    
    # Recursive formula
    new_form = alpha * previous_form + (1 - alpha) * new_points
    
    # Store for next calculation
    store_form_score(player_id, new_form)
    
    return new_form
```

**Configuration Update**:
```json
{
  "exponential_decay": {
    "description": "EWMA form calculation parameters",
    "enabled": true,
    "alpha": 0.87,
    "alpha_range": [0.70, 0.995],
    "interpretation": {
      "0.70": "Highly reactive (2-game focus)",
      "0.87": "5-game half-life (recommended)",
      "0.95": "Sticky form (10-game influence)"
    }
  }
}
```

#### **2.2 Dynamic Data Blending System**

**Research Reference**: Section IV - "A Strategy for Seasonal Adaptation"

**Current Problem**: Hard cutoffs create jarring transitions
- GW 1-10: Only historical data
- GW 11-15: Blend display only
- GW 16+: Only current data

**New Approach**: Smooth mathematical blending

```python
def calculate_blended_baseline(player_id, current_gameweek, params):
    """
    Dynamic blending of historical and current season data
    Research formula: w_current = min(1, (N-1)/(K-1))
    """
    K = params.get('dynamic_blending', {}).get('full_adaptation_gw', 16)
    
    # Calculate blending weights
    if current_gameweek <= 1:
        w_current, w_historical = 0.0, 1.0
    else:
        w_current = min(1.0, (current_gameweek - 1) / (K - 1))
        w_historical = 1.0 - w_current
    
    # Get data sources
    historical_ppg = get_historical_ppg(player_id)  # Previous season
    current_ppg = get_current_season_ppg(player_id, current_gameweek)
    
    # Handle edge cases
    if current_ppg == 0 and current_gameweek <= 3:
        # Not enough current data, use historical
        return historical_ppg, 0.0, 1.0
    
    if historical_ppg == 0:
        # No historical data (new player), use current
        return current_ppg, 1.0, 0.0
    
    # Smooth blending
    blended_ppg = w_current * current_ppg + w_historical * historical_ppg
    
    return blended_ppg, w_current, w_historical

def calculate_blended_xgi_baseline(player_id, current_gameweek, params):
    """Apply same blending logic to xGI baseline"""
    K = params.get('dynamic_blending', {}).get('full_adaptation_gw', 16)
    
    w_current = min(1.0, (current_gameweek - 1) / (K - 1)) if current_gameweek > 1 else 0.0
    w_historical = 1.0 - w_current
    
    historical_xgi = get_historical_xgi_per90(player_id)
    current_xgi = get_current_season_xgi_per90(player_id, current_gameweek)
    
    if historical_xgi and current_xgi:
        return w_current * current_xgi + w_historical * historical_xgi
    elif historical_xgi:
        return historical_xgi
    elif current_xgi:
        return current_xgi
    else:
        return 0.3  # Default for players without data
```

#### **2.3 xGI Normalization**

**Research Reference**: Section 2.4 - "The xGI Multiplier: Contextual Normalization"

**Current Problem**: Raw xGI values (0.0-1.2) used directly as multipliers, breaking scale consistency

**New Approach**: Ratio-based normalization around 1.0

```python
def calculate_normalized_xgi_multiplier(player_data, params):
    """
    Normalize xGI as ratio to baseline
    Research: xGI_Multiplier = Recent_xGI_per90 / Historical_Baseline_xGI_per90
    """
    recent_xgi_per90 = player_data.get('xgi_per90', 0.3)
    player_id = player_data.get('player_id')
    current_gameweek = params.get('current_gameweek', 1)
    
    # Get blended baseline using dynamic blending
    baseline_xgi = calculate_blended_xgi_baseline(player_id, current_gameweek, params)
    
    # Calculate ratio-based multiplier
    if baseline_xgi > 0.1:  # Avoid division by very small numbers
        xgi_multiplier = recent_xgi_per90 / baseline_xgi
    else:
        # For defenders or players without meaningful xGI
        xgi_multiplier = 1.0
    
    # Apply position-specific logic
    position = player_data.get('position', 'M')
    if position == 'G':
        # Goalkeepers - xGI not relevant
        return 1.0
    elif position == 'D' and baseline_xgi < 0.2:
        # Defensive players with low xGI - use minimal impact
        return 1.0 + (xgi_multiplier - 1.0) * 0.3  # 30% impact
    
    # Apply cap
    cap = params.get('multiplier_caps', {}).get('xgi', 2.5)
    return max(0.5, min(cap, xgi_multiplier))

def store_xgi_baselines():
    """One-time calculation to populate baseline xGI for all players"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate historical baseline for each player
    cursor.execute("""
        UPDATE players 
        SET baseline_xgi = (
            SELECT AVG(xgi_per90) 
            FROM historical_stats 
            WHERE historical_stats.player_id = players.player_id
            AND season = '2023-24'
        )
        WHERE baseline_xgi IS NULL
    """)
    
    conn.commit()
    print(f"Updated baseline xGI for {cursor.rowcount} players")
```

#### **2.4 Enhanced Gemini Pattern Recognition**

**File**: `src/gemini_integration.py` - Add advanced analysis

```python
def analyze_form_patterns(self, player_data: Dict) -> Optional[str]:
    """Use Gemini to identify form trends and patterns"""
    if not self.enabled:
        return None
    
    try:
        recent_points = player_data.get('recent_points', [])
        if len(recent_points) < 3:
            return None
        
        prompt = f"""
        Analyze this player's recent performance pattern:
        
        Player: {player_data.get('name')}
        Position: {player_data.get('position')}
        Last 5 games points: {recent_points}
        xGI trend: {player_data.get('xgi_trend', 'stable')}
        Form multiplier: {player_data.get('form_multiplier', 1.0):.2f}
        
        Identify in exactly 2 sentences:
        1. Form trajectory (improving/declining/stable)
        2. Key pattern or concern (consistency, fixtures, role change)
        
        Examples:
        - "Form trending upward with 3 double-digit scores in last 4 games. High xGI suggests underlying performance supports current returns."
        - "Inconsistent returns despite favorable fixtures suggest rotation risk. Consider downgrading until starting role clarified."
        """
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Form pattern analysis error: {e}")
        return None

def detect_value_opportunities(self, top_players: List[Dict]) -> Optional[str]:
    """Identify hidden value players using AI analysis"""
    if not self.enabled or len(top_players) < 10:
        return None
    
    try:
        # Format player data for analysis
        player_summary = []
        for p in top_players[:20]:
            player_summary.append(
                f"{p['name']} ({p['position']}): "
                f"True Value {p['true_value']:.1f}, "
                f"ROI {p['roi']:.2f}, "
                f"Ownership {p.get('ownership', 'unknown')}%"
            )
        
        prompt = f"""
        Identify 3 differential/value opportunities from these players:
        
        {chr(10).join(player_summary)}
        
        Find players who are:
        1. High True Value but low ownership (differentials)
        2. Excellent ROI in good form (value picks)
        3. About to rise in value due to fixtures/form
        
        Format as 3 bullet points, each with player name and 1-sentence reasoning.
        """
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Value opportunity analysis error: {e}")
        return None
```

### **Database Updates**

**File**: `migrations/sprint2_advanced_calcs.sql`

```sql
-- Add columns for exponential form tracking
ALTER TABLE players ADD COLUMN IF NOT EXISTS exponential_form_score DECIMAL(5,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS baseline_xgi DECIMAL(5,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS blended_ppg DECIMAL(5,2);
ALTER TABLE players ADD COLUMN IF NOT EXISTS current_weight DECIMAL(4,3);

-- Create table for form score history (for recursive EWMA)
CREATE TABLE IF NOT EXISTS form_scores (
    player_id VARCHAR(50),
    gameweek INTEGER,
    exponential_score DECIMAL(5,3),
    alpha_used DECIMAL(4,3),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, gameweek)
);

-- Comments
COMMENT ON COLUMN players.exponential_form_score IS 'EWMA form score';
COMMENT ON COLUMN players.baseline_xgi IS 'Historical xGI baseline for normalization';
COMMENT ON COLUMN players.blended_ppg IS 'Dynamically blended PPG (historical + current)';
COMMENT ON COLUMN players.current_weight IS 'Current season weight in blending (0-1)';
```

### **Configuration Updates**

**File**: `config/system_parameters.json` - Add Sprint 2 parameters

```json
{
  "dynamic_blending": {
    "description": "Smooth transition between historical and current season data",
    "enabled": true,
    "full_adaptation_gw": 16,
    "adaptation_range": [10, 25],
    "show_blend_indicator": true
  },
  "xgi_normalization": {
    "description": "Normalize xGI as ratio to baseline",
    "enabled": true,
    "position_adjustments": {
      "G": 0.0,
      "D": 0.3,
      "M": 1.0,
      "F": 1.0
    },
    "minimum_baseline": 0.1
  }
}
```

### **Dashboard Updates**

**File**: `templates/dashboard.html` - Add blending indicator

```html
<!-- Add blending status indicator -->
<div class="blending-indicator">
    <span id="blend-status">GW{{current_gw}}: 
        <span id="blend-weights">{{current_weight|round(2)}} current / {{historical_weight|round(2)}} historical</span>
    </span>
    <div class="tooltip">
        Dynamic blending: smooth transition from historical to current season data
    </div>
</div>

<!-- Add advanced parameter controls -->
<div class="parameter-group">
    <label for="alpha-slider">Form Decay (α): <span id="alpha-value">0.87</span></label>
    <input type="range" id="alpha-slider" min="0.70" max="0.995" step="0.005" value="0.87">
    <small>Half-life: <span id="half-life-display">5 games</span></small>
</div>

<div class="parameter-group">
    <label for="adaptation-gw-slider">Full Adaptation GW: <span id="adaptation-value">16</span></label>
    <input type="range" id="adaptation-gw-slider" min="10" max="25" step="1" value="16">
    <small>When to fully trust current season data</small>
</div>
```

### **Sprint 2 Testing**

**File**: `test_sprint2_advanced.py`

```python
def test_exponential_decay():
    """Test EWMA calculation vs fixed weights"""
    recent_games = [12, 8, 15, 6, 10]  # Most recent first
    
    # Old method (fixed weights)
    old_weights = [0.4, 0.25, 0.2, 0.1, 0.05]
    old_avg = sum(p * w for p, w in zip(recent_games, old_weights))
    
    # New method (exponential decay)
    alpha = 0.87
    new_weights = [alpha ** i for i in range(5)]
    new_weights = [w / sum(new_weights) for w in new_weights]
    new_avg = sum(p * w for p, w in zip(recent_games, new_weights))
    
    print(f"Old avg: {old_avg:.2f}, New avg: {new_avg:.2f}")
    assert abs(new_avg - old_avg) < 5  # Should be similar but not identical
    
def test_dynamic_blending():
    """Test smooth blending vs hard cutoffs"""
    test_cases = [
        (1, 0.0, 1.0),    # GW1: 0% current, 100% historical
        (8, 0.44, 0.56),  # GW8: 44% current, 56% historical  
        (16, 1.0, 0.0),   # GW16: 100% current, 0% historical
        (25, 1.0, 0.0)    # GW25: Still 100% current
    ]
    
    for gw, expected_current, expected_historical in test_cases:
        current, historical = calculate_blending_weights(gw, K=16)
        assert abs(current - expected_current) < 0.01
        assert abs(historical - expected_historical) < 0.01
    
    print("✅ Dynamic blending weights correct")

def test_xgi_normalization():
    """Test xGI ratio calculation"""
    test_player = {
        'xgi_per90': 0.6,
        'position': 'F',
        'player_id': 'test_player'
    }
    
    # Mock baseline
    baseline = 0.5
    expected_multiplier = 0.6 / 0.5  # = 1.2
    
    # Should be close to 1.2 (20% above baseline)
    result = calculate_normalized_xgi_multiplier(test_player, {})
    assert 1.1 <= result <= 1.3
    
    print("✅ xGI normalization working correctly")
```

### **Success Metrics Sprint 2**
- [ ] Exponential decay form implemented with configurable α
- [ ] Dynamic blending replaces hard cutoffs
- [ ] xGI normalized around 1.0 as ratio to baseline
- [ ] Blending indicator shows current/historical weights
- [ ] Parameter sliders functional
- [ ] Gemini pattern recognition working
- [ ] All calculations maintain sub-3 second performance

---

## **SPRINT 3: Validation & Backtesting Framework**
*Duration: 1 session (3-4 hours)*
*Priority: HIGH - Ensures accuracy and provides optimization data*

### **Objectives**
1. ✅ Build comprehensive backtesting system
2. ✅ Calculate validation metrics (RMSE, MAE, Spearman)
3. ✅ Parameter optimization through grid search
4. ✅ Use Gemini for anomaly detection and insights

### **Research Foundation**

**Validation Metrics** from research screenshots:
- **RMSE**: `√[(1/n) × Σ(Predicted_i - Actual_i)²]` - Penalizes large errors heavily
- **MAE**: `(1/n) × Σ|Predicted_i - Actual_i|` - Average absolute error, easier to interpret
- **Spearman Correlation**: Rank-based correlation for player ordering accuracy
- **Precision@K**: Hit rate for top-K player recommendations

**Backtesting Protocol**: Strict gameweek-by-gameweek simulation using only data available before each prediction

### **Tasks**

#### **3.1 Core Backtesting Framework**

**File**: Create `src/backtesting.py`

```python
"""
Comprehensive backtesting framework for fantasy football predictions
Implements research-specified validation methodology
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from typing import Dict, List, Tuple, Optional
import psycopg2
from datetime import datetime

class FantasyBacktester:
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.results = []
        
    def run_season_backtest(self, season: str = '2023-24', model_version: str = 'v2.0') -> Dict:
        """
        Run complete season backtest using historical data
        
        Critical: Only use data that would have been available BEFORE each gameweek
        This prevents lookahead bias which would inflate accuracy metrics
        """
        print(f"Starting backtest for {season} using model {model_version}")
        
        all_predictions = []
        all_actuals = []
        gameweek_results = []
        
        for gameweek in range(1, 39):  # Premier League has 38 gameweeks
            print(f"Backtesting GW{gameweek}...")
            
            # Get data as it existed BEFORE this gameweek's deadline
            historical_data = self._get_data_before_gameweek(season, gameweek)
            
            if not historical_data:
                continue
                
            # Generate predictions using only past data
            gw_predictions = []
            gw_actuals = []
            
            for player_data in historical_data:
                # Calculate prediction with historical parameters
                prediction = self._calculate_historical_prediction(
                    player_data, gameweek, model_version
                )
                
                # Get actual points scored in this gameweek
                actual = self._get_actual_points(
                    player_data['player_id'], gameweek, season
                )
                
                if actual is not None:
                    gw_predictions.append(prediction)
                    gw_actuals.append(actual)
                    
                    # Store individual prediction for analysis
                    self._store_prediction(
                        player_data['player_id'], gameweek, 
                        prediction, actual, model_version
                    )
            
            # Calculate gameweek metrics
            if len(gw_predictions) >= 10:  # Minimum players for meaningful metrics
                gw_metrics = self._calculate_metrics(gw_predictions, gw_actuals)
                gw_metrics['gameweek'] = gameweek
                gameweek_results.append(gw_metrics)
                
                all_predictions.extend(gw_predictions)
                all_actuals.extend(gw_actuals)
        
        # Calculate overall season metrics
        overall_metrics = self._calculate_metrics(all_predictions, all_actuals)
        overall_metrics.update({
            'season': season,
            'model_version': model_version,
            'total_predictions': len(all_predictions),
            'gameweek_breakdown': gameweek_results
        })
        
        # Store results
        self._store_validation_results(overall_metrics)
        
        return overall_metrics
    
    def _get_data_before_gameweek(self, season: str, gameweek: int) -> List[Dict]:
        """
        Get all data that would have been available before a specific gameweek
        This is critical for preventing lookahead bias
        """
        conn = psycopg2.connect(**self.db_config)
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get player data as it existed before this gameweek
            cursor.execute("""
                SELECT 
                    p.player_id,
                    p.name,
                    p.position,
                    p.team,
                    p.price,
                    -- Historical PPG (previous season)
                    COALESCE(hs.ppg, 0) as historical_ppg,
                    -- Current season PPG up to (not including) this gameweek
                    COALESCE(
                        (SELECT AVG(points) 
                         FROM player_form pf 
                         WHERE pf.player_id = p.player_id 
                         AND pf.gameweek < %s), 0
                    ) as current_ppg,
                    -- Recent form (last 5 games before this gameweek)
                    ARRAY(
                        SELECT points 
                        FROM player_form pf 
                        WHERE pf.player_id = p.player_id 
                        AND pf.gameweek < %s 
                        ORDER BY pf.gameweek DESC 
                        LIMIT 5
                    ) as recent_points,
                    -- Fixture difficulty for this gameweek
                    COALESCE(tf.difficulty_score, 0) as fixture_difficulty,
                    -- xGI data available before this gameweek
                    COALESCE(x.xgi_per90, 0.3) as xgi_per90,
                    COALESCE(x.baseline_xgi, 0.3) as baseline_xgi
                FROM players p
                LEFT JOIN historical_stats hs ON p.player_id = hs.player_id
                LEFT JOIN team_fixtures tf ON p.team_code = tf.team_code AND tf.gameweek = %s
                LEFT JOIN xgi_stats x ON p.player_id = x.player_id
                WHERE p.active = true
            """, [gameweek, gameweek, gameweek])
            
            return cursor.fetchall()
            
        finally:
            conn.close()
    
    def _calculate_historical_prediction(self, player_data: Dict, gameweek: int, model_version: str) -> float:
        """
        Calculate prediction using the formula as it would have been applied historically
        """
        # Use parameters that would have been in effect for this gameweek
        params = self._get_historical_parameters(gameweek, model_version)
        
        # Calculate blended PPG baseline
        blended_ppg = self._calculate_blended_ppg_historical(player_data, gameweek, params)
        
        # Calculate multipliers
        form_mult = self._calculate_form_multiplier_historical(player_data, params)
        fixture_mult = self._calculate_fixture_multiplier_historical(player_data, params)
        starter_mult = player_data.get('starter_multiplier', 1.0)  # Would come from predictions
        xgi_mult = self._calculate_xgi_multiplier_historical(player_data, params)
        
        # True Value calculation
        true_value = blended_ppg * form_mult * fixture_mult * starter_mult * xgi_mult
        
        # Apply global cap
        max_allowed = blended_ppg * params.get('global_multiplier_cap', 3.0)
        return min(true_value, max_allowed)
    
    def _calculate_metrics(self, predictions: List[float], actuals: List[float]) -> Dict:
        """
        Calculate all validation metrics from research
        """
        pred_array = np.array(predictions)
        actual_array = np.array(actuals)
        
        # RMSE: Root Mean Squared Error
        rmse = np.sqrt(np.mean((pred_array - actual_array) ** 2))
        
        # MAE: Mean Absolute Error
        mae = np.mean(np.abs(pred_array - actual_array))
        
        # Spearman Rank Correlation
        spearman_corr, spearman_p = spearmanr(predictions, actuals)
        
        # Precision@K (K=20 for top premium assets)
        precision_20 = self._calculate_precision_at_k(predictions, actuals, k=20)
        
        # Additional useful metrics
        mape = np.mean(np.abs((actual_array - pred_array) / np.maximum(actual_array, 0.1))) * 100
        r_squared = np.corrcoef(predictions, actuals)[0, 1] ** 2 if len(predictions) > 1 else 0
        
        return {
            'rmse': round(rmse, 3),
            'mae': round(mae, 3),
            'spearman_correlation': round(spearman_corr, 3),
            'spearman_p_value': round(spearman_p, 4),
            'precision_at_20': round(precision_20, 3),
            'mape': round(mape, 2),
            'r_squared': round(r_squared, 3),
            'n_predictions': len(predictions)
        }
    
    def _calculate_precision_at_k(self, predictions: List[float], actuals: List[float], k: int = 20) -> float:
        """
        Calculate Precision@K: Of top-K predicted players, how many were actually top-K?
        """
        if len(predictions) < k:
            return 0.0
        
        # Get indices of top-K predictions
        pred_top_k = np.argsort(predictions)[-k:]
        
        # Get indices of top-K actual performers
        actual_top_k = np.argsort(actuals)[-k:]
        
        # Calculate intersection
        intersection = len(set(pred_top_k) & set(actual_top_k))
        
        return intersection / k
    
    def _store_prediction(self, player_id: str, gameweek: int, predicted: float, actual: float, model_version: str):
        """Store individual prediction for detailed analysis"""
        conn = psycopg2.connect(**self.db_config)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO player_predictions 
                (player_id, gameweek, predicted_value, actual_points, model_version, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_id, gameweek, model_version) 
                DO UPDATE SET 
                    predicted_value = EXCLUDED.predicted_value,
                    actual_points = EXCLUDED.actual_points,
                    created_at = EXCLUDED.created_at
            """, [player_id, gameweek, predicted, actual, model_version, datetime.now()])
            conn.commit()
        finally:
            conn.close()
```

#### **3.2 Parameter Optimization Grid Search**

```python
class ParameterOptimizer:
    def __init__(self, backtester: FantasyBacktester):
        self.backtester = backtester
        
    def optimize_parameters(self, season: str = '2023-24') -> Dict:
        """
        Grid search to find optimal parameters
        Tests combinations of key parameters to minimize RMSE
        """
        # Define parameter grid from research
        param_grid = {
            'alpha': [0.80, 0.85, 0.87, 0.90, 0.95],              # Form decay
            'fixture_base': [1.03, 1.05, 1.07, 1.10],           # Fixture exponential base
            'adaptation_gw': [12, 14, 16, 18, 20],               # Blending full adaptation
            'form_cap': [1.8, 2.0, 2.2],                        # Form multiplier cap
            'xgi_cap': [2.0, 2.5, 3.0]                          # xGI multiplier cap
        }
        
        best_rmse = float('inf')
        best_params = {}
        results = []
        
        # Test subset of combinations (full grid would be 5*4*5*3*3 = 900 combinations)
        test_combinations = self._generate_test_combinations(param_grid, max_tests=50)
        
        for i, params in enumerate(test_combinations):
            print(f"Testing combination {i+1}/{len(test_combinations)}: {params}")
            
            # Run backtest with these parameters
            metrics = self.backtester.run_parameter_test(season, params)
            
            results.append({
                'params': params.copy(),
                'metrics': metrics
            })
            
            # Track best RMSE
            if metrics['rmse'] < best_rmse:
                best_rmse = metrics['rmse']
                best_params = params.copy()
                print(f"New best RMSE: {best_rmse:.3f}")
        
        # Store optimization results
        self._store_optimization_results(results)
        
        return {
            'best_params': best_params,
            'best_rmse': best_rmse,
            'all_results': results
        }
    
    def _generate_test_combinations(self, param_grid: Dict, max_tests: int = 50) -> List[Dict]:
        """Generate smart subset of parameter combinations to test"""
        import itertools
        import random
        
        # Start with baseline (research-recommended values)
        baseline = {
            'alpha': 0.87,
            'fixture_base': 1.05,
            'adaptation_gw': 16,
            'form_cap': 2.0,
            'xgi_cap': 2.5
        }
        
        combinations = [baseline]
        
        # Add systematic variations
        for param_name, values in param_grid.items():
            for value in values:
                if value != baseline[param_name]:
                    variant = baseline.copy()
                    variant[param_name] = value
                    combinations.append(variant)
        
        # Add some random combinations
        all_keys = list(param_grid.keys())
        for _ in range(max_tests - len(combinations)):
            random_combo = {}
            for key in all_keys:
                random_combo[key] = random.choice(param_grid[key])
            combinations.append(random_combo)
        
        return combinations[:max_tests]
```

#### **3.3 Gemini-Powered Anomaly Detection**

```python
def analyze_prediction_failures(self, min_error_threshold: float = 8.0) -> Optional[str]:
    """
    Use Gemini to analyze why certain predictions failed badly
    """
    if not self.enabled:
        return None
    
    # Get worst prediction errors from database
    conn = psycopg2.connect(**self.db_config)
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT 
                pp.player_id,
                p.name,
                p.position,
                pp.gameweek,
                pp.predicted_value,
                pp.actual_points,
                ABS(pp.predicted_value - pp.actual_points) as error,
                pp.predicted_value - pp.actual_points as signed_error
            FROM player_predictions pp
            JOIN players p ON pp.player_id = p.player_id
            WHERE ABS(pp.predicted_value - pp.actual_points) >= %s
            ORDER BY error DESC
            LIMIT 20
        """, [min_error_threshold])
        
        failures = cursor.fetchall()
        
    finally:
        conn.close()
    
    if not failures:
        return None
    
    # Format for Gemini analysis
    failure_summary = []
    for f in failures:
        failure_summary.append(
            f"GW{f['gameweek']}: {f['name']} ({f['position']}) - "
            f"Predicted {f['predicted_value']:.1f}, "
            f"Actual {f['actual_points']}, "
            f"Error {f['signed_error']:+.1f}"
        )
    
    prompt = f"""
    Analyze these worst prediction failures to identify systematic issues:
    
    {chr(10).join(failure_summary)}
    
    Identify patterns in:
    1. Common failure modes (over-prediction vs under-prediction)
    2. Position-specific issues (are forwards/defenders predicted worse?)
    3. Situational factors (early season, fixture difficulty, rotation)
    4. Suggested parameter adjustments
    
    Provide 3-4 actionable insights for model improvement.
    """
    
    try:
        response = self.model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Failure analysis error: {e}")
        return None

def generate_validation_insights(self, metrics: Dict) -> Optional[str]:
    """Generate AI insights about model performance"""
    if not self.enabled:
        return None
    
    prompt = f"""
    Analyze these fantasy football prediction model validation results:
    
    RMSE: {metrics['rmse']:.3f}
    MAE: {metrics['mae']:.3f}
    Spearman Correlation: {metrics['spearman_correlation']:.3f}
    Precision@20: {metrics['precision_at_20']:.3f}
    R²: {metrics['r_squared']:.3f}
    
    Industry benchmarks:
    - Good RMSE: < 3.0
    - Good Spearman: > 0.25
    - Good Precision@20: > 0.30
    
    Provide:
    1. Overall performance assessment
    2. Strongest/weakest aspects
    3. Comparison to benchmarks
    4. Priority improvements needed
    
    Keep response to 3-4 sentences.
    """
    
    try:
        response = self.model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Validation insights error: {e}")
        return None
```

#### **3.4 Database Schema for Validation**

**File**: `migrations/sprint3_validation.sql`

```sql
-- Table for storing individual predictions
CREATE TABLE IF NOT EXISTS player_predictions (
    player_id VARCHAR(50),
    gameweek INTEGER,
    predicted_value DECIMAL(8,2),
    actual_points DECIMAL(5,2),
    model_version VARCHAR(50),
    error_abs DECIMAL(8,2) GENERATED ALWAYS AS (ABS(predicted_value - actual_points)) STORED,
    error_signed DECIMAL(8,2) GENERATED ALWAYS AS (predicted_value - actual_points) STORED,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, gameweek, model_version)
);

-- Table for storing validation results
CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50),
    season VARCHAR(10),
    rmse DECIMAL(5,3),
    mae DECIMAL(5,3),
    spearman_correlation DECIMAL(5,3),
    spearman_p_value DECIMAL(6,4),
    precision_at_20 DECIMAL(5,3),
    r_squared DECIMAL(5,3),
    n_predictions INTEGER,
    test_date TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Table for parameter optimization results
CREATE TABLE IF NOT EXISTS parameter_optimization (
    id SERIAL PRIMARY KEY,
    test_date TIMESTAMP DEFAULT NOW(),
    parameters JSONB,
    rmse DECIMAL(5,3),
    mae DECIMAL(5,3),
    spearman_correlation DECIMAL(5,3),
    precision_at_20 DECIMAL(5,3),
    season_tested VARCHAR(10),
    notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_error ON player_predictions(error_abs DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_gameweek ON player_predictions(gameweek);
CREATE INDEX IF NOT EXISTS idx_validation_rmse ON validation_results(rmse);

-- Views for easy analysis
CREATE OR REPLACE VIEW worst_predictions AS
SELECT 
    pp.*,
    p.name,
    p.position,
    p.team
FROM player_predictions pp
JOIN players p ON pp.player_id = p.player_id
WHERE pp.error_abs >= 5.0
ORDER BY pp.error_abs DESC;

CREATE OR REPLACE VIEW model_comparison AS
SELECT 
    model_version,
    COUNT(*) as tests_run,
    AVG(rmse) as avg_rmse,
    AVG(mae) as avg_mae,
    AVG(spearman_correlation) as avg_spearman,
    AVG(precision_at_20) as avg_precision_20
FROM validation_results
GROUP BY model_version
ORDER BY avg_rmse;
```

#### **3.5 Validation Dashboard**

**File**: Create `templates/validation.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Model Validation Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="validation-container">
        <h1>Fantasy Football Model Validation</h1>
        
        <!-- Model Performance Summary -->
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>RMSE</h3>
                <div class="metric-value">{{ metrics.rmse }}</div>
                <div class="metric-target">Target: < 3.0</div>
            </div>
            
            <div class="metric-card">
                <h3>Spearman ρ</h3>
                <div class="metric-value">{{ metrics.spearman_correlation }}</div>
                <div class="metric-target">Target: > 0.25</div>
            </div>
            
            <div class="metric-card">
                <h3>Precision@20</h3>
                <div class="metric-value">{{ metrics.precision_at_20 }}</div>
                <div class="metric-target">Target: > 0.30</div>
            </div>
            
            <div class="metric-card">
                <h3>MAE</h3>
                <div class="metric-value">{{ metrics.mae }}</div>
                <div class="metric-target">Lower is better</div>
            </div>
        </div>
        
        <!-- Model Comparison Chart -->
        <div class="chart-container">
            <canvas id="model-comparison"></canvas>
        </div>
        
        <!-- Worst Predictions Analysis -->
        <div class="failures-section">
            <h3>Prediction Failures Analysis</h3>
            <div id="ai-failure-analysis">{{ ai_analysis }}</div>
            
            <table class="failures-table">
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>GW</th>
                        <th>Predicted</th>
                        <th>Actual</th>
                        <th>Error</th>
                    </tr>
                </thead>
                <tbody id="failures-list">
                    <!-- Populated by JavaScript -->
                </tbody>
            </table>
        </div>
        
        <!-- Parameter Optimization Results -->
        <div class="optimization-section">
            <h3>Parameter Optimization</h3>
            <div class="best-params">
                <h4>Optimal Parameters</h4>
                <pre>{{ best_params | tojsonpretty }}</pre>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize validation dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadModelComparison();
            loadFailuresAnalysis();
        });
        
        function loadModelComparison() {
            // Fetch and display model comparison chart
            fetch('/api/validation/model-comparison')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('model-comparison').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'RMSE',
                                data: data.rmse_values,
                                backgroundColor: 'rgba(54, 162, 235, 0.8)'
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'RMSE (Lower is Better)'
                                    }
                                }
                            }
                        }
                    });
                });
        }
    </script>
</body>
</html>
```

### **Sprint 3 API Endpoints**

**File**: `src/app.py` - Add validation endpoints

```python
@app.route('/validation')
def validation_dashboard():
    """Display validation dashboard"""
    # Get latest validation results
    metrics = get_latest_validation_metrics()
    
    # Get AI analysis of failures
    gemini = GeminiAnalyzer()
    ai_analysis = gemini.analyze_prediction_failures()
    
    # Get optimization results
    best_params = get_best_parameters()
    
    return render_template('validation.html', 
                         metrics=metrics,
                         ai_analysis=ai_analysis,
                         best_params=best_params)

@app.route('/api/validation/run-backtest')
def run_backtest_api():
    """Run full backtest and return results"""
    try:
        backtester = FantasyBacktester(DB_CONFIG)
        results = backtester.run_season_backtest('2023-24', 'v2.0')
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validation/optimize-parameters')
def optimize_parameters_api():
    """Run parameter optimization"""
    try:
        backtester = FantasyBacktester(DB_CONFIG)
        optimizer = ParameterOptimizer(backtester)
        results = optimizer.optimize_parameters('2023-24')
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validation/model-comparison')
def model_comparison_api():
    """Get model comparison data for charts"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT model_version, AVG(rmse) as avg_rmse, AVG(spearman_correlation) as avg_spearman
            FROM validation_results
            GROUP BY model_version
            ORDER BY avg_rmse
        """)
        
        results = cursor.fetchall()
        return jsonify({
            'labels': [r['model_version'] for r in results],
            'rmse_values': [float(r['avg_rmse']) for r in results],
            'spearman_values': [float(r['avg_spearman']) for r in results]
        })
    finally:
        conn.close()
```

### **Sprint 3 Success Metrics**
- [ ] Backtesting framework functional and tested
- [ ] RMSE < 2.85 achieved (research target)
- [ ] Spearman correlation > 0.30 achieved
- [ ] Parameter optimization identifies best values
- [ ] Validation dashboard displays metrics
- [ ] Gemini failure analysis providing insights
- [ ] Model comparison showing improvement over baseline

---

## **SPRINT 4: UI Integration & Polish**
*Duration: 1 session (2-3 hours)*
*Priority: MEDIUM - User experience and usability*

### **Objectives**
1. ✅ Update dashboard with new True Value and ROI columns
2. ✅ Add intuitive parameter control sliders
3. ✅ Create validation results viewer
4. ✅ Integrate Gemini insights into player display
5. ✅ Add visual indicators for data blending status

### **Tasks**

#### **4.1 Main Dashboard Updates**

**File**: `templates/dashboard.html` - Major UI enhancements

```html
<!-- Enhanced Header with Formula Version -->
<div class="dashboard-header">
    <h1>Fantrax Value Hunter 
        <span class="version-badge">v2.0</span>
        <span class="formula-indicator">Optimized Formula</span>
    </h1>
    
    <!-- Blending Status Indicator -->
    <div class="blending-status">
        <span id="blend-indicator">
            GW{{current_gameweek}}: 
            <span class="blend-weights">
                {{(current_weight*100)|round}}% current / {{(historical_weight*100)|round}}% historical
            </span>
        </span>
        <div class="tooltip">
            Dynamic blending: Smooth transition from historical to current season data.
            Full adaptation at GW{{adaptation_gameweek}}.
        </div>
    </div>
</div>

<!-- Enhanced Parameter Controls -->
<div class="parameter-controls-v2">
    <div class="control-section">
        <h3>Formula Parameters</h3>
        
        <!-- Form Decay Control -->
        <div class="parameter-group">
            <label for="alpha-slider">
                Form Decay (α): <span id="alpha-value">0.87</span>
                <span class="half-life">Half-life: <span id="half-life">5 games</span></span>
            </label>
            <input type="range" id="alpha-slider" 
                   min="0.70" max="0.995" step="0.005" value="0.87"
                   data-param="exponential_decay.alpha">
            <div class="param-description">
                Higher values = "sticky" form, Lower values = reactive to recent games
            </div>
        </div>
        
        <!-- Fixture Impact Control -->
        <div class="parameter-group">
            <label for="fixture-base-slider">
                Fixture Impact Base: <span id="fixture-base-value">1.05</span>
            </label>
            <input type="range" id="fixture-base-slider" 
                   min="1.02" max="1.10" step="0.01" value="1.05"
                   data-param="fixture_exponential.base">
            <div class="param-description">
                How much fixture difficulty affects predictions (1.02=minimal, 1.10=high impact)
            </div>
        </div>
        
        <!-- Adaptation Gameweek Control -->
        <div class="parameter-group">
            <label for="adaptation-gw-slider">
                Full Adaptation GW: <span id="adaptation-gw-value">16</span>
            </label>
            <input type="range" id="adaptation-gw-slider" 
                   min="10" max="25" step="1" value="16"
                   data-param="dynamic_blending.full_adaptation_gw">
            <div class="param-description">
                When to fully trust current season data over historical
            </div>
        </div>
        
        <!-- Multiplier Caps -->
        <div class="caps-section">
            <h4>Multiplier Caps <span class="info-icon" title="Prevent extreme outliers">ℹ</span></h4>
            <div class="caps-grid">
                <div class="cap-control">
                    <label>Form: <span id="form-cap-value">2.0</span></label>
                    <input type="range" id="form-cap-slider" min="1.5" max="3.0" step="0.1" value="2.0">
                </div>
                <div class="cap-control">
                    <label>Fixture: <span id="fixture-cap-value">1.8</span></label>
                    <input type="range" id="fixture-cap-slider" min="1.2" max="2.5" step="0.1" value="1.8">
                </div>
                <div class="cap-control">
                    <label>xGI: <span id="xgi-cap-value">2.5</span></label>
                    <input type="range" id="xgi-cap-slider" min="1.5" max="3.5" step="0.1" value="2.5">
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quick Presets -->
    <div class="presets-section">
        <h4>Quick Presets</h4>
        <button class="preset-btn" data-preset="conservative">Conservative</button>
        <button class="preset-btn" data-preset="balanced">Balanced (Default)</button>
        <button class="preset-btn" data-preset="aggressive">Aggressive</button>
    </div>
</div>

<!-- Enhanced Player Table -->
<table id="player-table" class="enhanced-table">
    <thead>
        <tr>
            <th data-column="name" class="sortable">Player</th>
            <th data-column="position" class="sortable">Pos</th>
            <th data-column="team" class="sortable">Team</th>
            <th data-column="price" class="sortable">Price</th>
            
            <!-- NEW: Separated Value Metrics -->
            <th data-column="true_value" class="sortable highlight-column">
                True Value
                <div class="tooltip">Pure point prediction (no price factor)</div>
            </th>
            <th data-column="roi" class="sortable highlight-column">
                ROI
                <div class="tooltip">Points per £1M spent</div>
            </th>
            
            <!-- Enhanced existing columns -->
            <th data-column="blended_ppg" class="sortable">
                Baseline PPG
                <div class="tooltip">Dynamically blended historical + current</div>
            </th>
            <th data-column="form_multiplier" class="sortable">
                Form
                <div class="tooltip">Exponential decay weighted recent performance</div>
            </th>
            <th data-column="fixture_multiplier" class="sortable">
                Fixture
                <div class="tooltip">Exponential difficulty transformation</div>
            </th>
            <th data-column="xgi_multiplier" class="sortable">
                xGI
                <div class="tooltip">Normalized to baseline ratio</div>
            </th>
            <th data-column="games_display" class="sortable">Games</th>
            
            <!-- NEW: AI Insights Column -->
            <th class="ai-insights-column">
                AI Insights
                <div class="tooltip">Gemini-powered analysis</div>
            </th>
        </tr>
    </thead>
    <tbody id="player-table-body">
        <!-- Enhanced row template with new columns -->
    </tbody>
</table>
```

#### **4.2 Enhanced JavaScript Controls**

**File**: `static/js/dashboard.js` - Add new parameter handling

```javascript
// Enhanced parameter management for v2.0 formula
class ParameterManager {
    constructor() {
        this.initializeControls();
        this.setupEventListeners();
        this.loadPresets();
    }
    
    initializeControls() {
        // Alpha slider with half-life calculation
        const alphaSlider = document.getElementById('alpha-slider');
        const halfLifeDisplay = document.getElementById('half-life');
        
        alphaSlider.addEventListener('input', (e) => {
            const alpha = parseFloat(e.target.value);
            const halfLife = this.calculateHalfLife(alpha);
            
            document.getElementById('alpha-value').textContent = alpha.toFixed(3);
            halfLifeDisplay.textContent = `${halfLife} games`;
            
            this.updateParameter('exponential_decay.alpha', alpha);
        });
        
        // Fixture base slider
        document.getElementById('fixture-base-slider').addEventListener('input', (e) => {
            const base = parseFloat(e.target.value);
            document.getElementById('fixture-base-value').textContent = base.toFixed(2);
            this.updateParameter('fixture_exponential.base', base);
        });
        
        // Adaptation gameweek slider
        document.getElementById('adaptation-gw-slider').addEventListener('input', (e) => {
            const gw = parseInt(e.target.value);
            document.getElementById('adaptation-gw-value').textContent = gw;
            this.updateParameter('dynamic_blending.full_adaptation_gw', gw);
            this.updateBlendingIndicator();
        });
        
        // Multiplier cap sliders
        ['form', 'fixture', 'xgi'].forEach(type => {
            const slider = document.getElementById(`${type}-cap-slider`);
            slider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                document.getElementById(`${type}-cap-value`).textContent = value.toFixed(1);
                this.updateParameter(`multiplier_caps.${type}`, value);
            });
        });
    }
    
    calculateHalfLife(alpha) {
        // Half-life formula: ln(0.5) / ln(alpha)
        return Math.round(Math.log(0.5) / Math.log(alpha));
    }
    
    updateParameter(paramPath, value) {
        // Debounced parameter update
        clearTimeout(this.updateTimeout);
        this.updateTimeout = setTimeout(() => {
            this.sendParameterUpdate(paramPath, value);
        }, 300);
    }
    
    sendParameterUpdate(paramPath, value) {
        const data = {};
        const keys = paramPath.split('.');
        let current = data;
        
        for (let i = 0; i < keys.length - 1; i++) {
            current[keys[i]] = {};
            current = current[keys[i]];
        }
        current[keys[keys.length - 1]] = value;
        
        fetch('/api/update-parameters', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.refreshPlayerTable();
                this.showParameterUpdate(paramPath, value);
            }
        });
    }
    
    loadPresets() {
        const presets = {
            conservative: {
                'exponential_decay.alpha': 0.95,
                'fixture_exponential.base': 1.03,
                'dynamic_blending.full_adaptation_gw': 20,
                'multiplier_caps.form': 1.8,
                'multiplier_caps.fixture': 1.5,
                'multiplier_caps.xgi': 2.0
            },
            balanced: {
                'exponential_decay.alpha': 0.87,
                'fixture_exponential.base': 1.05,
                'dynamic_blending.full_adaptation_gw': 16,
                'multiplier_caps.form': 2.0,
                'multiplier_caps.fixture': 1.8,
                'multiplier_caps.xgi': 2.5
            },
            aggressive: {
                'exponential_decay.alpha': 0.80,
                'fixture_exponential.base': 1.08,
                'dynamic_blending.full_adaptation_gw': 12,
                'multiplier_caps.form': 2.5,
                'multiplier_caps.fixture': 2.2,
                'multiplier_caps.xgi': 3.0
            }
        };
        
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const preset = e.target.dataset.preset;
                this.applyPreset(presets[preset]);
            });
        });
    }
    
    applyPreset(presetValues) {
        Object.entries(presetValues).forEach(([path, value]) => {
            this.setSliderValue(path, value);
            this.updateParameter(path, value);
        });
    }
    
    updateBlendingIndicator() {
        const currentGW = parseInt(document.getElementById('current-gameweek').value);
        const adaptationGW = parseInt(document.getElementById('adaptation-gw-value').textContent);
        
        const wCurrent = Math.min(1.0, (currentGW - 1) / (adaptationGW - 1));
        const wHistorical = 1.0 - wCurrent;
        
        document.querySelector('.blend-weights').innerHTML = 
            `${Math.round(wCurrent * 100)}% current / ${Math.round(wHistorical * 100)}% historical`;
    }
}

// Enhanced table rendering with new columns
class EnhancedTableRenderer {
    constructor() {
        this.initializeTable();
    }
    
    renderPlayerRow(player) {
        const aiInsight = player.ai_insight || '';
        const hasInsight = aiInsight.length > 0;
        
        return `
            <tr data-player-id="${player.player_id}">
                <td class="player-name">${player.name}</td>
                <td class="position">${player.position}</td>
                <td class="team">${player.team}</td>
                <td class="price">£${player.price}m</td>
                
                <!-- New separated value columns -->
                <td class="true-value highlight-value">
                    ${player.true_value.toFixed(1)}
                    <div class="value-breakdown" style="display: none;">
                        PPG: ${player.blended_ppg.toFixed(1)} × 
                        Form: ${player.multipliers.form.toFixed(2)} × 
                        Fixture: ${player.multipliers.fixture.toFixed(2)} × 
                        Starter: ${player.multipliers.starter.toFixed(2)} × 
                        xGI: ${player.multipliers.xgi.toFixed(2)}
                    </div>
                </td>
                <td class="roi highlight-value">
                    ${player.roi.toFixed(2)}
                    <span class="roi-indicator ${this.getRoiClass(player.roi)}"></span>
                </td>
                
                <!-- Enhanced existing columns -->
                <td class="blended-ppg">
                    ${player.blended_ppg.toFixed(1)}
                    <span class="blend-indicator" title="Current: ${player.current_weight.toFixed(2)}, Historical: ${(1-player.current_weight).toFixed(2)}">
                        ⚖️
                    </span>
                </td>
                <td class="form-multiplier ${this.getMultiplierClass(player.multipliers.form)}">
                    ${player.multipliers.form.toFixed(2)}
                </td>
                <td class="fixture-multiplier ${this.getMultiplierClass(player.multipliers.fixture)}">
                    ${player.multipliers.fixture.toFixed(2)}
                </td>
                <td class="xgi-multiplier ${this.getMultiplierClass(player.multipliers.xgi)}">
                    ${player.multipliers.xgi.toFixed(2)}
                </td>
                <td class="games">${player.games_display}</td>
                
                <!-- AI Insights column -->
                <td class="ai-insights">
                    ${hasInsight ? 
                        `<div class="insight-text">${aiInsight}</div>` : 
                        '<span class="no-insight">-</span>'
                    }
                    ${hasInsight ? '<span class="ai-badge">🤖</span>' : ''}
                </td>
            </tr>
        `;
    }
    
    getRoiClass(roi) {
        if (roi >= 1.0) return 'roi-excellent';
        if (roi >= 0.8) return 'roi-good';
        if (roi >= 0.6) return 'roi-average';
        return 'roi-poor';
    }
    
    getMultiplierClass(value) {
        if (value >= 1.3) return 'mult-high';
        if (value >= 1.1) return 'mult-good';
        if (value <= 0.8) return 'mult-low';
        return 'mult-neutral';
    }
}

// Initialize enhanced dashboard
document.addEventListener('DOMContentLoaded', function() {
    window.paramManager = new ParameterManager();
    window.tableRenderer = new EnhancedTableRenderer();
    
    // Add hover effects for value breakdown
    document.addEventListener('mouseover', function(e) {
        if (e.target.closest('.true-value')) {
            const breakdown = e.target.querySelector('.value-breakdown');
            if (breakdown) breakdown.style.display = 'block';
        }
    });
    
    document.addEventListener('mouseout', function(e) {
        if (e.target.closest('.true-value')) {
            const breakdown = e.target.querySelector('.value-breakdown');
            if (breakdown) breakdown.style.display = 'none';
        }
    });
});
```

#### **4.3 Enhanced CSS Styling**

**File**: `static/css/dashboard.css` - Add v2.0 styling

```css
/* Enhanced header styling */
.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
}

.version-badge {
    background: #4CAF50;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    margin-left: 10px;
}

.formula-indicator {
    background: #FF9800;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    margin-left: 5px;
}

/* Blending status indicator */
.blending-status {
    position: relative;
}

.blend-weights {
    font-weight: bold;
    color: #FFE0B2;
}

/* Enhanced parameter controls */
.parameter-controls-v2 {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    border: 1px solid #e9ecef;
}

.control-section h3 {
    color: #495057;
    margin-bottom: 15px;
    border-bottom: 2px solid #dee2e6;
    padding-bottom: 5px;
}

.parameter-group {
    margin-bottom: 20px;
    padding: 15px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.parameter-group label {
    display: block;
    font-weight: 600;
    margin-bottom: 8px;
    color: #343a40;
}

.half-life {
    font-size: 0.9em;
    color: #6c757d;
    margin-left: 10px;
}

.param-description {
    font-size: 0.85em;
    color: #6c757d;
    margin-top: 5px;
    font-style: italic;
}

/* Multiplier caps grid */
.caps-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 10px;
}

.cap-control {
    text-align: center;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 5px;
}

/* Preset buttons */
.presets-section {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #dee2e6;
}

.preset-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    margin-right: 10px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.preset-btn:hover {
    background: #0056b3;
}

/* Enhanced table styling */
.enhanced-table {
    border-collapse: collapse;
    width: 100%;
    background: white;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.highlight-column {
    background: #e3f2fd !important;
    font-weight: bold;
}

.highlight-value {
    background: #e8f5e8;
    font-weight: bold;
    font-size: 1.1em;
}

/* Value indicators */
.roi-excellent { color: #4CAF50; }
.roi-good { color: #8BC34A; }
.roi-average { color: #FF9800; }
.roi-poor { color: #f44336; }

.mult-high { background: #c8e6c9; color: #2e7d32; }
.mult-good { background: #dcedc8; color: #558b2f; }
.mult-neutral { background: #f5f5f5; color: #424242; }
.mult-low { background: #ffcdd2; color: #c62828; }

/* AI insights styling */
.ai-insights {
    max-width: 200px;
    position: relative;
}

.insight-text {
    font-size: 0.85em;
    line-height: 1.3;
    color: #495057;
    max-height: 60px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.ai-badge {
    position: absolute;
    top: 5px;
    right: 5px;
    font-size: 0.8em;
}

.no-insight {
    color: #adb5bd;
    font-style: italic;
}

/* Value breakdown tooltip */
.value-breakdown {
    position: absolute;
    background: #343a40;
    color: white;
    padding: 8px;
    border-radius: 4px;
    font-size: 0.8em;
    z-index: 1000;
    white-space: nowrap;
    top: 100%;
    left: 0;
    margin-top: 5px;
}

.blend-indicator {
    margin-left: 5px;
    opacity: 0.7;
    cursor: help;
}

/* Responsive design */
@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        gap: 10px;
    }
    
    .caps-grid {
        grid-template-columns: 1fr;
    }
    
    .ai-insights {
        display: none;
    }
}
```

#### **4.4 Validation Results Viewer**

**File**: Create `templates/validation_results.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Model Validation Results</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="validation-viewer">
        <h1>Model Validation Results</h1>
        
        <!-- Quick Summary Cards -->
        <div class="summary-cards">
            <div class="metric-card rmse">
                <h3>RMSE</h3>
                <div class="metric-value">{{ latest_metrics.rmse }}</div>
                <div class="metric-status {{ 'good' if latest_metrics.rmse < 3.0 else 'needs-work' }}">
                    {{ 'Excellent' if latest_metrics.rmse < 2.8 else 'Good' if latest_metrics.rmse < 3.0 else 'Needs Improvement' }}
                </div>
            </div>
            
            <div class="metric-card spearman">
                <h3>Spearman ρ</h3>
                <div class="metric-value">{{ latest_metrics.spearman_correlation }}</div>
                <div class="metric-status {{ 'good' if latest_metrics.spearman_correlation > 0.25 else 'needs-work' }}">
                    {{ 'Excellent' if latest_metrics.spearman_correlation > 0.35 else 'Good' if latest_metrics.spearman_correlation > 0.25 else 'Needs Improvement' }}
                </div>
            </div>
            
            <div class="metric-card precision">
                <h3>Precision@20</h3>
                <div class="metric-value">{{ latest_metrics.precision_at_20 }}</div>
                <div class="metric-status {{ 'good' if latest_metrics.precision_at_20 > 0.30 else 'needs-work' }}">
                    {{ 'Excellent' if latest_metrics.precision_at_20 > 0.40 else 'Good' if latest_metrics.precision_at_20 > 0.30 else 'Needs Improvement' }}
                </div>
            </div>
        </div>
        
        <!-- AI Analysis of Performance -->
        <div class="ai-analysis-section">
            <h3>🤖 AI Performance Analysis</h3>
            <div class="ai-insights">
                {{ ai_performance_analysis }}
            </div>
        </div>
        
        <!-- Model Evolution Chart -->
        <div class="chart-section">
            <h3>Model Performance Evolution</h3>
            <canvas id="performance-evolution"></canvas>
        </div>
        
        <!-- Parameter Impact Analysis -->
        <div class="parameter-impact">
            <h3>Parameter Impact on Performance</h3>
            <div id="parameter-analysis">
                <!-- Will be populated via JavaScript -->
            </div>
        </div>
        
        <!-- Detailed Results Table -->
        <div class="detailed-results">
            <h3>Detailed Validation History</h3>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Model Version</th>
                        <th>RMSE</th>
                        <th>MAE</th>
                        <th>Spearman ρ</th>
                        <th>Precision@20</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in validation_history %}
                    <tr>
                        <td>{{ result.test_date.strftime('%Y-%m-%d') }}</td>
                        <td>{{ result.model_version }}</td>
                        <td class="{{ 'good' if result.rmse < 3.0 else 'needs-work' }}">
                            {{ result.rmse }}
                        </td>
                        <td>{{ result.mae }}</td>
                        <td class="{{ 'good' if result.spearman_correlation > 0.25 else 'needs-work' }}">
                            {{ result.spearman_correlation }}
                        </td>
                        <td class="{{ 'good' if result.precision_at_20 > 0.30 else 'needs-work' }}">
                            {{ result.precision_at_20 }}
                        </td>
                        <td>{{ result.notes or '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Initialize validation results viewer
        document.addEventListener('DOMContentLoaded', function() {
            loadPerformanceChart();
            loadParameterAnalysis();
        });
        
        function loadPerformanceChart() {
            fetch('/api/validation/performance-history')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('performance-evolution').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.dates,
                            datasets: [
                                {
                                    label: 'RMSE',
                                    data: data.rmse_values,
                                    borderColor: 'rgb(255, 99, 132)',
                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                    yAxisID: 'y'
                                },
                                {
                                    label: 'Spearman ρ',
                                    data: data.spearman_values,
                                    borderColor: 'rgb(54, 162, 235)',
                                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                    yAxisID: 'y1'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: { display: true, text: 'RMSE' }
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: { display: true, text: 'Spearman ρ' },
                                    grid: { drawOnChartArea: false }
                                }
                            }
                        }
                    });
                });
        }
    </script>
</body>
</html>
```

### **Sprint 4 Success Metrics**
**Phase 1: Dashboard Integration** ✅ COMPLETED (2025-08-21)
- [x] ROI column added with proper NULL handling and green gradient styling
- [x] Formula version toggle implemented (v1.0/v2.0 switching)
- [x] Validation status indicators integrated (backend connected, awaiting data)
- [x] Visual indicators for v2.0 features with conditional CSS
- [x] Database NULL sorting issues resolved (NULLS LAST clause)

**Phase 2: Enhanced Controls** 🔄 PENDING
- [ ] Parameter sliders functional and update calculations
- [ ] Blending indicator shows current/historical weights

**Phase 3: Validation Integration** 🔄 PENDING  
- [ ] Validation results viewer accessible and informative
- [ ] AI insights displayed for relevant players

**Phase 4: Polish** 🔄 PENDING
- [ ] UI responsive and intuitive
- [ ] Performance maintains sub-3 second calculation time
- [ ] Formula toggle JavaScript state management fixed
- [ ] Visual styling edge cases resolved

---

## **SPRINT 5: Future Features (Optional)**
*Duration: 1-2 sessions*
*Priority: LOW - Advanced enhancements*

### **Objectives**
1. ⚪ Team Style multiplier integration
2. ⚪ Position-specific models
3. ⚪ Advanced Gemini analytics
4. ⚪ Automated parameter optimization

### **5.1 Team Style Multiplier**

**Research Reference**: Section 3.2 - "A New Multiplier: Quantifying Team Style"

**Data Requirements**:
- PPDA (Passes Per Defensive Action)
- Field Tilt (possession in final third)
- Progressive passing percentage

**Implementation**: Requires FBref integration for team tactical metrics

### **5.2 Position-Specific Models**

**Research Reference**: Section 3.3 - "Evolving to Position-Specific Formulations"

**Defender Model**: 
```
True_Value_DEF = (w1 × CleanSheetProb + w2 × BaselineAttack) × Form × Fixture
```

**Forward Model**:
```
True_Value_FWD = (w1 × xG + w2 × xA) × Form × Fixture × Service
```

### **5.3 Advanced Gemini Features**

- Season-long projections
- Injury risk assessment
- Transfer market insights
- Tactical matchup analysis

---

## **Implementation Schedule**

### **Session Planning**

**Session 1**: Sprint 1 + Sprint 2 (4-5 hours)
- Foundation fixes and advanced calculations
- Most critical improvements

**Session 2**: Sprint 3 (3-4 hours)  
- Validation and backtesting
- Parameter optimization

**Session 3**: Sprint 4 (2-3 hours)
- UI integration and polish
- User experience improvements

**Session 4+**: Sprint 5 (Future)
- Advanced features as time permits

### **Success Criteria**

**Sprint 1 Complete**: 
- ✅ True Value separated from price
- ✅ ROI calculated correctly
- ✅ Exponential fixture working

**Sprint 2 Complete**:
- ✅ EWMA form implemented
- ✅ Dynamic blending active
- ✅ xGI normalized

**Sprint 3 Complete**:
- ✅ RMSE < 2.85 achieved
- ✅ Spearman > 0.30 achieved
- ✅ Optimal parameters identified

**Sprint 4 Complete**:
- ✅ Dashboard updated and functional
- ✅ User experience excellent

### **Risk Mitigation**

1. **Backup Strategy**: Keep v1.0 formula as fallback
2. **Performance Monitoring**: Track calculation times throughout
3. **Data Quality**: Validate all multipliers stay within expected ranges
4. **User Testing**: Verify UI changes don't confuse existing users

---

## **Conclusion**

This sprint plan implements the research recommendations systematically while maintaining system stability and performance. The phased approach ensures each improvement builds on the previous work, culminating in a significantly more accurate and user-friendly fantasy football analysis tool.

**Expected Outcomes**:
- 10-15% improvement in prediction accuracy
- Better user experience with enhanced controls
- Data-driven optimization through backtesting
- AI-powered insights for competitive advantage

The research has provided a solid mathematical foundation; this sprint plan provides the roadmap to implement it successfully.