# Phase 3: Dashboard Implementation Plan
**Fantrax Value Hunter - Version 1.0 Dashboard Development**

## 🎯 Core Objective

Build a **two-panel Flask dashboard** for parameter tuning across **all 633 Premier League players**. Real-time parameter adjustment is the CORE feature - enabling users to optimize True Value discovery through UI controls.

**Version 1.0 Focus**: Parameter adjustment affecting True Value rankings for the complete player database (not limited to candidate pools).

---

## 📊 Dashboard Architecture

### Two-Panel Layout (Version 1.0 Simplified)
```
┌─────────────────────────────┬─────────────────────────────────┐
│ PARAMETER CONTROLS (Left)   │ ALL 633 PLAYERS (Right)        │
├─────────────────────────────┼─────────────────────────────────┤
│ ▼ Form Calculation          │ Name     Team  Pos  Price  TVL  │
│ □ Enable/Disable            │ Salah    LIV   M    21.57  0.687│
│   • Lookback: [3 games ▼]   │ Mbeumo   BRE   M    10.74  1.044│
│   • Min Games: [3      ]    │ Palmer   CHE   M    22.35  0.511│
│                             │                                 │
│ ▼ Fixture Difficulty        │ [Filter: Position □G □D □M □F] │
│ □ Enable/Disable            │ [Filter: Price Range Slider]    │
│   • Mode: [5-tier ▼]        │ [Filter: Team Selection]        │
│   • Very Easy: ━━━━ 1.3x    │ [Search: Player Name]           │
│   • Easy: ━━━━━━ 1.15x      │                                 │
│   • Hard: ━━━━━━ 0.85x      │ Showing 633 players total       │
│   • Very Hard: ━━━ 0.7x     │ (Filtered: 127 matching)        │
│                             │                                 │
│ ▼ Starter Predictions       │ [Sort by: True Value ▲]        │
│ □ Enable/Disable            │ [Export Filtered Results]       │
│   • Both Agree: ━━━ 1.15x   │                                 │
│   • Rotation Risk: ━━ 0.85x │                                 │
│   • Injury Doubt: ━ 0.7x    │                                 │
│                             │                                 │
│ [Import Lineups CSV]        │                                 │
│ [Apply Changes]             │                                 │
│ [Reset to Defaults]         │                                 │
└─────────────────────────────┴─────────────────────────────────┘
```

### Version 1.0 Scope - What We're Building
- ✅ **Parameter Controls**: All multipliers adjustable via dashboard UI
- ✅ **All 633 Players**: Complete database display with filtering
- ✅ **Real-time Updates**: Parameter changes trigger True Value recalculation
- ✅ **CSV Import**: Upload starter predictions for weekly updates
- ✅ **Export Functionality**: Save filtered player lists

### Explicitly Out of Scope for v1.0
- ❌ **Auto-lineup selection** - moved to FUTURE_IDEAS.md
- ❌ **Drag-and-drop builder** - moved to FUTURE_IDEAS.md  
- ❌ **Live web scraping** - CSV import provides controlled data input
- ❌ **Complex visualizations** - focus on parameter tuning functionality

---

## 🔧 Parameter Controls (CORE FEATURE)

### 1. Form Calculation Controls
```javascript
// Dashboard sends to backend
{
  "form_calculation": {
    "enabled": true,              // Checkbox
    "lookback_period": 3,         // Dropdown: 3 or 5
    "minimum_games_for_form": 3   // Number input
  }
}

// Backend updates system_parameters.json
self.form_tracker.toggle_form_calculation(enabled)
self.form_tracker.update_lookback_period(lookback_period)
```

### 2. Fixture Difficulty Controls
```javascript
{
  "fixture_difficulty": {
    "enabled": true,
    "mode": "5_tier",            // Radio: 3_tier or 5_tier
    "5_tier_multipliers": {
      "very_easy": {
        "multiplier": 1.3        // Slider: 1.2-1.5
      },
      "easy": {
        "multiplier": 1.15       // Slider: 1.05-1.25
      },
      "hard": {
        "multiplier": 0.85       // Slider: 0.75-0.95
      },
      "very_hard": {
        "multiplier": 0.7        // Slider: 0.6-0.8
      }
    }
  }
}
```

