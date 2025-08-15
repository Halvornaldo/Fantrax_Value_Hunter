# CLAUDE.md - AI Assistant Context File
**Fantrax Value Hunter - Fantasy Football Analytics Platform**

## 🎯 PROJECT OVERVIEW

**Purpose**: Find undervalued fantasy football players using advanced analytics and generate optimal $100 lineups for weekly Fantrax league competition.

**Current Status**: Phase 2 Complete (Enhanced Analytics) - Ready for Phase 3 (Dashboard Development)

**League Context**: 
- Its Coming Home (EPL 2025-26)
- $100 budget per game week
- Weekly resets (11 players: 1 GK, 3-5 DEF, 3-5 MID, 1-3 FWD)

---

## 🏗️ ARCHITECTURE & CORE SYSTEMS

### **True Value Formula (VALIDATED & Production Ready)**
```
TrueValue = ValueScore × Form × Fixture × Starter
where ValueScore = PPG ÷ Price (CORRECTED - August 15, 2025)
```

**Formula Validation Results:**
- ✅ Corrected from Price ÷ PPG to PPG ÷ Price 
- ✅ Real FP/G data integrated (633 players from 2024-25 season)
- ✅ Budget players correctly rank higher when value is superior
- ✅ Jason Steele ($5.0, 9.0 FP/G) = 1.800 value vs Salah ($21.6, 14.82 FP/G) = 0.687 value

**All multipliers are dashboard-configurable via `config/system_parameters.json`**

### **System Components (Phase 2 Complete)**

1. **candidate_analyzer.py** - Main ranking system (VALIDATED)
   - Integrates all multipliers into True Value calculation with corrected formula
   - Real FP/G data integration from CSV files (Historical + Estimated tagging)
   - Generates candidate pools by position (8 GK, 20 DEF, 20 MID, 20 FWD)
   - Outputs detailed analysis tables and JSON export

2. **fixture_difficulty.py** - Football-Data.org API integration
   - Real Premier League standings and team strength calculation
   - 5-tier multiplier system (very_easy: 1.3x → very_hard: 0.7x)
   - Automatic caching with 24-hour refresh
   - **API Key Required**: Set in `config/api_keys.json`

3. **starter_predictor.py** - Dual-source consensus system
   - Fantasy Football Scout + RotoWire integration (framework ready)
   - Consensus multipliers: both_agree: 1.15x, conflicting: 0.9x, etc.
   - Currently uses mock data - ready for Playwright MCP integration

4. **form_tracker.py** - Player form analysis
   - Weighted 3/5-game lookback with dashboard toggle
   - Currently disabled (neutral 1.0x multiplier)

---

## 📁 PROJECT STRUCTURE

```
Fantrax_Value_Hunter/
├── README.md                 # Project overview and current status
├── CLAUDE.md                 # This file - AI context
├── src/
│   ├── candidate_analyzer.py # Main True Value system (Phase 2 ✅)
│   ├── fixture_difficulty.py # Football-Data.org API (Phase 2 ✅)
│   ├── starter_predictor.py  # Dual-source predictions (Phase 2 ✅)
│   ├── form_tracker.py      # Player form analysis (Phase 1 ✅)
│   └── save_baseline.py     # 2024-25 baseline data (Phase 1 ✅)
├── config/
│   ├── system_parameters.json # All adjustable parameters (Phase 2 ✅)
│   ├── api_keys.json         # External API keys (Football-Data.org)
│   └── fantrax_cookies.json  # Authentication cookies
├── data/                     # Cache and historical data
├── docs/                     # Complete documentation suite
└── static/                   # Dashboard assets (Phase 3)
```

---

## 🔧 CONFIGURATION MANAGEMENT

**All system parameters are configurable via `config/system_parameters.json`:**

- **Fixture Difficulty**: 5-tier vs 3-tier modes, multiplier ranges
- **Starter Predictions**: Consensus confidence multipliers
- **Form Calculation**: Lookback periods, enable/disable
- **Candidate Pools**: Pool sizes by position

**Key Design Principle**: Dashboard-first approach - all parameters adjustable via UI

---

## 🔑 AUTHENTICATION & API SETUP

### **Fantrax API Access**
- Export browser cookies to `config/fantrax_cookies.json`
- See `../Fantrax_Wrapper/WRAPPER_SUMMARY.md` for detailed guide
- Provides access to 633+ players across 32 pages

### **Football-Data.org API**
- Free tier: 10 requests/minute (sufficient for our needs)
- Set API key in `config/api_keys.json`
- Provides real Premier League standings for fixture difficulty

---

## 📊 CURRENT PHASE STATUS

### **✅ Phase 1 Complete: Foundation**
- Complete API access and authentication
- Basic candidate ranking system
- Form tracking with weighted games
- Comprehensive documentation

