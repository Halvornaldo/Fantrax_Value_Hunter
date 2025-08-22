# Development Setup Guide

## Prerequisites

**Required Software**:
- Python 3.8+ (verify specific version requirement)
- PostgreSQL with custom port configuration
- Git (for version control)

## Quick Start

### 1. Repository Setup
```bash
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
```

### 2. Python Dependencies

Install core dependencies:
```bash
pip install -r requirements.txt
```

**Additional Required Dependencies** (verify against requirements.txt):
```bash
pip install psycopg2-binary  # PostgreSQL adapter
pip install flask            # Web framework
pip install pandas           # Data manipulation
pip install numpy            # Numerical calculations
pip install requests         # HTTP requests for APIs
pip install scraperfc        # Understat data integration
pip install python-dateutil  # Date parsing
```

### 3. Database Setup

**Connection Details**:
- **Host**: localhost
- **Port**: 5433 (custom port, not default 5432)
- **Database**: fantrax_value_hunter
- **Admin User**: postgres / Password (with capital P)
- **App User**: fantrax_user / fantrax_password

**v2.0 Migration Status**: ✅ Complete (2025-08-21)
- All v2.0 schema changes applied
- Database permissions fixed for fantrax_user
- Ready for v2.0 testing and development
- **Username**: fantrax_user
- **Password**: fantrax_password

**Database Verification**:
```bash
python check_db_structure.py
```
Expected output: "✅ Database connection successful" and "Database connected: 633 players loaded"

**Data Initialization** (for new setups):
```bash
# Initialize player database (if starting fresh)
python initialize_players.py

# Populate historical data (2024-25 season baseline)
python import_historical_data.py

# Set up initial xGI data sync
python sync_understat_data.py

# Initialize team fixtures and odds
python setup_fixture_data.py
```

### 4. Configuration Files

**System Parameters**:
- File: `config/system_parameters.json`
- Contains all dashboard parameter defaults
- No manual editing needed - managed via dashboard

**Configuration File Structure**:
```bash
config/
├── system_parameters.json     # Dashboard parameters (auto-managed)
├── api_keys.json             # API credentials 
├── fantrax_cookies.json      # Browser cookies for web scraping
└── database_config.json      # Database connection settings
```

**Environment Setup**:
```bash
# Copy example configurations (if they exist)
cp config/fantrax_cookies.json.example config/fantrax_cookies.json
cp config/api_keys.json.example config/api_keys.json

# Edit with your specific credentials
# Browser cookies needed only if web scraping features used
```

**System Parameters Structure** (automatically managed):
```json
{
  "form_calculation": {"enabled": true, "lookback_period": 3},
  "fixture_difficulty": {"enabled": true, "multiplier_strength": 0.2},
  "starter_prediction": {"enabled": true, "auto_rotation_penalty": 0.7},
  "xgi_integration": {"enabled": true, "multiplier_strength": 0.7},
  "games_display": {"baseline_switchover_gameweek": 10}
}
```

### 5. Launch Application

**Start Flask Server**:
```bash
python src/app.py
```

**Access Dashboard**:
- URL: http://localhost:5000
- Expected: Two-panel dashboard with Parameter Controls + Player Table
- Status indicator should show "⚡ Ready" and "🎯 633 players loaded"

## Development Tools

### Database Management

**Structure Verification**:
```bash
python check_db_structure.py          # View table structure and sample data
python check_games.py                 # Check games tracking data
```

**Schema Updates**:
```bash
python run_migration.py               # Run database migrations
```

### Testing

**Basic functionality**:
- Dashboard loads at http://localhost:5000
- Parameter controls respond to changes
- Player table displays 633+ players with pagination (50/100/200/All page sizes)
- Games column sorts numerically
- Manual override controls work in real-time
- Import pages accessible at `/form-upload` and `/odds-upload`

**Formula Optimization v2.0 Testing** (added 2025-08-21):
```bash
# Test v2.0 calculation engine
python test_v2_api.py

# Expected output:
# - SUCCESS: v2.0 API integration test PASSED!
# - True Values: 0.05-0.10 range
# - ROI values: 0.010-0.021
# - Exponential fixture multipliers: 0.958-1.029
```

