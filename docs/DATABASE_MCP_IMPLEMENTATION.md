# Database MCP Implementation Guide
**Fantrax Value Hunter - Phase 3 Dashboard Development**

## 🎯 Quick Summary

Database MCP is ALREADY connected in your environment and is SIMPLER than SQLAlchemy. It provides direct PostgreSQL access through function calls - no ORM complexity needed.

---

## 📊 Why Database is Required

Your `form_tracker.py` needs historical gameweek data to calculate form:
- Requires last 3-5 games of player performance 
- Currently returns 1.0x (disabled) because no historical data exists
- JSON files can't efficiently store time-series data
- Database enables form tracking to actually work

---

## 🔧 Database MCP Tools Available

```python
# Already in your environment - no installation needed!
mcp__database__connect_db     # One-time connection setup
mcp__database__query          # SELECT queries  
mcp__database__execute        # INSERT/UPDATE/DELETE
mcp__database__list_tables    # View all tables
mcp__database__describe_table # Get table structure
```

---

## 📁 Implementation Structure

```
Fantrax_Value_Hunter/
├── src/
│   ├── app.py                # Flask application
│   ├── db_manager.py         # Database MCP wrapper (NEW)
│   ├── candidate_analyzer.py # Existing logic (minimal changes)
│   └── form_tracker.py       # Update to use database
├── migrations/
│   ├── 001_create_schema.py  # Database setup
│   └── 002_import_data.py    # JSON to database migration
└── templates/
    └── dashboard.html        # Two-panel UI
```

---

## 🗄️ Minimal Database Schema

```sql
-- Only what we actually need - no feature creep!
CREATE TABLE players (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team VARCHAR(5),
    position VARCHAR(10)
);

CREATE TABLE player_form (
    player_id VARCHAR(10) REFERENCES players(id),
    gameweek INT NOT NULL,
    points DECIMAL(6,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, gameweek)
);

CREATE TABLE player_metrics (
    player_id VARCHAR(10) REFERENCES players(id),
    gameweek INT NOT NULL,
    price DECIMAL(6,2),
    ppg DECIMAL(6,2),
    ppg_source VARCHAR(20),
    value_score DECIMAL(8,3),
    true_value DECIMAL(8,3),
    form_multiplier DECIMAL(4,3) DEFAULT 1.0,
    fixture_multiplier DECIMAL(4,3) DEFAULT 1.0,
    starter_multiplier DECIMAL(4,3) DEFAULT 1.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, gameweek)
);
```

---

## 💻 Database Manager Implementation

### src/db_manager.py
```python
import json
from typing import Dict, List, Optional
import asyncio

class DatabaseManager:
    def __init__(self):
        self.connected = False
        
    async def connect(self):
        """One-time database connection"""
        if self.connected:
            return
            
        result = await mcp__database__connect_db(
            host="localhost",
            user="fantrax_user", 
            password="your_password",
            database="fantrax_value_hunter",
            port=5432
        )
        self.connected = True
        print(f"[SUCCESS] Connected to database")
        return result
    
    async def get_candidate_pools(self, gameweek: int, position: Optional[str] = None):
        """Get players ranked by True Value"""
        base_query = """
            SELECT 
                p.id, p.name, p.team, p.position,
                pm.price, pm.ppg, pm.value_score, pm.true_value,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier
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
            
        result = await mcp__database__query(sql=query, params=params)
        return result
    
    async def update_player_metrics(self, player_data: List[Dict], gameweek: int):
        """Update metrics after parameter changes"""
        for player in player_data:
            await mcp__database__execute(
                sql="""
                    INSERT INTO player_metrics 
                    (player_id, gameweek, price, ppg, value_score, true_value,
                     form_multiplier, fixture_multiplier, starter_multiplier)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (player_id, gameweek) 
                    DO UPDATE SET
                        price = $3, ppg = $4, value_score = $5, true_value = $6,
                        form_multiplier = $7, fixture_multiplier = $8, 
                        starter_multiplier = $9,
                        last_updated = CURRENT_TIMESTAMP
                """,
                params=[
                    player['id'], gameweek, player['price'], player['ppg'],
                    player['value_score'], player['true_value'],
                    player.get('form_multiplier', 1.0),
                    player.get('fixture_multiplier', 1.0),
                    player.get('starter_multiplier', 1.0)
                ]
            )
    
    async def get_player_form(self, player_id: str, lookback: int = 3):
        """Get historical form data for a player"""
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

# Helper function for sync Flask routes
def run_async(coro):
    """Run async database calls in sync Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
```

