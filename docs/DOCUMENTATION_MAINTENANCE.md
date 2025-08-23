# Documentation Maintenance Guide

## Post-Sprint Documentation Update Requirements

This document defines the mandatory documentation updates required after completing each Formula Optimization sprint.

## Core Documentation (MUST Update After Every Sprint)

### 1. `docs/DATABASE_SCHEMA.md`
**Update Requirements:**
- Add all new database columns with types and descriptions
- Document new tables created during sprint
- Update migration status and dates
- Add new indexes, constraints, or relationships

**Example Sprint 1 Updates:**
- Added v2.0 columns to `players` table (true_value, roi, formula_version, etc.)
- Added validation tables (player_predictions, formula_validation_results)
- Updated migration completion status

### 2. `docs/API_REFERENCE.md`  
**Update Requirements:**
- Document all new API endpoints with full request/response examples
- Update existing endpoint responses if changed
- Add authentication requirements for new endpoints
- Include curl examples for testing

**Example Sprint 1 Updates:**
- Added `/api/calculate-values-v2` endpoint with sample responses
- Added `/api/toggle-formula-version` admin endpoint
- Added `/api/get-formula-version` status endpoint

### 3. `docs/DEVELOPMENT_SETUP.md`
**Update Requirements:**
- Add new testing procedures and expected outputs
- Update feature status checklist with sprint completion
- Add new development dependencies or setup steps
- Update system requirements if changed

**Example Sprint 1 Updates:**
- Added `python test_v2_api.py` testing procedure
- Updated v2.0 feature status checklist
- Added curl testing examples

### 4. `docs/FEATURE_GUIDE.md`
**Update Requirements:**
- Add new dashboard features with usage instructions
- Update formula explanations and examples
- Add new parameter controls and their effects
- Update UI screenshots if visual changes made

**Example Sprint 1 Updates:**
- Added v2.0 status section explaining current vs future features
- Clear distinction between v1.0 (dashboard) and v2.0 (backend)

## Additional Documentation (Update As Relevant)

### Formula-Related Documents
- **`docs/V2_ENHANCED_FORMULA_GUIDE.md`** - Complete V2.0 formula documentation with calculations, examples, and API integration
- **`docs/FORMULA_OPTIMIZATION_SPRINTS.md`** - Mark sprints complete, update implementation results (DEPRECATED - moved to V2_ENHANCED_FORMULA_GUIDE.md)
- **`docs/FORMULA_REFERENCE.md`** - DEPRECATED - consolidated into V2_ENHANCED_FORMULA_GUIDE.md
- **`docs/FORMULA_MIGRATION_GUIDE.md`** - DEPRECATED - consolidated into V2_ENHANCED_FORMULA_GUIDE.md

### Project Management Documents
- **`CLAUDE.md`** - Update system status, recent features, and sprint progress
- **`README.md`** - Update feature highlights if user-facing changes implemented
- **`docs/TESTING_METHODOLOGY.md`** - Add new validation procedures and test cases

### Implementation-Specific Documents
- **`docs/FUTURE_IDEAS.md`** - Move implemented features from ideas to completed
- **`docs/VALUE_CALCULATION_ANALYSIS.md`** - Update with new calculation logic analysis
- **`docs/PRD.md`** - Update product requirements with implemented features

## Sprint-Specific Documentation Requirements

### Sprint 2: Advanced Calculations (EWMA Form, Dynamic Blending, Normalized xGI)
**Priority Updates:**
- `FORMULA_REFERENCE.md` - Add EWMA calculations, blending formulas
- `DATABASE_SCHEMA.md` - Document new calculation columns
- `FEATURE_GUIDE.md` - Update form calculation explanations

### Sprint 3: Validation Framework (Backtesting, RMSE/MAE)
**Priority Updates:**
- `TESTING_METHODOLOGY.md` - Add backtesting procedures and metrics
- `API_REFERENCE.md` - Add validation endpoint documentation
- `DATABASE_SCHEMA.md` - Document validation result tables

### Sprint 4: Dashboard Integration + Dynamic Blending Complete ✅ COMPLETED (2025-08-22)
**Priority Updates:**
- `FEATURE_GUIDE.md` - Major update with new v2.0 dashboard features  
- `API_REFERENCE.md` - Update player endpoints with v2.0 response format + historical_ppg
- `DEVELOPMENT_SETUP.md` - Update testing procedures for dual engine system
- `DATABASE_SCHEMA.md` - Document historical_ppg calculation and gameweek detection

