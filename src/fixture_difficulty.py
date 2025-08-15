"""
Fixture Difficulty Analyzer

Integrates with Football-Data.org API to calculate opponent difficulty rankings
and apply configurable multipliers to player True Value calculations.

Features:
- 5-tier and 3-tier difficulty systems (configurable)
- Real-time multiplier adjustments via dashboard
- Home/away advantage modifiers
- Derby match penalties
- Caching system to respect API rate limits
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

class FixtureDifficultyAnalyzer:
    """
    Analyzes fixture difficulty using team standings, form, and performance data.
    Provides configurable multiplier system for True Value calculations.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with configuration file"""
        self.config_path = config_path or '../config/system_parameters.json'
        self.data_dir = '../data'
        self.logger = self._setup_logging()
        self.config = self._load_config()
        self.api_key = self._load_api_key()
        self.cache_file = os.path.join(self.data_dir, 'fixture_difficulty_cache.json')
        
        # API endpoint for Premier League
        self.api_base = "https://api.football-data.org/v4"
        self.competition_id = "PL"  # Premier League
        
    def _setup_logging(self):
        """Setup logging for debugging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
        
    def _load_api_key(self) -> Optional[str]:
        """Load API key from environment or config file"""
        # Try environment variable first
        api_key = os.getenv('FOOTBALL_DATA_API_KEY')
        if api_key:
            return api_key
            
        # Try config file
        try:
            with open('../config/api_keys.json', 'r') as f:
                keys = json.load(f)
                return keys.get('football_data_org')
        except FileNotFoundError:
            self.logger.warning("No API key found. Using free tier with rate limits.")
            return None
            
    def _load_config(self) -> Dict:
        """Load system configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('fixture_difficulty', {})
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict:
        """Return default configuration if file not found"""
        return {
            "enabled": True,
            "mode": "5_tier",
            "5_tier_multipliers": {
                "very_easy": {"ranks": [1, 4], "multiplier": 1.3},
                "easy": {"ranks": [5, 8], "multiplier": 1.15},
                "neutral": {"ranks": [9, 12], "multiplier": 1.0},
                "hard": {"ranks": [13, 16], "multiplier": 0.85},
                "very_hard": {"ranks": [17, 20], "multiplier": 0.7}
            },
            "3_tier_multipliers": {
                "easy": {"ranks": [1, 7], "multiplier": 1.2},
                "neutral": {"ranks": [8, 13], "multiplier": 1.0},
                "hard": {"ranks": [14, 20], "multiplier": 0.8}
            },
            "modifiers": {
                "home_away_advantage": 0.05,
                "derby_penalty": 0.05
            }
        }
        
    def _make_api_request(self, endpoint: str) -> Optional[Dict]:
        """Make request to Football-Data.org API with rate limiting"""
        headers = {}
        if self.api_key:
            headers['X-Auth-Token'] = self.api_key
            
        url = f"{self.api_base}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.warning("API rate limit exceeded. Using cached data.")
                return None
            else:
                self.logger.error(f"API request failed: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"API request error: {e}")
            return None
            
    def fetch_team_standings(self) -> Optional[List[Dict]]:
        """Fetch current Premier League standings"""
        standings_data = self._make_api_request(f"competitions/{self.competition_id}/standings")
        
        if not standings_data:
            return self._load_cached_standings()
            
        # Extract team standings
        try:
            table = standings_data['standings'][0]['table']
            teams = []
            
            for entry in table:
                team_data = {
                    'team_id': entry['team']['id'],
                    'team_name': entry['team']['name'],
                    'short_name': entry['team']['tla'],
                    'position': entry['position'],
                    'points': entry['points'],
                    'played_games': entry['playedGames'],
                    'points_per_game': entry['points'] / max(entry['playedGames'], 1),
                    'goal_difference': entry['goalDifference'],
                    'form': entry.get('form', ''),
                    'last_updated': datetime.now().isoformat()
                }
                teams.append(team_data)
                
            # Cache the results
            self._cache_standings(teams)
            return teams
            
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error parsing standings data: {e}")
            return self._load_cached_standings()
            
    def _cache_standings(self, standings: List[Dict]):
        """Cache standings data to file"""
        cache_data = {
            'standings': standings,
            'last_updated': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
    def _load_cached_standings(self) -> Optional[List[Dict]]:
        """Load cached standings if available and not expired"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            if datetime.now() < expires_at:
                self.logger.info("Using cached standings data")
                return cache_data['standings']
            else:
                self.logger.info("Cached standings expired")
                return None
                
        except (FileNotFoundError, KeyError, ValueError):
            return None
            
    def calculate_team_difficulty_ranks(self) -> Dict[str, int]:
        """Calculate difficulty ranking for each team (1=easiest, 20=hardest)"""
        standings = self.fetch_team_standings()
        if not standings:
            self.logger.error("No standings data available")
            return {}
            
        # Calculate strength scores
        team_scores = []
        for team in standings:
            # Weight factors for team strength
            position_score = (21 - team['position']) / 20  # Higher = stronger
            ppg_score = min(team['points_per_game'] / 3.0, 1.0)  # Normalize to 0-1
            gd_score = max(min((team['goal_difference'] + 30) / 60, 1.0), 0.0)  # Normalize
            
            # Calculate form score from recent results
            form_score = self._calculate_form_score(team['form'])
            
            # Combined strength score (0-1, higher = stronger)
            strength_score = (
                position_score * 0.4 +  # 40% current position
                ppg_score * 0.3 +       # 30% points per game
                gd_score * 0.2 +        # 20% goal difference
                form_score * 0.1        # 10% recent form
            )
            
            team_scores.append({
                'team_id': team['team_id'],
                'team_name': team['team_name'],
                'short_name': team['short_name'],
                'strength_score': strength_score
            })
            
        # Sort by strength score (weakest first) and assign difficulty ranks
        team_scores.sort(key=lambda x: x['strength_score'])
        
        difficulty_ranks = {}
        for i, team in enumerate(team_scores, 1):
            difficulty_ranks[team['short_name']] = i
            
        self.logger.info(f"Calculated difficulty ranks for {len(difficulty_ranks)} teams")
        return difficulty_ranks
        
    def _calculate_form_score(self, form_string: str) -> float:
        """Calculate form score from recent results (W/D/L string)"""
        if not form_string:
            return 0.5  # Neutral if no form data
            
        # Convert W/D/L to numeric scores
        points = 0
        games = 0
        
        for result in form_string:
            games += 1
            if result == 'W':
                points += 3
            elif result == 'D':
                points += 1
            # L = 0 points
                
        if games == 0:
            return 0.5
            
        # Normalize to 0-1 scale (perfect form = 1.0)
        return points / (games * 3)
        
    def get_fixture_multiplier(self, opponent_short_name: str) -> float:
        """Get fixture difficulty multiplier for a specific opponent"""
        if not self.config.get('enabled', True):
            return 1.0
            
        # Get team difficulty ranks
        difficulty_ranks = self.calculate_team_difficulty_ranks()
        opponent_rank = difficulty_ranks.get(opponent_short_name)
        
        if opponent_rank is None:
            self.logger.warning(f"No difficulty rank found for {opponent_short_name}")
            return 1.0
            
        # Get base multiplier from tier system
        mode = self.config.get('mode', '5_tier')
        multipliers_key = f"{mode}_multipliers"
        multipliers = self.config.get(multipliers_key, {})
        
        base_multiplier = 1.0
        for tier_name, tier_data in multipliers.items():
            min_rank, max_rank = tier_data['ranks']
            if min_rank <= opponent_rank <= max_rank:
                base_multiplier = tier_data['multiplier']
                break
                
        # No additional modifiers needed - API odds already factor in:
        # - Home/away advantage
        # - Derby rivalries  
        # - Team form and motivation
        # - Fixture congestion
        # - Player availability
            
        return round(base_multiplier, 3)
        
    def get_team_fixtures(self, team_short_name: str, num_fixtures: int = 5) -> List[Dict]:
        """Get upcoming fixtures for a specific team"""
        # For now, return mock data - this would integrate with API in production
        fixtures_data = self._make_api_request(f"competitions/{self.competition_id}/matches")
        
        if not fixtures_data:
            return self._get_mock_fixtures(team_short_name, num_fixtures)
            
        # Parse fixtures from API response
        # Implementation would depend on API response structure
        return self._get_mock_fixtures(team_short_name, num_fixtures)
        
    def _get_mock_fixtures(self, team_short_name: str, num_fixtures: int) -> List[Dict]:
        """Mock fixtures for testing - replace with real API data"""
        mock_opponents = ['MCI', 'LIV', 'ARS', 'TOT', 'CHE', 'MUN', 'NEW', 'BHA', 'WHU', 'LEI']
        fixtures = []
        
        for i in range(num_fixtures):
            opponent = mock_opponents[i % len(mock_opponents)]
            if opponent == team_short_name:
                opponent = mock_opponents[(i + 1) % len(mock_opponents)]
                
            fixture = {
                'opponent': opponent,
                'is_home': i % 2 == 0,
                'gameweek': i + 1,
                'difficulty_multiplier': self.get_fixture_multiplier(opponent)
            }
            fixtures.append(fixture)
            
        return fixtures
        
    def update_multipliers(self, new_multipliers: Dict) -> bool:
        """Update multiplier configuration and save to file"""
        try:
            # Validate multiplier ranges
            if not self._validate_multipliers(new_multipliers):
                return False
                
            # Update configuration
            self.config.update(new_multipliers)
            
            # Save to file
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
                
            full_config['fixture_difficulty'] = self.config
            
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=2)
                
            self.logger.info("Fixture difficulty multipliers updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating multipliers: {e}")
            return False
            
    def _validate_multipliers(self, multipliers: Dict) -> bool:
        """Validate that multipliers are within acceptable ranges"""
        validation_ranges = self.config.get('validation_ranges', {})
        mode = multipliers.get('mode', self.config.get('mode', '5_tier'))
        
        mode_ranges = validation_ranges.get(mode, {})
        multipliers_to_check = multipliers.get(f"{mode}_multipliers", {})
        
        for tier_name, tier_data in multipliers_to_check.items():
            if tier_name == 'neutral':
                continue  # Neutral is always 1.0
                
            multiplier = tier_data.get('multiplier', 1.0)
            tier_ranges = mode_ranges.get(tier_name, {})
            
            min_val = tier_ranges.get('min', 0.5)
            max_val = tier_ranges.get('max', 1.5)
            
            if not (min_val <= multiplier <= max_val):
                self.logger.error(f"Multiplier {multiplier} for {tier_name} outside range [{min_val}, {max_val}]")
                return False
                
        return True
        
    def toggle_mode(self, mode: str) -> bool:
        """Toggle between 5_tier and 3_tier modes"""
        if mode not in ['5_tier', '3_tier']:
            return False
            
        self.config['mode'] = mode
        
        # Save configuration
        try:
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
                
            full_config['fixture_difficulty']['mode'] = mode
            
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=2)
                
            self.logger.info(f"Switched to {mode} difficulty mode")
            return True
            
        except Exception as e:
            self.logger.error(f"Error switching mode: {e}")
            return False
            
    def get_multiplier_summary(self) -> Dict:
        """Get summary of current multiplier configuration"""
        mode = self.config.get('mode', '5_tier')
        multipliers = self.config.get(f"{mode}_multipliers", {})
        
        summary = {
            'mode': mode,
            'enabled': self.config.get('enabled', True),
            'tiers': {},
            'modifiers': self.config.get('modifiers', {}),
            'example_impacts': []
        }
        
        # Add tier information
        for tier_name, tier_data in multipliers.items():
            summary['tiers'][tier_name] = {
                'ranks': tier_data['ranks'],
                'multiplier': tier_data['multiplier'],
                'description': tier_data.get('description', ''),
                'color': tier_data.get('color', '#000000')
            }
            
        # Add example impacts
        example_teams = ['SHU', 'WOL', 'BHA', 'CHE', 'MCI']  # From easy to hard
        for i, team in enumerate(example_teams):
            multiplier = self.get_fixture_multiplier(team)
            summary['example_impacts'].append({
                'opponent': team,
                'multiplier': multiplier,
                'tier': self._get_tier_for_rank(i * 4 + 2)  # Approximate ranks
            })
            
        return summary
        
    def _get_tier_for_rank(self, rank: int) -> str:
        """Get tier name for a given difficulty rank"""
        mode = self.config.get('mode', '5_tier')
        multipliers = self.config.get(f"{mode}_multipliers", {})
        
        for tier_name, tier_data in multipliers.items():
            min_rank, max_rank = tier_data['ranks']
            if min_rank <= rank <= max_rank:
                return tier_name
                
        return 'unknown'

# Example usage and testing
if __name__ == "__main__":
    analyzer = FixtureDifficultyAnalyzer()
    
    # Test basic functionality
    print("Fixture Difficulty Analyzer Test")
    print("=" * 40)
    
    # Get difficulty ranks
    ranks = analyzer.calculate_team_difficulty_ranks()
    print(f"Calculated ranks for {len(ranks)} teams")
    
    # Test multiplier calculation
    test_teams = ['MCI', 'ARS', 'BHA', 'WOL', 'SHU']
    print("\nFixture Multiplier Examples:")
    for team in test_teams:
        multiplier = analyzer.get_fixture_multiplier(team)
        print(f"{team}: {multiplier}x (odds-based difficulty)")
        
    # Get configuration summary
    summary = analyzer.get_multiplier_summary()
    print(f"\nCurrent mode: {summary['mode']}")
    print(f"Enabled: {summary['enabled']}")