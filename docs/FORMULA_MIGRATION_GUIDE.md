# Formula Migration Guide
## Technical Implementation Details for Fantasy Football Value Hunter v2.0

### **Overview**

This document provides step-by-step technical instructions for implementing the research-based formula optimizations. It covers database changes, code modifications, configuration updates, and testing procedures required to migrate from v1.0 to v2.0.

**Migration Goals:**
- Fix core formula (separate prediction from value)
- Implement exponential decay and dynamic blending
- Add validation framework
- Maintain backward compatibility during transition

---

## **Pre-Migration Checklist**

### **Backup Strategy**

```bash
# 1. Database backup
pg_dump -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter > backup_pre_v2_migration.sql

# 2. Code backup
cp -r /c/Users/halvo/.claude/Fantrax_Value_Hunter /c/Users/halvo/.claude/Fantrax_Value_Hunter_v1_backup

# 3. Configuration backup
cp config/system_parameters.json config/system_parameters_v1_backup.json
```

### **Environment Requirements**

```bash
# Install additional Python dependencies
pip install scipy redis google-generativeai

# Verify database connection
python check_db_structure.py

# Ensure sufficient disk space (minimum 500MB for new tables)
df -h
```

---

## **MIGRATION PHASE 1: Database Schema Updates**

### **Step 1.1: Create Migration Script**

**File**: `migrations/v2_formula_migration.sql`

```sql
-- Fantasy Football Value Hunter v2.0 Migration
-- Implements research-based formula optimizations

BEGIN;

-- Add new columns to players table
ALTER TABLE players ADD COLUMN IF NOT EXISTS true_value DECIMAL(8,2);
ALTER TABLE players ADD COLUMN IF NOT EXISTS roi DECIMAL(8,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS formula_version VARCHAR(10) DEFAULT 'v2.0';
ALTER TABLE players ADD COLUMN IF NOT EXISTS exponential_form_score DECIMAL(5,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS baseline_xgi DECIMAL(5,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS blended_ppg DECIMAL(5,2);
ALTER TABLE players ADD COLUMN IF NOT EXISTS current_season_weight DECIMAL(4,3);

-- Create validation tables
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
    parameters JSONB,
    notes TEXT
);

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

-- Create form tracking table for EWMA
CREATE TABLE IF NOT EXISTS form_scores (
    player_id VARCHAR(50),
    gameweek INTEGER,
    exponential_score DECIMAL(5,3),
    alpha_used DECIMAL(4,3),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, gameweek)
);

-- Create Gemini usage tracking
CREATE TABLE IF NOT EXISTS gemini_usage (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    endpoint VARCHAR(50),
    requests_count INTEGER DEFAULT 1,
    cached_responses INTEGER DEFAULT 0,
    estimated_cost DECIMAL(8,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, endpoint)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_error ON player_predictions(error_abs DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_gameweek ON player_predictions(gameweek);
CREATE INDEX IF NOT EXISTS idx_validation_rmse ON validation_results(rmse);
CREATE INDEX IF NOT EXISTS idx_players_roi ON players(roi DESC);
CREATE INDEX IF NOT EXISTS idx_players_true_value ON players(true_value DESC);
CREATE INDEX IF NOT EXISTS idx_form_scores_player_gw ON form_scores(player_id, gameweek);

-- Create views for analysis
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

-- Add comments for documentation
COMMENT ON COLUMN players.true_value IS 'Pure point prediction (no price factor) - v2.0 formula';
COMMENT ON COLUMN players.roi IS 'Return on Investment: true_value / price';
COMMENT ON COLUMN players.exponential_form_score IS 'EWMA form score using exponential decay';
COMMENT ON COLUMN players.baseline_xgi IS 'Historical xGI baseline for normalization';
COMMENT ON COLUMN players.blended_ppg IS 'Dynamically blended PPG (historical + current)';
COMMENT ON COLUMN players.current_season_weight IS 'Current season weight in blending (0-1)';

-- Initialize baseline xGI for existing players
UPDATE players 
SET baseline_xgi = (
    SELECT AVG(COALESCE(xgi_per90, 0.3))
    FROM (
        -- Use historical data if available, otherwise default
        SELECT 0.3 as xgi_per90  -- Default baseline
    ) as baseline_calc
)
WHERE baseline_xgi IS NULL;

COMMIT;

-- Verify migration
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as players_with_new_columns
FROM players 
WHERE true_value IS NOT NULL OR true_value IS NULL;  -- Check column exists
```

### **Step 1.2: Run Migration**

```bash
# Execute migration
psql -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter -f migrations/v2_formula_migration.sql

# Verify migration success
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, user='fantrax_user', password='fantrax_password', database='fantrax_value_hunter')
cursor = conn.cursor()
cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'players\' AND column_name IN (\'true_value\', \'roi\', \'exponential_form_score\')')
print('New columns:', [row[0] for row in cursor.fetchall()])
conn.close()
"
```

---

## **MIGRATION PHASE 2: Configuration Updates**

### **Step 2.1: Update System Parameters**

**File**: `config/system_parameters.json` - Add v2.0 parameters