**🎯 CRITICAL BREAKTHROUGH: Dynamic Blending Implementation (2025-08-22):**
- **Historical Data Integration**: Fixed missing 2024-25 season data in calculations
- **Gameweek Detection Fix**: Replaced hardcoded GW1 with database MAX(gameweek) query
- **API Enhancement**: Added historical_ppg calculation to both main and v2.0 endpoints  
- **Engine Separation**: Documented critical dual engine architecture warnings

**Recent Polish Fixes (2025-08-22):**
- Fixed tooltip auto-triggering on page load
- Resolved multiple tooltip cleanup and positioning issues
- Enhanced UI robustness with proper initialization timing
- Completed all Phase 4 polish requirements

### Sprint 5: Future Features (Team Style, Position Models)
**Priority Updates:**
- `FUTURE_IDEAS.md` - Move implemented features to completed section
- `FORMULA_REFERENCE.md` - Add new calculation methodologies
- `FEATURE_GUIDE.md` - Add advanced feature documentation

## Documentation Update Checklist

### After Each Sprint Completion:

1. **Core Documentation Updates**
   - [ ] Update `docs/DATABASE_SCHEMA.md` with new schema changes
   - [ ] Update `docs/API_REFERENCE.md` with new endpoints
   - [ ] Update `docs/DEVELOPMENT_SETUP.md` with testing procedures
   - [ ] Update `docs/FEATURE_GUIDE.md` with new features

2. **Additional Documentation Review**
   - [ ] Review and update sprint-specific documents (see above)
   - [ ] Update `CLAUDE.md` system status
   - [ ] Update `README.md` if user-facing changes
   - [ ] Check `FORMULA_OPTIMIZATION_SPRINTS.md` completion status

3. **Documentation Consistency Check**
   - [ ] Verify all implementation dates use YYYY-MM-DD format
   - [ ] Ensure consistent status indicators (✅ Complete, 🔄 Pending, ⏸️ Deferred)
   - [ ] Update "Last updated" dates at bottom of modified files
   - [ ] Verify cross-references between documents are accurate

4. **Git Best Practices**
   - [ ] Stage all documentation changes: `git add docs/`
   - [ ] Commit with semantic message: `git commit -m "docs: Update documentation for Sprint X completion"`
   - [ ] Tag sprint completion: `git tag "v2.X-sprintX-complete"`
   - [ ] Include Claude Code attribution in commit message

## Documentation Standards

### Status Indicators
- **✅ Complete** - Feature fully implemented and tested
- **🔄 Pending** - Feature planned for future sprint  
- **⏸️ Deferred** - Feature postponed to later release

### Date Format
- Always use **YYYY-MM-DD** format for implementation dates
- Example: "Added 2025-08-21" or "Complete (2025-08-21)"

### Version References
- **v1.0** - Current production system (mixed price/prediction formula)
- **v2.0** - New optimized system (separate true value/ROI)
- **Sprint N** - Implementation phase references

### Cross-References
- Link between related documents using relative paths
- Example: "See `docs/DATABASE_SCHEMA.md` for table structures"
- Verify all cross-references remain valid after updates

## Quality Assurance

### Documentation Review Process
1. **Technical Accuracy** - Verify all code examples and API responses are current
2. **Completeness** - Ensure all new features are documented with usage examples
3. **Consistency** - Check formatting, terminology, and cross-references
4. **User Experience** - Verify documentation helps users understand and use features

### Common Documentation Issues to Avoid
- Outdated API response examples
- Missing implementation dates
- Inconsistent status indicators across files
- Broken cross-references between documents
- Unclear distinction between v1.0 and v2.0 features

## 🚨 SYSTEM ARCHITECTURE (2025-08-23)

### **Consolidated V2.0 Enhanced Engine**

**✅ SYSTEM ARCHITECTURE UPDATE:**
The system has been consolidated to a single V2.0 Enhanced Formula engine:

**V2.0 Enhanced Engine:**
- Location: `calculation_engine_v2.py` (single engine)
- Parameters: `formula_optimization_v2` structure with enhanced controls
- Database: Uses `true_value` and `roi` columns (V2.0 calculations only)
- Formula: `True Value = Blended_PPG × multipliers`, `ROI = True Value ÷ Price`

**📋 DOCUMENTATION REQUIREMENTS:**
- `API_REFERENCE.md` - V2.0 Enhanced endpoints and calculations
- `DEVELOPMENT_SETUP.md` - V2.0 testing procedures and validation
- `FEATURE_GUIDE.md` - V2.0 Enhanced dashboard features and controls
- `DATABASE_SCHEMA.md` - V2.0 column usage and raw data snapshot system

### **Gameweek Detection Logic - Document in DATABASE_SCHEMA.md**

**🎯 CRITICAL FIX DISCOVERED:**
Many functions were using hardcoded `gameweek = 1` instead of database detection.

