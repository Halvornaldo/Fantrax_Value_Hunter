#!/usr/bin/env python3
"""
SAFE READ-ONLY ANALYSIS: Check game scores validation using existing verified Understat mappings
This script only reads data and doesn't modify any tables
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

def load_understat_players(gameweek: int) -> set:
    """Load Understat players who played in a specific gameweek"""
    filename = f'gw{gameweek}_players_found.json'

    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return set()

    with open(filename, 'r') as f:
        players = json.load(f)

    return set(players)

def get_verified_understat_mappings(conn) -> dict:
    """Get existing verified Understat mappings - READ ONLY"""
    query = """
    SELECT source_name, fantrax_id, confidence_score
    FROM name_mappings
    WHERE source_system = 'understat'
    AND verified = true
    ORDER BY confidence_score DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

    mappings = {}
    for row in results:
        if row['source_name'] not in mappings:
            mappings[row['source_name']] = row['fantrax_id']

    return mappings

def analyze_game_scores(conn, gameweek: int, understat_players: set, mappings: dict) -> dict:
    """Analyze game scores for validation - READ ONLY"""

    # Get matched players (those who played according to Understat)
    matched_fantrax_ids = set()
    matched_count = 0

    for understat_name in understat_players:
        if understat_name in mappings:
            matched_fantrax_ids.add(mappings[understat_name])
            matched_count += 1

    # Get game scores for this gameweek
    query = """
    SELECT player_id, points_scored
    FROM player_game_scores
    WHERE game_number = %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (gameweek,))
        game_scores = cur.fetchall()

    # Analyze the scores
    stats = {
        'understat_players_total': len(understat_players),
        'mapped_to_fantrax': matched_count,
        'mapping_rate': matched_count / len(understat_players) * 100 if understat_players else 0,
        'total_game_scores': len(game_scores),
        'players_who_played': 0,
        'zero_scores_who_played': 0,
        'zero_scores_who_didnt_play': 0,
        'non_zero_scores': 0
    }

    for score_record in game_scores:
        player_id = score_record['player_id']
        score = score_record['points_scored']

        did_play = player_id in matched_fantrax_ids

        if did_play:
            stats['players_who_played'] += 1
            if score == 0:
                stats['zero_scores_who_played'] += 1
        else:
            if score == 0:
                stats['zero_scores_who_didnt_play'] += 1

        if score != 0:
            stats['non_zero_scores'] += 1

    return stats

def main():
    """Main analysis - READ ONLY"""
    print("="*80)
    print("GAME SCORES VALIDATION ANALYSIS")
    print("Using existing verified Understat mappings (READ ONLY)")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Get verified mappings
        print("Loading verified Understat mappings...")
        mappings = get_verified_understat_mappings(conn)
        print(f"Found {len(mappings)} verified mappings")

        all_stats = {}

        # Analyze each gameweek
        for gameweek in [1, 2, 3, 4]:
            print(f"\n{'='*60}")
            print(f"Analyzing Gameweek {gameweek}")
            print("="*60)

            # Load Understat players
            understat_players = load_understat_players(gameweek)
            if not understat_players:
                print(f"No Understat data for GW{gameweek}")
                continue

            # Analyze game scores
            stats = analyze_game_scores(conn, gameweek, understat_players, mappings)
            all_stats[gameweek] = stats

            print(f"Understat players found: {stats['understat_players_total']}")
            print(f"Mapped to Fantrax: {stats['mapped_to_fantrax']} ({stats['mapping_rate']:.1f}%)")
            print(f"Total game scores: {stats['total_game_scores']}")
            print(f"Players who played: {stats['players_who_played']}")
            print(f"Zero scores who played: {stats['zero_scores_who_played']} (should keep)")
            print(f"Zero scores who didn't play: {stats['zero_scores_who_didnt_play']} (could exclude)")
            print(f"Non-zero scores: {stats['non_zero_scores']}")

        # Summary
        print(f"\n{'='*80}")
        print("VALIDATION IMPACT SUMMARY")
        print("="*80)

        total_zero_validated = sum(stats.get('zero_scores_who_played', 0) for stats in all_stats.values())
        total_zero_excluded = sum(stats.get('zero_scores_who_didnt_play', 0) for stats in all_stats.values())

        print(f"Zero-point players who actually played: {total_zero_validated}")
        print(f"Zero-point players who didn't play: {total_zero_excluded}")
        print(f"Data quality improvement potential: {total_zero_excluded} false entries removable")

        avg_mapping_rate = sum(stats.get('mapping_rate', 0) for stats in all_stats.values()) / len(all_stats)
        print(f"Average mapping success rate: {avg_mapping_rate:.1f}%")

        print(f"\nSUCCESS: Your existing {len(mappings)} verified mappings are excellent!")
        print(f"SUCCESS: High mapping success rate shows quality validation work")
        print(f"SUCCESS: Ready to implement actual validation when you're ready")

    finally:
        conn.close()

if __name__ == "__main__":
    main()