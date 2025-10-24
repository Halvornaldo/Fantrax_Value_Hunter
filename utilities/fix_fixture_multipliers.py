#!/usr/bin/env python3
"""
Fixture Multiplier Fix Utility
===============================
Fixes NPxG fixture multipliers to correctly apply home/away adjustments.

Problem: NPxG calculations were ignoring the is_home flag and treating all games as away.
Solution: This script recalculates all fixture multipliers using the correct home/away logic.

Usage: python utilities/fix_fixture_multipliers.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import psycopg2
import psycopg2.extras
from src.npxg_fixture_multiplier import get_npxg_multiplier_for_player
import json
import time
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def ensure_league_average():
    """Ensure the league average row exists in team_metrics"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("Ensuring league average row exists...")
    cursor.execute("""
        INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
        SELECT
            'AVG' as team_code,
            'League Average' as team_name,
            AVG(npxg) as npxg,
            AVG(npxga) as npxga,
            AVG(npxg) - AVG(npxga) as npxgd,
            20 as matches_played,
            NOW() as last_updated
        FROM team_metrics
        WHERE team_code != 'AVG' AND npxg IS NOT NULL
        ON CONFLICT (team_code) DO UPDATE SET
            npxg = EXCLUDED.npxg,
            npxga = EXCLUDED.npxga,
            npxgd = EXCLUDED.npxgd,
            last_updated = EXCLUDED.last_updated
    """)
    conn.commit()

    # Verify it was created
    cursor.execute("SELECT npxg, npxga FROM team_metrics WHERE team_code = 'AVG'")
    result = cursor.fetchone()
    if result:
        print(f"  League average: NPxG={result[0]:.2f}, NPxGA={result[1]:.2f}")

    cursor.close()
    conn.close()

def calculate_npxg_weight():
    """Calculate NPxG weight from slider value in parameters"""
    with open('config/system_parameters.json', 'r') as f:
        params = json.load(f)

    slider_value = params['formula_optimization_v2']['exponential_fixture']['base']
    middle = 1.325

    if slider_value <= middle:
        npxg_weight = 0.80 + (slider_value - 1.15) / (middle - 1.15) * 0.20
    else:
        npxg_weight = 1.00 + (slider_value - middle) / (1.50 - middle) * 0.20

    return slider_value, npxg_weight

def show_current_status():
    """Display current status of some example players"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Check Man City players as example
    cursor.execute("""
        SELECT
            p.name, p.position, p.team,
            pm.next_opponent, pm.is_home, pm.fixture_multiplier
        FROM player_metrics pm
        JOIN players p ON p.id = pm.player_id
        WHERE p.team = 'MCI' AND pm.next_opponent = 'EVE'
        LIMIT 5
    """)

    mci_players = cursor.fetchall()

    if mci_players:
        print("\nExample: Manchester City vs Everton")
        print("-" * 60)
        for player in mci_players:
            location = "HOME" if player['is_home'] else "AWAY"
            status = "OK" if (player['is_home'] and player['fixture_multiplier'] > 1.0) or \
                            (not player['is_home'] and player['fixture_multiplier'] < 1.0) else "WRONG"
            print(f"  {player['name'][:25]:25} {location:5} {player['fixture_multiplier']:6.3f} [{status}]")

    cursor.close()
    conn.close()

    return len([p for p in mci_players if p['is_home'] and p['fixture_multiplier'] < 1.0]) > 0

def fix_all_multipliers(npxg_weight):
    """Recalculate all fixture multipliers with correct logic"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get all players with opponents
    cursor.execute("""
        SELECT pm.player_id, p.position, pm.next_opponent, pm.is_home, pm.fixture_multiplier
        FROM player_metrics pm
        JOIN players p ON p.id = pm.player_id
        WHERE pm.next_opponent IS NOT NULL AND pm.next_opponent != ''
    """)

    players = cursor.fetchall()
    print(f"\nRecalculating {len(players)} player multipliers...")

    start_time = time.time()
    batch_updates = []
    fixes_applied = 0

    for player in players:
        player_data = {
            'position': player['position'],
            'next_opponent': player['next_opponent'],
            'is_home': player['is_home']
        }

        # Calculate correct multiplier
        new_mult = get_npxg_multiplier_for_player(player_data, DB_CONFIG, npxg_weight)
        old_mult = float(player['fixture_multiplier']) if player['fixture_multiplier'] else 0

        # Count fixes needed (home teams that were penalized)
        if player['is_home'] and old_mult < 1.0 and new_mult > 1.0:
            fixes_applied += 1

        batch_updates.append((new_mult, player['player_id']))

    # Apply updates
    cursor.executemany("""
        UPDATE player_metrics
        SET fixture_multiplier = %s
        WHERE player_id = %s
    """, batch_updates)

    conn.commit()
    elapsed = time.time() - start_time

    # Calculate averages
    cursor.execute("""
        SELECT
            AVG(CASE WHEN is_home = true THEN fixture_multiplier END) as home_avg,
            AVG(CASE WHEN is_home = false THEN fixture_multiplier END) as away_avg
        FROM player_metrics
        WHERE fixture_multiplier IS NOT NULL
    """)

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        'total_updated': len(players),
        'fixes_applied': fixes_applied,
        'elapsed': elapsed,
        'home_avg': result['home_avg'],
        'away_avg': result['away_avg']
    }

def main():
    """Main execution"""
    print("=" * 70)
    print("FIXTURE MULTIPLIER FIX UTILITY")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis utility fixes NPxG fixture multipliers to correctly apply")
    print("home/away adjustments based on the is_home database flag.\n")

    # Step 1: Ensure league average exists
    ensure_league_average()

    # Step 2: Calculate NPxG weight
    slider_value, npxg_weight = calculate_npxg_weight()
    print(f"\nNPxG Configuration:")
    print(f"  Slider value: {slider_value}")
    print(f"  NPxG weight: {npxg_weight:.3f}")

    # Step 3: Show current status
    needs_fix = show_current_status()

    if not needs_fix:
        print("\n[OK] Fixture multipliers appear to be correct!")
        return

    # Step 4: Apply fixes
    print("\n" + "=" * 70)
    response = input("Apply fixture multiplier fixes? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Step 5: Fix multipliers
    results = fix_all_multipliers(npxg_weight)

    # Step 6: Report results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total players updated: {results['total_updated']}")
    print(f"Home team fixes applied: {results['fixes_applied']}")
    print(f"Time elapsed: {results['elapsed']:.2f} seconds")
    print(f"\nNew averages:")
    print(f"  Home teams: {results['home_avg']:.3f} (should be >1.0)")
    print(f"  Away teams: {results['away_avg']:.3f} (should be <1.0)")

    # Step 7: Verify fix
    print("\nVerifying fix...")
    show_current_status()

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("Fixture multipliers have been corrected.")
    print("\nNext steps:")
    print("1. Go to the dashboard")
    print("2. Adjust any slider slightly (e.g., Form Alpha)")
    print("3. Click Apply to recalculate True Values")
    print("=" * 70)

if __name__ == "__main__":
    main()