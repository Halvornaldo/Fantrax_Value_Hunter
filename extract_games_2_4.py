#!/usr/bin/env python3
"""
Extract players who played in EPL Games 2, 3, and 4 from Understat
Based on successful GW1 extraction method
"""

import ScraperFC as sfc
import json
from datetime import datetime

def get_gameweek_matches(gameweek_number):
    """
    Map gameweek numbers to match ranges
    EPL has 10 matches per gameweek (20 teams = 10 matches)
    """
    # GW1 = matches 0-9 (first 10 matches)
    # GW2 = matches 10-19
    # GW3 = matches 20-29
    # GW4 = matches 30-39

    start_match = (gameweek_number - 1) * 10
    end_match = start_match + 10

    return start_match, end_match

def extract_players_from_gameweek(gameweek_number):
    """Extract players who actually played in a specific gameweek"""

    print(f"\n{'='*60}")
    print(f"Extracting players from EPL Gameweek {gameweek_number}")
    print(f"{'='*60}")

    understat = sfc.Understat()

    # Get all match links for the season
    match_links = understat.get_match_links("2025/2026", "EPL")

    if not match_links:
        print("No match links found")
        return set()

    print(f"Total matches available: {len(match_links)}")

    # Get match range for this gameweek
    start_idx, end_idx = get_gameweek_matches(gameweek_number)

    if end_idx > len(match_links):
        print(f"Warning: Not enough matches for GW{gameweek_number}")
        print(f"Requested: {start_idx}-{end_idx-1}, Available: 0-{len(match_links)-1}")
        return set()

    gw_matches = match_links[start_idx:end_idx]
    print(f"Processing GW{gameweek_number} matches {start_idx}-{end_idx-1}:")

    all_players = set()
    successful_extractions = 0

    for i, match_link in enumerate(gw_matches):
        match_num = start_idx + i + 1
        print(f"\nMatch {match_num}/40 (GW{gameweek_number} #{i+1}): {match_link}")

        try:
            match_data = understat.scrape_match(match_link)
            players_in_match = []

            if isinstance(match_data, tuple) and len(match_data) >= 3:
                # Element 2 contains complete lineup data with minutes
                lineup_data = match_data[2]

                if isinstance(lineup_data, dict):
                    for team_key in ['h', 'a']:  # home and away
                        if team_key in lineup_data:
                            team_data = lineup_data[team_key]

                            if isinstance(team_data, dict):
                                # Each player has a unique ID as key
                                for player_id, player_data in team_data.items():
                                    player_name = player_data.get('player')
                                    minutes = player_data.get('time', 0)

                                    # Include all players who actually played (minutes > 0)
                                    if player_name and int(minutes) > 0:
                                        players_in_match.append(player_name)

            # Remove duplicates and add to overall set
            unique_players = list(set(players_in_match))

            if unique_players:
                all_players.update(unique_players)
                successful_extractions += 1
                print(f"   Found {len(unique_players)} players")
            else:
                print(f"   No players extracted")

        except Exception as e:
            print(f"   Error processing match: {e}")

    print(f"\n{'='*60}")
    print(f"GW{gameweek_number} EXTRACTION SUMMARY:")
    print(f"Successful extractions: {successful_extractions}/10")
    print(f"Total unique players found: {len(all_players)}")
    print(f"Expected: ~299 players per gameweek")

    if len(all_players) > 0:
        # Save to file
        filename = f'gw{gameweek_number}_players_found.json'
        with open(filename, 'w') as f:
            json.dump(list(all_players), f, indent=2)
        print(f"Player list saved to {filename}")

        # Show sample
        print(f"\nSample players from GW{gameweek_number}:")
        for i, player in enumerate(list(all_players)[:10]):
            print(f"  {i+1:2d}. {player}")

    return all_players

def main():
    """Extract players for games 2, 3, and 4"""

    print("Starting EPL Games 2-4 Player Extraction")
    print("Using successful GW1 extraction method")

    results = {}

    for gameweek in [2, 3, 4]:
        try:
            players = extract_players_from_gameweek(gameweek)
            results[f'GW{gameweek}'] = len(players)

            if len(players) >= 280:  # Within acceptable range
                print(f"SUCCESS GW{gameweek}: ({len(players)} players)")
            elif len(players) >= 200:
                print(f"PARTIAL GW{gameweek}: ({len(players)} players)")
            else:
                print(f"FAILED GW{gameweek}: ({len(players)} players)")

        except Exception as e:
            print(f"ERROR GW{gameweek}: {e}")
            results[f'GW{gameweek}'] = 0

    print(f"\n{'='*60}")
    print("FINAL SUMMARY:")
    print("="*60)

    for gw, count in results.items():
        status = "SUCCESS" if count >= 280 else "PARTIAL" if count >= 200 else "FAILED"
        print(f"{gw}: {count} players - {status}")

    total_extracted = sum(results.values())
    print(f"\nTotal players extracted across GW2-4: {total_extracted}")
    print(f"Expected total: ~897 players (299 x 3)")

    if total_extracted >= 840:  # 95% of expected
        print("OVERALL SUCCESS: Ready for Form calculation integration!")
    else:
        print("May need investigation or alternative approach")

if __name__ == "__main__":
    main()