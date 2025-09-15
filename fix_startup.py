#!/usr/bin/env python3
"""Fix the startup database test to be non-blocking"""

import re

# Read the current app.py
with open('src/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new startup section
new_startup = '''if __name__ == '__main__':
    print("Starting Fantrax Value Hunter Flask Backend...")
    print(f"Database: {DB_CONFIG['database']} on port {DB_CONFIG['port']}")

    # Test database connection on startup with timeout
    def test_db_connection():
        """Test database connection in a separate thread"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            print(f"Database connected: {player_count} players loaded")

            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            print("App will start anyway - database operations may fail until connection is established")
            return False

    # Run database test with timeout
    import threading
    import time

    db_test_result = {'connected': False}

    def db_test_thread():
        db_test_result['connected'] = test_db_connection()

    # Start database test in background
    test_thread = threading.Thread(target=db_test_thread)
    test_thread.daemon = True
    test_thread.start()

    # Wait max 8 seconds for database test
    test_thread.join(timeout=8)

    if test_thread.is_alive():
        print("Database connection test timed out - starting app anyway")
        print("Note: Database operations may fail until connection is established")

    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))  # Use 5001 to avoid conflict
    debug = os.getenv('FLASK_ENV') == 'development'

    # DEVELOPMENT: Enable auto-reload for code changes
    # Set debug=True to auto-restart server when Python files change
    development_mode = False  # Production mode

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)'''

# Replace the old startup section
pattern = r'if __name__ == \'__main__\':\s*.*?app\.run\([^)]+\)'
new_content = re.sub(pattern, new_startup, content, flags=re.DOTALL)

# Write the updated content back
with open('src/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated startup section with non-blocking database test")