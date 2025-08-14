# Enhancement Ideas & Future Features
**Created**: August 14, 2025  
**Purpose**: Capture enhancement ideas for systematic evaluation and potential implementation

---

## 🆕 **New Player Projection System**

### **Problem Statement**
New signings lack historical Premier League data for PPG calculations, making ValueScore = Price ÷ PPG impossible to calculate reliably.

### **Proposed Solution Framework**
**Separate "New Player" candidate pool with projection-based valuations:**

#### **Transfer Value Indicators**
- **Transfer Fee**: High-fee signings likely get priority playing time
- **Position**: Attackers for good teams = higher point potential
- **Club Quality**: Top 6 clubs = better service, more goals/assists
- **Manager Comments**: Pre-season quotes about player role/importance

#### **Projection Formula Ideas (All Require Approval)**
```
Projected PPG = Base Position Average × Club Quality Multiplier × Transfer Priority Factor

Where:
- Base Position Average = League average PPG for position
- Club Quality Multiplier = Team's attacking/defensive strength
- Transfer Priority Factor = Transfer fee tier (£50M+ = 1.3x, £20-50M = 1.1x, <£20M = 1.0x)
```

#### **Sample Size Threshold**
- **Minimum Games**: 3-5 appearances before moving to standard PPG calculation
- **Confidence Indicator**: Show "PROJECTION" vs "DATA-BASED" in candidate tables
- **Separate Ranking**: New players in dedicated section until sample size adequate

---

## 📊 **Sample Size & Confidence Scoring**

### **Sample Size Factors**
- **Games Played**: <5 games = low confidence, 5-10 = medium, 10+ = high
- **Minutes per Game**: <60 mins = substitute pattern, >60 = likely starter
- **Recent Form Window**: Weight last 5 games heavier than season total

### **Confidence Score Ideas**
```
Confidence Score = (Games Played × 10) + (Avg Minutes ÷ 90 × 20) + Form Consistency Score

Display as: ★★★☆☆ (3/5 confidence)
```

---

## 🎯 **Advanced Value Adjustments**

### **Team Context Multipliers**
- **Attacking Teams**: Higher multiplier for forwards/midfielders
- **Defensive Teams**: Higher multiplier for defenders/goalkeepers  
- **Set Piece Specialists**: Bonus for corners/free kick takers
- **Penalty Takers**: Guaranteed goal opportunities

### **Fixture Run Analysis**
- **Next 3 Fixtures**: Easy run = value boost, tough run = value reduction
- **Home/Away Split**: Home form vs away form weighting
- **Double Gameweeks**: Identify fixtures with 2 games in one gameweek

---

## 🔄 **Dynamic Value Tracking**

### **Price Movement Predictions**
- **Rising Players**: Identify before price increases
- **Falling Players**: Avoid players likely to drop in price
- **Lock-in Advantages**: Players you own maintain their purchase price

### **Ownership Trend Analysis**
- **Rising Ownership**: Popular picks becoming mainstream
- **Falling Ownership**: Potential differential opportunities
- **Template Avoidance**: Identify over-owned "template" players

---

## 🧠 **Machine Learning Potential** (Phase 4+)

### **Pattern Recognition**
- **Breakout Player Profiles**: Identify characteristics of emerging stars
- **Bust Predictions**: Avoid overhyped players likely to disappoint
- **Form Cycles**: Predict when players enter/exit good form periods

### **Correlation Analysis**
- **Team Performance Impact**: How team results affect individual scores
- **Opposition Analysis**: Which players perform better vs specific opponents
- **Weather/Pitch Conditions**: External factors affecting performance

---

## 🛠 **Technical Implementation Ideas**

### **Data Pipeline Enhancements**
- **Real-time Updates**: Live injury news and lineup leaks integration
- **Multiple Data Sources**: Cross-validation from different providers
- **API Redundancy**: Backup data sources if primary API fails

### **Dashboard Parameter Controls**
- **Form Lookback Period**: Toggle between 3-game and 5-game analysis
  - 3 Games: [0.5, 0.3, 0.2] - Early season when data limited
  - 5 Games: [0.4, 0.25, 0.2, 0.1, 0.05] - Late season for more context
- **Baseline Switchover**: Adjust when to switch from 2024 baseline to current season (default: Game Week 10)
- **Pool Sizes**: Adjust candidate pool sizes (8 GK, 20 DEF, 20 MID, 20 FWD)
- **Differential Threshold**: Change ownership percentage for differential players (default: <40%)

### **User Interface Ideas**
- **Player Comparison Tool**: Side-by-side analysis of similar players
- **What-If Scenarios**: "What if I swap Player A for Player B?"
- **Historical Performance**: Track your decision accuracy over time
- **Real-time Parameter Testing**: See how form scores change with different lookback periods

---

## 📋 **Implementation Priority Framework**

### **Phase 2 Candidates** (Game Weeks 2-4)
1. **Sample Size Confidence Scoring**: Add confidence indicators to existing players
2. **New Player Projection System**: Handle mid-season transfers
3. **Fixture Run Analysis**: Next 3 games difficulty weighting

### **Phase 3 Candidates** (Game Weeks 5-8)  
1. **Team Context Multipliers**: Position-specific team strength adjustments
2. **Dynamic Ownership Tracking**: Monitor template vs differential shifts
3. **Advanced UI Features**: Player comparison and scenario tools

### **Phase 4+ Research** (Game Weeks 9+)
1. **Machine Learning Models**: Pattern recognition for breakout predictions
2. **External Data Integration**: Weather, pitch conditions, referee tendencies
3. **Advanced Analytics**: Expected goals/assists, underlying metrics

---

## 🔬 **Research Questions**

### **Formula Validation Needed**
- How much should transfer fee weight projection calculations?
- What's the optimal sample size threshold for PPG reliability?
- How do we balance recency vs total season performance?

### **Data Validation Required**
- Correlation between transfer fee and actual fantasy performance
- Club quality impact on individual player scoring rates
- Accuracy of predicted lineups vs actual lineups

---

**Note**: All mathematical formulas and weighting factors require justification, approval, and testing before implementation. This document serves as an idea repository, not implementation specifications.

---

*Last Updated: August 14, 2025*  
*Status: Brainstorming and conceptual framework*