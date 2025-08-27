"""
Test Suite for GameweekManager - Sprint 0 Testing Infrastructure
Fantasy Football Value Hunter

Comprehensive testing for GameweekManager functionality including
edge cases, anomaly detection, and data integrity validation.

Created: 2025-08-23 - Sprint 0 completion
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import psycopg2
from datetime import datetime

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gameweek_manager import GameweekManager

class TestGameweekManager(unittest.TestCase):
    """Test suite for GameweekManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Use test database configuration
        self.test_db_config = {
            'host': 'localhost',
            'port': 5433,
            'user': 'fantrax_user',
            'password': 'fantrax_password',
            'database': 'fantrax_value_hunter'  # Using production for now
        }
        self.manager = GameweekManager(self.test_db_config)
    
    def test_init_default_config(self):
        """Test GameweekManager initialization with default config."""
        manager = GameweekManager()
        self.assertEqual(manager.db_config['host'], 'localhost')
        self.assertEqual(manager.db_config['port'], 5433)
        self.assertEqual(manager.db_config['database'], 'fantrax_value_hunter')
    
    def test_init_custom_config(self):
        """Test GameweekManager initialization with custom config."""
        custom_config = {'host': 'test', 'port': 1234, 'database': 'test_db'}
        manager = GameweekManager(custom_config)
        self.assertEqual(manager.db_config, custom_config)
    
    @patch('psycopg2.connect')
    def test_get_current_gameweek_empty_database(self, mock_connect):
        """Test gameweek detection with empty database."""
        # Mock empty database response
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        manager = GameweekManager()
        result = manager.get_current_gameweek()
        self.assertEqual(result, 1)  # Should fallback to 1
    
    @patch('psycopg2.connect')
    def test_anomaly_detection_small_upload(self, mock_connect):
        """Test detection of anomalous small uploads like GW3."""
        # Mock database with GW3 anomaly (5 players) and GW2 normal (633 players)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # player_metrics data (first query)
            [(3, 5, datetime.now()), (2, 633, datetime.now()), (1, 647, datetime.now())],
            # raw_player_snapshots data (second query)
            [(1, 622)]
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        manager = GameweekManager()
        result = manager.get_current_gameweek()
        self.assertEqual(result, 2)  # Should ignore GW3 anomaly and return GW2
    
    @patch('psycopg2.connect')
    def test_normal_progression_detection(self, mock_connect):
        """Test normal gameweek progression detection."""
        # Mock normal progression: GW2 complete, GW1 complete
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # player_metrics data
            [(2, 633, datetime.now()), (1, 647, datetime.now())],
            # raw_player_snapshots data  
            [(1, 622)]
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        manager = GameweekManager()
        result = manager.get_current_gameweek()
        self.assertEqual(result, 2)  # Should return GW2
    
    def test_get_next_gameweek(self):
        """Test next gameweek calculation."""
        with patch.object(self.manager, 'get_current_gameweek', return_value=2):
            result = self.manager.get_next_gameweek()
            self.assertEqual(result, 3)
    
    def test_emergency_protection_gw1(self):
        """Test emergency protection blocks GW1 uploads."""
        result = self.manager.validate_gameweek_for_upload(1)
        self.assertFalse(result['valid'])
        self.assertEqual(result['action'], 'blocked')
        self.assertTrue(result['emergency_protection'])
    
    def test_future_gameweek_validation(self):
        """Test future gameweek uploads are allowed."""
        with patch.object(self.manager, 'get_current_gameweek', return_value=2):
            result = self.manager.validate_gameweek_for_upload(4)
            self.assertTrue(result['valid'])
            self.assertEqual(result['action'], 'safe')
    
    def test_historical_gameweek_blocked(self):
        """Test historical gameweek uploads are blocked."""
        with patch.object(self.manager, 'get_current_gameweek', return_value=3):
            result = self.manager.validate_gameweek_for_upload(1)
            self.assertFalse(result['valid'])
            self.assertEqual(result['action'], 'blocked')
    
    def test_force_override_historical(self):
        """Test force flag allows historical overwrites."""
        with patch.object(self.manager, 'get_current_gameweek', return_value=3):
            result = self.manager.validate_gameweek_for_upload(1, force=True)
            self.assertTrue(result['valid'])
            self.assertEqual(result['action'], 'forced_overwrite')
    
    @patch('psycopg2.connect')
    def test_backup_creation(self, mock_connect):
        """Test backup creation functionality."""
        # Mock database with data to backup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            [10],  # player_metrics count
            [8],   # raw_player_snapshots count
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        manager = GameweekManager()
        result = manager.create_backup_before_overwrite(2, 'test')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['gameweek'], 2)
        self.assertEqual(result['operation'], 'test')
        self.assertGreater(result['backup_count'], 0)
    
    def test_system_status_integration(self):
        """Test overall system status functionality."""
        with patch.object(self.manager, 'get_current_gameweek', return_value=2):
            with patch.object(self.manager, 'get_gameweek_status', return_value={
                'completeness': {'overall_score': 85}
            }):
                result = self.manager.get_system_status()
                
                self.assertEqual(result['current_gameweek'], 2)
                self.assertEqual(result['next_gameweek'], 3)
                self.assertEqual(result['system_health'], 'healthy')
                self.assertTrue(result['emergency_protection_active'])

class TestGameweekManagerIntegration(unittest.TestCase):
    """Integration tests using actual database."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.manager = GameweekManager()
    
    def test_real_database_connection(self):
        """Test connection to actual database."""
        try:
            conn = self.manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            conn.close()
            self.assertEqual(result[0], 1)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_current_gameweek_detection_integration(self):
        """Test gameweek detection against real data."""
        # This should return GW2 based on our audit findings
        current_gw = self.manager.get_current_gameweek()
        self.assertIsInstance(current_gw, int)
        self.assertGreaterEqual(current_gw, 1)
        self.assertLessEqual(current_gw, 38)  # Premier League max gameweeks
    
    def test_gw3_anomaly_detection_integration(self):
        """Test that real GW3 anomaly is detected correctly."""
        # Based on our audit: GW3 has only 5 records, should be ignored
        current_gw = self.manager.get_current_gameweek()
        
        # Verify it returns 2, not 3 (proving anomaly detection works)
        self.assertEqual(current_gw, 2, 
            "GameweekManager should detect GW3 as anomalous and return GW2")

def run_gameweek_tests():
    """Run all GameweekManager tests."""
    print("=== GAMEWEEK MANAGER TEST SUITE ===")
    print("Sprint 0 Testing Infrastructure")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGameweekManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGameweekManagerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\nERRORS:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'SUCCESS' if success else 'FAILED'}")
    
    return success

if __name__ == '__main__':
    success = run_gameweek_tests()
    sys.exit(0 if success else 1)