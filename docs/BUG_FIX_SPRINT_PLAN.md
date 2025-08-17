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

### **SPRINT 1: Critical Filter Fixes**
**Duration**: 2-3 hours  
**Goal**: Fix all filtering issues affecting player display

#### Tasks:
1. **Fix Position Filter Logic**
   - **Issue**: When no positions selected, sends empty array causing no results
   - **Root Cause**: Condition `if (currentFilters.positions.length < 4)` doesn't handle length=0 properly
   - **Fix**: Change to `if (currentFilters.positions.length > 0 && currentFilters.positions.length < 4)`
   - **File**: `static/js/dashboard.js` line ~65

2. **Implement Team Filter Population**
   - **Issue**: Team dropdown not populated with actual teams
   - **Investigation Needed**: 
     - Check if teams are loaded from backend
     - Verify HTML select element ID matches JavaScript
   - **Files**: `templates/dashboard.html`, `static/js/dashboard.js`

3. **Test Filter Combinations**
   - Verify position + team + price filters work together
   - Ensure "All" selections work properly
   - Test edge cases (no filters, all filters)

**Acceptance Criteria**:
- ✅ Unchecking all positions shows all players
- ✅ Team dropdown shows all 20 EPL teams
- ✅ Multiple filter combinations work correctly

---

### **SPRINT 2: Table Sorting Fix**
**Duration**: 3-4 hours  
**Goal**: Implement server-side sorting for full dataset

#### Tasks:
1. **Backend API Enhancement**
   - Add `sort_by` and `sort_direction` parameters to `/api/players`
   - Modify SQL query to include `ORDER BY` clause
   - **File**: `src/app.py` (get_players function)

2. **Frontend Integration**
   - Modify `handleSort()` to make API call instead of client-side sort
   - Update `loadPlayersData()` to include sort parameters
   - Remove `sortPlayersData()` function (no longer needed)
   - **File**: `static/js/dashboard.js`

3. **Performance Testing**
   - Ensure sorting is fast with 633 players
   - Verify pagination works with sorting

**Acceptance Criteria**:
- ✅ Sorting affects entire dataset, not just current page
- ✅ Sort state persists through pagination
- ✅ Performance remains acceptable (<1s response)

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
| 🔴 HIGH | Sprint 1 | Critical | Low | Pending |
| 🔴 HIGH | Sprint 2 | High | Medium | Pending |
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