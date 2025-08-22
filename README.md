# Fantrax Value Hunter
**Fantasy Football Analytics Platform - Production Ready**

Advanced dashboard for finding undervalued Premier League players through **dual calculation engines** (v1.0 Legacy + v2.0 Enhanced). Features dynamic historical data blending, real-time parameter adjustment, manual overrides, and comprehensive data integration for all 647+ Premier League players.

---

## 🎯 **Current Status: v2.0 Enhanced Formula Complete**

✅ **Formula Optimization v2.0** - **Dynamic Blending System**:
- **Historical Data Integration**: Real 2024-25 season performance blended with current 2025-26 data
- **Dual Engine System**: v1.0 Legacy + v2.0 Enhanced running in parallel
- **Smart Transition**: Early season uses 93.3% historical, 6.7% current data (GW2)
- **Enhanced Calculations**: EWMA form, exponential fixture difficulty, normalized xGI
- **True Value Separation**: Point prediction separate from ROI (value/price ratio)

✅ **Production Dashboard** with:
- **Two-Panel Design**: Parameter controls + filterable player table  
- **Formula Toggle**: Switch between v1.0 Legacy and v2.0 Enhanced modes
- **ROI Column**: Return on Investment calculations (v2.0 only)
- **Manual Override System**: Real-time starter prediction controls (S/B/O/A)
- **Advanced Filtering**: Position, price range, team, player search
- **Professional UI**: Tooltips, color coding, responsive design

**Major Updates (2025-08-22)**:
- **✅ COMPLETE**: Dynamic Blending with historical PPG integration from 2024-25 season
- **✅ COMPLETE**: Current gameweek detection (no more hardcoded GW1)  
- **✅ COMPLETE**: Enhanced API endpoints with complete dataset integration
- **✅ STABLE**: Git checkpoint created (`v2.0-dynamic-blending-stable`)

---

## 🚀 **Quick Start**

### **1. Launch Application**
```bash
cd C:/Users/halvo/.claude/Fantrax_Value_Hunter
python src/app.py
```
**Access**: http://localhost:5000  
**Database**: PostgreSQL on localhost:5433 (fantrax_user/fantrax_password)

### **2. Use Dashboard**
- **Left Panel**: Adjust form, fixture, starter, xGI, and blender display parameters
- **Right Panel**: View all players ranked by True Value with advanced filtering
- **Real-time Updates**: Parameter changes trigger immediate recalculation
- **Manual Overrides**: Use S/B/O/A radio buttons for starter predictions

### **3. Data Import Workflows**
- **📊 Upload Weekly Game Data**: Fantrax CSV via `/form-upload`
- **⚽ Upload Fixture Odds**: Betting odds CSV via `/odds-upload`  
- **Import Lineups CSV**: Starter predictions with intelligent name matching
- **Sync Understat**: xGI data integration with name resolution

---

## 📁 **Project Structure**

```
Fantrax_Value_Hunter/
├── README.md                           # This file - Production overview
├── CLAUDE.md                          # Development context
├── requirements.txt                   # Python dependencies
├── docs/                              # Complete documentation
│   ├── FEATURE_GUIDE.md              # Dashboard functionality guide
│   ├── API_REFERENCE.md              # Complete endpoint documentation  
│   ├── DATABASE_SCHEMA.md            # Database structure with credentials
│   └── DEVELOPMENT_SETUP.md          # Setup and testing instructions
├── src/
│   ├── app.py                        # ✅ Flask backend (2500+ lines)
│   ├── db_manager.py                 # Database management
│   ├── fixture_difficulty.py         # Odds-based difficulty calculation
│   ├── form_tracker.py               # Form calculation utilities
│   └── name_matching/                # Global name matching system
│       ├── unified_matcher.py        # Core matching service
│       ├── matching_strategies.py    # 6 matching algorithms
│       └── suggestion_engine.py      # Smart suggestions with confidence
├── templates/
│   ├── dashboard.html                # ✅ Two-panel UI with tooltips
│   ├── form_upload.html              # ✅ Weekly game data upload
│   ├── odds_upload.html              # ✅ Fixture odds upload
│   └── import_validation.html        # ✅ Name matching validation
├── static/
│   ├── css/dashboard.css             # ✅ Professional styling
│   └── js/dashboard.js               # ✅ Parameter controls & table logic
└── config/
    ├── system_parameters.json        # ✅ All adjustable parameters
    └── fantrax_cookies.json          # Browser cookies (optional)
```

### **🔧 Development Setup**
See `docs/DEVELOPMENT_SETUP.md` for complete setup instructions including:
- Python dependencies and database setup
- Configuration files and verification scripts
- Testing guidelines and development workflow

---

## 🎯 **Core Features**

### **🎯 Dual Engine System**

**⚠️ IMPORTANT: Two Calculation Engines**
- **v1.0 Legacy**: Original system with static weights and linear calculations
- **v2.0 Enhanced**: Research-based improvements with dynamic blending

**v2.0 Enhanced Formula:**
```
True Value = Blended PPG × Form × Fixture × Starter × xGI
ROI = True Value ÷ Player Price
```

