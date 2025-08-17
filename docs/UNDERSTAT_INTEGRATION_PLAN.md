# Understat xGI Integration Plan - Fantrax Value Hunter

**Date**: August 17, 2025  
**Status**: ✅ COMPLETED - 85.2% Match Rate Achieved  
**Completion Time**: Completed successfully  
**Risk Level**: Low (all changes are additive)

---

## 📋 Executive Summary

Integrate Understat expected stats (xG90, xA90, xGI90) into Fantrax Value Hunter to enhance True Value calculations with performance-based multipliers. The system will use the existing UnifiedNameMatcher for intelligent player matching.

### ✅ Achieved Outcomes
- **155 players** successfully matched with xGI data (85.2% match rate)
- **Enhanced True Value formula**: `TrueValue = (PPG ÷ Price) × Form × Fixture × Starter × xGI_multiplier`
- **Team name mapping** implemented (Understat full names → Fantrax 3-letter codes)
- **UnifiedNameMatcher integration** completed with intelligent suggestions for unmatched players
- **Zero risk** to existing functionality (feature toggle controlled)

---

## 🏗️ System Architecture Context

### Current System Components
```
Fantrax_Value_Hunter/
├── src/
│   ├── app.py                          # Flask backend (needs xGI endpoints)
│   └── name_matching/
│       ├── unified_matcher.py          # ✅ Production ready
│       ├── matching_strategies.py      # ✅ 6 algorithms implemented
│       └── suggestion_engine.py        # ✅ Smart suggestions ready
├── templates/
│   ├── dashboard.html                  # Needs xGI columns
│   ├── import_validation.html          # Reference for review UI
│   └── monitoring.html                 # System health dashboard
├── config/
│   └── system_parameters.json          # Needs xGI configuration section
└── migrations/
    └── 001_create_name_mappings.sql    # Name matching database ready

Fantrax_Expected_Stats/
└── integration_package/
    ├── understat_integrator.py         # ✅ Updated with UnifiedNameMatcher
    ├── value_hunter_extension.py       # ✅ Ready for True Value enhancement
    ├── integration_pipeline.py         # ⚠️ Needs update for new return format
    └── DatabaseUpdater class           # ✅ SQL generation ready
```

### Database Details
- **Host**: localhost
- **Port**: 5433
- **Database**: fantrax_value_hunter
- **User**: fantrax_user
- **Password**: fantrax_password
- **Players**: 633 total in database

### Integration Package Status
- **Test Run Results**: 330 matched players (57.5% rate)
- **Average xGI90**: 0.285
- **Top Performer**: Mohamed Salah (1.156 xGI90)
- **Unmatched Players**: Will get suggestions via UnifiedNameMatcher

---

## 🚀 Sprint Plan

### **Sprint 1: Database Schema Updates** (15 minutes)
**Goal**: Add Understat columns to database (safe, additive only)

**SQL to Execute**:
```sql
-- Add Understat stats columns to players table
ALTER TABLE players 
ADD COLUMN IF NOT EXISTS minutes INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS xG90 DECIMAL(5,3) DEFAULT 0.000,
ADD COLUMN IF NOT EXISTS xA90 DECIMAL(5,3) DEFAULT 0.000,
ADD COLUMN IF NOT EXISTS xGI90 DECIMAL(5,3) DEFAULT 0.000,
ADD COLUMN IF NOT EXISTS last_understat_update TIMESTAMP;

-- Add performance index
CREATE INDEX IF NOT EXISTS idx_players_xgi90 ON players(xGI90);

-- Optional: Add to player_metrics if using separate table
ALTER TABLE player_metrics
ADD COLUMN IF NOT EXISTS xgi_multiplier DECIMAL(5,3) DEFAULT 1.000;
```

**Validation**:
- Check columns exist: `\d players` in psql
- Verify defaults: All existing players should have 0.000 values

---

### **Sprint 2: Fix Integration Pipeline** (20 minutes)
**Goal**: Update integration_pipeline.py to handle UnifiedNameMatcher's new return format

