#!/usr/bin/env python3
"""
Test script for new positional xGI multiplier implementation
"""

def get_positional_average(position, config):
    """Get the appropriate positional average for a player"""
    pos_config = config.get('positional_xgi', {})
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

def calculate_positional_xgi_multiplier(player_data, config):
    """
    Calculate xGI multiplier using positional averages
    Formula: 1 + ((player_xGI90 / position_avg_xGI90) - 1) × weight
    """
    try:
        pos_config = config.get('positional_xgi', {})

        # Get player data
        current_xgi = float(player_data.get('xgi90', 0.0) or 0.0)
        position = player_data.get('position', 'M')

        # Goalkeepers always get 1.0 (xGI disabled)
        if position.startswith('G'):
            return 1.0

        # Get positional average
        position_avg = get_positional_average(position, config)

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
        print(f"Error calculating positional xGI multiplier: {e}")
        return 1.0

# Test configuration
test_config = {
    'positional_xgi': {
        'enabled': True,
        'xgi_weight': 0.5,
        'mf_position_weight': 0.7,
        'position_averages': {
            'G': 0.022,
            'D': 0.099,
            'M': 0.231,
            'F': 0.425
        },
        'fallback_values': {
            'G': 0.05,
            'D': 0.20,
            'M': 0.40,
            'F': 0.55
        }
    }
}

# Test cases
test_players = [
    {'name': 'Goalkeeper', 'position': 'G', 'xgi90': 0.05},
    {'name': 'Defender', 'position': 'D', 'xgi90': 0.150},  # Above average
    {'name': 'Midfielder', 'position': 'M', 'xgi90': 0.350},  # Above average
    {'name': 'Forward', 'position': 'F', 'xgi90': 0.600},  # Above average
    {'name': 'D/M Player', 'position': 'D,M', 'xgi90': 0.120},  # Should use D average
    {'name': 'M/F Player', 'position': 'M,F', 'xgi90': 0.400},  # Should use weighted average
    {'name': 'Low xGI Player', 'position': 'F', 'xgi90': 0.200},  # Below average
]

if __name__ == "__main__":
    print("=== Positional xGI Multiplier Test ===")
    print(f"Position Averages: {test_config['positional_xgi']['position_averages']}")
    print(f"xGI Weight: {test_config['positional_xgi']['xgi_weight']}")
    print(f"M/F Weight: {test_config['positional_xgi']['mf_position_weight']} (70% F)")
    print()

    for player in test_players:
        position_avg = get_positional_average(player['position'], test_config)
        multiplier = calculate_positional_xgi_multiplier(player, test_config)

        print(f"{player['name']:<12} | {player['position']:<4} | xGI90: {player['xgi90']:.3f} | Pos Avg: {position_avg:.3f} | Multiplier: {multiplier:.3f}")