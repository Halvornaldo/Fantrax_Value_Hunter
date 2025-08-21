#!/usr/bin/env python3
"""
Investigate Zero Baseline Players
Identify which players should have baseline data but don't
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

def check_zero_baselines():
    """Check if zero baseline players are legitimate (new signings) or problematic"""
    
    print("INVESTIGATING ZERO BASELINE PLAYERS")
    print("=" * 50)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get zero baseline players with their current stats
    cursor.execute("""
        SELECT 
            p.name,
            p.position,
            p.team,
            p.baseline_xgi,
            p.xgi90 as current_xgi,
            p.minutes
        FROM players p
        WHERE p.baseline_xgi = 0
          AND p.position IS NOT NULL
        ORDER BY p.xgi90 DESC NULLS LAST, p.minutes DESC NULLS LAST
    """)
    
    zero_players = cursor.fetchall()
    
    print(f"[DATA] Found {len(zero_players)} players with zero baseline")
    
    # Categorize by current performance (likely playing status)
    high_current_xgi = [p for p in zero_players if (p['current_xgi'] or 0) > 0.3]
    medium_current_xgi = [p for p in zero_players if 0.1 < (p['current_xgi'] or 0) <= 0.3] 
    low_current_xgi = [p for p in zero_players if 0 < (p['current_xgi'] or 0) <= 0.1]
    no_current_xgi = [p for p in zero_players if (p['current_xgi'] or 0) == 0]
    
    print(f"\n[CATEGORIES] Zero Baseline Player Analysis:")
    print(f"  High current xGI (>0.3): {len(high_current_xgi)} - LIKELY MISSING BASELINE")
    print(f"  Medium current xGI (0.1-0.3): {len(medium_current_xgi)} - POSSIBLY MISSING")
    print(f"  Low current xGI (<0.1): {len(low_current_xgi)} - LIKELY NEW/BENCH")
    print(f"  No current xGI: {len(no_current_xgi)} - LIKELY NEW SIGNINGS")
    
    # Show problematic cases (high current xGI but zero baseline)
    if high_current_xgi:
        print(f"\n[PROBLEMATIC] Players with high current xGI but zero baseline:")
        print(f"  (These should have had 24/25 data)")
        for i, player in enumerate(high_current_xgi[:10], 1):
            print(f"  {i:2}. {player['name']:<20} | {player['position']:2} | {player['team']:3} | Current: {player['current_xgi']:.3f}")
    
    # Show medium cases for review
    if medium_current_xgi:
        print(f"\n[REVIEW NEEDED] Players with medium current xGI:")
        for i, player in enumerate(medium_current_xgi[:10], 1):
            print(f"  {i:2}. {player['name']:<20} | {player['position']:2} | {player['team']:3} | Current: {player['current_xgi']:.3f}")
    
    # Sample of likely legitimate cases (new signings/bench players)
    print(f"\n[LIKELY OK] Sample of players with no/low current xGI (probably new signings):")
    legitimate_sample = (no_current_xgi + low_current_xgi)[:10]
    for i, player in enumerate(legitimate_sample, 1):
        current = player['current_xgi'] or 0
        print(f"  {i:2}. {player['name']:<20} | {player['position']:2} | {player['team']:3} | Current: {current:.3f}")
    
    conn.close()
    
    # Assessment
    problematic_count = len(high_current_xgi)
    questionable_count = len(medium_current_xgi)
    
    print(f"\n" + "=" * 50)
    print(f"[ASSESSMENT] Zero Baseline Issue Severity:")
    
    if problematic_count > 0:
        print(f"[HIGH PRIORITY] {problematic_count} players missing baseline data")
        print(f"  These players have high current xGI but zero baseline")
        print(f"  They likely played in 24/25 and should have baseline data")
    
    if questionable_count > 5:
        print(f"[MEDIUM PRIORITY] {questionable_count} players need review")
        print(f"  Medium current xGI - may be missing baseline data")
    
    total_legitimate = len(no_current_xgi) + len(low_current_xgi)
    print(f"[OK] {total_legitimate} players likely legitimate (new signings/bench)")
    
    # Impact on validation
    print(f"\n[VALIDATION IMPACT]:")
    print(f"  Current validation uses {366} players with baseline data")
    print(f"  Could potentially add {problematic_count + questionable_count} more players")
    print(f"  Would increase sample size by {((problematic_count + questionable_count) / 366) * 100:.1f}%")
    
    if problematic_count > 10:
        print(f"  RECOMMENDATION: Fix baseline import for high-priority players")
    else:
        print(f"  RECOMMENDATION: Current validation dataset is sufficient")
    
    return {
        'total_zero_baseline': len(zero_players),
        'high_priority_missing': problematic_count,
        'medium_priority_missing': questionable_count,
        'likely_legitimate': total_legitimate
    }

if __name__ == "__main__":
    results = check_zero_baselines()