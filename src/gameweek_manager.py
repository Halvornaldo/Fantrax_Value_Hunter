"""
GameweekManager - Unified Gameweek Management System
Fantasy Football Value Hunter

Provides single source of truth for gameweek detection, validation, and data protection.
Eliminates inconsistent gameweek handling across 50+ functions in the codebase.

Created: 2025-08-23
Version: 1.0
"""

import psycopg2
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class GameweekManager:
    """
    Unified gameweek management for Fantasy Football Value Hunter.
    
    Provides consistent gameweek detection, validation, and data protection
    across all system functions.
    """
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Initialize GameweekManager with database configuration.
        
        Args:
            db_config: Optional database configuration dict.
                      If None, uses default production config.
        """
        if db_config is None:
            self.db_config = {
                'host': 'localhost',
                'port': 5433,
                'user': 'fantrax_user',
                'password': 'fantrax_password',
                'database': 'fantrax_value_hunter'
            }
        else:
            self.db_config = db_config
            
        # Performance optimization: Simple caching
        self._cache_current_gw = None
        self._cache_timestamp = 0
        self._cache_duration = 30  # seconds
    
    def get_db_connection(self) -> psycopg2.extensions.connection:
        """Get database connection using configured parameters."""
        return psycopg2.connect(**self.db_config)
    
    def get_current_gameweek(self) -> int:
        """
        Get the current gameweek using intelligent detection logic with caching.
        
        Uses smart validation instead of blindly trusting MAX(gameweek).
        Detects anomalies like the GW3 issue where someone uploaded wrong data.
        
        Returns:
            int: Current gameweek (minimum 1)
        """
        # Check if cached result is still valid
        if (self._cache_current_gw is not None and 
            time.time() - self._cache_timestamp < self._cache_duration):
            return self._cache_current_gw
            
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get gameweek distribution from both tables
            cursor.execute('''
                SELECT gameweek, COUNT(*) as count, MAX(last_updated) as latest_update
                FROM player_metrics 
                WHERE gameweek IS NOT NULL 
                GROUP BY gameweek 
                ORDER BY gameweek DESC
            ''')
            metrics_data = cursor.fetchall()
            
            cursor.execute('''
                SELECT gameweek, COUNT(*) as count
                FROM raw_player_snapshots 
                WHERE gameweek IS NOT NULL 
                GROUP BY gameweek 
                ORDER BY gameweek DESC
            ''')
            raw_data = cursor.fetchall()
            
            conn.close()
            
            # Smart detection logic
            current_gw = self._analyze_gameweek_data(metrics_data, raw_data)
            
            # Update cache
            self._cache_current_gw = current_gw
            self._cache_timestamp = time.time()
            
            return current_gw
            
        except Exception as e:
            logger.error(f"Failed to get current gameweek: {e}")
            return 1  # Safe fallback
    
    def _analyze_gameweek_data(self, metrics_data: list, raw_data: list) -> int:
        """
        Analyze gameweek data to determine true current gameweek.
        
        Detects anomalies like small uploads to future gameweeks.
        """
        if not metrics_data:
            return 1
        
        # Get basic max values
        max_metrics_gw = metrics_data[0][0] if metrics_data else 1
        max_raw_gw = raw_data[0][0] if raw_data else 1
        
        # Analyze metrics data for anomalies
        total_players = 647  # Expected Premier League players
        
        for gw, count, latest_update in metrics_data:
            # Check for anomalous small uploads (like our GW3 issue)
            completion_rate = (count / total_players) * 100
            
            if completion_rate < 5:  # Less than 5% of players
                logger.warning(
                    f"Detected anomalous upload: GW{gw} has only {count}/{total_players} players ({completion_rate:.1f}%) - "
                    f"likely incorrect upload at {latest_update}"
                )
                continue  # Skip this gameweek as anomalous
            
            # This gameweek looks legitimate
            return gw
        
        # If all gameweeks look anomalous, fall back to raw data
        if raw_data:
            logger.warning(f"All player_metrics data appears anomalous, falling back to raw_player_snapshots: GW{max_raw_gw}")
            return max_raw_gw
        
        # Final fallback
        logger.warning("No reliable gameweek data found, defaulting to GW1")
        return 1
    
    def get_next_gameweek(self) -> int:
        """
        Get the next gameweek number for new data imports.
        
        Returns:
            int: Next gameweek number (current + 1)
        """
        return self.get_current_gameweek() + 1
    
    def get_gameweek_status(self, gameweek: int) -> Dict[str, Any]:
        """
        Get detailed status information for a specific gameweek.
        
        Args:
            gameweek: Gameweek number to check
            
        Returns:
            Dict with status information including data presence and completeness
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check data presence in both main tables
            cursor.execute('SELECT COUNT(*) FROM player_metrics WHERE gameweek = %s', (gameweek,))
            metrics_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM raw_player_snapshots WHERE gameweek = %s', (gameweek,))
            raw_count = cursor.fetchone()[0]
            
            # Check for any lineup prediction data (simplified - not gameweek specific)
            # Since lineup columns don't track gameweeks, just check if lineup data exists
            try:
                cursor.execute('SELECT COUNT(*) FROM players WHERE predicted_starter IS NOT NULL')
                lineup_count = cursor.fetchone()[0] or 0
            except psycopg2.errors.UndefinedColumn:
                # No lineup columns exist, that's fine
                lineup_count = 0
            
            current_gw = self.get_current_gameweek()
            
            conn.close()
            
            return {
                'gameweek': gameweek,
                'is_current': gameweek == current_gw,
                'is_future': gameweek > current_gw,
                'is_historical': gameweek < current_gw,
                'has_metrics_data': metrics_count > 0,
                'has_raw_data': raw_count > 0,
                'has_lineup_data': lineup_count > 0,
                'metrics_count': metrics_count,
                'raw_count': raw_count,
                'lineup_count': lineup_count,
                'completeness': self._calculate_completeness(metrics_count, raw_count, lineup_count)
            }
            
        except Exception as e:
            logger.error(f"Failed to get gameweek status for GW{gameweek}: {e}")
            return {
                'gameweek': gameweek,
                'error': str(e),
                'is_current': False,
                'is_future': False,
                'is_historical': False
            }
    
    def validate_gameweek_for_upload(self, gameweek: int, force: bool = False) -> Dict[str, Any]:
        """
        Validate if a gameweek is safe for data upload operations.
        
        Args:
            gameweek: Gameweek number to validate
            force: If True, bypass normal safety checks (admin override)
            
        Returns:
            Dict with validation results and recommendations
        """
        status = self.get_gameweek_status(gameweek)
        current_gw = self.get_current_gameweek()
        
        # Check for emergency protection (GW1 during system upgrade)
        if gameweek == 1 and not force:
            return {
                'valid': False,
                'action': 'blocked',
                'message': 'GW1 data is protected during gameweek unification system upgrade.',
                'recommendation': 'Contact admin if overwrite needed.',
                'requires_backup': False,
                'emergency_protection': True
            }
        
        # Future gameweeks with sanity checks
        if gameweek > current_gw:
            # Add sanity check for unrealistic gameweeks
            max_reasonable_gw = current_gw + 5  # Allow up to 5 gameweeks ahead
            if gameweek > max_reasonable_gw:
                return {
                    'valid': False,
                    'action': 'blocked',
                    'message': f'GW{gameweek} is too far in the future (current: GW{current_gw}).',
                    'recommendation': f'Did you mean GW{current_gw + 1}? Use force=True if this is intentional.',
                    'suggested_gameweek': current_gw + 1,
                    'requires_backup': False
                }
            
            return {
                'valid': True,
                'action': 'safe',
                'message': f'GW{gameweek} is a future gameweek - upload is safe.',
                'recommendation': 'Proceed with upload.',
                'requires_backup': False
            }
        
        # Current gameweek updates
        if gameweek == current_gw:
            if status.get('has_metrics_data') or status.get('has_raw_data'):
                return {
                    'valid': True,
                    'action': 'update',
                    'message': f'GW{gameweek} has existing data - this will update current gameweek.',
                    'recommendation': 'Backup will be created before update.',
                    'requires_backup': True
                }
            else:
                return {
                    'valid': True,
                    'action': 'safe',
                    'message': f'GW{gameweek} is current gameweek with no existing data.',
                    'recommendation': 'Proceed with upload.',
                    'requires_backup': False
                }
        
        # Historical gameweeks (dangerous)
        if gameweek < current_gw:
            if not force:
                return {
                    'valid': False,
                    'action': 'blocked',
                    'message': f'GW{gameweek} is historical (current: GW{current_gw}) - risk of data corruption.',
                    'recommendation': 'Use force=True if overwrite is intentional, or upload to correct gameweek.',
                    'requires_backup': True,
                    'is_historical_overwrite': True
                }
            else:
                return {
                    'valid': True,
                    'action': 'forced_overwrite',
                    'message': f'GW{gameweek} historical overwrite authorized by admin force flag.',
                    'recommendation': 'Backup will be created before overwrite.',
                    'requires_backup': True,
                    'is_historical_overwrite': True
                }
        
        # Default fallback
        return {
            'valid': False,
            'action': 'error',
            'message': f'Unable to validate GW{gameweek} upload.',
            'recommendation': 'Contact support.',
            'requires_backup': False
        }
    
    def create_backup_before_overwrite(self, gameweek: int, operation: str = 'upload') -> Dict[str, Any]:
        """
        Create backup of existing gameweek data before overwrite operations.
        
        Args:
            gameweek: Gameweek number to backup
            operation: Operation type for backup naming
            
        Returns:
            Dict with backup results and table names
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_suffix = f"gw{gameweek}_{operation}_{timestamp}"
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            backup_tables = {}
            
            # Backup player_metrics if data exists
            cursor.execute('SELECT COUNT(*) FROM player_metrics WHERE gameweek = %s', (gameweek,))
            if cursor.fetchone()[0] > 0:
                metrics_table = f"player_metrics_backup_{backup_suffix}"
                cursor.execute(f'CREATE TABLE {metrics_table} AS SELECT * FROM player_metrics WHERE gameweek = %s', (gameweek,))
                backup_tables['player_metrics'] = metrics_table
            
            # Backup raw_player_snapshots if data exists
            cursor.execute('SELECT COUNT(*) FROM raw_player_snapshots WHERE gameweek = %s', (gameweek,))
            if cursor.fetchone()[0] > 0:
                raw_table = f"raw_player_snapshots_backup_{backup_suffix}"
                cursor.execute(f'CREATE TABLE {raw_table} AS SELECT * FROM raw_player_snapshots WHERE gameweek = %s', (gameweek,))
                backup_tables['raw_player_snapshots'] = raw_table
            
            # Note: Lineup data doesn't track gameweeks in current schema
            # Skip lineup backup for now as it's not gameweek-specific
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created backup for GW{gameweek} before {operation}: {backup_tables}")
            
            return {
                'success': True,
                'gameweek': gameweek,
                'operation': operation,
                'timestamp': timestamp,
                'backup_tables': backup_tables,
                'backup_count': len(backup_tables)
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup for GW{gameweek}: {e}")
            return {
                'success': False,
                'error': str(e),
                'gameweek': gameweek,
                'operation': operation
            }
    
    def _calculate_completeness(self, metrics_count: int, raw_count: int, lineup_count: int) -> Dict[str, Any]:
        """Calculate data completeness metrics for a gameweek."""
        # Expected counts based on Premier League (647 players total)
        expected_players = 647
        
        return {
            'metrics_percentage': min(100, (metrics_count / expected_players) * 100) if metrics_count > 0 else 0,
            'raw_percentage': min(100, (raw_count / expected_players) * 100) if raw_count > 0 else 0,
            'lineup_percentage': min(100, (lineup_count / expected_players) * 100) if lineup_count > 0 else 0,
            'overall_score': (
                min(100, (metrics_count / expected_players) * 100) * 0.5 +
                min(100, (raw_count / expected_players) * 100) * 0.3 +
                min(100, (lineup_count / expected_players) * 100) * 0.2
            ) if (metrics_count > 0 or raw_count > 0 or lineup_count > 0) else 0
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system gameweek status and health metrics.
        
        Returns:
            Dict with comprehensive system status
        """
        try:
            current_gw = self.get_current_gameweek()
            current_status = self.get_gameweek_status(current_gw)
            next_gw = self.get_next_gameweek()
            next_status = self.get_gameweek_status(next_gw)
            
            return {
                'current_gameweek': current_gw,
                'next_gameweek': next_gw,
                'current_status': current_status,
                'next_status': next_status,
                'system_health': 'healthy' if current_status.get('completeness', {}).get('overall_score', 0) > 80 else 'warning',
                'emergency_protection_active': True,  # During implementation
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'error': str(e),
                'system_health': 'error',
                'last_updated': datetime.now().isoformat()
            }

# Convenience functions for backward compatibility during migration
def get_current_gameweek() -> int:
    """Convenience function for getting current gameweek."""
    manager = GameweekManager()
    return manager.get_current_gameweek()

def get_next_gameweek() -> int:
    """Convenience function for getting next gameweek."""
    manager = GameweekManager()
    return manager.get_next_gameweek()

# Feature flag support
USE_GAMEWEEK_MANAGER = os.getenv('USE_GAMEWEEK_MANAGER', 'false').lower() == 'true'

def get_gameweek_with_feature_flag() -> int:
    """
    Get current gameweek with feature flag support for gradual rollout.
    
    Returns:
        int: Current gameweek using GameweekManager if enabled, else legacy logic
    """
    if USE_GAMEWEEK_MANAGER:
        return get_current_gameweek()
    else:
        # Legacy detection logic (to be replaced during migration)
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='localhost', port=5433, 
                user='fantrax_user', password='fantrax_password',
                database='fantrax_value_hunter'
            )
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(gameweek) FROM player_metrics WHERE gameweek IS NOT NULL')
            result = cursor.fetchone()[0]
            conn.close()
            return result or 1
        except Exception:
            return 1