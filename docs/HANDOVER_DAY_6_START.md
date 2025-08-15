# 🚀 Day 6 Development Handover - CSV Import & Export Implementation
**Fantrax Value Hunter - Next Phase Development Guide**

---

## 📋 **Current Status (Day 3 Complete)**

### ✅ **What's Already Working**
1. **Database Foundation**: PostgreSQL with 633 players, full schema deployed
2. **Flask Backend**: Complete API with 5 endpoints operational (health, players, config, update-parameters, dashboard)
3. **Complete Dashboard UI**: Two-panel layout with all parameter controls implemented
4. **Enhanced Parameter Controls**: All missing features from screenshot comparison added:
   - Baseline switchover gameweek selector
   - 3-tier fixture difficulty mode toggle
   - Form strength slider
   - Manual override system (Force Starter/Bench/Out radio buttons)
5. **Real-time Updates**: Parameter changes trigger True Value recalculation across all 633 players in ~0.44 seconds

### 🎯 **Current Functionality**
- **Parameter Tuning**: All multipliers adjustable via dashboard UI
- **Player Display**: 633 players with filtering, sorting, pagination
- **True Value Engine**: Real-time recalculation with form/fixture/starter multipliers
- **Database Persistence**: All parameter changes saved to system_parameters.json

---

## 🎯 **Day 6 Objective: CSV Import & Export**

### **Core Goal**
Implement CSV-based starter prediction import and filtered player data export functionality to complete the weekly workflow integration.

### **Key Features to Implement**
1. **CSV Parser for Starter Predictions**
2. **Player Name Matching System**
3. **Export Functionality for Filtered Results**
4. **Validation and Error Handling**

---

## 📝 **Day 6 Implementation Tasks**

### **Priority 1: CSV Import System**

#### **Task 1.1: Build CSV Parser**
```python
# Target: src/starter_prediction_import.py
def parse_starter_csv(file_content):
    """
    Parse CSV with predicted starting lineups
    Expected format: Team, Player Name, Position, Predicted Status
    """
    # Handle multiple CSV formats:
    # - Fantasy Football Scout export
    # - Manual team sheets
    # - Custom format with team/player mapping
```

#### **Task 1.2: Player Name Matching**
```python
# Target: src/player_matcher.py  
def match_player_to_database(player_name, team_name=None):
    """
    Match CSV player names to database player IDs
    Handle variations: "Mohamed Salah" vs "M. Salah" vs "Salah"
    """
    # Use fuzzy matching with fuzzywuzzy
    # Consider team context for disambiguation
    # Return confidence scores for manual review
```

#### **Task 1.3: Update Flask Endpoint**
```python
# Target: src/app.py - Enhance existing /api/import-lineups
@app.route('/api/import-lineups', methods=['POST'])
def import_lineups():
    """
    Process uploaded CSV and update starter predictions
    Return: Match results, unmatched players, confidence scores
    """
```

### **Priority 2: Export Functionality**

#### **Task 2.1: Filtered Export**
```python
# Target: src/export_manager.py
def export_filtered_players(filters, format='csv'):
    """
    Export current filtered player view with all relevant columns
    Include: Name, Team, Position, Price, PPG, True Value, Multipliers
    """
```

#### **Task 2.2: Frontend Integration**
```javascript
// Target: static/js/dashboard.js - Enhance existing exportToCSV()
async function exportToCSV() {
    // Send current filter state to backend
    // Download file with timestamp
    // Include all visible columns and multipliers
}
```

### **Priority 3: Validation & Testing**

#### **Task 3.1: CSV Validation**
- Validate CSV format and required columns
- Handle missing data gracefully
- Provide clear error messages for malformed data

#### **Task 3.2: End-to-End Testing**
- Test CSV import with real Fantasy Football Scout data
- Verify starter multipliers update correctly
- Validate export includes all filtered data

---

## 🗂️ **File Structure Updates Needed**

```
Fantrax_Value_Hunter/
├── src/
│   ├── app.py                    # ✅ EXISTS - Enhance /api/import-lineups
│   ├── starter_prediction_import.py  # 🆕 CREATE - CSV parsing logic
│   ├── player_matcher.py        # 🆕 CREATE - Name matching system
│   ├── export_manager.py        # 🆕 CREATE - Export functionality
│   └── validation.py            # 🆕 CREATE - CSV validation
├── static/js/
│   └── dashboard.js             # ✅ EXISTS - Enhance export functions
├── uploads/                     # 🆕 CREATE - Temporary CSV storage
└── exports/                     # 🆕 CREATE - Generated export files
```

---

## 📊 **Technical Specifications**

### **CSV Import Format**
```csv
Team,Player Name,Position,Predicted Status
ARS,Bukayo Saka,M,Starter
ARS,Gabriel Jesus,F,Rotation Risk
LIV,Mohamed Salah,M,Starter
```

### **Export Format**
```csv
Name,Team,Position,Price,PPG,True Value,Form Multiplier,Fixture Multiplier,Starter Multiplier
Bukayo Saka,ARS,M,12.5,8.2,0.656,1.05,1.15,1.0
Gabriel Jesus,ARS,F,9.8,6.1,0.622,0.95,1.15,0.65
```