**v2.0 API Testing**:
```bash
# Test v2.0 endpoints via curl
curl -X POST http://localhost:5000/api/calculate-values-v2 \
  -H "Content-Type: application/json" \
  -d '{"formula_version": "v2.0", "gameweek": 1}'

# Get formula version
curl http://localhost:5000/api/get-formula-version
```

**v2.0 Sprint 1 & 2 Feature Status** (Updated 2025-08-21):
- ✅ **Sprint 1**: Core formula fixed (True Value separated from price)
- ✅ **Sprint 1**: Exponential fixture calculation (base^(-difficulty))
- ✅ **Sprint 1**: Multiplier caps (form: 2.0, fixture: 1.8, global: 3.0)
- ✅ **Sprint 1**: Data type handling (Decimal/float compatibility)
- ✅ **Sprint 1**: Database schema migration complete
- ✅ **Sprint 2**: EWMA form calculation with α=0.87 exponential decay
- ✅ **Sprint 2**: Dynamic PPG blending with smooth transition weights
- ✅ **Sprint 2**: Normalized xGI with 2024/25 historical baselines
- ✅ **Sprint 2**: Position-specific adjustments (defenders, goalkeepers)
- 🔄 **Sprint 3**: Validation framework pending
- 🔄 **Sprint 4**: Dashboard integration pending

## Sprint 2 Testing Procedures (Added 2025-08-21)

### Sprint 2 Validation Tests
```bash
# Test complete Sprint 2 implementation
python test_complete_sprint2.py

# Expected output:
# OK: Dynamic PPG blending working (w_current = 0.125)
# OK: EWMA form calculation working (α = 0.87)
# OK: Normalized xGI calculation working (ratio-based)
# OK: All Sprint 2 features validated successfully
```

### Sprint 2 Feature Testing
```bash
# Test individual Sprint 2 components
python -c "
from calculation_engine_v2 import CalculationEngineV2
engine = CalculationEngineV2()

# Test dynamic blending
test_player = {'ppg': 8.5, 'games_played': 2, 'historical_ppg': 8.9}
blended, weight = engine._calculate_blended_ppg(test_player)
print(f'Dynamic blending: {blended:.2f} (weight: {weight:.3f})')

# Test EWMA form
test_player['recent_points'] = [9.0, 7.5, 8.2, 6.8, 8.5]
form_mult = engine._calculate_exponential_form_multiplier(test_player)
print(f'EWMA form multiplier: {form_mult:.3f}')

# Test normalized xGI
test_player.update({'xgi90': 1.85, 'baseline_xgi': 2.06, 'position': 'F'})
xgi_mult = engine._calculate_normalized_xgi_multiplier(test_player)
print(f'Normalized xGI multiplier: {xgi_mult:.3f}')
"
```

### Sprint 2 Data Validation
```bash
# Verify Sprint 2 database enhancements
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, 
    user='fantrax_user', password='fantrax_password', 
    database='fantrax_value_hunter')
cur = conn.cursor()

# Check baseline_xgi data
cur.execute('SELECT COUNT(*) FROM players WHERE baseline_xgi IS NOT NULL')
baseline_count = cur.fetchone()[0]
print(f'Players with historical baselines: {baseline_count}')

# Check v2.0 columns
cur.execute('SELECT COUNT(*) FROM players WHERE true_value IS NOT NULL')
v2_count = cur.fetchone()[0] 
print(f'Players with v2.0 data: {v2_count}')

conn.close()
"
```

### Code Quality

**Available Tools** (from requirements.txt):
```bash
black .                               # Code formatting
flake8 .                             # Linting
pytest                               # Run tests (if test files exist)
```

## File Structure

### Core Application Files
```
src/
├── app.py                           # Main Flask application
├── candidate_analyzer.py           # Analysis utilities
├── db_manager.py                    # Database management
├── fixture_difficulty.py           # Odds-based difficulty calculation
├── form_tracker.py                  # Form calculation utilities
└── name_matching/                   # Name matching system
    ├── unified_matcher.py           # Core matching service
    ├── matching_strategies.py       # Matching algorithms
    └── suggestion_engine.py         # Smart suggestions
```

