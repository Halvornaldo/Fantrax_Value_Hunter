#!/usr/bin/env python3
"""
Fix the table alias error in /api/players endpoint
Changes players.games_current_season to p.games_current_season
"""

import os
import shutil
from datetime import datetime

# File paths
app_file = "src/app.py"
backup_file = f"src/app.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print("Fixing table alias error in /api/players endpoint...")

# Create backup
print(f"Creating backup: {backup_file}")
shutil.copy2(app_file, backup_file)

# Read the file
with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the problematic code exists
if "COALESCE(players.games_current_season, 0)" in content:
    print("Found problematic table alias")

    # Make the replacement
    new_content = content.replace(
        "COALESCE(players.games_current_season, 0)",
        "COALESCE(p.games_current_season, 0)"
    )

    # Write the fixed content
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Fixed table alias error!")
    print("Changed: players.games_current_season -> p.games_current_season")
    print(f"Backup saved as: {backup_file}")
    print("")
    print("Now restart your Flask backend and the players table should load!")

else:
    print("Could not find the problematic table alias")
    print("The file may have already been fixed")
    os.remove(backup_file)  # Remove unnecessary backup