### **API Endpoints to Enhance**

#### **POST /api/import-lineups**
```json
{
  "success": true,
  "matched_players": 287,
  "unmatched_players": 12,
  "confidence_warnings": [
    {"name": "J. Rodriguez", "matches": ["James Rodriguez", "Jay Rodriguez"], "team": "EVE"}
  ],
  "updated_starters": 275
}
```

#### **GET /api/export**
```
?format=csv&filters={"positions":["M","F"],"price_min":8.0}&columns=["name","team","true_value"]
```

---

## 🔧 **Required Dependencies**

### **Python Packages** (add to requirements.txt)
```txt
fuzzywuzzy==0.18.0      # Player name matching
python-levenshtein==0.12.2  # Faster fuzzy matching
pandas==1.5.3           # CSV processing
chardet==5.1.0          # CSV encoding detection
```

### **JavaScript Libraries** (already available)
```javascript
// File upload handling - already implemented
// CSV download - already implemented via Blob API
```

---

## 📋 **Weekly Workflow Integration**

### **Target User Experience**
1. **Upload CSV**: Click "Import Lineups CSV" → Select file → See match results
2. **Review Matches**: Confirm high-confidence matches, manually resolve ambiguous ones
3. **Apply Updates**: Starter multipliers automatically update based on predictions
4. **Export Results**: Filter players → Click export → Download CSV with True Values

### **Fantasy Football Scout Integration**
```
Source: https://www.fantasyfootballscout.co.uk/team-news/
Format: Predicted XI tables for all 20 Premier League teams
Export: Manual copy-paste into CSV or direct download
```

---

## 🚨 **Critical Implementation Notes**

### **Player Matching Strategy**
1. **Exact Match**: Try exact name + team match first
2. **Fuzzy Match**: Use fuzzywuzzy with 85%+ confidence threshold
3. **Manual Review**: Flag ambiguous matches for user confirmation
4. **Team Context**: Use team information to disambiguate common names

### **Performance Considerations**
- **File Size Limits**: Restrict CSV uploads to 10MB max
- **Processing Time**: Show progress indicator for large files
- **Memory Usage**: Stream large CSVs rather than loading entirely

### **Error Handling**
- **Invalid CSV**: Clear error messages with format examples
- **Encoding Issues**: Auto-detect and convert CSV encoding
- **Database Errors**: Rollback failed imports gracefully

---

## 🧪 **Testing Strategy**

### **Unit Tests**
```python
# Test CSV parsing with various formats
# Test player name matching accuracy
# Test export functionality with filters
```

### **Integration Tests**
```python
# Test full CSV import workflow
# Test export with real player data
# Test error handling scenarios
```

### **User Acceptance Testing**
```
1. Upload real Fantasy Football Scout CSV
2. Verify all players matched correctly
3. Check starter multipliers updated
4. Export filtered results and validate content
```

---

## 📚 **Reference Documentation**

### **Existing Codebase**
- **Backend API**: `src/app.py` (lines 150-180 for starter prediction logic)
- **Frontend Controls**: `static/js/dashboard.js` (lines 698-746 for file operations)
- **Database Schema**: PostgreSQL players table with starter_multiplier column
- **Parameter System**: `config/system_parameters.json` manual_overrides section

### **Implementation Patterns**
- **File Upload**: Use Flask request.files with validation
- **Player Matching**: Database queries with LIKE and fuzzy matching
- **Parameter Updates**: Follow existing buildParameterChanges() pattern
- **Export**: Generate CSV server-side and stream to client

---

## 🎯 **Success Criteria for Day 6**

### **Must Have**
- [ ] CSV import successfully updates starter predictions for 90%+ of common names
- [ ] Export functionality includes all filtered player data
- [ ] Error handling prevents system crashes from malformed data
- [ ] User feedback shows import/export progress and results

### **Nice to Have**
- [ ] Preview mode shows CSV content before applying changes
- [ ] Multiple CSV format support (Fantasy Football Scout, custom, etc.)
- [ ] Export format options (CSV, Excel, JSON)
- [ ] Batch import history and rollback capability

---

## 🚀 **Getting Started Commands**

### **Development Environment**
```bash
# Start database
cd "C:\Users\halvo\.claude\Fantrax_Value_Hunter"

# Start Flask development server
python src/app.py

# Open dashboard
http://localhost:5000
```

### **Testing CSV Import**
```bash
# Create test CSV file
echo "Team,Player Name,Position,Predicted Status" > test_lineups.csv
echo "ARS,Bukayo Saka,M,Starter" >> test_lineups.csv

# Test import endpoint
curl -X POST -F "lineups_csv=@test_lineups.csv" http://localhost:5000/api/import-lineups
```

---

**Ready to implement Day 6! CSV Import & Export functionality will complete the core weekly workflow for Fantrax Value Hunter.** 🚀

**Last Updated**: August 15, 2025 - Day 3 Complete, Day 6 Ready to Begin