# Enhanced Dashboard Implementation Guide
**Target Phase**: Phase 3 (Game Weeks 5-8)  
**Priority**: High - Complete candidate analysis and lineup construction platform

---

## 🎯 **Dashboard Layout Overview**

### **Three-Panel Layout**
```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│   Control Panel     │   Player Database   │   Lineup Builder    │
│   (Parameter        │   (Filterable       │   (Drag & Drop      │
│    Adjustments)     │    Candidate List)  │    Construction)    │
│                     │                     │                     │
│   - Boost Factors   │   - Advanced        │   - Position Groups │
│   - Pool Sizes      │     Filtering       │   - Team Filtering  │ 
│   - Value Settings  │   - Sorting Options │   - Budget Tracker  │
│                     │   - Sample Size     │   - Export Options  │
│                     │     Warnings        │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

---

## 🔧 **1. Enhanced Parameter Control Panel**
**Location**: Left sidebar (collapsible)  
**Layout**: Tabbed sections for different parameter types

### **Tab 1: Boost Factor Controls**
```html
<div class="boost-factors-tab">
  <h4>True Value Boost Factors</h4>
  
  <!-- Master Formula Display -->
  <div class="formula-display">
    <strong>True Value = ValueScore × BoostFactors</strong>
    <small>Where BoostFactors = Form × Fixture × Starter × Custom</small>
  </div>
  
  <!-- Form Boost -->
  <div class="boost-section">
    <label>
      <input type="checkbox" id="form-boost-enabled" checked="false">
      Form Boost (Weighted Recent Performance)
    </label>
    <div class="boost-details" id="form-boost-details" disabled>
      <label>Lookback Period:</label>
      <select id="form-lookback" value="3">
        <option value="3">3 Games [0.5, 0.3, 0.2]</option>
        <option value="5">5 Games [0.4, 0.25, 0.2, 0.1, 0.05]</option>
      </select>
      <label>Boost Range:</label>
      <input type="range" id="form-intensity" min="0.5" max="2.0" value="1.0" step="0.1">
      <span id="form-range-display">0.5x - 2.0x</span>
    </div>
  </div>
  
  <!-- Fixture Difficulty Boost -->
  <div class="boost-section">
    <label>
      <input type="checkbox" id="fixture-boost-enabled" checked="false">
      Fixture Difficulty Boost (Easy Opponents)
    </label>
    <div class="boost-details" id="fixture-boost-details" disabled>
      <label>Boost Easy Fixtures (Rank 1-5):</label>
      <input type="range" id="fixture-easy-boost" min="1.0" max="1.5" value="1.2" step="0.05">
      <span id="fixture-easy-display">1.2x</span>
      
      <label>Penalize Hard Fixtures (Rank 16-20):</label>
      <input type="range" id="fixture-hard-penalty" min="0.7" max="1.0" value="0.9" step="0.05">
      <span id="fixture-hard-display">0.9x</span>
    </div>
  </div>
  
  <!-- Predicted Starter Boost -->
  <div class="boost-section">
    <label>
      <input type="checkbox" id="starter-boost-enabled" checked="false">
      Predicted Starter Boost (Fantasy Football Scout)
    </label>
    <div class="boost-details" id="starter-boost-details" disabled>
      <label>Starter Confidence Boost:</label>
      <input type="range" id="starter-boost" min="1.0" max="1.3" value="1.1" step="0.05">
      <span id="starter-boost-display">1.1x</span>
      
      <label>Rotation Risk Penalty:</label>
      <input type="range" id="rotation-penalty" min="0.8" max="1.0" value="0.95" step="0.05">
      <span id="rotation-penalty-display">0.95x</span>
    </div>
  </div>
  
  <!-- Custom Boost (Future) -->
  <div class="boost-section">
    <label>
      <input type="checkbox" id="custom-boost-enabled" checked="false">
      Custom Boost Factor (Advanced)
    </label>
    <div class="boost-details" id="custom-boost-details" disabled>
      <textarea id="custom-boost-formula" placeholder="Enter custom boost logic (Python expression)"></textarea>
      <small>Example: 1.2 if ownership_pct < 10 else 1.0</small>
    </div>
  </div>
  
  <!-- Season Average Source -->
  <div class="baseline-section">
    <label>Season Average Source:</label>
    <input type="number" id="baseline-switchover" value="10" min="1" max="38">
    <span>Switch to current season at Game Week</span>
    <small>Before GW 10: Use 2024-25 baseline | After GW 10: Use current season</small>
  </div>
</div>
```

### **Tab 2: Pool & Filter Settings**
```html
<div class="pool-filter-tab">
  <h4>Candidate Pool Sizes</h4>
  <div class="pool-grid">
    <label>Goalkeepers: <input type="number" id="pool-gk" value="8" min="5" max="20"></label>
    <label>Defenders: <input type="number" id="pool-def" value="20" min="10" max="40"></label>
    <label>Midfielders: <input type="number" id="pool-mid" value="20" min="10" max="40"></label>
    <label>Forwards: <input type="number" id="pool-fwd" value="20" min="10" max="40"></label>
  </div>
  
  <h4>Sample Size Handling</h4>
  <div class="sample-size-controls">
    <label>Minimum Games for Form:</label>
    <input type="number" id="min-games-form" value="3" min="1" max="10">
    
    <label>
      <input type="checkbox" id="show-new-players" checked="true">
      Show New Players (separate section)
    </label>
    
    <label>
      <input type="checkbox" id="highlight-small-sample" checked="true">
      Highlight Small Sample Sizes (<5 games)
    </label>
  </div>
  
  <h4>Value Thresholds</h4>
  <div class="threshold-controls">
    <label>Differential Ownership Threshold:</label>
    <input type="range" id="differential-threshold" min="20" max="50" value="40" step="5">
    <span id="differential-display">< 40%</span>
    
    <label>Premium Player Threshold:</label>
    <input type="range" id="premium-threshold" min="15" max="25" value="20" step="1">
    <span id="premium-display">$20+</span>
  </div>
