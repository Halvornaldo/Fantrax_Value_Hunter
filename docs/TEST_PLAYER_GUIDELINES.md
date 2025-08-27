# Test Player System Guidelines
## Fantrax Value Hunter Test Data Management

### **System Status: Production Ready**

This document provides guidelines for using the test player system in the Fantrax Value Hunter to prevent data corruption and maintain clean separation between test and production data.

**Version**: 1.0  
**Last Updated**: 2025-08-26  
**System**: V2.0 Enhanced Formula with Test Player Integration

---

## **Overview**

The test player system provides dedicated test data that doesn't interfere with real player analysis. This prevents the need to use real players (like Haaland or Salah) for testing, which can corrupt the production database.

### **Key Benefits**

- **Data Integrity**: Keeps test data completely separate from real player data
- **Safe Testing**: No risk of corrupting real player calculations or analysis  
- **Clean Dashboard**: Test players are filtered out by default from main dashboard
- **Flexible Testing**: Various test scenarios available for different edge cases

---

## **Test Player System Structure**

### **Test Player Identification**
- **Player IDs**: All test players use `TEST_` prefix (e.g., `TEST_001`, `TEST_002`)
- **Team Code**: All test players belong to team `TST`
- **Names**: Clear test names (e.g., "Test Player High Value", "Test Player Zero Games")

### **Available Test Players**

| ID | Name | Position | Scenario |
|---|---|---|---|
| TEST_001 | Test Player High Value | F | High true value player for testing top-tier calculations |
| TEST_002 | Test Player Low Value | M | Low value player for testing budget options |
| TEST_003 | Test Player Zero Games | D | Player with no games played for edge case testing |
| TEST_004 | Test Player High xGI | F | High xGI multiplier testing |
| TEST_005 | Test Player Rotation Risk | M | Rotation/bench scenarios |

### **Test Data Coverage**
Test players have complete data across all relevant tables:
- `players` - Basic player information and calculated values
- `player_metrics` - Weekly performance metrics for current gameweek
- `player_games_data` - Games played and points data for dashboard filtering
- `raw_player_snapshots` - Raw data for trend analysis testing (GW99)
- `raw_form_snapshots` - Form data for EWMA calculations

---

## **Usage Guidelines**

### **For Testing Calculations**
```python
# Test with specific test player
test_player_id = "TEST_001"
result = calculate_player_value(test_player_id)
```

### **For Testing Dashboard API**
```bash
# Normal dashboard (test players filtered out)
curl "http://localhost:5001/api/players"

# Include test players for debugging
curl "http://localhost:5001/api/players?include_test=true"
```

### **For Testing Trend Analysis**
```python
# Test trend analysis with test gameweek
api_url = "/api/trends/calculate?gameweek_start=99&gameweek_end=99"
# GW99 contains only test player data
```

### **For Testing Raw Data Import**
- Use gameweek 99 for testing raw data snapshots
- Test players have complete raw data for testing import workflows
- No risk of corrupting real gameweek data

---

## **Dashboard Integration**

### **Default Filtering**
- **Main Dashboard**: Test players are hidden by default (`p.team != 'TST'`)
- **Production API**: Returns only real players (439 as of 2025-08-26)
- **Clean User Experience**: No test data visible to end users

### **Debug Mode**
- **Parameter**: Add `?include_test=true` to any API request
- **Use Case**: Developer debugging and testing scenarios
- **Result**: Shows both real players and test players

### **API Response Indicators**
```json
{
  "total_count": 444,
  "filtered_count": 439,
  "filters_applied": {
    "include_test": false
  }
}
```

---

## **Testing Scenarios**

### **High Value Player Testing**
```bash
# Test high-value calculations
curl "http://localhost:5001/api/players?include_test=true&search=TEST_001"
```

### **Edge Case Testing**  
```bash
# Test zero games player handling
curl "http://localhost:5001/api/players?include_test=true&search=TEST_003"
```

### **Calculation Engine Testing**
```python
# Test V2.0 Enhanced Formula with test data
test_params = {
    'formula_optimization_v2': {
        'exponential_form': {'alpha': 0.9}
    }
}
recalculate_true_values(gameweek=1, test_only=True)
```

### **Import Testing**
- Upload test CSV files with TEST_ player IDs
- Use gameweek 99 for testing raw data imports
- Test players won't affect production calculations

