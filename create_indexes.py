#!/usr/bin/env python3
"""
Create performance indexes for Fantrax Value Hunter
Executes the SQL commands to add database indexes for query optimization
"""

import psycopg2
import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import database config from Flask app
from app import DB_CONFIG

def create_indexes():
    """Create all performance indexes"""
    
    indexes_sql = [
        # Index 1: Speed up main player_metrics JOIN (most critical)
        """CREATE INDEX IF NOT EXISTS idx_player_metrics_gameweek_player 
           ON player_metrics(gameweek, player_id);""",
        
        # Index 2: Speed up player_games_data GROUP BY subquery
        """CREATE INDEX IF NOT EXISTS idx_player_games_data_player_id 
           ON player_games_data(player_id);""",
        
        # Index 3: Speed up team_fixtures JOIN  
        """CREATE INDEX IF NOT EXISTS idx_team_fixtures_team_gameweek 
           ON team_fixtures(team_code, gameweek);""",
        
        # Index 4: Speed up V2 form calculations
        """CREATE INDEX IF NOT EXISTS idx_player_form_player_gameweek 
           ON player_form(player_id, gameweek DESC);""",
        
        # Index 5: Primary key optimizations
        """CREATE INDEX IF NOT EXISTS idx_players_id 
           ON players(id);""",
        
        # Index 6: Speed up position and team filtering
        """CREATE INDEX IF NOT EXISTS idx_players_position_team 
           ON players(position, team);"""
    ]
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating performance indexes...")
        for i, sql in enumerate(indexes_sql, 1):
            print(f"Creating index {i}/6...")
            cursor.execute(sql)
            conn.commit()
            print(f"Index {i} created successfully")
        
        # Show current indexes
        print("\nVerifying indexes...")
        cursor.execute("""
            SELECT 
                schemaname,
                tablename, 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename IN ('players', 'player_metrics', 'player_games_data', 'team_fixtures', 'player_form')
              AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname;
        """)
        
        results = cursor.fetchall()
        print(f"\nFound {len(results)} performance indexes:")
        for row in results:
            print(f"  {row[1]}.{row[2]}")
        
        cursor.close()
        conn.close()
        
        print("\nAll indexes created successfully!")
        print("Expected performance improvement: 2-3x faster database queries")
        
    except Exception as e:
        print(f"Error creating indexes: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_indexes()