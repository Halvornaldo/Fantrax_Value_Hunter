#!/usr/bin/env python3
"""
Trend Analysis Engine - Retrospective Formula Calculations
Fantasy Football Value Hunter

Purpose: Apply V2.0 Enhanced Formula to raw historical data with ANY parameter set
This allows testing different formulas on same raw data for consistent trend analysis

Features:
- Apply current or custom parameters to historical raw data
- Calculate form multipliers using EWMA on raw points scored
- Calculate fixture multipliers using raw odds data  
- Calculate xGI multipliers using raw xG data
- Generate trend data for visualization
- Compare different parameter sets

Author: Claude Code Assistant
Date: 2025-08-23
Version: 1.0
"""

import math
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendAnalysisEngine:
    """
    Engine for applying V2.0 Enhanced Formula to raw historical data
    Enables consistent trend analysis and parameter comparison
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize the trend analysis engine"""
        self.db_config = db_config
        logger.info("TrendAnalysisEngine initialized")
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def calculate_historical_trends(self, 
                                   gameweek_start: int,
                                   gameweek_end: int,
                                   parameters: Optional[Dict] = None,
                                   player_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Apply V2.0 formula to raw historical data with specified parameters
        
        Args:
            gameweek_start: First gameweek to analyze
            gameweek_end: Last gameweek to analyze  
            parameters: Parameter set to use (uses current if None)
            player_ids: List of specific players to analyze (all if None)
            
        Returns:
            List of calculated values for each player/gameweek combination
        """
        logger.info(f"Calculating trends for GW{gameweek_start}-{gameweek_end}")
        
        if parameters is None:
            parameters = self._load_current_parameters()
        
        results = []
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Process each gameweek
            for gw in range(gameweek_start, gameweek_end + 1):
                logger.info(f"Processing gameweek {gw}")
                
                # Get raw data for this gameweek
                raw_data = self._fetch_raw_data(cursor, gw, player_ids)
                
                # Calculate each player's values using raw data
                for player_data in raw_data:
                    try:
                        calculated_values = self._calculate_player_values_from_raw(
                            cursor, player_data, gw, parameters
                        )
                        
                        # Add metadata
                        calculated_values.update({
                            'gameweek': gw,
                            'calculation_timestamp': datetime.now(),
                            'parameters_used': parameters
                        })
                        
                        results.append(calculated_values)
                        
                    except Exception as e:
                        logger.error(f"Error calculating for {player_data.get('player_id', 'unknown')} GW{gw}: {e}")
                        continue
        
        logger.info(f"Generated {len(results)} trend data points")
        return results
    
    def compare_parameter_sets(self,
                              parameter_sets: List[Dict],
                              gameweek_start: int,
                              gameweek_end: int,
                              player_ids: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        Compare how different parameter sets would have performed on same raw data
        
        Args:
            parameter_sets: List of parameter sets to compare (each with 'name' and 'parameters')
            gameweek_start: First gameweek to analyze
            gameweek_end: Last gameweek to analyze
            player_ids: List of specific players (all if None)
            
        Returns:
            Dictionary mapping parameter set names to their calculated trends
        """
        logger.info(f"Comparing {len(parameter_sets)} parameter sets")
        
        comparison_results = {}
        
        for param_set in parameter_sets:
            set_name = param_set.get('name', 'Unnamed')
            parameters = param_set.get('parameters', {})
            
            logger.info(f"Calculating trends for parameter set: {set_name}")
            
            trends = self.calculate_historical_trends(
                gameweek_start, gameweek_end, parameters, player_ids
            )
            
            comparison_results[set_name] = trends
        
        return comparison_results
    
    def _fetch_raw_data(self, cursor, gameweek: int, player_ids: Optional[List[str]] = None) -> List[Dict]:
        """Fetch raw data for a specific gameweek"""
        
        # Build query with optional player filtering
        where_clause = "WHERE r.gameweek = %s"
        params = [gameweek]
        
        if player_ids:
            placeholders = ','.join(['%s'] * len(player_ids))
            where_clause += f" AND r.player_id IN ({placeholders})"
            params.extend(player_ids)
        
        # Use the raw_data_complete view for comprehensive data
        query = f"""
            SELECT 
                r.player_id,
                r.gameweek,
                r.name,
                r.team,
                r.position,
                r.price,
                r.fpts,
                r.minutes_played,
                r.xg90,
                r.xa90,
                r.xgi90,
                r.baseline_xgi,
                r.historical_ppg,
                r.opponent,
                r.is_home,
                r.fixture_difficulty,
                r.home_odds,
                r.draw_odds,
                r.away_odds,
                r.is_predicted_starter,
                r.rotation_risk,
                
                -- Get historical baseline data (once per player)
                p.baseline_xgi as player_baseline_xgi
                
            FROM raw_data_complete r
            LEFT JOIN players p ON r.player_id = p.id
            {where_clause}
            ORDER BY r.player_id
        """
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def _calculate_player_values_from_raw(self, 
                                        cursor, 
                                        player_data: Dict,
                                        current_gw: int,
                                        parameters: Dict) -> Dict:
        """
        Calculate V2.0 Enhanced values using only raw data
        This mimics the V2.0 engine but works from raw snapshots
        """
        player_id = player_data['player_id']
        
        # Step 1: Calculate dynamic blended PPG from raw form data
        blended_ppg, current_weight = self._calculate_blended_ppg_from_raw(
            cursor, player_id, current_gw, parameters
        )
        
        # Step 2: Calculate form multiplier using raw points history
        form_mult = self._calculate_form_multiplier_from_raw(
            cursor, player_id, current_gw, parameters
        )
        
        # Step 3: Calculate fixture multiplier using raw odds data
        fixture_mult = self._calculate_fixture_multiplier_from_raw(
            player_data, parameters
        )
        
        # Step 4: Calculate starter multiplier (use prediction or default)
        starter_mult = self._calculate_starter_multiplier_from_raw(
            player_data, parameters
        )
        
        # Step 5: Calculate xGI multiplier using raw xG data
        xgi_mult = self._calculate_xgi_multiplier_from_raw(
            player_data, parameters
        )
        
        # Step 6: Apply multiplier caps
        v2_config = parameters.get('formula_optimization_v2', {})
        multiplier_caps = v2_config.get('multiplier_caps', {})
        
        form_mult = self._apply_multiplier_cap(form_mult, 'form', multiplier_caps)
        fixture_mult = self._apply_multiplier_cap(fixture_mult, 'fixture', multiplier_caps)
        xgi_mult = self._apply_multiplier_cap(xgi_mult, 'xgi', multiplier_caps)
        
        # Step 7: Calculate True Value
        true_value = blended_ppg * form_mult * fixture_mult * starter_mult * xgi_mult
        
        # Apply global cap
        global_cap = multiplier_caps.get('global', 3.0)
        max_allowed = blended_ppg * global_cap
        true_value = min(true_value, max_allowed)
        
        # Step 8: Calculate ROI
        price = player_data.get('price', 1.0) or 1.0
        roi = true_value / price if price > 0 else 0
        
        return {
            'player_id': player_id,
            'name': player_data.get('name'),
            'team': player_data.get('team'), 
            'position': player_data.get('position'),
            'price': price,
            'fpts': player_data.get('fpts'),
            'blended_ppg': blended_ppg,
            'current_season_weight': current_weight,
            'form_multiplier': form_mult,
            'fixture_multiplier': fixture_mult, 
            'starter_multiplier': starter_mult,
            'xgi_multiplier': xgi_mult,
            'true_value': true_value,
            'roi': roi,
            'value_score': roi  # Legacy compatibility
        }
    
    def _calculate_blended_ppg_from_raw(self, cursor, player_id: str, current_gw: int, parameters: Dict) -> Tuple[float, float]:
        """Calculate dynamically blended PPG using raw form data"""
        
        # Get raw form data
        cursor.execute("""
            SELECT points_scored, games_played 
            FROM raw_form_snapshots 
            WHERE player_id = %s AND gameweek <= %s
            ORDER BY gameweek
        """, [player_id, current_gw])
        
        form_data = cursor.fetchall()
        
        if not form_data:
            # Use default baseline if no current data
            return 6.0, 0.0
        
        # Calculate current season PPG
        total_points = sum(row['points_scored'] for row in form_data)
        games_played = sum(row['games_played'] for row in form_data)
        current_ppg = total_points / games_played if games_played > 0 else 0.0
        
        # Get historical baseline
        cursor.execute("""
            SELECT historical_ppg FROM players WHERE id = %s
        """, [player_id])
        result = cursor.fetchone()
        historical_ppg = result['historical_ppg'] if result and result['historical_ppg'] else 6.0
        
        # Dynamic blending logic (from V2.0)
        v2_config = parameters.get('formula_optimization_v2', {})
        blending = v2_config.get('dynamic_blending', {})
        
        baseline_switchover = blending.get('baseline_switchover_gw', 10)
        current_weight_param = blending.get('current_weight_parameter', 7)
        
        if current_gw <= baseline_switchover:
            # Early season - use historical baseline
            return historical_ppg, 0.0
        else:
            # Calculate blending weight
            N = games_played
            K = current_weight_param
            current_weight = min(1.0, (N-1)/(K-1)) if K > 1 else 1.0
            
            # Blend historical and current
            blended_ppg = historical_ppg * (1 - current_weight) + current_ppg * current_weight
            return blended_ppg, current_weight
    
    def _calculate_form_multiplier_from_raw(self, cursor, player_id: str, current_gw: int, parameters: Dict) -> float:
        """Calculate EWMA form multiplier using raw points data"""
        
        v2_config = parameters.get('formula_optimization_v2', {})
        form_config = v2_config.get('exponential_form', {})
        
        if not form_config.get('enabled', True):
            return 1.0
            
        lookback_games = form_config.get('lookback_games', 8)
        alpha = form_config.get('ewma_alpha', 0.87)
        
        # Get recent form data
        cursor.execute("""
            SELECT points_scored 
            FROM raw_form_snapshots 
            WHERE player_id = %s AND gameweek < %s 
            ORDER BY gameweek DESC 
            LIMIT %s
        """, [player_id, current_gw, lookback_games])
        
        form_data = cursor.fetchall()
        
        if len(form_data) < 2:
            return 1.0
        
        # Calculate EWMA
        points = [row['points_scored'] for row in form_data]
        
        ewma_score = points[0]  # Most recent game
        for i in range(1, len(points)):
            ewma_score = alpha * ewma_score + (1 - alpha) * points[i]
        
        # Get player's season average for baseline
        cursor.execute("""
            SELECT AVG(points_scored) as avg_points
            FROM raw_form_snapshots 
            WHERE player_id = %s AND gameweek < %s
        """, [player_id, current_gw])
        
        result = cursor.fetchone()
        avg_points = result['avg_points'] if result and result['avg_points'] else ewma_score
        
        # Convert to multiplier
        if avg_points > 0:
            multiplier = ewma_score / avg_points
            # Apply form-specific bounds
            min_mult = form_config.get('min_multiplier', 0.5)
            max_mult = form_config.get('max_multiplier', 2.0)
            return max(min_mult, min(max_mult, multiplier))
        
        return 1.0
    
    def _calculate_fixture_multiplier_from_raw(self, player_data: Dict, parameters: Dict) -> float:
        """Calculate fixture multiplier using raw odds data"""
        
        v2_config = parameters.get('formula_optimization_v2', {})
        fixture_config = v2_config.get('exponential_fixture', {})
        
        if not fixture_config.get('enabled', True):
            return 1.0
        
        difficulty_score = player_data.get('fixture_difficulty')
        if difficulty_score is None:
            return 1.0
        
        # Exponential fixture calculation
        base = fixture_config.get('exponential_base', 1.05)
        multiplier = base ** (-float(difficulty_score))
        
        # Apply position weights
        position = player_data.get('position', 'M')
        position_weights = fixture_config.get('position_weights', {
            'G': 1.10,
            'D': 1.20, 
            'M': 1.00,
            'F': 1.05
        })
        
        position_weight = position_weights.get(position, 1.0)
        final_multiplier = multiplier * position_weight
        
        # Apply bounds
        min_mult = fixture_config.get('min_multiplier', 0.5)
        max_mult = fixture_config.get('max_multiplier', 1.8)
        
        return max(min_mult, min(max_mult, final_multiplier))
    
    def _calculate_starter_multiplier_from_raw(self, player_data: Dict, parameters: Dict) -> float:
        """Calculate starter multiplier from raw prediction data"""
        
        v2_config = parameters.get('formula_optimization_v2', {})
        starter_config = v2_config.get('starter_prediction', {})
        
        if not starter_config.get('enabled', True):
            return 1.0
        
        is_starter = player_data.get('is_predicted_starter')
        rotation_risk = player_data.get('rotation_risk', '').lower()
        
        if is_starter is False or rotation_risk == 'benched':
            return starter_config.get('bench_penalty', 0.1)
        elif rotation_risk == 'high':
            return starter_config.get('high_rotation_penalty', 0.6) 
        elif rotation_risk == 'medium':
            return starter_config.get('medium_rotation_penalty', 0.8)
        else:
            return 1.0  # Starter or no data
    
    def _calculate_xgi_multiplier_from_raw(self, player_data: Dict, parameters: Dict) -> float:
        """Calculate normalized xGI multiplier using raw xG data"""
        
        v2_config = parameters.get('formula_optimization_v2', {})
        xgi_config = v2_config.get('normalized_xgi', {})
        
        if not xgi_config.get('enabled', True):
            return 1.0
        
        current_xgi = player_data.get('xgi90')
        baseline_xgi = player_data.get('baseline_xgi') or player_data.get('player_baseline_xgi')
        
        if not current_xgi or not baseline_xgi or baseline_xgi <= 0:
            return 1.0
        
        # Calculate ratio
        ratio = current_xgi / baseline_xgi
        
        # Apply position adjustments
        position = player_data.get('position', 'M')
        position_adjustments = xgi_config.get('position_adjustments', {
            'G': 0.5,
            'D': 0.8,
            'M': 1.0, 
            'F': 1.2
        })
        
        position_factor = position_adjustments.get(position, 1.0)
        final_multiplier = 1.0 + (ratio - 1.0) * position_factor
        
        # Apply bounds
        min_mult = xgi_config.get('min_multiplier', 0.5)
        max_mult = xgi_config.get('max_multiplier', 2.5)
        
        return max(min_mult, min(max_mult, final_multiplier))
    
    def _apply_multiplier_cap(self, multiplier: float, multiplier_type: str, caps_config: Dict) -> float:
        """Apply multiplier caps from parameters"""
        if multiplier_type in caps_config:
            cap = caps_config[multiplier_type]
            return min(multiplier, cap)
        return multiplier
    
    def _load_current_parameters(self) -> Dict:
        """Load current system parameters from config file"""
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_parameters.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading parameters: {e}")
            return self._get_default_parameters()
    
    def _get_default_parameters(self) -> Dict:
        """Return default V2.0 parameters if config unavailable"""
        return {
            'formula_optimization_v2': {
                'dynamic_blending': {
                    'baseline_switchover_gw': 10,
                    'current_weight_parameter': 7
                },
                'exponential_form': {
                    'enabled': True,
                    'lookback_games': 8,
                    'ewma_alpha': 0.87,
                    'min_multiplier': 0.5,
                    'max_multiplier': 2.0
                },
                'exponential_fixture': {
                    'enabled': True,
                    'exponential_base': 1.05,
                    'position_weights': {
                        'G': 1.10,
                        'D': 1.20,
                        'M': 1.00,
                        'F': 1.05
                    },
                    'min_multiplier': 0.5,
                    'max_multiplier': 1.8
                },
                'normalized_xgi': {
                    'enabled': True,
                    'position_adjustments': {
                        'G': 0.5,
                        'D': 0.8,
                        'M': 1.0,
                        'F': 1.2
                    },
                    'min_multiplier': 0.5,
                    'max_multiplier': 2.5
                },
                'multiplier_caps': {
                    'form': 2.0,
                    'fixture': 1.8,
                    'xgi': 2.5,
                    'global': 3.0
                }
            }
        }

# Convenience functions for API usage
def calculate_player_trends(db_config: Dict, 
                          player_id: str,
                          gameweek_start: int = 1,
                          gameweek_end: int = None,
                          parameters: Dict = None) -> List[Dict]:
    """Calculate trends for a specific player"""
    if gameweek_end is None:
        # Get current gameweek from database
        with psycopg2.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(gameweek) FROM raw_player_snapshots")
            result = cursor.fetchone()
            gameweek_end = result[0] if result and result[0] else 1
    
    engine = TrendAnalysisEngine(db_config)
    return engine.calculate_historical_trends(
        gameweek_start, gameweek_end, parameters, [player_id]
    )

def compare_parameters_for_player(db_config: Dict,
                                player_id: str,
                                parameter_sets: List[Dict],
                                gameweek_start: int = 1,
                                gameweek_end: int = None) -> Dict:
    """Compare different parameter sets for a specific player"""
    if gameweek_end is None:
        # Get current gameweek
        with psycopg2.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(gameweek) FROM raw_player_snapshots")
            result = cursor.fetchone()
            gameweek_end = result[0] if result and result[0] else 1
    
    engine = TrendAnalysisEngine(db_config)
    return engine.compare_parameter_sets(
        parameter_sets, gameweek_start, gameweek_end, [player_id]
    )