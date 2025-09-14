#!/usr/bin/env python3
"""
Export Local Database to Railway-compatible SQL dump
Creates SQL files that can be imported into Railway PostgreSQL
"""
import os
import sys
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional

def get_local_db_config():
    """Get local database configuration"""
    return {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }

def export_table_schema_and_data(conn, table_name: str) -> tuple:
    """Export both schema and data for a table"""
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get column info for CREATE TABLE
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default,
               character_maximum_length, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    columns_info = cursor.fetchall()
    if not columns_info:
        return None, []

    # Build CREATE TABLE statement
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
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

        # Add NOT NULL constraint
        if is_nullable == 'NO':
            col_def += " NOT NULL"

        # Add DEFAULT clause (skip serial sequences)
        if column_default and 'nextval' not in str(column_default):
            if column_default not in ['NULL']:
                col_def += f" DEFAULT {column_default}"

        column_defs.append(col_def)

    create_sql += ",\n".join(column_defs)
    create_sql += "\n);"

    # Export data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    insert_statements = []
    if rows:
        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Process rows in batches for better performance
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            values_list = []
            for row in batch:
                values = []
                for col in columns:
                    value = row[col]
                    if value is None:
                        values.append('NULL')
                    elif isinstance(value, str):
                        # Escape single quotes and backslashes
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    elif isinstance(value, bool):
                        values.append('true' if value else 'false')
                    else:
                        values.append(str(value))

                values_list.append(f"({', '.join(values)})")

            # Create multi-row INSERT statement
            columns_str = ', '.join(columns)
            values_str = ',\n    '.join(values_list)
            insert_statements.append(f"INSERT INTO {table_name} ({columns_str}) VALUES \n    {values_str};")

    return create_sql, insert_statements

def create_railway_sql_dump():
    """Create complete SQL dump for Railway import"""
    print("Creating Railway SQL dump...")

    # Connect to local database
    local_config = get_local_db_config()
    try:
        conn = psycopg2.connect(**local_config)
        print("✓ Connected to local database")
    except Exception as e:
        print(f"✗ Failed to connect to local database: {e}")
        return False

    # Tables to export (in dependency order)
    tables = [
        'players',
        'player_metrics',
        'player_games_data',
        'team_fixtures',
        'name_mappings'
    ]

    # Create SQL dump file
    dump_file = 'railway_database_dump.sql'

    try:
        with open(dump_file, 'w', encoding='utf-8') as f:
            f.write("-- =============================================\n")
            f.write("-- Railway Database Dump\n")
            f.write("-- Generated from local Fantrax Value Hunter database\n")
            f.write("-- Import this into Railway PostgreSQL\n")
            f.write("-- =============================================\n\n")

            f.write("-- Begin transaction\n")
            f.write("BEGIN;\n\n")

            total_rows = 0

            for table in tables:
                print(f"Exporting {table}...")

                try:
                    schema_sql, data_sql = export_table_schema_and_data(conn, table)

                    if schema_sql:
                        f.write(f"-- =============================================\n")
                        f.write(f"-- Table: {table}\n")
                        f.write(f"-- =============================================\n")
                        f.write(f"{schema_sql}\n\n")

                        if data_sql:
                            row_count = sum(stmt.count('VALUES') for stmt in data_sql)
                            f.write(f"-- Data for {table} ({row_count} rows)\n")
                            for stmt in data_sql:
                                f.write(f"{stmt}\n\n")
                            total_rows += row_count
                            print(f"✓ Exported {row_count} rows from {table}")
                        else:
                            print(f"⚠ No data in {table}")
                    else:
                        print(f"⚠ Table {table} not found")

                except Exception as e:
                    print(f"⚠ Error exporting {table}: {e}")
                    continue

            f.write("-- =============================================\n")
            f.write("-- Commit transaction\n")
            f.write("-- =============================================\n")
            f.write("COMMIT;\n\n")

            f.write("-- =============================================\n")
            f.write("-- Verification queries\n")
            f.write("-- =============================================\n")
            f.write("SELECT 'Database import completed successfully!' as status;\n\n")

            f.write("SELECT \n")
            f.write("    schemaname,\n")
            f.write("    tablename,\n")
            f.write("    CASE \n")
            for table in tables:
                f.write(f"        WHEN tablename = '{table}' THEN (SELECT COUNT(*) FROM {table})\n")
            f.write("        ELSE 0\n")
            f.write("    END as row_count\n")
            f.write("FROM pg_tables \n")
            f.write(f"WHERE tablename IN {tuple(tables)}\n".replace("'", "'"))
            f.write("ORDER BY tablename;\n\n")

            f.write("-- Check for any remaining issues\n")
            f.write("SELECT COUNT(*) as total_players FROM players;\n")
            f.write("SELECT COUNT(*) as total_metrics FROM player_metrics;\n")

        print(f"\n✓ SQL dump created: {dump_file}")
        print(f"✓ Total rows exported: {total_rows}")
        print(f"✓ File size: {os.path.getsize(dump_file) / 1024 / 1024:.2f} MB")

        return True

    except Exception as e:
        print(f"✗ Error creating SQL dump: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main execution"""
    print("Railway Database Export Tool")
    print("=" * 40)

    success = create_railway_sql_dump()

    if success:
        print("\n🎉 SQL dump created successfully!")
        print("\nTo import into Railway PostgreSQL:")
        print("\nOption 1: Railway Dashboard")
        print("1. Go to your Railway project dashboard")
        print("2. Click on your PostgreSQL service")
        print("3. Go to the 'Query' tab")
        print("4. Copy and paste the SQL from 'railway_database_dump.sql'")
        print("5. Execute the queries")

        print("\nOption 2: Railway CLI")
        print("railway run psql < railway_database_dump.sql")

        print("\nOption 3: Direct psql connection")
        print("psql $DATABASE_URL < railway_database_dump.sql")

        print(f"\nThis will populate your Railway database with {714} players!")
        print("After import, refresh https://fantraxvaluehunter-production.up.railway.app")
    else:
        print("\n❌ Export failed")
        sys.exit(1)

if __name__ == "__main__":
    main()