# Starter Predictions Import Guide
**Simple CSV Import System for Weekly Lineup Updates**

## 🎯 Overview

Instead of clicking through 600+ players or complex web scraping, we use a simple Google Sheets → CSV → Dashboard workflow that takes 10 minutes per gameweek.

---

## 📊 Google Sheets Template

### Option A: Team Lineups Format (Recommended)

**Premier League Team Abbreviations (2025-26 Season):**
```
ARS - Arsenal
AVL - Aston Villa  
BOU - Bournemouth
BRE - Brentford (may appear as BRF)
BHA - Brighton & Hove Albion
BUR - Burnley (PROMOTED)
CHE - Chelsea
CRY - Crystal Palace
EVE - Everton
FUL - Fulham
LEE - Leeds United (PROMOTED)
LIV - Liverpool
MCI - Manchester City
MUN - Manchester United
NEW - Newcastle United
NFO - Nottingham Forest (may appear as NOT)
SUN - Sunderland (PROMOTED)
TOT - Tottenham Hotspur
WHU - West Ham United
WOL - Wolverhampton Wanderers
```

**Note:** Leicester (LEI), Ipswich (IPS), and Southampton (SOU) were relegated to Championship

**Google Sheets Template:**
```
Team | Predicted Starting XI
-----|----------------------
ARS  | Raya, White, Saliba, Gabriel, Timber, Rice, Partey, Odegaard, Saka, Havertz, Martinelli
AVL  | Martinez, Cash, Konsa, Torres, Digne, McGinn, Onana, Tielemans, Bailey, Watkins, Philogene
BOU  | Neto, Smith, Zabarnyi, Senesi, Kerkez, Christie, Cook, Semenyo, Kluivert, Evanilson, Ouattara
BRE  | Flekken, Roerslev, Collins, Pinnock, Henry, Janelt, Norgaard, Jensen, Mbeumo, Schade, Wissa
BHA  | [Add 11 players]
BUR  | [Add 11 players - Promoted team]
CHE  | [Add 11 players]
CRY  | [Add 11 players]
EVE  | [Add 11 players]
FUL  | [Add 11 players]
LEE  | [Add 11 players - Promoted team]
LIV  | [Add 11 players]
MCI  | [Add 11 players]
MUN  | [Add 11 players]
NEW  | [Add 11 players]
NFO  | [Add 11 players]
SUN  | [Add 11 players - Promoted team]
TOT  | [Add 11 players]
WHU  | [Add 11 players]
WOL  | [Add 11 players]
```
- 20 rows (one per team) 
- 11 players per team = 220 starters identified
- Everyone else automatically marked as rotation risk
- Use EXACT abbreviations above for team codes

### Option B: Player Status Format (For Your Candidate Pool Only)
```
Player Name | Team | Status        | Confidence
------------|------|---------------|------------
Raya        | ARS  | Starter       | High
Vicario     | TOT  | Starter       | High  
Van de Ven  | TOT  | Rotation Risk | Medium
Konsa       | AVL  | Starter       | High
```
- Only ~70 rows (your top candidates)
- More precise control over individual players

---

## 🔄 Weekly Workflow

### Step 1: Gather Lineup Data (5 minutes)
**Source: Fantasy Football Scout**
1. Visit FFS Team News section
2. Copy predicted lineups for each team
3. Paste into your Google Sheet

**Alternative Sources:**
- RotoWire lineup predictions
- Official team Twitter accounts
- Press conference reports

### Step 2: Convert Format (1 minute)
**Option A: Direct FFS Export (RECOMMENDED)**
```bash
cd src/
python convert_ffs_csv.py "C:/Users/halvo/Downloads/fantasyfootballscout.csv" "gameweek_X_lineups.csv"
```

**Option B: Manual Google Sheets**
1. In Google Sheets: File → Download → CSV
2. Save as `gameweek_X_lineups.csv`

### Step 3: Import to Dashboard (1 minute)
1. Open dashboard: `http://localhost:5000`
2. Click "Import Lineups CSV" button
3. Select your CSV file
4. System automatically:
   - Matches player names to IDs
   - Keeps 220 starters at 1.0x (no change)
   - Applies rotation penalty to 413 non-starters (0.65x default)

### Step 4: Review & Adjust (3 minutes)
1. Check import summary
2. Manually adjust any mismatches
3. Click "Apply Changes" to recalculate True Values

---

## 🔄 FFS CSV Converter (src/convert_ffs_csv.py)

The converter automatically handles:
- **Team name mapping**: "Arsenal" → "ARS", "Brighton and Hove Albion" → "BHA"
- **Column restructuring**: 12 columns → 2 columns (Team, Predicted Starting XI)
- **Player formatting**: Separate columns → comma-separated string

