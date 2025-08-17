# Fantrax Value Hunter - Bug Fix & Feature Enhancement Sprint Plan
**Date Created**: August 17, 2025  
**Status**: Planning Phase  
**Priority**: High

## Executive Summary
This document outlines identified bugs and feature enhancements for the Fantrax Value Hunter dashboard, organized into actionable sprints. Each sprint focuses on specific issues with clear acceptance criteria.

---

## 🐛 IDENTIFIED BUGS

### Critical Bugs (Affecting Core Functionality)
1. **Position Filter Bug** - Unchecking positions causes all players to disappear
2. **Team Filter Missing** - Dropdown only shows "All Teams", no individual team options
3. **Table Sorting Bug** - Only sorts current page (100 players), not entire dataset
4. **xGI Multiplier Not Displayed** - Column exists in DB but not shown in UI

### Medium Priority Bugs
5. **Fixture Difficulty Neutral Lock** - Shows as locked but unclear if working correctly
6. **xGI Multiplier Values** - All set to 1.000 despite different xGI90 values

### Low Priority Issues
7. **Form Data Empty** - Table exists but contains no historical data
8. **Data Validation Missing** - No way to verify data accuracy

---

## 🚀 FEATURE REQUESTS

1. **Rolling Form Data Workflow** - System to import and track weekly performance
2. **Data Validation Dashboard** - Spot checks and integrity verification
3. **Weekly Upload Calendar** - Fixture schedule and optimal upload times
4. **Complete Workflow Documentation** - End-to-end process documentation

---

## 📋 SPRINT PLAN

### **SPRINT 1: Critical Filter Fixes** ✅ **COMPLETED**
**Duration**: 2-3 hours (Actual: 2.5 hours)  
**Goal**: Fix all filtering issues affecting player display  
**Status**: ✅ **COMPLETED** - August 17, 2025

#### Tasks:
1. **✅ Fix Position Filter Logic** 
   - **Issue**: When no positions selected, sends empty array causing no results
   - **Root Cause**: Condition `if (currentFilters.positions.length < 4)` didn't handle length=0 properly
   - **Fix Applied**: Changed to `if (currentFilters.positions.length > 0 && currentFilters.positions.length < 4)`
   - **Files Fixed**: `static/js/dashboard.js` line 111 + `src/app.py` lines 270-274, 722-726
   - **Verification**: Tested G+D filter (287 players), single position filters, and empty position handling

2. **✅ Implement Team Filter Population**
   - **Issue**: Team dropdown not populated with actual teams, backend didn't handle multiple teams
   - **Solutions Implemented**: 
     - Created `/api/teams` endpoint returning all 20 EPL teams
     - Added `loadTeams()` and `populateTeamDropdown()` functions
     - Fixed backend team filtering to handle comma-separated multiple teams with `IN` clause
     - Updated `handleFilterChange()` to read multiple selected teams from dropdown
   - **Files Modified**: `src/app.py` (new endpoint + team filter fix), `static/js/dashboard.js` (team handling)
   - **Verification**: Tested single team (ARS: 29 players), multiple teams (ARS,MCI: 62 players)

3. **✅ Test Filter Combinations**
   - **Complex Tests Passed**:
     - Position + Team: Arsenal goalkeepers (4 players, all G+ARS)
     - Position + Team + Price: Arsenal/City forwards $8-15 (3 players)
     - Search + Position: "son" in M,F positions (24 players: Jackson, Nelson, Wilson)
   - **Edge Cases Verified**: Empty filters, all filters, partial selections

**Acceptance Criteria**: ✅ **ALL COMPLETED**
- ✅ Unchecking all positions shows all players (633 total)
- ✅ Team dropdown shows all 20 EPL teams (populated via `/api/teams`)
- ✅ Multiple filter combinations work correctly (verified with complex tests)

**Key Fixes Applied**:
- Frontend: Fixed empty array condition in position filter logic
- Backend: Added multiple team support with `IN` clause for both `/api/players` and `/api/export`
- Integration: Complete team filter implementation with dropdown population and event handling

---

### **SPRINT 2: Import Validation Critical Fixes** ✅ **COMPLETED**
**Duration**: 4-5 hours (Actual: 4 hours)  
**Goal**: Fix critical 500 errors and validation system issues  
**Status**: ✅ **COMPLETED** - August 17, 2025

#### Tasks:
1. **✅ Fixed 500 Error on Dry Run**
   - **Issue**: Syntax error with malformed `else` statement in `/api/apply-import` endpoint
   - **Root Cause**: `else` clause incorrectly attached to `for` loop after function body
   - **Fix Applied**: Removed problematic `else` clause and simplified dry run logic
   - **File**: `src/app.py` lines 1172-1179

2. **✅ Fixed "Only 10 Players Showing" Bug**
   - **Issue**: Import validation only showed 10 unmatched players instead of all 190
   - **Root Cause**: Debug limitation `[:10]` left in production code
   - **Fix Applied**: Changed `'unmatched_details': unmatched_players[:10]` to `'unmatched_details': unmatched_players`
   - **File**: `src/app.py` line 751

