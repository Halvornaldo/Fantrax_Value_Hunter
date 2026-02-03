"""
Flask Backend for Fantrax Value Hunter Dashboard
Provides API endpoints for parameter adjustment and True Value recalculation
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
from flask_caching import Cache
from whitenoise import WhiteNoise
import psycopg2
import psycopg2.extras
import json
import io
import csv
import os
from typing import Dict, List, Optional, Any
import time
import sys
from datetime import datetime
import pulp  # For lineup optimization (Integer Linear Programming)

# Add name_matching module to path
sys.path.append(os.path.dirname(__file__))
from name_matching import UnifiedNameMatcher

# Add integration package to path (optional for production)
try:
    # Use environment variable for integration path
    integration_path = os.getenv('INTEGRATION_PATH', 'C:/Users/halvo/.claude/Fantrax_Expected_Stats')
    if os.path.exists(integration_path):
        sys.path.append(integration_path)
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

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
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

# Configure WhiteNoise to serve React build files in production
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=os.path.join(os.path.dirname(__file__), 'static', 'react-build'),
    prefix='/',
    index_file='index.html',
    autorefresh=True  # Enable file change detection for deployments
)

# Configure WhiteNoise to serve React static assets
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=os.path.join(os.path.dirname(__file__), 'static', 'react-build', 'static'),
    prefix='/static/',
    autorefresh=True  # Enable file change detection for deployments
)

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
    """Get database connection with error handling and Railway optimizations"""
    try:
        # Add Railway-specific connection parameters
        connection_params = DB_CONFIG.copy()

        # Check if we're running on Railway
        is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None

        if is_railway or os.getenv('DATABASE_URL'):
            # Railway requires specific connection settings
            connection_params.update({
                'connect_timeout': 10,  # 10 second connection timeout
                'sslmode': 'require',   # Railway proxy requires SSL
                'options': '-c statement_timeout=30000',  # 30 second query timeout
                'application_name': 'fantrax_value_hunter'
            })
        else:
            # Local development settings
            connection_params.update({
                'connect_timeout': 5,
                'sslmode': 'prefer'
            })

        conn = psycopg2.connect(**connection_params)

        # Set connection encoding and timezone
        conn.set_client_encoding('UTF8')

        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        print(f"Connection params: host={connection_params.get('host')}, port={connection_params.get('port')}, db={connection_params.get('database')}")
        raise
    except Exception as e:
        print(f"Unexpected database error: {e}")
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

def load_default_system_parameters():
    """Load default system parameters from defaults config file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_parameters_defaults.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading default system parameters: {e}")
        return {}

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
    
    # Use latest gameweek if none specified
    if gameweek is None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(gameweek) FROM player_form")
        result = cursor.fetchone()
        gameweek = result[0] if result and result[0] else 1
        cursor.close()
        conn.close()
    
    params = load_system_parameters()
    
    # Use v2.0 calculation engine exclusively
    try:
        from calculation_engine_v2 import FormulaEngineV2
        
        # Initialize v2.0 engine
        v2_engine = FormulaEngineV2(DB_CONFIG, params)
        
        # Get all players with enhanced data for v2.0
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Enhanced query for v2.0 with all required data including NPxG fields
        cursor.execute("""
            SELECT
                p.id as player_id, p.name, p.team, p.position,
                pm.price,
                COALESCE(pf.total_points, 0) as total_fpts,
                CASE
                    WHEN COALESCE(p.games_current_season, 0) > 0
                    THEN COALESCE(pf.total_points, 0) / p.games_current_season
                    ELSE 0
                END as ppg,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier,
                p.xgi90, p.baseline_xgi,
                p.games_current_season,
                pgd.total_points_historical, pgd.games_played_historical,
                pgd.total_points_current, pgd.games_played_current,
                tf.difficulty_score as fixture_difficulty,
                pm.next_opponent, pm.is_home
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
            LEFT JOIN team_fixtures tf ON p.team = tf.team_code
            WHERE 1=1
        """)
        
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

                # NPxG fixture fields for opponent-based calculations
                'next_opponent': player['next_opponent'],
                'is_home': player['is_home'],

                # Historical data for dynamic blending
                'total_points_historical': float(player['total_points_historical']) if player['total_points_historical'] else 0.0,
                'games_played_historical': int(player['games_played_historical']) if player['games_played_historical'] else 0,
                'games_historical': int(player['games_played_historical']) if player['games_played_historical'] else 0,  # NEW: For blending formula
                'total_points_current': float(player['total_points_current']) if player['total_points_current'] else 0.0,
                'games_current': int(player['games_current_season']) if player['games_current_season'] else 0,
            }
            
            # Calculate historical PPG for blending
            if player_data['games_played_historical'] > 0:
                player_data['historical_ppg'] = player_data['total_points_historical'] / player_data['games_played_historical']
            else:
                player_data['historical_ppg'] = None  # Changed from 0.0 to None for proper handling
            
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
                player['player_id']
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
            WHERE player_id = %s
        """, [(u[0], u[1], u[4], u[5], u[6], u[7]) for u in batch_updates])
        
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

# Add cache-control headers to prevent stale content
@app.after_request
def after_request(response):
    """Add cache control headers to ensure fresh content for index.html"""
    # Check if this is serving the main page or index.html
    if (request.path == "/" or
        "index.html" in request.path or
        request.path.endswith(".html")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
@app.route('/api/status')
def api_status():
    """API Status endpoint for production"""
    return jsonify({
        "status": "ok",
        "message": "Fantrax Value Hunter API is running",
        "integration_available": INTEGRATION_AVAILABLE,
        "endpoints": {
            "players": "/api/players",
            "sync_understat": "/api/understat/sync",
            "upload_fantrax": "/api/upload-fantrax",
            "parameters": "/api/parameters"
        }
    })

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
    
    # Always use gameweek 1 for live data system (no gameweek dependencies)
    gameweek = 1
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
        'ppg': 'CASE WHEN COALESCE(p.games_current_season, 0) > 0 THEN COALESCE(pf.total_points, 0) / p.games_current_season ELSE 0 END',
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
        'games_total': '(COALESCE(pgd.games_played_historical, 0) + COALESCE(pgd.games_played, 0))',
        'next_opponent': 'tf.opponent_code',
        'is_home': 'tf.is_home'
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
                p.games_current_season,
                COALESCE(p.exclude_from_optimizer, FALSE) as exclude_from_optimizer,
                pm.price, 
                COALESCE(pf.total_points, 0) as total_fpts,
                CASE
                    WHEN COALESCE(p.games_current_season, 0) > 0
                    THEN COALESCE(pf.total_points, 0) / p.games_current_season
                    ELSE 0
                END as ppg,
                pm.value_score, pm.true_value,
                p.roi,
                p.blended_ppg, p.current_season_weight,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier, pm.xgi_multiplier,
                pm.last_updated,
                COALESCE(p.games_current_season, 0) as games_played,
                COALESCE(pgd.games_played_historical, 0) as games_played_historical,
                COALESCE(pgd.data_source, 'current') as data_source,
                CASE 
                    WHEN COALESCE(pgd.games_played_historical, 0) > 0 
                    THEN COALESCE(pgd.total_points_historical, 0) / pgd.games_played_historical 
                    ELSE NULL 
                END as historical_ppg,
                p.id as player_id,
                COALESCE(tf.difficulty_score, 0) as fixture_difficulty,
                pm.next_opponent,
                pm.is_home
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
            # Handle multi-position matching: check if any requested position appears in player's positions
            position_conditions = []
            for pos in positions:
                position_conditions.append("p.position LIKE %s")
                params.append(f"%{pos}%")
            conditions.append(f"({' OR '.join(position_conditions)})")
            
        if min_price is not None:
            conditions.append("pm.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("pm.price <= %s")
            params.append(max_price)
            
        if team:
            teams = [t.strip() for t in team.split(',')]
            placeholders = ', '.join(['%s'] * len(teams))
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

        # Get total database player count (all players, not just active ones)
        cursor.execute("SELECT COUNT(*) as total FROM players WHERE team != 'TST'")
        total_database_count = cursor.fetchone()['total']
        
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
            games_current = player_dict.get('games_played_current', 0)
            games_historical = player_dict.get('games_played_historical', 0)
            
            # Ensure games data is properly typed and handle None values
            player_dict['games_current'] = int(games_current) if games_current is not None else 0
            player_dict['games_historical'] = int(games_historical) if games_historical is not None else 0
            player_dict['games_total'] = player_dict['games_current'] + player_dict['games_historical']
            player_dict['has_historical_data'] = player_dict['games_historical'] > 0  # NEW: Flag for frontend visual indicators
            players_list.append(player_dict)
        
        # V2.0 calculations are pre-calculated in database - no need for live calculation
        # Mark all players as using V2.0 calculations since they're pre-populated
        manual_overrides = parameters.get('starter_prediction', {}).get('manual_overrides', {})
        for player_dict in players_list:
            player_dict['v2_calculation'] = True
            # Convert string numbers to floats for proper JSON serialization
            if 'total_fpts' in player_dict and player_dict['total_fpts'] is not None:
                player_dict['total_fpts'] = float(player_dict['total_fpts'])
            if 'ppg' in player_dict and player_dict['ppg'] is not None:
                player_dict['ppg'] = float(player_dict['ppg'])
            # ROI and true_value are already loaded from database
            # All multipliers are already loaded from database

            # Add override status
            player_id = player_dict.get('id')
            if player_id in manual_overrides:
                player_dict['has_override'] = True
                player_dict['override_type'] = manual_overrides[player_id].get('type', 'unknown')
            else:
                player_dict['has_override'] = False
                player_dict['override_type'] = 'auto'
        
        # DEBUG: Check final state before JSON response
        semenyo_player = next((p for p in players_list if 'semenyo' in p.get('name', '').lower()), None)
        if semenyo_player:
            print(f"FINAL DEBUG Semenyo before JSON: games_played={semenyo_player.get('games_played')}")
        
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'players': players_list,
            'total_count': total_count,
            'total_database_count': total_database_count,
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
                'detection_method': 'live_data_system',
                'data_source': 'unified_detection',
                'emergency_protection_active': False,  # Removed with gameweek manager
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

        # Recalculate starter multipliers for CSV-imported players with new parameters
        # Always run this when any parameters change
        try:
            conn_param = get_db_connection()
            cursor_param = conn_param.cursor()

            # Get new parameter values
            starter_config = current_params.get('starter_prediction', {})
            likely_penalty = starter_config.get('likely_starter_penalty', 0.8)
            rotation_penalty = starter_config.get('auto_rotation_penalty', 0.7)
            unlikely_penalty = starter_config.get('unlikely_starter_penalty', 0.5)
            bench_penalty = starter_config.get('force_bench_penalty', 0.15)
            out_penalty = starter_config.get('force_out_penalty', 0.0)

            # Get manual overrides to exclude them
            manual_overrides = starter_config.get('manual_overrides', {})
            manual_override_ids = list(manual_overrides.keys())

            # Build exclusion clause for manual overrides
            if manual_override_ids:
                placeholders = ','.join(['%s'] * len(manual_override_ids))
                exclusion_clause = f"AND pm.player_id NOT IN ({placeholders})"
                query_params = [likely_penalty, rotation_penalty, unlikely_penalty, bench_penalty] + manual_override_ids
            else:
                exclusion_clause = ""
                query_params = [likely_penalty, rotation_penalty, unlikely_penalty, bench_penalty]

            # Recalculate multipliers based on stored confidence percentages
            cursor_param.execute(f"""
                UPDATE player_metrics pm
                SET starter_multiplier =
                    CASE
                        WHEN csv_confidence_percentage >= 90 THEN 1.0
                        WHEN csv_confidence_percentage >= 70 THEN %s
                        WHEN csv_confidence_percentage >= 50 THEN %s
                        WHEN csv_confidence_percentage >= 30 THEN %s
                        WHEN csv_confidence_percentage > 0 THEN %s
                        ELSE starter_multiplier
                    END,
                    csv_confidence_multiplier =
                    CASE
                        WHEN csv_confidence_percentage >= 90 THEN 1.0
                        WHEN csv_confidence_percentage >= 70 THEN %s
                        WHEN csv_confidence_percentage >= 50 THEN %s
                        WHEN csv_confidence_percentage >= 30 THEN %s
                        WHEN csv_confidence_percentage > 0 THEN %s
                        ELSE csv_confidence_multiplier
                    END
                WHERE csv_confidence_percentage IS NOT NULL
                {exclusion_clause}
            """, query_params + query_params[:4])  # Duplicate params for both updates

            updated_json_players = cursor_param.rowcount

            # Update non-CSV players with the same parameter values
            cursor_param.execute("""
                UPDATE player_metrics
                SET starter_multiplier = %s,
                    form_multiplier = %s,
                    fixture_multiplier = %s,
                    xgi_multiplier = %s
                WHERE player_name NOT IN (
                    SELECT DISTINCT player_name
                    FROM player_metrics
                    WHERE csv_upload_id IS NOT NULL
                )
            """, query_params[:4])

            updated_non_json_players = cursor_param.rowcount

            conn_param.commit()
            cursor_param.close()
            conn_param.close()

            print(f"Updated {updated_json_players} CSV players with new parameter values")
            print(f"Updated {updated_non_json_players} non-CSV players with new parameter values")

        except Exception as e:
            print(f"Error updating CSV multipliers: {e}")

        # Trigger True Value recalculation using live_data_system for default
        gameweek = data.get('gameweek')
        if gameweek is None:
            conn_temp = get_db_connection()
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT MAX(gameweek) FROM player_form")
            result = cursor_temp.fetchone()
            gameweek = result[0] if result and result[0] else 1
            cursor_temp.close()
            conn_temp.close()
        recalc_result = recalculate_true_values(gameweek)
        
        if not recalc_result['success']:
            return jsonify({
                'error': 'Parameter update succeeded but recalculation failed',
                'recalc_error': recalc_result.get('error')
            }), 500
        
        # Clear the cache so frontend gets fresh data immediately
        # Clear only this player's cache entries for efficiency
        if 'player_id' in locals():
            cache_keys_to_delete = [key for key in cache.cache._cache.keys() if str(player_id) in str(key)]
            for key in cache_keys_to_delete:
                cache.delete(key)
        
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
        
        # First update fixture multipliers with new parameters
        # This ensures correct values are calculated with the new slider setting
        from calculation_engine_v2 import FormulaEngineV2

        engine = FormulaEngineV2(DB_CONFIG, current_params)
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get all players with opponents
        cursor.execute("""
            SELECT p.id as player_id, p.position, pm.next_opponent, pm.is_home
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.next_opponent IS NOT NULL AND pm.next_opponent != ''
        """)

        updates = []
        for row in cursor.fetchall():
            player_data = {
                'player_id': row['player_id'],
                'name': '',
                'position': row['position'],
                'next_opponent': row['next_opponent'],
                'is_home': row['is_home'],
                # Dummy data
                'price': 10.0,
                'ppg': 5.0,
                'xgi90': 0.3,
                'baseline_xgi': None,
                'fixture_difficulty': 0.0,
                'starter_multiplier': 1.0,
                'total_points_historical': 0,
                'games_played_historical': 0,
                'games_historical': 0,
                'total_points_current': 50,
                'games_current': 10,
                'historical_ppg': None
            }

            new_mult = engine._calculate_npxg_fixture_multiplier(player_data)
            updates.append((new_mult, row['player_id']))

        # Update all fixture multipliers
        cursor.executemany("""
            UPDATE player_metrics
            SET fixture_multiplier = %s,
                last_updated = NOW()
            WHERE player_id = %s
        """, updates)

        conn.commit()
        cursor.close()
        conn.close()

        # Now trigger full recalculation with updated fixture multipliers
        # Gameweek manager removed - using database queries
        # Using database query instead
        gameweek = 1  # Fixed for live data system
        recalc_result = recalculate_true_values(gameweek)

        # Clear the cache so frontend gets fresh data immediately
        # Without this, the /api/players endpoint returns 60-second cached data
        cache.clear()

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

@app.route('/api/system/reset-to-defaults', methods=['POST'])
def reset_system_parameters_to_defaults():
    """Reset system parameters to default values"""
    try:
        # Load default parameters
        default_params = load_default_system_parameters()
        if not default_params:
            return jsonify({'error': 'Failed to load default system configuration'}), 500

        # Save defaults as current parameters
        if not save_system_parameters(default_params):
            return jsonify({'error': 'Failed to save default parameters'}), 500

        # Trigger recalculation using the same pattern as regular parameter updates
        gameweek = 1  # Fixed for live data system
        recalc_result = recalculate_true_values(gameweek)

        return jsonify({
            'success': True,
            'message': 'Successfully reset to default parameters and recalculated all player values',
            'updated_config': default_params
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
        
        # Get current gameweek using live_data_system for consistency
        # Gameweek manager removed - using database queries
        # Using database query instead
        gameweek = 1  # Fixed for live data system
        
        if not player_id or not override_type:
            return jsonify({'error': 'player_id and override_type required'}), 400
        
        # Load current system parameters to get penalties
        params = load_system_parameters()
        starter_config = params.get('starter_prediction', {})
        likely_penalty = starter_config.get('likely_starter_penalty', 0.8)
        rotation_penalty = starter_config.get('auto_rotation_penalty', 0.7)
        unlikely_penalty = starter_config.get('unlikely_starter_penalty', 0.50)
        bench_penalty = starter_config.get('force_bench_penalty', 0.15)
        out_penalty = starter_config.get('force_out_penalty', 0.0)
        
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate multiplier based on override type (5-category system)
        if override_type == 'starter':
            multiplier = 1.0
        elif override_type == 'likely':
            multiplier = likely_penalty
        elif override_type == 'rotation':
            multiplier = rotation_penalty
        elif override_type == 'unlikely':
            multiplier = unlikely_penalty
        elif override_type == 'bench':
            multiplier = bench_penalty
        elif override_type == 'out':
            multiplier = out_penalty
        elif override_type == 'auto':
            # Remove manual override - restore original CSV confidence multiplier
            cursor.execute("""
                SELECT csv_confidence_multiplier
                FROM player_metrics
                WHERE player_id = %s AND gameweek = %s
            """, [player_id, gameweek])
            result = cursor.fetchone()
            multiplier = result[0] if result else 0.75  # fallback to rotation if no CSV value
        
        # Update player's starter multiplier
        cursor.execute("""
            UPDATE player_metrics 
            SET starter_multiplier = %s
            WHERE player_id = %s AND gameweek = %s
        """, [multiplier, player_id, gameweek])
        
        # Recalculate True Value for this player
        cursor.execute("""
            UPDATE player_metrics 
            SET true_value = (
                SELECT p.blended_ppg * pm2.form_multiplier * pm2.fixture_multiplier * pm2.starter_multiplier * pm2.xgi_multiplier
                FROM players p, player_metrics pm2
                WHERE p.id = pm2.player_id
                AND pm2.player_id = %s
                AND pm2.gameweek = %s
            )
            WHERE player_id = %s AND gameweek = %s
        """, [player_id, gameweek, player_id, gameweek])
        
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
        
        # Clear the cache so frontend gets fresh data immediately
        cache.clear()
        
        return jsonify({
            'success': True,
            'player_id': player_id,
            'override_type': override_type,
            'new_multiplier': multiplier,
            'new_true_value': round(float(updated_player[0]), 3) if updated_player else 0,
            'player_name': updated_player[2] if updated_player else 'Unknown'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<player_id>/toggle-exclude', methods=['POST'])
def toggle_exclude_player(player_id):
    """Toggle exclude_from_optimizer flag for a player"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Toggle the current value
        cursor.execute("""
            UPDATE players
            SET exclude_from_optimizer = NOT COALESCE(exclude_from_optimizer, FALSE)
            WHERE id = %s
            RETURNING id, name, exclude_from_optimizer
        """, (player_id,))

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if result:
            return jsonify({
                'success': True,
                'player_id': result[0],
                'player_name': result[1],
                'excluded': result[2],
                'message': f"{'Excluded' if result[2] else 'Included'} {result[1]} from optimizer"
            })
        else:
            return jsonify({'success': False, 'error': 'Player not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/players/reset-exclusions', methods=['POST'])
def reset_all_exclusions():
    """Reset all player exclusions (set exclude_from_optimizer to FALSE for all)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE players
            SET exclude_from_optimizer = FALSE
            WHERE exclude_from_optimizer = TRUE
        """)

        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'players_reset': affected,
            'message': f"Reset {affected} player exclusions"
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/verify-starter-status', methods=['GET'])
def verify_starter_status():
    """Validate starter status consistency and identify potential issues"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current gameweek using live_data_system for consistency
        # Gameweek manager removed - using database queries
        # Using database query instead
        current_gameweek = 1  # Fixed for live data system
        
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
        standard_multipliers = {1.0, 0.90, 0.75, 0.50, 0.35, 0.0}
        cursor.execute("""
            SELECT player_name, starter_multiplier, team, position
            FROM players 
            WHERE starter_multiplier IS NOT NULL 
              AND starter_multiplier NOT IN (1.0, 0.90, 0.75, 0.50, 0.35, 0.0)
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
        
        # Get 5-category multiplier statistics
        cursor.execute("""
            SELECT COUNT(*) as total_players,
                   COUNT(CASE WHEN starter_multiplier = 1.0 THEN 1 END) as definite_starters,
                   COUNT(CASE WHEN starter_multiplier = 0.90 THEN 1 END) as likely_starters,
                   COUNT(CASE WHEN starter_multiplier = 0.75 THEN 1 END) as rotation_risks,
                   COUNT(CASE WHEN starter_multiplier = 0.50 THEN 1 END) as unlikely_starters,
                   COUNT(CASE WHEN starter_multiplier = 0.35 THEN 1 END) as bench_players,
                   COUNT(CASE WHEN starter_multiplier = 0.0 THEN 1 END) as out_players
            FROM players 
            WHERE starter_multiplier IS NOT NULL
        """)
        
        stats_row = cursor.fetchone()
        statistics = {
            'total_players': stats_row[0],
            'definite_starters': stats_row[1],
            'likely_starters': stats_row[2],
            'rotation_risks': stats_row[3], 
            'unlikely_starters': stats_row[4],
            'bench_players': stats_row[5],
            'out_players': stats_row[6],
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
        # Gameweek manager removed - using database queries
        # Using database query instead
        
        # Get current gameweek from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(gameweek), 0) FROM player_metrics")
        result = cursor.fetchone()
        current_gw = result[0] if result and result[0] else 1
        next_gw = current_gw + 1
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'current_gameweek': current_gw,
            'next_gameweek': next_gw,
            'current_status': 'active',  # Simplified status
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
        # Gameweek manager removed - using database queries
        # Using database query instead
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        consistency_report = {
            'timestamp': datetime.now().isoformat(),
            'gameweek_manager_detection': 3,  # Temporarily hardcoded - will implement database query
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
                            'issue': f'Table shows GW{latest_gw} but live_data_system detects GW{gm_detection}',
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
    FFP CSV Import - Working Implementation

    IMPORTANT: Only use the main dashboard football icon button for FFP imports:
    ✅ WORKING: Main dashboard → Football icon button → "Import lineup CSV" (hover text)
    ❌ NOT WORKING: Top menu "Upload & Sync" → "Import Lineup CSV"

    Features:
    - Confidence-based multiplier assignment using configurable frontend parameters
    - Name mapping persistence (no repeated validations)
    - Automatic true value recalculation after multiplier application
    - Source system consistency ('ffp' for Fantasy Football Pundit)
    """
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
        
        # Read JSON content and parse properly with quotes
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
        
        # Check for enhanced FFP format (6 columns with confidence and multiplier)
        expected_ffp_headers = ['Team', 'Player Name', 'Position', 'Predicted Status', 'Confidence', 'Multiplier']
        expected_ffp_normalized = [h.strip().lower().replace(' ', '_') for h in expected_ffp_headers]
        
        is_ffp_format = header_normalized == expected_ffp_normalized
        
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
        
        # Check for FFP format (scraped web content with Arsenal first)
        # FFP: HTML headers + data rows starting with "Arsenal Predicted Lineup"
        if not is_formation_format:
            for i, line in enumerate(lines[1:], 1):  # Skip header, check data rows
                if i > 15:  # Don't check too many rows
                    break
                if 'arsenal' in line.lower() and 'predicted lineup' in line.lower():
                    is_formation_format = True
                    break
        
        # Debug logging (optional)
        # print(f"CSV format detection: {is_formation_format}, teams will be mapped")
        
        if not is_individual_format and not is_ffp_format and not is_formation_format:
            return jsonify({
                'error': f'Invalid CSV format. Expected either:\n' +
                        f'1. Individual format: {expected_individual_headers}\n' +
                        f'2. FFP enhanced format: {expected_ffp_headers}\n' +
                        f'3. Formation format: Team + 11 player columns\n' +
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
        
        # Clear all manual overrides before processing new CSV import
        # User requested that overrides be reset to Auto on new file imports
        params = load_system_parameters()
        if 'starter_prediction' in params and 'manual_overrides' in params['starter_prediction']:
            params['starter_prediction']['manual_overrides'] = {}
            save_system_parameters(params)
            print("Cleared all manual overrides - all players reset to Auto")
        
        # Get system parameters for multipliers
        rotation_penalty = params.get('starter_prediction', {}).get('auto_rotation_penalty', 0.75)
        
        # Initialize UnifiedNameMatcher for improved name matching
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        if is_formation_format:
            # Check if it's FFP format (Arsenal first) or FFS format
            is_ffp_formation = False
            ffp_data_start = 0
            for i, line in enumerate(lines[1:], 1):  # Skip header, check data rows
                if i > 15:  # Don't check too many rows
                    break
                if 'arsenal' in line.lower() and 'predicted lineup' in line.lower():
                    is_ffp_formation = True
                    ffp_data_start = i  # Store the line where data starts
                    break
            
            if is_ffp_formation:
                # Process FFP format (team rows with multiple players and percentages)
                # Pass all lines since the function will find Arsenal Predicted Lineup as starting point
                starter_params = params.get('starter_prediction', {})
                players_to_process = parse_ffp_formation_csv(lines, cursor, starter_params)
            else:
                # Process formation matrix format (FFS scraping)
                players_to_process = parse_formation_csv(lines[1:], cursor)  # Skip header
        elif is_ffp_format:
            # Process FFP enhanced format (confidence-based multipliers)
            players_to_process = parse_ffp_csv(lines[1:])  # Skip header
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
            # Determine source system based on format type
            # FFP = Fantasy Football Pundit (current system)
            # FFS = Fantasy Football Scout (legacy system)
            if is_ffp_formation:
                source_system = 'ffp'  # Fantasy Football Pundit format
            else:
                source_system = 'ffs'  # Legacy FFS format (if still used)
            match_result = matcher.match_player(
                source_name=player_name,
                source_system=source_system,
                team=team,
                position=position
            )
            
            # Check if we have a good match (fantrax_id exists and high confidence or verified)
            # Use lower threshold for formation imports since names are often shortened
            # Lower threshold for FFP format debugging - exact matches should be 100% but let's be safe
            confidence_threshold = 80.0 if (is_formation_format or is_ffp_format) else 90.0
            
            if match_result['fantrax_id'] and (not match_result['needs_review'] or match_result['confidence'] >= confidence_threshold):
                # We have a confident match
                print(f"[OK] MATCHED: {player_name} -> {match_result['fantrax_name']} (confidence: {match_result['confidence']:.1f}%)")
                
                # Determine multiplier: use multiplier from FFP format if available, otherwise use traditional logic
                if 'multiplier' in player_info:
                    # FFP format with confidence-based multipliers
                    multiplier = player_info['multiplier']
                else:
                    # Traditional format - use binary starter/non-starter logic
                    if status.lower() in ['starter', 'starting', 'start']:
                        multiplier = 1.0
                    else:
                        multiplier = rotation_penalty
                
                # Add to appropriate list (still using status for categorization)
                if status.lower() in ['starter', 'starting', 'start'] or multiplier >= 0.9:
                    starters.append({
                        'player_id': match_result['fantrax_id'],
                        'name': match_result['fantrax_name'],
                        'team': team,
                        'multiplier': multiplier,
                        'confidence': match_result['confidence'],
                        'match_type': match_result['match_type']
                    })
                else:
                    non_starters.append({
                        'player_id': match_result['fantrax_id'],
                        'name': match_result['fantrax_name'],
                        'team': team,
                        'multiplier': multiplier,
                        'confidence': match_result['confidence'],
                        'match_type': match_result['match_type']
                    })
            else:
                # No match or low confidence - add to unmatched for review
                print(f"[X] FAILED: {player_name} (team: {team}, pos: {position}) - confidence: {match_result.get('confidence', 0):.1f}%, needs_review: {match_result.get('needs_review', True)}")
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
        
        # Update starter_multiplier in database using live_data_system
        # Gameweek manager removed - using database queries
        # Using database query instead
        gameweek = 1  # Fixed for live data system  # Use current gameweek for lineup updates
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
            # STEP 1: Set ALL players to lowest category (bench) - clean slate approach
            # This aligns with the weekly archive workflow where we start fresh each week
            starter_config = params.get('starter_prediction', {})
            lowest_multiplier = starter_config.get('force_bench_penalty', 0.15)
            cursor.execute("""
                UPDATE player_metrics
                SET starter_multiplier = %s,
                    csv_confidence_multiplier = %s,
                    csv_confidence_percentage = NULL
                WHERE gameweek = %s
            """, [lowest_multiplier, lowest_multiplier, gameweek])
            
            all_players_updated = cursor.rowcount
            print(f"Set {all_players_updated} players to lowest category ({lowest_multiplier}x - bench level)")
            
            # STEP 2: Set matched CSV players with their specific multipliers - BUT don't override manual settings
            starter_ids = []
            
            # Process both starters and non-starters (all matched players)
            all_matched_players = starters + non_starters
            
            for player in all_matched_players:
                # Check if this player has a manual override - if so, skip CSV update
                if player['player_id'] not in manual_overrides:
                    cursor.execute("""
                        UPDATE player_metrics
                        SET starter_multiplier = %s,
                            csv_confidence_multiplier = %s,
                            csv_confidence_percentage = %s
                        WHERE player_id = %s AND gameweek = %s
                    """, [player['multiplier'], player['multiplier'], player.get('confidence', None), player['player_id'], gameweek])
                    rows_affected = cursor.rowcount
                    starter_ids.append(player['player_id'])
                    updated_count += 1
                else:
                    print(f"Skipping {player['name']} - has manual override")
            
            print(f"Updated {len(starter_ids)} CSV players with confidence-based multipliers")
            print(f"Remaining players stay at lowest category ({lowest_multiplier:.2f}x) as expected")
            
            # STEP 3: Re-apply any existing manual overrides (5-category system)
            starter_config = params.get('starter_prediction', {})
            likely_penalty = starter_config.get('likely_starter_penalty', 0.8)
            rotation_penalty = starter_config.get('auto_rotation_penalty', 0.7)
            unlikely_penalty = starter_config.get('unlikely_starter_penalty', 0.50)
            bench_penalty = starter_config.get('force_bench_penalty', 0.15)
            out_penalty = starter_config.get('force_out_penalty', 0.0)
            
            for player_id, override in manual_overrides.items():
                override_type = override.get('type')
                if override_type == 'starter':
                    multiplier = 1.0
                elif override_type == 'likely':
                    multiplier = likely_penalty
                elif override_type == 'rotation':
                    multiplier = rotation_penalty
                elif override_type == 'unlikely':
                    multiplier = unlikely_penalty
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
            
            # Store unmatched players for validation UI (if any) - similar to Understat
            if unmatched_players:
                import json
                import os
                import time
                validation_data = {
                    'source_system': 'ffp',
                    'unmatched_players': unmatched_players,
                    'timestamp': time.time(),
                    'confidence_threshold': confidence_threshold,
                    'import_source': 'ffp_starter_import',
                    'csv_format': 'formation_matrix' if is_formation_format else 'individual_players'
                }
                
                temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                with open(os.path.join(temp_dir, 'ffp_unmatched.json'), 'w') as f:
                    json.dump(validation_data, f)
            
            # Prepare response data with validation info
            response_data = {
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
            }
            
            # Add verification redirect if there are unmatched players
            if len(unmatched_players) > 0:
                response_data['verification_needed'] = True
                response_data['verification_url'] = '/import-validation?source=ffp'
                response_data['message'] = f'Import completed. {len(unmatched_players)} players need manual verification.'
            else:
                response_data['verification_needed'] = False
                response_data['message'] = 'Import completed successfully. All players matched.'
            
            # Clear the cache so frontend gets fresh data immediately
            cache.clear()
            
            return jsonify(response_data)
            
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
        include_all = request.args.get('include_all', 'false').lower() == 'true'
        # Use live_data_system for unified gameweek detection
        # Gameweek manager removed - using database queries
        # Using database query instead
        gameweek = 1  # Fixed for live data system
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build query (same logic as /api/players but without pagination)
        base_query = """
            SELECT 
                p.name, p.team, p.position,
                p.games_current_season,
                COALESCE(pgd.games_played_historical, 0) as games_played_historical,
                pm.price, pm.ppg, p.blended_ppg, COALESCE(pf.total_points, 0) as total_fpts, pm.true_value, p.roi,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier, pm.xgi_multiplier,
                p.current_season_weight,
                p.minutes, p.xg90, p.xa90, p.xgi90,
                (COALESCE(p.xg90, 0) + COALESCE(p.xa90, 0)) as xgi
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            LEFT JOIN (
                SELECT player_id, MAX(points) as total_points
                FROM player_form
                GROUP BY player_id
            ) pf ON p.id = pf.player_id
            LEFT JOIN (
                SELECT player_id,
                       MAX(games_played_historical) as games_played_historical
                FROM player_games_data
                GROUP BY player_id
            ) pgd ON p.id = pgd.player_id
            WHERE pm.gameweek = %s
        """
        
        params = [gameweek]
        conditions = []
        
        # Add filters
        if position:
            positions = [p.strip() for p in position.split(',')]
            # Handle multi-position matching: check if any requested position appears in player's positions
            position_conditions = []
            for pos in positions:
                position_conditions.append("p.position LIKE %s")
                params.append(f"%{pos}%")
            conditions.append(f"({' OR '.join(position_conditions)})")
            
        if min_price is not None:
            conditions.append("pm.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("pm.price <= %s")
            params.append(max_price)
            
        if team:
            teams = [t.strip() for t in team.split(',')]
            placeholders = ', '.join(['%s'] * len(teams))
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
        csv_lines.append("Name,Team,Position 1,Position 2,Price,PPG,PP90,Blended PPG,Total FPts,24-25,25-26,True Value,ROI,Form Multiplier,Fixture Multiplier,Starter Multiplier,xGI Multiplier,Current Season Weight,Minutes,xG90,xA90,xGI90,xGI")
        
        for player in players:
            current_weight = float(player['current_season_weight']) if player['current_season_weight'] else 0.0
            minutes = player['minutes'] if player['minutes'] else 0
            xg90 = float(player['xg90']) if player['xg90'] else 0.0
            xa90 = float(player['xa90']) if player['xa90'] else 0.0
            xgi90 = float(player['xgi90']) if player['xgi90'] else 0.0
            xgi = float(player['xgi']) if player['xgi'] else 0.0

            # Calculate PP90 (Points Per 90 minutes)
            total_fpts = float(player['total_fpts']) if player['total_fpts'] else 0.0
            pp90 = (total_fpts / minutes * 90) if minutes >= 90 else 0.0

            # Split positions to prevent Excel data shifting
            positions = player['position'].split(',') if player['position'] else ['']
            position1 = positions[0].strip() if len(positions) > 0 else ''
            position2 = positions[1].strip() if len(positions) > 1 else ''
            csv_lines.append(f"{player['name']},{player['team']},{position1},{position2},{player['price']},{player['ppg']},{pp90:.1f},{player['blended_ppg']:.2f},{player['total_fpts']:.3f},{player['games_played_historical']},{player['games_current_season']},{player['true_value']:.3f},{player['roi']:.3f},{player['form_multiplier']:.2f},{player['fixture_multiplier']:.2f},{player['starter_multiplier']:.2f},{player['xgi_multiplier']:.2f},{current_weight:.3f},{minutes},{xg90:.3f},{xa90:.3f},{xgi90:.3f},{xgi:.3f}")
        
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

        print(f"[DEBUG] Apply import called with:")
        print(f"  confirmed_mappings count: {len(confirmed_mappings)}")
        print(f"  source_system: '{source_system}'")
        print(f"  players count: {len(players)}")
        print(f"  dry_run: {dry_run}")
        print(f"  user_id: {user_id}")
        
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

        # Apply starter multipliers for FFP imports
        multipliers_applied = 0
        print(f"[DEBUG] Source system: '{source_system}', checking for FFP multiplier application...")
        if source_system == 'ffp':
            print(f"[DEBUG] Starting FFP multiplier application...")
            try:
                # Load system parameters for starter predictions
                cursor = get_db_connection().cursor()
                cursor.execute("SELECT parameters FROM system_parameters WHERE id = 1")
                params_row = cursor.fetchone()

                if params_row:
                    params = json.loads(params_row[0])
                    starter_params = params.get('starter_prediction', {})

                    # Load FFP data from temp file
                    ffp_unmatched_path = os.path.join('temp', 'ffp_unmatched.json')
                    if os.path.exists(ffp_unmatched_path):
                        with open(ffp_unmatched_path, 'r', encoding='utf-8') as f:
                            ffp_data = json.load(f)
                            ffp_players = ffp_data.get('unmatched_players', [])
                    else:
                        ffp_players = players

                    # Apply multipliers for successfully mapped players
                    for player in ffp_players:
                        player_name = player.get('name', '')
                        confidence = player.get('confidence', 0.0)

                        # Check if player has a mapping (either new or existing)
                        fantrax_id = None
                        if player_name in confirmed_mappings:
                            fantrax_id = confirmed_mappings[player_name]['fantrax_id']
                        else:
                            match_result = matcher.match_player(
                                source_name=player_name,
                                source_system=source_system,
                                team=player.get('team', ''),
                                position=player.get('position', '')
                            )
                            if match_result['fantrax_id'] and not match_result['needs_review']:
                                fantrax_id = match_result['fantrax_id']

                        if fantrax_id and confidence > 0:
                            # Calculate multiplier using system parameters
                            from convert_ffp_csv import confidence_to_multiplier
                            multiplier = confidence_to_multiplier(confidence, starter_params)

                            # Update player_metrics with new starter multiplier
                            cursor.execute("""
                                UPDATE player_metrics
                                SET starter_multiplier = %s,
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE fantrax_id = %s
                            """, (multiplier, fantrax_id))

                            if cursor.rowcount > 0:
                                multipliers_applied += 1
                                print(f"Applied {multiplier:.2f}x multiplier to player {player_name} ({fantrax_id}) based on {confidence}% confidence")

                    # Commit multiplier updates
                    cursor.connection.commit()

                    # Trigger true value recalculation for updated players
                    if multipliers_applied > 0:
                        print(f"Triggering true value recalculation for {multipliers_applied} players...")
                        cursor.execute("SELECT trigger_true_value_calculation()")
                        cursor.connection.commit()

                cursor.close()

            except Exception as e:
                print(f"Error applying starter multipliers: {e}")

        return jsonify({
            'success': True,
            'import_count': import_count,
            'mappings_saved': saved_count,
            'multipliers_applied': multipliers_applied,
            'failed_mappings': failed_mappings,
            'message': f'Successfully imported {import_count} players with {saved_count} new mappings and {multipliers_applied} starter multipliers applied'
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
    Import gameweek form data from Fantrax JSON export
    Expects CSV with columns: ID, Player, Team, Position, RkOv, Opponent, Salary, FPts, etc.
    Extracts player ID and FPts for storage in player_form table
    """
    try:
        # Use fixed gameweek 1 for live data system (no gameweek dependencies)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Always use gameweek 1 for current/live data
        gameweek = 1
        
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
                else:
                    # Update existing player's team and position if they have changed
                    cursor.execute("""
                        UPDATE players 
                        SET team = %s, position = %s, updated_at = NOW()
                        WHERE id = %s AND (team != %s OR position != %s)
                    """, (team, position, player_id, team, position))
                    
                    if cursor.rowcount > 0:
                        print(f"[OK] Updated team/position for {player_name}: team={team}, position={position}")
                        if 'team_updates' not in locals():
                            team_updates = []
                        team_updates.append(f"{player_name} -> team:{team}, pos:{position}")
                
                # Get fantasy points and price
                fpts = float(row['FPts'])
                salary = float(row['Salary'])
                print(f"DEBUG - Price for {player_name}: {salary} (from CSV column 'Salary')")

                # Extract opponent data from CSV
                opponent_raw = row.get('Opponent', '')
                next_opponent = None
                is_home = None

                if opponent_raw:
                    # Parse Fantrax opponent format: "BUR Sat 4:00PM" (home) or "@EVE Mon 9:00PM" (away)
                    opponent_raw = opponent_raw.strip()
                    if opponent_raw.startswith('@'):
                        # Away game: "@EVE Mon 9:00PM" -> extract "EVE"
                        parts = opponent_raw[1:].split()
                        if parts:
                            next_opponent = parts[0].strip()
                            is_home = False
                    else:
                        # Home game: "BUR Sat 4:00PM" -> extract "BUR"
                        parts = opponent_raw.split()
                        if parts:
                            next_opponent = parts[0].strip()
                            is_home = True

                # Insert/update player form data
                cursor.execute("""
                    INSERT INTO player_form (player_id, gameweek, points, timestamp)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek)
                    DO UPDATE SET points = EXCLUDED.points, timestamp = NOW()
                """, [player_id, gameweek, fpts])

                # Insert/update player_metrics with price and opponent data
                cursor.execute("""
                    INSERT INTO player_metrics (player_id, gameweek, price, next_opponent, is_home, last_updated)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (player_id, gameweek)
                    DO UPDATE SET
                        price = EXCLUDED.price,
                        next_opponent = EXCLUDED.next_opponent,
                        is_home = EXCLUDED.is_home,
                        last_updated = NOW()
                """, [player_id, gameweek, salary, next_opponent, is_home])
                
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
                        WHEN COALESCE(players.games_current_season, 0) > 0 
                        THEN COALESCE(pf_max.total_points, 0) / players.games_current_season
                        ELSE 0 
                    END
                FROM players
                LEFT JOIN (
                    SELECT player_id, MAX(points) as total_points
                    FROM player_form
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pf_max ON players.id = pf_max.player_id
                WHERE players.id = pm.player_id
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
                p.games_current_season,
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
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
            
        # Use fixed gameweek 1 for live data system (no gameweek dependencies)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Always use gameweek 1 for current/live data
        gameweek = 1
            
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
            
            
            try:
                home_odds = float(row[odds_start_index].strip().strip('"'))
                draw_odds = float(row[odds_start_index + 1].strip().strip('"'))
                away_odds = float(row[odds_start_index + 2].strip().strip('"'))
            except (ValueError, IndexError):
                skipped_matches += 1
                continue
                
                
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
                # Check if date contains a comma (e.g., "Tomorrow, 13 Sep")
                if ',' in date_str:
                    # Extract the actual date part after the comma
                    date_part = date_str.split(', ', 1)[1]  # Gets "13 Sep" 
                    # Add current year if not present
                    if len(date_part.split()) == 2:  # "13 Sep"
                        current_year = datetime.now().year
                        date_part = f"{date_part} {current_year}"
                    match_date = datetime.strptime(date_part, '%d %b %Y').date()
                else:
                    # Normal date format "14 Sep 2025"
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
        
        # Second pass: take first 10 matches with unique teams (Premier League gameweek = 10 matches)
        # CSV is already sorted chronologically, so no need to sort
        
        # Filter to ensure each team appears only once per gameweek
        filtered_matches = []
        teams_in_gameweek = set()
        
        for match in all_matches:
            # Only add if neither team has been seen in this gameweek
            if match['home_code'] not in teams_in_gameweek and match['away_code'] not in teams_in_gameweek:
                filtered_matches.append(match)
                teams_in_gameweek.add(match['home_code'])
                teams_in_gameweek.add(match['away_code'])
                
                # Stop when we have 10 matches (20 unique teams)
                if len(filtered_matches) == 10:
                    break
        
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
        
        # Trigger V2.0 recalculation after odds import (same as form data import)
        print(f"Triggering V2.0 True Value recalculation after odds import...")
        recalc_result = recalculate_true_values(gameweek)
        
        # Debug logging
        print(f"\n=== ODDS IMPORT DEBUG (GW{gameweek}) ===")
        print(f"Total valid matches found: {len(all_matches)}")
        print(f"Matches after filtering: {len(filtered_matches)}")
        print(f"Teams processed: {len(teams_processed)}")
        print("Teams in filtered matches:", sorted(teams_processed))
        print(f"V2.0 Recalculation: {recalc_result.get('updated_count', 0)} players updated")
        
        # Calculate filtering stats
        total_valid_matches = len(all_matches)
        skipped_due_to_filtering = total_valid_matches - len(filtered_matches)
        
        # Create detailed match lists for verification
        imported_matches = []
        for match in filtered_matches:
            imported_matches.append({
                'home': match['home_code'],
                'away': match['away_code'],
                'date': match['date'].strftime('%d %b %Y'),
                'home_odds': match['home_odds'],
                'draw_odds': match['draw_odds'],
                'away_odds': match['away_odds']
            })
        
        skipped_matches_detail = []
        for match in all_matches[len(filtered_matches):]:  # Matches that were skipped due to filtering
            skipped_matches_detail.append({
                'home': match['home_code'],
                'away': match['away_code'], 
                'date': match['date'].strftime('%d %b %Y'),
                'reason': 'Team already played'
            })
        
        # Return success response with detailed match info
        return jsonify({
            'success': True,
            'processed_matches': len(filtered_matches),
            'skipped_matches': skipped_matches + skipped_due_to_filtering,
            'gameweek': gameweek,
            'message': f'Successfully imported {len(filtered_matches)} matches for gameweek {gameweek}',
            'imported_matches': imported_matches,
            'skipped_matches': skipped_matches_detail,
            'recalculation': {
                'triggered': True,
                'updated_players': recalc_result.get('updated_count', 0),
                'success': recalc_result.get('success', False),
                'elapsed_time': recalc_result.get('elapsed_time', 0)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500

# ===============================
# INDIVIDUAL GAME SCORES IMPORT
# ===============================

@app.route('/api/import-game-scores', methods=['POST'])
def import_game_scores():
    """
    Import individual game scores from Fantrax JSON export
    Expects CSV with columns: ID, Player, Team, Position, RkOv, Opponent, Salary, FPts, etc.
    Stores individual game scores in player_game_scores table for enhanced Form calculation
    """
    try:
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

        # Get game number from form data
        game_number = request.form.get('game_number')
        if not game_number:
            return jsonify({
                'success': False,
                'error': 'Game number is required'
            }), 400

        try:
            game_number = int(game_number)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Game number must be a valid integer'
            }), 400

        # Read CSV file
        import pandas as pd

        # Read the CSV content
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = pd.read_csv(stream)

        # Validate required columns
        required_columns = ['ID', 'Player', 'FPts', 'Opponent']
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

        # Get all existing player IDs to check against
        cursor.execute("SELECT id FROM players")
        existing_player_ids = set(row[0] for row in cursor.fetchall())

        for index, row in csv_input.iterrows():
            try:
                # Extract player ID (remove asterisks from ID column)
                player_id = str(row['ID']).strip('*')
                player_name = row.get('Player', 'Unknown')
                opponent = row.get('Opponent', 'Unknown')

                # Skip if player not in our database
                if player_id not in existing_player_ids:
                    continue

                # Get fantasy points
                fpts = float(row['FPts'])

                # Insert/update game score data
                cursor.execute("""
                    INSERT INTO player_game_scores (player_id, game_number, points_scored, opponent, import_timestamp)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (player_id, game_number)
                    DO UPDATE SET
                        points_scored = EXCLUDED.points_scored,
                        opponent = EXCLUDED.opponent,
                        import_timestamp = NOW()
                """, [player_id, game_number, fpts, opponent])

                imported_count += 1

            except Exception as e:
                error_count += 1
                player_name = row.get('Player', 'Unknown')
                errors.append(f"Row {index + 1} ({player_name}): {str(e)}")
                continue

        # Commit all changes
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Game {game_number} scores imported successfully',
            'imported_count': imported_count,
            'error_count': error_count,
            'errors': errors[:10],  # Limit errors shown
            'game_number': game_number
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

@app.route('/railway-sync')
def railway_sync_ui():
    """Serve the Railway sync progress UI"""
    return render_template('railway_sync.html')

@app.route('/form-upload')
def form_upload_ui():
    """Serve the form data upload UI"""
    return render_template('form_upload.html')

@app.route('/odds-upload')
def odds_upload_ui():
    """Serve the fixture odds upload UI"""
    return render_template('odds_upload.html')

@app.route('/import-games')
def import_games_ui():
    """Serve the game scores import UI"""
    try:
        # Get the last imported game number
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(game_number) FROM player_game_scores")
        last_game = cursor.fetchone()[0] or 0
        next_game = last_game + 1

        # Get import statistics
        cursor.execute("""
            SELECT game_number, COUNT(DISTINCT player_id) as players,
                   COUNT(*) as total_scores,
                   COUNT(CASE WHEN did_play = true THEN 1 END) as validated_played
            FROM player_game_scores
            GROUP BY game_number
            ORDER BY game_number DESC
            LIMIT 5
        """)
        recent_imports = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('import_game_scores.html',
                             next_game=next_game,
                             recent_imports=recent_imports)
    except Exception as e:
        return render_template('import_game_scores.html',
                             next_game=5,
                             recent_imports=[],
                             error=f"Error loading import data: {str(e)}")

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
        
        # First, reset all players to baseline values for the new season
        # This ensures players not found in current Understat data get proper defaults
        cursor.execute("""
            UPDATE players 
            SET minutes = 0, 
                games_current_season = 0, 
                xg90 = 0, 
                xa90 = 0, 
                xgi90 = 0,
                last_understat_update = CURRENT_TIMESTAMP
        """)
        players_reset = cursor.rowcount
        
        # Load system parameters to get current bench penalty
        params = load_system_parameters()
        starter_config = params.get('starter_prediction', {})
        bench_penalty = starter_config.get('force_bench_penalty', 0.15)

        # Also reset starter_multiplier to default bench level for consistency
        cursor.execute("""
            UPDATE player_metrics
            SET starter_multiplier = %s
            WHERE gameweek = 1
        """, [bench_penalty])
        starter_reset = cursor.rowcount
        
        reset_count = players_reset
        
        updated_count = 0
        for player in matched_players:
            # Use actual games from Understat API instead of estimating from minutes
            games_played = player.get('games', 0)
            
            # Calculate xGI90 as xG90 + xA90 (not from Understat directly)
            xg90_val = round(player['xG90'], 3)
            xa90_val = round(player['xA90'], 3)
            xgi90_val = round(xg90_val + xa90_val, 3)
            
            cursor.execute("""
                UPDATE players 
                SET minutes = %s, xg90 = %s, xa90 = %s, xgi90 = %s,
                    games_current_season = %s,
                    last_understat_update = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [
                player['minutes'], 
                xg90_val,
                xa90_val, 
                xgi90_val,
                games_played,
                player['fantrax_id']
            ])
            
            # NEW: Update raw snapshots with xG data and minutes for all existing gameweeks
            cursor.execute("""
                UPDATE raw_player_snapshots 
                SET minutes_played = %s, xg90 = %s, xa90 = %s, xgi90 = %s, 
                    games_current_season = %s,
                    understat_import = TRUE, import_timestamp = NOW()
                WHERE player_id = %s
            """, [
                player['minutes'],
                xg90_val,
                xa90_val,
                xgi90_val,
                games_played,
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
            'players_updated': updated_count,
            'players_reset': reset_count,
            'starter_values_reset': starter_reset
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

@app.route('/api/ffp/get-unmatched-data', methods=['GET'])
def get_ffp_unmatched_data():
    """Load saved unmatched FFP players for validation UI"""
    try:
        import os
        import json
        
        # Check if unmatched data file exists
        temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
        unmatched_file = os.path.join(temp_dir, 'ffp_unmatched.json')
        
        if not os.path.exists(unmatched_file):
            return jsonify({
                'status': 'error',
                'message': 'No unmatched FFP data found. Please import FFP data first.'
            }), 404
        
        # Load the saved unmatched data
        with open(unmatched_file, 'r') as f:
            saved_data = json.load(f)
        
        # Check data age (only use if less than 1 hour old)
        data_age_hours = (time.time() - saved_data['timestamp']) / 3600
        if data_age_hours > 1:
            return jsonify({
                'status': 'error',
                'message': f'FFP data is {data_age_hours:.1f} hours old. Please import again.'
            }), 410
        
        # Convert saved data to validation UI format
        unmatched_players = saved_data['unmatched_players']
        needs_review_count = len(unmatched_players)
        
        # Format for validation UI (similar to Understat but adapted for FFP)
        formatted_players = []
        position_breakdown = {}
        
        for player in unmatched_players:
            position = player.get('position', 'Unknown')
            
            # Update position breakdown
            if position not in position_breakdown:
                position_breakdown[position] = {'total': 0, 'matched': 0}
            position_breakdown[position]['total'] += 1
            
            formatted_player = {
                'original_name': player['name'],
                'original_team': player['team'], 
                'original_position': position,
                'line_number': player.get('line', 0),
                'status': player.get('status', 'Unknown'),
                'suggestions': player.get('suggestions', []),
                'needs_review': True,
                'confidence': player.get('confidence', 0),
                'suggested_match': player.get('suggested_match', '')
            }
            formatted_players.append(formatted_player)
        
        # Calculate position match rates (all unmatched so 0%)
        for pos_stats in position_breakdown.values():
            pos_stats['match_rate'] = 0.0
        
        # Summary statistics
        summary = {
            'total_players': needs_review_count,
            'matched_players': 0,
            'unmatched_players': needs_review_count,
            'match_rate': 0.0,
            'confidence_threshold': saved_data.get('confidence_threshold', 80.0),
            'import_source': saved_data.get('import_source', 'ffp'),
            'csv_format': saved_data.get('csv_format', 'individual_players')
        }
        
        return jsonify({
            'status': 'success',
            'has_unmatched': True,
            'unmatched_count': needs_review_count,
            'unmatched_details': formatted_players,
            'summary': summary,
            'position_breakdown': position_breakdown,
            'source_system': 'ffp',
            'timestamp': saved_data['timestamp']
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
                        SET xg90 = %s, xa90 = %s, xgi90 = %s, minutes = %s, games_current_season = %s,
                            last_understat_update = %s
                        WHERE id = %s
                    """
                    
                    # Calculate xGI90 as xG90 + xA90 (not from Understat directly)
                    xg90_val = understat_player.get('xG90', 0)
                    xa90_val = understat_player.get('xA90', 0)
                    xgi90_val = round(float(xg90_val) + float(xa90_val), 3)
                    
                    cursor.execute(update_query, (
                        xg90_val,  # Correct case: xG90
                        xa90_val,   # Correct case: xA90
                        xgi90_val,  # Calculated: xG90 + xA90
                        understat_player.get('minutes', 0),
                        understat_player.get('games', 0),  # Add games field
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


@app.route('/api/understat/import-player-json', methods=['POST'])
def import_understat_player_json():
    """
    Import Understat player xGI data from JSON export.
    Workaround for broken ScraperFC library.

    Expected JSON format (array of objects):
    "number";"player";"team";"apps";"min";"goals";"a";"xG";"xA";"xG90";"xA90";"xG90xA90"
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read JSON content

        content = file.read().decode('utf-8-sig')  # Handle BOM
        players_data = json.loads(content)
        if not isinstance(players_data, list):
            return jsonify({'error': 'JSON must be an array of player objects'}), 400

        # Extract player data from JSON
        json_players = []
        for player_row in players_data:
            player_name = player_row.get('player', '')
            team = player_row.get('team', '')

            # Skip empty rows
            if not player_name:
                continue

            json_players.append({
                'player_name': player_name,
                'team': team,
                'apps': int(player_row.get('apps', 0)),
                'minutes': int(player_row.get('min', 0)),
                'xG': float(player_row.get('xG', 0)),
                'xA': float(player_row.get('xA', 0)),
                'xG90': float(player_row.get('xG90', 0)),
                'xA90': float(player_row.get('xA90', 0)),
                'xGI90': float(player_row.get('xG90xA90', 0))  # JSON uses xG90xA90
            })

        # Use Global Name Matching System for player matching
        matcher = UnifiedNameMatcher(DB_CONFIG)
        matched_players = []
        unmatched_players = []

        for player in json_players:
            match_result = matcher.match_player(
                source_name=player['player_name'],
                source_system='understat',
                team=player['team'],
                position=None
            )

            if match_result['fantrax_id'] is not None and match_result['confidence'] >= 70:
                # High confidence match
                player['fantrax_id'] = match_result['fantrax_id']
                player['fantrax_name'] = match_result['fantrax_name']
                player['confidence'] = match_result['confidence']
                matched_players.append(player)
            else:
                # Low confidence or no match - needs manual review
                player['suggestions'] = match_result.get('suggested_matches', [])
                player['needs_review'] = True
                player['confidence'] = match_result.get('confidence', 0)
                unmatched_players.append(player)

        # Save unmatched players for validation UI
        if unmatched_players:
            validation_data = {
                'source_system': 'understat_csv',
                'unmatched_players': unmatched_players,
                'matched_players': matched_players,
                'timestamp': time.time()
            }

            temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            with open(os.path.join(temp_dir, 'understat_csv_unmatched.json'), 'w') as f:
                json.dump(validation_data, f)

        # Calculate match rate
        total_players = len(matched_players) + len(unmatched_players)
        match_rate = (len(matched_players) / total_players * 100) if total_players > 0 else 0

        response_data = {
            'success': True,
            'total_json_players': total_players,
            'successfully_matched': len(matched_players),
            'unmatched_players': len(unmatched_players),
            'unmatched_names': [p['player_name'] for p in unmatched_players],
            'match_rate': match_rate,
            'matched_data': matched_players,
            'unmatched_data': unmatched_players
        }

        if len(unmatched_players) > 0:
            response_data['verification_needed'] = True
            response_data['message'] = f'CSV parsed. {len(unmatched_players)} players need manual verification.'
        else:
            response_data['verification_needed'] = False
            response_data['message'] = f'All {total_players} players matched successfully.'

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'CSV import failed: {str(e)}'}), 500


@app.route('/api/understat/apply-player-csv', methods=['POST'])
def apply_understat_player_csv():
    """
    Apply Understat CSV data to database after validation.
    Accepts both auto-matched and manually confirmed players.
    """
    try:
        data = request.get_json()
        matched_players = data.get('matched_players', [])
        confirmed_mappings = data.get('confirmed_mappings', {})

        if not matched_players and not confirmed_mappings:
            return jsonify({'error': 'No player data to apply'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Load system parameters to get current bench penalty
        params = load_system_parameters()
        starter_config = params.get('starter_prediction', {})
        bench_penalty = starter_config.get('force_bench_penalty', 0.15)

        # First, reset all players to baseline (same as regular sync)
        cursor.execute("""
            UPDATE players
            SET minutes = 0,
                games_current_season = 0,
                xg90 = 0,
                xa90 = 0,
                xgi90 = 0,
                last_understat_update = CURRENT_TIMESTAMP
        """)
        players_reset = cursor.rowcount

        # Reset starter_multiplier to default
        cursor.execute("""
            UPDATE player_metrics
            SET starter_multiplier = %s
            WHERE gameweek = 1
        """, [bench_penalty])

        updated_count = 0

        # Apply auto-matched players
        for player in matched_players:
            fantrax_id = player.get('fantrax_id')
            if not fantrax_id:
                continue

            xg90_val = round(float(player.get('xG90', 0)), 3)
            xa90_val = round(float(player.get('xA90', 0)), 3)
            xgi90_val = round(float(player.get('xGI90', xg90_val + xa90_val)), 3)
            minutes = int(player.get('minutes', 0))
            games = int(player.get('apps', 0))

            cursor.execute("""
                UPDATE players
                SET minutes = %s, xg90 = %s, xa90 = %s, xgi90 = %s,
                    games_current_season = %s,
                    last_understat_update = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [minutes, xg90_val, xa90_val, xgi90_val, games, fantrax_id])

            # Also update raw snapshots
            cursor.execute("""
                UPDATE raw_player_snapshots
                SET minutes_played = %s, xg90 = %s, xa90 = %s, xgi90 = %s,
                    games_current_season = %s,
                    understat_import = TRUE, import_timestamp = NOW()
                WHERE player_id = %s
            """, [minutes, xg90_val, xa90_val, xgi90_val, games, fantrax_id])

            updated_count += 1

        # Apply manually confirmed mappings
        # Load saved unmatched data to get the original xGI data
        temp_file = os.path.join(os.path.dirname(__file__), '..', 'temp', 'understat_csv_unmatched.json')
        saved_data = None
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)

        for original_name, mapping in confirmed_mappings.items():
            fantrax_id = mapping.get('fantrax_id')
            fantrax_name = mapping.get('fantrax_name')

            if not fantrax_id:
                continue

            # Find the original CSV data for this player
            player_data = None
            if saved_data:
                for player in saved_data.get('unmatched_players', []):
                    if player.get('player_name') == original_name:
                        player_data = player
                        break

            if not player_data:
                print(f"Warning: Could not find CSV data for {original_name}")
                continue

            xg90_val = round(float(player_data.get('xG90', 0)), 3)
            xa90_val = round(float(player_data.get('xA90', 0)), 3)
            xgi90_val = round(float(player_data.get('xGI90', xg90_val + xa90_val)), 3)
            minutes = int(player_data.get('minutes', 0))
            games = int(player_data.get('apps', 0))

            cursor.execute("""
                UPDATE players
                SET minutes = %s, xg90 = %s, xa90 = %s, xgi90 = %s,
                    games_current_season = %s,
                    last_understat_update = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [minutes, xg90_val, xa90_val, xgi90_val, games, fantrax_id])

            cursor.execute("""
                UPDATE raw_player_snapshots
                SET minutes_played = %s, xg90 = %s, xa90 = %s, xgi90 = %s,
                    games_current_season = %s,
                    understat_import = TRUE, import_timestamp = NOW()
                WHERE player_id = %s
            """, [minutes, xg90_val, xa90_val, xgi90_val, games, fantrax_id])

            # Save mapping to name_mappings table for future use
            cursor.execute("""
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
                    verified = EXCLUDED.verified,
                    verification_date = EXCLUDED.verification_date,
                    last_used = EXCLUDED.last_used,
                    usage_count = name_mappings.usage_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                'understat', original_name, fantrax_id, fantrax_name,
                mapping.get('confidence', 100.0), 'manual', True,
                datetime.now(), 'csv_import', datetime.now(), 1
            ))

            updated_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)

        # Update system parameters
        system_params = load_system_parameters()
        if 'xgi_integration' not in system_params:
            system_params['xgi_integration'] = {}
        system_params['xgi_integration']['last_sync'] = time.time()
        system_params['xgi_integration']['source'] = 'csv_import'
        system_params['xgi_integration']['matched_players'] = len(matched_players)
        system_params['xgi_integration']['manual_mappings'] = len(confirmed_mappings)
        save_system_parameters(system_params)

        return jsonify({
            'success': True,
            'players_updated': updated_count,
            'players_reset': players_reset,
            'auto_matched': len(matched_players),
            'manual_mapped': len(confirmed_mappings),
            'message': f'Successfully updated {updated_count} players with Understat CSV data'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to apply CSV data: {str(e)}'}), 500


def parse_formation_csv(lines, cursor):
    """
    Parse formation matrix CSV format from FFS scraping.
    Returns list of player dictionaries with position constraint checking.
    """
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

def parse_ffp_formation_csv(lines, cursor, starter_params=None):
    """
    Parse FFP formation CSV format (scraped web data).
    Format: Team Name, Player1, %, Player2, %, Player3, %...
    Returns list of player dictionaries.
    """
    from io import StringIO
    from src.convert_ffp_csv import confidence_to_multiplier
    
    # Team name mapping from CSV (full names) to database (abbreviations)
    team_name_mapping = {
        'arsenal': 'ARS',
        'aston villa': 'AVL', 
        'bournemouth': 'BOU',
        'brentford': 'BRF',
        'brighton': 'BHA',
        'burnley': 'BUR',
        'chelsea': 'CHE',
        'crystal palace': 'CRY',
        'everton': 'EVE',
        'fulham': 'FUL',
        'leeds': 'LEE',
        'liverpool': 'LIV',
        'man city': 'MCI',
        'manchester city': 'MCI',
        'man utd': 'MUN',
        'manchester united': 'MUN',
        'newcastle': 'NEW',
        'nottingham forest': 'NOT',
        'sunderland': 'SUN',
        'tottenham': 'TOT',
        'west ham': 'WHU',
        'wolves': 'WOL',
        'wolverhampton wanderers': 'WOL'
    }
    
    players_to_process = []
    
    # Find the starting point (Arsenal Predicted Lineup)
    start_processing = False
    
    for line in lines:
        if not line.strip():
            continue
            
        # Start processing from Arsenal Predicted Lineup (first team alphabetically)
        if not start_processing:
            if 'arsenal predicted lineup' in line.lower():
                start_processing = True
            else:
                continue
                
        # Skip lines that don't contain "predicted lineup"
        if 'predicted lineup' not in line.lower():
            continue
            
        # Use CSV reader to properly handle quotes
        csv_reader = csv.reader(StringIO(line))
        line_data = next(csv_reader)
        
        if len(line_data) < 3:  # Need at least team + 1 player + 1 percentage
            continue
            
        # Extract team name (remove "Predicted Lineup" suffix)
        team_raw = line_data[0].strip().strip('"')
        team_clean = team_raw.replace('Predicted Lineup', '').strip()
        
        # Map team name to database abbreviation
        team = team_name_mapping.get(team_clean.lower(), team_clean)
        
        # Process players and percentages (skip team column)
        # Format: Player1, %, Player2, %, Player3, %...
        for i in range(1, len(line_data), 2):  # Step by 2 (player, percentage)
            if i >= len(line_data) or i+1 >= len(line_data):
                break
                
            player_name = line_data[i].strip()
            percentage_str = line_data[i+1].strip().rstrip('%')
            
            if not player_name or not percentage_str:
                continue
                
            # Parse percentage as confidence
            try:
                confidence = float(percentage_str)
            except ValueError:
                confidence = 0
            
            # Determine status based on confidence
            if confidence >= 70:
                status = 'starter'
            elif confidence >= 30:
                status = 'rotation' 
            else:
                status = 'bench'
            
            # Try to determine position from database
            db_position = lookup_player_position(cursor, player_name, team)
            predicted_position = db_position if db_position else 'Unknown'
            
            player_info = {
                'name': player_name,
                'team': team,
                'position': predicted_position,
                'status': status,
                'confidence': confidence,
                'multiplier': confidence_to_multiplier(confidence, starter_params)  # Use proper 5-category system
            }
            
            players_to_process.append(player_info)
    
    return players_to_process

def parse_individual_csv(lines):
    """
    Parse individual player CSV format (original format).
    Returns list of player dictionaries.
    """
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

def parse_ffp_csv(lines):
    """
    Parse FFP enhanced CSV format with confidence-based multipliers.
    Returns list of player dictionaries with custom multipliers.
    Format: Team, Player Name, Position, Predicted Status, Confidence, Multiplier
    """
    from io import StringIO
    
    players_to_process = []
    
    for line in lines:
        if not line.strip():
            continue
        # Use CSV reader to properly handle quotes
        csv_reader = csv.reader(StringIO(line))
        line_data = next(csv_reader)
        if len(line_data) < 6:
            continue
            
        team = line_data[0].strip()
        player_name = line_data[1].strip()
        position = line_data[2].strip()
        status = line_data[3].strip()
        confidence = line_data[4].strip()
        multiplier_str = line_data[5].strip()
        
        # Parse multiplier value
        try:
            custom_multiplier = float(multiplier_str)
        except (ValueError, TypeError):
            custom_multiplier = 1.0  # Default fallback
        
        player_info = {
            'name': player_name,
            'team': team,
            'position': position,
            'status': status,
            'formation_position': None,
            'position_conflict': False,
            'confidence': confidence,
            'custom_multiplier': custom_multiplier  # Store the FFP-calculated multiplier
        }
        
        players_to_process.append(player_info)
    
    return players_to_process


def lookup_player_position(cursor, player_name, team):
    """
    Look up player position in database for position constraint checking.
    Returns position from database or None if not found.
    """
    try:
        # Team is already converted to correct code by parse_ffp_formation_csv
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
        # Gameweek manager removed - using database queries
        # Using database query instead
        
        data = request.get_json() or {}
        formula_version = data.get('formula_version', 'v2.0')
        
        # Always use gameweek 1 for live data system (no gameweek dependencies)
        gameweek = 1
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
                    WHEN COALESCE(p.games_current_season, 0) > 0
                    THEN COALESCE(pf_max.total_points, 0) / p.games_current_season
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
        # Use live_data_system if no gameweek specified
        if gameweek is None:
            conn_temp = get_db_connection()
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT MAX(gameweek) FROM player_form")
            result = cursor_temp.fetchone()
            gameweek = result[0] if result and result[0] else 1
            cursor_temp.close()
            conn_temp.close()
            
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
        # Gameweek manager removed - using database queries
        # Using database query instead
        gameweek = 1  # Fixed for live data system
        
        cursor.execute("""
            SELECT 
                p.name,
                p.team,
                pm.ppg as stored_ppg,
                CASE
                    WHEN COALESCE(p.games_current_season, 0) > 0
                    THEN COALESCE(pf.total_points, 0) / p.games_current_season
                    ELSE 0
                END as calculated_ppg,
                ROUND(ABS(pm.ppg - COALESCE(pf.total_points / NULLIF(p.games_current_season, 0), 0)), 2) as difference,
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
            ORDER BY ABS(pm.ppg - COALESCE(pf.total_points / NULLIF(p.games_current_season, 0), 0)) DESC
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
        
        # Use live_data_system to provide intelligent default range
        if 'gameweek_range' not in data:
            # Gameweek manager removed - using database queries
            # Using database query instead
            current_gw = 3  # Temporarily hardcoded - will implement database query
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
        
        # Use live_data_system to provide intelligent default range
        if 'gameweek_range' not in data:
            # Gameweek manager removed - using database queries
            # Using database query instead
            current_gw = 3  # Temporarily hardcoded - will implement database query
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

# ===============================
# Weekly Archive System
# ===============================

@app.route('/api/archive-week', methods=['POST'])
def archive_current_week():
    """
    Archive the current gameweek analysis data
    This prepares the system for the next gameweek by storing current data
    """
    try:
        # Use fixed gameweek 3 for simple weekly archive system
        current_gameweek = 3
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"Archiving Gameweek {current_gameweek} analysis data...")
        
        # 1. Collect player analysis data
        cursor.execute("""
            SELECT 
                pm.player_id, pm.gameweek, pm.price, pm.ppg, pm.value_score,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier,
                p.name, p.team, p.position, p.games_current_season
            FROM player_metrics pm
            JOIN players p ON pm.player_id = p.id  
            WHERE pm.gameweek = %s
            ORDER BY pm.value_score DESC
        """, [current_gameweek])
        
        player_data = []
        for row in cursor.fetchall():
            player_data.append({
                'player_id': row[0],
                'gameweek': row[1], 
                'price': float(row[2]) if row[2] else 0,
                'ppg': float(row[3]) if row[3] else 0,
                'value_score': float(row[4]) if row[4] else 0,
                'form_multiplier': float(row[5]) if row[5] else 1.0,
                'fixture_multiplier': float(row[6]) if row[6] else 1.0,
                'starter_multiplier': float(row[7]) if row[7] else 1.0,
                'name': row[8],
                'team': row[9],
                'position': row[10],
                'games_played': row[11] if row[11] else 0
            })
        
        # 2. Collect form data used for this gameweek
        cursor.execute("""
            SELECT player_id, gameweek, points 
            FROM player_form 
            WHERE gameweek < %s
            ORDER BY player_id, gameweek
        """, [current_gameweek])
        
        form_data = []
        for row in cursor.fetchall():
            form_data.append({
                'player_id': row[0],
                'gameweek': row[1],
                'points': float(row[2]) if row[2] else 0
            })
        
        # 3. Collect fixture data for this gameweek
        cursor.execute("""
            SELECT gameweek, team_code, opponent_code, is_home, difficulty_score
            FROM team_fixtures
            WHERE gameweek = %s
            ORDER BY team_code
        """, [current_gameweek])
        
        fixture_data = []
        for row in cursor.fetchall():
            fixture_data.append({
                'gameweek': row[0],
                'team': row[1],
                'opponent': row[2],
                'is_home': row[3],
                'difficulty': float(row[4]) if row[4] else 0
            })
        
        # 4. Get top value players for summary
        top_players = sorted(player_data, key=lambda x: x['value_score'], reverse=True)[:20]
        
        # 5. Get current system parameters
        parameters = load_system_parameters()
        
        # 6. Store archive
        cursor.execute("""
            INSERT INTO gameweek_archives (
                gameweek, total_players, analysis_purpose,
                player_data, form_data, fixture_data, 
                parameters_snapshot, top_value_players
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (gameweek) DO UPDATE SET
                archived_at = NOW(),
                total_players = EXCLUDED.total_players,
                player_data = EXCLUDED.player_data,
                form_data = EXCLUDED.form_data, 
                fixture_data = EXCLUDED.fixture_data,
                parameters_snapshot = EXCLUDED.parameters_snapshot,
                top_value_players = EXCLUDED.top_value_players
        """, [
            current_gameweek,
            len(player_data),
            f"Analysis for Gameweek {current_gameweek}",
            json.dumps(player_data),
            json.dumps(form_data),
            json.dumps(fixture_data),
            json.dumps(parameters),
            json.dumps(top_players)
        ])
        
        conn.commit()
        
        print(f"Archived {len(player_data)} players for GW{current_gameweek}")
        print(f"Archived {len(form_data)} form records")
        print(f"Archived {len(fixture_data)} fixture records")
        
        # 7. Return summary
        return jsonify({
            'success': True,
            'gameweek': current_gameweek,
            'archived_data': {
                'players': len(player_data),
                'form_records': len(form_data), 
                'fixtures': len(fixture_data),
                'top_player': top_players[0]['name'] if top_players else 'None'
            },
            'message': f'Gameweek {current_gameweek} analysis archived successfully',
            'next_steps': f'Ready to analyze Gameweek {current_gameweek + 1}'
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'error': f'Archive failed: {str(e)}',
            'success': False
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/archives', methods=['GET'])
def get_archived_gameweeks():
    """Get list of archived gameweeks"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gameweek, archived_at, total_players, analysis_purpose
            FROM gameweek_archives 
            ORDER BY gameweek DESC
        """)
        
        archives = []
        for row in cursor.fetchall():
            archives.append({
                'gameweek': row[0],
                'archived_at': row[1].isoformat() if row[1] else None,
                'total_players': row[2],
                'purpose': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'archives': archives,
            'count': len(archives)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# REACT FRONTEND ROUTES - Added for Railway deployment
# ============================================================================

# DISABLED - WhiteNoise handles this: @app.route('/static/<path:filename>')
# DISABLED - WhiteNoise handles this: def serve_react_static(filename):
# DISABLED - WhiteNoise handles this:     """Serve React static files with robust fallback paths"""
# DISABLED - WhiteNoise handles this: 
# DISABLED - WhiteNoise handles this:     # Try multiple paths in order of preference
# DISABLED - WhiteNoise handles this:     static_paths = [
# DISABLED - WhiteNoise handles this:         # Primary: Built files copied by Railway build process
# DISABLED - WhiteNoise handles this:         os.path.join(os.path.dirname(__file__), 'static', 'react-build', 'static'),
# DISABLED - WhiteNoise handles this:         # Fallback: Direct from frontend build (for development/Git)
# DISABLED - WhiteNoise handles this:         os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'build', 'static')
# DISABLED - WhiteNoise handles this:     ]
# DISABLED - WhiteNoise handles this: 
# DISABLED - WhiteNoise handles this:     app.logger.info(f"📁 Static file request: {filename}")
# DISABLED - WhiteNoise handles this: 
# DISABLED - WhiteNoise handles this:     for i, static_dir in enumerate(static_paths, 1):
# DISABLED - WhiteNoise handles this:         file_path = os.path.join(static_dir, filename)
# DISABLED - WhiteNoise handles this:         app.logger.info(f"🔍 Trying path {i}: {static_dir}")
# DISABLED - WhiteNoise handles this: 
# DISABLED - WhiteNoise handles this:         if os.path.exists(file_path):
# DISABLED - WhiteNoise handles this:             app.logger.info(f"✅ Found file at path {i}: {file_path}")
# DISABLED - WhiteNoise handles this:             return send_file(file_path)
# DISABLED - WhiteNoise handles this:         else:
# DISABLED - WhiteNoise handles this:             app.logger.info(f"❌ Not found at path {i}: {file_path}")
# DISABLED - WhiteNoise handles this: 
# DISABLED - WhiteNoise handles this:     # If no file found, log directory contents for debugging
# DISABLED - WhiteNoise handles this:     for i, static_dir in enumerate(static_paths, 1):
# DISABLED - WhiteNoise handles this:         if os.path.exists(static_dir):
# DISABLED - WhiteNoise handles this:             try:
# DISABLED - WhiteNoise handles this:                 contents = os.listdir(static_dir)[:10]  # Limit to 10 items
# DISABLED - WhiteNoise handles this:                 app.logger.info(f"📋 Directory {i} contents: {contents}")
# DISABLED - WhiteNoise handles this:             except Exception as e:
# DISABLED - WhiteNoise handles this:                 app.logger.error(f"📋 Could not list directory {i}: {e}")
# DISABLED - WhiteNoise handles this:         else:
# DISABLED - WhiteNoise handles this:             app.logger.error(f"📂 Directory {i} does not exist: {static_dir}")
# DISABLED - WhiteNoise handles this: 
# DISABLED - WhiteNoise handles this:     app.logger.error(f"❌ Static file not found in any location: {filename}")
# DISABLED - WhiteNoise handles this:     return f"Static file not found: {filename}", 404

def serve_react_static_old(filename):
    """Serve React static files (CSS, JS, images)"""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), 'static', 'react-build', 'static'),
        filename
    )

@app.route('/manifest.json')
@app.route('/favicon.ico')
@app.route('/robots.txt')
def serve_react_assets():
    """Serve React assets from the build directory"""
    filename = request.path[1:]  # Remove leading slash
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), 'static', 'react-build'),
        filename
    )

@app.route('/api/validate-game-scores', methods=['POST'])
def validate_game_scores():
    """
    Validate game scores using Understat participation data
    Fetches players who actually played in the gameweek and matches them to Fantrax IDs
    """
    try:
        data = request.get_json()

        if not data or 'game_number' not in data:
            return jsonify({'error': 'game_number is required'}), 400

        game_number = int(data['game_number'])

        # Check if integration package is available
        if not INTEGRATION_AVAILABLE:
            return jsonify({
                'error': 'Integration package not available in production mode',
                'message': 'Understat validation requires development environment'
            }), 503

        print(f"Starting validation for Game {game_number}...")

        # Step 1: Extract Understat players who played in this gameweek
        import ScraperFC as sfc
        understat = sfc.Understat()

        # Get match links for the season
        match_links = understat.get_match_links("2025/2026", "EPL")

        # Calculate match range for this gameweek (10 matches per gameweek)
        start_match = (game_number - 1) * 10
        end_match = start_match + 10

        if end_match > len(match_links):
            return jsonify({
                'error': f'Game {game_number} not available yet',
                'message': f'Only {len(match_links) // 10} gameweeks available'
            }), 400

        gameweek_matches = match_links[start_match:end_match]
        players_who_played = set()

        print(f"Processing {len(gameweek_matches)} matches for Game {game_number}...")

        # Extract players from each match
        for i, match_link in enumerate(gameweek_matches):
            try:
                match_data = understat.scrape_match(match_link)
                lineup_data = match_data[2]  # Element 2 contains lineup data

                # Extract players from both teams
                for team_key in ['h', 'a']:  # home and away
                    team_data = lineup_data[team_key]
                    for player_id, player_data in team_data.items():
                        player_name = player_data.get('player')
                        minutes = player_data.get('time', 0)

                        # Only include players who actually played (minutes > 0)
                        if player_name and int(minutes) > 0:
                            players_who_played.add(player_name)

            except Exception as e:
                print(f"Warning: Error processing match {i+1}: {e}")
                continue

        print(f"Found {len(players_who_played)} players who played in Game {game_number}")

        # Step 2: Match Understat players to Fantrax IDs using UnifiedNameMatcher
        matcher = UnifiedNameMatcher(DB_CONFIG)
        matched_players = []
        unmatched_players = []

        for understat_name in players_who_played:
            match_result = matcher.match_player(
                source_name=understat_name,
                source_system='understat',
                team=None,
                position=None
            )

            if match_result['fantrax_id'] is not None and match_result['confidence'] >= 70:
                # High confidence match
                matched_players.append({
                    'understat_name': understat_name,
                    'fantrax_id': match_result['fantrax_id'],
                    'fantrax_name': match_result['fantrax_name'],
                    'confidence': match_result['confidence']
                })
            else:
                # Low confidence or no match - needs manual review
                unmatched_players.append({
                    'understat_name': understat_name,
                    'suggestions': match_result.get('suggested_matches', []),
                    'confidence': match_result.get('confidence', 0)
                })

        print(f"Matched {len(matched_players)}/{len(players_who_played)} players automatically")

        # Step 3: Get current game scores for this gameweek
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT pgs.id, pgs.player_id, pgs.points_scored, pgs.did_play,
                   p.name as player_name
            FROM player_game_scores pgs
            JOIN players p ON pgs.player_id = p.id
            WHERE pgs.game_number = %s
        """, (game_number,))

        game_scores = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f"Found {len(game_scores)} game score records for Game {game_number}")

        # Return validation data for frontend processing
        return jsonify({
            'success': True,
            'game_number': game_number,
            'understat_players_found': len(players_who_played),
            'matched_automatically': len(matched_players),
            'need_manual_matching': len(unmatched_players),
            'matched_players': matched_players,
            'unmatched_players': unmatched_players,
            'game_scores_total': len(game_scores),
            'message': f'Found {len(players_who_played)} players who played in Game {game_number}'
        })

    except Exception as e:
        print(f"Error in validate_game_scores: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@app.route('/api/validate-game-scores-json', methods=['POST'])
def validate_game_scores_json():
    """
    Validate game scores using Understat JSON export (filtered by gameweek dates).
    Workaround for broken ScraperFC library.

    Expected CSV format (semicolon-delimited, filtered by gameweek dates on Understat):
    "number";"player";"team";"apps";"min";"goals";"a";"xG";"xA";"xG90";"xA90";"xG90xA90"

    Players with min > 0 are considered to have played in the gameweek.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get game_number from form data
        game_number = request.form.get('game_number')
        if not game_number:
            return jsonify({'error': 'game_number is required'}), 400
        game_number = int(game_number)

        # Read JSON content

        content = file.read().decode('utf-8-sig')  # Handle BOM
        players_data = json.loads(content)
        if not isinstance(players_data, list):
            return jsonify({'error': 'JSON must be an array of player objects'}), 400

        # Extract players who played (min > 0)
        players_who_played = []
        for player_row in players_data:
            player_name = player_row.get('player', '')
            team = player_row.get('team', '')
            minutes = int(player_row.get('min', 0))

            # Only include players who actually played
            if player_name and minutes > 0:
                players_who_played.append({
                    'player_name': player_name,
                    'team': team,
                    'minutes': minutes
                })

        print(f"JSON Validation: Found {len(players_who_played)} players who played in Game {game_number}")

        # Use Global Name Matching System for player matching
        matcher = UnifiedNameMatcher(DB_CONFIG)
        matched_players = []
        unmatched_players = []

        for player in players_who_played:
            match_result = matcher.match_player(
                source_name=player['player_name'],
                source_system='understat',
                team=player['team'],
                position=None
            )

            if match_result['fantrax_id'] is not None and match_result['confidence'] >= 70:
                matched_players.append({
                    'understat_name': player['player_name'],
                    'fantrax_id': match_result['fantrax_id'],
                    'fantrax_name': match_result['fantrax_name'],
                    'confidence': match_result['confidence'],
                    'minutes': player['minutes']
                })
            else:
                unmatched_players.append({
                    'understat_name': player['player_name'],
                    'team': player['team'],
                    'minutes': player['minutes'],
                    'suggestions': match_result.get('suggested_matches', []),
                    'confidence': match_result.get('confidence', 0)
                })

        print(f"JSON Validation: Matched {len(matched_players)}/{len(players_who_played)} players automatically")

        # Get current game scores for this gameweek
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT pgs.id, pgs.player_id, pgs.points_scored, pgs.did_play,
                   p.name as player_name
            FROM player_game_scores pgs
            JOIN players p ON pgs.player_id = p.id
            WHERE pgs.game_number = %s
        """, (game_number,))

        game_scores = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f"JSON Validation: Found {len(game_scores)} game score records for Game {game_number}")

        # Return validation data in same format as ScraperFC endpoint
        return jsonify({
            'success': True,
            'game_number': game_number,
            'understat_players_found': len(players_who_played),
            'matched_automatically': len(matched_players),
            'need_manual_matching': len(unmatched_players),
            'matched_players': matched_players,
            'unmatched_players': unmatched_players,
            'game_scores_total': len(game_scores),
            'message': f'Found {len(players_who_played)} players who played in Game {game_number} (from CSV)',
            'source': 'json_import'
        })

    except Exception as e:
        print(f"Error in validate_game_scores_json: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'CSV validation failed: {str(e)}'}), 500


@app.route('/api/apply-game-validation', methods=['POST'])
def apply_game_validation():
    """
    Apply the validation results to update did_play field and save new mappings
    """
    try:
        data = request.get_json()

        if not data or 'game_number' not in data:
            return jsonify({'error': 'game_number is required'}), 400

        game_number = int(data['game_number'])
        confirmed_mappings = data.get('confirmed_mappings', {})
        matched_players = data.get('matched_players', [])

        print(f"Applying validation for Game {game_number}...")
        print(f"Received {len(confirmed_mappings)} manual mappings")
        print(f"Received {len(matched_players)} automatic matches")

        # Combine automatic and manual mappings
        all_mappings = {}

        # Add automatic matches
        for match in matched_players:
            all_mappings[match['understat_name']] = match['fantrax_id']

        # Add manual confirmations (these override automatic matches)
        for understat_name, fantrax_id in confirmed_mappings.items():
            if fantrax_id:  # Only if user selected a mapping
                all_mappings[understat_name] = fantrax_id

        print(f"Total mappings to apply: {len(all_mappings)}")

        # Get all players who played according to Understat
        played_fantrax_ids = set(all_mappings.values())

        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Save new mappings to name_mappings table
        saved_mappings = 0
        for understat_name, fantrax_id in confirmed_mappings.items():
            if fantrax_id:  # Only save if user made a selection
                try:
                    cursor.execute("""
                        INSERT INTO name_mappings (source_name, fantrax_id, source_system, confidence_score, verified, created_at)
                        VALUES (%s, %s, 'understat', 100, true, NOW())
                        ON CONFLICT (source_name, source_system)
                        DO UPDATE SET
                            fantrax_id = EXCLUDED.fantrax_id,
                            confidence_score = 100,
                            verified = true,
                            updated_at = NOW(),
                            usage_count = name_mappings.usage_count + 1
                    """, [understat_name, fantrax_id])
                    saved_mappings += 1
                except Exception as e:
                    print(f"Warning: Error saving mapping {understat_name} -> {fantrax_id}: {e}")

        print(f"Saved {saved_mappings} new/updated mappings")

        # Step 2: Update did_play field in player_game_scores
        cursor.execute("""
            UPDATE player_game_scores
            SET did_play = CASE
                WHEN player_id = ANY(%s) THEN true
                ELSE false
            END
            WHERE game_number = %s
        """, [list(played_fantrax_ids), game_number])

        updated_scores = cursor.rowcount

        # Step 3: Get validation statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_scores,
                COUNT(CASE WHEN did_play = true THEN 1 END) as players_played,
                COUNT(CASE WHEN did_play = false THEN 1 END) as players_benched,
                COUNT(CASE WHEN did_play = true AND points_scored = 0 THEN 1 END) as legitimate_zeros,
                COUNT(CASE WHEN did_play = false AND points_scored = 0 THEN 1 END) as excluded_zeros
            FROM player_game_scores
            WHERE game_number = %s
        """, (game_number,))

        stats = cursor.fetchone()

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'game_number': game_number,
            'mappings_saved': saved_mappings,
            'scores_updated': updated_scores,
            'validation_stats': {
                'total_scores': stats[0],
                'players_played': stats[1],
                'players_benched': stats[2],
                'legitimate_zeros': stats[3],
                'excluded_zeros': stats[4]
            },
            'message': f'Validation complete: {stats[1]} players marked as played, {stats[2]} as benched'
        })

    except Exception as e:
        print(f"Error in apply_game_validation: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({'error': f'Failed to apply validation: {str(e)}'}), 500
@app.route('/')
@app.route('/<path:path>')
def serve_react_app(path=''):
    """Serve React app for all non-API routes"""
    # Skip API routes
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404

    # Serve React index.html for all other routes
    try:
        return send_file(
            os.path.join(os.path.dirname(__file__), 'static', 'react-build', 'index.html')
        )
    except FileNotFoundError:
        return jsonify({
            'error': 'Frontend not built. Run ./build.sh to build the React frontend.',
            'instructions': [
                '1. Run: chmod +x build.sh',
                '2. Run: ./build.sh',
                '3. Restart the Flask server'
            ]
        }), 404




@app.route('/api/npxg/sync-team-stats', methods=['POST'])
def sync_npxg_team_stats():
    """Sync NPxG team statistics from Understat for all 20 Premier League teams"""
    try:
        # Check if integration package is available
        if not INTEGRATION_AVAILABLE:
            return jsonify({
                'error': 'Integration package not available in production mode',
                'message': 'This feature is only available in development environment'
            }), 503

        # Import ScraperFC using the same pattern as UnderstatIntegrator
        try:
            import ScraperFC as sfc
        except ImportError:
            return jsonify({
                'error': 'ScraperFC library not available',
                'message': 'Please install ScraperFC: pip install ScraperFC'
            }), 503

        # Initialize scraper
        understat = sfc.Understat()

        # Fetch current season team stats (NPxG/NPxGA directly available)
        try:
            # Returns 3 tables: overall, home, away - we want overall (index 0)
            tables = understat.scrape_league_tables(year='2025/2026', league='EPL')
            team_stats_df = tables[0] if tables else None
        except Exception as e:
            return jsonify({
                'error': f'Failed to fetch team NPxG data: {str(e)}',
                'message': 'Unable to retrieve team statistics from Understat'
            }), 500

        if team_stats_df is None or team_stats_df.empty:
            return jsonify({'error': 'No NPxG team data available for 2025/2026 season'}), 500

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing team metrics
        cursor.execute("DELETE FROM team_metrics")

        updated_teams = 0
        league_totals = {'npxg': 0, 'npxga': 0, 'matches': 0}

        for idx, team in team_stats_df.iterrows():
            # Extract team data using correct column names from ScraperFC
            team_name = team.get('Team', '')
            npxg = float(team.get('NPxG', 0))
            npxga = float(team.get('NPxGA', 0))
            matches_played = int(team.get('M', 0))

            # Calculate NPxGD (Difference)
            npxgd = npxg - npxga

            # Generate 3-letter team code from team name
            # Use first 3 letters, converting common names
            team_code_mapping = {
                'Manchester United': 'MUN',
                'Manchester City': 'MCI',
                'Arsenal': 'ARS',
                'Liverpool': 'LIV',
                'Chelsea': 'CHE',
                'Tottenham': 'TOT',
                'Newcastle United': 'NEW',
                'Brighton': 'BHA',
                'Aston Villa': 'AVL',
                'West Ham': 'WHU',
                'Crystal Palace': 'CRY',
                'Fulham': 'FUL',
                'Brentford': 'BRE',
                'Wolverhampton Wanderers': 'WOL',
                'Wolverhampton': 'WOL',  # Alternative name
                'Everton': 'EVE',
                'Bournemouth': 'BOU',
                'Nottingham Forest': 'NFO',
                # Current 2025-26 season promoted teams
                'Leeds United': 'LEE',
                'Burnley': 'BUR',
                'Sunderland': 'SUN',
                # Relegated teams (may still appear in data)
                'Leicester City': 'LEI',
                'Ipswich Town': 'IPS',
                'Southampton': 'SOU'
            }

            team_code = team_code_mapping.get(team_name, team_name[:3].upper())

            # Insert team metrics
            cursor.execute("""
                INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (team_code) DO UPDATE SET
                    team_name = EXCLUDED.team_name,
                    npxg = EXCLUDED.npxg,
                    npxga = EXCLUDED.npxga,
                    npxgd = EXCLUDED.npxgd,
                    matches_played = EXCLUDED.matches_played,
                    last_updated = EXCLUDED.last_updated
            """, [team_code, team_name, npxg, npxga, npxgd, matches_played])

            # Accumulate league totals for averaging
            league_totals['npxg'] += npxg
            league_totals['npxga'] += npxga
            league_totals['matches'] += matches_played
            updated_teams += 1

        # Calculate league averages
        total_teams = updated_teams
        league_avg_npxg = league_totals['npxg'] / total_teams if total_teams > 0 else 0
        league_avg_npxga = league_totals['npxga'] / total_teams if total_teams > 0 else 0

        conn.commit()
        conn.close()

        # Update system parameters with sync timestamp
        system_params = load_system_parameters()
        if 'npxg_fixture' not in system_params:
            system_params['npxg_fixture'] = {}

        system_params['npxg_fixture']['last_sync'] = time.time()
        system_params['npxg_fixture']['teams_updated'] = updated_teams
        system_params['npxg_fixture']['league_avg_npxg'] = round(league_avg_npxg, 3)
        system_params['npxg_fixture']['league_avg_npxga'] = round(league_avg_npxga, 3)
        save_system_parameters(system_params)

        return jsonify({
            'success': True,
            'teams_updated': updated_teams,
            'league_avg_npxg': round(league_avg_npxg, 3),
            'league_avg_npxga': round(league_avg_npxga, 3),
            'total_matches': league_totals['matches'],
            'message': f'Successfully synced NPxG data for {updated_teams} Premier League teams'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/npxg/import-team-json', methods=['POST'])
def import_npxg_team_json():
    """
    Import NPxG team statistics from Understat JSON export.
    Workaround for broken ScraperFC library.

    Expected JSON format (array of objects):
    "number";"team";"matches";"wins";"draws";"loses";"goals";"ga";"points";"xG";"NPxG";"xGA";"NPxGA";"xPTS"
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read JSON content

        content = file.read().decode('utf-8-sig')  # Handle BOM
        teams_data = json.loads(content)

        # Team name to code mapping (same as ScraperFC endpoint)
        team_code_mapping = {
            'Manchester United': 'MUN',
            'Manchester City': 'MCI',
            'Arsenal': 'ARS',
            'Liverpool': 'LIV',
            'Chelsea': 'CHE',
            'Tottenham': 'TOT',
            'Newcastle United': 'NEW',
            'Brighton': 'BHA',
            'Aston Villa': 'AVL',
            'West Ham': 'WHU',
            'Crystal Palace': 'CRY',
            'Fulham': 'FUL',
            'Brentford': 'BRE',
            'Wolverhampton Wanderers': 'WOL',
            'Wolverhampton': 'WOL',
            'Everton': 'EVE',
            'Bournemouth': 'BOU',
            'Nottingham Forest': 'NFO',
            'Leeds United': 'LEE',
            'Leeds': 'LEE',
            'Burnley': 'BUR',
            'Sunderland': 'SUN',
            'Leicester City': 'LEI',
            'Ipswich Town': 'IPS',
            'Southampton': 'SOU'
        }

        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing team metrics
        cursor.execute("DELETE FROM team_metrics")

        updated_teams = 0
        league_totals = {'npxg': 0, 'npxga': 0, 'matches': 0}

        for team in teams_data:
            # Extract data from JSON object
            team_name = team.get('team', '')
            npxg = float(team.get('NPxG', 0))
            npxga = float(team.get('NPxGA', 0))
            matches_played = int(team.get('matches', 0))

            # Calculate NPxGD (Difference)
            npxgd = npxg - npxga

            # Get team code
            team_code = team_code_mapping.get(team_name, team_name[:3].upper())

            # Insert team metrics
            cursor.execute("""
                INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (team_code) DO UPDATE SET
                    team_name = EXCLUDED.team_name,
                    npxg = EXCLUDED.npxg,
                    npxga = EXCLUDED.npxga,
                    npxgd = EXCLUDED.npxgd,
                    matches_played = EXCLUDED.matches_played,
                    last_updated = EXCLUDED.last_updated
            """, [team_code, team_name, npxg, npxga, npxgd, matches_played])

            # Accumulate league totals
            league_totals['npxg'] += npxg
            league_totals['npxga'] += npxga
            league_totals['matches'] += matches_played
            updated_teams += 1

        # Calculate league averages
        total_teams = updated_teams
        league_avg_npxg = league_totals['npxg'] / total_teams if total_teams > 0 else 0
        league_avg_npxga = league_totals['npxga'] / total_teams if total_teams > 0 else 0

        conn.commit()
        cursor.close()
        conn.close()

        # Update system parameters with sync timestamp
        system_params = load_system_parameters()
        if 'npxg_fixture' not in system_params:
            system_params['npxg_fixture'] = {}

        system_params['npxg_fixture']['last_sync'] = time.time()
        system_params['npxg_fixture']['teams_updated'] = updated_teams
        system_params['npxg_fixture']['league_avg_npxg'] = round(league_avg_npxg, 3)
        system_params['npxg_fixture']['league_avg_npxga'] = round(league_avg_npxga, 3)
        system_params['npxg_fixture']['source'] = 'csv_import'
        save_system_parameters(system_params)

        return jsonify({
            'success': True,
            'teams_updated': updated_teams,
            'league_avg_npxg': round(league_avg_npxg, 3),
            'league_avg_npxga': round(league_avg_npxga, 3),
            'total_matches': league_totals['matches'],
            'message': f'Successfully imported NPxG data for {updated_teams} Premier League teams from CSV'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'CSV import failed: {str(e)}'}), 500


@app.route('/api/railway/sync', methods=['POST'])
def sync_to_railway():
    """Sync all essential tables to Railway database with progress tracking"""
    try:
        import subprocess
        import threading
        import queue
        from optimized_railway_sync import OptimizedRailwaySync

        # Store progress updates
        progress_queue = queue.Queue()
        sync_results = []

        def progress_callback(progress_data):
            """Callback to receive progress updates"""
            progress_queue.put(progress_data)
            sync_results.append(progress_data)

        def run_sync():
            """Run sync in background thread"""
            try:
                syncer = OptimizedRailwaySync(progress_callback=progress_callback)
                result = syncer.sync_all()
                progress_queue.put({'type': 'complete', 'result': result})
            except Exception as e:
                progress_queue.put({'type': 'error', 'error': str(e)})

        # Start sync in background thread
        sync_thread = threading.Thread(target=run_sync)
        sync_thread.start()

        # Store thread and queue in session for progress checking
        import secrets
        sync_id = secrets.token_urlsafe(16)

        # Store in global dict (in production, use Redis or similar)
        if not hasattr(app, 'sync_sessions'):
            app.sync_sessions = {}

        app.sync_sessions[sync_id] = {
            'thread': sync_thread,
            'queue': progress_queue,
            'results': sync_results,
            'started_at': time.time()
        }

        # Clean up old sessions (older than 1 hour)
        current_time = time.time()
        app.sync_sessions = {
            k: v for k, v in app.sync_sessions.items()
            if current_time - v['started_at'] < 3600
        }

        return jsonify({
            'success': True,
            'sync_id': sync_id,
            'message': 'Railway sync started',
            'check_progress_url': f'/api/railway/sync-progress/{sync_id}'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to start sync: {str(e)}'}), 500

@app.route('/api/railway/sync-progress/<sync_id>', methods=['GET'])
def get_railway_sync_progress(sync_id):
    """Get progress of ongoing Railway sync"""
    try:
        if not hasattr(app, 'sync_sessions') or sync_id not in app.sync_sessions:
            return jsonify({'error': 'Invalid or expired sync ID'}), 404

        session = app.sync_sessions[sync_id]
        progress_updates = []

        # Get all available progress updates (non-blocking)
        while not session['queue'].empty():
            try:
                update = session['queue'].get_nowait()
                progress_updates.append(update)

                # Check if sync is complete
                if update.get('type') == 'complete':
                    result = update.get('result', {})
                    # Clean up session
                    del app.sync_sessions[sync_id]
                    return jsonify({
                        'status': 'complete',
                        'success': result.get('success', False),
                        'tables_synced': result.get('tables_synced', 0),
                        'total_tables': result.get('total_tables', 0),
                        'results': result.get('results', {}),
                        'updates': progress_updates
                    })
                elif update.get('type') == 'error':
                    # Clean up session
                    del app.sync_sessions[sync_id]
                    return jsonify({
                        'status': 'error',
                        'error': update.get('error', 'Unknown error'),
                        'updates': progress_updates
                    })
            except:
                break

        # Check if thread is still alive
        is_running = session['thread'].is_alive()

        return jsonify({
            'status': 'running' if is_running else 'unknown',
            'updates': progress_updates,
            'all_results': session['results']
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500

@app.route('/api/npxg/team-stats', methods=['GET'])
def get_npxg_team_stats():
    """Retrieve current NPxG team statistics from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT team_code, team_name, npxg, npxga, npxgd,
                   matches_played, last_updated
            FROM team_metrics
            ORDER BY npxg DESC
        """)

        teams = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to list of dictionaries for JSON response
        team_stats = []
        for team in teams:
            team_stats.append({
                'team_code': team['team_code'],
                'team_name': team['team_name'],
                'npxg': float(team['npxg']),
                'npxga': float(team['npxga']),
                'npxgd': float(team['npxgd']),
                'matches_played': team['matches_played'],
                'last_updated': team['last_updated'].isoformat() if team['last_updated'] else None
            })

        return jsonify({
            'success': True,
            'teams': team_stats,
            'total_teams': len(team_stats)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/npxg/config', methods=['GET', 'PUT'])
def manage_npxg_config():
    """Get or update NPxG fixture configuration parameters"""
    try:
        if request.method == 'GET':
            # Return current NPxG configuration
            system_params = load_system_parameters()
            npxg_config = system_params.get('npxg_fixture', {})

            return jsonify({
                'success': True,
                'config': npxg_config
            })

        elif request.method == 'PUT':
            # Update NPxG configuration
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No configuration data provided'}), 400

            system_params = load_system_parameters()

            # Update NPxG config section
            if 'npxg_fixture' not in system_params:
                system_params['npxg_fixture'] = {}

            # Update provided fields
            for key, value in data.items():
                if key in ['enabled', 'weight', 'home_away_adjustments', 'position_mappings', 'bounds']:
                    system_params['npxg_fixture'][key] = value

            # Save updated parameters
            save_system_parameters(system_params)

            return jsonify({
                'success': True,
                'message': 'NPxG configuration updated successfully',
                'config': system_params['npxg_fixture']
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# LINEUP OPTIMIZER ENDPOINTS
# ============================================================================

# In-memory storage for current lineup (per-session in production, use Flask session)
_current_lineup_roster = []

@app.route('/api/lineup/import', methods=['POST'])
def import_lineup_roster():
    """
    Import team roster CSV from Fantrax export.
    Expects CSV with columns: ID, Player, Team, Position, Salary
    Returns enriched roster with current prices and True Values from database.
    """
    global _current_lineup_roster

    try:
        # Check for uploaded file
        if 'roster_csv' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded. Use form field name "roster_csv"'
            }), 400

        file = request.files['roster_csv']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Read CSV file - Fantrax Team Roster has multiple sections (GK vs Outfield)
        import pandas as pd

        file_content = file.stream.read().decode("UTF8")
        lines = file_content.strip().split('\n')

        # Parse Fantrax multi-section Team Roster CSV
        # Format: Section header row, then column header row, then data rows
        # Sections: "Goalkeeper" and "Outfielder" with different column counts
        players_data = []
        current_section = None
        header_row = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers (e.g., "","Goalkeeper" or "","Outfielder")
            if line.startswith('""') and ('Goalkeeper' in line or 'Outfielder' in line):
                current_section = 'G' if 'Goalkeeper' in line else 'Outfield'
                header_row = None  # Next row will be the header
                continue

            # Parse the row
            # Handle CSV quoting properly
            try:
                reader = csv.reader([line])
                row = next(reader)
            except:
                continue

            # Check if this is a header row (starts with "ID")
            if row and row[0] == 'ID':
                header_row = row
                continue

            # Skip if no header yet or empty row
            if not header_row or not row or not row[0]:
                continue

            # Skip rows that don't start with a player ID (e.g., "*044ei*")
            if not row[0].startswith('*'):
                continue

            # Parse data row using header mapping
            try:
                row_dict = dict(zip(header_row, row))

                # Extract required fields with fallbacks
                player_id = row_dict.get('ID', '').strip('*')
                player_name = row_dict.get('Player', 'Unknown')
                team = row_dict.get('Team', 'UNK')
                position = row_dict.get('Pos', row_dict.get('Position', 'UNK'))
                salary = float(row_dict.get('Salary', '0') or '0')

                if player_id and player_name:
                    players_data.append({
                        'ID': player_id,
                        'Player': player_name,
                        'Team': team,
                        'Position': position,
                        'Salary': salary
                    })
            except Exception as parse_error:
                print(f"Skipping row due to parse error: {parse_error}")
                continue

        if not players_data:
            return jsonify({
                'success': False,
                'error': 'No valid player data found in CSV. Expected Fantrax Team Roster format.'
            }), 400

        # Convert to DataFrame for consistent processing
        csv_input = pd.DataFrame(players_data)

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        roster = []
        unmatched = []

        for index, row in csv_input.iterrows():
            # Extract player data from CSV
            player_id = str(row['ID']).strip('*')
            player_name = row['Player']
            team = row['Team']
            position = row['Position']
            purchase_price = float(row['Salary'])

            # Look up current data from database
            cursor.execute("""
                SELECT
                    p.id, p.name, p.team, p.position,
                    pm.price as current_price,
                    pm.true_value,
                    p.roi,
                    pm.form_multiplier,
                    pm.fixture_multiplier,
                    pm.starter_multiplier,
                    pm.xgi_multiplier,
                    pm.next_opponent,
                    pm.is_home
                FROM players p
                JOIN player_metrics pm ON p.id = pm.player_id AND pm.gameweek = 1
                WHERE p.id = %s
            """, [player_id])

            db_player = cursor.fetchone()

            if db_player:
                roster.append({
                    'csv_id': player_id,
                    'player_id': db_player['id'],
                    'name': db_player['name'],
                    'team': db_player['team'],
                    'position': db_player['position'],
                    'purchase_price': purchase_price,
                    'current_price': float(db_player['current_price']) if db_player['current_price'] else purchase_price,
                    'true_value': float(db_player['true_value']) if db_player['true_value'] else 0,
                    'roi': float(db_player['roi']) if db_player['roi'] else 0,
                    'form_multiplier': float(db_player['form_multiplier']) if db_player['form_multiplier'] else 1.0,
                    'fixture_multiplier': float(db_player['fixture_multiplier']) if db_player['fixture_multiplier'] else 1.0,
                    'starter_multiplier': float(db_player['starter_multiplier']) if db_player['starter_multiplier'] else 1.0,
                    'xgi_multiplier': float(db_player['xgi_multiplier']) if db_player['xgi_multiplier'] else 1.0,
                    'next_opponent': db_player['next_opponent'],
                    'is_home': db_player['is_home'],
                    'matched': True
                })
            else:
                # Player not in database - still include but mark as unmatched
                unmatched.append({
                    'csv_id': player_id,
                    'name': player_name,
                    'team': team,
                    'position': position,
                    'purchase_price': purchase_price
                })
                roster.append({
                    'csv_id': player_id,
                    'player_id': player_id,
                    'name': player_name,
                    'team': team,
                    'position': position,
                    'purchase_price': purchase_price,
                    'current_price': purchase_price,
                    'true_value': 0,
                    'roi': 0,
                    'form_multiplier': 1.0,
                    'fixture_multiplier': 1.0,
                    'starter_multiplier': 1.0,
                    'xgi_multiplier': 1.0,
                    'next_opponent': None,
                    'is_home': None,
                    'matched': False
                })

        cursor.close()
        conn.close()

        # Store roster in memory for subsequent calls
        _current_lineup_roster = roster

        # Calculate totals
        total_purchase = sum(p['purchase_price'] for p in roster)
        total_current = sum(p['current_price'] for p in roster)
        total_true_value = sum(p['true_value'] for p in roster)

        return jsonify({
            'success': True,
            'roster': roster,
            'unmatched': unmatched,
            'total_players': len(roster),
            'matched_count': len([p for p in roster if p['matched']]),
            'totals': {
                'purchase_price': round(total_purchase, 2),
                'current_price': round(total_current, 2),
                'true_value': round(total_true_value, 2),
                'price_change': round(total_current - total_purchase, 2)
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/lineup/current', methods=['GET'])
def get_current_lineup():
    """Return the current imported lineup roster."""
    global _current_lineup_roster

    if not _current_lineup_roster:
        return jsonify({
            'success': True,
            'roster': [],
            'message': 'No roster imported yet'
        })

    # Calculate totals
    total_purchase = sum(p['purchase_price'] for p in _current_lineup_roster)
    total_current = sum(p['current_price'] for p in _current_lineup_roster)
    total_true_value = sum(p['true_value'] for p in _current_lineup_roster)

    # Detect formation
    def detect_formation(players):
        positions = {'G': 0, 'D': 0, 'M': 0, 'F': 0}
        for p in players:
            pos = p['position'].split(',')[0]  # Primary position
            if pos in positions:
                positions[pos] += 1
        return f"{positions['D']}-{positions['M']}-{positions['F']}"

    return jsonify({
        'success': True,
        'roster': _current_lineup_roster,
        'formation': detect_formation(_current_lineup_roster),
        'totals': {
            'purchase_price': round(total_purchase, 2),
            'current_price': round(total_current, 2),
            'true_value': round(total_true_value, 2),
            'budget_used': round(total_current, 2),
            'budget_remaining': round(100 - total_current, 2)
        }
    })


@app.route('/api/lineup/optimize', methods=['POST'])
def optimize_lineup():
    """
    Generate 3 optimized lineup alternatives based on True Value.

    Request body:
    {
        "locked_player_ids": ["id1", "id2"],  # Players to keep in lineup
        "locked_players_data": [{"player_id": "id1", "purchase_price": 5.5}, ...],  # Optional: with purchase prices
        "roster_players_data": [{"player_id": "id1", "purchase_price": 5.5}, ...],  # Full CSV roster with purchase prices
        "budget": 100,                         # Total budget constraint
    }
    """
    try:
        data = request.get_json() or {}
        locked_player_ids = set(data.get('locked_player_ids', []))
        locked_players_data = {p['player_id']: p for p in data.get('locked_players_data', [])}
        # NEW: Full roster with purchase prices - use these as "owned player" costs
        roster_players_data = {p['player_id']: float(p.get('purchase_price', 0)) for p in data.get('roster_players_data', [])}
        budget = float(data.get('budget', 100))

        # Load position value weights for optimizer bias control
        params = load_system_parameters()
        lineup_config = params.get('lineup_optimizer', {})
        position_value_weights = lineup_config.get('position_value_weights', {
            'G': 0.85, 'D': 0.90, 'M': 1.0, 'F': 1.0
        })

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get all available players with their stats
        # Note: No gameweek filter - using live table approach (matches main /api/players)
        cursor.execute("""
            SELECT
                p.id, p.name, p.team, p.position,
                pm.price as current_price,
                pm.true_value,
                p.roi,
                pm.form_multiplier,
                pm.fixture_multiplier,
                pm.starter_multiplier,
                pm.xgi_multiplier,
                pm.next_opponent,
                pm.is_home
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.price > 0 
              AND pm.true_value IS NOT NULL
              AND COALESCE(p.exclude_from_optimizer, FALSE) = FALSE
            ORDER BY pm.true_value DESC
        """)

        all_players = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to list of dicts with proper types
        players_pool = []
        for p in all_players:
            players_pool.append({
                'player_id': p['id'],
                'name': p['name'],
                'team': p['team'],
                'position': p['position'],
                'current_price': float(p['current_price']) if p['current_price'] else 0,
                'true_value': float(p['true_value']) if p['true_value'] else 0,
                'roi': float(p['roi']) if p['roi'] else 0,
                'form_multiplier': float(p['form_multiplier']) if p['form_multiplier'] else 1.0,
                'fixture_multiplier': float(p['fixture_multiplier']) if p['fixture_multiplier'] else 1.0,
                'starter_multiplier': float(p['starter_multiplier']) if p['starter_multiplier'] else 1.0,
                'xgi_multiplier': float(p['xgi_multiplier']) if p['xgi_multiplier'] else 1.0,
                'next_opponent': p['next_opponent'],
                'is_home': p['is_home']
            })

        # Get locked players from pool
        locked_players = [p for p in players_pool if p['player_id'] in locked_player_ids]

        # Get effective cost for ANY player:
        # - If player is in roster (CSV), use their purchase_price (discounted cost)
        # - Otherwise, use current_price (market cost to acquire)
        def get_player_cost(player):
            player_id = player['player_id']
            # First check roster_players_data (full CSV roster with purchase prices)
            if player_id in roster_players_data and roster_players_data[player_id] > 0:
                return roster_players_data[player_id]
            # Fallback to locked_players_data for backward compatibility
            if player_id in locked_players_data and 'purchase_price' in locked_players_data[player_id]:
                return float(locked_players_data[player_id]['purchase_price'])
            # New player - use market price
            return player['current_price']

        locked_cost = sum(get_player_cost(p) for p in locked_players)

        # Position constraints
        POSITION_CONSTRAINTS = {
            'G': {'min': 1, 'max': 1},
            'D': {'min': 3, 'max': 5},
            'M': {'min': 3, 'max': 5},
            'F': {'min': 1, 'max': 3}
        }

        def get_primary_position(position_str):
            """Get primary position from multi-position string like 'M,F'"""
            return position_str.split(',')[0].strip()

        def can_play_position(player, target_pos):
            """Check if player can fill a position slot"""
            return target_pos in player['position']

        def count_positions(lineup):
            """Count players in each position (uses selected_position if available from ILP)"""
            counts = {'G': 0, 'D': 0, 'M': 0, 'F': 0}
            for p in lineup:
                # Use selected_position from ILP if available, otherwise fall back to primary position
                pos = p.get('selected_position') or get_primary_position(p['position'])
                if pos in counts:
                    counts[pos] += 1
            return counts

        def validate_formation(lineup):
            """Check if lineup meets position constraints"""
            counts = count_positions(lineup)
            for pos, constraints in POSITION_CONSTRAINTS.items():
                if counts[pos] < constraints['min'] or counts[pos] > constraints['max']:
                    return False
            return len(lineup) == 11

        def optimize_lineup_ilp(locked, available, remaining_budget, excluded_ids=None, previous_lineups=None, formation="3-5-2", pos_weights=None):
            """
            Use Integer Linear Programming to find optimal lineup.

            Args:
                locked: List of locked player dicts
                available: List of all available player dicts
                remaining_budget: Budget after locked players
                excluded_ids: Set of player IDs to exclude
                previous_lineups: List of previous lineup player ID sets (for generating alternatives)
                formation: Target formation ("3-5-2" or "3-4-3")
                pos_weights: Dict of position value weights {'G': 0.85, 'D': 0.90, 'M': 1.0, 'F': 1.0}

            Returns: (lineup, total_cost) or (None, 0) if infeasible
            """
            if pos_weights is None:
                pos_weights = {'G': 1.0, 'D': 1.0, 'M': 1.0, 'F': 1.0}
            if excluded_ids is None:
                excluded_ids = set()
            if previous_lineups is None:
                previous_lineups = []

            # Filter available players (exclude locked and excluded)
            locked_ids = set(p['player_id'] for p in locked)
            candidates = [
                p for p in available
                if p['player_id'] not in locked_ids
                and p['player_id'] not in excluded_ids
                and p['current_price'] <= remaining_budget  # Basic budget filter
            ]

            if not candidates:
                return None, 0

            # Create the ILP problem
            prob = pulp.LpProblem("LineupOptimization", pulp.LpMaximize)

            # Create binary variables for each player-position combination
            # For multi-position players like "M,F", create separate variables for each position
            player_vars = {}  # (player_id, position) -> variable
            player_to_positions = {}  # player_id -> list of positions

            for p in candidates:
                positions = [pos.strip() for pos in p['position'].split(',')]
                player_to_positions[p['player_id']] = positions
                for pos in positions:
                    var_name = f"x_{p['player_id']}_{pos}"
                    player_vars[(p['player_id'], pos)] = pulp.LpVariable(var_name, cat='Binary')

            # Also add locked players (they're fixed at 1)
            for p in locked:
                positions = [pos.strip() for pos in p['position'].split(',')]
                player_to_positions[p['player_id']] = positions
                # Use primary position for locked players
                primary_pos = positions[0]
                var_name = f"x_{p['player_id']}_{primary_pos}"
                player_vars[(p['player_id'], primary_pos)] = pulp.LpVariable(var_name, cat='Binary')

            # Objective: Maximize total true value (with position weights applied)
            # Position weights reduce priority of certain positions (e.g., G=0.85, D=0.90)
            # This only affects optimization, not the actual True Value shown in results
            prob += pulp.lpSum([
                player_vars[(p['player_id'], pos)] * p['true_value'] * pos_weights.get(pos, 1.0)
                for p in candidates
                for pos in player_to_positions[p['player_id']]
                if (p['player_id'], pos) in player_vars
            ]) + pulp.lpSum([
                player_vars[(p['player_id'], player_to_positions[p['player_id']][0])] * p['true_value'] * pos_weights.get(player_to_positions[p['player_id']][0], 1.0)
                for p in locked
                if (p['player_id'], player_to_positions[p['player_id']][0]) in player_vars
            ]), "WeightedTrueValue"

            # Constraint 1: Budget (only for candidates, locked players already accounted for)
            # Use get_player_cost() to respect CSV purchase prices for owned players
            prob += pulp.lpSum([
                player_vars[(p['player_id'], pos)] * get_player_cost(p)
                for p in candidates
                for pos in player_to_positions[p['player_id']]
                if (p['player_id'], pos) in player_vars
            ]) <= remaining_budget, "Budget"

            # Constraint 2: Each player can only be selected once (across all positions)
            for player_id, positions in player_to_positions.items():
                if len(positions) > 1:  # Multi-position player
                    prob += pulp.lpSum([
                        player_vars[(player_id, pos)]
                        for pos in positions
                        if (player_id, pos) in player_vars
                    ]) <= 1, f"OnePosition_{player_id}"

            # Constraint 3: Locked players must be selected
            for p in locked:
                primary_pos = player_to_positions[p['player_id']][0]
                if (p['player_id'], primary_pos) in player_vars:
                    prob += player_vars[(p['player_id'], primary_pos)] == 1, f"Locked_{p['player_id']}"

            # Constraint 4: Position constraints
            # Count how many locked players are in each position
            locked_counts = {'G': 0, 'D': 0, 'M': 0, 'F': 0}
            for p in locked:
                primary_pos = player_to_positions[p['player_id']][0]
                if primary_pos in locked_counts:
                    locked_counts[primary_pos] += 1

            # GK: exactly 1
            gk_needed = 1 - locked_counts['G']
            if gk_needed > 0:
                prob += pulp.lpSum([
                    player_vars[(p['player_id'], 'G')]
                    for p in candidates
                    if 'G' in player_to_positions[p['player_id']] and (p['player_id'], 'G') in player_vars
                ]) == gk_needed, "GK_Count"

            # DEF: exactly 3 (formations: 3-5-2 or 3-4-3)
            def_candidates_sum = pulp.lpSum([
                player_vars[(p['player_id'], 'D')]
                for p in candidates
                if 'D' in player_to_positions[p['player_id']] and (p['player_id'], 'D') in player_vars
            ])
            def_needed = 3 - locked_counts['D']
            prob += def_candidates_sum == def_needed, "DEF_Exact"

            # MID/FWD constraints based on formation parameter
            # Parse formation (e.g., "3-5-2" -> DEF=3, MID=5, FWD=2)
            formation_parts = formation.split('-')
            target_mid = int(formation_parts[1])
            target_fwd = int(formation_parts[2])

            mid_candidates_sum = pulp.lpSum([
                player_vars[(p['player_id'], 'M')]
                for p in candidates
                if 'M' in player_to_positions[p['player_id']] and (p['player_id'], 'M') in player_vars
            ])
            mid_needed = target_mid - locked_counts['M']
            prob += mid_candidates_sum == mid_needed, "MID_Exact"

            fwd_candidates_sum = pulp.lpSum([
                player_vars[(p['player_id'], 'F')]
                for p in candidates
                if 'F' in player_to_positions[p['player_id']] and (p['player_id'], 'F') in player_vars
            ])
            fwd_needed = target_fwd - locked_counts['F']
            prob += fwd_candidates_sum == fwd_needed, "FWD_Exact"

            # Constraint 5: Total players = 11
            total_candidates_needed = 11 - len(locked)
            prob += pulp.lpSum([
                player_vars[(p['player_id'], pos)]
                for p in candidates
                for pos in player_to_positions[p['player_id']]
                if (p['player_id'], pos) in player_vars
            ]) == total_candidates_needed, "TotalPlayers"

            # Constraint 6: For generating alternatives - must differ from previous lineups
            for i, prev_lineup_ids in enumerate(previous_lineups):
                # At least one player from candidates that was in prev lineup must NOT be selected
                prev_candidates = [p for p in candidates if p['player_id'] in prev_lineup_ids]
                if prev_candidates:
                    prob += pulp.lpSum([
                        player_vars[(p['player_id'], pos)]
                        for p in prev_candidates
                        for pos in player_to_positions[p['player_id']]
                        if (p['player_id'], pos) in player_vars
                    ]) <= len(prev_candidates) - 1, f"DifferFromPrev_{i}"

            # Solve
            prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=30))

            # Check if solution found
            if prob.status != pulp.LpStatusOptimal:
                print(f"[DEBUG] ILP status: {pulp.LpStatus[prob.status]}")
                return None, 0

            # Extract solution - track which position each player was selected for
            lineup = []
            selected_ids = set()

            # Add locked players with their primary position
            for p in locked:
                player_copy = dict(p)
                player_copy['selected_position'] = player_to_positions[p['player_id']][0]
                player_copy['purchase_price'] = get_player_cost(p)  # Include purchase price
                lineup.append(player_copy)
                selected_ids.add(p['player_id'])

            # Add selected candidates with their ILP-selected position
            for p in candidates:
                for pos in player_to_positions[p['player_id']]:
                    if (p['player_id'], pos) in player_vars:
                        if player_vars[(p['player_id'], pos)].value() == 1:
                            player_copy = dict(p)
                            player_copy['selected_position'] = pos  # Track which position ILP chose
                            player_copy['purchase_price'] = get_player_cost(p)  # Include purchase price
                            lineup.append(player_copy)
                            selected_ids.add(p['player_id'])
                            break  # Don't double-count multi-position players

            # Use get_player_cost to respect CSV purchase prices for owned players
            total_cost = sum(get_player_cost(p) for p in lineup)
            return lineup, total_cost

        # Generate 18 alternative lineups: 9 per formation (6 optimal + 3 differential)
        alternatives = []

        # Get top performers by true_value (excluding locked players) for differential lineups
        non_locked_pool = [p for p in players_pool if p['player_id'] not in locked_player_ids]
        top_performers = sorted(non_locked_pool, key=lambda x: x.get('true_value', 0), reverse=True)[:8]
        top_performer_ids = set(p['player_id'] for p in top_performers)

        for target_formation in ["3-5-2", "3-4-3"]:
            # Phase 1: 6 Optimal lineups
            previous_lineup_ids = []

            for alt_num in range(6):
                remaining_budget = budget - locked_cost

                lineup, total_cost = optimize_lineup_ilp(
                    locked_players,
                    players_pool,
                    remaining_budget,
                    excluded_ids=set(),
                    previous_lineups=previous_lineup_ids,
                    formation=target_formation,
                    pos_weights=position_value_weights
                )

                if lineup and len(lineup) == 11:
                    total_true_value = sum(p['true_value'] for p in lineup)

                    alternatives.append({
                        'lineup': lineup,
                        'formation': target_formation,
                        'total_true_value': round(total_true_value, 2),
                        'total_cost': round(total_cost, 2),
                        'budget_remaining': round(budget - total_cost, 2),
                        'locked_count': len(locked_players),
                        'positions': count_positions(lineup),
                        'type': 'optimal'
                    })

                    this_lineup_ids = set(p['player_id'] for p in lineup if p['player_id'] not in locked_player_ids)
                    previous_lineup_ids.append(this_lineup_ids)

            # Phase 2: 3 Differential lineups (excluding top performers to surface alternatives)
            differential_previous = []

            for alt_num in range(3):
                remaining_budget = budget - locked_cost

                lineup, total_cost = optimize_lineup_ilp(
                    locked_players,
                    players_pool,
                    remaining_budget,
                    excluded_ids=top_performer_ids,
                    previous_lineups=differential_previous,
                    formation=target_formation,
                    pos_weights=position_value_weights
                )

                if lineup and len(lineup) == 11:
                    total_true_value = sum(p['true_value'] for p in lineup)

                    alternatives.append({
                        'lineup': lineup,
                        'formation': target_formation,
                        'total_true_value': round(total_true_value, 2),
                        'total_cost': round(total_cost, 2),
                        'budget_remaining': round(budget - total_cost, 2),
                        'locked_count': len(locked_players),
                        'positions': count_positions(lineup),
                        'type': 'differential'
                    })

                    this_lineup_ids = set(p['player_id'] for p in lineup if p['player_id'] not in locked_player_ids)
                    differential_previous.append(this_lineup_ids)

        return jsonify({
            'success': True,
            'alternatives': alternatives,
            'locked_players': locked_players,
            'locked_cost': round(locked_cost, 2),
            'budget': budget
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("Starting Fantrax Value Hunter Flask Backend...")
    print(f"Database: {DB_CONFIG['database']} on port {DB_CONFIG['port']}")

    # Test database connection on startup with timeout
    def test_db_connection():
        """Test database connection in a separate thread"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            print(f"Database connected: {player_count} players loaded")

            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            print("App will start anyway - database operations may fail until connection is established")
            return False

    # Run database test with timeout
    import threading
    import time

    db_test_result = {'connected': False}

    def db_test_thread():
        db_test_result['connected'] = test_db_connection()

    # Start database test in background
    test_thread = threading.Thread(target=db_test_thread)
    test_thread.daemon = True
    test_thread.start()

    # Wait max 8 seconds for database test
    test_thread.join(timeout=8)

    if test_thread.is_alive():
        print("Database connection test timed out - starting app anyway")
        print("Note: Database operations may fail until connection is established")

    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))  # Use 5001 to avoid conflict
    debug = os.getenv('FLASK_ENV') == 'development'

    # File modification error mitigation: Allow disabling auto-reloader
    disable_reloader = os.getenv('FLASK_NO_RELOAD', '').lower() in ('true', '1', 'yes')

    # DEVELOPMENT: Enable auto-reload for code changes
    # Set debug=True to auto-restart server when Python files change
    development_mode = False  # Production mode
    use_reloader = development_mode and not disable_reloader

    # Log reloader status (helps diagnose file modification conflicts)
    if development_mode:
        reloader_backend = "watchdog" if disable_reloader else "watchdog (if installed) or stat polling"
        print(f"Flask reloader: {'disabled' if disable_reloader else 'enabled'} - backend: {reloader_backend}")

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=use_reloader)

