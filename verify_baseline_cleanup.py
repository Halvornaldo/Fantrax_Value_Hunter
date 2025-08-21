#!/usr/bin/env python3
"""
Verify Baseline Cleanup Plan
Show exactly which players will keep/lose baseline data before making changes
"""

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter', 
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def show_cleanup_plan():
    """Show exactly which players will be affected by baseline cleanup"""
    
    print("BASELINE CLEANUP VERIFICATION")
    print("=" * 60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Players who will KEEP baseline data (have PL history)
    cursor.execute("""
        SELECT DISTINCT
            p.name,
            p.position,
            p.team,
            p.baseline_xgi,
            pgd.games_played_historical as prem_games_24_25
        FROM players p
        JOIN player_games_data pgd ON p.id = pgd.player_id
        WHERE p.baseline_xgi > 0 
          AND pgd.games_played_historical > 0
        ORDER BY p.team, p.name
    """)
    
    keep_baseline = cursor.fetchall()
    
    # Players who will LOSE baseline data (no PL history)
    cursor.execute("""
        SELECT DISTINCT
            p.name,
            p.position,
            p.team,
            p.baseline_xgi,
            COALESCE(pgd.games_played_historical, 0) as prem_games_24_25
        FROM players p
        LEFT JOIN player_games_data pgd ON p.id = pgd.player_id
        WHERE p.baseline_xgi > 0 
          AND (pgd.games_played_historical = 0 OR pgd.games_played_historical IS NULL)
        ORDER BY p.team, p.name
    """)
    
    lose_baseline = cursor.fetchall()
    
    print(f"[SUMMARY] Baseline Cleanup Plan:")
    print(f"  Players keeping baseline data: {len(keep_baseline)}")
    print(f"  Players losing baseline data: {len(lose_baseline)}")
    print(f"  Total affected: {len(keep_baseline) + len(lose_baseline)}")
    
    # Show players keeping baseline by team
    print(f"\n[KEEPING BASELINE] {len(keep_baseline)} players with valid PL 24/25 history:")
    print("  (These played Premier League 2024/25 season)")
    
    current_team = None
    for player in keep_baseline:
        if player['team'] != current_team:
            current_team = player['team']
            print(f"\n  {current_team}:")
        print(f"    {player['name']:<20} | {player['position']:2} | Games: {player['prem_games_24_25']:2} | xGI: {player['baseline_xgi']:.3f}")
    
    # Show players losing baseline by team  
    print(f"\n[LOSING BASELINE] {len(lose_baseline)} players without PL 24/25 history:")
    print("  (These will have baseline_xgi set to 0)")
    
    current_team = None
    for player in lose_baseline:
        if player['team'] != current_team:
            current_team = player['team']
            print(f"\n  {current_team}:")
        print(f"    {player['name']:<20} | {player['position']:2} | PL Games: {player['prem_games_24_25']:2} | xGI: {player['baseline_xgi']:.3f}")
    
    # Show teams with most players losing baseline (likely promoted teams)
    print(f"\n[TEAM ANALYSIS] Teams losing most baseline players:")
    team_losses = {}
    for player in lose_baseline:
        team = player['team']
        team_losses[team] = team_losses.get(team, 0) + 1
    
    for team, count in sorted(team_losses.items(), key=lambda x: x[1], reverse=True):
        print(f"  {team}: {count} players losing baseline")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print(f"[REVIEW REQUIRED] Please check the lists above:")
    print(f"1. Do the 'KEEPING BASELINE' players look correct?")
    print(f"   (Should be established PL players from 24/25)")
    print(f"2. Do the 'LOSING BASELINE' players look correct?") 
    print(f"   (Should be new signings, promoted team players)")
    print(f"3. Are there any obvious errors in either list?")
    print(f"\nIf everything looks correct, I'll proceed with the cleanup.")
    
    return {
        'keeping_baseline': len(keep_baseline),
        'losing_baseline': len(lose_baseline),
        'keep_list': keep_baseline,
        'lose_list': lose_baseline
    }

if __name__ == "__main__":
    results = show_cleanup_plan()