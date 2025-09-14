#!/usr/bin/env python3
"""
Fix production mode in Flask app.py
"""

import re

# Read the current app.py
with open('src/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the production mode issue
old_section = '''    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))  # Use 5001 to avoid conflict
    debug = os.getenv('FLASK_ENV') == 'development'

    # DEVELOPMENT: Enable auto-reload for code changes
    # Set debug=True to auto-restart server when Python files change
    development_mode = True  # Change to False for production

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)'''

new_section = '''    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'

    # For Railway: disable development mode in production
    is_production = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None
    development_mode = debug and not is_production

    print(f"Starting Flask server on port {port}")
    print(f"Debug mode: {development_mode}")
    print(f"Production mode: {is_production}")

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)'''

# Replace the section
updated_content = content.replace(old_section, new_section)

# Write back to file
with open('src/app.py', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("✅ Fixed Flask production mode configuration!")
print("Changes made:")
print("- Added Railway production detection")
print("- Disabled debug mode and reloader in production")
print("- Added startup logging for debugging")