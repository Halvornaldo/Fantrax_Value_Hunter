# Development Setup Guide - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter Development Environment

### **System Status: V2.0 Production Environment**

This document describes the complete development setup for the V2.0 Enhanced Formula system. The system has been consolidated to a single V2.0 engine with all legacy components removed.

**Development Environment**: Windows MINGW64  
**Current System**: V2.0 Enhanced Formula fully operational

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

**V2.0 Configuration Structure**:
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
# ✅ Dynamic blending: PASSED (6.7% current + 93.3% historical)
# ✅ EWMA form calculation: PASSED (α=0.87)
# ✅ Exponential fixtures: PASSED (base^-difficulty)
# ✅ Normalized xGI: PASSED (ratio-based)
# ✅ V2.0 engine fully validated
```

**V2.0 API Testing**:
```bash
# Test V2.0 enhanced endpoints
curl -X POST http://localhost:5001/api/calculate-values-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "formula_version": "v2.0",
    "gameweek": 2,
    "features": {
      "dynamic_blending": true,
      "exponential_form": true,
      "normalized_xgi": true,
      "exponential_fixtures": true
    }
  }'

# Test V2.0 player data endpoint
curl "http://localhost:5001/api/players?limit=10&sort_by=true_value"
```

**V2.0 Dashboard Testing**:
- Dashboard loads at `http://localhost:5001`
- V2.0 Enhanced Formula controls respond
- True Value and ROI columns display properly
- Player table shows 647 players with V2.0 calculations
- Dynamic blending display format ("27+1", "38+2")
- Manual override system works with V2.0 recalculation
- Import workflows accessible at `/form-upload` and `/odds-upload`

### **V2.0 Feature Validation**

**Dynamic Blending System Testing**:
```bash
python -c "
from calculation_engine_v2 import FormulaEngineV2
engine = FormulaEngineV2()

# Test early season blending (GW2)
test_player = {
    'games_played': 1,
    'ppg': 6.5,
    'total_points_historical': 216,
    'games_played_historical': 27
}

blended_ppg, weight = engine._calculate_dynamic_blending(test_player, 2)
print(f'Blended PPG: {blended_ppg:.2f}')
print(f'Current weight: {weight:.3f} (6.7% expected)')
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

### **V2.0 Formula Validation Testing**

**Complete V2.0 System Test**:
```bash
python test_complete_v2_system.py

# Expected output:
# ✅ V2.0 Enhanced Engine: OPERATIONAL
# ✅ Dynamic Blending: 6.7% current + 93.3% historical
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

**Last Updated**: 2025-08-22 - V2.0 Enhanced Formula Development Setup Complete

*This document reflects the current V2.0-only development environment with all legacy components removed. The development setup supports 647 Premier League players with optimized V2.0 Enhanced Formula calculations including True Value predictions, ROI analysis, dynamic blending, EWMA form calculations, and normalized xGI integration.*