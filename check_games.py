import psycopg2
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from gameweek_manager import GameweekManager

# Get current gameweek using GameweekManager
gw_manager = GameweekManager()
current_gameweek = gw_manager.get_current_gameweek()

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    user='fantrax_user', 
    password='fantrax_password', 
    database='fantrax_value_hunter'
)
cursor = conn.cursor()

print(f"Games tracking analysis (Gameweek {current_gameweek}):")
print("-" * 60)

# Check how many games players have played in current season
cursor.execute("""
    SELECT p.name, 
           COUNT(DISTINCT pf.gameweek) as current_games,
           pgd.games_played as stored_current,
           pgd.games_played_historical as historical
    FROM players p
    LEFT JOIN player_form pf ON p.id = pf.player_id
    LEFT JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = %s
    WHERE p.name IN ('Erling Haaland', 'Mohamed Salah', 'Cole Palmer')
    GROUP BY p.name, pgd.games_played, pgd.games_played_historical
""", (current_gameweek,))

for name, current_actual, stored_current, historical in cursor.fetchall():
    print(f"{name:20} | Actual: {current_actual} | Stored: {stored_current or 0} | Historical: {historical or 0}")

cursor.close()
conn.close()