#!/usr/bin/env python3
"""Test different SSL modes with Railway database"""

import psycopg2
import os
import time

# Railway DATABASE_URL
DATABASE_URL = "postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway"

# Parse URL
import urllib.parse
result = urllib.parse.urlparse(DATABASE_URL)

base_params = {
    'host': result.hostname,
    'port': result.port,
    'user': result.username,
    'password': result.password,
    'database': result.path[1:]
}

# Test different SSL modes
ssl_modes = ['disable', 'prefer', 'require', 'verify-ca', 'verify-full']

for ssl_mode in ssl_modes:
    print(f"\n--- Testing sslmode={ssl_mode} ---")

    test_params = base_params.copy()
    test_params.update({
        'connect_timeout': 5,  # Short timeout for testing
        'sslmode': ssl_mode,
        'application_name': 'fantrax_test'
    })

    try:
        start_time = time.time()
        conn = psycopg2.connect(**test_params)
        elapsed = time.time() - start_time

        print(f"SUCCESS: Connected in {elapsed:.2f} seconds with sslmode={ssl_mode}")

        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL: {version[:50]}...")

        cursor.close()
        conn.close()

        print(f"RECOMMENDED: Use sslmode={ssl_mode}")
        break

    except psycopg2.OperationalError as e:
        elapsed = time.time() - start_time
        print(f"FAILED after {elapsed:.2f}s: {str(e)[:100]}...")

    except Exception as e:
        print(f"ERROR: {e}")

print("\nTest completed.")