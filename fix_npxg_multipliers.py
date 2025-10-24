#!/usr/bin/env python3
"""
Fix NPxG Multipliers in Database
Updates the database with correctly calculated NPxG fixture multipliers
"""

import sys
import time
sys.path.append('src')
sys.path.append('.')

# Import the recalculation function
from src.app import recalculate_true_values
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def check_values(description):
    """Check current Man City multipliers"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT
            p.name, p.position,
            pm.fixture_multiplier, pm.true_value,
            pm.next_opponent, pm.is_home
        FROM player_metrics pm
        JOIN players p ON p.id = pm.player_id
        WHERE p.team = 'MCI'
        AND p.name IN ('Erling Haaland', 'Phil Foden', 'Jack Grealish')
        ORDER BY p.name
    """)

    print(f"\n{description}")
    print("-" * 70)
    print(f"{'Player':20} {'Pos':4} {'Fix Mult':10} {'True Val':10} {'Status':15}")
    print("-" * 70)

    for row in cursor.fetchall():
        status = "HOME" if row['is_home'] else "AWAY"
        correct = "OK" if row['fixture_multiplier'] > 1.0 else "WRONG"
        print(f"{row['name'][:20]:20} {row['position'][:4]:4} {row['fixture_multiplier']:10.3f} "
              f"{row['true_value']:10.2f} {status:8} {correct:7}")

    cursor.close()
    conn.close()

print("=" * 70)
print("FIXING NPxG FIXTURE MULTIPLIERS")
print("=" * 70)
print("\nThis will recalculate all player values with the fixed NPxG logic")

# Check before
check_values("BEFORE RECALCULATION")

# Run recalculation
print("\n>> Running recalculation...")
start_time = time.time()

try:
    result = recalculate_true_values()
    elapsed = time.time() - start_time

    if result.get('success'):
        print(f"SUCCESS! Updated {result.get('updated_count')} players in {elapsed:.2f}s")
    else:
        print(f"FAILED: {result.get('error', 'Unknown error')}")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Check after
check_values("AFTER RECALCULATION")

print("\n" + "=" * 70)
print("NPxG fixture multipliers should now be correct!")
print("   Home teams get boosts (>1.0), away teams get penalties (<1.0)")