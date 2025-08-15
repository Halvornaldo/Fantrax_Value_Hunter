#!/usr/bin/env python3
"""
Test accessing historical season data from Fantrax API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Fantrax_Wrapper'))

from fantraxapi import FantraxAPI
import json
import requests

def test_historical_data():
    """Test if we can get 2023-24 season data with FP/G"""
    print("=== Testing Historical Data Access ===")
    
    try:
        # Load cookies
        print("Loading cookies...")
        with open('config/fantrax_cookies.json', 'r') as f:
            cookies = json.load(f)
        
        # Create session
        session = requests.Session()
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.fantrax.com')
        
        # Initialize API
        api = FantraxAPI('gjbogdx2mcmcvzqa', session=session)
        print("API initialized successfully")
        
        # Try to get 2023-24 season data
        print("\n--- Testing 2023-24 Season Data ---")
        
        # Test different parameter combinations
        test_params = [
            {'seasonOrProjections': 'SEASON_923_YEAR_TO_DATE'},
            {'season': 'SEASON_923_YEAR_TO_DATE'},
            {'seasonId': 'SEASON_923_YEAR_TO_DATE'},
            {'displayedSeason': 'SEASON_923_YEAR_TO_DATE'},
        ]
        
        for i, params in enumerate(test_params):
            try:
                print(f"\nTesting parameter set {i+1}: {params}")
                stats = api._request('getPlayerStats', **params)
                
                if 'statsTable' in stats and stats['statsTable']:
                    players = stats['statsTable']
                    print(f"[SUCCESS] Got {len(players)} players with params: {params}")
                    
                    # Check first player for data structure
                    if players:
                        first_player = players[0]
                        print(f"Sample player: {first_player['scorer']['name']}")
                        print(f"Cell data: {[cell['content'] for cell in first_player['cells'][:7]]}")
                        
                        # Look for FP/G data in cells  
                        cells = first_player['cells']
                        print(f"Total cells: {len(cells)}")
                        for j, cell in enumerate(cells):
                            print(f"  Cell {j}: {cell['content']}")
                        
                        # Check if there's more data available
                        print(f"Season info: {stats.get('seasonOrProjections', 'Not found')}")
                        print(f"Period info: {stats.get('displayedPeriod', 'Not found')}")
                        
                    break  # Found working params
                else:
                    print(f"[FAILED] No data with params: {params}")
                    
            except Exception as e:
                print(f"[ERROR] Params {params} failed: {e}")
        
        # Also test current data to compare structure
        print(f"\n--- Current Season Data for Comparison ---")
        current_stats = api._request('getPlayerStats')
        if 'statsTable' in current_stats and current_stats['statsTable']:
            current_player = current_stats['statsTable'][0]
            print(f"Current player: {current_player['scorer']['name']}")
            print(f"Current cells: {[cell['content'] for cell in current_player['cells'][:7]]}")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")

if __name__ == "__main__":
    test_historical_data()