# Troubleshooting Guide - V2.0 Enhanced Formula System
## Fantasy Football Value Hunter Common Issues & Solutions

### **System Status: V2.0 Production Troubleshooting**

This guide documents common issues, their root causes, and proven solutions for the V2.0 Enhanced Formula system.

**Environment:**
- **Backend**: Flask API on `localhost:5001`
- **Frontend**: React dashboard on `localhost:3000`
- **Database**: PostgreSQL on `localhost:5433`
- **Total Players**: 714 Premier League players

---

## **🚨 CRITICAL ISSUE: 2x Dynamic PPG Problem**

### **Problem Description**
Players showing exactly **2x expected Dynamic PPG** after recalculation, indicating incorrect games count source usage.

### **Symptoms**
- Players with 4 games played show Dynamic PPG that is exactly double their PPG
- Pattern affects all players with >1 game in current season
- Not approximately 2x, but **exactly 2x** - suggests games count error

### **Root Cause** ✅ *RESOLVED 2025-09-17*
**Incorrect games count data source** used in calculation:
- **Wrong Source**: `pgd.games_played_current` (SUM aggregation from `player_games_data`)
- **Correct Source**: `p.games_current_season` (direct from Understat sync)

### **Technical Details**
The issue occurred in two locations in `src/app.py`:

1. **PPG Calculation (Line 423)**:
   ```python
   # WRONG (caused 2x issue)
   ppg = player['total_points'] / pgd.games_played_current if pgd.games_played_current > 0 else 0

   # FIXED
   ppg = player['total_points'] / p.games_current_season if p.games_current_season > 0 else 0
   ```

2. **Dynamic Blending Parameter (Line 475)**:
   ```python
   # WRONG (caused 2x issue)
   'games_current': player['games_played_current']

   # FIXED
   'games_current': player['games_current_season']
   ```

### **Resolution Applied**
1. Modified `src/app.py` to use `p.games_current_season` consistently
2. Added `p.games_current_season` to SQL SELECT queries
3. Updated dynamic blending to use correct games source
4. Verified fix through recalculation testing

### **Prevention**
- Always use `p.games_current_season` for games count in calculations
- Populate via Understat sync for accurate data
- Document data source requirements in code comments

---

## **💾 Data Source Issues**

### **Games Count Data Sources** ⚠️
The system has **TWO** different sources for games count:

1. **`players.games_current_season`** - ✅ **ACCURATE** (from Understat sync)
2. **`player_games_data` (SUM aggregation)** - ⚠️ **May have discrepancies**

**Always Use**: `p.games_current_season` for:
- PPG calculations
- Dynamic blending `games_current` parameter
- Frontend display (25-26 column)

### **Blending Formula Issues**

#### **Problem**: Players without historical data get unfairly low True Values
**Symptoms**: New Premier League players (no 2024-25 data) show very low values
**Solution**: Implemented MAX formula for fair weighting:

```python
# Enhanced MAX Formula
weight_A = games_current / (games_current + games_historical)  # Games-based ratio
weight_B = min(1.0, games_current / transition_period)         # Transition-based
w_current = max(weight_A, weight_B)                           # Take maximum
```

**Visual Indicator**: Orange/amber color coding for players without historical data

---

## **🔧 Server & Application Issues**

### **Server Startup Problems**

#### **Port Already in Use**
**Error**: `Address already in use`
**Solution**:
```bash
# Kill existing Flask processes
taskkill /f /im python.exe
# Or find specific process
netstat -ano | findstr :5001
taskkill /PID [process_id] /f
```

#### **Database Connection Issues**
**Error**: `Connection to localhost:5433 failed`
**Solution**:
1. Verify PostgreSQL is running
2. Check credentials in environment
3. Test connection: `psql -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter`

### **File Modification Errors**

#### **"File has been unexpectedly modified"**
**Error**: When trying to edit files
**Solution**: Use `sed` commands for direct file modification:
```bash
sed -i 's/old_text/new_text/g' filename
```

---

## **📊 Calculation Issues**

### **Missing Baseline xGI Data**
**Problem**: Players missing `baseline_xgi` causing calculation failures
**Symptoms**: V2.0 calculations fail for affected players
**Solution**:
1. Run Understat sync: `POST /api/understat/sync`
2. Review unmatched players in validation UI
3. Manually map players with <85% confidence

### **Multiplier Range Issues**

#### **Form Multipliers Out of Range**
**Problem**: Form multipliers exceeding progressive ranges
**Solution**: Check progressive ranges configuration:
```json
"progressive_form_ranges": {
  "enabled": true,
  "ranges_by_games": [
    {"games": 2, "min": 0.95, "max": 1.05},
    {"games": 4, "min": 0.85, "max": 1.15},
    // ...
  ]
}
```

### **Dynamic Blending Weight Issues**
**Problem**: Unrealistic current season weights
**Symptoms**: Weight >1.0 or unexpected blending results
**Check**:
1. Games count source (use `p.games_current_season`)
2. Transition period configuration (default: 12 games)
3. Historical data availability

---

## **🎯 Frontend Issues**

### **Player Table Display Problems**

#### **Missing Dynamic PPG Color Coding**
**Problem**: Players without historical data not visually distinguished
**Solution**: Verify `has_historical_data` flag in API response and orange styling in `PlayerTable.js`

#### **Games Display Format**
**Expected Format**: "27+4" (historical+current games)
**Fix**: Ensure `games_display` field populated correctly in API

