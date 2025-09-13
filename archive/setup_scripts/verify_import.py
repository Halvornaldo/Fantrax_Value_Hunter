import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    user='fantrax_user', 
    password='fantrax_password', 
    database='fantrax_value_hunter'
)
cursor = conn.cursor()

print('=== VERIFICATION RESULTS ===')
print()

# Check games tracking
cursor.execute("""
    SELECT p.name, pgd.games_played, pgd.games_played_historical, pm.price
    FROM players p 
    JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = 1
    JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = 1
    WHERE p.name LIKE %s OR p.name LIKE %s OR p.name LIKE %s
    ORDER BY p.name
""", ('%Haaland%', '%Salah%', '%Palmer%'))

print('Games & Price Tracking:')
print('Player               | Current | Historical | Price')
print('-' * 55)
for name, current, historical, price in cursor.fetchall():
    print(f'{name:20} | {current:7} | {historical:10} | ${price}')

print()
print('Overall Statistics:')
# Total imports
cursor.execute('SELECT COUNT(*) FROM player_form WHERE gameweek = 1')
form_count = cursor.fetchone()[0]
print(f'Form records imported: {form_count}')

cursor.execute('SELECT COUNT(*) FROM player_games_data WHERE gameweek = 1 AND games_played > 0')
games_count = cursor.fetchone()[0] 
print(f'Players with games_played = 1: {games_count}')

cursor.execute('SELECT COUNT(*) FROM player_metrics WHERE gameweek = 1 AND price IS NOT NULL')
price_count = cursor.fetchone()[0]
print(f'Players with price data: {price_count}')

conn.close()