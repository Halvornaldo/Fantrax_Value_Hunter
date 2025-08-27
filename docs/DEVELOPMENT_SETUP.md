# Development Setup Guide - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter Development Environment

### **System Status: V2.0 Production Environment + Enterprise Gameweek Management**

This document describes the complete development setup for the V2.0 Enhanced Formula system with unified gameweek management. The system has been consolidated to a single V2.0 engine with enterprise-grade gameweek consistency.

**Development Environment**: Windows MINGW64  
**Current System**: V2.0 Enhanced Formula + GameweekManager fully operational  
**Gameweek Management**: 100% unified detection across all functions

---

## **Prerequisites**

### **Required Software**
- **Python**: 3.8+ (verified compatible)
- **PostgreSQL**: Version 12+ with custom port 5433
- **Git**: For version control
- **Node.js**: For any frontend build tools (optional)

### **System Requirements**
- **Memory**: 8GB RAM recommended for full dataset processing
- **Storage**: 5GB for database, application files, and development tools
- **Network**: Internet access for Understat integration and external data sources

---

## **Quick Start - V2.0 Enhanced System**

### **1. Repository Setup**
```bash
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
git status  # Verify clean working directory
```

### **2. Python Environment Setup**

**Virtual Environment (Recommended)**:
```bash
# Create isolated environment
python -m venv fantrax_v2_env

# Activate environment (Windows)
fantrax_v2_env\Scripts\activate

# Activate environment (Linux/Mac)
source fantrax_v2_env/bin/activate
```

**Install V2.0 Dependencies**:
```bash
pip install -r requirements.txt

# Core V2.0 dependencies
pip install psycopg2-binary    # PostgreSQL adapter
pip install flask             # Web framework (V2.0 enhanced)
pip install pandas            # Data manipulation
pip install numpy             # V2.0 mathematical calculations
pip install requests          # API integrations
pip install scraperfc         # Understat data for xGI baselines
pip install python-dateutil   # Date processing
```

### **3. V2.0 Database Setup**

**Connection Details**:
- **Host**: `localhost`
- **Port**: `5433` (custom port for isolation)
- **Database**: `fantrax_value_hunter`
- **User**: `fantrax_user`
- **Password**: `fantrax_password`

**V2.0 Database Verification**:
```bash
python check_db_structure.py
```

**Expected V2.0 Output**:
```
✅ Database connection successful
🎯 647 Premier League players loaded
✅ V2.0 schema complete: true_value, roi, blended_ppg columns present
✅ Baseline data: 335 players with baseline_xgi for normalized calculations
✅ Historical data: 2024-25 season data integrated for dynamic blending
```

**V2.0 Data Initialization** (for fresh setups):
```bash
# Initialize V2.0 enhanced player database
python initialize_v2_players.py

# Populate 2024-25 historical data for dynamic blending
python import_historical_season_data.py

# Set up xGI baseline data for normalized calculations
python sync_understat_baselines.py

# Initialize exponential fixture difficulty system
python setup_v2_fixture_system.py
```

### **4. V2.0 Configuration Management**

**System Parameters**:
- **File**: `config/system_parameters.json`
- **V2.0 Structure**: Enhanced parameter organization
- **Management**: Dashboard-controlled (no manual editing)

**V2.0 Enhanced Configuration Structure with Starter System**:
```json
{
  "formula_optimization_v2": {
    "exponential_form": {
      "enabled": true,
      "alpha": 0.87
    },
    "dynamic_blending": {
      "enabled": true,
      "full_adaptation_gw": 12
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
  "starter_prediction": {
    "auto_rotation_penalty": 0.75,
    "force_bench_penalty": 0.6,
    "force_out_penalty": 0.0
  },
  "formula_toggles": {
    "form_enabled": true,
    "fixture_enabled": true,
    "starter_enabled": true,
    "xgi_enabled": true
  },
  "multiplier_caps": {
    "form": 2.0,
    "fixture": 1.8,
    "xgi": 2.5,
    "global": 3.0
  }
}
```

**Configuration Files Structure**:
```bash
config/
├── system_parameters.json     # V2.0 enhanced parameters
├── api_keys.json             # External API credentials
└── database_config.json      # Database connection settings
```

