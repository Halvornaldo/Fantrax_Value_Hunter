#!/usr/bin/env python3
"""
Fix Flask startup configuration for Railway deployment
"""

import re

# Read the current app.py
with open('src/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the Flask startup section
old_section = '''    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))  # Use 5001 to avoid conflict
    debug = os.getenv('FLASK_ENV') == 'development'

    # DEVELOPMENT: Enable auto-reload for code changes
    # Set debug=True to auto-restart server when Python files change
    development_mode = False  # Production mode

    app.run(debug=development_mode, host='0.0.0.0', port=port, use_reloader=development_mode)'''

new_section = '''    # Production-ready configuration
    port = int(os.getenv('PORT', 5001))
    is_production = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None

    print(f"Starting Flask server on port {port}")
    print(f"Production mode: {is_production}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'not set')}")

    # Use simple configuration that works in containers
    if is_production:
        # Production: no debug, no reloader
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    else:
        # Local development: enable debug and reloader
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)'''

# Replace the section
if old_section in content:
    updated_content = content.replace(old_section, new_section)

    # Write back to file
    with open('src/app.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print("✅ Fixed Flask startup configuration!")
    print("Changes made:")
    print("- Added Railway production detection")
    print("- Separated production and development configurations")
    print("- Added startup logging for debugging")
else:
    print("❌ Could not find the Flask startup section to replace")
    print("The file may have already been modified")