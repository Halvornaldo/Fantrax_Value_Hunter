#!/usr/bin/env python3
"""
Production Server for Fantrax Value Hunter
Uses Waitress WSGI server for production-quality performance

This replaces the Flask development server (app.run()) with a proper
production server that can handle concurrent requests efficiently.

Usage:
    python server_production.py

Expected performance improvement: 10x faster than development server
"""

import os
import sys
from waitress import serve

# Add src directory to path so we can import the Flask app
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the Flask app from src/app.py
from app import app

def main():
    """Start the production server"""
    print("Starting Fantrax Value Hunter - Production Server (Waitress)")
    print("=" * 60)
    
    # Server configuration
    host = '0.0.0.0'  # Accept connections from any IP
    port = int(os.getenv('PORT', 5001))  # Use port 5001 by default
    threads = 4  # Handle up to 4 concurrent requests
    
    print(f"Server: Waitress WSGI Server")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Threads: {threads}")
    print(f"URL: http://localhost:{port}")
    print("=" * 60)
    
    # Test database connection before starting server
    try:
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        print(f"Database connected: {player_count} players loaded")
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Please check your database configuration and try again.")
        sys.exit(1)
    
    print("\nPerformance Expectations:")
    print("- 10x faster than development server")
    print("- Can handle multiple concurrent requests")
    print("- Expected API response time: 2-5 seconds (vs 30+ seconds)")
    print("\nStarting server...")
    
    try:
        # Start the Waitress server
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            cleanup_interval=30,  # Clean up connections every 30 seconds
            channel_timeout=120   # 2 minute timeout for long-running requests
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nServer error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()