#!/usr/bin/env python3
"""
Validation workflow for imported game scores
Validates player participation using Understat match data
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
import ScraperFC as sfc
from datetime import datetime
import argparse
import sys

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def extract_gameweek_players(gameweek_number: int) -> list:
    """Extract players who actually played in a specific gameweek from Understat"""
    print(f"Extracting Understat data for Gameweek {gameweek_number}...")

    try:
        understat = sfc.Understat()

        # Get match links for the season
        match_links = understat.get_match_links("2025/2026", "EPL")

        if not match_links:
            print("ERROR: No match links found")
            return []

        # Calculate match indices for this gameweek (10 matches per gameweek)
        start_match = (gameweek_number - 1) * 10
        end_match = start_match + 10

        if start_match >= len(match_links):
            print(f"ERROR: Gameweek {gameweek_number} matches not available yet")
            return []

        gameweek_matches = match_links[start_match:end_match]
        print(f"Processing {len(gameweek_matches)} matches for Gameweek {gameweek_number}")

        players_who_played = set()

        for i, match_link in enumerate(gameweek_matches):
            print(f"  Processing match {i+1}/{len(gameweek_matches)}...")

            try:
                match_data = understat.scrape_match(match_link)

                # Element 2 contains lineup data
                lineup_data = match_data[2]

                # Extract players from both teams
                for team_key in ['h', 'a']:  # home and away
                    team_data = lineup_data[team_key]
                    for player_id, player_data in team_data.items():
                        player_name = player_data.get('player')
                        minutes = player_data.get('time', 0)

                        # Only include players who actually played (minutes > 0)
                        if player_name and int(minutes) > 0:
                            players_who_played.add(player_name)

            except Exception as e:
                print(f"    WARNING: Error processing match: {e}")
                continue

        players_list = list(players_who_played)
        print(f"Found {len(players_list)} players who played in Gameweek {gameweek_number}")

        # Save to file for reference
        output_file = f'gw{gameweek_number}_players_found.json'
        with open(output_file, 'w') as f:
            json.dump(players_list, f, indent=2)
        print(f"Player list saved to {output_file}")

        return players_list

    except Exception as e:
        print(f"ERROR extracting Understat data: {e}")
        return []

def validate_game_scores(gameweek_number: int, understat_players: list) -> dict:
    """Validate game scores using Understat participation data"""
    print(f"\nValidating game scores for Gameweek {gameweek_number}...")

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Get verified name mappings
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT source_name, fantrax_id
                FROM name_mappings
                WHERE source_system = 'understat' AND verified = true
            """)
            mappings = {row['source_name']: row['fantrax_id'] for row in cur.fetchall()}

        print(f"Using {len(mappings)} verified name mappings")

        # Get Fantrax IDs of players who played according to Understat
        played_fantrax_ids = set()
        mapped_understat_players = 0

        for understat_name in understat_players:
            if understat_name in mappings:
                played_fantrax_ids.add(mappings[understat_name])
                mapped_understat_players += 1

        print(f"Mapped {mapped_understat_players}/{len(understat_players)} Understat players to Fantrax IDs")

        # Get all game scores for this gameweek
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, player_id, points_scored, did_play
                FROM player_game_scores
                WHERE game_number = %s
            """, (gameweek_number,))
            game_scores = cur.fetchall()

        print(f"Found {len(game_scores)} game score records for Gameweek {gameweek_number}")

        # Validation logic
        stats = {
            'total_scores': len(game_scores),
            'players_who_played': 0,
            'zero_scores_who_played': 0,
            'zero_scores_who_didnt_play': 0,
            'non_zero_scores': 0,
            'already_validated': 0,
            'newly_validated': 0
        }

        updates = []

        for score_record in game_scores:
            player_id = score_record['player_id']
            score = float(score_record['points_scored'])
            current_did_play = score_record['did_play']
            record_id = score_record['id']

            # Determine if player actually played
            did_play = player_id in played_fantrax_ids

            # Players with non-zero scores definitely played
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

            # Only update if validation status changed
            if current_did_play != did_play:
                updates.append((did_play, record_id))
                stats['newly_validated'] += 1
            else:
                stats['already_validated'] += 1

        # Apply updates
        if updates:
            with conn.cursor() as cur:
                cur.executemany("""
                    UPDATE player_game_scores
                    SET did_play = %s
                    WHERE id = %s
                """, updates)
                conn.commit()
            print(f"Updated {len(updates)} validation records")
        else:
            print("No validation updates needed")

        return stats

    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Validate game scores using Understat data')
    parser.add_argument('gameweek', type=int, help='Gameweek number to validate (e.g., 5)')
    parser.add_argument('--skip-extraction', action='store_true', help='Skip Understat extraction, use existing data')

    args = parser.parse_args()

    print("=" * 80)
    print(f"GAME SCORES VALIDATION - GAMEWEEK {args.gameweek}")
    print("=" * 80)

    # Step 1: Extract Understat data (unless skipped)
    if args.skip_extraction:
        # Try to load existing data
        try:
            with open(f'gw{args.gameweek}_players_found.json', 'r') as f:
                understat_players = json.load(f)
            print(f"Loaded {len(understat_players)} players from existing file")
        except FileNotFoundError:
            print("ERROR: No existing data found, run without --skip-extraction first")
            sys.exit(1)
    else:
        understat_players = extract_gameweek_players(args.gameweek)
        if not understat_players:
            print("ERROR: Failed to extract Understat data")
            sys.exit(1)

    # Step 2: Validate game scores
    stats = validate_game_scores(args.gameweek, understat_players)

    # Step 3: Report results
    print(f"\n{'=' * 80}")
    print("VALIDATION RESULTS")
    print("=" * 80)

    print(f"Gameweek {args.gameweek} Summary:")
    print(f"  Total game scores: {stats['total_scores']}")
    print(f"  Players who actually played: {stats['players_who_played']}")
    print(f"  Legitimate zero-scores: {stats['zero_scores_who_played']} (keep)")
    print(f"  False zero-scores: {stats['zero_scores_who_didnt_play']} (exclude)")
    print(f"  Non-zero scores: {stats['non_zero_scores']}")
    print(f"  Already validated: {stats['already_validated']}")
    print(f"  Newly validated: {stats['newly_validated']}")

    if stats['total_scores'] > 0:
        accuracy = (stats['players_who_played'] / len(understat_players)) * 100
        print(f"  Validation accuracy: {accuracy:.1f}%")

    data_quality_improvement = stats['zero_scores_who_didnt_play']
    if data_quality_improvement > 0:
        print(f"\n✅ Data quality improvement: {data_quality_improvement:,} false entries excluded!")

    print(f"\n🎯 Form calculations will now use only validated data (did_play = true)")

if __name__ == "__main__":
    main()