</div>
```

---

## 📊 **2. Advanced Player Database (Center Panel)**
**Location**: Center section of dashboard  
**Features**: Multi-level filtering, sorting, search, and sample size warnings

### **Filter Bar (Top of Player Database)**
```html
<div class="filter-bar">
  <!-- Position Filtering -->
  <div class="position-filters">
    <button class="filter-btn active" data-position="all">All</button>
    <button class="filter-btn" data-position="G">GK</button>
    <button class="filter-btn" data-position="D">DEF</button>
    <button class="filter-btn" data-position="M">MID</button>
    <button class="filter-btn" data-position="F">FWD</button>
  </div>
  
  <!-- Team Filtering (Multi-select checkboxes) -->
  <div class="team-filters">
    <label>Teams:</label>
    <div class="team-checkboxes">
      <label><input type="checkbox" value="ARS"> Arsenal</label>
      <label><input type="checkbox" value="MCI"> Man City</label>
      <label><input type="checkbox" value="LIV"> Liverpool</label>
      <label><input type="checkbox" value="TOT"> Tottenham</label>
      <!-- ... all 20 teams -->
      <button id="select-big6">Big 6</button>
      <button id="select-promoted">Promoted</button>
      <button id="clear-teams">Clear All</button>
    </div>
  </div>
  
  <!-- Value Range Filters -->
  <div class="value-filters">
    <label>Price Range:</label>
    <input type="range" id="price-min" min="5" max="30" value="5">
    <input type="range" id="price-max" min="5" max="30" value="30">
    <span id="price-range-display">$5.00 - $30.00</span>
    
    <label>True Value Range:</label>
    <input type="range" id="value-min" min="5" max="50" value="5">
    <input type="range" id="value-max" min="5" max="50" value="50">
    <span id="value-range-display">5.0 - 50.0</span>
  </div>
  
  <!-- Sample Size & Special Filters -->
  <div class="special-filters">
    <label><input type="checkbox" id="filter-differential"> Differentials Only (<40%)</label>
    <label><input type="checkbox" id="filter-predicted-starters"> Predicted Starters Only</label>
    <label><input type="checkbox" id="filter-good-fixtures"> Easy Fixtures Only (Rank 1-10)</label>
    <label><input type="checkbox" id="filter-good-form"> Good Form Only (>110)</label>
    <label><input type="checkbox" id="filter-new-players"> New Players Only (<5 games)</label>
    <label><input type="checkbox" id="filter-small-sample"> Small Sample Warning</label>
  </div>
  
  <!-- Quick Sort Options -->
  <div class="sort-options">
    <label>Sort By:</label>
    <select id="sort-field">
      <option value="true_value">True Value (Best)</option>
      <option value="value_score">Value Score (Basic)</option>
      <option value="form_score">Form</option>
      <option value="predicted_starter">Starting Likelihood</option>
      <option value="price">Price (Low to High)</option>
      <option value="ownership_pct">Ownership (Low to High)</option>
      <option value="next_opponent_rank">Fixture Difficulty</option>
    </select>
  </div>
  
  <!-- Search -->
  <div class="search-box">
    <input type="text" id="player-search" placeholder="Search player names...">
  </div>
</div>
```

### **Enhanced Data Table**
```javascript
const enhancedTableColumns = [
  { field: 'drag_handle', title: '', width: 30, sortable: false }, // Drag icon for lineup builder
  { field: 'rank', title: 'Rank', width: 50 },
  { field: 'name', title: 'Player', width: 160 },
  { field: 'team', title: 'Team', width: 50 },
  { field: 'position', title: 'Pos', width: 40 },
  { field: 'price', title: 'Price', width: 60, format: '$0.00' },
  { field: 'ppg', title: 'PPG', width: 50, format: '0.00' },
  { field: 'games_played', title: 'GP', width: 40 }, // NEW: Sample size indicator
  { field: 'value_score', title: 'ValueSc', width: 65, format: '0.00' },
  { field: 'true_value', title: 'TrueVal', width: 65, format: '0.00', sortable: true },
  { field: 'boost_breakdown', title: 'Boosts', width: 80 }, // NEW: Shows active boost factors
  { field: 'ownership_pct', title: 'Own%', width: 50, format: '0%' },
  { field: 'form_score', title: 'Form', width: 50, format: '0.0' },
  { field: 'predicted_starter', title: 'Start?', width: 50 }, // Icons: ✓, ?, ✗
  { field: 'next_opponent_rank', title: 'Fix', width: 40 }, // Fixture difficulty rank
  { field: 'sample_warning', title: '⚠️', width: 30 }, // NEW: Warning icon for small samples
  { field: 'differential', title: 'Diff', width: 40, format: 'boolean' }
];
```

### **Sample Size Warning System**
```html
<!-- Warning badges for players with insufficient data -->
<div class="sample-warnings">
  <span class="warning-badge new-player" title="New player - no historical data">NEW</span>
  <span class="warning-badge small-sample" title="Less than 5 games played">⚠️ <5GP</span>
  <span class="warning-badge injury-return" title="Returning from injury">🏥 RTN</span>
  <span class="warning-badge rotation-risk" title="Rotation risk - inconsistent starts">🔄 ROT</span>
