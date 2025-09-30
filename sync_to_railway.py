#!/usr/bin/env python3
"""
Sync local Fantrax database to Railway
Runs after local imports to keep Railway fresh

Usage:
    python sync_to_railway.py                 # Sync all tables
    python sync_to_railway.py --tables players player_metrics  # Sync specific tables
    python sync_to_railway.py --schema-fix    # First run: fix schema + sync data
"""
import psycopg2
import psycopg2.extras
import subprocess
import sys
import argparse
from datetime import datetime
from typing import List, Optional

class RailwayDatabaseSyncer:

    def __init__(self):
        self.local_config = {
            'host': 'localhost',
            'port': 5433,
            'user': 'fantrax_user',
            'password': 'fantrax_password',
            'database': 'fantrax_value_hunter'
        }

        # Get Railway DATABASE_URL
        self.railway_url = self._get_railway_url()

        # Tables to sync (in dependency order)
        self.sync_tables = [
            'players',           # Core player data (referenced by others)
            'team_fixtures',     # Team/fixture data
            'fixture_odds',      # Odds data
            'name_mappings',     # Name mapping data
            'player_games_data', # Games tracking data
            'player_form',       # Player form history
            'player_metrics',    # Main metrics (references players)
        ]

    def _get_railway_url(self) -> str:
        """Get Railway database URL from environment or default"""
        import os

        # Try to get from environment first (production best practice)
        railway_url = os.getenv('RAILWAY_DATABASE_URL')

        if railway_url:
            return railway_url

        # Fallback for local development (friends access)
        # Note: In production, this should be set via environment variables
        return "postgresql://postgres:PaTNNWrtNvFRYFYppIRjjJoaGSiwmyfg@gondola.proxy.rlwy.net:17291/railway"

    def fix_railway_schema(self) -> bool:
        """Add missing columns to Railway database"""
        print("Fixing Railway database schema...")

        try:
            conn = psycopg2.connect(self.railway_url)
            cursor = conn.cursor()

            schema_fixes = [
                "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS next_opponent VARCHAR(3);",
                "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS is_home BOOLEAN;",
                "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_multiplier NUMERIC DEFAULT 1.0;",
                "ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_percentage NUMERIC;"
            ]

            for sql in schema_fixes:
                print(f"  Executing: {sql}")
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
            print(f"Schema fix complete. Added columns: {added_columns}")

            cursor.close()
            conn.close()
            return True

        except psycopg2.Error as e:
            print(f"Database error during schema fix: {e}")
            return False

    def sync_table(self, table_name: str) -> bool:
        """Sync a single table from local to Railway"""
        print(f"  Syncing {table_name}...")

        try:
            # Connect to both databases
            local_conn = psycopg2.connect(**self.local_config)
            railway_conn = psycopg2.connect(self.railway_url)

            local_cursor = local_conn.cursor()
            railway_cursor = railway_conn.cursor()

            # Get data from local database
            local_cursor.execute(f"SELECT * FROM {table_name}")
            data = local_cursor.fetchall()

            if not data:
                print(f"    No data found in local {table_name}")
                return True

            # Get column names
            columns = [desc[0] for desc in local_cursor.description]

            # Clear Railway table and insert new data
            print(f"    Clearing Railway {table_name}...")
            railway_cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")

            # Build and execute insert query
            placeholders = ','.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"

            print(f"    Inserting {len(data)} rows...")
            railway_cursor.executemany(insert_query, data)

            railway_conn.commit()
            print(f"    Successfully synced {len(data)} rows to {table_name}")

            # Close connections
            local_cursor.close()
            local_conn.close()
            railway_cursor.close()
            railway_conn.close()

            return True

        except psycopg2.Error as e:
            print(f"    ERROR syncing {table_name}: {e}")
            return False

    def sync_all_tables(self, specific_tables: Optional[List[str]] = None) -> bool:
        """Sync all tables or specific tables"""
        tables_to_sync = specific_tables or self.sync_tables

        print(f"Starting database sync to Railway - {datetime.now()}")
        print(f"Tables to sync: {', '.join(tables_to_sync)}")

        success_count = 0

        for table in tables_to_sync:
            if self.sync_table(table):
                success_count += 1
            else:
                print(f"  Failed to sync {table}")

        print(f"\nSync complete: {success_count}/{len(tables_to_sync)} tables synced successfully")
        return success_count == len(tables_to_sync)

def main():
    parser = argparse.ArgumentParser(description='Sync local database to Railway')
    parser.add_argument('--schema-fix', action='store_true',
                       help='Fix Railway schema before syncing')
    parser.add_argument('--tables', nargs='+',
                       help='Specific tables to sync (default: all)')

    args = parser.parse_args()

    syncer = RailwayDatabaseSyncer()

    # Fix schema first if requested
    if args.schema_fix:
        if not syncer.fix_railway_schema():
            print("Schema fix failed!")
            sys.exit(1)
        print()

    # Sync tables
    success = syncer.sync_all_tables(args.tables)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()