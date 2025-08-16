#!/usr/bin/env python3
"""
Realistic Understat test without Unicode characters
"""

import requests

def test_realistic_understat():
    realistic_players = [
        # Should have mappings
        {'name': 'emiliano buendia', 'team': 'AVL', 'position': 'M'},
        {'name': 'bruno', 'team': 'NEW', 'position': 'M'},
        
        # Common names that probably don't have exact mappings
        {'name': 'son heung-min', 'team': 'TOT', 'position': 'F'},
        {'name': 'virgil van dijk', 'team': 'LIV', 'position': 'D'},
        {'name': 'de bruyne', 'team': 'MCI', 'position': 'M'},
        {'name': 'salah', 'team': 'LIV', 'position': 'F'},
        {'name': 'kane', 'team': 'BAY', 'position': 'F'},
        
        # HTML encoded
        {'name': 'o&#039;neil', 'team': 'BOU', 'position': 'M'},
        
        # Challenging cases
        {'name': 'saint-maximin', 'team': 'NEW', 'position': 'F'},
        {'name': 'ake', 'team': 'MCI', 'position': 'D'},
        {'name': 'wood', 'team': 'NEW', 'position': 'F'},
        
        # Edge cases
        {'name': 'nonexistent player', 'team': 'MCI', 'position': 'M'},
        {'name': 'x', 'team': 'MCI', 'position': 'D'}
    ]
    
    response = requests.post(
        "http://localhost:5000/api/validate-import",
        json={'source_system': 'understat_realistic', 'players': realistic_players}
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("REALISTIC UNDERSTAT RESULTS:")
        print(f"Total: {result['summary']['total']}")
        print(f"Direct Matches: {result['summary']['matched']} ({result['summary']['match_rate']:.1f}%)")
        print(f"Need Review: {result['summary']['needs_review']}")
        print(f"Failed: {result['summary']['failed']}")
        
        # Show breakdown by result type
        direct_matches = []
        needs_review = []
        no_matches = []
        
        for player in result['players']:
            name = player['original_name']
            match = player['match_result']
            
            if match['fantrax_name'] and not player['needs_review']:
                direct_matches.append((name, match['fantrax_name'], match['confidence']))
            elif player['needs_review']:
                if match['fantrax_name']:
                    needs_review.append((name, match['fantrax_name'], match['confidence']))
                else:
                    suggestions = len(match.get('suggested_matches', []))
                    needs_review.append((name, f"{suggestions} suggestions", 0))
            else:
                no_matches.append(name)
        
        print(f"\nDIRECT MATCHES ({len(direct_matches)}):")
        for name, fantrax_name, confidence in direct_matches:
            print(f"  + {name} -> {fantrax_name} ({confidence:.1f}%)")
        
        print(f"\nNEEDS REVIEW ({len(needs_review)}):")
        for name, result, confidence in needs_review[:8]:  # Show first 8
            if confidence > 0:
                print(f"  ? {name} -> {result} ({confidence:.1f}%)")
            else:
                print(f"  ? {name} -> {result}")
        
        print(f"\nNO MATCHES ({len(no_matches)}):")
        for name in no_matches:
            print(f"  x {name}")
        
        # Calculate realistic expectations
        total_valid = len([p for p in realistic_players if p['name'] and len(p['name']) > 1])
        actionable = len(direct_matches) + len(needs_review)
        
        print(f"\nREALISTIC ASSESSMENT:")
        print(f"Automatic: {len(direct_matches)}/{total_valid} ({len(direct_matches)/total_valid*100:.1f}%)")
        print(f"Manual review: {len(needs_review)}/{total_valid} ({len(needs_review)/total_valid*100:.1f}%)")
        print(f"Total actionable: {actionable}/{total_valid} ({actionable/total_valid*100:.1f}%)")
        
        if actionable/total_valid >= 0.8:
            print("STATUS: Excellent - Ready for production")
        elif actionable/total_valid >= 0.6:
            print("STATUS: Good - Expect regular manual reviews")
        else:
            print("STATUS: Needs improvement")
    else:
        print(f"ERROR: {response.status_code}")

if __name__ == "__main__":
    test_realistic_understat()