"""
Trend Analysis API Endpoints
To be integrated into main app.py

These endpoints provide access to the raw data snapshot system
and retrospective calculation engine for trend analysis.
"""

# Add these imports to app.py:
# from trend_analysis_engine import TrendAnalysisEngine

# Add these endpoints before if __name__ == '__main__':

# ===============================
# TREND ANALYSIS API ENDPOINTS
# ===============================

@app.route('/api/trends/calculate', methods=['POST'])
def calculate_trends():
    """
    Calculate historical trends using raw data with specified parameters
    
    Expected JSON:
    {
        "player_ids": ["player1", "player2"] or null for all,
        "gameweek_start": 1,
        "gameweek_end": 5,
        "parameters": {...} or null for current parameters
    }
    """
    try:
        data = request.get_json()
        
        # Extract parameters
        player_ids = data.get('player_ids')  # None = all players
        gameweek_start = data.get('gameweek_start', 1)
        gameweek_end = data.get('gameweek_end')
        parameters = data.get('parameters')  # None = current parameters
        
        # Get current max gameweek if end not specified
        if gameweek_end is None:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(gameweek) FROM raw_player_snapshots")
            result = cursor.fetchone()
            gameweek_end = result[0] if result and result[0] else 1
            cursor.close()
            conn.close()
        
        # Validate input
        if gameweek_start < 1 or gameweek_end < gameweek_start:
            return jsonify({
                'success': False,
                'error': 'Invalid gameweek range'
            }), 400
        
        # Calculate trends using raw data
        engine = TrendAnalysisEngine(DB_CONFIG)
        trends = engine.calculate_historical_trends(
            gameweek_start, gameweek_end, parameters, player_ids
        )
        
        return jsonify({
            'success': True,
            'trends': trends,
            'gameweek_range': [gameweek_start, gameweek_end],
            'player_count': len(set(t['player_id'] for t in trends)),
            'parameters_used': parameters or 'current_system_parameters'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Trend calculation failed: {str(e)}'
        }), 500

@app.route('/api/trends/player/<player_id>', methods=['GET'])
def get_player_trends(player_id):
    """
    Get trend data for a specific player
    
    Query parameters:
    - gameweek_start: Starting gameweek (default: 1)
    - gameweek_end: Ending gameweek (default: current max)
    - parameters: 'current' or JSON string of custom parameters
    """
    try:
        # Get query parameters
        gameweek_start = request.args.get('gameweek_start', 1, type=int)
        gameweek_end = request.args.get('gameweek_end', type=int)
        parameters_param = request.args.get('parameters', 'current')
        
        # Parse parameters
        if parameters_param == 'current':
            parameters = None  # Use current system parameters
        else:
            try:
                parameters = json.loads(parameters_param)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameters JSON'
                }), 400
        
        # Get current max gameweek if end not specified
        if gameweek_end is None:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(gameweek) FROM raw_player_snapshots")
            result = cursor.fetchone()
            gameweek_end = result[0] if result and result[0] else 1
            cursor.close()
            conn.close()
        
        # Calculate player trends
        engine = TrendAnalysisEngine(DB_CONFIG)
        trends = engine.calculate_historical_trends(
            gameweek_start, gameweek_end, parameters, [player_id]
        )
        
        if not trends:
            return jsonify({
                'success': False,
                'error': f'No trend data found for player {player_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'player_id': player_id,
            'trends': trends,
            'gameweek_range': [gameweek_start, gameweek_end],
            'data_points': len(trends)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Player trends failed: {str(e)}'
        }), 500