### **5. Launch V2.0 Application**

**Start V2.0 Enhanced Server**:
```bash
python src/app.py
```

**Access V2.0 Dashboard**:
- **URL**: `http://localhost:5001`
- **Expected Interface**: V2.0 Enhanced Formula dashboard
- **Status Indicators**: "⚡ V2.0 Ready" and "🎯 647 players loaded"
- **Features**: True Value/ROI columns, dynamic blending display, exponential controls

---

## **V2.0 Development Tools**

### **V2.0 Enhanced Database Management**

**V2.0 Structure Verification**:
```bash
python check_v2_db_structure.py    # V2.0 schema validation
python check_v2_calculations.py    # V2.0 formula verification
python validate_v2_data.py         # V2.0 data quality checks
```

**V2.0 Schema Management**:
```bash
python run_v2_migrations.py        # Apply V2.0 schema updates
python verify_v2_integrity.py      # Validate V2.0 data integrity
```

### **V2.0 Testing Framework**

**Core V2.0 Functionality Testing**:
```bash
# Test V2.0 Enhanced Formula calculations
python test_v2_enhanced_engine.py

# Expected output:
# ✅ Dynamic blending: PASSED (18.2% current + 81.8% historical @ GW3)
# ✅ EWMA form calculation: PASSED (α=0.87)
# ✅ Exponential fixtures: PASSED (base^-difficulty)
# ✅ Normalized xGI: PASSED (ratio-based)
# ✅ V2.0 engine fully validated
```

**V2.0 API Testing with Starter System**:
```bash
# Test V2.0 enhanced endpoints with Starter system
curl -X POST http://localhost:5001/api/calculate-values-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "formula_version": "v2.0",
    "gameweek": 2,
    "features": {
      "dynamic_blending": true,
      "exponential_form": true,
      "normalized_xgi": true,
      "exponential_fixtures": true,
      "starter_prediction": true
    }
  }'

# Test V2.0 player data endpoint
curl "http://localhost:5001/api/players?limit=10&sort_by=true_value"

# Test Starter system endpoints
curl "http://localhost:5001/api/verify-starter-status"
curl -X POST "http://localhost:5001/api/manual-override" \
  -H "Content-Type: application/json" \
  -d '{"player_id": "P123456", "override_type": "starter"}'
```

**V2.0 Dashboard Testing with Starter System**:
- Dashboard loads at `http://localhost:5001`
- V2.0 Enhanced Formula controls respond
- True Value and ROI columns display properly
- Player table shows 647 players with V2.0 calculations
- Dynamic blending display format ("27+1", "38+2")
- **Starter System Integration**:
  - 5-button manual override system (S/R/B/O/A) functional
  - 3 penalty control sliders (Rotation/Bench/Out) responsive
  - 4 formula toggle switches (Form/Fixture/Starter/xGI) working
  - CSV lineup import button accessible
  - Real-time V2.0 recalculation on all changes
- Import workflows accessible at `/form-upload` and `/odds-upload`

### **V2.0 Feature Validation**

**Dynamic Blending System Testing**:
```bash
python -c "
from calculation_engine_v2 import FormulaEngineV2
engine = FormulaEngineV2()

# Test early season blending (GW3) - Updated for GW12 adaptation
test_player = {
    'games_played': 2,
    'ppg': 15.0,
    'total_points_historical': 216,
    'games_played_historical': 27
}

blended_ppg, weight = engine._calculate_dynamic_blending(test_player, 3)
print(f'Blended PPG: {blended_ppg:.2f}')
print(f'Current weight: {weight:.3f} (18.2% expected with GW12 adaptation)')
"
```

**EWMA Form Testing**:
```bash
python -c "
from calculation_engine_v2 import FormulaEngineV2
engine = FormulaEngineV2()

# Test exponential form calculation
recent_points = [8.5, 7.2, 9.1, 6.8, 8.0]
baseline_ppg = 8.0
alpha = 0.87

form_multiplier = engine._calculate_exponential_form(recent_points, baseline_ppg, alpha)
print(f'EWMA form multiplier: {form_multiplier:.3f}')
"
```

