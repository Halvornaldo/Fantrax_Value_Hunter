# CLAUDE.md - AI Assistant Context  
# Fantrax Value Hunter - Version 1.0

This file contains essential context for AI assistants working on the Fantrax Value Hunter project.

---

## 🎯 **Project Mission - Version 1.0**
Build a **two-panel Flask dashboard** for parameter tuning across **all 633 Premier League players**. Focus on True Value discovery through real-time parameter adjustment, not automatic lineup generation.

**Version 1.0 Goal**: Parameter adjustment controls affecting True Value rankings for complete player database.

## 📋 **League Rules & Context**

### **League Information**
- **Name**: Its Coming Home (EPL 2025-26)
- **League ID**: `gjbogdx2mcmcvzqa`
- **Format**: Weekly reset (can change entire 11-player team each week)
- **Budget**: $100 salary cap per game week
- **Season**: Starts August 15, 2025 (38 game weeks)

### **Roster Requirements**
- **Total Players**: 11
- **Goalkeeper (G)**: 1 (required)
- **Defenders (D)**: 3-5 players
- **Midfielders (M)**: 3-5 players  
- **Forwards (F)**: 1-3 players

### **Key Strategic Insight**
🔒 **Price Lock Advantage**: Once you buy a player at a specific price, you keep that price for as long as you own them. This means finding undervalued players early provides massive long-term value.

---

## ⚡ **Scoring System Weights**

### **High Value Actions**
- **Goals (G)**: 7 points - Highest scoring action
- **Clean Sheets**: 6 points - Defenders/Goalkeepers only  
- **Penalty Saves (PKS)**: 8 points - Goalkeepers only
- **Assists (A)**: 4 points - All positions

### **Medium Value Actions**  
- **Shots on Target (SOT)**: 3 points - Key metric for midfielders/forwards
- **Free Kick Goals (FKG)**: 3 bonus points
- **Hat Tricks (HT)**: 3 bonus points
- **Saves (Sv)**: 2 points each - Goalkeeper volume stat
- **Wins (W)**: 4 points - Goalkeepers only

### **Negative Actions (Avoid)**
- **Red Cards (RC)**: -8 points - Season killers

---

## 🔗 **Global Name Matching System** *(PRODUCTION READY)*

### **Critical Context for AI Assistants**

**Status**: ✅ Complete and Production Deployed (August 16, 2025)

The Global Name Matching System is a **production-ready enterprise solution** that resolves player name discrepancies across multiple data sources. This system eliminates the original 99.1% accuracy problem with 3 silent failures.

### **Current Implementation Status**
- ✅ **Database Schema**: `migrations/001_create_name_mappings.sql` 
- ✅ **Core Engine**: `src/name_matching/unified_matcher.py`
- ✅ **6 Matching Strategies**: `src/name_matching/matching_strategies.py`
- ✅ **Smart Suggestions**: `src/name_matching/suggestion_engine.py`
- ✅ **5 API Endpoints**: Integrated into `src/app.py` 
- ✅ **Validation UI**: `templates/import_validation.html`
- ✅ **FFS Integration**: Updated `import-lineups` endpoint
- ✅ **HTML Entity Support**: Handles `&#039;` → `'` for web sources
- ✅ **50+ Verified Mappings**: Production database with learning system

### **Performance Metrics** *(Tested and Validated)*
- **FFS CSV Import**: 71.4% automatic match rate, 95%+ confidence
- **Understat Ready**: 16.7% automatic, 91.7% reviewable (realistic)
- **Validation UI**: 100% visibility, 0% silent failures
- **Database**: 50+ mappings across 3 source systems

### **Key Files for AI Context**
```
ESSENTIAL READING:
├── docs/GLOBAL_NAME_MATCHING_SYSTEM.md  # Complete technical documentation
├── README.md                            # Updated with system overview
├── src/name_matching/                   # Core implementation
├── test_validation_api.py               # API test results
├── test_validation_workflow.py         # End-to-end workflow test
└── import_existing_mappings.py         # Bootstrap data import

PRODUCTION ENDPOINTS:
├── /api/validate-import                 # Preview imports with suggestions
├── /api/get-player-suggestions         # Smart recommendations  
├── /api/confirm-mapping                 # User confirmations
├── /api/apply-import                    # Execute validated imports
├── /api/name-mapping-stats             # System health metrics
└── /import-validation                   # Web UI for manual review
```

