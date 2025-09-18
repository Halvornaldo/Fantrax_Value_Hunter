#!/usr/bin/env python3
"""
Find the extra player(s) causing 100.3% match rate in each gameweek
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

def analyze_gameweek_discrepancy(conn, gameweek: int):
    """Find the extra player(s) in a specific gameweek"""

    # Load Understat players
    filename = f'gw{gameweek}_players_found.json'
    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found")
        return

    with open(filename, 'r') as f:
        understat_players = set(json.load(f))

    print(f"\nGameweek {gameweek} Analysis:")
    print(f"  Understat players: {len(understat_players)}")

    # Get verified mappings
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT source_name, fantrax_id
            FROM name_mappings
            WHERE source_system = 'understat' AND verified = true
        """)
        mappings = {row['source_name']: row['fantrax_id'] for row in cur.fetchall()}

    # Get Fantrax IDs of players who played according to Understat
    expected_fantrax_ids = set()
    for understat_name in understat_players:
        if understat_name in mappings:
            expected_fantrax_ids.add(mappings[understat_name])

    print(f"  Expected Fantrax players: {len(expected_fantrax_ids)}")

    # Get actual players marked as "played" in this gameweek
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT player_id, points_scored
            FROM player_game_scores
            WHERE game_number = %s AND did_play = true
        """, (gameweek,))
        actual_played = cur.fetchall()

    actual_fantrax_ids = {row['player_id'] for row in actual_played}
    print(f"  Actual players marked as played: {len(actual_fantrax_ids)}")

    # Find the discrepancy
    extra_players = actual_fantrax_ids - expected_fantrax_ids
    missing_players = expected_fantrax_ids - actual_fantrax_ids

    if extra_players:
        print(f"  Extra players ({len(extra_players)}):")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for player_id in extra_players:
                cur.execute("SELECT name, team, position FROM players WHERE id = %s", (player_id,))
                player = cur.fetchone()

                # Get their score in this gameweek
                cur.execute("SELECT points_scored FROM player_game_scores WHERE player_id = %s AND game_number = %s", (player_id, gameweek))
                score = cur.fetchone()

                if player and score:
                    print(f"    {player_id} - {player['name']} ({player['team']}, {player['position']}) - {score['points_scored']} pts")

                    # Check why they were marked as played
                    if score['points_scored'] != 0:
                        print(f"      REASON: Non-zero score ({score['points_scored']} pts) - automatically marked as played")
                    else:
                        print(f"      REASON: Zero score but marked as played - investigate mapping")

    if missing_players:
        print(f"  Missing players ({len(missing_players)}):")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for player_id in missing_players:
                cur.execute("SELECT name, team, position FROM players WHERE id = %s", (player_id,))
                player = cur.fetchone()

                # Check if they have a score for this gameweek
                cur.execute("SELECT points_scored, did_play FROM player_game_scores WHERE player_id = %s AND game_number = %s", (player_id, gameweek))
                score = cur.fetchone()

                if player:
                    if score:
                        print(f"    {player_id} - {player['name']} ({player['team']}, {player['position']}) - {score['points_scored']} pts (did_play: {score['did_play']})")
                    else:
                        print(f"    {player_id} - {player['name']} ({player['team']}, {player['position']}) - NO GAME SCORE")

def main():
    print("="*80)
    print("INVESTIGATING 100.3% MATCH RATE DISCREPANCY")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        for gameweek in [1, 2, 3, 4]:
            analyze_gameweek_discrepancy(conn, gameweek)

        # Summary analysis
        print(f"\n{'='*60}")
        print("SUMMARY ANALYSIS")
        print("="*60)

        # Check if the same player(s) appear as extra in all gameweeks
        extra_players_by_gw = {}

        for gameweek in [1, 2, 3, 4]:
            with open(f'gw{gameweek}_players_found.json', 'r') as f:
                understat_players = set(json.load(f))

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT source_name, fantrax_id
                    FROM name_mappings
                    WHERE source_system = 'understat' AND verified = true
                """)
                mappings = {row['source_name']: row['fantrax_id'] for row in cur.fetchall()}

            expected_fantrax_ids = set()
            for understat_name in understat_players:
                if understat_name in mappings:
                    expected_fantrax_ids.add(mappings[understat_name])

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT player_id
                    FROM player_game_scores
                    WHERE game_number = %s AND did_play = true
                """, (gameweek,))
                actual_fantrax_ids = {row['player_id'] for row in cur.fetchall()}

            extra_players_by_gw[gameweek] = actual_fantrax_ids - expected_fantrax_ids

        # Find common extra players
        if extra_players_by_gw:
            all_extra = set.intersection(*extra_players_by_gw.values()) if len(extra_players_by_gw) > 1 else extra_players_by_gw[1]

            if all_extra:
                print(f"Player(s) appearing as 'extra' in all gameweeks:")
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    for player_id in all_extra:
                        cur.execute("SELECT name, team, position FROM players WHERE id = %s", (player_id,))
                        player = cur.fetchone()
                        if player:
                            print(f"  {player_id} - {player['name']} ({player['team']}, {player['position']})")

    finally:
        conn.close()

if __name__ == "__main__":
    main()