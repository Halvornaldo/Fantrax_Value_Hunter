#!/usr/bin/env python3
"""
Test API Parameter Features
Test parameter toggles and manual overrides via API
"""

import requests
import json
import time
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

def test_parameter_toggles():
    """Test parameter toggle switches"""
    print("Testing Parameter Toggles...")

    # Get current config
    try:
        response = requests.get(f"{API_BASE}/system/config")
        if response.status_code != 200:
            print(f"FAIL: Cannot get config ({response.status_code})")
            return False

        config = response.json()
        toggles = config.get('formula_optimization_v2', {}).get('formula_toggles', {})

        print("Current toggle states:")
        for toggle, state in toggles.items():
            print(f"  {toggle}: {'ON' if state else 'OFF'}")

        # Test fixture toggle (safe to test)
        original_fixture = toggles.get('fixture_enabled', True)
        print(f"\nTesting fixture toggle (original: {original_fixture})...")

        # Toggle fixture OFF
        update_data = {"fixture_enabled": False}
        response = requests.post(f"{API_BASE}/system/update-parameters", json=update_data)

        if response.status_code == 200:
            print("PASS: Toggled fixture OFF")
        else:
            print(f"FAIL: Could not toggle fixture OFF ({response.status_code})")
            return False

        # Toggle fixture back ON
        update_data = {"fixture_enabled": True}
        response = requests.post(f"{API_BASE}/system/update-parameters", json=update_data)

        if response.status_code == 200:
            print("PASS: Toggled fixture back ON")
        else:
            print(f"FAIL: Could not toggle fixture back ON ({response.status_code})")
            return False

        print("PASS: Parameter toggles working")
        return True

    except Exception as e:
        print(f"FAIL: Parameter toggle error - {e}")
        return False

def test_manual_overrides():
    """Test manual override functionality"""
    print("\nTesting Manual Overrides...")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Find a test player
    cursor.execute("SELECT id, name, starter_multiplier FROM player_metrics LIMIT 1")
    test_player = cursor.fetchone()

    if not test_player:
        print("FAIL: No test player found")
        return False

    player_id = test_player['id']
    original_multiplier = test_player['starter_multiplier']
    print(f"Testing with player ID: {player_id} (original: {original_multiplier}x)")

    # Test override levels
    test_levels = [
        ('S', 1.0),    # Starter
        ('L', 0.90),   # Likely
        ('R', 0.75),   # Rotation
        ('U', 0.50),   # Unlikely
    ]

    for level, expected_multiplier in test_levels:
        try:
            # Make override request
            override_data = {
                "player_id": player_id,
                "override_type": level
            }

            response = requests.post(f"{API_BASE}/manual-override", json=override_data)

            if response.status_code == 200:
                # Check database
                time.sleep(0.5)
                cursor.execute("SELECT starter_multiplier FROM player_metrics WHERE player_id = %s", [player_id])
                result = cursor.fetchone()

                if result and abs(result['starter_multiplier'] - expected_multiplier) < 0.001:
                    print(f"PASS: Override {level} -> {expected_multiplier}x")
                else:
                    print(f"FAIL: Override {level} -> Expected {expected_multiplier}x, got {result['starter_multiplier']}x")
                    return False
            else:
                print(f"FAIL: Override {level} -> API error ({response.status_code})")
                return False

        except Exception as e:
            print(f"FAIL: Override {level} -> Exception: {e}")
            return False

    # Restore original
    if original_multiplier == 1.0:
        restore_type = 'S'
    elif original_multiplier == 0.90:
        restore_type = 'L'
    elif original_multiplier == 0.75:
        restore_type = 'R'
    elif original_multiplier == 0.50:
        restore_type = 'U'
    elif original_multiplier == 0.35:
        restore_type = 'B'
    else:
        restore_type = 'O'

    override_data = {"player_id": player_id, "override_type": restore_type}
    requests.post(f"{API_BASE}/manual-override", json=override_data)
    print(f"Restored original multiplier: {original_multiplier}x")

    conn.close()
    print("PASS: Manual overrides working")
    return True

def test_calculation_update():
    """Test that true values get recalculated after parameter changes"""
    print("\nTesting Calculation Updates...")

    try:
        # Trigger recalculation
        response = requests.post(f"{API_BASE}/calculate-values-v2")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("PASS: Values recalculated successfully")
                return True
            else:
                print(f"FAIL: Recalculation failed - {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"FAIL: Cannot trigger recalculation ({response.status_code})")
            return False

    except Exception as e:
        print(f"FAIL: Calculation update error - {e}")
        return False

def main():
    print("API FEATURE TESTS")
    print("=" * 50)

    tests = [
        ("Parameter Toggles", test_parameter_toggles),
        ("Manual Overrides", test_manual_overrides),
        ("Calculation Updates", test_calculation_update),
    ]

    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")

    print(f"\nResults: {passed}/{len(tests)} API tests passed")

    if passed == len(tests):
        print("All API features working correctly!")
    else:
        print("Some API features failed - Check above")

if __name__ == "__main__":
    main()