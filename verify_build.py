#!/usr/bin/env python3
"""
Build verification script for Railway deployment
Checks if React build files exist in expected locations
"""

import os
import sys

def check_build_verification():
    """Verify that build files exist in expected locations"""

    print("=== Fantrax Value Hunter Build Verification ===")

    # Define required files and directories
    required_paths = [
        # React build files in Railway target location
        'src/static/react-build/index.html',
        'src/static/react-build/static/js',
        'src/static/react-build/static/css',
        'src/static/react-build/manifest.json',
        'src/static/react-build/favicon.ico'
    ]

    fallback_paths = [
        # Fallback React build files (for development)
        'frontend/build/index.html',
        'frontend/build/static/js',
        'frontend/build/static/css',
        'frontend/build/manifest.json',
        'frontend/build/favicon.ico'
    ]

    primary_missing = []
    fallback_available = []

    # Check primary paths
    print("\n1. Checking primary build location (src/static/react-build/):")
    for path in required_paths:
        if os.path.exists(path):
            print(f"   ✓ {path}")
        else:
            print(f"   ✗ {path}")
            primary_missing.append(path)

    # Check fallback paths
    print("\n2. Checking fallback location (frontend/build/):")
    for path in fallback_paths:
        if os.path.exists(path):
            print(f"   ✓ {path}")
            fallback_available.append(path)
        else:
            print(f"   ✗ {path}")

    # Check specific JS and CSS files
    print("\n3. Checking for specific static files:")
    js_files = []
    css_files = []

    for location in ['src/static/react-build/static', 'frontend/build/static']:
        js_dir = os.path.join(location, 'js')
        css_dir = os.path.join(location, 'css')

        if os.path.exists(js_dir):
            js_files.extend([f for f in os.listdir(js_dir) if f.endswith('.js') and not f.endswith('.map')])

        if os.path.exists(css_dir):
            css_files.extend([f for f in os.listdir(css_dir) if f.endswith('.css') and not f.endswith('.map')])

    if js_files:
        print(f"   ✓ Found JS files: {js_files}")
    else:
        print("   ✗ No JS files found")

    if css_files:
        print(f"   ✓ Found CSS files: {css_files}")
    else:
        print("   ✗ No CSS files found")

    # Summary and decision
    print("\n=== BUILD VERIFICATION RESULTS ===")

    if not primary_missing:
        print("✅ PRIMARY BUILD SUCCESSFUL: All files found in src/static/react-build/")
        return True
    elif fallback_available:
        print("⚠️  PRIMARY BUILD MISSING: Files found in fallback location frontend/build/")
        print("   Flask will serve from fallback location.")
        return True
    else:
        print("❌ BUILD FAILED: Required files not found in any location")
        print("\nMissing primary files:")
        for path in primary_missing:
            print(f"   - {path}")
        return False

if __name__ == "__main__":
    success = check_build_verification()
    if not success:
        print("\n🔧 To fix this issue:")
        print("   1. Run: cd frontend && npm install && npm run build")
        print("   2. Ensure build process copies files to src/static/react-build/")
        print("   3. Check nixpacks.toml configuration")
        sys.exit(1)
    else:
        print("\n🚀 Build verification passed! Ready for deployment.")
        sys.exit(0)