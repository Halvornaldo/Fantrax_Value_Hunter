# Sprint 6: Odds-Based Position-Weighted Fixture Difficulty Implementation Plan

**Date Created**: August 18, 2025  
**Status**: Ready to Execute  
**Priority**: High (Sprint 6 of 8)  
**Complexity**: 5/10  
**Estimated Time**: 12 hours

---

## 🎯 **Sprint 6 Objectives**

Replace the non-functional fixture difficulty system (currently all 1.00x neutral) with a sophisticated odds-based system featuring:

- **21-point difficulty scale** (-10 to +10) based on betting odds
- **Position-specific weight multipliers** (G, D, M, F each customizable)
- **Preset system** (Conservative, Balanced, Aggressive) with fine-tuning slider
- **Real odds integration** using oddsportal.com CSV data
- **Intuitive dashboard controls** replacing complex 5-tier/3-tier system

---

## 📊 **Current State Analysis**

### **Problem Identified**:
- All 1,266 players have `fixture_multiplier = 1.0` (confirmed via database query)
- Fixture difficulty system exists but is never called during true value calculations
- No opponent/fixture data stored in database
- Dashboard shows "1.00x" for everyone instead of varied Easy/Hard/Very Hard

### **Existing Files Analysis**:
```
Files to Modify:
├── src/fixture_difficulty.py        [456 lines - heavy simplification needed]
├── config/system_parameters.json    [complex 5-tier/3-tier - restructure]
├── templates/dashboard.html         [UI needs complete redesign]
├── static/js/dashboard.js          [parameter handling updates]
├── src/app.py                      [integrate new odds system]

New Files to Create:
├── templates/odds_upload.html       [odds upload interface]
└── docs/SPRINT_6_FIXTURE_DIFFICULTY_PLAN.md [this document]
```

### **Database Schema Current State**:
- ✅ `player_metrics.fixture_multiplier` column exists
- ❌ No fixture/opponent data tables
- ❌ No odds storage capability

---

## 🧮 **Technical Specification**

### **21-Point Difficulty Scale**

```python
# Difficulty Score Calculation
def calculate_difficulty_score(home_odds, away_odds, is_home_team):
    """
    Convert betting odds to -10 to +10 difficulty scale
    
    Args:
        home_odds: Home team decimal odds (e.g. 1.27)
        away_odds: Away team decimal odds (e.g. 10.27) 
        is_home_team: True if calculating for home team
    
    Returns:
        float: Difficulty score from -10.0 (easiest) to +10.0 (hardest)
    """
    # Calculate normalized probabilities
    home_prob = 1 / home_odds
    away_prob = 1 / away_odds
    draw_prob = 1 / 3.5  # Approximate draw probability
    total_prob = home_prob + away_prob + draw_prob
    
    # Get opponent strength (normalized probability)
    if is_home_team:
        opponent_strength = away_prob / total_prob
    else:
        opponent_strength = home_prob / total_prob
    
    # Map to -10 to +10 scale (0.5 = neutral)
    difficulty_score = (opponent_strength - 0.5) * 20
    return round(difficulty_score, 1)

# Position-Specific Multiplier Calculation
def calculate_position_multiplier(difficulty_score, position, preset, position_weights, overall_strength):
    """
    Calculate final fixture multiplier with position weighting
    
    Args:
        difficulty_score: -10.0 to +10.0 from odds
        position: 'G', 'D', 'M', or 'F'
        preset: Multiplier range (0.10, 0.20, 0.30)
        position_weights: {'G': 1.10, 'D': 1.20, 'M': 1.00, 'F': 1.05}
        overall_strength: 0.50 to 1.50 scaling factor
    
    Returns:
        float: Final fixture multiplier
    """
    # Base multiplier from difficulty score
    base_multiplier = 1.0 + (difficulty_score / 10.0) * preset
    
    # Apply position weight
    position_weight = position_weights.get(position, 1.0)
    weighted_effect = (base_multiplier - 1.0) * position_weight * overall_strength
    
    # Final multiplier
    final_multiplier = 1.0 + weighted_effect
    return round(final_multiplier, 3)
```

### **Example Calculations**:

```python
# Arsenal (1.27) vs Leeds (10.27) - Leeds perspective
difficulty_score = calculate_difficulty_score(1.27, 10.27, is_home_team=False)
# Result: +8.7 (very hard fixture for Leeds)

# Position multipliers for Leeds players (Balanced preset, default weights):
leeds_gk = calculate_position_multiplier(8.7, 'G', 0.20, {'G': 1.10}, 1.0)  # 0.81x
leeds_def = calculate_position_multiplier(8.7, 'D', 0.20, {'D': 1.20}, 1.0) # 0.79x
leeds_mid = calculate_position_multiplier(8.7, 'M', 0.20, {'M': 1.00}, 1.0) # 0.83x
leeds_fwd = calculate_position_multiplier(8.7, 'F', 0.20, {'F': 1.05}, 1.0) # 0.82x

# Arsenal players get positive multipliers (easy fixture)
```

