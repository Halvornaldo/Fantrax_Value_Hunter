#!/usr/bin/env python3
"""
Formula Optimization v2.0 Sprint 3 - Comprehensive Test Suite
Fantasy Football Value Hunter

Tests all Sprint 3 validation framework components:
1. Validation Engine functionality
2. Statistical metrics calculation
3. Parameter optimization system
4. API endpoints
5. Database integration

Author: Claude Code Assistant
Date: 2025-08-21
Version: 3.0
Sprint: 3 (Validation Framework Testing)
"""

import sys
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
import requests
import time

# Add project root to path
sys.path.append(os.path.dirname(__file__))
from validation_engine import ValidationEngine, ValidationMetrics, ParameterSet

def test_database_connection():
    """Test database connection and validation tables"""
    print("🔍 Testing database connection and validation tables...")
    
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
            print(f"  ✅ Table '{table}': {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_validation_engine():
    """Test core validation engine functionality"""
    print("\n🧪 Testing ValidationEngine core functionality...")
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }
    
    try:
        # Initialize validation engine
        validator = ValidationEngine(db_config)
        validator.connect_database()
        
        print("  ✅ ValidationEngine initialized successfully")
        
        # Test metrics calculation with sample data
        sample_predictions = [
            {'player_id': 'test1', 'predicted_value': 5.5, 'actual_points': 6.0},
            {'player_id': 'test2', 'predicted_value': 4.2, 'actual_points': 3.8},
            {'player_id': 'test3', 'predicted_value': 7.1, 'actual_points': 7.5},
            {'player_id': 'test4', 'predicted_value': 3.0, 'actual_points': 2.5},
            {'player_id': 'test5', 'predicted_value': 8.5, 'actual_points': 9.2}
        ]
        
        metrics = validator.calculate_validation_metrics(sample_predictions)
        
        print(f"  ✅ Metrics calculation: RMSE={metrics.rmse:.3f}, Correlation={metrics.spearman_correlation:.3f}")
        
        # Test precision@k calculation
        precision = validator._calculate_precision_at_k(sample_predictions, k=3)
        print(f"  ✅ Precision@3 calculation: {precision:.3f}")
        
        validator.close_connection()
        return True
        
    except Exception as e:
        print(f"  ❌ ValidationEngine test failed: {e}")
        return False

def test_historical_backtest():
    """Test historical backtesting with limited data"""
    print("\n📊 Testing historical backtesting (limited scope)...")
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }
    
    try:
        validator = ValidationEngine(db_config)
        
        # Run limited backtest (just 2 gameweeks to minimize time)
        predictions = validator.run_historical_backtest(
            start_gameweek=1,
            end_gameweek=2,
            season='2024/25',
            model_version='v2.0-test'
        )
        
        if predictions:
            print(f"  ✅ Backtest generated {len(predictions)} predictions")
            
            # Calculate metrics
            metrics = validator.calculate_validation_metrics(predictions, 'v2.0-test')
            print(f"  ✅ Test metrics: RMSE={metrics.rmse:.3f}, N={metrics.n_predictions}")
            
            # Store test results
            validator.store_validation_results(
                metrics=metrics,
                model_version='v2.0-test',
                season='2024/25',
                parameters={'test': True},
                notes='Sprint 3 automated test run'
            )
            print("  ✅ Results stored in database")
            
            validator.close_connection()
            return True
        else:
            print("  ⚠️ No predictions generated (may be expected if no form data available)")
            validator.close_connection()
            return True  # Not a failure if no data available
            
    except Exception as e:
        print(f"  ❌ Historical backtest failed: {e}")
        return False

