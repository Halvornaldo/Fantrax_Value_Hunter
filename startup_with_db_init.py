#!/usr/bin/env python3
"""
Startup script for Railway deployment
Initializes database and starts Flask app
"""

import os
import sys
import psycopg2

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_migrations():
    """Run database migrations to add any missing columns"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️ No DATABASE_URL found, skipping migrations")
        return

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Migration: Add exclude_from_optimizer column if missing
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'players' AND column_name = 'exclude_from_optimizer'
        """)
        if not cursor.fetchone():
            print("📦 Adding exclude_from_optimizer column to players table...")
            cursor.execute("""
                ALTER TABLE players
                ADD COLUMN exclude_from_optimizer BOOLEAN DEFAULT FALSE
            """)
            conn.commit()
            print("✅ Column added successfully")
        else:
            print("✅ exclude_from_optimizer column already exists")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Migration warning: {e}")

def main():
    print("Starting Fantrax Value Hunter...")

    # Run migrations first (safe - only adds columns, never drops)
    print("Running database migrations...")
    run_migrations()

    # NOTE: Database initialization removed - Railway is a read-only mirror
    # Data is synced from local database via dashboard "Sync to Railway" button
    # The old init_database_if_needed() could DROP all tables if it detected
    # an "incomplete" database, which caused data loss issues.

    # Import and start the Flask app
    print("Starting Flask application...")
    from app import app

    # Get port from environment (Railway sets this)
    port = int(os.getenv('PORT', 8080))

    print(f"🎯 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()