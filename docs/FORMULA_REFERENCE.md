# Formula Reference Guide

## Core Formula Overview

The Fantrax Value Hunter system calculates player value using a cascading multiplier approach:

```
True Value = Base Value × Form Multiplier × Fixture Multiplier × Starter Multiplier × xGI Multiplier
```

Where:
```
Base Value = Points Per Game (PPG) ÷ Player Price
```

## Detailed Formula Breakdown

### 1. Base Value Calculation (`app.py:301`)

```python
base_value = ppg / price if price > 0 else 0
```

**Components:**
- **PPG**: Points per game from Fantrax data
- **Price**: Current player price in millions (e.g., 5.5)
- **Protection**: Division by zero protection returns 0 for invalid prices

### 2. Form Multiplier (`app.py:69-129`)

The form multiplier compares recent performance to baseline performance using weighted averages.

#### Calculation Process:

**Step 1: Calculate Recent Form Average**
```python
# Weighted average of recent games (default: last 4 games)
total_weighted_points = sum(points * weight for points, weight in recent_games_with_weights)
total_weights = sum(weights)
recent_avg = total_weighted_points / total_weights if total_weights > 0 else 0
```

**Step 2: Determine Baseline**
- **Historical Phase** (GW 1-10): `baseline = previous_season_ppg`
- **Transition Phase** (GW 11-15): `baseline = weighted_blend(historical_ppg, current_season_ppg)`  
- **Current Phase** (GW 16+): `baseline = current_season_ppg`

**Step 3: Calculate Multiplier**
```python
form_multiplier = recent_avg / baseline if baseline > 0 else 1.0
# Capped between 0.5x and 1.5x
form_multiplier = max(0.5, min(1.5, form_multiplier))
```

#### Weighting System:
- **Game 1** (most recent): Weight = 4
- **Game 2**: Weight = 3  
- **Game 3**: Weight = 2
- **Game 4** (oldest): Weight = 1

### 3. Fixture Difficulty Multiplier (`app.py:131-180`)

Adjusts player value based on upcoming fixture difficulty using betting odds data.

#### Calculation Process:

**Step 1: Get Fixture Difficulty Score**
```sql
SELECT difficulty_score FROM team_fixtures 
WHERE team_code = %s AND gameweek = %s
```
- **Range**: -10 (easiest) to +10 (hardest)
- **Source**: Betting odds-based difficulty assessment

**Step 2: Apply Position Weights**
```python
position_weights = {
    'G': 1.10,  # Goalkeepers: 110% (more saves vs stronger teams)
    'D': 1.20,  # Defenders: 120% (clean sheets vs weaker teams)  
    'M': 1.00,  # Midfielders: 100% (baseline)
    'F': 1.05   # Forwards: 105% (goals vs weaker teams)
}
```

**Step 3: Calculate Final Multiplier**
```python
base_strength = 0.2  # 20% default impact
position_weight = position_weights.get(position, 1.0)
multiplier_adjustment = (difficulty_score / 10.0) * base_strength * position_weight
final_multiplier = 1.0 - multiplier_adjustment

# Constrained between 0.5x and 1.5x
return max(0.5, min(1.5, final_multiplier))
```

#### Examples:
- **Easy fixture** (score = -5): Multiplier ≈ 1.1x (boost)
- **Hard fixture** (score = +5): Multiplier ≈ 0.9x (penalty)

### 4. Starter Prediction Multiplier (`app.py:218-284`)

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

### 5. xGI (Expected Goals Involvement) Multiplier (`app.py:285-292`)

Incorporates underlying performance metrics from Understat data.

#### Data Source:
- **Metric**: xGI90 = (Expected Goals + Expected Assists) per 90 minutes
- **Provider**: Understat via ScraperFC integration  
- **Coverage**: 99% player match rate
- **Update**: Weekly manual sync

#### Calculation Modes:

**Capped Mode (Default):**
```python
multiplier = max(0.5, min(1.5, xGI90))
```

**Direct Mode:**
```python  
multiplier = xGI90 * strength_parameter  # strength = 0.7 default
```

**Adjusted Mode:**
```python
multiplier = 1 + (xGI90 * strength_parameter)
```

#### Fallback:
```python
# For unmatched players
xgi_multiplier = 1.0  # Neutral impact
```

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

## Parameter Validation Ranges

### Form Multiplier Parameters:
- **Recent Games Window**: 1-8 games (default: 4)
- **Baseline Switchover**: GW 5-15 (default: 10)
- **Transition End**: GW 10-20 (default: 15)
- **Form Impact Strength**: 0.0-2.0 (default: 1.0)

### Fixture Difficulty Parameters:
- **Enable/Disable**: Boolean toggle
- **Multiplier Strength**: 0.0-1.0 (default: 0.2)
- **Position Weights**: 0.5-2.0 per position

### Starter Prediction Parameters:
- **Manual Override**: JSON object format
- **Confidence Thresholds**: 0.0-1.0
- **Default Penalties**: Configurable per status level

### xGI Integration Parameters:
- **Calculation Mode**: Capped/Direct/Adjusted
- **Multiplier Strength**: 0.0-2.0 (default: 0.7)
- **Enable/Disable**: Boolean toggle
- **Display Stats**: Boolean toggle

## Performance Specifications

### Processing Targets:
- **Player Count**: 633 Premier League players
- **Calculation Time**: Efficient for weekly analysis workflow
- **Parameter Updates**: Smooth real-time responsiveness
- **Database Queries**: Optimized with caching where possible

### Data Dependencies:
- **Fantrax**: Player prices, positions, points data
- **Historical**: Previous season PPG baselines
- **Fixtures**: Team difficulty scores via betting odds
- **xGI**: Understat data via ScraperFC integration

## Error Handling and Fallbacks

### Missing Data Handling:
```python
# Form calculation
if no_recent_games:
    form_multiplier = 1.0  # Neutral

# Fixture difficulty  
if no_fixture_data:
    fixture_multiplier = 1.0  # Neutral

# Starter prediction
if unknown_status:
    starter_multiplier = 1.0  # No penalty

# xGI integration
if no_xgi_match:
    xgi_multiplier = 1.0  # Neutral
```

### Validation Constraints:
- All multipliers constrained between 0.5x and 1.5x (except where noted)
- Division by zero protection throughout
- Database connection error handling with graceful degradation
- Parameter range validation before application

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

This reference provides the complete mathematical foundation for the Fantrax Value Hunter system, enabling precise understanding and modification of the value calculation methodology.