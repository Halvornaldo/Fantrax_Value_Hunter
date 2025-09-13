#!/usr/bin/env python3
"""
Test CSV import with the fantasyfootballpundit CSV
"""
import sys
import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import parse_ffp_formation_csv
from src.name_matching.unified_matcher import UnifiedNameMatcher

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'fantrax_user', 
    'password': 'fantrax_password',
    'database': 'fantrax_value_hunter'
}

def test_csv_import():
    """Test the CSV import process"""
    csv_file_path = r'c:/Users/halvo/Downloads/fantasyfootballpundit (1).csv'
    
    print("Testing FFP CSV Import")
    print(f"File: {csv_file_path}")
    print("=" * 60)
    
    # Read CSV file
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        print(f"Read {len(lines)} lines from CSV")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("Connected to database")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return
    
    try:
        # Parse the FFP CSV
        print("\nParsing FFP CSV format...")
        players_to_process = parse_ffp_formation_csv(lines, cursor)
        print(f"Parsed {len(players_to_process)} players from CSV")
        
        if len(players_to_process) == 0:
            print("No players found in CSV - checking first few lines:")
            for i, line in enumerate(lines[:10]):
                print(f"Line {i+1}: {line.strip()[:100]}...")
            return
        
        # Initialize name matcher
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        # Track results
        matched_players = []
        failed_players = []
        
        print(f"\nProcessing {len(players_to_process)} players...")
        print("=" * 60)
        
        for i, player_info in enumerate(players_to_process, 1):
            player_name = player_info['name']
            team = player_info['team']
            position = player_info['position']
            confidence = player_info['confidence']
            multiplier = player_info['multiplier']
            
            print(f"\n[{i:3d}] {player_name} ({team}) - {confidence}% confidence -> {multiplier}x multiplier")
            
            # Try to match the player
            match_result = matcher.match_player(
                source_name=player_name,
                source_system='ffp',
                team=team,
                position=position
            )
            
            confidence_threshold = 80.0
            
            if match_result['fantrax_id'] and (not match_result['needs_review'] or match_result['confidence'] >= confidence_threshold):
                print(f"     SUCCESS -> {match_result['fantrax_name']} (confidence: {match_result['confidence']:.1f}%)")
                matched_players.append({
                    'csv_name': player_name,
                    'db_name': match_result['fantrax_name'],
                    'team': team,
                    'confidence': match_result['confidence'],
                    'multiplier': multiplier
                })
            else:
                print(f"     FAILED - confidence: {match_result.get('confidence', 0):.1f}%, needs_review: {match_result.get('needs_review', True)}")
                if match_result.get('suggested_matches'):
                    print(f"     Suggestions: {[s['name'] for s in match_result['suggested_matches'][:3]]}")
                failed_players.append({
                    'csv_name': player_name,
                    'team': team,
                    'position': position,
                    'confidence': match_result.get('confidence', 0),
                    'fantrax_id': match_result.get('fantrax_id'),
                    'needs_review': match_result.get('needs_review', True)
                })
        
        # Print summary
        print("\n" + "=" * 60)
        print("IMPORT RESULTS SUMMARY")
        print("=" * 60)
        
        total_players = len(players_to_process)
        matched_count = len(matched_players)
        failed_count = len(failed_players)
        match_rate = (matched_count / total_players * 100) if total_players > 0 else 0
        
        print(f"Total Players Processed: {total_players}")
        print(f"Successfully Matched: {matched_count} ({match_rate:.1f}%)")
        print(f"Failed to Match: {failed_count} ({100-match_rate:.1f}%)")
        
        if matched_players:
            print(f"\nMATCHED PLAYERS ({matched_count}):")
            for player in matched_players:
                print(f"   {player['csv_name']} -> {player['db_name']} ({player['team']}) [{player['multiplier']:.2f}x]")
        
        if failed_players and len(failed_players) <= 20:
            print(f"\nFAILED PLAYERS ({failed_count}):")
            for player in failed_players:
                print(f"   {player['csv_name']} ({player['team']}) - conf: {player['confidence']:.1f}%")
        elif failed_players:
            print(f"\nFAILED PLAYERS (showing first 20 of {failed_count}):")
            for player in failed_players[:20]:
                print(f"   {player['csv_name']} ({player['team']}) - conf: {player['confidence']:.1f}%")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_csv_import()