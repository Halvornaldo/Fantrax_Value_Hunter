#!/usr/bin/env python3
"""
Safe Railway Database Sync with Backup and Progress Tracking
Syncs essential tables from local to Railway with proper error handling
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import time

# Essential tables needed for dashboard functionality
ESSENTIAL_TABLES = [
    # Core tables (existing on Railway - will be updated)
    'players',                # Core player data
    'player_metrics',         # Live performance metrics
    'player_games_data',      # Games tracking for blending
    'team_metrics',          # NPxG team data
    'name_mappings',         # Player name resolution
    'player_form',           # Form calculations
    'player_game_scores',    # Historical scores
    'team_fixtures',         # Upcoming fixtures
    'understat_name_mappings', # xGI mappings
    'raw_player_snapshots',  # Historical snapshots
    'raw_form_snapshots',    # Form history
    'raw_fixture_snapshots', # Fixture history
    'clean_player_game_scores', # Clean game data
    'fixture_odds',          # Legacy fixture data

    # New tables with data (will be created if needed)
    'verified_name_mappings', # Verified player mappings
    'raw_data_complete',     # Complete raw data
]

class SafeRailwaySync:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.local_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'fantrax_value_hunter',
            'user': 'fantrax_user',
            'password': 'fantrax_password'
        }
        self.railway_config = {
            'host': 'gondola.proxy.rlwy.net',
            'port': 17291,
            'database': 'railway',
            'user': 'postgres',
            'password': 'PaTNNWrtNvFRYFYppIRjjJoaGSiwmyfg'
        }
        self.sync_results = {}

    def report_progress(self, table, status, message="", rows_synced=0, total_rows=0):
        """Report progress to callback if available"""
        progress_data = {
            'table': table,
            'status': status,  # 'starting', 'backing_up', 'syncing', 'success', 'error'
            'message': message,
            'rows_synced': rows_synced,
            'total_rows': total_rows,
            'timestamp': datetime.now().isoformat()
        }

        # Store result
        if table not in self.sync_results:
            self.sync_results[table] = {}
        self.sync_results[table].update(progress_data)

        # Call progress callback if provided
        if self.progress_callback:
            self.progress_callback(progress_data)
        else:
            # Print to console if no callback
            if status == 'error':
                print(f"ERROR [{table}]: {message}")
            else:
                print(f"[{table}] {status}: {message} ({rows_synced}/{total_rows} rows)")

    def create_backup(self, railway_conn, table_name):
        """Create a backup of the table before modifying"""
        railway_cur = railway_conn.cursor()
        backup_name = f"{table_name}_backup_{int(time.time())}"

        try:
            # Check if table exists
            railway_cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))

            if railway_cur.fetchone()[0] == 0:
                # Table doesn't exist, no need to backup
                return None

            # Create backup table
            railway_cur.execute(f"""
                CREATE TABLE {backup_name} AS
                SELECT * FROM {table_name}
            """)
            railway_conn.commit()

            railway_cur.close()
            return backup_name

        except Exception as e:
            railway_conn.rollback()
            railway_cur.close()
            raise Exception(f"Failed to create backup: {e}")

    def sync_table_safe(self, local_conn, railway_conn, table_name):
        """Sync a single table with proper transaction handling"""
        local_cur = local_conn.cursor()
        railway_cur = railway_conn.cursor()

        try:
            self.report_progress(table_name, 'starting', 'Checking local table...')

            # Check if table exists locally
            local_cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            if local_cur.fetchone()[0] == 0:
                self.report_progress(table_name, 'error', f'Table does not exist locally')
                return False

            # Get total row count
            local_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = local_cur.fetchone()[0]

            if total_rows == 0:
                self.report_progress(table_name, 'success', 'No data to sync', 0, 0)
                return True

            self.report_progress(table_name, 'backing_up', f'Creating backup...', 0, total_rows)

            # Create backup on Railway
            backup_name = self.create_backup(railway_conn, table_name)

            # Get table structure from local
            local_cur.execute(f"""
                SELECT column_name, data_type, character_maximum_length,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = local_cur.fetchall()

            # Get primary key columns (needed for ON CONFLICT clause)
            # Initialize pk_columns as empty list first to avoid undefined variable error
            pk_columns = []
            try:
                local_cur.execute(f"""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_name = %s
                """, (table_name,))
                pk_columns = [row[0] for row in local_cur.fetchall()]
            except Exception as e:
                # If we can't get primary keys, continue without them
                self.report_progress(table_name, 'syncing',
                    f'Could not detect primary keys: {str(e)[:100]}', 0, total_rows)

            # Check if table exists on Railway
            railway_cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            table_exists = railway_cur.fetchone()[0] > 0

            if table_exists:
                # Clear existing data
                self.report_progress(table_name, 'syncing', 'Clearing existing data...', 0, total_rows)
                railway_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
                railway_conn.commit()
            else:
                # Create table structure
                self.report_progress(table_name, 'syncing', 'Creating table...', 0, total_rows)

                col_defs = []
                for col in columns:
                    col_def = f'"{col[0]}" {col[1]}'
                    if col[1] == 'character varying' and col[2]:
                        col_def += f'({col[2]})'
                    if col[3] == 'NO':
                        col_def += ' NOT NULL'
                    if col[4]:
                        col_def += f' DEFAULT {col[4]}'
                    col_defs.append(col_def)

                create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
                railway_cur.execute(create_sql)

                # Create primary key if exists
                if pk_columns:
                    railway_cur.execute(f"""
                        ALTER TABLE {table_name}
                        ADD PRIMARY KEY ({', '.join([f'"{col}"' for col in pk_columns])})
                    """)

                railway_conn.commit()

            # Copy data with individual row commits
            self.report_progress(table_name, 'syncing', 'Copying data...', 0, total_rows)

            col_names = [col[0] for col in columns]
            col_names_str = ', '.join([f'"{col}"' for col in col_names])
            placeholders = ', '.join(['%s'] * len(col_names))

            # Use ON CONFLICT for tables with primary keys
            insert_sql = f"""
                INSERT INTO {table_name} ({col_names_str})
                VALUES ({placeholders})
            """

            # Check if table has primary key for ON CONFLICT clause
            if pk_columns and table_name == 'player_game_scores':
                # Special handling for player_game_scores with ON CONFLICT
                pk_conflict = ', '.join([f'"{col}"' for col in pk_columns])
                insert_sql = f"""
                    INSERT INTO {table_name} ({col_names_str})
                    VALUES ({placeholders})
                    ON CONFLICT ({pk_conflict}) DO NOTHING
                """

            # Fetch and insert in smaller batches with individual commits
            batch_size = 100
            offset = 0
            rows_synced = 0
            errors_count = 0

            while offset < total_rows:
                local_cur.execute(f"""
                    SELECT {col_names_str}
                    FROM {table_name}
                    ORDER BY 1
                    LIMIT {batch_size} OFFSET {offset}
                """)
                rows = local_cur.fetchall()

                if not rows:
                    break

                for row in rows:
                    try:
                        railway_cur.execute(insert_sql, row)
                        railway_conn.commit()  # Commit each row immediately
                        rows_synced += 1
                    except psycopg2.IntegrityError as e:
                        # Handle duplicate key or other integrity errors
                        railway_conn.rollback()
                        errors_count += 1
                        if errors_count <= 5:  # Only log first 5 errors
                            self.report_progress(table_name, 'syncing',
                                f'Skipped duplicate row: {str(e)[:100]}',
                                rows_synced, total_rows)
                    except Exception as e:
                        # For other errors, try to continue
                        railway_conn.rollback()
                        errors_count += 1
                        if errors_count <= 5:
                            self.report_progress(table_name, 'syncing',
                                f'Error on row: {str(e)[:100]}',
                                rows_synced, total_rows)

                offset += batch_size

                # Report progress every batch
                if rows_synced % 500 == 0 or rows_synced == total_rows:
                    self.report_progress(table_name, 'syncing',
                        f'Progress: {rows_synced}/{total_rows} rows',
                        rows_synced, total_rows)

            # Verify sync
            railway_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            actual_count = railway_cur.fetchone()[0]

            if actual_count == 0 and total_rows > 0:
                # Sync failed, restore backup if exists
                if backup_name:
                    railway_cur.execute(f"""
                        INSERT INTO {table_name}
                        SELECT * FROM {backup_name}
                    """)
                    railway_conn.commit()
                    railway_cur.execute(f"DROP TABLE IF EXISTS {backup_name}")
                    railway_conn.commit()

                self.report_progress(table_name, 'error',
                    f'Sync failed - no data inserted. Restored backup.', 0, total_rows)
                return False

            # Clean up backup on success
            if backup_name:
                railway_cur.execute(f"DROP TABLE IF EXISTS {backup_name}")
                railway_conn.commit()

            success_msg = f'Successfully synced {actual_count} rows'
            if errors_count > 0:
                success_msg += f' ({errors_count} rows skipped)'

            self.report_progress(table_name, 'success', success_msg, actual_count, total_rows)
            return True

        except Exception as e:
            railway_conn.rollback()
            self.report_progress(table_name, 'error', f'Failed: {str(e)}', 0, 0)
            return False
        finally:
            local_cur.close()
            railway_cur.close()

    def sync_all(self):
        """Sync all essential tables"""
        print("Safe Railway Database Sync")
        print("=" * 50)

        print(f"Local DB: {self.local_config['host']}:{self.local_config['port']}")
        print(f"Railway DB: {self.railway_config['host']}:{self.railway_config['port']}")

        try:
            # Connect to databases
            local_conn = psycopg2.connect(**self.local_config)
            print("SUCCESS: Connected to local database")

            railway_conn = psycopg2.connect(**self.railway_config)
            print("SUCCESS: Connected to Railway database")

            # Sync essential tables
            print(f"\nSyncing {len(ESSENTIAL_TABLES)} essential tables...")
            success_count = 0

            for table in ESSENTIAL_TABLES:
                print(f"\n--- Processing {table} ---")
                if self.sync_table_safe(local_conn, railway_conn, table):
                    success_count += 1

            print("\n" + "=" * 50)
            print(f"Sync complete: {success_count}/{len(ESSENTIAL_TABLES)} tables synced successfully")

            # Verify critical data
            railway_cur = railway_conn.cursor()

            railway_cur.execute("SELECT COUNT(*) FROM players")
            player_count = railway_cur.fetchone()[0]
            print(f"\nVerification:")
            print(f"  - Players: {player_count}")

            railway_cur.execute("SELECT COUNT(*) FROM player_metrics")
            metrics_count = railway_cur.fetchone()[0]
            print(f"  - Player metrics: {metrics_count}")

            railway_cur.execute("SELECT COUNT(*) FROM team_metrics WHERE npxg IS NOT NULL")
            team_count = railway_cur.fetchone()[0]
            print(f"  - Teams with NPxG data: {team_count}")

            railway_cur.close()

            return {
                'success': success_count == len(ESSENTIAL_TABLES),
                'tables_synced': success_count,
                'total_tables': len(ESSENTIAL_TABLES),
                'results': self.sync_results
            }

        except Exception as e:
            print(f"ERROR: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': self.sync_results
            }
        finally:
            if 'local_conn' in locals():
                local_conn.close()
            if 'railway_conn' in locals():
                railway_conn.close()

def main():
    """Run sync from command line"""
    syncer = SafeRailwaySync()
    result = syncer.sync_all()
    return 0 if result['success'] else 1

if __name__ == "__main__":
    exit(main())