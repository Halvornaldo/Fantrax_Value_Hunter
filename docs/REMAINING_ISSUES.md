# Remaining Issues & Features - Fantrax Value Hunter
**Date**: August 17, 2025  
**Last Updated**: Post Import Validation Fixes  
**Priority Order**: Based on user impact and development effort

---

## 🔴 **HIGH PRIORITY - CORE FUNCTIONALITY**

### **1. Table Sorting Bug (Sprint 3)**
- **Issue**: Sorting only affects current page (100 players), not entire dataset of 633 players
- **Impact**: HIGH - Affects player discovery and value identification
- **User Experience**: When sorting by True Value, users can't see the actual top performers from the full dataset
- **Technical**: Need server-side sorting with `ORDER BY` clause in SQL
- **Effort**: Medium (3-4 hours)
- **Files**: `src/app.py` (add sort parameters), `static/js/dashboard.js` (API integration)

### **2. Starter Multiplier Investigation (Sprint 3.5)**
- **Issue**: Only 2 players (Matt ORiley, David Raya) have 1.00x starter multipliers
- **Expected**: Either 0 players OR ~220 players (20 teams × 11 starters each)
- **Impact**: HIGH - Affects True Value calculations for entire dataset
- **Likely Cause**: Related to Global Name Matching System implementation
- **Effort**: Low (1-2 hours investigation)
- **Database Query Needed**: Check `player_metrics.starter_multiplier` distribution

---

## 🟡 **MEDIUM PRIORITY - DISPLAY & USABILITY**

### **3. xGI Multiplier Column Missing (Sprint 4)**
- **Issue**: xGI multipliers calculated but not displayed in UI table
- **Impact**: MEDIUM - Users can't see xGI contribution to True Value
- **Current State**: All players show 1.000x despite having different xGI90 values
- **Technical**: Need to add column to table and update display logic
- **Effort**: Low (2-3 hours)
- **Files**: `templates/dashboard.html`, `static/js/dashboard.js`, `src/app.py`

### **4. Form Data Infrastructure (Sprint 5)**
- **Issue**: `player_form` table exists but is empty - no historical performance data
- **Impact**: MEDIUM - Form calculations default to 1.0x multiplier
- **User Need**: Weekly gameweek results import to enable form-based value adjustments
- **Technical**: Need CSV import endpoint for weekly points data
- **Effort**: High (4-5 hours)
- **Components**: Data import endpoint, form calculation enhancement, UI integration

---

## 🟢 **LOW PRIORITY - SYSTEM OPTIMIZATION**

### **5. Fixture Difficulty "Neutral" Lock (Sprint 6)**
- **Issue**: Fixture difficulty appears locked to "Neutral" setting
- **Impact**: LOW - May be intentional behavior (neutral = 1.0x multiplier)
- **Investigation Needed**: Verify if this is correct behavior or actual bug
- **Effort**: Low (2 hours investigation)
- **Technical**: Check if fixture data fetching works and multipliers apply correctly

### **6. Data Validation Dashboard (Sprint 7)**
- **Issue**: No systematic data quality checks or integrity verification
- **Impact**: LOW - Current data appears accurate, but no validation system
- **Features Needed**: 
  - Missing player detection
  - Duplicate entry checks  
  - Invalid value identification (negative prices, etc.)
  - Name matching accuracy reporting
- **Effort**: Medium (3-4 hours)
- **Components**: Validation endpoint, quality metrics UI, automated checks

### **7. Complete Workflow Documentation (Sprint 8)**
- **Issue**: Missing comprehensive user guides and troubleshooting
- **Impact**: LOW - System works but needs better documentation
- **Components Needed**:
  - Weekly upload process guide
  - Parameter adjustment best practices
  - Fixture calendar integration
  - Common issues and solutions
- **Effort**: Medium (3-4 hours)
- **Focus**: User-friendly guides and visual aids

---

## ✅ **RECENTLY COMPLETED**

### **Import Validation System (Sprint 2) - COMPLETED**
- ✅ Fixed 500 error on dry run functionality
- ✅ Fixed "only 10 players showing" limitation  
- ✅ Fixed empty team dropdowns for manual mapping
- ✅ Verified Global Name Matching System learning capability
- ✅ Achieved 100% data quality with mandatory player mapping

### **Filter System (Sprint 1) - COMPLETED**
- ✅ Position filter bug: Fixed empty array handling
- ✅ Team filter population: All 20 EPL teams in dropdown
- ✅ Complex filter combinations: Verified working

---

## 🎯 **RECOMMENDED NEXT SESSION PRIORITIES**

1. **Start with Sprint 3 (Table Sorting)** - Highest user impact for core functionality
2. **Quick Sprint 3.5 investigation** - Check starter multiplier data integrity  
3. **Sprint 4 (xGI Display)** - Easy win for better visibility
4. **Consider Sprint 5 (Form Data)** - If weekly workflow is needed soon

---

## 📊 **IMPACT vs EFFORT MATRIX**

| Issue | Impact | Effort | Priority | Status |
|-------|--------|--------|----------|--------|
| Table Sorting | HIGH | MEDIUM | 🔴 | Sprint 3 |
| Starter Multiplier | HIGH | LOW | 🔴 | Sprint 3.5 |
| xGI Display | MEDIUM | LOW | 🟡 | Sprint 4 |
| Form Infrastructure | MEDIUM | HIGH | 🟡 | Sprint 5 |
| Fixture Investigation | LOW | LOW | 🟢 | Sprint 6 |
| Data Validation | LOW | MEDIUM | 🟢 | Sprint 7 |
| Documentation | LOW | MEDIUM | 🟢 | Sprint 8 |

---

## 🔧 **TECHNICAL DEBT**

### **Current Limitations:**
- Client-side sorting limits scalability beyond current 633 players
- No automated testing suite for regression prevention  
- Limited error handling in some API endpoints
- Missing comprehensive data validation system

### **Architecture Strengths:**
- Robust Global Name Matching System with learning capability
- Clean separation between Flask backend and frontend
- PostgreSQL database with proper indexing
- Modular parameter system with real-time updates

---

## 💡 **DEVELOPMENT APPROACH**

### **Sprint Methodology:**
- Continue systematic one-issue-at-a-time approach
- Test thoroughly after each fix before moving to next sprint
- Document all changes for knowledge preservation
- Maintain focus on user impact and core functionality

### **Quality Assurance:**
- Verify each fix doesn't break existing functionality
- Test edge cases and error conditions
- Maintain backwards compatibility where possible
- Document any breaking changes

---

**Status**: Ready for systematic bug resolution starting with Sprint 3  
**Next Priority**: Table Sorting Fix (highest user impact)  
**System Health**: Stable with all critical validation bugs resolved ✅