---

## **Maintenance Guidelines**

### **Adding New Test Players**
```sql
-- Always use TEST_ prefix and TST team
INSERT INTO players (id, name, team, position, true_value, roi)
VALUES ('TEST_006', 'Test Player New Scenario', 'TST', 'G', 5.0, 0.3);

-- Add supporting data in other tables
INSERT INTO player_metrics (player_id, gameweek, price, true_value)
VALUES ('TEST_006', 1, 16.0, 5.0);

INSERT INTO player_games_data (player_id, gameweek, games_played, total_points)
VALUES ('TEST_006', 1, 1, 5.0);
```

### **Cleaning Test Data**
```sql
-- Remove all test players and their data
DELETE FROM player_games_data WHERE player_id LIKE 'TEST_%';
DELETE FROM player_metrics WHERE player_id LIKE 'TEST_%';
DELETE FROM raw_player_snapshots WHERE player_id LIKE 'TEST_%';
DELETE FROM raw_form_snapshots WHERE player_id LIKE 'TEST_%';
DELETE FROM players WHERE team = 'TST';
```

### **Test Gameweek Management**
- **GW99**: Reserved for test raw snapshots
- **GW98**: Available for additional test scenarios
- **GW97**: Available for multi-gameweek testing

---

## **Best Practices**

### **DO**
- ✅ Always use TEST_ prefix for test player IDs
- ✅ Use team code 'TST' for easy filtering  
- ✅ Use clear, descriptive test player names
- ✅ Test with various scenarios (high/low values, edge cases)
- ✅ Use gameweek 99 for raw data testing
- ✅ Document any new test scenarios you create

### **DON'T**
- ❌ Never use real player IDs for testing
- ❌ Don't test with real gameweeks (1-38)
- ❌ Don't modify real player data for testing purposes
- ❌ Don't leave test players in production API responses
- ❌ Don't use confusing or production-like test names

### **Testing Real Data Issues**
If you need to test with real data scenarios:
```python
# Create test players based on real player characteristics
real_player_data = get_player_data("061vq")  # Haaland
create_test_player("TEST_HAALAND_LIKE", real_player_data)
```

---

## **API Documentation Updates**

### **New Parameter**
- **Parameter**: `include_test`
- **Type**: Boolean (default: false)
- **Description**: Include test players in API responses
- **Usage**: `?include_test=true`

### **Response Changes**
All `/api/players` responses now include:
```json
{
  "filters_applied": {
    "include_test": false
  }
}
```

---

## **Troubleshooting**

### **Test Players Appear in Production Dashboard**
- **Cause**: `include_test=true` parameter used in production
- **Fix**: Remove parameter or set to `false`
- **Prevention**: Check API calls don't include test parameter

### **Test Data Corrupted**
- **Cause**: Real player data mixed with test data
- **Fix**: Clean up using SQL queries above
- **Prevention**: Always use TEST_ prefix and TST team

### **Dashboard Player Count Wrong**
- **Expected**: 439 real players (as of 2025-08-26)
- **With Test**: 444 total (439 real + 5 test)
- **Debug**: Check `?include_test=true` parameter

### **Test Players Missing**
- **Cause**: Test data not created or accidentally deleted
- **Fix**: Re-run test player creation script
- **Verify**: Check players table for team = 'TST'

---

## **Integration with Existing Systems**

### **Calculation Engine V2.0**
- Test players work with all V2.0 Enhanced Formula calculations
- All multipliers (form, fixture, xGI, starter) are testable
- Test players have proper baseline data for normalized calculations

### **Gameweek Manager**
- Test gameweeks (GW99) are ignored by production gameweek detection
- GameweekManager correctly identifies current gameweek without test interference
- Emergency protection doesn't apply to test gameweeks

### **Trend Analysis System**
- Test players have raw snapshots in GW99 for trend testing
- Trend analysis API works with test data using `gameweek=99`
- No interference with production trend analysis

### **Name Matching System**
- Test players bypass name matching (no external data sources)
- Name mappings not required for test players
- Clean separation from production name matching workflows

---

**This test player system ensures clean, safe testing practices while maintaining full production data integrity. Always use test players for development and debugging to prevent corruption of real player analysis data.**