### **Integration Examples**
```python
# Current production usage in FFS import
matcher = UnifiedNameMatcher(DB_CONFIG)
result = matcher.match_player("O'Riley", "ffs", "BHA", "M")
# Returns: {'fantrax_name': 'Matt ORiley', 'confidence': 78.6, ...}

# Ready for Understat integration
result = matcher.match_player("matt o&#039;riley", "understat", "BHA", "M")  
# HTML decoded: returns same Matt ORiley match
```

### **AI Assistant Guidelines**
1. **System is Production Ready**: No need to reimplement, use existing APIs
2. **Integration Pattern**: Always use validation workflow for new data sources
3. **Testing Available**: Comprehensive test suite validates all functionality
4. **Documentation Complete**: Full technical docs in `GLOBAL_NAME_MATCHING_SYSTEM.md`
5. **Learning System**: Each user confirmation improves future accuracy

### **Bug Fix Sprint Progress** *(August 17, 2025)*

**✅ SPRINT 1 COMPLETED - Critical Filter Fixes**
- ✅ Position filter bug: Fixed empty array handling (frontend + backend)
- ✅ Team filter population: Created `/api/teams` endpoint, populated dropdown with all 20 EPL teams  
- ✅ Filter combinations: All complex combinations verified and working

**✅ SPRINT 2 COMPLETED - Critical Import Validation Fixes**
- ✅ **Import validation bug**: Fixed 500 error on dry run functionality
- ✅ **Player mapping bug**: Fixed "only 10 players showing" issue (was limiting to 10 for debugging)
- ✅ **Team dropdown bug**: Fixed empty dropdowns for manual player selection
- ✅ **Syntax error fix**: Resolved malformed `else` statement in `/api/apply-import` endpoint
- ✅ **Global Name Matching learning verified**: System successfully learns from manual mappings
  - Match rate improved from 13.6% → 17.3% (30 → 38 automatic matches)
  - 8 additional players automatically matched after learning from manual confirmations

**✅ SPRINT 3 COMPLETED - Table Sorting Fix**
- ✅ Table sorting: Fixed to work on full dataset (server-side) instead of current page only

**✅ SPRINT 4 COMPLETED - xGI Multiplier Display**  
- ✅ xGI multiplier column now displayed in table alongside other multipliers

**✅ SPRINT 5 COMPLETED - Form Data Infrastructure** 
- ✅ **Complete form data system**: `/api/import-form-data` endpoint with auto-add functionality
- ✅ **Web upload UI**: Complete interface at `/form-upload` with step-by-step workflow
- ✅ **Dashboard integration**: Navigation button added to main dashboard
- ✅ **100% import success**: Auto-add missing players from transfer window
- ✅ **Safe duplicate handling**: ON CONFLICT DO UPDATE for weekly uploads
- ✅ **Documentation**: Complete technical documentation in FORM_DATA_INFRASTRUCTURE.md

**✅ SPRINT 6 COMPLETED - Odds-Based Fixture Difficulty**
**Status**: ✅ Complete and Production Deployed (August 18, 2025)  
**Objective**: Replace non-functional fixture difficulty system with sophisticated odds-based position-weighted system
**Documentation**: Complete technical documentation in `docs/FIXTURE_DIFFICULTY_SYSTEM.md`

**Key Achievements**:
- ✅ **21-point difficulty scale** (-10 to +10) from betting odds - fully operational
- ✅ **Position-specific weight multipliers** (G: 110%, D: 120%, M: 100%, F: 105%) - implemented
- ✅ **Preset system** (Conservative ±10%, Balanced ±20%, Aggressive ±30%) with fine-tuning - working
- ✅ **CSV upload integration** - OddsPortal.com data import via `/odds-upload` interface
- ✅ **Dashboard controls** - Complete UI replacing 5-tier/3-tier system
- ✅ **Performance optimization** - Calculation time reduced from 90s → 46s (2x faster)
- ✅ **Upload page integration** - Both form and odds upload accessible from main dashboard

**Live System Verification**:
- Current gameweek: 1 (using gameweek 2 odds as test data)
- Arsenal players: 1.209x (defenders), 1.191x (goalkeepers), 1.174x (midfielders)  
- Leeds players: 0.791x (defenders), 0.809x (goalkeepers) - proper penalty for hard fixtures
- All 633 players: Dynamic fixture multipliers (no more 1.00x lock)

