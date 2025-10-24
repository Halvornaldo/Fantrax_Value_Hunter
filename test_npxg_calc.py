#!/usr/bin/env python3
"""
Test NPxG calculation directly
"""

import sys
sys.path.append('src')
sys.path.append('.')

from calculation_engine_v2 import FormulaEngineV2
import json

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

# Load parameters
with open('config/system_parameters.json', 'r') as f:
    params = json.load(f)

print(f"Fixture enabled: {params['formula_optimization_v2']['formula_toggles']['fixture_enabled']}")
print(f"NPxG enabled: {params['npxg_fixture']['enabled']}")
print(f"Slider value: {params['formula_optimization_v2']['exponential_fixture']['base']}")

# Initialize engine
engine = FormulaEngineV2(DB_CONFIG, params)

# Test player data
test_player = {
    'player_id': 1,
    'name': 'Test Haaland',
    'position': 'F',
    'next_opponent': 'EVE',
    'is_home': True,
    'price': 15.0,
    'ppg': 10.0,
    'xgi90': 0.5,
    'baseline_xgi': 0.4,
    'fixture_difficulty': 0.0,
    'starter_multiplier': 1.0,
    'total_points_historical': 0,
    'games_played_historical': 0,
    'games_historical': 0,
    'total_points_current': 100,
    'games_current': 10,
    'historical_ppg': None
}

print(f"\nTesting with: {test_player['name']} vs {test_player['next_opponent']} ({'HOME' if test_player['is_home'] else 'AWAY'})")

# Calculate value
result = engine.calculate_player_value(test_player)

print(f"\nResult:")
print(f"  Fixture multiplier: {result['multipliers']['fixture']}")
print(f"  All multipliers: {result['multipliers']}")