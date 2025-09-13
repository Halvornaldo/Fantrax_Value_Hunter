#!/usr/bin/env python3
"""
Debug script to isolate FFP import issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from name_matching.unified_matcher import UnifiedNameMatcher
import time

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'fantrax_user',
    'password': 'fantrax_password',
    'database': 'fantrax_value_hunter'
}

def test_name_matching():
    """Test name matching for specific players"""
    print("🔍 Testing UnifiedNameMatcher...")
    
    matcher = UnifiedNameMatcher(DB_CONFIG)
    
    test_players = [
        {"name": "Mohamed Salah", "team": "LIV", "position": "Unknown"},
        {"name": "Erling Haaland", "team": "MCI", "position": "Unknown"}
    ]
    
    for player in test_players:
        print(f"\nTesting: {player['name']} ({player['team']})")
        
        start_time = time.time()
        
        # Test with FFP source system
        result_ffp = matcher.match_player(
            source_name=player['name'],
            source_system='ffp',
            team=player['team'],
            position=player['position']
        )
        
        ffp_time = time.time() - start_time
        
        print(f"  FFP result: fantrax_id={result_ffp['fantrax_id']}, confidence={result_ffp['confidence']}, time={ffp_time:.2f}s")
        
        # Test with FFS source system for comparison
        start_time = time.time()
        
        result_ffs = matcher.match_player(
            source_name=player['name'],
            source_system='ffs',
            team=player['team'],
            position=player['position']
        )
        
        ffs_time = time.time() - start_time
        
        print(f"  FFS result: fantrax_id={result_ffs['fantrax_id']}, confidence={result_ffs['confidence']}, time={ffs_time:.2f}s")

def test_database_update():
    """Test database update operations"""
    print("\n💾 Testing database operations...")
    
    import psycopg2
    import psycopg2.extras
    from src.gameweek_manager import GameweekManager
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get current gameweek
    gw_manager = GameweekManager()
    gameweek = gw_manager.get_current_gameweek()
    print(f"Current gameweek: {gameweek}")
    
    # Test setting all players to 0.35
    start_time = time.time()
    cursor.execute("""
        UPDATE player_metrics 
        SET starter_multiplier = %s
        WHERE gameweek = %s
    """, [0.35, gameweek])
    
    all_players_updated = cursor.rowcount
    update_time = time.time() - start_time
    
    print(f"Set {all_players_updated} players to 0.35x in {update_time:.2f}s")
    
    # Test updating specific players
    test_updates = [
        {"player_id": 8, "multiplier": 1.0, "name": "Mohamed Salah"},  # Salah should be ID 8 based on previous tests
        {"player_id": 11, "multiplier": 1.0, "name": "Erling Haaland"}  # Haaland ID - we need to find this
    ]
    
    for update in test_updates:
        start_time = time.time()
        cursor.execute("""
            UPDATE player_metrics 
            SET starter_multiplier = %s
            WHERE player_id = %s AND gameweek = %s
        """, [update['multiplier'], update['player_id'], gameweek])
        
        rows_affected = cursor.rowcount
        update_time = time.time() - start_time
        
        print(f"Updated {update['name']} (ID {update['player_id']}) to {update['multiplier']}x: {rows_affected} rows affected in {update_time:.3f}s")
    
    conn.commit()
    conn.close()

def test_recalculation():
    """Test the recalculation step"""
    print("\n🧮 Testing recalculation...")
    
    # This imports from app.py where recalculate_true_values is defined
    from src.app import recalculate_true_values
    from src.gameweek_manager import GameweekManager
    
    gw_manager = GameweekManager()
    gameweek = gw_manager.get_current_gameweek()
    
    start_time = time.time()
    result = recalculate_true_values(gameweek)
    recalc_time = time.time() - start_time
    
    print(f"Recalculation completed in {recalc_time:.2f}s")
    print(f"Result: {result}")

if __name__ == "__main__":
    print("🚀 FFP Import Debug Script")
    print("=" * 50)
    
    try:
        test_name_matching()
        test_database_update()
        test_recalculation()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()