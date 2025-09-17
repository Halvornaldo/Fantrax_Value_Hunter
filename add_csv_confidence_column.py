#!/usr/bin/env python3
"""
Add csv_confidence_multiplier column to player_metrics table
This stores the original CSV confidence-based multiplier values
"""

import psycopg2
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def add_csv_confidence_column():
    """Add csv_confidence_multiplier column to player_metrics table"""
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'player_metrics'
            AND column_name = 'csv_confidence_multiplier'
        """)

        if cursor.fetchone():
            print("Column csv_confidence_multiplier already exists!")
            return True

        # Add the column
        print("Adding csv_confidence_multiplier column...")
        cursor.execute("""
            ALTER TABLE player_metrics
            ADD COLUMN csv_confidence_multiplier DECIMAL(5,3) DEFAULT 0.35
        """)

        # Initialize with current starter_multiplier values as a baseline
        print("Initializing column with current starter_multiplier values...")
        cursor.execute("""
            UPDATE player_metrics
            SET csv_confidence_multiplier = starter_multiplier
        """)

        rows_updated = cursor.rowcount
        print(f"Initialized {rows_updated} rows with current starter multiplier values")

        # Commit changes
        conn.commit()
        print("✅ Successfully added csv_confidence_multiplier column!")

        # Verify the column was added
        cursor.execute("""
            SELECT COUNT(*)
            FROM player_metrics
            WHERE csv_confidence_multiplier IS NOT NULL
        """)
        count = cursor.fetchone()[0]
        print(f"✅ Verified: {count} players have csv_confidence_multiplier values")

        return True

    except Exception as e:
        print(f"❌ Error adding column: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = add_csv_confidence_column()
    sys.exit(0 if success else 1)