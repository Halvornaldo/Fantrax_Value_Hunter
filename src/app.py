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
import sys

# Add name_matching module to path
sys.path.append(os.path.dirname(__file__))
from name_matching import UnifiedNameMatcher

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
        
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        if len(lines) < 2:
            return jsonify({'error': 'CSV must have header and data rows'}), 400
        
        # Parse header
        header = lines[0].strip().split(',')
        expected_headers = ['Team', 'Player Name', 'Position', 'Predicted Status']
        
        # Normalize headers for comparison
        header_normalized = [h.strip().lower().replace(' ', '_') for h in header]
        expected_normalized = [h.strip().lower().replace(' ', '_') for h in expected_headers]
        
        if header_normalized != expected_normalized:
            return jsonify({
                'error': f'Invalid CSV format. Expected headers: {expected_headers}, got: {header}'
            }), 400
        
        # Parse data rows
        starters = []
        non_starters = []
        unmatched_players = []
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get system parameters for multipliers
        params = load_system_parameters()
        rotation_penalty = params.get('starter_prediction', {}).get('auto_rotation_penalty', 0.65)
        
        # Initialize UnifiedNameMatcher for improved name matching
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        for line_num, line in enumerate(lines[1:], 2):
            if not line.strip():
                continue
                
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 4:
                continue
                
            team, player_name, position, status = parts[:4]
            
            # Use UnifiedNameMatcher for improved matching
            match_result = matcher.match_player(
                source_name=player_name,
                source_system='ffs',
                team=team,
                position=position
            )
            
            # Check if we have a good match (fantrax_id exists and high confidence or verified)
            if match_result['fantrax_id'] and (not match_result['needs_review'] or match_result['confidence'] >= 90.0):
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
        
        # Update starter_multiplier in database
        gameweek = 1  # Default gameweek
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
            bench_penalty = params.get('starter_prediction', {}).get('force_bench_penalty', 0.6)
            for player_id, override in manual_overrides.items():
                override_type = override.get('type')
                if override_type == 'starter':
                    multiplier = 1.0
                elif override_type == 'bench':
                    multiplier = bench_penalty
                elif override_type == 'out':
                    multiplier = 0.0
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
                'total_players': total_players,
                'matched_players': matched_players,
                'starters_identified': len(starters),
                'rotation_risk': len(non_starters),
                'unmatched_players': len(unmatched_players),
                'match_rate': round(match_rate, 1),
                'confidence_breakdown': {
                    'high_confidence_95plus': high_confidence,
                    'medium_confidence_85_94': medium_confidence,
                    'needs_review': len(unmatched_players)
                },
                'unmatched_details': unmatched_players[:10],  # First 10 for debugging
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
        gameweek = request.args.get('gameweek', 1, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build query (same logic as /api/players but without pagination)
        base_query = """
            SELECT 
                p.name, p.team, p.position,
                pm.price, pm.ppg, pm.value_score, pm.true_value,
                pm.form_multiplier, pm.fixture_multiplier, pm.starter_multiplier
            FROM players p
            JOIN player_metrics pm ON p.id = pm.player_id
            WHERE pm.gameweek = %s
        """
        
        params = [gameweek]
        conditions = []
        
        # Add filters
        if position:
            positions = position.split(',')
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
            conditions.append("p.team = %s")
            params.append(team)
            
        if search:
            conditions.append("p.name ILIKE %s")
            params.append(f"%{search}%")
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
            
        # Order by True Value descending
        final_query = base_query + " ORDER BY pm.true_value DESC"
        
        cursor.execute(final_query, params)
        players = cursor.fetchall()
        
        # Generate CSV content
        csv_lines = []
        csv_lines.append("Name,Team,Position,Price,PPG,Value Score,True Value,Form Multiplier,Fixture Multiplier,Starter Multiplier")
        
        for player in players:
            csv_lines.append(f"{player['name']},{player['team']},{player['position']},{player['price']},{player['ppg']},{player['value_score']:.3f},{player['true_value']:.3f},{player['form_multiplier']:.2f},{player['fixture_multiplier']:.2f},{player['starter_multiplier']:.2f}")
        
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
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        confirmed_mappings = data.get('confirmed_mappings', {})
        source_system = data.get('source_system', 'unknown')
        user_id = data.get('user_id', 'web_user')
        dry_run = data.get('dry_run', False)
        players = data.get('players', [])
        
        matcher = UnifiedNameMatcher(DB_CONFIG)
        
        # Save all confirmed mappings (unless dry run)
        saved_count = 0
        failed_mappings = []
        import_count = 0
        
        if not dry_run:
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
        
        if dry_run:
            return jsonify({
                'success': True,
                'import_count': import_count,
                'message': f'Would import {import_count} players with {len(confirmed_mappings)} manual mappings'
            })
        else:
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
# VALIDATION UI ROUTES
# ===============================

@app.route('/import-validation')
def import_validation_ui():
    """Serve the import validation UI"""
    return render_template('import_validation.html')

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