#!/usr/bin/env python3
"""
Database Auto-Initialization for Railway Deployment
Automatically sets up the database with 714 players if empty
"""

import os
import psycopg2
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection using Railway's DATABASE_URL or local config"""
    try:
        # Try Railway environment variable first
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            logger.info("Using Railway DATABASE_URL")
            return psycopg2.connect(database_url)

        # Fall back to local development config
        logger.info("Using local database configuration")
        return psycopg2.connect(
            host="localhost",
            port=5433,
            user="fantrax_user",
            password="fantrax_password",
            database="fantrax_value_hunter"
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def check_database_empty(conn):
    """Check if database is empty or missing the players table"""
    try:
        cursor = conn.cursor()

        # Check if players table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'players'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            logger.info("Players table does not exist - database is empty")
            return True

        # Check if players table has data
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]

        logger.info(f"Players table has {player_count} records")

        if player_count == 0:
            logger.info("Players table is empty - needs initialization")
            return True
        elif player_count < 700:
            logger.warning(f"Players table has only {player_count} records - may need reinitialization")
            return True
        else:
            logger.info(f"Database already populated with {player_count} players")
            return False

    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return True  # Assume empty if we can't check

def initialize_database(conn):
    """Initialize database with data from railway_database_dump.sql"""
    try:
        cursor = conn.cursor()

        # Get the SQL dump file path
        dump_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'railway_database_dump.sql')

        if not os.path.exists(dump_file):
            raise FileNotFoundError(f"Database dump file not found: {dump_file}")

        logger.info(f"Loading database from {dump_file}")

        # Read and execute the SQL dump
        with open(dump_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Split into individual statements and execute
        statements = sql_content.split(';\n')

        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    if i % 100 == 0:  # Log progress every 100 statements
                        logger.info(f"Executed {i} SQL statements...")
                except Exception as e:
                    # Log error but continue - some statements might be expected to fail
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Statement failed (continuing): {e}")

        conn.commit()

        # Verify the import
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]

        logger.info(f"✅ Database initialization completed successfully!")
        logger.info(f"✅ Loaded {player_count} players")

        # Log some basic stats
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        table_count = cursor.fetchone()[0]
        logger.info(f"✅ Created {table_count} tables")

        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        conn.rollback()
        raise

def init_database_if_needed():
    """Main function to initialize database if needed"""
    try:
        logger.info("🔍 Checking database status...")

        conn = get_database_connection()

        if check_database_empty(conn):
            logger.info("🚀 Initializing database...")
            initialize_database(conn)
        else:
            logger.info("✅ Database already initialized")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization process failed: {e}")
        return False

if __name__ == "__main__":
    init_database_if_needed()