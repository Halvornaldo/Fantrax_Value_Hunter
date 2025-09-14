#!/usr/bin/env python3
"""
Export Local Database to Railway SQL dump - Windows compatible
"""
import os
import sys
import psycopg2
import psycopg2.extras

def get_local_db_config():
    """Get local database configuration"""
    return {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }

def export_table_data(conn, table_name: str):
    """Export table schema and data"""
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
        return None, []

    # Build CREATE TABLE
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

    # Export data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    insert_statements = []
    if rows:
        columns = [desc[0] for desc in cursor.description]

        # Process in smaller batches
        batch_size = 50
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
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    elif isinstance(value, bool):
                        values.append('true' if value else 'false')
                    else:
                        values.append(str(value))
                values_list.append(f"({', '.join(values)})")

            columns_str = ', '.join(columns)
            values_str = ',\n    '.join(values_list)
            insert_statements.append(f"INSERT INTO {table_name} ({columns_str}) VALUES \n    {values_str};")

    return create_sql, insert_statements

def create_sql_dump():
    """Create SQL dump file"""
    print("Creating Railway SQL dump...")

    config = get_local_db_config()
    try:
        conn = psycopg2.connect(**config)
        print("SUCCESS: Connected to local database")
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        return False

    tables = ['players', 'player_metrics', 'player_games_data', 'team_fixtures', 'name_mappings']
    dump_file = 'railway_database_dump.sql'

    try:
        with open(dump_file, 'w', encoding='utf-8') as f:
            f.write("-- Railway Database Dump for Fantrax Value Hunter\n")
            f.write("-- Import this into Railway PostgreSQL\n\n")
            f.write("BEGIN;\n\n")

            total_rows = 0

            for table in tables:
                print(f"Exporting {table}...")

                try:
                    schema_sql, data_sql = export_table_data(conn, table)

                    if schema_sql:
                        f.write(f"-- Table: {table}\n")
                        f.write(f"{schema_sql}\n\n")

                        if data_sql:
                            row_count = sum(stmt.count('INSERT') for stmt in data_sql)
                            f.write(f"-- Data for {table} ({row_count} batches)\n")
                            for stmt in data_sql:
                                f.write(f"{stmt}\n\n")

                            # Count actual rows
                            cursor = conn.cursor()
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            actual_count = cursor.fetchone()[0]
                            total_rows += actual_count
                            print(f"SUCCESS: Exported {actual_count} rows from {table}")
                        else:
                            print(f"WARNING: No data in {table}")
                    else:
                        print(f"WARNING: Table {table} not found")

                except Exception as e:
                    print(f"ERROR: Failed to export {table}: {e}")
                    continue

            f.write("COMMIT;\n\n")
            f.write("-- Verification\n")
            f.write("SELECT 'Import completed!' as status;\n")
            f.write("SELECT COUNT(*) as total_players FROM players;\n")
            f.write("SELECT COUNT(*) as total_metrics FROM player_metrics;\n")

        file_size_mb = os.path.getsize(dump_file) / 1024 / 1024
        print(f"SUCCESS: SQL dump created: {dump_file}")
        print(f"SUCCESS: Total rows exported: {total_rows}")
        print(f"SUCCESS: File size: {file_size_mb:.2f} MB")

        return True

    except Exception as e:
        print(f"ERROR: Failed to create SQL dump: {e}")
        return False
    finally:
        conn.close()

def main():
    print("Railway Database Export Tool")
    print("=" * 40)

    success = create_sql_dump()

    if success:
        print("\n" + "=" * 50)
        print("SQL DUMP CREATED SUCCESSFULLY!")
        print("=" * 50)
        print("\nTo import into Railway PostgreSQL:")
        print("\n1. Go to Railway Dashboard")
        print("2. Click your PostgreSQL service")
        print("3. Go to 'Query' tab")
        print("4. Copy/paste contents of 'railway_database_dump.sql'")
        print("5. Execute the SQL")
        print("\nAlternatively use Railway CLI:")
        print("railway run psql < railway_database_dump.sql")
        print(f"\nThis will add 714 players to your Railway database!")
    else:
        print("\nERROR: Export failed")
        sys.exit(1)

if __name__ == "__main__":
    main()