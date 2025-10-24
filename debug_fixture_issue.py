#!/usr/bin/env python3
"""
Debug script to check fixture multiplier calculations
"""

import sys
sys.path.append('src')
sys.path.append('.')

import psycopg2
import psycopg2.extras
from src.npxg_fixture_multiplier import get_npxg_multiplier_for_player
import json

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

print("=" * 70)
print("FIXTURE MULTIPLIER DEBUG")
print("=" * 70)

# Load current parameters
with open('config/system_parameters.json', 'r') as f:
    params = json.load(f)

slider_value = params['formula_optimization_v2']['exponential_fixture']['base']
print(f"\nCurrent slider value: {slider_value}")

# Calculate NPxG weight
middle = 1.325
if slider_value <= middle:
    npxg_weight = 0.80 + (slider_value - 1.15) / (middle - 1.15) * 0.20
else:
    npxg_weight = 1.00 + (slider_value - middle) / (1.50 - middle) * 0.20

print(f"Calculated NPxG weight: {npxg_weight:.3f}")

# Connect to database
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Check Man City players
print("\n" + "-" * 70)
print("MAN CITY PLAYERS vs EVERTON:")
print("-" * 70)

cursor.execute("""
    SELECT
        p.id, p.name, p.position, p.team,
        pm.next_opponent, pm.is_home, pm.fixture_multiplier as stored_mult
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE p.team = 'MCI'
    AND p.name IN ('Erling Haaland', 'Phil Foden', 'Kevin De Bruyne', 'Jack Grealish')
    ORDER BY p.name
""")

players = cursor.fetchall()

for player in players:
    # Create player_data dict for calculation
    player_data = {
        'position': player['position'],
        'next_opponent': player['next_opponent'],
        'is_home': player['is_home']
    }

    # Calculate new multiplier
    calculated_mult = get_npxg_multiplier_for_player(player_data, DB_CONFIG, npxg_weight)

    # Display comparison
    location = "HOME" if player['is_home'] else "AWAY"
    stored = float(player['stored_mult']) if player['stored_mult'] else 0.0

    print(f"\n{player['name']:20} ({player['position']})")
    print(f"  Opponent: {player['next_opponent']} ({location})")
    print(f"  Stored in DB: {stored:.3f}")
    print(f"  Calculated fresh: {calculated_mult:.3f}")

    if abs(stored - calculated_mult) > 0.001:
        print(f"  >>> MISMATCH! Difference: {calculated_mult - stored:+.3f}")

# Check team metrics
print("\n" + "-" * 70)
print("TEAM METRICS CHECK:")
print("-" * 70)

cursor.execute("""
    SELECT team_code, team_name, npxg, npxga
    FROM team_metrics
    WHERE team_code IN ('MCI', 'EVE', 'AVG')
    ORDER BY team_code
""")

for team in cursor.fetchall():
    print(f"{team['team_code']:3} - {team['team_name']:20} NPxG: {team['npxg']:6.2f}, NPxGA: {team['npxga']:6.2f}")

# Check if is_home flag is correct
print("\n" + "-" * 70)
print("HOME/AWAY FLAG VERIFICATION:")
print("-" * 70)

cursor.execute("""
    SELECT COUNT(*) as count, is_home
    FROM player_metrics pm
    JOIN players p ON p.id = pm.player_id
    WHERE p.team = 'MCI' AND pm.next_opponent = 'EVE'
    GROUP BY is_home
""")

for row in cursor.fetchall():
    status = "HOME" if row['is_home'] else "AWAY"
    print(f"  Man City players marked as {status}: {row['count']}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)