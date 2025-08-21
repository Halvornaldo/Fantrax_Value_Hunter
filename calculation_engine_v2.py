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
            # Step 1: Calculate base PPG (will be enhanced in Sprint 2 with dynamic blending)
            base_ppg = self._calculate_base_ppg(player_data)
            
            # Step 2: Calculate all multipliers with v2.0 improvements
            form_mult = self._calculate_form_multiplier(player_data)
            fixture_mult = self._calculate_exponential_fixture_multiplier(player_data)
            starter_mult = player_data.get('starter_multiplier', 1.0)
            xgi_mult = self._calculate_xgi_multiplier(player_data)
            
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
            
            result = {
                'player_id': player_id,
                'true_value': round(true_value, 2),
                'roi': round(roi, 3),
                'value_score': round(value_score, 3),  # For compatibility
                'base_ppg': round(base_ppg, 2),
                'multipliers': {
                    'form': round(form_mult, 3),
                    'fixture': round(fixture_mult, 3),
                    'starter': round(starter_mult, 3),
                    'xgi': round(xgi_mult, 3)
                },
                'metadata': {
                    'formula_version': '2.0',
                    'calculation_time': datetime.now().isoformat(),
                    'gameweek': self.current_gameweek,
                    'caps_applied': {
                        'form': form_mult != self._calculate_form_multiplier(player_data),
                        'fixture': fixture_mult != self._calculate_exponential_fixture_multiplier_raw(player_data),
                        'xgi': xgi_mult != self._calculate_xgi_multiplier_raw(player_data),
                        'global': true_value == max_allowed
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
        Calculate form multiplier
        Sprint 1: Uses existing form logic
        Sprint 2: Will implement exponential decay (EWMA)
        """
        # For Sprint 1, use existing form multiplier or default
        existing_form = player_data.get('form_multiplier', 1.0)
        # Handle None and convert Decimal to float if needed
        if existing_form is None:
            existing_form = 1.0
        elif hasattr(existing_form, 'quantize'):
            existing_form = float(existing_form)
        return max(0.5, existing_form)  # Apply minimum floor
    
    def _calculate_exponential_fixture_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        NEW v2.0: Calculate fixture multiplier using exponential transformation
        Research formula: multiplier = base^(-difficulty_score)
        """
        try:
            difficulty_score = player_data.get('fixture_difficulty', 0)
            position = player_data.get('position', 'M')
            
            # Convert Decimal to float if needed
            if hasattr(difficulty_score, 'quantize'):
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
            position = player_data.get('position', 'M')
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
        Calculate xGI multiplier
        Sprint 1: Uses existing xGI logic  
        Sprint 2: Will implement normalized ratio-based calculation
        """
        # For Sprint 1, use existing xGI multiplier or default
        existing_xgi = player_data.get('xgi_multiplier', 1.0)
        # Handle None and convert Decimal to float if needed
        if existing_xgi is None:
            existing_xgi = 1.0
        elif hasattr(existing_xgi, 'quantize'):
            existing_xgi = float(existing_xgi)
        return max(0.5, existing_xgi)  # Apply minimum floor
    
    def _calculate_xgi_multiplier_raw(self, player_data: Dict[str, Any]) -> float:
        """Raw calculation without caps for metadata tracking"""
        return player_data.get('xgi_multiplier', 1.0)
    
    def _apply_multiplier_cap(self, value: float, multiplier_type: str) -> float:
        """
        NEW v2.0: Apply multiplier caps to prevent extreme outliers
        """
        if not self.v2_config.get('multiplier_caps', {}).get('enabled', True):
            return value
        
        caps = self.v2_config.get('multiplier_caps', {})
        cap = caps.get(multiplier_type, 2.0)
        
        return max(0.5, min(cap, value))
    
    def _get_current_gameweek(self) -> int:
        """Get current gameweek from database or parameters"""
        # This would be implemented based on your current gameweek logic
        return 1  # Placeholder for Sprint 1
    
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


class LegacyFormulaEngine:
    """
    Wrapper for v1.0 formula - maintains backward compatibility
    Used for A/B testing and gradual migration
    """
    
    def __init__(self, db_config: Dict[str, Any], parameters: Dict[str, Any]):
        self.db_config = db_config
        self.params = parameters
        
    def calculate_player_value(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate using v1.0 formula for comparison"""
        try:
            player_id = player_data.get('player_id', 'unknown')
            ppg = player_data.get('ppg', 0.0)
            price = player_data.get('price', 1.0)
            
            # Original v1.0 calculation (price mixed with prediction)
            base_value = ppg / price if price > 0 else 0
            
            # Apply existing multipliers
            form_mult = player_data.get('form_multiplier', 1.0)
            fixture_mult = player_data.get('fixture_multiplier', 1.0)
            starter_mult = player_data.get('starter_multiplier', 1.0)
            xgi_mult = player_data.get('xgi_multiplier', 1.0)
            
            # v1.0 final calculation
            value_score = base_value * form_mult * fixture_mult * starter_mult * xgi_mult
            
            return {
                'player_id': player_id,
                'true_value': round(value_score, 2),  # In v1.0, true_value = value_score
                'roi': round(value_score, 3),  # In v1.0, ROI = value_score
                'value_score': round(value_score, 3),
                'base_ppg': round(ppg, 2),
                'multipliers': {
                    'form': round(form_mult, 3),
                    'fixture': round(fixture_mult, 3),
                    'starter': round(starter_mult, 3),
                    'xgi': round(xgi_mult, 3)
                },
                'metadata': {
                    'formula_version': '1.0',
                    'calculation_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in legacy calculation: {e}")
            return {
                'player_id': player_data.get('player_id', 'unknown'),
                'true_value': 0.0,
                'roi': 0.0,
                'value_score': 0.0,
                'base_ppg': 0.0,
                'multipliers': {'form': 1.0, 'fixture': 1.0, 'starter': 1.0, 'xgi': 1.0},
                'metadata': {'formula_version': '1.0', 'error': str(e)}
            }


def load_system_parameters(config_path: str = 'config/system_parameters.json') -> Dict[str, Any]:
    """Load system parameters from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
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
    
    # Create engines
    v2_engine = FormulaEngineV2(db_config, parameters)
    v1_engine = LegacyFormulaEngine(db_config, parameters)
    
    # Test data
    test_player = {
        'player_id': 'test_001',
        'name': 'Test Player',
        'position': 'M',
        'price': 8.5,
        'ppg': 6.2,
        'form_multiplier': 1.15,
        'fixture_multiplier': 1.1,
        'starter_multiplier': 1.0,
        'xgi_multiplier': 1.2,
        'fixture_difficulty': -3  # Easy fixture
    }
    
    # Calculate with both engines
    v2_result = v2_engine.calculate_player_value(test_player)
    v1_result = v1_engine.calculate_player_value(test_player)
    
    # Compare results
    print("=== FORMULA OPTIMIZATION v2.0 TEST ===")
    print(f"v1.0 Value Score: {v1_result['value_score']:.3f}")
    print(f"v2.0 True Value:  {v2_result['true_value']:.2f}")
    print(f"v2.0 ROI:         {v2_result['roi']:.3f}")
    print(f"v2.0 Fixture Mult: {v2_result['multipliers']['fixture']:.3f} (exponential)")
    print(f"v1.0 Fixture Mult: {v1_result['multipliers']['fixture']:.3f} (linear)")
    
    logger.info("v2.0 calculation engine test completed")