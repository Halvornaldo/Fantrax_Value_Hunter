#!/usr/bin/env python3
"""
Fantasy League Validation - Sprint 3
Tests Formula v2.0 accuracy against actual GW1 performance

Focus: Validate predictions that will help win the fantasy league
Data: 366 players with baseline xGI vs GW1 actual points
"""

import psycopg2
import psycopg2.extras
import json
import math
from typing import Dict, List, Tuple

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter', 
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def get_validation_data() -> List[Dict]:
    """Get players with baseline data for validation against GW1 actual points"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get players with baseline xGI data and GW1 actual performance
    cursor.execute("""
        SELECT 
            p.id,
            p.name,
            p.position,
            p.team,
            p.xgi90 as current_xgi,
            p.baseline_xgi,
            pm.price,
            pm.ppg,
            pm.true_value as predicted_value,
            pm.xgi_multiplier,
            pm.form_multiplier,
            pm.fixture_multiplier,
            pf.points as actual_points_gw1
        FROM players p
        JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = 1
        JOIN player_form pf ON p.id = pf.player_id AND pf.gameweek = 1
        WHERE p.baseline_xgi > 0
          AND pm.true_value IS NOT NULL
          AND pf.points IS NOT NULL
        ORDER BY pm.true_value DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    print(f"✅ Found {len(results)} players with baseline data for validation")
    return [dict(row) for row in results]

def calculate_basic_metrics(predictions: List[Dict]) -> Dict:
    """Calculate core validation metrics"""
    
    predicted_values = [p['predicted_value'] for p in predictions]
    actual_points = [p['actual_points_gw1'] for p in predictions]
    
    # Remove any None values
    valid_pairs = [(pred, actual) for pred, actual in zip(predicted_values, actual_points) 
                   if pred is not None and actual is not None]
    
    if len(valid_pairs) < 10:
        print("❌ Not enough valid data for metrics")
        return {}
    
    predicted_values = [p[0] for p in valid_pairs]
    actual_points = [p[1] for p in valid_pairs]
    
    # Calculate RMSE
    squared_errors = [(pred - actual) ** 2 for pred, actual in valid_pairs]
    rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
    
    # Calculate MAE  
    absolute_errors = [abs(pred - actual) for pred, actual in valid_pairs]
    mae = sum(absolute_errors) / len(absolute_errors)
    
    # Calculate correlation (simplified)
    n = len(predicted_values)
    sum_pred = sum(predicted_values)
    sum_actual = sum(actual_points)
    sum_pred_sq = sum(p**2 for p in predicted_values)
    sum_actual_sq = sum(a**2 for a in actual_points)
    sum_pred_actual = sum(p*a for p, a in valid_pairs)
    
    correlation_num = n * sum_pred_actual - sum_pred * sum_actual
    correlation_den = math.sqrt((n * sum_pred_sq - sum_pred**2) * (n * sum_actual_sq - sum_actual**2))
    
    correlation = correlation_num / correlation_den if correlation_den != 0 else 0
    
    return {
        'rmse': rmse,
        'mae': mae, 
        'correlation': correlation,
        'n_players': len(valid_pairs),
        'avg_predicted': sum(predicted_values) / len(predicted_values),
        'avg_actual': sum(actual_points) / len(actual_points)
    }

def calculate_precision_at_k(predictions: List[Dict], k: int = 20) -> float:
    """Calculate Precision@K for top player predictions"""
    
    # Sort by predicted value (descending)
    sorted_by_predicted = sorted(predictions, key=lambda x: x['predicted_value'] or 0, reverse=True)
    top_k_predicted = sorted_by_predicted[:k]
    
    # Sort by actual points (descending)
    sorted_by_actual = sorted(predictions, key=lambda x: x['actual_points_gw1'] or 0, reverse=True)
    top_k_actual_ids = {p['id'] for p in sorted_by_actual[:k]}
    
    # Count how many predicted top-K are in actual top-K
    correct_predictions = sum(1 for p in top_k_predicted if p['id'] in top_k_actual_ids)
    
    return correct_predictions / k

def analyze_xgi_component(predictions: List[Dict]) -> Dict:
    """Analyze how well the xGI component predicts performance"""
    
    # Filter players with xGI data
    xgi_players = [p for p in predictions if p['current_xgi'] and p['baseline_xgi'] and p['xgi_multiplier']]
    
    if len(xgi_players) < 50:
        return {'error': 'Not enough xGI data'}
    
    # Calculate xGI ratio (current vs baseline)
    for player in xgi_players:
        player['xgi_ratio'] = float(player['current_xgi']) / float(player['baseline_xgi'])
    
    # Test correlation between xGI ratio and actual points
    xgi_ratios = [p['xgi_ratio'] for p in xgi_players]
    actual_points = [float(p['actual_points_gw1']) for p in xgi_players]
    
    # Simple correlation
    n = len(xgi_ratios)
    sum_xgi = sum(xgi_ratios)
    sum_points = sum(actual_points)
    sum_xgi_sq = sum(x**2 for x in xgi_ratios)
    sum_points_sq = sum(p**2 for p in actual_points)
    sum_xgi_points = sum(x*p for x, p in zip(xgi_ratios, actual_points))
    
    correlation_num = n * sum_xgi_points - sum_xgi * sum_points
    correlation_den = math.sqrt((n * sum_xgi_sq - sum_xgi**2) * (n * sum_points_sq - sum_points**2))
    
    xgi_correlation = correlation_num / correlation_den if correlation_den != 0 else 0
    
    return {
        'xgi_correlation': xgi_correlation,
        'n_players': n,
        'avg_xgi_ratio': sum(xgi_ratios) / n,
        'players_above_baseline': sum(1 for r in xgi_ratios if r > 1.0),
        'players_below_baseline': sum(1 for r in xgi_ratios if r < 1.0)
    }

