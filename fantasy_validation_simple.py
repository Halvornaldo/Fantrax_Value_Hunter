#!/usr/bin/env python3
"""
Fantasy League Validation - Simple Version
Tests Formula v2.0 accuracy against actual GW1 performance
"""

import psycopg2
import psycopg2.extras
import math

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter', 
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def run_simple_validation():
    """Run basic validation test"""
    
    print("FANTASY LEAGUE VALIDATION - Formula v2.0")
    print("=" * 50)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get players with predictions and actual GW1 points
    cursor.execute("""
        SELECT 
            p.name,
            p.position,
            pm.true_value as predicted,
            pf.points as actual
        FROM players p
        JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = 1
        JOIN player_form pf ON p.id = pf.player_id AND pf.gameweek = 1
        WHERE p.baseline_xgi > 0
          AND pm.true_value IS NOT NULL
          AND pf.points IS NOT NULL
          AND pm.true_value > 0
        ORDER BY pm.true_value DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    print(f"[DATA] Found {len(results)} players for validation")
    
    if len(results) < 50:
        print("[ERROR] Need more data for validation")
        return
    
    # Extract data
    predicted = [float(r['predicted']) for r in results]
    actual = [float(r['actual']) for r in results]
    
    # Calculate RMSE
    squared_errors = [(p - a) ** 2 for p, a in zip(predicted, actual)]
    rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
    
    # Calculate MAE
    absolute_errors = [abs(p - a) for p, a in zip(predicted, actual)]
    mae = sum(absolute_errors) / len(absolute_errors)
    
    # Calculate basic correlation
    n = len(predicted)
    sum_pred = sum(predicted)
    sum_actual = sum(actual)
    sum_pred_sq = sum(p**2 for p in predicted)
    sum_actual_sq = sum(a**2 for a in actual)
    sum_pred_actual = sum(p*a for p, a in zip(predicted, actual))
    
    correlation_num = n * sum_pred_actual - sum_pred * sum_actual
    correlation_den = math.sqrt((n * sum_pred_sq - sum_pred**2) * (n * sum_actual_sq - sum_actual**2))
    correlation = correlation_num / correlation_den if correlation_den != 0 else 0
    
    print(f"\n[RESULTS] Core Metrics:")
    print(f"  RMSE: {rmse:.3f} (target: <2.85)")
    print(f"  MAE: {mae:.3f}")
    print(f"  Correlation: {correlation:.3f} (target: >0.30)")
    print(f"  Players: {n}")
    print(f"  Avg predicted: {sum_pred/n:.1f}")
    print(f"  Avg actual: {sum_actual/n:.1f}")
    
    # Show top 10 predictions vs actual
    print(f"\n[TOP 10] Our Predictions vs Actual GW1 Points:")
    for i in range(min(10, len(results))):
        r = results[i]
        print(f"  {i+1:2}. {r['name']:<20} | Predicted: {r['predicted']:5.1f} | Actual: {r['actual']:4.1f}")
    
    # Assessment for fantasy league
    print(f"\n" + "=" * 50)
    print(f"[ASSESSMENT] Formula Performance:")
    
    targets_met = 0
    
    if rmse < 2.85:
        print("[PASS] RMSE target met - Good accuracy")
        targets_met += 1
    else:
        print("[FAIL] RMSE too high - Poor accuracy")
    
    if correlation > 0.30:
        print("[PASS] Correlation target met - Good ranking")
        targets_met += 1
    else:
        print("[FAIL] Low correlation - Poor ranking")
    
    if targets_met >= 1:
        print(f"\n[RESULT] Formula shows promise for fantasy league")
        print(f"Targets met: {targets_met}/2")
    else:
        print(f"\n[RESULT] Formula needs improvement")
        print(f"Targets met: {targets_met}/2")
    
    return {
        'rmse': rmse,
        'mae': mae,
        'correlation': correlation,
        'n_players': n,
        'targets_met': targets_met
    }

if __name__ == "__main__":
    results = run_simple_validation()