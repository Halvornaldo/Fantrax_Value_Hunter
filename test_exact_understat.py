#!/usr/bin/env python3
"""
Test with exact Understat names from our mappings
"""

import requests

def test_exact_understat_mappings():
    # Test exact names that should match our imported mappings
    exact_players = [
        {'name': 'emiliano buendia', 'team': 'AVL', 'position': 'M'},
        {'name': 'bruno', 'team': 'NEW', 'position': 'M'},
        {'name': 'martinez', 'team': 'AVL', 'position': 'G'},
        {'name': 'gabriel', 'team': 'ARS', 'position': 'D'},
        {'name': 'matt o&#039;riley', 'team': 'BHA', 'position': 'M'}
    ]
    
    response = requests.post(
        "http://localhost:5000/api/validate-import",
        json={'source_system': 'understat', 'players': exact_players}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Match Rate: {result['summary']['match_rate']:.1f}%")
        print(f"Matched: {result['summary']['matched']}")
        print(f"Need Review: {result['summary']['needs_review']}")
        
        print("\nPlayer Results:")
        for player in result['players']:
            name = player['original_name']
            match = player['match_result']
            
            if match['fantrax_name']:
                if not player['needs_review']:
                    print(f"  {name} -> {match['fantrax_name']} ({match['confidence']:.1f}% DIRECT HIT!)")
                else:
                    print(f"  {name} -> {match['fantrax_name']} ({match['confidence']:.1f}% needs review)")
            else:
                suggestions = len(match.get('suggested_matches', []))
                print(f"  {name} -> NO MATCH ({suggestions} suggestions)")
    else:
        print(f"ERROR: {response.status_code}")

if __name__ == "__main__":
    test_exact_understat_mappings()