**Normalized xGI Testing**:
```bash
python -c "
from calculation_engine_v2 import FormulaEngineV2
engine = FormulaEngineV2()

# Test normalized xGI calculation
test_cases = [
    {'name': 'Ben White', 'xgi90': 0.099, 'baseline_xgi': 0.142, 'position': 'D'},
    {'name': 'Calafiori', 'xgi90': 1.041, 'baseline_xgi': 0.108, 'position': 'D'},
    {'name': 'Haaland', 'xgi90': 1.845, 'baseline_xgi': 2.064, 'position': 'F'}
]

for player in test_cases:
    xgi_mult = engine._calculate_normalized_xgi(player)
    print(f'{player[\"name\"]}: {xgi_mult:.3f}x')
"
```

---

## **V2.0 File Structure**

### **Core V2.0 Application Files**
```
src/
├── app.py                          # V2.0 Enhanced Flask application
├── calculation_engine_v2.py        # V2.0 Enhanced Formula engine
├── db_manager_v2.py               # V2.0 database management
├── fixture_difficulty_v2.py       # Exponential difficulty calculation
├── form_tracker_v2.py             # EWMA form calculation
└── name_matching/                  # Enhanced name matching system
    ├── unified_matcher_v2.py       # V2.0 matching service
    ├── matching_strategies.py      # Advanced matching algorithms
    └── suggestion_engine_v2.py     # AI-powered suggestions
```

### **V2.0 Enhanced Frontend**
```
templates/
├── dashboard.html                  # V2.0 Enhanced dashboard UI
├── form_upload.html               # Enhanced CSV upload interface
├── odds_upload.html               # V2.0 odds upload interface
└── import_validation.html         # Enhanced validation interface

static/
├── css/
│   ├── dashboard_v2.css           # V2.0 enhanced styling
│   └── components_v2.css          # V2.0 component styles
└── js/
    ├── dashboard_v2.js            # V2.0 enhanced frontend logic
    ├── calculations_v2.js         # V2.0 calculation helpers
    └── api_client_v2.js           # V2.0 API client
```

### **V2.0 Configuration**
```
config/
├── system_parameters.json         # V2.0 enhanced parameters
├── v2_feature_flags.json         # V2.0 feature toggles
└── calculation_constants.json     # V2.0 mathematical constants
```

---

## **V2.0 Development Workflow**

### **1. V2.0 Feature Development**
1. **Code Changes**: Implement V2.0 enhanced features
2. **Local Testing**: Test with V2.0 server at `http://localhost:5001`
3. **Formula Validation**: Verify V2.0 calculations match expected results
4. **Database Verification**: Check V2.0 schema changes with verification scripts
5. **Performance Testing**: Ensure 647-player dataset processes efficiently

### **2. V2.0 Database Changes**
1. **Migration Creation**: Create V2.0 migration SQL in `migrations/v2/`
2. **Migration Execution**: Run with `python run_v2_migration.py`
3. **Schema Verification**: Validate with `python check_v2_db_structure.py`
4. **Data Validation**: Test V2.0 calculations work with new schema

### **3. V2.0 Parameter Management**
- **Dashboard Controls**: Edit parameters via V2.0 enhanced interface
- **Real-time Updates**: Changes apply immediately with V2.0 recalculation
- **Persistence**: V2.0 settings saved to `config/system_parameters.json`
- **Validation**: Parameter ranges validated for V2.0 formula stability

---

## **V2.0 Enhanced Testing Procedures**

### **Name Matching System Testing** ✅ VERIFIED (2025-08-23)
**Complete Name Matching Workflow Test**:
```bash
# 1. Start server
python src/app.py

# 2. Test Understat sync with name matching
curl -X POST http://localhost:5001/api/understat/sync
# Expected: 98%+ match rate, unmatched players flagged

# 3. Verify unmatched data for manual review
curl -X GET http://localhost:5001/api/understat/get-unmatched-data
# Expected: Structured validation data with original names
```

