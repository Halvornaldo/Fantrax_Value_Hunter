# Value Calculation Analysis & Improvements
**Date**: August 14, 2025  
**Status**: ⚠️ OUTDATED - See PRD.md and CLAUDE.md for current approved formulas
**Issue**: Current gems finder using flawed value metric

**New Formula (Approved)**: ValueScore = Price ÷ PPG, True Value = ValueScore × weekly factors

---

## 🚨 **Current System Flaw**

### **What We're Currently Calculating:**
```python
value_ratio = projected_points / salary
```

**Problems:**
- Uses **total season points** without games played adjustment
- No minutes played consideration  
- Treats 10 points in 1 game same as 10 points in 10 games
- Injured/suspended players still show season totals

---

## 📊 **Better Value Metrics**

### **Option 1: Points Per Game** (Recommended for MVP fix)
```python
points_per_game = total_points / games_played
value_ratio = points_per_game / salary
```

**Pros**: Simple, accounts for availability  
**Cons**: Doesn't account for minutes (sub vs starter)

### **Option 2: Points Per 90 Minutes** (Most Accurate)
```python
points_per_90 = (total_points / total_minutes) * 90
value_ratio = points_per_90 / salary
```

**Pros**: True efficiency metric, fair for subs  
**Cons**: Need minutes data from API

### **Option 3: Weighted Recent Form** (Future Enhancement)
```python
recent_ppg = points_last_5_games / games_last_5
season_ppg = total_points / total_games
weighted_ppg = (recent_ppg * 0.7) + (season_ppg * 0.3)
value_ratio = weighted_ppg / salary
```

**Pros**: Captures current form  
**Cons**: Complex, need game-by-game data

---

## 🔍 **Data Investigation Needed**

### **Check What's Available in Fantrax API:**

From the current player data structure:
```python
player = {
  'scorer': {...},
  'cells': [
    rank,           # cells[0]
    opponent,       # cells[1] 
    salary,         # cells[2] ✅ Have this
    fantasy_points, # cells[3] ✅ Have this - but total or per game?
    percent_drafted,# cells[4]
    adp,           # cells[5]
    percent_owned  # cells[6]
  ]
}
```

**Questions to Research:**
1. Is `cells[3]` total season points or average per game?
2. Are there additional cells with games played?
3. Can we access minutes played data?
4. Is there recent form data (last 5 games)?

---

## 🧪 **Investigation Script Needed**

```python
# Add to complete_lineup.py for debugging
def investigate_player_data(self, players_sample=5):
    """Debug what data is actually available"""
    print("=== PLAYER DATA INVESTIGATION ===")
    
    for i, player in enumerate(self.all_players[:players_sample]):
        print(f"\nPlayer {i+1}: {player['name']} ({player['team']})")
        print(f"Salary: ${player['salary']}")
        print(f"Points: {player['projected_points']}")
        
        # Check if there are more cells beyond index 6
        cells = player.get('raw_cells', [])  # Store original cells
        print(f"Total cells available: {len(cells)}")
        
        for idx, cell in enumerate(cells):
            content = cell.get('content', 'N/A')
            print(f"  Cell[{idx}]: {content}")
        
        print(f"Current value ratio: {player['value_ratio']:.3f}")
```

---

## ⚡ **Quick Fix for Tonight**

### **Assumption-Based Improvement:**
If `projected_points` is season total, estimate games played:

```python
# Rough games played estimation
def estimate_games_played(self, player):
    """Estimate games played based on ownership and points"""
    
    # High ownership + low points = probably injured/poor
    # Low ownership + decent points = might be form/rotation
    
    ownership = player['ownership_pct']
    points = player['projected_points']
    
    if ownership > 80 and points < 50:  # Popular but low scoring
        estimated_games = points / 2  # Assume 2 pts/game (poor)
    elif ownership < 20 and points > 30:  # Unpopular but decent
        estimated_games = points / 6  # Assume 6 pts/game (good when playing)
    else:
        estimated_games = points / 4  # Assume 4 pts/game (average)
    
    return max(1, min(estimated_games, 38))  # Cap at 1-38 games

def calculate_improved_value(self, player):
    """Better value calculation"""
    est_games = self.estimate_games_played(player)
    points_per_game = player['projected_points'] / est_games
    return points_per_game / player['salary']
```

---

## 🎯 **Recommended Action Plan**

### **Phase 1: Tonight (Quick Fix)**
1. **Investigate available data** - Add debug script to see all cell contents
2. **Implement PPG estimation** - Use ownership/points correlation  
3. **Re-rank gems** - See if Richarlison still looks good
4. **Manual validation** - Use GEMS_VALIDATION.md checklist

### **Phase 2: Next Week (Proper Fix)**  
1. **Research API thoroughly** - Find games played / minutes data
2. **Implement points per 90** - Most accurate efficiency metric
3. **Add form weighting** - Recent games vs season average
4. **Validate against manual research** - Check if algorithm matches reality

---

## 🚨 **Red Flags from Current Rankings**

Given the flawed calculation, be extra suspicious of:

**Players with decent points but low ownership might be:**
- Injured for months (season total looks OK, but 0 recent games)
- Transferred/sold mid-season (good early season, terrible later)  
- Lost starting position (good when playing, rarely plays now)
- Playing in wrong position (defender scoring as midfielder)

**Manual check priority:**
1. **Richarlison**: Why only 32% owned if good value?
2. **Jose Sa**: Why only 37% owned for $5 keeper?  
3. **Any defender under $6**: Probably injury/form issues

---

## 🔧 **Debug Tonight's Lineup**

Before submitting Game Week 1 team:

```python
# Add this validation to complete_lineup.py
def validate_gems_before_submit(self, lineup):
    """Final sanity check on low-owned players"""
    
    print("\n=== GEMS VALIDATION ===")
    low_owned = [p for p in lineup if p['ownership_pct'] < 50]
    
    for player in low_owned:
        print(f"\n{player['name']} ({player['team']}) - {player['ownership_pct']}% owned")
        print(f"  Salary: ${player['salary']}")  
        print(f"  Points: {player['projected_points']}")
        print(f"  Value: {player['value_ratio']:.3f}")
        print(f"  🚨 MANUAL CHECK REQUIRED: Why so low ownership?")
```

---

**Bottom Line**: The current value calculation is fundamentally flawed. Manual validation tonight is critical, then fix the algorithm properly for Game Week 2.