### 3. Starter Prediction Controls (Penalty-Based)
```javascript
{
  "starter_prediction": {
    "enabled": true,
    "auto_rotation_penalty": 0.65,    // Slider: 0.5-0.8 (CSV bulk import)
    "force_bench_penalty": 0.6,       // Slider: 0.4-0.8 (manual overrides)
    "manual_overrides": {
      // Per-player overrides stored here
      "player_id_123": {
        "override_type": "force_starter",  // or "force_bench", "force_out"
        "multiplier": 1.0
      }
    }
  }
}
```

### 4. Display Filters (No Pool Size Limits)
```javascript
{
  "display_filters": {
    "position": ["G", "D", "M", "F"],     // Checkboxes
    "price_range": {"min": 5.0, "max": 25.0}, // Slider
    "ownership_threshold": 40,               // Number input
    "team_selection": [],                    // Multi-select
    "player_name_search": ""                 // Text input
  }
}
```

---

## 🏗️ Implementation Timeline

### Week 1: Foundation (Days 1-5)

#### Day 1: Database Foundation ✅ COMPLETE
- ✅ **PostgreSQL 17.6 Installed**: Operational on port 5433
- ✅ **Database Created**: fantrax_value_hunter with fantrax_user
- ✅ **Schema Deployed**: players, player_form, player_metrics tables
- ✅ **Data Imported**: All 633 players with gameweek 1 metrics
- ✅ **True Value Formula**: PPG ÷ Price calculations verified

#### Day 2: Flask Backend ✅ COMPLETE
- ✅ **Flask Application**: Complete `src/app.py` with all parameter adjustment endpoints
- ✅ **Database Integration**: PostgreSQL connection via psycopg2 for Python operations
- ✅ **API Routes**: 5 endpoints implemented (health, players, config, update-parameters, dashboard)
- ✅ **Form Calculation**: Complete weighted average implementation (3/5 gameweek lookback)
- ✅ **Performance Verified**: Sub-second response times for all 633 player queries

#### Day 3: Enhanced Parameter Controls ✅ COMPLETE  
- ✅ **Complete Dashboard UI**: Two-panel layout with all missing parameter controls
- ✅ **Baseline Switchover**: Gameweek selector for form calculation transition
- ✅ **3-Tier Fixture Mode**: Toggle between 3-tier and 5-tier difficulty systems
- ✅ **Form Strength Slider**: Missing multiplier control in Form Calculation section
- ✅ **Manual Override System**: Per-player Force Starter/Bench/Out radio buttons
- ✅ **Real-time Updates**: All controls trigger True Value recalculation across 633 players
- ✅ **Complete Styling**: Professional CSS with color-coded manual override controls
- ✅ **JavaScript Integration**: Full parameter change detection and API communication

#### Days 4-5: SKIPPED (Functionality Combined into Day 3)
- ✅ **Dashboard UI**: Complete two-panel layout implemented
- ✅ **Interactive Controls**: All parameter sliders and toggles operational
- ✅ **API Integration**: Real-time parameter updates with visual feedback

### Week 2: Data Import & Polish (Days 6-8)

#### Day 6: CSV Import & Export
- [ ] Build CSV parser for starter prediction uploads
- [ ] Implement player name matching to database IDs
- [ ] Add export functionality for filtered player lists
- [ ] Test CSV import updates starter multipliers correctly
- [ ] Validate export includes all relevant columns

#### Day 7: Integration Testing
- [ ] Test parameter changes affect all 633 players correctly
- [ ] Verify filtering works with full dataset
- [ ] Test performance with complete player database
- [ ] Validate calculation accuracy across all multipliers
- [ ] Test CSV import/export with real data

#### Day 8: Final Testing & Polish
- [ ] Complete user acceptance testing
- [ ] Performance optimization for 633 players
- [ ] Error handling and validation
- [ ] Documentation updates
- [ ] Version 1.0 readiness verification

---

## 📁 File Structure

