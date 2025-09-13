# Archive Directory

This directory contains historical files that were moved during project cleanup to improve maintainability and reduce clutter.

## Structure

### `setup_scripts/`
One-time utility scripts used during development and database setup:
- **Database setup**: `add_column.py`, `add_xgi_column.py`, `create_games_table.py`
- **Data import**: `import_*.py`, `convert_*.py` files
- **Verification**: `check_*.py`, `verify_*.py`, `debug_*.py` files  
- **Migrations**: `run_migration.py`, `run_v2_migration.py`
- **Validation**: `fantasy_validation*.py`, `validation_*.py`

### `old_docs/`
Obsolete documentation files:
- **Sprint documentation**: Sprint-specific planning docs (SPRINT4_*, SPRINT_6_*)
- **Unimplemented features**: Gemini AI integration plans (1700+ lines)
- **API integrations**: FBR API documentation (never implemented)
- **Completed migrations**: Gameweek unification plan
- **Historical planning**: Original PRD, PLAN.md files
- **Utility docs**: Database access, testing methodology, etc.

### `experimental/`
Research and testing code:
- **R scripts**: FBref integration testing using worldfootballr
- **API testing**: FBR API endpoint discovery and testing
- **Proof-of-concept**: Various integration approaches

## Why Archived

These files were archived to:
1. **Reduce documentation from 10,000+ lines to ~1,500 lines**
2. **Remove 20+ one-time utility scripts from root directory**
3. **Focus on current V2.0 system** (removed legacy references)
4. **Improve project navigation** and maintainability

All functionality remains available - these are just moved for organization.

## Access

Files can still be accessed if needed:
```bash
# Run archived setup scripts
python archive/setup_scripts/check_db_structure.py

# Reference old documentation
cat archive/old_docs/GEMINI_INTEGRATION_PLAN.md
```

*Archived: September 2025 - Project cleanup initiative*