```json
{
  "formula_version": "v2.0",
  "migration_status": "in_progress",
  "legacy_support": true,
  
  "form_calculation": {
    "description": "Form tracking parameters - v2.0 with exponential decay",
    "enabled": true,
    "version": "exponential_decay",
    "lookback_period": 5,
    "exponential_decay": {
      "enabled": true,
      "alpha": 0.87,
      "alpha_range": [0.70, 0.995],
      "interpretation": {
        "0.70": "Highly reactive (2-game focus)",
        "0.87": "5-game half-life (recommended)",
        "0.95": "Sticky form (10-game influence)"
      }
    },
    "legacy_weights": {
      "3_games": [0.5, 0.3, 0.2],
      "5_games": [0.4, 0.25, 0.2, 0.1, 0.05]
    },
    "baseline_switchover_gameweek": 10,
    "minimum_games_for_form": 3
  },
  
  "value_calculation": {
    "description": "Enhanced value calculation - v2.0",
    "pure_prediction_mode": true,
    "separate_roi_calculation": true,
    "estimated_games_played": 20,
    "form_multiplier_enabled": true,
    "differential_threshold": 40
  },
  
  "multiplier_caps": {
    "description": "Prevent extreme outlier multipliers",
    "enabled": true,
    "form": 2.0,
    "fixture": 1.8,
    "starter": 1.0,
    "xgi": 2.5,
    "global": 3.0
  },
  
  "fixture_calculation": {
    "description": "Exponential fixture difficulty transformation",
    "version": "exponential",
    "exponential": {
      "enabled": true,
      "base": 1.05,
      "base_range": [1.02, 1.10]
    },
    "legacy_linear": {
      "base_strength": 0.2,
      "position_weights": {
        "G": 1.10,
        "D": 1.20,
        "M": 1.00,
        "F": 1.05
      }
    }
  },
  
  "dynamic_blending": {
    "description": "Smooth transition between historical and current season data",
    "enabled": true,
    "full_adaptation_gw": 16,
    "adaptation_range": [10, 25],
    "show_blend_indicator": true
  },
  
  "xgi_calculation": {
    "description": "Normalized xGI as ratio to baseline",
    "version": "normalized_ratio",
    "enabled": true,
    "normalization": {
      "enabled": true,
      "position_adjustments": {
        "G": 0.0,
        "D": 0.3,
        "M": 1.0,
        "F": 1.0
      },
      "minimum_baseline": 0.1
    },
    "legacy_modes": {
      "capped": true,
      "direct": false,
      "adjusted": false
    }
  },
  
  "validation": {
    "description": "Model validation and backtesting parameters",
    "enabled": true,
    "auto_validation": false,
    "target_metrics": {
      "rmse": 2.85,
      "spearman_correlation": 0.30,
      "precision_at_20": 0.30
    }
  },
  
  "gemini_integration": {
    "description": "AI-powered insights configuration",
    "enabled": false,
    "max_daily_requests": 100,
    "cache_duration_hours": 24,
    "priority_analysis": {
      "min_true_value": 7.0,
      "min_roi": 0.8,
      "extreme_form_threshold": 1.5
    }
  }
}
```

### **Step 2.2: Create Parameter Migration Script**

**File**: `src/migrate_parameters.py`

```python
"""
Migrate system parameters to v2.0 format
Preserves existing user settings while adding new parameters
"""

import json
import os
from typing import Dict, Any

def migrate_parameters():
    """Migrate parameters from v1.0 to v2.0 format"""
    config_path = os.path.join('config', 'system_parameters.json')
    backup_path = os.path.join('config', 'system_parameters_v1_backup.json')
    
    # Load existing parameters
    try:
        with open(config_path, 'r') as f:
            current_params = json.load(f)
        print("✅ Loaded existing parameters")
    except Exception as e:
        print(f"❌ Error loading parameters: {e}")
        return False
    
    # Create backup
    try:
        with open(backup_path, 'w') as f:
            json.dump(current_params, f, indent=2)
        print("✅ Created parameter backup")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False
    
    # Load v2.0 template
    v2_template = get_v2_template()
    
    # Merge parameters (preserve existing values where possible)
    migrated_params = merge_parameters(current_params, v2_template)
    
    # Save migrated parameters
    try:
        with open(config_path, 'w') as f:
            json.dump(migrated_params, f, indent=2)
        print("✅ Migrated parameters to v2.0")
        return True
    except Exception as e:
        print(f"❌ Error saving migrated parameters: {e}")
        return False

def merge_parameters(current: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """Intelligently merge current parameters with v2.0 template"""
    result = template.copy()
    
    # Preserve existing form calculation settings
    if 'form_calculation' in current:
        result['form_calculation']['lookback_period'] = current['form_calculation'].get('lookback_period', 5)
        result['form_calculation']['baseline_switchover_gameweek'] = current['form_calculation'].get('baseline_switchover_gameweek', 10)
    
    # Preserve existing games display settings
    if 'games_display' in current:
        result['dynamic_blending']['full_adaptation_gw'] = current['games_display'].get('transition_period_end', 16)
        result['dynamic_blending']['show_blend_indicator'] = current['games_display'].get('show_historical_data', True)
    
    # Preserve xGI settings
    if 'value_calculation' in current:
        result['xgi_calculation']['enabled'] = current['value_calculation'].get('form_multiplier_enabled', True)
    
    # Mark migration status
    result['formula_version'] = 'v2.0'
    result['migration_status'] = 'completed'
    result['legacy_support'] = True
    
    return result

def get_v2_template() -> Dict[str, Any]:
    """Get v2.0 parameter template"""
    # Return the full v2.0 template from above
    return {
        # ... (full template as shown in Step 2.1)
    }

if __name__ == "__main__":
    success = migrate_parameters()
    if success:
        print("\n🎉 Parameter migration completed successfully!")
        print("📋 Backup saved to: config/system_parameters_v1_backup.json")
    else:
        print("\n❌ Parameter migration failed. Check error messages above.")
```

---

## **MIGRATION PHASE 3: Code Implementation**

### **Step 3.1: Create New Calculation Engine**

**File**: `src/calculation_engine_v2.py`

