#!/usr/bin/env python3
"""
PRODUCTION SCRIPT: Implement game scores validation using 100% verified Understat mappings
This will add the did_play column and update all game scores for GW1-4
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def load_understat_players(gameweek: int) -> set:
    """Load Understat players who played in a specific gameweek"""
    filename = f'gw{gameweek}_players_found.json'

    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found")
        return set()

    with open(filename, 'r') as f:
        players = json.load(f)

    return set(players)

def get_verified_mappings(conn) -> dict:
    """Get all verified Understat mappings"""
    query = """
    SELECT source_name, fantrax_id
    FROM name_mappings
    WHERE source_system = 'understat'
    AND verified = true
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

    return {row['source_name']: row['fantrax_id'] for row in results}

def add_did_play_column(conn):
    """Add did_play column to player_game_scores if it doesn't exist"""
    with conn.cursor() as cur:
        # Check if column exists
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='player_game_scores'
            AND column_name='did_play'
        """)

        if not cur.fetchone():
            print("Adding did_play column to player_game_scores...")
            cur.execute("""
                ALTER TABLE player_game_scores
                ADD COLUMN did_play BOOLEAN DEFAULT NULL
            """)
            conn.commit()
            print("SUCCESS: did_play column added")
        else:
            print("SUCCESS: did_play column already exists")

def validate_gameweek(conn, gameweek: int, understat_players: set, mappings: dict) -> dict:
    """Validate and update game scores for a specific gameweek"""

    # Get players who played according to Understat
    played_fantrax_ids = set()
    mapped_count = 0

    for understat_name in understat_players:
        if understat_name in mappings:
            played_fantrax_ids.add(mappings[understat_name])
            mapped_count += 1

    print(f"  Understat players: {len(understat_players)}")
    print(f"  Mapped to Fantrax: {mapped_count} ({mapped_count/len(understat_players)*100:.1f}%)")

    # Get all game scores for this gameweek
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, player_id, points_scored
            FROM player_game_scores
            WHERE game_number = %s
        """, (gameweek,))
        game_scores = cur.fetchall()

    print(f"  Game scores in database: {len(game_scores)}")

    # Analyze and prepare updates
    updates = []
    stats = {
        'total_scores': len(game_scores),
        'players_who_played': 0,
        'zero_scores_who_played': 0,
        'zero_scores_who_didnt_play': 0,
        'non_zero_scores': 0
    }

    for score_record in game_scores:
        player_id = score_record['player_id']
        score = float(score_record['points_scored'])
        record_id = score_record['id']

        # Determine if player actually played
        did_play = player_id in played_fantrax_ids

        # Override: non-zero score means they definitely played
        if score != 0:
            did_play = True
            stats['non_zero_scores'] += 1

        # Track statistics
        if did_play:
            stats['players_who_played'] += 1
            if score == 0:
                stats['zero_scores_who_played'] += 1
        else:
            if score == 0:
                stats['zero_scores_who_didnt_play'] += 1

        updates.append((did_play, record_id))

    # Execute batch update
    print(f"  Updating {len(updates)} records...")
    with conn.cursor() as cur:
        cur.executemany("""
            UPDATE player_game_scores
            SET did_play = %s
            WHERE id = %s
        """, updates)
        conn.commit()

    print(f"  Results:")
    print(f"    Players who played: {stats['players_who_played']}")
    print(f"    Zero scores who played: {stats['zero_scores_who_played']} (keep)")
    print(f"    Zero scores who didn't play: {stats['zero_scores_who_didnt_play']} (exclude)")
    print(f"    Non-zero scores: {stats['non_zero_scores']}")

    return stats

def create_clean_view(conn):
    """Create a view for clean game scores (excluding players who didn't play)"""
    with conn.cursor() as cur:
        cur.execute("""
            DROP VIEW IF EXISTS clean_player_game_scores
        """)

        cur.execute("""
            CREATE VIEW clean_player_game_scores AS
            SELECT
                id,
                player_id,
                game_number,
                points_scored,
                opponent,
                date_played,
                import_timestamp,
                did_play
            FROM player_game_scores
            WHERE did_play = true
        """)
        conn.commit()
        print("SUCCESS: Created clean_player_game_scores view")

def validate_results(conn):
    """Validate the results and show summary"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Total records
        cur.execute("SELECT COUNT(*) as total FROM player_game_scores")
        total = cur.fetchone()['total']

        # Records with did_play data
        cur.execute("SELECT COUNT(*) as with_data FROM player_game_scores WHERE did_play IS NOT NULL")
        with_data = cur.fetchone()['with_data']

        # Clean records (players who played)
        cur.execute("SELECT COUNT(*) as clean FROM player_game_scores WHERE did_play = true")
        clean = cur.fetchone()['clean']

        # Excluded records (players who didn't play)
        cur.execute("SELECT COUNT(*) as excluded FROM player_game_scores WHERE did_play = false")
        excluded = cur.fetchone()['excluded']

        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"Total game score records: {total:,}")
        print(f"Records with validation data: {with_data:,}")
        print(f"Clean records (did_play=true): {clean:,}")
        print(f"Excluded records (did_play=false): {excluded:,}")
        print(f"Data quality improvement: {excluded:,} false entries identified")
        print(f"Coverage: {with_data/total*100:.1f}% of all records validated")

def main():
    """Main validation implementation"""
    print("="*80)
    print("IMPLEMENTING GAME SCORES VALIDATION")
    print("Using 100% verified Understat mappings")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Step 1: Add did_play column
        print("\nStep 1: Database Schema Update")
        print("-" * 40)
        add_did_play_column(conn)

        # Step 2: Get verified mappings
        print("\nStep 2: Loading Verified Mappings")
        print("-" * 40)
        mappings = get_verified_mappings(conn)
        print(f"SUCCESS: Loaded {len(mappings)} verified Understat mappings")

        # Step 3: Validate each gameweek
        print("\nStep 3: Validating Game Scores")
        print("-" * 40)
        all_stats = {}

        for gameweek in [1, 2, 3, 4]:
            print(f"\nProcessing Gameweek {gameweek}:")

            # Load Understat players who played
            understat_players = load_understat_players(gameweek)
            if not understat_players:
                print(f"  ERROR: No Understat data for GW{gameweek}")
                continue

            # Validate and update
            stats = validate_gameweek(conn, gameweek, understat_players, mappings)
            all_stats[gameweek] = stats

        # Step 4: Create clean view
        print(f"\nStep 4: Creating Clean Data View")
        print("-" * 40)
        create_clean_view(conn)

        # Step 5: Validate results
        print(f"\nStep 5: Validation Results")
        print("-" * 40)
        validate_results(conn)

        # Final summary
        total_excluded = sum(stats.get('zero_scores_who_didnt_play', 0) for stats in all_stats.values())
        total_validated = sum(stats.get('zero_scores_who_played', 0) for stats in all_stats.values())

        print(f"\n{'='*80}")
        print("IMPLEMENTATION COMPLETE")
        print("="*80)
        print(f"SUCCESS: Database schema updated with did_play column")
        print(f"SUCCESS: All GW1-4 game scores validated using Understat data")
        print(f"SUCCESS: {total_excluded:,} false zero-point entries identified for exclusion")
        print(f"SUCCESS: {total_validated:,} legitimate zero-point performances preserved")
        print(f"SUCCESS: Clean data view created: clean_player_game_scores")
        print(f"\nREADY: Form calculation can now use clean, validated data!")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()