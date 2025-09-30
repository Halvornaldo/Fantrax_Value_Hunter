"""
NPxG-Based Fixture Difficulty Multiplier System

Calculates fixture difficulty multipliers based on team NPxG and NPxGA stats
from Understat, with position-specific formulas and home/away adjustments.

Features:
- Position-specific multiplier calculations (FWD, MID, DEF, GK)
- Multi-position handling (D/M, M/F)
- Home/away advantage adjustments
- League average normalization
- Configurable weights and adjustments
"""

import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import ScraperFC as sfc

logger = logging.getLogger(__name__)

class NPxGFixtureMultiplier:
    """
    Calculate fixture difficulty multipliers using NPxG and NPxGA data
    """

    def __init__(self, db_config: Dict, config_path: str = None):
        """Initialize with database configuration"""
        self.db_config = db_config
        self.config_path = config_path or 'config/system_parameters.json'
        self.config = self._load_config()
        self.understat = sfc.Understat()

        # Team name mapping from Understat to Fantrax codes
        self.team_mapping = {
            'Arsenal': 'ARS',
            'Aston Villa': 'AVL',
            'Brighton': 'BHA',
            'Bournemouth': 'BOU',
            'Brentford': 'BRE',
            'Burnley': 'BUR',
            'Chelsea': 'CHE',
            'Crystal Palace': 'CRY',
            'Everton': 'EVE',
            'Fulham': 'FUL',
            'Leeds United': 'LEE',
            'Liverpool': 'LIV',
            'Manchester City': 'MCI',
            'Manchester United': 'MUN',
            'Newcastle United': 'NEW',
            'Nottingham Forest': 'NFO',
            'Sunderland': 'SUN',
            'Tottenham': 'TOT',
            'West Ham': 'WHU',
            'Wolverhampton Wanderers': 'WOL'
        }

        # Team code aliases for compatibility with other systems
        self.team_aliases = {
            'BRF': 'BRE',  # Brentford: Fantrax uses BRF, NPxG uses BRE
            'NOT': 'NFO',  # Nottingham Forest: Fantrax uses NOT, NPxG uses NFO
        }

    def resolve_team_alias(self, team_code: str) -> str:
        """
        Resolve team code aliases to the canonical code used in team_metrics

        Args:
            team_code: Team code that might be an alias (e.g., BRF, NOT)

        Returns:
            Canonical team code for database lookup (e.g., BRE, NFO)
        """
        return self.team_aliases.get(team_code, team_code)

    def _load_config(self) -> Dict:
        """Load NPxG fixture configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('npxg_fixture', self._get_default_config())
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Default NPxG fixture configuration"""
        return {
            "enabled": True,
            "weight": 1.0,
            "home_away_adjustments": {
                "attacking": {
                    "home_boost": 1.10,
                    "away_penalty": 0.90
                },
                "defensive": {
                    "home_boost": 1.15,
                    "away_penalty": 0.85
                }
            },
            "position_mappings": {
                "pure_mid_attack_weight": 0.75,
                "pure_mid_defense_weight": 0.25
            },
            "bounds": {
                "min": 0.4,
                "max": 2.5
            }
        }

    def fetch_and_update_team_stats(self, season: str = "2025/2026") -> bool:
        """
        Fetch latest NPxG/NPxGA data from Understat and update database
        """
        try:
            logger.info(f"Fetching NPxG data for {season}")

            # Get league tables from Understat (includes NPxG, NPxGA)
            tables = self.understat.scrape_league_tables(year=season, league='EPL')
            overall_table = tables[0]

            # Calculate league averages
            league_avg_npxg = overall_table['NPxG'].mean()
            league_avg_npxga = overall_table['NPxGA'].mean()

            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Update team stats
            for _, team in overall_table.iterrows():
                team_name = team['Team']
                fantrax_code = self.team_mapping.get(team_name, team_name[:3].upper())

                cursor.execute("""
                    INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (team_code) DO UPDATE SET
                        team_name = EXCLUDED.team_name,
                        npxg = EXCLUDED.npxg,
                        npxga = EXCLUDED.npxga,
                        npxgd = EXCLUDED.npxgd,
                        matches_played = EXCLUDED.matches_played,
                        last_updated = EXCLUDED.last_updated
                """, (
                    fantrax_code,
                    team_name,
                    float(team['NPxG']),
                    float(team['NPxGA']),
                    float(team['NPxGD']),
                    int(team['M']),
                    datetime.now()
                ))

            # Update league averages
            cursor.execute("""
                INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
                VALUES ('AVG', 'League Average', %s, %s, %s, %s, %s)
                ON CONFLICT (team_code) DO UPDATE SET
                    npxg = EXCLUDED.npxg,
                    npxga = EXCLUDED.npxga,
                    npxgd = EXCLUDED.npxgd,
                    matches_played = EXCLUDED.matches_played,
                    last_updated = EXCLUDED.last_updated
            """, (
                float(league_avg_npxg),
                float(league_avg_npxga),
                float(league_avg_npxg - league_avg_npxga),
                20,  # All 20 teams
                datetime.now()
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Updated NPxG stats for {len(overall_table)} teams")
            logger.info(f"League averages - NPxG: {league_avg_npxg:.2f}, NPxGA: {league_avg_npxga:.2f}")

            return True

        except Exception as e:
            logger.error(f"Error updating team stats: {e}")
            return False

    def get_team_stats(self, team_code: str) -> Optional[Dict]:
        """Get NPxG stats for a specific team"""
        try:
            # Resolve team alias to canonical code
            canonical_code = self.resolve_team_alias(team_code)

            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated
                FROM team_metrics
                WHERE team_code = %s
            """, (canonical_code,))

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error fetching team stats for {team_code} (canonical: {self.resolve_team_alias(team_code)}): {e}")
            return None

    def get_league_averages(self) -> Dict[str, float]:
        """Get league average NPxG and NPxGA"""
        avg_stats = self.get_team_stats('AVG')
        if avg_stats:
            return {
                'npxg': float(avg_stats['npxg']),
                'npxga': float(avg_stats['npxga'])
            }
        else:
            # Fallback to manual calculation if AVG row doesn't exist
            logger.warning("League averages not found, calculating from all teams")
            return self._calculate_league_averages()

    def _calculate_league_averages(self) -> Dict[str, float]:
        """Calculate league averages from all team data"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT AVG(npxg) as avg_npxg, AVG(npxga) as avg_npxga
                FROM team_metrics
                WHERE team_code != 'AVG' AND npxg IS NOT NULL
            """)

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0] is not None:
                return {
                    'npxg': float(result[0]),
                    'npxga': float(result[1])
                }
            else:
                # Ultimate fallback
                return {'npxg': 8.0, 'npxga': 8.0}

        except Exception as e:
            logger.error(f"Error calculating league averages: {e}")
            return {'npxg': 8.0, 'npxga': 8.0}

    def parse_opponent_info(self, next_opponent: str) -> Tuple[str, bool]:
        """
        Parse next_opponent field to extract team code and home/away status

        Args:
            next_opponent: e.g., "vs BUR", "@ EVE", "vs BHA Sat 4:00PM"

        Returns:
            (opponent_code, is_home)
        """
        if not next_opponent:
            return '', True

        is_home = next_opponent.startswith('vs ')
        # Remove prefix and extract team code (first 3 characters after vs/@ and space)
        clean_opponent = next_opponent.replace('vs ', '').replace('@ ', '').strip()
        opponent_code = clean_opponent.split()[0] if clean_opponent else ''

        return opponent_code, is_home

    def determine_player_type(self, position: str) -> str:
        """
        Determine player type for home/away adjustments

        Returns: 'attacking', 'defensive', or 'mixed'
        """
        if not position:
            return 'mixed'

        position = position.upper()

        # Goalkeeper - always defensive
        if 'G' in position:
            return 'defensive'

        # Multi-position handling
        if 'D' in position and 'M' in position:  # D/M -> defensive
            return 'defensive'

        if 'M' in position and ('F' in position or 'A' in position):  # M/F, M/A -> attacking
            return 'attacking'

        # Single positions
        if 'F' in position or 'A' in position:  # Forward/Attacker
            return 'attacking'

        if 'D' in position:  # Defender
            return 'defensive'

        if 'M' in position:  # Pure midfielder - mixed type
            return 'mixed'

        return 'mixed'  # Default

    def calculate_base_multiplier(self, position: str, opponent_npxg: float, opponent_npxga: float,
                                 league_avg_npxg: float, league_avg_npxga: float) -> float:
        """
        Calculate base NPxG multiplier based on position
        """
        if not position:
            return 1.0

        position = position.upper()

        # Goalkeeper - defensive formula
        if 'G' in position:
            return league_avg_npxg / max(opponent_npxg, 0.1)

        # Multi-position handling
        if 'D' in position and 'M' in position:  # D/M -> treat as defender
            return league_avg_npxg / max(opponent_npxg, 0.1)

        if 'M' in position and ('F' in position or 'A' in position):  # M/F, M/A -> treat as attacker
            return max(opponent_npxga, 0.1) / league_avg_npxga

        # Single positions
        if 'F' in position or 'A' in position:  # Pure attacker
            return max(opponent_npxga, 0.1) / league_avg_npxga

        if 'D' in position:  # Pure defender
            return league_avg_npxg / max(opponent_npxg, 0.1)

        if 'M' in position:  # Pure midfielder - weighted combination
            attack_weight = self.config['position_mappings']['pure_mid_attack_weight']
            defense_weight = self.config['position_mappings']['pure_mid_defense_weight']

            attacking_mult = max(opponent_npxga, 0.1) / league_avg_npxga
            defensive_mult = league_avg_npxg / max(opponent_npxg, 0.1)

            return (attack_weight * attacking_mult) + (defense_weight * defensive_mult)

        return 1.0  # Default

    def apply_home_away_adjustment(self, base_multiplier: float, player_type: str, is_home: bool) -> float:
        """
        Apply home/away adjustments based on player type
        """
        adjustments = self.config['home_away_adjustments']

        if player_type == 'attacking':
            if is_home:
                adjustment = adjustments['attacking']['home_boost']
            else:
                adjustment = adjustments['attacking']['away_penalty']

        elif player_type == 'defensive':
            if is_home:
                adjustment = adjustments['defensive']['home_boost']
            else:
                adjustment = adjustments['defensive']['away_penalty']

        else:  # mixed (pure midfielders)
            # Weighted average of attacking and defensive adjustments
            attack_weight = self.config['position_mappings']['pure_mid_attack_weight']
            defense_weight = self.config['position_mappings']['pure_mid_defense_weight']

            if is_home:
                attacking_adj = adjustments['attacking']['home_boost']
                defensive_adj = adjustments['defensive']['home_boost']
            else:
                attacking_adj = adjustments['attacking']['away_penalty']
                defensive_adj = adjustments['defensive']['away_penalty']

            adjustment = (attack_weight * attacking_adj) + (defense_weight * defensive_adj)

        return base_multiplier * adjustment

    def calculate_fixture_multiplier(self, player_data: Dict) -> float:
        """
        Calculate complete NPxG fixture multiplier for a player

        Args:
            player_data: Dictionary containing player info (position, next_opponent, etc.)

        Returns:
            Final fixture multiplier
        """
        if not self.config.get('enabled', True):
            return 1.0

        try:
            # Parse opponent and home/away status
            next_opponent = player_data.get('next_opponent', '')
            opponent_code, is_home = self.parse_opponent_info(next_opponent)

            if not opponent_code:
                logger.debug(f"No opponent found for player {player_data.get('player_id', 'unknown')}")
                return 1.0

            # Get opponent stats
            opponent_stats = self.get_team_stats(opponent_code)
            if not opponent_stats:
                logger.warning(f"No stats found for opponent {opponent_code}")
                return 1.0

            # Get league averages
            league_averages = self.get_league_averages()

            # Get player position and type
            position = player_data.get('position', 'M')
            player_type = self.determine_player_type(position)

            # Calculate base multiplier - ensure all values are float to avoid Decimal/float mixing
            base_multiplier = self.calculate_base_multiplier(
                position=position,
                opponent_npxg=float(opponent_stats['npxg']),
                opponent_npxga=float(opponent_stats['npxga']),
                league_avg_npxg=float(league_averages['npxg']),
                league_avg_npxga=float(league_averages['npxga'])
            )

            # Apply home/away adjustment
            adjusted_multiplier = self.apply_home_away_adjustment(
                base_multiplier=base_multiplier,
                player_type=player_type,
                is_home=is_home
            )

            # Apply user weight control
            weight = self.config.get('weight', 1.0)
            final_multiplier = 1 + (adjusted_multiplier - 1) * weight

            # Apply bounds
            bounds = self.config.get('bounds', {'min': 0.4, 'max': 2.5})
            final_multiplier = max(bounds['min'], min(bounds['max'], final_multiplier))

            return round(final_multiplier, 3)

        except Exception as e:
            logger.error(f"Error calculating NPxG fixture multiplier: {e}")
            return 1.0

    def bulk_update_player_multipliers(self) -> int:
        """
        Update NPxG fixture multipliers for all active players

        Returns:
            Number of players updated
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get all active players with their positions and opponents
            cursor.execute("""
                SELECT player_id, position, next_opponent
                FROM player_metrics
                WHERE next_opponent IS NOT NULL AND next_opponent != ''
            """)

            players = cursor.fetchall()
            updated_count = 0

            for player in players:
                player_data = dict(player)
                multiplier = self.calculate_fixture_multiplier(player_data)

                # Update the player's NPxG fixture multiplier
                cursor.execute("""
                    UPDATE player_metrics
                    SET npxg_fixture_multiplier = %s
                    WHERE player_id = %s
                """, (multiplier, player['player_id']))

                updated_count += 1

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Updated NPxG fixture multipliers for {updated_count} players")
            return updated_count

        except Exception as e:
            logger.error(f"Error bulk updating player multipliers: {e}")
            return 0

    def get_multiplier_summary(self) -> Dict:
        """Get summary of current NPxG fixture configuration and examples"""
        config = self.config
        league_averages = self.get_league_averages()

        return {
            'enabled': config.get('enabled', True),
            'weight': config.get('weight', 1.0),
            'league_averages': league_averages,
            'home_away_adjustments': config.get('home_away_adjustments', {}),
            'position_mappings': config.get('position_mappings', {}),
            'bounds': config.get('bounds', {}),
            'last_update': self._get_last_update_time()
        }

    def _get_last_update_time(self) -> str:
        """Get the last time team stats were updated"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MAX(last_updated)
                FROM team_metrics
                WHERE team_code != 'AVG'
            """)

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0]:
                return result[0].isoformat()
            else:
                return "Never"

        except Exception:
            return "Unknown"


