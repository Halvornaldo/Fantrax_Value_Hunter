"""
Data Integrity Validation Scripts - Sprint 0 Completion
Fantasy Football Value Hunter

Comprehensive validation scripts to ensure data integrity throughout
the Gameweek Unification implementation process.

Created: 2025-08-23 - Sprint 0 final deliverable
"""

import psycopg2
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

class GameweekIntegrityValidator:
    """Validates gameweek data integrity across all database tables."""
    
    def __init__(self):
        """Initialize validator with database connection."""
        self.db_config = {
            'host': 'localhost',
            'port': 5433,
            'user': 'fantrax_user',
            'password': 'fantrax_password',
            'database': 'fantrax_value_hunter'
        }
    
    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)
    
    def validate_gameweek_distribution(self) -> Dict[str, Any]:
        """Validate gameweek data distribution across all tables."""
        print("=== GAMEWEEK DATA DISTRIBUTION VALIDATION ===")
        
        results = {}
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check player_metrics distribution
            cursor.execute("""
                SELECT gameweek, COUNT(*) as count, 
                       MIN(last_updated) as earliest,
                       MAX(last_updated) as latest
                FROM player_metrics 
                GROUP BY gameweek 
                ORDER BY gameweek
            """)
            player_metrics = cursor.fetchall()
            results['player_metrics'] = player_metrics
            
            print("player_metrics gameweek distribution:")
            for gw, count, earliest, latest in player_metrics:
                print(f"  GW{gw}: {count} records ({earliest} to {latest})")
            
            # Check raw_player_snapshots distribution
            cursor.execute("""
                SELECT gameweek, COUNT(*) as count
                FROM raw_player_snapshots 
                GROUP BY gameweek 
                ORDER BY gameweek
            """)
            raw_snapshots = cursor.fetchall()
            results['raw_player_snapshots'] = raw_snapshots
            
            print("\nraw_player_snapshots gameweek distribution:")
            for gw, count in raw_snapshots:
                print(f"  GW{gw}: {count} records")
            
            # Check for anomalies
            anomalies = []
            total_players = 647  # Expected Premier League players
            
            for gw, count, earliest, latest in player_metrics:
                completion_rate = (count / total_players) * 100
                if completion_rate < 5 and count > 0:  # Small uploads
                    anomalies.append({
                        'type': 'small_upload',
                        'gameweek': gw,
                        'count': count,
                        'completion_rate': completion_rate,
                        'latest_update': latest
                    })
                elif completion_rate > 105:  # Duplicate data
                    anomalies.append({
                        'type': 'duplicate_data',
                        'gameweek': gw,
                        'count': count,
                        'completion_rate': completion_rate
                    })
            
            results['anomalies'] = anomalies
            
            if anomalies:
                print("\n🚨 ANOMALIES DETECTED:")
                for anomaly in anomalies:
                    print(f"  GW{anomaly['gameweek']}: {anomaly['type']} - "
                          f"{anomaly['count']} records ({anomaly['completion_rate']:.1f}%)")
            else:
                print("\n✅ No anomalies detected")
            
            conn.close()
            
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return results
    
    def validate_gameweek_consistency(self) -> Dict[str, Any]:
        """Validate consistency between different tables."""
        print("\n=== GAMEWEEK CONSISTENCY VALIDATION ===")
        
        results = {}
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get max gameweeks from each table
            cursor.execute('SELECT MAX(gameweek) FROM player_metrics WHERE gameweek IS NOT NULL')
            max_metrics = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT MAX(gameweek) FROM raw_player_snapshots WHERE gameweek IS NOT NULL')
            max_raw = cursor.fetchone()[0] or 0
            
            results['max_gameweeks'] = {
                'player_metrics': max_metrics,
                'raw_player_snapshots': max_raw
            }
            
            print(f"Maximum gameweeks:")
            print(f"  player_metrics: GW{max_metrics}")
            print(f"  raw_player_snapshots: GW{max_raw}")
            
            # Check consistency
            inconsistency = abs(max_metrics - max_raw)
            results['inconsistency_gap'] = inconsistency
            
            if inconsistency > 1:
                print(f"🚨 INCONSISTENCY: {inconsistency} gameweek gap between tables")
                results['consistent'] = False
            else:
                print("✅ Tables are reasonably consistent")
                results['consistent'] = True
            
            conn.close()
            
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return results
    
    def validate_data_completeness(self) -> Dict[str, Any]:
        """Validate data completeness for each gameweek."""
        print("\n=== DATA COMPLETENESS VALIDATION ===")
        
        results = {}
        expected_players = 647
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check completeness for each gameweek in player_metrics
            cursor.execute("""
                SELECT gameweek, COUNT(*) as count,
                       COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_price,
                       COUNT(CASE WHEN true_value IS NOT NULL THEN 1 END) as with_true_value
                FROM player_metrics 
                GROUP BY gameweek 
                ORDER BY gameweek
            """)
            completeness_data = cursor.fetchall()
            
            results['completeness'] = []
            
            print("Data completeness by gameweek:")
            for gw, total, with_price, with_true_value in completeness_data:
                completion_rate = (total / expected_players) * 100
                price_rate = (with_price / total) * 100 if total > 0 else 0
                value_rate = (with_true_value / total) * 100 if total > 0 else 0
                
                completeness_info = {
                    'gameweek': gw,
                    'total_players': total,
                    'completion_rate': completion_rate,
                    'price_completion': price_rate,
                    'value_completion': value_rate
                }
                results['completeness'].append(completeness_info)
                
                print(f"  GW{gw}: {total}/{expected_players} players ({completion_rate:.1f}%) "
                      f"| Price: {price_rate:.0f}% | Value: {value_rate:.0f}%")
            
            conn.close()
            
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return results
    
    def validate_backup_integrity(self) -> Dict[str, Any]:
        """Validate that backups were created successfully."""
        print("\n=== BACKUP INTEGRITY VALIDATION ===")
        
        results = {}
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check for backup tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%backup%'
                ORDER BY table_name
            """)
            backup_tables = [row[0] for row in cursor.fetchall()]
            results['backup_tables'] = backup_tables
            
            print(f"Found {len(backup_tables)} backup tables:")
            for table in backup_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
            
            # Specifically check for GW1 backups
            gw1_backups = [t for t in backup_tables if 'gw1' in t.lower()]
            results['gw1_backups'] = gw1_backups
            
            if gw1_backups:
                print(f"\n✅ GW1 emergency backups found: {len(gw1_backups)} tables")
            else:
                print("\n⚠️  No GW1 emergency backups found")
            
            conn.close()
            
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ ERROR: {e}")
        
        return results
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        print("=== GAMEWEEK INTEGRITY VALIDATION SUITE ===")
        print(f"Timestamp: {datetime.now()}")
        print("Sprint 0 - Data Integrity Validation")
        print()
        
        full_results = {}
        
        # Run all validations
        full_results['distribution'] = self.validate_gameweek_distribution()
        full_results['consistency'] = self.validate_gameweek_consistency()
        full_results['completeness'] = self.validate_data_completeness()
        full_results['backups'] = self.validate_backup_integrity()
        
        # Overall assessment
        print("\n=== OVERALL ASSESSMENT ===")
        
        issues = []
        
        # Check for critical issues
        if 'anomalies' in full_results['distribution'] and full_results['distribution']['anomalies']:
            issues.append(f"{len(full_results['distribution']['anomalies'])} gameweek anomalies detected")
        
        if not full_results['consistency'].get('consistent', True):
            issues.append("Gameweek inconsistency between tables")
        
        if not full_results['backups'].get('gw1_backups'):
            issues.append("Missing GW1 emergency backups")
        
        if issues:
            print("🚨 ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ All validations passed")
        
        full_results['overall_status'] = 'PASSED' if not issues else 'ISSUES_FOUND'
        full_results['issues'] = issues
        full_results['timestamp'] = datetime.now().isoformat()
        
        return full_results

def main():
    """Main validation script entry point."""
    validator = GameweekIntegrityValidator()
    
    try:
        results = validator.run_full_validation()
        
        print(f"\n=== VALIDATION COMPLETE ===")
        print(f"Status: {results['overall_status']}")
        
        if results['overall_status'] == 'PASSED':
            print("✅ System ready for Sprint 1 implementation")
            return 0
        else:
            print("⚠️  Issues detected - review before proceeding")
            return 1
            
    except Exception as e:
        print(f"❌ VALIDATION FAILED: {e}")
        return 2

if __name__ == '__main__':
    sys.exit(main())