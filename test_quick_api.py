#!/usr/bin/env python3
"""
Quick API Test - Test basic functionality without timeout
"""

import requests
import json

API_BASE = "http://localhost:5001/api"

def test_config_access():
    """Test API config access"""
    print("Testing config access...")
    try:
        response = requests.get(f"{API_BASE}/system/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            toggles = config.get('formula_optimization_v2', {}).get('formula_toggles', {})
            print(f"PASS: Config accessible")
            print(f"  Form: {'ON' if toggles.get('form_enabled') else 'OFF'}")
            print(f"  Fixture: {'ON' if toggles.get('fixture_enabled') else 'OFF'}")
            print(f"  Starter: {'ON' if toggles.get('starter_enabled') else 'OFF'}")
            print(f"  xGI: {'ON' if toggles.get('xgi_enabled') else 'OFF'}")
            return True
        else:
            print(f"FAIL: Config status {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Config error - {e}")
        return False

def test_parameter_update():
    """Test parameter update without heavy calculation"""
    print("\nTesting parameter update...")
    try:
        # Simple toggle test
        update_data = {"fixture_enabled": False}
        response = requests.post(f"{API_BASE}/system/update-parameters", json=update_data, timeout=10)

        if response.status_code == 200:
            print("PASS: Parameter update successful")

            # Toggle back
            update_data = {"fixture_enabled": True}
            response = requests.post(f"{API_BASE}/system/update-parameters", json=update_data, timeout=10)

            if response.status_code == 200:
                print("PASS: Parameter restored")
                return True
            else:
                print(f"FAIL: Cannot restore parameter")
                return False
        else:
            print(f"FAIL: Parameter update failed ({response.status_code})")
            return False

    except Exception as e:
        print(f"FAIL: Parameter update error - {e}")
        return False

def test_health():
    """Test basic health endpoint"""
    print("\nTesting health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("PASS: Health check OK")
            return True
        else:
            print(f"FAIL: Health check failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"FAIL: Health check error - {e}")
        return False

def main():
    print("QUICK API TESTS")
    print("=" * 40)

    tests = [
        ("Health Check", test_health),
        ("Config Access", test_config_access),
        ("Parameter Update", test_parameter_update),
    ]

    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")

    print(f"\nResults: {passed}/{len(tests)} quick tests passed")

if __name__ == "__main__":
    main()