**Frontend Upload Testing** ✅ VERIFIED (2025-08-23):
- Form upload page navigation: ✅ Working
- File upload mechanism: ✅ Working  
- CSV validation and processing: ✅ Working
- Error handling (missing columns): ✅ Working
- Success confirmation display: ✅ Working

### **🎯 NEW: Starter System Testing (2025-08-26)**

**Complete Starter System Workflow Testing**:
The system now includes comprehensive Starter system controls with configurable penalties and manual overrides.

**Starter System Test Workflow**:
```bash
# 1. Test CSV lineup import
curl -X POST "http://localhost:5001/api/import-lineups" \
  -F "lineups_csv=@lineup_predictions.csv"
# Expected: Player status assignments (Starter/Rotation/Bench/Out)

# 2. Test manual override system
curl -X POST "http://localhost:5001/api/manual-override" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "P123456", 
    "override_type": "rotation"
  }'
# Expected: Instant V2.0 True Value recalculation

# 3. Test penalty configuration
curl -X POST "http://localhost:5001/api/update-parameters" \
  -H "Content-Type: application/json" \
  -d '{
    "starter_prediction": {
      "auto_rotation_penalty": 0.8,
      "force_bench_penalty": 0.5,
      "force_out_penalty": 0.0
    }
  }'
# Expected: Real-time parameter updates

# 4. Test formula component toggles
curl -X POST "http://localhost:5001/api/update-parameters" \
  -H "Content-Type: application/json" \
  -d '{
    "formula_toggles": {
      "starter_enabled": false
    }
  }'
# Expected: Starter multiplier set to 1.0x for all players
```

### **🎯 Starter System Validation Testing**:

**Manual Override System Testing**:
```bash
# Test all 5 override options
python test_starter_overrides.py

# Expected test results:
# ✅ S (Starter): 1.000x multiplier applied
# ✅ R (Rotation): 0.750x multiplier applied (configurable)
# ✅ B (Bench): 0.600x multiplier applied (configurable) 
# ✅ O (Out): 0.000x multiplier applied
# ✅ A (Auto): CSV prediction used
# ✅ Real-time V2.0 recalculation triggered
```

**Configurable Penalty Testing**:
```bash
# Test penalty slider functionality
python test_penalty_sliders.py

# Expected test results:
# ✅ Rotation penalty: 0.0-1.0 range, step 0.05
# ✅ Bench penalty: 0.0-1.0 range, step 0.05
# ✅ Out penalty: 0.0-1.0 range, step 0.05  
# ✅ Real-time application to affected players
# ✅ Parameter persistence in system_parameters.json
```

### **🎯 NEW: Weekly Data Upload Workflow (2025-08-26)**

**Rolling Minutes-Based Upload Process**:
The system now uses intelligent minutes comparison for accurate games_played detection.

**Required Workflow Order**:
```bash
# 1. FIRST: Sync Understat Data (updates total minutes)
curl -X POST "http://localhost:5001/api/understat/sync"

# 2. THEN: Upload CSV (uses minutes comparison)
# Navigate to http://localhost:5001/form-upload
# Upload your CSV file - system will automatically:
#   - Compare total_minutes vs previous gameweek snapshot
#   - Set games_played = 1 if minutes increased, 0 otherwise
#   - Create new raw snapshot for next upload comparison
```

**Upload Logic Validation**:
```bash
# Test the minutes-based detection
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, user='fantrax_user', password='fantrax_password', database='fantrax_value_hunter')
cursor = conn.cursor()

# Check a player's snapshot progression
cursor.execute('''
    SELECT gameweek, minutes_played, 
           LAG(minutes_played) OVER (ORDER BY gameweek) as prev_minutes
    FROM raw_player_snapshots 
    WHERE player_id = 'PLAYER_ID' 
    ORDER BY gameweek
''')
results = cursor.fetchall()
for gw, minutes, prev_minutes in results:
    played = 'YES' if prev_minutes and minutes > prev_minutes else 'NO'
    print(f'GW{gw}: {minutes} min (prev: {prev_minutes}) → Played: {played}')
"
```