# Utility functions for external use
def get_npxg_multiplier_for_player(player_data: Dict, db_config: Dict, weight: float = None) -> float:
    """
    Convenience function to get NPxG fixture multiplier for a single player

    Args:
        player_data: Player information dictionary
        db_config: Database configuration
        weight: Optional weight override (0.80-1.20, defaults to config value)
    """
    calculator = NPxGFixtureMultiplier(db_config)

    # Override weight if provided
    if weight is not None:
        calculator.config['weight'] = weight

    return calculator.calculate_fixture_multiplier(player_data)


def update_all_team_stats(db_config: Dict, season: str = "2025/2026") -> bool:
    """
    Convenience function to update all team NPxG stats from Understat
    """
    calculator = NPxGFixtureMultiplier(db_config)
    return calculator.fetch_and_update_team_stats(season)


if __name__ == "__main__":
    # Test the NPxG fixture multiplier system
    import sys
    sys.path.append('..')

    # Test database config
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }

    calculator = NPxGFixtureMultiplier(db_config)

    # Test updating team stats
    print("Testing NPxG Fixture Multiplier System")
    print("="*50)

    success = calculator.fetch_and_update_team_stats()
    print(f"Team stats update: {'Success' if success else 'Failed'}")

    # Test calculating multipliers for different scenarios
    test_players = [
        {'player_id': 'test1', 'position': 'F', 'next_opponent': 'vs BUR'},  # Attacker vs weak defense
        {'player_id': 'test2', 'position': 'D', 'next_opponent': '@ MCI'},   # Defender vs strong attack
        {'player_id': 'test3', 'position': 'M', 'next_opponent': 'vs AVL'},  # Midfielder vs average
        {'player_id': 'test4', 'position': 'G', 'next_opponent': '@ ARS'},   # Goalkeeper away
    ]

    print("\nExample Multiplier Calculations:")
    for player in test_players:
        multiplier = calculator.calculate_fixture_multiplier(player)
        print(f"{player['position']} {player['next_opponent']}: {multiplier:.3f}x")

    # Get summary
    summary = calculator.get_multiplier_summary()
    print(f"\nSystem Summary:")
    print(f"Enabled: {summary['enabled']}")
    print(f"Weight: {summary['weight']}")
    print(f"League Avg NPxG: {summary['league_averages']['npxg']:.2f}")
    print(f"League Avg NPxGA: {summary['league_averages']['npxga']:.2f}")