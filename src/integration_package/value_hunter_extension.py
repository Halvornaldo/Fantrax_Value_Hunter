#!/usr/bin/env python3
"""
Value Hunter Extension Module
Clean integration components for adding Understat stats to Value Hunter calculations
"""

import pandas as pd
from typing import Dict, List, Optional


class ValueHunterExtension:
    """Extension module for integrating Understat stats into Value Hunter"""
    
    def __init__(self, xgi_multiplier_table: Dict[str, float]):
        """
        Initialize with xGI multiplier lookup table
        
        Args:
            xgi_multiplier_table: Dict mapping fantrax_id -> xGI90 multiplier
        """
        self.xgi_multipliers = xgi_multiplier_table
    
    def get_xgi_multiplier(self, fantrax_id: str) -> float:
        """
        Get xGI multiplier for a player
        
        Args:
            fantrax_id: Fantrax player ID
        
        Returns:
            float: xGI90 multiplier (default 1.0 if not found)
        """
        return self.xgi_multipliers.get(fantrax_id, 1.0)
    
    def calculate_enhanced_true_value(self, 
                                    ppg: float, 
                                    price: float, 
                                    form: float, 
                                    fixture: float, 
                                    starter: float, 
                                    fantrax_id: str) -> float:
        """
        Calculate enhanced True Value with xGI multiplier
        
        Original formula: TrueValue = (PPG ÷ Price) × Form × Fixture × Starter
        Enhanced formula: TrueValue = (PPG ÷ Price) × Form × Fixture × Starter × xGI_multiplier
        
        Args:
            ppg: Points per game
            price: Player price
            form: Form factor
            fixture: Fixture factor  
            starter: Starter factor
            fantrax_id: Player's Fantrax ID
        
        Returns:
            float: Enhanced True Value
        """
        if price == 0:
            return 0.0
        
        # Get xGI multiplier for this player
        xgi_multiplier = self.get_xgi_multiplier(fantrax_id)
        
        # Calculate enhanced True Value
        enhanced_true_value = (ppg / price) * form * fixture * starter * xgi_multiplier
        
        return enhanced_true_value
    
    def create_player_stats_display_data(self, player_data: Dict, understat_stats: Optional[Dict] = None) -> Dict:
        """
        Create display data for player with Understat stats
        
        Args:
            player_data: Existing player data from Value Hunter
            understat_stats: Optional Understat stats (minutes, xG90, xA90, xGI90)
        
        Returns:
            Dict: Enhanced player data for display
        """
        display_data = player_data.copy()
        
        if understat_stats:
            display_data.update({
                'minutes': understat_stats.get('minutes', 0),
                'xG90': round(understat_stats.get('xG90', 0), 3),
                'xA90': round(understat_stats.get('xA90', 0), 3),
                'xGI90': round(understat_stats.get('xGI90', 0), 3)
            })
        else:
            # Default values if no Understat data
            display_data.update({
                'minutes': 0,
                'xG90': 0.0,
                'xA90': 0.0,
                'xGI90': 0.0
            })
        
        return display_data
    
    def batch_calculate_enhanced_true_values(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate enhanced True Values for a batch of players
        
        Args:
            players_df: DataFrame with player data including fantrax_id
        
        Returns:
            pd.DataFrame: DataFrame with enhanced_true_value column
        """
        enhanced_df = players_df.copy()
        
        enhanced_df['enhanced_true_value'] = enhanced_df.apply(
            lambda row: self.calculate_enhanced_true_value(
                ppg=row.get('ppg', 0),
                price=row.get('price', 1),
                form=row.get('form', 1),
                fixture=row.get('fixture', 1), 
                starter=row.get('starter', 1),
                fantrax_id=row.get('fantrax_id', '')
            ), axis=1
        )
        
        return enhanced_df
    
    def get_stats_summary(self) -> Dict:
        """
        Get summary statistics about xGI multipliers
        
        Returns:
            Dict: Summary statistics
        """
        if not self.xgi_multipliers:
            return {
                'total_players_with_xgi': 0,
                'avg_xgi_multiplier': 0.0,
                'max_xgi_multiplier': 0.0,
                'min_xgi_multiplier': 0.0
            }
        
        multipliers = list(self.xgi_multipliers.values())
        
        return {
            'total_players_with_xgi': len(multipliers),
            'avg_xgi_multiplier': sum(multipliers) / len(multipliers),
            'max_xgi_multiplier': max(multipliers),
            'min_xgi_multiplier': min(multipliers)
        }


class DatabaseUpdater:
    """Handles database schema updates for Understat integration"""
    
    @staticmethod
    def generate_schema_update_sql() -> str:
        """
        Generate SQL for adding Understat stats columns to Value Hunter
        
        Returns:
            str: SQL statements for schema update
        """
        return """
        -- Add Understat stats columns to players table
        ALTER TABLE players 
        ADD COLUMN IF NOT EXISTS minutes INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS xG90 DECIMAL(5,3) DEFAULT 0.000,
        ADD COLUMN IF NOT EXISTS xA90 DECIMAL(5,3) DEFAULT 0.000,
        ADD COLUMN IF NOT EXISTS xGI90 DECIMAL(5,3) DEFAULT 0.000,
        ADD COLUMN IF NOT EXISTS last_understat_update TIMESTAMP;
        
        -- Add index for xGI90 for performance
        CREATE INDEX IF NOT EXISTS idx_players_xgi90 ON players(xGI90);
        
        -- Add xGI multiplier to player_metrics table
        ALTER TABLE player_metrics
        ADD COLUMN IF NOT EXISTS xgi_multiplier DECIMAL(5,3) DEFAULT 1.000;
        """
    
    @staticmethod  
    def generate_data_update_sql(matched_players_df: pd.DataFrame) -> List[str]:
        """
        Generate SQL statements to update player data with Understat stats
        
        Args:
            matched_players_df: DataFrame with matched players and stats
        
        Returns:
            List[str]: List of SQL UPDATE statements
        """
        update_statements = []
        
        for idx, player in matched_players_df.iterrows():
            sql = f"""
            UPDATE players 
            SET 
                minutes = {player['minutes']},
                xG90 = {player['xG90']:.3f},
                xA90 = {player['xA90']:.3f},
                xGI90 = {player['xGI90']:.3f},
                last_understat_update = NOW()
            WHERE id = '{player['fantrax_id']}';
            """
            update_statements.append(sql.strip())
        
        return update_statements


def test_value_hunter_extension():
    """Test the Value Hunter extension module"""
    
    # Sample xGI multiplier table
    test_multipliers = {
        'player1': 1.156,  # Salah-level
        'player2': 0.800,  # Good forward
        'player3': 0.400,  # Midfielder
        'player4': 0.100   # Defender
    }
    
    extension = ValueHunterExtension(test_multipliers)
    
    # Test enhanced True Value calculation
    enhanced_tv = extension.calculate_enhanced_true_value(
        ppg=8.5,
        price=12.0,
        form=1.1,
        fixture=1.05,
        starter=1.0,
        fantrax_id='player1'
    )
    
    print(f"Enhanced True Value test: {enhanced_tv:.3f}")
    
    # Test stats summary
    summary = extension.get_stats_summary()
    print(f"Stats summary: {summary}")
    
    return True


if __name__ == "__main__":
    test_value_hunter_extension()