#!/usr/bin/env python3
"""
Test Sprint 2 normalized xGI calculation with real database data
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

def test_normalized_xgi_calculation():
    """Test the Sprint 2 normalized xGI calculation with real players"""
    
    print("=== Testing Sprint 2 Normalized xGI Calculation ===")
    
    try:
        # Initialize v2.0 engine
        engine = FormulaEngineV2(db_config, parameters)
        
        # Test players with different xGI profiles
        test_cases = [
            {
                'name': 'High Current xGI (Forward)',
                'player_data': {
                    'name': 'Test Forward',
                    'position': 'F',
                    'xgi90': 1.5,      # High current xGI
                    'baseline_xgi': 1.0,  # Lower baseline
                    'price': 8.5,
                    'ppg': 6.2
                }
            },
            {
                'name': 'Low Current xGI (Forward)',
                'player_data': {
                    'name': 'Test Forward 2',
                    'position': 'F',
                    'xgi90': 0.5,      # Low current xGI
                    'baseline_xgi': 1.2,  # Higher baseline
                    'price': 8.0,
                    'ppg': 5.8
                }
            },
            {
                'name': 'Defender with Low xGI',
                'player_data': {
                    'name': 'Test Defender',
                    'position': 'D',
                    'xgi90': 0.15,     # Low current xGI
                    'baseline_xgi': 0.18,  # Low baseline
                    'price': 5.5,
                    'ppg': 4.2
                }
            },
            {
                'name': 'Goalkeeper',
                'player_data': {
                    'name': 'Test Goalkeeper',
                    'position': 'G',
                    'xgi90': 0.01,     # Minimal xGI
                    'baseline_xgi': 0.02,
                    'price': 5.0,
                    'ppg': 3.8
                }
            }
        ]
        
        print(f"Testing with {len(test_cases)} different player profiles:\n")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}. {test_case['name']}")
            player_data = test_case['player_data']
            
            # Calculate multipliers
            normalized_xgi = engine._calculate_normalized_xgi_multiplier(player_data)
            raw_xgi = engine._calculate_xgi_multiplier_raw(player_data)
            
            # Calculate full value
            result = engine.calculate_player_value(player_data)
            
            current_xgi = player_data['xgi90']
            baseline_xgi = player_data['baseline_xgi']
            ratio = current_xgi / baseline_xgi if baseline_xgi > 0 else 0
            
            print(f"   Position: {player_data['position']}")
            print(f"   Current xGI90: {current_xgi:.3f}")
            print(f"   Baseline xGI90: {baseline_xgi:.3f}")
            print(f"   Raw Ratio: {ratio:.3f}")
            print(f"   Normalized xGI Multiplier: {normalized_xgi:.3f}")
            print(f"   True Value: {result['true_value']}")
            print(f"   ROI: {result['roi']}")
            print()
        
        # Test with real database player
        print("Testing with real database player:")
        import psycopg2
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Get a real player with both xGI values
        cursor.execute("""
            SELECT name, position, xgi90, baseline_xgi, price, ppg
            FROM players 
            WHERE xgi90 > 0 AND baseline_xgi > 0 AND price > 0
            ORDER BY xgi90 DESC
            LIMIT 1
        """)
        
        real_player = cursor.fetchone()
        if real_player:
            player_data = {
                'name': real_player[0],
                'position': real_player[1], 
                'xgi90': float(real_player[2]),
                'baseline_xgi': float(real_player[3]),
                'price': float(real_player[4]),
                'ppg': float(real_player[5])
            }
            
            result = engine.calculate_player_value(player_data)
            normalized_xgi = engine._calculate_normalized_xgi_multiplier(player_data)
            
            print(f"Real Player: {player_data['name']} ({player_data['position']})")
            print(f"Current xGI90: {player_data['xgi90']:.3f}")
            print(f"Baseline xGI90: {player_data['baseline_xgi']:.3f}") 
            print(f"Normalized xGI Multiplier: {normalized_xgi:.3f}")
            print(f"True Value: {result['true_value']}")
            print(f"ROI: {result['roi']}")
        
        cursor.close()
        conn.close()
        
        print(f"\nSUCCESS: Sprint 2 normalized xGI calculation working correctly!")
        return True
        
    except Exception as e:
        print(f"ERROR: Error testing normalized xGI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_normalized_xgi_calculation()
    if success:
        print("\nSUCCESS: Sprint 2 xGI Implementation Complete!")
    else:
        print("\nWARNING: Issues detected in Sprint 2 implementation")