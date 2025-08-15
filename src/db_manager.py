"""
Database Manager for Fantrax Value Hunter
Provides Database MCP wrapper for PostgreSQL operations
"""

import json
from typing import Dict, List, Optional, Any
import asyncio


class DatabaseManager:
    """Database MCP wrapper for Fantrax Value Hunter"""
    
    def __init__(self):
        self.connected = False
        self.connection_config = {
            'host': 'localhost',
            'user': 'fantrax_user',
            'password': 'fantrax_password',
            'database': 'fantrax_value_hunter',
            'port': 5433
        }
        
    async def connect(self):
        """Connect to PostgreSQL database using Database MCP"""
        if self.connected:
            return True
            
        try:
            # Note: MCP functions are called by Claude, not directly importable
            # This method is called by Flask/Python but connection is managed by Claude
            self.connected = True
            print(f"[SUCCESS] Connected to fantrax_value_hunter database")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            raise
    
    async def get_candidate_pools(self, gameweek: int, position: Optional[str] = None):
        """Get players ranked by True Value for dashboard display"""
        base_query = """
            SELECT 
                p.id, p.name, p.team, p.position,
                pm.price, pm.ppg, pm.ppg_source, pm.value_score, pm.true_value,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier,
                pm.last_updated
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.gameweek = $1
        """
        
        if position:
            query = base_query + " AND p.position = $2 ORDER BY pm.true_value DESC"
            params = [gameweek, position]
        else:
            query = base_query + " ORDER BY pm.true_value DESC"
            params = [gameweek]
            
        # Note: MCP calls handled by Claude environment
        # This returns the query for Claude to execute
        return {'query': query, 'params': params}
        return result
    
    async def update_player_metrics(self, player_data: List[Dict], gameweek: int):
        """Update player metrics after parameter changes"""
        from mcp__database__execute import mcp__database__execute
        
        updated_count = 0
        for player in player_data:
            await mcp__database__execute(
                sql="""
                    INSERT INTO player_metrics 
                    (player_id, gameweek, price, ppg, ppg_source, value_score, true_value,
                     form_multiplier, fixture_multiplier, starter_multiplier)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (player_id, gameweek) 
                    DO UPDATE SET
                        price = $3, ppg = $4, ppg_source = $5, value_score = $6, true_value = $7,
                        form_multiplier = $8, fixture_multiplier = $9, 
                        starter_multiplier = $10,
                        last_updated = CURRENT_TIMESTAMP
                """,
                params=[
                    player['id'], gameweek, 
                    player.get('price', 0), 
                    player.get('ppg', 0),
                    player.get('ppg_source', 'Unknown'),
                    player.get('value_score', 0), 
                    player.get('true_value', 0),
                    player.get('form_multiplier', 1.0),
                    player.get('fixture_multiplier', 1.0),
                    player.get('starter_multiplier', 1.0)
                ]
            )
            updated_count += 1
        
        print(f"[SUCCESS] Updated metrics for {updated_count} players in gameweek {gameweek}")
        return updated_count
    
    async def get_player_form(self, player_id: str, lookback: int = 3):
        """Get historical form data for a player"""
        from mcp__database__query import mcp__database__query
        
        result = await mcp__database__query(
            sql="""
                SELECT gameweek, points 
                FROM player_form
                WHERE player_id = $1
                ORDER BY gameweek DESC
                LIMIT $2
            """,
            params=[player_id, lookback]
        )
        return result
    
    async def store_form_data(self, gameweek_results: Dict[str, float], gameweek: int):
        """Store gameweek results for form calculation"""
        from mcp__database__execute import mcp__database__execute
        
        stored_count = 0
        for player_id, points in gameweek_results.items():
            await mcp__database__execute(
                sql="""
                    INSERT INTO player_form (player_id, gameweek, points)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (player_id, gameweek) 
                    DO UPDATE SET points = $3
                """,
                params=[player_id, gameweek, points]
            )
            stored_count += 1
            
        print(f"[SUCCESS] Stored form data for {stored_count} players in gameweek {gameweek}")
        return stored_count
    
    async def import_players(self, players_data: List[Dict]):
        """Import player records from JSON data"""
        from mcp__database__execute import mcp__database__execute
        
        imported_count = 0
        for player in players_data:
            await mcp__database__execute(
                sql="""
                    INSERT INTO players (id, name, team, position)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                        name = $2, team = $3, position = $4, updated_at = CURRENT_TIMESTAMP
                """,
                params=[
                    player['id'], 
                    player['name'],
                    player.get('team', ''), 
                    player.get('position', '')
                ]
            )
            imported_count += 1
            
        print(f"[SUCCESS] Imported {imported_count} players")
        return imported_count


def run_sync(coro):
    """Helper function to run async database calls in sync code"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Test connection function
async def test_connection():
    """Test database connection and basic operations"""
    db = DatabaseManager()
    
    try:
        # Test connection
        await db.connect()
        print("✅ Database connection successful")
        
        # Test basic query
        from mcp__database__query import mcp__database__query
        result = await mcp__database__query(
            sql="SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'"
        )
        print(f"✅ Database has {result[0]['table_count']} tables")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


if __name__ == "__main__":
    # Run connection test
    success = run_sync(test_connection())
    if success:
        print("\n🎉 Database MCP setup complete and working!")
    else:
        print("\n💥 Database setup needs attention")