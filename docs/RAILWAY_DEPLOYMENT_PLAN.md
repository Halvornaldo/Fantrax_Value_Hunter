# Railway Deployment Plan - Fantrax Value Hunter

## Current System Overview

### Local Database (Master)
- **Database**: `fantrax_value_hunter` on PostgreSQL (localhost:5433)
- **Total Players**: 714 (Premier League)
- **Tables**: 27 total (only 5-6 essential for dashboard)
- **Live Data**: Single live table approach, no snapshots needed for Railway
- **Imports**: Fantrax, Understat, FFP, and OddsPortal data

### Railway Database (Read-Only Mirror)
- **Host**: `centerbeam.proxy.rlwy.net`
- **Port**: `16207`
- **Database**: `railway`
- **Purpose**: Friends access dashboard online
- **Strategy**: Read-only mirror of local data

## Implementation Plan

### Phase 1: Stabilize Local System (Week 1)

#### ✅ Completed Tasks:
1. **Database Analysis & Export Optimization**
   - Analyzed all 27 tables through code inspection
   - Identified 7 essential tables for Railway deployment
   - Created and tested export scripts (`railway_export.bat` / `railway_export.sh`)
   - Verified 714 players and all data integrity in export

#### 🔄 Remaining Tasks:
1. **Fix Parameter Adjustments** - CRITICAL
   - Test all parameter toggles in `system_parameters.json`
   - Fix any broken adjustment features in the dashboard
   - Document which parameters work/don't work
   - Ensure V2.0 formula calculations are stable

2. **Validate System Functionality**
   ```bash
   # Run validation scripts
   python archive/setup_scripts/check_db_structure.py
   python archive/setup_scripts/fantasy_validation.py

   # Test parameter adjustments manually in dashboard
   # Verify all 4 data sources working (Fantrax, Understat, FFP, OddsPortal)
   ```

3. **Local System Verification**
   - Ensure all 714 players display correctly with calculations
   - Test form multipliers, fixture difficulty, starter predictions
   - Verify True Value and ROI calculations are working
   - Fix any calculation errors before Railway deployment

### Phase 2: Deploy to Railway (Week 2)

#### Step 1: Export Local Database

**Verified Essential Tables (7 tables)** - Based on code analysis:
```bash
# Create optimized export script
#!/bin/bash
echo "Exporting essential tables for Railway..."

pg_dump fantrax_value_hunter \
  -t players \
  -t player_metrics \
  -t player_form \
  -t team_fixtures \
  -t fixture_odds \
  -t name_mappings \
  -t player_games_data \
  --no-owner \
  --no-privileges \
  --clean \
  > railway_sync_$(date +%Y%m%d).sql

echo "Export complete: railway_sync_$(date +%Y%m%d).sql"
echo "File size: $(du -h railway_sync_$(date +%Y%m%d).sql | cut -f1)"
```

**Why these 7 tables?**
- `players` - Core player data (714 players)
- `player_metrics` - Live performance stats
- `player_form` - Critical for form calculations
- `team_fixtures` - Fixture difficulty scores
- `fixture_odds` - Betting odds for difficulty calculation
- `name_mappings` - Global name matching (critical for cross-source data)
- `player_games_data` - Games tracking for blending calculations

#### Step 2: Import to Railway
```bash
# Set environment variable
export DATABASE_URL="postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway"

# Import database (use today's export file)
psql $DATABASE_URL < railway_sync_$(date +%Y%m%d).sql
```

#### Step 3: Configure Railway App
- Set `DATABASE_PUBLIC_URL` environment variable in Railway
- Deploy updated `app.py` with connection timeout fixes
- Disable parameter adjustments for Railway version

### Phase 3: Automate Weekly Sync (Week 3)