3. **✅ Fixed Empty Team Dropdowns**
   - **Issue**: Manual player selection dropdowns showed "Select a player from X..." but no actual players
   - **Root Cause**: Database column naming issue (`fantrax_id` vs `id`)
   - **Fix Applied**: Changed SQL query from `SELECT fantrax_id` to `SELECT id` while keeping 'fantrax_id' key for frontend
   - **File**: `src/app.py` lines 481-495 (`/api/players-by-team` endpoint)

4. **✅ Verified Global Name Matching Learning**
   - **Test Result**: Match rate improved from 13.6% → 17.3% (30 → 38 automatic matches)
   - **Learning Confirmed**: System successfully saved and applied 8 additional automatic matches after manual confirmations
   - **User Impact**: Future imports will be progressively easier as system learns

**Acceptance Criteria**:
- ✅ Dry run functionality works without 500 errors
- ✅ All 190 unmatched players visible for review (not just 10)
- ✅ Team-filtered dropdowns populated with actual players
- ✅ Global Name Matching System learns from manual confirmations
- ✅ No skipping allowed - mandatory player mapping ensures 100% data quality

**Key Fixes Applied**:
- Backend: Fixed syntax error, removed debug limitation, corrected database column references
- Learning System: Verified that manual mappings improve future import accuracy
- Data Quality: Enforced mandatory mapping for all unmatched players

---

### **SPRINT 3: Table Sorting Fix** 📋 **PENDING**
**Duration**: 3-4 hours  
**Goal**: Implement server-side sorting for full dataset  
**Status**: 📋 **PENDING** - Next Priority

#### Tasks:
1. **Backend API Enhancement**
   - Add `sort_by` and `sort_direction` parameters to `/api/players`
   - Modify SQL query to include dynamic `ORDER BY` clause
   - Add validation for sortable fields
   - **File**: `src/app.py` (get_players function)

2. **Frontend Integration**
   - Modify `handleSort()` to make API call instead of client-side sort
   - Update `loadPlayersData()` to include sort parameters
   - **File**: `static/js/dashboard.js`

3. **Performance Testing**
   - Verify sorting performance for 633 players
   - Confirm pagination maintains sort order

**Acceptance Criteria**:
- ✅ Sorting affects entire dataset, not just current page
- ✅ Sort state persists through pagination  
- ✅ Performance remains acceptable (<1s response)

---

### **SPRINT 3.5: Starter Multiplier Investigation** 🔍 **INVESTIGATION NEEDED**
**Duration**: 1-2 hours  
**Goal**: Investigate and fix starter multiplier anomaly  
**Status**: 📋 **PENDING** - Newly Identified Issue

#### Issue Description:
Only 2 players (Matt ORiley, David Raya) have 1.00x starter multipliers instead of expected pattern:
- **Expected**: Either 0 players with 1.00x OR 220 players (20 full starting lineups × 11 players each)
- **Current**: Only 2 players with 1.00x, rest at 0.650x rotation penalty
- **Likely Cause**: Related to Global Name Matching System implementation

#### Tasks:
1. **Database Investigation**
   - Query `player_metrics` table for starter_multiplier distribution
   - Check if Matt ORiley and David Raya have special mappings in `name_mappings` table
   - Verify connection to Global Name Matching System fixes

2. **Root Cause Analysis**
   - Review starter prediction logic in `src/app.py` (import_lineups endpoint)
   - Check manual override system implementation
   - Investigate if names were processed during name matching system development

3. **Fix Implementation**
   - Reset all players to proper rotation penalty (0.650x) as baseline
   - Ensure consistent starter multiplier application
   - Update documentation of expected behavior

**Acceptance Criteria**:
- ✅ Understand why only 2 players have 1.00x multipliers
- ✅ All players have consistent starter multipliers (either baseline or proper starters)
- ✅ Starter prediction system works as designed

**Investigation Priority**: HIGH - Data integrity issue affecting value calculations

---

### **SPRINT 3: xGI Multiplier Display**
**Duration**: 2-3 hours  
**Goal**: Show xGI multiplier in table alongside other multipliers

#### Tasks:
1. **Backend Calculations**
   - Store calculated `xgi_mult` in `xgi_multiplier` column
   - Add to UPDATE statement in `recalculate_true_values()`
   - **File**: `src/app.py` lines ~190-200

2. **API Response Update**
   - Add `pm.xgi_multiplier` to SELECT statement
   - **File**: `src/app.py` line ~259

3. **Frontend Display**
   - Add "xGI" column header after "Starter"
   - Update colspan from 13 to 14
   - Add xGI multiplier to table row rendering
   - **Files**: `templates/dashboard.html`, `static/js/dashboard.js`

**Acceptance Criteria**:
- ✅ xGI multiplier column visible in table
- ✅ Values show actual multipliers (not all 1.000)
- ✅ Format matches other multipliers (e.g., "0.292x")

---

