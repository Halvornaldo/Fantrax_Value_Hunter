# Week 1 Import Fix Plan - Fantrax Value Hunter

## Project Context
**Fantrax Value Hunter** - Fantasy Premier League analytics dashboard that tracks player performance, calculates value metrics, and provides insights for team selection. We're transitioning from 2024-25 season (historical data) to 2025-26 season (current data).

## Current Situation (2025-08-20)
Successfully imported 622 players' Week 1 (2025-26 season) data via dashboard upload from Fantrax CSV export, but several display and data issues need fixing.

### Key System Information
- **Database**: PostgreSQL on port 5433
- **Credentials**: fantrax_user / fantrax_password  
- **Database Name**: fantrax_value_hunter
- **Main App**: src/app.py (Flask backend)
- **Import Endpoint**: `/api/import-form-data` (lines 1556-1701)
- **CSV Source**: `c:/Users/halvo/Downloads/Fantrax-Players-Its Coming Home (10).csv`
- **CSV Columns**: ID, Player, Team, Position, FPts, Salary
- **Frontend**: Dashboard at http://localhost:5000
- **Working Directory**: C:/Users/halvo/.claude/Fantrax_Value_Hunter

## Database State
- **Form data**: 622 records with real Week 1 points imported
- **Games data**: ALL players incorrectly have `games_played = 1` (should only be ~196 who actually played)
- **Price data**: NULL values despite import attempt
- **PPG**: Showing historical averages instead of current season

## Sprint 1: Fix Games Played Logic 🔴 CRITICAL

### Problem
Import endpoint sets `games_played = 1` for ALL players, but only players who actually played should have this.

### Current Code (src/app.py lines 1671-1677)
```python
# Update games_played count in player_games_data
cursor.execute("""
    INSERT INTO player_games_data (player_id, gameweek, games_played, last_updated)
    VALUES (%s, %s, 1, NOW())
    ON CONFLICT (player_id, gameweek)
    DO UPDATE SET games_played = 1, last_updated = NOW()
""", [player_id, gameweek])
```

### Fix Required
```python
# Update games_played count in player_games_data (only if player actually played)
games_played = 1 if points != 0 else 0
cursor.execute("""
    INSERT INTO player_games_data (player_id, gameweek, games_played, last_updated)
    VALUES (%s, %s, %s, NOW())
    ON CONFLICT (player_id, gameweek)
    DO UPDATE SET games_played = EXCLUDED.games_played, last_updated = NOW()
""", [player_id, gameweek, games_played])
```

### Manual Data Fix for Week 1
After implementing the code fix, you'll need to:
1. Identify players who scored 0 but actually played (e.g., Bart Verbruggen)
2. Manually update their `games_played` to 1
3. Create a list of these edge cases for future reference

Example SQL for manual updates:
```sql
UPDATE player_games_data 
SET games_played = 1 
WHERE player_id = (SELECT id FROM players WHERE name = 'Bart Verbruggen')
AND gameweek = 1;
```

## Sprint 2: Fix Games Display Logic

### Problem
Frontend shows "38 (24-25)" instead of "38+1" for players with both historical and current season games.

### Current Code (src/app.py lines 513-517)
```python
if gameweek <= 10:
    games_display = f"{games_historical} (24-25)"
```

### Fix Required
```python
if gameweek <= 10:
    if games_current > 0:
        games_display = f"{games_historical}+{games_current}"
    else:
        games_display = f"{games_historical} (24-25)"
```

## Sprint 3: Fix Price Import Issue

### Problem
Prices showing as NULL despite adding capture logic.

### Investigation Needed
1. Check if 'Salary' column exists in CSV
2. Verify float conversion is working
3. Ensure database commit is happening

### Current Code (src/app.py lines 1663-1669)
```python
cursor.execute("""
    INSERT INTO player_metrics (player_id, gameweek, price, last_updated)
    VALUES (%s, %s, %s, NOW())
    ON CONFLICT (player_id, gameweek) 
    DO UPDATE SET price = EXCLUDED.price, last_updated = NOW()
""", [player_id, gameweek, salary])
```

