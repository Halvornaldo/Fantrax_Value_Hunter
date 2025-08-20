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

**Additional Required Dependencies** (missing from requirements.txt):
```bash
pip install psycopg2-binary  # PostgreSQL adapter
```

### 3. Database Setup

**Connection Details**:
- **Host**: localhost
- **Port**: 5433 (custom port, not default 5432)
- **Database**: fantrax_value_hunter
- **Username**: fantrax_user
- **Password**: fantrax_password

**Database Verification**:
```bash
python check_db_structure.py
```
Expected output: "✅ Database connection successful" and "Database connected: 647 players loaded"

### 4. Configuration Files

**System Parameters**:
- File: `config/system_parameters.json`
- Contains all dashboard parameter defaults
- No manual editing needed - managed via dashboard

**API Keys** (if needed):
```bash
cp config/fantrax_cookies.json.example config/fantrax_cookies.json
# Edit with your browser cookies if web scraping features used
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

1. **Python Version**: What minimum Python version is required?
2. **Virtual Environment**: Should developers use venv/conda for isolation?
3. **PostgreSQL Setup**: How do developers set up local PostgreSQL on port 5433?
4. **Environment Variables**: Are there any .env files or environment configuration needed?
5. **Data Initialization**: How do developers populate the initial player database?
6. **Test Data**: Are there any test datasets for development?

*Please verify these details and update this guide accordingly.*