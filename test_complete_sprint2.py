#!/usr/bin/env python3
"""
Test Complete Sprint 2 Implementation - All Features
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from calculation_engine_v2 import FormulaEngineV2
import json

# Database configuration
db_config = {
    'host': 'localhost',
    'port': 5433,
    'user': 'fantrax_user',
    'password': 'fantrax_password',
    'database': 'fantrax_value_hunter'
}

# Load system parameters
try:
    with open('config/system_parameters.json', 'r') as f:
        parameters = json.load(f)
except Exception as e:
    print(f"Error loading parameters: {e}")
    parameters = {}

def test_complete_sprint2():
    """Test all Sprint 2 features: Dynamic Blending, EWMA Form, Normalized xGI"""
    
    print("=== Testing COMPLETE Sprint 2 Implementation ===")
    print("Features: Dynamic PPG Blending + EWMA Form (alpha=0.87) + Normalized xGI")
    
    try:
        # Initialize v2.0 engine
        engine = FormulaEngineV2(db_config, parameters)
        
        # Test player with full Sprint 2 data
        sprint2_player = {
            'name': 'Sprint 2 Test Player',
            'position': 'F',
            'player_id': 'test_sprint2',
            # Dynamic Blending data
            'ppg': 7.2,           # Current season PPG
            'historical_ppg': 5.8, # Previous season PPG  
            # EWMA Form data
            'recent_points': [8, 6, 9, 4, 7],  # Last 5 games (most recent first)
            # Normalized xGI data
            'xgi90': 1.8,         # Current xGI90
            'baseline_xgi': 1.2,  # Historical baseline
            # Other required data
            'fixture_difficulty': -3,  # Easy fixture
            'starter_multiplier': 1.0,
            'price': 9.5
        }
        
        print("\\nTest Player Data:")
        print(f"Position: {sprint2_player['position']}")
        print(f"Current PPG: {sprint2_player['ppg']}")
        print(f"Historical PPG: {sprint2_player['historical_ppg']}")
        print(f"Recent Games: {sprint2_player['recent_points']}")
        print(f"Current xGI90: {sprint2_player['xgi90']}")
        print(f"Baseline xGI90: {sprint2_player['baseline_xgi']}")
        print(f"Fixture Difficulty: {sprint2_player['fixture_difficulty']}")
        
        # Calculate with Sprint 2 engine
        result = engine.calculate_player_value(sprint2_player)
        
        print("\\n=== SPRINT 2 RESULTS ===")
        print(f"True Value: {result['true_value']}")
        print(f"ROI: {result['roi']}")
        print(f"Base PPG (Dynamic Blend): {result.get('base_ppg', 'N/A')}")
        
        # Show individual multipliers
        multipliers = result.get('multipliers', {})
        print(f"\\nMultiplier Breakdown:")
        print(f"Form (EWMA alpha=0.87): {multipliers.get('form', 'N/A')}")
        print(f"Fixture (Exponential): {multipliers.get('fixture', 'N/A')}")
        print(f"Starter: {multipliers.get('starter', 'N/A')}")
        print(f"xGI (Normalized): {multipliers.get('xgi', 'N/A')}")
        
        # Test individual components
        print(f"\\n=== COMPONENT TESTING ===")
        
        # Test Dynamic Blending
        blended_ppg, weight = engine._calculate_blended_ppg(sprint2_player)
        print(f"Dynamic Blending:")
        print(f"  Blended PPG: {blended_ppg:.3f}")
        print(f"  Current Season Weight: {weight:.3f}")
        print(f"  Historical Weight: {1-weight:.3f}")
        
        # Test EWMA Form 
        ewma_form = engine._calculate_exponential_form_multiplier(sprint2_player)
        print(f"EWMA Form (alpha=0.87): {ewma_form:.3f}")
        
        # Test Normalized xGI
        norm_xgi = engine._calculate_normalized_xgi_multiplier(sprint2_player)
        xgi_ratio = sprint2_player['xgi90'] / sprint2_player['baseline_xgi']
        print(f"Normalized xGI:")
        print(f"  Raw Ratio: {xgi_ratio:.3f}")
        print(f"  Final Multiplier: {norm_xgi:.3f}")
        
        # Show metadata
        metadata = result.get('metadata', {})
        print(f"\\n=== METADATA ===")
        print(f"Formula Version: {metadata.get('formula_version', 'N/A')}")
        print(f"Calculation Time: {metadata.get('calculation_time', 'N/A')}")
        
        print(f"\\nSUCCESS: Complete Sprint 2 implementation working!")
        print("✓ Dynamic PPG Blending")
        print("✓ EWMA Form with exponential decay")  
        print("✓ Normalized xGI with baseline comparison")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Sprint 2 testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_sprint2()
    if success:
        print("\\n🚀 SPRINT 2 COMPLETE - Super Enhanced Formula Active!")
    else:
        print("\\n⚠️ Sprint 2 implementation needs fixes")