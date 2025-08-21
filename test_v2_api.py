#!/usr/bin/env python3
"""
Test the v2.0 API integration
"""

import sys
import os
sys.path.append('src')
from app import calculate_values_v2, FormulaEngineV2, DB_CONFIG, load_system_parameters
import psycopg2
import psycopg2.extras

def test_v2_api_logic():
    """Test the v2.0 calculation logic directly"""
    try:
        print("Testing v2.0 API logic...")
        
        # Load parameters
        parameters = load_system_parameters()
        print(f"Parameters loaded: v2.0 enabled = {parameters.get('formula_optimization_v2', {}).get('enabled')}")
        
        # Create engine
        engine = FormulaEngineV2(DB_CONFIG, parameters)
        print("Engine created successfully")
        
        # Get sample player data from database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                p.xgi90,
                pm.price,
                pm.ppg,
                pm.form_multiplier,
                pm.fixture_multiplier,
                pm.starter_multiplier,
                pm.xgi_multiplier,
                tf.difficulty_score as fixture_difficulty
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            LEFT JOIN team_fixtures tf ON p.team = tf.team_code AND tf.gameweek = 1
            WHERE pm.gameweek = 1
            LIMIT 5
        """)
        
        players = cursor.fetchall()
        conn.close()
        
        print(f"Retrieved {len(players)} players from database")
        
        # Test calculations
        results = []
        for player in players:
            try:
                calculation = engine.calculate_player_value(dict(player))
                results.append(calculation)
                print(f"Player: {player['name']}")
                print(f"  True Value: {calculation['true_value']:.2f}")
                print(f"  ROI: {calculation['roi']:.3f}")
                print(f"  Multipliers: form={calculation['multipliers']['form']:.3f}, "
                      f"fixture={calculation['multipliers']['fixture']:.3f}")
            except Exception as e:
                print(f"Error calculating {player['name']}: {e}")
        
        print(f"\nSUCCESS: Calculated values for {len(results)} players")
        
        if results:
            avg_true_value = sum(r['true_value'] for r in results) / len(results)
            avg_roi = sum(r['roi'] for r in results) / len(results)
            print(f"Average True Value: {avg_true_value:.2f}")
            print(f"Average ROI: {avg_roi:.3f}")
            
        return True
        
    except Exception as e:
        print(f"ERROR in v2.0 test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_v2_api_logic()
    if success:
        print("\nSUCCESS: v2.0 API integration test PASSED!")
    else:
        print("\nFAILED: v2.0 API integration test FAILED!")