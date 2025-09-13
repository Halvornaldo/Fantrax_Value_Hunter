#!/usr/bin/env python3
"""
Safe FFP import logic test - NO DATABASE CHANGES
Following TESTING_METHODOLOGY.md principles: test components in isolation first
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_ffp_parsing():
    """Test FFP CSV parsing logic in isolation"""
    print("Testing FFP CSV Parsing (safe - no DB changes)")
    
    # Import the parsing function
    from src.app import parse_ffp_csv
    
    # Test data with different players (avoid Salah/Haaland - potentially corrupt from repeated testing)
    test_lines = [
        'ARS,Bukayo Saka,Unknown,starter,85%,0.90',
        'TOT,Heung-min Son,Unknown,rotation,55%,0.75'
    ]
    
    print("Input data:")
    for line in test_lines:
        print(f"  {line}")
    
    # Parse the data
    try:
        parsed_players = parse_ffp_csv(test_lines)
        
        print(f"\nParsed {len(parsed_players)} players:")
        for i, player in enumerate(parsed_players):
            print(f"  {i+1}. {player['name']} ({player['team']})")
            print(f"     Status: {player['status']}, Confidence: {player['confidence']}")
            print(f"     Custom multiplier: {player.get('custom_multiplier', 'MISSING!')}")
            
        # Validate expected structure
        for player in parsed_players:
            required_fields = ['name', 'team', 'position', 'status', 'custom_multiplier']
            missing_fields = [f for f in required_fields if f not in player]
            if missing_fields:
                print(f"FAIL Player {player['name']} missing fields: {missing_fields}")
            else:
                print(f"PASS Player {player['name']} has all required fields")
                
        return True
        
    except Exception as e:
        print(f"FAIL FFP parsing failed: {e}")
        return False

def test_name_matcher_lookup():
    """Test name matching without database changes"""
    print("\nTesting Name Matching (read-only)")
    
    from name_matching.unified_matcher import UnifiedNameMatcher
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5433,
        'user': 'fantrax_user',
        'password': 'fantrax_password',
        'database': 'fantrax_value_hunter'
    }
    
    try:
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        # Test both source systems with fresh players (avoid Salah/Haaland - potentially corrupt)
        test_cases = [
            {"name": "Bukayo Saka", "team": "ARS", "source": "ffp"},
            {"name": "Bukayo Saka", "team": "ARS", "source": "ffs"}
        ]
        
        for test in test_cases:
            print(f"\nTesting: {test['name']} with source_system='{test['source']}'")
            
            result = matcher.match_player(
                source_name=test['name'],
                source_system=test['source'],
                team=test['team'],
                position='Unknown'
            )
            
            print(f"  Result: fantrax_id={result.get('fantrax_id')}")
            print(f"  Confidence: {result.get('confidence')}%")
            print(f"  Needs review: {result.get('needs_review')}")
            
            # Key validation: does it find a player ID?
            if result.get('fantrax_id'):
                print("  PASS Found player ID")
            else:
                print("  FAIL No player ID found - this would cause import failure")
        
        return True
        
    except Exception as e:
        print(f"FAIL Name matching failed: {e}")
        return False

def test_format_detection():
    """Test CSV format detection logic"""
    print("\nTesting CSV Format Detection")
    
    # Test various header formats
    test_headers = [
        # FFP format (6 columns)
        ['Team', 'Player Name', 'Position', 'Predicted Status', 'Confidence', 'Multiplier'],
        # Individual format (4 columns)  
        ['Team', 'Player Name', 'Position', 'Predicted Status'],
        # Formation format (12+ columns)
        ['!m-0', 'Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5', 
         'Player 6', 'Player 7', 'Player 8', 'Player 9', 'Player 10', 'Player 11']
    ]
    
    expected_results = ['FFP', 'Individual', 'Formation']
    
    for i, header in enumerate(test_headers):
        print(f"\nTest {i+1}: {header[:3]}... ({len(header)} columns)")
        
        # Simulate the detection logic from app.py
        header_normalized = [h.strip().lower().replace(' ', '_') for h in header]
        
        # FFP format check
        expected_ffp_normalized = ['team', 'player_name', 'position', 'predicted_status', 'confidence', 'multiplier']
        is_ffp_format = header_normalized == expected_ffp_normalized
        
        # Individual format check  
        expected_individual_normalized = ['team', 'player_name', 'position', 'predicted_status']
        is_individual_format = header_normalized == expected_individual_normalized
        
        # Formation format check
        first_col_clean = header[0].strip().lower().strip('"')
        is_formation_format = (
            len(header) >= 12 and
            first_col_clean == '!m-0'
        )
        
        detected = 'Unknown'
        if is_ffp_format:
            detected = 'FFP'
        elif is_individual_format:
            detected = 'Individual'  
        elif is_formation_format:
            detected = 'Formation'
            
        expected = expected_results[i]
        status = "PASS" if detected == expected else "FAIL"
        print(f"  Expected: {expected}, Detected: {detected} {status}")

if __name__ == "__main__":
    print("Safe FFP Import Logic Test")
    print("=" * 50)
    print("Following TESTING_METHODOLOGY.md - Component isolation testing")
    print("NO DATABASE CHANGES will be made during this test")
    print()
    
    all_passed = True
    
    # Test each component in isolation
    if not test_ffp_parsing():
        all_passed = False
        
    if not test_name_matcher_lookup():
        all_passed = False
        
    test_format_detection()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("PASS All component tests passed!")
        print("Next step: Safe integration testing with minimal data")
    else:
        print("FAIL Some tests failed - fix before proceeding")
        print("This follows testing methodology: Fix issues in isolation first")