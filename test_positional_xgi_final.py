#!/usr/bin/env python3
"""
Test the final positional xGI implementation
"""

import sys
import os
sys.path.append(os.getcwd())

from calculation_engine_v2 import FormulaEngineV2, load_system_parameters

def test_positional_xgi():
    """Test the positional xGI implementation"""
    print("=== Testing Positional xGI Implementation ===")

    # Initialize engine with required parameters
    db_config = {}  # Mock config for testing
    parameters = load_system_parameters()
    engine = FormulaEngineV2(db_config, parameters)

    # Test data with different positions and xGI values
    test_players = [
        {
            "name": "Mo Salah",
            "position": "M/F",
            "xgi90": 0.65,  # High xGI
            "team": "Liverpool"
        },
        {
            "name": "Van Dijk",
            "position": "D",
            "xgi90": 0.15,  # High for defender
            "team": "Liverpool"
        },
        {
            "name": "Average Midfielder",
            "position": "M",
            "xgi90": 0.231,  # Exactly average
            "team": "Arsenal"
        },
        {
            "name": "Poor Forward",
            "position": "F",
            "xgi90": 0.20,  # Below average for forward
            "team": "Brighton"
        },
        {
            "name": "D/M Player",
            "position": "D/M",
            "xgi90": 0.12,  # Should use D average
            "team": "Newcastle"
        },
        {
            "name": "Goalkeeper",
            "position": "G",
            "xgi90": 0.05,  # Should always get 1.0x
            "team": "ManCity"
        }
    ]

    print("\nTesting individual players:")
    print("-" * 60)
    print(f"{'Player':<20} {'Pos':<5} {'xGI90':<6} {'Multiplier':<10} {'Expected'}")
    print("-" * 60)

    for player in test_players:
        multiplier = engine._calculate_xgi_multiplier(player)

        # Calculate expected values for verification
        if player["position"] == "G":
            expected = "1.0x (GK)"
        elif player["position"] == "M/F":
            # Should use weighted average: 0.7 * 0.425 + 0.3 * 0.231 = 0.3664
            expected = f"~{1 + ((player['xgi90'] / 0.3664) - 1) * 0.5:.2f}x"
        elif player["position"] == "D/M":
            # Should use D average: 0.099
            expected = f"~{1 + ((player['xgi90'] / 0.099) - 1) * 0.5:.2f}x"
        elif player["position"] == "M":
            # Exactly average should be 1.0x
            expected = f"~{1 + ((player['xgi90'] / 0.231) - 1) * 0.5:.2f}x"
        elif player["position"] == "F":
            expected = f"~{1 + ((player['xgi90'] / 0.425) - 1) * 0.5:.2f}x"
        elif player["position"] == "D":
            expected = f"~{1 + ((player['xgi90'] / 0.099) - 1) * 0.5:.2f}x"

        print(f"{player['name']:<20} {player['position']:<5} {player['xgi90']:<6} {multiplier:<10.3f} {expected}")

    print("\n=== Configuration Check ===")
    params = engine.params.get('formula_optimization_v2', {})
    pos_xgi = params.get('positional_xgi', {})

    print(f"Positional xGI enabled: {pos_xgi.get('enabled', False)}")
    print(f"xGI weight: {pos_xgi.get('xgi_weight', 'N/A')}")
    print(f"M/F position weight: {pos_xgi.get('mf_position_weight', 'N/A')}")
    print(f"Position averages: {pos_xgi.get('position_averages', 'N/A')}")

    print("\n=== Integration Check ===")
    xgi_integration = engine.params.get('xgi_integration', {})
    print(f"xGI integration enabled: {xgi_integration.get('enabled', False)}")

    print("\n[SUCCESS] Positional xGI implementation test completed!")

if __name__ == "__main__":
    test_positional_xgi()