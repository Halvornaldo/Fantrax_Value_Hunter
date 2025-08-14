#!/usr/bin/env python3
"""
Complete Fantrax Value Hunter - All 633 Players
Generate optimal $100 lineup with proper pagination
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Fantrax_Wrapper'))

from fantraxapi import FantraxAPI
import json
import requests
from collections import defaultdict

class CompleteFantraxOptimizer:
    def __init__(self):
        self.api = None
        self.all_players = []
        self.positions = {'G': [], 'D': [], 'M': [], 'F': []}
        self.budget = 100.0
        
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
    
    def fetch_all_players_paginated(self):
        """Fetch ALL players using proper pagination"""
        print("[INFO] Fetching all player data with pagination...")
        
        all_players_data = []
        total_pages = 1  # Start with assumption of 1 page
        
        for page_num in range(1, 33):  # Try up to 32 pages based on HAR data
            try:
                print(f"[INFO] Fetching page {page_num}...")
                
                # Use the exact parameter format from HAR file
                if page_num == 1:
                    # First page uses standard call
                    player_stats = self.api._request('getPlayerStats')
                else:
                    # Subsequent pages need pageNumber parameter
                    player_stats = self.api._request('getPlayerStats', pageNumber=str(page_num))
                
                if 'statsTable' in player_stats and player_stats['statsTable']:
                    players = player_stats['statsTable']
                    all_players_data.extend(players)
                    
                    # Get pagination info from first page
                    if page_num == 1:
                        pagination = player_stats.get('paginatedResultSet', {})
                        total_pages = pagination.get('totalNumPages', 32)
                        total_results = pagination.get('totalNumResults', 633)
                        print(f"[INFO] Found {total_pages} total pages with {total_results} players")
                    
                    print(f"[SUCCESS] Page {page_num}: {len(players)} players")
                    
                    # Stop if we've reached the last page
                    if page_num >= total_pages:
                        break
                        
                else:
                    print(f"[INFO] Page {page_num}: No more data")
                    break
                    
            except Exception as e:
                print(f"[ERROR] Page {page_num} failed: {e}")
                # If we get errors on later pages, stop trying
                if page_num > 3:
                    break
                continue
        
        print(f"[SUCCESS] Retrieved {len(all_players_data)} total players across {page_num} pages")
        
        if all_players_data:
            self.process_players(all_players_data)
            return True
        else:
            print("[ERROR] No players retrieved")
            return False
    
    def process_players(self, players):
        """Process all player data"""
        print("[INFO] Processing player data...")
        
        for player in players:
            try:
                scorer = player.get('scorer', {})
                cells = player.get('cells', [])
                
                if len(cells) < 4:
                    continue
                
                player_data = {
                    'name': scorer.get('name', 'Unknown'),
                    'team': scorer.get('teamShortName', 'UNK'),
                    'position': scorer.get('posShortNames', 'UNK'),
                    'salary': float(cells[2].get('content', 5.0)),
                    'projected_points': float(cells[3].get('content', 0.0)),
                    'ownership': cells[6].get('content', '0%') if len(cells) > 6 else '0%',
                    'opponent': cells[1].get('content', 'TBD')
                }
                
                player_data['value_ratio'] = player_data['projected_points'] / player_data['salary'] if player_data['salary'] > 0 else 0
                player_data['ownership_pct'] = float(player_data['ownership'].rstrip('%')) if player_data['ownership'] != '0%' else 0
                
                # Better position categorization
                pos = player_data['position']
                if 'G' in pos:
                    self.positions['G'].append(player_data)
                elif 'D' in pos:
                    self.positions['D'].append(player_data)
                elif 'M' in pos:
                    self.positions['M'].append(player_data)
                elif 'F' in pos:
                    self.positions['F'].append(player_data)
                
                self.all_players.append(player_data)
                
            except Exception as e:
                continue
        
        # Sort each position by value ratio
        for pos in self.positions:
            self.positions[pos].sort(key=lambda x: x['value_ratio'], reverse=True)
        
        print(f"[INFO] Final player counts: G:{len(self.positions['G'])}, D:{len(self.positions['D'])}, M:{len(self.positions['M'])}, F:{len(self.positions['F'])}")
    
    def show_top_values_by_position(self):
        """Show top value players for each position"""
        print("\n=== TOP VALUE PLAYERS BY POSITION ===")
        
        for pos_name, pos_code in [('GOALKEEPERS', 'G'), ('DEFENDERS', 'D'), ('MIDFIELDERS', 'M'), ('FORWARDS', 'F')]:
            print(f"\n{pos_name}:")
            print("-" * 40)
            
            for i, player in enumerate(self.positions[pos_code][:5]):
                diff_indicator = "[DIFF]" if player['ownership_pct'] < 40 else "[POP]" if player['ownership_pct'] > 70 else "[AVG]"
                print(f"{i+1}. {diff_indicator} {player['name']:18} ({player['team']})")
                print(f"    ${player['salary']:5.2f} | {player['projected_points']:4.1f}pts | {player['value_ratio']:4.2f}pp$ | {player['ownership']}")
    
    def build_optimal_lineup(self):
        """Build the best possible $100 lineup"""
        print("\n=== BUILDING OPTIMAL $100 LINEUP ===")
        
        lineup = []
        remaining_budget = self.budget
        
        # Position requirements: 1 GK, 4 DEF, 4 MID, 2 FWD
        position_targets = {'G': 1, 'D': 4, 'M': 4, 'F': 2}
        
        for pos, target_count in position_targets.items():
            print(f"\nSelecting {target_count} {pos} player(s):")
            
            available = [p for p in self.positions[pos]]
            selected = 0
            
            for player in available:
                if selected >= target_count:
                    break
                    
                if player['salary'] <= remaining_budget:
                    lineup.append(player)
                    remaining_budget -= player['salary']
                    selected += 1
                    
                    value_indicator = "[VALUE]" if player['value_ratio'] > 1.5 else "[DIFF]" if player['ownership_pct'] < 40 else "[SOLID]"
                    print(f"  {value_indicator} {player['name']:18} ({player['team']}) - ${player['salary']:5.2f} | {player['projected_points']:4.1f}pts")
            
            if selected < target_count:
                print(f"  [WARNING] Only found {selected} of {target_count} {pos} players within budget")
        
        return lineup, remaining_budget
    
    def display_final_lineup(self, lineup, remaining_budget):
        """Display the complete lineup"""
        print("\n" + "="*70)
        print("COMPLETE FANTRAX VALUE HUNTER - OPTIMAL $100 LINEUP")
        print("="*70)
        
        total_cost = sum(p['salary'] for p in lineup)
        total_points = sum(p['projected_points'] for p in lineup)
        
        # Group by position for display
        by_position = defaultdict(list)
        for player in lineup:
            by_position[player['position']].append(player)
        
        position_names = {'G': 'GOALKEEPER', 'D': 'DEFENDERS', 'M': 'MIDFIELDERS', 'F': 'FORWARDS'}
        
        for pos in ['G', 'D', 'M', 'F']:
            if pos in by_position:
                print(f"\n{position_names[pos]} ({len(by_position[pos])}):")
                print("-" * 50)
                
                for player in by_position[pos]:
                    value_score = "[STEAL]" if player['value_ratio'] > 1.8 else "[VALUE]" if player['value_ratio'] > 1.4 else "[SOLID]"
                    diff_score = "[DIFF]" if player['ownership_pct'] < 30 else "[LOW]" if player['ownership_pct'] < 50 else "[POP]"
                    
                    print(f"{value_score} {diff_score} {player['name']:20} ({player['team']}) vs {player['opponent']}")
                    print(f"     ${player['salary']:5.2f} | {player['projected_points']:4.1f} pts | {player['value_ratio']:4.2f} pp$ | {player['ownership']}")
        
        print(f"\n{'='*50}")
        print(f"LINEUP SUMMARY")
        print(f"{'='*50}")
        print(f"Players: {len(lineup)}/11")
        print(f"Total Cost: ${total_cost:.2f} / $100.00")
        print(f"Remaining Budget: ${remaining_budget:.2f}")
        print(f"Projected Points: {total_points:.1f}")
        print(f"Average Cost Per Player: ${total_cost/len(lineup):.2f}")
        
        # Value insights
        bargain_count = len([p for p in lineup if p['salary'] == 5.0])
        diff_count = len([p for p in lineup if p['ownership_pct'] < 40])
        
        print(f"\nSTRATEGY INSIGHTS:")
        print(f"Minimum price players: {bargain_count}/11 (${bargain_count * 5:.0f} total)")
        print(f"Differential players: {diff_count}/11 (<40% owned)")
        print(f"Budget efficiency: {(total_cost/100)*100:.1f}%")
        
        return lineup
    
    def run(self):
        """Execute complete analysis"""
        print("FANTRAX VALUE HUNTER - COMPLETE VERSION")
        print("="*60)
        print("Analyzing all 633+ players for optimal Game Week 1 lineup")
        
        if not self.authenticate():
            return False
        
        if not self.fetch_all_players_paginated():
            return False
        
        self.show_top_values_by_position()
        lineup, remaining_budget = self.build_optimal_lineup()
        self.display_final_lineup(lineup, remaining_budget)
        
        print(f"\n[SUCCESS] Complete analysis finished!")
        print(f"Your optimal lineup is ready for Game Week 1!")
        return True

if __name__ == "__main__":
    optimizer = CompleteFantraxOptimizer()
    success = optimizer.run()
    
    if not success:
        print("[ERROR] Analysis failed. Check connection and try again.")
        sys.exit(1)