```python
"""
Enhanced calculation engine for Fantasy Football Value Hunter v2.0
Implements research-based formula optimizations
"""

import math
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple
import json

class FormulaEngineV2:
    def __init__(self, db_config: Dict, parameters: Dict):
        self.db_config = db_config
        self.params = parameters
        self.current_gameweek = self._get_current_gameweek()
        
    def calculate_player_value(self, player_data: Dict) -> Dict:
        """
        Main calculation function for v2.0 formula
        
        Returns:
            {
                'player_id': str,
                'true_value': float,
                'roi': float,
                'blended_ppg': float,
                'multipliers': {
                    'form': float,
                    'fixture': float,
                    'starter': float,
                    'xgi': float
                },
                'metadata': dict
            }
        """
        player_id = player_data['player_id']
        
        # Step 1: Calculate blended baseline PPG
        blended_ppg, current_weight = self._calculate_blended_ppg(player_data)
        
        # Step 2: Calculate all multipliers
        form_mult = self._calculate_exponential_form_multiplier(player_data)
        fixture_mult = self._calculate_exponential_fixture_multiplier(player_data)
        starter_mult = player_data.get('starter_multiplier', 1.0)
        xgi_mult = self._calculate_normalized_xgi_multiplier(player_data)
        
        # Step 3: Calculate True Value (pure prediction)
        true_value = blended_ppg * form_mult * fixture_mult * starter_mult * xgi_mult
        
        # Step 4: Apply global cap
        max_allowed = blended_ppg * self.params.get('multiplier_caps', {}).get('global', 3.0)
        true_value = min(true_value, max_allowed)
        
        # Step 5: Calculate ROI separately
        price = player_data.get('price', 1.0)
        roi = true_value / price if price > 0 else 0
        
        return {
            'player_id': player_id,
            'true_value': round(true_value, 2),
            'roi': round(roi, 3),
            'blended_ppg': round(blended_ppg, 2),
            'current_season_weight': round(current_weight, 3),
            'multipliers': {
                'form': round(form_mult, 3),
                'fixture': round(fixture_mult, 3),
                'starter': round(starter_mult, 3),
                'xgi': round(xgi_mult, 3)
            },
            'metadata': {
                'formula_version': 'v2.0',
                'calculation_time': self._get_current_timestamp(),
                'gameweek': self.current_gameweek
            }
        }
    
    def _calculate_blended_ppg(self, player_data: Dict) -> Tuple[float, float]:
        """
        Calculate dynamically blended PPG using smooth transition
        Research formula: w_current = min(1, (N-1)/(K-1))
        """
        K = self.params.get('dynamic_blending', {}).get('full_adaptation_gw', 16)
        
        # Calculate blending weights
        if self.current_gameweek <= 1:
            w_current, w_historical = 0.0, 1.0
        else:
            w_current = min(1.0, (self.current_gameweek - 1) / (K - 1))
            w_historical = 1.0 - w_current
        
        # Get data sources
        historical_ppg = player_data.get('historical_ppg', 0)
        current_ppg = self._calculate_current_season_ppg(player_data)
        
        # Handle edge cases
        if current_ppg == 0 and self.current_gameweek <= 3:
            return historical_ppg, 0.0
        
        if historical_ppg == 0:
            return current_ppg, 1.0
        
        # Smooth blending
        blended_ppg = w_current * current_ppg + w_historical * historical_ppg
        
        return max(0.1, blended_ppg), w_current
    
    def _calculate_exponential_form_multiplier(self, player_data: Dict) -> float:
        """
        Calculate form using exponential decay (EWMA)
        Research formula: F_N = α × F_(N-1) + (1-α) × P_(N-1)
        """
        recent_games = player_data.get('recent_points', [])
        alpha = self.params.get('form_calculation', {}).get('exponential_decay', {}).get('alpha', 0.87)
        
        if not recent_games:
            return 1.0
        
        # Generate exponential decay weights
        weights = [alpha ** i for i in range(len(recent_games))]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        form_score = sum(points * weight for points, weight in zip(recent_games, normalized_weights))
        
        # Get baseline for normalization
        baseline_ppg, _ = self._calculate_blended_ppg(player_data)
        
        if baseline_ppg > 0:
            form_multiplier = form_score / baseline_ppg
        else:
            form_multiplier = 1.0
        
        # Apply cap
        cap = self.params.get('multiplier_caps', {}).get('form', 2.0)
        return max(0.5, min(cap, form_multiplier))
    
    def _calculate_exponential_fixture_multiplier(self, player_data: Dict) -> float:
        """
        Calculate fixture multiplier using exponential transformation
        Research formula: multiplier = base^(-difficulty_score)
        """
        difficulty_score = player_data.get('fixture_difficulty', 0)
        position = player_data.get('position', 'M')
        
        # Get exponential base
        base = self.params.get('fixture_calculation', {}).get('exponential', {}).get('base', 1.05)
        
        # Position-specific adjustments
        position_weights = {
            'G': 1.1,   # Goalkeepers
            'D': 1.2,   # Defenders
            'M': 1.0,   # Midfielders (baseline)
            'F': 1.05   # Forwards
        }
        
        pos_weight = position_weights.get(position, 1.0)
        
        # Exponential transformation
        # Note: negative difficulty = easier fixture = higher multiplier
        adjusted_score = (-difficulty_score * pos_weight) / 10.0
        fixture_multiplier = base ** adjusted_score
        
        # Apply cap
        cap = self.params.get('multiplier_caps', {}).get('fixture', 1.8)
        return max(0.5, min(cap, fixture_multiplier))
    
    def _calculate_normalized_xgi_multiplier(self, player_data: Dict) -> float:
        """
        Calculate xGI multiplier as ratio to baseline
        Research: xGI_Multiplier = Recent_xGI_per90 / Historical_Baseline_xGI_per90
        """
        recent_xgi_per90 = player_data.get('xgi_per90', 0.3)
        baseline_xgi = player_data.get('baseline_xgi', None)
        position = player_data.get('position', 'M')
        
        # Handle missing baseline
        if baseline_xgi is None or baseline_xgi < 0.1:
            baseline_xgi = self._get_default_xgi_baseline(position)
        
        # Calculate ratio-based multiplier
        if baseline_xgi > 0.1:
            xgi_multiplier = recent_xgi_per90 / baseline_xgi
        else:
            xgi_multiplier = 1.0
        
        # Apply position-specific adjustments
        position_adjustments = self.params.get('xgi_calculation', {}).get('normalization', {}).get('position_adjustments', {})
        pos_factor = position_adjustments.get(position, 1.0)
        
        if pos_factor < 1.0:  # Reduce impact for defenders
            xgi_multiplier = 1.0 + (xgi_multiplier - 1.0) * pos_factor
        
        # Apply cap
        cap = self.params.get('multiplier_caps', {}).get('xgi', 2.5)
        return max(0.5, min(cap, xgi_multiplier))
    
    def _get_default_xgi_baseline(self, position: str) -> float:
        """Get position-appropriate xGI baseline"""
        defaults = {
            'G': 0.05,  # Goalkeepers
            'D': 0.15,  # Defenders
            'M': 0.35,  # Midfielders
            'F': 0.55   # Forwards
        }
        return defaults.get(position, 0.30)
    
    def _calculate_current_season_ppg(self, player_data: Dict) -> float:
        """Calculate current season PPG from games played"""
        games_current = player_data.get('games_current', 0)
        total_points_current = player_data.get('total_points_current', 0)
        
        if games_current > 0:
            return total_points_current / games_current
        return 0.0
    
    def _get_current_gameweek(self) -> int:
        """Get current gameweek from database or parameters"""
        # This would be implemented based on your current gameweek logic
        return self.params.get('current_gameweek', 1)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for metadata"""
        from datetime import datetime
        return datetime.now().isoformat()

class LegacyFormulaEngine:
    """
    Wrapper for v1.0 formula - maintains backward compatibility
    """
    def __init__(self, db_config: Dict, parameters: Dict):
        self.db_config = db_config
        self.params = parameters
    
    def calculate_player_value(self, player_data: Dict) -> Dict:
        """Calculate using v1.0 formula for comparison"""
        # Import your existing calculation logic
        from app import calculate_base_value, calculate_form_multiplier
        
        ppg = player_data.get('ppg', 0)
        price = player_data.get('price', 1.0)
        
        # Original calculation
        base_value = ppg / price if price > 0 else 0
        form_mult = calculate_form_multiplier(player_data.get('player_id'), 1, 3)  # Legacy parameters
        
        # Apply other multipliers (simplified for comparison)
        true_value = base_value * form_mult
        
        return {
            'player_id': player_data['player_id'],
            'true_value': round(true_value, 2),
            'roi': round(true_value, 3),  # Same as true_value in v1.0
            'multipliers': {
                'form': round(form_mult, 3),
                'fixture': 1.0,  # Simplified
                'starter': 1.0,
                'xgi': 1.0
            },
            'metadata': {
                'formula_version': 'v1.0',
                'calculation_time': self._get_current_timestamp()
            }
        }
    
    def _get_current_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
```

