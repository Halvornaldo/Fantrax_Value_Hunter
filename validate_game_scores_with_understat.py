#!/usr/bin/env python3
"""
Validate player_game_scores using Understat participation data and existing name mappings
Leverages already validated Understat mappings from the name_mappings table
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Set, List, Tuple
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from name_matching.unified_matcher import UnifiedNameMatcher

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def load_understat_players(gameweek: int) -> Set[str]:
    """Load Understat players who played in a specific gameweek"""
    filename = f'gw{gameweek}_players_found.json'

    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return set()

    with open(filename, 'r') as f:
        players = json.load(f)

    print(f"Loaded {len(players)} players from GW{gameweek}")
    return set(players)

def get_existing_understat_mappings(conn) -> Dict[str, str]:
    """Get all existing validated Understat to Fantrax mappings"""
    query = """
    SELECT
        source_name,
        fantrax_id,
        confidence_score,
        validation_status
    FROM name_mappings
    WHERE source_system = 'understat'
    AND validation_status = 'validated'
    ORDER BY confidence_score DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

    mappings = {}
    for row in results:
        # Store the highest confidence mapping for each source name
        if row['source_name'] not in mappings:
            mappings[row['source_name']] = row['fantrax_id']

    print(f"Found {len(mappings)} existing validated Understat mappings")
    return mappings

def get_pending_understat_mappings(conn) -> List[Dict]:
    """Get pending Understat mappings that need validation"""
    query = """
    SELECT
        source_name,
        fantrax_id,
        confidence_score
    FROM name_mappings
    WHERE source_system = 'understat'
    AND validation_status = 'pending'
    AND confidence_score >= 0.8
    ORDER BY confidence_score DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def match_understat_to_fantrax(understat_players: Set[str], existing_mappings: Dict[str, str],
                               matcher: UnifiedNameMatcher) -> Tuple[Dict[str, str], Set[str]]:
    """
    Match Understat players to Fantrax IDs using existing mappings first,
    then UnifiedNameMatcher for remaining players
    """
    matched = {}
    unmatched = set()
    used_existing = 0
    new_matches = 0

    for understat_name in understat_players:
        # First check existing validated mappings
        if understat_name in existing_mappings:
            matched[understat_name] = existing_mappings[understat_name]
            used_existing += 1
        else:
            # Try to match using UnifiedNameMatcher
            match_result = matcher.match_player(
                source_name=understat_name,
                source_system='understat',
                force_refresh=False
            )

            if match_result and match_result['confidence'] >= 0.8:
                matched[understat_name] = match_result['fantrax_id']
                new_matches += 1
                print(f"  New match: {understat_name} -> {match_result['fantrax_id']} (confidence: {match_result['confidence']:.2f})")
            else:
                unmatched.add(understat_name)

    print(f"Matching summary:")
    print(f"  - Used existing mappings: {used_existing}")
    print(f"  - New matches found: {new_matches}")
    print(f"  - Total matched: {len(matched)}/{len(understat_players)}")
    print(f"  - Unmatched: {len(unmatched)}")

    return matched, unmatched

def get_game_scores_for_validation(conn, gameweek: int) -> Dict[str, float]:
    """Get all player scores for a specific gameweek"""
    query = """
    SELECT
        player_id,
        score
    FROM player_game_scores
    WHERE gameweek = %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (gameweek,))
        results = cur.fetchall()

    return {row['player_id']: row['score'] for row in results}

def validate_and_update_game_scores(conn, gameweek: int, matched_players: Dict[str, str],
                                    game_scores: Dict[str, float]) -> Dict:
    """
    Validate game scores and prepare updates for did_play column
    Returns statistics about the validation
    """
    stats = {
        'total_scores': len(game_scores),
        'players_who_played': 0,
        'zero_scores_who_played': 0,
        'zero_scores_who_didnt_play': 0,
        'non_zero_scores': 0
    }

    # Players who played according to Understat
    played_fantrax_ids = set(matched_players.values())

    updates = []

    for player_id, score in game_scores.items():
        did_play = player_id in played_fantrax_ids

        if did_play:
            stats['players_who_played'] += 1
            if score == 0:
                stats['zero_scores_who_played'] += 1
        else:
            if score == 0:
                stats['zero_scores_who_didnt_play'] += 1

        if score != 0:
            stats['non_zero_scores'] += 1
            did_play = True  # Non-zero score means they definitely played

        updates.append((did_play, player_id, gameweek))

    # Add did_play column if it doesn't exist
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

    # Update did_play values
    with conn.cursor() as cur:
        cur.executemany("""
            UPDATE player_game_scores
            SET did_play = %s
            WHERE player_id = %s AND gameweek = %s
        """, updates)
        conn.commit()

    return stats

