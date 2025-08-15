"""
Convert Fantasy Football Scout CSV to our expected format
Handles team name mapping and column restructuring

This script only converts the CSV format. The penalty-based starter prediction logic
(1.0x for 220 starters, 0.65x penalty for 413 non-starters) will be applied by the
dashboard's CSV import functionality in src/lineup_importer.py
"""

import csv
import sys
import os

# Team name mapping from FFS format to our abbreviations
TEAM_MAPPING = {
    "Arsenal": "ARS",
    "Aston Villa": "AVL", 
    "Bournemouth": "BOU",
    "Brentford": "BRE",
    "Brighton and Hove Albion": "BHA",
    "Burnley": "BUR",
    "Chelsea": "CHE",
    "Crystal Palace": "CRY",
    "Everton": "EVE",
    "Fulham": "FUL",
    "Leeds United": "LEE",
    "Liverpool": "LIV",
    "Manchester City": "MCI",
    "Manchester United": "MUN",
    "Newcastle United": "NEW",
    "Nottingham Forest": "NFO",
    "Sunderland": "SUN",
    "Tottenham Hotspur": "TOT",
    "West Ham United": "WHU",
    "Wolverhampton Wanderers": "WOL"
}

def convert_ffs_csv(input_path, output_path):
    """Convert FFS CSV to our expected format"""
    
    converted_teams = []
    skipped_teams = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Skip header row
            
            # Process each team row
            for row in reader:
                team_name = row[0]
                players = row[1:12]  # Get 11 players (columns 1-11)
                
                # Map team name to abbreviation
                if team_name in TEAM_MAPPING:
                    team_abbrev = TEAM_MAPPING[team_name]
                    players_str = ", ".join(players)
                    converted_teams.append([team_abbrev, players_str])
                else:
                    skipped_teams.append(team_name)
        
        # Write converted CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['Team', 'Predicted Starting XI'])
            writer.writerows(converted_teams)
        
        print(f"[SUCCESS] Conversion successful!")
        print(f"   Input: {input_path}")
        print(f"   Output: {output_path}")
        print(f"   Teams converted: {len(converted_teams)}")
        
        if skipped_teams:
            print(f"   Teams skipped: {skipped_teams}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        return False

def main():
    """Convert FFS CSV with command line arguments"""
    
    if len(sys.argv) != 3:
        print("Usage: python convert_ffs_csv.py <input_csv> <output_csv>")
        print("Example: python convert_ffs_csv.py fantasyfootballscout.csv gameweek_1_lineups.csv")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    
    success = convert_ffs_csv(input_path, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()