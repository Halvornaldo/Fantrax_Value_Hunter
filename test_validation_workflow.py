#!/usr/bin/env python3
"""
Test the validation UI workflow with the 11 players that need manual review
This simulates the real workflow users would follow
"""

import requests
import json

def test_validation_ui_workflow():
    """Test the complete validation workflow for manual review players"""
    
    print("=" * 60)
    print("TESTING VALIDATION UI WORKFLOW")
    print("Simulating user reviewing the 11 problematic players")
    print("=" * 60)
    
    # The 11 players that needed manual review from our realistic test
    review_players = [
        {'name': 'bruno', 'team': 'NEW', 'position': 'M'},
        {'name': 'son heung-min', 'team': 'TOT', 'position': 'F'}, 
        {'name': 'de bruyne', 'team': 'MCI', 'position': 'M'},
        {'name': 'salah', 'team': 'LIV', 'position': 'F'},
        {'name': 'kane', 'team': 'BAY', 'position': 'F'},
        {'name': 'o&#039;neil', 'team': 'BOU', 'position': 'M'},
        {'name': 'saint-maximin', 'team': 'NEW', 'position': 'F'},
        {'name': 'ake', 'team': 'MCI', 'position': 'D'},
        {'name': 'wood', 'team': 'NEW', 'position': 'F'},
        {'name': 'nonexistent player', 'team': 'MCI', 'position': 'M'},
        {'name': 'x', 'team': 'MCI', 'position': 'D'}
    ]
    
    # Step 1: Validate the import (what the UI does first)
    print("STEP 1: Validating import data...")
    validation_response = requests.post(
        "http://localhost:5000/api/validate-import",
        json={'source_system': 'understat_validation_test', 'players': review_players}
    )
    
    if validation_response.status_code != 200:
        print(f"ERROR in validation: {validation_response.status_code}")
        return
    
    validation_data = validation_response.json()
    print(f"Validation complete: {validation_data['summary']['needs_review']} players need review")
    
    # Step 2: For each player needing review, get detailed suggestions
    print(f"\nSTEP 2: Getting suggestions for each player...")
    suggestions_results = []
    
    for player in review_players:
        print(f"\nGetting suggestions for: {player['name']} ({player['team']}, {player['position']})")
        
        suggestion_response = requests.post(
            "http://localhost:5000/api/get-player-suggestions",
            json={
                'source_name': player['name'],
                'team': player['team'],
                'position': player['position'],
                'source_system': 'understat_validation_test',
                'top_n': 3
            }
        )
        
        if suggestion_response.status_code == 200:
            suggestion_data = suggestion_response.json()
            suggestions = suggestion_data.get('suggestions', [])
            
            if suggestions:
                print(f"  Found {len(suggestions)} suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"    {i}. {suggestion['name']} ({suggestion['team']}, {suggestion['position']}) - {suggestion['confidence']:.1f}%")
                
                suggestions_results.append({
                    'player': player,
                    'suggestions': suggestions,
                    'has_good_suggestion': any(s['confidence'] >= 70 for s in suggestions)
                })
            else:
                print(f"  No suggestions found")
                suggestions_results.append({
                    'player': player,
                    'suggestions': [],
                    'has_good_suggestion': False
                })
        else:
            print(f"  ERROR getting suggestions: {suggestion_response.status_code}")
    
    # Step 3: Simulate user confirming some obvious matches
    print(f"\nSTEP 3: Simulating user confirmations...")
    confirmed_mappings = []
    
    for result in suggestions_results:
        player = result['player']
        suggestions = result['suggestions']
        
        # Simulate user logic: confirm if there's a high-confidence suggestion
        if suggestions and suggestions[0]['confidence'] >= 60:
            best_suggestion = suggestions[0]
            print(f"\nUser confirms: {player['name']} -> {best_suggestion['name']}")
            
            # Test the confirm mapping API
            confirm_response = requests.post(
                "http://localhost:5000/api/confirm-mapping",
                json={
                    'source_name': player['name'],
                    'source_system': 'understat_validation_test',
                    'fantrax_id': best_suggestion['fantrax_id'],
                    'user_id': 'validation_test_user'
                }
            )
            
            if confirm_response.status_code == 200:
                confirm_data = confirm_response.json()
                print(f"  Mapping confirmed successfully (ID: {confirm_data.get('mapping_id')})")
                confirmed_mappings.append({
                    'source_name': player['name'],
                    'fantrax_id': best_suggestion['fantrax_id'],
                    'fantrax_name': best_suggestion['name'],
                    'confidence': best_suggestion['confidence']
                })
            else:
                print(f"  ERROR confirming mapping: {confirm_response.status_code}")
        else:
            print(f"\nUser skips: {player['name']} (no good suggestions)")
    
    # Step 4: Test apply import with confirmed mappings
    print(f"\nSTEP 4: Testing apply import with {len(confirmed_mappings)} confirmed mappings...")
    
    confirmed_mappings_dict = {
        mapping['source_name']: {
            'fantrax_id': mapping['fantrax_id'],
            'fantrax_name': mapping['fantrax_name'],
            'confidence': mapping['confidence']
        }
        for mapping in confirmed_mappings
    }
    
    # Test dry run first
    apply_response = requests.post(
        "http://localhost:5000/api/apply-import",
        json={
            'source_system': 'understat_validation_test',
            'players': review_players,
            'confirmed_mappings': confirmed_mappings_dict,
            'dry_run': True
        }
    )
    
    if apply_response.status_code == 200:
        apply_data = apply_response.json()
        print(f"Dry run successful: Would import {apply_data['import_count']} players")
        print(f"Message: {apply_data['message']}")
    else:
        print(f"ERROR in apply import: {apply_response.status_code}")
    
    # Step 5: Check system stats after our test
    print(f"\nSTEP 5: Checking system improvements...")
    stats_response = requests.get("http://localhost:5000/api/name-mapping-stats")
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"Total mappings now: {stats.get('total_mappings', 'N/A')}")
        
        by_source = stats.get('by_source_system', {})
        validation_test_count = by_source.get('understat_validation_test', 0)
        print(f"New validation test mappings: {validation_test_count}")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("VALIDATION WORKFLOW SUMMARY")
    print("=" * 60)
    
    total_players = len(review_players)
    players_with_suggestions = len([r for r in suggestions_results if r['suggestions']])
    players_with_good_suggestions = len([r for r in suggestions_results if r['has_good_suggestion']])
    confirmed_count = len(confirmed_mappings)
    
    print(f"Total problematic players: {total_players}")
    print(f"Players with suggestions: {players_with_suggestions} ({players_with_suggestions/total_players*100:.1f}%)")
    print(f"Players with good suggestions (60%+): {players_with_good_suggestions} ({players_with_good_suggestions/total_players*100:.1f}%)")
    print(f"User confirmed mappings: {confirmed_count} ({confirmed_count/total_players*100:.1f}%)")
    print(f"Still need manual work: {total_players - confirmed_count} ({(total_players-confirmed_count)/total_players*100:.1f}%)")
    
    if players_with_suggestions/total_players >= 0.6:
        print("\nEXCELLENT: Validation tool provides good guidance for most players")
    elif players_with_suggestions/total_players >= 0.4:
        print("\nGOOD: Validation tool helps with many players")
    else:
        print("\nNEEDS WORK: Validation tool provides limited help")

if __name__ == "__main__":
    test_validation_ui_workflow()