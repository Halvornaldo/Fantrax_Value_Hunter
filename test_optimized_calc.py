#!/usr/bin/env python3
"""
Test the optimized NPxG calculation
"""

import sys
sys.path.append('src')
sys.path.append('.')

from calculation_engine_v2 import FormulaEngineV2
import json
import time

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

print("=" * 70)
print("TESTING OPTIMIZED NPxG CALCULATION")
print("=" * 70)

print(f"\nNPxG enabled: {params['npxg_fixture']['enabled']}")
print(f"Slider value: {params['formula_optimization_v2']['exponential_fixture']['base']}")

# Initialize engine with optimized session
print("\nInitializing calculation engine...")
start_time = time.time()
engine = FormulaEngineV2(DB_CONFIG, params)
init_time = time.time() - start_time
print(f"Engine initialized in {init_time:.2f} seconds")

# Test multiple players
test_players = [
    {
        'player_id': 1,
        'name': 'Erling Haaland',
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
    },
    {
        'player_id': 2,
        'name': 'Mohamed Salah',
        'position': 'F',
        'next_opponent': 'CHE',
        'is_home': False,
        'price': 14.0,
        'ppg': 9.5,
        'xgi90': 0.45,
        'baseline_xgi': 0.4,
        'fixture_difficulty': 0.0,
        'starter_multiplier': 1.0,
        'total_points_historical': 0,
        'games_played_historical': 0,
        'games_historical': 0,
        'total_points_current': 95,
        'games_current': 10,
        'historical_ppg': None
    }
]

print("\nCalculating multipliers for test players:")
print("-" * 50)

calc_start = time.time()
for player in test_players:
    result = engine.calculate_player_value(player)
    location = "HOME" if player['is_home'] else "AWAY"
    print(f"{player['name']:20} vs {player['next_opponent']} ({location})")
    print(f"  Fixture multiplier: {result['multipliers']['fixture']:.3f}")
    print(f"  All multipliers: Form={result['multipliers']['form']:.3f}, "
          f"Fixture={result['multipliers']['fixture']:.3f}, "
          f"Starter={result['multipliers']['starter']:.3f}, "
          f"xGI={result['multipliers']['xgi']:.3f}")
    print()

calc_time = time.time() - calc_start
print(f"Calculated {len(test_players)} players in {calc_time:.3f} seconds")

print("=" * 70)
print("TEST COMPLETE")
print("The optimized version should be much faster with no repeated warnings")
print("=" * 70)