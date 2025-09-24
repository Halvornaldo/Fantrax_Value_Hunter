#!/usr/bin/env python3
"""
Update _calculate_xgi_multiplier to call new positional method
"""

def update_method_call():
    """Update the method call to use positional xGI"""
    engine_path = "calculation_engine_v2.py"

    print("=== Updating xGI method call ===")

    # Read current file
    with open(engine_path, 'r') as f:
        content = f.read()

    # Replace the method call
    old_call = "return self._calculate_normalized_xgi_multiplier(player_data)"
    new_call = "return self._calculate_positional_xgi_multiplier(player_data)"

    if old_call in content:
        content = content.replace(old_call, new_call)
        print("[OK] Updated method call to use positional xGI")
    else:
        print("[INFO] Method call already updated or not found")

    # Write updated file
    with open(engine_path, 'w') as f:
        f.write(content)
    print("[OK] File updated")

if __name__ == "__main__":
    update_method_call()