# Sprint 4 - Issues & Polish Items

## Overview
This document tracks issues, bugs, and polish items discovered during Sprint 4 implementation. These will be addressed during Phase 4 (Polish) or post-Sprint 4 completion.

---

## Issues Found During Phase 1

### 🔄 Formula Toggle Issues
**Issue**: Formula version switching back to v2.0 doesn't work properly
- **Behavior**: Switching v2.0 → v1.0 works, but v1.0 → v2.0 requires F5 refresh
- **Impact**: Minor - workaround available (refresh page)
- **Root Cause**: JavaScript state management issue in toggle functionality
- **Location**: `static/js/dashboard.js` - updateV2ColumnVisibility function
- **Priority**: Low (testing feature, not critical for production)
- **Status**: Identified

### 🎨 Visual Styling Edge Cases
**Issue**: Form column highlighting in v1.0 mode
- **Behavior**: When switching to v1.0, Form column retains v2.0-style highlighting
- **Impact**: Cosmetic only
- **Root Cause**: CSS conditional styling needs refinement
- **Location**: `static/css/dashboard.css` - v2.0 conditional styling section
- **Priority**: Low (cosmetic)
- **Status**: Identified

---

## Technical Discoveries & Lessons Learned

### 🔍 Database NULL Handling
**Discovery**: ROI sorting showed only 0/NULL values initially
- **Solution**: Added `NULLS LAST` clause specifically for ROI column sorting
- **Learning**: PostgreSQL sorts NULLs first by default - needs explicit handling
- **Code**: `src/app.py:507-510` - Special ROI sorting logic
- **Impact**: Critical for user experience with new v2.0 columns

### 🔄 Formula Engine Coexistence
**Discovery**: v1.0 and v2.0 engines running in parallel successfully
- **Learning**: Toggle system works well for A/B testing
- **Architecture**: Clean separation allows safe switching between formula versions
- **Validation**: Both engines produce consistent results for overlapping features

### 📊 Validation System Architecture
**Discovery**: Validation system properly handles insufficient data scenarios
- **Status**: Backend connected, frontend shows "Not Available" (expected)
- **Data**: Only 2 gameweeks available (GW1, GW2) - insufficient for meaningful validation
- **Learning**: System correctly detects data availability and responds appropriately
- **Timeline**: Will activate automatically as more gameweek data becomes available

---

## Planning Notes for Remaining Phases

### Phase 2 Considerations
- **Enhanced Controls**: Need to integrate Sprint 2 parameter controls
- **Lesson**: Test formula switching early to avoid state management issues
- **UI Pattern**: Follow established parameter section styling from Phase 1

### Phase 3 Considerations  
- **Validation Integration**: Backend ready, waiting for sufficient data
- **Timeline**: Realistic validation available after 5+ gameweeks of data
- **Display**: Consider "Coming Soon" vs "Not Available" messaging

### Phase 4 Polish Items
- [ ] Fix formula toggle JavaScript state management
- [ ] Refine CSS conditional styling for edge cases
- [ ] Enhanced visual feedback for formula switching
- [ ] Performance testing with larger datasets
- [ ] User experience testing and refinement

---

## Priority Classification

### 🔴 High Priority
*None identified*

### 🟡 Medium Priority  
*None identified*

### 🟢 Low Priority
- Formula toggle JavaScript fix
- Visual styling edge cases
- Enhanced error messaging
- Performance optimizations

---

## Resolution Timeline

**Target**: Address during Phase 4 (Polish) or post-Sprint 4
**Approach**: Batch fix all issues together for efficiency
**Testing**: Comprehensive testing of all toggle states and edge cases

---

*Last Updated: 2025-08-21 - Phase 1 Completion*
*Next Update: After Phase 2 completion*