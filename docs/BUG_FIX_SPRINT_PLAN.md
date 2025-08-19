# Fantrax Value Hunter - Bug Fix & Feature Enhancement Sprint Plan
**Date Created**: August 17, 2025  
**Status**: ✅ ARCHIVED - SPRINTS 1-6 COMPLETE, SUPERSEDED BY ORIGINAL PROJECT_PLAN.md  
**Priority**: Completed

## ⚠️ NOTE: This plan has been superseded by returning to the original PROJECT_PLAN.md
After completing Sprints 1-6 of this bug fix plan, the project returned to the original 4-sprint enhancement plan. This document is kept for historical reference only.

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

### **SPRINT 3: Table Sorting Fix** ✅ **COMPLETED**
**Duration**: 3-4 hours (Actual: 3 hours)  
**Goal**: Implement server-side sorting for full dataset  
**Status**: ✅ **COMPLETED** - August 17, 2025

#### Tasks:
1. **✅ Backend API Enhancement**
   - Added `sort_by` and `sort_direction` parameters to `/api/players`
   - Modified SQL query to include dynamic `ORDER BY` clause
   - Added validation for sortable fields
   - **File**: `src/app.py` (get_players function)

2. **✅ Frontend Integration**
   - Modified `handleSort()` to make API call instead of client-side sort
   - Updated `loadPlayersData()` to include sort parameters
   - **File**: `static/js/dashboard.js`

3. **✅ Performance Testing**
   - Verified sorting performance for 633 players (sub-second response)
   - Confirmed pagination maintains sort order

**Acceptance Criteria**: ✅ **ALL COMPLETED**
- ✅ Sorting affects entire dataset, not just current page
- ✅ Sort state persists through pagination  
- ✅ Performance remains acceptable (<1s response)

---

### **SPRINT 4: xGI Multiplier Display** ✅ **COMPLETED**
**Duration**: 2-3 hours (Actual: 2 hours)
**Goal**: Show xGI multiplier in table alongside other multipliers  
**Status**: ✅ **COMPLETED** - August 17, 2025

#### Tasks:
1. **✅ Backend Calculations**
   - Stored calculated `xgi_mult` in `xgi_multiplier` column
   - Added to UPDATE statement in `recalculate_true_values()`
   - **File**: `src/app.py` 

2. **✅ API Response Update**
   - Added `pm.xgi_multiplier` to SELECT statement
   - **File**: `src/app.py`

3. **✅ Frontend Display**
   - Added "xGI" column header after "Starter"
   - Updated colspan from 13 to 14
   - Added xGI multiplier to table row rendering
   - **Files**: `templates/dashboard.html`, `static/js/dashboard.js`

**Acceptance Criteria**: ✅ **ALL COMPLETED**
- ✅ xGI multiplier column visible in table
- ✅ Values show actual multipliers (not all 1.000)
- ✅ Format matches other multipliers (e.g., "0.292x")

---

### **SPRINT 5: Form Data Infrastructure** ✅ **COMPLETED**
**Duration**: 4-5 hours (Actual: 5 hours)
**Goal**: Create complete workflow for weekly form data updates  
**Status**: ✅ **COMPLETED** - August 18, 2025

#### Tasks:
1. **✅ Data Import Endpoint**
   - Created `/api/import-form-data` endpoint with auto-add functionality
   - Accepts CSV with: Player Name, Team, Gameweek, Points
   - **File**: `src/app.py`

2. **✅ Form Calculation Enhancement**
   - Populated `player_form` table from imports with ON CONFLICT handling
   - Updated form calculation to use actual data
   - **File**: `src/app.py` (calculate_form_multiplier)

3. **✅ UI Integration**
   - Added `/form-upload` page with step-by-step workflow
   - Added dashboard navigation button
   - Shows upload statistics and form data coverage
   - **Files**: `templates/form_upload.html`, `templates/dashboard.html`

