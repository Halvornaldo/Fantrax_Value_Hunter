#!/usr/bin/env python3
"""
Test script for the UnifiedNameMatcher
Tests the three problematic names we identified:
1. "Raya Martin" -> "David Raya"
2. "O'Riley" -> "Matt ORiley"  
3. "Fernando López" -> TBD
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from name_matching import UnifiedNameMatcher

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def test_problematic_names():
    """Test the three problematic names from our CSV import"""
    
    print("="*60)
    print("TESTING UNIFIED NAME MATCHER")
    print("="*60)
    
    matcher = UnifiedNameMatcher(DB_CONFIG)
    
    # Test cases from our problematic players
    test_cases = [
        {
            'name': 'Raya Martin',
            'team': 'ARS',
            'position': 'G',
            'expected': 'David Raya'
        },
        {
            'name': "O'Riley",
            'team': 'BHA',
            'position': 'M',
            'expected': 'Matt ORiley'
        },
        {
            'name': 'Fernando López',
            'team': 'WOL',
            'position': 'F',
            'expected': 'Unknown'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']} ({test_case['team']}, {test_case['position']})")
        print("-" * 40)
        
        result = matcher.match_player(
            source_name=test_case['name'],
            source_system='ffs_test',
            team=test_case['team'],
            position=test_case['position']
        )
        
        print(f"Match Found: {result['fantrax_name'] or 'NO MATCH'}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Strategy: {result['match_type']}")
        print(f"Needs Review: {result['needs_review']}")
        
        if result['suggested_matches']:
            print(f"\nSuggestions:")
            for j, suggestion in enumerate(result['suggested_matches'], 1):
                print(f"  {j}. {suggestion['name']} ({suggestion['confidence']:.1f}%)")
        
        if test_case['expected'] != 'Unknown':
            if result['fantrax_name'] == test_case['expected']:
                print("SUCCESS: CORRECT MATCH!")
            else:
                print(f"MISMATCH: Expected: {test_case['expected']}")

def test_matching_strategies():
    """Test individual matching strategies"""
    
    print("\n" + "="*60)
    print("TESTING MATCHING STRATEGIES")
    print("="*60)
    
    from name_matching.matching_strategies import MatchingStrategies
    
    strategies = MatchingStrategies()
    
    test_pairs = [
        ("Raya Martin", "David Raya"),
        ("O'Riley", "Matt ORiley"),
        ("Fernando López", "Pablo Sarabia"),
        ("Jhon Durán", "Duran"),
        ("Calvert-Lewin", "Dominic Calvert-Lewin")
    ]
    
    for source, target in test_pairs:
        print(f"\nTesting: '{source}' vs '{target}'")
        print("-" * 30)
        
        # Test each strategy
        strategy_methods = strategies.get_all_strategies()
        
        for strategy_name, strategy_func in strategy_methods:
            is_match, confidence = strategy_func(source, target)
            if is_match:
                print(f"  {strategy_name}: {confidence:.1f}%")

def test_suggestion_engine():
    """Test the suggestion engine"""
    
    print("\n" + "="*60)
    print("TESTING SUGGESTION ENGINE")
    print("="*60)
    
    from name_matching.suggestion_engine import SuggestionEngine
    
    engine = SuggestionEngine(DB_CONFIG)
    
    test_cases = [
        ('Fernando López', 'WOL', 'F'),
        ('Raya Martin', 'ARS', 'G'),
        ('Unknown Player', 'MCI', 'M')
    ]
    
    for name, team, position in test_cases:
        print(f"\nSuggestions for: {name} ({team}, {position})")
        print("-" * 40)
        
        suggestions = engine.get_player_suggestions(name, team, position, top_n=5)
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion['name']} ({suggestion['confidence']:.1f}%)")
        else:
            print("  No suggestions found")

if __name__ == "__main__":
    try:
        test_problematic_names()
        test_matching_strategies()
        test_suggestion_engine()
        
        print("\n" + "="*60)
        print("TESTING COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()