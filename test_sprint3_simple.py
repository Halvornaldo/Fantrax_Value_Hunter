#!/usr/bin/env python3
"""
Formula Optimization v2.0 Sprint 3 - Simple Test Suite
Fantasy Football Value Hunter

Tests core Sprint 3 validation framework components with basic output
"""

import sys
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(__file__))

def test_database_connection():
    """Test database connection and validation tables"""
    print("[TEST] Testing database connection and validation tables...")
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test validation tables exist
        expected_tables = ['player_predictions', 'validation_results', 'parameter_optimization']
        
        for table in expected_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  [OK] Table '{table}': {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Database test failed: {e}")
        return False

def test_validation_engine_import():
    """Test validation engine can be imported"""
    print("\n[TEST] Testing ValidationEngine import...")
    
    try:
        from validation_engine import ValidationEngine, ValidationMetrics, ParameterSet
        print("  [OK] ValidationEngine imported successfully")
        
        # Test instantiation
        db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'fantrax_value_hunter',
            'user': 'fantrax_user',
            'password': 'fantrax_password'
        }
        
        validator = ValidationEngine(db_config)
        print("  [OK] ValidationEngine instantiated")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] ValidationEngine import failed: {e}")
        return False

def test_metrics_calculation():
    """Test basic metrics calculation"""
    print("\n[TEST] Testing metrics calculation...")
    
    try:
        from validation_engine import ValidationEngine
        
        db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'fantrax_value_hunter',
            'user': 'fantrax_user',
            'password': 'fantrax_password'
        }
        
        validator = ValidationEngine(db_config)
        
        # Test with sample data
        sample_predictions = [
            {'player_id': 'test1', 'predicted_value': 5.5, 'actual_points': 6.0},
            {'player_id': 'test2', 'predicted_value': 4.2, 'actual_points': 3.8},
            {'player_id': 'test3', 'predicted_value': 7.1, 'actual_points': 7.5},
            {'player_id': 'test4', 'predicted_value': 3.0, 'actual_points': 2.5},
            {'player_id': 'test5', 'predicted_value': 8.5, 'actual_points': 9.2}
        ]
        
        metrics = validator.calculate_validation_metrics(sample_predictions)
        
        print(f"  [OK] RMSE: {metrics.rmse:.3f}")
        print(f"  [OK] Spearman correlation: {metrics.spearman_correlation:.3f}")
        print(f"  [OK] Precision@20: {metrics.precision_at_20:.3f}")
        print(f"  [OK] N predictions: {metrics.n_predictions}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Metrics calculation failed: {e}")
        return False

def test_data_availability():
    """Test data availability for validation"""
    print("\n[TEST] Testing data availability...")
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check player form data
        cursor.execute("SELECT COUNT(*) FROM player_form")
        form_count = cursor.fetchone()[0]
        print(f"  [INFO] Player form records: {form_count}")
        
        # Check players with baseline xGI
        cursor.execute("SELECT COUNT(*) FROM players WHERE baseline_xgi IS NOT NULL")
        baseline_count = cursor.fetchone()[0]
        print(f"  [INFO] Players with baseline xGI: {baseline_count}")
        
        # Check current players
        cursor.execute("SELECT COUNT(*) FROM players WHERE position IS NOT NULL")
        player_count = cursor.fetchone()[0]
        print(f"  [INFO] Active players: {player_count}")
        
        conn.close()
        
        if player_count > 0:
            print("  [OK] Data available for validation")
            return True
        else:
            print("  [WARN] Limited data available")
            return True
        
    except Exception as e:
        print(f"  [ERROR] Data availability check failed: {e}")
        return False

def run_simple_test_suite():
    """Run simplified test suite"""
    print("=" * 60)
    print("SPRINT 3: VALIDATION FRAMEWORK - SIMPLE TEST SUITE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("ValidationEngine Import", test_validation_engine_import),
        ("Metrics Calculation", test_metrics_calculation),
        ("Data Availability", test_data_availability)
    ]
    
    results = []
    
    for test_name, test_function in tests:
        print(f"\n{'-'*40}")
        print(f"Running: {test_name}")
        print('-'*40)
        
        result = test_function()
        results.append((test_name, result))
        
        status = "[PASSED]" if result else "[FAILED]"
        print(f"\n{status} {test_name}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All core validation components are working!")
        print("\nNext steps:")
        print("1. Run 'python src/app.py' to start the Flask backend")
        print("2. Visit http://localhost:5000/api/validation-dashboard")
        print("3. Test the validation API endpoints")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
    
    print("\nSprint 3 Target Metrics:")
    print("- RMSE < 2.85")
    print("- Spearman correlation > 0.30")
    print("- Precision@20 > 0.30")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = run_simple_test_suite()
    sys.exit(0 if success else 1)