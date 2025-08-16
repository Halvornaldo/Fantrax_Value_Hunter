#!/usr/bin/env python3
"""
Simple test of Understat names without Unicode characters
"""

import requests

def test_understat_names():
    understat_players = [
        {'name': 'jhon duran', 'team': 'AVL', 'position': 'F'},
        {'name': 'matt o&#039;riley', 'team': 'BHA', 'position': 'M'},
        {'name': 'bruno', 'team': 'NEW', 'position': 'M'},
        {'name': 'martinez', 'team': 'AVL', 'position': 'G'},
        {'name': 'luis diaz', 'team': 'LIV', 'position': 'F'}
    ]
    
    response = requests.post(
        "http://localhost:5000/api/validate-import",
        json={'source_system': 'understat_test', 'players': understat_players}
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
                status = "MATCHED" if not player['needs_review'] else "REVIEW"
                print(f"  {name} -> {match['fantrax_name']} ({match['confidence']:.1f}% {status})")
            else:
                suggestions = len(match.get('suggested_matches', []))
                print(f"  {name} -> NO MATCH ({suggestions} suggestions)")
    else:
        print(f"ERROR: {response.status_code}")

if __name__ == "__main__":
    test_understat_names()