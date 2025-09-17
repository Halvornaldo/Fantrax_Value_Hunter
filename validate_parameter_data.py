#!/usr/bin/env python3
"""
Parameter Data Validation Script
Check if all required data exists for parameter adjustments to work properly
"""

import psycopg2
import psycopg2.extras
import json

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def validate_data():
    """Check current state of all parameter-dependent data"""

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("🔍 PARAMETER DATA VALIDATION")
    print("=" * 50)

    # 1. Check form data (for form multiplier)
    cursor.execute("SELECT COUNT(*) as count FROM player_form WHERE points > 0")
    form_data = cursor.fetchone()['count']
    print(f"📊 Form Data: {form_data} players with points > 0")

    if form_data > 0:
        cursor.execute("SELECT AVG(points) as avg_points, MAX(points) as max_points FROM player_form WHERE points > 0")
        form_stats = cursor.fetchone()
        print(f"   └─ Average points: {form_stats['avg_points']:.1f}, Max: {form_stats['max_points']:.1f}")

    # 2. Check fixture data (for fixture multiplier)
    cursor.execute("SELECT COUNT(*) as count FROM team_fixtures WHERE difficulty_score IS NOT NULL")
    fixture_data = cursor.fetchone()['count']
    print(f"🏟️  Fixture Data: {fixture_data} teams with difficulty scores")

    if fixture_data > 0:
        cursor.execute("SELECT MIN(difficulty_score) as min_diff, MAX(difficulty_score) as max_diff FROM team_fixtures WHERE difficulty_score IS NOT NULL")
        fixture_stats = cursor.fetchone()
        print(f"   └─ Difficulty range: {fixture_stats['min_diff']:.2f} to {fixture_stats['max_diff']:.2f}")

    # 3. Check xGI data (for xGI multiplier)
    cursor.execute("SELECT COUNT(*) as count FROM players WHERE xgi90 > 0")
    xgi_data = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as total FROM players")
    total_players = cursor.fetchone()['count']
    print(f"⚽ xGI Data: {xgi_data}/{total_players} players with xGI > 0 ({xgi_data/total_players*100:.1f}%)")

    if xgi_data > 0:
        cursor.execute("SELECT AVG(xgi90) as avg_xgi, MAX(xgi90) as max_xgi FROM players WHERE xgi90 > 0")
        xgi_stats = cursor.fetchone()
        print(f"   └─ Average xGI90: {xgi_stats['avg_xgi']:.2f}, Max: {xgi_stats['max_xgi']:.2f}")

    # 4. Check starter prediction data (for starter multiplier)
    cursor.execute("SELECT COUNT(*) as count FROM player_metrics WHERE starter_multiplier != 1.0")
    starter_overrides = cursor.fetchone()['count']
    print(f"👤 Starter Overrides: {starter_overrides} players with non-default multipliers")

    if starter_overrides > 0:
        cursor.execute("""
            SELECT starter_multiplier, COUNT(*) as count
            FROM player_metrics
            WHERE starter_multiplier != 1.0
            GROUP BY starter_multiplier
            ORDER BY starter_multiplier DESC
        """)
        multiplier_breakdown = cursor.fetchall()
        print("   └─ Multiplier breakdown:")
        for row in multiplier_breakdown:
            print(f"      • {row['starter_multiplier']}x: {row['count']} players")

    # 5. Check manual overrides in config
    try:
        with open('config/system_parameters.json', 'r') as f:
            params = json.load(f)

        manual_overrides = params.get('starter_prediction', {}).get('manual_overrides', {})
        print(f"🔧 Manual Overrides: {len(manual_overrides)} in config file")

        if manual_overrides:
            for player_id, override in manual_overrides.items():
                print(f"   └─ Player {player_id}: {override['type']} ({override['multiplier']}x)")

    except Exception as e:
        print(f"❌ Error reading config: {e}")

    # 6. Check current parameter states
    try:
        formula_config = params.get('formula_optimization_v2', {}).get('formula_toggles', {})
        print(f"\n⚙️  Current Parameter States:")
        print(f"   • Form: {'✅ ON' if formula_config.get('form_enabled', False) else '❌ OFF'}")
        print(f"   • Fixture: {'✅ ON' if formula_config.get('fixture_enabled', True) else '❌ OFF'}")
        print(f"   • Starter: {'✅ ON' if formula_config.get('starter_enabled', True) else '❌ OFF'}")
        print(f"   • xGI: {'✅ ON' if formula_config.get('xgi_enabled', False) else '❌ OFF'}")

    except Exception as e:
        print(f"❌ Error reading parameter states: {e}")

    # 7. Sample a few players to check actual multiplier values
    print(f"\n🎯 Sample Player Multipliers:")
    cursor.execute("""
        SELECT p.name, p.position, p.team,
               pm.form_multiplier, pm.fixture_multiplier,
               pm.starter_multiplier, pm.xgi_multiplier,
               pm.true_value, pm.price
        FROM players p
        JOIN player_metrics pm ON p.id = pm.player_id
        WHERE pm.true_value > 0
        ORDER BY pm.true_value DESC
        LIMIT 5
    """)

    sample_players = cursor.fetchall()
    for player in sample_players:
        print(f"   • {player['name']} ({player['position']}, {player['team']})")
        print(f"     Form: {player['form_multiplier']:.2f}x | Fixture: {player['fixture_multiplier']:.2f}x | Starter: {player['starter_multiplier']:.2f}x | xGI: {player['xgi_multiplier']:.2f}x")
        print(f"     True Value: {player['true_value']:.1f} | Price: £{player['price']:.1f}")

    conn.close()

    print("\n✅ Data validation complete!")

if __name__ == "__main__":
    validate_data()