#!/usr/bin/env python3
"""
Test Validation API Script
Tests the 5 new validation endpoints we added to the Flask app.
Uses the problematic CSV data to test the validation workflow.
"""

import requests
import json
import sys
import os

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_name_mapping_stats():
    """Test the name mapping statistics endpoint"""
    print("=" * 60)
    print("TESTING NAME MAPPING STATS ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/name-mapping-stats")
        
        if response.status_code == 200:
            stats = response.json()
            print("SUCCESS: Stats endpoint working")
            print(f"Total mappings: {stats.get('total_mappings', 'N/A')}")
            
            if 'by_source_system' in stats:
                print("\nBy source system:")
                for source, count in stats['by_source_system'].items():
                    print(f"  {source}: {count}")
            
            if 'accuracy_stats' in stats:
                print(f"\nAccuracy stats: {stats['accuracy_stats']}")
                
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

def test_get_player_suggestions():
    """Test the player suggestions endpoint"""
    print("\n" + "=" * 60)
    print("TESTING PLAYER SUGGESTIONS ENDPOINT")
    print("=" * 60)
    
    # Test cases from our problematic players
    test_cases = [
        {
            'source_name': 'Fernando López',
            'team': 'WOL',
            'position': 'F',
            'source_system': 'ffs'
        },
        {
            'source_name': 'Unknown Player',
            'team': 'MCI',
            'position': 'M',
            'source_system': 'ffs'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['source_name']} ({test_case['team']}, {test_case['position']})")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/get-player-suggestions",
                json=test_case
            )
            
            if response.status_code == 200:
                suggestions = response.json()
                print("SUCCESS: Suggestions received")
                
                if suggestions.get('suggestions'):
                    for j, suggestion in enumerate(suggestions['suggestions'], 1):
                        print(f"  {j}. {suggestion['name']} ({suggestion['confidence']:.1f}%)")
                        if 'team' in suggestion:
                            print(f"     Team: {suggestion['team']}, Position: {suggestion['position']}")
                else:
                    print("  No suggestions found")
                    
            else:
                print(f"ERROR: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"ERROR: {e}")

def test_validate_import():
    """Test the validate import endpoint with sample CSV data"""
    print("\n" + "=" * 60)
    print("TESTING VALIDATE IMPORT ENDPOINT")
    print("=" * 60)
    
    # Sample CSV data with our problematic players
    sample_import_data = [
        {
            'name': 'David Raya',
            'team': 'ARS',
            'position': 'G',
            'points': 150
        },
        {
            'name': 'Raya Martin',  # Problematic name
            'team': 'ARS',
            'position': 'G',
            'points': 150
        },
        {
            'name': "O'Riley",  # Problematic name
            'team': 'BHA',
            'position': 'M',
            'points': 120
        },
        {
            'name': 'Fernando López',  # Problematic name
            'team': 'WOL',
            'position': 'F',
            'points': 80
        },
        {
            'name': 'Unknown Player',  # Should fail
            'team': 'MCI',
            'position': 'M',
            'points': 90
        }
    ]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/validate-import",
            json={
                'source_system': 'ffs_test',
                'players': sample_import_data
            }
        )
        
        if response.status_code == 200:
            validation = response.json()
            print("SUCCESS: Import validation completed")
            
            print(f"\nMatched: {validation['summary']['matched']}")
            print(f"Needs Review: {validation['summary']['needs_review']}")
            print(f"Failed: {validation['summary']['failed']}")
            print(f"Match Rate: {validation['summary']['match_rate']:.1f}%")
            
            if validation['summary']['needs_review'] > 0:
                print(f"\nPlayers needing review:")
                for player in validation['players']:
                    if player['needs_review']:
                        print(f"  {player['original_name']} -> {player['match_result']['fantrax_name'] or 'NO MATCH'}")
                        if player['match_result']['suggested_matches']:
                            print(f"    Suggestions: {len(player['match_result']['suggested_matches'])}")
            
            # Show position breakdown
            print(f"\nPosition breakdown:")
            for pos, stats in validation['position_breakdown'].items():
                print(f"  {pos}: {stats['matched']}/{stats['total']} ({stats['match_rate']:.1f}%)")
                
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

def test_confirm_mapping():
    """Test the confirm mapping endpoint"""
    print("\n" + "=" * 60)
    print("TESTING CONFIRM MAPPING ENDPOINT")
    print("=" * 60)
    
    # Get a valid fantrax_id first (David Raya)
    test_mapping = {
        'source_system': 'ffs_test',
        'source_name': 'Test Player Mapping',
        'fantrax_id': '05tqx',  # David Raya's ID from our test data
        'user_id': 'test_user'
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/confirm-mapping",
            json=test_mapping
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Mapping confirmed")
            print(f"Mapping ID: {result.get('mapping_id', 'N/A')}")
            print(f"Message: {result.get('message', 'N/A')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

def test_apply_import():
    """Test the apply import endpoint (won't actually apply, just test the endpoint)"""
    print("\n" + "=" * 60)
    print("TESTING APPLY IMPORT ENDPOINT (DRY RUN)")
    print("=" * 60)
    
    # Simple test data - just one player that should match
    test_import = {
        'source_system': 'ffs_test',
        'players': [
            {
                'name': 'David Raya',
                'team': 'ARS',
                'position': 'G',
                'points': 150
            }
        ],
        'confirmed_mappings': {},  # No manual mappings
        'dry_run': True  # Don't actually apply
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/apply-import",
            json=test_import
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Apply import endpoint working")
            print(f"Would import: {result.get('import_count', 0)} players")
            print(f"Message: {result.get('message', 'N/A')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

def check_server_status():
    """Check if the Flask server is running"""
    print("=" * 60)
    print("CHECKING SERVER STATUS")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/name-mapping-stats", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Flask server is running on localhost:5000")
            return True
        else:
            print(f"Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Flask server on localhost:5000")
        print("Please make sure the Flask app is running:")
        print("  python src/app.py")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    try:
        if not check_server_status():
            sys.exit(1)
        
        test_name_mapping_stats()
        test_get_player_suggestions()
        test_validate_import()
        test_confirm_mapping()
        test_apply_import()
        
        print("\n" + "=" * 60)
        print("VALIDATION API TESTING COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Create validation UI with smart suggestions")
        print("2. Update FFS CSV import to use validation workflow")
        print("3. Test end-to-end import process")
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()