#### Create Sync Script
```python
#!/usr/bin/env python3
"""auto_sync_railway.py - Weekly sync to Railway"""
import subprocess
import os
import sys
from datetime import datetime

def validate_local_db():
    """Ensure local DB is ready for sync"""
    # Check player count
    # Verify tables exist
    # Return True if valid
    pass

def export_database():
    """Export local database to SQL file"""
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f'railway_sync_{timestamp}.sql'

    subprocess.run([
        'pg_dump',
        'fantrax_value_hunter',
        '-f', filename
    ])
    return filename

def import_to_railway(sql_file):
    """Import SQL file to Railway"""
    database_url = os.getenv('DATABASE_URL')

    # Clear existing data
    subprocess.run(['psql', database_url, '-c', 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'])

    # Import new data
    subprocess.run(['psql', database_url, '-f', sql_file])

def main():
    print("Starting Railway sync...")

    if not validate_local_db():
        print("Local database validation failed!")
        sys.exit(1)

    sql_file = export_database()
    import_to_railway(sql_file)

    print(f"✓ Railway sync complete: {datetime.now()}")

if __name__ == "__main__":
    main()
```

#### Schedule Automation
- Windows Task Scheduler for weekly runs
- Or manual run after imports: `python auto_sync_railway.py`

## Configuration Changes

### app.py Modifications for Railway

```python
# Detect Railway environment
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

if IS_RAILWAY:
    # Disable parameter adjustments
    ALLOW_PARAMETER_UPDATES = False

    # Use pre-calculated values
    USE_CACHED_CALCULATIONS = True

    # Longer cache timeout
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
```

### Connection Parameters
```python
# Already implemented in app.py
if is_railway or os.getenv('DATABASE_URL'):
    connection_params.update({
        'connect_timeout': 10,  # 10 second timeout
        'sslmode': 'prefer',    # SSL preferred
        'options': '-c statement_timeout=30000',  # 30 second query timeout
    })
```

## Maintenance Process

### Weekly Workflow
1. **Monday Morning**: Complete data update sequence
   - Upload OddsPortal CSV for upcoming gameweek fixtures (automatic difficulty scoring)
   - Run Fantrax import (player data and pricing)
   - Run Understat import (xG/xA statistics)
   - Run FFP import (starter predictions)
2. **Monday Evening**: Run sync script to Railway
3. **Tuesday**: Friends see fully updated data with all metrics
4. **No further intervention needed**

### Troubleshooting

#### If Sync Fails:
```bash
# Restore from backup
psql $DATABASE_URL < last_good_backup.sql
```

#### If App Won't Start:
- Check `DATABASE_URL` and `DATABASE_PUBLIC_URL` are set
- Verify TCP proxy is enabled in Railway settings
- Check logs: `railway logs`

## What Friends Get

✅ **Full Dashboard Access**
- All 714 players with complete metrics
- True Value and ROI calculations
- Sorting and filtering
- CSV export functionality

❌ **Disabled Features** (for stability)
- Parameter adjustments (read-only)
- Data imports (handled locally)
- Admin functions

## Success Metrics

- **Uptime**: Dashboard accessible 99% of the time
- **Data Freshness**: Updated within 24 hours of gameweek
- **Performance**: Page loads under 3 seconds
- **Maintenance**: Less than 15 minutes per week

## Current Status & Next Steps

### ✅ Completed:
- Database table analysis and optimization
- Railway export scripts created and tested
- Documentation updated with findings

### 🔄 Next Priority (Phase 1 Completion):
1. **Fix local parameter adjustment issues** - CRITICAL
   - Test all toggles in system_parameters.json
   - Verify V2.0 formula calculations are stable
   - Fix any broken dashboard features
2. **Validate complete system functionality**
   - Run validation scripts
   - Test all data imports (Fantrax, Understat, FFP, OddsPortal)
   - Verify 714 players show correctly with all metrics

### 📋 After Phase 1 Complete:
3. Run first Railway sync with verified data
4. Verify dashboard works online for friends
5. Set up weekly automation
6. Document any Railway-specific configurations

---

*Last Updated: September 2025*
*System Version: V2.0 Enhanced Formula*
*Total Players: 714*