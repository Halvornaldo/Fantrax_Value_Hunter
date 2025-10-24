#!/usr/bin/env python3
"""
Optimized Railway Database Sync - Fast batch processing with minimal backups
Syncs essential tables from local to Railway with high performance
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
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

class OptimizedRailwaySync:
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
            'status': status,  # 'starting', 'syncing', 'success', 'error'
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

    def clean_old_backups(self, railway_conn):
        """Clean up old backup tables from previous syncs"""
        railway_cur = railway_conn.cursor()

        try:
            # Find all backup tables (they have _backup_ in the name)
            railway_cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename LIKE '%_backup_%'
            """)

            backup_tables = railway_cur.fetchall()

            if backup_tables:
                print(f"Found {len(backup_tables)} old backup tables to clean up...")
                for (table_name,) in backup_tables:
                    try:
                        railway_cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                        print(f"  Dropped: {table_name}")
                    except Exception as e:
                        print(f"  Failed to drop {table_name}: {e}")

                railway_conn.commit()
                print(f"Cleaned up {len(backup_tables)} backup tables")

        except Exception as e:
            print(f"Error cleaning backups: {e}")
            railway_conn.rollback()
        finally:
            railway_cur.close()

    def sync_table_optimized(self, local_conn, railway_conn, table_name):
        """Sync a single table using batch operations for speed"""
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

            self.report_progress(table_name, 'syncing', f'Preparing to sync {total_rows} rows...', 0, total_rows)

            # Get table structure from local
            local_cur.execute(f"""
                SELECT column_name, data_type, character_maximum_length,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = local_cur.fetchall()

            # Check if table exists on Railway
            railway_cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            table_exists = railway_cur.fetchone()[0] > 0

            if table_exists:
                # Simply truncate - no backup needed since we're replacing everything
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

                # Get and create primary key if exists
                local_cur.execute(f"""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_name = %s
                """, (table_name,))
                pk_columns = [row[0] for row in local_cur.fetchall()]

                if pk_columns:
                    railway_cur.execute(f"""
                        ALTER TABLE {table_name}
                        ADD PRIMARY KEY ({', '.join([f'"{col}"' for col in pk_columns])})
                    """)

                railway_conn.commit()

            # Copy data using execute_values for MUCH faster batch insertion
            self.report_progress(table_name, 'syncing', 'Copying data in batches...', 0, total_rows)

            col_names = [col[0] for col in columns]
            col_names_str = ', '.join([f'"{col}"' for col in col_names])

            # Use larger batch size for better performance
            batch_size = 5000
            offset = 0
            rows_synced = 0
            start_time = time.time()

            while offset < total_rows:
                # Fetch batch
                local_cur.execute(f"""
                    SELECT {col_names_str}
                    FROM {table_name}
                    ORDER BY 1
                    LIMIT {batch_size} OFFSET {offset}
                """)
                rows = local_cur.fetchall()

                if not rows:
                    break

                # Insert batch using execute_values (MUCH faster than individual inserts)
                insert_sql = f"""
                    INSERT INTO {table_name} ({col_names_str})
                    VALUES %s
                    ON CONFLICT DO NOTHING
                """

                try:
                    execute_values(
                        railway_cur,
                        insert_sql,
                        rows,
                        template=None,
                        page_size=1000  # Process 1000 rows at a time internally
                    )
                    railway_conn.commit()
                    rows_synced += len(rows)

                    # Calculate and report speed
                    elapsed = time.time() - start_time
                    rows_per_sec = rows_synced / elapsed if elapsed > 0 else 0
                    eta = (total_rows - rows_synced) / rows_per_sec if rows_per_sec > 0 else 0

                    self.report_progress(table_name, 'syncing',
                        f'Progress: {rows_synced}/{total_rows} rows ({rows_per_sec:.0f} rows/sec, ETA: {eta:.0f}s)',
                        rows_synced, total_rows)

                except psycopg2.IntegrityError as e:
                    # If batch fails due to duplicates, fall back to row-by-row for this batch only
                    railway_conn.rollback()
                    self.report_progress(table_name, 'syncing',
                        f'Batch conflict, processing individually...', rows_synced, total_rows)

                    for row in rows:
                        try:
                            railway_cur.execute(f"""
                                INSERT INTO {table_name} ({col_names_str})
                                VALUES ({', '.join(['%s'] * len(col_names))})
                                ON CONFLICT DO NOTHING
                            """, row)
                            railway_conn.commit()
                            rows_synced += 1
                        except:
                            railway_conn.rollback()
                            continue

                offset += batch_size

            # Verify sync
            railway_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            actual_count = railway_cur.fetchone()[0]

            elapsed = time.time() - start_time
            success_msg = f'Successfully synced {actual_count} rows in {elapsed:.1f} seconds'

            if actual_count < total_rows:
                success_msg += f' ({total_rows - actual_count} duplicates skipped)'

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
        print("Optimized Railway Database Sync")
        print("=" * 50)

        print(f"Local DB: {self.local_config['host']}:{self.local_config['port']}")
        print(f"Railway DB: {self.railway_config['host']}:{self.railway_config['port']}")

        try:
            # Connect to databases
            local_conn = psycopg2.connect(**self.local_config)
            print("SUCCESS: Connected to local database")

            railway_conn = psycopg2.connect(**self.railway_config)
            print("SUCCESS: Connected to Railway database")

            # Clean up old backup tables first
            self.clean_old_backups(railway_conn)

            # Sync essential tables
            print(f"\nSyncing {len(ESSENTIAL_TABLES)} essential tables...")
            success_count = 0
            total_start_time = time.time()

            for table in ESSENTIAL_TABLES:
                print(f"\n--- Processing {table} ---")
                if self.sync_table_optimized(local_conn, railway_conn, table):
                    success_count += 1

            total_elapsed = time.time() - total_start_time

            print("\n" + "=" * 50)
            print(f"Sync complete: {success_count}/{len(ESSENTIAL_TABLES)} tables synced successfully")
            print(f"Total time: {total_elapsed:.1f} seconds ({total_elapsed/60:.1f} minutes)")

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
                'total_time': total_elapsed,
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
    syncer = OptimizedRailwaySync()
    result = syncer.sync_all()
    return 0 if result['success'] else 1

if __name__ == "__main__":
    exit(main())