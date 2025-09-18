#!/usr/bin/env python3
"""
Import historical game scores from Fantrax CSV files
Imports games 1-4 for enhanced Form calculation
"""

import pandas as pd
import psycopg2
import sys
import os

def import_game_data(csv_file_path, game_number):
    """Import data from a single game CSV file"""

    # Database connection
    conn = psycopg2.connect(
        host='localhost',
        database='fantrax_value_hunter',
        user='fantrax_user',
        password='fantrax_password',
        port=5433
    )
    cursor = conn.cursor()

    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)

        # Validate required columns
        required_columns = ['ID', 'Player', 'FPts', 'Opponent']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing columns {missing_columns} in {csv_file_path}")
            return False

        # Get existing player IDs
        cursor.execute("SELECT id FROM players")
        existing_player_ids = set(row[0] for row in cursor.fetchall())

        imported_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # Extract player ID (remove asterisks)
                player_id = str(row['ID']).strip('*')
                player_name = row.get('Player', 'Unknown')
                opponent = row.get('Opponent', 'Unknown')

                # Skip if player not in database
                if player_id not in existing_player_ids:
                    continue

                # Get fantasy points
                fpts = float(row['FPts'])

                # Insert game score
                cursor.execute("""
                    INSERT INTO player_game_scores (player_id, game_number, points_scored, opponent, import_timestamp)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (player_id, game_number)
                    DO UPDATE SET
                        points_scored = EXCLUDED.points_scored,
                        opponent = EXCLUDED.opponent,
                        import_timestamp = NOW()
                """, [player_id, game_number, fpts, opponent])

                imported_count += 1

            except Exception as e:
                error_count += 1
                print(f"Error processing row {index} ({row.get('Player', 'Unknown')}): {e}")
                continue

        conn.commit()
        print(f"Game {game_number}: Imported {imported_count} players, {error_count} errors")
        return True

    except Exception as e:
        print(f"Error importing {csv_file_path}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Import all historical game files"""

    # Define the game files
    game_files = [
        ("c:/Users/halvo/Downloads/Fantrax G1.csv", 1),
        ("c:/Users/halvo/Downloads/Fantrax G2.csv", 2),
        ("c:/Users/halvo/Downloads/Fantrax G3.csv", 3),
        ("c:/Users/halvo/Downloads/Fantrax G4.csv", 4)
    ]

    print("Starting historical game data import...")

    total_imported = 0
    for file_path, game_num in game_files:
        if os.path.exists(file_path):
            print(f"\nImporting game {game_num} from {file_path}")
            success = import_game_data(file_path, game_num)
            if success:
                total_imported += 1
            else:
                print(f"Failed to import game {game_num}")
        else:
            print(f"Warning: File not found: {file_path}")

    print(f"\nImport complete. Successfully imported {total_imported} game files.")

    # Check results
    conn = psycopg2.connect(
        host='localhost',
        database='fantrax_value_hunter',
        user='fantrax_user',
        password='fantrax_password',
        port=5433
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT game_number, COUNT(DISTINCT player_id) as player_count
        FROM player_game_scores
        GROUP BY game_number
        ORDER BY game_number
    """)

    results = cursor.fetchall()
    print("\nData imported:")
    for game_num, player_count in results:
        print(f"Game {game_num}: {player_count} players")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()