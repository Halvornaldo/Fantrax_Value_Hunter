#!/usr/bin/env python3
"""
Convert Fantasy Football Scout CSV format to our expected format
Input: Team,player-name,player-name 2,...,player-name 11
Output: Team,Player Name,Position,Predicted Status

Updated for 2025-26 Premier League season with correct teams
"""

import csv
import sys

def convert_ffs_csv(input_file, output_file):
    """Convert FFS format to our import format"""
    
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader)  # Skip header row
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.writer(f_out)
            
            # Write our expected header
            writer.writerow(['Team', 'Player Name', 'Position', 'Predicted Status'])
            
            for row in reader:
                if len(row) < 2:
                    continue
                    
                team = row[0].strip('"')
                
                # Convert team names to 3-letter codes (matching database codes)
                team_mapping = {
                    'Arsenal': 'ARS',
                    'Aston Villa': 'AVL', 
                    'Bournemouth': 'BOU',
                    'Brentford': 'BRF',     # Database uses BRF not BRE
                    'Brighton and Hove Albion': 'BHA',
                    'Burnley': 'BUR',       # PROMOTED 2025-26
                    'Chelsea': 'CHE',
                    'Crystal Palace': 'CRY',
                    'Everton': 'EVE',
                    'Fulham': 'FUL',
                    'Leeds United': 'LEE',  # PROMOTED 2025-26
                    'Liverpool': 'LIV',
                    'Manchester City': 'MCI',
                    'Manchester United': 'MUN',
                    'Newcastle United': 'NEW',
                    'Nottingham Forest': 'NOT', # Database uses NOT not NFO
                    'Sunderland': 'SUN',    # PROMOTED 2025-26
                    'Tottenham Hotspur': 'TOT',
                    'West Ham United': 'WHU',
                    'Wolverhampton Wanderers': 'WOL'
                }
                
                team_code = team_mapping.get(team, team[:3].upper())
                print(f"Processing {team} ({team_code})")
                
                # Process each player in the starting XI (columns 1-11)
                for i, player in enumerate(row[1:12], 1):
                    if not player or player.strip('"') == '':
                        continue
                        
                    player_name = player.strip('"')
                    
                    # Estimate position based on typical formation positions
                    if i == 1:
                        position = 'G'  # Goalkeeper
                    elif i <= 4:
                        position = 'D'  # Defenders (positions 2-4)
                    elif i <= 8:
                        position = 'M'  # Midfielders (positions 5-8)
                    else:
                        position = 'F'  # Forwards (positions 9-11)
                    
                    # All players in starting XI are predicted starters
                    writer.writerow([team_code, player_name, position, 'Starter'])

if __name__ == '__main__':
    input_file = 'c:/Users/halvo/Downloads/fantasyfootballscout (2).csv'
    output_file = 'C:/Users/halvo/.claude/Fantrax_Value_Hunter/converted_lineups_fixed.csv'
    
    print(f"Converting {input_file} to {output_file}")
    print("2025-26 Premier League teams: All 20 teams included (LEE, BUR, SUN promoted)")
    convert_ffs_csv(input_file, output_file)
    print("Conversion complete!")
    
    # Show first few lines and summary
    print("\nFirst few lines of converted file:")
    with open(output_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:15]):
            print(f"{i+1:2d}: {line.strip()}")
        
        print(f"\nTotal lines: {len(lines)} (including header)")
        print(f"Expected: ~221 lines (1 header + 220 players from 20 teams)")