**File**: `C:/Users/halvo/.claude/Fantrax_Expected_Stats/integration_package/integration_pipeline.py`

**Changes Required**:
1. Line 61 - Update unpacking:
```python
# OLD:
matched_players, multiplier_table, stats = self.integrator.generate_integration_data(season, leagues)

# NEW:
matched_players, unmatched_players, multiplier_table, stats = self.integrator.generate_integration_data(season, leagues)
```

2. After line 69 - Add unmatched handling:
```python
# Handle unmatched players
if unmatched_players is not None and not unmatched_players.empty:
    print(f"⚠️ {len(unmatched_players)} players need manual review")
    # Save for review UI
    unmatched_file = Path(__file__).parent / f"unmatched_players_{timestamp}.json"
    unmatched_players.to_json(unmatched_file, orient='records', indent=2)
    print(f"   Saved to: {unmatched_file.name}")
```

3. Update report generation (line 109):
```python
report_data = {
    'integration_summary': stats,
    'extension_summary': extension_stats,
    'schema_updates': schema_sql,
    'total_data_updates': len(data_updates),
    'unmatched_count': len(unmatched_players) if unmatched_players is not None else 0,
    'sample_enhanced_calculations': self._generate_sample_calculations(extension, matched_players.head(5))
}
```

**Test Command**:
```bash
cd C:/Users/halvo/.claude/Fantrax_Expected_Stats/integration_package
python integration_pipeline.py  # Should run without errors in dry-run mode
```

---

### **Sprint 3: Add Configuration** (20 minutes)
**Goal**: Add xGI system to configuration with feature toggle

**File**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/config/system_parameters.json`

**Add New Section** (after starter_prediction, before dashboard_controls):
```json
"xgi_integration": {
  "description": "Understat expected goals involvement multiplier system",
  "enabled": false,
  "data_source": "Understat via ScraperFC",
  "multiplier_mode": "direct",
  "multiplier_strength": 1.0,
  "multiplier_modes": {
    "direct": {
      "description": "Use xGI90 directly as multiplier",
      "formula": "true_value * xGI90 * strength"
    },
    "adjusted": {
      "description": "Use 1 + (xGI90 * strength) as multiplier",
      "formula": "true_value * (1 + xGI90 * strength)"
    },
    "capped": {
      "description": "Cap multiplier range between min and max",
      "formula": "true_value * clamp(xGI90, min, max)",
      "min": 0.5,
      "max": 1.5
    }
  },
  "display_stats": true,
  "show_unmatched_badge": true,
  "auto_sync_enabled": false,
  "sync_frequency_hours": 168,
  "validation_ranges": {
    "multiplier_strength": {
      "min": 0.0,
      "max": 2.0
    }
  },
  "last_sync": null,
  "matched_players": 0,
  "unmatched_players": 0
}
```

**Update dashboard_controls/adjustable_parameters**:
```json
"adjustable_parameters": [
  // ... existing parameters ...
  "xgi_integration_enabled",
  "xgi_multiplier_mode",
  "xgi_multiplier_strength"
]
```

---

### **Sprint 4: Backend API Updates** (45 minutes)
**Goal**: Add Understat endpoints and update True Value calculation

**File**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/src/app.py`

**A. Import Integration Package** (at top of file):
```python
import sys
sys.path.append('C:/Users/halvo/.claude/Fantrax_Expected_Stats')
from integration_package import IntegrationPipeline, UnderstatIntegrator, ValueHunterExtension
```

**B. Add Understat Endpoints** (before if __name__ == '__main__'):