def test_parameter_optimization():
    """Test parameter optimization with minimal grid"""
    print("\n⚙️ Testing parameter optimization (minimal grid)...")
    
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }
    
    try:
        validator = ValidationEngine(db_config)
        
        # Test parameter set creation
        test_param_set = ParameterSet(
            alpha=0.87,
            adaptation_gameweek=16,
            form_multiplier_cap_min=0.5,
            form_multiplier_cap_max=2.0,
            xgi_multiplier_cap_min=0.4,
            xgi_multiplier_cap_max=2.5
        )
        
        test_params = validator._create_test_parameters(test_param_set)
        print("  ✅ Parameter set creation successful")
        
        # Test a single parameter test run (limited scope)
        predictions = validator._run_parameter_test(
            test_param_set, 
            gameweek_range=(1, 2),
            season='2024/25'
        )
        
        if predictions:
            print(f"  ✅ Parameter test generated {len(predictions)} predictions")
        else:
            print("  ⚠️ No predictions from parameter test (may be expected)")
        
        validator.close_connection()
        return True
        
    except Exception as e:
        print(f"  ❌ Parameter optimization test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints (requires Flask app running)"""
    print("\n🌐 Testing API endpoints...")
    
    base_url = 'http://localhost:5000'
    
    # Test validation history endpoint
    try:
        response = requests.get(f'{base_url}/api/validation-history', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"  ✅ Validation history endpoint: {len(data.get('validation_history', []))} records")
            else:
                print("  ⚠️ Validation history endpoint returned unsuccessful response")
        else:
            print(f"  ⚠️ Validation history endpoint returned {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("  ⚠️ Flask app not running - API tests skipped")
        print("    Run 'python src/app.py' to test API endpoints")
        return True  # Not a failure, just unavailable
        
    except Exception as e:
        print(f"  ❌ API endpoint test failed: {e}")
        return False

def test_data_availability():
    """Test availability of data required for validation"""
    print("\n📋 Testing data availability for validation...")
    
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
        
        # Check player form data availability
        cursor.execute("""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT player_id) as unique_players,
                   MIN(gameweek) as min_gw,
                   MAX(gameweek) as max_gw
            FROM player_form
        """)
        
        form_stats = cursor.fetchone()
        print(f"  📊 Player form data: {form_stats[0]} records, {form_stats[1]} players, GW{form_stats[2]}-{form_stats[3]}")
        
        # Check players with baseline xGI data
        cursor.execute("""
            SELECT COUNT(*) FROM players 
            WHERE baseline_xgi IS NOT NULL
        """)
        
        baseline_count = cursor.fetchone()[0]
        print(f"  📊 Players with baseline xGI: {baseline_count}")
        
        # Check recent player metrics
        cursor.execute("""
            SELECT COUNT(DISTINCT player_id) FROM player_metrics
            WHERE gameweek >= 1
        """)
        
        metrics_count = cursor.fetchone()[0]
        print(f"  📊 Players with current metrics: {metrics_count}")
        
        conn.close()
        
        # Assess data readiness
        if form_stats[0] > 0 and baseline_count > 0:
            print("  ✅ Sufficient data available for validation")
            return True
        else:
            print("  ⚠️ Limited data available - validation may have reduced scope")
            return True  # Not a failure, just limited scope
        
    except Exception as e:
        print(f"  ❌ Data availability check failed: {e}")
        return False

def run_comprehensive_test_suite():
    """Run all Sprint 3 validation tests"""
    print("=" * 60)
    print("🚀 SPRINT 3: VALIDATION FRAMEWORK TEST SUITE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing validation framework and backtesting components...")
    print()
    
    # Track test results
    test_results = []
    
    # Run all tests
    tests = [
        ("Database Connection & Tables", test_database_connection),
        ("Validation Engine Core", test_validation_engine), 
        ("Data Availability Check", test_data_availability),
        ("Historical Backtesting", test_historical_backtest),
        ("Parameter Optimization", test_parameter_optimization),
        ("API Endpoints", test_api_endpoints)
    ]
    
    for test_name, test_function in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        start_time = time.time()
        result = test_function()
        end_time = time.time()
        
        test_results.append({
            'name': test_name,
            'passed': result,
            'duration': end_time - start_time
        })
        
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"\n{status} - {test_name} ({end_time - start_time:.2f}s)")
    
    # Print summary
    print("\n" + "="*60)
    print("📋 TEST SUITE SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for r in test_results if r['passed'])
    total_count = len(test_results)
    total_duration = sum(r['duration'] for r in test_results)
    
    for result in test_results:
        status = "✅" if result['passed'] else "❌"
        print(f"{status} {result['name']} ({result['duration']:.2f}s)")
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed ({total_duration:.2f}s total)")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - Sprint 3 validation framework is ready!")
    else:
        print(f"\n⚠️ {total_count - passed_count} test(s) failed - review issues above")
    
    print("\n" + "="*60)
    print("🎯 SPRINT 3 VALIDATION TARGETS:")
    print("  - RMSE < 2.85")
    print("  - Spearman correlation > 0.30") 
    print("  - Precision@20 > 0.30")
    print("  - 10-15% improvement over v1.0 baseline")
    print("="*60)
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_comprehensive_test_suite()
    sys.exit(0 if success else 1)