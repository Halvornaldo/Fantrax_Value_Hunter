#!/usr/bin/env python3
"""
Formula Optimization v2.0 - Enhanced Calculation Engine
Fantasy Football Value Hunter

Implements research-based formula improvements:
1. Separate True Value from price (core fix)
2. Exponential fixture calculation 
3. Multiplier cap system
4. Foundation for Sprint 2 features

Author: Claude Code Assistant
Date: 2025-08-21
Version: 2.0
"""

import math
import json
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormulaEngineV2:
    """
    Enhanced calculation engine for Formula Optimization v2.0
    Implements research-based improvements while maintaining backward compatibility
    """
    
    def __init__(self, db_config: Dict[str, Any], parameters: Dict[str, Any]):
        """Initialize the v2.0 calculation engine"""
        self.db_config = db_config
        self.params = parameters
        self.v2_config = parameters.get('formula_optimization_v2', {})
        self.current_gameweek = self._get_current_gameweek()
        
        logger.info(f"FormulaEngineV2 initialized - GW{self.current_gameweek}")  
    def _get_primary_position(self, position: str) -> str:
        """
        Get primary position from multi-position string
        D,M -> D (defensive priority)
        M,F -> M (midfield priority)
        """
        if not position:
            return 'M'

        positions = [p.strip() for p in position.split(',')]

        # Priority order: G > D > M > F
        if 'G' in positions:
            return 'G'
        elif 'D' in positions:
            return 'D'
        elif 'M' in positions:
            return 'M'
        elif 'F' in positions or 'A' in positions:
            return 'F'

        return positions[0] if positions else 'M'

    def calculate_player_value(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main calculation function implementing v2.0 improvements
        
        Args:
            player_data: Dictionary containing player metrics and stats
            
        Returns:
            Dictionary with calculated values and metadata
        """
        player_id = player_data.get('player_id', 'unknown')
        
        try:
            # Step 1: SPRINT 2 - Calculate dynamically blended PPG
            base_ppg, current_weight = self._calculate_blended_ppg(player_data)
            
            # Step 2: Calculate all multipliers with v2.0 improvements
            # Apply formula toggles - if disabled, use 1.0x (no effect)
            formula_toggles = self.v2_config.get('formula_toggles', {})
            
            form_mult = self._calculate_form_multiplier(player_data) if formula_toggles.get('form_enabled', False) else 1.0
            fixture_mult = self._calculate_exponential_fixture_multiplier(player_data) if formula_toggles.get('fixture_enabled', True) else 1.0
            starter_mult = player_data.get('starter_multiplier', 1.0) if formula_toggles.get('starter_enabled', True) else 1.0
            xgi_mult = self._calculate_xgi_multiplier(player_data) if formula_toggles.get('xgi_enabled', True) else 1.0
            
            # Ensure all multipliers are floats and handle None
            if starter_mult is None:
                starter_mult = 1.0
            elif hasattr(starter_mult, 'quantize'):
                starter_mult = float(starter_mult)
            
            # Step 3: Apply multiplier caps (NEW v2.0 feature)
            form_mult = self._apply_multiplier_cap(form_mult, 'form')
            fixture_mult = self._apply_multiplier_cap(fixture_mult, 'fixture') 
            xgi_mult = self._apply_multiplier_cap(xgi_mult, 'xgi')
            
            # Step 4: Calculate True Value (CORE v2.0 FIX - separate from price)
            # Ensure all values are float for multiplication
            true_value = float(base_ppg) * float(form_mult) * float(fixture_mult) * float(starter_mult) * float(xgi_mult)
            
            # Step 5: Apply global multiplier cap
            global_cap = self.v2_config.get('multiplier_caps', {}).get('global', 3.0)
            max_allowed = float(base_ppg) * float(global_cap)
            true_value = min(true_value, max_allowed)
            
            # Step 6: Calculate ROI separately (CORE v2.0 FIX)
            price = player_data.get('price', 1.0)
            # Convert Decimal to float if needed and handle None
            if price is None:
                price = 1.0
            elif hasattr(price, 'quantize'):
                price = float(price)
            roi = true_value / float(price) if float(price) > 0 else 0
            
            # Step 7: Calculate legacy "value_score" for backward compatibility
            value_score = roi  # In v2.0, value_score becomes ROI
            
            # SPRINT 2: Enhanced result structure with blending information
            blended_ppg, current_weight = self._calculate_blended_ppg(player_data)
            
            result = {
                'player_id': player_id,
                'true_value': round(true_value, 2),
                'roi': round(roi, 3),
                'value_score': round(value_score, 3),  # For compatibility
                'base_ppg': round(base_ppg, 2),
                'blended_ppg': round(blended_ppg, 2),  # SPRINT 2: Dynamic blending
                'current_season_weight': round(current_weight, 3),  # SPRINT 2: Blending weight
                'multipliers': {
                    'form': round(form_mult, 3),
                    'fixture': round(fixture_mult, 3),
                    'starter': round(starter_mult, 3),
                    'xgi': round(xgi_mult, 3)
                },
                'metadata': {
                    'formula_version': '2.0',
                    'sprint_version': '2.0',  # SPRINT 2 features
                    'calculation_time': datetime.now().isoformat(),
                    'gameweek': self.current_gameweek,
                    'blending_info': {  # SPRINT 2: Blending metadata
                        'current_weight': round(current_weight, 3),
                        'historical_weight': round(1.0 - current_weight, 3),
                        'adaptation_gw': self.v2_config.get('dynamic_blending', {}).get('full_adaptation_gw', 12)
                    },
                    'caps_applied': {
                        'form': form_mult != self._calculate_form_multiplier(player_data) if formula_toggles.get('form_enabled', False) else False,
                        'fixture': fixture_mult != self._calculate_exponential_fixture_multiplier_raw(player_data) if formula_toggles.get('fixture_enabled', True) else False,
                        'xgi': xgi_mult != self._calculate_xgi_multiplier_raw(player_data) if formula_toggles.get('xgi_enabled', True) else False,
                        'global': true_value == max_allowed
                    },
                    'feature_flags': {  # SPRINT 2: Feature status
                        'exponential_form': self.v2_config.get('exponential_form', {}).get('enabled', True),
                        'dynamic_blending': self.v2_config.get('dynamic_blending', {}).get('enabled', True),
                        'normalized_xgi': self.v2_config.get('normalized_xgi', {}).get('enabled', True)
                    }
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating value for player {player_id}: {e}")
            return self._get_error_result(player_id, str(e))
    
    def _calculate_base_ppg(self, player_data: Dict[str, Any]) -> float:
        """
        Calculate base PPG for the player
        In Sprint 1: Uses existing PPG
        In Sprint 2: Will implement dynamic blending
        """
        ppg = player_data.get('ppg', 0.0)
        # Handle None and convert Decimal to float if needed
        if ppg is None:
            ppg = 0.0
        elif hasattr(ppg, 'quantize'):  # Check if it's a Decimal
            ppg = float(ppg)
        return max(0.1, ppg)  # Ensure minimum positive value
    
    def _calculate_form_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        SPRINT 2: Calculate form multiplier using EWMA with α=0.87
        """
        return self._calculate_exponential_form_multiplier(player_data)
    
    def _calculate_exponential_form_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        SPRINT 2: Calculate form using Exponential Weighted Moving Average (EWMA)
        Algorithm: More recent games have exponentially higher weights (α=0.87)
        """
        try:
            alpha = self.v2_config.get('exponential_form', {}).get('alpha', 0.87)
            
            # Get recent points from database if not provided
            recent_games = player_data.get('recent_points', [])
            if not recent_games:
                recent_games = self._get_recent_points_from_db(player_data.get('player_id'))
            
            if not recent_games or len(recent_games) == 0:
                return 1.0  # No recent data
            
            # Ensure we have numeric data
            numeric_games = []
            for game in recent_games:
                try:
                    numeric_games.append(float(game))
                except (ValueError, TypeError):
                    continue
                    
            if not numeric_games:
                return 1.0  # No valid numeric data
                
            # Generate exponential decay weights (most recent = highest weight)
            weights = []
            for i in range(len(numeric_games)):
                weight = alpha ** i  # Exponential decay: α^0, α^1, α^2, ...
                weights.append(weight)
            
            # Normalize weights to sum to 1
            total_weight = sum(weights)
            if total_weight == 0:
                return 1.0
                
            normalized_weights = [w / total_weight for w in weights]
            
            # Calculate weighted average form score
            form_score = sum(points * weight for points, weight in zip(numeric_games, normalized_weights))
            
            # Get dynamic baseline using blended PPG for normalization
            blended_baseline, _ = self._calculate_blended_ppg(player_data)
            
            if blended_baseline > 0:
                form_multiplier = form_score / blended_baseline
            else:
                form_multiplier = 1.0
                
            # Apply progressive range based on games played
            games_played = len(numeric_games)
            progressive_config = self.v2_config.get('progressive_form_ranges', {})
            
            if progressive_config.get('enabled', True):
                # Find appropriate range based on games played
                ranges = progressive_config.get('ranges_by_games', [])
                form_min, form_max = 0.9, 1.1  # Default tight range for safety
                
                for range_config in ranges:
                    if games_played <= range_config['games']:
                        form_min = range_config['min']
                        form_max = range_config['max']
                        break
                else:
                    # If more games than any defined range, use the last (most permissive) range
                    if ranges:
                        last_range = ranges[-1]
                        form_min = last_range['min']
                        form_max = last_range['max']
                
                # Apply the progressive bounds
                form_multiplier = max(form_min, min(form_max, form_multiplier))
                
                logger.debug(f"Player form: {games_played} games played, range [{form_min}, {form_max}], multiplier: {form_multiplier:.3f}")
            else:
                # Fallback to early season bounds if progressive ranges disabled
                form_multiplier = max(0.9, min(1.1, form_multiplier))
                
            return form_multiplier
            
        except Exception as e:
            logger.warning(f"Error calculating exponential form multiplier: {e}")
            return 1.0
    
    def _get_recent_points_from_db(self, player_id: str, limit: int = 5) -> List[float]:
        """
        Fetch recent points from player_game_scores table for EWMA calculation
        Only includes games where player actually played (did_play = true)
        Returns points in chronological order (most recent first)
        """
        if not player_id:
            return []

        try:
            import psycopg2
            import psycopg2.extras

            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Get last N games where player actually played, ordered by game_number DESC (most recent first)
            cursor.execute("""
                SELECT points_scored
                FROM player_game_scores
                WHERE player_id = %s AND did_play = true
                ORDER BY game_number DESC
                LIMIT %s
            """, [player_id, limit])

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # Convert to list of floats
            recent_points = []
            for row in results:
                try:
                    points = float(row['points_scored'] or 0.0)
                    recent_points.append(points)
                except (ValueError, TypeError):
                    continue

            logger.debug(f"Found {len(recent_points)} recent games for player {player_id}: {recent_points}")
            return recent_points

        except Exception as e:
            logger.warning(f"Error fetching recent points for player {player_id}: {e}")
            return []
    
    def _calculate_exponential_fixture_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        NEW v2.0: Calculate fixture multiplier using exponential transformation
        Research formula: multiplier = base^(-difficulty_score)
        """
        try:
            difficulty_score = player_data.get('fixture_difficulty', 0)
            position = self._get_primary_position(player_data.get('position', 'M'))
            
            # Handle None values
            if difficulty_score is None:
                difficulty_score = 0
            elif hasattr(difficulty_score, 'quantize'):
                difficulty_score = float(difficulty_score)
            
            # Get exponential base from v2.0 config
            base = self.v2_config.get('exponential_fixture', {}).get('base', 1.05)
            
            # Position-specific adjustments
            position_weights = self.v2_config.get('exponential_fixture', {}).get('position_weights', {
                'G': 1.1, 'D': 1.2, 'M': 1.0, 'F': 1.05
            })
            pos_weight = position_weights.get(position, 1.0)
            
            # Exponential transformation
            # Note: negative difficulty = easier fixture = higher multiplier
            adjusted_score = (float(-difficulty_score) * float(pos_weight)) / 10.0
            fixture_multiplier = base ** adjusted_score
            
            # Ensure reasonable bounds
            return max(0.5, min(2.0, fixture_multiplier))
            
        except Exception as e:
            logger.warning(f"Error calculating exponential fixture multiplier: {e}")
            return 1.0
    
    def _calculate_exponential_fixture_multiplier_raw(self, player_data: Dict[str, Any]) -> float:
        """Raw calculation without caps for metadata tracking"""
        try:
            difficulty_score = player_data.get('fixture_difficulty', 0)
            position = self._get_primary_position(player_data.get('position', 'M'))
            base = self.v2_config.get('exponential_fixture', {}).get('base', 1.05)
            position_weights = self.v2_config.get('exponential_fixture', {}).get('position_weights', {
                'G': 1.1, 'D': 1.2, 'M': 1.0, 'F': 1.05
            })
            pos_weight = position_weights.get(position, 1.0)
            adjusted_score = (-difficulty_score * pos_weight) / 10.0
            return base ** adjusted_score
        except:
            return 1.0
    
    def _calculate_xgi_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        Calculate xGI multiplier using Sprint 2 normalized ratio calculation
        """
        # Check if xGI integration is enabled (use main xgi_integration config)
        xgi_config = self.params.get('xgi_integration', {})
        if not xgi_config.get('enabled', False):
            return 1.0
            
        return self._calculate_normalized_xgi_multiplier(player_data)
    
    def _calculate_normalized_xgi_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        SPRINT 2: Calculate normalized xGI as ratio to historical baseline
        Formula: Current_xGI90 / Historical_Baseline_xGI90
        """
        try:
            # Get current and baseline xGI values
            current_xgi = float(player_data.get('xgi90', 0.0) or 0.0)
            baseline_xgi = float(player_data.get('baseline_xgi', 0.0) or 0.0)
            position = self._get_primary_position(player_data.get('position', 'M'))
            
            # Position-specific logic for xGI relevance
            if position == 'G':
                # Goalkeepers - xGI not relevant
                return 1.0
            
            # Calculate ratio if baseline exists and is meaningful
            if baseline_xgi > 0.1:  # Avoid division by very small numbers
                xgi_ratio = current_xgi / baseline_xgi
                
                # Position-specific scaling
                if position == 'D' and baseline_xgi < 0.2:
                    # Defensive players with low baseline xGI - reduce impact
                    impact_factor = 0.3  # 30% impact for defenders
                    xgi_multiplier = 1.0 + (xgi_ratio - 1.0) * impact_factor
                else:
                    # Full impact for midfielders and forwards
                    xgi_multiplier = xgi_ratio
                
                # Apply reasonable bounds to prevent extreme outliers
                return max(0.5, min(2.5, xgi_multiplier))
            
            else:
                # No meaningful baseline - use neutral multiplier
                return 1.0
                
        except Exception as e:
            logger.warning(f"Error calculating normalized xGI multiplier: {e}")
            return 1.0
    
    def _calculate_xgi_multiplier_raw(self, player_data: Dict[str, Any]) -> float:
        """Raw calculation without caps for metadata tracking"""
        try:
            current_xgi = float(player_data.get('xgi90', 0.0) or 0.0)
            baseline_xgi = float(player_data.get('baseline_xgi', 0.0) or 0.0)
            position = self._get_primary_position(player_data.get('position', 'M'))
            
            if position == 'G' or baseline_xgi <= 0.1:
                return 1.0
                
            return current_xgi / baseline_xgi
        except:
            return 1.0
    
    def _apply_multiplier_cap(self, value: float, multiplier_type: str) -> float:
        """
        NEW v2.0: Apply multiplier caps to prevent extreme outliers
        Note: Form bounds are now handled by progressive ranges in _calculate_exponential_form_multiplier
        """
        if not self.v2_config.get('multiplier_caps', {}).get('enabled', True):
            return value
        
        caps = self.v2_config.get('multiplier_caps', {})
        cap = caps.get(multiplier_type, 2.0)
        
        # Apply consistent bounds for all multipliers
        # Form bounds are handled separately by progressive ranges
        return max(0.5, min(cap, value))
    
    def _calculate_blended_ppg(self, player_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Enhanced blending using games-based weighting with MAX formula
        Formula: MAX(games_ratio, transition_ratio) for fair weighting
        Returns (blended_ppg, current_weight)
        """
        current_ppg = player_data.get('ppg', 0.0)
        historical_ppg = player_data.get('historical_ppg', None)
        games_current = player_data.get('games_current', 0)
        games_historical = player_data.get('games_historical', 0)

        # Handle Decimal conversion
        if hasattr(current_ppg, 'quantize'):
            current_ppg = float(current_ppg)
        if historical_ppg is not None and hasattr(historical_ppg, 'quantize'):
            historical_ppg = float(historical_ppg)

        # Handle no historical data (new players or no 2024-25 data)
        if historical_ppg is None or historical_ppg == 0.0 or games_historical == 0:
            # Use current PPG only for players without historical data
            blended_ppg = current_ppg
            w_current = 1.0
            logger.debug(f"Player without historical data - using 100% current PPG: {current_ppg:.2f}")
        else:
            # Get transition period from config (default 12 games)
            transition_period = self.v2_config.get('dynamic_blending', {}).get('transition_period', 12)

            # Step 1: Calculate Weight_A (games-based ratio)
            total_games = games_current + games_historical
            if total_games > 0:
                weight_A = games_current / total_games
            else:
                weight_A = 0.0

            # Step 2: Calculate Weight_B (transition-based)
            weight_B = min(1.0, games_current / transition_period)

            # Step 3: Take maximum of both weights (ensures fair weighting)
            w_current = max(weight_A, weight_B)
            w_historical = 1.0 - w_current

            # Step 4: Blend the PPG values
            blended_ppg = (w_current * current_ppg) + (w_historical * historical_ppg)

            logger.debug(f"Blending: {games_current}c + {games_historical}h games, "
                        f"Weight_A={weight_A:.3f}, Weight_B={weight_B:.3f}, "
                        f"Final={w_current:.3f} current, {w_historical:.3f} historical")

        return max(0.1, blended_ppg), w_current
    
    def _get_current_gameweek(self) -> int:
        """Get current gameweek from database"""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(gameweek) FROM player_metrics WHERE gameweek IS NOT NULL')
            current_gameweek = cursor.fetchone()[0] or 1
            cursor.close()
            conn.close()
            return current_gameweek
        except Exception as e:
            logger.warning(f"Failed to get current gameweek from database: {e}")
            return 1  # Fallback to GW1
    
    def _get_error_result(self, player_id: str, error_msg: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            'player_id': player_id,
            'true_value': 0.0,
            'roi': 0.0,
            'value_score': 0.0,
            'base_ppg': 0.0,
            'multipliers': {'form': 1.0, 'fixture': 1.0, 'starter': 1.0, 'xgi': 1.0},
            'metadata': {
                'formula_version': '2.0',
                'error': error_msg,
                'calculation_time': datetime.now().isoformat()
            }
        }




def load_system_parameters(config_path: str = 'config/system_parameters.json') -> Dict[str, Any]:
    """Load system parameters from JSON file with validation and fallback handling"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            params = json.load(f)
            
        # Validate critical parameters
        v2_config = params.get('formula_optimization_v2', {})
        
        # Log warnings if configuration is falling back to defaults
        if not v2_config.get('formula_toggles', {}).get('form_enabled', True):
            logger.info("Form calculation is disabled in configuration")
        
        adaptation_gw = v2_config.get('dynamic_blending', {}).get('full_adaptation_gw')
        if adaptation_gw != 12:
            logger.warning(f"Configuration full_adaptation_gw is {adaptation_gw}, expected 12")
            
        form_cap = v2_config.get('multiplier_caps', {}).get('form')
        if form_cap != 1.1:
            logger.warning(f"Configuration form cap is {form_cap}, expected 1.1 for early season")
            
        logger.info("System parameters loaded successfully with validation")
        return params
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading system parameters: {e}")
        return {}


def get_db_connection(db_config: Dict[str, Any]) -> psycopg2.extensions.connection:
    """Create database connection"""
    return psycopg2.connect(**db_config)


# Example usage and testing
if __name__ == "__main__":
    # Test configuration
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }
    
    # Load parameters
    parameters = load_system_parameters()
    
    # Create V2.0 engine
    v2_engine = FormulaEngineV2(db_config, parameters)
    
    # Test data
    test_player = {
        'player_id': 'test_001',
        'name': 'Test Player',
        'position': 'M',
        'price': 8.5,
        'ppg': 6.2,
        'historical_ppg': 5.8,
        'baseline_xgi': 0.4,
        'xgi90': 0.6,
        'fixture_difficulty': -3,  # Easy fixture
        'starter_multiplier': 1.0
    }
    
    # Calculate with V2.0 engine
    v2_result = v2_engine.calculate_player_value(test_player)
    
    # Display results
    print("=== V2.0 ENHANCED FORMULA TEST ===")
    print(f"True Value:    {v2_result['true_value']:.2f}")
    print(f"ROI:           {v2_result['roi']:.3f}")
    print(f"Base PPG:      {v2_result['base_ppg']:.2f}")
    print(f"Blended PPG:   {v2_result['blended_ppg']:.2f}")
    print(f"Form Mult:     {v2_result['multipliers']['form']:.3f}")
    print(f"Fixture Mult:  {v2_result['multipliers']['fixture']:.3f} (exponential)")
    print(f"Starter Mult:  {v2_result['multipliers']['starter']:.3f}")
    print(f"xGI Mult:      {v2_result['multipliers']['xgi']:.3f} (normalized)")
    print(f"Current Weight: {v2_result['current_season_weight']:.3f}")
    
    logger.info("V2.0 Enhanced Formula test completed")