### **Step 3.2: Update Main Application**

**File**: `src/app.py` - Add v2.0 integration

```python
# Add imports at top of file
from calculation_engine_v2 import FormulaEngineV2, LegacyFormulaEngine

# Add new calculation endpoint
@app.route('/api/calculate-values-v2', methods=['POST'])
def calculate_values_v2():
    """
    Calculate player values using v2.0 formula
    Supports both v2.0 and legacy v1.0 for comparison
    """
    try:
        data = request.get_json()
        formula_version = data.get('formula_version', 'v2.0')
        compare_versions = data.get('compare_versions', False)
        
        # Load current parameters
        parameters = load_system_parameters()
        
        # Get player data
        players = get_all_players_with_data()
        
        if formula_version == 'v2.0':
            engine = FormulaEngineV2(DB_CONFIG, parameters)
        else:
            engine = LegacyFormulaEngine(DB_CONFIG, parameters)
        
        # Calculate values for all players
        results = []
        for player in players:
            calculation = engine.calculate_player_value(player)
            results.append(calculation)
        
        # Optional: Compare versions
        comparison = None
        if compare_versions and formula_version == 'v2.0':
            legacy_engine = LegacyFormulaEngine(DB_CONFIG, parameters)
            comparison = []
            
            for player in players[:10]:  # Limited comparison for performance
                v2_calc = engine.calculate_player_value(player)
                v1_calc = legacy_engine.calculate_player_value(player)
                
                comparison.append({
                    'player_id': player['player_id'],
                    'name': player.get('name'),
                    'v1_value': v1_calc['true_value'],
                    'v2_value': v2_calc['true_value'],
                    'difference': v2_calc['true_value'] - v1_calc['true_value'],
                    'v2_roi': v2_calc['roi']
                })
        
        # Store calculations in database
        store_calculations(results, formula_version)
        
        return jsonify({
            'success': True,
            'formula_version': formula_version,
            'player_count': len(results),
            'results': results,
            'comparison': comparison,
            'calculation_time': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'formula_version': formula_version
        })

def store_calculations(calculations: List[Dict], version: str):
    """Store calculation results in database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        for calc in calculations:
            cursor.execute("""
                UPDATE players 
                SET 
                    true_value = %s,
                    roi = %s,
                    blended_ppg = %s,
                    current_season_weight = %s,
                    exponential_form_score = %s,
                    formula_version = %s
                WHERE player_id = %s
            """, [
                calc['true_value'],
                calc['roi'],
                calc.get('blended_ppg'),
                calc.get('current_season_weight'),
                calc['multipliers'].get('form'),
                version,
                calc['player_id']
            ])
        
        conn.commit()
        print(f"✅ Stored {len(calculations)} calculations for {version}")
        
    except Exception as e:
        print(f"❌ Error storing calculations: {e}")
        conn.rollback()
    finally:
        conn.close()

# Add version toggle endpoint
@app.route('/api/toggle-formula-version', methods=['POST'])
def toggle_formula_version():
    """Toggle between v1.0 and v2.0 formulas"""
    try:
        data = request.get_json()
        new_version = data.get('version', 'v2.0')
        
        # Update parameters
        parameters = load_system_parameters()
        parameters['formula_version'] = new_version
        parameters['migration_status'] = 'active'
        
        save_success = save_system_parameters(parameters)
        
        if save_success:
            return jsonify({
                'success': True,
                'formula_version': new_version,
                'message': f'Switched to formula {new_version}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save parameters'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

---

## **MIGRATION PHASE 4: Testing & Validation**

### **Step 4.1: Create Test Suite**

**File**: `tests/test_v2_migration.py`

```python
"""
Comprehensive test suite for v2.0 formula migration
Tests all new calculations and ensures backward compatibility
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculation_engine_v2 import FormulaEngineV2, LegacyFormulaEngine
import json

class TestV2Migration(unittest.TestCase):
    
    def setUp(self):
        """Set up test data and parameters"""
        self.db_config = {
            'host': 'localhost',
            'port': 5433,
            'user': 'fantrax_user',
            'password': 'fantrax_password',
            'database': 'fantrax_value_hunter'
        }
        
        # Load test parameters
        with open('../config/system_parameters.json', 'r') as f:
            self.params = json.load(f)
        
        self.engine_v2 = FormulaEngineV2(self.db_config, self.params)
        self.engine_v1 = LegacyFormulaEngine(self.db_config, self.params)
        
        # Test player data
        self.test_player = {
            'player_id': 'test_player_1',
            'name': 'Test Player',
            'position': 'M',
            'price': 8.5,
            'ppg': 6.2,
            'historical_ppg': 5.8,
            'recent_points': [8, 12, 4, 7, 9],
            'fixture_difficulty': -3,
            'xgi_per90': 0.65,
            'baseline_xgi': 0.55,
            'games_current': 5,
            'total_points_current': 31
        }
    
    def test_blended_ppg_calculation(self):
        """Test dynamic blending of historical and current PPG"""
        self.engine_v2.current_gameweek = 8  # Mid-season
        
        blended_ppg, current_weight = self.engine_v2._calculate_blended_ppg(self.test_player)
        
        # Should be blend of historical (5.8) and current (6.2)
        self.assertGreater(blended_ppg, 5.8)
        self.assertLess(blended_ppg, 6.2)
        self.assertGreater(current_weight, 0.0)
        self.assertLess(current_weight, 1.0)
        
        print(f"✅ Blended PPG: {blended_ppg:.2f} (weight: {current_weight:.2f})")
    
    def test_exponential_form_calculation(self):
        """Test exponential decay form multiplier"""
        form_mult = self.engine_v2._calculate_exponential_form_multiplier(self.test_player)
        
        # Should be reasonable multiplier around baseline
        self.assertGreater(form_mult, 0.5)
        self.assertLess(form_mult, 2.5)
        
        # Test with different alpha values
        original_alpha = self.params['form_calculation']['exponential_decay']['alpha']
        
        # Test high alpha (sticky form)
        self.params['form_calculation']['exponential_decay']['alpha'] = 0.95
        high_alpha_mult = self.engine_v2._calculate_exponential_form_multiplier(self.test_player)
        
        # Test low alpha (reactive form)
        self.params['form_calculation']['exponential_decay']['alpha'] = 0.75
        low_alpha_mult = self.engine_v2._calculate_exponential_form_multiplier(self.test_player)
        
        # Restore original
        self.params['form_calculation']['exponential_decay']['alpha'] = original_alpha
        
        print(f"✅ Form multipliers - Standard: {form_mult:.3f}, High α: {high_alpha_mult:.3f}, Low α: {low_alpha_mult:.3f}")
    
    def test_exponential_fixture_calculation(self):
        """Test exponential fixture multiplier"""
        # Test easy fixture
        self.test_player['fixture_difficulty'] = -5
        easy_mult = self.engine_v2._calculate_exponential_fixture_multiplier(self.test_player)
        
        # Test hard fixture
        self.test_player['fixture_difficulty'] = 5
        hard_mult = self.engine_v2._calculate_exponential_fixture_multiplier(self.test_player)
        
        # Test neutral fixture
        self.test_player['fixture_difficulty'] = 0
        neutral_mult = self.engine_v2._calculate_exponential_fixture_multiplier(self.test_player)
        
        # Assertions
        self.assertGreater(easy_mult, neutral_mult)
        self.assertLess(hard_mult, neutral_mult)
        self.assertAlmostEqual(neutral_mult, 1.0, places=1)
        
        print(f"✅ Fixture multipliers - Easy: {easy_mult:.3f}, Neutral: {neutral_mult:.3f}, Hard: {hard_mult:.3f}")
    
    def test_normalized_xgi_calculation(self):
        """Test xGI normalization"""
        xgi_mult = self.engine_v2._calculate_normalized_xgi_multiplier(self.test_player)
        
        # Should be ratio of current to baseline (0.65 / 0.55 ≈ 1.18)
        expected_ratio = 0.65 / 0.55
        self.assertAlmostEqual(xgi_mult, expected_ratio, places=1)
        
        print(f"✅ xGI multiplier: {xgi_mult:.3f} (expected ~{expected_ratio:.3f})")
    
    def test_true_value_vs_roi_separation(self):
        """Test that True Value and ROI are properly separated"""
        # Test expensive player
        expensive_player = self.test_player.copy()
        expensive_player['price'] = 12.0
        expensive_player['ppg'] = 8.0
        
        result_expensive = self.engine_v2.calculate_player_value(expensive_player)
        
        # Test cheap player with same PPG
        cheap_player = self.test_player.copy()
        cheap_player['price'] = 6.0
        cheap_player['ppg'] = 8.0
        
        result_cheap = self.engine_v2.calculate_player_value(cheap_player)
        
        # True Values should be similar (both have same PPG and multipliers)
        self.assertAlmostEqual(
            result_expensive['true_value'], 
            result_cheap['true_value'], 
            places=1
        )
        
        # ROI should be different (cheaper player has better ROI)
        self.assertGreater(result_cheap['roi'], result_expensive['roi'])
        
        print(f"✅ Expensive player - True Value: {result_expensive['true_value']}, ROI: {result_expensive['roi']:.3f}")
        print(f"✅ Cheap player - True Value: {result_cheap['true_value']}, ROI: {result_cheap['roi']:.3f}")
    
    def test_multiplier_caps(self):
        """Test that multiplier caps are working"""
        # Create player with extreme data
        extreme_player = self.test_player.copy()
        extreme_player['recent_points'] = [25, 20, 18, 22]  # Extreme form
        extreme_player['fixture_difficulty'] = -10  # Easiest possible
        extreme_player['xgi_per90'] = 2.0  # Very high
        extreme_player['baseline_xgi'] = 0.3  # Low baseline
        
        result = self.engine_v2.calculate_player_value(extreme_player)
        
        # Check caps
        form_cap = self.params['multiplier_caps']['form']
        fixture_cap = self.params['multiplier_caps']['fixture']
        xgi_cap = self.params['multiplier_caps']['xgi']
        
        self.assertLessEqual(result['multipliers']['form'], form_cap)
        self.assertLessEqual(result['multipliers']['fixture'], fixture_cap)
        self.assertLessEqual(result['multipliers']['xgi'], xgi_cap)
        
        print(f"✅ Caps working - Form: {result['multipliers']['form']:.3f}/{form_cap}, "
              f"Fixture: {result['multipliers']['fixture']:.3f}/{fixture_cap}, "
              f"xGI: {result['multipliers']['xgi']:.3f}/{xgi_cap}")
    
    def test_version_comparison(self):
        """Test comparison between v1.0 and v2.0 calculations"""
        result_v1 = self.engine_v1.calculate_player_value(self.test_player)
        result_v2 = self.engine_v2.calculate_player_value(self.test_player)
        
        # Results should be different (v2.0 improvements)
        self.assertNotEqual(result_v1['true_value'], result_v2['true_value'])
        
        # Both should be reasonable values
        self.assertGreater(result_v1['true_value'], 0)
        self.assertGreater(result_v2['true_value'], 0)
        
        # v2.0 should have more detailed multipliers
        self.assertIn('blended_ppg', result_v2)
        self.assertNotIn('blended_ppg', result_v1)
        
        print(f"✅ Version comparison - v1.0: {result_v1['true_value']}, v2.0: {result_v2['true_value']}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test player with no recent games
        no_games_player = self.test_player.copy()
        no_games_player['recent_points'] = []
        
        result = self.engine_v2.calculate_player_value(no_games_player)
        self.assertEqual(result['multipliers']['form'], 1.0)
        
        # Test player with zero price
        zero_price_player = self.test_player.copy()
        zero_price_player['price'] = 0
        
        result = self.engine_v2.calculate_player_value(zero_price_player)
        self.assertEqual(result['roi'], 0)
        
        # Test player with missing xGI data
        no_xgi_player = self.test_player.copy()
        no_xgi_player['xgi_per90'] = None
        no_xgi_player['baseline_xgi'] = None
        
        result = self.engine_v2.calculate_player_value(no_xgi_player)
        self.assertGreater(result['multipliers']['xgi'], 0)
        
        print("✅ Edge cases handled correctly")

if __name__ == '__main__':
    # Run specific tests
    suite = unittest.TestSuite()
    
    # Add all test methods
    suite.addTest(TestV2Migration('test_blended_ppg_calculation'))
    suite.addTest(TestV2Migration('test_exponential_form_calculation'))
    suite.addTest(TestV2Migration('test_exponential_fixture_calculation'))
    suite.addTest(TestV2Migration('test_normalized_xgi_calculation'))
    suite.addTest(TestV2Migration('test_true_value_vs_roi_separation'))
    suite.addTest(TestV2Migration('test_multiplier_caps'))
    suite.addTest(TestV2Migration('test_version_comparison'))
    suite.addTest(TestV2Migration('test_edge_cases'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n🎉 All migration tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
```

### **Step 4.2: Run Migration Tests**

```bash
# Run migration tests
cd tests
python test_v2_migration.py

# Expected output:
# test_blended_ppg_calculation ... ok
# test_exponential_fixture_calculation ... ok
# test_exponential_form_calculation ... ok
# test_multiplier_caps ... ok
# test_normalized_xgi_calculation ... ok
# test_true_value_vs_roi_separation ... ok
# test_version_comparison ... ok
# test_edge_cases ... ok
# 
# 🎉 All migration tests passed!
```

---

## **MIGRATION PHASE 5: Dashboard Integration**

### **Step 5.1: Update Dashboard JavaScript**

**File**: `static/js/dashboard.js` - Add v2.0 support

```javascript
// Add version toggle functionality
class FormulaVersionManager {
    constructor() {
        this.currentVersion = 'v2.0';
        this.setupVersionToggle();
        this.loadVersionStatus();
    }
    
    setupVersionToggle() {
        const toggleButton = document.createElement('button');
        toggleButton.id = 'version-toggle';
        toggleButton.className = 'version-toggle-btn';
        toggleButton.innerHTML = '🔄 Switch to v1.0';
        toggleButton.onclick = () => this.toggleVersion();
        
        document.querySelector('.dashboard-header').appendChild(toggleButton);
    }
    
    async toggleVersion() {
        const newVersion = this.currentVersion === 'v2.0' ? 'v1.0' : 'v2.0';
        
        try {
            const response = await fetch('/api/toggle-formula-version', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({version: newVersion})
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentVersion = newVersion;
                this.updateVersionDisplay();
                this.refreshPlayerTable();
                this.showVersionMessage(result.message);
            } else {
                console.error('Version toggle failed:', result.error);
            }
        } catch (error) {
            console.error('Version toggle error:', error);
        }
    }
    
    updateVersionDisplay() {
        const toggleBtn = document.getElementById('version-toggle');
        const targetVersion = this.currentVersion === 'v2.0' ? 'v1.0' : 'v2.0';
        toggleBtn.innerHTML = `🔄 Switch to ${targetVersion}`;
        
        // Update version badge
        const versionBadge = document.querySelector('.version-badge');
        if (versionBadge) {
            versionBadge.textContent = this.currentVersion;
            versionBadge.className = `version-badge ${this.currentVersion === 'v2.0' ? 'v2' : 'v1'}`;
        }
    }
    
    showVersionMessage(message) {
        const notification = document.createElement('div');
        notification.className = 'version-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    async loadVersionStatus() {
        try {
            const response = await fetch('/api/get-formula-version');
            const result = await response.json();
            
            if (result.success) {
                this.currentVersion = result.version;
                this.updateVersionDisplay();
            }
        } catch (error) {
            console.error('Error loading version status:', error);
        }
    }
    
    async refreshPlayerTable() {
        // Trigger recalculation with current version
        const response = await fetch('/api/calculate-values-v2', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                formula_version: this.currentVersion,
                compare_versions: false
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updatePlayerTable(result.results);
        }
    }
}

// Enhanced table display for v2.0 features
function updatePlayerTable(players) {
    const tableBody = document.getElementById('player-table-body');
    tableBody.innerHTML = '';
    
    players.forEach(player => {
        const row = createPlayerRow(player);
        tableBody.appendChild(row);
    });
}

function createPlayerRow(player) {
    const row = document.createElement('tr');
    row.dataset.playerId = player.player_id;
    
    // Determine if this is v2.0 data
    const isV2 = player.metadata?.formula_version === 'v2.0';
    
    row.innerHTML = `
        <td class="player-name">${player.name || 'Unknown'}</td>
        <td class="position">${player.position || ''}</td>
        <td class="team">${player.team || ''}</td>
        <td class="price">£${player.price || 0}m</td>
        
        <!-- True Value column -->
        <td class="true-value ${isV2 ? 'v2-value' : 'v1-value'}">
            ${player.true_value?.toFixed(1) || '0.0'}
            ${isV2 ? '<span class="v2-badge">v2</span>' : ''}
        </td>
        
        <!-- ROI column (highlighted for v2.0) -->
        <td class="roi ${isV2 ? 'v2-roi' : 'v1-roi'}">
            ${player.roi?.toFixed(2) || '0.00'}
            ${isV2 && player.roi !== player.true_value ? '<span class="roi-indicator">💰</span>' : ''}
        </td>
        
        <!-- Blended PPG (v2.0 only) -->
        <td class="blended-ppg">
            ${isV2 && player.blended_ppg ? 
                `${player.blended_ppg.toFixed(1)} 
                 <span class="blend-weight" title="Current season weight: ${(player.current_season_weight * 100).toFixed(0)}%">
                    ⚖️
                 </span>` : 
                (player.ppg?.toFixed(1) || '0.0')
            }
        </td>
        
        <!-- Enhanced multiplier displays -->
        <td class="form-multiplier ${getMultiplierClass(player.multipliers?.form)}">
            ${player.multipliers?.form?.toFixed(3) || '1.000'}
            ${isV2 ? '<span class="v2-indicator">📈</span>' : ''}
        </td>
        
        <td class="fixture-multiplier ${getMultiplierClass(player.multipliers?.fixture)}">
            ${player.multipliers?.fixture?.toFixed(3) || '1.000'}
        </td>
        
        <td class="xgi-multiplier ${getMultiplierClass(player.multipliers?.xgi)}">
            ${player.multipliers?.xgi?.toFixed(3) || '1.000'}
            ${isV2 ? '<span class="normalized-indicator" title="Normalized to baseline">🎯</span>' : ''}
        </td>
        
        <td class="games">${player.games_display || '0'}</td>
    `;
    
    return row;
}

function getMultiplierClass(value) {
    if (!value) return 'mult-neutral';
    if (value >= 1.5) return 'mult-very-high';
    if (value >= 1.2) return 'mult-high';
    if (value >= 1.1) return 'mult-good';
    if (value <= 0.7) return 'mult-low';
    if (value <= 0.8) return 'mult-poor';
    return 'mult-neutral';
}

// Initialize version management when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.versionManager = new FormulaVersionManager();
});
```

### **Step 5.2: Add CSS for v2.0 Features**

**File**: `static/css/dashboard.css` - Add v2.0 styling

```css
/* Version toggle button */
.version-toggle-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.9em;
    margin-left: 15px;
}

.version-toggle-btn:hover {
    background: #218838;
}

/* Version badges */
.version-badge.v2 {
    background: #007bff;
}

.version-badge.v1 {
    background: #6c757d;
}

/* v2.0 value indicators */
.v2-value {
    background: linear-gradient(135deg, #e3f2fd 0%, #f8f9fa 100%);
    font-weight: bold;
    position: relative;
}

.v2-badge {
    background: #007bff;
    color: white;
    font-size: 0.7em;
    padding: 2px 4px;
    border-radius: 3px;
    margin-left: 5px;
}

.v2-roi {
    background: linear-gradient(135deg, #e8f5e8 0%, #f8f9fa 100%);
    font-weight: bold;
}

.roi-indicator {
    margin-left: 5px;
    font-size: 0.8em;
}

/* Blended PPG indicators */
.blend-weight {
    margin-left: 5px;
    opacity: 0.7;
    cursor: help;
}

/* Enhanced multiplier styling */
.mult-very-high { 
    background: #c8e6c9; 
    color: #1b5e20; 
    font-weight: bold; 
}

.mult-high { 
    background: #dcedc8; 
    color: #2e7d32; 
}

.mult-good { 
    background: #f1f8e9; 
    color: #558b2f; 
}

.mult-neutral { 
    background: #f5f5f5; 
    color: #424242; 
}

.mult-poor { 
    background: #ffebee; 
    color: #c62828; 
}

.mult-low { 
    background: #ffcdd2; 
    color: #d32f2f; 
}

/* v2.0 multiplier indicators */
.v2-indicator {
    font-size: 0.7em;
    margin-left: 3px;
    opacity: 0.8;
}

.normalized-indicator {
    font-size: 0.7em;
    margin-left: 3px;
    opacity: 0.8;
}

/* Version notification */
.version-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #28a745;
    color: white;
    padding: 10px 20px;
    border-radius: 5px;
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Comparison mode styling */
.comparison-mode .true-value {
    border-left: 3px solid #007bff;
}

.comparison-mode .roi {
    border-left: 3px solid #28a745;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .version-toggle-btn {
        font-size: 0.8em;
        padding: 6px 12px;
    }
    
    .v2-badge,
    .v2-indicator,
    .normalized-indicator {
        display: none;
    }
}
```

---

## **MIGRATION PHASE 6: Final Validation**

### **Step 6.1: Performance Testing**

**File**: `tests/test_performance.py`

```python
"""
Performance testing for v2.0 migration
Ensures calculation times remain under 3 seconds
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculation_engine_v2 import FormulaEngineV2
import json

