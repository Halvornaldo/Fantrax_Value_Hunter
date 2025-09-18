#!/usr/bin/env python3
"""
Investigate exactly why 10 players are missing from GW1 game scores
"""

import psycopg2
from psycopg2.extras import RealDictCursor

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
    print("INVESTIGATING MISSING GW1 PLAYERS")
    print("="*80)

    missing_players = [
        '05trb',  # Bryan Mbeumo
        '04io4',  # Richarlison
        '05g2o',  # Joao Pedro
        '068n8',  # Noni Madueke
        '02lm7',  # Jack Grealish
        '03dx3',  # Kieran Trippier
        '04mup',  # Trevoh Chalobah
        '04tsb',  # Viktor Gyokeres
        '068y0',  # Antoine Semenyo
        '05nzu'   # Gabriel Magalhaes
    ]

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for player_id in missing_players:
                print(f"\nPlayer {player_id}:")

                # Get player details
                cur.execute("SELECT name, team, position FROM players WHERE id = %s", (player_id,))
                player = cur.fetchone()

                if player:
                    print(f"  Name: {player['name']}")
                    print(f"  Team: {player['team']}")
                    print(f"  Position: {player['position']}")

                    # Check if they have ANY game scores
                    cur.execute("SELECT game_number, points_scored FROM player_game_scores WHERE player_id = %s ORDER BY game_number", (player_id,))
                    scores = cur.fetchall()

                    if scores:
                        print(f"  Game scores found: {len(scores)} games")
                        for score in scores:
                            print(f"    GW{score['game_number']}: {score['points_scored']} points")
                    else:
                        print("  NO GAME SCORES FOUND AT ALL")

                        # Check if they exist in players table with different criteria
                        cur.execute("SELECT COUNT(*) FROM players WHERE name ILIKE %s", (f"%{player['name'].split()[0]}%",))
                        similar_count = cur.fetchone()['count']
                        print(f"  Similar names in database: {similar_count}")

                else:
                    print(f"  ERROR: Player {player_id} not found in players table")

            # Check import timestamps to see when game scores were imported
            print(f"\n{'='*60}")
            print("GAME SCORES IMPORT ANALYSIS")
            print("="*60)

            cur.execute("""
                SELECT game_number,
                       MIN(import_timestamp) as earliest_import,
                       MAX(import_timestamp) as latest_import,
                       COUNT(DISTINCT player_id) as player_count,
                       COUNT(*) as total_scores
                FROM player_game_scores
                WHERE game_number IN (1,2,3,4)
                GROUP BY game_number
                ORDER BY game_number
            """)
            imports = cur.fetchall()

            for imp in imports:
                print(f"GW{imp['game_number']}:")
                print(f"  Players: {imp['player_count']}")
                print(f"  Total scores: {imp['total_scores']}")
                print(f"  Import window: {imp['earliest_import']} to {imp['latest_import']}")

            # Check when these specific players were added to the system
            print(f"\n{'='*60}")
            print("PLAYER ADDITION TIMELINE")
            print("="*60)

            for player_id in missing_players:
                cur.execute("SELECT name, updated_at FROM players WHERE id = %s", (player_id,))
                player = cur.fetchone()
                if player:
                    print(f"{player_id} ({player['name']}): Added {player['updated_at']}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()