#!/usr/bin/env python3
"""
Re-import the corrected full CSV files for GW1-4 and re-run validation
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

# CSV file paths
CSV_FILES = {
    1: "c:/Users/halvo/Downloads/Fantrax G1 Full.csv",
    2: "c:/Users/halvo/Downloads/Fantrax G2 Full.csv",
    3: "c:/Users/halvo/Downloads/Fantrax G3 Full.csv",
    4: "c:/Users/halvo/Downloads/Fantrax G4 Full.csv"
}

def clear_existing_data(conn):
    """Clear existing game scores for GW1-4"""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM player_game_scores WHERE game_number IN (1,2,3,4)")
        deleted_count = cur.rowcount
        conn.commit()
        print(f"Cleared {deleted_count} existing game score records")

def import_csv_file(conn, gameweek: int, csv_path: str) -> dict:
    """Import a single CSV file"""
    print(f"\nImporting {csv_path}...")

    if not os.path.exists(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        return {'imported': 0, 'errors': ['File not found']}

    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"  CSV loaded: {len(df)} players")

        imported_count = 0
        errors = []

        with conn.cursor() as cur:
            for _, row in df.iterrows():
                try:
                    # Extract player ID (remove asterisk if present)
                    player_id = str(row['ID']).strip('*')
                    points = float(row['FPts'])
                    opponent = row.get('Opp', 'Unknown')

                    # Insert game score
                    cur.execute("""
                        INSERT INTO player_game_scores
                        (player_id, game_number, points_scored, opponent, import_timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (player_id, gameweek, points, opponent, datetime.now()))

                    imported_count += 1

                except Exception as e:
                    errors.append(f"Row error: {e}")

        conn.commit()
        print(f"  Successfully imported: {imported_count} players")

        if errors:
            print(f"  Errors: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                print(f"    {error}")

        return {'imported': imported_count, 'errors': errors}

    except Exception as e:
        print(f"  ERROR importing {csv_path}: {e}")
        return {'imported': 0, 'errors': [str(e)]}

def validate_gameweek_full(conn, gameweek: int) -> dict:
    """Re-validate gameweek with full dataset"""

    # Load Understat players
    filename = f'gw{gameweek}_players_found.json'
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found")
        return {}

    with open(filename, 'r') as f:
        understat_players = set(json.load(f))

    # Get verified mappings
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT source_name, fantrax_id
            FROM name_mappings
            WHERE source_system = 'understat' AND verified = true
        """)
        mappings = {row['source_name']: row['fantrax_id'] for row in cur.fetchall()}

    # Get players who played according to Understat
    played_fantrax_ids = set()
    for understat_name in understat_players:
        if understat_name in mappings:
            played_fantrax_ids.add(mappings[understat_name])

    # Get game scores for this gameweek
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, player_id, points_scored
            FROM player_game_scores
            WHERE game_number = %s
        """, (gameweek,))
        game_scores = cur.fetchall()

    # Analyze and update
    stats = {
        'understat_players': len(understat_players),
        'mapped_players': len(played_fantrax_ids),
        'total_scores': len(game_scores),
        'players_who_played': 0,
        'zero_scores_who_played': 0,
        'zero_scores_who_didnt_play': 0,
        'non_zero_scores': 0
    }

    updates = []

    for score_record in game_scores:
        player_id = score_record['player_id']
        score = float(score_record['points_scored'])
        record_id = score_record['id']

        did_play = player_id in played_fantrax_ids

        if score != 0:
            did_play = True
            stats['non_zero_scores'] += 1

        if did_play:
            stats['players_who_played'] += 1
            if score == 0:
                stats['zero_scores_who_played'] += 1
        else:
            if score == 0:
                stats['zero_scores_who_didnt_play'] += 1

        updates.append((did_play, record_id))

    # Update did_play column
    with conn.cursor() as cur:
        cur.executemany("""
            UPDATE player_game_scores
            SET did_play = %s
            WHERE id = %s
        """, updates)
        conn.commit()

    return stats

def main():
    print("="*80)
    print("RE-IMPORTING FULL GAME SCORES AND RE-VALIDATING")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Step 1: Clear existing data
        print("\nStep 1: Clearing existing game scores...")
        clear_existing_data(conn)

        # Step 2: Import all CSV files
        print("\nStep 2: Importing corrected CSV files...")
        import_results = {}

        for gameweek, csv_path in CSV_FILES.items():
            result = import_csv_file(conn, gameweek, csv_path)
            import_results[gameweek] = result

        # Step 3: Re-validate all gameweeks
        print("\nStep 3: Re-validating with complete data...")
        validation_results = {}

        for gameweek in [1, 2, 3, 4]:
            print(f"\nValidating Gameweek {gameweek}:")
            stats = validate_gameweek_full(conn, gameweek)
            validation_results[gameweek] = stats

            if stats:
                print(f"  Understat players: {stats['understat_players']}")
                print(f"  Mapped to Fantrax: {stats['mapped_players']}")
                print(f"  Game scores imported: {stats['total_scores']}")
                print(f"  Players who played: {stats['players_who_played']}")
                print(f"  Zero scores who played: {stats['zero_scores_who_played']} (keep)")
                print(f"  Zero scores who didn't play: {stats['zero_scores_who_didnt_play']} (exclude)")
                print(f"  Match rate: {stats['players_who_played']/stats['understat_players']*100:.1f}%")

        # Step 4: Summary
        print(f"\n{'='*80}")
        print("RE-IMPORT AND RE-VALIDATION COMPLETE")
        print("="*80)

        total_imported = sum(r['imported'] for r in import_results.values())
        total_understat = sum(s.get('understat_players', 0) for s in validation_results.values())
        total_matched = sum(s.get('players_who_played', 0) for s in validation_results.values())
        total_excluded = sum(s.get('zero_scores_who_didnt_play', 0) for s in validation_results.values())
        total_validated_zeros = sum(s.get('zero_scores_who_played', 0) for s in validation_results.values())

        print(f"Total game scores imported: {total_imported:,}")
        print(f"Total Understat players (GW1-4): {total_understat}")
        print(f"Total players who actually played: {total_matched}")
        print(f"Total false zero-scores excluded: {total_excluded:,}")
        print(f"Total legitimate zero-scores preserved: {total_validated_zeros}")

        if total_understat > 0:
            overall_match_rate = (total_matched / total_understat) * 100
            print(f"Overall match rate: {overall_match_rate:.1f}%")

        print(f"\nData quality improvement: {total_excluded:,} false entries removed!")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()