</div>
```

---

## ⚽ **3. Drag & Drop Lineup Builder (Right Panel)**
**Location**: Right sidebar  
**Features**: Visual lineup construction with budget tracking and constraint validation

### **Lineup Formation Display**
```html
<div class="lineup-builder">
  <h4>Lineup Builder</h4>
  
  <!-- Budget Tracker -->
  <div class="budget-tracker">
    <div class="budget-bar">
      <div class="budget-used" style="width: 65%"></div>
    </div>
    <span class="budget-text">$65.50 / $100.00 used</span>
    <span class="budget-remaining">$34.50 remaining</span>
  </div>
  
  <!-- Formation Display (Visual 11-player layout) -->
  <div class="formation-display">
    <!-- Goalkeeper -->
    <div class="position-section gk-section">
      <h5>Goalkeeper (1)</h5>
      <div class="drop-zone" data-position="G" data-min="1" data-max="1">
        <div class="player-slot" id="gk-slot">
          <span class="placeholder">Drop GK here</span>
        </div>
      </div>
    </div>
    
    <!-- Defenders -->
    <div class="position-section def-section">
      <h5>Defenders (3-5)</h5>
      <div class="drop-zone" data-position="D" data-min="3" data-max="5">
        <div class="player-slot" id="def-slot-1"><span class="placeholder">Drop DEF here</span></div>
        <div class="player-slot" id="def-slot-2"><span class="placeholder">Drop DEF here</span></div>
        <div class="player-slot" id="def-slot-3"><span class="placeholder">Drop DEF here</span></div>
        <div class="player-slot optional" id="def-slot-4"><span class="placeholder">Optional DEF</span></div>
        <div class="player-slot optional" id="def-slot-5"><span class="placeholder">Optional DEF</span></div>
      </div>
    </div>
    
    <!-- Midfielders -->
    <div class="position-section mid-section">
      <h5>Midfielders (3-5)</h5>
      <div class="drop-zone" data-position="M" data-min="3" data-max="5">
        <div class="player-slot" id="mid-slot-1"><span class="placeholder">Drop MID here</span></div>
        <div class="player-slot" id="mid-slot-2"><span class="placeholder">Drop MID here</span></div>
        <div class="player-slot" id="mid-slot-3"><span class="placeholder">Drop MID here</span></div>
        <div class="player-slot optional" id="mid-slot-4"><span class="placeholder">Optional MID</span></div>
        <div class="player-slot optional" id="mid-slot-5"><span class="placeholder">Optional MID</span></div>
      </div>
    </div>
    
    <!-- Forwards -->
    <div class="position-section fwd-section">
      <h5>Forwards (1-3)</h5>
      <div class="drop-zone" data-position="F" data-min="1" data-max="3">
        <div class="player-slot" id="fwd-slot-1"><span class="placeholder">Drop FWD here</span></div>
        <div class="player-slot optional" id="fwd-slot-2"><span class="placeholder">Optional FWD</span></div>
        <div class="player-slot optional" id="fwd-slot-3"><span class="placeholder">Optional FWD</span></div>
      </div>
    </div>
  </div>
  
  <!-- Lineup Statistics -->
  <div class="lineup-stats">
    <h5>Lineup Analysis</h5>
    <div class="stats-grid">
      <div class="stat-item">
        <label>Total Cost:</label>
        <span id="total-cost">$65.50</span>
      </div>
      <div class="stat-item">
        <label>Projected Points:</label>
        <span id="projected-points">85.2</span>
      </div>
      <div class="stat-item">
        <label>Average True Value:</label>
        <span id="avg-true-value">14.8</span>
      </div>
      <div class="stat-item">
        <label>Differentials:</label>
        <span id="differential-count">4 / 11</span>
      </div>
      <div class="stat-item">
        <label>Teams Represented:</label>
        <span id="team-count">8 teams</span>
      </div>
      <div class="stat-item">
        <label>Small Sample Players:</label>
        <span id="small-sample-count">2 / 11</span>
      </div>
    </div>
  </div>
  
  <!-- Constraint Validation -->
  <div class="constraint-validation">
    <div class="validation-item valid" id="position-validation">
      ✓ Position requirements met (1G, 4D, 4M, 2F)
    </div>
    <div class="validation-item valid" id="budget-validation">
      ✓ Within budget ($100.00)
    </div>
    <div class="validation-item warning" id="sample-validation">
      ⚠️ 2 players with small sample sizes
    </div>
  </div>
  
  <!-- Action Buttons -->
  <div class="lineup-actions">
    <button id="save-lineup" class="primary-btn">Save Lineup</button>
    <button id="export-csv" class="secondary-btn">Export CSV</button>
    <button id="clear-lineup" class="danger-btn">Clear All</button>
    <button id="auto-complete" class="secondary-btn">Auto-Complete (Best Value)</button>
  </div>
  
  <!-- Saved Lineups -->
  <div class="saved-lineups">
    <h5>Saved Lineups</h5>
    <div class="lineup-list">
      <div class="saved-lineup-item">
        <span>Lineup 1 - Conservative ($87.50)</span>
        <button class="load-btn">Load</button>
        <button class="delete-btn">×</button>
      </div>
      <div class="saved-lineup-item">
        <span>Lineup 2 - Differential ($92.30)</span>
        <button class="load-btn">Load</button>
        <button class="delete-btn">×</button>
      </div>
    </div>
  </div>
