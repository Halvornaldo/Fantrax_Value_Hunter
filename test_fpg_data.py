#!/usr/bin/env python3
"""
Test accessing 2024-25 FP/G data using exact parameters from URL
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Fantrax_Wrapper'))

from fantraxapi import FantraxAPI
import json
import requests

def test_fpg_data():
    """Test if we can get 2024-25 FP/G data using URL parameters"""
    print("=== Testing 2024-25 FP/G Data Access ===")
    
    try:
        # Load cookies
        with open('config/fantrax_cookies.json', 'r') as f:
            cookies = json.load(f)
        
        # Create session
        session = requests.Session()
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.fantrax.com')
        
        # Initialize API
        api = FantraxAPI('gjbogdx2mcmcvzqa', session=session)
        print("API initialized successfully")
        
        # Try exact parameters from URL
        print("\n--- Testing 2024-25 BY_DATE (FP/G Data) ---")
        
        params = {
            'seasonOrProjections': 'SEASON_924_BY_DATE',
            'timeframeTypeCode': 'BY_DATE'
        }
        
        print(f"Testing parameters: {params}")
        stats = api._request('getPlayerStats', **params)
        
        if 'statsTable' in stats and stats['statsTable']:
            players = stats['statsTable']
            print(f"[SUCCESS] Got {len(players)} players")
            
            # Check first few players for FP/G data
            for i in range(min(5, len(players))):
                player = players[i]
                name = player['scorer']['name']
                cells = [cell['content'] for cell in player['cells']]
                print(f"Player {i+1}: {name}")
                print(f"  Cells: {cells}")
                
                # The FP/G should be in one of these cells
                if len(cells) >= 5:
                    rank, opp, salary, fpts = cells[0], cells[1], cells[2], cells[3]
                    print(f"  Rank: {rank}, Opponent: {opp}, Salary: ${salary}, FPts: {fpts}")
                    
                    # Look for FP/G in remaining cells
                    remaining = cells[4:]
                    print(f"  Other data: {remaining}")
        else:
            print("[FAILED] No data returned")
            
        # Check metadata
        if 'seasonOrProjections' in stats:
            seasons = stats['seasonOrProjections']
            current_season = next((s for s in seasons if s['code'] == 'SEASON_924_BY_DATE'), None)
            if current_season:
                print(f"\n[INFO] Found 2024-25 season: {current_season['name']}")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fpg_data()