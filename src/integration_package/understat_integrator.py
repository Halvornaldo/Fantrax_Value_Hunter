#!/usr/bin/env python3
"""
Understat Integration Module
Clean, production-ready component for integrating Understat per-90 stats into Value Hunter
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# ScraperFC is optional - only needed for live scraping (not used on Railway)
try:
    import ScraperFC as sfc
    SCRAPERFC_AVAILABLE = True
except (ImportError, FileNotFoundError):
    sfc = None
    SCRAPERFC_AVAILABLE = False

# Add the src directory to the path to import UnifiedNameMatcher
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Fantrax_Value_Hunter', 'src'))
from name_matching.unified_matcher import UnifiedNameMatcher


class UnderstatIntegrator:
    """Production-ready Understat integration for Value Hunter"""

    # Team mapping from Understat names to Fantrax codes
    TEAM_MAPPING = {
        'Arsenal': 'ARS',
        'Aston Villa': 'AVL',
        'Brighton': 'BHA',
        'Bournemouth': 'BOU',
        'Brentford': 'BRF',
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
        'Nottingham Forest': 'NOT',
        'Sunderland': 'SUN',
        'Tottenham': 'TOT',
        'West Ham': 'WHU',
        'Wolverhampton Wanderers': 'WOL'
    }

    def __init__(self, db_config):
        """
        Initialize integrator with database config

        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.understat = sfc.Understat() if SCRAPERFC_AVAILABLE else None
        self.name_matcher = UnifiedNameMatcher(db_config)

    def extract_understat_per90_stats(self, season="2025/2026", leagues=["EPL"]):
        """
        Extract per-90 stats from Understat for specified leagues

        Returns:
            pd.DataFrame: Players with xG90, xA90, xGI90, and minutes
        """
        if not SCRAPERFC_AVAILABLE:
            print("ScraperFC not available - use JSON import instead")
            return pd.DataFrame()

        all_players = []

        for league in leagues:
            try:
                data = self.understat.scrape_all_teams_data(season, league, as_df=False)

                if not data:
                    continue

                for team_url, team_data in data.items():
                    if 'players_data' in team_data:
                        players_df = pd.DataFrame(team_data['players_data'])

                        if not players_df.empty:
                            team_name = team_url.split('/')[-2].replace('_', ' ')
                            players_df['team'] = team_name
                            players_df['league'] = league

                            # Ensure numeric types
                            players_df['minutes'] = pd.to_numeric(players_df.get('time', 0), errors='coerce').fillna(0)
                            players_df['games'] = pd.to_numeric(players_df.get('games', 0), errors='coerce').fillna(0)
                            players_df['xG'] = pd.to_numeric(players_df.get('xG', 0), errors='coerce').fillna(0)
                            players_df['xA'] = pd.to_numeric(players_df.get('xA', 0), errors='coerce').fillna(0)

                            # Calculate per-90 stats
                            players_df['xG90'] = players_df.apply(
                                lambda row: (row['xG'] * 90 / row['minutes']) if row['minutes'] > 0 else 0, axis=1
                            )
                            players_df['xA90'] = players_df.apply(
                                lambda row: (row['xA'] * 90 / row['minutes']) if row['minutes'] > 0 else 0, axis=1
                            )
                            players_df['xGI90'] = players_df['xG90'] + players_df['xA90']

                            all_players.append(players_df)

            except Exception as e:
                print(f"Error processing {league}: {e}")
                continue

        if all_players:
            return pd.concat(all_players, ignore_index=True)
        else:
            return pd.DataFrame()

    def match_fantrax_names(self, understat_df):
        """
        Match Understat players to Fantrax players using UnifiedNameMatcher

        Args:
            understat_df: DataFrame with Understat players

        Returns:
            pd.DataFrame: Matched players with fantrax_id and matching metadata
        """
        matched_players = []
        unmatched_players = []

        for idx, player in understat_df.iterrows():
            understat_name = player['player_name']
            understat_team = player.get('team')

            # Map Understat team name to Fantrax team code
            fantrax_team = self.TEAM_MAPPING.get(understat_team, understat_team)

            # Use UnifiedNameMatcher for intelligent matching
            match_result = self.name_matcher.match_player(
                source_name=understat_name,
                source_system='understat',
                team=fantrax_team
            )

            if match_result['fantrax_id']:
                # Successful match
                player_data = player.to_dict()
                player_data['fantrax_id'] = match_result['fantrax_id']
                player_data['fantrax_name'] = match_result['fantrax_name']
                player_data['match_confidence'] = match_result['confidence']
                player_data['match_type'] = match_result['match_type']
                player_data['needs_review'] = match_result['needs_review']
                player_data['mapping_id'] = match_result['mapping_id']
                matched_players.append(player_data)
            else:
                # No match found - track for review
                player_data = player.to_dict()
                player_data['suggested_matches'] = match_result['suggested_matches']
                unmatched_players.append(player_data)

        matched_df = pd.DataFrame(matched_players)
        unmatched_df = pd.DataFrame(unmatched_players)

        return matched_df, unmatched_df


    def create_xgi_multiplier_table(self, matched_players_df):
        """
        Create xGI multiplier lookup table for True Value calculations

        Args:
            matched_players_df: DataFrame with matched players and xGI90

        Returns:
            dict: fantrax_id -> xGI90 multiplier mapping
        """
        multiplier_table = {}

        for idx, player in matched_players_df.iterrows():
            fantrax_id = player['fantrax_id']
            xgi90 = player['xGI90']

            # Convert xGI90 to multiplier (could be 1 + xGI90, or custom formula)
            # For now, using xGI90 directly as multiplier
            multiplier_table[fantrax_id] = xgi90

        return multiplier_table

    def generate_integration_data(self, season="2025/2026", leagues=["EPL"]):
        """
        Generate complete integration data ready for Value Hunter

        Returns:
            tuple: (matched_players_df, unmatched_players_df, multiplier_table, stats_summary)
        """
        # Extract Understat data
        understat_df = self.extract_understat_per90_stats(season, leagues)

        if understat_df.empty:
            return None, None, None, None

        # Match names using UnifiedNameMatcher
        matched_players_df, unmatched_players_df = self.match_fantrax_names(understat_df)

        # Create multiplier table
        multiplier_table = self.create_xgi_multiplier_table(matched_players_df)

        # Generate comprehensive summary stats
        stats_summary = {
            'total_understat_players': len(understat_df),
            'successfully_matched': len(matched_players_df),
            'unmatched_players': len(unmatched_players_df),
            'match_rate': len(matched_players_df) / len(understat_df) * 100 if len(understat_df) > 0 else 0,
            'avg_xGI90': matched_players_df['xGI90'].mean() if not matched_players_df.empty else 0,
            'top_xGI90_player': matched_players_df.loc[matched_players_df['xGI90'].idxmax()]['player_name'] if not matched_players_df.empty else None,
            'max_xGI90': matched_players_df['xGI90'].max() if not matched_players_df.empty else 0,
            'high_confidence_matches': len(matched_players_df[matched_players_df['match_confidence'] >= 90]) if not matched_players_df.empty else 0,
            'needs_review_count': len(matched_players_df[matched_players_df['needs_review']]) if not matched_players_df.empty else 0,
            'mapping_statistics': self.name_matcher.get_mapping_statistics()
        }

        return matched_players_df, unmatched_players_df, multiplier_table, stats_summary


def test_integration():
    """Test the integration module"""

    # Test database config
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }

    integrator = UnderstatIntegrator(db_config)

    try:
        matched_players, unmatched_players, multiplier_table, stats = integrator.generate_integration_data()

        if matched_players is not None:
            print(f"Integration test successful!")
            print(f"Total Understat players: {stats['total_understat_players']}")
            print(f"Successfully matched: {stats['successfully_matched']}")
            print(f"Unmatched players: {stats['unmatched_players']}")
            print(f"Match rate: {stats['match_rate']:.1f}%")
            print(f"High confidence matches: {stats['high_confidence_matches']}")
            print(f"Needs review: {stats['needs_review_count']}")
            if stats['top_xGI90_player']:
                print(f"Top xGI90 player: {stats['top_xGI90_player']} ({stats['max_xGI90']:.3f})")

            return True
        else:
            print("Integration test failed - no data extracted")
            return False

    except Exception as e:
        print(f"Integration test failed: {e}")
        return False


if __name__ == "__main__":
    test_integration()
