#!/usr/bin/env python3
"""
Simplified Trend Analysis Engine - Current Season Only
Fantasy Football Value Hunter

Purpose: Apply V2.0 Enhanced Formula to raw historical data using ONLY current season baselines
This version removes all historical baseline dependencies for immediate Week 1 data capture

Author: Claude Code Assistant  
Date: 2025-08-23
Version: 1.1 (Simplified)
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

class SimpleTrendAnalysisEngine:
    """
    Simplified engine for current-season-only trend analysis
    Uses running averages and weekly increments instead of historical baselines
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize the simplified trend analysis engine"""
        self.db_config = db_config
        logger.info("SimpleTrendAnalysisEngine initialized - current season only")
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def calculate_historical_trends(self, 
                                   gameweek_start: int,
                                   gameweek_end: int,
                                   parameters: Optional[Dict] = None,
                                   player_ids: Optional[List[str]] = None) -> List[Dict]:
        """Apply V2.0 formula to raw data using current-season baselines only"""
        
        logger.info(f"Calculating current-season trends for GW{gameweek_start}-{gameweek_end}")
        
        if parameters is None:
            parameters = self._get_default_parameters()
        
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
                            'parameters_used': 'current_season_only'
                        })
                        
                        results.append(calculated_values)
                        
                    except Exception as e:
                        logger.error(f"Error calculating for {player_data.get('player_id', 'unknown')} GW{gw}: {e}")
                        continue
        
        logger.info(f"Generated {len(results)} trend data points")
        return results
    
    def _fetch_raw_data(self, cursor, gameweek: int, player_ids: Optional[List[str]] = None) -> List[Dict]:
        """Fetch raw data for a specific gameweek"""
        
        # Build query with optional player filtering
        where_clause = "WHERE r.gameweek = %s"
        params = [gameweek]
        
        if player_ids:
            placeholders = ','.join(['%s'] * len(player_ids))
            where_clause += f" AND r.player_id IN ({placeholders})"
            params.extend(player_ids)
        
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
                r.opponent,
                r.is_home,
                r.fixture_difficulty,
                r.is_predicted_starter,
                r.rotation_risk
                
            FROM raw_data_complete r
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
        """Calculate V2.0 Enhanced values using current-season baselines only"""
        
        player_id = player_data['player_id']
        
        # Step 1: Calculate current season PPG (no historical blending)
        season_ppg = self._calculate_season_ppg(cursor, player_id, current_gw)
        
        # Step 2: Calculate form multiplier using raw points history
        form_mult = self._calculate_form_multiplier_from_raw(
            cursor, player_id, current_gw, parameters
        )
        
        # Step 3: Calculate fixture multiplier using raw odds data
        fixture_mult = self._calculate_fixture_multiplier_from_raw(
            player_data, parameters
        )
        
        # Step 4: Calculate starter multiplier 
        starter_mult = self._calculate_starter_multiplier_from_raw(
            player_data, parameters
        )
        
        # Step 5: Calculate xGI multiplier using current season average as baseline
        xgi_mult = self._calculate_xgi_multiplier_current_season(
            cursor, player_data, current_gw, parameters
        )
        
        # Step 6: Apply multiplier caps
        v2_config = parameters.get('formula_optimization_v2', {})
        multiplier_caps = v2_config.get('multiplier_caps', {})
        
        form_mult = self._apply_multiplier_cap(form_mult, 'form', multiplier_caps)
        fixture_mult = self._apply_multiplier_cap(fixture_mult, 'fixture', multiplier_caps)
        xgi_mult = self._apply_multiplier_cap(xgi_mult, 'xgi', multiplier_caps)
        
        # Step 7: Calculate True Value
        true_value = season_ppg * form_mult * fixture_mult * starter_mult * xgi_mult
        
        # Apply global cap
        global_cap = multiplier_caps.get('global', 3.0)
        max_allowed = season_ppg * global_cap
        true_value = min(true_value, max_allowed)
        
        # Step 8: Calculate ROI
        price = float(player_data.get('price', 1.0) or 1.0)
        roi = true_value / price if price > 0 else 0
        
        return {
            'player_id': player_id,
            'name': player_data.get('name'),
            'team': player_data.get('team'), 
            'position': player_data.get('position'),
            'price': price,
            'fpts': player_data.get('fpts'),
            'season_ppg': season_ppg,
            'current_season_weight': 1.0,  # Always 100% current season
            'form_multiplier': form_mult,
            'fixture_multiplier': fixture_mult, 
            'starter_multiplier': starter_mult,
            'xgi_multiplier': xgi_mult,
            'true_value': true_value,
            'roi': roi,
            'value_score': roi
        }
    
    def _calculate_season_ppg(self, cursor, player_id: str, current_gw: int) -> float:
        """Calculate current season PPG from raw form data"""
        
        cursor.execute("""
            SELECT 
                SUM(points_scored) as total_points,
                SUM(games_played) as total_games
            FROM raw_form_snapshots 
            WHERE player_id = %s AND gameweek <= %s
        """, [player_id, current_gw])
        
        result = cursor.fetchone()
        
        if result and result['total_games'] and result['total_games'] > 0:
            return float(result['total_points']) / float(result['total_games'])
        else:
            return 6.0  # Default for players with no data yet
    
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
        points = [float(row['points_scored']) for row in form_data]
        
        ewma_score = points[0]  # Most recent game
        for i in range(1, len(points)):
            ewma_score = alpha * ewma_score + (1 - alpha) * points[i]
        
        # Get player's season average for baseline
        season_avg = self._calculate_season_ppg(cursor, player_id, current_gw)
        
        # Convert to multiplier
        if season_avg > 0:
            multiplier = ewma_score / season_avg
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
        rotation_risk = (player_data.get('rotation_risk') or '').lower()
        
        if is_starter is False or rotation_risk == 'benched':
            return starter_config.get('bench_penalty', 0.1)
        elif rotation_risk == 'high':
            return starter_config.get('high_rotation_penalty', 0.6) 
        elif rotation_risk == 'medium':
            return starter_config.get('medium_rotation_penalty', 0.8)
        else:
            return 1.0  # Starter or no data
    
    def _calculate_xgi_multiplier_current_season(self, cursor, player_data: Dict, current_gw: int, parameters: Dict) -> float:
        """Calculate xGI multiplier using current season average as baseline"""
        
        v2_config = parameters.get('formula_optimization_v2', {})
        xgi_config = v2_config.get('normalized_xgi', {})
        
        if not xgi_config.get('enabled', True):
            return 1.0
        
        player_id = player_data.get('player_id')
        current_xgi = player_data.get('xgi90')
        
        if not current_xgi or not player_id:
            return 1.0
        
        # Calculate player's season average xGI as baseline
        cursor.execute("""
            SELECT AVG(xgi90) as season_avg_xgi
            FROM raw_player_snapshots 
            WHERE player_id = %s AND gameweek <= %s AND xgi90 > 0
        """, [player_id, current_gw])
        
        result = cursor.fetchone()
        season_avg_xgi = result['season_avg_xgi'] if result and result['season_avg_xgi'] else None
        
        if not season_avg_xgi or season_avg_xgi <= 0:
            return 1.0
        
        # Calculate ratio using season average as baseline
        ratio = float(current_xgi) / float(season_avg_xgi)
        
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
    
    def _get_default_parameters(self) -> Dict:
        """Return default V2.0 parameters"""
        return {
            'formula_optimization_v2': {
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