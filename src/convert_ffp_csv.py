"""
Convert Fantasy Football Pundit CSV to our expected format
Handles team name mapping, confidence percentage parsing, and confidence-based multiplier assignment

This script converts FFP's confidence-based predictions to weighted starter multipliers:
- 90-100% confidence → 1.0x (definite starter)
- 70-89% confidence → 0.85x (likely starter)
- 50-69% confidence → 0.70x (rotation risk)
- 30-49% confidence → 0.50x (unlikely starter)
- <30% confidence → 0.15x (bench)
"""

import csv
import sys
import os
import re

# Team name mapping from FFP format to our abbreviations
TEAM_MAPPING = {
    "Arsenal": "ARS",
    "Aston Villa": "AVL", 
    "Bournemouth": "BOU",
    "Brentford": "BRE",
    "Brighton": "BHA",
    "Brighton and Hove Albion": "BHA",
    "Burnley": "BUR",
    "Chelsea": "CHE",
    "Crystal Palace": "CRY",
    "Everton": "EVE",
    "Fulham": "FUL",
    "Leeds": "LEE",
    "Leeds United": "LEE",
    "Liverpool": "LIV",
    "Manchester City": "MCI",
    "Man City": "MCI",
    "Manchester United": "MUN",
    "Man Utd": "MUN",
    "Newcastle": "NEW",
    "Newcastle United": "NEW",
    "Nottingham Forest": "NFO",
    "Sunderland": "SUN",
    "Tottenham": "TOT",
    "Tottenham Hotspur": "TOT",
    "West Ham": "WHU",
    "West Ham United": "WHU",
    "Wolves": "WOL",
    "Wolverhampton Wanderers": "WOL"
}

def confidence_to_multiplier(confidence_percentage, starter_params=None):
    """
    Convert confidence percentage to starter multiplier using system parameters

    Args:
        confidence_percentage (float): Confidence percentage (0-100)
        starter_params (dict): System parameters for starter multipliers

    Returns:
        float: Starter multiplier
    """
    if starter_params is None:
        # Default values if no parameters provided (backwards compatibility)
        starter_params = {
            'likely_starter_penalty': 0.85,
            'auto_rotation_penalty': 0.70,
            'unlikely_starter_penalty': 0.50,
            'force_bench_penalty': 0.15
        }

    if confidence_percentage >= 90:
        return 1.0    # Definite starter
    elif confidence_percentage >= 70:
        return starter_params.get('likely_starter_penalty', 0.85)
    elif confidence_percentage >= 50:
        return starter_params.get('auto_rotation_penalty', 0.70)
    elif confidence_percentage >= 30:
        return starter_params.get('unlikely_starter_penalty', 0.50)
    else:
        return starter_params.get('force_bench_penalty', 0.15)

def parse_confidence_percentage(confidence_str):
    """
    Parse confidence percentage from string (e.g., "95%" -> 95.0)
    
    Args:
        confidence_str (str): Confidence string with percentage
        
    Returns:
        float: Confidence as float, or 0.0 if cannot parse
    """
    if not confidence_str:
        return 0.0
    
    # Remove % and any whitespace, try to convert to float
    try:
        return float(confidence_str.replace('%', '').strip())
    except (ValueError, AttributeError):
        return 0.0

