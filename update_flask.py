#!/usr/bin/env python3
"""
Update Flask app.py to serve React frontend
"""

import re
import os

# Read the current app.py file
with open('src/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the Flask imports
content = re.sub(
    r'from flask import Flask, request, jsonify, render_template',
    'from flask import Flask, request, jsonify, render_template, send_from_directory, send_file',
    content
)

# 2. Add React serving routes before the if __name__ == '__main__': block
react_routes = '''
# ============================================================================
# REACT FRONTEND ROUTES - Added for Railway deployment
# ============================================================================

@app.route('/static/<path:filename>')
def serve_react_static(filename):
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

'''

# Insert the React routes before the if __name__ == '__main__': block
if_name_pattern = r"(if __name__ == '__main__':)"
if re.search(if_name_pattern, content):
    content = re.sub(if_name_pattern, react_routes + r"\n\1", content)

# 3. Update the main block to include frontend detection
main_block_old = """if __name__ == '__main__':
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

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)"""

main_block_new = """if __name__ == '__main__':
    print("Starting Fantrax Value Hunter Flask Backend with React Frontend...")
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

    # Check if React build exists
    react_build_path = os.path.join(os.path.dirname(__file__), 'static', 'react-build', 'index.html')
    if os.path.exists(react_build_path):
        print("SUCCESS: React frontend build found - full stack mode enabled")
    else:
        print("WARNING: React frontend not built - API only mode")
        print("   Run ./build.sh to enable full frontend")

    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'

    # For Railway: disable development mode in production
    is_production = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None
    development_mode = debug and not is_production

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)"""

content = content.replace(main_block_old, main_block_new)

# Write the updated content to a new file
with open('src/app_with_frontend.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Created src/app_with_frontend.py with React frontend support")
print("NOTE: Review the changes and then rename it to replace src/app.py")