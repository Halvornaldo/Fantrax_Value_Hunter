#!/usr/bin/env python3
"""
Find all Understat players from GW1-4 that are not yet mapped to Fantrax
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
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

def load_all_understat_players() -> set:
    """Load all Understat players from GW1-4"""
    all_players = set()

    for gameweek in [1, 2, 3, 4]:
        filename = f'gw{gameweek}_players_found.json'

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                players = json.load(f)
                all_players.update(players)
                print(f"GW{gameweek}: {len(players)} players")
        else:
            print(f"Warning: {filename} not found")

    return all_players

def get_existing_mappings(conn) -> dict:
    """Get all existing Understat mappings (verified and unverified)"""
    query = """
    SELECT source_name, fantrax_id, verified, confidence_score
    FROM name_mappings
    WHERE source_system = 'understat'
    ORDER BY confidence_score DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

    mappings = {}
    for row in results:
        if row['source_name'] not in mappings:
            mappings[row['source_name']] = {
                'fantrax_id': row['fantrax_id'],
                'verified': row['verified'],
                'confidence': row['confidence_score']
            }

    return mappings

def find_unmapped_players(all_players: set, existing_mappings: dict) -> list:
    """Find players that don't have any mapping yet"""
    unmapped = []

    for player in all_players:
        if player not in existing_mappings:
            unmapped.append(player)

    return sorted(unmapped)

def find_unverified_players(all_players: set, existing_mappings: dict) -> list:
    """Find players that have mappings but aren't verified yet"""
    unverified = []

    for player in all_players:
        if player in existing_mappings:
            mapping = existing_mappings[player]
            if not mapping['verified']:
                unverified.append({
                    'name': player,
                    'fantrax_id': mapping['fantrax_id'],
                    'confidence': mapping['confidence']
                })

    return sorted(unverified, key=lambda x: x['confidence'], reverse=True)

def attempt_new_mappings(unmapped_players: list, matcher: UnifiedNameMatcher) -> tuple:
    """Try to create new mappings for unmapped players"""
    new_matches = []
    still_unmapped = []

    print(f"\nAttempting to match {len(unmapped_players)} unmapped players...")

    for i, player_name in enumerate(unmapped_players):
        print(f"  [{i+1}/{len(unmapped_players)}] Trying to match: {player_name}")

        try:
            match_result = matcher.match_player(
                source_name=player_name,
                source_system='understat',
                force_refresh=True  # Force new matching attempt
            )

            if match_result and match_result.get('confidence', 0) >= 0.7:
                new_matches.append({
                    'name': player_name,
                    'fantrax_id': match_result['fantrax_id'],
                    'confidence': match_result['confidence'],
                    'match_type': match_result.get('match_type', 'unknown')
                })
                print(f"    ✓ Matched to {match_result['fantrax_id']} (confidence: {match_result['confidence']:.2f})")
            else:
                still_unmapped.append(player_name)
                print(f"    ✗ No good match found")

        except Exception as e:
            still_unmapped.append(player_name)
            print(f"    ✗ Error: {e}")

    return new_matches, still_unmapped

def main():
    """Main execution"""
    print("="*80)
    print("FINDING UNMAPPED UNDERSTAT PLAYERS")
    print("="*80)

    # Load all Understat players from GW1-4
    print("\nLoading Understat players from GW1-4...")
    all_players = load_all_understat_players()
    print(f"Total unique players found: {len(all_players)}")

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Get existing mappings
        print("\nChecking existing mappings...")
        existing_mappings = get_existing_mappings(conn)

        verified_count = sum(1 for m in existing_mappings.values() if m['verified'])
        unverified_count = len(existing_mappings) - verified_count

        print(f"Existing mappings: {len(existing_mappings)} total")
        print(f"  - Verified: {verified_count}")
        print(f"  - Unverified: {unverified_count}")

        # Find unmapped players
        unmapped_players = find_unmapped_players(all_players, existing_mappings)
        print(f"\nCompletely unmapped players: {len(unmapped_players)}")

        # Find unverified players
        unverified_players = find_unverified_players(all_players, existing_mappings)
        print(f"Players with unverified mappings: {len(unverified_players)}")

        if unmapped_players:
            print(f"\nUnmapped players:")
            for i, player in enumerate(unmapped_players):
                print(f"  {i+1:2d}. {player}")

        if unverified_players:
            print(f"\nUnverified mappings (high confidence first):")
            for i, player in enumerate(unverified_players):
                print(f"  {i+1:2d}. {player['name']} -> {player['fantrax_id']} (conf: {player['confidence']:.2f})")

        # Attempt new mappings for unmapped players
        if unmapped_players:
            print(f"\n{'='*60}")
            print("ATTEMPTING NEW MAPPINGS")
            print("="*60)

            matcher = UnifiedNameMatcher(conn)
            new_matches, still_unmapped = attempt_new_mappings(unmapped_players, matcher)

            print(f"\n{'='*60}")
            print("NEW MAPPING RESULTS")
            print("="*60)

            if new_matches:
                print(f"\nNew matches found ({len(new_matches)}):")
                for match in new_matches:
                    print(f"  ✓ {match['name']} -> {match['fantrax_id']} (conf: {match['confidence']:.2f}, {match['match_type']})")

            if still_unmapped:
                print(f"\nStill unmapped ({len(still_unmapped)}):")
                for player in still_unmapped:
                    print(f"  ✗ {player}")

                # Save unmapped players for manual review
                with open('still_unmapped_players.json', 'w') as f:
                    json.dump(still_unmapped, f, indent=2)
                print(f"\nSaved unmapped players to still_unmapped_players.json")

        # Summary
        print(f"\n{'='*80}")
        print("MAPPING COMPLETION SUMMARY")
        print("="*80)

        mapped_count = len(all_players) - len(unmapped_players)
        mapping_rate = (mapped_count / len(all_players)) * 100

        print(f"Total Understat players (GW1-4): {len(all_players)}")
        print(f"Players with mappings: {mapped_count}")
        print(f"Players without mappings: {len(unmapped_players)}")
        print(f"Current mapping rate: {mapping_rate:.1f}%")

        if len(unmapped_players) == 0:
            print("\n🎉 ALL PLAYERS MAPPED! 100% coverage achieved!")
        else:
            print(f"\nNext steps:")
            print(f"  1. Review unverified mappings (may auto-verify high confidence ones)")
            print(f"  2. Manually map remaining {len(unmapped_players)} players")
            print(f"  3. Use validation dashboard for final verification")

    finally:
        conn.close()

if __name__ == "__main__":
    main()