# Known Issues & Bug Tracking

## Minor Issues

### Games Column Sorting Issue
- **Status**: Open
- **Priority**: Low  
- **Description**: Games column sorts alphabetically on display string instead of numerically
- **Current Behavior**: "38 (24-25)" appears after "0" when sorting ascending
- **Expected Behavior**: Should sort by actual games count (38 > 0)
- **Root Cause**: Frontend sorting on `games_display` string instead of `games_played_historical` numeric field
- **API**: Backend sorting works correctly - issue is frontend table sorting
- **Screenshots**: `Screenshot 2025-08-19 233742.png`, `Screenshot 2025-08-19 233818.png`, `Screenshot 2025-08-19 234007.png`
- **Solution Ideas**: 
  - Add `data-sort-value` attribute to Games column cells with numeric value
  - Override table sorting for Games column to use numeric field
  - Use separate hidden column for sorting
- **Planned Fix**: Sprint 4 (Polish & Optimization) in PROJECT_PLAN.md

---

## Completed Issues
- None yet

## Feature Requests  
- None yet