@app.route('/api/trends/raw-data/status', methods=['GET'])
def get_raw_data_status():
    """
    Get status of raw data snapshots - how much data is captured
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get snapshot statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_snapshots,
                COUNT(DISTINCT player_id) as players_with_data,
                COUNT(DISTINCT gameweek) as gameweeks_with_data,
                MIN(gameweek) as earliest_gw,
                MAX(gameweek) as latest_gw,
                COUNT(*) FILTER (WHERE fantrax_import = TRUE) as fantrax_snapshots,
                COUNT(*) FILTER (WHERE understat_import = TRUE) as understat_snapshots,
                COUNT(*) FILTER (WHERE odds_import = TRUE) as odds_snapshots,
                COUNT(*) FILTER (WHERE lineup_import = TRUE) as lineup_snapshots,
                MAX(import_timestamp) as latest_import
            FROM raw_player_snapshots
        """)
        
        player_stats = dict(cursor.fetchone())
        
        # Get fixture data status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_fixtures,
                COUNT(DISTINCT gameweek) as gameweeks_with_fixtures,
                COUNT(DISTINCT team) as teams_with_fixtures,
                MAX(import_timestamp) as latest_fixture_import
            FROM raw_fixture_snapshots
        """)
        
        fixture_stats = dict(cursor.fetchone())
        
        # Get form data status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_form_records,
                COUNT(DISTINCT player_id) as players_with_form,
                COUNT(DISTINCT gameweek) as gameweeks_with_form,
                AVG(points_scored) as avg_points_per_record
            FROM raw_form_snapshots
        """)
        
        form_stats = dict(cursor.fetchone())
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'player_snapshots': player_stats,
            'fixture_snapshots': fixture_stats,
            'form_snapshots': form_stats,
            'system_ready': (
                player_stats['total_snapshots'] > 0 and 
                fixture_stats['total_fixtures'] > 0 and
                form_stats['total_form_records'] > 0
            )
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500

@app.route('/api/trends/migrate-existing-data', methods=['POST'])
def migrate_existing_data():
    """
    UTILITY: Migrate existing GW1 data to raw snapshots
    This helps populate the system with historical data that was imported before raw capture
    """
    try:
        # Get existing data from current tables
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        migrated_players = 0
        migrated_fixtures = 0
        migrated_form = 0
        
        # Migrate player data from player_form + player_metrics 
        cursor.execute("""
            SELECT 
                pf.player_id,
                pf.gameweek,
                p.name,
                p.team,
                p.position,
                pm.price,
                pf.points as fpts,
                0 as minutes_played,
                p.xg90,
                p.xa90,
                p.xgi90,
                p.baseline_xgi,
                p.historical_ppg
            FROM player_form pf
            JOIN players p ON pf.player_id = p.id
            LEFT JOIN player_metrics pm ON pf.player_id = pm.player_id AND pf.gameweek = pm.gameweek
            WHERE NOT EXISTS (
                SELECT 1 FROM raw_player_snapshots rps 
                WHERE rps.player_id = pf.player_id AND rps.gameweek = pf.gameweek
            )
        """)
        
        existing_data = cursor.fetchall()
        
        for row in existing_data:
            cursor.execute("""
                INSERT INTO raw_player_snapshots 
                (player_id, gameweek, name, team, position, price, fpts, minutes_played,
                 xg90, xa90, xgi90, baseline_xgi, historical_ppg, fantrax_import, understat_import)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)
                ON CONFLICT (player_id, gameweek) DO NOTHING
            """, [
                row['player_id'], row['gameweek'], row['name'], row['team'], 
                row['position'], row['price'], row['fpts'], row['minutes_played'],
                row['xg90'], row['xa90'], row['xgi90'], row['baseline_xgi'],
                row['historical_ppg']
            ])
            if cursor.rowcount > 0:
                migrated_players += 1
        
        # Migrate form data
        cursor.execute("""
            INSERT INTO raw_form_snapshots (player_id, gameweek, points_scored, games_played)
            SELECT player_id, gameweek, points, 
                   CASE WHEN points > 0 THEN 1 ELSE 0 END
            FROM player_form
            WHERE NOT EXISTS (
                SELECT 1 FROM raw_form_snapshots rfs 
                WHERE rfs.player_id = player_form.player_id 
                AND rfs.gameweek = player_form.gameweek
            )
            ON CONFLICT (player_id, gameweek) DO NOTHING
        """)
        migrated_form = cursor.rowcount
        
        # Migrate fixture data
        cursor.execute("""
            INSERT INTO raw_fixture_snapshots 
            (gameweek, team, opponent, is_home, difficulty_score, odds_source)
            SELECT gameweek, team_code, opponent_code, is_home, difficulty_score, 'migrated'
            FROM team_fixtures
            WHERE NOT EXISTS (
                SELECT 1 FROM raw_fixture_snapshots rfs 
                WHERE rfs.gameweek = team_fixtures.gameweek 
                AND rfs.team = team_fixtures.team_code
            )
            ON CONFLICT (gameweek, team) DO NOTHING
        """)
        migrated_fixtures = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Data migration completed',
            'migrated_players': migrated_players,
            'migrated_fixtures': migrated_fixtures,
            'migrated_form': migrated_form
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Migration failed: {str(e)}'
        }), 500