**✅ CORRECT PATTERN:**
```sql
SELECT MAX(gameweek) FROM player_metrics WHERE gameweek IS NOT NULL
```

**❌ INCORRECT PATTERNS TO AVOID:**
- `gameweek = 1` (hardcoded)
- `current_gameweek = getCurrentGameweek()` without database query
- Using parameter gameweek without validation

**📋 FILES THAT NEED GAMEWEEK LOGIC:**
- `src/app.py` (manual overrides, data imports)
- `calculation_engine_v2.py` (dynamic blending)
- Any new calculation or import functionality

### **Historical Data Integration - Document in API_REFERENCE.md**

**🎯 ESSENTIAL DATA PIPELINE:**
V2.0 Dynamic Blending requires historical PPG calculation in ALL player queries:

```sql
CASE 
    WHEN COALESCE(pgd.games_played_historical, 0) > 0 
    THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
    ELSE pm.ppg 
END as historical_ppg
```

**📋 AFFECTED ENDPOINTS:**
- `/api/players` - Main dashboard data
- `/api/trends/calculate` - Raw data trend analysis
- Any new player data endpoints

### **Raw Data Snapshot System - Document in DATABASE_SCHEMA.md**

**🎯 NEW TREND ANALYSIS ARCHITECTURE (2025-08-23):**
The system now captures weekly raw data snapshots for retrospective trend analysis:

**Raw Snapshot Tables:**
```sql
raw_player_snapshots   -- Weekly player performance and context data
raw_fixture_snapshots  -- Weekly fixture difficulty and odds data  
raw_form_snapshots     -- Weekly form tracking for EWMA calculations
```

**Key Features:**
- Captures raw imported data (prices, FPts, xG stats, odds) without calculations
- Enables "apples-to-apples" analysis by applying formulas retroactively
- Supports home/away context and opponent data for comprehensive trend analysis

**📋 TESTING REQUIREMENTS:**
- Test trend analysis endpoints with historical gameweek data
- Verify raw data capture during weekly imports (Fantrax, Understat, odds)
- Confirm V2.0 parameter consistency across trend calculations

## Tools and Automation

### Documentation Validation Commands
```bash
# Check for broken internal links (if tool available)
find docs/ -name "*.md" -exec grep -l "docs/" {} \;

# Verify all files have updated timestamps
grep -r "Last updated" docs/

# Check for consistent status indicators
grep -r "Complete\|Pending\|Deferred" docs/
```

### Suggested Automation
- Git pre-commit hooks to validate documentation formatting
- Automated cross-reference checking
- Date stamp validation for modified files

---

**This maintenance guide ensures comprehensive, accurate, and up-to-date documentation throughout the Formula Optimization project lifecycle.**

## 🎯 POST-V2.0 CONSOLIDATION MANDATORY UPDATES (2025-08-23)

### **Every Documentation Update Must Now Include:**

1. **V2.0 Enhanced System** - All features are V2.0 Enhanced Formula only
2. **Parameter Structure** - `formula_optimization_v2` parameter format documentation
3. **Database Columns** - V2.0 columns (`true_value`, `roi`) and raw snapshot tables
4. **Gameweek Handling** - Verify proper database-driven gameweek detection
5. **Historical Data** - Document historical PPG calculation and raw data capture

### **Critical Files Requiring V2.0 Enhanced Documentation:**

**High Priority:**
- `DATABASE_SCHEMA.md` - V2.0 column usage, raw snapshot system, gameweek detection patterns
- `API_REFERENCE.md` - V2.0 Enhanced endpoints, trend analysis endpoints, historical_ppg requirements  
- `DEVELOPMENT_SETUP.md` - V2.0 testing procedures, raw data snapshot validation
- `FEATURE_GUIDE.md` - V2.0 Enhanced dashboard features, trend analysis system

**Medium Priority:**
- `FORMULA_REFERENCE.md` - V2.0 Enhanced Formula calculations only
- `TESTING_METHODOLOGY.md` - V2.0 Enhanced validation procedures, trend analysis testing

### **New Documentation Standards (Post-2025-08-23):**

**System References:**
- Always specify "V2.0 Enhanced" when discussing the calculation system
- Reference "raw data snapshot system" for trend analysis features

**Code Examples:**
- Include V2.0 Enhanced Formula examples only
- Show correct gameweek detection pattern in any time-based functionality
- Include historical_ppg calculation in player data queries
- Document raw data capture patterns for new import functionality

**Cross-References:**
- Link to CLAUDE.md V2.0-only architecture from technical documents
- Reference raw snapshot table structures for trend analysis features

---

*Last updated: 2025-08-23 - Major update: Consolidated to V2.0-only system, added raw data snapshot system for trend analysis*