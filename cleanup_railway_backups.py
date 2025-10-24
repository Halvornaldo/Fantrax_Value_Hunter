#!/usr/bin/env python3
"""
Clean up backup tables from Railway database
Run this once to remove all accumulated backup tables
"""

import psycopg2

railway_config = {
    'host': 'gondola.proxy.rlwy.net',
    'port': 17291,
    'database': 'railway',
    'user': 'postgres',
    'password': 'PaTNNWrtNvFRYFYppIRjjJoaGSiwmyfg'
}

def cleanup_backups():
    """Remove all backup tables from Railway"""
    try:
        conn = psycopg2.connect(**railway_config)
        cur = conn.cursor()

        print("Connected to Railway database")
        print("Looking for backup tables...")

        # Find all backup tables
        cur.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE '%_backup_%'
            ORDER BY tablename
        """)

        backup_tables = cur.fetchall()

        if not backup_tables:
            print("No backup tables found!")
            return

        print(f"\nFound {len(backup_tables)} backup tables:")
        for (table_name,) in backup_tables:
            print(f"  - {table_name}")

        # Confirm deletion
        response = input(f"\nDelete all {len(backup_tables)} backup tables? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled")
            return

        # Delete each backup table
        deleted_count = 0
        for (table_name,) in backup_tables:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                conn.commit()
                deleted_count += 1
                print(f"Deleted: {table_name}")
            except Exception as e:
                print(f"Failed to delete {table_name}: {e}")
                conn.rollback()

        print(f"\n✅ Successfully deleted {deleted_count}/{len(backup_tables)} backup tables")

        # Show remaining tables
        cur.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        all_tables = cur.fetchall()
        print(f"\nRemaining tables in Railway ({len(all_tables)} total):")
        for (table_name,) in all_tables:
            if '_backup_' not in table_name:
                print(f"  - {table_name}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    cleanup_backups()