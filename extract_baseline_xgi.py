#!/usr/bin/env python3
"""
Extract 2024/25 season xGI data from Understat for Sprint 2 baseline
This will populate proper baseline_xgi values for normalized xGI calculation
"""

import sys
import os
import pandas as pd
import psycopg2
from datetime import datetime

# Add integration package to path
sys.path.append('C:/Users/halvo/.claude/Fantrax_Expected_Stats')
from integration_package import UnderstatIntegrator

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'fantrax_user',
    'password': 'fantrax_password',
    'database': 'fantrax_value_hunter'
}

def extract_historical_xgi_baseline():
    """Extract 2024/25 season xGI data to use as baseline for 2025/26 predictions"""
    
    print("=== Extracting 2024/25 xGI Data for Baseline ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize Understat integrator
        integrator = UnderstatIntegrator(DB_CONFIG)
        
        # Extract 2024/25 season data
        print("\n1. Extracting 2024/25 season data from Understat...")
        historical_df = integrator.extract_understat_per90_stats(season="2024/2025")
        
        if historical_df.empty:
            print("ERROR: No historical data available for 2024/25 season")
            return False
            
        print(f"   OK Extracted {len(historical_df)} players from 2024/25 season")
        
        # Connect to database
        print("\n2. Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get current players for matching
        print("\n3. Loading current player roster for matching...")
        cursor.execute("""
            SELECT id, name, team, position 
            FROM players 
            ORDER BY name
        """)
        current_players = cursor.fetchall()
        print(f"   OK Loaded {len(current_players)} current players")
        
        # Match historical data to current players
        print("\n4. Matching historical xGI to current players...")
        matched_count = 0
        unmatched_players = []
        updates = []
        
        for _, historical_player in historical_df.iterrows():
            hist_name = historical_player.get('player_name', '').strip()
            hist_xgi90 = float(historical_player.get('xGI90', 0.0))
            hist_team = historical_player.get('team', '').strip()
            
            # Try to find matching current player
            best_match = None
            
            for player_id, curr_name, curr_team, position in current_players:
                # Exact name match (preferred)
                if hist_name.lower() == curr_name.lower():
                    best_match = (player_id, curr_name, curr_team, position)
                    break
                    
                # Partial name match with same team
                if (hist_name.lower() in curr_name.lower() or 
                    curr_name.lower() in hist_name.lower()) and \
                   hist_team.lower() in curr_team.lower():
                    best_match = (player_id, curr_name, curr_team, position)
                    break
            
            if best_match:
                player_id, curr_name, curr_team, position = best_match
                updates.append((hist_xgi90, player_id, hist_name, curr_name))
                matched_count += 1
            else:
                unmatched_players.append({
                    'historical_name': hist_name,
                    'historical_team': hist_team,
                    'xGI90': hist_xgi90
                })
        
        print(f"   OK Matched {matched_count} players")
        print(f"   WARNING {len(unmatched_players)} unmatched historical players")
        
        # Apply updates to database
        if updates:
            print(f"\n5. Updating baseline_xgi for {len(updates)} players...")
            
            update_sql = """
                UPDATE players 
                SET baseline_xgi = %s,
                    last_understat_update = NOW()
                WHERE id = %s
            """
            
            batch_updates = [(xgi90, player_id) for xgi90, player_id, _, _ in updates]
            cursor.executemany(update_sql, batch_updates)
            conn.commit()
            
            print(f"   OK Updated {len(batch_updates)} baseline_xgi values")
            
            # Show sample of updates
            print(f"\n6. Sample updates:")
            for i, (xgi90, player_id, hist_name, curr_name) in enumerate(updates[:5]):
                print(f"   {i+1}. {curr_name}: {xgi90:.3f} xGI90 (from {hist_name})")
            
            if len(updates) > 5:
                print(f"   ... and {len(updates)-5} more")
        
        # Verify results
        print(f"\n7. Verification:")
        cursor.execute("""
            SELECT COUNT(*) as total_players,
                   COUNT(baseline_xgi) as with_baseline,
                   AVG(baseline_xgi) as avg_baseline,
                   AVG(xgi90) as avg_current
            FROM players
            WHERE baseline_xgi > 0 OR xgi90 > 0
        """)
        stats = cursor.fetchone()
        
        print(f"   Total players: {stats[0]}")
        print(f"   With baseline xGI: {stats[1]}")
        print(f"   Average baseline xGI: {stats[2]:.3f}")
        print(f"   Average current xGI: {stats[3]:.3f}")
        
        # Show unmatched players for manual review
        if unmatched_players:
            print(f"\n8. Unmatched players (top 10):")
            for i, player in enumerate(unmatched_players[:10]):
                print(f"   {i+1}. {player['historical_name']} ({player['historical_team']}) - {player['xGI90']:.3f}")
        
        cursor.close()
        conn.close()
        
        print(f"\nSUCCESS: Baseline xGI extraction completed successfully!")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Error during baseline xGI extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = extract_historical_xgi_baseline()
    if success:
        print("\nREADY: Sprint 2 normalized xGI calculation can now use proper historical baselines!")
    else:
        print("\nWARNING: Manual intervention may be required")