**Workflow Benefits**:
- **Accurate Detection**: Uses actual minutes played vs points-based detection
- **Rolling Pattern**: Works across all gameweeks (GW2→GW38)  
- **Exception Handling**: Special cases (like injured players) handled correctly
- **Data Integrity**: Previous gameweek snapshots preserved for comparison

### **🎯 PPG Verification Testing (2025-08-26)**

**PPG Consistency Monitoring**:
The system now includes comprehensive PPG calculation verification to ensure V2.0 True Value accuracy.

**New Verification Endpoint**:
```bash
# Test PPG calculation consistency
curl "http://localhost:5001/api/verify-ppg"

# Expected response structure:
{
  "status": "success",
  "summary": {
    "total_players": 647,
    "accurate_ppg": 645,
    "accuracy_rate": "99.7%",
    "max_discrepancy": 0.05
  },
  "sample_discrepancies": [
    {
      "player_id": "P123456",
      "name": "Player Name", 
      "stored_ppg": 14.0,
      "calculated_ppg": 14.05,
      "discrepancy": 0.05
    }
  ],
  "validation_notes": "Minor discrepancies within acceptable tolerance"
}
```

**PPG Testing Workflow**:
```bash
# 1. Test form import with PPG verification
python -c "
import requests
import json

# Upload form data (triggers PPG recalculation)
response = requests.post('http://localhost:5001/api/form-upload', files={'file': open('test_form.csv', 'rb')})
print('Form upload:', response.json())

# Verify PPG consistency 
response = requests.get('http://localhost:5001/api/verify-ppg')
data = response.json()
print(f'PPG accuracy: {data[\"summary\"][\"accuracy_rate\"]}')
print(f'Max discrepancy: {data[\"summary\"][\"max_discrepancy\"]}')

# Test V2.0 calculation with fresh PPG
response = requests.post('http://localhost:5001/api/calculate-values-v2')
print('V2.0 calculation:', response.json()['message'])
"
```

**PPG Integration Testing**:
```bash
# Test complete PPG workflow integration
python test_ppg_workflow.py

# Expected test results:
# ✅ Form upload triggers PPG recalculation
# ✅ V2.0 engine uses fresh PPG calculation
# ✅ Auto-trigger V2.0 recalculation after PPG update
# ✅ PPG storage consistency maintained
# ✅ Verification endpoint accuracy >99%
```

**Critical PPG Test Cases**:
```bash
# Test specific PPG calculation scenarios
python -c "
# Test cumulative form data aggregation
# Player form data: GW1: 22 points, GW3: 28 points total (2 games)
# Correct PPG: MAX(28) ÷ 2 = 14.0 
# Incorrect AVG: AVG(22, 28) = 25.0

# Test database query correctness
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, user='fantrax_user', password='fantrax_password', database='fantrax_value_hunter')
cursor = conn.cursor()

cursor.execute('''
SELECT p.id, p.name,
    CASE 
        WHEN COALESCE(pgd.games_played, 0) > 0 
        THEN COALESCE(pf_max.total_points, 0) / pgd.games_played
        ELSE 0 
    END as calculated_ppg,
    pm.ppg as stored_ppg
FROM players p
LEFT JOIN player_games_data pgd ON p.id = pgd.player_id
LEFT JOIN (
    SELECT player_id, MAX(points) as total_points
    FROM player_form
    GROUP BY player_id
) pf_max ON p.id = pf_max.player_id
LEFT JOIN player_metrics pm ON p.id = pm.player_id
WHERE p.name LIKE '%Semenyo%'
''')

result = cursor.fetchone()
if result:
    print(f'Player: {result[1]}')
    print(f'Calculated PPG: {result[2]}')
    print(f'Stored PPG: {result[3]}')
    print(f'Match: {\"✅\" if abs(result[2] - result[3]) < 0.1 else \"❌\"}')
"
```

### **🏆 Enterprise Gameweek Management Testing** ✅ VERIFIED (2025-08-23)

**Complete Gameweek Unification Test Suite**:
```bash
# 1. Test GameweekManager core functionality
python test_gameweek_manager.py
# Expected: GameweekManager detection, caching, validation

# 2. Comprehensive Sprint 5 completion validation
python test_sprint5_completion.py
# Expected: 6/6 tests passed - all systems unified

# 3. Test monitoring endpoints
curl http://localhost:5001/api/gameweek-status
curl http://localhost:5001/api/gameweek-consistency
# Expected: Current gameweek detection, health status
```

