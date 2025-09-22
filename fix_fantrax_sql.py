#!/usr/bin/env python3
"""
Fix the SQL error in Fantrax upload at line 2660
The issue: References p.games_current_season but 'p' alias doesn't exist
Solution: Properly join the players table to access games_current_season
"""

import os
import shutil
from datetime import datetime

# File paths
app_file = "src/app.py"
backup_file = f"src/app.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print("Fixing SQL error in Fantrax upload at line 2660...")

# Create backup
print(f"Creating backup: {backup_file}")
shutil.copy2(app_file, backup_file)

# Read the file
with open(app_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the problematic query (lines 2655-2679)
# We need to fix the subquery to properly access the players table
if len(lines) > 2679:
    # Build the new fixed query
    new_query_lines = [
        '        cursor.execute("""\n',
        '            UPDATE player_metrics pm\n',
        '            SET ppg = (\n',
        '                SELECT \n',
        '                    CASE \n',
        '                        WHEN COALESCE(players.games_current_season, 0) > 0 \n',
        '                        THEN COALESCE(pf_max.total_points, 0) / players.games_current_season\n',
        '                        ELSE 0 \n',
        '                    END\n',
        '                FROM players\n',
        '                LEFT JOIN (\n',
        '                    SELECT player_id, MAX(points) as total_points\n',
        '                    FROM player_form\n',
        '                    WHERE player_id = pm.player_id\n',
        '                    GROUP BY player_id\n',
        '                ) pf_max ON players.id = pf_max.player_id\n',
        '                WHERE players.id = pm.player_id\n',
        '                LIMIT 1\n',
        '            )\n',
        '            WHERE pm.gameweek = %s\n',
        '        """, [gameweek])\n'
    ]

    # Replace lines 2655-2679 (0-indexed: 2654-2678)
    lines[2654:2679] = new_query_lines

    # Write the fixed content
    with open(app_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("Fixed SQL error!")
    print("Key changes:")
    print("  1. Added proper FROM players clause")
    print("  2. Changed p.games_current_season to players.games_current_season")
    print("  3. Removed unnecessary pgd subquery (we get games from players table)")
    print("  4. Use players.games_current_season directly for division")
    print(f"Backup saved as: {backup_file}")
    print("")
    print("The Fantrax upload should now work correctly!")
    print("Note: The backend should auto-reload due to file changes.")
else:
    print("Error: File structure seems different than expected")
    print("Manual intervention may be required")
    os.remove(backup_file)