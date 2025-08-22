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
- **`docs/FORMULA_OPTIMIZATION_SPRINTS.md`** - Mark sprints complete, update implementation results
- **`docs/FORMULA_REFERENCE.md`** - Update calculation formulas and mathematical examples
- **`docs/FORMULA_MIGRATION_GUIDE.md`** - Add new migration steps and rollback procedures

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

## 🚨 CRITICAL ARCHITECTURAL DISCOVERIES (2025-08-22)

### **Dual Engine System - MUST Document in All Relevant Files**

**⚠️ CRITICAL FOR LONG-TERM MAINTENANCE:**
The system now runs two completely separate calculation engines that developers MUST NOT mix:

**v1.0 Legacy Engine:**
- Location: `src/app.py` (main calculation logic)
- Parameters: `form_calculation.strength`, `fixture_difficulty.strength`
- Database: Writes to `value_score` column
- Formula: `(PPG ÷ Price) × multipliers`

**v2.0 Enhanced Engine:**
- Location: `calculation_engine_v2.py` (separate module)
- Parameters: `formula_optimization_v2.exponential_form.alpha`
- Database: Writes to `true_value` and `roi` columns
- Formula: `Blended_PPG × multipliers ÷ Price`

**📋 DOCUMENTATION REQUIREMENTS:**
- `API_REFERENCE.md` - Both engines must be clearly separated in endpoint documentation
- `DEVELOPMENT_SETUP.md` - Testing procedures must cover both engines
- `FEATURE_GUIDE.md` - UI toggle between engines must be explained
- `DATABASE_SCHEMA.md` - Column usage by engine must be documented

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
v2.0 Dynamic Blending requires historical PPG calculation in ALL player queries:

```sql
CASE 
    WHEN COALESCE(pgd.games_played_historical, 0) > 0 
    THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
    ELSE pm.ppg 
END as historical_ppg
```

**📋 AFFECTED ENDPOINTS:**
- `/api/players` - Main dashboard data
- `/api/calculate-values-v2` - v2.0 calculations
- Any new player data endpoints

### **Parameter Structure Conflicts - Document in DEVELOPMENT_SETUP.md**

**⚠️ JAVASCRIPT CONFLICTS DISCOVERED:**
The frontend parameter detection must handle both engines separately:

**v1.0 Parameters:**
```javascript
form_calculation: { strength: 0.5 }
fixture_difficulty: { strength: 0.8 }
```

**v2.0 Parameters:**
```javascript
formula_optimization_v2: {
  exponential_form: { alpha: 0.87 }
}
```

**📋 TESTING REQUIREMENTS:**
- Test parameter changes in both v1.0 Legacy and v2.0 Enhanced modes
- Verify Apply Changes button works correctly for each engine
- Confirm database updates go to correct columns (value_score vs true_value/roi)

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

## 🎯 POST-DUAL ENGINE MANDATORY UPDATES

### **Every Documentation Update Must Now Include:**

1. **Engine Specification** - Which engine(s) the feature/change affects
2. **Parameter Structure** - v1.0 vs v2.0 parameter format documentation
3. **Database Columns** - Which columns are read/written by each engine
4. **Gameweek Handling** - Verify proper database-driven gameweek detection
5. **Historical Data** - Document any historical PPG calculation requirements

### **Critical Files Requiring Dual Engine Documentation:**

**High Priority:**
- `DATABASE_SCHEMA.md` - Engine-specific column usage, gameweek detection patterns
- `API_REFERENCE.md` - Separate v1.0/v2.0 endpoints, historical_ppg requirements  
- `DEVELOPMENT_SETUP.md` - Dual engine testing procedures, parameter structure conflicts
- `FEATURE_GUIDE.md` - UI toggle behavior, engine-specific features

**Medium Priority:**
- `FORMULA_REFERENCE.md` - v1.0 vs v2.0 calculation differences
- `TESTING_METHODOLOGY.md` - Engine-specific validation procedures

### **New Documentation Standards (Post-2025-08-22):**

**Engine References:**
- Always specify "v1.0 Legacy" or "v2.0 Enhanced" when discussing features
- Never use ambiguous terms like "current system" without engine specification

**Code Examples:**
- Include both v1.0 and v2.0 examples where applicable
- Show correct gameweek detection pattern in any time-based functionality
- Include historical_ppg calculation in any player data queries

**Cross-References:**
- Link to CLAUDE.md dual engine warnings from technical documents
- Reference `v2.0-dynamic-blending-stable` git tag for safe reversion points

---

*Last updated: 2025-08-22 - Major update: Added critical architectural discoveries and dual engine documentation requirements*