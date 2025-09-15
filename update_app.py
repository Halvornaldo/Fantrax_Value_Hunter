#!/usr/bin/env python3
"""Update app.py with the fixed database connection"""

import re

# Read the current app.py
with open('src/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new get_db_connection function
new_function = '''def get_db_connection():
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
        raise'''

# Replace the old function with the new one
pattern = r'def get_db_connection\(\):\s*"""[^"]*"""\s*try:.*?raise'
replacement = new_function

# Use DOTALL flag to match across newlines
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content back
with open('src/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Updated get_db_connection() function in app.py")