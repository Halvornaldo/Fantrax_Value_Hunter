#!/usr/bin/env python3
"""
Save 2024-25 Season Baseline Data
Extract current player data as season averages before 2025-26 season starts
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Fantrax_Wrapper'))

from fantraxapi import FantraxAPI
import json
import requests
from datetime import datetime

class BaselineSaver:
    def __init__(self):
        self.api = None
        self.baseline_data = {
            "metadata": {
                "fetched_date": datetime.now().strftime("%Y-%m-%d"),
                "total_players": 0,
                "season": "2024-25",
                "description": "Baseline season averages for form calculation"
            },
            "players": {}
        }
        
    def authenticate(self):
        """Set up Fantrax API authentication"""
        try:
            with open('../config/fantrax_cookies.json', 'r') as f:
                cookies = json.load(f)
            
            session = requests.Session()
            for name, value in cookies.items():
                session.cookies.set(name, value, domain='.fantrax.com')
            
            self.api = FantraxAPI('gjbogdx2mcmcvzqa', session=session)
            print("[SUCCESS] Authentication successful")
            return True
            
        except Exception as e:
            print(f"[ERROR] Authentication failed: {e}")
            return False
    
    def fetch_and_save_baseline(self):
        """Fetch all players and save as baseline"""
        print("[INFO] Fetching baseline data for 2024-25 season...")
        
        all_players_data = []
        
        for page_num in range(1, 33):
            try:
                print(f"[INFO] Fetching page {page_num}...")
                
                if page_num == 1:
                    player_stats = self.api._request('getPlayerStats')
                else:
                    player_stats = self.api._request('getPlayerStats', pageNumber=str(page_num))
                
                if 'statsTable' in player_stats and player_stats['statsTable']:
                    players = player_stats['statsTable']
                    all_players_data.extend(players)
                    print(f"[SUCCESS] Page {page_num}: {len(players)} players")
                else:
                    print(f"[INFO] Page {page_num}: No more data")
                    break
                    
            except Exception as e:
                print(f"[ERROR] Page {page_num} failed: {e}")
                if page_num > 3:
                    break
                continue
        
        print(f"[SUCCESS] Retrieved {len(all_players_data)} total players")
        
        # Process and save baseline data
        for player in all_players_data:
            try:
                scorer = player.get('scorer', {})
                cells = player.get('cells', [])
                
                if len(cells) < 4:
                    continue
                
                player_id = scorer.get('scorerId', '')
                if not player_id:
                    continue
                
                # Extract season average (projected points as baseline)
                season_points = float(cells[3].get('content', 0.0))
                
                self.baseline_data["players"][player_id] = {
                    "name": scorer.get('name', 'Unknown'),
                    "team": scorer.get('teamShortName', 'UNK'),
                    "position": scorer.get('posShortNames', 'UNK'),
                    "season_average_2024": season_points,
                    "salary_2024": float(cells[2].get('content', 5.0))
                }
                
            except Exception as e:
                continue
        
        self.baseline_data["metadata"]["total_players"] = len(self.baseline_data["players"])
        
        # Save to file
        baseline_file = '../data/season_2024_baseline.json'
        with open(baseline_file, 'w') as f:
            json.dump(self.baseline_data, f, indent=2)
        
        print(f"[SUCCESS] Baseline data saved to {baseline_file}")
        print(f"[INFO] Saved {len(self.baseline_data['players'])} players")
        return True
    
    def run(self):
        """Execute baseline saving"""
        print("SAVING 2024-25 SEASON BASELINE DATA")
        print("="*50)
        
        if not self.authenticate():
            return False
        
        if not self.fetch_and_save_baseline():
            return False
        
        print(f"\n[SUCCESS] Baseline data saved successfully!")
        print(f"This data will be used for form calculations in the first 10 games.")
        return True

if __name__ == "__main__":
    saver = BaselineSaver()
    success = saver.run()
    
    if not success:
        print("[ERROR] Failed to save baseline data.")
        sys.exit(1)