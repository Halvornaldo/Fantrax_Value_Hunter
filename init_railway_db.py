#!/usr/bin/env python3
"""
Railway Database Initialization Script
Connects to Railway PostgreSQL and initializes the database with player data
"""
import os
import sys
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional
import urllib.parse

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
        print("Set it with: export DATABASE_URL='your_railway_postgres_url'")
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

def get_table_schema(conn, table_name: str) -> str:
    """Get CREATE TABLE statement for a table"""
    cursor = conn.cursor()

    # Get table columns and types
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    columns = cursor.fetchall()
    if not columns:
        return None

    # Build CREATE TABLE statement
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    column_defs = []

    for col_name, data_type, is_nullable, column_default in columns:
        col_def = f"    {col_name} {data_type.upper()}"

        if data_type == 'character varying':
            cursor.execute("""
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (table_name, col_name))
            max_length = cursor.fetchone()[0]
            if max_length:
                col_def = f"    {col_name} VARCHAR({max_length})"
            else:
                col_def = f"    {col_name} TEXT"
        elif data_type == 'numeric':
            cursor.execute("""
                SELECT numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (table_name, col_name))
            precision, scale = cursor.fetchone()
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

        if is_nullable == 'NO':
            col_def += " NOT NULL"

        if column_default:
            if 'nextval' in column_default:
                col_def = f"    {col_name} SERIAL"
            elif column_default not in ['NULL']:
                col_def += f" DEFAULT {column_default}"

        column_defs.append(col_def)

    create_sql += ",\n".join(column_defs)
    create_sql += "\n);"

    return create_sql

def export_table_data(conn, table_name: str) -> List[str]:
    """Export table data as INSERT statements"""
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(f"No data found in table {table_name}")
            return []

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        insert_statements = []
        for row in rows:
            values = []
            for col in columns:
                value = row[col]
                if value is None:
                    values.append('NULL')
                elif isinstance(value, str):
                    # Escape single quotes
                    escaped_value = value.replace("'", "''")
                    values.append(f"'{escaped_value}'")
                elif isinstance(value, bool):
                    values.append('true' if value else 'false')
                else:
                    values.append(str(value))

            values_str = ', '.join(values)
            columns_str = ', '.join(columns)
            insert_statements.append(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")

        print(f"Exported {len(insert_statements)} rows from {table_name}")
        return insert_statements

    except Exception as e:
        print(f"Error exporting data from {table_name}: {e}")
        return []

def initialize_railway_database():
    """Initialize Railway database with schema and data"""
    print("Initializing Railway Database...")

    # Get configurations
    local_config = get_local_db_config()
    railway_config = get_railway_db_config()

    print(f"Local DB: {local_config['host']}:{local_config['port']}")
    print(f"Railway DB: {railway_config['host']}:{railway_config['port']}")

    # Connect to local database to get schema and data
    print("\nConnecting to local database...")
    try:
        local_conn = psycopg2.connect(**local_config)
        print("✓ Connected to local database")
    except Exception as e:
        print(f"✗ Failed to connect to local database: {e}")
        return False

    # Connect to Railway database
    print("Connecting to Railway database...")
    try:
        railway_conn = psycopg2.connect(**railway_config)
        print("✓ Connected to Railway database")
    except Exception as e:
        print(f"✗ Failed to connect to Railway database: {e}")
        return False

    # Tables to migrate (in dependency order)
    tables = [
        'players',
        'player_metrics',
        'player_games_data',
        'team_fixtures',
        'name_mappings',
        'player_forms'
    ]

    try:
        railway_cursor = railway_conn.cursor()

        for table in tables:
            print(f"\n--- Processing table: {table} ---")

            # Get schema from local database
            schema_sql = get_table_schema(local_conn, table)
            if not schema_sql:
                print(f"⚠ Table {table} not found in local database, skipping")
                continue

            print(f"Creating table {table}...")
            railway_cursor.execute(schema_sql)
            print(f"✓ Table {table} created")

            # Export and import data
            print(f"Exporting data from {table}...")
            insert_statements = export_table_data(local_conn, table)

            if insert_statements:
                print(f"Importing {len(insert_statements)} rows into {table}...")
                for stmt in insert_statements:
                    try:
                        railway_cursor.execute(stmt)
                    except Exception as e:
                        print(f"Warning: Failed to insert row: {e}")
                        # Continue with other rows

                print(f"✓ Data imported to {table}")
            else:
                print(f"⚠ No data to import for {table}")

        # Commit all changes
        railway_conn.commit()
        print("\n✓ All changes committed to Railway database")

        # Verify the import
        print("\n--- Verification ---")
        railway_cursor.execute("SELECT COUNT(*) FROM players")
        player_count = railway_cursor.fetchone()[0]
        print(f"Players in Railway database: {player_count}")

        return True

    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        railway_conn.rollback()
        return False
    finally:
        local_conn.close()
        railway_conn.close()

def main():
    """Main execution"""
    print("Railway Database Initialization Tool")
    print("=" * 40)

    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nTo set it, use your Railway PostgreSQL URL:")
        print("export DATABASE_URL='postgresql://postgres:password@host:port/database'")
        sys.exit(1)

    success = initialize_railway_database()

    if success:
        print("\n🎉 Railway database initialization completed successfully!")
        print("The dashboard should now show player data at:")
        print("https://fantraxvaluehunter-production.up.railway.app")
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()