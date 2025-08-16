# Fantrax Value Hunter
**Fantasy Football Analytics Platform - Version 1.0**

Two-panel dashboard for finding undervalued players through real-time parameter adjustment. Shows all 633 Premier League players with True Value calculations and advanced filtering.

---

## 🎯 **Version 1.0 Goal**

Build a **two-panel Flask dashboard** that displays all 633 players with:
- **Left Panel**: Parameter controls for adjusting True Value calculations
- **Right Panel**: Filterable table showing all players ranked by True Value
- **Core Feature**: Real-time parameter adjustment affecting rankings

**NO auto-lineup selection, NO drag-and-drop, NO complex features** - focus on parameter tuning for value discovery.

---

## 🚀 **Quick Start (Version 1.0)**

### **1. Database Setup (✅ Complete)**
```bash
# PostgreSQL is installed and populated with 633 players
# Database: fantrax_value_hunter on port 5433
```

### **2. Launch Dashboard (Coming Days 2-8)**
```bash
cd src/
python app.py  # Flask dashboard with parameter controls
```

### **3. Use Parameter Controls**
- Adjust form, fixture, and starter multipliers in left panel
- See immediate impact on True Value rankings in right panel
- Filter players by position, price, ownership, team

---

## 📁 **Project Structure**

```
Fantrax_Value_Hunter/
├── README.md                           # This file - v1.0 overview
├── requirements.txt                    # Python dependencies
├── docs/
│   ├── VERSION_1.0_SPECIFICATION.md   # Clear v1.0 definition
│   ├── CURRENT_STATUS.md              # Day 1 completion status  
│   ├── PHASE_3_IMPLEMENTATION_PLAN.md # Days 2-8 dashboard plan
│   ├── FUTURE_IDEAS.md                # Post-v1.0 features
│   ├── DATABASE_MCP_IMPLEMENTATION.md # Database setup guide
│   └── CLAUDE.md                      # AI context file
├── src/
│   ├── app.py                         # Flask dashboard (Days 2-3)
│   ├── db_manager.py                  # Database wrapper (✅ Complete)
│   ├── candidate_analyzer.py          # True Value calculations
│   ├── form_tracker.py               # Form multiplier logic
│   ├── fixture_difficulty.py         # Fixture multiplier logic
│   └── starter_predictor.py          # Starter multiplier logic
├── templates/
│   └── dashboard.html                 # Two-panel UI (Days 4-5)
├── static/
│   ├── css/dashboard.css             # Dashboard styling
│   └── js/dashboard.js               # Parameter controls
├── migrations/
│   └── import_csv_data.py            # Database population (✅ Complete)
├── config/
│   └── system_parameters.json        # All adjustable parameters
└── data/
    ├── fpg_data_2024.csv            # 633 players with FP/G data
    └── season_2024_baseline.json    # Historical baseline data
```

### **🔧 Development Setup**
```bash
# 1. Clone repository (after Git initialization)
git clone <repository-url>
cd Fantrax_Value_Hunter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up configuration
cp config/fantrax_cookies.json.example config/fantrax_cookies.json
# Edit with your browser cookies

# 4. Run current analysis
python src/candidate_analyzer.py

# 5. Future: Launch dashboard
python src/dashboard.py
```

---

## 🎯 **Development Philosophy**

### **⚖️ Scope & Quality First**
- **Stick to defined scope**: No feature creep or over-engineering
- **Test each component**: Validate every feature before moving forward
- **Incremental progress**: Small, tested steps toward the end goal
- **Slow and steady**: Build it right rather than build it fast

### **🧪 Testing Approach**
- **Unit validation**: Test each function with known data
- **API testing**: Verify data accuracy against Fantrax
- **Integration testing**: Ensure components work together
- **Real-world validation**: Compare recommendations to actual results

---

## 📊 **Current Status (Day 1 Complete + Documentation)**

### **✅ Database Foundation (August 15, 2025)**
- ✅ **PostgreSQL Setup**: Database operational on port 5433
- ✅ **Schema Created**: players, player_form, player_metrics tables
- ✅ **Data Imported**: All 633 players with complete metrics
- ✅ **True Value Formula**: PPG ÷ Price validated and working
- ✅ **Multiplier System**: Form, fixture, starter calculations ready
- ✅ **Form Calculation**: player_form table ready for 5 gameweek lookback

### **✅ Documentation Updated (August 15, 2025)**
- ✅ **Version 1.0 Scope**: Clearly defined in VERSION_1.0_SPECIFICATION.md
- ✅ **Future Features**: Moved to FUTURE_IDEAS.md (out of v1.0 scope)
- ✅ **Implementation Plan**: Updated for simplified two-panel dashboard
- ✅ **AI Context**: CLAUDE.md consolidated in docs/ folder

### **📊 Database Contents**
- **633 total players** with complete metrics for gameweek 1
- **Position breakdown**: 74 GK, 213 DEF, 232 MID, 114 FWD  
- **Value calculations**: PPG ÷ Price formula working correctly
- **Multipliers**: All default to 1.0, ready for dashboard adjustment

