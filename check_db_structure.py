#!/usr/bin/env python3
"""
Check current database structure to avoid duplicate data imports
"""
import psycopg2

def check_database_structure():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='fantrax_user',
            password='fantrax_password',
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        print("=== CURRENT PLAYER_METRICS TABLE STRUCTURE ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' 
            ORDER BY ordinal_position
        """)
        
        for row in cursor.fetchall():
            print(f"  {row[0]:<25} {row[1]:<15} {row[2]:<10} {row[3] or 'None'}")
        
        print("\n=== SAMPLE DATA FROM PLAYER_METRICS ===")
        cursor.execute("""
            SELECT COUNT(*) as total_records, 
                   COUNT(DISTINCT gameweek) as gameweeks,
                   MIN(gameweek) as min_gw, 
                   MAX(gameweek) as max_gw
            FROM player_metrics
        """)
        
        total, gws, min_gw, max_gw = cursor.fetchone()
        print(f"Total records: {total}")
        print(f"Gameweeks: {gws} (range: {min_gw} to {max_gw})")
        
        print("\n=== CHECK FOR EXISTING GAMES DATA ===")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' 
                AND column_name ILIKE '%game%'
        """)
        
        games_columns = cursor.fetchall()
        if games_columns:
            print("Found games-related columns:")
            for col in games_columns:
                print(f"  - {col[0]}")
        else:
            print("No games-related columns found")
        
        print("\n=== CHECK FOR HISTORICAL DATA ===")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' 
                AND (column_name ILIKE '%historical%' OR column_name ILIKE '%2024%')
        """)
        
        hist_columns = cursor.fetchall()
        if hist_columns:
            print("Found historical data columns:")
            for col in hist_columns:
                print(f"  - {col[0]}")
        else:
            print("No historical data columns found")
            
        print("\n=== SAMPLE PLAYER DATA ===")
        cursor.execute("""
            SELECT name, ppg, price, value_score, gameweek
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE gameweek = 1
            ORDER BY value_score DESC
            LIMIT 5
        """)
        
        print("Top 5 players by PP$ (value_score):")
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} PPG:{row[1]:<6} Price:{row[2]:<6} PP$:{row[3]:<6} GW:{row[4]}")
        
        conn.close()
        print("\n✅ Database connection successful")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database_structure()