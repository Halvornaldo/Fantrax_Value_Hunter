#!/usr/bin/env python3
"""
Fix method placement in calculation_engine_v2.py
Move methods inside the FormulaEngineV2 class
"""

def fix_method_placement():
    """Fix the method placement in calculation engine"""
    engine_path = "calculation_engine_v2.py"

    print("=== Fixing method placement ===")

    # Read current file
    with open(engine_path, 'r') as f:
        content = f.read()

    # Find the misplaced methods
    misplaced_start = "# Example usage and testing\n\n    def _get_positional_average"
    misplaced_end = "return 1.0\n\n\\nif __name__"

    if misplaced_start in content and misplaced_end in content:
        # Extract the misplaced methods
        start_idx = content.find(misplaced_start)
        end_idx = content.find(misplaced_end) + len("return 1.0\n")

        # Get the methods block
        methods_block = content[start_idx:end_idx]
        # Remove the comment and fix indentation
        methods_block = methods_block.replace("# Example usage and testing\n\n    def", "    def")

        # Remove misplaced block from content
        content = content[:start_idx] + content[end_idx:]

        # Find where to insert methods (before load_system_parameters function)
        insert_point = "def load_system_parameters("
        if insert_point in content:
            insert_idx = content.find(insert_point)
            # Insert methods before the function
            content = content[:insert_idx] + methods_block + "\n\n" + content[insert_idx:]
            print("[OK] Fixed method placement - moved inside FormulaEngineV2 class")
        else:
            print("[WARNING] Could not find insertion point")
    else:
        print("[INFO] Methods already in correct position")

    # Write fixed file
    with open(engine_path, 'w') as f:
        f.write(content)
    print("[OK] File updated")

if __name__ == "__main__":
    fix_method_placement()