</div>
```

### **Drag & Drop JavaScript Implementation**
```javascript
// Drag and Drop functionality
function initializeDragDrop() {
  // Make player rows draggable
  document.querySelectorAll('.player-row').forEach(row => {
    row.draggable = true;
    row.addEventListener('dragstart', handleDragStart);
  });
  
  // Make lineup slots drop targets
  document.querySelectorAll('.player-slot').forEach(slot => {
    slot.addEventListener('dragover', handleDragOver);
    slot.addEventListener('drop', handleDrop);
    slot.addEventListener('dragenter', handleDragEnter);
    slot.addEventListener('dragleave', handleDragLeave);
  });
}

function handleDragStart(e) {
  const playerData = {
    id: e.target.dataset.playerId,
    name: e.target.dataset.playerName,
    position: e.target.dataset.position,
    price: parseFloat(e.target.dataset.price),
    team: e.target.dataset.team
  };
  e.dataTransfer.setData('text/plain', JSON.stringify(playerData));
  e.target.classList.add('dragging');
}

function handleDrop(e) {
  e.preventDefault();
  const playerData = JSON.parse(e.dataTransfer.getData('text/plain'));
  const slot = e.target.closest('.player-slot');
  const dropZone = slot.closest('.drop-zone');
  
  // Validate position compatibility
  if (dropZone.dataset.position !== playerData.position) {
    showError(`Cannot place ${playerData.position} in ${dropZone.dataset.position} slot`);
    return;
  }
  
  // Validate budget constraint
  if (currentBudget + playerData.price > 100) {
    showError(`Adding ${playerData.name} would exceed budget`);
    return;
  }
  
  // Add player to lineup
  addPlayerToSlot(slot, playerData);
  updateBudgetDisplay();
  updateLineupStats();
  validateConstraints();
}

function addPlayerToSlot(slot, playerData) {
  slot.innerHTML = `
    <div class="player-card" data-player-id="${playerData.id}">
      <span class="player-name">${playerData.name}</span>
      <span class="player-team">${playerData.team}</span>
      <span class="player-price">$${playerData.price}</span>
      <button class="remove-player" onclick="removePlayer('${slot.id}')">×</button>
    </div>
  `;
  slot.classList.add('filled');
}
```

---

## 🔄 **4. Real-Time Parameter Updates**
**Requirement**: All changes immediately recalculate candidate pools and lineup validation

#### **JavaScript API Calls**
```javascript
// Form Calculation Toggle
function toggleFormCalculation(enabled) {
  fetch('/api/form-calculation', {
    method: 'POST',
    body: JSON.stringify({ enabled: enabled }),
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    updateTable(data.candidates);
    updateStatus(`Form calculation ${enabled ? 'enabled' : 'disabled'}`);
  });
}

// Lookback Period Change
function updateLookbackPeriod(period) {
  fetch('/api/lookback-period', {
    method: 'POST', 
    body: JSON.stringify({ period: parseInt(period) }),
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    updateTable(data.candidates);
    updateWeightsDisplay(data.weights);
  });
}

// Pool Size Updates
function updatePoolSizes(sizes) {
  fetch('/api/pool-sizes', {
    method: 'POST',
    body: JSON.stringify(sizes),
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    updateTable(data.candidates);
    updatePoolCounts(data.counts);
  });
}

// Boost Factor Updates
function updateBoostFactors(boostSettings) {
  fetch('/api/boost-factors', {
    method: 'POST',
    body: JSON.stringify(boostSettings),
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    updateTable(data.candidates);
    updateBoostDisplay(data.active_boosts);
  });
}

// Filter Updates (Debounced)
let filterUpdateTimeout;
function updateFilters(filters) {
  clearTimeout(filterUpdateTimeout);
  filterUpdateTimeout = setTimeout(() => {
    fetch('/api/apply-filters', {
      method: 'POST',
      body: JSON.stringify(filters),
      headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
      updateTable(data.filtered_candidates);
      updateFilterCounts(data.filter_counts);
    });
  }, 500); // 500ms debounce
}

// Real-time Table Update
function updateTable(candidates) {
  const tableBody = document.getElementById('player-table-body');
  tableBody.innerHTML = '';
  
  candidates.forEach((player, index) => {
    const row = createPlayerRow(player, index + 1);
    tableBody.appendChild(row);
  });
  
  // Reinitialize drag-drop after table update
  initializeDragDrop();
}

