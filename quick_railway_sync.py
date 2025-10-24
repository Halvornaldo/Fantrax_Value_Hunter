#!/usr/bin/env python3
"""
Quick Database Sync - Essential tables only
Syncs only the critical tables needed for the dashboard
"""
import os
import sys
import psycopg2
import psycopg2.extras
import urllib.parse
from datetime import datetime
from decimal import Decimal

def get_local_db_config():
    """Get local database configuration"""
    return {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }

def get_railway_db_config():
    """Get Railway database configuration from environment"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Parse Railway DATABASE_URL
    result = urllib.parse.urlparse(DATABASE_URL)
    return {
        'host': result.hostname,
        'port': result.port,
        'user': result.username,
        'password': result.password,
        'database': result.path[1:]  # Remove leading slash
    }

def sync_essential_tables():
    """Sync only essential tables for dashboard operation"""

    # Essential tables in priority order
    essential_tables = [
        'players',
        'player_metrics',
        'team_metrics',
        'player_games_data',
        'name_mappings',
        'understat_name_mappings'
    ]

    try:
        # Connect to both databases
        local_conn = psycopg2.connect(**get_local_db_config())
        railway_conn = psycopg2.connect(**get_railway_db_config())

        local_cur = local_conn.cursor()
        railway_cur = railway_conn.cursor()

        print("Quick Sync - Essential Tables Only")
        print("=" * 50)
        print(f"Local DB: {get_local_db_config()['host']}:{get_local_db_config()['port']}")
        print(f"Railway DB: {get_railway_db_config()['host']}:{get_railway_db_config()['port']}")
        print()

        for table_name in essential_tables:
            print(f"\n--- Syncing {table_name} ---")

            # Check if table exists locally
            local_cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table_name,))

            if not local_cur.fetchone()[0]:
                print(f"  Table {table_name} not found locally, skipping...")
                continue

            # Get table structure from local
            local_cur.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = local_cur.fetchall()

            # Check if table exists on Railway
            railway_cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table_name,))

            if railway_cur.fetchone()[0]:
                # Table exists, truncate it
                print(f"  Clearing existing data in {table_name}...")
                railway_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
                railway_conn.commit()
            else:
                # Create table structure
                print(f"  Creating table {table_name}...")
                local_cur.execute(f"""
                    SELECT pg_get_tabledef('{table_name}'::regclass::oid)
                """)
                create_sql = local_cur.fetchone()[0]

                # Use alternative method if pg_get_tabledef doesn't exist
                if not create_sql:
                    local_cur.execute(f"""
                        SELECT
                            'CREATE TABLE ' || '{table_name}' || ' (' ||
                            string_agg(
                                column_name || ' ' ||
                                data_type ||
                                CASE WHEN character_maximum_length IS NOT NULL
                                    THEN '(' || character_maximum_length || ')'
                                    ELSE ''
                                END ||
                                CASE WHEN is_nullable = 'NO'
                                    THEN ' NOT NULL'
                                    ELSE ''
                                END ||
                                CASE WHEN column_default IS NOT NULL
                                    THEN ' DEFAULT ' || column_default
                                    ELSE ''
                                END,
                                ', '
                            ) || ');'
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)
                    create_sql = local_cur.fetchone()[0]

                if create_sql:
                    railway_cur.execute(create_sql)
                    railway_conn.commit()

            # Copy data
            print(f"  Copying data from {table_name}...")
            local_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = local_cur.fetchone()[0]

            if total_rows > 0:
                print(f"    Total rows to copy: {total_rows}")

                # Use COPY for faster transfer
                local_cur.execute(f"SELECT * FROM {table_name}")

                # Get column names
                col_names = [desc[0] for desc in local_cur.description]

                # Fetch in batches
                batch_size = 1000
                copied = 0

                while True:
                    rows = local_cur.fetchmany(batch_size)
                    if not rows:
                        break

                    # Use execute_values for batch insert
                    template = f"INSERT INTO {table_name} ({','.join(col_names)}) VALUES %s"
                    psycopg2.extras.execute_values(railway_cur, template, rows)

                    copied += len(rows)
                    print(f"    Progress: {copied}/{total_rows} rows")

                    railway_conn.commit()

                print(f"  SUCCESS: {copied} rows copied to {table_name}")
            else:
                print(f"  No data to copy for {table_name}")

        # Final verification
        print("\n" + "=" * 50)
        print("VERIFICATION:")
        for table_name in essential_tables:
            railway_cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table_name,))

            if railway_cur.fetchone()[0]:
                railway_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = railway_cur.fetchone()[0]
                print(f"  {table_name}: {count} rows")
            else:
                print(f"  {table_name}: NOT CREATED")

        print("\nSync completed successfully!")

        # Close connections
        local_conn.close()
        railway_conn.close()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sync_essential_tables()