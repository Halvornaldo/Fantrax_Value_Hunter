"""
Unified Name Matcher
Central matching service for all data imports into Fantrax Value Hunter
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from .matching_strategies import MatchingStrategies
from .suggestion_engine import SuggestionEngine


class UnifiedNameMatcher:
    """
    Unified name matching system for all external data sources
    
    Features:
    - Persistent mapping storage in database
    - Multi-strategy matching with confidence scoring
    - Smart suggestions for manual review
    - Learning system that improves over time
    - Audit trail for all mappings
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.strategies = MatchingStrategies()
        self.suggestion_engine = SuggestionEngine(db_config)
        self.cache = {}  # In-memory cache for session performance
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def match_player(self, source_name: str, source_system: str, 
                    team: Optional[str] = None, position: Optional[str] = None,
                    force_refresh: bool = False) -> Dict:
        """
        Main entry point for player name matching
        
        Args:
            source_name: Player name from external source
            source_system: Source identifier ('ffs', 'understat', 'fbref', etc.)
            team: Team code for additional validation (optional)
            position: Position for additional validation (optional)
            force_refresh: Skip cache and force new matching (default: False)
            
        Returns:
            {
                'fantrax_id': str or None,
                'fantrax_name': str or None,
                'confidence': float (0-100),
                'match_type': str,
                'needs_review': bool,
                'suggested_matches': List[Dict],  # Top 3 suggestions
                'mapping_id': int or None,  # Database mapping ID if exists
                'from_cache': bool
            }
        """
        cache_key = f"{source_system}:{source_name}"
        
        # Check cache first (unless force refresh)
        if not force_refresh and cache_key in self.cache:
            result = self.cache[cache_key].copy()
            result['from_cache'] = True
            return result
        
        # Step 1: Check for existing verified mapping
        existing_mapping = self._check_existing_mapping(source_name, source_system)
        if existing_mapping:
            self._update_usage_stats(existing_mapping['id'])
            result = self._format_result_from_mapping(existing_mapping)
            self.cache[cache_key] = result
            return result
        
        # Step 2: Try multi-strategy matching against database
        match_result = self._multi_strategy_match(source_name, team, position)
        
        # Step 3: Generate suggestions for manual review if needed
        suggestions = []
        if not match_result['fantrax_id'] or match_result['confidence'] < 85.0:
            suggestions = self.suggestion_engine.get_player_suggestions(
                source_name, team, position, top_n=3
            )
        
        # Step 4: Determine if manual review is needed
        needs_review = (
            not match_result['fantrax_id'] or 
            match_result['confidence'] < 85.0 or
            len(suggestions) > 0
        )
        
        # Step 5: Save mapping if confidence is reasonable
        mapping_id = None
        if match_result['fantrax_id'] and match_result['confidence'] >= 50.0:
            mapping_id = self._save_mapping({
                'source_system': source_system,
                'source_name': source_name,
                'fantrax_id': match_result['fantrax_id'],
                'fantrax_name': match_result['fantrax_name'],
                'team': team,
                'position': position,
                'confidence_score': match_result['confidence'],
                'match_type': match_result['match_type'],
                'verified': not needs_review  # Auto-verify high confidence matches
            })
        
        result = {
            'fantrax_id': match_result['fantrax_id'],
            'fantrax_name': match_result['fantrax_name'],
            'confidence': match_result['confidence'],
            'match_type': match_result['match_type'],
            'needs_review': needs_review,
            'suggested_matches': suggestions,
            'mapping_id': mapping_id,
            'from_cache': False
        }
        
        # Cache the result
        self.cache[cache_key] = result
        
        return result
    
    def _check_existing_mapping(self, source_name: str, source_system: str) -> Optional[Dict]:
        """Check if we already have a mapping for this name/system combination"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT nm.*, p.name as current_fantrax_name
                FROM name_mappings nm
                LEFT JOIN players p ON nm.fantrax_id = p.id
                WHERE nm.source_system = %s AND nm.source_name = %s
                ORDER BY nm.verified DESC, nm.confidence_score DESC
                LIMIT 1
            """
            
            cursor.execute(query, [source_system, source_name])
            result = cursor.fetchone()
            
            return dict(result) if result else None
            
        finally:
            conn.close()
    
    def _multi_strategy_match(self, source_name: str, team: Optional[str] = None,
                            position: Optional[str] = None) -> Dict:
        """
        Apply multiple matching strategies to find best match
        """
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get potential candidates from database
            base_query = """
                SELECT p.id, p.name, p.team, p.position
                FROM players p
                WHERE 1=1
            """
            params = []
            
            # Filter by team and position if provided
            if team:
                base_query += " AND p.team = %s"
                params.append(team)
            
            if position:
                base_query += " AND p.position = %s"
                params.append(position)
            
            cursor.execute(base_query, params)
            candidates = cursor.fetchall()
            
            if not candidates:
                return {
                    'fantrax_id': None,
                    'fantrax_name': None,
                    'confidence': 0.0,
                    'match_type': 'no_candidates'
                }
            
            # Apply matching strategies
            candidate_names = [c['name'] for c in candidates]
            best_match_name, confidence, strategy = self.strategies.find_best_match(
                source_name, candidate_names
            )
            
            if best_match_name:
                # Find the matching candidate details
                for candidate in candidates:
                    if candidate['name'] == best_match_name:
                        return {
                            'fantrax_id': candidate['id'],
                            'fantrax_name': candidate['name'],
                            'confidence': confidence,
                            'match_type': strategy
                        }
            
            return {
                'fantrax_id': None,
                'fantrax_name': None,
                'confidence': 0.0,
                'match_type': 'no_match'
            }
            
        finally:
            conn.close()
    
    def _save_mapping(self, mapping_data: Dict) -> int:
        """Save a new mapping to the database"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO name_mappings (
                    source_system, source_name, fantrax_id, fantrax_name,
                    team, position, confidence_score, match_type, verified,
                    last_used, usage_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (source_system, source_name) 
                DO UPDATE SET
                    fantrax_id = EXCLUDED.fantrax_id,
                    fantrax_name = EXCLUDED.fantrax_name,
                    confidence_score = EXCLUDED.confidence_score,
                    match_type = EXCLUDED.match_type,
                    verified = EXCLUDED.verified,
                    last_used = EXCLUDED.last_used,
                    usage_count = name_mappings.usage_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            cursor.execute(query, [
                mapping_data['source_system'],
                mapping_data['source_name'],
                mapping_data['fantrax_id'],
                mapping_data['fantrax_name'],
                mapping_data.get('team'),
                mapping_data.get('position'),
                mapping_data['confidence_score'],
                mapping_data['match_type'],
                mapping_data.get('verified', False),
                datetime.now(),
                1  # Initial usage count
            ])
            
            mapping_id = cursor.fetchone()[0]
            conn.commit()
            
            self.logger.info(f"Saved mapping: {mapping_data['source_name']} -> {mapping_data['fantrax_name']} ({mapping_data['confidence_score']:.1f}%)")
            
            return mapping_id
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to save mapping: {e}")
            raise
        finally:
            conn.close()
    
    def _update_usage_stats(self, mapping_id: int):
        """Update usage statistics for an existing mapping"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor()
            
            query = """
                UPDATE name_mappings 
                SET usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            
            cursor.execute(query, [mapping_id])
            conn.commit()
            
        finally:
            conn.close()
    
    def _format_result_from_mapping(self, mapping: Dict) -> Dict:
        """Format a database mapping into a standard result format"""
        return {
            'fantrax_id': mapping['fantrax_id'],
            'fantrax_name': mapping.get('current_fantrax_name') or mapping['fantrax_name'],
            'confidence': mapping['confidence_score'],
            'match_type': mapping['match_type'],
            'needs_review': not mapping['verified'],
            'suggested_matches': [],  # Existing mappings don't need suggestions
            'mapping_id': mapping['id'],
            'from_cache': False
        }
    
    def confirm_mapping(self, source_name: str, source_system: str, 
                       fantrax_id: str, user_id: str = 'unknown',
                       confidence_override: Optional[float] = None) -> bool:
        """
        Confirm/verify a name mapping manually
        
        Args:
            source_name: Original source name
            source_system: Source system identifier
            fantrax_id: Confirmed Fantrax player ID
            user_id: User who confirmed the mapping
            confidence_override: Override confidence score (optional)
            
        Returns:
            True if successful, False otherwise
        """
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get player details
            cursor.execute("SELECT name, team, position FROM players WHERE id = %s", [fantrax_id])
            player = cursor.fetchone()
            
            if not player:
                self.logger.error(f"Player ID {fantrax_id} not found")
                return False
            
            # Save/update the mapping
            query = """
                INSERT INTO name_mappings (
                    source_system, source_name, fantrax_id, fantrax_name,
                    team, position, confidence_score, match_type, verified,
                    verification_date, verified_by, last_used, usage_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (source_system, source_name)
                DO UPDATE SET
                    fantrax_id = EXCLUDED.fantrax_id,
                    fantrax_name = EXCLUDED.fantrax_name,
                    team = EXCLUDED.team,
                    position = EXCLUDED.position,
                    confidence_score = EXCLUDED.confidence_score,
                    match_type = 'manual',
                    verified = TRUE,
                    verification_date = CURRENT_TIMESTAMP,
                    verified_by = EXCLUDED.verified_by,
                    last_used = CURRENT_TIMESTAMP,
                    usage_count = name_mappings.usage_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            confidence = confidence_override or 100.0  # Manual confirmations get high confidence
            
            cursor.execute(query, [
                source_system, source_name, fantrax_id, player['name'],
                player['team'], player['position'], confidence, 'manual',
                True, datetime.now(), user_id, datetime.now(), 1
            ])
            
            conn.commit()
            
            # Clear cache for this mapping
            cache_key = f"{source_system}:{source_name}"
            if cache_key in self.cache:
                del self.cache[cache_key]
            
            self.logger.info(f"Confirmed mapping: {source_name} -> {player['name']} by {user_id}")
            
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to confirm mapping: {e}")
            return False
        finally:
            conn.close()
    
    def get_mapping_statistics(self) -> Dict:
        """Get comprehensive statistics about the matching system"""
        return self.suggestion_engine.get_suggestion_statistics()
    
    def batch_match_players(self, players: List[Dict], source_system: str) -> List[Dict]:
        """
        Match a batch of players efficiently
        
        Args:
            players: List of player dicts with 'name', 'team', 'position'
            source_system: Source system identifier
            
        Returns:
            List of matching results
        """
        results = []
        
        for player_data in players:
            result = self.match_player(
                source_name=player_data['name'],
                source_system=source_system,
                team=player_data.get('team'),
                position=player_data.get('position')
            )
            
            # Add original player data to result
            result['original_data'] = player_data
            results.append(result)
        
        return results
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        self.cache.clear()
        self.logger.info("Name matching cache cleared")