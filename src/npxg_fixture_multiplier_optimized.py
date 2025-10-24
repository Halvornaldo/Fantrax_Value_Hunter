"""
Optimized NPxG Fixture Multiplier with Session Caching
This version caches database lookups during a single calculation session
"""

import logging
from typing import Dict, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class NPxGFixtureSession:
    """
    A session-based calculator that caches data for efficient batch processing
    Caches are only valid for the duration of a single recalculation
    """

    def __init__(self, db_config: Dict, npxg_weight: float):
        self.db_config = db_config
        self.npxg_weight = npxg_weight

        # Session caches - populated once per recalculation
        self.team_stats_cache = {}
        self.league_averages = None
        self.team_aliases = {
            'BRF': 'BRE',  # Brentford
            'NOT': 'NFO',  # Nottingham Forest
            'MAC': 'MCI',  # Manchester City
            'MAU': 'MUN',  # Manchester United
        }

        # Home/away adjustments
        self.home_adjustments = {
            'attacking': 1.10,
            'defensive': 1.15
        }
        self.away_adjustments = {
            'attacking': 0.90,
            'defensive': 0.85
        }

        # Position mappings
        self.position_mappings = {
            'pure_mid_attack_weight': 0.75,
            'pure_mid_defense_weight': 0.25
        }

        # Bounds
        self.min_multiplier = 0.4
        self.max_multiplier = 2.5

        # Pre-load all data at session start
        self._initialize_session()

    def _initialize_session(self):
        """Load all team data and league averages once at session start"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Load all team stats in one query
            cursor.execute("""
                SELECT team_code, team_name, npxg, npxga
                FROM team_metrics
                WHERE npxg IS NOT NULL
            """)

            for row in cursor.fetchall():
                self.team_stats_cache[row['team_code']] = {
                    'npxg': float(row['npxg']),
                    'npxga': float(row['npxga']),
                    'team_name': row['team_name']
                }

            # Calculate league averages
            if 'AVG' in self.team_stats_cache:
                self.league_averages = {
                    'npxg': self.team_stats_cache['AVG']['npxg'],
                    'npxga': self.team_stats_cache['AVG']['npxga']
                }
            else:
                # Calculate from all teams
                valid_teams = [k for k in self.team_stats_cache.keys() if k != 'AVG']
                if valid_teams:
                    avg_npxg = sum(self.team_stats_cache[t]['npxg'] for t in valid_teams) / len(valid_teams)
                    avg_npxga = sum(self.team_stats_cache[t]['npxga'] for t in valid_teams) / len(valid_teams)
                    self.league_averages = {
                        'npxg': avg_npxg,
                        'npxga': avg_npxga
                    }
                else:
                    self.league_averages = {'npxg': 8.0, 'npxga': 8.0}

            cursor.close()
            conn.close()

            # Count actual teams (excluding AVG)
            actual_teams = len([k for k in self.team_stats_cache.keys() if k != 'AVG'])
            logger.info(f"NPxG session initialized: {actual_teams} teams loaded, "
                       f"league avg NPxG={self.league_averages['npxg']:.2f}")

        except Exception as e:
            logger.error(f"Error initializing NPxG session: {e}")
            # Fallback values
            self.league_averages = {'npxg': 8.0, 'npxga': 8.0}

    def calculate_multiplier(self, player_data: Dict) -> float:
        """
        Calculate NPxG fixture multiplier for a player
        Uses cached data for efficiency
        """
        position = player_data.get('position', 'M')
        next_opponent = player_data.get('next_opponent', '')
        is_home = player_data.get('is_home', True)

        if not next_opponent:
            return 1.0

        # Resolve team alias if needed
        opponent_code = self.team_aliases.get(next_opponent, next_opponent)

        # Get opponent stats from cache
        opponent_stats = self.team_stats_cache.get(opponent_code)
        if not opponent_stats:
            return 1.0

        # Calculate base multiplier based on position
        base_mult = self._calculate_base_multiplier(
            position,
            opponent_stats['npxg'],
            opponent_stats['npxga']
        )

        # Apply home/away adjustment
        player_type = self._determine_player_type(position)
        if player_type == 'attacking':
            adjustment = self.home_adjustments['attacking'] if is_home else self.away_adjustments['attacking']
        elif player_type == 'defensive':
            adjustment = self.home_adjustments['defensive'] if is_home else self.away_adjustments['defensive']
        else:
            # Mixed type - average of attacking and defensive
            if is_home:
                adjustment = (self.home_adjustments['attacking'] + self.home_adjustments['defensive']) / 2
            else:
                adjustment = (self.away_adjustments['attacking'] + self.away_adjustments['defensive']) / 2

        final_mult = base_mult * adjustment

        # Apply bounds
        return max(self.min_multiplier, min(self.max_multiplier, final_mult))

    def _calculate_base_multiplier(self, position: str, opponent_npxg: float, opponent_npxga: float) -> float:
        """Calculate base multiplier based on position and opponent stats"""
        position = position.upper()

        # Handle multi-position players
        if 'D' in position and 'M' in position:
            # D/M players - defensive focus
            attack_component = (opponent_npxga / self.league_averages['npxga'])
            defense_component = (self.league_averages['npxg'] / opponent_npxg) if opponent_npxg > 0 else 1.0
            base = (attack_component * 0.3 + defense_component * 0.7)

        elif 'M' in position and ('F' in position or 'A' in position):
            # M/F or M/A players - attacking focus
            attack_component = (opponent_npxga / self.league_averages['npxga'])
            defense_component = (self.league_averages['npxg'] / opponent_npxg) if opponent_npxg > 0 else 1.0
            base = (attack_component * 0.7 + defense_component * 0.3)

        elif 'F' in position or 'A' in position:
            # Pure forwards - mainly affected by opponent's defensive weakness
            base = (opponent_npxga / self.league_averages['npxga'])

        elif 'D' in position:
            # Pure defenders - mainly affected by opponent's attacking threat
            base = (self.league_averages['npxg'] / opponent_npxg) if opponent_npxg > 0 else 1.0

        elif 'G' in position:
            # Goalkeepers - similar to defenders but more extreme
            base = (self.league_averages['npxg'] / opponent_npxg) if opponent_npxg > 0 else 1.0

        elif 'M' in position:
            # Pure midfielders - balanced
            attack_component = (opponent_npxga / self.league_averages['npxga'])
            defense_component = (self.league_averages['npxg'] / opponent_npxg) if opponent_npxg > 0 else 1.0
            base = (attack_component * self.position_mappings['pure_mid_attack_weight'] +
                   defense_component * self.position_mappings['pure_mid_defense_weight'])
        else:
            base = 1.0

        # Apply weight adjustment
        return 1.0 + (base - 1.0) * self.npxg_weight

    def _determine_player_type(self, position: str) -> str:
        """Determine if player is attacking, defensive, or mixed"""
        if not position:
            return 'mixed'

        position = position.upper()

        # Goalkeeper - always defensive
        if 'G' in position:
            return 'defensive'

        # Multi-position handling
        if 'D' in position and 'M' in position:
            return 'defensive'

        if 'M' in position and ('F' in position or 'A' in position):
            return 'attacking'

        # Single positions
        if 'F' in position or 'A' in position:
            return 'attacking'

        if 'D' in position:
            return 'defensive'

        if 'M' in position:
            return 'mixed'

        return 'mixed'


def get_npxg_multiplier_for_session(player_data: Dict, session: NPxGFixtureSession) -> float:
    """
    Calculate multiplier using a pre-initialized session
    Much more efficient for batch processing
    """
    return session.calculate_multiplier(player_data)