**Usage:**
```bash
python convert_ffs_csv.py <input_csv> <output_csv>
```

**Example:**
```bash
python convert_ffs_csv.py "C:/Users/halvo/Downloads/fantasyfootballscout.csv" "gameweek_1_lineups.csv"
```

**Output format:**
```csv
Team,Predicted Starting XI
ARS,"Raya Martin, White, Gabriel, Saliba, Lewis-Skelly, Odegaard, Rice, Saka, Martinelli"
AVL,"Bizot, Cash, Konsa Ngoyo, Torres, Maatsen, Kamara, Tielemans, McGinn, Watkins"
```

---

## 💻 Backend Implementation

### CSV Parser (src/lineup_importer.py)
```python
import csv
from typing import Dict, List

class LineupImporter:
    def __init__(self, db_manager):
        self.db = db_manager
        self.player_name_map = self._build_name_map()
    
    def import_team_lineups(self, csv_file) -> Dict:
        """Import team lineup format CSV"""
        lineups = {}
        starters = set()
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = row['Team']
                players = row['Predicted Starting XI'].split(', ')
                lineups[team] = players
                
                # Match names to IDs
                for player_name in players:
                    player_id = self._match_player_name(player_name, team)
                    if player_id:
                        starters.add(player_id)
        
        # Update multipliers
        return self._apply_starter_multipliers(starters)
    
    def _match_player_name(self, name: str, team: str) -> str:
        """Fuzzy match player name to ID"""
        # Try exact match first
        if name in self.player_name_map:
            return self.player_name_map[name]
        
        # Try last name only
        last_name = name.split()[-1]
        for full_name, player_id in self.player_name_map.items():
            if last_name in full_name and team == self.get_player_team(player_id):
                return player_id
        
        return None
    
    def _apply_starter_multipliers(self, starter_ids: set) -> Dict:
        """Apply penalty-based multipliers"""
        updates = {}
        auto_rotation_penalty = self.config['starter_prediction']['auto_rotation_penalty']
        
        # Starters stay at 1.0x (no change)
        for player_id in starter_ids:
            updates[player_id] = {
                'starter_status': 'predicted_starter',
                'starter_multiplier': 1.0
            }
        
        # Non-starters get rotation penalty
        all_players = self.db.get_all_player_ids()
        for player_id in all_players:
            if player_id not in starter_ids:
                updates[player_id] = {
                    'starter_status': 'rotation_risk',
                    'starter_multiplier': auto_rotation_penalty  # 0.65 default
                }
        
        return updates
```

### Flask Route (src/app.py)
```python
@app.route('/api/import-lineups', methods=['POST'])
def import_lineups():
    """Import starter predictions from CSV"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename.endswith('.csv'):
        # Save temporarily
        temp_path = f'/tmp/{file.filename}'
        file.save(temp_path)
        
        # Import lineups
        importer = LineupImporter(db)
        results = importer.import_team_lineups(temp_path)
        
        # Update database
        for player_id, updates in results.items():
            db.update_starter_prediction(player_id, updates)
        
        # Recalculate True Values
        analyzer.fetch_fantrax_data()
        candidate_pools = analyzer.generate_candidate_pools()
        
        return jsonify({
            'success': True,
            'starters_identified': len([r for r in results.values() if r['starter_multiplier'] == 1.0]),
            'rotation_risks': len([r for r in results.values() if r['starter_multiplier'] < 1.0])
        })
```

---

## 🔍 Name Matching Logic

### Handling Common Issues

**Problem**: "Gabriel" vs "Gabriel Magalhães"
```python
# Solution: Match by last name + team
if "Gabriel" in name and team == "ARS":
    return arsenal_gabriel_id
```

**Problem**: "Bruno F." vs "Bruno Fernandes"
```python
# Solution: Partial match with team validation
if "Bruno" in name and "Fernandes" in full_name and team == "MUN":
    return bruno_fernandes_id
```

**Problem**: Nicknames like "Trent" for "Alexander-Arnold"
```python
# Solution: Maintain nickname dictionary
nicknames = {
    "Trent": "Alexander-Arnold",
    "KDB": "De Bruyne",
    "Bruno": "Fernandes"
}
```

---

## 📈 Benefits of This Approach

1. **Fast**: 10 minutes vs hours of web scraping
2. **Reliable**: No broken scrapers to debug
3. **Flexible**: Easy manual adjustments for late team news
4. **Transparent**: See exactly what's being imported
5. **Batch Processing**: Update all 220 starters at once

---

## 🚨 Important Notes

- **Manual Override**: You can always adjust individual players after import
- **Late Team News**: Check Twitter 1 hour before deadline for changes
- **Injury Updates**: FPL Scout usually has latest injury news
- **European Games**: Check if key players might be rested after midweek games

---

This system gives you the speed of automation with the control of manual entry!