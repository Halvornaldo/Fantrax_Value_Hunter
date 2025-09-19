#!/usr/bin/env python3
"""
Startup script for Railway deployment
Initializes database and starts Flask app
"""

import os
import sys

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🚀 Starting Fantrax Value Hunter with Database Auto-Initialization...")

    # Import and run database initialization
    try:
        from init_database import init_database_if_needed
        print("📊 Initializing database if needed...")
        init_success = init_database_if_needed()
        if init_success:
            print("✅ Database initialization completed successfully")
        else:
            print("⚠️ Database initialization had issues but continuing...")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("⚠️ Continuing with app startup...")

    # Import and start the Flask app
    print("🌐 Starting Flask application...")
    from app import app

    # Get port from environment (Railway sets this)
    port = int(os.getenv('PORT', 8080))

    print(f"🎯 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()