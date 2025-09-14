#!/usr/bin/env python3
"""
Quick fix for undefined placeholders variable in app.py
"""

# Read the file
with open('src/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the placeholders issue
old_pattern = """            conditions.append(f"p.team IN ({placeholders})")"""
new_pattern = """            placeholders = ', '.join(['%s'] * len(teams))
            conditions.append(f"p.team IN ({placeholders})")"""

# Replace all occurrences
content = content.replace(old_pattern, new_pattern)

# Write back to file
with open('src/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed placeholders variable in app.py")