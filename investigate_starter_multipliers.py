#!/usr/bin/env python3
"""
Investigate Starter Multiplier Coverage
Find out why only 598/714 players have non-default starter multipliers
"""

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("STARTER MULTIPLIER INVESTIGATION")
print("=" * 50)

# 1. Get total counts
cursor.execute("SELECT COUNT(*) as total FROM players")
total_players = cursor.fetchone()['total']

cursor.execute("SELECT COUNT(*) as count FROM player_metrics WHERE starter_multiplier != 1.0")
non_default_count = cursor.fetchone()['count']

cursor.execute("SELECT COUNT(*) as count FROM player_metrics WHERE starter_multiplier = 1.0")
default_count = cursor.fetchone()['count']

cursor.execute("SELECT COUNT(*) as count FROM player_metrics WHERE starter_multiplier IS NULL")
null_count = cursor.fetchone()['count']

print(f"Total players: {total_players}")
print(f"Players with non-default (!=1.0): {non_default_count}")
print(f"Players with default (=1.0): {default_count}")
print(f"Players with NULL: {null_count}")
print(f"Total in player_metrics: {non_default_count + default_count + null_count}")

# 2. Check distribution of starter multipliers
print("\nStarter Multiplier Distribution:")
cursor.execute("""
    SELECT starter_multiplier, COUNT(*) as count
    FROM player_metrics
    GROUP BY starter_multiplier
    ORDER BY starter_multiplier DESC
""")

for row in cursor.fetchall():
    mult = row['starter_multiplier']
    count = row['count']
    if mult is None:
        print(f"  NULL: {count} players")
    else:
        # Map to category
        if mult == 1.0:
            category = "Definite Starter"
        elif mult == 0.9:
            category = "Likely Starter"
        elif mult == 0.75:
            category = "Rotation Risk"
        elif mult == 0.5:
            category = "Unlikely Starter"
        elif mult == 0.35:
            category = "Bench"
        elif mult == 0.0:
            category = "Out"
        else:
            category = "Unknown"
        print(f"  {mult}x ({category}): {count} players")

# 3. Find players without starter data (=1.0)
print("\nPlayers with DEFAULT (1.0) multiplier:")
cursor.execute("""
    SELECT p.id, p.name, p.team, p.position, pm.starter_multiplier
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.starter_multiplier = 1.0
    ORDER BY p.team, p.position, p.name
    LIMIT 20
""")

default_players = cursor.fetchall()
for player in default_players:
    print(f"  {player['name']:25} {player['team']:3} {player['position']:3}")

print(f"  ... and {default_count - 20} more")

# 4. Check for players not in player_metrics at all
print("\nChecking for missing player_metrics entries:")
cursor.execute("""
    SELECT p.id, p.name, p.team, p.position
    FROM players p
    LEFT JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.player_id IS NULL
""")

missing_metrics = cursor.fetchall()
if missing_metrics:
    print(f"Found {len(missing_metrics)} players without player_metrics entries:")
    for player in missing_metrics[:10]:
        print(f"  {player['name']:25} {player['team']:3} {player['position']:3}")
else:
    print("All players have player_metrics entries")

# 5. Check teams with most default multipliers
print("\nTeams with most DEFAULT (1.0) multipliers:")
cursor.execute("""
    SELECT p.team, COUNT(*) as count
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.starter_multiplier = 1.0
    GROUP BY p.team
    ORDER BY count DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"  {row['team']}: {row['count']} players")

# 6. Check positions with most default multipliers
print("\nPositions with DEFAULT (1.0) multipliers:")
cursor.execute("""
    SELECT p.position, COUNT(*) as count
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.starter_multiplier = 1.0
    GROUP BY p.position
    ORDER BY count DESC
""")

for row in cursor.fetchall():
    print(f"  {row['position']}: {row['count']} players")

# 7. Check if these are low-value players
print("\nPrice distribution of DEFAULT (1.0) multiplier players:")
cursor.execute("""
    SELECT
        CASE
            WHEN pm.price < 5 THEN 'Under 5.0'
            WHEN pm.price < 7.5 THEN '5.0-7.5'
            WHEN pm.price < 10 THEN '7.5-10.0'
            WHEN pm.price < 15 THEN '10.0-15.0'
            ELSE 'Over 15.0'
        END as price_range,
        COUNT(*) as count
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.starter_multiplier = 1.0
    GROUP BY price_range
    ORDER BY price_range
""")

for row in cursor.fetchall():
    print(f"  {row['price_range']}: {row['count']} players")

# 8. Sample high-value players with default multiplier
print("\nHigh-value players with DEFAULT (1.0) multiplier:")
cursor.execute("""
    SELECT p.name, p.team, p.position, pm.price, pm.true_value
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.starter_multiplier = 1.0
    ORDER BY pm.price DESC
    LIMIT 10
""")

for player in cursor.fetchall():
    print(f"  {player['name']:25} {player['team']:3} {player['position']:3} Price: {player['price']:.1f}")

conn.close()
print("\nInvestigation complete!")