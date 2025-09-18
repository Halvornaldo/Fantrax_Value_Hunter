#!/usr/bin/env python3
"""
Simple script to identify missing Understat mappings
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

def load_all_understat_players():
    """Load all Understat players from GW1-4"""
    all_players = set()

    for gameweek in [1, 2, 3, 4]:
        filename = f'gw{gameweek}_players_found.json'

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                players = json.load(f)
                all_players.update(players)
                print(f"GW{gameweek}: {len(players)} players")

    return all_players

def get_existing_mappings(conn):
    """Get all existing Understat mappings"""
    query = """
    SELECT source_name, fantrax_id, verified, confidence_score
    FROM name_mappings
    WHERE source_system = 'understat'
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

    return {row['source_name']: row for row in results}

def main():
    print("="*60)
    print("MISSING UNDERSTAT MAPPINGS ANALYSIS")
    print("="*60)

    # Load players
    all_players = load_all_understat_players()
    print(f"Total unique players: {len(all_players)}")

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        mappings = get_existing_mappings(conn)

        verified_count = sum(1 for m in mappings.values() if m['verified'])
        unverified_count = len(mappings) - verified_count

        print(f"Existing mappings: {len(mappings)}")
        print(f"  Verified: {verified_count}")
        print(f"  Unverified: {unverified_count}")

        # Find unmapped
        unmapped = []
        for player in all_players:
            if player not in mappings:
                unmapped.append(player)

        # Find unverified
        unverified = []
        for player in all_players:
            if player in mappings and not mappings[player]['verified']:
                unverified.append({
                    'name': player,
                    'fantrax_id': mappings[player]['fantrax_id'],
                    'confidence': mappings[player]['confidence_score']
                })

        print(f"\nUNMAPPED PLAYERS: {len(unmapped)}")
        for i, player in enumerate(unmapped):
            print(f"  {i+1}. {player}")

        print(f"\nUNVERIFIED MAPPINGS: {len(unverified)}")
        unverified.sort(key=lambda x: x['confidence'], reverse=True)
        for i, item in enumerate(unverified):
            print(f"  {i+1}. {item['name']} -> {item['fantrax_id']} (conf: {item['confidence']:.1f})")

        # Summary
        total_complete = len(all_players) - len(unmapped)
        completion_rate = (total_complete / len(all_players)) * 100

        print(f"\nSUMMARY:")
        print(f"Total players: {len(all_players)}")
        print(f"Mapped: {total_complete}")
        print(f"Unmapped: {len(unmapped)}")
        print(f"Completion rate: {completion_rate:.1f}%")

        if len(unmapped) == 0:
            print("\nSUCCESS: All players have mappings!")
            if len(unverified) > 0:
                print(f"Next step: Verify {len(unverified)} unverified mappings")
            else:
                print("PERFECT: 100% mapped and verified!")
        else:
            print(f"\nTODO: Map remaining {len(unmapped)} players")

    finally:
        conn.close()

if __name__ == "__main__":
    main()