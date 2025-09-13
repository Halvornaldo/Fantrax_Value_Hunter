#!/usr/bin/env python3
"""
Run database migration to add games columns
"""
import psycopg2

def run_migration():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='fantrax_user',
            password='fantrax_password',
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        print("Running migration: add_games_columns.sql")
        
        # Read and execute migration
        with open('migrations/add_games_columns.sql', 'r') as f:
            migration_sql = f.read()
        
        cursor.execute(migration_sql)
        conn.commit()
        
        print("Migration completed successfully!")
        print("\nNew columns added:")
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' 
                AND column_name IN ('total_points', 'games_played', 'total_points_historical', 'games_played_historical', 'data_source')
            ORDER BY column_name
        """)
        
        for row in cursor.fetchall():
            print(f"  - {row[0]:<30} {row[1]:<15} (default: {row[2] or 'None'})")
        
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()