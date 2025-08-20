import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    user='fantrax_user', 
    password='fantrax_password', 
    database='fantrax_value_hunter'
)
cursor = conn.cursor()

# Check how many games players have played in current season
cursor.execute("""
    SELECT p.name, 
           COUNT(DISTINCT pf.gameweek) as current_games,
           pgd.games_played as stored_current,
           pgd.games_played_historical as historical
    FROM players p
    LEFT JOIN player_form pf ON p.id = pf.player_id
    LEFT JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = 1
    WHERE p.name IN ('Erling Haaland', 'Mohamed Salah', 'Cole Palmer')
    GROUP BY p.name, pgd.games_played, pgd.games_played_historical
""")

print("Games tracking analysis:")
print("-" * 60)
for name, current_actual, stored_current, historical in cursor.fetchall():
    print(f"{name:20} | Actual: {current_actual} | Stored: {stored_current or 0} | Historical: {historical or 0}")

cursor.close()
conn.close()