---

## 🚀 Migration Scripts

### migrations/001_create_schema.py
```python
import asyncio

async def create_database():
    """Create database and tables"""
    
    # First connect as admin to create database
    await mcp__database__connect_db(
        host="localhost",
        user="postgres",
        password="admin_password", 
        database="postgres",
        port=5432
    )
    
    # Create database (PostgreSQL doesn't support IF NOT EXISTS in CREATE DATABASE)
    try:
        await mcp__database__execute(sql="CREATE DATABASE fantrax_value_hunter")
        print("[SUCCESS] Database created")
    except Exception as e:
        if "already exists" in str(e):
            print("[INFO] Database already exists")
        else:
            raise
    
    # Reconnect to new database
    await mcp__database__connect_db(
        host="localhost",
        user="fantrax_user",
        password="your_password",
        database="fantrax_value_hunter",
        port=5432
    )
    
    # Create tables
    tables = [
        """CREATE TABLE IF NOT EXISTS players (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            team VARCHAR(5),
            position VARCHAR(10),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS player_form (
            player_id VARCHAR(10) REFERENCES players(id),
            gameweek INT NOT NULL,
            points DECIMAL(6,2),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, gameweek)
        )""",
        
        """CREATE TABLE IF NOT EXISTS player_metrics (
            player_id VARCHAR(10) REFERENCES players(id),
            gameweek INT NOT NULL,
            price DECIMAL(6,2),
            ppg DECIMAL(6,2),
            ppg_source VARCHAR(20),
            value_score DECIMAL(8,3),
            true_value DECIMAL(8,3),
            form_multiplier DECIMAL(4,3) DEFAULT 1.0,
            fixture_multiplier DECIMAL(4,3) DEFAULT 1.0,
            starter_multiplier DECIMAL(4,3) DEFAULT 1.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, gameweek)
        )"""
    ]
    
    for table_sql in tables:
        await mcp__database__execute(sql=table_sql)
        
    print("[SUCCESS] All tables created")
    
    # Verify tables
    tables = await mcp__database__list_tables()
    print(f"[INFO] Database has {len(tables)} tables")

if __name__ == "__main__":
    asyncio.run(create_database())
```

### migrations/002_import_data.py
```python
import json
import asyncio

async def import_existing_data():
    """Import JSON data to database"""
    
    # Connect to database
    await mcp__database__connect_db(
        host="localhost",
        user="fantrax_user",
        password="your_password",
        database="fantrax_value_hunter",
        port=5432
    )
    
    # Load candidate pools
    with open('../data/candidate_pools.json', 'r') as f:
        data = json.load(f)
    
    gameweek = data['metadata']['gameweek']
    imported_count = 0
    
    # Import each position's players
    for position, players in data['pools'].items():
        for player in players:
            # Insert player
            await mcp__database__execute(
                sql="""
                    INSERT INTO players (id, name, team, position)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                        name = $2, team = $3, position = $4
                """,
                params=[
                    player['id'], 
                    player['name'],
                    player['team'], 
                    player['position']
                ]
            )
            
            # Insert metrics
            await mcp__database__execute(
                sql="""
                    INSERT INTO player_metrics
                    (player_id, gameweek, price, ppg, ppg_source, 
                     value_score, true_value, form_multiplier,
                     fixture_multiplier, starter_multiplier)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                params=[
                    player['id'], gameweek, player['price'],
                    player['ppg'], player.get('ppg_source', 'Estimated'),
                    player['value_score'], player['true_value'],
                    player.get('form_multiplier', 1.0),
                    player.get('fixture_multiplier', 1.0),
                    player.get('starter_multiplier', 1.0)
                ]
            )
            imported_count += 1
    
    print(f"[SUCCESS] Imported {imported_count} players for gameweek {gameweek}")
    
    # Import baseline form data if available
    try:
        with open('../data/season_2024_baseline.json', 'r') as f:
            baseline = json.load(f)
            
        for player_id, player_data in baseline.get('players', {}).items():
            if 'season_average_2024' in player_data:
                # Store as gameweek 0 for baseline reference
                await mcp__database__execute(
                    sql="""
                        INSERT INTO player_form (player_id, gameweek, points)
                        VALUES ($1, 0, $2)
                        ON CONFLICT (player_id, gameweek) DO NOTHING
                    """,
                    params=[player_id, player_data['season_average_2024']]
                )
        
        print(f"[SUCCESS] Imported baseline data for {len(baseline.get('players', {}))} players")
        
    except FileNotFoundError:
        print("[INFO] No baseline data to import")

if __name__ == "__main__":
    asyncio.run(import_existing_data())
```

