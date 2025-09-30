#!/usr/bin/env python3
"""
Simple Railway schema fix using connection string from environment variables
"""
import psycopg2
import os

# Railway database connection - try environment first, fallback to default
# Format from Railway variables: postgresql://postgres:PASSWORD@HOST:PORT/railway
database_url = os.getenv('RAILWAY_DATABASE_URL',
                        "postgresql://postgres:PaTNNWrtNvFRYFYppIRjjJoaGSiwmyfg@gondola.proxy.rlwy.net:17291/railway")

print("Connecting to Railway database...")

try:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    print("Adding missing columns to player_metrics...")

    # Add missing columns
    schema_fixes = [
        "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS next_opponent VARCHAR(3);",
        "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS is_home BOOLEAN;",
        "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_multiplier NUMERIC DEFAULT 1.0;",
        "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_percentage NUMERIC;"
    ]

    for sql in schema_fixes:
        print(f"Executing: {sql}")
        cursor.execute(sql)

    conn.commit()

    # Verify columns were added
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'player_metrics'
        AND column_name IN ('next_opponent', 'is_home', 'csv_confidence_multiplier', 'csv_confidence_percentage')
        ORDER BY column_name
    """)

    added_columns = [row[0] for row in cursor.fetchall()]
    print(f"Successfully added columns: {added_columns}")

    cursor.close()
    conn.close()

    print("Railway database schema fix complete!")

except psycopg2.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Error: {e}")