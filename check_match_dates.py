#!/usr/bin/env python3
"""
Check the dates of matches to verify gameweek mapping
"""

import ScraperFC as sfc
from datetime import datetime

def check_match_dates():
    """Check dates for first 40 matches to understand gameweek structure"""

    understat = sfc.Understat()
    match_links = understat.get_match_links("2025/2026", "EPL")

    if not match_links:
        print("No match links found")
        return

    print("MATCH DATES AND GAMEWEEK MAPPING")
    print("="*60)

    # Check first 40 matches (4 gameweeks)
    for i, match_link in enumerate(match_links[:40]):
        try:
            match_data = understat.scrape_match(match_link)

            if isinstance(match_data, tuple) and len(match_data) >= 2:
                # Element 1 contains match metadata including date
                match_info = match_data[1]

                if isinstance(match_info, dict) and 'date' in match_info:
                    date = match_info['date']
                    team_h = match_info.get('team_h', 'Unknown')
                    team_a = match_info.get('team_a', 'Unknown')

                    # Determine likely gameweek based on position
                    gameweek = (i // 10) + 1

                    print(f"Match {i+1:2d} (GW{gameweek}): {date} - {team_h} vs {team_a}")

                    # Stop after every 10 matches to see pattern
                    if (i + 1) % 10 == 0:
                        print("-" * 60)

        except Exception as e:
            print(f"Match {i+1:2d}: Error - {e}")

    print("\nGAMEWEEK DATE RANGES:")
    print("Please provide the actual dates for games 2-4 to verify mapping")

if __name__ == "__main__":
    check_match_dates()