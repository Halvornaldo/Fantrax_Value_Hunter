#!/usr/bin/env python3
"""
Apply positional xGI changes - simplified version
"""

import json
import shutil
import os
from datetime import datetime

def update_system_parameters():
    """Update system_parameters.json with new positional xGI config"""
    config_path = "config/system_parameters.json"

    print("=== Updating system_parameters.json ===")

    # Load current config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Add new positional_xgi configuration
    positional_xgi_config = {
        "enabled": True,
        "xgi_weight": 0.5,
        "mf_position_weight": 0.7,
        "position_averages": {
            "G": 0.022,
            "D": 0.099,
            "M": 0.231,
            "F": 0.425
        },
        "min_sample_size": 10,
        "fallback_values": {
            "G": 0.05,
            "D": 0.20,
            "M": 0.40,
            "F": 0.55
        },
        "description": "Live positional xGI multiplier: 1 + ((player_xGI90 / position_avg) - 1) × weight"
    }

    # Insert positional_xgi before normalized_xgi
    formula_config = config["formula_optimization_v2"]

    # Add positional_xgi config
    formula_config["positional_xgi"] = positional_xgi_config

    # Disable normalized_xgi (old approach)
    if "normalized_xgi" in formula_config:
        formula_config["normalized_xgi"]["enabled"] = False
        formula_config["normalized_xgi"]["description"] = "Legacy individual baseline approach - replaced by positional_xgi"

    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print("[OK] Successfully updated system_parameters.json")

def update_calculation_engine():
    """Update calculation_engine_v2.py with new positional methods"""
    engine_path = "calculation_engine_v2.py"

    print("\\n=== Updating calculation_engine_v2.py ===")

    # Read current file
    with open(engine_path, 'r') as f:
        content = f.read()

    # Replace the main _calculate_xgi_multiplier method
    old_method = '''    def _calculate_xgi_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        Calculate xGI multiplier using Sprint 2 normalized ratio calculation
        """
        # Check if xGI integration is enabled (use main xgi_integration config)
        xgi_config = self.params.get('xgi_integration', {})
        if not xgi_config.get('enabled', False):
            return 1.0

        return self._calculate_normalized_xgi_multiplier(player_data)'''

    new_method = '''    def _calculate_xgi_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        Calculate xGI multiplier using positional average comparison
        Formula: 1 + ((player_xGI90 / position_avg_xGI90) - 1) × weight
        """
        # Check if positional xGI is enabled in formula toggles
        formula_toggles = self.params.get('formula_optimization_v2', {}).get('formula_toggles', {})
        if not formula_toggles.get('xgi_enabled', True):
            return 1.0

        return self._calculate_positional_xgi_multiplier(player_data)'''

    # Apply replacements
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("[OK] Updated main _calculate_xgi_multiplier method")
    else:
        print("[WARNING] Could not find exact match for _calculate_xgi_multiplier method")

    # Add new methods at the end before test section
    new_methods = '''
    def _get_positional_average(self, position: str) -> float:
        """Get the appropriate positional average for a player"""
        pos_config = self.params.get('formula_optimization_v2', {}).get('positional_xgi', {})
        position_averages = pos_config.get('position_averages', {})
        fallback_values = pos_config.get('fallback_values', {})
        mf_weight = pos_config.get('mf_position_weight', 0.7)

        # Handle multi-position players
        if ',' in position or '/' in position:
            # Split position string
            positions = position.replace('/', ',').split(',')
            primary = positions[0].strip()
            secondary = positions[1].strip() if len(positions) > 1 else None

            # D/M or D,M -> Use D average (defensive players)
            if primary == 'D' and secondary == 'M':
                return position_averages.get('D', fallback_values.get('D', 0.20))

            # M/F or M,F -> Weighted average (attacking mids)
            elif primary == 'M' and secondary == 'F':
                m_avg = position_averages.get('M', fallback_values.get('M', 0.40))
                f_avg = position_averages.get('F', fallback_values.get('F', 0.55))
                return (1 - mf_weight) * m_avg + mf_weight * f_avg

            # Other combinations -> Use primary position
            else:
                return position_averages.get(primary, fallback_values.get(primary, 0.40))

        # Single position
        return position_averages.get(position, fallback_values.get(position, 0.40))

    def _calculate_positional_xgi_multiplier(self, player_data: Dict[str, Any]) -> float:
        """
        Calculate xGI multiplier using positional averages
        Formula: 1 + ((player_xGI90 / position_avg_xGI90) - 1) × weight
        """
        try:
            pos_config = self.params.get('formula_optimization_v2', {}).get('positional_xgi', {})

            # Get player data
            current_xgi = float(player_data.get('xgi90', 0.0) or 0.0)
            position = player_data.get('position', 'M')

            # Goalkeepers always get 1.0 (xGI disabled)
            if position.startswith('G'):
                return 1.0

            # Get positional average
            position_avg = self._get_positional_average(position)

            # Calculate multiplier
            if position_avg > 0.01:  # Avoid division by very small numbers
                xgi_weight = pos_config.get('xgi_weight', 0.5)
                ratio = current_xgi / position_avg
                multiplier = 1.0 + (ratio - 1.0) * xgi_weight

                # Apply bounds (0.5x to 2.5x)
                return max(0.5, min(2.5, multiplier))
            else:
                return 1.0

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculating positional xGI multiplier: {e}")
            return 1.0

'''

    # Insert new methods before the test section
    insert_point = 'if __name__ == "__main__":'
    if insert_point in content:
        content = content.replace(insert_point, new_methods + '\\n' + insert_point)
        print("[OK] Added new positional xGI methods")
    else:
        # Fallback: add at the end of the file
        content += new_methods
        print("[OK] Added new positional xGI methods at end of file")

    # Write updated file
    with open(engine_path, 'w') as f:
        f.write(content)
    print("[OK] Successfully updated calculation_engine_v2.py")

def main():
    """Apply all xGI implementation changes"""
    print("=== Applying Positional xGI Implementation ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Update configuration
        update_system_parameters()

        # Update calculation engine
        update_calculation_engine()

        print("\\n=== SUCCESS: All changes applied! ===")
        print("Changes made:")
        print("- Added positional_xgi config to system_parameters.json")
        print("- Disabled old normalized_xgi approach")
        print("- Updated calculation engine with new positional methods")
        print()
        print("Next steps:")
        print("1. Restart Flask backend to load new config")
        print("2. Test the new xGI multiplier in dashboard")

    except Exception as e:
        print(f"\\nERROR: {e}")
        raise

if __name__ == "__main__":
    main()