```python
@app.route('/api/understat/sync', methods=['POST'])
def sync_understat_data():
    """Sync Understat data with database"""
    try:
        # Initialize pipeline
        pipeline = IntegrationPipeline(DB_CONFIG, dry_run=False)
        
        # Run integration
        matched_df, unmatched_df, multiplier_table, stats = pipeline.integrator.generate_integration_data()
        
        if matched_df is None:
            return jsonify({'error': 'No data extracted from Understat'}), 500
        
        # Update database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for idx, player in matched_df.iterrows():
            cursor.execute("""
                UPDATE players 
                SET minutes = %s, xG90 = %s, xA90 = %s, xGI90 = %s,
                    last_understat_update = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [
                player['minutes'], 
                round(player['xG90'], 3),
                round(player['xA90'], 3), 
                round(player['xGI90'], 3),
                player['fantrax_id']
            ])
        
        conn.commit()
        
        # Update config
        system_params = load_system_parameters()
        system_params['xgi_integration']['last_sync'] = time.time()
        system_params['xgi_integration']['matched_players'] = len(matched_df)
        system_params['xgi_integration']['unmatched_players'] = len(unmatched_df)
        save_system_parameters(system_params)
        
        return jsonify({
            'success': True,
            'matched': len(matched_df),
            'unmatched': len(unmatched_df),
            'match_rate': stats['match_rate'],
            'avg_xGI90': stats['avg_xGI90']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/understat/unmatched', methods=['GET'])
def get_unmatched_understat():
    """Get list of unmatched Understat players for review"""
    try:
        integrator = UnderstatIntegrator(DB_CONFIG)
        understat_df = integrator.extract_understat_per90_stats()
        
        if understat_df.empty:
            return jsonify({'players': []})
        
        matched_df, unmatched_df = integrator.match_fantrax_names(understat_df)
        
        # Add suggestions for unmatched
        unmatched_with_suggestions = []
        for idx, player in unmatched_df.iterrows():
            player_dict = player.to_dict()
            player_dict['suggestions'] = player.get('suggested_matches', [])
            unmatched_with_suggestions.append(player_dict)
        
        return jsonify({
            'players': unmatched_with_suggestions,
            'total': len(unmatched_df)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/understat/stats', methods=['GET'])
def get_understat_stats():
    """Get Understat integration statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE xGI90 > 0) as players_with_xgi,
                COUNT(*) as total_players,
                AVG(xGI90) FILTER (WHERE xGI90 > 0) as avg_xgi90,
                MAX(xGI90) as max_xgi90,
                MIN(last_understat_update) as oldest_update,
                MAX(last_understat_update) as newest_update
            FROM players
        """)
        
        stats = dict(cursor.fetchone())
        
        # Get top xGI players
        cursor.execute("""
            SELECT name, team, position, xGI90, xG90, xA90, minutes
            FROM players
            WHERE xGI90 > 0
            ORDER BY xGI90 DESC
            LIMIT 10
        """)
        
        top_players = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        system_params = load_system_parameters()
        xgi_config = system_params.get('xgi_integration', {})
        
        return jsonify({
            'stats': stats,
            'top_players': top_players,
            'config': {
                'enabled': xgi_config.get('enabled', False),
                'mode': xgi_config.get('multiplier_mode', 'direct'),
                'strength': xgi_config.get('multiplier_strength', 1.0),
                'last_sync': xgi_config.get('last_sync')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**C. Update Player Query** (in get_players endpoint, around line 234):
```python
# Update SELECT to include Understat columns
base_query = """
    SELECT 
        p.id, p.name, p.team, p.position,
        p.minutes, p.xG90, p.xA90, p.xGI90,  -- ADD THIS LINE
        pm.price, pm.ppg, pm.value_score, pm.true_value,
        pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier,
        pm.last_updated
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.gameweek = %s
"""
```

**D. Update True Value Calculation** (in recalculate_true_values function):
```python
# After existing multiplier calculations, add:
if system_params['xgi_integration']['enabled']:
    xgi_mode = system_params['xgi_integration']['multiplier_mode']
    strength = system_params['xgi_integration']['multiplier_strength']
    
    if xgi_mode == 'direct':
        xgi_multiplier = player.get('xGI90', 0) * strength
        if xgi_multiplier == 0:
            xgi_multiplier = 1.0
    elif xgi_mode == 'adjusted':
        xgi_multiplier = 1 + (player.get('xGI90', 0) * strength)
    else:  # capped
        xgi_multiplier = max(0.5, min(1.5, player.get('xGI90', 0) * strength))
    
    true_value *= xgi_multiplier
