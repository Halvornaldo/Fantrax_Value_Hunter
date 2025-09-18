#!/usr/bin/env python3
"""
Analyze form multipliers from the test calculation to verify ranges
"""

import json
import requests

def analyze_form_multipliers():
    """Get form multipliers from API and analyze their distribution"""

    try:
        # Get calculation results from API
        response = requests.post("http://localhost:5001/api/calculate-values-v2", json={})
        data = response.json()

        if not data.get('success', False):
            print("ERROR: API call failed")
            return

        results = data.get('results', [])
        form_multipliers = []

        # Extract form multipliers
        for player in results:
            multipliers = player.get('multipliers', {})
            form = multipliers.get('form', 1.0)
            form_multipliers.append(form)

        print(f"FORM MULTIPLIER ANALYSIS")
        print(f"=" * 50)
        print(f"Total players analyzed: {len(form_multipliers)}")

        # Calculate statistics
        min_form = min(form_multipliers)
        max_form = max(form_multipliers)
        avg_form = sum(form_multipliers) / len(form_multipliers)

        print(f"Range: {min_form:.3f} to {max_form:.3f}")
        print(f"Average: {avg_form:.3f}")

        # Count players in target range (0.9-1.1)
        in_target_range = [f for f in form_multipliers if 0.9 <= f <= 1.1]
        target_percentage = (len(in_target_range) / len(form_multipliers)) * 100

        print(f"\nTarget Range (0.9-1.1):")
        print(f"Players in range: {len(in_target_range)}/{len(form_multipliers)} ({target_percentage:.1f}%)")

        # Count extreme values
        below_09 = [f for f in form_multipliers if f < 0.9]
        above_11 = [f for f in form_multipliers if f > 1.1]

        print(f"Below 0.9: {len(below_09)} players ({len(below_09)/len(form_multipliers)*100:.1f}%)")
        print(f"Above 1.1: {len(above_11)} players ({len(above_11)/len(form_multipliers)*100:.1f}%)")

        # Show extremes
        if below_09:
            print(f"Lowest values: {sorted(below_09)[:5]}")
        if above_11:
            print(f"Highest values: {sorted(above_11, reverse=True)[:5]}")

        # Success criteria
        print(f"\n{'='*50}")
        if target_percentage >= 90:
            print(f"✅ SUCCESS: {target_percentage:.1f}% of players are within 0.9-1.1 range (target: 90%+)")
        else:
            print(f"❌ NEEDS IMPROVEMENT: Only {target_percentage:.1f}% within range (target: 90%+)")

            # Suggest alpha adjustment
            if target_percentage < 80:
                print("SUGGESTION: Consider reducing alpha further (e.g., 0.55) for tighter ranges")
            elif target_percentage < 90:
                print("SUGGESTION: Consider reducing alpha slightly (e.g., 0.60) for tighter ranges")

        return {
            'total_players': len(form_multipliers),
            'target_percentage': target_percentage,
            'min_form': min_form,
            'max_form': max_form,
            'avg_form': avg_form,
            'below_target': len(below_09),
            'above_target': len(above_11)
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    analyze_form_multipliers()