**📋 SPRINT 7 IN PROGRESS - Critical Bug Fixes**
**Status**: ⚠️ Partial completion - Manual override fixed, Understat validation partially fixed  
**Objective**: Fix two critical functionality issues discovered in production

**✅ Bug 1: Manual Override of Starter Predictions Not Working** 
- ✅ **FIXED**: Created `/api/manual-override` endpoint for immediate processing
- ✅ **FIXED**: Manual override radio buttons now update starter multiplier in real-time
- ✅ **FIXED**: Removed dependency on "Apply Changes" button click
- ✅ **VERIFIED**: All manual override buttons (S/B/O/A) working correctly

**✅ Bug 2: xGI Integration Name Matching Issues - FIXED**  
- ✅ **FIXED**: "undefined" display issue - now shows actual player counts (36 unmatched)
- ✅ **FIXED**: Understat unmatched players route through Global Name Matching System
- ✅ **FIXED**: Team assignment reversal (Fulham/Wolves data corruption in Understat source)
- ✅ **FIXED**: Empty BRE/NFO dropdowns (database uses BRF/NOT codes)  
- ✅ **FIXED**: Apply-mappings endpoint 500 error (field name mismatches resolved)
- ✅ **FIXED**: Database ID column confusion (id column contains fantrax_id values)

**Technical Fixes Applied**:
- Enhanced corruption detection logic for Fulham↔Wolves team swap in Understat data
- Team code mapping verified: BRF (Brentford), NOT (Nottingham Forest) are correct
- Fixed field name mismatches: `player_name` vs `name`, `xG90` vs `xg90` capitalization
- Corrected database query structure: `WHERE id = %s` with fantrax_id value
- Added comprehensive error handling and logging for debugging
- Enhanced team validation with known corruption pattern detection

**📋 SPRINT 8 PENDING - Data Validation Dashboard**
- Complete data validation dashboard for quality checks
- Comprehensive workflow documentation and user guides

**🎯 KEY ACHIEVEMENT**: Complete fixture difficulty system operational with real-time odds-based calculation, 2x performance optimization, and full dashboard integration. All 633 players now have dynamic fixture multipliers replacing the non-functional 1.00x system.

### **⚠️ CRITICAL: Database Team Codes Reference (2025-26 Season)**

**Correct team codes in database:**
- **Brentford**: `BRF` (NOT `BRE`)
- **Nottingham Forest**: `NOT` (NOT `NFO`)
- **All Other Teams**: Standard 3-letter codes

**Complete team list verified in database:**
`['ARS', 'AVL', 'BHA', 'BOU', 'BRF', 'BUR', 'CHE', 'CRY', 'EVE', 'FUL', 'LEE', 'LIV', 'MCI', 'MUN', 'NEW', 'NOT', 'SUN', 'TOT', 'WHU', 'WOL']`

**Database ID Column Structure:**
- **Column Name**: `id` (primary key)
- **Column Content**: Contains Fantrax player IDs (e.g., "04tm0", "06yb9")
- **SQL Usage**: `WHERE id = %s` (use column name 'id', not 'fantrax_id')
- **Frontend Variables**: Often named `fantrax_id` for clarity, but maps to `id` column

---

## 💰 **Value Strategy Framework**

### **Position-Specific Targeting**
1. **Goalkeepers**: 
   - Target: Teams with tough fixtures (more saves)
   - Bonus: Clean sheet potential from good defenses
   - Sweet spot: $5-8 range

2. **Defenders**:
   - Primary: Clean sheet probability (6 points!)
   - Secondary: Set piece threats (corners/free kicks)
   - Target: Big club defenders in good form

3. **Midfielders**:
   - Primary: Shots on target (3 points each)
   - Secondary: Assist potential from creative roles
   - Target: Advanced midfielders, avoid defensive mids

4. **Forwards**:
   - Primary: Goal scoring (7 points)
   - Secondary: Penalty takers (guaranteed goals)
   - Target: In-form strikers with good fixtures

### **Value Identification Strategy**
- **Points per Dollar**: Primary metric regardless of absolute price
- **Ownership %**: Under 40% = differential opportunity  
- **True Value Discovery**: Best value can be any price ($5, $8, $12, $20+)
- **Form Trends**: Recent performance vs season averages
- **Opponent Difficulty**: Numerical rank of next fixture difficulty

---

## 🔧 **Technical Implementation Context**

