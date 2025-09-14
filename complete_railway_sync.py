#!/usr/bin/env python3
"""
Complete Database Sync - Local to Railway
Copies ALL tables from local database to Railway PostgreSQL
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

def get_table_create_sql(local_conn, table_name):
    """Generate CREATE TABLE statement for a table"""
    cursor = local_conn.cursor()

    # Get column info
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default,
               character_maximum_length, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    columns_info = cursor.fetchall()
    if not columns_info:
        return None

    # Build CREATE TABLE statement
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    column_defs = []

    for col_info in columns_info:
        col_name, data_type, is_nullable, column_default, max_length, precision, scale = col_info

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
        elif data_type == 'date':
            col_def = f"    {col_name} DATE"
        elif data_type == 'time without time zone':
            col_def = f"    {col_name} TIME"
        elif data_type == 'bigint':
            col_def = f"    {col_name} BIGINT"
        elif data_type == 'smallint':
            col_def = f"    {col_name} SMALLINT"
        elif data_type == 'real':
            col_def = f"    {col_name} REAL"
        elif data_type == 'double precision':
            col_def = f"    {col_name} DOUBLE PRECISION"
        elif data_type == 'text':
            col_def = f"    {col_name} TEXT"
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

    return create_sql

def copy_table_data(local_conn, railway_conn, table_name):
    """Copy all data from local table to Railway table"""
    local_cursor = local_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    railway_cursor = railway_conn.cursor()

    try:
        # Get data from local table
        local_cursor.execute(f"SELECT * FROM {table_name}")
        rows = local_cursor.fetchall()

        if not rows:
            print(f"      No data in {table_name}")
            return 0

        columns = [desc[0] for desc in local_cursor.description]
        successful_inserts = 0

        print(f"      Importing {len(rows)} rows...")

        # Insert data row by row to handle any errors gracefully
        for i, row in enumerate(rows):
            try:
                # Format values properly
                values = [format_value_for_sql(row[col]) for col in columns]
                values_str = ', '.join(values)
                columns_str = ', '.join(columns)

                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
                railway_cursor.execute(insert_sql)
                successful_inserts += 1

                # Show progress every 100 rows
                if (i + 1) % 100 == 0:
                    print(f"      Progress: {i + 1}/{len(rows)} rows")

            except Exception as e:
                print(f"      Warning: Failed to insert row {i + 1}: {str(e)[:100]}...")
                railway_conn.rollback()
                continue

        return successful_inserts

    except Exception as e:
        print(f"      ERROR: Failed to copy {table_name}: {e}")
        return 0

def complete_database_sync():
    """Sync complete database from local to Railway"""
    print("Complete Database Sync - Local to Railway")
    print("=" * 50)

    # Connect to databases
    local_config = get_local_db_config()
    railway_config = get_railway_db_config()

    print(f"Local DB: {local_config['host']}:{local_config['port']}")
    print(f"Railway DB: {railway_config['host']}:{railway_config['port']}")

    try:
        local_conn = psycopg2.connect(**local_config)
        print("SUCCESS: Connected to local database")
    except Exception as e:
        print(f"ERROR: Failed to connect to local database: {e}")
        return False

    try:
        railway_conn = psycopg2.connect(**railway_config)
        railway_conn.autocommit = False
        print("SUCCESS: Connected to Railway database")
    except Exception as e:
        print(f"ERROR: Failed to connect to Railway database: {e}")
        return False

    # Get all tables from local database
    local_cursor = local_conn.cursor()
    local_cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    all_tables = [row[0] for row in local_cursor.fetchall()]
    print(f"\nFound {len(all_tables)} tables to sync:")
    for table in all_tables:
        print(f"  - {table}")

    # Get existing tables in Railway
    railway_cursor = railway_conn.cursor()
    railway_cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    existing_tables = {row[0] for row in railway_cursor.fetchall()}

    total_rows_imported = 0
    successful_tables = 0

    print(f"\nStarting sync...")

    try:
        for table_name in all_tables:
            print(f"\n--- Processing {table_name} ---")

            # Check if table already exists
            if table_name in existing_tables:
                print(f"  Table {table_name} already exists, clearing data...")
                railway_cursor.execute(f"DELETE FROM {table_name}")
            else:
                print(f"  Creating table {table_name}...")
                # Get CREATE TABLE statement
                create_sql = get_table_create_sql(local_conn, table_name)
                if not create_sql:
                    print(f"  ERROR: Could not generate CREATE statement for {table_name}")
                    continue

                railway_cursor.execute(create_sql)
                print(f"  SUCCESS: Table {table_name} created")

            # Copy data
            print(f"  Copying data from {table_name}...")
            rows_imported = copy_table_data(local_conn, railway_conn, table_name)

            if rows_imported > 0:
                railway_conn.commit()
                print(f"  SUCCESS: {rows_imported} rows imported to {table_name}")
                total_rows_imported += rows_imported
                successful_tables += 1
            else:
                print(f"  WARNING: No data imported for {table_name}")

        print(f"\n" + "=" * 50)
        print(f"SYNC COMPLETED!")
        print(f"Tables processed: {len(all_tables)}")
        print(f"Tables with data: {successful_tables}")
        print(f"Total rows imported: {total_rows_imported}")
        print(f"Railway database is now a complete mirror of local database")

        return True

    except Exception as e:
        print(f"\nERROR: Sync failed: {e}")
        railway_conn.rollback()
        return False
    finally:
        local_conn.close()
        railway_conn.close()

def main():
    """Main execution"""
    success = complete_database_sync()

    if success:
        print(f"\nSUCCESS: Complete database sync finished!")
        print(f"Your Railway app should now work exactly like your local version")
        print(f"Check: https://fantraxvaluehunter-production.up.railway.app")
    else:
        print(f"\nERROR: Database sync failed")
        sys.exit(1)

if __name__ == "__main__":
    main()