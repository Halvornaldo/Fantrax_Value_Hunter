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

**v2.0 Feature Status**:
- ✅ Core formula fixed (True Value separated from price)
- ✅ Exponential fixture calculation (base^(-difficulty))
- ✅ Multiplier caps (form: 2.0, fixture: 1.8, global: 3.0)
- ✅ Data type handling (Decimal/float compatibility)
- ✅ Database schema migration complete
- 🔄 Dashboard integration pending (Sprint 4)
- 🔄 EWMA form calculation pending (Sprint 2)

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

*Last updated: 2025-08-21 - Post Formula Optimization v2.0 Sprint 1 completion*