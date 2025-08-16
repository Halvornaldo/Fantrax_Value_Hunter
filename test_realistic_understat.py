#!/usr/bin/env python3
"""
Test with a realistic mix of Understat player names
Including names we DON'T have mappings for and edge cases
"""

import requests

def test_realistic_understat_data():
    """Test with a realistic mix of Understat names"""
    
    # Mix of names: some we have mappings for, some we don't, some edge cases
    realistic_players = [
        # Names we should have mappings for
        {'name': 'emiliano buendia', 'team': 'AVL', 'position': 'M'},
        {'name': 'bruno', 'team': 'NEW', 'position': 'M'},
        
        # Common variations that might not have exact mappings
        {'name': 'son heung-min', 'team': 'TOT', 'position': 'F'},
        {'name': 'trent alexander-arnold', 'team': 'LIV', 'position': 'D'},
        {'name': 'virgil van dijk', 'team': 'LIV', 'position': 'D'},
        
        # Names with accents/special chars (might need normalization)
        {'name': 'joão félix', 'team': 'CHE', 'position': 'F'},
        {'name': 'rúben dias', 'team': 'MCI', 'position': 'D'},
        {'name': 'raphaël varane', 'team': 'MUN', 'position': 'D'},
        
        # Understat-style variations (lowercase, shortened)
        {'name': 'de bruyne', 'team': 'MCI', 'position': 'M'},
        {'name': 'salah', 'team': 'LIV', 'position': 'F'},
        {'name': 'kane', 'team': 'BAY', 'position': 'F'},  # Wrong team (moved to Bayern)
        
        # HTML encoded names
        {'name': 'o&#039;neil', 'team': 'BOU', 'position': 'M'},
        {'name': 'joão pedro', 'team': 'BHA', 'position': 'F'},
        
        # Names that definitely won't match
        {'name': 'nonexistent player', 'team': 'MCI', 'position': 'M'},
        {'name': 'random name 123', 'team': 'ARS', 'position': 'F'},
        
        # Edge cases
        {'name': '', 'team': 'LIV', 'position': 'M'},  # Empty name
        {'name': 'x', 'team': 'MCI', 'position': 'D'},  # Single character
        
        # Real challenging cases from Understat
        {'name': 'saint-maximin', 'team': 'NEW', 'position': 'F'},
        {'name': 'ake', 'team': 'MCI', 'position': 'D'},
        {'name': 'mccarthy', 'team': 'SOU', 'position': 'G'},
        {'name': 'wood', 'team': 'NEW', 'position': 'F'}
    ]
    
    print("=" * 60)
    print("REALISTIC UNDERSTAT NAME MATCHING TEST")
    print("Testing with diverse, challenging player names")
    print("=" * 60)
    
    response = requests.post(
        "http://localhost:5000/api/validate-import",
        json={'source_system': 'understat_realistic', 'players': realistic_players}
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"OVERALL RESULTS:")
        print(f"Total Players: {result['summary']['total']}")
        print(f"Direct Matches: {result['summary']['matched']}")
        print(f"Need Review: {result['summary']['needs_review']}")
        print(f"Failed: {result['summary']['failed']}")
        print(f"Match Rate: {result['summary']['match_rate']:.1f}%")
        
        print(f"\nPosition Breakdown:")
        for pos, stats in result['position_breakdown'].items():
            if stats['total'] > 0:
                print(f"  {pos}: {stats['matched']}/{stats['total']} ({stats['match_rate']:.1f}%)")
        
        # Categorize results
        direct_matches = []
        needs_review = []
        no_match = []
        
        for player in result['players']:
            name = player['original_name']
            match = player['match_result']
            
            if match['fantrax_name'] and not player['needs_review']:
                direct_matches.append((name, match['fantrax_name'], match['confidence']))
            elif match['fantrax_name'] and player['needs_review']:
                needs_review.append((name, match['fantrax_name'], match['confidence']))
            else:
                suggestions = match.get('suggested_matches', [])
                no_match.append((name, len(suggestions)))
        
        print(f"\nDIRECT MATCHES ({len(direct_matches)}):")
        for name, fantrax_name, confidence in direct_matches[:5]:  # Show first 5
            print(f"  ✓ {name} → {fantrax_name} ({confidence:.1f}%)")
        if len(direct_matches) > 5:
            print(f"  ... and {len(direct_matches) - 5} more")
        
        print(f"\nNEEDS MANUAL REVIEW ({len(needs_review)}):")
        for name, fantrax_name, confidence in needs_review[:5]:  # Show first 5
            print(f"  ? {name} → {fantrax_name} ({confidence:.1f}%)")
        if len(needs_review) > 5:
            print(f"  ... and {len(needs_review) - 5} more")
        
        print(f"\nNO MATCHES FOUND ({len(no_match)}):")
        for name, suggestion_count in no_match[:5]:  # Show first 5
            print(f"  ✗ {name} ({suggestion_count} suggestions)")
        if len(no_match) > 5:
            print(f"  ... and {len(no_match) - 5} more")
        
        # Calculate realistic assessment
        effective_resolution = len(direct_matches) + len(needs_review)
        total_valid = len([p for p in realistic_players if p['name'] and len(p['name']) > 1])
        
        print(f"\nREALISTIC ASSESSMENT:")
        print("=" * 30)
        print(f"Automatic processing: {len(direct_matches)}/{total_valid} ({len(direct_matches)/total_valid*100:.1f}%)")
        print(f"Manual review needed: {len(needs_review)}/{total_valid} ({len(needs_review)/total_valid*100:.1f}%)")
        print(f"Truly problematic: {len(no_match)}/{total_valid} ({len(no_match)/total_valid*100:.1f}%)")
        print(f"Overall actionable: {effective_resolution}/{total_valid} ({effective_resolution/total_valid*100:.1f}%)")
        
        if effective_resolution/total_valid >= 0.8:
            print("\n✅ EXCELLENT: System ready for production Understat integration")
        elif effective_resolution/total_valid >= 0.6:
            print("\n⚠️  GOOD: System mostly ready, expect regular manual reviews")
        else:
            print("\n❌ NEEDS WORK: Significant manual intervention required")
            
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_realistic_understat_data()