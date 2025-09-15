#!/usr/bin/env python3
"""Test the database connection fix before applying to app.py"""

import psycopg2
import os
import urllib.parse

# Database configuration - supports both local and production environments
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', 5433)),
    'user': os.getenv('PGUSER', 'fantrax_user'),
    'password': os.getenv('PGPASSWORD', 'fantrax_password'),
    'database': os.getenv('PGDATABASE', 'fantrax_value_hunter')
}

# Alternative: use DATABASE_URL if provided (Railway format)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Railway provides DATABASE_URL in format: postgresql://user:pass@host:port/db
    result = urllib.parse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': result.hostname,
        'port': result.port,
        'user': result.username,
        'password': result.password,
        'database': result.path[1:]  # Remove leading slash
    }

def get_db_connection():
    """Get database connection with error handling and Railway optimizations"""
    try:
        # Add Railway-specific connection parameters
        connection_params = DB_CONFIG.copy()

        # Check if we're running on Railway
        is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None

        if is_railway or os.getenv('DATABASE_URL'):
            # Railway requires specific connection settings
            connection_params.update({
                'connect_timeout': 10,  # 10 second connection timeout
                'sslmode': 'require',   # Railway proxy requires SSL
                'options': '-c statement_timeout=30000',  # 30 second query timeout
                'application_name': 'fantrax_value_hunter'
            })
        else:
            # Local development settings
            connection_params.update({
                'connect_timeout': 5,
                'sslmode': 'prefer'
            })

        conn = psycopg2.connect(**connection_params)

        # Set connection encoding and timezone
        conn.set_client_encoding('UTF8')

        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        print(f"Connection params: host={connection_params.get('host')}, port={connection_params.get('port')}, db={connection_params.get('database')}")
        raise
    except Exception as e:
        print(f"Unexpected database error: {e}")
        raise

def test_connection():
    """Test the database connection"""
    print("Testing database connection...")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✓ Connected! PostgreSQL version: {version[:50]}...")

        # Test if players table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'players'
            )
        """)
        players_exists = cursor.fetchone()[0]

        if players_exists:
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            print(f"✓ Players table exists with {player_count} players")
        else:
            print("⚠ Players table does not exist")

        cursor.close()
        conn.close()

        print("✅ Database connection test successful!")
        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    # For testing with Railway DATABASE_URL locally
    # os.environ['DATABASE_URL'] = "postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway"
    success = test_connection()
    exit(0 if success else 1)