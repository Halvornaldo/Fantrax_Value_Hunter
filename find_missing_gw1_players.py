#!/usr/bin/env python3
"""
Find the 9-player discrepancy in GW1: 299 Understat vs 290 matched
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def main():
    print("="*80)
    print("INVESTIGATING GW1 PLAYER DISCREPANCY")
    print("299 Understat players vs 290 matched to Fantrax")
    print("="*80)

    # Load GW1 Understat players
    with open('gw1_players_found.json', 'r') as f:
        understat_players = set(json.load(f))

    print(f"Understat GW1 players: {len(understat_players)}")

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Get all verified mappings
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT source_name, fantrax_id, fantrax_name
                FROM name_mappings
                WHERE source_system = 'understat'
                AND verified = true
            """)
            mappings = {row['source_name']: {'fantrax_id': row['fantrax_id'], 'fantrax_name': row['fantrax_name']} for row in cur.fetchall()}

        print(f"Verified mappings: {len(mappings)}")

        # Find which Understat players are mapped to Fantrax
        mapped_understat_players = set()
        mapped_fantrax_ids = set()

        for understat_name in understat_players:
            if understat_name in mappings:
                mapped_understat_players.add(understat_name)
                mapped_fantrax_ids.add(mappings[understat_name]['fantrax_id'])

        print(f"GW1 players mapped to Fantrax: {len(mapped_understat_players)}")
        print(f"Unique Fantrax IDs from GW1: {len(mapped_fantrax_ids)}")

        # Find the missing 9 players
        unmapped_understat = understat_players - mapped_understat_players
        print(f"\nUnmapped Understat players: {len(unmapped_understat)}")

        if unmapped_understat:
            print("Players in Understat GW1 but not mapped:")
            for i, player in enumerate(sorted(unmapped_understat), 1):
                print(f"  {i:2d}. {player}")

        # Check if the issue is with Fantrax players not having game scores
        print(f"\nChecking game scores for mapped players...")

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get game scores for GW1
            cur.execute("""
                SELECT DISTINCT player_id
                FROM player_game_scores
                WHERE game_number = 1
            """)
            players_with_gw1_scores = {row['player_id'] for row in cur.fetchall()}

        print(f"Players with GW1 game scores: {len(players_with_gw1_scores)}")

        # Find mapped players who don't have game scores
        mapped_fantrax_ids_without_scores = mapped_fantrax_ids - players_with_gw1_scores
        players_with_scores_but_mapped = mapped_fantrax_ids & players_with_gw1_scores

        print(f"Mapped GW1 players with game scores: {len(players_with_scores_but_mapped)}")
        print(f"Mapped GW1 players WITHOUT game scores: {len(mapped_fantrax_ids_without_scores)}")

        if mapped_fantrax_ids_without_scores:
            print("\nMapped players missing from game scores:")
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for fantrax_id in mapped_fantrax_ids_without_scores:
                    cur.execute("SELECT name, team, position FROM players WHERE id = %s", (fantrax_id,))
                    player = cur.fetchone()
                    if player:
                        print(f"  {fantrax_id} - {player['name']} ({player['team']}, {player['position']})")

        # Show the discrepancy analysis
        print(f"\n{'='*60}")
        print("DISCREPANCY ANALYSIS")
        print("="*60)
        print(f"Understat GW1 players: {len(understat_players)}")
        print(f"Successfully mapped: {len(mapped_understat_players)}")
        print(f"Unmapped Understat players: {len(unmapped_understat)}")
        print(f"Mapped players with GW1 scores: {len(players_with_scores_but_mapped)}")
        print(f"Mapped players missing GW1 scores: {len(mapped_fantrax_ids_without_scores)}")

        total_expected = len(players_with_scores_but_mapped)
        discrepancy = len(understat_players) - total_expected
        print(f"\nEffective discrepancy: {discrepancy}")

        if discrepancy == 9:
            print("✓ Found the 9-player discrepancy!")
            print("Issue: 9 Understat players either unmapped or mapped players without game scores")

        # Check if these are legitimate player absences
        print(f"\nPossible explanations:")
        print(f"1. {len(unmapped_understat)} unmapped players (need manual mapping)")
        print(f"2. {len(mapped_fantrax_ids_without_scores)} mapped players missing from Fantrax CSV")
        print(f"3. Name variations not caught by matching algorithm")
        print(f"4. Players who transferred/moved between systems")

    finally:
        conn.close()

if __name__ == "__main__":
    main()