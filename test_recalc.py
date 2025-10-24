#!/usr/bin/env python3
"""
Test recalculation to see what fixture multiplier is being calculated
"""

import sys
sys.path.append('src')
sys.path.append('.')

from src.app import recalculate_true_values

print("Running recalculation...")
result = recalculate_true_values()
print(f"Result: {result}")