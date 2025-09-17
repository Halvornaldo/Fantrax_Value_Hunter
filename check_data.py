#!/usr/bin/env python3
"""Quick data check for parameter validation"""

import psycopg2
import psycopg2.extras
import json

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("PARAMETER DATA CHECK")
print("=" * 30)

# Form data
cursor.execute("SELECT COUNT(*) as count FROM player_form WHERE points > 0")
form_count = cursor.fetchone()['count']
print(f"Form Data: {form_count} players")

# Fixture data
cursor.execute("SELECT COUNT(*) as count FROM team_fixtures WHERE difficulty_score IS NOT NULL")
fixture_count = cursor.fetchone()['count']
print(f"Fixture Data: {fixture_count} teams")

# xGI data
cursor.execute("SELECT COUNT(*) as count FROM players WHERE xgi90 > 0")
xgi_count = cursor.fetchone()['count']
cursor.execute("SELECT COUNT(*) as total FROM players")
total_count = cursor.fetchone()['total']
print(f"xGI Data: {xgi_count}/{total_count} players ({xgi_count/total_count*100:.0f}%)")

# Starter overrides
cursor.execute("SELECT COUNT(*) as count FROM player_metrics WHERE starter_multiplier != 1.0")
override_count = cursor.fetchone()['count']
print(f"Starter Overrides: {override_count} players")

# Parameter states
try:
    with open('config/system_parameters.json', 'r') as f:
        params = json.load(f)

    toggles = params.get('formula_optimization_v2', {}).get('formula_toggles', {})
    print(f"\nParameter States:")
    print(f"  Form: {'ON' if toggles.get('form_enabled', False) else 'OFF'}")
    print(f"  Fixture: {'ON' if toggles.get('fixture_enabled', True) else 'OFF'}")
    print(f"  Starter: {'ON' if toggles.get('starter_enabled', True) else 'OFF'}")
    print(f"  xGI: {'ON' if toggles.get('xgi_enabled', False) else 'OFF'}")
except Exception as e:
    print(f"Config error: {e}")

# Sample multipliers
print(f"\nSample Multipliers (Top 3 players):")
cursor.execute("""
    SELECT p.name, pm.form_multiplier, pm.fixture_multiplier,
           pm.starter_multiplier, pm.xgi_multiplier, pm.true_value
    FROM players p
    JOIN player_metrics pm ON p.id = pm.player_id
    WHERE pm.true_value > 0
    ORDER BY pm.true_value DESC
    LIMIT 3
""")

for player in cursor.fetchall():
    print(f"  {player['name']}: Form={player['form_multiplier']:.2f}x, Fixture={player['fixture_multiplier']:.2f}x, Starter={player['starter_multiplier']:.2f}x, xGI={player['xgi_multiplier']:.2f}x")

conn.close()
print("\nDone!")