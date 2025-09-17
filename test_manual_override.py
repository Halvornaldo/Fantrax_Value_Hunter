#!/usr/bin/env python3
"""
Test manual override functionality specifically
"""

import requests
import json
import psycopg2
import psycopg2.extras

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

API_BASE = "http://localhost:5001/api"

def test_manual_override():
    """Test manual override without heavy recalculation"""
    print("Testing Manual Override...")

    # Get a test player
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id, name FROM players LIMIT 1")
    test_player = cursor.fetchone()

    if not test_player:
        print("FAIL: No test player found")
        return False

    player_id = test_player['id']
    print(f"Testing with player: {test_player['name']} (ID: {player_id})")

    # Test override to Likely Starter (0.90x)
    try:
        override_data = {
            "player_id": player_id,
            "override_type": "L"  # Likely
        }

        print("Sending override request...")
        response = requests.post(f"{API_BASE}/manual-override", json=override_data, timeout=30)

        if response.status_code == 200:
            print("PASS: Override API call successful")

            # Check database
            cursor.execute("SELECT starter_multiplier FROM player_metrics WHERE player_id = %s", [player_id])
            result = cursor.fetchone()

            if result:
                multiplier = result['starter_multiplier']
                if abs(multiplier - 0.90) < 0.001:
                    print(f"PASS: Database updated correctly (0.90x)")
                    return True
                else:
                    print(f"FAIL: Expected 0.90x, got {multiplier}x")
                    return False
            else:
                print("FAIL: No result from database")
                return False
        else:
            print(f"FAIL: Override API failed ({response.status_code})")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"FAIL: Override error - {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    test_manual_override()