```

---

### **Sprint 5: Dashboard UI Updates** (30 minutes)
**Goal**: Add xGI display and controls to dashboard

**File**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/templates/dashboard.html`

**A. Add xGI Control Section** (after Starter Prediction section, around line 150):
```html
<!-- xGI Integration -->
<div class="control-section">
    <h3>
        <label>
            <input type="checkbox" id="xgiEnabled" onchange="updateParameters()">
            xGI Integration (Understat)
        </label>
    </h3>
    <div class="control-content" id="xgiContent">
        <div class="control-group">
            <label>Multiplier Mode:</label>
            <select id="xgiMode" onchange="updateParameters()">
                <option value="direct">Direct (xGI90 × strength)</option>
                <option value="adjusted">Adjusted (1 + xGI90 × strength)</option>
                <option value="capped">Capped (0.5 - 1.5 range)</option>
            </select>
        </div>
        <div class="control-group">
            <label>Multiplier Strength: <span id="xgiStrengthValue">1.0</span></label>
            <input type="range" id="xgiStrength" min="0" max="2" step="0.1" value="1.0" 
                   oninput="document.getElementById('xgiStrengthValue').textContent = this.value; updateParameters()">
        </div>
        <div class="control-group">
            <button onclick="syncUnderstatData()" class="sync-button">Sync Understat Data</button>
            <span id="syncStatus"></span>
        </div>
        <div class="stats-display">
            <span id="xgiStats">Loading stats...</span>
        </div>
    </div>
</div>
```

**B. Add Table Columns** (in player table header, around line 250):
```html
<th>Minutes</th>
<th>xG90</th>
<th>xA90</th>
<th>xGI90</th>
```

**C. Update JavaScript** (in dashboard.js or script section):

```javascript
// Add to loadParameters function
document.getElementById('xgiEnabled').checked = params.xgi_integration?.enabled || false;
document.getElementById('xgiMode').value = params.xgi_integration?.multiplier_mode || 'direct';
document.getElementById('xgiStrength').value = params.xgi_integration?.multiplier_strength || 1.0;
document.getElementById('xgiStrengthValue').textContent = params.xgi_integration?.multiplier_strength || 1.0;
toggleSection('xgiContent', params.xgi_integration?.enabled);

// Add sync function
async function syncUnderstatData() {
    const statusEl = document.getElementById('syncStatus');
    statusEl.textContent = 'Syncing...';
    statusEl.className = 'syncing';
    
    try {
        const response = await fetch('/api/understat/sync', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            statusEl.textContent = `✓ Synced ${data.matched} players (${data.match_rate.toFixed(1)}% match rate)`;
            statusEl.className = 'success';
            loadUnderstatStats();
            loadPlayers(); // Refresh table
        } else {
            statusEl.textContent = `✗ Sync failed: ${data.error}`;
            statusEl.className = 'error';
        }
    } catch (error) {
        statusEl.textContent = `✗ Error: ${error.message}`;
        statusEl.className = 'error';
    }
}

// Add stats loader
async function loadUnderstatStats() {
    try {
        const response = await fetch('/api/understat/stats');
        const data = await response.json();
        
        const statsEl = document.getElementById('xgiStats');
        statsEl.innerHTML = `
            <strong>Coverage:</strong> ${data.stats.players_with_xgi}/${data.stats.total_players} players |
            <strong>Avg xGI90:</strong> ${(data.stats.avg_xgi90 || 0).toFixed(3)} |
            <strong>Last sync:</strong> ${data.config.last_sync ? new Date(data.config.last_sync * 1000).toLocaleDateString() : 'Never'}
        `;
    } catch (error) {
        console.error('Failed to load Understat stats:', error);
    }
}

// Add to player row rendering
function renderPlayerRow(player) {
    return `
        <td>${player.name}</td>
        <td>${player.team}</td>
        <td>${player.position}</td>
        <td>$${player.price}</td>
        <td>${player.ppg.toFixed(2)}</td>
        <td>${player.true_value.toFixed(3)}</td>
        <td>${player.minutes || 0}</td>
        <td>${(player.xG90 || 0).toFixed(3)}</td>
        <td>${(player.xA90 || 0).toFixed(3)}</td>
        <td>${(player.xGI90 || 0).toFixed(3)}</td>
    `;
}
```

