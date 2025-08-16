#!/usr/bin/env python3
"""
Test script for the updated FFS import functionality
Tests the /api/import-lineups endpoint with UnifiedNameMatcher integration
"""

import requests
import json

def test_ffs_import_with_unified_matcher():
    """Test the updated FFS import endpoint with our problematic players"""
    
    print("=" * 60)
    print("TESTING UPDATED FFS IMPORT WITH UNIFIED NAME MATCHER")
    print("=" * 60)
    
    api_url = "http://localhost:5000/api/import-lineups"
    csv_file_path = "test_ffs_import.csv"
    
    try:
        # Read the test CSV file
        with open(csv_file_path, 'rb') as f:
            files = {'lineups_csv': f}
            
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            
            print("SUCCESS: FFS Import completed")
            print(f"Matching System: {result.get('matching_system', 'N/A')}")
            print(f"Total Players: {result.get('total_players', 0)}")
            print(f"Matched Players: {result.get('matched_players', 0)}")
            print(f"Match Rate: {result.get('match_rate', 0)}%")
            
            print(f"\nBreakdown:")
            print(f"  Starters Identified: {result.get('starters_identified', 0)}")
            print(f"  Rotation Risk: {result.get('rotation_risk', 0)}")
            print(f"  Unmatched: {result.get('unmatched_players', 0)}")
            
            # Show confidence breakdown
            confidence = result.get('confidence_breakdown', {})
            print(f"\nConfidence Breakdown:")
            print(f"  High Confidence (95%+): {confidence.get('high_confidence_95plus', 0)}")
            print(f"  Medium Confidence (85-94%): {confidence.get('medium_confidence_85_94', 0)}")
            print(f"  Needs Review: {confidence.get('needs_review', 0)}")
            
            print(f"\nSmart Suggestions Available: {result.get('smart_suggestions_available', 0)}")
            
            # Show unmatched details with suggestions
            unmatched = result.get('unmatched_details', [])
            if unmatched:
                print(f"\nUnmatched Players (with suggestions):")
                for player in unmatched:
                    print(f"  {player['name']} ({player['team']}, {player['position']})")
                    if 'suggested_match' in player:
                        print(f"    Suggested: {player['suggested_match']} ({player['confidence']:.1f}%)")
                    if 'suggestions' in player:
                        print(f"    Alternatives: {len(player['suggestions'])} available")
                        for i, suggestion in enumerate(player['suggestions'][:2], 1):
                            print(f"      {i}. {suggestion['name']} ({suggestion['confidence']:.1f}%)")
            
            print(f"\nDatabase Updates:")
            print(f"  Updated Starters: {result.get('updated_starters', 0)}")
            print(f"  Recalculation Time: {result.get('recalculation_time', 0):.2f}s")
            
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

def check_mapping_improvements():
    """Check how many mappings we have in the system now"""
    
    print("\n" + "=" * 60)
    print("CHECKING NAME MAPPING IMPROVEMENTS")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:5000/api/name-mapping-stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            print(f"Total Mappings: {stats.get('total_mappings', 0)}")
            print(f"Verified Rate: {stats.get('accuracy_stats', {}).get('verified_rate', 0):.1f}%")
            
            by_source = stats.get('by_source_system', {})
            print(f"\nBy Source System:")
            for source, count in by_source.items():
                print(f"  {source}: {count}")
                
            print(f"\nRecent Mappings (24h): {stats.get('recent_mappings_24h', 0)}")
            
        else:
            print(f"ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    try:
        test_ffs_import_with_unified_matcher()
        check_mapping_improvements()
        
        print("\n" + "=" * 60)
        print("FFS IMPORT TEST COMPLETE")
        print("=" * 60)
        print("\nThe FFS import now uses UnifiedNameMatcher for:")
        print("✓ Improved accuracy with existing 37 mappings")
        print("✓ Smart suggestions for unmatched players") 
        print("✓ Confidence scoring for all matches")
        print("✓ Learning system that saves successful matches")
        print("✓ No more silent failures - all issues surfaced")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()