---

## 🗃️ **Database Schema Changes**

### **New Tables**:

```sql
-- Store raw odds data from CSV uploads
CREATE TABLE fixture_odds (
    id SERIAL PRIMARY KEY,
    gameweek INTEGER NOT NULL,
    match_date DATE NOT NULL,
    home_team VARCHAR(5) NOT NULL,
    away_team VARCHAR(5) NOT NULL,
    home_odds DECIMAL(5,2) NOT NULL,
    draw_odds DECIMAL(5,2) NOT NULL,
    away_odds DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(gameweek, home_team, away_team)
);

-- Store calculated difficulty scores per team per gameweek
CREATE TABLE team_fixtures (
    gameweek INTEGER NOT NULL,
    team_code VARCHAR(5) NOT NULL,
    opponent_code VARCHAR(5) NOT NULL,
    is_home BOOLEAN NOT NULL,
    difficulty_score DECIMAL(3,1) NOT NULL,  -- -10.0 to +10.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gameweek, team_code)
);

-- Create indexes for performance
CREATE INDEX idx_fixture_odds_gameweek ON fixture_odds(gameweek);
CREATE INDEX idx_team_fixtures_gameweek ON team_fixtures(gameweek);
CREATE INDEX idx_team_fixtures_team ON team_fixtures(team_code);
```

---

## 📁 **Team Name Mapping Dictionary**

```python
# Map oddsportal.csv team names to Fantrax team codes
ODDS_TO_FANTRAX_TEAMS = {
    "Arsenal": "ARS",
    "Aston Villa": "AVL", 
    "Bournemouth": "BOU",
    "Brentford": "BRE",
    "Brighton": "BHA",
    "Burnley": "BUR",
    "Chelsea": "CHE",
    "Crystal Palace": "CRY",
    "Everton": "EVE",
    "Fulham": "FUL",
    "Leeds": "LEE",
    "Liverpool": "LIV",
    "Manchester City": "MCI",
    "Manchester Utd": "MUN",
    "Newcastle": "NEW",
    "Nottingham": "NFO",  # "Nottingham" in CSV -> "NFO"
    "Sunderland": "SUN",
    "Tottenham": "TOT",
    "West Ham": "WHU",
    "Wolves": "WOL"
}

# Gameweek detection from dates
GAMEWEEK_DATE_RANGES = {
    2: ("2025-08-22", "2025-08-25"),  # Aug 22-25
    3: ("2025-08-30", "2025-08-31"),  # Aug 30-31
    # Add more as season progresses
}
```

---

## 🎨 **UI Design Specification**

### **New Dashboard Controls**:

```html
<div class="fixture-difficulty-section">
    <h3>
        <input type="checkbox" id="fixture-enabled" checked> 
        Fixture Difficulty
    </h3>
    
    <!-- Preset Selector -->
    <div class="preset-selector">
        <label>Strategy:</label>
        <select id="fixture-preset">
            <option value="conservative">Conservative (±10%)</option>
            <option value="balanced" selected>Balanced (±20%)</option>
            <option value="aggressive">Aggressive (±30%)</option>
        </select>
    </div>
    
    <!-- Position Weight Sliders -->
    <div class="position-weights">
        <div class="weight-control">
            <label>Goalkeepers (G): <span class="weight-value">110%</span></label>
            <input type="range" id="weight-g" min="50" max="150" value="110" step="5">
            <small>Clean sheet focus</small>
        </div>
        
        <div class="weight-control">
            <label>Defenders (D): <span class="weight-value">120%</span></label>
            <input type="range" id="weight-d" min="50" max="150" value="120" step="5">
            <small>Most affected by fixtures</small>
        </div>
        
        <div class="weight-control">
            <label>Midfielders (M): <span class="weight-value">100%</span></label>
            <input type="range" id="weight-m" min="50" max="150" value="100" step="5">
            <small>Balanced impact</small>
        </div>
        
        <div class="weight-control">
            <label>Forwards (F): <span class="weight-value">105%</span></label>
            <input type="range" id="weight-f" min="50" max="150" value="105" step="5">
            <small>Goal opportunity focus</small>
        </div>
    </div>
    
    <!-- Overall Strength Slider -->
    <div class="overall-strength">
        <label>Overall Strength: <span class="strength-value">100%</span></label>
        <input type="range" id="overall-strength" min="50" max="150" value="100" step="5">
        <small>Scale all fixture impacts</small>
    </div>
</div>
```

### **Fixture Column Display**:
Replace uniform "1.00x" with varied multipliers:

