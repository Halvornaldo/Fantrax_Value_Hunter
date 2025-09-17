#!/usr/bin/env python3
"""
Simple Parameter System Test Script
Tests form multiplier range and basic functionality
"""

import psycopg2
import psycopg2.extras
import requests

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def test_form_range():
    """Test that form multipliers are capped to 0.95-1.05"""
    print("Testing Form Range Enforcement...")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT
            MIN(form_multiplier) as min_form,
            MAX(form_multiplier) as max_form,
            COUNT(*) as total_players,
            COUNT(CASE WHEN form_multiplier < 0.95 THEN 1 END) as below_min,
            COUNT(CASE WHEN form_multiplier > 1.05 THEN 1 END) as above_max
        FROM player_metrics
        WHERE form_multiplier IS NOT NULL
    """)

    result = cursor.fetchone()
    print(f"Form range: {result['min_form']:.3f} to {result['max_form']:.3f}")
    print(f"Total players: {result['total_players']}")
    print(f"Below 0.95: {result['below_min']} players")
    print(f"Above 1.05: {result['above_max']} players")

    if result['below_min'] == 0 and result['above_max'] == 0:
        print("PASS: Form multipliers within expected range")
        return True
    else:
        print("FAIL: Form multipliers outside expected range")
        return False

def test_true_value_formula():
    """Test that true value formula is applied correctly"""
    print("\nTesting True Value Formula...")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT
            p.name,
            p.blended_ppg,
            pm.form_multiplier,
            pm.fixture_multiplier,
            pm.starter_multiplier,
            pm.xgi_multiplier,
            pm.true_value,
            (p.blended_ppg * pm.form_multiplier * pm.fixture_multiplier *
             pm.starter_multiplier * pm.xgi_multiplier) as calculated_value
        FROM players p
        JOIN player_metrics pm ON p.id = pm.player_id
        WHERE pm.true_value > 0
        ORDER BY pm.true_value DESC
        LIMIT 3
    """)

    all_correct = True
    for player in cursor.fetchall():
        diff = abs(player['true_value'] - player['calculated_value'])
        is_correct = diff < 0.01
        status = "PASS" if is_correct else "FAIL"

        print(f"{status}: {player['name']} - True: {player['true_value']:.2f}, Calc: {player['calculated_value']:.2f}")
        if not is_correct:
            all_correct = False

    return all_correct

def test_api_connection():
    """Test if API is running"""
    print("\nTesting API Connection...")

    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            print("PASS: API is running")
            return True
        else:
            print(f"FAIL: API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Cannot connect to API - {e}")
        return False

def main():
    print("PARAMETER SYSTEM TESTS")
    print("=" * 50)

    tests = [
        ("Form Range", test_form_range),
        ("True Value Formula", test_true_value_formula),
        ("API Connection", test_api_connection),
    ]

    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")

    print(f"\nResults: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("All tests passed - System working correctly!")
    else:
        print("Some tests failed - Check issues above")

if __name__ == "__main__":
    main()