// Status Banner Updates
function updateStatus(message, type = 'info') {
  const statusBanner = document.getElementById('status-banner');
  statusBanner.className = `status-banner ${type}`;
  statusBanner.textContent = message;
  
  // Auto-hide after 3 seconds for success messages
  if (type === 'success') {
    setTimeout(() => {
      statusBanner.style.opacity = '0.5';
    }, 3000);
  }
}
```

---

## 🔧 **Backend API Requirements**

### **Flask/FastAPI Endpoints**
```python
from flask import Flask, request, jsonify
from src.candidate_analyzer import CandidateAnalyzer
from src.form_tracker import FormTracker

app = Flask(__name__)
analyzer = CandidateAnalyzer()

@app.route('/api/form-calculation', methods=['POST'])
def toggle_form_calculation():
    enabled = request.json.get('enabled', False)
    analyzer.form_tracker.toggle_form_calculation(enabled)
    
    # Regenerate candidates with new settings
    candidate_pools = analyzer.generate_candidate_pools()
    
    return jsonify({
        'success': True,
        'form_enabled': enabled,
        'candidates': candidate_pools,
        'message': f'Form calculation {"enabled" if enabled else "disabled"}'
    })

@app.route('/api/lookback-period', methods=['POST']) 
def update_lookback_period():
    period = request.json.get('period', 3)
    analyzer.form_tracker.update_lookback_period(period)
    
    candidate_pools = analyzer.generate_candidate_pools()
    
    return jsonify({
        'success': True,
        'lookback_period': period,
        'weights': analyzer.form_tracker.recent_game_weights,
        'candidates': candidate_pools
    })

