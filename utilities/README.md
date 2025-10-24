# Utilities Directory

This directory contains utility scripts for maintaining and fixing various aspects of the Fantrax Value Hunter system.

## Available Utilities

### fix_fixture_multipliers.py
**Purpose**: Fixes NPxG fixture multipliers when home/away adjustments are not being applied correctly.

**Problem it solves**: The NPxG calculation was ignoring the `is_home` flag from the database and treating all games as away games, resulting in home teams getting penalties instead of boosts.

**When to use**:
- When home teams are showing multipliers < 1.0
- When away teams are showing multipliers > 1.0
- After updating NPxG team data if multipliers look incorrect
- If fixture difficulty seems inverted

**Usage**:
```bash
python utilities/fix_fixture_multipliers.py
```

The script will:
1. Ensure league average row exists in team_metrics
2. Show current status with example players
3. Ask for confirmation before applying fixes
4. Recalculate all player fixture multipliers
5. Display results and verification

**Expected output**:
- Home teams should average ~1.11 multiplier
- Away teams should average ~0.98 multiplier
- Man City at home vs Everton should show multipliers > 1.0

**After running**: Go to the dashboard and adjust any slider (e.g., Form Alpha) and click Apply to trigger a full True Value recalculation.

## Adding New Utilities

When adding new utility scripts:
1. Place them in this directory
2. Add clear documentation at the top of the file
3. Update this README with usage instructions
4. Include error handling and user confirmation for destructive operations
5. Provide clear output messages about what the utility is doing