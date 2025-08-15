# Team Code Mapping Guide
**Handling Season-to-Season Team Changes**

## 🎯 Season Changes

### Promoted to Premier League (2025-26 Season)
- **LEE** - Leeds United (promoted from Championship)
- **BUR** - Burnley (promoted from Championship)
- **SUN** - Sunderland (promoted from Championship)

### Relegated from Premier League (were in 2024-25, not in 2025-26)
- **LEI** - Leicester City (relegated to Championship)
- **IPS** - Ipswich Town (relegated to Championship)
- **SOU** - Southampton (relegated to Championship)

---

## 📊 Team Code Standards

### Current Premier League Teams (2025-26 Season)
```python
TEAM_CODES_2025_26 = {
    "ARS": "Arsenal",
    "AVL": "Aston Villa",
    "BOU": "Bournemouth",
    "BRE": "Brentford",      # Note: Sometimes appears as "BRF" 
    "BHA": "Brighton & Hove Albion",
    "BUR": "Burnley",        # PROMOTED for 2025-26
    "CHE": "Chelsea",
    "CRY": "Crystal Palace",
    "EVE": "Everton",
    "FUL": "Fulham",
    "LEE": "Leeds United",   # PROMOTED for 2025-26
    "LIV": "Liverpool",
    "MCI": "Manchester City",
    "MUN": "Manchester United",
    "NEW": "Newcastle United",
    "NFO": "Nottingham Forest", # Note: Sometimes appears as "NOT"
    "SUN": "Sunderland",     # PROMOTED for 2025-26
    "TOT": "Tottenham Hotspur",
    "WHU": "West Ham United",
    "WOL": "Wolverhampton Wanderers"
}
```

### Teams Only in 2024-25 Data (Now Relegated)
```python
RELEGATED_TEAMS = {
    "LEI": "Leicester City",   # In 2024-25 data but relegated
    "IPS": "Ipswich Town",     # In 2024-25 data but relegated
    "SOU": "Southampton"       # In 2024-25 data but relegated
}
```

---

## 💻 Implementation Considerations

### Code Translation Map
```python
# Handle different abbreviation standards
TEAM_CODE_ALIASES = {
    "BRF": "BRE",  # Brentford alternative
    "NOT": "NFO",  # Nottingham Forest alternative
}

# Teams that changed divisions
DIVISION_CHANGES = {
    # Relegated (remove from 2025-26 predictions)
    "LEI": "relegated",
    "IPS": "relegated", 
    "SOU": "relegated",
    
    # Promoted (new to track for 2025-26)
    "LEE": "promoted",
    "BUR": "promoted",
    "SUN": "promoted"
}
```

### Handling in Database Migration
```python
def import_2024_25_baseline(self, player_data):
    """Import baseline data with season change handling"""
    team = player_data.get('team')
    
    # Handle team aliases
    if team in TEAM_CODE_ALIASES:
        team = TEAM_CODE_ALIASES[team]
    
    # Skip players from relegated teams (unless they transferred)
    if team in ["LEI", "IPS", "SOU"]:
        print(f"Note: {player_data['name']} was on {team} (now relegated)")
        # Could check if player transferred to a PL team
        return None
    
    # Flag players from newly promoted teams as "new data needed"
    if team in ["LEE", "BUR", "SUN"]:
        player_data['needs_update'] = True
        player_data['note'] = f"Team {team} promoted - verify player still there"
    
    return player_data
```

---

## 📝 Important Notes

1. **Your existing data is actually correct!** The teams in your candidate_pools.json (BUR, LEE, SUN) are the promoted teams that ARE in the Premier League for 2025-26.

2. **The issue is with the STARTER_IMPORT_GUIDE.md** - it incorrectly listed:
   - IPS, LEI, SOU as current Premier League teams (they're actually relegated)
   - Missing BUR, LEE, SUN from the list (they're actually promoted)

3. **Form baseline data** from 2024-25 season will need careful handling:
   - Players from LEI, IPS, SOU are no longer in Premier League
   - Players from LEE, BUR, SUN are new to track

---

## ✅ Action Items

1. **Update STARTER_IMPORT_GUIDE.md** with correct team list
2. **No changes needed** to candidate_pools.json - it's already correct!
3. **Migration scripts** should handle relegated team players appropriately
4. **Watch for transfers** - some players from relegated teams may have moved to PL clubs

The good news is your candidate analyzer is already pulling the correct current season data with the right teams!