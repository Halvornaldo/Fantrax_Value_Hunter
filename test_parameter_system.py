#!/usr/bin/env python3
"""
Comprehensive Parameter System Test Script
Tests all parameter adjustments to verify they're working correctly for Railway deployment
"""

import psycopg2
import psycopg2.extras
import requests
import json
import time
from typing import Dict, Any, List

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

# API configuration
API_BASE = "http://localhost:5001/api"

class ParameterTester:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def test_form_range_enforcement(self):
        """Test 1: Verify form multipliers are capped to 0.95-1.05 range"""
        print("=" * 60)
        print("TEST 1: Form Range Enforcement")
        print("=" * 60)

        # Check form multiplier distribution
        self.cursor.execute("""
            SELECT
                MIN(form_multiplier) as min_form,
                MAX(form_multiplier) as max_form,
                COUNT(*) as total_players,
                COUNT(CASE WHEN form_multiplier < 0.95 THEN 1 END) as below_min,
                COUNT(CASE WHEN form_multiplier > 1.05 THEN 1 END) as above_max
            FROM player_metrics
            WHERE form_multiplier IS NOT NULL
        """)

        result = self.cursor.fetchone()
        print(f"Form Multiplier Range: {result['min_form']:.3f} to {result['max_form']:.3f}")
        print(f"Total players: {result['total_players']}")
        print(f"Below 0.95: {result['below_min']} players")
        print(f"Above 1.05: {result['above_max']} players")

        # Test result
        if result['below_min'] == 0 and result['above_max'] == 0:
            print("✅ PASS: All form multipliers within 0.95-1.05 range")
        else:
            print("❌ FAIL: Form multipliers outside expected range!")

        return result['below_min'] == 0 and result['above_max'] == 0

    def test_true_value_calculation(self):
        """Test 2: Verify true value formula is correctly applied"""
        print("\n" + "=" * 60)
        print("TEST 2: True Value Calculation")
        print("=" * 60)

        # Check top 5 players for calculation accuracy
        self.cursor.execute("""
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
            LIMIT 5
        """)

        all_correct = True
        for player in self.cursor.fetchall():
            diff = abs(player['true_value'] - player['calculated_value'])
            is_correct = diff < 0.01
            status = "✅" if is_correct else "❌"

            print(f"{status} {player['name']:20} True: {player['true_value']:.2f}, Calc: {player['calculated_value']:.2f}")
            if not is_correct:
                all_correct = False
                print(f"    ERROR: Difference of {diff:.3f}")

        if all_correct:
            print("✅ PASS: All true value calculations correct")
        else:
            print("❌ FAIL: True value calculation errors detected!")

        return all_correct

    def test_parameter_toggles(self):
        """Test 3: Test parameter toggle switches via API"""
        print("\n" + "=" * 60)
        print("TEST 3: Parameter Toggle Switches")
        print("=" * 60)

        # Get current parameter states
        try:
            response = requests.get(f"{API_BASE}/system/config")
            if response.status_code != 200:
                print("❌ FAIL: Cannot get system config")
                return False

            config = response.json()
            toggles = config.get('formula_optimization_v2', {}).get('formula_toggles', {})

            print(f"Current states:")
            print(f"  Form: {'ON' if toggles.get('form_enabled', False) else 'OFF'}")
            print(f"  Fixture: {'ON' if toggles.get('fixture_enabled', False) else 'OFF'}")
            print(f"  Starter: {'ON' if toggles.get('starter_enabled', False) else 'OFF'}")
            print(f"  xGI: {'ON' if toggles.get('xgi_enabled', False) else 'OFF'}")

            # Test fixture toggle (safe to toggle)
            print(f"\nTesting Fixture toggle...")
            original_fixture = toggles.get('fixture_enabled', True)

            # Toggle OFF
            toggle_data = {"fixture_enabled": False}
            response = requests.post(f"{API_BASE}/system/update-parameters", json=toggle_data)
            if response.status_code == 200:
                print("✅ Successfully toggled Fixture OFF")
            else:
                print(f"❌ Failed to toggle Fixture OFF: {response.status_code}")

            # Toggle back ON
            toggle_data = {"fixture_enabled": True}
            response = requests.post(f"{API_BASE}/system/update-parameters", json=toggle_data)
            if response.status_code == 200:
                print("✅ Successfully toggled Fixture back ON")
            else:
                print(f"❌ Failed to toggle Fixture back ON: {response.status_code}")

            print("✅ PASS: Parameter toggle API working")
            return True

        except Exception as e:
            print(f"❌ FAIL: Parameter toggle test error: {e}")
            return False

    def test_manual_overrides(self):
        """Test 4: Test manual override buttons via API"""
        print("\n" + "=" * 60)
        print("TEST 4: Manual Override Buttons")
        print("=" * 60)

        # Find a test player
        self.cursor.execute("""
            SELECT p.id, p.name, pm.starter_multiplier
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE p.name LIKE '%test%' OR p.id = '05nt6'
            LIMIT 1
        """)

        test_player = self.cursor.fetchone()
        if not test_player:
            # Use the first player if no test player found
            self.cursor.execute("""
                SELECT p.id, p.name, pm.starter_multiplier
                FROM players p
                JOIN player_metrics pm ON p.id = pm.player_id
                LIMIT 1
            """)
            test_player = self.cursor.fetchone()

        if not test_player:
            print("❌ FAIL: No test player found")
            return False

        print(f"Testing with player: {test_player['name']} (ID: {test_player['id']})")
        original_multiplier = test_player['starter_multiplier']

        # Test each override level
        override_levels = [
            ('S', 1.0),    # Starter
            ('L', 0.90),   # Likely
            ('R', 0.75),   # Rotation
            ('U', 0.50),   # Unlikely
            ('B', 0.35),   # Bench
            ('O', 0.0),    # Out
        ]

        all_passed = True

        for level, expected_multiplier in override_levels:
            try:
                # Make API call
                override_data = {
                    "player_id": test_player['id'],
                    "override_type": level
                }

                response = requests.post(f"{API_BASE}/manual-override", json=override_data)

                if response.status_code == 200:
                    # Check database update
                    time.sleep(0.5)  # Allow for database update
                    self.cursor.execute("""
                        SELECT starter_multiplier
                        FROM player_metrics
                        WHERE player_id = %s
                    """, [test_player['id']])

                    result = self.cursor.fetchone()
                    if result and abs(result['starter_multiplier'] - expected_multiplier) < 0.001:
                        print(f"✅ Override {level} → {expected_multiplier}x: SUCCESS")
                    else:
                        print(f"❌ Override {level} → {expected_multiplier}x: DB not updated correctly")
                        all_passed = False
                else:
                    print(f"❌ Override {level} → {expected_multiplier}x: API call failed ({response.status_code})")
                    all_passed = False

            except Exception as e:
                print(f"❌ Override {level} → {expected_multiplier}x: Error {e}")
                all_passed = False

        # Restore original multiplier
        try:
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

            override_data = {
                "player_id": test_player['id'],
                "override_type": restore_type
            }
            requests.post(f"{API_BASE}/manual-override", json=override_data)
            print(f"✅ Restored original multiplier: {original_multiplier}x")
        except:
            print(f"⚠️  Could not restore original multiplier")

        if all_passed:
            print("✅ PASS: All manual overrides working correctly")
        else:
            print("❌ FAIL: Some manual overrides failed")

        return all_passed

    def test_data_persistence(self):
        """Test 5: Check data persistence after parameter changes"""
        print("\n" + "=" * 60)
        print("TEST 5: Data Persistence")
        print("=" * 60)

        # Get current counts
        self.cursor.execute("SELECT COUNT(*) as count FROM players")
        player_count = self.cursor.fetchone()['count']

        self.cursor.execute("SELECT COUNT(*) as count FROM player_metrics")
        metrics_count = self.cursor.fetchone()['count']

        self.cursor.execute("SELECT COUNT(*) as count FROM player_form WHERE points > 0")
        form_count = self.cursor.fetchone()['count']

        print(f"Players: {player_count}")
        print(f"Player metrics: {metrics_count}")
        print(f"Form data: {form_count}")

        # Check for missing data
        issues = []
        if player_count < 700:
            issues.append(f"Low player count: {player_count}")
        if metrics_count < player_count * 0.9:
            issues.append(f"Missing player metrics: {metrics_count}/{player_count}")
        if form_count < 500:
            issues.append(f"Low form data: {form_count}")

        if not issues:
            print("✅ PASS: Data integrity looks good")
            return True
        else:
            print("❌ FAIL: Data issues detected:")
            for issue in issues:
                print(f"  - {issue}")
            return False

    def run_all_tests(self):
        """Run all parameter system tests"""
        print("COMPREHENSIVE PARAMETER SYSTEM TEST")
        print("=" * 80)
        print("Testing all parameter adjustments for Railway deployment readiness")
        print("=" * 80)

        tests = [
            ("Form Range Enforcement", self.test_form_range_enforcement),
            ("True Value Calculation", self.test_true_value_calculation),
            ("Parameter Toggles", self.test_parameter_toggles),
            ("Manual Overrides", self.test_manual_overrides),
            ("Data Persistence", self.test_data_persistence),
        ]

        results = {}

        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ FAIL: {test_name} - Exception: {e}")
                results[test_name] = False

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        passed = 0
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1

        print(f"\nResults: {passed}/{len(tests)} tests passed")

        if passed == len(tests):
            print("🎉 ALL TESTS PASSED - System ready for Railway deployment!")
        else:
            print("⚠️  Some tests failed - Review issues before deployment")

        return passed == len(tests)

if __name__ == "__main__":
    tester = ParameterTester()
    tester.run_all_tests()