"""
Migration script to import CSV data into PostgreSQL
Run this with: python import_csv_data.py
"""

import csv
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="fantrax_user",
            password="fantrax_password",
            database="fantrax_value_hunter",
            port=5433
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def clean_player_id(player_id):
    """Remove asterisks from player ID"""
    return player_id.strip('*')

def parse_position(position_str):
    """Parse position string and return primary position"""
    # Take first position if multiple (e.g., "M,F" -> "M")
    return position_str.split(',')[0].strip()

def calculate_value_score(ppg, price):
    """Calculate value score: PPG / Price"""
    try:
        ppg_float = float(ppg)
        price_float = float(price)
        if price_float > 0:
            return round(ppg_float / price_float, 3)
        return 0
    except:
        return 0

def import_csv_data():
    """Import all CSV data into database"""
    conn = connect_to_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Read CSV file
    csv_path = "../data/fpg_data_2024.csv"
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            players_data = []
            metrics_data = []
            
            for row in csv_reader:
                # Clean and prepare data
                player_id = clean_player_id(row['ID'])
                name = row['Player']
                team = row['Team']
                position = parse_position(row['Position'])
                price = float(row['Salary'])
                ppg = float(row['FP/G'])
                value_score = calculate_value_score(ppg, price)
                
                # Prepare player record
                players_data.append((player_id, name, team, position))
                
                # Prepare metrics record (gameweek 1)
                metrics_data.append((
                    player_id, 1, price, ppg, 'Historical', 
                    value_score, value_score,  # true_value = value_score initially
                    1.0, 1.0, 1.0  # multipliers default to 1.0
                ))
            
            # Bulk insert players
            print(f"Importing {len(players_data)} players...")
            execute_values(
                cursor,
                """
                INSERT INTO players (id, name, team, position)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    team = EXCLUDED.team,
                    position = EXCLUDED.position,
                    updated_at = CURRENT_TIMESTAMP
                """,
                players_data
            )
            
            # Bulk insert metrics
            print(f"Importing {len(metrics_data)} player metrics...")
            execute_values(
                cursor,
                """
                INSERT INTO player_metrics 
                (player_id, gameweek, price, ppg, ppg_source, value_score, true_value,
                 form_multiplier, fixture_multiplier, starter_multiplier)
                VALUES %s
                ON CONFLICT (player_id, gameweek) 
                DO UPDATE SET
                    price = EXCLUDED.price,
                    ppg = EXCLUDED.ppg,
                    ppg_source = EXCLUDED.ppg_source,
                    value_score = EXCLUDED.value_score,
                    true_value = EXCLUDED.true_value,
                    form_multiplier = EXCLUDED.form_multiplier,
                    fixture_multiplier = EXCLUDED.fixture_multiplier,
                    starter_multiplier = EXCLUDED.starter_multiplier,
                    last_updated = CURRENT_TIMESTAMP
                """,
                metrics_data
            )
            
            conn.commit()
            print(f"\n[SUCCESS] Successfully imported {len(players_data)} players and metrics!")
            
            # Verify import
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM player_metrics WHERE gameweek = 1")
            metrics_count = cursor.fetchone()[0]
            
            print(f"[INFO] Database now contains:")
            print(f"   - {player_count} players")
            print(f"   - {metrics_count} player metrics for gameweek 1")
            
            return True
            
    except FileNotFoundError:
        print(f"[ERROR] CSV file not found: {csv_path}")
        return False
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("[START] Starting CSV data import...")
    success = import_csv_data()
    
    if success:
        print("\n[COMPLETE] Migration completed successfully!")
        print("[INFO] Database is ready for Flask dashboard development")
    else:
        print("\n[FAILED] Migration failed - check error messages above")