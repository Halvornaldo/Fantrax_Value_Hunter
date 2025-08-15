"""
Flask Backend for Fantrax Value Hunter Dashboard
Provides API endpoints for parameter adjustment and True Value recalculation
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import json
import os
from typing import Dict, List, Optional, Any
import time

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'fantrax_user',
    'password': 'fantrax_password',
    'database': 'fantrax_value_hunter'
}

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def load_system_parameters():
    """Load system parameters from config file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_parameters.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading system parameters: {e}")
        return {}

def save_system_parameters(parameters: Dict):
    """Save updated system parameters to config file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_parameters.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(parameters, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving system parameters: {e}")
        return False

def calculate_form_multiplier(player_id: str, current_gameweek: int, lookback_period: int = 3):
    """
    Calculate weighted form multiplier using historical data from player_form table
    Returns 1.0 if insufficient data (early season)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get form data for lookback period
        start_gw = max(1, current_gameweek - lookback_period + 1)
        cursor.execute("""
            SELECT points FROM player_form 
            WHERE player_id = %s 
            AND gameweek BETWEEN %s AND %s
            ORDER BY gameweek DESC
        """, [player_id, start_gw, current_gameweek])
        
        form_data = cursor.fetchall()
        
        # If insufficient data, return neutral multiplier
        if len(form_data) < 2:
            return 1.0
            
        # Apply weighted average based on lookback period
        if lookback_period == 3:
            weights = [0.5, 0.3, 0.2]
        else:  # 5 games
            weights = [0.4, 0.25, 0.2, 0.1, 0.05]
            
        # Calculate weighted average
        weighted_sum = 0
        weight_total = 0
        for i, row in enumerate(form_data):
            if i < len(weights):
                weighted_sum += row['points'] * weights[i]
                weight_total += weights[i]
                
        if weight_total == 0:
            return 1.0
            
        weighted_avg = weighted_sum / weight_total
        
        # Get player's season average for comparison
        cursor.execute("""
            SELECT AVG(points) as season_avg FROM player_form 
            WHERE player_id = %s
        """, [player_id])
        
        result = cursor.fetchone()
        season_avg = result['season_avg'] if result and result['season_avg'] else weighted_avg
        
        # Convert to multiplier (constrained between 0.5x and 1.5x)
        if season_avg > 0:
            form_multiplier = weighted_avg / season_avg
            return max(0.5, min(1.5, form_multiplier))
        
        return 1.0
        
    finally:
        conn.close()

def recalculate_true_values(gameweek: int = 1):
    """
    Recalculate True Value for all players based on current parameters
    TrueValue = (PPG ÷ Price) × Form × Fixture × Starter
    """
    start_time = time.time()
    
    params = load_system_parameters()
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get all players with current metrics
        cursor.execute("""
            SELECT p.id, p.name, p.team, p.position,
                   pm.price, pm.ppg, pm.value_score,
                   pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.gameweek = %s
        """, [gameweek])
        
        players = cursor.fetchall()
        updated_count = 0
        
        for player in players:
            # Calculate form multiplier if enabled
            form_mult = 1.0
            if params.get('form_calculation', {}).get('enabled', False):
                lookback = params['form_calculation'].get('lookback_period', 3)
                form_mult = calculate_form_multiplier(player['id'], gameweek, lookback)
            
            # Fixture and starter multipliers come from external systems (default 1.0)
            fixture_mult = float(player.get('fixture_multiplier', 1.0))
            starter_mult = float(player.get('starter_multiplier', 1.0))
            
            # Calculate True Value: (PPG ÷ Price) × Form × Fixture × Starter
            ppg = float(player['ppg']) if player['ppg'] else 0
            price = float(player['price']) if player['price'] else 0
            base_value = ppg / price if price > 0 else 0
            true_value = base_value * form_mult * fixture_mult * starter_mult
            
            # Update player metrics
            cursor.execute("""
                UPDATE player_metrics 
                SET value_score = %s, 
                    true_value = %s,
                    form_multiplier = %s,
                    fixture_multiplier = %s,
                    starter_multiplier = %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE player_id = %s AND gameweek = %s
            """, [base_value, true_value, form_mult, fixture_mult, starter_mult, 
                  player['id'], gameweek])
            
            updated_count += 1
        
        conn.commit()
        
        elapsed_time = time.time() - start_time
        print(f"Recalculated True Values for {updated_count} players in {elapsed_time:.2f}s")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'elapsed_time': elapsed_time
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error recalculating True Values: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()

