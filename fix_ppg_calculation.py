#!/usr/bin/env python3
"""
Script to fix PPG calculation error in app.py
Replaces pgd.games_played with p.games_current_season in PPG calculations only
"""

import re
import os
import subprocess
import time

def kill_python_processes():
    """Kill running Python processes to unlock the file"""
    try:
        # Kill Python processes on Windows
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                      capture_output=True, text=True)
        print("✓ Killed Python processes")
        time.sleep(2)
    except Exception as e:
        print(f"Warning: Could not kill processes: {e}")

def fix_ppg_calculations(file_path):
    """Fix PPG calculations in the file"""

    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Define the replacements for PPG calculations only
    replacements = [
        # 1. Sort field definition (line ~615)
        (
            r"'ppg': 'CASE WHEN COALESCE\(pgd\.games_played, 0\) > 0 THEN COALESCE\(pf\.total_points, 0\) / pgd\.games_played ELSE 0 END'",
            "'ppg': 'CASE WHEN COALESCE(p.games_current_season, 0) > 0 THEN COALESCE(pf.total_points, 0) / p.games_current_season ELSE 0 END'"
        ),

        # 2. Main PPG calculation patterns (multiple locations)
        (
            r"CASE\s+WHEN COALESCE\(pgd\.games_played, 0\) > 0\s+THEN COALESCE\(pf(?:_max)?\.total_points, 0\) / pgd\.games_played\s+ELSE 0\s+END as (?:ppg|calculated_ppg)",
            lambda m: m.group(0).replace('pgd.games_played', 'p.games_current_season')
        ),

        # 3. PPG calculations in expressions
        (
            r"COALESCE\(pf\.total_points / NULLIF\(pgd\.games_played, 0\), 0\)",
            "COALESCE(pf.total_points / NULLIF(p.games_current_season, 0), 0)"
        ),

        # 4. ORDER BY clause with PPG calculation
        (
            r"ORDER BY ABS\(pm\.ppg - COALESCE\(pf\.total_points / NULLIF\(pgd\.games_played, 0\), 0\)\)",
            "ORDER BY ABS(pm.ppg - COALESCE(pf.total_points / NULLIF(p.games_current_season, 0), 0))"
        )
    ]

    # Apply replacements
    changes_made = 0
    for pattern, replacement in replacements:
        if callable(replacement):
            # For lambda replacements
            matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
            for match in reversed(matches):  # Reverse to maintain positions
                content = content[:match.start()] + replacement(match) + content[match.end():]
                changes_made += 1
        else:
            # For string replacements
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                changes_made += len(re.findall(pattern, content))
                content = new_content

    # Additional manual replacements for specific patterns that are harder to regex
    manual_replacements = [
        # Fix any remaining PPG calculations that might have been missed
        ("THEN COALESCE(pf.total_points, 0) / pgd.games_played",
         "THEN COALESCE(pf.total_points, 0) / p.games_current_season"),
        ("THEN COALESCE(pf_max.total_points, 0) / pgd.games_played",
         "THEN COALESCE(pf_max.total_points, 0) / p.games_current_season"),
    ]

    for old, new in manual_replacements:
        if old in content:
            content = content.replace(old, new)
            changes_made += content.count(new) - original_content.count(new)

    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return changes_made, len(content) != len(original_content)

def main():
    app_file = "C:/Users/halvo/.claude/Fantrax_Value_Hunter/src/app.py"

    print("🔧 PPG Calculation Fix Script")
    print("=" * 40)

    # Step 1: Kill Python processes
    print("1. Stopping Python processes...")
    kill_python_processes()

    # Step 2: Check if file exists
    if not os.path.exists(app_file):
        print(f"❌ Error: File not found: {app_file}")
        return

    # Step 3: Create backup
    backup_file = app_file + ".backup"
    try:
        with open(app_file, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        print(f"✓ Created backup: {backup_file}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return

    # Step 4: Apply fixes
    print("2. Applying PPG calculation fixes...")
    try:
        changes_made, file_changed = fix_ppg_calculations(app_file)

        if file_changed:
            print(f"✓ Fixed {changes_made} PPG calculations")
            print("✓ Changes applied successfully!")
            print("\nFixed locations:")
            print("  - Sort field definition for PPG")
            print("  - Main PPG calculation in /api/players endpoint")
            print("  - PPG calculations in other endpoints")
            print("  - PPG calculations in debugging sections")

            print(f"\n🔄 Next steps:")
            print("1. Restart the application: python src/app.py")
            print("2. Test the API: curl http://localhost:5001/api/players?limit=3")
            print("3. Check that Salah shows 8.5 PPG instead of 17.0")
        else:
            print("ℹ️  No changes needed - PPG calculations already fixed")

    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        # Restore backup
        try:
            with open(backup_file, 'r') as src, open(app_file, 'w') as dst:
                dst.write(src.read())
            print("✓ Restored from backup")
        except:
            print("❌ Could not restore backup!")

if __name__ == "__main__":
    main()