#!/usr/bin/env python3
"""
Railway Database Initialization Script - Final Version
Properly handles timestamps and data types for Railway PostgreSQL import
"""
import os
import sys
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional
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

def format_value_for_sql(value):
    """Format a value for SQL insertion with proper quoting and typing"""
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        # Escape single quotes
        escaped_value = value.replace("'", "''")
        return f"'{escaped_value}'"
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, datetime):
        # Format datetime as properly quoted timestamp
        return f"'{value.isoformat()}'"
    elif isinstance(value, (int, float, Decimal)):
        # Numeric values don't need quotes
        return str(value)
    else:
        # For any other type, convert to string and quote
        str_value = str(value)
        # Check if it looks like a timestamp
        if len(str_value) > 18 and ('T' in str_value or '-' in str_value[:10]):
            return f"'{str_value}'"
        else:
            escaped_value = str_value.replace("'", "''")
            return f"'{escaped_value}'"

def initialize_railway_database():
    """Initialize Railway database with schema and data"""
    print("Railway Database Initialization Tool")
    print("=" * 40)
    print("Initializing Railway Database...")

    # Get configurations
    local_config = get_local_db_config()
    railway_config = get_railway_db_config()

    print(f"Local DB: {local_config['host']}:{local_config['port']}")
    print(f"Railway DB: {railway_config['host']}:{railway_config['port']}")

    # Connect to local database
    print("\nConnecting to local database...")
    try:
        local_conn = psycopg2.connect(**local_config)
        print("SUCCESS: Connected to local database")
    except Exception as e:
        print(f"ERROR: Failed to connect to local database: {e}")
        return False

    # Connect to Railway database
    print("Connecting to Railway database...")
    try:
        railway_conn = psycopg2.connect(**railway_config)
        railway_conn.autocommit = False  # Use transactions
        print("SUCCESS: Connected to Railway database")
    except Exception as e:
        print(f"ERROR: Failed to connect to Railway database: {e}")
        return False

    # Tables to migrate (in dependency order)
    tables = [
        'players',
        'player_metrics',
        'player_games_data',
        'team_fixtures',
        'name_mappings'
    ]

    try:
        local_cursor = local_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        railway_cursor = railway_conn.cursor()

        total_rows = 0

        for table in tables:
            print(f"\n--- Processing table: {table} ---")

            # Get table structure from local database
            local_cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default,
                       character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table,))

            columns_info = local_cursor.fetchall()
            if not columns_info:
                print(f"WARNING: Table {table} not found, skipping")
                continue

            # Build CREATE TABLE statement
            create_sql = f"CREATE TABLE IF NOT EXISTS {table} (\n"
            column_defs = []

            for col_info in columns_info:
                col_name = col_info['column_name']
                data_type = col_info['data_type']
                is_nullable = col_info['is_nullable']
                column_default = col_info['column_default']
                max_length = col_info['character_maximum_length']
                precision = col_info['numeric_precision']
                scale = col_info['numeric_scale']

                # Map data types
                if data_type == 'character varying':
                    if max_length:
                        col_def = f"    {col_name} VARCHAR({max_length})"
                    else:
                        col_def = f"    {col_name} TEXT"
                elif data_type == 'numeric':
                    if precision and scale is not None:
                        col_def = f"    {col_name} DECIMAL({precision},{scale})"
                    else:
                        col_def = f"    {col_name} NUMERIC"
                elif data_type == 'integer':
                    col_def = f"    {col_name} INTEGER"
                elif data_type == 'boolean':
                    col_def = f"    {col_name} BOOLEAN"
                elif data_type == 'timestamp without time zone':
                    col_def = f"    {col_name} TIMESTAMP"
                else:
                    col_def = f"    {col_name} {data_type.upper()}"

                if is_nullable == 'NO':
                    col_def += " NOT NULL"

                if column_default and 'nextval' not in str(column_default):
                    if column_default not in ['NULL']:
                        col_def += f" DEFAULT {column_default}"

                column_defs.append(col_def)

            create_sql += ",\n".join(column_defs)
            create_sql += "\n);"

            # Create table
            print(f"Creating table {table}...")
            railway_cursor.execute(create_sql)
            print(f"SUCCESS: Table {table} created")

            # Get data from local table
            local_cursor.execute(f"SELECT * FROM {table}")
            rows = local_cursor.fetchall()

            if rows:
                print(f"Exporting {len(rows)} rows from {table}...")
                columns = [desc[0] for desc in local_cursor.description]

                # Insert data in batches
                batch_size = 100
                successful_inserts = 0

                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]

                    for row in batch:
                        try:
                            # Format values properly
                            values = [format_value_for_sql(row[col]) for col in columns]
                            values_str = ', '.join(values)
                            columns_str = ', '.join(columns)

                            insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({values_str});"
                            railway_cursor.execute(insert_sql)
                            successful_inserts += 1

                        except Exception as e:
                            print(f"Warning: Failed to insert row: {e}")
                            railway_conn.rollback()
                            continue

                print(f"SUCCESS: {successful_inserts} rows imported to {table}")
                total_rows += successful_inserts
            else:
                print(f"WARNING: No data in {table}")

        # Commit all changes
        railway_conn.commit()
        print(f"\nSUCCESS: All changes committed to Railway database")
        print(f"SUCCESS: Total rows imported: {total_rows}")

        # Verify the import
        print("\n--- Verification ---")
        railway_cursor.execute("SELECT COUNT(*) FROM players")
        player_count = railway_cursor.fetchone()[0]
        print(f"Players in Railway database: {player_count}")

        if player_count > 0:
            railway_cursor.execute("SELECT COUNT(*) FROM player_metrics")
            metrics_count = railway_cursor.fetchone()[0]
            print(f"Player metrics in Railway database: {metrics_count}")

        return True

    except Exception as e:
        print(f"\nERROR: Error during initialization: {e}")
        railway_conn.rollback()
        return False
    finally:
        local_conn.close()
        railway_conn.close()

def main():
    """Main execution"""
    success = initialize_railway_database()

    if success:
        print("\nSUCCESS: Railway database initialization completed!")
        print("The dashboard should now show player data at:")
        print("https://fantraxvaluehunter-production.up.railway.app")
    else:
        print("\nERROR: Database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()