---

## 🔑 Key Database MCP Patterns

### Pattern 1: Simple Query
```python
# Get top goalkeepers
result = await mcp__database__query(
    sql="SELECT * FROM players WHERE position = $1 ORDER BY true_value DESC LIMIT $2",
    params=["G", 8]
)
```

### Pattern 2: Bulk Update
```python
# Update all metrics after recalculation
for player in recalculated_players:
    await mcp__database__execute(
        sql="UPDATE player_metrics SET true_value = $2 WHERE player_id = $1 AND gameweek = $3",
        params=[player['id'], player['true_value'], current_gameweek]
    )
```

### Pattern 3: Form Calculation Query
```python
# Get last 3 games for form calculation
form_data = await mcp__database__query(
    sql="""
        SELECT gameweek, points 
        FROM player_form 
        WHERE player_id = $1 
        ORDER BY gameweek DESC 
        LIMIT $2
    """,
    params=[player_id, 3]
)
```

---

## ⚡ PostgreSQL Setup (Windows/Mac/Linux)

### Windows
1. Download installer from postgresql.org
2. Run installer, set password for postgres user
3. Add to PATH if not done automatically
4. Open pgAdmin or psql to create database

### Mac
```bash
brew install postgresql
brew services start postgresql
psql postgres
CREATE USER fantrax_user WITH PASSWORD 'your_password';
CREATE DATABASE fantrax_value_hunter OWNER fantrax_user;
```

### Linux
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres psql
CREATE USER fantrax_user WITH PASSWORD 'your_password';
CREATE DATABASE fantrax_value_hunter OWNER fantrax_user;
```

---

## ✅ Why This Approach is Better

1. **No ORM Learning Curve**: Direct SQL queries, no model classes
2. **Connection Pooling Handled**: MCP manages this automatically
3. **Type Safety**: Parameterized queries prevent SQL injection
4. **Async Support**: Modern Python async/await pattern
5. **Simple Testing**: Can query directly during development

---

## 🚨 Common Gotchas & Solutions

### Issue: "Database does not exist"
```python
# Solution: Create it first
CREATE DATABASE fantrax_value_hunter;
```

### Issue: "Permission denied"
```python
# Solution: Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fantrax_value_hunter TO fantrax_user;
```

### Issue: Async in sync Flask routes
```python
# Solution: Use the helper function
from db_manager import run_async
result = run_async(db.get_candidate_pools(gameweek=1))
```

---

## 📝 Testing Database Connection

```python
# Quick test script
import asyncio

async def test_connection():
    result = await mcp__database__connect_db(
        host="localhost",
        user="fantrax_user",
        password="your_password",
        database="fantrax_value_hunter",
        port=5432
    )
    print("Connected:", result)
    
    tables = await mcp__database__list_tables()
    print("Tables:", tables)

asyncio.run(test_connection())
```

---

## 📊 Integration with Existing Code

Your `candidate_analyzer.py` needs minimal changes:

```python
# Old: Load from JSON
with open('../data/candidate_pools.json', 'r') as f:
    data = json.load(f)

# New: Load from database
from db_manager import DatabaseManager, run_async
db = DatabaseManager()
run_async(db.connect())
data = run_async(db.get_candidate_pools(gameweek=1))
```

---

This guide eliminates the Database MCP learning curve - it's just SQL queries through function calls!