def parse_ffp_row(row, starter_params=None):
    """
    Parse a single FFP CSV row into player predictions

    Args:
        row (list): CSV row data
        starter_params (dict): System parameters for starter multipliers

    Returns:
        list: List of player dictionaries with name, confidence, and multiplier
    """
    if not row or len(row) < 3:
        return []
    
    # First column should be team name (includes " Predicted Lineup")
    team_name_raw = row[0].strip().strip('"')
    
    # Skip if this isn't a team row (header or empty)
    if not team_name_raw or team_name_raw == '' or not 'Predicted Lineup' in team_name_raw:
        return []
    
    # Extract team name by removing " Predicted Lineup"
    team_name = team_name_raw.replace(' Predicted Lineup', '').strip()
    
    players = []
    
    # Process pairs of (player_name, confidence) starting from column 1
    for i in range(1, len(row) - 1, 2):  # Step by 2, stop before last to ensure we have pairs
        if i + 1 >= len(row):
            break
            
        player_name = row[i].strip().strip('"')
        confidence_str = row[i + 1].strip().strip('"')
        
        # Skip empty players or empty confidence
        if not player_name or player_name == '' or not confidence_str or confidence_str == '':
            continue
            
        # Parse confidence percentage
        confidence = parse_confidence_percentage(confidence_str)
        
        # Skip if no valid confidence
        if confidence <= 0:
            continue
            
        # Convert to multiplier using system parameters
        multiplier = confidence_to_multiplier(confidence, starter_params)
        
        players.append({
            'team': team_name,
            'name': player_name,
            'confidence': confidence,
            'multiplier': multiplier,
            'status': 'starter' if multiplier >= 0.9 else 'rotation'
        })
    
    return players

def convert_ffp_csv(input_path, output_path):
    """Convert FFP CSV to our expected individual player format"""
    
    converted_players = []
    skipped_teams = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            
            # Process each row
            for row_num, row in enumerate(reader, 1):
                players = parse_ffp_row(row)
                
                if not players:
                    continue
                    
                # Get team abbreviation
                team_name = players[0]['team']
                if team_name in TEAM_MAPPING:
                    team_abbrev = TEAM_MAPPING[team_name]
                    
                    # Add team abbreviation to each player
                    for player in players:
                        player['team_abbrev'] = team_abbrev
                        converted_players.append(player)
                        
                else:
                    skipped_teams.append(team_name)
        
        # Write converted CSV in individual player format
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['Team', 'Player Name', 'Position', 'Predicted Status', 'Confidence', 'Multiplier'])
            
            for player in converted_players:
                writer.writerow([
                    player['team_abbrev'],
                    player['name'],
                    'Unknown',  # Position will be looked up via name matching
                    player['status'],
                    f"{player['confidence']:.0f}%",
                    f"{player['multiplier']:.2f}"
                ])
        
        print(f"[SUCCESS] FFP Conversion successful!")
        print(f"   Input: {input_path}")
        print(f"   Output: {output_path}")
        print(f"   Players converted: {len(converted_players)}")
        print(f"   Teams processed: {len(set(p['team'] for p in converted_players))}")
        
        # Show confidence distribution
        confidence_ranges = {
            '90-100%': len([p for p in converted_players if p['confidence'] >= 90]),
            '70-89%': len([p for p in converted_players if 70 <= p['confidence'] < 90]),
            '50-69%': len([p for p in converted_players if 50 <= p['confidence'] < 70]),
            '30-49%': len([p for p in converted_players if 30 <= p['confidence'] < 50]),
            '<30%': len([p for p in converted_players if p['confidence'] < 30])
        }
        
        print(f"   Confidence distribution:")
        for range_name, count in confidence_ranges.items():
            multiplier = confidence_to_multiplier(float(range_name.split('-')[0].replace('%', '').replace('<', '')))
            print(f"     {range_name}: {count} players → {multiplier}x multiplier")
        
        if skipped_teams:
            print(f"   Teams skipped (not in mapping): {skipped_teams}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] FFP Conversion failed: {e}")
        return False

def main():
    """Convert FFP CSV with command line arguments"""
    
    if len(sys.argv) != 3:
        print("Usage: python convert_ffp_csv.py <input_csv> <output_csv>")
        print("Example: python convert_ffp_csv.py fantasyfootballpundit.csv gameweek_1_lineups.csv")
        print("")
        print("Converts Fantasy Football Pundit confidence-based predictions to individual player format")
        print("with confidence-based multipliers:")
        print("  90-100% → 1.0x (definite starter)")
        print("  70-89%  → 0.85x (likely starter)")
        print("  50-69%  → 0.70x (rotation risk)")
        print("  30-49%  → 0.50x (unlikely starter)")
        print("  <30%    → 0.15x (bench)")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    
    success = convert_ffp_csv(input_path, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()