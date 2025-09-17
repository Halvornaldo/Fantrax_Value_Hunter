#!/usr/bin/env python3
"""
Verify csv_confidence_multiplier column was added successfully
"""

import psycopg2

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def verify_column():
    """Verify csv_confidence_multiplier column exists and has data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'player_metrics'
            AND column_name = 'csv_confidence_multiplier'
        """)

        result = cursor.fetchone()
        if result:
            print(f"[SUCCESS] Column exists: {result[0]} ({result[1]}) DEFAULT {result[2]}")
        else:
            print("[ERROR] Column does not exist!")
            return False

        # Check data
        cursor.execute("""
            SELECT COUNT(*),
                   MIN(csv_confidence_multiplier),
                   MAX(csv_confidence_multiplier),
                   AVG(csv_confidence_multiplier)
            FROM player_metrics
            WHERE csv_confidence_multiplier IS NOT NULL
        """)

        count, min_val, max_val, avg_val = cursor.fetchone()
        print(f"[SUCCESS] Data: {count} rows, range {min_val:.3f}-{max_val:.3f}, avg {avg_val:.3f}")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verify_column()