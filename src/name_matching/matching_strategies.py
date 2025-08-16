"""
Matching Strategies Module
Contains various algorithms for matching player names
"""

import unicodedata
import re
import html
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple


class MatchingStrategies:
    """Collection of name matching strategies with confidence scoring"""
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize name for better matching:
        - Decode HTML entities (&#039; -> ')
        - Remove accents and diacritics
        - Remove apostrophes, hyphens, periods
        - Convert to lowercase
        - Remove extra spaces
        """
        if not name:
            return ""
        
        # First decode HTML entities (&#039; -> ', &amp; -> &, etc.)
        name = html.unescape(name)
            
        # Remove accents using Unicode normalization
        normalized = unicodedata.normalize('NFD', name)
        ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Replace common characters
        ascii_name = ascii_name.replace("'", "").replace("-", " ").replace(".", "")
        ascii_name = ascii_name.replace("ß", "ss")
        
        # Clean up spaces and convert to lowercase
        ascii_name = re.sub(r'\s+', ' ', ascii_name.strip().lower())
        
        return ascii_name
    
    @staticmethod
    def exact_match(source_name: str, target_name: str) -> Tuple[bool, float]:
        """
        Exact string match (case insensitive)
        Returns: (match_found, confidence_score)
        """
        if source_name.lower().strip() == target_name.lower().strip():
            return True, 100.0
        return False, 0.0
    
    @staticmethod
    def normalized_match(source_name: str, target_name: str) -> Tuple[bool, float]:
        """
        Match using normalized names (removes accents, apostrophes, etc.)
        """
        norm_source = MatchingStrategies.normalize_name(source_name)
        norm_target = MatchingStrategies.normalize_name(target_name)
        
        if norm_source == norm_target:
            return True, 95.0
        return False, 0.0
    
    @staticmethod
    def contains_match(source_name: str, target_name: str) -> Tuple[bool, float]:
        """
        Check if one name contains the other (useful for partial names)
        """
        norm_source = MatchingStrategies.normalize_name(source_name)
        norm_target = MatchingStrategies.normalize_name(target_name)
        
        # Skip very short names to avoid false positives
        if len(norm_source) < 3 or len(norm_target) < 3:
            return False, 0.0
            
        if norm_source in norm_target or norm_target in norm_source:
            # Calculate confidence based on length similarity
            shorter = min(len(norm_source), len(norm_target))
            longer = max(len(norm_source), len(norm_target))
            confidence = (shorter / longer) * 85.0  # Max 85% for contains match
            return True, confidence
        
        return False, 0.0
    
    @staticmethod
    def name_component_match(source_name: str, target_name: str) -> Tuple[bool, float]:
        """
        Match based on individual name components (first name, last name, etc.)
        Handles cases like "Raya Martin" -> "David Raya"
        """
        norm_source = MatchingStrategies.normalize_name(source_name)
        norm_target = MatchingStrategies.normalize_name(target_name)
        
        source_parts = set(norm_source.split())
        target_parts = set(norm_target.split())
        
        # Remove very short parts (initials, etc.)
        source_parts = {part for part in source_parts if len(part) >= 2}
        target_parts = {part for part in target_parts if len(part) >= 2}
        
        if not source_parts or not target_parts:
            return False, 0.0
        
        # Find matching components
        matching_parts = source_parts & target_parts
        
        if matching_parts:
            # Calculate confidence based on proportion of matching parts
            match_ratio = len(matching_parts) / max(len(source_parts), len(target_parts))
            
            # Higher confidence if a significant word matches
            max_word_length = max(len(word) for word in matching_parts)
            length_bonus = min(max_word_length * 2, 20)  # Up to 20% bonus for long matching words
            
            confidence = (match_ratio * 70) + length_bonus  # Base 70% + length bonus
            confidence = min(confidence, 90.0)  # Cap at 90%
            
            return True, confidence
        
        return False, 0.0
    
    @staticmethod
    def fuzzy_similarity_match(source_name: str, target_name: str) -> Tuple[bool, float]:
        """
        Fuzzy string matching using sequence similarity
        Good for catching typos and slight variations
        """
        norm_source = MatchingStrategies.normalize_name(source_name)
        norm_target = MatchingStrategies.normalize_name(target_name)
        
        if not norm_source or not norm_target:
            return False, 0.0
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, norm_source, norm_target).ratio()
        confidence = similarity * 100
        
        # Only consider it a match if similarity is above threshold
        if confidence >= 75.0:
            return True, min(confidence, 85.0)  # Cap fuzzy matches at 85%
        
        return False, 0.0
    
    @staticmethod
    def last_name_match(source_name: str, target_name: str) -> Tuple[bool, float]:
        """
        Match based on last name similarity
        Useful when first names differ but last names match
        """
        norm_source = MatchingStrategies.normalize_name(source_name)
        norm_target = MatchingStrategies.normalize_name(target_name)
        
        source_parts = norm_source.split()
        target_parts = norm_target.split()
        
        if len(source_parts) < 2 or len(target_parts) < 2:
            return False, 0.0
        
        # Get last names
        source_last = source_parts[-1]
        target_last = target_parts[-1]
        
        # Skip very short last names
        if len(source_last) < 3 or len(target_last) < 3:
            return False, 0.0
        
        # Check for exact last name match
        if source_last == target_last:
            return True, 70.0
        
        # Check for fuzzy last name match
        similarity = SequenceMatcher(None, source_last, target_last).ratio()
        if similarity >= 0.85:
            confidence = 60.0 + (similarity - 0.85) * 200  # 60-90% confidence
            return True, min(confidence, 80.0)
        
        return False, 0.0
    
    @classmethod
    def get_all_strategies(cls) -> List[Tuple[str, callable]]:
        """
        Get all matching strategies in order of preference
        Returns list of (strategy_name, strategy_function) tuples
        """
        return [
            ('exact', cls.exact_match),
            ('normalized', cls.normalized_match),
            ('contains', cls.contains_match),
            ('name_component', cls.name_component_match),
            ('fuzzy_similarity', cls.fuzzy_similarity_match),
            ('last_name', cls.last_name_match),
        ]
    
    @classmethod
    def find_best_match(cls, source_name: str, target_names: List[str]) -> Tuple[Optional[str], float, str]:
        """
        Find the best match from a list of target names
        
        Args:
            source_name: Name to match
            target_names: List of possible target names
            
        Returns:
            (best_match_name, confidence_score, strategy_used)
        """
        best_match = None
        best_confidence = 0.0
        best_strategy = "no_match"
        
        strategies = cls.get_all_strategies()
        
        for target_name in target_names:
            for strategy_name, strategy_func in strategies:
                is_match, confidence = strategy_func(source_name, target_name)
                
                if is_match and confidence > best_confidence:
                    best_match = target_name
                    best_confidence = confidence
                    best_strategy = strategy_name
                    
                    # If we find a perfect match, stop searching
                    if confidence >= 100.0:
                        return best_match, best_confidence, best_strategy
        
        return best_match, best_confidence, best_strategy