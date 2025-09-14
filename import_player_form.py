#!/usr/bin/env python3
"""
Import Critical Missing Table - player_form
This table is essential for the main app query
"""
import os
import sys
import psycopg2
import psycopg2.extras
import urllib.parse
from datetime import datetime

def get_local_db_config():
    return {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }

def get_railway_db_config():
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        sys.exit(1)

    result = urllib.parse.urlparse(DATABASE_URL)
    return {
        'host': result.hostname,
        'port': result.port,
        'user': result.username,
        'password': result.password,
        'database': result.path[1:]
    }

def format_value_for_sql(value):
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        escaped_value = value.replace("'", "''")
        return f"'{escaped_value}'"
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, datetime):
        return f"'{value.isoformat()}'"
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        str_value = str(value)
        if len(str_value) > 18 and ('T' in str_value or '-' in str_value[:10]):
            return f"'{str_value}'"
        else:
            escaped_value = str_value.replace("'", "''")
            return f"'{escaped_value}'"

def import_player_form():
    print("Importing Critical player_form Table")
    print("=" * 40)

    # Connect to databases
    local_config = get_local_db_config()
    railway_config = get_railway_db_config()

    try:
        local_conn = psycopg2.connect(**local_config)
        railway_conn = psycopg2.connect(**railway_config)
        print("Connected to both databases")
    except Exception as e:
        print(f"Connection error: {e}")
        return False

    try:
        local_cursor = local_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        railway_cursor = railway_conn.cursor()

        # Create player_form table in Railway
        create_sql = """
        CREATE TABLE IF NOT EXISTS player_form (
            player_id VARCHAR(255),
            gameweek INTEGER,
            points NUMERIC,
            timestamp TIMESTAMP,
            imported_at TIMESTAMP
        );
        """

        railway_cursor.execute(create_sql)
        print("Created player_form table")

        # Get data from local
        local_cursor.execute("SELECT * FROM player_form")
        rows = local_cursor.fetchall()

        if not rows:
            print("No data in local player_form table")
            return True

        print(f"Found {len(rows)} rows to import")

        # Import data
        columns = ['player_id', 'gameweek', 'points', 'timestamp', 'imported_at']
        successful = 0

        for i, row in enumerate(rows):
            try:
                values = [format_value_for_sql(row[col]) for col in columns]
                values_str = ', '.join(values)
                columns_str = ', '.join(columns)

                insert_sql = f"INSERT INTO player_form ({columns_str}) VALUES ({values_str});"
                railway_cursor.execute(insert_sql)
                successful += 1

                if (i + 1) % 100 == 0:
                    print(f"Progress: {i + 1}/{len(rows)} rows")

            except Exception as e:
                print(f"Warning: Failed row {i + 1}: {str(e)[:100]}")
                railway_conn.rollback()
                continue

        railway_conn.commit()
        print(f"SUCCESS: {successful} rows imported to player_form")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        railway_conn.rollback()
        return False
    finally:
        local_conn.close()
        railway_conn.close()

if __name__ == "__main__":
    success = import_player_form()
    if success:
        print("\nplayer_form table imported successfully!")
        print("The Railway app should now work correctly.")
    else:
        sys.exit(1)