```
Fantrax_Value_Hunter/
├── src/
│   ├── app.py                    # NEW: Flask application
│   ├── db_manager.py             # NEW: Database MCP wrapper
│   ├── candidate_analyzer.py     # MODIFY: Use database
│   ├── form_tracker.py           # MODIFY: Use database
│   ├── fixture_difficulty.py     # NO CHANGE
│   └── starter_predictor.py      # MODIFY: Add CSV import
├── templates/
│   └── dashboard.html            # NEW: Two-panel UI
├── static/
│   ├── css/
│   │   └── dashboard.css         # NEW: Dashboard styles
│   └── js/
│       └── dashboard.js          # NEW: Parameter controls
├── migrations/
│   ├── 001_create_schema.py      # NEW: Database setup
│   └── 002_import_data.py        # NEW: Data migration
└── config/
    └── system_parameters.json    # EXISTING: Updated by dashboard
```

---

## 🔄 Flask Application Structure

### src/app.py
```python
from flask import Flask, render_template, jsonify, request
from db_manager import DatabaseManager, run_async
from candidate_analyzer import CandidateAnalyzer
import json

app = Flask(__name__)
db = DatabaseManager()
analyzer = CandidateAnalyzer()

@app.before_first_request
def init():
    """Initialize database connection"""
    run_async(db.connect())

@app.route('/')
def dashboard():
    """Render main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/candidates')
def get_candidates():
    """Get current candidate pools from database"""
    gameweek = request.args.get('gameweek', 1, type=int)
    position = request.args.get('position', None)
    
    candidates = run_async(db.get_candidate_pools(gameweek, position))
    return jsonify(candidates)

@app.route('/api/update-parameters', methods=['POST'])
def update_parameters():
    """Update system parameters and recalculate"""
    params = request.json
    
    # Load current config
    with open('../config/system_parameters.json', 'r') as f:
        config = json.load(f)
    
    # Update specific sections
    if 'form_calculation' in params:
        config['form_calculation'].update(params['form_calculation'])
        analyzer.form_tracker.toggle_form_calculation(
            params['form_calculation'].get('enabled', False)
        )
    
    if 'fixture_difficulty' in params:
        config['fixture_difficulty'].update(params['fixture_difficulty'])
        analyzer.fixture_analyzer.reload_config()
    
    if 'starter_prediction' in params:
        config['starter_prediction']['multipliers'].update(
            params['starter_prediction']['multipliers']
        )
        analyzer.starter_predictor.update_multipliers(
            params['starter_prediction']['multipliers']
        )
    
    # Save updated config
    with open('../config/system_parameters.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Recalculate with new parameters
    analyzer.fetch_fantrax_data()
    candidate_pools = analyzer.generate_candidate_pools()
    
    # Save to database
    gameweek = request.json.get('gameweek', 1)
    all_players = []
    for position, players in candidate_pools.items():
        all_players.extend(players)
    
    run_async(db.update_player_metrics(all_players, gameweek))
    
    return jsonify({
        'success': True,
        'message': 'Parameters updated and recalculated',
        'candidate_count': len(all_players)
    })

@app.route('/api/import-lineups', methods=['POST'])
def import_lineups():
    """Import starter predictions from CSV"""
    file = request.files['lineups_csv']
    # Parse CSV and update starter predictions
    # Implementation depends on CSV format
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 📊 Dashboard JavaScript (Parameter Controls)

### static/js/dashboard.js
```javascript
// Track pending changes
let pendingChanges = {};
let originalConfig = {};

// Load current configuration
async function loadConfig() {
    const response = await fetch('/api/get-config');
    originalConfig = await response.json();
    updateUIFromConfig(originalConfig);
}

// Handle parameter changes
function onParameterChange(section, param, value) {
    if (!pendingChanges[section]) {
        pendingChanges[section] = {};
    }
    pendingChanges[section][param] = value;
    
    // Show pending changes indicator
    document.getElementById('pending-changes').style.display = 'block';
    document.getElementById('apply-changes').disabled = false;
    
    // Update preview
    updateTrueValuePreview();
}

