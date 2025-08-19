#!/usr/bin/env python3

import psycopg2
import sys

# Try different connection configurations
configs = [
    {'host': 'localhost', 'database': 'fantrax_value_hunter', 'user': 'postgres', 'password': 'postgres', 'port': 5433},
    {'host': 'localhost', 'database': 'fantrax_value_hunter', 'user': 'postgres', 'password': 'password', 'port': 5433},
    {'host': 'localhost', 'database': 'fantrax_value_hunter', 'user': 'halvo', 'password': '', 'port': 5433},
]

for i, config in enumerate(configs):
    try:
        print(f"Trying connection config {i+1}...")
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player_metrics' AND column_name = 'xgi_multiplier'
        """)
        exists = cursor.fetchone()
        
        if exists:
            print("xgi_multiplier column already exists!")
        else:
            print("Adding xgi_multiplier column...")
            cursor.execute("ALTER TABLE player_metrics ADD COLUMN xgi_multiplier DECIMAL(5,3) DEFAULT 1.0")
            conn.commit()
            print("Successfully added xgi_multiplier column!")
        
        cursor.close()
        conn.close()
        sys.exit(0)
        
    except Exception as e:
        print(f"Config {i+1} failed: {e}")
        continue

print("All connection attempts failed!")