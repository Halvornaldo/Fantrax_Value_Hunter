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
        'src/static/react-build/index.html',
        'src/static/react-build/static/js',
        'src/static/react-build/static/css'
    ]

    fallback_paths = [
        'frontend/build/index.html',
        'frontend/build/static/js',
        'frontend/build/static/css'
    ]

    primary_missing = []

    # Check primary paths
    print("\n1. Checking primary build location (src/static/react-build/):")
    for path in required_paths:
        if os.path.exists(path):
            print(f"   OK {path}")
        else:
            print(f"   MISSING {path}")
            primary_missing.append(path)

    # Check fallback paths
    print("\n2. Checking fallback location (frontend/build/):")
    fallback_available = 0
    for path in fallback_paths:
        if os.path.exists(path):
            print(f"   OK {path}")
            fallback_available += 1
        else:
            print(f"   MISSING {path}")

    # Summary
    print("\n=== RESULTS ===")
    if not primary_missing:
        print("SUCCESS: All files found in primary location")
        return True
    elif fallback_available == len(fallback_paths):
        print("PARTIAL: Primary missing, fallback available")
        print("Flask will serve from fallback location.")
        return True
    else:
        print("FAILED: Required files not found")
        return False

if __name__ == "__main__":
    success = check_build_verification()
    if not success:
        print("\nTo fix: run 'npm run build' in frontend directory")
        sys.exit(1)
    else:
        print("\nBuild verification passed!")
        sys.exit(0)