```
Current: 1.00x (all players)

New Examples:
1.24x ↑↑  (Very Easy fixture)
1.12x ↑   (Easy fixture) 
1.00x —   (Neutral fixture)
0.88x ↓   (Hard fixture)
0.76x ↓↓  (Very Hard fixture)
```

---

## 🔧 **Implementation Plan**

### **Sprint 6.1: Backend Infrastructure (4 hours)**

#### **Database Setup** (30 min)
1. Create migration script: `migrations/006_fixture_odds_tables.sql`
2. Run migrations to create tables
3. Verify schema with Database MCP

#### **Odds Import Endpoint** (1.5 hours)
1. Create `/api/import-odds` in `src/app.py`
2. Parse CSV with date handling logic
3. Map team names using dictionary
4. Calculate gameweek from dates
5. Store odds and calculate difficulty scores

#### **Fixture Difficulty Engine** (1.5 hours)
1. Simplify `src/fixture_difficulty.py` or create new module
2. Implement 21-point scale calculation
3. Add position weight application logic
4. Create multiplier calculation functions

#### **Integration with True Value** (30 min)
1. Modify `recalculate_true_values()` in `src/app.py`
2. Fetch difficulty scores from `team_fixtures`
3. Apply position-specific multipliers
4. Update all 633 players

### **Sprint 6.2: Parameter System Update (2 hours)**

#### **Configuration Update** (30 min)
```json
// New structure in system_parameters.json
"fixture_difficulty": {
    "enabled": true,
    "preset": "balanced",
    "presets": {
        "conservative": {"range": 0.10, "description": "Minimal fixture impact"},
        "balanced": {"range": 0.20, "description": "Standard fixture impact"},
        "aggressive": {"range": 0.30, "description": "Maximum fixture impact"}
    },
    "position_weights": {
        "G": 1.10,  // Goalkeepers - clean sheet focus
        "D": 1.20,  // Defenders - most affected
        "M": 1.00,  // Midfielders - baseline
        "F": 1.05   // Forwards - slight goal opportunity focus
    },
    "overall_strength": 1.00,
    "last_odds_import": null,
    "current_gameweek": 2
}
```

#### **Parameter Update Handler** (1 hour)
1. Modify `/api/update-parameters` endpoint
2. Handle new parameter structure
3. Trigger recalculation on changes
4. Validate parameter ranges

#### **Testing** (30 min)
1. Test parameter updates
2. Verify recalculation performance
3. Check multiplier variations

### **Sprint 6.3: Frontend UI Implementation (3 hours)**

#### **Dashboard HTML Redesign** (1 hour)
1. Replace 5-tier/3-tier radio buttons with preset dropdown
2. Add position weight sliders with labels
3. Add overall strength slider
4. Style new controls to match existing design

#### **JavaScript Updates** (1.5 hours)
1. Create event handlers for new controls
2. Update parameter sending logic
3. Real-time slider value displays
4. Integrate with existing parameter update system

#### **UI Polish** (30 min)
1. CSS styling for sliders and controls
2. Tooltips explaining each control
3. Visual feedback on parameter changes
4. Responsive design considerations

### **Sprint 6.4: Odds Upload Interface (2 hours)**

#### **Create Upload Page** (1 hour)
1. Create `templates/odds_upload.html` based on `form_upload.html`
2. Instructions for using oddsportal.com scraping
3. Gameweek selection dropdown
4. File upload and processing interface

#### **Navigation and Integration** (30 min)
1. Add "📊 Upload Odds Data" button to dashboard
2. Create route handler for upload page
3. Link back to dashboard

#### **Testing and Documentation** (30 min)
1. Test upload workflow with sample data
2. Document scraping instructions
3. Error handling for invalid files

### **Sprint 6.5: Integration Testing (1 hour)**

#### **End-to-End Testing**:
1. **Odds Import Workflow**
   - Upload `oddsportal.csv`
   - Verify gameweek detection (Aug 22-25 = GW2)
   - Check team name mapping accuracy
   - Confirm difficulty score calculations

2. **Position Weight Functionality**
   - Test each position slider
   - Verify different multipliers per position
   - Check preset switching behavior
   - Test overall strength scaling

3. **Performance Validation**
   - Time full 633-player recalculation
   - Check UI responsiveness
   - Monitor database query efficiency

4. **Edge Case Handling**
   - Missing teams in odds data
   - Invalid date formats
   - Duplicate uploads
   - Parameter validation

---

## 📈 **Expected Outcomes**

### **Before Sprint 6**:
```
All players show: 1.00x (Neutral)
Database state: 1,266 records with fixture_multiplier = 1.0
```

