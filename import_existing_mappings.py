#!/usr/bin/env python3
"""
Import Existing Mappings Script
Imports name mappings from existing sources:
1. Understat alias mapping (JSON file)
2. FFS CSV mappings we discovered (hardcoded high-confidence ones)
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from name_matching import UnifiedNameMatcher
import psycopg2

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

def import_understat_aliases():
    """Import alias mappings from Understat project"""
    
    print("="*60)
    print("IMPORTING UNDERSTAT ALIAS MAPPINGS")
    print("="*60)
    
    alias_file = "c:/Users/halvo/.claude/Fantrax_Expected_Stats/data/fantrax_alias_map.json"
    
    try:
        with open(alias_file, 'r', encoding='utf-8') as f:
            alias_data = json.load(f)
    except Exception as e:
        print(f"Error reading alias file: {e}")
        return
    
    matcher = UnifiedNameMatcher(DB_CONFIG)
    conn = psycopg2.connect(**DB_CONFIG)
    
    imported_count = 0
    failed_count = 0
    
    try:
        cursor = conn.cursor()
        
        # Get all Fantrax players for matching
        cursor.execute("SELECT id, name FROM players")
        fantrax_players = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        for understat_name, fantrax_variants in alias_data.items():
            # Find the best match in our database
            matched_fantrax_id = None
            matched_fantrax_name = None
            
            for variant in fantrax_variants:
                variant_lower = variant.lower()
                if variant_lower in fantrax_players:
                    matched_fantrax_id = fantrax_players[variant_lower]
                    matched_fantrax_name = variant
                    break
            
            if matched_fantrax_id:
                # Insert mapping
                try:
                    cursor.execute("""
                        INSERT INTO name_mappings (
                            source_system, source_name, fantrax_id, fantrax_name,
                            confidence_score, match_type, verified, verified_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_system, source_name) DO NOTHING
                    """, [
                        'understat', understat_name, matched_fantrax_id, matched_fantrax_name,
                        95.0, 'alias', True, 'import_script'
                    ])
                    imported_count += 1
                    
                    if imported_count % 50 == 0:
                        print(f"Imported {imported_count} mappings...")
                        
                except Exception as e:
                    print(f"Failed to import {understat_name}: {e}")
                    failed_count += 1
            else:
                failed_count += 1
                print(f"No match found for: {understat_name}")
        
        conn.commit()
        print(f"\nUnderstat Import Complete:")
        print(f"  Successfully imported: {imported_count}")
        print(f"  Failed to match: {failed_count}")
        
    finally:
        conn.close()

def import_ffs_discovered_mappings():
    """Import high-confidence mappings we discovered from FFS CSV testing"""
    
    print("\n" + "="*60)
    print("IMPORTING FFS DISCOVERED MAPPINGS")
    print("="*60)
    
    # High-confidence mappings we discovered from testing
    ffs_mappings = [
        ('Raya Martin', 'David Raya', 'ARS', 'G'),
        ("O'Riley", 'Matt ORiley', 'BHA', 'M'),
        ('Fernando López', 'Fer Lopez', 'WOL', 'F'),
    ]
    
    matcher = UnifiedNameMatcher(DB_CONFIG)
    conn = psycopg2.connect(**DB_CONFIG)
    
    imported_count = 0
    
    try:
        cursor = conn.cursor()
        
        for source_name, fantrax_name, team, position in ffs_mappings:
            # Get the fantrax_id for this player
            cursor.execute("""
                SELECT id FROM players 
                WHERE name = %s AND team = %s AND position = %s
            """, [fantrax_name, team, position])
            
            result = cursor.fetchone()
            if result:
                fantrax_id = result[0]
                
                try:
                    cursor.execute("""
                        INSERT INTO name_mappings (
                            source_system, source_name, fantrax_id, fantrax_name,
                            team, position, confidence_score, match_type, verified, verified_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_system, source_name) DO NOTHING
                    """, [
                        'ffs', source_name, fantrax_id, fantrax_name,
                        team, position, 95.0, 'manual', True, 'import_script'
                    ])
                    imported_count += 1
                    print(f"Imported: {source_name} -> {fantrax_name}")
                    
                except Exception as e:
                    print(f"Failed to import {source_name}: {e}")
            else:
                print(f"Player not found: {fantrax_name} ({team}, {position})")
        
        conn.commit()
        print(f"\nFFS Import Complete: {imported_count} mappings imported")
        
    finally:
        conn.close()

def verify_imports():
    """Verify the imported mappings are working"""
    
    print("\n" + "="*60)
    print("VERIFYING IMPORTED MAPPINGS")
    print("="*60)
    
    matcher = UnifiedNameMatcher(DB_CONFIG)
    
    test_cases = [
        ('understat', 'jhon duran'),
        ('understat', 'matt o&#039;riley'),  # HTML encoded apostrophe
        ('ffs', 'Raya Martin'),
        ('ffs', "O'Riley"),
        ('ffs', 'Fernando López'),
    ]
    
    for source_system, source_name in test_cases:
        result = matcher.match_player(source_name, source_system)
        
        print(f"\nTest: {source_system} - {source_name}")
        print(f"  Match: {result['fantrax_name'] or 'NO MATCH'}")
        print(f"  Confidence: {result['confidence']:.1f}%")
        print(f"  From existing mapping: {not result['needs_review']}")

def get_import_statistics():
    """Show statistics about imported mappings"""
    
    print("\n" + "="*60)
    print("IMPORT STATISTICS")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("""
            SELECT 
                source_system,
                COUNT(*) as total_mappings,
                COUNT(*) FILTER (WHERE verified = TRUE) as verified_mappings,
                AVG(confidence_score) as avg_confidence
            FROM name_mappings
            GROUP BY source_system
            ORDER BY total_mappings DESC
        """)
        
        for row in cursor.fetchall():
            source_system, total, verified, avg_conf = row
            print(f"{source_system}:")
            print(f"  Total mappings: {total}")
            print(f"  Verified: {verified}")
            print(f"  Average confidence: {avg_conf:.1f}%")
            print()
        
        # Recent additions
        cursor.execute("""
            SELECT source_system, source_name, fantrax_name, confidence_score
            FROM name_mappings
            WHERE created_at > NOW() - INTERVAL '1 hour'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent = cursor.fetchall()
        if recent:
            print("Recent imports (last hour):")
            for source_system, source_name, fantrax_name, confidence in recent:
                print(f"  {source_system}: {source_name} -> {fantrax_name} ({confidence:.0f}%)")
    
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        import_understat_aliases()
        import_ffs_discovered_mappings()
        verify_imports()
        get_import_statistics()
        
        print("\n" + "="*60)
        print("IMPORT COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()