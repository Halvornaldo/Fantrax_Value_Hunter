#!/usr/bin/env python3
"""
Complete Override Management System Test
Tests all features:
1. Manual overrides work correctly
2. Override status is returned in API
3. CSV import clears all overrides
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

def test_override_management_system():
    """Complete test of override management system"""
    print("=" * 60)
    print("COMPLETE OVERRIDE MANAGEMENT SYSTEM TEST")
    print("=" * 60)

    # Get a test player
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id, name FROM players LIMIT 1")
    test_player = cursor.fetchone()

    if not test_player:
        print("FAIL: No test player found")
        return False

    player_id = test_player['id']
    player_name = test_player['name']
    print(f"Test player: {player_name} (ID: {player_id})")
    print()

    tests_passed = 0
    total_tests = 4

    # TEST 1: Manual Override Functionality
    print("TEST 1: Manual Override Functionality")
    print("-" * 40)
    try:
        # Set override to "likely" (0.90x)
        override_data = {"player_id": player_id, "override_type": "likely"}
        response = requests.post(f"{API_BASE}/manual-override", json=override_data, timeout=10)

        if response.status_code == 200:
            print("PASS: Override API call successful")

            # Check database
            cursor.execute("SELECT starter_multiplier FROM player_metrics WHERE player_id = %s", [player_id])
            result = cursor.fetchone()

            if result and abs(float(result['starter_multiplier']) - 0.90) < 0.001:
                print("PASS: Database updated correctly (0.90x)")
                tests_passed += 1
            else:
                print(f"FAIL: Database update failed")
        else:
            print(f"FAIL: Override API failed ({response.status_code})")
    except Exception as e:
        print(f"FAIL: Override test error: {e}")

    print()

    # TEST 2: Override Status in Player API
    print("TEST 2: Override Status in Player API")
    print("-" * 40)
    try:
        response = requests.get(f"{API_BASE}/players?limit=5", timeout=10)
        if response.status_code == 200:
            api_response = response.json()
            players = api_response.get('players', [])

            # Find our test player
            test_player_data = None
            for player in players:
                if player['id'] == player_id:
                    test_player_data = player
                    break

            if test_player_data:
                has_override = test_player_data.get('has_override', False)
                override_type = test_player_data.get('override_type', 'unknown')

                if has_override and override_type == 'likely':
                    print("PASS: Override status correctly returned in API")
                    print(f"  has_override: {has_override}")
                    print(f"  override_type: {override_type}")
                    tests_passed += 1
                else:
                    print(f"FAIL: Override status incorrect: has_override={has_override}, type={override_type}")
            else:
                print("FAIL: Test player not found in API response")
        else:
            print(f"FAIL: Player API failed ({response.status_code})")
    except Exception as e:
        print(f"FAIL: Player API test error: {e}")

    print()

    # TEST 3: System Config Shows Override
    print("TEST 3: System Config Shows Override")
    print("-" * 40)
    try:
        response = requests.get(f"{API_BASE}/system/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            overrides = config.get('starter_prediction', {}).get('manual_overrides', {})

            if player_id in overrides and overrides[player_id].get('type') == 'likely':
                print("PASS: Override correctly stored in system config")
                print(f"  Player {player_id}: {overrides[player_id]}")
                tests_passed += 1
            else:
                print(f"FAIL: Override not found in system config")
                print(f"  Found overrides: {overrides}")
        else:
            print(f"FAIL: Config API failed ({response.status_code})")
    except Exception as e:
        print(f"FAIL: Config test error: {e}")

    print()

    # TEST 4: CSV Import Clears Overrides
    print("TEST 4: CSV Import Clears Overrides")
    print("-" * 40)
    try:
        # Check current overrides count
        response = requests.get(f"{API_BASE}/system/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            overrides_before = config.get('starter_prediction', {}).get('manual_overrides', {})
            print(f"Overrides before import: {len(overrides_before)}")

            # Import test CSV
            with open('test_lineups.csv', 'rb') as f:
                files = {'lineups_csv': f}
                response = requests.post(f"{API_BASE}/import-lineups", files=files, timeout=60)

            if response.status_code == 200:
                print("PASS: CSV import completed")

                # Check if overrides were cleared
                response = requests.get(f"{API_BASE}/system/config", timeout=10)
                if response.status_code == 200:
                    config = response.json()
                    overrides_after = config.get('starter_prediction', {}).get('manual_overrides', {})
                    print(f"Overrides after import: {len(overrides_after)}")

                    if len(overrides_after) == 0:
                        print("PASS: All manual overrides were cleared by CSV import")
                        tests_passed += 1
                    else:
                        print(f"FAIL: {len(overrides_after)} overrides still remain")
                else:
                    print("FAIL: Cannot read config after import")
            else:
                print(f"FAIL: CSV import failed ({response.status_code})")
        else:
            print("FAIL: Cannot read initial config")
    except Exception as e:
        print(f"FAIL: CSV import test error: {e}")

    conn.close()

    print()
    print("=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)

    if tests_passed == total_tests:
        print("SUCCESS: COMPLETE OVERRIDE MANAGEMENT SYSTEM WORKING CORRECTLY!")
        return True
    else:
        print("WARNING: Some tests failed - system needs attention")
        return False

if __name__ == "__main__":
    test_override_management_system()