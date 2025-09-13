#!/usr/bin/env python3
"""
Import 2024-25 historical games data from CSV file
Calculates games_played = FPts ÷ FP/G and stores in player_games_data table
"""
import csv
import psycopg2
import sys
import os

# Team mapping from CSV to database codes
TEAM_MAPPING = {
    'ARS': 'ARS', 'AVL': 'AVL', 'BOU': 'BOU', 'BRF': 'BRF', 'BHA': 'BHA',
    'BUR': 'BUR', 'CHE': 'CHE', 'CRY': 'CRY', 'EVE': 'EVE', 'FUL': 'FUL',
    'LIV': 'LIV', 'MCI': 'MCI', 'MUN': 'MUN', 'NEW': 'NEW', 'NOT': 'NOT',
    'SOU': 'SUN', 'TOT': 'TOT', 'WHU': 'WHU', 'WOL': 'WOL', 'LEE': 'LEE'
}

def clean_player_id(player_id):
    """Clean player ID by removing asterisks"""
    return player_id.replace('*', '') if player_id else None

def calculate_games_played(fpts_str, fpg_str):
    """Calculate games played from FPts and FP/G"""
    try:
        fpts = float(fpts_str) if fpts_str else 0
        fpg = float(fpg_str) if fpg_str else 0
        
        if fpg > 0:
            return round(fpts / fpg)
        return 0
    except (ValueError, TypeError):
        return 0

def import_historical_data():
    csv_file = 'c:/Users/halvo/Downloads/Fantrax-Players-Its Coming Home (9).csv'
    
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='fantrax_user',
            password='fantrax_password',
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        print(f"Reading 2024-25 data from: {csv_file}")
        
        # Read CSV file
        players_processed = 0
        players_matched = 0
        players_imported = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                players_processed += 1
                
                # Extract data from CSV
                csv_id = clean_player_id(row.get('ID', ''))
                player_name = row.get('Player', '').strip()
                team_code = row.get('Team', '').strip()
                fpts = row.get('FPts', '0')
                fpg = row.get('FP/G', '0')
                
                # Calculate games played
                games_played = calculate_games_played(fpts, fpg)
                total_points = float(fpts) if fpts else 0
                
                if not csv_id or not player_name:
                    continue
                
                # Find matching player in our database
                cursor.execute("""
                    SELECT id, name, team 
                    FROM players 
                    WHERE id = %s OR LOWER(name) = LOWER(%s)
                    LIMIT 1
                """, (csv_id, player_name))
                
                player_match = cursor.fetchone()
                
                if player_match:
                    players_matched += 1
                    player_id = player_match[0]
                    
                    # Insert/update historical games data for all gameweeks (1 and 2)
                    for gameweek in [1, 2]:
                        cursor.execute("""
                            INSERT INTO player_games_data 
                            (player_id, gameweek, total_points_historical, games_played_historical, data_source)
                            VALUES (%s, %s, %s, %s, 'historical')
                            ON CONFLICT (player_id, gameweek) 
                            DO UPDATE SET
                                total_points_historical = EXCLUDED.total_points_historical,
                                games_played_historical = EXCLUDED.games_played_historical,
                                data_source = 'historical',
                                last_updated = CURRENT_TIMESTAMP
                        """, (player_id, gameweek, total_points, games_played))
                    
                    players_imported += 1
                    
                    if players_imported <= 5:  # Show first 5 for verification
                        print(f"  {player_name:<25} {games_played:>3} games ({total_points:>6.1f} pts, {fpg:>5} ppg)")
                
                # Show progress every 100 players
                if players_processed % 100 == 0:
                    print(f"Processed {players_processed} players...")
        
        conn.commit()
        
        print(f"\n=== IMPORT SUMMARY ===")
        print(f"Players in CSV: {players_processed}")
        print(f"Players matched: {players_matched}")
        print(f"Players imported: {players_imported}")
        print(f"Match rate: {(players_matched/players_processed)*100:.1f}%")
        
        # Verify data was imported
        cursor.execute("""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT player_id) as unique_players,
                   AVG(games_played_historical) as avg_games,
                   MAX(games_played_historical) as max_games
            FROM player_games_data 
            WHERE games_played_historical > 0
        """)
        
        stats = cursor.fetchone()
        print(f"\n=== DATABASE VERIFICATION ===")
        print(f"Total records: {stats[0]}")
        print(f"Unique players: {stats[1]}")
        print(f"Average games: {stats[2]:.1f}")
        print(f"Max games: {stats[3]}")
        
        # Show top players by games played
        cursor.execute("""
            SELECT p.name, pgd.games_played_historical, pgd.total_points_historical
            FROM player_games_data pgd
            JOIN players p ON pgd.player_id = p.id
            WHERE pgd.games_played_historical > 0
            ORDER BY pgd.games_played_historical DESC
            LIMIT 5
        """)
        
        print(f"\n=== TOP 5 BY GAMES PLAYED ===")
        for row in cursor.fetchall():
            print(f"  {row[0]:<25} {row[1]:>3} games ({row[2]:>6.1f} pts)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Import failed: {e}")
        return False

if __name__ == "__main__":
    success = import_historical_data()
    if success:
        print("\nHistorical data import completed successfully!")
    else:
        print("\nHistorical data import failed!")