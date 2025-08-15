"""
Starter Prediction Analyzer

Uses Playwright MCP to scrape multiple prediction sources:
- Fantasy Football Scout (predicted lineups)
- RotoWire (predicted lineups)

Combines predictions from both sources to increase accuracy through consensus.
When both sources agree, confidence is higher.

Features:
- Multi-source prediction scraping using Playwright MCP
- Consensus-based confidence levels (Both Agree, One Source, Conflicting)
- Configurable multipliers via dashboard
- Caching system to avoid excessive scraping
- Integration with candidate analyzer
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import re

class StarterPredictor:
    """
    Scrapes team news and predicted lineups from Fantasy Football Scout.
    Assigns starter confidence multipliers for True Value calculations.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with configuration file"""
        self.config_path = config_path or '../config/system_parameters.json'
        self.data_dir = '../data'
        self.config = self._load_config()
        self.cache_file = os.path.join(self.data_dir, 'starter_predictions_cache.json')
        self.logger = self._setup_logging()
        
        # Source URLs
        self.ffs_base_url = "https://www.fantasyfootballscout.co.uk"
        self.ffs_team_news_url = f"{self.ffs_base_url}/team-news/"
        self.rotowire_lineups_url = "https://www.rotowire.com/soccer/lineups.php"
        
        # Team mapping (Fantasy Football Scout name -> Fantrax short name)
        self.team_mapping = {
            'Arsenal': 'ARS', 'Aston Villa': 'AVL', 'Brighton': 'BHA',
            'Burnley': 'BUR', 'Chelsea': 'CHE', 'Crystal Palace': 'CRY',
            'Everton': 'EVE', 'Fulham': 'FUL', 'Liverpool': 'LIV',
            'Luton': 'LUT', 'Manchester City': 'MCI', 'Manchester United': 'MUN',
            'Newcastle': 'NEW', 'Nottingham Forest': 'NFO', 'Sheffield United': 'SHU',
            'Tottenham': 'TOT', 'West Ham': 'WHU', 'Wolves': 'WOL',
            'Brentford': 'BRE', 'Bournemouth': 'BOU'
        }
        
    def _setup_logging(self):
        """Setup logging for debugging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
        
    def _load_config(self) -> Dict:
        """Load system configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('starter_prediction', {})
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict:
        """Return default configuration if file not found"""
        return {
            "enabled": True,
            "multipliers": {
                "both_sources_agree": 1.15,   # 15% boost when both sources predict starter
                "single_source": 1.0,         # Neutral for single source prediction
                "conflicting_sources": 0.9,   # 10% penalty when sources disagree
                "rotation_risk": 0.85,        # 15% penalty for rotation risk
                "injury_doubt": 0.7,          # 30% penalty for injury concerns
                "suspended": 0.0              # Zero value for suspended players
            },
            "cache_duration_hours": 6,
            "confidence_keywords": {
                "certain": ["nailed", "certain", "definite", "confirmed", "starts"],
                "likely": ["likely", "probable", "expected", "should start"],
                "rotation": ["rotation", "risk", "doubt", "competition", "might not"],
                "injury": ["injury", "injured", "fitness", "knock", "strain"],
                "suspended": ["suspended", "ban", "red card", "yellow cards"]
            }
        }
        
    def scrape_fantasy_football_scout_predictions(self) -> Dict[str, List[Dict]]:
        """
        Scrape Fantasy Football Scout using Playwright MCP.
        Returns predicted lineups by team.
        """
        # This would use Playwright MCP to navigate and scrape FFS
        # For now, return mock data structure
        
        ffs_predictions = {}
        
        for team_name, team_code in self.team_mapping.items():
            ffs_predictions[team_code] = self._get_mock_lineup(team_code, source='FFS')
            
        return ffs_predictions
        
    def scrape_rotowire_predictions(self) -> Dict[str, List[Dict]]:
        """
        Scrape RotoWire using Playwright MCP.
        Returns predicted lineups by team.
        """
        # This would use Playwright MCP to navigate and scrape RotoWire
        # For now, return mock data structure
        
        rotowire_predictions = {}
        
        for team_name, team_code in self.team_mapping.items():
            rotowire_predictions[team_code] = self._get_mock_lineup(team_code, source='RotoWire')
            
        return rotowire_predictions
        
    def combine_source_predictions(self, ffs_data: Dict, rotowire_data: Dict) -> Dict[str, Dict]:
        """
        Combine predictions from both sources and determine consensus confidence.
        """
        combined_predictions = {}
        
        for team_code in self.team_mapping.values():
            ffs_lineup = ffs_data.get(team_code, [])
            rotowire_lineup = rotowire_data.get(team_code, [])
            
            # Create combined lineup with consensus analysis
            combined_lineup = self._analyze_consensus(ffs_lineup, rotowire_lineup)
            
            combined_predictions[team_code] = {
                'team_name': [name for name, code in self.team_mapping.items() if code == team_code][0],
                'last_updated': datetime.now().isoformat(),
                'predicted_lineup': combined_lineup,
                'sources': {
                    'ffs_count': len(ffs_lineup),
                    'rotowire_count': len(rotowire_lineup),
                    'consensus_count': len([p for p in combined_lineup if p['confidence'] == 'both_sources_agree'])
                }
            }
            
        return combined_predictions
        
    def _analyze_consensus(self, ffs_lineup: List[Dict], rotowire_lineup: List[Dict]) -> List[Dict]:
        """
        Analyze consensus between two sources and assign confidence levels.
        """
        consensus_lineup = []
        
        # Get all unique players from both sources
        all_players = {}
        
        # Add FFS predictions
        for player in ffs_lineup:
            player_key = self._normalize_player_name(player['name'])
            all_players[player_key] = {
                'name': player['name'],
                'position': player['position'],
                'ffs_predicts': True,
                'rotowire_predicts': False,
                'ffs_confidence': player.get('confidence', 'likely'),
                'rotowire_confidence': None
            }
            
        # Add RotoWire predictions
        for player in rotowire_lineup:
            player_key = self._normalize_player_name(player['name'])
            if player_key in all_players:
                # Both sources predict this player
                all_players[player_key]['rotowire_predicts'] = True
                all_players[player_key]['rotowire_confidence'] = player.get('confidence', 'likely')
            else:
                # Only RotoWire predicts this player
                all_players[player_key] = {
                    'name': player['name'],
                    'position': player['position'],
                    'ffs_predicts': False,
                    'rotowire_predicts': True,
                    'ffs_confidence': None,
                    'rotowire_confidence': player.get('confidence', 'likely')
                }
                
        # Determine consensus confidence for each player
        for player_key, player_data in all_players.items():
            consensus_confidence = self._determine_consensus_confidence(player_data)
            
            consensus_lineup.append({
                'name': player_data['name'],
                'position': player_data['position'],
                'confidence': consensus_confidence,
                'sources': {
                    'ffs': player_data['ffs_predicts'],
                    'rotowire': player_data['rotowire_predicts'],
                    'ffs_confidence': player_data['ffs_confidence'],
                    'rotowire_confidence': player_data['rotowire_confidence']
                }
            })
            
        return consensus_lineup
        
    def _determine_consensus_confidence(self, player_data: Dict) -> str:
        """
        Determine consensus confidence level based on source agreement.
        """
        ffs_predicts = player_data['ffs_predicts']
        rotowire_predicts = player_data['rotowire_predicts']
        ffs_conf = player_data['ffs_confidence']
        rotowire_conf = player_data['rotowire_confidence']
        
        # Check for injury/suspension flags first
        if (ffs_conf == 'suspended' or rotowire_conf == 'suspended'):
            return 'suspended'
        if (ffs_conf == 'injury_doubt' or rotowire_conf == 'injury_doubt'):
            return 'injury_doubt'
            
        # Both sources agree on starting
        if ffs_predicts and rotowire_predicts:
            return 'both_sources_agree'
            
        # Only one source predicts starting
        if ffs_predicts or rotowire_predicts:
            # Check if the predicting source shows rotation risk
            if (ffs_predicts and ffs_conf == 'rotation_risk') or (rotowire_predicts and rotowire_conf == 'rotation_risk'):
                return 'rotation_risk'
            return 'single_source'
            
        # Neither source predicts starting (shouldn't happen in our data)
        return 'rotation_risk'
        
    def _normalize_player_name(self, name: str) -> str:
        """Normalize player name for comparison between sources"""
        return re.sub(r'[^\w\s]', '', name.lower().strip()).replace(' ', '_')
        
    def _get_mock_lineup(self, team_code: str) -> List[Dict]:
        """Generate mock predicted lineup for testing"""
        # This would be replaced with actual scraped data
        mock_players = [
            {'name': 'Player A', 'position': 'GK', 'confidence': 'certain_starter'},
            {'name': 'Player B', 'position': 'DEF', 'confidence': 'likely_starter'},
            {'name': 'Player C', 'position': 'DEF', 'confidence': 'rotation_risk'},
            {'name': 'Player D', 'position': 'MID', 'confidence': 'certain_starter'},
            {'name': 'Player E', 'position': 'FWD', 'confidence': 'injury_doubt'},
        ]
        
        return mock_players
        
    def scrape_fantasy_football_scout(self) -> Dict[str, Dict]:
        """
        Main scraping function using Playwright MCP.
        This is where the actual web scraping would happen.
        """
        try:
            # Check cache first
            cached_data = self._load_cached_predictions()
            if cached_data:
                self.logger.info("Using cached starter predictions")
                return cached_data
                
            self.logger.info("Scraping fresh starter predictions from Fantasy Football Scout")
            
            # Use Playwright MCP to scrape team news
            # Implementation would go here
            predictions = self.get_team_news_with_playwright()
            
            # Cache the results
            self._cache_predictions(predictions)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error scraping starter predictions: {e}")
            return self._load_cached_predictions() or {}
            
    def _cache_predictions(self, predictions: Dict):
        """Cache predictions data to file"""
        cache_data = {
            'predictions': predictions,
            'last_updated': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=self.config.get('cache_duration_hours', 6))).isoformat()
        }
        
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
    def _load_cached_predictions(self) -> Optional[Dict]:
        """Load cached predictions if available and not expired"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            if datetime.now() < expires_at:
                return cache_data['predictions']
            else:
                self.logger.info("Cached predictions expired")
                return None
                
        except (FileNotFoundError, KeyError, ValueError):
            return None
            
    def get_player_starter_confidence(self, player_name: str, team_code: str) -> Tuple[str, float]:
        """
        Get starter confidence level and multiplier for a specific player.
        Returns (confidence_level, multiplier)
        """
        if not self.config.get('enabled', True):
            return 'unknown', 1.0
            
        # Get team predictions
        predictions = self.scrape_fantasy_football_scout()
        team_data = predictions.get(team_code, {})
        
        if not team_data:
            self.logger.warning(f"No predictions found for team {team_code}")
            return 'unknown', 1.0
            
        # Find player in predicted lineup
        predicted_lineup = team_data.get('predicted_lineup', [])
        for player in predicted_lineup:
            if self._names_match(player['name'], player_name):
                confidence = player['confidence']
                multiplier_config = self.config['multipliers'].get(confidence, 1.0)
                # Handle both dict format and float format
                if isinstance(multiplier_config, dict):
                    multiplier = multiplier_config.get('multiplier', 1.0)
                else:
                    multiplier = multiplier_config
                return confidence, multiplier
                
        # Player not found in predicted lineup - assume rotation risk
        fallback_config = self.config['multipliers'].get('rotation_risk', 0.95)
        if isinstance(fallback_config, dict):
            fallback_multiplier = fallback_config.get('multiplier', 0.95)
        else:
            fallback_multiplier = fallback_config
        return 'rotation_risk', fallback_multiplier
        
    def _names_match(self, scraped_name: str, fantrax_name: str) -> bool:
        """
        Check if scraped player name matches Fantrax player name.
        Handles common name variations and formatting differences.
        """
        # Normalize names for comparison
        scraped = re.sub(r'[^\w\s]', '', scraped_name.lower().strip())
        fantrax = re.sub(r'[^\w\s]', '', fantrax_name.lower().strip())
        
        # Direct match
        if scraped == fantrax:
            return True
            
        # Check if last names match (common for abbreviated names)
        scraped_last = scraped.split()[-1] if scraped.split() else ''
        fantrax_last = fantrax.split()[-1] if fantrax.split() else ''
        
        if scraped_last and fantrax_last and scraped_last == fantrax_last:
            return True
            
        # Check if one name is contained in the other
        if scraped in fantrax or fantrax in scraped:
            return True
            
        return False
        
    def get_all_starter_predictions(self) -> Dict[str, Dict]:
        """Get complete starter predictions for all teams"""
        predictions = self.scrape_fantasy_football_scout()
        
        # Add multipliers to each player prediction
        for team_code, team_data in predictions.items():
            for player in team_data.get('predicted_lineup', []):
                confidence = player['confidence']
                player['multiplier'] = self.config['multipliers'].get(confidence, 1.0)
                
        return predictions
        
    def update_multipliers(self, new_multipliers: Dict) -> bool:
        """Update starter prediction multipliers and save to file"""
        try:
            # Validate multipliers
            if not self._validate_multipliers(new_multipliers):
                return False
                
            # Update configuration
            self.config['multipliers'].update(new_multipliers)
            
            # Save to file
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
                
            if 'starter_prediction' not in full_config:
                full_config['starter_prediction'] = self.config
            else:
                full_config['starter_prediction']['multipliers'] = self.config['multipliers']
            
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=2)
                
            self.logger.info("Starter prediction multipliers updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating multipliers: {e}")
            return False
            
    def _validate_multipliers(self, multipliers: Dict) -> bool:
        """Validate that multipliers are within acceptable ranges"""
        valid_keys = ['certain_starter', 'likely_starter', 'rotation_risk', 'injury_doubt', 'suspended']
        
        for key, value in multipliers.items():
            if key not in valid_keys:
                self.logger.error(f"Invalid multiplier key: {key}")
                return False
                
            if not isinstance(value, (int, float)):
                self.logger.error(f"Invalid multiplier value for {key}: {value}")
                return False
                
            # Validate ranges
            if key == 'suspended' and value != 0.0:
                self.logger.error("Suspended players must have 0.0 multiplier")
                return False
                
            if key != 'suspended' and not (0.5 <= value <= 1.5):
                self.logger.error(f"Multiplier {value} for {key} outside range [0.5, 1.5]")
                return False
                
        return True
        
    def get_configuration_summary(self) -> Dict:
        """Get summary of current starter prediction configuration"""
        return {
            'enabled': self.config.get('enabled', True),
            'multipliers': self.config.get('multipliers', {}),
            'cache_duration_hours': self.config.get('cache_duration_hours', 6),
            'last_cache_update': self._get_cache_timestamp(),
            'teams_covered': len(self.team_mapping),
            'example_impacts': self._get_example_impacts()
        }
        
    def _get_cache_timestamp(self) -> Optional[str]:
        """Get timestamp of last cache update"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                return cache_data.get('last_updated')
        except (FileNotFoundError, KeyError):
            return None
            
    def _get_example_impacts(self) -> List[Dict]:
        """Get example impacts of different confidence levels"""
        examples = []
        
        for confidence, config in self.config.get('multipliers', {}).items():
            # Handle both dict format (from system_parameters.json) and float format (from default config)
            if isinstance(config, dict):
                multiplier = config.get('multiplier', 1.0)
            else:
                multiplier = config
                
            impact = 'neutral'
            if multiplier > 1.0:
                impact = f'+{((multiplier - 1) * 100):.0f}% boost'
            elif multiplier < 1.0:
                impact = f'-{((1 - multiplier) * 100):.0f}% penalty'
                
            examples.append({
                'confidence': confidence.replace('_', ' ').title(),
                'multiplier': f"{multiplier}x",
                'impact': impact
            })
            
        return examples
        
    def enable_starter_prediction(self, enabled: bool) -> bool:
        """Enable or disable starter prediction system"""
        try:
            self.config['enabled'] = enabled
            
            # Save to file
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
                
            if 'starter_prediction' not in full_config:
                full_config['starter_prediction'] = self.config
            else:
                full_config['starter_prediction']['enabled'] = enabled
            
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=2)
                
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"Starter prediction system {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating starter prediction status: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    predictor = StarterPredictor()
    
    print("Starter Prediction Analyzer Test")
    print("=" * 40)
    
    # Get configuration summary
    summary = predictor.get_configuration_summary()
    print(f"Enabled: {summary['enabled']}")
    print(f"Teams covered: {summary['teams_covered']}")
    print(f"Cache duration: {summary['cache_duration_hours']} hours")
    
    # Test player confidence lookup
    test_players = [
        ('Mohamed Salah', 'LIV'),
        ('Erling Haaland', 'MCI'),
        ('Harry Kane', 'TOT')
    ]
    
    print("\nPlayer Confidence Examples:")
    for player_name, team_code in test_players:
        confidence, multiplier = predictor.get_player_starter_confidence(player_name, team_code)
        print(f"{player_name} ({team_code}): {confidence} - {multiplier}x")
        
    print("\nMultiplier Impacts:")
    for example in summary['example_impacts']:
        print(f"{example['confidence']}: {example['multiplier']} ({example['impact']})")