def find_top_predictions_vs_actual(predictions: List[Dict], top_n: int = 20) -> Dict:
    """Compare our top predictions vs actual top performers"""
    
    # Our top predictions
    top_predicted = sorted(predictions, key=lambda x: x['predicted_value'] or 0, reverse=True)[:top_n]
    
    # Actual top performers
    top_actual = sorted(predictions, key=lambda x: x['actual_points_gw1'] or 0, reverse=True)[:top_n]
    
    return {
        'predicted_top': [{'name': p['name'], 'predicted': p['predicted_value'], 'actual': p['actual_points_gw1']} 
                         for p in top_predicted[:10]],
        'actual_top': [{'name': p['name'], 'predicted': p['predicted_value'], 'actual': p['actual_points_gw1']} 
                      for p in top_actual[:10]],
        'overlap': len(set(p['id'] for p in top_predicted) & set(p['id'] for p in top_actual))
    }

def run_fantasy_validation():
    """Run comprehensive validation for fantasy league success"""
    
    print("🏆 FANTASY LEAGUE VALIDATION - Formula v2.0")
    print("=" * 50)
    
    # Get validation data
    print("\n📊 Loading validation data...")
    predictions = get_validation_data()
    
    if len(predictions) < 100:
        print("❌ Insufficient data for meaningful validation")
        return
    
    # Calculate core metrics
    print("\n📈 Calculating core metrics...")
    metrics = calculate_basic_metrics(predictions)
    
    if metrics:
        print(f"  RMSE: {metrics['rmse']:.3f} (target: <2.85)")
        print(f"  MAE: {metrics['mae']:.3f}")  
        print(f"  Correlation: {metrics['correlation']:.3f} (target: >0.30)")
        print(f"  Players tested: {metrics['n_players']}")
        print(f"  Avg predicted: {metrics['avg_predicted']:.1f} points")
        print(f"  Avg actual: {metrics['avg_actual']:.1f} points")
    
    # Calculate Precision@20
    print("\n🎯 Testing top player prediction accuracy...")
    precision_20 = calculate_precision_at_k(predictions, 20)
    precision_50 = calculate_precision_at_k(predictions, 50)
    
    print(f"  Precision@20: {precision_20:.3f} (target: >0.30)")
    print(f"  Precision@50: {precision_50:.3f}")
    
    # Analyze xGI component
    print("\n⚽ Analyzing xGI prediction component...")
    xgi_analysis = analyze_xgi_component(predictions)
    
    if 'error' not in xgi_analysis:
        print(f"  xGI correlation: {xgi_analysis['xgi_correlation']:.3f}")
        print(f"  Players tested: {xgi_analysis['n_players']}")
        print(f"  Above baseline: {xgi_analysis['players_above_baseline']}")
        print(f"  Below baseline: {xgi_analysis['players_below_baseline']}")
    
    # Compare top predictions vs actual
    print("\n🏅 Top Predictions vs Actual Performance:")
    top_comparison = find_top_predictions_vs_actual(predictions)
    
    print(f"\n  Our Top 10 Predictions:")
    for i, player in enumerate(top_comparison['predicted_top'], 1):
        print(f"    {i:2}. {player['name']:20} | Predicted: {player['predicted']:5.1f} | Actual: {player['actual']:4.1f}")
    
    print(f"\n  Actual Top 10 Performers:")
    for i, player in enumerate(top_comparison['actual_top'], 1):
        print(f"    {i:2}. {player['name']:20} | Predicted: {player['predicted']:5.1f} | Actual: {player['actual']:4.1f}")
    
    print(f"\n  Overlap in top 20: {top_comparison['overlap']}/20 players")
    
    # Fantasy league assessment
    print("\n" + "=" * 50)
    print("🏆 FANTASY LEAGUE ASSESSMENT:")
    
    target_met = 0
    if metrics.get('rmse', 999) < 2.85:
        print("✅ RMSE target met - Good prediction accuracy")
        target_met += 1
    else:
        print("❌ RMSE too high - Predictions not accurate enough")
        
    if metrics.get('correlation', 0) > 0.30:
        print("✅ Correlation target met - Predictions follow actual performance")  
        target_met += 1
    else:
        print("❌ Low correlation - Predictions don't match actual rankings")
        
    if precision_20 > 0.30:
        print("✅ Precision@20 target met - Good at identifying top players")
        target_met += 1
    else:
        print("❌ Poor precision - Missing too many top performers")
    
    print(f"\nFormula readiness: {target_met}/3 targets met")
    
    if target_met >= 2:
        print("🎉 Formula ready for competitive fantasy league use!")
    else:
        print("⚠️  Formula needs improvement before league deployment")
    
    return {
        'metrics': metrics,
        'precision_20': precision_20,
        'xgi_analysis': xgi_analysis,
        'top_comparison': top_comparison,
        'targets_met': target_met
    }

if __name__ == "__main__":
    results = run_fantasy_validation()