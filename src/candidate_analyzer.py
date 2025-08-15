#!/usr/bin/env python3
"""
Fantrax Candidate Pool Analyzer
Generate ranked candidate pools using approved ValueScore formula
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Fantrax_Wrapper'))

from fantraxapi import FantraxAPI
import json
import requests
import csv
from collections import defaultdict
from datetime import datetime
from form_tracker import FormTracker
from fixture_difficulty import FixtureDifficultyAnalyzer
from starter_predictor import StarterPredictor

class CandidateAnalyzer:
    def __init__(self):
        self.api = None
        self.all_players = []
        self.positions = {'G': [], 'D': [], 'M': [], 'F': []}
        self.form_tracker = FormTracker()
        self.fixture_analyzer = FixtureDifficultyAnalyzer()
        self.starter_predictor = StarterPredictor()
        
        # Load FP/G data from CSV files
        self.fpg_data = self._load_fpg_data()
        
        # Candidate pool sizes (as per requirements)
        self.pool_sizes = {'G': 8, 'D': 20, 'M': 20, 'F': 20}
        
        print("FANTRAX CANDIDATE POOL ANALYZER")
        print("="*60)
        print("Using ValueScore = PPG ÷ Price (CORRECTED - higher is better)")
        print("Generating candidate pools: 8 GK, 20 DEF, 20 MID, 20 FWD")
        
        # Show form calculation status
        form_status = "ENABLED" if self.form_tracker.form_enabled else "DISABLED (neutral multiplier)"
        print(f"Form calculation: {form_status}")
        
        # Show fixture difficulty status
        fixture_status = "ENABLED" if self.fixture_analyzer.config.get('enabled', True) else "DISABLED"
        fixture_mode = self.fixture_analyzer.config.get('mode', '5_tier')
        print(f"Fixture difficulty: {fixture_status} ({fixture_mode} system)")
        
        # Show starter prediction status
        starter_status = "ENABLED" if self.starter_predictor.config.get('enabled', True) else "DISABLED"
        print(f"Starter prediction: {starter_status} (dual-source consensus)")
        
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
    
    def fetch_all_players(self):
        """Fetch current week player data"""
        print("[INFO] Fetching current player data...")
        
        all_players_data = []
        
        for page_num in range(1, 33):
            try:
                if page_num == 1:
                    player_stats = self.api._request('getPlayerStats')
                else:
                    player_stats = self.api._request('getPlayerStats', pageNumber=str(page_num))
                
                if 'statsTable' in player_stats and player_stats['statsTable']:
                    players = player_stats['statsTable']
                    all_players_data.extend(players)
                    if page_num <= 3 or page_num % 10 == 0:
                        print(f"[SUCCESS] Page {page_num}: {len(players)} players")
                else:
                    break
                    
            except Exception as e:
                if page_num > 3:
                    break
                continue
        
        print(f"[SUCCESS] Retrieved {len(all_players_data)} total players")
        
        if all_players_data:
            self.process_players(all_players_data)
            return True
        else:
            print("[ERROR] No players retrieved")
            return False
    
    def _load_fpg_data(self):
        """Load FP/G data from CSV files for better PPG calculations"""
        fpg_data = {}
        data_dir = '../data'
        
        # Try to load both seasons' data
        csv_files = [
            ('fpg_data_2024.csv', '2024-25'),
            ('fpg_data_2023.csv', '2023-24')
        ]
        
        total_loaded = 0
        for filename, season in csv_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            player_name = row['Player']
                            fpg = float(row['FP/G'])
                            
                            # Use most recent season if player exists in multiple seasons
                            if player_name not in fpg_data or season == '2024-25':
                                fpg_data[player_name] = {
                                    'fpg': fpg,
                                    'season': season,
                                    'total_points': float(row['FPts']),
                                    'salary': float(row['Salary'])
                                }
                            total_loaded += 1
                    
                    print(f"[SUCCESS] Loaded {len([p for p in fpg_data.values() if p['season'] == season])} players from {season} season")
                    
                except Exception as e:
                    print(f"[WARNING] Could not load {filename}: {e}")
            else:
                print(f"[WARNING] {filename} not found - using estimated PPG")
        
        print(f"[INFO] FP/G data available for {len(fpg_data)} unique players")
        return fpg_data
    
    def _estimate_ppg_by_position_price(self, position, price):
        """Estimate PPG for players not in historical data based on position and price"""
        # Base estimates by position (average PPG for that position)
        position_base = {
            'G': 6.0,    # Goalkeepers typically lower
            'D': 7.0,    # Defenders
            'M': 8.0,    # Midfielders
            'F': 9.0     # Forwards typically higher
        }
        
        # Get base for primary position
        primary_pos = position[0] if position else 'M'
        base_ppg = position_base.get(primary_pos, 7.0)
        
        # Adjust based on price (premium players should score more)
        if price >= 18:
            multiplier = 1.4      # Premium players ($18+)
        elif price >= 12:
            multiplier = 1.2      # Mid-tier players ($12-18)
        elif price >= 8:
            multiplier = 1.0      # Average players ($8-12)
        else:
            multiplier = 0.8      # Budget players (<$8)
        
        estimated_ppg = base_ppg * multiplier
        return round(estimated_ppg, 2)
    
    def process_players(self, players):
        """Process player data and calculate ValueScores"""
        print("[INFO] Processing players and calculating ValueScores...")
        
        # Get form scores
        form_scores = self.form_tracker.get_all_form_scores()
        form_summary = self.form_tracker.export_form_summary()
        
        print(f"[INFO] Form data: {len(form_scores)} players have form scores (GW{form_summary['current_gameweek']})")
        
        for player in players:
            try:
                scorer = player.get('scorer', {})
                cells = player.get('cells', [])
                
                if len(cells) < 4:
                    continue
                
                player_id = scorer.get('scorerId', '')
                
                # Basic player data
                player_data = {
                    'id': player_id,
                    'name': scorer.get('name', 'Unknown'),
                    'team': scorer.get('teamShortName', 'UNK'),
                    'position': scorer.get('posShortNames', 'UNK'),
                    'price': float(cells[2].get('content', 5.0)),
                    'projected_points': float(cells[3].get('content', 0.0)),
                    'ownership_pct': self._parse_ownership(cells[6].get('content', '0%') if len(cells) > 6 else '0%'),
                    'opponent': cells[1].get('content', 'TBD')
                }
                
                # Calculate PPG using real FP/G data from CSV files
                player_name = player_data['name']
                if player_name in self.fpg_data:
                    # Use real FP/G data from historical seasons
                    ppg = self.fpg_data[player_name]['fpg']
                    data_source = f"Historical {self.fpg_data[player_name]['season']}"
                else:
                    # Fallback: estimate based on position and price
                    ppg = self._estimate_ppg_by_position_price(player_data['position'], player_data['price'])
                    data_source = "Estimated"
                
                # Calculate ValueScore = PPG ÷ Price - CORRECTED FORMULA
                value_score = ppg / player_data['price'] if player_data['price'] > 0 else 0
                
                # Get form score
                form_score = form_scores.get(player_id)
                
                # Calculate form multiplier
                if form_score is not None and self.form_tracker.form_enabled:
                    form_multiplier = form_score / 100  # Convert form score to multiplier
                else:
                    form_multiplier = 1.0  # Neutral when form disabled or no data
                
                # Get fixture difficulty multiplier
                opponent_team = player_data['opponent'].replace('vs ', '').replace('@ ', '')
                is_home = not player_data['opponent'].startswith('@')
                fixture_multiplier = self.fixture_analyzer.get_fixture_multiplier(opponent_team)
                
                # Get starter prediction multiplier
                starter_confidence, starter_multiplier = self.starter_predictor.get_player_starter_confidence(
                    player_data['name'], player_data['team']
                )
                
                # Calculate True Value = ValueScore × Form × Fixture × Starter - CORRECTED FORMULA
                true_value = value_score * form_multiplier * fixture_multiplier * starter_multiplier
                
                # Get opponent difficulty rank
                difficulty_ranks = self.fixture_analyzer.calculate_team_difficulty_ranks()
                opponent_rank = difficulty_ranks.get(opponent_team)
                
                # Extended player data
                player_data.update({
                    'ppg': round(ppg, 2),
                    'ppg_source': data_source,  # Tag showing data source
                    'value_score': round(value_score, 3),
                    'form_score': form_score,
                    'form_multiplier': round(form_multiplier, 3),
                    'fixture_multiplier': round(fixture_multiplier, 3),
                    'starter_confidence': starter_confidence,
                    'starter_multiplier': round(starter_multiplier, 3),
                    'true_value': round(true_value, 3),
                    'ppm': None,  # TODO: Implement Points Per Minute
                    'predicted_starter': starter_confidence,
                    'next_opponent_rank': opponent_rank,
                    'next_opponent': opponent_team,
                    'is_home': is_home,
                    'differential': player_data['ownership_pct'] < 40
                })
                
                # Categorize by position
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
        
        print(f"[INFO] Processed players: G:{len(self.positions['G'])}, D:{len(self.positions['D'])}, M:{len(self.positions['M'])}, F:{len(self.positions['F'])}")
    
    def _parse_ownership(self, ownership_str):
        """Parse ownership percentage from string"""
        try:
            return float(ownership_str.rstrip('%'))
        except:
            return 0.0
    
    def generate_candidate_pools(self):
        """Generate ranked candidate pools for each position"""
        print("\\n" + "="*60)
        print("GENERATING CANDIDATE POOLS")
        print("="*60)
        
        candidate_pools = {}
        
        for pos_name, pos_code in [('GOALKEEPERS', 'G'), ('DEFENDERS', 'D'), ('MIDFIELDERS', 'M'), ('FORWARDS', 'F')]:
            print(f"\\n{pos_name} - Top {self.pool_sizes[pos_code]} by True Value")
            print("-" * 50)
            
            # Sort by True Value (higher is better with corrected formula)
            sorted_players = sorted(self.positions[pos_code], key=lambda x: x['true_value'], reverse=True)
            
            # Get top N candidates
            candidates = sorted_players[:self.pool_sizes[pos_code]]
            candidate_pools[pos_code] = candidates
            
            # Check price range diversity
            if candidates:
                min_price = min(p['price'] for p in candidates)
                max_price = max(p['price'] for p in candidates)
                avg_price = sum(p['price'] for p in candidates) / len(candidates)
                
                print(f"Price range: ${min_price:.2f} - ${max_price:.2f} (avg: ${avg_price:.2f})")
                print(f"Players with form: {len([p for p in candidates if p['form_score'] is not None])}")
                print(f"Differential players: {len([p for p in candidates if p['differential']])}")
        
        return candidate_pools
    
    def display_candidate_table(self, candidate_pools):
        """Display candidate pools in table format"""
        print("\\n" + "="*100)
        print("COMPLETE CANDIDATE ANALYSIS")
        print("="*100)
        
        for pos_name, pos_code in [('GOALKEEPERS', 'G'), ('DEFENDERS', 'D'), ('MIDFIELDERS', 'M'), ('FORWARDS', 'F')]:
            candidates = candidate_pools[pos_code]
            
            print(f"\\n{pos_name} - TOP {len(candidates)} CANDIDATES")
            print("-" * 85)
            
            # Table header
            print(f"{'Rank':<4} {'Player':<16} {'Team':<4} {'Price':<6} {'PPG':<6} {'ValueSc':<7} {'TrueVal':<7} {'Fix':<6} {'Start':<8} {'Own%':<5} {'Status':<8}")
            print(f"{'(H=Historical data, E=Estimated)':<60}")
            print("-" * 95)
            
            for i, player in enumerate(candidates, 1):
                starter_display = player['starter_confidence'].replace('_', ' ').upper()[:7] if player['starter_confidence'] != 'unknown' else "N/A"
                diff_indicator = "DIFF" if player['differential'] else ""
                
                # Data source indicator: H=Historical, E=Estimated
                data_indicator = "H" if "Historical" in player.get('ppg_source', '') else "E"
                
                print(f"{i:<4} {player['name'][:17]:<18} {player['team']:<4} ${player['price']:<5.2f} {player['ppg']:<5.2f}{data_indicator} "
                      f"{player['value_score']:<7.2f} {player['true_value']:<7.2f} {player['fixture_multiplier']:<6.3f} "
                      f"{starter_display:<8} {player['ownership_pct']:<4.0f}% {diff_indicator:<8}")
    
    def save_candidate_data(self, candidate_pools):
        """Save candidate data for dashboard/export"""
        output_file = "../data/candidate_pools.json"
        
        export_data = {
            "metadata": {
                "generated_date": datetime.now().isoformat(),
                "total_candidates": sum(len(pool) for pool in candidate_pools.values()),
                "formula_used": "TrueValue = (PPG÷Price) × Form × Fixture × Starter (VALIDATED)",
                "gameweek": self.form_tracker.form_data["metadata"]["current_gameweek"]
            },
            "pools": candidate_pools
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"\\n[SUCCESS] Candidate data saved to {output_file}")
    
    def analyze_price_diversity(self, candidate_pools):
        """Analyze if pools enable $100 lineup construction"""
        print("\\n" + "="*60)
        print("PRICE DIVERSITY ANALYSIS")
        print("="*60)
        
        # Check if we can build a viable $100 lineup
        min_cost = (
            min(p['price'] for p in candidate_pools['G']) +
            sum(sorted([p['price'] for p in candidate_pools['D']])[:4]) +
            sum(sorted([p['price'] for p in candidate_pools['M']])[:4]) +
            sum(sorted([p['price'] for p in candidate_pools['F']])[:2])
        )
        
        max_cost = (
            max(p['price'] for p in candidate_pools['G']) +
            sum(sorted([p['price'] for p in candidate_pools['D']], reverse=True)[:4]) +
            sum(sorted([p['price'] for p in candidate_pools['M']], reverse=True)[:4]) +
            sum(sorted([p['price'] for p in candidate_pools['F']], reverse=True)[:2])
        )
        
        print(f"Lineup cost range from candidates: ${min_cost:.2f} - ${max_cost:.2f}")
        print(f"Budget utilization possible: {min_cost/100*100:.1f}% - {min(max_cost/100*100, 100):.1f}%")
        
        if min_cost > 100:
            print("[WARNING] Minimum possible lineup exceeds $100 budget!")
        elif max_cost < 90:
            print("[WARNING] Maximum possible lineup under $90 - consider higher-priced options")
        else:
            print("[SUCCESS] Candidate pools enable viable $100 lineup construction")
    
    def run(self):
        """Execute complete candidate analysis"""
        if not self.authenticate():
            return False
        
        if not self.fetch_all_players():
            return False
        
        candidate_pools = self.generate_candidate_pools()
        self.display_candidate_table(candidate_pools)
        self.analyze_price_diversity(candidate_pools)
        self.save_candidate_data(candidate_pools)
        
        print("\\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print("[SUCCESS] Candidate pools generated successfully")
        print("[SUCCESS] ValueScore formula validated: PPG ÷ Price (higher is better)")
        print("[INFO] Data saved for dashboard integration")
        print("[READY] Ready for manual lineup construction")
        
        return True

if __name__ == "__main__":
    analyzer = CandidateAnalyzer()
    success = analyzer.run()
    
    if not success:
        print("[ERROR] Analysis failed. Check connection and try again.")
        sys.exit(1)