**Dynamic Blending (v2.0 only):**
```
Blended PPG = (w_current × Current PPG) + (w_historical × Historical PPG)
w_current = min(1, (gameweek-1)/(16-1))  // 6.7% current, 93.3% historical at GW2
```

### **Parameter Control Systems**

**Form Calculation**
- Weighted recent performance vs season/historical baseline
- Configurable lookback period (3-5 games) and strength multiplier
- Automatic baseline switchover at configurable gameweek

**Odds-Based Fixture Difficulty**  
- 21-point scale (-10 to +10) from real betting odds
- Position-specific weights (Defenders 120%, Goalkeepers 110%)
- Preset levels: Conservative/Balanced/Aggressive or custom

**Starter Predictions**
- CSV import with intelligent name matching
- Configurable rotation and bench penalties
- Real-time manual overrides (S/B/O/A controls)

**xGI Integration (Understat)**
- Expected Goals Involvement data (xG90 + xA90)
- Multiple multiplier modes: Direct, Adjusted, Capped
- Automatic sync with confidence-based name matching

**Blender Display Configuration**
- Configurable thresholds for historical vs current season data
- Smart display formats: "38 (24-25)", "38+2", "5"
- Transition periods for data source blending

### **Advanced Table Features**

**Sorting & Pagination**
- Click any column header to sort (Games column sorts numerically)
- Page size options: 50, 100, 200, All (~647 players)
- Efficient pagination with Previous/Next navigation

**Filtering System**
- Position checkboxes (G/D/M/F)
- Price range sliders ($5.0-$25.0)
- Team dropdown (multi-select)
- Player name search with real-time filtering

**Data Integration**
- Global Name Matching System with 100% visibility
- 6 matching algorithms with confidence scoring
- Manual review interface for unmatched players
- Learning system builds persistent mapping database

---

## 📊 **Database System**

**Core Tables**:
- `players` (647+ players) - Core player data with xG statistics
- `player_metrics` - Weekly performance data with all multipliers
- `player_games_data` - Games tracking (historical vs current)
- `name_mappings` - Cross-source player name resolution
- `team_fixtures` - Odds-based fixture difficulty scores
- `player_form` - Historical form data for calculations

**Performance**:
- Handles all Premier League players efficiently
- Optimized queries with appropriate indexes
- Real-time parameter updates in ~2-3 seconds
- Memory caching for fixture difficulty calculations

---

## 🔗 **API Endpoints**

**Player Data**: `/api/players` (filtering, sorting, pagination with historical_ppg)  
**v2.0 Calculations**: `/api/calculate-values-v2` (enhanced formula with dynamic blending)  
**Configuration**: `/api/config`, `/api/update-parameters`  
**Data Import**: `/api/import-form-data`, `/api/import-lineups`, `/api/import-odds`  
**Manual Overrides**: `/api/manual-override` (real-time starter adjustments)  
**Understat Integration**: `/api/understat/sync`, `/api/understat/stats`  
**Name Matching**: `/api/validate-import`, `/api/confirm-mapping`

See `docs/API_REFERENCE.md` for complete endpoint documentation.

---

## 🎲 **League Context**

- **League**: Its Coming Home (EPL 2025-26)
- **Budget**: $100 per game week
- **Format**: Weekly reset (complete team changes allowed)
- **Players**: 11 starters (1 GK, 3-5 DEF, 3-5 MID, 1-3 FWD)
- **Data Source**: All 647+ Premier League players with comprehensive metrics

---

## 📖 **Documentation**

Complete documentation available in `docs/` folder:

- **FEATURE_GUIDE.md**: Comprehensive dashboard functionality guide
- **API_REFERENCE.md**: All 25+ endpoints with request/response formats
- **DATABASE_SCHEMA.md**: Complete database structure with credentials
- **DEVELOPMENT_SETUP.md**: Setup instructions and development workflow

---

## 🔧 **System Status**

### **✅ Production Ready Features**
- Two-panel dashboard with real-time parameter adjustment
- All 647+ Premier League players with comprehensive filtering
- Manual override system for starter predictions
- Professional UI with tooltips and color coding
- Comprehensive data import workflows with name matching
- Optimized performance and caching systems

### **📊 Current Performance**
- **Database**: 647+ players with complete metrics
- **Response Time**: Parameter changes recalculate all players in ~2-3 seconds
- **Match Accuracy**: 71.4% automatic for FFS imports, 85%+ confidence scoring
- **UI Features**: Professional tooltips, numeric sorting, advanced pagination

### **🔄 Recent Major Updates (2025-08-22)**
- **v2.0 Enhanced Formula**: Complete dynamic blending system with historical data integration
- **Historical PPG Calculation**: Real 2024-25 season performance data properly integrated
- **Current Gameweek Detection**: Fixed hardcoded GW1 to use database MAX(gameweek)
- **Enhanced APIs**: Both main and v2.0 calculation endpoints include complete dataset
- **Git Safety**: Stable checkpoint created (`v2.0-dynamic-blending-stable`) for safe reversion

---

**🎯 Focus: Advanced parameter tuning for fantasy value discovery**  
**🔗 Production-ready data integration with intelligent name matching**