def test_calculation_performance():
    """Test that v2.0 calculations meet performance requirements"""
    
    # Load parameters
    with open('../config/system_parameters.json', 'r') as f:
        params = json.load(f)
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }
    
    engine = FormulaEngineV2(db_config, params)
    
    # Create test dataset (simulate 633 Premier League players)
    test_players = []
    for i in range(633):
        test_players.append({
            'player_id': f'player_{i}',
            'name': f'Player {i}',
            'position': ['G', 'D', 'D', 'D', 'M', 'M', 'M', 'F'][i % 8],
            'price': 4.0 + (i % 10) * 0.8,
            'ppg': 2.0 + (i % 15) * 0.4,
            'historical_ppg': 2.1 + (i % 15) * 0.35,
            'recent_points': [(i % 12) + 2, (i % 8) + 4, (i % 10) + 3],
            'fixture_difficulty': (i % 21) - 10,
            'xgi_per90': 0.1 + (i % 10) * 0.08,
            'baseline_xgi': 0.15 + (i % 8) * 0.06,
            'games_current': (i % 5) + 1,
            'total_points_current': (i % 25) + 5
        })
    
    # Performance test
    start_time = time.time()
    
    results = []
    for player in test_players:
        result = engine.calculate_player_value(player)
        results.append(result)
    
    end_time = time.time()
    calculation_time = end_time - start_time
    
    # Assertions
    assert len(results) == 633, f"Expected 633 results, got {len(results)}"
    assert calculation_time < 3.0, f"Calculation took {calculation_time:.2f}s, expected < 3.0s"
    
    # Check result quality
    valid_results = [r for r in results if r['true_value'] > 0]
    assert len(valid_results) > 600, f"Only {len(valid_results)} valid results"
    
    print(f"✅ Performance test passed!")
    print(f"   - Calculated 633 players in {calculation_time:.2f} seconds")
    print(f"   - Average time per player: {(calculation_time/633)*1000:.1f}ms")
    print(f"   - Valid results: {len(valid_results)}/633")
    
    return True

