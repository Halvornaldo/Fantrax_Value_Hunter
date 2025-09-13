#!/usr/bin/env python3
"""
Run v2.0 database migration for Fantasy Football Value Hunter
"""

import psycopg2
import sys
import os

def run_migration():
    """Execute the v2.0 migration SQL"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user', 
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }
    
    # Read migration SQL
    migration_file = os.path.join('migrations', 'v2_formula_migration.sql')
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
    except Exception as e:
        print(f"Error reading migration file: {e}")
        return False
    
    # Connect and execute migration
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()
        
        print("Starting v2.0 database migration...")
        
        # Execute migration SQL
        cursor.execute(migration_sql)
        
        # Verify new columns were created
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' 
            AND column_name IN ('true_value', 'roi', 'blended_ppg', 'exponential_form_score')
        """)
        
        new_columns = [row[0] for row in cursor.fetchall()]
        
        # Verify new tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('player_predictions', 'validation_results', 'form_scores')
        """)
        
        new_tables = [row[0] for row in cursor.fetchall()]
        
        # Check player count
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        
        conn.commit()
        
        print("Migration completed successfully!")
        print(f"New columns added: {new_columns}")
        print(f"New tables created: {new_tables}")
        print(f"Players in database: {player_count}")
        
        return True
        
    except Exception as e:
        print(f"Migration error: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\nv2.0 Database migration completed!")
    else:
        print("\nMigration failed!")
        sys.exit(1)