### Frontend Files
```
templates/
├── dashboard.html                   # Main dashboard UI
├── form_upload.html                 # CSV upload interface
├── odds_upload.html                 # Odds upload interface
└── import_validation.html           # Name matching validation

static/
├── css/dashboard.css                # Dashboard styling
└── js/dashboard.js                  # Frontend logic
```

### Configuration
```
config/
├── system_parameters.json           # Dashboard parameters
├── api_keys.json                    # API credentials
└── fantrax_cookies.json             # Browser cookies (optional)
```

## Development Workflow

### 1. Feature Development
1. Make code changes
2. Test locally with `python src/app.py`
3. Verify functionality in browser at http://localhost:5000
4. Check database with verification scripts

### 2. Database Changes
1. Create migration SQL in `migrations/` folder
2. Run with `python run_migration.py`
3. Verify with `python check_db_structure.py`

### 3. Parameter Changes
- Edit parameters via dashboard interface
- Changes saved to `config/system_parameters.json`
- No manual file editing needed

## Common Issues

### Database Connection Fails
- Verify PostgreSQL running on port 5433
- Check credentials: fantrax_user/fantrax_password
- Ensure database 'fantrax_value_hunter' exists

### Missing Dependencies
- Add `psycopg2-binary` if not installed
- Run `pip install -r requirements.txt` again

### Port Conflicts
- Default Flask port 5000 may conflict with other services
- Check console output for actual running port

## API Documentation

See `docs/API_REFERENCE.md` for complete endpoint documentation.

## Database Schema

See `docs/DATABASE_SCHEMA.md` for complete table structures and relationships.

## Feature Guide

See `docs/FEATURE_GUIDE.md` for dashboard functionality explanation.

---

## Development Questions (To Verify)

## System Requirements & Performance

### Minimum Requirements
- **Python**: 3.8+ (verify specific version requirement)
- **Memory**: 4GB RAM minimum (8GB recommended for full dataset)
- **Storage**: 2GB for database and application files
- **PostgreSQL**: Version 12+ with custom port configuration

### Performance Expectations
- **Startup Time**: Reasonable initialization time for weekly analysis tool
- **Database Queries**: Efficient response for 633 player dataset
- **Parameter Updates**: Timely recalculation suitable for parameter testing
- **CSV Processing**: Processing time varies with file size, optimized for weekly workflows