### **Data Access**
```python
# Authentication Setup
api = FantraxAPI('gjbogdx2mcmcvzqa', session=authenticated_session)

# Core Data Structure
player = {
  'scorer': {
    'name': 'Player Name',
    'teamShortName': 'ARS', 
    'posShortNames': 'M',  # Position
    'scorerId': 'unique_id'
  },
  'cells': [
    rank, opponent, salary, fantasy_points, 
    percent_drafted, adp, percent_rostered
  ]
}
```

### **Key Challenges & Solutions**
1. **Pagination**: API only returns 20 players per page (32 pages total)
   - Solution: Loop through all pages programmatically
   
2. **Historical Data**: Season/period switching parameters not working
   - Workaround: Focus on current projections + manual fixture analysis
   
3. **Real-time Updates**: Player values change frequently  
   - Solution: Cache data with timestamps, refresh hourly

### **Value Calculation Framework**
**Base Formula (Requires Approval):**
- **ValueScore** = Price ÷ Fantasy Points per Game (PPG)
- **True Value** = ValueScore × weekly adjustment factors (starter likelihood, fixture difficulty, form)
- **Points per Minute (PPM)** = For gem finder analysis (substitute/rotation upside)

**Candidate Pool Strategy:**
**Target Pool Sizes:**
- **Goalkeepers**: Top 8 by True Value (price ranges: $5-15)
- **Defenders**: Top 20 by True Value (full spectrum: $5-20+)  
- **Midfielders**: Top 20 by True Value (full spectrum: $5-25+)
- **Forwards**: Top 20 by True Value (full spectrum: $5-25+)

**Required Columns**: Player | Position | Price | PPG | ValueScore | True Value | PPM | Ownership% | Predicted Starter | Next Opponent Rank | Form Score

---

## 🎲 **Fixture Analysis Strategy**

### **Odds-Based Difficulty**
- **OddsChecker.com**: Primary source for match odds
- **Clean Sheet Probability**: Lower odds = stronger team = better defense
- **Goal Scoring Odds**: Higher odds = weaker defense = attacking opportunity

### **Fixture Factors**
- **Home vs Away**: Home teams ~65% more likely to keep clean sheets
- **Form**: Recent results more predictive than season averages  
- **Injuries/Rotation**: Monitor team news for lineup changes
- **European Competition**: Midweek games cause fatigue/rotation

---

## 🏆 **Success Patterns**

### **Proven Strategies**
1. **True Value Targeting**: Highest points-per-dollar regardless of absolute price
2. **Price Range Balance**: Mix of budget ($5-8), mid-tier ($9-15), and premium ($16+) players
3. **Differential Targeting**: Players under 40% ownership with upside
4. **Clean Sheet Hunting**: Defenders from top 6 teams in home fixtures
5. **Shot Volume**: Midfielders with 3+ shots per game average

### **Avoid These Traps**
1. **Expensive Goalkeepers**: Rarely worth premium pricing
2. **Defensive Midfielders**: Low scoring upside despite stability  
3. **Rotation Risks**: Players likely to be benched/substituted early
4. **Card-Prone Players**: Defenders with disciplinary issues

---

## 📊 **Expected Performance Benchmarks**

### **MVP Success Metrics**
- Generate valid $100 lineup recommendation ✅
- Identify 3+ value players (>1.5 points per dollar) ✅  
- Outperform league average by 10%+ in first week

