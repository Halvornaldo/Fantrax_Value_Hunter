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

### Sprint 4: Dashboard Integration (v2.0 UI) ✅ COMPLETED (2025-08-22)
**Priority Updates:**
- `FEATURE_GUIDE.md` - Major update with new v2.0 dashboard features
- `API_REFERENCE.md` - Update player endpoints with v2.0 response format
- `DEVELOPMENT_SETUP.md` - Update testing procedures for new UI

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

*Last updated: 2025-08-21 - Created after Sprint 1 completion*