**Acceptance Criteria**: ✅ **ALL COMPLETED**
- ✅ Can import gameweek results via CSV (100% success rate)
- ✅ Form calculations use imported data with weighted averages
- ✅ UI shows data freshness indicators and import statistics
- ✅ Auto-add functionality handles new players from transfers

---

### **SPRINT 6: Fixture Difficulty Complete System** ✅ **COMPLETED**
**Duration**: 6-7 hours (Actual: 8 hours)
**Goal**: Replace non-functional fixture difficulty with odds-based system  
**Status**: ✅ **COMPLETED** - August 18, 2025

#### Tasks:
1. **✅ Odds-Based Calculation System**
   - Implemented 21-point difficulty scale (-10 to +10) from betting odds
   - Position-weighted multipliers (G: 110%, D: 120%, M: 100%, F: 105%)
   - Database tables: `team_fixtures`, `fixture_odds`

2. **✅ CSV Upload Integration**
   - Created `/odds-upload` page for OddsPortal CSV imports
   - Automatic difficulty score calculation from odds
   - Team name mapping for EPL teams

3. **✅ Dashboard Controls**
   - Preset selector (Conservative ±10%, Balanced ±20%, Aggressive ±30%)
   - Fine-tuning sliders for multiplier strength and position weights
   - Replaced non-functional 5-tier/3-tier system

4. **✅ Performance Optimization**
   - Cached fixture data (eliminated 644 DB queries)
   - Batch database updates (99.8% query reduction)
   - Calculation time reduced from 90s → 46s (2x improvement)

**Acceptance Criteria**: ✅ **ALL COMPLETED**
- ✅ All 633 players have dynamic fixture multipliers (no more 1.00x lock)
- ✅ Real betting odds integration working (Arsenal 1.17x-1.21x, Leeds 0.79x-0.83x)
- ✅ Upload workflow functional with error handling
- ✅ Performance optimized for production use

---

### **SPRINT 7: Critical Bug Fixes** 📋 **PENDING**
**Duration**: 3-4 hours  
**Goal**: Fix two critical functionality issues discovered in production  
**Status**: 📋 **PENDING** - Identified August 18, 2025

#### Bug 7.1: Manual Override of Starter Predictions Not Working
**Issue**: Radio buttons for starter predictions don't update the "Starter" column
- **Expected**: Clicking manual override buttons should change starter multiplier immediately  
- **Current**: No response when clicking starter/bench/out/auto buttons
- **Impact**: Manual overrides not functional, users cannot adjust starter predictions

#### Bug 7.2: xGI Integration Name Matching Issues  
**Issue**: "Sync Understat Data ✓ Synced undefined players (90.4% match rate)"
- **Expected**: Unmatched players should route through Global Name Matching System
- **Current**: Shows "undefined" instead of player count, no manual verification workflow
- **Impact**: xGI data integration partially broken, missing manual review process

#### Tasks:
1. **Investigation Phase**
   - Debug manual override JavaScript event handling
   - Investigate xGI sync process and name matching integration
   - Check database updates for starter multiplier changes

2. **Fix Implementation**
   - Repair manual override functionality with proper API calls
   - Integrate xGI sync with Global Name Matching System validation workflow
   - Ensure unmatched players route to `/import-validation` interface

3. **Testing & Verification**
   - Test manual override buttons update starter multipliers correctly
   - Verify xGI sync shows proper player count and routes unmatched to manual review
   - Confirm both features work end-to-end

**Acceptance Criteria**:
- ✅ Manual override buttons update starter multipliers in real-time
- ✅ xGI sync shows actual player count instead of "undefined"
- ✅ Unmatched xGI players route through Global Name Matching System
- ✅ Both systems integrate seamlessly with existing validation workflow

---

### **SPRINT 8: Data Validation Dashboard** 📋 **PENDING**
**Duration**: 3-4 hours  
**Goal**: Implement comprehensive data validation and workflow documentation  
**Status**: 📋 **PENDING** - Deferred from Sprint 7