### **✅ Phase 2 Complete: Enhanced Analytics**
- Fixture difficulty integration with real API data
- Dual-source starter prediction framework
- Complete True Value formula implementation
- Full configuration system

### **🎯 Phase 3 Ready: Dashboard Development**
- Complete specification in `docs/DASHBOARD_IMPLEMENTATION.md`
- Three-panel Flask dashboard with drag-and-drop lineup builder
- Real-time parameter adjustment
- Database MCP integration planned

---

## 🧪 TESTING & VALIDATION

### **Current Test Results (August 15, 2025)**
- ✅ **Formula Validation**: ValueScore = PPG ÷ Price confirmed mathematically correct
- ✅ **Real Data Integration**: 633 players loaded from 2024-25 FP/G CSV data
- ✅ **Value Rankings**: Budget players correctly outrank expensive players when value is superior
- ✅ StarterPredictor: All imports successful, configuration working
- ✅ FixtureDifficultyAnalyzer: Real API data, 20 teams loaded, multipliers working
- ✅ CandidateAnalyzer: All systems integrated, True Value calculation operational

### **Known Limitations**
- Starter predictions currently use mock data (real scraping in Phase 3)
- Form calculation disabled (can be enabled via config)
- Database integration pending (using JSON files for now)

---

## 🛠️ DEVELOPMENT COMMANDS

### **Quick Start**
```bash
cd src/
python candidate_analyzer.py  # Full analysis with all systems
```

### **Individual Component Testing**
```bash
python fixture_difficulty.py   # Test API integration
python starter_predictor.py    # Test prediction system
python form_tracker.py         # Test form calculation
python test_real_formula.py    # Validate corrected formula with real data
```

### **Configuration Changes**
All parameter adjustments in `config/system_parameters.json` take effect immediately

---

## 🚀 NEXT DEVELOPMENT PRIORITIES

### **Immediate (Phase 3)**
1. ✅ **Formula Validation**: COMPLETE - PPG ÷ Price validated with real data
2. **Flask Dashboard**: Begin three-panel interface development
3. **Database MCP**: PostgreSQL integration for persistent data
4. **Real Scraping**: Implement Playwright MCP for starter predictions

### **Future Enhancements**
- Advanced analytics (PPM, injury tracking, transfer analysis)
- Machine learning integration
- Historical performance validation
- Mobile-responsive dashboard

---

## 🎯 DEVELOPMENT PHILOSOPHY

### **Core Principles**
- **Scope First**: Stick to defined requirements, avoid feature creep
- **Test Everything**: Validate each component before integration
- **Dashboard-Configurable**: All parameters adjustable via UI
- **Real Data**: Use live APIs wherever possible

### **MCP Server Integration**
- **Playwright MCP**: Web scraping for predictions and additional data
- **Database MCP**: Structured data storage and retrieval
- **Memory MCP**: Player relationship tracking
- **Context7 MCP**: Latest framework documentation

---

## ⚠️ CRITICAL RULES FOR AI ASSISTANTS

### **🚫 STRICTLY FORBIDDEN**
- **NO NEW FEATURES**: Do not add any features not explicitly mentioned in existing documentation
- **NO SCOPE CREEP**: Stick exactly to defined requirements in README.md, PLAN.md, and docs/
- **NO UNSOLICITED IMPROVEMENTS**: Only implement what is specifically requested
- **NO FRAMEWORK CHANGES**: Do not modify the core True Value formula without explicit approval

### **✅ WHEN WORKING ON THIS PROJECT**
1. **Always check current phase status** in README.md
2. **Respect the True Value formula** - all changes need approval
3. **Use existing configuration patterns** in system_parameters.json
4. **Test changes** with the component test commands above
5. **Update documentation** when making significant changes
6. **Ask before adding ANYTHING** not mentioned in existing docs

### **Key Dependencies**
- **fantraxapi**: Custom wrapper for Fantrax data access
- **requests**: HTTP requests for Football-Data.org API
- **json**: Configuration and data management
- **datetime**: Timestamp and caching logic

### **Common Gotchas**
- **Configuration Format**: Multipliers stored as dicts with metadata, not simple floats
- **API Rate Limits**: Football-Data.org free tier has 10 req/min limit
- **Path References**: Most scripts expect to run from `src/` directory
- **Authentication**: Fantrax cookies expire periodically and need refresh
- **Formula Direction**: ValueScore = PPG ÷ Price (NOT Price ÷ PPG) - validated August 15, 2025

---

**Last Updated**: August 15, 2025 - Phase 2 Enhanced Analytics Complete + Formula Validated
**Next Milestone**: Phase 3 dashboard development (formula validation ✅ COMPLETE)