import psycopg2
import sys
import os
sys.path.append(os.path.dirname(os.path.join(os.path.dirname(__file__), 'src')))
from src.gameweek_manager import GameweekManager

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

print(f'=== VERIFICATION RESULTS (Gameweek {current_gameweek}) ===')
print()

# Check games tracking
cursor.execute("""
    SELECT p.name, pgd.games_played, pgd.games_played_historical, pm.price
    FROM players p 
    JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = %s
    JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = %s
    WHERE p.name LIKE %s OR p.name LIKE %s OR p.name LIKE %s
    ORDER BY p.name
""", (current_gameweek, current_gameweek, '%Haaland%', '%Salah%', '%Palmer%'))

print('Games & Price Tracking:')
print('Player               | Current | Historical | Price')
print('-' * 55)
for name, current, historical, price in cursor.fetchall():
    print(f'{name:20} | {current:7} | {historical:10} | ${price}')

print()
print('Overall Statistics:')
# Total imports
cursor.execute('SELECT COUNT(*) FROM player_form WHERE gameweek = %s', (current_gameweek,))
form_count = cursor.fetchone()[0]
print(f'Form records imported: {form_count}')

cursor.execute('SELECT COUNT(*) FROM player_games_data WHERE gameweek = %s AND games_played > 0', (current_gameweek,))
games_count = cursor.fetchone()[0] 
print(f'Players with games played: {games_count}')

cursor.execute('SELECT COUNT(*) FROM player_metrics WHERE gameweek = %s AND price IS NOT NULL', (current_gameweek,))
price_count = cursor.fetchone()[0]
print(f'Players with price data: {price_count}')

conn.close()