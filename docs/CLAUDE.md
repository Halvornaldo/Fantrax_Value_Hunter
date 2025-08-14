# CLAUDE.md - AI Assistant Context
# Fantrax Value Hunter Project

This file contains essential context for AI assistants working on the Fantrax Value Hunter project.

---

## 🎯 **Project Mission**
Create a comprehensive fantasy football analytics platform with accurate value metrics, context-aware player analysis, and an interactive web dashboard for optimal $100 lineups.

**🔄 Strategic Pivot**: Skip Game Week 1 to build a proper, reliable tool rather than rush a flawed MVP.

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
- **Own Goals (OG)**: -7 points
- **Penalty Misses (PKM)**: -6 points
- **Yellow Cards (YC)**: -3 points
- **Errors Leading to Goal (ErG)**: -3 points

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

### **📊 Dashboard Parameter Controls (Phase 3)**
**Key Adjustable Parameters:**
- **Form Calculation**: Enable/disable toggle (currently DISABLED for GW 1-3)
- **Lookback Period**: 3-game vs 5-game analysis with weighted values
- **Baseline Switchover**: When to switch from 2024 baseline to current season (default: GW 10)
- **Pool Sizes**: Candidate pool sizes per position (8 GK, 20 DEF, 20 MID, 20 FWD)
- **Differential Threshold**: Ownership percentage for differential status (<40%)

**Implementation Guide**: See `docs/DASHBOARD_IMPLEMENTATION.md` for complete specification

### **Testing Priorities**
1. **Value calculation accuracy**: Per-game vs season metrics
2. **Player data integrity**: All 633 players correctly parsed
3. **Constraint validation**: Budget and position requirements
4. **Real-world performance**: Recommendations vs actual results

---

**Last Updated**: August 14, 2025  
**Status**: Ready for systematic, tested development 🧪🎯