// Apply all pending changes
async function applyChanges() {
    const response = await fetch('/api/update-parameters', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(pendingChanges)
    });
    
    if (response.ok) {
        // Reload candidate table
        await loadCandidates();
        
        // Clear pending changes
        pendingChanges = {};
        document.getElementById('pending-changes').style.display = 'none';
        document.getElementById('apply-changes').disabled = true;
        
        // Show success message
        showNotification('Parameters updated successfully!');
    }
}

// Form calculation toggle
document.getElementById('form-enabled').addEventListener('change', (e) => {
    const enabled = e.target.checked;
    document.getElementById('form-controls').style.opacity = enabled ? '1' : '0.5';
    onParameterChange('form_calculation', 'enabled', enabled);
});

// Lookback period change
document.getElementById('lookback-period').addEventListener('change', (e) => {
    onParameterChange('form_calculation', 'lookback_period', parseInt(e.target.value));
});

// Fixture difficulty sliders
document.getElementById('fixture-easy-boost').addEventListener('input', (e) => {
    const value = parseFloat(e.target.value);
    document.getElementById('fixture-easy-display').textContent = value.toFixed(2) + 'x';
    onParameterChange('fixture_difficulty', 'easy_multiplier', value);
});

// Load candidates with current parameters
async function loadCandidates() {
    const response = await fetch('/api/candidates?gameweek=1');
    const candidates = await response.json();
    updateCandidateTable(candidates);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadCandidates();
});
```

---

## 📝 Weekly Workflow

### Before Each Gameweek (10 minutes)

1. **Get Predicted Lineups**
   - Visit Fantasy Football Scout
   - Copy predicted XIs for all 20 teams

2. **Update Google Sheet**
   ```
   Team | Predicted Starting XI
   -----|----------------------
   ARS  | Raya, White, Saliba, Gabriel...
   AVL  | Martinez, Cash, Konsa...
   ```

3. **Import to Dashboard**
   - Export Sheet as CSV
   - Click "Import Lineups CSV" button
   - System matches names to player IDs
   - Applies starter multipliers automatically

4. **Tune Parameters**
   - Adjust boost factor sliders if needed
   - Enable/disable specific boosts
   - Click "Apply Changes" to recalculate

5. **Select Your Team**
   - Sort by True Value
   - Consider late team news
   - Manually pick best 11 within budget

---

## ✅ Success Criteria

- [ ] Database stores historical form data
- [ ] All parameter changes update True Values in real-time  
- [ ] CSV import correctly identifies starters
- [ ] Player table sorts and filters properly
- [ ] Form calculations work with gameweek history
- [ ] Configuration persists between sessions
- [ ] No manual JSON editing required

---

## 🚨 Critical Requirements

1. **Parameter Adjustment is CORE**
   - Every multiplier must be adjustable via UI
   - Changes must trigger immediate recalculation
   - Visual feedback for pending changes

2. **Database is REQUIRED**
   - Form tracking cannot work without historical data
   - JSON files inadequate for time-series storage

3. **Manual Selection Required**
   - No auto-selection of "best" team
   - User judgment critical for final decisions
   - System provides data, user makes choices

---

## 🧹 Post-Implementation Cleanup Tasks

### Legacy Parameter Removal
After dashboard implementation is complete and tested, the following unused parameters should be removed from `config/system_parameters.json`:

1. **`"estimated_games_played": 20`** (line 42)
   - **Reason**: Replaced by FPG/Points calculation from actual CSV data
   - **Impact**: Safe to remove - not used in current system

2. **`"differential_threshold": 44`** (line 44) 
   - **Reason**: Legacy from ownership percentage tracking system
   - **Impact**: Safe to remove - current system doesn't use ownership data

3. **`"pool_sizes": {"G": 8, "D": 20, "M": 20, "F": 20}`** (lines 47-52)
   - **Reason**: Replaced by filterable all-players table approach
   - **Impact**: Safe to remove - candidate pools no longer used

4. **Update `dashboard_controls.adjustable_parameters`** (lines 231-243)
   - Remove: `"estimated_games_played"`, `"differential_threshold"`, `"pool_sizes"`
   - Keep only active parameters used by dashboard

**⚠️ Testing Required**: Verify removal doesn't break existing functionality before deployment.

---

This plan focuses on the CORE features with parameter tuning as the primary goal!