### **Weekly Targets**
- **Budget Efficiency**: Spend $95-100 (don't leave money on table)
- **Value Players**: 3-4 players at $5-7 range for high ROI
- **Premium Allocation**: 1-2 expensive players ($15+) only if exceptional value
- **Differential Count**: 2-3 low ownership players for competitive edge

---

## 🚨 **Critical Reminders**

### **Always Remember**
1. **Weekly Reset**: No long-term commitment, pivot freely each week
2. **Price Lock**: Early value picks provide season-long advantage
3. **Budget Constraint**: Must stay within $100, no exceptions
4. **Position Limits**: Respect min/max position requirements
5. **Deadline**: Lineups lock 1.5 hours before first match

### **Game Week 1 Priority**
🏃‍♂️ **URGENT**: Season starts tomorrow (August 15, 2025)
- Focus on MVP functionality first
- Get working lineup generator ASAP  
- Identify immediate value opportunities
- Build foundation for future enhancements

---

## 🔗 **File Structure Reference**
```
Fantrax_Value_Hunter/
├── PRD.md                 # Product requirements
├── CLAUDE.md             # This context file  
├── PLAN.md               # Development roadmap
├── quick_lineup.py       # MVP lineup generator
├── config.py             # League/scoring configuration
├── data_fetcher.py       # API data collection
└── value_calculator.py   # Player analysis logic
```

## 📞 **Quick Reference Commands**
```bash
# Test Fantrax connection
cd ../Fantrax_Wrapper && python test_with_cookies.py

# Run value analysis  
python analyze_value.py

# Generate lineup (after MVP built)
python quick_lineup.py
```

## 🧪 **Development Approach**

### **Quality-First Development**
- **Test each component**: Validate functionality before integration
- **Scope discipline**: Stick to documented requirements, no feature creep
- **Incremental progress**: Small, tested steps toward reliable system
- **Data validation**: Cross-check all calculations against known values

### **🚨 CRITICAL: Math & Formula Approval Process**
- **ALL mathematical formulas** must be justified, reviewed, and approved before deployment
- **No formula changes** without explicit approval and reasoning documentation
- **Easy tweaking required**: All calculations must be parameterized for post-launch adjustments
- **Real sample validation**: Test with actual game week data once available

### **📊 Version 1.0 Dashboard Features**
**Core Parameter Controls:**
- **Form Calculation**: Enable/disable toggle with 3/5 game lookback options
- **Fixture Difficulty**: 5-tier multiplier system with adjustable sliders
- **Starter Predictions**: Confidence multipliers for CSV-imported lineup data
- **Display Filters**: Position, price range, ownership, team, name search
- **Real-time Updates**: Parameter changes trigger True Value recalculation for all 633 players

**Implementation Guide**: See `docs/VERSION_1.0_SPECIFICATION.md` and `docs/PHASE_3_IMPLEMENTATION_PLAN.md`

### **Database Foundation Complete (Day 1)**
1. **PostgreSQL Setup**: Database operational with 633 players imported
2. **True Value Formula**: PPG ÷ Price validated with real data
3. **Multiplier Framework**: Form, fixture, starter calculations ready
4. **MCP Integration**: Database queries working through Claude interface

### **Flask Backend Complete (Day 2)**
1. **Flask Application**: Complete `src/app.py` with all required API endpoints operational
2. **Database Integration**: PostgreSQL connection via psycopg2 for Python operations
3. **API Routes**: 5 endpoints implemented and tested (health, players, config, update-parameters, dashboard)
4. **Performance Verified**: Sub-second response times for all 633 player queries
5. **Form Calculation**: Complete weighted average implementation (3/5 gameweek lookback)
6. **True Value Engine**: Real-time recalculation across all 633 players in ~0.44 seconds
7. **Parameter Persistence**: Updates automatically saved to `system_parameters.json`
8. **Error Handling**: Robust decimal/float conversion and database error handling

### **Enhanced Parameter Controls Complete (Day 3)**
1. **Baseline Switchover Control**: Added gameweek selector for form calculation transition (dashboard.html:46-49)
2. **3-Tier Fixture Difficulty**: Complete implementation with toggle visibility and separate multiplier controls
3. **Form Strength Slider**: Added missing strength multiplier to Form Calculation section
4. **Manual Override System**: Per-player radio buttons (Starter/Bench/Out/Auto) with color-coded styling
5. **Complete JavaScript Integration**: All new controls properly handle parameter changes and API communication
6. **CSS Styling**: Comprehensive manual override controls with intuitive color scheme
7. **Real-time Updates**: All enhanced controls trigger immediate True Value recalculation
8. **Legacy Parameter Analysis**: Identified 3 unused parameters for future cleanup

### **Key Technical Patterns Established**
- **MCP for Analysis**: Use Database MCP for Claude queries and data exploration
- **psycopg2 for Flask**: Standard Python database driver for application operations
- **API Response Format**: Consistent JSON responses with pagination and metadata
- **Parameter Management**: Real-time updates with immediate True Value recalculation

---

**Last Updated**: August 18, 2025 - Sprint 6 Complete, Sprint 7 Bug Fixes Identified  
**Status**: Production dashboard operational with complete fixture difficulty system (6 sprints complete). Two critical bugs identified requiring Sprint 7 fixes before proceeding to Sprint 8 data validation dashboard. 🎯