#!/usr/bin/env python3
"""
Form Tracker System
Weighted form calculation with season average switching logic
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class FormTracker:
    def __init__(self, data_dir="../data", config_file="../config/system_parameters.json"):
        self.data_dir = data_dir
        self.baseline_file = os.path.join(data_dir, "season_2024_baseline.json")
        self.form_file = os.path.join(data_dir, "player_form_tracking.json")
        self.config_file = config_file
        self.current_gameweek = 1
        
        # Load configuration parameters
        self.config = self._load_config()
        
        # Load baseline data
        self.baseline_data = self._load_baseline()
        
        # Load or initialize form tracking
        self.form_data = self._load_form_data()
        
        # Form calculation parameters (from config)
        self.form_enabled = self.config["form_calculation"]["enabled"]
        self.lookback_period = self.config["form_calculation"]["lookback_period"]
        self.lookback_options = self.config["form_calculation"]["lookback_options"]
        self.baseline_switchover_gw = self.config["form_calculation"]["baseline_switchover_gameweek"]
        self.min_games_for_form = self.config["form_calculation"]["minimum_games_for_form"]
        self.disabled_multiplier = self.config["form_calculation"]["disabled_multiplier"]
        
        # Get current weights based on lookback period
        self.recent_game_weights = self._get_current_weights()
    
    def _get_current_weights(self):
        """Get weights based on current lookback period setting"""
        period_key = f"{self.lookback_period}_games"
        if period_key in self.lookback_options:
            return self.lookback_options[period_key]["weights"]
        else:
            # Default to 3 games if invalid period
            return self.lookback_options["3_games"]["weights"]
    
    def update_lookback_period(self, new_period: int):
        """Update lookback period (3 or 5 games) - for dashboard control"""
        if new_period in [3, 5]:
            self.lookback_period = new_period
            self.recent_game_weights = self._get_current_weights()
            print(f"[INFO] Lookback period updated to {new_period} games")
            print(f"[INFO] New weights: {self.recent_game_weights}")
        else:
            print(f"[ERROR] Invalid lookback period: {new_period}. Must be 3 or 5.")
    
    def toggle_form_calculation(self, enabled: bool):
        """Enable or disable form calculation - for dashboard control"""
        self.form_enabled = enabled
        status = "enabled" if enabled else "disabled"
        multiplier = "variable" if enabled else f"{self.disabled_multiplier}"
        print(f"[INFO] Form calculation {status} (multiplier: {multiplier})")
        print(f"[INFO] True Value = ValueScore × {multiplier if not enabled else 'form_score/100'}")
    
    def _load_config(self) -> Dict:
        """Load system configuration parameters"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[WARNING] Config file not found: {self.config_file}")
            # Return default config
            return {
                "form_calculation": {
                    "enabled": False,
                    "lookback_period": 3,
                    "lookback_options": {
                        "3_games": {"weights": [0.5, 0.3, 0.2]},
                        "5_games": {"weights": [0.4, 0.25, 0.2, 0.1, 0.05]}
                    },
                    "baseline_switchover_gameweek": 10,
                    "minimum_games_for_form": 3,
                    "disabled_multiplier": 1.0
                }
            }
    
    def _load_baseline(self) -> Dict:
        """Load 2024-25 season baseline data"""
        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[WARNING] Baseline file not found: {self.baseline_file}")
            return {"players": {}}
    
    def _load_form_data(self) -> Dict:
        """Load existing form tracking data or initialize"""
        try:
            with open(self.form_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "metadata": {
                    "current_gameweek": 1,
                    "last_updated": datetime.now().isoformat(),
                    "season": "2025-26"
                },
                "players": {}
            }
    
    def _save_form_data(self):
        """Save form tracking data to file"""
        self.form_data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.form_file, 'w') as f:
            json.dump(self.form_data, f, indent=2)
        print(f"[SUCCESS] Form data saved to {self.form_file}")
    
    def update_gameweek_results(self, gameweek_results: Dict[str, float]):
        """
        Update form tracking with new gameweek results
        gameweek_results: {player_id: points_scored}
        """
        self.current_gameweek = self.form_data["metadata"]["current_gameweek"]
        print(f"[INFO] Updating results for Game Week {self.current_gameweek}")
        
        for player_id, points in gameweek_results.items():
            if player_id not in self.form_data["players"]:
                # Initialize new player
                self.form_data["players"][player_id] = {
                    "weekly_points": [],
                    "games_played": 0,
                    "current_season_average": None,
                    "form_score": None
                }
            
            # Add latest points
            player_form = self.form_data["players"][player_id]
            player_form["weekly_points"].append(points)
            player_form["games_played"] += 1
            
            # Keep only last 10 games for rolling calculation
            if len(player_form["weekly_points"]) > 10:
                player_form["weekly_points"] = player_form["weekly_points"][-10:]
            
            # Update current season average
            if player_form["games_played"] >= 1:
                player_form["current_season_average"] = sum(player_form["weekly_points"]) / len(player_form["weekly_points"])
            
            # Calculate form score if enough data
            form_score = self._calculate_form_score(player_id)
            player_form["form_score"] = form_score
        
        # Increment gameweek
        self.form_data["metadata"]["current_gameweek"] += 1
        self._save_form_data()
        print(f"[SUCCESS] Updated {len(gameweek_results)} players for GW{self.current_gameweek}")
    
    def _calculate_form_score(self, player_id: str) -> Optional[float]:
        """
        Calculate weighted form score
        Form Score = (Weighted Recent N Games) ÷ (Season Average) × 100
        
        Season Average Logic:
        - Game Weeks 1-10: Use 2024-25 baseline
        - Game Week 11+: Use current season average
        
        Lookback Period: 3 or 5 games (configurable)
        
        Returns 100.0 (neutral) if form calculation is disabled
        """
        # If form calculation is disabled, return neutral multiplier (100 = 1.0x when divided by 100)
        if not self.form_enabled:
            return 100.0
        
        player_form = self.form_data["players"].get(player_id)
        if not player_form or len(player_form["weekly_points"]) < self.min_games_for_form:
            return 100.0  # Return neutral form if insufficient data
        
        # Get weighted recent performance (last N games based on lookback period)
        available_games = len(player_form["weekly_points"])
        games_to_use = min(self.lookback_period, available_games)
        
        recent_points = player_form["weekly_points"][-games_to_use:]
        weights_to_use = self.recent_game_weights[:games_to_use]
        
        weighted_recent = sum(points * weight for points, weight in zip(recent_points, weights_to_use))
        
        # Determine season average to use
        current_gw = self.form_data["metadata"]["current_gameweek"]
        
        if current_gw <= 10:
            # Use 2024-25 baseline for first 10 games
            baseline_player = self.baseline_data["players"].get(player_id)
            if not baseline_player:
                return None  # No baseline data available
            season_average = baseline_player["season_average_2024"]
        else:
            # Use current season average from game 11 onwards
            if not player_form["current_season_average"]:
                return None
            season_average = player_form["current_season_average"]
        
        # Calculate form score (avoid division by zero)
        if season_average <= 0:
            return 100  # Neutral form if no baseline
        
        form_score = (weighted_recent / season_average) * 100
        return round(form_score, 1)
    
    def get_form_score(self, player_id: str) -> Optional[float]:
        """Get current form score for a player"""
        player_form = self.form_data["players"].get(player_id)
        if player_form:
            return player_form.get("form_score")
        return None
    
    def get_all_form_scores(self) -> Dict[str, float]:
        """Get all current form scores"""
        form_scores = {}
        for player_id, player_data in self.form_data["players"].items():
            if player_data.get("form_score") is not None:
                form_scores[player_id] = player_data["form_score"]
        return form_scores
    
    def get_player_form_details(self, player_id: str) -> Optional[Dict]:
        """Get detailed form information for a player"""
        player_form = self.form_data["players"].get(player_id)
        if not player_form:
            return None
        
        # Get baseline info
        baseline_player = self.baseline_data["players"].get(player_id, {})
        
        return {
            "games_played": player_form["games_played"],
            "recent_points": player_form["weekly_points"][-3:] if len(player_form["weekly_points"]) >= 3 else player_form["weekly_points"],
            "current_season_avg": player_form.get("current_season_average"),
            "baseline_2024": baseline_player.get("season_average_2024"),
            "form_score": player_form.get("form_score"),
            "form_status": self._get_form_status(player_form.get("form_score"))
        }
    
    def _get_form_status(self, form_score: Optional[float]) -> str:
        """Convert form score to readable status"""
        if form_score is None:
            return "UNKNOWN"
        elif form_score >= 120:
            return "EXCELLENT"
        elif form_score >= 110:
            return "GOOD"
        elif form_score >= 90:
            return "AVERAGE"
        elif form_score >= 80:
            return "POOR"
        else:
            return "TERRIBLE"
    
    def export_form_summary(self) -> Dict:
        """Export summary of all form data for candidate analyzer"""
        current_gw = self.form_data["metadata"]["current_gameweek"]
        using_baseline = current_gw <= 10
        
        summary = {
            "current_gameweek": current_gw,
            "using_2024_baseline": using_baseline,
            "players_with_form": 0,
            "form_scores": {}
        }
        
        for player_id, player_data in self.form_data["players"].items():
            if player_data.get("form_score") is not None:
                summary["players_with_form"] += 1
                summary["form_scores"][player_id] = {
                    "form_score": player_data["form_score"],
                    "games_played": player_data["games_played"],
                    "status": self._get_form_status(player_data["form_score"])
                }
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Initialize form tracker
    tracker = FormTracker()
    
    print("FORM TRACKING SYSTEM - INITIALIZED")
    print("="*50)
    print(f"Baseline data loaded: {len(tracker.baseline_data.get('players', {}))} players")
    print(f"Current game week: {tracker.form_data['metadata']['current_gameweek']}")
    
    # Example: Simulate updating results (this would come from actual game data)
    print("\n[DEMO] Simulating Game Week 1 results...")
    demo_results = {
        "06cmb": 8.5,  # Vicario
        "05tqx": 12.0,  # Raya  
        "06rf9": 6.2    # Marmoush
    }
    
    # tracker.update_gameweek_results(demo_results)
    
    # Show form summary
    summary = tracker.export_form_summary()
    print(f"\nForm Summary:")
    print(f"- Current Game Week: {summary['current_gameweek']}")
    print(f"- Using 2024 baseline: {summary['using_2024_baseline']}")
    print(f"- Players with form scores: {summary['players_with_form']}")