**Gameweek System Validation** ✅ VERIFIED (2025-08-23):
- GameweekManager unified detection: ✅ Working (GW2 detected)
- Smart anomaly filtering: ✅ Working (GW3/GW7/GW99 ignored) 
- Dashboard API integration: ✅ Working (real-time data freshness)
- Consistency monitoring: ✅ Working (cross-table validation)
- Upload protection: ✅ Working (GW1 emergency protection active)

### **V2.0 Formula Validation Testing**

**Complete V2.0 System Test**:
```bash
python test_complete_v2_system.py

# Expected output:
# ✅ V2.0 Enhanced Engine: OPERATIONAL
# ✅ Dynamic Blending: 18.2% current + 81.8% historical @ GW3 (GW12 adaptation)
# ✅ EWMA Form (α=0.87): Responsive form tracking
# ✅ Exponential Fixtures (base=1.05): Advanced difficulty scaling
# ✅ Normalized xGI: Ratio-based with position adjustments
# ✅ Multiplier Caps: Form 2.0x, Fixture 1.8x, xGI 2.5x, Global 3.0x
# ✅ Database Integration: 647 players with complete V2.0 data
# ✅ API Endpoints: All V2.0 endpoints responding correctly
# ✅ Performance: <1s calculation time for full dataset
```

**V2.0 Component Testing**:
```bash
# Test individual V2.0 features
python test_v2_dynamic_blending.py
python test_v2_exponential_form.py
python test_v2_normalized_xgi.py
python test_v2_exponential_fixtures.py
python test_v2_multiplier_caps.py
```

### **V2.0 API Integration Testing**

**V2.0 Endpoint Testing**:
```bash
# Test V2.0 enhanced API responses
python test_v2_api_integration.py

# Expected validations:
# - True Value and ROI columns present
# - Dynamic blending metadata included
# - V2.0 calculation indicators active
# - Enhanced parameter structure verified
# - Performance metrics within targets
```

**V2.0 Dashboard Integration Testing**:
```bash
# Test V2.0 dashboard functionality
python test_v2_dashboard_integration.py

# Expected validations:
# - V2.0 Enhanced Formula controls functional
# - True Value/ROI columns display correctly
# - Dynamic blending display format working
# - Manual override system with V2.0 recalculation
# - Enhanced tooltips and visual indicators
```

### **V2.0 Data Quality Testing**

**V2.0 Database Validation**:
```bash
python test_v2_data_quality.py

# Expected validations:
# - 647 players with complete V2.0 data
# - 335 players with baseline_xgi for normalization
# - Historical PPG calculated correctly for blending
# - All V2.0 columns populated appropriately
# - Data integrity maintained across calculations
```

**V2.0 Calculation Accuracy Testing**:
```bash
# Test V2.0 calculation accuracy
python validate_v2_calculations.py

# Expected results:
# - Formula calculations match manual verification
# - Multiplier caps applied correctly
# - Position adjustments working as designed
# - Edge cases handled gracefully
```

---

## **V2.0 Performance Optimization**

### **V2.0 Performance Targets**
- **Full Recalculation**: <1 second for 647 players
- **API Response Time**: <500ms for player data endpoint
- **Parameter Updates**: <300ms for configuration changes
- **Database Queries**: <200ms for complex V2.0 queries
- **Memory Usage**: <200MB peak during calculation

### **V2.0 Performance Monitoring**
```bash
# Monitor V2.0 system performance
python monitor_v2_performance.py

# Metrics tracked:
# - Calculation time per player
# - Database query efficiency
# - Memory usage patterns
# - API response times
# - Frontend rendering performance
```

### **V2.0 Optimization Tools**
```bash
# Profile V2.0 calculation performance
python profile_v2_calculations.py

# Optimize V2.0 database queries
python optimize_v2_queries.py

# Memory profiling for V2.0 engine
python profile_v2_memory.py
```

---

## **V2.0 Troubleshooting Guide**