### Virtual Environment Setup (Recommended)
```bash
# Create virtual environment
python -m venv fantrax_env

# Activate (Windows)
fantrax_env\Scripts\activate

# Activate (Linux/Mac) 
source fantrax_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### PostgreSQL Setup Notes
- **Custom Port 5433**: Avoid conflicts with default PostgreSQL instances
- **Database Creation**: `CREATE DATABASE fantrax_value_hunter;`
- **User Setup**: `CREATE USER fantrax_user WITH PASSWORD 'fantrax_password';`
- **Permissions**: `GRANT ALL PRIVILEGES ON DATABASE fantrax_value_hunter TO fantrax_user;`

### Development Environment Variables
```bash
# Optional .env file for development
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=postgresql://fantrax_user:fantrax_password@localhost:5433/fantrax_value_hunter
```

## Documentation Maintenance

### Post-Sprint Documentation Updates

After completing each Formula Optimization sprint, the following documents MUST be updated:

**Core Documentation (Always Update):**
- `docs/DATABASE_SCHEMA.md` - Add new columns, tables, migrations
- `docs/API_REFERENCE.md` - Document new endpoints, response formats  
- `docs/DEVELOPMENT_SETUP.md` - Update testing procedures, feature status
- `docs/FEATURE_GUIDE.md` - Add new dashboard features, update status

**Additional Documentation (Update As Relevant):**
- `docs/FORMULA_OPTIMIZATION_SPRINTS.md` - Mark sprints complete, update status
- `docs/FORMULA_REFERENCE.md` - Update calculation formulas and examples
- `docs/FORMULA_MIGRATION_GUIDE.md` - Add new migration steps
- `CLAUDE.md` - Update system status and recent features
- `README.md` - Update feature highlights if user-facing changes

**Sprint-Specific Updates:**
- **Sprint 2 (EWMA/Dynamic Blending)**: Update FORMULA_REFERENCE.md with new calculations
- **Sprint 3 (Validation)**: Update TESTING_METHODOLOGY.md with new validation procedures  
- **Sprint 4 (Dashboard)**: Major updates to FEATURE_GUIDE.md and API_REFERENCE.md
- **Sprint 5 (Future Features)**: Update FUTURE_IDEAS.md with implemented features

**Maintenance Checklist:**
```bash
# After each sprint completion:
1. Update all "Core Documentation" files above
2. Review and update relevant "Additional Documentation" 
3. Run documentation consistency check
4. Commit with semantic message: "docs: Update documentation for Sprint X completion"
5. Tag sprint completion: git tag "vX.X-sprintX-complete"
```

**Documentation Standards:**
- Always include implementation dates (YYYY-MM-DD format)
- Mark features as ✅ Complete, 🔄 Pending, or ⏸️ Deferred  
- Use consistent status indicators across all docs
- Update "Last updated" dates at bottom of files

---

## Sprint 4 Phase 1 Development Notes (2025-08-21)

### New Development Considerations

**Database NULL Handling Best Practices:**
- When adding new calculated columns (like ROI), always consider NULL value scenarios
- PostgreSQL sorts NULLs first by default - use `NULLS LAST` for better UX
- Test sorting behavior on new columns during development
- Add NULL handling documentation to database schema changes

**Dual Formula Engine Architecture:**
- v1.0 and v2.0 engines can coexist safely in the same codebase
- Use body classes for conditional CSS styling instead of JavaScript style manipulation
- Toggle functionality should be tested across all browser states (F5, back/forward navigation)
- Consider state management complexity early when building UI toggles

**Frontend Development Patterns:**
- Use body classes (`v2-enabled`, `v1-enabled`) for feature-specific styling
- Add console logging for debugging complex state management
- Test edge cases like switching between formula versions multiple times
- Consider visual feedback for all user interactions

### Testing Workflow Updates
```bash
# New testing steps for v2.0 features:
1. Test ROI column sorting (both directions)
2. Verify NULL value handling in new columns  
3. Test formula version toggle functionality
4. Validate visual indicators show correct state
5. Check validation system connectivity (should show "Not Available" with insufficient data)
```

### Development Environment Notes
- Validation system requires 5+ gameweeks of data for meaningful results
- Current environment has 2 gameweeks (testing phase appropriate)
- Formula toggle is intended for testing/development - not critical for production
- Backend transaction errors may occur if database connections aren't properly closed

## V2.0 xGI Testing Procedures (Added 2025-08-22)

### xGI Toggle Testing
**Purpose**: Validate the v2.0 xGI enable/disable functionality works correctly

**Testing Steps**:
```bash
# 1. Test v2.0 xGI disabled (default state)
curl -X POST http://localhost:5000/api/calculate-values-v2 \
  -H "Content-Type: application/json" \
  -d '{"formula_version": "v2.0", "gameweek": 2}'

# Expected: All players show xGI multiplier = 1.000x in response
```

**Frontend Testing**:
1. Load dashboard in v2.0 Enhanced mode
2. Navigate to Normalized xGI section
3. Verify "Apply xGI to True Value Calculation" checkbox is UNCHECKED by default
4. Check help text displays: "When unchecked, xGI multiplier = 1.0x (no effect on True Value)"
5. Player table should show 1.000x in xGI column for all players

**Toggle Enable Testing**:
```bash
# 2. Test xGI enabled state
# Check the checkbox in dashboard, click "Apply Changes"
# Verify player table shows calculated xGI values (not all 1.000x)
# Expected examples:
# - Ben White: ~0.909x
# - Calafiori: ~2.500x (capped by system limits)
```

**Backend Parameter Testing**:
```bash
# 3. Verify parameter structure
python -c "
import json
with open('config/system_parameters.json') as f:
    params = json.load(f)
    xgi_config = params.get('formula_optimization_v2', {}).get('normalized_xgi', {})
    print(f'xGI enabled: {xgi_config.get(\"enabled\", \"NOT FOUND\")}')
    print(f'xGI cap: {xgi_config.get(\"cap\", \"NOT FOUND\")}')
