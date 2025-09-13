#!/usr/bin/env python3
"""
Test corrected formula with REAL players only from CSV data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Fantrax_Wrapper'))

import csv

def test_real_players_only():
    """Test formula with actual players from CSV data"""
    print("=== REAL PLAYER FORMULA VALIDATION ===")
    print("Testing corrected formula: ValueScore = FP/G ÷ Salary")
    print("Using only REAL players from 2024-25 CSV data")
    print()
    
    # Load real FP/G data
    fpg_data = []
    data_file = '../data/fpg_data_2024.csv'
    
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                player_name = row['Player']
                fpg = float(row['FP/G'])
                salary = float(row['Salary'])
                
                # Calculate ValueScore = FP/G ÷ Salary
                value_score = fpg / salary if salary > 0 else 0
                
                fpg_data.append({
                    'name': player_name,
                    'fpg': fpg,
                    'salary': salary,
                    'value_score': value_score,
                    'total_points': float(row['FPts'])
                })
    
    print(f"[SUCCESS] Loaded {len(fpg_data)} real players from CSV")
    
    # Sort by ValueScore (higher is better)
    fpg_data.sort(key=lambda x: x['value_score'], reverse=True)
    
    print("\nTOP 10 VALUE PLAYERS (Real Data):")
    print("-" * 65)
    print(f"{'Rank':<4} {'Player':<20} {'FP/G':<6} {'Salary':<7} {'ValueScore':<10}")
    print("-" * 65)
    
    for i in range(min(10, len(fpg_data))):
        player = fpg_data[i]
        print(f"{i+1:<4} {player['name'][:19]:<20} {player['fpg']:<6.2f} ${player['salary']:<6.1f} {player['value_score']:<9.3f}")
    
    print("\nBOTTOM 5 VALUE PLAYERS:")
    print("-" * 65)
    
    for i in range(max(0, len(fpg_data)-5), len(fpg_data)):
        player = fpg_data[i]
        print(f"{i+1:<4} {player['name'][:19]:<20} {player['fpg']:<6.2f} ${player['salary']:<6.1f} {player['value_score']:<9.3f}")
    
    # Check some known players
    known_players = ['Mohamed Salah', 'Cole Palmer', 'Chris Wood', 'Bukayo Saka']
    print(f"\nKNOWN PLAYERS COMPARISON:")
    print("-" * 65)
    
    for name in known_players:
        player = next((p for p in fpg_data if name in p['name']), None)
        if player:
            rank = fpg_data.index(player) + 1
            print(f"#{rank:<3} {player['name'][:19]:<20} {player['fpg']:<6.2f} ${player['salary']:<6.1f} {player['value_score']:<9.3f}")
    
    # Analysis
    top_player = fpg_data[0]
    print(f"\n[VALIDATION] Best Value Player: {top_player['name']}")
    print(f"  FP/G: {top_player['fpg']:.2f}, Salary: ${top_player['salary']:.1f}, Value: {top_player['value_score']:.3f}")
    
    # Check if expensive players rank lower
    expensive_players = [p for p in fpg_data if p['salary'] > 20]
    if expensive_players:
        best_expensive = max(expensive_players, key=lambda x: x['value_score'])
        best_expensive_rank = fpg_data.index(best_expensive) + 1
        print(f"\n[EXPENSIVE] Best $20+ Player: {best_expensive['name']} (Rank #{best_expensive_rank})")
    
    print("\n[SUCCESS] Real player formula validation complete!")

if __name__ == "__main__":
    test_real_players_only()