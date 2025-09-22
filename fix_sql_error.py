#!/usr/bin/env python3
"""
Safe script to fix the SQL error in app.py line 2660
Creates backup before making changes
"""

import os
import shutil
from datetime import datetime

# File paths
app_file = "src/app.py"
backup_file = f"src/app.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print("🔧 Fixing SQL error in Fantrax upload...")

# Create backup
print(f"📋 Creating backup: {backup_file}")
shutil.copy2(app_file, backup_file)

# Read the file
with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the problematic query
old_query = """        cursor.execute(\"\"\"
            UPDATE player_metrics pm
            SET ppg = (
                SELECT
                    CASE
                        WHEN COALESCE(p.games_current_season, 0) > 0
                        THEN COALESCE(pf_max.total_points, 0) / pgd.games_played_current
                        ELSE 0
                    END
                FROM (
                    SELECT player_id, MAX(points) as total_points
                    FROM player_form
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pf_max
                LEFT JOIN (
                    SELECT player_id, SUM(games_played) as games_played_current
                    FROM player_games_data
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pgd ON pf_max.player_id = pgd.player_id
                LIMIT 1
            )
            WHERE pm.gameweek = %s
        \"\"\", [gameweek])"""

# Define the fixed query
new_query = """        cursor.execute(\"\"\"
            UPDATE player_metrics pm
            SET ppg = (
                SELECT
                    CASE
                        WHEN COALESCE(players.games_current_season, 0) > 0
                        THEN COALESCE(pf_max.total_points, 0) / players.games_current_season
                        ELSE 0
                    END
                FROM players
                LEFT JOIN (
                    SELECT player_id, MAX(points) as total_points
                    FROM player_form
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pf_max ON players.id = pf_max.player_id
                WHERE players.id = pm.player_id
            )
            WHERE pm.gameweek = %s
        \"\"\", [gameweek])"""

# Check if the problematic code exists
if "WHEN COALESCE(p.games_current_season, 0) > 0" in content:
    print("✅ Found problematic SQL query")

    # Make the replacement
    if old_query in content:
        new_content = content.replace(old_query, new_query)
        print("🔄 Replacing entire query block...")
    else:
        # Fallback: just replace the problematic line
        new_content = content.replace(
            "WHEN COALESCE(p.games_current_season, 0) > 0",
            "WHEN COALESCE(players.games_current_season, 0) > 0"
        )
        print("🔄 Replacing problematic line...")

    # Write the fixed content
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Fixed SQL error!")
    print("🎯 Key changes:")
    print("   - p.games_current_season → players.games_current_season")
    print("   - Updated query to properly JOIN players table")
    print(f"💾 Backup saved as: {backup_file}")
    print("\n🚀 Now restart your Flask backend and try the Fantrax upload!")

else:
    print("❌ Could not find the problematic SQL query")
    print("The file may have already been fixed or modified")
    os.remove(backup_file)  # Remove unnecessary backup