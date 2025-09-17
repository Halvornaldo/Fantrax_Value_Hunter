#!/usr/bin/env python3
"""
Test CSV import clearing of manual overrides
"""

import requests
import json

API_BASE = "http://localhost:5001/api"

def test_csv_import_clearing():
    """Test that CSV import clears manual overrides"""
    print("Testing CSV import clearing of manual overrides...")

    # First check if we have overrides
    response = requests.get(f"{API_BASE}/system/config", timeout=10)
    if response.status_code == 200:
        config = response.json()
        overrides = config.get('starter_prediction', {}).get('manual_overrides', {})
        print(f"Current overrides before import: {len(overrides)} players")
        for player_id, override in overrides.items():
            print(f"  {player_id}: {override.get('type', 'unknown')}")

    # Import CSV file
    try:
        with open('test_lineups.csv', 'rb') as f:
            files = {'lineups_csv': f}
            response = requests.post(f"{API_BASE}/import-lineups", files=files, timeout=30)

        if response.status_code == 200:
            print("PASS: CSV import successful")

            # Check if overrides were cleared
            response = requests.get(f"{API_BASE}/system/config", timeout=10)
            if response.status_code == 200:
                config = response.json()
                overrides = config.get('starter_prediction', {}).get('manual_overrides', {})
                print(f"Overrides after import: {len(overrides)} players")

                if len(overrides) == 0:
                    print("PASS: All manual overrides were cleared")
                    return True
                else:
                    print(f"FAIL: {len(overrides)} overrides still remain:")
                    for player_id, override in overrides.items():
                        print(f"  {player_id}: {override.get('type', 'unknown')}")
                    return False
            else:
                print(f"FAIL: Cannot read config after import")
                return False
        else:
            print(f"FAIL: CSV import failed ({response.status_code})")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"FAIL: CSV import error - {e}")
        return False

if __name__ == "__main__":
    if test_csv_import_clearing():
        print("CSV clearing system working correctly!")
    else:
        print("CSV clearing system has issues")