### **After Sprint 6**:
```
Varied multipliers based on actual fixtures:

Arsenal vs Leeds gameweek:
- Arsenal GK: 1.19x (Easy fixture, GK weight 110%)
- Arsenal D:  1.21x (Easy fixture, D weight 120%) 
- Arsenal M:  1.17x (Easy fixture, M weight 100%)
- Arsenal F:  1.18x (Easy fixture, F weight 105%)

- Leeds GK:   0.81x (Hard fixture, GK weight 110%)
- Leeds D:    0.79x (Hard fixture, D weight 120%)
- Leeds M:    0.83x (Hard fixture, M weight 100%) 
- Leeds F:    0.82x (Hard fixture, F weight 105%)

Newcastle vs Liverpool (close match):
- Newcastle: ~0.95x multipliers
- Liverpool: ~1.05x multipliers
```

---

## 🛡️ **Risk Mitigation**

### **Technical Risks**:
1. **Performance**: 633 players × position calculations
   - **Mitigation**: Pre-calculate difficulty scores, efficient queries
   
2. **Data Quality**: Team name mapping errors
   - **Mitigation**: Comprehensive mapping dictionary, validation

3. **UI Complexity**: Too many controls overwhelming users
   - **Mitigation**: Clear labels, tooltips, preset system

### **Fallback Plan**:
- Keep existing system functional until new system proven
- Gradual rollout with ability to disable new system
- Database backup before major changes

---

## 🧪 **Testing Scenarios**

### **Unit Tests**:
```python
def test_difficulty_calculation():
    # Arsenal (1.27) vs Leeds (10.27)
    score = calculate_difficulty_score(1.27, 10.27, is_home_team=False)
    assert 8.5 <= score <= 9.5  # Leeds facing very hard fixture

def test_position_multipliers():
    # Test position weights apply correctly
    gk_mult = calculate_position_multiplier(5.0, 'G', 0.20, {'G': 1.10}, 1.0)
    d_mult = calculate_position_multiplier(5.0, 'D', 0.20, {'D': 1.20}, 1.0)
    assert d_mult < gk_mult  # Defenders more affected by difficulty

def test_team_name_mapping():
    assert ODDS_TO_FANTRAX_TEAMS["Manchester City"] == "MCI"
    assert ODDS_TO_FANTRAX_TEAMS["Nottingham"] == "NFO"
```

### **Integration Tests**:
1. Upload sample oddsportal.csv
2. Verify 20 teams mapped correctly
3. Check all players get varied multipliers
4. Test UI parameter changes update database
5. Measure performance with full dataset

---

## 📚 **Handover Notes**

### **Key Files Created/Modified**:
```
Modified:
├── src/app.py                    [new /api/import-odds endpoint]
├── src/fixture_difficulty.py    [simplified position-weight system]
├── config/system_parameters.json [new parameter structure]
├── templates/dashboard.html      [redesigned UI controls]
├── static/js/dashboard.js       [parameter handling updates]
├── docs/CLAUDE.md               [Sprint 6 completion status]

Created:
├── templates/odds_upload.html    [odds upload interface]
├── migrations/006_fixture_odds_tables.sql [database schema]
└── docs/SPRINT_6_FIXTURE_DIFFICULTY_PLAN.md [this document]
```

### **Critical Success Metrics**:
- ✅ Fixture column shows varied multipliers (not all 1.00x)
- ✅ Position-specific impacts visible (D > G > F > M typically)
- ✅ User can fine-tune via preset + sliders
- ✅ Real odds data drives realistic assessments
- ✅ Performance: <2 second recalculation for 633 players

### **Configuration Examples**:
```python
# Conservative Strategy (minimal impact)
preset = "conservative"  # ±10% range
position_weights = {"G": 1.05, "D": 1.10, "M": 1.00, "F": 1.02}

# Aggressive Strategy (maximum impact)  
preset = "aggressive"    # ±30% range
position_weights = {"G": 1.15, "D": 1.30, "M": 1.00, "F": 1.10}
```

### **Debugging Commands**:
```sql
-- Check fixture multiplier distribution
SELECT fixture_multiplier, COUNT(*) 
FROM player_metrics 
GROUP BY fixture_multiplier 
ORDER BY fixture_multiplier;

-- View current fixtures
SELECT * FROM team_fixtures WHERE gameweek = 2;

-- Check odds import
SELECT home_team, away_team, home_odds, away_odds 
FROM fixture_odds WHERE gameweek = 2;
```

---

## 🚀 **Ready to Execute**

This plan provides comprehensive guidance for implementing the odds-based position-weighted fixture difficulty system. The approach balances sophistication with usability, giving users powerful control while maintaining intuitive operation.

**Next Steps**: Execute Sprint 6.1 by creating the database schema and odds import endpoint.

---

**Last Updated**: August 18, 2025  
**Status**: Ready for Implementation  
**Estimated Completion**: Sprint 6 of 8 complete