### Debug Steps
1. Add logging: `print(f"Price for {name}: {salary}")`
2. Check CSV headers match exactly
3. Verify transaction commit

## Sprint 4: Add PPG Recalculation

### Problem
PPG shows historical averages (e.g., 14.82 for Salah) instead of Week 1 data (19.00).

### Solution
After form import, recalculate PPG from current season data:

```python
# After successful import
cursor.execute("""
    UPDATE player_metrics pm
    SET ppg = (
        SELECT AVG(pf.points)
        FROM player_form pf
        WHERE pf.player_id = pm.player_id
        AND pf.gameweek <= %s
    )
    WHERE pm.gameweek = %s
""", [gameweek, gameweek])
```

## Sprint 5: Trigger Full Recalculation

### After Import Completion
Call the calculate endpoint to update all derived metrics:
- True Value
- PP$ (value_score)
- Form multipliers
- All other calculated fields

```python
# At end of import endpoint
return jsonify({
    'status': 'success',
    'imported': imported_count,
    'new_players': new_players_count,
    'errors': errors,
    'trigger_recalc': True  # Signal to frontend to trigger recalculation
})
```

## Testing Checklist

### After Each Sprint
- [ ] Re-import Week 1 data
- [ ] Verify games_played counts (should be ~196, not 622)
- [ ] Check games display shows "38+1" format
- [ ] Confirm prices are populated
- [ ] Verify PPG shows Week 1 averages
- [ ] Check True Value calculations update

### Verification Queries
```sql
-- Check games played distribution
SELECT games_played, COUNT(*) 
FROM player_games_data 
WHERE gameweek = 1 
GROUP BY games_played;

-- Check price import
SELECT COUNT(*) 
FROM player_metrics 
WHERE gameweek = 1 AND price IS NOT NULL;

-- Sample player check
SELECT p.name, pgd.games_played, pm.price, pm.ppg, pf.points
FROM players p
JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = 1
JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = 1
JOIN player_form pf ON p.id = pf.player_id AND pf.gameweek = 1
WHERE p.name IN ('Mohamed Salah', 'Erling Haaland', 'Cole Palmer', 'Bart Verbruggen');
```

## Manual Week 1 Players List (To Be Completed)

Players who scored 0 but actually played:
1. Bart Verbruggen (BHA) - Goalkeeper
2. [TO BE IDENTIFIED]
3. [TO BE IDENTIFIED]

## Priority Order
1. **Sprint 1** - Fix games_played logic (CRITICAL)
2. **Sprint 3** - Fix price import (CRITICAL for PP$ calculations)
3. **Sprint 4** - Fix PPG calculation (CRITICAL for sorting)
4. **Sprint 2** - Fix games display (Visual issue)
5. **Sprint 5** - Trigger recalculation (Final step)

## Files to Modify
- `src/app.py`: Lines 1671-1677 (games_played), 513-517 (display), 1663-1669 (price import)
- No frontend changes needed

## Important Context for New Session
When starting a fresh session after /clear, the assistant will need:
1. This plan file location: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/WEEK1_IMPORT_FIX_PLAN.md`
2. Database connection details (in this file)
3. Understanding that Week 1 data is already imported but needs fixes
4. The distinction between 2024-25 (historical) and 2025-26 (current) season data

## Session Continuation Text
After conversation reset, paste:
```
Continue Week 1 import fixes from WEEK1_IMPORT_FIX_PLAN.md. 
Project: Fantrax Value Hunter - Fantasy Premier League analytics dashboard
Location: C:/Users/halvo/.claude/Fantrax_Value_Hunter
Database: PostgreSQL port 5433, user: fantrax_user, pass: fantrax_password

Current task: Fix games_played logic to only mark players with points != 0 as having played. 
Need to modify src/app.py lines 1671-1677. 
Context: 622 players imported but all incorrectly have games_played=1, should be ~196.
```