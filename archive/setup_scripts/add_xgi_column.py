#!/usr/bin/env python3

import psycopg2
import sys

# Use the correct database credentials from the Flask app
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'fantrax_user',
    'password': 'fantrax_password',
    'database': 'fantrax_value_hunter'
}

def add_xgi_column():
    try:
        print("Connecting to database with correct credentials...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' AND column_name = 'xgi_multiplier'
        """)
        exists = cursor.fetchone()
        
        if exists:
            print("SUCCESS: xgi_multiplier column already exists!")
        else:
            print("Adding xgi_multiplier column...")
            cursor.execute("ALTER TABLE player_metrics ADD COLUMN xgi_multiplier DECIMAL(5,3) DEFAULT 1.0")
            conn.commit()
            print("SUCCESS: Successfully added xgi_multiplier column!")
        
        # Verify column was added/exists
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' AND column_name = 'xgi_multiplier'
        """)
        column_info = cursor.fetchone()
        
        if column_info:
            print(f"Column details: {column_info[0]} ({column_info[1]}) DEFAULT {column_info[2]}")
        
        cursor.close()
        conn.close()
        print("SUCCESS: Database connection closed successfully")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = add_xgi_column()
    sys.exit(0 if success else 1)