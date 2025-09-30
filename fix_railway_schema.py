#!/usr/bin/env python3
"""
Fix Railway database schema by adding missing columns
"""
import psycopg2
import subprocess
import sys

def fix_railway_schema():
    print("Fixing Railway database schema...")

    try:
        # Get Railway database URL
        result = subprocess.run(['railway', 'run', 'echo', '$DATABASE_URL'],
                              capture_output=True, text=True, check=True)
        database_url = result.stdout.strip()

        print("Connecting to Railway database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Add missing columns to player_metrics table
        schema_fixes = [
            "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS next_opponent VARCHAR(3);",
            "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS is_home BOOLEAN;",
            "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_multiplier NUMERIC DEFAULT 1.0;",
            "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_percentage NUMERIC;"
        ]

        for sql in schema_fixes:
            print(f"  Executing: {sql}")
            cursor.execute(sql)

        conn.commit()

        # Verify the columns were added
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'player_metrics'
            AND column_name IN ('next_opponent', 'is_home', 'csv_confidence_multiplier', 'csv_confidence_percentage')
            ORDER BY column_name
        """)

        added_columns = [row[0] for row in cursor.fetchall()]

        print("Schema fix complete!")
        print(f"Added columns: {', '.join(added_columns)}")

        cursor.close()
        conn.close()

        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to get Railway DATABASE_URL: {e}")
        return False
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = fix_railway_schema()
    sys.exit(0 if success else 1)