### **SPRINT 4: Form Data Infrastructure**
**Duration**: 4-5 hours  
**Goal**: Create complete workflow for weekly form data updates

#### Tasks:
1. **Data Import Endpoint**
   - Create `/api/import-form-data` endpoint
   - Accept CSV with: Player Name, Team, Gameweek, Points
   - **File**: New endpoint in `src/app.py`

2. **Form Calculation Enhancement**
   - Populate `player_form` table from imports
   - Update form calculation to use actual data
   - **File**: `src/app.py` (calculate_form_multiplier)

3. **UI Integration**
   - Add "Import Form Data" button
   - Show last import date/gameweek
   - Display form data coverage stats

**Acceptance Criteria**:
- ✅ Can import gameweek results via CSV
- ✅ Form calculations use imported data
- ✅ UI shows data freshness indicators

---

### **SPRINT 5: Data Validation & Testing**
**Duration**: 3-4 hours  
**Goal**: Implement comprehensive data validation

#### Tasks:
1. **Validation Endpoint**
   - Create `/api/validate-data` endpoint
   - Check for:
     - Missing players
     - Duplicate entries
     - Invalid values (negative prices, etc.)
     - Name matching accuracy

2. **Validation Dashboard**
   - New page/section for data quality metrics
   - Show coverage percentages
   - Highlight potential issues

3. **Automated Tests**
   - Unit tests for calculations
   - Integration tests for key workflows
   - Data integrity checks

**Acceptance Criteria**:
- ✅ Can run validation checks on demand
- ✅ Clear visibility of data quality issues
- ✅ Automated tests pass

---

### **SPRINT 6: Fixture Difficulty Investigation**
**Duration**: 2 hours  
**Goal**: Verify fixture difficulty system works correctly

#### Tasks:
1. **Investigate "Neutral" Lock**
   - Verify if intentional (neutral should always be 1.0x)
   - Check if fixture data is being fetched
   - Confirm multipliers are applied correctly

2. **Testing**
   - Verify different difficulty tiers work
   - Check if API integration is functional
   - Test manual fixture difficulty adjustments

**Acceptance Criteria**:
- ✅ Understanding of why neutral is locked
- ✅ Confirmation that fixture system works
- ✅ Documentation of expected behavior

---

### **SPRINT 7: Documentation & Workflow**
**Duration**: 3-4 hours  
**Goal**: Complete documentation and workflow calendar

#### Tasks:
1. **Workflow Documentation**
   - Document weekly upload process
   - Create step-by-step guides
   - Include troubleshooting section

2. **Fixture Calendar Integration**
   - Add fixture schedule view
   - Mark optimal upload windows
   - Show gameweek deadlines

3. **User Guide**
   - How to use each feature
   - Best practices
   - Common issues and solutions

**Acceptance Criteria**:
- ✅ Complete workflow documentation
- ✅ Visual fixture calendar
- ✅ User-friendly guides

---

## 📊 QUICK REFERENCE

### File Locations
- **Backend**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/src/app.py`
- **Frontend JS**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/static/js/dashboard.js`
- **HTML Template**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/templates/dashboard.html`
- **Config**: `C:/Users/halvo/.claude/Fantrax_Value_Hunter/config/system_parameters.json`

### Database Tables
- `players` - Main player data with xGI stats
- `player_metrics` - Calculated values and multipliers
- `player_form` - Historical performance (currently empty)
- `name_mappings` - Name matching system

### Key Issues Summary
1. **Filters**: Position & Team filters broken
2. **Sorting**: Only client-side, needs server-side
3. **xGI**: Calculated but not displayed
4. **Form**: Infrastructure exists but no data
5. **Validation**: No data quality checks

---

## 🎯 PRIORITY MATRIX

| Priority | Sprint | Impact | Effort | Status |
|----------|--------|--------|--------|--------|
| 🔴 HIGH | Sprint 1 | Critical | Low | ✅ **COMPLETED** |
| 🔴 HIGH | Sprint 2 | High | Medium | ✅ **COMPLETED** |
| 🔴 HIGH | Sprint 2.5 | High | Low | 📋 **PENDING** |
| 🟡 MEDIUM | Sprint 3 | Medium | Low | Pending |
| 🟡 MEDIUM | Sprint 4 | High | High | Pending |
| 🟢 LOW | Sprint 5 | Medium | Medium | Pending |
| 🟢 LOW | Sprint 6 | Low | Low | Pending |
| 🟢 LOW | Sprint 7 | Medium | Medium | Pending |

---

## 📝 NOTES

### Current State Summary
- **Working**: Basic dashboard, xGI data sync (85% match rate), parameter controls
- **Broken**: Position/Team filters, sorting, xGI display
- **Missing**: Form data, validation, documentation

### Technical Debt
- Client-side sorting limits scalability
- No automated testing
- Limited error handling
- Missing data validation

### Next Steps
1. Start with Sprint 1 (Critical Filter Fixes)
2. Test each fix thoroughly before moving on
3. Document changes as we go
4. Consider adding automated tests

---

**END OF DOCUMENT**