@app.route('/')
def dashboard():
    """Main dashboard UI"""
    return render_template('dashboard.html')

@app.route('/api/players', methods=['GET'])
def get_players():
    """
    Get all 633 players with filtering options
    Query parameters: position, min_price, max_price, team, search
    """
    start_time = time.time()
    
    # Parse query parameters
    position = request.args.get('position')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    team = request.args.get('team')
    search = request.args.get('search', '').strip()
    gameweek = request.args.get('gameweek', 1, type=int)
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build dynamic query
        base_query = """
            SELECT 
                p.id, p.name, p.team, p.position,
                pm.price, pm.ppg, pm.value_score, pm.true_value,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier,
                pm.last_updated
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.gameweek = %s
        """
        
        params = [gameweek]
        conditions = []
        
        # Add filters
        if position:
            conditions.append("p.position = %s")
            params.append(position)
            
        if min_price is not None:
            conditions.append("pm.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("pm.price <= %s")
            params.append(max_price)
            
        if team:
            conditions.append("p.team = %s")
            params.append(team)
            
        if search:
            conditions.append("p.name ILIKE %s")
            params.append(f"%{search}%")
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
            
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as filtered"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        
        # Add ordering and pagination
        final_query = base_query + " ORDER BY pm.true_value DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(final_query, params)
        players = cursor.fetchall()
        
        # Convert to list of dicts for JSON serialization
        players_list = []
        for player in players:
            player_dict = dict(player)
            # Convert any datetime objects to strings
            if player_dict.get('last_updated'):
                player_dict['last_updated'] = player_dict['last_updated'].isoformat()
            players_list.append(player_dict)
        
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'players': players_list,
            'total_count': total_count,
            'filtered_count': len(players_list),
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            },
            'query_time': elapsed_time,
            'filters_applied': {
                'position': position,
                'min_price': min_price,
                'max_price': max_price,
                'team': team,
                'search': search,
                'gameweek': gameweek
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current system parameters"""
    try:
        parameters = load_system_parameters()
        return jsonify({
            'success': True,
            'parameters': parameters
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update-parameters', methods=['POST'])
def update_parameters():
    """
    Update system parameters and trigger True Value recalculation
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Load current parameters
        current_params = load_system_parameters()
        
        # Update parameters based on request
        if 'form_calculation' in data:
            current_params['form_calculation'].update(data['form_calculation'])
            
        if 'fixture_difficulty' in data:
            if '5_tier_multipliers' in data['fixture_difficulty']:
                current_params['fixture_difficulty']['5_tier_multipliers'].update(
                    data['fixture_difficulty']['5_tier_multipliers']
                )
            if '3_tier_multipliers' in data['fixture_difficulty']:
                current_params['fixture_difficulty']['3_tier_multipliers'].update(
                    data['fixture_difficulty']['3_tier_multipliers']
                )
                
        if 'starter_prediction' in data:
            current_params['starter_prediction'].update(data['starter_prediction'])
        
        # Save updated parameters
        if not save_system_parameters(current_params):
            return jsonify({'error': 'Failed to save parameters'}), 500
        
        # Trigger True Value recalculation
        gameweek = data.get('gameweek', 1)
        recalc_result = recalculate_true_values(gameweek)
        
        if not recalc_result['success']:
            return jsonify({
                'error': 'Parameter update succeeded but recalculation failed',
                'recalc_error': recalc_result.get('error')
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Parameters updated and True Values recalculated',
            'updated_players': recalc_result['updated_count'],
            'calculation_time': recalc_result['elapsed_time']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'player_count': player_count,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': time.time()
        }), 500

if __name__ == '__main__':
    print("Starting Fantrax Value Hunter Flask Backend...")
    print(f"Database: {DB_CONFIG['database']} on port {DB_CONFIG['port']}")
    
    # Test database connection on startup
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        print(f"Database connected: {player_count} players loaded")
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {e}")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5000)