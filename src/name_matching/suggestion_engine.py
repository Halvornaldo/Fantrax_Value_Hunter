"""
Suggestion Engine Module
Generates smart suggestions for manual name matching review
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Tuple
from .matching_strategies import MatchingStrategies


class SuggestionEngine:
    """Generates intelligent suggestions for manual name matching"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.strategies = MatchingStrategies()
    
    def get_player_suggestions(self, source_name: str, team: Optional[str] = None, 
                             position: Optional[str] = None, top_n: int = 3) -> List[Dict]:
        """
        Get top N suggestions for a player name with confidence scores
        
        Args:
            source_name: Name from external source to match
            team: Team code to filter by (optional)
            position: Position to filter by (optional)
            top_n: Number of suggestions to return
            
        Returns:
            List of suggestion dictionaries with fantrax_id, name, confidence
        """
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query to get potential matches
            base_query = """
                SELECT p.id as fantrax_id, p.name, p.team, p.position
                FROM players p
                WHERE 1=1
            """
            params = []
            
            # Add filters
            if team:
                base_query += " AND p.team = %s"
                params.append(team)
            
            if position:
                base_query += " AND p.position = %s"
                params.append(position)
            
            # Order by name for consistent results
            base_query += " ORDER BY p.name"
            
            cursor.execute(base_query, params)
            candidates = cursor.fetchall()
            
            # Score each candidate
            scored_suggestions = []
            
            for candidate in candidates:
                candidate_name = candidate['name']
                
                # Try all matching strategies
                strategies = self.strategies.get_all_strategies()
                best_confidence = 0.0
                best_strategy = "no_match"
                
                for strategy_name, strategy_func in strategies:
                    is_match, confidence = strategy_func(source_name, candidate_name)
                    
                    if is_match and confidence > best_confidence:
                        best_confidence = confidence
                        best_strategy = strategy_name
                
                # Include candidates with confidence > 20% for suggestions
                if best_confidence > 20.0:
                    # Apply additional scoring factors
                    final_confidence = self._apply_contextual_scoring(
                        source_name, candidate, best_confidence, team, position
                    )
                    
                    scored_suggestions.append({
                        'fantrax_id': candidate['fantrax_id'],
                        'name': candidate['name'],
                        'team': candidate['team'],
                        'position': candidate['position'],
                        'confidence': final_confidence,
                        'strategy': best_strategy
                    })
            
            # Sort by confidence and return top N
            scored_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
            
            return scored_suggestions[:top_n]
            
        finally:
            conn.close()
    
    def _apply_contextual_scoring(self, source_name: str, candidate: Dict, 
                                base_confidence: float, expected_team: Optional[str] = None,
                                expected_position: Optional[str] = None) -> float:
        """
        Apply contextual scoring adjustments based on team and position matches
        """
        final_confidence = base_confidence
        
        # Team match bonus
        if expected_team and candidate['team'] == expected_team:
            final_confidence += 10.0  # 10% bonus for team match
        elif expected_team and candidate['team'] != expected_team:
            final_confidence -= 15.0  # 15% penalty for team mismatch
        
        # Position match bonus
        if expected_position and candidate['position'] == expected_position:
            final_confidence += 5.0  # 5% bonus for position match
        elif expected_position and candidate['position'] != expected_position:
            final_confidence -= 10.0  # 10% penalty for position mismatch
        
        # Special position penalties (goalkeepers are very distinct)
        if expected_position == 'G' and candidate['position'] != 'G':
            final_confidence -= 30.0  # Heavy penalty for wrong GK
        elif expected_position != 'G' and candidate['position'] == 'G':
            final_confidence -= 25.0  # Heavy penalty for GK in wrong position
        
        # Ensure confidence stays within valid range
        return max(0.0, min(100.0, final_confidence))
    
    def get_suggestions_for_team_position(self, team: str, position: str, 
                                        excluded_ids: List[str] = None) -> List[Dict]:
        """
        Get all players for a specific team and position
        Useful for manual override dropdowns
        """
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT p.id as fantrax_id, p.name, p.team, p.position
                FROM players p
                WHERE p.team = %s AND p.position = %s
            """
            params = [team, position]
            
            if excluded_ids:
                placeholders = ','.join(['%s'] * len(excluded_ids))
                query += f" AND p.id NOT IN ({placeholders})"
                params.extend(excluded_ids)
            
            query += " ORDER BY p.name"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        finally:
            conn.close()
    
    def analyze_similar_mappings(self, source_name: str, source_system: str) -> List[Dict]:
        """
        Find similar mappings that might help with current match
        Looks for patterns in verified mappings
        """
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Look for similar source names in verified mappings
            query = """
                SELECT nm.source_name, nm.fantrax_name, nm.confidence_score, nm.match_type
                FROM name_mappings nm
                WHERE nm.source_system = %s 
                AND nm.verified = TRUE
                AND (
                    nm.source_name ILIKE %s
                    OR %s ILIKE nm.source_name
                    OR nm.fantrax_name ILIKE %s
                )
                ORDER BY nm.confidence_score DESC
                LIMIT 5
            """
            
            pattern = f"%{source_name}%"
            cursor.execute(query, [source_system, pattern, pattern, pattern])
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        finally:
            conn.close()
    
    def get_suggestion_statistics(self) -> Dict:
        """
        Get statistics about suggestion accuracy and usage
        """
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get basic mapping stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_mappings,
                    COUNT(*) FILTER (WHERE verified = TRUE) as verified_mappings,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(*) FILTER (WHERE confidence_score >= 90) as high_confidence_count,
                    COUNT(*) FILTER (WHERE confidence_score BETWEEN 70 AND 89) as medium_confidence_count,
                    COUNT(*) FILTER (WHERE confidence_score < 70) as low_confidence_count
                FROM name_mappings
            """)
            stats = dict(cursor.fetchone())
            
            # Get strategy usage stats
            cursor.execute("""
                SELECT match_type, COUNT(*) as usage_count
                FROM name_mappings
                WHERE verified = TRUE
                GROUP BY match_type
                ORDER BY usage_count DESC
            """)
            strategy_stats = cursor.fetchall()
            stats['strategy_usage'] = [dict(row) for row in strategy_stats]
            
            return stats
            
        finally:
            conn.close()