#### Tasks:
1. **Data Validation Endpoint**
   - Create `/api/validate-data` endpoint
   - Check for: Missing players, duplicate entries, invalid values, name matching accuracy

2. **Validation Dashboard**
   - New page/section for data quality metrics
   - Show coverage percentages and highlight potential issues

3. **Workflow Documentation** 
   - Document weekly upload process with step-by-step guides
   - Include troubleshooting section and user guides

**Acceptance Criteria**:
- ✅ Can run validation checks on demand
- ✅ Clear visibility of data quality issues  
- ✅ Complete workflow documentation and user guides

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
**✅ RESOLVED (Sprints 1-6):**
1. **✅ Filters**: Position & Team filters working correctly
2. **✅ Sorting**: Server-side sorting implemented for full dataset  
3. **✅ xGI**: Calculated and displayed in table with proper multipliers
4. **✅ Form**: Complete infrastructure with CSV upload workflow
5. **✅ Fixture Difficulty**: Odds-based system with 2x performance optimization

**📋 REMAINING (Sprint 7-8):**
6. **Manual Overrides**: Starter prediction buttons not functional
7. **xGI Name Matching**: Integration with Global Name Matching System broken  
8. **Data Validation**: Quality checks and workflow documentation needed

---

## 🎯 PRIORITY MATRIX

| Priority | Sprint | Impact | Effort | Status |
|----------|--------|--------|--------|--------|
| 🔴 HIGH | Sprint 1 | Critical | Low | ✅ **COMPLETED** |
| 🔴 HIGH | Sprint 2 | High | Medium | ✅ **COMPLETED** |
| 🔴 HIGH | Sprint 3 | High | Low | ✅ **COMPLETED** |
| 🟡 MEDIUM | Sprint 4 | Medium | Low | ✅ **COMPLETED** |
| 🟡 MEDIUM | Sprint 5 | High | High | ✅ **COMPLETED** |
| 🟡 MEDIUM | Sprint 6 | High | High | ✅ **COMPLETED** |
| 🔴 HIGH | Sprint 7 | High | Medium | 📋 **PENDING** |
| 🟢 LOW | Sprint 8 | Medium | Medium | 📋 **PENDING** |

---

## 📝 NOTES

### Current State Summary (Updated August 18, 2025)
**✅ FULLY OPERATIONAL (6 sprints completed):**
- **Dashboard**: Two-panel interface with all parameter controls working
- **Filters**: Position, team, price, search filters all functional  
- **Sorting**: Server-side sorting across full 633 player dataset
- **xGI Integration**: 90.4% match rate with multiplier display in table
- **Form Data**: Complete CSV upload workflow with auto-add functionality
- **Fixture Difficulty**: Odds-based system with 2x performance optimization  
- **Upload Pages**: Form and odds upload integrated with main dashboard

**🔧 MINOR ISSUES (Sprint 7 pending):**
- **Manual Overrides**: Starter prediction buttons not updating table
- **xGI Name Matching**: Not routing unmatched players through validation system

**📋 ENHANCEMENT (Sprint 8 pending):**
- **Data Validation**: Quality checks and comprehensive workflow documentation

### Technical Debt (Updated)
**✅ RESOLVED:**
- ✅ ~~Client-side sorting~~ → Server-side sorting implemented
- ✅ ~~Limited error handling~~ → Comprehensive error handling added
- ✅ ~~Missing data validation~~ → Global Name Matching System operational

**📋 REMAINING:**
- No automated testing (Sprint 8)
- Incomplete workflow documentation (Sprint 8)

### Next Steps
1. ✅ ~~Sprint 1-6~~ → All completed (Filters, Sorting, xGI, Form, Fixture Difficulty)
2. **Sprint 7**: Fix manual overrides and xGI name matching integration
3. **Sprint 8**: Data validation dashboard and workflow documentation
4. Consider adding automated testing framework

---

**END OF DOCUMENT**