"
```

### Baseline Data Validation Testing
**Purpose**: Ensure baseline_xgi column is properly required and handled

**Database Testing**:
```bash
# 4. Test baseline_xgi column presence
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, 
    user='fantrax_user', password='fantrax_password', 
    database='fantrax_value_hunter')
cur = conn.cursor()

# Check baseline_xgi in /api/players query
cur.execute('''SELECT COUNT(*) FROM players p 
               WHERE p.baseline_xgi IS NOT NULL''')
count = cur.fetchone()[0]
print(f'Players with baseline_xgi: {count}/633')

# Test specific players mentioned in conversation
cur.execute('''SELECT name, baseline_xgi, xgi90 
               FROM players 
               WHERE name IN (\'Ben White\', \'Riccardo Calafiori\')''')
for row in cur.fetchall():
    print(f'{row[0]}: baseline={row[1]}, current={row[2]}')
    
conn.close()
"
```

**API Response Testing**:
```bash
# 5. Test baseline_xgi appears in API response
curl "http://localhost:5000/api/players?limit=5" | python -m json.tool | grep baseline_xgi

# Expected: baseline_xgi field should appear in player objects
# If missing, v2.0 xGI calculations will fail
```

### Early Season Strategy Validation
**Purpose**: Document expected behavior for low sample size scenarios

**Expected Behaviors**:
- **GW1-4**: xGI disabled by default (insufficient current season data)
- **GW5-8**: User choice - can enable for aggressive early xGI or keep disabled for stability
- **GW9+**: Safe to enable - sufficient current season sample size

**Testing Low Sample Size**:
```bash
# 6. Test volatile ratio detection
python -c "
# Simulate early season scenario
current_xgi = 0.45  # Low current season sample
baseline_xgi = 2.06  # Historical 2024-25 baseline
ratio = current_xgi / baseline_xgi if baseline_xgi > 0 else 1.0
print(f'Early season ratio: {ratio:.3f}x')
print(f'Volatility concern: {\"HIGH\" if ratio < 0.5 or ratio > 2.0 else \"NORMAL\"}')
"
```

### Engine Separation Testing
**Purpose**: Validate v1.0 and v2.0 engines handle xGI independently

**v1.0 vs v2.0 Testing**:
```bash
# 7. Compare xGI calculations between engines
# In dashboard:
# a) Switch to v1.0 Legacy mode - xGI should use capped calculations (0.5-1.5x)
# b) Switch to v2.0 Enhanced mode - xGI should use normalized ratios (baseline-relative)
# c) Verify same player shows different xGI values in different modes
```

**Parameter Structure Testing**:
```bash
# 8. Verify parameter structures don't conflict
python -c "
import json
with open('config/system_parameters.json') as f:
    params = json.load(f)
    
    # v1.0 parameters
    v1_xgi = params.get('xgi_integration', {})
    print(f'v1.0 xGI structure: {list(v1_xgi.keys())}')
    
    # v2.0 parameters  
    v2_xgi = params.get('formula_optimization_v2', {}).get('normalized_xgi', {})
    print(f'v2.0 xGI structure: {list(v2_xgi.keys())}')
    
    # Should be completely separate parameter structures
"
```

### Critical Requirement Validation

**⚠️ MUST VERIFY** during testing:
1. `/api/players` endpoint includes `p.baseline_xgi` in SQL SELECT statement
2. v2.0 xGI toggle defaults to UNCHECKED (disabled)
3. When disabled, ALL players show xGI multiplier = 1.000x
4. When enabled, players show calculated ratios (current_xgi90 / baseline_xgi)
5. Position adjustments apply correctly (defenders get 30% reduction when baseline < 0.2)

**Testing Checklist**:
- [ ] xGI toggle shows unchecked by default
- [ ] baseline_xgi column present in API responses
- [ ] Toggle enable/disable changes xGI calculations
- [ ] v1.0 and v2.0 modes show different xGI values
- [ ] Parameter changes persist after "Apply Changes"

*Last updated: 2025-08-22 - Added comprehensive v2.0 xGI testing procedures and validation requirements*