def display_validation_summary(all_stats: Dict[int, Dict], unmatched_by_gw: Dict[int, Set[str]]):
    """Display comprehensive validation summary"""
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    total_zero_validated = 0
    total_zero_excluded = 0

    for gw in sorted(all_stats.keys()):
        stats = all_stats[gw]
        print(f"\nGameweek {gw}:")
        print(f"  Total game scores: {stats['total_scores']}")
        print(f"  Players who played (Understat): {stats['players_who_played']}")
        print(f"  Non-zero scores: {stats['non_zero_scores']}")
        print(f"  Zero scores who played: {stats['zero_scores_who_played']} ✓")
        print(f"  Zero scores who didn't play: {stats['zero_scores_who_didnt_play']} (excluded)")

        total_zero_validated += stats['zero_scores_who_played']
        total_zero_excluded += stats['zero_scores_who_didnt_play']

    print(f"\n" + "-"*80)
    print(f"TOTAL IMPACT:")
    print(f"  Zero-point players validated as playing: {total_zero_validated}")
    print(f"  Zero-point players excluded (didn't play): {total_zero_excluded}")
    print(f"  Data quality improvement: {total_zero_excluded} false data points removed")

    # Show unmatched players if any
    total_unmatched = sum(len(players) for players in unmatched_by_gw.values())
    if total_unmatched > 0:
        print(f"\n" + "-"*80)
        print(f"UNMATCHED PLAYERS (need manual review): {total_unmatched}")
        for gw, players in unmatched_by_gw.items():
            if players:
                print(f"\nGW{gw} unmatched ({len(players)}):")
                for player in sorted(list(players)[:10]):  # Show first 10
                    print(f"  - {player}")
                if len(players) > 10:
                    print(f"  ... and {len(players) - 10} more")

def main():
    """Main validation process"""
    print("="*80)
    print("PLAYER GAME SCORES VALIDATION WITH UNDERSTAT")
    print("Using existing validated mappings from name_mappings table")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Initialize UnifiedNameMatcher
        print("\nInitializing UnifiedNameMatcher...")
        matcher = UnifiedNameMatcher(conn)

        # Get existing validated Understat mappings
        print("\nLoading existing Understat mappings...")
        existing_mappings = get_existing_understat_mappings(conn)

        # Check for high-confidence pending mappings
        pending = get_pending_understat_mappings(conn)
        if pending:
            print(f"\nFound {len(pending)} high-confidence pending mappings (>=0.8)")
            print("Consider validating these to improve coverage")

        all_stats = {}
        unmatched_by_gw = {}

        # Process each gameweek
        for gameweek in [1, 2, 3, 4]:
            print(f"\n" + "="*60)
            print(f"Processing Gameweek {gameweek}")
            print("="*60)

            # Load Understat players who played
            understat_players = load_understat_players(gameweek)

            if not understat_players:
                print(f"Skipping GW{gameweek} - no Understat data")
                continue

            # Match to Fantrax IDs
            print(f"\nMatching {len(understat_players)} Understat players to Fantrax IDs...")
            matched, unmatched = match_understat_to_fantrax(
                understat_players, existing_mappings, matcher
            )
            unmatched_by_gw[gameweek] = unmatched

            # Get game scores for validation
            game_scores = get_game_scores_for_validation(conn, gameweek)
            print(f"Found {len(game_scores)} game scores for GW{gameweek}")

            # Validate and update
            print(f"\nValidating and updating did_play column...")
            stats = validate_and_update_game_scores(
                conn, gameweek, matched, game_scores
            )
            all_stats[gameweek] = stats

            print(f"Validation complete for GW{gameweek}")

        # Display summary
        display_validation_summary(all_stats, unmatched_by_gw)

        print("\n" + "="*80)
        print("VALIDATION COMPLETE")
        print("player_game_scores table updated with did_play column")
        print("Ready for clean Form calculation with validated data")
        print("="*80)

    finally:
        conn.close()

if __name__ == "__main__":
    main()