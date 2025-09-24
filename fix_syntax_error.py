#!/usr/bin/env python3
"""
Fix syntax error with literal \n before if __name__
"""

def fix_syntax_error():
    """Fix the syntax error in calculation engine"""
    engine_path = "calculation_engine_v2.py"

    print("=== Fixing syntax error ===")

    # Read current file
    with open(engine_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the literal \n with proper newline
    if "\\nif __name__" in content:
        content = content.replace("\\nif __name__", "\nif __name__")
        print("[OK] Fixed literal \\n before if __name__")
    else:
        print("[INFO] Syntax error not found")

    # Write fixed file
    with open(engine_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] File updated")

if __name__ == "__main__":
    fix_syntax_error()