if __name__ == "__main__":
    success = test_calculation_performance()
    if success:
        print("\n🎉 Performance requirements met!")
    else:
        print("\n❌ Performance test failed!")
```

### **Step 6.2: Data Integrity Check**

**File**: `scripts/validate_migration.py`

```python
"""
Validate data integrity after migration
"""

import psycopg2
import psycopg2.extras

def validate_migration_integrity():
    """Check that migration completed successfully"""
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("🔍 Validating migration integrity...")
    
    # Check new columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'players' 
        AND column_name IN ('true_value', 'roi', 'blended_ppg', 'exponential_form_score')
    """)
    new_columns = [row['column_name'] for row in cursor.fetchall()]
    
    expected_columns = ['true_value', 'roi', 'blended_ppg', 'exponential_form_score']
    missing_columns = [col for col in expected_columns if col not in new_columns]
    
    if missing_columns:
        print(f"❌ Missing columns: {missing_columns}")
        return False
    else:
        print("✅ All new columns present")
    
    # Check new tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('player_predictions', 'validation_results', 'form_scores')
    """)
    new_tables = [row['table_name'] for row in cursor.fetchall()]
    
    expected_tables = ['player_predictions', 'validation_results', 'form_scores']
    missing_tables = [table for table in expected_tables if table not in new_tables]
    
    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        return False
    else:
        print("✅ All new tables present")
    
    # Check data quality
    cursor.execute("SELECT COUNT(*) as count FROM players WHERE true_value IS NOT NULL")
    players_with_values = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM players")
    total_players = cursor.fetchone()['count']
    
    if players_with_values == 0:
        print("⚠️ No players have calculated True Values yet")
    else:
        print(f"✅ {players_with_values}/{total_players} players have True Values")
    
    # Check ROI separation
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM players 
        WHERE true_value IS NOT NULL 
        AND roi IS NOT NULL 
        AND ABS(true_value - roi) > 0.1
    """)
    separated_values = cursor.fetchone()['count']
    
    if separated_values > 0:
        print(f"✅ {separated_values} players show True Value ≠ ROI (formula separation working)")
    else:
        print("⚠️ True Value and ROI appear identical (check separation logic)")
    
    # Check multiplier ranges
    cursor.execute("""
        SELECT 
            MIN(exponential_form_score) as min_form,
            MAX(exponential_form_score) as max_form,
            AVG(exponential_form_score) as avg_form
        FROM players 
        WHERE exponential_form_score IS NOT NULL
    """)
    form_stats = cursor.fetchone()
    
    if form_stats and form_stats['avg_form']:
        print(f"✅ Form multiplier stats - Min: {form_stats['min_form']:.3f}, "
              f"Max: {form_stats['max_form']:.3f}, Avg: {form_stats['avg_form']:.3f}")
    else:
        print("⚠️ No form multiplier data found")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = validate_migration_integrity()
    if success:
        print("\n🎉 Migration validation completed!")
    else:
        print("\n❌ Migration validation failed!")
```

---

## **Post-Migration Checklist**

### **Step 7.1: Deployment Verification**

```bash
# 1. Run all tests
python tests/test_v2_migration.py
python tests/test_performance.py
python scripts/validate_migration.py

# 2. Start application and verify
python src/app.py

# 3. Test API endpoints
curl -X POST http://localhost:5000/api/calculate-values-v2 \
     -H "Content-Type: application/json" \
     -d '{"formula_version": "v2.0"}'

# 4. Test version toggle
curl -X POST http://localhost:5000/api/toggle-formula-version \
     -H "Content-Type: application/json" \
     -d '{"version": "v1.0"}'

# 5. Verify dashboard loads correctly
# Navigate to http://localhost:5000 and test features
```

### **Step 7.2: Performance Monitoring**

```bash
# Monitor calculation times
tail -f logs/calculation_performance.log

# Monitor database performance
psql -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter -c "
SELECT 
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements 
WHERE query LIKE '%true_value%' 
ORDER BY total_time DESC 
LIMIT 10;"
```

### **Step 7.3: User Documentation Update**

**File**: `docs/V2_USER_GUIDE.md`

```markdown
# Fantasy Football Value Hunter v2.0 - User Guide

## What's New in v2.0

### 🎯 **Separated Prediction from Value**
- **True Value**: Pure point prediction (no price factor)
- **ROI**: Value for money (True Value ÷ Price)

### 📈 **Enhanced Form Calculation**
- Exponential decay weighting (recent games weighted higher)
- Configurable decay factor (α = 0.87 default)
- More responsive to form changes

### ⚖️ **Dynamic Data Blending**
- Smooth transition from historical to current season data
- No more hard cutoffs at GW10/GW15
- Visual indicator shows current blend ratio

### 🎯 **Improved xGI Integration**
- Normalized against player's baseline
- Position-specific adjustments
- Better scaling with other multipliers

### 🔧 **Advanced Controls**
- Parameter sliders for fine-tuning
- Formula version toggle (v1.0 ↔ v2.0)
- Multiplier caps prevent extreme values

## Using v2.0 Features

### Reading the New Columns
- **True Value**: How many points the player is predicted to score
- **ROI**: How many points you get per £1M spent
- **Blended PPG**: Base calculation showing historical/current mix

### Parameter Controls
- **Form Decay (α)**: Controls form reactivity (0.70-0.995)
- **Fixture Impact**: How much fixtures affect predictions
- **Adaptation GW**: When to fully trust current season data

### Comparing Versions
Use the version toggle to compare v1.0 vs v2.0 calculations for the same players.
```

---

## **Rollback Plan**

### **Emergency Rollback Procedure**

```bash
# If migration causes issues, rollback using:

# 1. Restore v1.0 parameters
cp config/system_parameters_v1_backup.json config/system_parameters.json

# 2. Switch application to v1.0 mode
curl -X POST http://localhost:5000/api/toggle-formula-version \
     -H "Content-Type: application/json" \
     -d '{"version": "v1.0"}'

# 3. If database issues, restore backup
psql -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter < backup_pre_v2_migration.sql

# 4. Restart application
python src/app.py
```

---

## **Success Metrics**

### **Technical Metrics**
- [ ] All calculations complete within 3 seconds
- [ ] No database errors or connection issues
- [ ] All tests passing (8/8 test cases)
- [ ] Memory usage within acceptable limits

### **Formula Metrics**
- [ ] True Value ≠ ROI for most players (separation working)
- [ ] Multipliers within expected ranges (0.5-2.5)
- [ ] Exponential decay producing different results than fixed weights
- [ ] Dynamic blending showing smooth transitions

### **User Experience Metrics**
- [ ] Dashboard loads without errors
- [ ] Version toggle working correctly
- [ ] Parameter controls responsive
- [ ] No significant performance degradation

---

## **Conclusion**

This migration guide provides a comprehensive, step-by-step approach to implementing the research-based formula optimizations. The phased approach ensures system stability while introducing significant improvements in prediction accuracy and user experience.

**Key Migration Benefits:**
- Mathematically sound formula improvements
- Better prediction accuracy (target: RMSE < 2.85)
- Enhanced user interface and controls
- Comprehensive validation framework
- Backward compatibility during transition

**Post-Migration:**
- Run validation tests regularly
- Monitor performance metrics
- Gather user feedback
- Plan for Sprint 2 advanced features

The migration preserves all existing functionality while adding the foundation for continued optimization through the sprint plan.