### **🎯 Next Steps (Days 2-8)**
1. **Day 2-3**: Flask backend with parameter adjustment endpoints
2. **Day 4-5**: Two-panel dashboard UI with all controls
3. **Day 6**: CSV import for starter predictions
4. **Day 7-8**: Testing and validation

---

## 🎯 **Version 1.0 Features**

### **Left Panel - Parameter Controls**
All boost factors adjustable via dashboard UI:

**Form Calculation**
- ✅ Enable/disable toggle
- Lookback period (3 or 5 games)
- Minimum games threshold

**Fixture Difficulty** 
- ✅ Enable/disable toggle
- 5-tier multiplier system with sliders
- Very Easy (1.2x-1.5x) through Very Hard (0.6x-0.8x)

**Starter Predictions**
- ✅ Enable/disable toggle  
- Confidence multipliers for consensus levels
- CSV import for weekly lineup updates

**Display Filters**
- Position checkboxes (G/D/M/F)
- Price range slider
- Ownership % threshold
- Team selector
- Name search

### **Right Panel - Player Table**
- **All 633 players** (not limited to 68)
- Sortable by True Value, Price, PPG, Ownership
- Real-time updates when parameters change
- Export filtered results to CSV

### **Core Workflow**
1. Adjust multipliers → True Value recalculates for all 633 players
2. Apply filters → See subset matching criteria  
3. Sort by True Value → Find best value opportunities
4. Export selection → Use for lineup construction

---

## 🔧 **Technical Stack**

- **Backend**: Flask + PostgreSQL with Database MCP integration
- **Frontend**: HTML/CSS/JavaScript with real-time parameter controls
- **Database**: 633 players with historical FP/G data
- **Formula**: `TrueValue = (PPG ÷ Price) × Form × Fixture × Starter`

---

## 📝 **Development Philosophy**

### **Version 1.0 Scope Discipline**
- ✅ **Core Feature**: Parameter adjustment affecting True Value rankings
- ✅ **Data Display**: All 633 players with filtering capabilities  
- ❌ **Out of Scope**: Auto-selection, drag-and-drop, web scraping

### **Quality First**
- Every parameter change must trigger accurate recalculation
- Database performance must handle 633 players smoothly
- UI must be responsive and intuitive for parameter tuning

---

## 📊 **League Context**

- **League**: Its Coming Home (EPL 2025-26)
- **Budget**: $100 per game week
- **Format**: Weekly reset (complete team changes allowed)
- **Players**: 11 (1 GK, 3-5 DEF, 3-5 MID, 1-3 FWD)

---

## 🔗 **Related Projects**

- **API Wrapper**: `../Fantrax_Wrapper/` - Complete Fantrax API documentation
- **Technical Guide**: `../Fantrax_Wrapper/WRAPPER_SUMMARY.md` - How to access all player data

---

---

## 🔗 **Global Name Matching System** *(Production Ready)*

### **Overview**
Enterprise-grade name matching system that resolves player name discrepancies across data sources (FFS CSV, Understat xG/xA, future integrations). Eliminates silent failures and provides smart suggestions for manual review.

### **Key Features**
- ✅ **100% Visibility**: No more silent failures - every player gets matched or flagged for review
- ✅ **Smart Suggestions**: AI-powered recommendations with confidence scoring
- ✅ **Learning System**: Builds mapping database through user confirmations (50+ mappings)
- ✅ **Validation UI**: Web interface at `/import-validation` for easy manual review
- ✅ **Multi-Strategy Matching**: 6 different algorithms (exact, fuzzy, component, etc.)
- ✅ **HTML Entity Support**: Handles encoded characters from web sources (`&#039;` → `'`)

### **Production Performance**
- **FFS CSV Import**: 71.4% automatic match rate, 95%+ confidence on matches
- **Understat Integration**: 16.7% automatic, 91.7% reviewable (realistic for first-time)
- **Database**: 50+ verified mappings across 3 source systems
- **API**: 5 endpoints for programmatic access and UI integration

### **Usage**
```bash
# Import with validation
curl -X POST http://localhost:5000/api/validate-import \
  -H "Content-Type: application/json" \
  -d '{"source_system": "ffs", "players": [...]}'

# Manual review UI
http://localhost:5000/import-validation

# Updated FFS import (now uses UnifiedNameMatcher)
curl -X POST http://localhost:5000/api/import-lineups \
  -F "lineups_csv=@your_file.csv"
```

### **Architecture**
```
name_matching/
├── unified_matcher.py      # Main matching service
├── matching_strategies.py  # 6 matching algorithms  
├── suggestion_engine.py    # Smart suggestions with confidence
└── __init__.py

Database Tables:
├── name_mappings           # Persistent player mappings
├── name_mapping_history    # Audit trail
└── players (existing)      # Canonical player database
```

### **Integration Status**
- ✅ **FFS CSV Import**: Fully integrated, production ready
- 🔄 **Understat xG/xA**: Ready for integration (tested, working)
- ⏳ **Future Sources**: Framework ready for any new data source

---

**Version 1.0: Focus on parameter tuning for value discovery 🎯⚽**
**Global Name Matching: Production-ready data integration system 🔗✨**