### **Common V2.0 Issues**

**Database Connection Issues**:
- Verify PostgreSQL running on port 5433
- Check V2.0 schema is properly applied
- Ensure `fantrax_user` has V2.0 table permissions
- Validate database contains 647 players with V2.0 columns

**V2.0 Calculation Issues**:
- Check `baseline_xgi` column present in `/api/players` endpoint
- Verify V2.0 parameter structure in `system_parameters.json`
- Ensure historical data properly integrated for dynamic blending
- Validate xGI toggle default state (disabled)

**V2.0 Dashboard Issues**:
- Confirm server running on port 5001 (not 5000)
- Check V2.0 Enhanced Formula indicators display
- Verify True Value and ROI columns visible
- Ensure parameter controls respond to changes

### **V2.0 Debugging Tools**

**V2.0 System Diagnostics**:
```bash
# Comprehensive V2.0 system check
python diagnose_v2_system.py

# Debug specific V2.0 calculations
python debug_v2_calculations.py --player="Erling Haaland"

# Validate V2.0 API responses
python validate_v2_api_responses.py
```

**V2.0 Logging Configuration**:
```python
# Enhanced logging for V2.0 development
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - V2.0 - %(name)s - %(levelname)s - %(message)s'
)
```

---

## **V2.0 Documentation Standards**

### **V2.0 Development Documentation**
- Always include V2.0 implementation dates (YYYY-MM-DD format)
- Mark features as ✅ Complete, 🔄 In Progress, or ⚠️ Requires Attention
- Document V2.0 formula validation results
- Include performance benchmarks for V2.0 features

### **V2.0 Code Documentation**
- Document V2.0 mathematical formulas with examples
- Include performance considerations for V2.0 calculations
- Explain V2.0 parameter ranges and constraints
- Document V2.0 API response structures

### **V2.0 Testing Documentation**
- Document expected V2.0 calculation results
- Include test cases for edge conditions
- Record V2.0 performance benchmarks
- Maintain V2.0 feature validation checklists

---

---

## **🎯 NEW: Dynamic Blending Testing Enhancement (2025-08-27)**

### **Enhanced Dynamic Blending Validation**

**Updated Testing Procedures**:
The Dynamic Blending testing procedures have been updated to reflect the new GW12 adaptation parameter:

**Enhanced Test Case (GW3)**:
```bash
# Test dynamic blending with GW12 adaptation
python test_dynamic_blending_v2.py

# Expected results with GW12 parameter:
# ✅ GW3: 18.2% current + 81.8% historical
# ✅ GW6: 45.5% current + 54.5% historical  
# ✅ GW12: 100% current + 0% historical (full adaptation)
# ✅ Faster transition to current season data
```

**Enhanced Dashboard Testing**:
- **Dynamic PPG Column**: Visible in dashboard with color coding
- **Blending Transparency**: Current season weight percentage shown
- **Export CSV**: Includes `blended_ppg`, `current_season_weight` columns
- **Configuration Panel**: Shows GW12 adaptation parameter

**API Testing Enhancement**:
```bash
# Test enhanced player data response
curl "http://localhost:5001/api/players?limit=5" | jq '.players[0] | {name, blended_ppg, current_season_weight, historical_ppg}'

# Expected response includes new fields:
{
  "name": "Erling Haaland",
  "blended_ppg": 8.45,
  "current_season_weight": 0.182,
  "historical_ppg": 8.0
}
```

**Testing Integration Notes**:
- All existing V2.0 tests updated for GW12 parameter
- New blending fields validated in API response tests
- Dashboard rendering tests include Dynamic PPG column
- Export CSV tests verify enhanced column set

---

**Last Updated**: 2025-08-27 - Dynamic Blending Testing Enhancement with GW12 adaptation parameter

*This document reflects the current V2.0-only development environment with enhanced dynamic blending transparency. The development setup supports 647 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending (GW12 adaptation), EWMA form calculations, normalized xGI integration, and comprehensive Starter control system. The enhanced testing procedures validate the new dynamic blending transparency features including blended PPG display, current season weight indicators, and improved Export CSV functionality.*