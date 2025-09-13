#!/usr/bin/env python3
"""
Verify Baseline xGI Import Accuracy
Checks that imported 2024/25 baseline xGI data matches expected players
"""

import psycopg2
import psycopg2.extras

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter', 
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def verify_baseline_import():
    """Verify baseline xGI import accuracy"""
    
    print("BASELINE xGI IMPORT VERIFICATION")
    print("=" * 50)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get all players and their baseline status
    cursor.execute("""
        SELECT 
            COUNT(*) as total_players,
            COUNT(*) FILTER (WHERE baseline_xgi IS NOT NULL) as players_with_baseline,
            COUNT(*) FILTER (WHERE baseline_xgi > 0) as players_with_positive_baseline,
            COUNT(*) FILTER (WHERE baseline_xgi = 0) as players_with_zero_baseline,
            AVG(baseline_xgi) FILTER (WHERE baseline_xgi > 0) as avg_baseline_xgi
        FROM players
    """)
    
    summary = cursor.fetchone()
    
    print(f"[SUMMARY] Baseline Import Status:")
    print(f"  Total players in database: {summary['total_players']}")
    print(f"  Players with baseline data: {summary['players_with_baseline']}")
    print(f"  Players with positive baseline: {summary['players_with_positive_baseline']}")
    print(f"  Players with zero baseline: {summary['players_with_zero_baseline']}")
    print(f"  Average baseline xGI: {summary['avg_baseline_xgi']:.3f}")
    
    # Check which players are missing baseline data
    cursor.execute("""
        SELECT 
            p.name,
            p.position,
            p.team,
            p.xgi90 as current_xgi,
            p.baseline_xgi,
            CASE 
                WHEN p.baseline_xgi IS NULL THEN 'NO_BASELINE'
                WHEN p.baseline_xgi = 0 THEN 'ZERO_BASELINE' 
                WHEN p.baseline_xgi > 0 THEN 'HAS_BASELINE'
            END as baseline_status
        FROM players p
        WHERE p.position IS NOT NULL
        ORDER BY p.baseline_xgi DESC NULLS LAST, p.name
    """)
    
    players = cursor.fetchall()
    
    # Categorize players
    no_baseline = [p for p in players if p['baseline_status'] == 'NO_BASELINE']
    zero_baseline = [p for p in players if p['baseline_status'] == 'ZERO_BASELINE'] 
    has_baseline = [p for p in players if p['baseline_status'] == 'HAS_BASELINE']
    
    print(f"\n[BREAKDOWN] Player Categories:")
    print(f"  Players with baseline data: {len(has_baseline)}")
    print(f"  Players with zero baseline: {len(zero_baseline)}")
    print(f"  Players missing baseline: {len(no_baseline)}")
    
    # Show players with highest baseline xGI (should be realistic values)
    print(f"\n[TOP 10] Highest Baseline xGI (24/25 season):")
    top_baseline = sorted(has_baseline, key=lambda x: x['baseline_xgi'] or 0, reverse=True)[:10]
    
    for i, player in enumerate(top_baseline, 1):
        print(f"  {i:2}. {player['name']:<20} | {player['position']:2} | {player['team']:3} | Baseline: {player['baseline_xgi']:.3f}")
    
    # Show players missing baseline (these should mostly be new signings)
    print(f"\n[MISSING] Players Without Baseline Data (should be new signings):")
    if no_baseline:
        for i, player in enumerate(no_baseline[:15], 1):  # Show first 15
            current = player['current_xgi'] or 0
            print(f"  {i:2}. {player['name']:<20} | {player['position']:2} | {player['team']:3} | Current: {current:.3f}")
        if len(no_baseline) > 15:
            print(f"  ... and {len(no_baseline) - 15} more players")
    else:
        print("  (None - all players have baseline data)")
    
    # Show players with zero baseline (suspicious - should investigate)
    print(f"\n[ZERO BASELINE] Players With Zero Baseline (needs investigation):")
    if zero_baseline:
        for i, player in enumerate(zero_baseline[:10], 1):  # Show first 10
            current = player['current_xgi'] or 0
            print(f"  {i:2}. {player['name']:<20} | {player['position']:2} | {player['team']:3} | Current: {current:.3f}")
        if len(zero_baseline) > 10:
            print(f"  ... and {len(zero_baseline) - 10} more players")
    else:
        print("  (None - good, no suspicious zero baselines)")
    
    # Sanity checks
    print(f"\n[SANITY CHECKS] Data Quality Assessment:")
    
    # Check 1: Reasonable baseline xGI ranges
    very_high_baseline = [p for p in has_baseline if p['baseline_xgi'] > 1.0]  # Very high xGI per 90
    very_low_baseline = [p for p in has_baseline if p['baseline_xgi'] < 0.05]  # Very low but not zero
    
    print(f"  Players with very high baseline (>1.0): {len(very_high_baseline)}")
    print(f"  Players with very low baseline (<0.05): {len(very_low_baseline)}")
    
    # Check 2: Position distribution 
    position_breakdown = {}
    for player in has_baseline:
        pos = player['position'] or 'Unknown'
        position_breakdown[pos] = position_breakdown.get(pos, 0) + 1
    
    print(f"  Position distribution with baseline:")
    for pos, count in sorted(position_breakdown.items()):
        print(f"    {pos}: {count} players")
    
    # Check 3: Team distribution (should have players from all 20 teams)
    team_breakdown = {}
    for player in has_baseline:
        team = player['team'] or 'Unknown'
        team_breakdown[team] = team_breakdown.get(team, 0) + 1
    
    teams_with_baseline = len([t for t in team_breakdown.keys() if t != 'Unknown'])
    print(f"  Teams represented in baseline: {teams_with_baseline}/20")
    
    conn.close()
    
    # Assessment
    print(f"\n" + "=" * 50)
    print(f"[ASSESSMENT] Baseline Import Quality:")
    
    issues_found = 0
    
    if len(has_baseline) < 300:
        print(f"[WARNING] Only {len(has_baseline)} players with baseline - expected ~400+")
        issues_found += 1
    else:
        print(f"[OK] {len(has_baseline)} players with baseline data")
    
    if len(zero_baseline) > 50:
        print(f"[WARNING] {len(zero_baseline)} players with zero baseline - investigate")
        issues_found += 1
    else:
        print(f"[OK] Only {len(zero_baseline)} players with zero baseline")
    
    if teams_with_baseline < 15:
        print(f"[WARNING] Only {teams_with_baseline} teams represented - missing data")
        issues_found += 1
    else:
        print(f"[OK] {teams_with_baseline} teams represented")
    
    if summary['avg_baseline_xgi'] < 0.1 or summary['avg_baseline_xgi'] > 0.8:
        print(f"[WARNING] Average baseline {summary['avg_baseline_xgi']:.3f} seems unrealistic")
        issues_found += 1
    else:
        print(f"[OK] Average baseline {summary['avg_baseline_xgi']:.3f} looks reasonable")
    
    if issues_found == 0:
        print(f"\n[RESULT] Baseline import appears correct - ready for validation")
    else:
        print(f"\n[RESULT] {issues_found} potential issues found - review recommended")
    
    return {
        'total_players': summary['total_players'],
        'players_with_baseline': len(has_baseline),
        'players_missing_baseline': len(no_baseline),
        'players_zero_baseline': len(zero_baseline),
        'avg_baseline': summary['avg_baseline_xgi'],
        'teams_represented': teams_with_baseline,
        'issues_found': issues_found
    }

if __name__ == "__main__":
    results = verify_baseline_import()