@app.route('/api/pool-sizes', methods=['POST'])
def update_pool_sizes():
    sizes = request.json  # {'G': 8, 'D': 20, 'M': 20, 'F': 20}
    analyzer.pool_sizes.update(sizes)
    
    candidate_pools = analyzer.generate_candidate_pools()
    
    return jsonify({
        'success': True,
        'pool_sizes': sizes,
        'candidates': candidate_pools,
        'counts': {pos: len(pool) for pos, pool in candidate_pools.items()}
    })

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get current candidate pools"""
    candidate_pools = analyzer.generate_candidate_pools()
    return jsonify({
        'candidates': candidate_pools,
        'metadata': {
            'form_enabled': analyzer.form_tracker.form_enabled,
            'lookback_period': analyzer.form_tracker.lookback_period,
            'pool_sizes': analyzer.pool_sizes,
            'gameweek': analyzer.form_tracker.form_data['metadata']['current_gameweek']
        }
    })

@app.route('/api/boost-factors', methods=['POST'])
def update_boost_factors():
    """Update all boost factor settings"""
    boost_settings = request.json
    
    # Update form boost
    if 'form' in boost_settings:
        form_settings = boost_settings['form']
        analyzer.form_tracker.toggle_form_calculation(form_settings.get('enabled', False))
        if 'lookback_period' in form_settings:
            analyzer.form_tracker.update_lookback_period(form_settings['lookback_period'])
    
    # Update fixture boost (when implemented)
    if 'fixture' in boost_settings:
        fixture_settings = boost_settings['fixture']
        # analyzer.fixture_tracker.update_settings(fixture_settings)
    
    # Update starter prediction boost (when implemented)
    if 'starter' in boost_settings:
        starter_settings = boost_settings['starter']
        # analyzer.starter_predictor.update_settings(starter_settings)
    
    candidate_pools = analyzer.generate_candidate_pools()
    
    return jsonify({
        'success': True,
        'active_boosts': analyzer.get_active_boost_summary(),
        'candidates': candidate_pools
    })

@app.route('/api/apply-filters', methods=['POST'])
def apply_filters():
    """Apply filtering to candidate pools"""
    filters = request.json
    
    # Get all candidates first
    all_candidates = analyzer.generate_candidate_pools()
    
    # Apply filters
    filtered_candidates = analyzer.apply_filters(all_candidates, filters)
    
    # Calculate filter counts for UI feedback
    filter_counts = {
        'total_before': len(all_candidates),
        'total_after': len(filtered_candidates),
        'filtered_out': len(all_candidates) - len(filtered_candidates)
    }
    
    return jsonify({
        'success': True,
        'filtered_candidates': filtered_candidates,
        'filter_counts': filter_counts,
        'applied_filters': filters
    })

@app.route('/api/lineup/validate', methods=['POST'])
def validate_lineup():
    """Validate a proposed lineup against constraints"""
    lineup = request.json.get('players', [])
    
    validation_result = analyzer.validate_lineup(lineup)
    
    return jsonify({
        'valid': validation_result['valid'],
        'errors': validation_result['errors'],
        'warnings': validation_result['warnings'],
        'stats': validation_result['stats']
    })

@app.route('/api/lineup/save', methods=['POST'])
def save_lineup():
    """Save a completed lineup"""
    lineup_data = request.json
    
    # Save to database or file
    lineup_id = analyzer.save_lineup(lineup_data)
    
    return jsonify({
        'success': True,
        'lineup_id': lineup_id,
        'message': 'Lineup saved successfully'
    })
```

---

## 🎨 **UI/UX Requirements**

### **Status Indicators**
```html
<!-- Form Status Banner -->
<div class="status-banner" id="form-status">
  <span class="indicator disabled">●</span>
  Form Calculation: DISABLED (neutral multiplier)
  <small>Enable after Game Week 3 when players have sufficient data</small>
</div>

<!-- Budget Analysis -->
<div class="budget-analysis">
  <h4>Lineup Construction Viability</h4>
  <div class="budget-range">
    <span>Min Cost: $55.00</span>
    <span>Max Cost: $79.31</span>
    <span class="warning">⚠️ Max under $90 - consider higher-priced options</span>
  </div>
</div>
```

### **Value Highlighting**
```css
/* Table row highlighting */
.differential { background-color: #e8f5e8; }
.high-value { background-color: #fff3cd; }
.premium { background-color: #f8d7da; }

/* Form score coloring */
.form-excellent { color: #28a745; font-weight: bold; }
.form-good { color: #6c757d; }
.form-poor { color: #dc3545; }
.form-disabled { color: #6c757d; font-style: italic; }
```

### **Enhanced CSS Framework**
```css
/* Three-Panel Dashboard Layout */
.dashboard-container {
  display: grid;
  grid-template-columns: 300px 1fr 350px;
  grid-template-rows: 60px 1fr;
  grid-template-areas: 
    "header header header"
    "controls database lineup";
  height: 100vh;
  gap: 10px;
  padding: 10px;
}

.header-bar {
  grid-area: header;
  background: #2c3e50;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-radius: 5px;
}

.control-panel {
  grid-area: controls;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  overflow-y: auto;
}

.player-database {
  grid-area: database;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.lineup-builder {
  grid-area: lineup;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  overflow-y: auto;
}

/* Player Table Styling */
.player-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.player-table th {
  background: #343a40;
  color: white;
  padding: 8px 4px;
  text-align: left;
  position: sticky;
  top: 0;
  z-index: 10;
}

.player-table td {
  padding: 6px 4px;
  border-bottom: 1px solid #e9ecef;
}

/* Row Highlighting */
.player-row.differential { background-color: #e8f5e8; }
.player-row.high-value { background-color: #fff3cd; }
.player-row.premium { background-color: #f8d7da; }
.player-row.new-player { background-color: #e3f2fd; }
.player-row.small-sample { border-left: 3px solid #ff9800; }

/* Form Score Coloring */
.form-excellent { color: #28a745; font-weight: bold; }
.form-good { color: #6c757d; }
.form-poor { color: #dc3545; }
.form-disabled { color: #6c757d; font-style: italic; }

/* Boost Factor Controls */
.boost-section {
  margin: 15px 0;
  padding: 10px;
  border: 1px solid #dee2e6;
  border-radius: 3px;
}

.boost-section input[type="checkbox"] {
  margin-right: 8px;
}

.boost-details {
  margin-top: 10px;
  padding-left: 20px;
}

.boost-details[disabled] {
  opacity: 0.5;
  pointer-events: none;
}

/* Drag and Drop Styling */
.player-row[draggable="true"] {
  cursor: move;
}

.player-row.dragging {
  opacity: 0.5;
}

.player-slot {
  min-height: 40px;
  border: 2px dashed #dee2e6;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 5px 0;
  transition: all 0.3s ease;
}

.player-slot.filled {
  border: 2px solid #28a745;
  background: #e8f5e8;
}

.player-slot:hover {
  border-color: #007bff;
  background: #f8f9fa;
}

.player-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 5px;
  background: white;
  border-radius: 3px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  position: relative;
  width: 100%;
}

.remove-player {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 12px;
  cursor: pointer;
}

/* Budget Tracker */
.budget-bar {
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin: 10px 0;
}

.budget-used {
  height: 100%;
  background: linear-gradient(90deg, #28a745 0%, #ffc107 70%, #dc3545 90%);
  transition: width 0.3s ease;
}

/* Sample Size Warnings */
.warning-badge {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: bold;
  margin: 0 2px;
}

.warning-badge.new-player {
  background: #e3f2fd;
  color: #1976d2;
}

.warning-badge.small-sample {
  background: #fff3e0;
  color: #f57c00;
}

.warning-badge.injury-return {
  background: #ffebee;
  color: #d32f2f;
}

.warning-badge.rotation-risk {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Status Indicators */
.status-banner {
  padding: 10px;
  border-radius: 5px;
  margin: 10px 0;
  font-weight: bold;
}

.status-banner.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.status-banner.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-banner.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.status-banner.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
```

### **Responsive Design**
```css
/* Tablet Layout (768px - 1024px) */
@media (max-width: 1024px) {
  .dashboard-container {
    grid-template-columns: 250px 1fr;
    grid-template-areas: 
      "header header"
      "controls database";
  }
  
  .lineup-builder {
    display: none; /* Hide lineup builder on tablet */
  }
  
  /* Hide less important columns */
  .player-table .opponent-rank,
  .player-table .predicted-starter {
    display: none;
  }
}

/* Mobile Layout (< 768px) */
@media (max-width: 768px) {
  .dashboard-container {
    grid-template-columns: 1fr;
    grid-template-rows: 60px auto 1fr;
    grid-template-areas: 
      "header"
      "controls"
      "database";
  }
  
  .control-panel {
    max-height: 200px;
    overflow-y: auto;
  }
  
  /* Show only essential columns */
  .player-table .games-played,
  .player-table .boost-breakdown,
  .player-table .ownership-pct,
  .player-table .form-score,
  .player-table .sample-warning {
    display: none;
  }
  
  .player-table {
    font-size: 11px;
  }
  
  .player-table th,
  .player-table td {
    padding: 4px 2px;
  }
}
```

---

## 📋 **Development Timeline**

### **Phase 3 Sprint Planning (Game Weeks 5-8)**

#### **Week 1: Foundation**
- [ ] Set up Flask/FastAPI backend with API endpoints
- [ ] Create basic HTML table structure
- [ ] Implement parameter control forms
- [ ] Test form calculation toggle

#### **Week 2: Real-time Updates**
- [ ] JavaScript API integration
- [ ] Live table updates without page refresh
- [ ] Parameter validation and error handling
- [ ] Status indicator updates

#### **Week 3: UX Polish**
- [ ] Table sorting and filtering
- [ ] Visual highlighting and styling
- [ ] Responsive design implementation
- [ ] Performance optimization

#### **Week 4: Testing & Launch**
- [ ] Cross-browser testing
- [ ] Parameter edge case testing
- [ ] User acceptance testing
- [ ] Production deployment

---

## 🚨 **Critical Implementation Notes**

### **Form Calculation Logic**
```javascript
// Dashboard must handle form calculation state properly
if (formEnabled && gameWeek >= 3) {
  // Show form scores and enable form controls
  enableFormControls();
} else if (gameWeek < 3) {
  // Show "Insufficient data" message
  showInsufficientDataWarning();
} else {
  // Form disabled by user choice
  showFormDisabledStatus();
}
```

### **Configuration Persistence**
- Save parameter changes to `config/system_parameters.json`
- Load user preferences on dashboard startup
- Validate parameter ranges before applying

### **Error Handling**
- API connection failures
- Invalid parameter values
- Missing data scenarios
- Form calculation errors

### **Performance Considerations**
- Cache candidate calculations
- Debounce parameter changes (500ms delay)
- Progressive loading for large datasets
- Background updates without blocking UI

---

## 🎯 **Success Criteria**

### **User Experience**
- [ ] Parameters can be changed in real-time
- [ ] Table updates within 2 seconds of parameter change
- [ ] Clear status indicators for all settings
- [ ] Intuitive controls that don't require documentation

### **Technical Performance**
- [ ] Sub-second response times for parameter updates
- [ ] No data loss during parameter changes
- [ ] Graceful error handling and recovery
- [ ] Cross-browser compatibility (Chrome, Firefox, Safari)

### **Feature Completeness**
- [ ] All identified parameters are adjustable
- [ ] Form calculation can be enabled/disabled seamlessly
- [ ] Lookback period switching works correctly
- [ ] Pool size changes immediately reflect in results

---

## ⚡ **Performance Optimization**

### **Large Dataset Handling (633+ Players)**
```javascript
// Virtual Scrolling for Large Tables
class VirtualTable {
  constructor(container, data, rowHeight = 35) {
    this.container = container;
    this.data = data;
    this.rowHeight = rowHeight;
    this.visibleRows = Math.ceil(container.clientHeight / rowHeight) + 5;
    this.startIndex = 0;
    this.init();
  }
  
  init() {
    this.container.addEventListener('scroll', this.onScroll.bind(this));
    this.render();
  }
  
  onScroll() {
    const scrollTop = this.container.scrollTop;
    const newStartIndex = Math.floor(scrollTop / this.rowHeight);
    
    if (newStartIndex !== this.startIndex) {
      this.startIndex = newStartIndex;
      this.render();
    }
  }
  
  render() {
    const endIndex = Math.min(this.startIndex + this.visibleRows, this.data.length);
    const visibleData = this.data.slice(this.startIndex, endIndex);
    
    // Render only visible rows
    this.updateTable(visibleData, this.startIndex);
  }
}

// Debounced Search and Filtering
const debouncedSearch = debounce((searchTerm) => {
  const filteredData = playerData.filter(player => 
    player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    player.team.toLowerCase().includes(searchTerm.toLowerCase())
  );
  updateTable(filteredData);
}, 300);

// Efficient Data Caching
class DataCache {
  constructor(ttl = 300000) { // 5 minutes
    this.cache = new Map();
    this.ttl = ttl;
  }
  
  set(key, data) {
    this.cache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }
  
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
}

// Background Updates
class BackgroundUpdater {
  constructor(updateInterval = 60000) { // 1 minute
    this.updateInterval = updateInterval;
    this.isRunning = false;
  }
  
  start() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.intervalId = setInterval(async () => {
      try {
        const latestData = await fetch('/api/candidates').then(r => r.json());
        this.updateDataSilently(latestData);
      } catch (error) {
        console.warn('Background update failed:', error);
      }
    }, this.updateInterval);
  }
  
  updateDataSilently(newData) {
    // Update data without disrupting user interaction
    if (!document.querySelector('.player-table').matches(':hover')) {
      updateTable(newData.candidates);
    }
  }
  
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.isRunning = false;
    }
  }
}
```

### **Memory Management**
```javascript
// Efficient DOM Updates
function updatePlayerRow(playerId, newData) {
  const row = document.querySelector(`[data-player-id="${playerId}"]`);
  if (!row) return;
  
  // Update only changed cells
  const cells = row.querySelectorAll('td');
  
  if (cells[6].textContent !== newData.true_value.toString()) {
    cells[6].textContent = newData.true_value;
    cells[6].classList.add('updated');
    setTimeout(() => cells[6].classList.remove('updated'), 1000);
  }
}

// Cleanup Event Listeners
function cleanup() {
  // Remove all event listeners when switching views
  document.querySelectorAll('.player-row').forEach(row => {
    row.removeEventListener('dragstart', handleDragStart);
  });
  
  // Clear timeouts and intervals
  if (filterUpdateTimeout) clearTimeout(filterUpdateTimeout);
  backgroundUpdater.stop();
}
```

### **API Response Optimization**
```python
# Efficient Data Serialization
@app.route('/api/candidates/minimal', methods=['GET'])
def get_minimal_candidates():
    """Get only essential data for initial load"""
    candidates = analyzer.generate_candidate_pools()
    
    # Return only essential fields for performance
    minimal_data = []
    for player in candidates:
        minimal_data.append({
            'id': player['id'],
            'name': player['name'][:20],  # Truncate names
            'position': player['position'],
            'price': round(player['price'], 1),
            'true_value': round(player['true_value'], 1),
            'differential': player['ownership_pct'] < 40
        })
    
    return jsonify({
        'candidates': minimal_data,
        'total_count': len(candidates)
    })

# Compressed Response
@app.after_request
def after_request(response):
    if request.endpoint and 'api' in request.endpoint:
        response.headers['Content-Encoding'] = 'gzip'
    return response
```

---

## 🔒 **Security & Error Handling**

### **Input Validation**
```python
from marshmallow import Schema, fields, validate

class BoostFactorSchema(Schema):
    form = fields.Dict(missing={})
    fixture = fields.Dict(missing={})
    starter = fields.Dict(missing={})

class FilterSchema(Schema):
    positions = fields.List(fields.Str(validate=validate.OneOf(['G', 'D', 'M', 'F'])))
    price_min = fields.Float(validate=validate.Range(min=5.0, max=30.0))
    price_max = fields.Float(validate=validate.Range(min=5.0, max=30.0))
    teams = fields.List(fields.Str(validate=validate.Length(max=3)))

@app.route('/api/boost-factors', methods=['POST'])
def update_boost_factors():
    schema = BoostFactorSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid input', 'details': err.messages}), 400
    
    # Process validated data...
```

### **Error Recovery**
```javascript
// Graceful Error Handling
async function safeApiCall(url, data = null) {
  try {
    const response = await fetch(url, {
      method: data ? 'POST' : 'GET',
      body: data ? JSON.stringify(data) : null,
      headers: data ? { 'Content-Type': 'application/json' } : {}
    });
    
    if (!response.ok) {
      throw new Error(`API call failed: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    updateStatus('Connection error. Using cached data.', 'warning');
    
    // Fallback to cached data
    return getCachedData(url) || { error: 'No cached data available' };
  }
}

// Auto-retry Failed Requests
class ApiManager {
  constructor(maxRetries = 3, retryDelay = 1000) {
    this.maxRetries = maxRetries;
    this.retryDelay = retryDelay;
  }
  
  async callWithRetry(url, data, retryCount = 0) {
    try {
      return await safeApiCall(url, data);
    } catch (error) {
      if (retryCount < this.maxRetries) {
        await this.delay(this.retryDelay * Math.pow(2, retryCount));
        return this.callWithRetry(url, data, retryCount + 1);
      }
      throw error;
    }
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

## 🎯 **Final Implementation Checklist**

### **Phase 3A: Core Dashboard (Week 1)**
- [ ] Three-panel HTML layout with CSS Grid
- [ ] Flask backend with core API endpoints
- [ ] Basic parameter controls (form toggle, lookback period)
- [ ] Player data table with sorting
- [ ] Real-time updates without page refresh

### **Phase 3B: Advanced Features (Week 2)**
- [ ] Drag-and-drop lineup builder
- [ ] Advanced filtering system
- [ ] Team selection checkboxes
- [ ] Sample size warning system
- [ ] Budget tracking and validation

### **Phase 3C: UX Polish (Week 3)**
- [ ] Enhanced boost factor controls
- [ ] Visual highlighting and styling
- [ ] Responsive design implementation
- [ ] Performance optimization
- [ ] Error handling and recovery

### **Phase 3D: Testing & Launch (Week 4)**
- [ ] Cross-browser compatibility testing
- [ ] Parameter edge case validation
- [ ] Load testing with full 633 player dataset
- [ ] User acceptance testing
- [ ] Production deployment

---

**Dashboard implementation ready for Phase 3 development! 🚀**

**Key Features Delivered:**
- ✅ Complete three-panel dashboard specification
- ✅ Real-time parameter control system
- ✅ Advanced filtering and team selection
- ✅ Drag-and-drop lineup builder
- ✅ Performance optimization for 633+ players
- ✅ Responsive design for all devices
- ✅ Comprehensive boost factor controls
- ✅ Sample size warning system
- ✅ Full API endpoint specifications

*Last Updated: August 14, 2025*  
*Status: Specification Complete - Ready for Development*  
*Next Phase: Begin Flask backend implementation*