### **Dashboard Loading Issues**
**Problem**: Dashboard not loading or showing errors
**Check**:
1. Backend API health: `curl http://localhost:5001/api/health`
2. Frontend console errors
3. CORS configuration

---

## **🔄 Data Import Issues**

### **Understat Sync Problems**

#### **Low Match Rate**
**Expected**: >95% match rate
**If Low**:
1. Check name matching confidence thresholds
2. Review unmatched players: `GET /api/understat/get-unmatched-data`
3. Use validation UI for manual mapping

#### **Name Matching Failures**
**Solution**: Use UnifiedNameMatcher with fuzzy matching:
- Exact matches prioritized
- Fuzzy matches with >85% confidence
- Manual review for <85% confidence

### **CSV Import Issues**

#### **Format Validation Errors**
**Common Problems**:
- Incorrect column headers
- Missing required fields
- Data type mismatches

**Solution**: Verify CSV format matches expected schema

#### **FFP Lineup Import**
**Expected Format**: "Team Predicted Lineup", "Player1", "Confidence%"
**Common Issues**:
- Team name translation (full names → 3-letter codes)
- Confidence percentage parsing
- Player name variations

---

## **💡 Performance Issues**

### **Slow Calculation Times**
**Target**: <1 second for 714 players
**If Slow**:
1. Check database indexes
2. Review query optimization
3. Monitor memory usage

### **High Memory Usage**
**Target**: <200MB peak
**If High**:
1. Check for memory leaks in calculation engine
2. Review data structure efficiency
3. Consider garbage collection tuning

---

## **🧪 Testing & Validation**

### **Formula Validation Failures**
**Problem**: Poor RMSE/MAE scores
**Investigation Steps**:
1. Check data quality (missing baselines, invalid games counts)
2. Verify parameter configuration
3. Review historical data completeness
4. Test individual multiplier components

### **Recalculation Verification**
**Test Pattern**:
1. Note player values before recalculation
2. Trigger recalculation
3. Verify expected changes (no 2x Dynamic PPG)
4. Check calculation timestamps

---

## **⚙️ Configuration Issues**

### **Parameter Update Failures**
**Problem**: Configuration changes not applied
**Solution**:
1. Verify JSON format
2. Check parameter validation
3. Restart calculation engine if needed

### **Toggle States Not Persisting**
**Common Toggles**:
- xGI integration enabled/disabled
- Form enabled/disabled
- Fixture enabled/disabled

**Fix**: Verify `system_parameters.json` updates and API persistence

---

## **🔍 Diagnostic Commands**

### **System Health Checks**
```bash
# Backend health
curl http://localhost:5001/api/health

# Database connection
curl "http://localhost:5001/api/players?limit=1"

# Configuration check
curl http://localhost:5001/api/config

# Specific player check
curl "http://localhost:5001/api/players?search=Haaland"
```

### **Data Quality Validation**
```sql
-- Check V2.0 data completeness
SELECT
    COUNT(*) as total_players,
    COUNT(true_value) as with_true_value,
    COUNT(baseline_xgi) as with_baseline_xgi,
    COUNT(blended_ppg) as with_blending
FROM players;

-- Verify games count consistency
SELECT
    COUNT(*) as players_with_discrepancy
FROM players p
LEFT JOIN player_games_data pgd ON p.id = pgd.player_id
WHERE p.games_current_season != COALESCE(pgd.games_played, 0);
```

### **Log Analysis**
```bash
# Backend logs (if using logging)
tail -f src/app.log

# Frontend console (in browser dev tools)
# Check for errors, network failures, API response issues
```

---

## **📞 Escalation Procedures**

### **Critical Issues** (System Down)
1. Check server processes (`tasklist | findstr python`)
2. Verify database connectivity
3. Review recent code changes
4. Restart services in order: Database → Backend → Frontend

### **Data Integrity Issues**
1. Backup current database state
2. Identify scope of corruption
3. Restore from known good state if needed
4. Re-run affected calculations

### **Performance Degradation**
1. Monitor resource usage (CPU, memory, disk)
2. Check database query performance
3. Review recent data imports for anomalies
4. Consider system resource constraints

---

## **📝 Common Resolution Patterns**

### **"Have you tried turning it off and on again?"**
**Order for Service Restart**:
1. Stop frontend (`Ctrl+C` in npm terminal)
2. Stop backend (`Ctrl+C` in Flask terminal)
3. Stop database (if needed)
4. Start database
5. Start backend (`python src/app.py`)
6. Start frontend (`npm start`)

### **Data Inconsistency Resolution**
1. Identify affected data scope
2. Backup current state
3. Re-import from source data
4. Trigger recalculation
5. Validate results

### **Calculation Accuracy Issues**
1. Verify input data quality
2. Check parameter configuration
3. Test with known good examples
4. Compare against manual calculations
5. Review recent formula changes

---

## **🎓 Best Practices**

### **Development Workflow**
- Always backup before major changes
- Test with small data subsets first
- Verify calculations with manual examples
- Document any parameter changes

### **Data Management**
- Use Understat sync for accurate games counts
- Validate import data before processing
- Monitor match rates for name mapping
- Archive weekly states for trend analysis

### **Troubleshooting Approach**
1. **Isolate**: Narrow down to specific component
2. **Reproduce**: Create minimal test case
3. **Validate**: Check against known good state
4. **Document**: Record resolution for future reference

---

**Last Updated**: 2025-09-17 - V2.0 Enhanced Formula Troubleshooting Guide

*This guide documents proven solutions for common issues in the V2.0 Enhanced Formula system. Keep this updated with new issues and resolutions as they are discovered.*