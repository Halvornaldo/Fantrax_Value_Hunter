"""
Flask Backend for Fantrax Value Hunter Dashboard
Provides API endpoints for parameter adjustment and True Value recalculation
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
import psycopg2
import psycopg2.extras
import json
import os
from typing import Dict, List, Optional, Any
import time
import sys
from datetime import datetime

# Add name_matching module to path
sys.path.append(os.path.dirname(__file__))
from name_matching import UnifiedNameMatcher

# Add integration package to path (optional for production)
try:
    sys.path.append('C:/Users/halvo/.claude/Fantrax_Expected_Stats')
    from integration_package import IntegrationPipeline, UnderstatIntegrator, ValueHunterExtension
    INTEGRATION_AVAILABLE = True
except ImportError:
    # Integration package not available in production - disable related features
    INTEGRATION_AVAILABLE = False
    print("Integration package not available - running in production mode")

# Add v2.0 calculation engine
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from calculation_engine_v2 import FormulaEngineV2

# Add trend analysis engine
from trend_analysis_engine import TrendAnalysisEngine

# Configure Flask to serve React frontend
frontend_build_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
app = Flask(__name__, 
            template_folder='../templates',
            static_folder=frontend_build_dir,
            static_url_path='')
# Enable CORS with specific configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True
    }
})

# Configure caching for performance optimization
app.config['CACHE_TYPE'] = 'simple'  # Simple in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 60  # Cache for 60 seconds
cache = Cache(app)

# Database configuration - supports both local and production environments
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', 5433)),
    'user': os.getenv('PGUSER', 'fantrax_user'),
    'password': os.getenv('PGPASSWORD', 'fantrax_password'),
    'database': os.getenv('PGDATABASE', 'fantrax_value_hunter')
}

# Alternative: use DATABASE_URL if provided (Railway format)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Railway provides DATABASE_URL in format: postgresql://user:pass@host:port/db
    import urllib.parse
    result = urllib.parse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': result.hostname,
        'port': result.port,
        'user': result.username,
        'password': result.password,
        'database': result.path[1:]  # Remove leading slash
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

def get_data_freshness_info(gameweek: int) -> Dict:
    """Get detailed data freshness information for monitoring"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        freshness_info = {
            'gameweek': gameweek,
            'last_updated': {},
            'record_counts': {},
            'data_completeness': {}
        }
        
        # Check player_metrics freshness
        cursor.execute("""
            SELECT 
                MAX(last_updated) as latest_update,
                COUNT(*) as record_count
            FROM player_metrics 
            WHERE gameweek = %s
        """, (gameweek,))
        metrics_data = cursor.fetchone()
        
        if metrics_data:
            freshness_info['last_updated']['player_metrics'] = metrics_data['latest_update'].isoformat() if metrics_data['latest_update'] else None
            freshness_info['record_counts']['player_metrics'] = metrics_data['record_count']
        
        # Check player_form freshness
        cursor.execute("""
            SELECT 
                MAX(last_updated) as latest_update,
                COUNT(*) as record_count
            FROM player_form 
            WHERE gameweek = %s
        """, (gameweek,))
        form_data = cursor.fetchone()
        
        if form_data:
            freshness_info['last_updated']['player_form'] = form_data['latest_update'].isoformat() if form_data['latest_update'] else None
            freshness_info['record_counts']['player_form'] = form_data['record_count']
        
        # Check raw_player_snapshots freshness
        cursor.execute("""
            SELECT 
                MAX(created_at) as latest_update,
                COUNT(*) as record_count
            FROM raw_player_snapshots 
            WHERE gameweek = %s
        """, (gameweek,))
        raw_data = cursor.fetchone()
        
        if raw_data:
            freshness_info['last_updated']['raw_snapshots'] = raw_data['latest_update'].isoformat() if raw_data['latest_update'] else None
            freshness_info['record_counts']['raw_snapshots'] = raw_data['record_count']
        
        # Calculate data completeness percentages
        expected_player_count = 647  # Premier League players
        for table, count in freshness_info['record_counts'].items():
            if count:
                freshness_info['data_completeness'][table] = round((count / expected_player_count) * 100, 1)
        
        return freshness_info
        
    except Exception as e:
        return {
            'error': f'Failed to get data freshness info: {str(e)}',
            'gameweek': gameweek
        }
    finally:
        conn.close()

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
                weighted_sum += float(row['points']) * weights[i]
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
        season_avg = float(result['season_avg']) if result and result['season_avg'] else weighted_avg
        
        # Convert to multiplier (constrained between 0.5x and 1.5x)
        if season_avg > 0:
            form_multiplier = weighted_avg / season_avg
            return max(0.5, min(1.5, form_multiplier))
        
        return 1.0
        
    finally:
        conn.close()

def calculate_fixture_difficulty_multiplier(team_code: str, position: str, gameweek: int, params: dict):
    """
    Calculate fixture difficulty multiplier based on odds data and position weights
    Returns 1.0 if no fixture data available
    """
    # Check if fixture difficulty is enabled
    fixture_config = params.get('fixture_difficulty', {})
    if not fixture_config.get('enabled', False):
        return 1.0
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get fixture difficulty score for this team and gameweek
        cursor.execute("""
            SELECT difficulty_score FROM team_fixtures 
            WHERE team_code = %s AND gameweek = %s
        """, [team_code, gameweek])
        
        result = cursor.fetchone()
        if not result:
            return 1.0  # No fixture data available
            
        difficulty_score = float(result['difficulty_score'])
        
        # Get base multiplier strength from parameters
        base_strength = fixture_config.get('multiplier_strength', 0.2)  # Default 20%
        
        # Apply position-specific weights
        position_weights = fixture_config.get('position_weights', {
            'G': 1.10,  # Goalkeepers: 110% (more saves vs stronger teams)
            'D': 1.20,  # Defenders: 120% (clean sheets vs weaker teams)
            'M': 1.00,  # Midfielders: 100% (baseline)
            'F': 1.05   # Forwards: 105% (goals vs weaker teams)
        })
        
        position_weight = position_weights.get(position, 1.0)
        
        # Convert difficulty score (-10 to +10) to multiplier
        # Negative scores = easier fixtures = higher multiplier
        # Positive scores = harder fixtures = lower multiplier
        multiplier_adjustment = (difficulty_score / 10.0) * base_strength * position_weight
        
        # Final multiplier: 1.0 + adjustment (constrained between 0.5x and 1.5x)
        final_multiplier = 1.0 - multiplier_adjustment
        return max(0.5, min(1.5, final_multiplier))
        
    except Exception as e:
        print(f"Error calculating fixture difficulty for {team_code}: {e}")
        return 1.0
    finally:
        conn.close()

def calculate_fixture_difficulty_multiplier_cached(team_code: str, position: str, params: dict, fixture_cache: dict):
    """
    OPTIMIZED: Calculate fixture difficulty multiplier using cached fixture data
    No database queries - uses pre-loaded fixture_cache dictionary
    """
    # Check if fixture difficulty is enabled
    fixture_config = params.get('fixture_difficulty', {})
    if not fixture_config.get('enabled', False):
        return 1.0
    
    # Get difficulty score from cache
    difficulty_score = fixture_cache.get(team_code)
    if difficulty_score is None:
        return 1.0  # No fixture data available
    
    # Get base multiplier strength from parameters
    base_strength = fixture_config.get('multiplier_strength', 0.2)  # Default 20%
    
    # Apply position-specific weights
    position_weights = fixture_config.get('position_weights', {
        'G': 1.10,  # Goalkeepers: 110% (more saves vs stronger teams)
        'D': 1.20,  # Defenders: 120% (clean sheets vs weaker teams)
        'M': 1.00,  # Midfielders: 100% (baseline)
        'F': 1.05   # Forwards: 105% (goals vs weaker teams)
    })
    
    position_weight = position_weights.get(position, 1.0)
    
    # Convert difficulty score (-10 to +10) to multiplier
    # Negative scores = easier fixtures = higher multiplier
    # Positive scores = harder fixtures = lower multiplier
    multiplier_adjustment = (difficulty_score / 10.0) * base_strength * position_weight
    
    # Final multiplier: 1.0 + adjustment (constrained between 0.5x and 1.5x)
    final_multiplier = 1.0 - multiplier_adjustment
    return max(0.5, min(1.5, final_multiplier))

def recalculate_true_values(gameweek: int = None):
    """
    Recalculate True Value for all players using v2.0 Enhanced Formula
    TrueValue = Blended_PPG × Form × Fixture × Starter × xGI
    ROI = TrueValue ÷ Price
    """
    start_time = time.time()
    
    # Use GameweekManager if no gameweek specified
    if gameweek is None:
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        gameweek = gw_manager.get_current_gameweek()
    
    params = load_system_parameters()
    
    # Use v2.0 calculation engine exclusively
    try:
        from calculation_engine_v2 import FormulaEngineV2
        
        # Initialize v2.0 engine
        v2_engine = FormulaEngineV2(DB_CONFIG, params)
        
        # Get all players with enhanced data for v2.0
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Enhanced query for v2.0 with all required data
        cursor.execute("""
            SELECT 
                p.id as player_id, p.name, p.team, p.position,
                pm.price, 
                COALESCE(pf.total_points, 0) as total_fpts,
                CASE 
                    WHEN COALESCE(pgd.games_played_current, 0) > 0 
                    THEN COALESCE(pf.total_points, 0) / pgd.games_played_current
                    ELSE 0 
                END as ppg, 
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier,
                p.xgi90, p.baseline_xgi,
                pgd.total_points_historical, pgd.games_played_historical,
                pgd.total_points_current, pgd.games_played_current,
                tf.difficulty_score as fixture_difficulty
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            LEFT JOIN (
                SELECT player_id, 
                       SUM(games_played) as games_played_current,
                       MAX(games_played_historical) as games_played_historical,
                       MAX(total_points_historical) as total_points_historical,
                       SUM(total_points) as total_points_current,
                       MAX(data_source) as data_source
                FROM player_games_data 
                GROUP BY player_id
            ) pgd ON p.id = pgd.player_id
            LEFT JOIN (
                SELECT player_id, MAX(points) as total_points
                FROM player_form
                GROUP BY player_id
            ) pf ON p.id = pf.player_id
            LEFT JOIN team_fixtures tf ON p.team = tf.team_code AND tf.gameweek = %s
            WHERE pm.gameweek = %s
        """, [gameweek, gameweek])
        
        players = cursor.fetchall()
        updated_count = 0
        batch_updates = []
        
        for player in players:
            # Convert to v2.0 calculation format
            player_data = {
                'player_id': player['player_id'],
                'name': player['name'],
                'position': player['position'],
                'price': float(player['price']) if player['price'] else 1.0,
                'ppg': float(player['ppg']) if player['ppg'] else 0.0,
                'xgi90': float(player['xgi90']) if player['xgi90'] else 0.0,
                'baseline_xgi': float(player['baseline_xgi']) if player['baseline_xgi'] else None,
                'fixture_difficulty': float(player['fixture_difficulty']) if player['fixture_difficulty'] else 0.0,
                'starter_multiplier': float(player['starter_multiplier']) if player['starter_multiplier'] else 1.0,
                
                # Historical data for dynamic blending
                'total_points_historical': float(player['total_points_historical']) if player['total_points_historical'] else 0.0,
                'games_played_historical': int(player['games_played_historical']) if player['games_played_historical'] else 0,
                'total_points_current': float(player['total_points_current']) if player['total_points_current'] else 0.0,
                'games_played_current': int(player['games_played_current']) if player['games_played_current'] else 0,
            }
            
            # Calculate historical PPG for blending
            if player_data['games_played_historical'] > 0:
                player_data['historical_ppg'] = player_data['total_points_historical'] / player_data['games_played_historical']
            else:
                player_data['historical_ppg'] = 0.0
            
            # Use v2.0 engine for calculation
            v2_result = v2_engine.calculate_player_value(player_data)
            
            # Prepare batch update
            batch_updates.append((
                v2_result['true_value'],
                v2_result['roi'],
                v2_result.get('blended_ppg', player_data['ppg']),
                v2_result.get('current_season_weight', 0.0),
                v2_result['multipliers']['form'],
                v2_result['multipliers']['fixture'],
                v2_result['multipliers']['xgi'],
                player['player_id'],
                gameweek
            ))
            updated_count += 1
        
        # Batch update player_metrics table (ROI is stored in players table)
        cursor.executemany("""
            UPDATE player_metrics 
            SET 
                true_value = %s,
                value_score = %s,
                form_multiplier = %s,
                fixture_multiplier = %s,
                xgi_multiplier = %s
            WHERE player_id = %s AND gameweek = %s
        """, [(u[0], u[1], u[4], u[5], u[6], u[7], u[8]) for u in batch_updates])
        
        # Also update players table with v2.0 columns
        cursor.executemany("""
            UPDATE players 
            SET 
                true_value = %s,
                roi = %s,
                blended_ppg = %s,
                current_season_weight = %s
            WHERE id = %s
        """, [(u[0], u[1], u[2], u[3], u[7]) for u in batch_updates])
        
        conn.commit()
        elapsed_time = time.time() - start_time
        
        print(f"SUCCESS v2.0 Enhanced: Updated {updated_count} players in {elapsed_time:.2f}s")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'elapsed_time': round(elapsed_time, 2),
            'formula_version': 'v2.0'
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"ERROR v2.0 calculation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/')
def dashboard():
    """Main dashboard UI - Serve React frontend"""
    return send_from_directory(frontend_build_dir, 'index.html')

def make_cache_key():
    """Generate cache key based on all query parameters"""
    args = request.args
    # Include all parameters that affect the result
    key_parts = [
        args.get('position', ''),
        str(args.get('min_price', '')),
        str(args.get('max_price', '')),
        args.get('team', ''),
        args.get('search', ''),
        str(args.get('limit', 100)),
        str(args.get('offset', 0)),
        args.get('sort_by', 'true_value'),
        args.get('sort_direction', 'desc')
    ]
    return 'players:' + ':'.join(key_parts)

