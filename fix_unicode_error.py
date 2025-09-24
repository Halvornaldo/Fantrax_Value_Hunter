#!/usr/bin/env python3
"""
Fix Unicode character encoding issue in calculation engine
"""

def fix_unicode_issue():
    """Fix the Unicode character that's causing syntax error"""
    engine_path = "calculation_engine_v2.py"

    print("=== Fixing Unicode character issue ===")

    # Read current file with explicit encoding
    try:
        with open(engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(engine_path, 'r', encoding='latin-1') as f:
            content = f.read()

    # Replace problematic Unicode character
    # The character should be multiplication symbol (*) not the Unicode character
    old_formula = "Formula: 1 + ((player_xGI90 / position_avg_xGI90) - 1) � weight"
    new_formula = "Formula: 1 + ((player_xGI90 / position_avg_xGI90) - 1) * weight"

    if "� weight" in content:
        content = content.replace("� weight", "* weight")
        print("[OK] Fixed Unicode multiplication character")
    else:
        print("[INFO] Unicode character not found")

    # Write fixed file with UTF-8 encoding
    with open(engine_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] File updated with proper encoding")

if __name__ == "__main__":
    fix_unicode_issue()