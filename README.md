# Fantrax Value Hunter
**Fantasy Football Analytics Platform**

Comprehensive tool for finding undervalued players and generating optimal $100 lineups for weekly Fantrax league competition.

---

## 🚀 **Quick Start**

### **1. Authentication Setup**
```bash
# Copy your browser cookies to config/fantrax_cookies.json
# See ../Fantrax_Wrapper/WRAPPER_SUMMARY.md for cookie export guide
```

### **2. Run Value Analysis**
```bash
cd src/
python candidate_analyzer.py  # Generates ranked candidate pools by position
```

### **3. Future: Launch Dashboard**
```bash
# Coming in Game Week 2-3
python dashboard.py
```

---

## 📁 **Project Structure**

```
Fantrax_Value_Hunter/
├── README.md                           # This file - Project overview
├── .gitignore                          # Git ignore rules
├── requirements.txt                    # Python dependencies
├── docs/                              # Documentation
│   ├── PRD.md                         # Product requirements
│   ├── PLAN.md                        # Development roadmap
│   ├── CLAUDE.md                      # AI context file
│   ├── DASHBOARD_IMPLEMENTATION.md    # Complete dashboard specification
│   └── IDEAS.md                       # Enhancement ideas
├── src/                               # Source code
│   ├── candidate_analyzer.py          # Main candidate ranking system
│   ├── form_tracker.py               # Form calculation with weighted games
│   ├── save_baseline.py              # 2024-25 baseline data preservation
│   └── dashboard.py                   # Flask web dashboard (Phase 3)
├── config/                            # Configuration
│   ├── fantrax_cookies.json          # Authentication (not in git)
│   └── system_parameters.json        # Adjustable parameters
├── data/                              # Cache/historical data (not in git)
│   ├── season_2024_baseline.json     # 2024-25 baseline for first 10 GW
│   └── player_form_tracking.json     # Weekly form scores
├── tests/                             # Unit tests
│   ├── test_form_tracker.py          # Form calculation tests
│   └── test_candidate_analyzer.py    # Value calculation tests
└── static/                            # Dashboard assets (Phase 3)
    ├── css/
    ├── js/
    └── templates/
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

## 📊 **Current Status**

### **✅ Phase 1 Complete: Foundation (August 14, 2025)**
- ✅ Complete API access (633 players across 32 pages)
- ✅ Authentication with exported browser cookies  
- ✅ Candidate ranking system foundation
- ✅ Comprehensive documentation suite
- ✅ Form tracking system with weighted recent games
- ✅ 2024-25 baseline data preservation
- ✅ Complete dashboard specification (DASHBOARD_IMPLEMENTATION.md)

### **🔄 Phase 2 In Progress: Enhanced Analytics**
- ✅ **Form Calculation Framework**: Weighted 3/5-game lookback with enable/disable
- ✅ **Baseline Data System**: 2024-25 season data saved for first 10 games
- ✅ **Configuration System**: JSON-based parameter management
- 🚧 **Fixture Difficulty Integration**: OddsChecker.com scraping (pending)
- 🚧 **Predicted Starter Data**: Fantasy Football Scout integration (pending)
- 🚧 **Value Formula Validation**: Mathematical approval process (pending)

### **📋 Phase 3 Ready: Dashboard Development**
- ✅ **Complete Specification**: Three-panel dashboard with all features defined
- ✅ **API Endpoints**: Flask backend architecture documented
- ✅ **UI/UX Design**: Drag-and-drop lineup builder, real-time controls
- ✅ **Performance Optimization**: Virtual scrolling for 633+ players
- 🎯 **Ready to Build**: Implementation can begin immediately

### **🚀 Next Immediate Actions**
1. **Git Setup**: Initialize repository with proper .gitignore and structure
2. **Phase 2 Completion**: Add fixture difficulty and starter prediction data
3. **Phase 3 Start**: Begin Flask dashboard development
4. **Formula Approval**: Validate all mathematical calculations

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

**Built for the 2025-26 Premier League season 🏆⚽**