# ===============================
# INDIVIDUAL GAME SCORES IMPORT
# ===============================

@app.route('/api/import-game-scores', methods=['POST'])
def import_game_scores():
    """
    Import individual game scores from Fantrax CSV export
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
        import io

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