@app.route('/api/players', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def get_players():
    """
    Get all 633 players with filtering and sorting options
    Query parameters: position, min_price, max_price, team, search, sort_by, sort_direction
    """
    start_time = time.time()
    
    # Load system parameters for configurable games display
    parameters = load_system_parameters()
    
    # Parse query parameters
    position = request.args.get('position')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    team = request.args.get('team')
    search = request.args.get('search', '').strip()
    include_test = request.args.get('include_test', 'false').lower() == 'true'
    
    # Use GameweekManager for unified detection instead of hardcoded default
    from src.gameweek_manager import GameweekManager
    gw_manager = GameweekManager()
    gameweek = gw_manager.get_current_gameweek()  # Main dashboard always shows current data
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort_by = request.args.get('sort_by', 'true_value')
    sort_direction = request.args.get('sort_direction', 'desc')
    
    # Validate sorting parameters
    valid_sort_fields = {
        'name': 'p.name',
        'team': 'p.team', 
        'position': 'p.position',
        'price': 'pm.price',
        'total_fpts': 'COALESCE(pf.total_points, 0)',
        'ppg': 'CASE WHEN COALESCE(pgd.games_played, 0) > 0 THEN COALESCE(pf.total_points, 0) / pgd.games_played ELSE 0 END',
        'value_score': 'pm.value_score',
        'true_value': 'pm.true_value',
        'roi': 'p.roi',
        'minutes': 'p.minutes',
        'xg90': 'p.xg90',
        'xa90': 'p.xa90',
        'xgi90': 'p.xgi90',
        'form_multiplier': 'pm.form_multiplier',
        'fixture_multiplier': 'pm.fixture_multiplier',
        'starter_multiplier': 'pm.starter_multiplier',
        'xgi_multiplier': 'pm.xgi_multiplier',
        'games_played': 'pgd.games_played',
        'games_played_historical': 'pgd.games_played_historical',
        'games_total': '(COALESCE(pgd.games_played_historical, 0) + COALESCE(pgd.games_played, 0))'
    }
    
    if sort_by not in valid_sort_fields:
        sort_by = 'true_value'
    
    if sort_direction.lower() not in ['asc', 'desc']:
        sort_direction = 'desc'
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build dynamic query with games data
        base_query = """
            SELECT 
                p.id, p.name, p.team, p.position,
                p.minutes, p.xg90, p.xa90, p.xgi90, p.baseline_xgi,
                pm.price, 
                COALESCE(pf.total_points, 0) as total_fpts,
                CASE 
                    WHEN COALESCE(pgd.games_played, 0) > 0 
                    THEN COALESCE(pf.total_points, 0) / pgd.games_played
                    ELSE 0 
                END as ppg,
                pm.value_score, pm.true_value,
                p.roi,
                p.blended_ppg, p.current_season_weight,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier, pm.xgi_multiplier,
                pm.last_updated,
                COALESCE(pgd.games_played, 0) as games_played,
                COALESCE(pgd.games_played_historical, 0) as games_played_historical,
                COALESCE(pgd.data_source, 'current') as data_source,
                CASE 
                    WHEN COALESCE(pgd.games_played_historical, 0) > 0 
                    THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
                    ELSE NULL 
                END as historical_ppg,
                p.id as player_id,
                COALESCE(tf.difficulty_score, 0) as fixture_difficulty
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            LEFT JOIN (
                SELECT player_id, 
                       SUM(games_played) as games_played,
                       MAX(games_played_historical) as games_played_historical,
                       MAX(total_points_historical) as total_points_historical,
                       SUM(total_points) as total_points_current,
                       MAX(data_source) as data_source
                FROM player_games_data 
                GROUP BY player_id
            ) pgd ON p.id = pgd.player_id
            LEFT JOIN (
                SELECT player_id, MAX(points) as total_points
                FROM player_form
                GROUP BY player_id
            ) pf ON p.id = pf.player_id
            LEFT JOIN team_fixtures tf ON p.team = tf.team_code AND tf.gameweek = %s
            WHERE pm.gameweek = %s
              AND (COALESCE(pgd.games_played, 0) > 0 
                   OR COALESCE(pgd.games_played_historical, 0) > 0)
        """
        
        params = [gameweek, gameweek]
        conditions = []
        
        # Filter out test players by default (unless include_test=true)
        if not include_test:
            conditions.append("p.team != 'TST'")
        
        # Add filters
        if position:
            positions = [p.strip() for p in position.split(',')]
            placeholders = ','.join(['%s'] * len(positions))
            conditions.append(f"p.position IN ({placeholders})")
            params.extend(positions)
            
        if min_price is not None:
            conditions.append("pm.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("pm.price <= %s")
            params.append(max_price)
            
        if team:
            teams = [t.strip() for t in team.split(',')]
            placeholders = ','.join(['%s'] * len(teams))
            conditions.append(f"p.team IN ({placeholders})")
            params.extend(teams)
            
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
        sort_column = valid_sort_fields[sort_by]
        
        # Special handling for ROI sorting to put NULL values last
        if sort_by == 'roi':
            final_query = base_query + f" ORDER BY {sort_column} {sort_direction.upper()} NULLS LAST LIMIT %s OFFSET %s"
        else:
            final_query = base_query + f" ORDER BY {sort_column} {sort_direction.upper()} LIMIT %s OFFSET %s"
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
            
            # Send games data separately for frontend to handle display
            games_current = player_dict.get('games_played', 0)
            games_historical = player_dict.get('games_played_historical', 0)
            
            # Ensure games data is properly typed and handle None values
            player_dict['games_current'] = int(games_current) if games_current is not None else 0
            player_dict['games_historical'] = int(games_historical) if games_historical is not None else 0
            player_dict['games_total'] = player_dict['games_current'] + player_dict['games_historical']
            players_list.append(player_dict)
        
        # V2.0 calculations are pre-calculated in database - no need for live calculation
        # Mark all players as using V2.0 calculations since they're pre-populated
        for player_dict in players_list:
            player_dict['v2_calculation'] = True
            # Convert string numbers to floats for proper JSON serialization
            if 'total_fpts' in player_dict and player_dict['total_fpts'] is not None:
                player_dict['total_fpts'] = float(player_dict['total_fpts'])
            if 'ppg' in player_dict and player_dict['ppg'] is not None:
                player_dict['ppg'] = float(player_dict['ppg'])
            # ROI and true_value are already loaded from database
            # All multipliers are already loaded from database
        
        # DEBUG: Check final state before JSON response
        semenyo_player = next((p for p in players_list if 'semenyo' in p.get('name', '').lower()), None)
        if semenyo_player:
            print(f"FINAL DEBUG Semenyo before JSON: games_played={semenyo_player.get('games_played')}")
        
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
                'gameweek': gameweek,
                'include_test': include_test
            },
            'sort_applied': {
                'sort_by': sort_by,
                'sort_direction': sort_direction
            },
            'gameweek_info': {
                'current_gameweek': gameweek,
                'detection_method': 'GameweekManager',
                'data_source': 'unified_detection',
                'emergency_protection_active': gw_manager.get_system_status()['emergency_protection_active'],
                'data_freshness': get_data_freshness_info(gameweek)
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

@app.route('/api/system/config', methods=['GET'])
def get_system_config():
    """Get current system parameters - React API path"""
    try:
        parameters = load_system_parameters()
        return jsonify(parameters)
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
        
        # Check if configuration loaded successfully
        if not current_params:
            return jsonify({'error': 'Failed to load current system configuration'}), 500
        
        # Update parameters based on request
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
            
        if 'xgi_integration' in data:
            current_params['xgi_integration'].update(data['xgi_integration'])
            
        # v2.0 Formula Optimization Parameters
        if 'formula_optimization_v2' in data:
            if 'formula_optimization_v2' not in current_params:
                current_params['formula_optimization_v2'] = {}
            current_params['formula_optimization_v2'].update(data['formula_optimization_v2'])
        
        # Save updated parameters
        if not save_system_parameters(current_params):
            return jsonify({'error': 'Failed to save parameters'}), 500
        
        # Trigger True Value recalculation using GameweekManager for default
        gameweek = data.get('gameweek')
        if gameweek is None:
            from src.gameweek_manager import GameweekManager
            gw_manager = GameweekManager()
            gameweek = gw_manager.get_current_gameweek()
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

@app.route('/api/system/update-parameters', methods=['POST'])
def update_system_parameters():
    """Update system parameters - React API path"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Load current parameters
        current_params = load_system_parameters()
        
        # Check if configuration loaded successfully
        if not current_params:
            return jsonify({'error': 'Failed to load current system configuration'}), 500
        
        # Update parameters with deep merge for v2.0 structure
        if 'formula_optimization_v2' in data:
            if 'formula_optimization_v2' not in current_params:
                current_params['formula_optimization_v2'] = {}
            
            # Deep merge for v2.0 parameters
            v2_data = data['formula_optimization_v2']
            v2_current = current_params['formula_optimization_v2']
            
            # Update nested configurations
            for key, value in v2_data.items():
                if isinstance(value, dict) and key in v2_current:
                    v2_current[key].update(value)
                else:
                    v2_current[key] = value
        
        if 'starter_prediction' in data:
            if 'starter_prediction' not in current_params:
                current_params['starter_prediction'] = {}
            current_params['starter_prediction'].update(data['starter_prediction'])
        
        # Save updated parameters
        if not save_system_parameters(current_params):
            return jsonify({'error': 'Failed to save parameters'}), 500
        
        # Trigger recalculation
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        gameweek = gw_manager.get_current_gameweek()
        recalc_result = recalculate_true_values(gameweek)
        
        return jsonify({
            'success': True,
            'message': 'Parameters updated successfully',
            'updated_config': current_params
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/manual-override', methods=['POST'])
def manual_override():
    """Apply manual starter override immediately for a specific player"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        player_id = data.get('player_id')
        override_type = data.get('override_type')  # 'starter', 'bench', 'out', 'auto'
        
        # Get current gameweek using GameweekManager for consistency
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        gameweek = gw_manager.get_current_gameweek()
        
        if not player_id or not override_type:
            return jsonify({'error': 'player_id and override_type required'}), 400
        
        # Load current system parameters to get penalties
        params = load_system_parameters()
        starter_config = params.get('starter_prediction', {})
        rotation_penalty = starter_config.get('auto_rotation_penalty', 0.75)
        bench_penalty = starter_config.get('force_bench_penalty', 0.6)
        out_penalty = starter_config.get('force_out_penalty', 0.0)
        
        # Calculate multiplier based on override type
        if override_type == 'starter':
            multiplier = 1.0
        elif override_type == 'rotation':
            multiplier = rotation_penalty
        elif override_type == 'bench':
            multiplier = bench_penalty
        elif override_type == 'out':
            multiplier = out_penalty
        elif override_type == 'auto':
            # Remove override - will use default CSV prediction or rotation penalty
            multiplier = None  # Will be calculated based on CSV data
        else:
            return jsonify({'error': 'Invalid override_type. Valid types: starter, rotation, bench, out, auto'}), 400
        
        # Update database immediately
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if override_type == 'auto':
            # Remove manual override - use default rotation penalty
            # (CSV starter logic is handled in bulk operations, not individual overrides)
            rotation_penalty = params.get('starter_prediction', {}).get('auto_rotation_penalty', 0.65)
            multiplier = rotation_penalty
        
        # Update player's starter multiplier
        cursor.execute("""
            UPDATE player_metrics 
            SET starter_multiplier = %s
            WHERE player_id = %s AND gameweek = %s
        """, [multiplier, player_id, gameweek])
        
        # Recalculate True Value for this player
        cursor.execute("""
            UPDATE player_metrics 
            SET true_value = (ppg / NULLIF(price, 0)) * form_multiplier * fixture_multiplier * starter_multiplier
            WHERE player_id = %s AND gameweek = %s
        """, [player_id, gameweek])
        
        # Get updated player data
        cursor.execute("""
            SELECT pm.true_value, pm.starter_multiplier, p.name
            FROM player_metrics pm
            JOIN players p ON pm.player_id = p.id
            WHERE pm.player_id = %s AND pm.gameweek = %s
        """, [player_id, gameweek])
        
        updated_player = cursor.fetchone()
        conn.commit()
        conn.close()
        
        # Update manual overrides in system parameters
        if 'manual_overrides' not in params['starter_prediction']:
            params['starter_prediction']['manual_overrides'] = {}
        
        if override_type == 'auto':
            # Remove from manual overrides
            if player_id in params['starter_prediction']['manual_overrides']:
                del params['starter_prediction']['manual_overrides'][player_id]
        else:
            # Add/update manual override
            params['starter_prediction']['manual_overrides'][player_id] = {
                'type': override_type,
                'multiplier': multiplier
            }
        
        save_system_parameters(params)
        
        return jsonify({
            'success': True,
            'player_id': player_id,
            'override_type': override_type,
            'new_multiplier': multiplier,
            'new_true_value': float(updated_player[0]) if updated_player else 0,
            'player_name': updated_player[2] if updated_player else 'Unknown'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-starter-status', methods=['GET'])
def verify_starter_status():
    """Validate starter status consistency and identify potential issues"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current gameweek using GameweekManager for consistency
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        current_gameweek = gw_manager.get_current_gameweek()
        
        # Analyze starter multiplier distribution
        cursor.execute("""
            SELECT 
                starter_multiplier,
                COUNT(*) as player_count,
                ARRAY_AGG(player_name ORDER BY player_name) as players
            FROM players 
            WHERE starter_multiplier IS NOT NULL
            GROUP BY starter_multiplier
            ORDER BY starter_multiplier DESC
        """)
        
        multiplier_distribution = []
        for row in cursor.fetchall():
            multiplier, count, players = row
            multiplier_distribution.append({
                'multiplier': float(multiplier),
                'count': count,
                'players': players[:10]  # Limit to first 10 for readability
            })
        
        # Check for unusual multiplier values (not in standard set)
        standard_multipliers = {1.0, 0.65, 0.6, 0.0}
        cursor.execute("""
            SELECT player_name, starter_multiplier, team, position
            FROM players 
            WHERE starter_multiplier IS NOT NULL 
              AND starter_multiplier NOT IN (1.0, 0.65, 0.6, 0.0)
            ORDER BY starter_multiplier DESC, player_name
        """)
        
        unusual_multipliers = []
        for row in cursor.fetchall():
            name, multiplier, team, position = row
            unusual_multipliers.append({
                'player_name': name,
                'multiplier': float(multiplier),
                'team': team,
                'position': position
            })
        
        # Check for players with missing starter data
        cursor.execute("""
            SELECT COUNT(*) as missing_count
            FROM players 
            WHERE starter_multiplier IS NULL
        """)
        missing_count = cursor.fetchone()[0]
        
        # Get manual override statistics
        cursor.execute("""
            SELECT COUNT(*) as total_players,
                   COUNT(CASE WHEN starter_multiplier = 1.0 THEN 1 END) as starters,
                   COUNT(CASE WHEN starter_multiplier = 0.65 THEN 1 END) as rotation_risks,
                   COUNT(CASE WHEN starter_multiplier = 0.6 THEN 1 END) as bench_players,
                   COUNT(CASE WHEN starter_multiplier = 0.0 THEN 1 END) as out_players
            FROM players 
            WHERE starter_multiplier IS NOT NULL
        """)
        
        stats_row = cursor.fetchone()
        statistics = {
            'total_players': stats_row[0],
            'starters': stats_row[1],
            'rotation_risks': stats_row[2], 
            'bench_players': stats_row[3],
            'out_players': stats_row[4],
            'missing_data': missing_count
        }
        
        # Determine overall health status
        health_status = "HEALTHY"
        issues = []
        
        if unusual_multipliers:
            health_status = "WARNING"
            issues.append(f"{len(unusual_multipliers)} players have non-standard multipliers")
        
        if missing_count > 50:  # More than 50 players missing data
            health_status = "CRITICAL"
            issues.append(f"{missing_count} players missing starter multiplier data")
        elif missing_count > 0:
            health_status = "WARNING" if health_status == "HEALTHY" else health_status
            issues.append(f"{missing_count} players missing starter multiplier data")
        
        conn.close()
        
        return jsonify({
            'success': True,
            'gameweek': current_gameweek,
            'health_status': health_status,
            'issues': issues,
            'statistics': statistics,
            'multiplier_distribution': multiplier_distribution,
            'unusual_multipliers': unusual_multipliers,
            'validation_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of all teams"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT team FROM players ORDER BY team")
        teams = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'teams': teams,
            'count': len(teams)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players-by-team', methods=['GET'])
def get_players_by_team():
    """Get list of players for a specific team"""
    try:
        team = request.args.get('team')
        if not team:
            return jsonify({'error': 'Team parameter is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get players from the specified team, ordered by name
        cursor.execute("""
            SELECT id, name, team, position 
            FROM players 
            WHERE team = %s 
            ORDER BY name
        """, (team,))
        
        players = []
        for row in cursor.fetchall():
            players.append({
                'fantrax_id': row[0],  # Using 'id' column but keeping 'fantrax_id' key for frontend compatibility
                'name': row[1],
                'team': row[2],
                'position': row[3]
            })
        
        conn.close()
        
        return jsonify(players)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gameweek-status', methods=['GET'])
def get_gameweek_status():
    """Get current gameweek status for smart upload system"""
    try:
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        
        current_gw = gw_manager.get_current_gameweek()
        next_gw = gw_manager.get_next_gameweek()
        
        # Get detailed status for current gameweek
        current_status = gw_manager.get_gameweek_status(current_gw)
        
        return jsonify({
            'success': True,
            'current_gameweek': current_gw,
            'next_gameweek': next_gw,
            'current_status': current_status,
            'system_message': f'System currently at GW{current_gw}. Upload GW{current_gw} to update or GW{next_gw} for new data.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'fallback_message': 'Could not determine current gameweek. System will validate your choice during upload.'
        }), 500

@app.route('/api/gameweek-consistency', methods=['GET'])
def check_gameweek_consistency():
    """Comprehensive gameweek consistency monitoring across all tables"""
    try:
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        consistency_report = {
            'timestamp': datetime.now().isoformat(),
            'gameweek_manager_detection': gw_manager.get_current_gameweek(),
            'table_analysis': {},
            'consistency_issues': [],
            'overall_status': 'HEALTHY'
        }
        
        # Check each table's gameweek data
        tables_to_check = [
            ('player_metrics', 'gameweek'),
            ('player_form', 'gameweek'), 
            ('raw_player_snapshots', 'gameweek'),
            ('player_games_data', 'gameweek'),
            ('team_fixtures', 'gameweek')
        ]
        
        for table_name, gw_column in tables_to_check:
            try:
                # Get gameweek distribution
                cursor.execute(f"""
                    SELECT 
                        {gw_column},
                        COUNT(*) as record_count,
                        MAX(COALESCE(last_updated, created_at, now())) as latest_update
                    FROM {table_name}
                    WHERE {gw_column} IS NOT NULL
                    GROUP BY {gw_column}
                    ORDER BY {gw_column} DESC
                    LIMIT 5
                """)
                
                gameweek_data = cursor.fetchall()
                
                if gameweek_data:
                    latest_gw = gameweek_data[0]['gameweek']
                    latest_count = gameweek_data[0]['record_count']
                    
                    consistency_report['table_analysis'][table_name] = {
                        'latest_gameweek': latest_gw,
                        'latest_record_count': latest_count,
                        'latest_update': gameweek_data[0]['latest_update'].isoformat() if gameweek_data[0]['latest_update'] else None,
                        'gameweek_distribution': [
                            {'gameweek': row['gameweek'], 'count': row['record_count']} 
                            for row in gameweek_data
                        ]
                    }
                    
                    # Check for consistency issues
                    gm_detection = consistency_report['gameweek_manager_detection']
                    if latest_gw != gm_detection:
                        consistency_report['consistency_issues'].append({
                            'table': table_name,
                            'issue': f'Table shows GW{latest_gw} but GameweekManager detects GW{gm_detection}',
                            'severity': 'HIGH' if abs(latest_gw - gm_detection) > 1 else 'MEDIUM'
                        })
                    
                    # Check for anomalous record counts (< 5% of expected)
                    if latest_count < 32:  # Less than 5% of 647 players
                        consistency_report['consistency_issues'].append({
                            'table': table_name,
                            'issue': f'Anomalous record count: {latest_count} records in GW{latest_gw} (expected >32)',
                            'severity': 'HIGH'
                        })
                        
                else:
                    consistency_report['table_analysis'][table_name] = {
                        'status': 'NO_DATA',
                        'issue': 'No gameweek data found'
                    }
                    
            except Exception as e:
                consistency_report['table_analysis'][table_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        # Determine overall status
        high_severity_issues = [i for i in consistency_report['consistency_issues'] if i.get('severity') == 'HIGH']
        if high_severity_issues:
            consistency_report['overall_status'] = 'CRITICAL'
        elif consistency_report['consistency_issues']:
            consistency_report['overall_status'] = 'WARNING'
        
        # Add summary
        consistency_report['summary'] = {
            'total_issues': len(consistency_report['consistency_issues']),
            'high_severity': len(high_severity_issues),
            'tables_checked': len(tables_to_check),
            'healthy_tables': len([t for t, data in consistency_report['table_analysis'].items() 
                                 if data.get('status') != 'ERROR' and data.get('status') != 'NO_DATA'])
        }
        
        conn.close()
        return jsonify(consistency_report)
        
    except Exception as e:
        return jsonify({
            'error': f'Consistency check failed: {str(e)}',
            'overall_status': 'ERROR',
            'timestamp': datetime.now().isoformat()
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

@app.route('/api/import-lineups', methods=['POST'])
def import_lineups():
    """
    Import starter predictions from CSV file
    Updates starter_multiplier for players based on CSV data
    """
    try:
        if 'lineups_csv' not in request.files:
            return jsonify({'error': 'No CSV file provided'}), 400
        
        file = request.files['lineups_csv']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read CSV content and parse properly with quotes
        import csv
        from io import StringIO
        
        csv_content = file.read().decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        if len(lines) < 2:
            return jsonify({'error': 'CSV must have header and data rows'}), 400
        
        # Parse header using CSV reader to handle quotes properly
        csv_reader = csv.reader(StringIO(lines[0]))
        header = next(csv_reader)
        
        # Check for individual player format (original)
        expected_individual_headers = ['Team', 'Player Name', 'Position', 'Predicted Status']
        header_normalized = [h.strip().lower().replace(' ', '_') for h in header]
        expected_individual_normalized = [h.strip().lower().replace(' ', '_') for h in expected_individual_headers]
        
        is_individual_format = header_normalized == expected_individual_normalized
        
        # Check for formation matrix format (FFS scraping)
        first_col_clean = header[0].strip().lower().strip('"')
        
        # Check if it's formation format: either starts with !m-0 OR has 12 columns with "player" pattern
        is_formation_format = (
            len(header) >= 12 and  # At least team + 11 players
            (first_col_clean in ['team', '!m-0'] or  # Known team identifiers
             (first_col_clean == '!m-0' and  # FFS format specifically
              all('player' in h.lower() for h in header[1:12])))  # Player columns 1-11
        )
        
        # Alternative detection: if we have 12 columns and the pattern looks like FFS format
        if not is_formation_format and len(header) == 12:
            is_formation_format = (
                first_col_clean == '!m-0' and
                header[1].lower().startswith('player') and
                header[2].lower().startswith('player')
            )
        
        # Debug logging (optional)
        # print(f"CSV format detection: {is_formation_format}, teams will be mapped")
        
        if not is_individual_format and not is_formation_format:
            return jsonify({
                'error': f'Invalid CSV format. Expected either:\n' +
                        f'1. Individual format: {expected_individual_headers}\n' +
                        f'2. Formation format: Team + 11 player columns\n' +
                        f'Got: {header}\n' +
                        f'First column detected as: "{first_col_clean}"'
            }), 400
        
        # Parse data rows
        starters = []
        non_starters = []
        unmatched_players = []
        position_conflicts = []
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get system parameters for multipliers
        params = load_system_parameters()
        rotation_penalty = params.get('starter_prediction', {}).get('auto_rotation_penalty', 0.65)
        
        # Initialize UnifiedNameMatcher for improved name matching
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        if is_formation_format:
            # Process formation matrix format (FFS scraping)
            players_to_process = parse_formation_csv(lines[1:], cursor)  # Skip header
        else:
            # Process individual player format (original)
            players_to_process = parse_individual_csv(lines[1:])  # Skip header
        
        for line_num, player_info in enumerate(players_to_process, 1):
            player_name = player_info['name']
            team = player_info['team']
            position = player_info['position']
            status = player_info['status']
            formation_position = player_info.get('formation_position')
            
            # Check for position conflicts from formation parsing
            if player_info.get('position_conflict'):
                position_conflicts.append({
                    'name': player_name,
                    'team': team,
                    'formation_position': formation_position,
                    'database_position': position,
                    'conflict_reason': f"Formation pos {formation_position} suggests {'D/M' if 5 <= formation_position <= 8 else 'M/F'}, but database shows {position}"
                })
                continue
            
            # Use UnifiedNameMatcher for improved matching
            match_result = matcher.match_player(
                source_name=player_name,
                source_system='ffs',
                team=team,
                position=position
            )
            
            # Check if we have a good match (fantrax_id exists and high confidence or verified)
            # Use lower threshold for formation imports since names are often shortened
            confidence_threshold = 80.0 if is_formation_format else 90.0
            if match_result['fantrax_id'] and (not match_result['needs_review'] or match_result['confidence'] >= confidence_threshold):
                # We have a confident match
                if status.lower() in ['starter', 'starting', 'start']:
                    starters.append({
                        'player_id': match_result['fantrax_id'],
                        'name': match_result['fantrax_name'],
                        'team': team,
                        'multiplier': 1.0,
                        'confidence': match_result['confidence'],
                        'match_type': match_result['match_type']
                    })
                else:
                    non_starters.append({
                        'player_id': match_result['fantrax_id'],
                        'name': match_result['fantrax_name'],
                        'team': team,
                        'multiplier': rotation_penalty,
                        'confidence': match_result['confidence'],
                        'match_type': match_result['match_type']
                    })
            else:
                # No match or low confidence - add to unmatched for review
                unmatched_info = {
                    'name': player_name,
                    'team': team,
                    'position': position,
                    'line': line_num,
                    'status': status
                }
                
                # Include match details if we have suggestions
                if match_result['fantrax_id']:
                    unmatched_info.update({
                        'suggested_match': match_result['fantrax_name'],
                        'confidence': match_result['confidence'],
                        'needs_review': True
                    })
                
                # Add top suggestions if available
                if match_result['suggested_matches']:
                    unmatched_info['suggestions'] = match_result['suggested_matches'][:3]  # Top 3
                
                unmatched_players.append(unmatched_info)
        
        # Update starter_multiplier in database using GameweekManager
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        gameweek = gw_manager.get_current_gameweek()  # Use current gameweek for lineup updates
        updated_count = 0
        
        # Get manual overrides from system parameters to preserve them
        params = load_system_parameters()
        manual_overrides_section = params.get('starter_prediction', {}).get('manual_overrides', {})
        
        # Handle case where manual_overrides is just a description dict
        if isinstance(manual_overrides_section, dict) and 'description' in manual_overrides_section:
            manual_overrides = {}  # No actual overrides yet
        else:
            manual_overrides = manual_overrides_section if isinstance(manual_overrides_section, dict) else {}
        
        try:
            # STEP 1: Set ALL players to rotation penalty EXCEPT those with manual overrides
            cursor.execute("""
                UPDATE player_metrics 
                SET starter_multiplier = %s
                WHERE gameweek = %s
            """, [rotation_penalty, gameweek])
            
            all_players_updated = cursor.rowcount
            print(f"Set {all_players_updated} players to rotation penalty ({rotation_penalty}x)")
            
            # STEP 2: Set matched CSV players to starter (1.0x) - BUT don't override manual settings
            starter_ids = []
            for starter in starters:
                # Check if this player has a manual override - if so, skip CSV update
                if starter['player_id'] not in manual_overrides:
                    cursor.execute("""
                        UPDATE player_metrics 
                        SET starter_multiplier = %s
                        WHERE player_id = %s AND gameweek = %s
                    """, [1.0, starter['player_id'], gameweek])
                    starter_ids.append(starter['player_id'])
                    updated_count += 1
                else:
                    print(f"Skipping {starter['name']} - has manual override")
            
            print(f"Set {len(starter_ids)} matched players to starter (1.0x)")
            
            # STEP 3: Re-apply any existing manual overrides
            starter_config = params.get('starter_prediction', {})
            rotation_penalty = starter_config.get('auto_rotation_penalty', 0.75)
            bench_penalty = starter_config.get('force_bench_penalty', 0.6)
            out_penalty = starter_config.get('force_out_penalty', 0.0)
            
            for player_id, override in manual_overrides.items():
                override_type = override.get('type')
                if override_type == 'starter':
                    multiplier = 1.0
                elif override_type == 'rotation':
                    multiplier = rotation_penalty
                elif override_type == 'bench':
                    multiplier = bench_penalty
                elif override_type == 'out':
                    multiplier = out_penalty
                else:
                    continue  # Skip 'auto' - already handled above
                
                cursor.execute("""
                    UPDATE player_metrics 
                    SET starter_multiplier = %s
                    WHERE player_id = %s AND gameweek = %s
                """, [multiplier, player_id, gameweek])
                print(f"Applied manual override: {player_id} = {multiplier}x ({override_type})")
            
            conn.commit()
            
            # Trigger True Value recalculation
            recalc_result = recalculate_true_values(gameweek)
            
            # Calculate matching statistics
            total_players = len(starters) + len(non_starters) + len(unmatched_players)
            matched_players = len(starters) + len(non_starters)
            match_rate = (matched_players / total_players * 100) if total_players > 0 else 0
            
            # Calculate confidence statistics
            all_matches = starters + non_starters
            high_confidence = sum(1 for m in all_matches if m.get('confidence', 0) >= 95)
            medium_confidence = sum(1 for m in all_matches if 85 <= m.get('confidence', 0) < 95)
            
            return jsonify({
                'success': True,
                'matching_system': 'UnifiedNameMatcher',
                'csv_format': 'formation_matrix' if is_formation_format else 'individual_players',
                'total_players': total_players,
                'matched_players': matched_players,
                'starters_identified': len(starters),
                'rotation_risk': len(non_starters),
                'unmatched_players': len(unmatched_players),
                'position_conflicts': len(position_conflicts),
                'match_rate': round(match_rate, 1),
                'confidence_breakdown': {
                    'high_confidence_95plus': high_confidence,
                    'medium_confidence_85_94': medium_confidence,
                    'needs_review': len(unmatched_players)
                },
                'unmatched_details': unmatched_players,  # All unmatched players for validation
                'position_conflicts_details': position_conflicts,  # All conflicts for manual review
                'updated_starters': updated_count,
                'recalculation_time': recalc_result.get('elapsed_time', 0),
                'rotation_penalty_applied': rotation_penalty,
                'smart_suggestions_available': sum(1 for u in unmatched_players if 'suggestions' in u)
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({
                'error': f'Database update failed: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': f'CSV processing failed: {str(e)}'
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/export', methods=['GET'])
def export_players():
    """
    Export filtered player data as CSV
    """
    try:
        # Parse query parameters (same as /api/players)
        position = request.args.get('position')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        team = request.args.get('team')
        search = request.args.get('search', '').strip()
        # Use GameweekManager for unified gameweek detection
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        gameweek = gw_manager.get_current_gameweek()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build query (same logic as /api/players but without pagination)
        base_query = """
            SELECT 
                p.name, p.team, p.position,
                pm.price, pm.ppg, p.blended_ppg, pm.value_score, pm.true_value, p.roi,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier, pm.xgi_multiplier,
                p.current_season_weight,
                p.minutes, p.xg90, p.xa90, p.xgi90,
                (COALESCE(p.xg90, 0) + COALESCE(p.xa90, 0)) as xgi
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.gameweek = %s
        """
        
        params = [gameweek]
        conditions = []
        
        # Add filters
        if position:
            positions = [p.strip() for p in position.split(',')]
            placeholders = ','.join(['%s'] * len(positions))
            conditions.append(f"p.position IN ({placeholders})")
            params.extend(positions)
            
        if min_price is not None:
            conditions.append("pm.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("pm.price <= %s")
            params.append(max_price)
            
        if team:
            teams = [t.strip() for t in team.split(',')]
            placeholders = ','.join(['%s'] * len(teams))
            conditions.append(f"p.team IN ({placeholders})")
            params.extend(teams)
            
        if search:
            conditions.append("p.name ILIKE %s")
            params.append(f"%{search}%")
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
            
        # Order by True Value descending
        final_query = base_query + " ORDER BY pm.true_value DESC"
        
        cursor.execute(final_query, params)
        players = cursor.fetchall()
        
        # Generate CSV content with gameweek metadata
        csv_lines = []
        csv_lines.append(f"# Fantrax Value Hunter Export - Gameweek {gameweek} - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        csv_lines.append("Name,Team,Position,Price,PPG,Blended PPG,Value Score,True Value,ROI,Form Multiplier,Fixture Multiplier,Starter Multiplier,xGI Multiplier,Current Season Weight,Minutes,xG90,xA90,xGI90,xGI")
        
        for player in players:
            current_weight = float(player['current_season_weight']) if player['current_season_weight'] else 0.0
            minutes = player['minutes'] if player['minutes'] else 0
            xg90 = float(player['xg90']) if player['xg90'] else 0.0
            xa90 = float(player['xa90']) if player['xa90'] else 0.0
            xgi90 = float(player['xgi90']) if player['xgi90'] else 0.0
            xgi = float(player['xgi']) if player['xgi'] else 0.0
            csv_lines.append(f"{player['name']},{player['team']},{player['position']},{player['price']},{player['ppg']},{player['blended_ppg']:.2f},{player['value_score']:.3f},{player['true_value']:.3f},{player['roi']:.3f},{player['form_multiplier']:.2f},{player['fixture_multiplier']:.2f},{player['starter_multiplier']:.2f},{player['xgi_multiplier']:.2f},{current_weight:.3f},{minutes},{xg90:.3f},{xa90:.3f},{xgi90:.3f},{xgi:.3f}")
        
        csv_content = '\n'.join(csv_lines)
        
        # Return CSV as downloadable file
        from flask import Response
        
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=fantrax_players_gw{gameweek}.csv'}
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# ===============================
# NAME MATCHING VALIDATION API
# ===============================

@app.route('/api/validate-import', methods=['POST'])
def validate_import():
    """
    Validate name matching for import data without applying changes
    Returns summary with position breakdown and suggestions for unmatched players
    """
    try:
        data = request.get_json()
        
        if not data or 'players' not in data:
            return jsonify({'error': 'players data is required'}), 400
        
        players = data['players']
        source_system = data.get('source_system', 'unknown')
        
        if not players:
            return jsonify({'error': 'No player data provided'}), 400
        
        # Initialize matcher
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        # Process each player
        validation_results = []
        position_breakdown = {}
        
        for player_data in players:
            player_name = player_data.get('name', '')
            team = player_data.get('team', '')
            position = player_data.get('position', '')
            
            if not player_name:
                continue
            
            # Update position breakdown
            if position not in position_breakdown:
                position_breakdown[position] = {'total': 0, 'matched': 0, 'match_rate': 0}
            position_breakdown[position]['total'] += 1
            
            # Try to match the player
            match_result = matcher.match_player(
                source_name=player_name,
                source_system=source_system,
                team=team,
                position=position
            )
            
            # Create player result
            player_result = {
                'original_name': player_name,
                'original_team': team,
                'original_position': position,
                'original_data': player_data,
                'needs_review': match_result['needs_review'],
                'match_result': match_result
            }
            
            validation_results.append(player_result)
            
            # Update position stats
            if match_result['fantrax_id'] and not match_result['needs_review']:
                position_breakdown[position]['matched'] += 1
        
        # Calculate position match rates
        for pos_stats in position_breakdown.values():
            if pos_stats['total'] > 0:
                pos_stats['match_rate'] = (pos_stats['matched'] / pos_stats['total']) * 100
        
        # Calculate overall stats
        total_players = len(validation_results)
        matched_players = sum(1 for p in validation_results if p['match_result']['fantrax_id'] and not p['needs_review'])
        needs_review = sum(1 for p in validation_results if p['needs_review'])
        failed = total_players - matched_players - needs_review
        match_rate = (matched_players / total_players * 100) if total_players > 0 else 0
        
        return jsonify({
            'summary': {
                'total': total_players,
                'matched': matched_players,
                'needs_review': needs_review,
                'failed': failed,
                'match_rate': match_rate
            },
            'players': validation_results,
            'position_breakdown': position_breakdown,
            'source_system': source_system
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-player-suggestions', methods=['POST'])
def get_player_suggestions():
    """
    Get suggested matches for a specific unmatched player
    """
    try:
        data = request.get_json()
        
        if not data or 'source_name' not in data:
            return jsonify({'error': 'source_name is required'}), 400
        
        source_name = data['source_name']
        team = data.get('team')
        position = data.get('position')
        top_n = data.get('top_n', 5)
        
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        suggestions = matcher.suggestion_engine.get_player_suggestions(
            source_name=source_name,
            team=team,
            position=position,
            top_n=top_n
        )
        
        return jsonify({
            'success': True,
            'source_name': source_name,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/confirm-mapping', methods=['POST'])
def confirm_mapping():
    """
    Save user-confirmed name mapping
    """
    try:
        data = request.get_json()
        
        required_fields = ['source_name', 'source_system', 'fantrax_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        source_name = data['source_name']
        source_system = data['source_system']
        fantrax_id = data['fantrax_id']
        user_id = data.get('user_id', 'web_user')
        confidence_override = data.get('confidence_override')
        
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        success = matcher.confirm_mapping(
            source_name=source_name,
            source_system=source_system,
            fantrax_id=fantrax_id,
            user_id=user_id,
            confidence_override=confidence_override
        )
        
        if success:
            # Get the mapping ID for response
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM name_mappings WHERE source_system = %s AND source_name = %s",
                [source_system, source_name]
            )
            mapping_id = cursor.fetchone()
            conn.close()
            
            return jsonify({
                'success': True,
                'mapping_id': mapping_id[0] if mapping_id else None,
                'message': 'Mapping confirmed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to confirm mapping'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apply-import', methods=['POST'])
def apply_import():
    """
    Apply import with validated mappings
    """
    try:
        data = request.get_json()
        print(f"Apply import called with data keys: {list(data.keys()) if data else 'None'}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        confirmed_mappings = data.get('confirmed_mappings', {})
        source_system = data.get('source_system', 'unknown')
        user_id = data.get('user_id', 'web_user')
        dry_run = data.get('dry_run', False)
        players = data.get('players', [])
        
        print(f"confirmed_mappings count: {len(confirmed_mappings)}")
        print(f"players count: {len(players)}")
        print(f"dry_run: {dry_run}")
        
        # Handle dry run case - just count confirmed mappings
        if dry_run:
            import_count = len(confirmed_mappings)
            return jsonify({
                'success': True,
                'import_count': import_count,
                'message': f'Would import {import_count} players with {len(confirmed_mappings)} manual mappings'
            })
        
        # Only create matcher for actual imports (not dry runs)
        try:
            matcher = UnifiedNameMatcher(DB_CONFIG)
            print("UnifiedNameMatcher created successfully")
        except Exception as e:
            print(f"Error creating UnifiedNameMatcher: {e}")
            return jsonify({
                'success': False,
                'error': f'UnifiedNameMatcher initialization failed: {str(e)}'
            }), 500
        
        # Save all confirmed mappings
        saved_count = 0
        failed_mappings = []
        import_count = 0
        
        for source_name, mapping_info in confirmed_mappings.items():
            try:
                success = matcher.confirm_mapping(
                    source_name=source_name,
                    source_system=source_system,
                    fantrax_id=mapping_info['fantrax_id'],
                    user_id=user_id,
                    confidence_override=mapping_info.get('confidence', 100.0)
                )
                
                if success:
                    saved_count += 1
                else:
                    failed_mappings.append(source_name)
                    
            except Exception as e:
                failed_mappings.append(f"{source_name}: {str(e)}")
        
        # Count how many players would be imported
        for player in players:
            player_name = player.get('name', '')
            
            # Check if this player would be successfully imported
            if player_name in confirmed_mappings:
                import_count += 1
            else:
                # Check if it has an existing mapping
                match_result = matcher.match_player(
                    source_name=player_name,
                    source_system=source_system,
                    team=player.get('team', ''),
                    position=player.get('position', '')
                )
                if match_result['fantrax_id'] and not match_result['needs_review']:
                    import_count += 1
        
        return jsonify({
            'success': True,
            'import_count': import_count,
            'mappings_saved': saved_count,
            'failed_mappings': failed_mappings,
            'message': f'Successfully imported {import_count} players with {saved_count} new mappings'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recent-unmatched-players', methods=['GET'])
def get_recent_unmatched_players():
    """
    Get recently unmatched players from last import for validation page
    """
    try:
        # For now, return empty - this is a placeholder for future session storage
        # In a full implementation, you'd store unmatched players in Redis/session
        return jsonify({
            'has_unmatched': False,
            'unmatched_count': 0,
            'validation_data': None,
            'message': 'No recent import data available'
        })
        
    except Exception as e:
        return jsonify({
            'has_unmatched': False,
            'error': str(e)
        }), 500

@app.route('/api/name-mapping-stats', methods=['GET'])
def get_name_mapping_stats():
    """
    Get statistics about the name matching system
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total mappings
        cursor.execute("SELECT COUNT(*) FROM name_mappings")
        total_mappings = cursor.fetchone()[0]
        
        # Get by source system
        cursor.execute("""
            SELECT source_system, COUNT(*) 
            FROM name_mappings 
            GROUP BY source_system 
            ORDER BY COUNT(*) DESC
        """)
        by_source_system = dict(cursor.fetchall())
        
        # Get verified vs unverified
        cursor.execute("""
            SELECT verified, COUNT(*) 
            FROM name_mappings 
            GROUP BY verified
        """)
        verification_stats = dict(cursor.fetchall())
        
        # Get recent stats (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM name_mappings 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        recent_mappings = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_mappings': total_mappings,
            'by_source_system': by_source_system,
            'verified_mappings': verification_stats.get(True, 0),
            'unverified_mappings': verification_stats.get(False, 0),
            'recent_mappings_24h': recent_mappings,
            'accuracy_stats': {
                'verified_rate': (verification_stats.get(True, 0) / total_mappings * 100) if total_mappings > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===============================
# FORM DATA IMPORT
# ===============================

@app.route('/api/import-form-data', methods=['POST'])
def import_form_data():
    """
    Import gameweek form data from Fantrax CSV export
    Expects CSV with columns: ID, Player, Team, Position, RkOv, Opponent, Salary, FPts, etc.
    Extracts player ID and FPts for storage in player_form table
    """
    try:
        # GameweekManager integration with intelligent validation
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        
        gameweek_input = request.form.get('gameweek')
        if gameweek_input:
            try:
                gameweek_input = int(gameweek_input)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Gameweek must be a number'
                }), 400
            
            # Validate gameweek for upload using GameweekManager
            validation_result = gw_manager.validate_gameweek_for_upload(gameweek_input)
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': validation_result['message'],
                    'suggested_gameweek': validation_result.get('suggested_gameweek'),
                    'current_gameweek': gw_manager.get_current_gameweek()
                }), 400
                
            gameweek = gameweek_input
        else:
            # If no gameweek provided, use next gameweek for new uploads
            gameweek = gw_manager.get_next_gameweek()
            
        # Legacy emergency protection (redundant but keeping for extra safety)
        if gameweek == 1:
            return jsonify({
                'success': False,
                'error': 'GW1 data is protected during gameweek unification system upgrade. Contact admin if overwrite needed.'
            }), 400
        
        # Check for uploaded file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Read CSV file
        import pandas as pd
        import io
        
        # Read the CSV content
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = pd.read_csv(stream)
        
        # Validate required columns
        required_columns = ['ID', 'Player', 'FPts', 'Salary']
        missing_columns = [col for col in required_columns if col not in csv_input.columns]
        if missing_columns:
            return jsonify({
                'success': False,
                'error': f'Missing required columns: {missing_columns}'
            }), 400
        
        # Process the data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        imported_count = 0
        error_count = 0
        errors = []
        skipped_players = []
        
        # Get all existing player IDs to check against
        cursor.execute("SELECT id FROM players")
        existing_player_ids = set(row[0] for row in cursor.fetchall())
        new_players_added = []
        
        for index, row in csv_input.iterrows():
            try:
                # Extract player ID (remove asterisks from ID column)
                player_id = str(row['ID']).strip('*')
                player_name = row.get('Player', 'Unknown')
                team = row.get('Team', 'UNK')
                position = row.get('Position', 'UNK')
                
                # Check if player exists in our database
                if player_id not in existing_player_ids:
                    # Auto-add new player to database
                    try:
                        cursor.execute("""
                            INSERT INTO players (id, name, team, position, updated_at, minutes, xg90, xa90, xgi90, last_understat_update)
                            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, NOW())
                        """, (player_id, player_name, team, position, 0, 0.000, 0.000, 0.000))
                        
                        existing_player_ids.add(player_id)  # Add to our tracking set
                        new_players_added.append(f"{player_name} ({team}, {position})")
                        print(f"Auto-added new player: {player_name} - {team} ({position}) [ID: {player_id}]")
                        
                    except Exception as add_error:
                        error_count += 1
                        skipped_players.append(f"{player_name} (ID: {player_id}) - Failed to add: {add_error}")
                        continue
                
                # Get fantasy points and price
                fpts = float(row['FPts'])
                salary = float(row['Salary'])
                print(f"DEBUG - Price for {player_name}: {salary} (from CSV column 'Salary')")
                
                # Insert/update player form data
                cursor.execute("""
                    INSERT INTO player_form (player_id, gameweek, points, timestamp)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek) 
                    DO UPDATE SET points = EXCLUDED.points, timestamp = NOW()
                """, [player_id, gameweek, fpts])
                
                # Insert/update player_metrics with price
                cursor.execute("""
                    INSERT INTO player_metrics (player_id, gameweek, price, last_updated)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek) 
                    DO UPDATE SET price = EXCLUDED.price, last_updated = NOW()
                """, [player_id, gameweek, salary])
                
                # Update games_played count using minutes-based logic
                # Compare current total minutes vs first game minutes to detect if player played this gameweek
                
                # Get current total minutes from players table (updated by Understat sync)
                cursor.execute("SELECT COALESCE(minutes, 0) FROM players WHERE id = %s", [player_id])
                current_total_minutes = cursor.fetchone()[0] or 0
                
                # Get previous gameweek minutes from raw_player_snapshots for rolling comparison
                previous_gameweek = gameweek - 1
                cursor.execute("""
                    SELECT COALESCE(minutes_played, 0) 
                    FROM raw_player_snapshots 
                    WHERE player_id = %s AND gameweek = %s
                """, [player_id, previous_gameweek])
                previous_gameweek_result = cursor.fetchone()
                previous_gameweek_minutes = previous_gameweek_result[0] if previous_gameweek_result else 0
                
                # Player played this gameweek if total minutes > previous gameweek minutes
                games_played = 1 if current_total_minutes > previous_gameweek_minutes else 0
                cursor.execute("""
                    INSERT INTO player_games_data (player_id, gameweek, games_played, last_updated)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek)
                    DO UPDATE SET games_played = EXCLUDED.games_played, last_updated = NOW()
                """, [player_id, gameweek, games_played])
                
                # NEW: Capture raw data snapshot for trend analysis
                cursor.execute("""
                    INSERT INTO raw_player_snapshots 
                    (player_id, gameweek, name, team, position, price, fpts, 
                     minutes_played, fantrax_import, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek) 
                    DO UPDATE SET 
                        price = EXCLUDED.price,
                        fpts = EXCLUDED.fpts,
                        name = EXCLUDED.name,
                        team = EXCLUDED.team,
                        position = EXCLUDED.position,
                        fantrax_import = TRUE,
                        import_timestamp = NOW()
                """, [player_id, gameweek, player_name, team, position, salary, fpts, 0, True])
                
                # Also capture in raw form snapshots for EWMA calculations
                cursor.execute("""
                    INSERT INTO raw_form_snapshots 
                    (player_id, gameweek, points_scored, minutes_played, games_played, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek)
                    DO UPDATE SET 
                        points_scored = EXCLUDED.points_scored,
                        games_played = EXCLUDED.games_played,
                        import_timestamp = NOW()
                """, [player_id, gameweek, fpts, 0, games_played])
                
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                player_name = row.get('Player', 'Unknown')
                errors.append(f"Row {index + 1} ({player_name}): {str(e)}")
                
                # Don't fail completely for individual row errors
                continue
        
        # Recalculate PPG from current season data after import
        print(f"Recalculating PPG for gameweek {gameweek}...")
        cursor.execute("""
            UPDATE player_metrics pm
            SET ppg = (
                SELECT 
                    CASE 
                        WHEN COALESCE(pgd.games_played_current, 0) > 0 
                        THEN COALESCE(pf_max.total_points, 0) / pgd.games_played_current
                        ELSE 0 
                    END
                FROM (
                    SELECT player_id, MAX(points) as total_points
                    FROM player_form
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pf_max
                LEFT JOIN (
                    SELECT player_id, SUM(games_played) as games_played_current
                    FROM player_games_data 
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pgd ON pf_max.player_id = pgd.player_id
                LIMIT 1
            )
            WHERE pm.gameweek = %s
        """, [gameweek])
        print(f"PPG recalculation completed.")
        
        # Auto-trigger V2.0 recalculation with fresh PPG data
        print(f"Triggering V2.0 True Value recalculation...")
        try:
            # Import at function level to avoid circular imports
            from calculation_engine_v2 import FormulaEngineV2
            
            parameters = load_system_parameters()
            engine = FormulaEngineV2(DB_CONFIG, parameters)
            
            # Get fresh player data with corrected PPG using same logic as V2.0 API
            cursor.execute("""
                SELECT 
                    p.id as player_id, p.name, p.team, p.position,
                    p.xgi90, p.baseline_xgi, pm.price,
                    -- Calculate fresh PPG using same logic as form import
                    CASE 
                        WHEN COALESCE(pgd.games_played, 0) > 0 
                        THEN COALESCE(pf_max.total_points, 0) / pgd.games_played
                        ELSE 0 
                    END as ppg,
                    pm.form_multiplier, pm.fixture_multiplier, 
                    pm.starter_multiplier, pm.xgi_multiplier,
                    tf.difficulty_score as fixture_difficulty,
                    COALESCE(pgd.games_played, 0) as games_played,
                    COALESCE(pgd.games_played_historical, 0) as games_played_historical,
                    CASE 
                        WHEN COALESCE(pgd.games_played_historical, 0) > 0 
                        THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
                        ELSE NULL 
                    END as historical_ppg
                FROM players p
                JOIN player_metrics pm ON p.id = pm.player_id
                LEFT JOIN (
                    SELECT player_id, MAX(points) as total_points
                    FROM player_form
                    GROUP BY player_id
                ) pf_max ON p.id = pf_max.player_id
                LEFT JOIN team_fixtures tf ON p.team = tf.team_code AND tf.gameweek = %s
                LEFT JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = %s
                WHERE pm.gameweek = %s
                  AND p.team != 'TST'  -- Exclude test players
                ORDER BY p.name
            """, [gameweek, gameweek, gameweek])
            
            players = cursor.fetchall()
            updated = 0
            
            for player in players:
                calc = engine.calculate_player_value(dict(player))
                cursor.execute("""
                    UPDATE player_metrics 
                    SET true_value = %s, value_score = %s, last_updated = NOW()
                    WHERE player_id = %s AND gameweek = %s
                """, [calc['true_value'], calc['roi'], player['player_id'], gameweek])
                
                cursor.execute("""
                    UPDATE players 
                    SET true_value = %s, roi = %s, blended_ppg = %s
                    WHERE id = %s
                """, [calc['true_value'], calc['roi'], calc.get('base_ppg', 0), player['player_id']])
                
                updated += 1
            
            print(f"V2.0 recalculation completed for {updated} players")
        except Exception as e:
            print(f"Warning: V2.0 recalculation failed: {e}")
            # Don't fail the entire import if V2.0 recalc fails
        
        # Commit all changes (including V2.0 updates)
        conn.commit()
        conn.close()
        
        # V2.0 calculations are always enabled - no parameter toggles needed
        
        return jsonify({
            'success': True,
            'message': f'Form data import completed for gameweek {gameweek}',
            'imported_count': imported_count,
            'error_count': error_count,
            'errors': errors[:10],  # Limit errors shown
            'skipped_players': skipped_players[:20],  # Show first 20 skipped players
            'new_players_added': new_players_added[:20],  # Show first 20 auto-added players
            'total_new_players': len(new_players_added),
            'gameweek': gameweek,
            'trigger_recalc': True  # Signal to frontend to trigger recalculation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500

# ===============================
# ODDS IMPORT ENDPOINT (Sprint 6)
# ===============================

@app.route('/api/import-odds', methods=['POST'])
def import_odds():
    """
    Import betting odds data from oddsportal.com CSV
    Expected format: Date, Time, Home Team, Away Team, Home Odds, Draw Odds, Away Odds
    """
    try:
        # Import GameweekManager for validation
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
            
        # Get gameweek from form with GameweekManager validation
        gameweek_input = request.form.get('gameweek', type=int)
        
        # First validation: basic input check
        if not gameweek_input or gameweek_input < 1:
            return jsonify({
                'success': False, 
                'error': 'Valid gameweek number required',
                'suggested_gameweek': gw_manager.get_current_gameweek()
            }), 400
        
        # Second validation: GameweekManager smart validation
        validation_result = gw_manager.validate_gameweek_for_upload(gameweek_input)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result['message'],
                'suggestion': validation_result['recommendation'],
                'suggested_gameweek': validation_result.get('suggested_gameweek'),
                'current_gameweek': gw_manager.get_current_gameweek()
            }), 400
        
        # Use validated gameweek
        gameweek = gameweek_input
            
        # Team name mapping dictionary
        ODDS_TO_FANTRAX = {
            "Arsenal": "ARS", "Aston Villa": "AVL", "Bournemouth": "BOU",
            "Brentford": "BRF", "Brighton": "BHA", "Burnley": "BUR", 
            "Chelsea": "CHE", "Crystal Palace": "CRY", "Everton": "EVE",
            "Fulham": "FUL", "Leeds": "LEE", "Liverpool": "LIV",
            "Manchester City": "MCI", "Manchester Utd": "MUN", "Newcastle": "NEW",
            "Nottingham": "NOT", "Sunderland": "SUN", "Tottenham": "TOT",
            "West Ham": "WHU", "Wolves": "WOL",
            # OddsPortal variations for missing teams
            "Man City": "MCI", "Man United": "MUN", "Tottenham Hotspur": "TOT",
            "West Ham United": "WHU", "Wolverhampton": "WOL", "Brighton & Hove Albion": "BHA",
            "Nottm Forest": "NOT", "Nottingham Forest": "NOT", "Leeds United": "LEE"
        }
        
        # Parse CSV content
        import csv, io
        from datetime import datetime
        
        csv_content = file.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        
        # Skip header row
        next(csv_reader, None)
        
        processed_matches = 0
        skipped_matches = 0
        current_date = None
        unmatched_teams = set()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing odds for this gameweek
        cursor.execute("DELETE FROM fixture_odds WHERE gameweek = %s", [gameweek])
        cursor.execute("DELETE FROM team_fixtures WHERE gameweek = %s", [gameweek])
        
        # First pass: collect all valid matches with dates
        all_matches = []
        teams_seen_this_gw = set()  # Track teams for current gameweek only
        
        for row in csv_reader:
            if len(row) < 7:
                continue
                
            # Auto-detect CSV format
            date_str = row[0].strip().strip('"')
            
            # Check if row[2] is a separator (new format) or team name (old format)
            potential_separator = row[2].strip().strip('"')
            is_new_format = potential_separator in [':', '–', '-', 'vs']
            
            if is_new_format:
                # New format: Date, Home, Separator, Away, Odds...
                home_team = row[1].strip().strip('"')
                away_team = row[3].strip().strip('"')
                odds_start_index = 4
            else:
                # Old format: Date, Time, Home, Away, Odds...
                home_team = row[2].strip().strip('"')
                away_team = row[3].strip().strip('"')
                odds_start_index = 4
            
            # Skip if we've already seen both teams for current gameweek
            team_pair = tuple(sorted([home_team, away_team]))
            if team_pair in teams_seen_this_gw:
                continue
                
            try:
                home_odds = float(row[odds_start_index].strip().strip('"'))
                draw_odds = float(row[odds_start_index + 1].strip().strip('"'))
                away_odds = float(row[odds_start_index + 2].strip().strip('"'))
            except (ValueError, IndexError):
                skipped_matches += 1
                continue
                
            # Mark this team pair as seen for current gameweek
            teams_seen_this_gw.add(team_pair)
                
            # Handle date continuation (empty date means same as previous)
            if date_str:
                current_date = date_str
            elif current_date:
                date_str = current_date
            else:
                skipped_matches += 1
                continue
                
            # Parse date (handle different formats)
            try:
                if date_str.startswith('Today'):
                    match_date = datetime.now().date()
                else:
                    # Try parsing "22 Aug 2025" format
                    match_date = datetime.strptime(date_str, '%d %b %Y').date()
            except ValueError:
                try:
                    # Try alternative formats if needed
                    match_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    skipped_matches += 1
                    continue
                    
            # Map team names to codes
            home_code = ODDS_TO_FANTRAX.get(home_team)
            away_code = ODDS_TO_FANTRAX.get(away_team)
            
            if not home_code or not away_code:
                if not home_code:
                    unmatched_teams.add(home_team)
                if not away_code:
                    unmatched_teams.add(away_team)
                skipped_matches += 1
                continue
            
            print(f"VALID: '{home_team}' vs '{away_team}' -> {home_code} vs {away_code} on {match_date}")
            
            # Store match data for filtering
            all_matches.append({
                'date': match_date,
                'home_team': home_team,
                'away_team': away_team,
                'home_code': home_code,
                'away_code': away_code,
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds
            })
        
        # Second pass: take the first 10 matches chronologically (Premier League gameweek = 10 matches)
        # Sort matches by date (earliest first)
        all_matches.sort(key=lambda x: x['date'])
        
        # Take exactly the first 10 matches
        filtered_matches = all_matches[:10]
        
        # Get teams from filtered matches  
        teams_processed = set()
        for match in filtered_matches:
            teams_processed.add(match['home_code'])
            teams_processed.add(match['away_code'])
        
        # Third pass: process the filtered matches
        for match in filtered_matches:
            try:
                cursor.execute("""
                    INSERT INTO fixture_odds 
                    (gameweek, match_date, home_team, away_team, home_odds, draw_odds, away_odds)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (gameweek, home_team, away_team) DO UPDATE SET
                        match_date = EXCLUDED.match_date,
                        home_odds = EXCLUDED.home_odds,
                        draw_odds = EXCLUDED.draw_odds,
                        away_odds = EXCLUDED.away_odds
                """, [gameweek, match['date'], match['home_code'], match['away_code'], match['home_odds'], match['draw_odds'], match['away_odds']])
                
                # Calculate difficulty scores
                def calculate_difficulty_score(home_odds, away_odds, is_home_team):
                    # Calculate implied probabilities (simplified - not accounting for overround)
                    home_prob = 1 / match['home_odds']
                    away_prob = 1 / match['away_odds']
                    total_prob = home_prob + away_prob + (1/match['draw_odds'])
                    
                    # Normalize probabilities
                    home_prob_norm = home_prob / total_prob
                    away_prob_norm = away_prob / total_prob
                    
                    # Get opponent strength
                    opponent_strength = away_prob_norm if is_home_team else home_prob_norm
                    
                    # Map to -10 to +10 scale (0.5 = neutral)
                    difficulty_score = (opponent_strength - 0.5) * 20
                    return round(difficulty_score, 1)
                
                home_difficulty = calculate_difficulty_score(match['home_odds'], match['away_odds'], True)
                away_difficulty = calculate_difficulty_score(match['home_odds'], match['away_odds'], False)
                
                # Insert fixture difficulty data
                cursor.execute("""
                    INSERT INTO team_fixtures 
                    (gameweek, team_code, opponent_code, is_home, difficulty_score)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (gameweek, team_code) DO UPDATE SET
                        opponent_code = EXCLUDED.opponent_code,
                        is_home = EXCLUDED.is_home,
                        difficulty_score = EXCLUDED.difficulty_score
                """, [gameweek, match['home_code'], match['away_code'], True, home_difficulty])
                
                cursor.execute("""
                    INSERT INTO team_fixtures 
                    (gameweek, team_code, opponent_code, is_home, difficulty_score)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (gameweek, team_code) DO UPDATE SET
                        opponent_code = EXCLUDED.opponent_code,
                        is_home = EXCLUDED.is_home,
                        difficulty_score = EXCLUDED.difficulty_score
                """, [gameweek, match['away_code'], match['home_code'], False, away_difficulty])
                
                # NEW: Capture raw fixture snapshots for trend analysis
                cursor.execute("""
                    INSERT INTO raw_fixture_snapshots 
                    (gameweek, team, opponent, is_home, home_odds, draw_odds, away_odds, 
                     difficulty_score, odds_source, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (gameweek, team)
                    DO UPDATE SET 
                        opponent = EXCLUDED.opponent,
                        is_home = EXCLUDED.is_home,
                        home_odds = EXCLUDED.home_odds,
                        draw_odds = EXCLUDED.draw_odds,
                        away_odds = EXCLUDED.away_odds,
                        difficulty_score = EXCLUDED.difficulty_score,
                        import_timestamp = NOW()
                """, [gameweek, match['home_code'], match['away_code'], True, match['home_odds'], match['draw_odds'], match['away_odds'], home_difficulty, 'oddsportal'])
                
                cursor.execute("""
                    INSERT INTO raw_fixture_snapshots 
                    (gameweek, team, opponent, is_home, home_odds, draw_odds, away_odds, 
                     difficulty_score, odds_source, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (gameweek, team)
                    DO UPDATE SET 
                        opponent = EXCLUDED.opponent,
                        is_home = EXCLUDED.is_home,
                        home_odds = EXCLUDED.home_odds,
                        draw_odds = EXCLUDED.draw_odds,
                        away_odds = EXCLUDED.away_odds,
                        difficulty_score = EXCLUDED.difficulty_score,
                        import_timestamp = NOW()
                """, [gameweek, match['away_code'], match['home_code'], False, match['home_odds'], match['draw_odds'], match['away_odds'], away_difficulty, 'oddsportal'])
                
                # Update player snapshots with home/away status, opponent, and fixture difficulty
                cursor.execute("""
                    UPDATE raw_player_snapshots 
                    SET opponent = %s, is_home = %s, fixture_difficulty = %s, odds_import = TRUE
                    WHERE gameweek = %s AND team = %s
                """, [match['away_code'], True, home_difficulty, gameweek, match['home_code']])
                
                cursor.execute("""
                    UPDATE raw_player_snapshots 
                    SET opponent = %s, is_home = %s, fixture_difficulty = %s, odds_import = TRUE
                    WHERE gameweek = %s AND team = %s
                """, [match['home_code'], False, away_difficulty, gameweek, match['away_code']])
                
                processed_matches += 1
                
            except Exception as e:
                print(f"Error processing match {match['home_team']} vs {match['away_team']}: {e}")
                skipped_matches += 1
                continue
                
        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()
        
        # Debug logging
        print(f"\n=== ODDS IMPORT DEBUG (GW{gameweek}) ===")
        print(f"Total valid matches found: {len(all_matches)}")
        print(f"Matches after filtering: {len(filtered_matches)}")
        print(f"Teams processed: {len(teams_processed)}")
        print("Teams in filtered matches:", sorted(teams_processed))
        
        # Calculate filtering stats
        total_valid_matches = len(all_matches)
        skipped_due_to_filtering = total_valid_matches - len(filtered_matches)
        
        # Return success response
        return jsonify({
            'success': True,
            'processed_matches': len(filtered_matches),
            'skipped_matches': skipped_matches + skipped_due_to_filtering,
            'gameweek': gameweek,
            'message': f'Successfully imported {len(filtered_matches)} matches for gameweek {gameweek} (filtered from {total_valid_matches} valid matches to ensure only earliest match per team)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500

# ===============================
# VALIDATION UI ROUTES
# ===============================

@app.route('/import-validation')
def import_validation_ui():
    """Serve the import validation UI"""
    return render_template('import_validation.html')

@app.route('/form-upload')
def form_upload_ui():
    """Serve the form data upload UI"""
    return render_template('form_upload.html')

@app.route('/odds-upload')
def odds_upload_ui():
    """Serve the fixture odds upload UI"""
    return render_template('odds_upload.html')

@app.route('/monitoring')
def monitoring_ui():
    """Serve the monitoring dashboard UI"""
    return render_template('monitoring.html')

@app.route('/api/monitoring/metrics', methods=['GET'])
def get_monitoring_metrics():
    """
    Get comprehensive monitoring metrics for the name matching system
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get overall mapping statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_mappings,
                COUNT(*) FILTER (WHERE verified = true) as verified_mappings,
                COUNT(*) FILTER (WHERE verified = false) as unverified_mappings,
                AVG(confidence_score) as avg_confidence,
                COUNT(DISTINCT source_system) as source_systems,
                SUM(usage_count) as total_usage
            FROM name_mappings
        """)
        overall_stats = dict(cursor.fetchone())
        
        # Get statistics by source system
        cursor.execute("""
            SELECT 
                source_system,
                COUNT(*) as total_mappings,
                COUNT(*) FILTER (WHERE verified = true) as verified,
                AVG(confidence_score) as avg_confidence,
                SUM(usage_count) as usage_count,
                COUNT(*) FILTER (WHERE confidence_score >= 90) as high_confidence,
                COUNT(*) FILTER (WHERE confidence_score < 50) as low_confidence
            FROM name_mappings
            GROUP BY source_system
            ORDER BY total_mappings DESC
        """)
        source_system_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get recent mapping activity (last 7 days)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_mappings,
                COUNT(*) FILTER (WHERE verified = true) as verified_on_date
            FROM name_mappings
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        recent_activity = [dict(row) for row in cursor.fetchall()]
        
        # Get match quality distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 95 THEN '95-100%'
                    WHEN confidence_score >= 85 THEN '85-94%'
                    WHEN confidence_score >= 70 THEN '70-84%'
                    WHEN confidence_score >= 50 THEN '50-69%'
                    ELSE '<50%'
                END as confidence_range,
                COUNT(*) as count
            FROM name_mappings
            GROUP BY 
                CASE 
                    WHEN confidence_score >= 95 THEN '95-100%'
                    WHEN confidence_score >= 85 THEN '85-94%'
                    WHEN confidence_score >= 70 THEN '70-84%'
                    WHEN confidence_score >= 50 THEN '50-69%'
                    ELSE '<50%'
                END
            ORDER BY count DESC
        """)
        confidence_distribution = [dict(row) for row in cursor.fetchall()]
        
        # Get top performers (most used mappings)
        cursor.execute("""
            SELECT 
                source_name,
                fantrax_name,
                source_system,
                usage_count,
                confidence_score,
                verified
            FROM name_mappings
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        top_performers = [dict(row) for row in cursor.fetchall()]
        
        # Get problem mappings (low confidence, unverified)
        cursor.execute("""
            SELECT 
                source_name,
                fantrax_name,
                source_system,
                confidence_score,
                usage_count,
                created_at
            FROM name_mappings
            WHERE verified = false AND confidence_score < 70
            ORDER BY usage_count DESC, confidence_score ASC
            LIMIT 10
        """)
        problem_mappings = [dict(row) for row in cursor.fetchall()]
        
        # Get match type distribution
        cursor.execute("""
            SELECT 
                match_type,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence
            FROM name_mappings
            GROUP BY match_type
            ORDER BY count DESC
        """)
        match_type_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Calculate derived metrics
        verification_rate = (overall_stats['verified_mappings'] / overall_stats['total_mappings'] * 100) if overall_stats['total_mappings'] > 0 else 0
        
        return jsonify({
            'timestamp': time.time(),
            'overall_stats': {
                **overall_stats,
                'verification_rate': round(verification_rate, 2)
            },
            'source_system_breakdown': source_system_stats,
            'recent_activity': recent_activity,
            'confidence_distribution': confidence_distribution,
            'top_performers': top_performers,
            'problem_mappings': problem_mappings,
            'match_type_distribution': match_type_stats,
            'health_indicators': {
                'high_confidence_rate': (sum(1 for s in source_system_stats for _ in range(s['high_confidence'])) / overall_stats['total_mappings'] * 100) if overall_stats['total_mappings'] > 0 else 0,
                'low_confidence_rate': (sum(1 for s in source_system_stats for _ in range(s['low_confidence'])) / overall_stats['total_mappings'] * 100) if overall_stats['total_mappings'] > 0 else 0,
                'avg_confidence': round(overall_stats['avg_confidence'], 2) if overall_stats['avg_confidence'] else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': time.time()
        }), 500

# ===============================
# UNDERSTAT INTEGRATION API
# ===============================

@app.route('/api/understat/sync', methods=['POST'])
def sync_understat_data():
    """Sync Understat data with database using Global Name Matching System"""
    try:
        # Check if integration package is available
        if not INTEGRATION_AVAILABLE:
            return jsonify({
                'error': 'Integration package not available in production mode',
                'message': 'This feature is only available in development environment'
            }), 503
            
        # Initialize integrator to get raw Understat data
        integrator = UnderstatIntegrator(DB_CONFIG)
        understat_df = integrator.extract_understat_per90_stats()
        
        if understat_df.empty:
            return jsonify({'error': 'No Understat data available'}), 500
        
        # Use Global Name Matching System for improved matching
        matcher = UnifiedNameMatcher(DB_CONFIG)
        matched_players = []
        unmatched_players = []
        
        for idx, player in understat_df.iterrows():
            player_name = player.get('player_name', '')
            team = player.get('team', '')
            
            # Try to match using Global Name Matching System
            match_result = matcher.match_player(
                source_name=player_name,
                source_system='understat',
                team=team,
                position=None  # Understat doesn't always have reliable position data
            )
            
            if match_result['fantrax_id'] is not None and match_result['confidence'] >= 70:
                # High confidence match - add to matched list
                player_dict = player.to_dict()
                player_dict['fantrax_id'] = match_result['fantrax_id']
                player_dict['fantrax_name'] = match_result['fantrax_name']
                player_dict['confidence'] = match_result['confidence']
                matched_players.append(player_dict)
            else:
                # Low confidence or no match - add to unmatched list for manual review
                player_dict = player.to_dict()
                player_dict['suggestions'] = match_result.get('suggested_matches', [])
                player_dict['needs_review'] = match_result.get('needs_review', True)
                player_dict['confidence'] = match_result.get('confidence', 0)
                unmatched_players.append(player_dict)
        
        # Update database with matched players
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updated_count = 0
        for player in matched_players:
            cursor.execute("""
                UPDATE players 
                SET minutes = %s, xg90 = %s, xa90 = %s, xgi90 = %s,
                    last_understat_update = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [
                player['minutes'], 
                round(player['xG90'], 3),
                round(player['xA90'], 3), 
                round(player['xGI90'], 3),
                player['fantrax_id']
            ])
            
            # NEW: Update raw snapshots with xG data and minutes for all existing gameweeks
            cursor.execute("""
                UPDATE raw_player_snapshots 
                SET minutes_played = %s, xg90 = %s, xa90 = %s, xgi90 = %s, 
                    understat_import = TRUE, import_timestamp = NOW()
                WHERE player_id = %s
            """, [
                player['minutes'],
                round(player['xG90'], 3),
                round(player['xA90'], 3),
                round(player['xGI90'], 3),
                player['fantrax_id']
            ])
            
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        # Store unmatched players for validation UI (if any)
        if unmatched_players:
            # Save unmatched data to session or temporary storage for validation
            import json
            import os
            validation_data = {
                'source_system': 'understat',
                'unmatched_players': unmatched_players,
                'timestamp': time.time()
            }
            
            # Save to temporary file for validation UI to access
            temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            with open(os.path.join(temp_dir, 'understat_unmatched.json'), 'w') as f:
                json.dump(validation_data, f)
        
        # Calculate match rate
        total_players = len(matched_players) + len(unmatched_players)
        match_rate = (len(matched_players) / total_players * 100) if total_players > 0 else 0
        
        # Update config
        system_params = load_system_parameters()
        system_params['xgi_integration']['last_sync'] = time.time()
        system_params['xgi_integration']['matched_players'] = len(matched_players)
        system_params['xgi_integration']['unmatched_players'] = len(unmatched_players)
        save_system_parameters(system_params)
        
        response_data = {
            'success': True,
            'total_understat_players': total_players,
            'successfully_matched': len(matched_players),
            'unmatched_players': len(unmatched_players),
            'match_rate': match_rate,
            'players_updated': updated_count
        }
        
        # Add verification redirect if there are unmatched players
        if len(unmatched_players) > 0:
            response_data['verification_needed'] = True
            response_data['verification_url'] = '/import-validation?source=understat'
            response_data['message'] = f'Sync completed. {len(unmatched_players)} players need manual verification.'
        else:
            response_data['verification_needed'] = False
            response_data['message'] = 'Sync completed successfully. All players matched.'
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/understat/get-unmatched-data', methods=['GET'])
def get_understat_unmatched_data():
    """Load saved unmatched Understat players for validation UI"""
    try:
        import os
        import json
        
        # Check if unmatched data file exists
        temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
        unmatched_file = os.path.join(temp_dir, 'understat_unmatched.json')
        
        if not os.path.exists(unmatched_file):
            return jsonify({
                'status': 'error',
                'message': 'No unmatched Understat data found. Please sync Understat data first.'
            }), 404
        
        # Load the saved unmatched data
        with open(unmatched_file, 'r') as f:
            saved_data = json.load(f)
        
        # Check data age (only use if less than 1 hour old)
        data_age_hours = (time.time() - saved_data['timestamp']) / 3600
        if data_age_hours > 1:
            return jsonify({
                'status': 'error',
                'message': f'Understat data is {data_age_hours:.1f} hours old. Please sync again.'
            }), 410
        
        # Convert saved data to validation UI format
        unmatched_players = saved_data['unmatched_players']
        needs_review_count = len(unmatched_players)
        
        # Understat team name mapping to database team codes (2025-26 Premier League season)
        understat_team_mapping = {
            'Arsenal': 'ARS',
            'Aston Villa': 'AVL',
            'Bournemouth': 'BOU', 
            'Brentford': 'BRF',  # Database uses BRF, not BRE
            'Brighton': 'BHA',
            'Brighton and Hove Albion': 'BHA',  # Alternative name
            'Burnley': 'BUR',
            'Chelsea': 'CHE',
            'Crystal Palace': 'CRY',
            'Everton': 'EVE',
            'Fulham': 'FUL',
            'Leeds United': 'LEE',
            'Liverpool': 'LIV',
            'Manchester City': 'MCI',
            'Manchester United': 'MUN', 
            'Newcastle United': 'NEW',
            'Nottingham Forest': 'NOT',  # Database uses NOT, not NFO
            'Sunderland': 'SUN',
            'Tottenham': 'TOT',
            'Tottenham Hotspur': 'TOT',  # Alternative name
            'West Ham United': 'WHU',
            'Wolverhampton Wanderers': 'WOL'
        }
        
        # Current Premier League teams only (2025-26 season) - all 20 teams
        current_pl_teams = {
            'ARS', 'AVL', 'BOU', 'BRF', 'BHA', 'BUR', 'CHE', 'CRY', 
            'EVE', 'FUL', 'LEE', 'LIV', 'MCI', 'MUN', 'NEW', 'NOT', 
            'SUN', 'TOT', 'WHU', 'WOL'
        }
        
        # Known data corruption patterns in Understat source
        KNOWN_CORRUPTED_ASSIGNMENTS = {
            # Fulham vs Wolves match has reversed team assignments
            'Fulham': 'Wolverhampton Wanderers',
            'Wolverhampton Wanderers': 'Fulham',
        }
        
        # Team validation for known Understat data issues
        def validate_and_correct_team(player_name, understat_team):
            """Check if player's team assignment matches our database and correct if needed"""
            
            # Step 1: Check for known corruption patterns first
            if understat_team in KNOWN_CORRUPTED_ASSIGNMENTS:
                potential_correct_team = KNOWN_CORRUPTED_ASSIGNMENTS[understat_team]
                print(f"Corruption check: {player_name} claims {understat_team}, checking if actually {potential_correct_team}")
                
                # Verify if player actually belongs to the "swapped" team
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        correct_team_code = understat_team_mapping.get(potential_correct_team, potential_correct_team)
                        cursor.execute("""
                            SELECT name, team FROM players 
                            WHERE team = %s AND (
                                LOWER(name) LIKE LOWER(%s) 
                                OR LOWER(name) LIKE LOWER(%s)
                                OR LOWER(%s) LIKE LOWER(CONCAT('%%', name, '%%'))
                            )
                            LIMIT 1
                        """, (correct_team_code, f'%{player_name}%', f'{player_name}%', player_name))
                        result = cursor.fetchone()
                        
                        if result:
                            print(f"CORRUPTION DETECTED: {player_name} actually plays for {potential_correct_team}, not {understat_team}")
                            return potential_correct_team, understat_team_mapping.get(potential_correct_team, potential_correct_team)
            
            # Step 2: Standard database lookup for other cases
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Use fuzzy matching for name
                    cursor.execute("""
                        SELECT name, team FROM players 
                        WHERE LOWER(name) LIKE LOWER(%s) 
                        OR LOWER(name) LIKE LOWER(%s)
                        OR LOWER(%s) LIKE LOWER(CONCAT('%%', name, '%%'))
                        LIMIT 1
                    """, (f'%{player_name}%', f'{player_name}%', player_name))
                    result = cursor.fetchone()
                    
                    if result:
                        db_name, actual_team = result
                        mapped_understat_team = understat_team_mapping.get(understat_team, understat_team)
                        
                        if actual_team != mapped_understat_team:
                            print(f"Team mismatch: {player_name} - Understat says {understat_team} ({mapped_understat_team}) but DB has {actual_team}")
                            # Return the correct team name for the dropdown
                            reverse_mapping = {v: k for k, v in understat_team_mapping.items()}
                            correct_understat_name = reverse_mapping.get(actual_team, actual_team)
                            return correct_understat_name, actual_team
                    
            return understat_team, understat_team_mapping.get(understat_team, understat_team)

        # Format players for validation UI
        formatted_players = []
        position_breakdown = {}
        
        for player in unmatched_players:
            # Extract player info
            player_name = player.get('player_name', '')
            understat_team = player.get('team', '')
            position = 'Unknown'  # Understat doesn't provide reliable position data
            
            # Validate and correct team assignment
            corrected_understat_team, db_team = validate_and_correct_team(player_name, understat_team)
            
            # Skip players from teams not in current Premier League
            if db_team not in current_pl_teams:
                print(f"Skipping {player_name} from {understat_team} - not in current Premier League")
                continue
            
            # Update position breakdown
            if position not in position_breakdown:
                position_breakdown[position] = {'total': 0, 'matched': 0, 'match_rate': 0}
            position_breakdown[position]['total'] += 1
            
            # Format for validation UI
            formatted_player = {
                'original_name': player_name,
                'original_team': db_team,  # Use corrected team code for consistency
                'original_position': position,
                'needs_review': True,
                'match_result': {
                    'fantrax_name': None,
                    'confidence': 0,
                    'suggested_matches': player.get('suggestions', [])
                },
                'original_data': {**player, 'team': corrected_understat_team}  # Update team in original data
            }
            
            formatted_players.append(formatted_player)
        
        # Create summary statistics
        summary = {
            'total': needs_review_count,
            'matched': 0,  # All are unmatched at this point
            'needs_review': needs_review_count,
            'failed': 0,
            'match_rate': 0.0
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_players': saved_data.get('total_players', needs_review_count),
                'matched_players': saved_data.get('matched_players', 0),
                'unmatched_count': needs_review_count,
                'unmatched_details': formatted_players,
                'summary': summary,
                'position_breakdown': position_breakdown,
                'source_system': 'understat',
                'timestamp': saved_data['timestamp']
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/understat/unmatched', methods=['GET'])
def get_unmatched_understat():
    """Get list of unmatched Understat players for review (legacy endpoint)"""
    try:
        # Check if integration package is available
        if not INTEGRATION_AVAILABLE:
            return jsonify({
                'error': 'Integration package not available in production mode',
                'message': 'This feature is only available in development environment',
                'unmatched_players': []
            }), 503
            
        integrator = UnderstatIntegrator(DB_CONFIG)
        understat_df = integrator.extract_understat_per90_stats()
        
        if understat_df.empty:
            return jsonify({'players': []})
        
        matched_df, unmatched_df = integrator.match_fantrax_names(understat_df)
        
        # Add suggestions for unmatched
        unmatched_with_suggestions = []
        for idx, player in unmatched_df.iterrows():
            player_dict = player.to_dict()
            player_dict['suggestions'] = player.get('suggested_matches', [])
            unmatched_with_suggestions.append(player_dict)
        
        return jsonify({
            'players': unmatched_with_suggestions,
            'total': len(unmatched_df)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/understat/stats', methods=['GET'])
def get_understat_stats():
    """Get Understat integration statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE xgi90 > 0) as players_with_xgi,
                COUNT(*) as total_players,
                AVG(xgi90) FILTER (WHERE xgi90 > 0) as avg_xgi90,
                MAX(xgi90) as max_xgi90,
                MIN(last_understat_update) as oldest_update,
                MAX(last_understat_update) as newest_update
            FROM players
        """)
        
        stats = dict(cursor.fetchone())
        
        # Get top xGI players
        cursor.execute("""
            SELECT name, team, position, xgi90, xg90, xa90, minutes
            FROM players
            WHERE xgi90 > 0
            ORDER BY xgi90 DESC
            LIMIT 10
        """)
        
        top_players = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        system_params = load_system_parameters()
        xgi_config = system_params.get('xgi_integration', {})
        
        return jsonify({
            'stats': stats,
            'top_players': top_players,
            'config': {
                'enabled': xgi_config.get('enabled', False),
                'mode': xgi_config.get('multiplier_mode', 'direct'),
                'strength': xgi_config.get('multiplier_strength', 1.0),
                'last_sync': xgi_config.get('last_sync')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/understat/apply-mappings', methods=['POST'])
def apply_understat_mappings():
    """Apply confirmed name mappings for Understat players and update the database"""
    try:
        print("=== APPLY-MAPPINGS ENDPOINT HIT ===")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        data = request.get_json()
        confirmed_mappings = data.get('confirmed_mappings', {})
        dry_run = data.get('dry_run', False)
        
        # DEBUG: Log the request payload
        print(f"=== APPLY-MAPPINGS DEBUG ===")
        print(f"Request data keys: {list(data.keys())}")
        print(f"Confirmed mappings count: {len(confirmed_mappings)}")
        print(f"Dry run: {dry_run}")
        
        # Handle case where frontend sends players array instead of confirmed_mappings
        if not confirmed_mappings and 'players' in data:
            print("WARNING: Frontend sent 'players' array instead of 'confirmed_mappings'")
            print("This indicates the frontend needs to be fixed to send user selections properly")
            return jsonify({
                'error': 'Invalid request format: Frontend sent raw player data instead of confirmed user mappings. Please ensure manual player selections are captured correctly in the UI.',
                'debug_info': {
                    'received_keys': list(data.keys()),
                    'confirmed_mappings_count': len(confirmed_mappings),
                    'players_count': len(data.get('players', [])) if 'players' in data else 0
                }
            }), 400
        
        if not confirmed_mappings:
            print("WARNING: No confirmed mappings received - returning empty response")
            return jsonify({
                'status': 'success',
                'import_count': 0,
                'message': 'No mappings to apply - no manual selections were captured from the UI',
                'updated_players': []
            })
        
        # Load the saved unmatched data
        temp_file = os.path.join('temp', 'understat_unmatched.json')
        if not os.path.exists(temp_file):
            return jsonify({'error': 'No unmatched Understat data found. Please sync again.'}), 404
        
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        
        # Check data age (must be < 1 hour old)
        data_age_minutes = (time.time() - saved_data['timestamp']) / 60
        if data_age_minutes > 60:
            return jsonify({'error': 'Unmatched data is too old. Please sync again.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Create understat_name_mappings table if it doesn't exist
        create_table_query = """
            CREATE TABLE IF NOT EXISTS understat_name_mappings (
                id SERIAL PRIMARY KEY,
                understat_name VARCHAR(255) UNIQUE NOT NULL,
                fantrax_id VARCHAR(50) NOT NULL,
                confidence DECIMAL(5,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("Created/verified understat_name_mappings table")
        
        updated_players = []
        
        for original_name, mapping in confirmed_mappings.items():
            fantrax_id = mapping.get('fantrax_id')
            fantrax_name = mapping.get('fantrax_name')
            
            if not fantrax_id or not fantrax_name:
                print(f"Warning: Missing ID or name for {original_name}: fantrax_id={fantrax_id}, fantrax_name={fantrax_name}")
                continue
            
            # Find the original Understat data for this player
            understat_player = None
            for player in saved_data['unmatched_players']:  # Correct key: unmatched_players
                if player['player_name'] == original_name:  # Correct field: player_name
                    understat_player = player
                    break
            
            if not understat_player:
                print(f"Warning: Could not find Understat data for {original_name}")
                continue
            
            if not dry_run:
                try:
                    # Update the database with Understat stats
                    update_query = """
                        UPDATE players 
                        SET xg90 = %s, xa90 = %s, xgi90 = %s, minutes = %s,
                            last_understat_update = %s
                        WHERE id = %s
                    """
                    
                    cursor.execute(update_query, (
                        understat_player.get('xG90', 0),  # Correct case: xG90
                        understat_player.get('xA90', 0),   # Correct case: xA90
                        understat_player.get('xGI90', 0),  # Correct case: xGI90
                        understat_player.get('minutes', 0),
                        datetime.now(),
                        fantrax_id  # Correct: fantrax_id value goes to 'id' column
                    ))
                    
                    if cursor.rowcount == 0:
                        print(f"Warning: No player found with id={fantrax_id} for {original_name}")
                        continue
                    
                except Exception as e:
                    print(f"Database error updating {original_name}: {e}")
                    continue
                
                # Add to understat_name_mappings for backwards compatibility
                understat_mapping_query = """
                    INSERT INTO understat_name_mappings (understat_name, fantrax_id, confidence, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (understat_name) DO UPDATE SET
                        fantrax_id = EXCLUDED.fantrax_id,
                        confidence = EXCLUDED.confidence,
                        updated_at = %s
                """
                
                cursor.execute(understat_mapping_query, (
                    original_name,
                    fantrax_id,
                    mapping.get('confidence', 100.0),
                    datetime.now(),
                    datetime.now()
                ))
                
                # ALSO add to Global Name Matching System for cross-source benefits
                global_mapping_query = """
                    INSERT INTO name_mappings (
                        source_system, source_name, fantrax_id, fantrax_name, 
                        confidence_score, match_type, verified, verification_date, 
                        verified_by, last_used, usage_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_system, source_name) DO UPDATE SET
                        fantrax_id = EXCLUDED.fantrax_id,
                        fantrax_name = EXCLUDED.fantrax_name,
                        confidence_score = EXCLUDED.confidence_score,
                        match_type = EXCLUDED.match_type,
                        verified = EXCLUDED.verified,
                        verification_date = EXCLUDED.verification_date,
                        verified_by = EXCLUDED.verified_by,
                        last_used = EXCLUDED.last_used,
                        usage_count = EXCLUDED.usage_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                try:
                    cursor.execute(global_mapping_query, (
                        'understat',                         # source_system
                        original_name,                       # source_name  
                        fantrax_id,                         # fantrax_id
                        fantrax_name,                       # fantrax_name
                        mapping.get('confidence', 100.0),   # confidence_score
                        'manual',                           # match_type
                        True,                               # verified
                        datetime.now(),                     # verification_date
                        'user_manual_import',               # verified_by
                        datetime.now(),                     # last_used
                        1                                   # usage_count
                    ))
                    print(f"Added {original_name} → {fantrax_name} to Global Name Matching System")
                except Exception as e:
                    print(f"Warning: Could not add to Global Name Matching System: {e}")
                    # Continue - understat_name_mappings still worked
            
            updated_players.append({
                'understat_name': original_name,
                'fantrax_name': fantrax_name,
                'fantrax_id': fantrax_id,
                'xGI90': understat_player.get('xGI90', 0)  # Correct case: xGI90
            })
        
        if not dry_run:
            conn.commit()
            
            # Clean up the temp file after successful import
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'import_count': len(updated_players),
            'message': f"{'Would update' if dry_run else 'Updated'} {len(updated_players)} players with Understat data",
            'updated_players': updated_players
        })
        
    except Exception as e:
        print(f"CRITICAL ERROR in apply_understat_mappings: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'error': f'Database error: {str(e)}',
            'error_type': type(e).__name__,
            'debug': True
        }), 500

def parse_formation_csv(lines, cursor):
    """
    Parse formation matrix CSV format from FFS scraping.
    Returns list of player dictionaries with position constraint checking.
    """
    import csv
    from io import StringIO
    
    # Team name mapping from CSV (full names) to database (abbreviations)
    # Based on TEAM_CODE_MAPPING.md 
    team_name_mapping = {
        'arsenal': 'ARS',
        'aston villa': 'AVL', 
        'bournemouth': 'BOU',
        'brentford': 'BRF',  # Using BRF as per current database
        'brighton and hove albion': 'BHA',
        'brighton & hove albion': 'BHA',
        'burnley': 'BUR',
        'chelsea': 'CHE',
        'crystal palace': 'CRY',
        'everton': 'EVE',
        'fulham': 'FUL',
        'leeds united': 'LEE',
        'liverpool': 'LIV',
        'manchester city': 'MCI',
        'manchester united': 'MUN',
        'newcastle united': 'NEW',
        'nottingham forest': 'NOT',  # Using NOT as per current database
        'sunderland': 'SUN',
        'tottenham hotspur': 'TOT',
        'west ham united': 'WHU',
        'wolverhampton wanderers': 'WOL'
    }
    
    players_to_process = []
    
    for line in lines:
        if not line.strip():
            continue
        # Use CSV reader to properly handle quotes
        csv_reader = csv.reader(StringIO(line))
        line_data = next(csv_reader)
        team_raw = line_data[0].strip().strip('"')
        
        # Map team name from full name to database abbreviation
        team = team_name_mapping.get(team_raw.lower(), team_raw)
        
        # Process each formation position (skip team column)
        for pos_idx, player_name in enumerate(line_data[1:12], 1):  # Positions 1-11
            player_name = player_name.strip()
            if not player_name:
                continue
                
            # Apply position constraints
            predicted_position = None
            position_conflict = False
            
            if pos_idx == 1:
                # Position 1: Always Goalkeeper
                predicted_position = 'G'
            elif 2 <= pos_idx <= 4:
                # Positions 2-4: Always Defenders (confirmed by user)
                predicted_position = 'D'
            elif 5 <= pos_idx <= 8:
                # Positions 5-8: Could be D or M, prefer database lookup but default to M
                db_position = lookup_player_position(cursor, player_name, team)
                if db_position and db_position in ['D', 'M']:
                    predicted_position = db_position
                elif db_position and db_position not in ['D', 'M']:
                    # Database shows F or G, but formation says D/M - conflict!
                    predicted_position = 'M'  # Default to midfielder for positions 5-8
                    position_conflict = True
                else:
                    # No database match, default to midfielder for positions 5-8
                    predicted_position = 'M'
            elif 9 <= pos_idx <= 11:
                # Positions 9-11: Could be M or F, prefer database lookup but default to F
                db_position = lookup_player_position(cursor, player_name, team)
                if db_position and db_position in ['M', 'F']:
                    predicted_position = db_position
                elif db_position and db_position == 'D':
                    # Database shows D, but formation says M/F - conflict!
                    predicted_position = 'F'  # Default to forward for positions 9-11
                    position_conflict = True
                else:
                    # No database match, default to forward for positions 9-11
                    predicted_position = 'F'
            
            player_info = {
                'name': player_name,
                'team': team,
                'position': predicted_position or 'Unknown',
                'status': 'starter',  # All players in formation are starters
                'formation_position': pos_idx,
                'position_conflict': position_conflict
            }
            
            players_to_process.append(player_info)
    
    return players_to_process

def parse_individual_csv(lines):
    """
    Parse individual player CSV format (original format).
    Returns list of player dictionaries.
    """
    import csv
    from io import StringIO
    
    players_to_process = []
    
    for line in lines:
        if not line.strip():
            continue
        # Use CSV reader to properly handle quotes
        csv_reader = csv.reader(StringIO(line))
        line_data = next(csv_reader)
        if len(line_data) < 4:
            continue
            
        team = line_data[0].strip()
        player_name = line_data[1].strip()
        position = line_data[2].strip()
        status = line_data[3].strip()
        
        player_info = {
            'name': player_name,
            'team': team,
            'position': position,
            'status': status,
            'formation_position': None,
            'position_conflict': False
        }
        
        players_to_process.append(player_info)
    
    return players_to_process

def lookup_player_position(cursor, player_name, team):
    """
    Look up player position in database for position constraint checking.
    Returns position from database or None if not found.
    """
    try:
        # Try exact name match first
        cursor.execute("""
            SELECT position FROM players 
            WHERE LOWER(name) = LOWER(%s) AND LOWER(team) = LOWER(%s)
            LIMIT 1
        """, [player_name, team])
        
        result = cursor.fetchone()
        if result:
            return result[0]
            
        # Try partial name match if exact fails
        cursor.execute("""
            SELECT position FROM players 
            WHERE LOWER(name) LIKE LOWER(%s) AND LOWER(team) = LOWER(%s)
            LIMIT 1
        """, [f'%{player_name}%', team])
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        print(f"Database lookup error for {player_name}: {e}")
        return None


# =============================================================================
# FORMULA OPTIMIZATION v2.0 ENDPOINTS
# =============================================================================

@app.route('/api/calculate-values-v2', methods=['POST'])
def calculate_values_v2():
    """
    Calculate player values using Formula Optimization v2.0
    Supports both v2.0 and legacy v1.0 for comparison
    """
    try:
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        
        data = request.get_json() or {}
        formula_version = data.get('formula_version', 'v2.0')
        
        # Use GameweekManager for consistent gameweek detection
        gameweek = data.get('gameweek', gw_manager.get_current_gameweek())
        compare_versions = data.get('compare_versions', False)
        
        # Load current parameters
        parameters = load_system_parameters()
        
        # Always use V2.0 Enhanced Formula Engine
        engine = FormulaEngineV2(DB_CONFIG, parameters)
        
        # Get player data from database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Enhanced query to get all necessary data including fresh PPG calculation
        cursor.execute("""
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                p.xgi90,
                p.baseline_xgi,
                pm.price,
                -- Calculate fresh PPG using same logic as form import
                CASE 
                    WHEN COALESCE(pgd.games_played, 0) > 0 
                    THEN COALESCE(pf_max.total_points, 0) / pgd.games_played
                    ELSE 0 
                END as ppg,
                pm.form_multiplier,
                pm.fixture_multiplier,
                pm.starter_multiplier,
                pm.xgi_multiplier,
                tf.difficulty_score as fixture_difficulty,
                COALESCE(pgd.games_played, 0) as games_played,
                COALESCE(pgd.games_played_historical, 0) as games_played_historical,
                CASE 
                    WHEN COALESCE(pgd.games_played_historical, 0) > 0 
                    THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
                    ELSE NULL 
                END as historical_ppg
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            LEFT JOIN (
                SELECT player_id, MAX(points) as total_points
                FROM player_form
                GROUP BY player_id
            ) pf_max ON p.id = pf_max.player_id
            LEFT JOIN team_fixtures tf ON p.team = tf.team_code AND tf.gameweek = %s
            LEFT JOIN player_games_data pgd ON p.id = pgd.player_id AND pm.gameweek = pgd.gameweek
            WHERE pm.gameweek = %s
            ORDER BY pm.true_value DESC NULLS LAST
            LIMIT 100
        """, [gameweek, gameweek])
        
        players = cursor.fetchall()
        conn.close()
        
        # Calculate values for all players
        results = []
        for player in players:
            calculation = engine.calculate_player_value(dict(player))
            results.append(calculation)
        
        # V2.0 calculations only - no version comparisons needed
        
        # Store calculations in database
        if results:
            store_v2_calculations(results, formula_version, gameweek)
        
        return jsonify({
            'success': True,
            'formula_version': formula_version,
            'player_count': len(results),
            'gameweek': gameweek,
            'results': results[:50],  # Limit response size
            'calculation_time': time.time(),
            'summary': {
                'avg_true_value': sum(r['true_value'] for r in results) / len(results) if results else 0,
                'avg_roi': sum(r['roi'] for r in results) / len(results) if results else 0,
                'top_true_value': max((r['true_value'] for r in results), default=0),
                'top_roi': max((r['roi'] for r in results), default=0)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'formula_version': formula_version if 'formula_version' in locals() else 'unknown'
        }), 500




def store_v2_calculations(calculations: List[Dict], version: str, gameweek: int = None):
    """Store v2.0 calculation results in database"""
    try:
        # Use GameweekManager if no gameweek specified
        if gameweek is None:
            from src.gameweek_manager import GameweekManager
            gw_manager = GameweekManager()
            gameweek = gw_manager.get_current_gameweek()
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for calc in calculations:
            # Update player_metrics with v2.0 values
            cursor.execute("""
                UPDATE player_metrics 
                SET 
                    true_value = %s,
                    value_score = %s,
                    ppg = %s,
                    form_multiplier = %s,
                    fixture_multiplier = %s,
                    starter_multiplier = %s,
                    xgi_multiplier = %s,
                    last_updated = NOW()
                WHERE player_id = %s AND gameweek = %s
            """, [
                calc['true_value'],
                calc['roi'],  # In v2.0, value_score becomes ROI
                calc.get('base_ppg', 0),  # Store the blended PPG from calculation
                calc['multipliers']['form'],
                calc['multipliers']['fixture'],
                calc['multipliers']['starter'],
                calc['multipliers']['xgi'],
                calc['player_id'],
                gameweek
            ])
            
            # Store in players table (new v2.0 columns)
            cursor.execute("""
                UPDATE players 
                SET 
                    true_value = %s,
                    roi = %s,
                    formula_version = %s,
                    blended_ppg = %s
                WHERE id = %s
            """, [
                calc['true_value'],
                calc['roi'],
                version,
                calc.get('base_ppg'),
                calc['player_id']
            ])
        
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Stored {len(calculations)} calculations for {version}")
        
    except Exception as e:
        print(f"[ERROR] Error storing v2.0 calculations: {e}")
        if conn:
            conn.rollback()
            conn.close()


@app.route('/api/verify-ppg', methods=['GET'])
def verify_ppg():
    """Verify PPG calculations are consistent between stored and calculated values"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get current gameweek
        from src.gameweek_manager import GameweekManager
        gw_manager = GameweekManager()
        gameweek = gw_manager.get_current_gameweek()
        
        cursor.execute("""
            SELECT 
                p.name,
                p.team,
                pm.ppg as stored_ppg,
                CASE 
                    WHEN COALESCE(pgd.games_played, 0) > 0 
                    THEN COALESCE(pf.total_points, 0) / pgd.games_played
                    ELSE 0 
                END as calculated_ppg,
                ROUND(ABS(pm.ppg - COALESCE(pf.total_points / NULLIF(pgd.games_played, 0), 0)), 2) as difference,
                pf.total_points,
                pgd.games_played,
                pm.true_value,
                p.roi
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            LEFT JOIN (
                SELECT player_id, MAX(points) as total_points 
                FROM player_form GROUP BY player_id
            ) pf ON p.id = pf.player_id
            LEFT JOIN player_games_data pgd ON p.id = pgd.player_id AND pgd.gameweek = %s
            WHERE pm.gameweek = %s
              AND p.team != 'TST'  -- Exclude test players
              AND COALESCE(pgd.games_played, 0) > 0  -- Only players with games played
            ORDER BY ABS(pm.ppg - COALESCE(pf.total_points / NULLIF(pgd.games_played, 0), 0)) DESC
            LIMIT 50
        """, [gameweek, gameweek])
        
        results = cursor.fetchall()
        
        # Calculate summary statistics
        total_players = len(results)
        discrepancies = len([r for r in results if r['difference'] > 0.1])
        
        conn.close()
        
        return jsonify({
            'gameweek': gameweek,
            'summary': {
                'total_players_checked': total_players,
                'players_with_discrepancies': discrepancies,
                'accuracy_rate': round((total_players - discrepancies) / total_players * 100, 1) if total_players > 0 else 100
            },
            'top_discrepancies': results[:20],  # Show top 20 discrepancies
            'message': f'PPG verification completed for gameweek {gameweek}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================
# SPRINT 3: VALIDATION API ENDPOINTS
# ================================

@app.route('/api/run-validation', methods=['POST'])
def run_validation_endpoint():
    """
    API endpoint to run backtesting validation
    
    Request body:
    {
        "start_gameweek": 1,
        "end_gameweek": 10, 
        "model_version": "v2.0",
        "season": "2024/25"
    }
    """
    try:
        data = request.get_json() or {}
        
        start_gw = data.get('start_gameweek', 1)
        end_gw = data.get('end_gameweek', 5)
        model_version = data.get('model_version', 'v2.0')
        season = data.get('season', '2024/25')
        
        # Import validation engine
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from validation_engine import ValidationEngine
        
        # Run validation
        validator = ValidationEngine(DB_CONFIG)
        predictions = validator.run_historical_backtest(
            start_gameweek=start_gw,
            end_gameweek=end_gw,
            season=season,
            model_version=model_version
        )
        
        if predictions:
            # Calculate metrics
            metrics = validator.calculate_validation_metrics(predictions, model_version)
            
            # Store results
            validator.store_validation_results(
                metrics=metrics,
                model_version=model_version,
                season=season,
                parameters=data.get('parameters', {}),
                notes=f"API validation run: GW{start_gw}-{end_gw}"
            )
            
            validator.close_connection()
            
            return jsonify({
                'success': True,
                'predictions_count': len(predictions),
                'metrics': {
                    'rmse': round(metrics.rmse, 3),
                    'mae': round(metrics.mae, 3),
                    'spearman_correlation': round(metrics.spearman_correlation, 3),
                    'spearman_p_value': round(metrics.spearman_p_value, 4),
                    'precision_at_20': round(metrics.precision_at_20, 3),
                    'r_squared': round(metrics.r_squared, 3),
                    'n_predictions': metrics.n_predictions
                },
                'target_achievement': {
                    'rmse_target': metrics.rmse < 2.85,
                    'correlation_target': metrics.spearman_correlation > 0.30,
                    'precision_target': metrics.precision_at_20 > 0.30
                },
                'message': f'Validation completed: {len(predictions)} predictions analyzed'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No predictions generated - check data availability'
            }), 400
            
    except Exception as e:
        print(f"Validation API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500

@app.route('/api/optimize-parameters', methods=['POST']) 
def optimize_parameters_endpoint():
    """
    API endpoint for parameter optimization
    
    Request body:
    {
        "gameweek_range": [1, 15],
        "season": "2024/25"
    }
    """
    try:
        data = request.get_json() or {}
        
        # Use GameweekManager to provide intelligent default range
        if 'gameweek_range' not in data:
            from src.gameweek_manager import GameweekManager
            gw_manager = GameweekManager()
            current_gw = gw_manager.get_current_gameweek()
            # Default to analyzing from GW1 to current gameweek (minimum 3 gameweeks for analysis)
            end_gw = max(3, current_gw)
            default_range = [1, end_gw]
        else:
            default_range = [1, 10]
            
        gameweek_range = tuple(data.get('gameweek_range', default_range))
        season = data.get('season', '2024/25')
        
        # Import validation engine  
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from validation_engine import ValidationEngine
        
        # Run optimization
        validator = ValidationEngine(DB_CONFIG)
        results = validator.optimize_parameters(
            gameweek_range=gameweek_range,
            season=season
        )
        
        validator.close_connection()
        
        return jsonify({
            'success': True,
            'optimization_results': results,
            'message': 'Parameter optimization completed'
        })
        
    except Exception as e:
        print(f"Parameter optimization API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Parameter optimization failed: {str(e)}'
        }), 500

@app.route('/api/benchmark-versions', methods=['POST'])
def benchmark_versions_endpoint():
    """
    API endpoint for v1.0 vs v2.0 benchmarking
    
    Request body:
    {
        "gameweek_range": [1, 15]
    }
    """
    try:
        data = request.get_json() or {}
        
        # Use GameweekManager to provide intelligent default range
        if 'gameweek_range' not in data:
            from src.gameweek_manager import GameweekManager
            gw_manager = GameweekManager()
            current_gw = gw_manager.get_current_gameweek()
            # Default to analyzing from GW1 to current gameweek (minimum 3 gameweeks for analysis)
            end_gw = max(3, current_gw)
            default_range = [1, end_gw]
        else:
            default_range = [1, 10]
            
        gameweek_range = tuple(data.get('gameweek_range', default_range))
        
        # Import validation engine
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from validation_engine import ValidationEngine
        
        # Run benchmark
        validator = ValidationEngine(DB_CONFIG)
        results = validator.benchmark_v1_vs_v2(gameweek_range=gameweek_range)
        
        validator.close_connection()
        
        return jsonify({
            'success': True,
            'benchmark_results': results,
            'message': 'Version benchmark completed'
        })
        
    except Exception as e:
        print(f"Benchmark API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Benchmark failed: {str(e)}'
        }), 500

@app.route('/api/validation-history', methods=['GET'])
def validation_history_endpoint():
    """Get historical validation results"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT id, model_version, season, rmse, mae, 
                   spearman_correlation, precision_at_20, r_squared,
                   n_predictions, test_date, parameters, notes
            FROM validation_results
            ORDER BY test_date DESC
            LIMIT 50
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert to JSON-serializable format
        history = []
        for row in results:
            result_dict = dict(row)
            result_dict['test_date'] = row['test_date'].isoformat() if row['test_date'] else None
            history.append(result_dict)
        
        return jsonify({
            'success': True,
            'validation_history': history
        })
        
    except Exception as e:
        print(f"Validation history API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to load validation history: {str(e)}'
        }), 500

@app.route('/api/validation-dashboard')
def validation_dashboard():
    """Render validation dashboard page"""
    return render_template('validation_dashboard.html')

# Catch-all route to serve React app for client-side routing
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes"""
    if path.startswith('api/'):
        return {'error': 'API endpoint not found'}, 404
    
    # Check if it's a static file
    if '.' in path:
        try:
            return send_from_directory(frontend_build_dir, path)
        except FileNotFoundError:
            pass
    
    # For all other routes, serve the React app
    return send_from_directory(frontend_build_dir, 'index.html')


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
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Starting app anyway...")
    
    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))  # Use 5001 to avoid conflict
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # DEVELOPMENT: Enable auto-reload for code changes
    # Set debug=True to auto-restart server when Python files change
    development_mode = True  # Change to False for production
    
    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)