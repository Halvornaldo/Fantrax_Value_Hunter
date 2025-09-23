# Deprecated Scripts Archive

These scripts have been archived due to issues discovered during September 2025 file editing troubleshooting session.

## Issues with Archived Scripts:
- `start_dashboard_fixed.bat` - Had WERKZEUG_RUN_MAIN KeyError issue
- `start_dev_no_reload_fixed.bat` - Had WERKZEUG_RUN_MAIN KeyError issue

## Current Working Scripts (in root directory):
- `start_dashboard_safe.bat` - RECOMMENDED: Safe startup preventing file lock issues
- `start_dashboard_corrected.bat` - Alternative working version
- `start_dev_no_reload_corrected.bat` - Backend only without auto-reload
- `emergency_recovery.bat` - For recovery situations

## Historical Context:
These scripts were created during file lock diagnosis but contained environment variable issues that caused Flask startup failures. The "corrected" and "safe" versions resolve these problems.

For current documentation, see CLAUDE.md in the root directory.