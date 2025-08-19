#!/usr/bin/env python3
"""
Create player_games_data table with fantrax_user permissions
This table will store all games-related data separately from player_metrics
"""
import psycopg2

def create_games_table():
    try:
        # Connect as fantrax_user (has CREATE TABLE permissions)
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='fantrax_user',
            password='fantrax_password',
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        print("Creating player_games_data table...")
        
        # Create the new table with fantrax_user as owner
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS player_games_data (
            player_id VARCHAR(50) NOT NULL,
            gameweek INTEGER NOT NULL,
            total_points DECIMAL(8,2) DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            total_points_historical DECIMAL(8,2) DEFAULT 0,
            games_played_historical INTEGER DEFAULT 0,
            data_source VARCHAR(20) DEFAULT 'current',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, gameweek)
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Add indexes for performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_player_games_player_id ON player_games_data(player_id);",
            "CREATE INDEX IF NOT EXISTS idx_player_games_gameweek ON player_games_data(gameweek);",
            "CREATE INDEX IF NOT EXISTS idx_player_games_data_source ON player_games_data(data_source);",
            "CREATE INDEX IF NOT EXISTS idx_player_games_historical ON player_games_data(games_played_historical);"
        ]
        
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
        
        # Add comments for documentation
        comments_sql = [
            "COMMENT ON TABLE player_games_data IS 'Games tracking data for players - owned by fantrax_user';",
            "COMMENT ON COLUMN player_games_data.total_points IS 'Current season total fantasy points';",
            "COMMENT ON COLUMN player_games_data.games_played IS 'Current season games played count';",
            "COMMENT ON COLUMN player_games_data.total_points_historical IS '2024-25 season total fantasy points';",
            "COMMENT ON COLUMN player_games_data.games_played_historical IS '2024-25 season games played count';",
            "COMMENT ON COLUMN player_games_data.data_source IS 'Primary data source: current, historical, or blended';"
        ]
        
        for comment_sql in comments_sql:
            cursor.execute(comment_sql)
        
        conn.commit()
        
        print("✅ Table created successfully!")
        
        # Verify table ownership and structure
        cursor.execute("""
            SELECT 
                tablename,
                tableowner
            FROM pg_tables 
            WHERE tablename = 'player_games_data'
        """)
        
        table_info = cursor.fetchone()
        if table_info:
            print(f"Table owner: {table_info[1]}")
        
        # Check column structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'player_games_data'
            ORDER BY ordinal_position
        """)
        
        print("\nTable structure:")
        for row in cursor.fetchall():
            print(f"  {row[0]:<30} {row[1]:<15} nullable:{row[2]} default:{row[3]}")
        
        # Test permissions
        print("\nTesting table permissions...")
        cursor.execute("INSERT INTO player_games_data (player_id, gameweek) VALUES ('test', 1)")
        cursor.execute("UPDATE player_games_data SET data_source = 'test' WHERE player_id = 'test'")
        cursor.execute("DELETE FROM player_games_data WHERE player_id = 'test'")
        conn.commit()
        print("✅ All permissions work correctly!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        return False

if __name__ == "__main__":
    success = create_games_table()
    if success:
        print("\n🎯 Games table ready for Sprint 2 implementation!")
    else:
        print("\n💥 Table creation failed!")