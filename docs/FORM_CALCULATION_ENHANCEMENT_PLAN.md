# Form Calculation Enhancement Plan

## Current State Summary

### What's Already Implemented
1. **Database Structure**
   - Table: `player_game_scores` created
   - Fields: `player_id`, `game_number`, `points_scored`, `opponent`, `import_timestamp`
   - Primary key: `(player_id, game_number)`

2. **Import Infrastructure**
   - `import_historical_games.py` - Bulk import script for games 1-4
   - `game_scores_endpoint.py` - API endpoint `/api/import-game-scores`
   - Games 1-4 data imported (but includes invalid 0-point players)

3. **Current EWMA Implementation**
   - Located in `calculation_engine_v2.py`
   - Uses `player_form` table (NOT the new `player_game_scores`)
   - Alpha = 0.87 (produces wide form ranges)
   - Progressive ranges: 0.95-1.05 (early) → 0.70-1.30 (late season)

### Current Problems
1. **Data Quality**: ~400 players with 0 FPts who didn't actually play
2. **EWMA Source**: Still using `player_form` instead of granular game data
3. **Form Range**: Too wide (0.70-1.30) vs target (0.9-1.1)
4. **No UI**: Manual import process for future games

## Enhancement Roadmap

### Phase 1: Data Quality Fix (Priority 1)
**Goal**: Clean existing data and ensure only actual players are included

#### 1.1 Identify Valid 0-Point Players
- [ ] Implement Understat match data extraction (see UNDERSTAT_MATCH_DATA_INVESTIGATION.md)
- [ ] Cross-reference with `games_current_season` column
- [ ] Create validation script to categorize players:
  - Definitely played (4 games in DB)
  - Possibly played (1-3 games)
  - Didn't play (0 games)

#### 1.2 Clean Existing Data
```sql
-- Add validation column
ALTER TABLE player_game_scores
ADD COLUMN did_play BOOLEAN DEFAULT TRUE;

-- Remove invalid entries after validation
DELETE FROM player_game_scores
WHERE did_play = FALSE;
```

#### 1.3 Re-import Games 1-4
- [ ] Run validation to identify who actually played
- [ ] Re-import with proper filtering
- [ ] Verify data quality

### Phase 2: EWMA Integration (Priority 2)
**Goal**: Use granular game data for accurate form calculation

#### 2.1 Update Data Source
```python
# In calculation_engine_v2.py
def _get_recent_points_from_db(self, player_id: str, limit: int = 5):
    """Fetch from player_game_scores instead of player_form"""
    cursor.execute("""
        SELECT points_scored
        FROM player_game_scores
        WHERE player_id = %s
        AND did_play = TRUE
        ORDER BY game_number DESC
        LIMIT %s
    """, [player_id, limit])

    results = cursor.fetchall()
    return [float(row[0]) for row in results]
```

#### 2.2 Integrate into Main App
- [ ] Add `game_scores_endpoint.py` to main `app.py`
- [ ] Ensure proper database connections
- [ ] Test with existing frontend

### Phase 3: Alpha Tuning (Priority 3)
**Goal**: Achieve 0.9-1.1 form multiplier range

#### 3.1 Adjust Alpha Parameter
```json
// config/system_parameters.json
{
  "formula_optimization_v2": {
    "exponential_form": {
      "alpha": 0.65  // Reduced from 0.87
    }
  }
}
```

#### 3.2 Consider Alternative Approaches
- **Option A**: Lower alpha (0.5-0.7)
- **Option B**: Tighter progressive ranges
- **Option C**: Apply additional dampening factor

#### 3.3 Testing Matrix
| Alpha | Early Range | Late Range | Target Met? |
|-------|------------|------------|-------------|
| 0.87  | 0.95-1.05  | 0.70-1.30  | No         |
| 0.70  | 0.97-1.03  | 0.85-1.15  | Partial    |
| 0.65  | 0.98-1.02  | 0.90-1.10  | Yes?       |
| 0.60  | 0.99-1.01  | 0.93-1.07  | Too narrow?|

### Phase 4: Import UI (Priority 4)
**Goal**: User-friendly interface for importing game data

#### 4.1 Create Import Page
```html
<!-- templates/import_game_scores.html -->
<form action="/api/import-game-scores" method="POST">
  <input type="file" name="csv_file" accept=".csv" required>
  <input type="number" name="game_number" min="5" required>
  <button type="submit">Import Game Data</button>
</form>
```

#### 4.2 Enhanced Features
- [ ] Drag-and-drop file upload
- [ ] Game number auto-increment
- [ ] Import summary display
- [ ] 0-point player review panel

#### 4.3 Add Route to App
```python
@app.route('/import-games')
def import_games_page():
    # Get last imported game number
    # Show import form
    return render_template('import_game_scores.html')
```

### Phase 5: Future Game Process (Priority 5)
**Goal**: Streamlined process for games 5+

#### 5.1 Pre-Import Validation
```python
def prepare_for_import(game_number):
    # Snapshot current state
    snapshot_player_stats()

    # Sync with Understat
    sync_understat_data()

    # Get players who played
    return get_gameweek_participants(game_number)
```

#### 5.2 Smart Import Logic
```python
def import_future_game(csv_file, game_number):
    # Get validation data
    players_who_played = prepare_for_import(game_number)

    # Import with validation
    df = pd.read_csv(csv_file)
    for row in df.iterrows():
        if should_import_player(row, players_who_played):
            insert_game_score(row, game_number)
```

## Testing & Validation

### Test Cases
1. **0-Point Player Validation**
   - Player with 0 points who played (e.g., red card)
   - Player with 0 points who didn't play
   - Edge cases (late substitutions, etc.)

2. **Form Calculation**
   - New player (no history)
   - Player with gaps in games
   - Consistent performer vs volatile

3. **Alpha Tuning**
   - Track form multipliers across all players
   - Verify 90% stay within 0.9-1.1 range
   - Check outliers and edge cases

## Implementation Timeline

### Week 1: Investigation & Data Cleaning
- Day 1-2: Investigate Understat match data access
- Day 3-4: Create validation scripts
- Day 5: Clean and re-import games 1-4

### Week 2: Core Integration
- Day 1-2: Update EWMA to use `player_game_scores`
- Day 3-4: Test and tune Alpha parameter
- Day 5: Verify form calculations

### Week 3: UI & Polish
- Day 1-2: Create import UI
- Day 3-4: Test with game 5 data
- Day 5: Documentation and deployment

## Configuration Management

### System Parameters Update
```json
{
  "form_calculation": {
    "data_source": "player_game_scores",
    "alpha": 0.65,
    "progressive_ranges": {
      "enabled": true,
      "target_range": [0.9, 1.1]
    }
  },
  "import_validation": {
    "use_understat": true,
    "min_minutes_to_count": 1,
    "allow_zero_point_players": true
  }
}
```

## Success Metrics
1. **Data Quality**: 95%+ accuracy in player participation
2. **Form Range**: 90% of multipliers within 0.9-1.1
3. **Import Speed**: < 30 seconds per game file
4. **User Experience**: One-click import with validation

## Notes & Considerations
- Understat data may lag 24-48 hours after matches
- Name matching between systems needs fuzzy logic
- Consider caching Understat data for performance
- Plan for API rate limiting
- Handle edge cases (postponed games, red cards, etc.)