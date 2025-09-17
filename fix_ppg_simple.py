#!/usr/bin/env python3
"""
Simple script to fix PPG calculation error in app.py
Replaces pgd.games_played with p.games_current_season in PPG calculations only
"""

import subprocess
import time
import os

def main():
    app_file = "C:/Users/halvo/.claude/Fantrax_Value_Hunter/src/app.py"

    print("PPG Calculation Fix Script")
    print("=" * 30)

    # Kill Python processes
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                      capture_output=True, text=True)
        print("Stopped Python processes")
        time.sleep(2)
    except:
        pass

    # Read file
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create backup
    backup_file = app_file + ".backup"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup: {backup_file}")

    # Apply fixes
    original_content = content

    # Fix 1: Sort field definition
    content = content.replace(
        "'ppg': 'CASE WHEN COALESCE(pgd.games_played, 0) > 0 THEN COALESCE(pf.total_points, 0) / pgd.games_played ELSE 0 END'",
        "'ppg': 'CASE WHEN COALESCE(p.games_current_season, 0) > 0 THEN COALESCE(pf.total_points, 0) / p.games_current_season ELSE 0 END'"
    )

    # Fix 2: Main PPG calculations
    content = content.replace(
        "THEN COALESCE(pf.total_points, 0) / pgd.games_played",
        "THEN COALESCE(pf.total_points, 0) / p.games_current_season"
    )

    # Fix 3: PPG calculations with pf_max
    content = content.replace(
        "THEN COALESCE(pf_max.total_points, 0) / pgd.games_played",
        "THEN COALESCE(pf_max.total_points, 0) / p.games_current_season"
    )

    # Fix 4: NULLIF expressions
    content = content.replace(
        "COALESCE(pf.total_points / NULLIF(pgd.games_played, 0), 0)",
        "COALESCE(pf.total_points / NULLIF(p.games_current_season, 0), 0)"
    )

    # Fix 5: Condition checks for PPG
    content = content.replace(
        "WHEN COALESCE(pgd.games_played, 0) > 0",
        "WHEN COALESCE(p.games_current_season, 0) > 0"
    )

    # Write file back
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)

    if content != original_content:
        print("Applied PPG calculation fixes!")
        print("Changes made:")
        print("- Fixed sort field definition")
        print("- Fixed main PPG calculations")
        print("- Fixed conditional checks")
        print("- Fixed NULLIF expressions")
        print("\nNext steps:")
        print("1. python src/app.py")
        print("2. Test API: curl http://localhost:5001/api/players?limit=3")
    else:
        print("No changes needed")

if __name__ == "__main__":
    main()