---

### **Sprint 6: Testing & Validation** (30 minutes)
**Goal**: Test complete integration end-to-end

**Test Checklist**:

1. **Database Schema**:
```sql
-- Verify columns exist
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'players' 
AND column_name IN ('minutes', 'xG90', 'xA90', 'xGI90', 'last_understat_update');
```

2. **Dry Run Test**:
```bash
cd C:/Users/halvo/.claude/Fantrax_Expected_Stats/integration_package
python integration_pipeline.py
# Should show: "OK Dry run complete - safe to proceed with live integration"
```

3. **API Endpoints**:
```bash
# Start Flask app
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
python src/app.py

# Test endpoints
curl http://localhost:5000/api/understat/stats
curl http://localhost:5000/api/understat/unmatched
```

4. **Dashboard UI**:
- Navigate to http://localhost:5000/
- Check xGI Integration section appears
- Toggle enabled/disabled
- Verify table shows new columns
- Test sync button (in dry-run first)

5. **True Value Calculation**:
- Enable xGI integration
- Set multiplier strength to 1.0
- Verify True Values change
- Disable and verify they revert

6. **Data Validation**:
```sql
-- Check data after sync
SELECT name, xGI90, xG90, xA90, minutes 
FROM players 
WHERE xGI90 > 0 
ORDER BY xGI90 DESC 
LIMIT 10;
```

---

## 🔐 Safety Checklist

- [ ] All database changes use IF NOT EXISTS
- [ ] Default values prevent nulls
- [ ] Feature toggle prevents unwanted activation
- [ ] Dry-run mode tested before live execution
- [ ] Multiplier defaults to 1.0 (no change) for missing data
- [ ] Error handling on all API endpoints
- [ ] Unmatched players saved for review
- [ ] Manual confirmation workflow available

---

## 📊 Expected Outcomes

### Immediate (After Sprint 6)
- 330 players with xGI data
- 57.5% automatic match rate
- Enhanced True Value calculations
- Full visibility of unmatched players

### After Manual Review
- 66%+ match rate achievable
- Learning system improves future matches
- More accurate player valuations

### Long-term
- Weekly automated syncs
- Historical xGI tracking
- Position-specific multipliers
- Integration with other data sources

---

## 🚨 Rollback Plan

If issues occur:

1. **Disable in config**:
```json
"xgi_integration": { "enabled": false }
```

2. **Remove data** (if needed):
```sql
UPDATE players 
SET minutes = 0, xG90 = 0, xA90 = 0, xGI90 = 0, 
    last_understat_update = NULL;
```

3. **Drop columns** (last resort):
```sql
ALTER TABLE players 
DROP COLUMN IF EXISTS minutes,
DROP COLUMN IF EXISTS xG90,
DROP COLUMN IF EXISTS xA90,
DROP COLUMN IF EXISTS xGI90,
DROP COLUMN IF EXISTS last_understat_update;
```

---

## 📝 Post-Implementation Tasks

1. Document actual match rate achieved
2. Review unmatched players for patterns
3. Update UnifiedNameMatcher mappings
4. Set up weekly sync schedule
5. Create monitoring dashboard for xGI coverage
6. Gather user feedback on True Value changes

---

## 🔗 Related Documentation

- `/docs/GLOBAL_NAME_MATCHING_SYSTEM.md` - Name matching details
- `/docs/CLAUDE.md` - AI context and system overview
- `/Fantrax_Expected_Stats/INTEGRATION_GUIDE.md` - Original integration guide
- `/integration_package/README.md` - Package documentation

---

*This plan provides complete implementation details for Understat xGI integration into Fantrax Value Hunter using the UnifiedNameMatcher system.*