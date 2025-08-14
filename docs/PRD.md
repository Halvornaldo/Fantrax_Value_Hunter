# Product Requirements Document (PRD)
# Fantrax Value Hunter System

**Version**: 1.0  
**Date**: August 14, 2025  
**Project**: Fantrax Fantasy Football Value Optimization Tool  

---

## 1. Executive Summary

### 1.1 Product Vision
Create a comprehensive fantasy football analytics platform for the "Its Coming Home" Fantrax league, featuring accurate value analysis, context-aware player recommendations, and an interactive web dashboard for optimal $100 salary cap lineups each game week.

**Strategic Pivot**: Skip Game Week 1 to build a reliable, accurate system rather than rushing a flawed MVP.

### 1.2 Success Metrics
- **Primary**: Generate lineups that consistently outperform league average by 15%+
- **Secondary**: Identify 2-3 "hidden gems" per week (low ownership, high value players)
- **Tertiary**: Achieve top 3 league finish through superior player selection

---

## 2. Product Context

### 2.1 League Specifications
- **League Name**: Its Coming Home (EPL 2025-26)
- **League ID**: gjbogdx2mcmcvzqa
- **Format**: Weekly reset (complete team change allowed)
- **Budget**: $100 salary cap per game week
- **Team Size**: 11 players (1 GK, 3-5 DEF, 3-5 MID, 1-3 FWD)
- **Player Pool**: 633+ Premier League players

### 2.2 Scoring System
- **Goals**: 7 points (highest value action)
- **Clean Sheets**: 6 points (defenders/goalkeepers)
- **Assists**: 4 points
- **Shots on Target**: 3 points  
- **Penalty Saves**: 8 points (goalkeepers)
- **Cards/Errors**: Negative points (-3 to -8)

### 2.3 Strategic Advantages
- **Price Lock**: Players maintain purchase price for entire ownership period
- **Weekly Reset**: No long-term commitment, can pivot completely each week
- **Low Competition**: Undervalued players often have <50% ownership

---

## 3. User Stories

### 3.1 Primary User: League Manager
**As a** fantasy football manager  
**I want to** quickly identify the best value players for each game week  
**So that** I can optimize my $100 budget for maximum points  

**As a** competitive fantasy player  
**I want to** find undervalued players before the market discovers them  
**So that** I can gain long-term pricing advantages  

**As a** time-constrained user  
**I want** automated lineup recommendations  
**So that** I don't spend hours analyzing 633 players manually  

### 3.2 Core Use Cases
1. **Candidate Pool Generation**: Get ranked player pools (8 GK, 20 DEF, 20 MID, 20 FWD)
2. **Value Hunting**: Identify best points-per-dollar ratio across all price ranges
3. **Hidden Gem Detection**: Find low-ownership players with high upside potential
4. **Flexible Lineup Construction**: Build multiple $100 lineup scenarios from candidates
5. **Form & Fixture Analysis**: Factor in recent performance and opponent difficulty

---

## 4. Functional Requirements

### 4.1 MVP Features (Game Week 1 - Tomorrow)

#### 4.1.1 Data Collection
- **REQ-001**: Fetch all available player data from Fantrax API (633+ players)
- **REQ-002**: Extract key metrics: name, position, team, salary, projected points, ownership %
- **REQ-003**: Handle API pagination to access complete player database

#### 4.1.2 Value Analysis
- **REQ-004**: Calculate base ValueScore = Price ÷ Fantasy Points per Game (PPG)
- **REQ-005**: Calculate True Value = ValueScore adjusted by weekly factors (starter likelihood, fixture difficulty, form)
- **REQ-006**: Calculate Points per Minute (PPM) for gem finder analysis (substitute/injury return potential)
- **REQ-007**: Flag players with <40% ownership as differential candidates
- **REQ-008**: Ensure price range diversity to enable $100 lineup construction

#### 4.1.3 Candidate Pool Generation
- **REQ-009**: Generate ranked candidate pools: 8 GK, 20 DEF, 20 MID, 20 FWD
- **REQ-010**: Include full price spectrum ($5-25+) within each position's top candidates
- **REQ-011**: Output table with columns: Player | Position | Price | PPG | ValueScore | True Value | PPM | Ownership% | Predicted Starter | Next Opponent Rank | Form Score
- **REQ-012**: Provide extensible data structure for adding new metrics

### 4.2 Enhanced Features (Game Week 2+)

#### 4.2.1 Enhanced Data Integration
- **REQ-013**: Scrape fixture difficulty from OddsChecker.com and convert to 1-20 ranking (1=easiest, 20=hardest)
- **REQ-014**: Add form analysis (recent 3-5 games vs season average) as Form Score
- **REQ-015**: Integrate predicted starter data (Fantasy Football Scout) as value multiplier boost
- **REQ-016**: Add extensible data columns for new weekly factors

#### 4.2.2 Formula Framework & Approval System
- **REQ-017**: Base ValueScore = Price ÷ PPG (requires approval before deployment)
- **REQ-018**: True Value = ValueScore × weekly adjustment factors (requires approval)
- **REQ-019**: PPM calculation for gem finder analysis (requires approval)
- **REQ-020**: All formula parameters must be easily adjustable post-launch

#### 4.2.3 User Interface
- **REQ-017**: Web dashboard for interactive player analysis
- **REQ-018**: Automated weekly reports with recommendations
- **REQ-019**: Mobile-friendly lineup display

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **Response Time**: Generate lineup recommendations within 30 seconds
- **Data Freshness**: Update player data within 2 hours of Fantrax updates
- **Availability**: 99% uptime during critical decision periods

### 5.2 Usability
- **Simplicity**: One-click lineup generation for MVP
- **Clarity**: Clear explanation of player selection rationale
- **Accessibility**: Readable on mobile devices for quick decisions

### 5.3 Reliability
- **Data Accuracy**: Validate all salary and points data against Fantrax
- **Error Handling**: Graceful fallbacks if API data unavailable
- **Backup Strategy**: Cache recent data for offline analysis

---

## 6. Technical Specifications

### 6.1 Data Sources
- **Primary**: Fantrax API (authenticated with cookies)
- **Secondary**: OddsChecker.com (fixture difficulty)
- **Tertiary**: Manual data entry for edge cases

### 6.2 Technology Stack
- **Language**: Python 3.x
- **Libraries**: fantraxapi, requests, pandas, sqlite3
- **Storage**: SQLite database for historical tracking
- **UI**: Plotly/Dash for web dashboard (Phase 2)

### 6.3 Integration Points
- **Authentication**: Fantrax cookie-based session management
- **Data Export**: CSV export for spreadsheet analysis
- **Notifications**: Console output for immediate recommendations

---

## 7. Business Requirements

### 7.1 Constraints
- **Budget**: $0 (personal project)
- **Timeline**: MVP by Game Week 1 (August 15, 2025)
- **Resources**: Single developer (Claude AI assistance)

### 7.2 Dependencies
- **Critical**: Fantrax API access and authentication
- **Important**: Stable internet connection for data fetching
- **Nice-to-have**: Third-party odds/fixture APIs

### 7.3 Risk Mitigation
- **API Changes**: Monitor Fantrax updates, create manual backups
- **Data Quality**: Implement validation checks on all inputs
- **Time Constraints**: Focus on MVP features first, iterate rapidly

---

## 8. Success Criteria

### 8.1 MVP Success (Game Week 1)
- ✅ Generate valid $100 lineup recommendation
- ✅ Identify 3+ value players (>1.5 points per dollar)
- ✅ Complete setup and first run within 24 hours

### 8.2 Long-term Success (Season)
- 📈 Achieve top 25% league ranking by mid-season
- 🎯 Identify 10+ "breakout" players before market recognition
- 💰 Consistently find 2-3 minimum-price value players per week

### 8.3 User Satisfaction
- ⚡ Reduce lineup selection time from 2 hours to 15 minutes
- 📊 Provide data-driven confidence in player selections
- 🏆 Enable competitive advantage through superior analytics

---

## 9. Future Roadmap

### Phase 1: MVP (Week 1)
- Basic value analysis and lineup optimization

### Phase 2: Enhancement (Weeks 2-4) 
- Fixture analysis and advanced metrics

### Phase 3: Automation (Weeks 5-8)
- Web dashboard and automated recommendations

### Phase 4: Intelligence (Weeks 9+)
- Machine learning predictions and trend analysis

---

## 10. Appendix

### 10.1 Value Calculation Framework
- **Base ValueScore**: Price ÷ Fantasy Points per Game (PPG)
- **True Value**: ValueScore adjusted by weekly factors (starter likelihood, fixture difficulty, form)
- **Gem Finder**: Points per Minute (PPM) for identifying substitute/rotation players with upside
- **Output Columns**: Player | Position | Price | PPG | ValueScore | True Value | PPM | Ownership% | Predicted Starter | Next Opponent Rank | Form Score

### 10.2 League Context
- Season starts August 15, 2025 (tomorrow)
- 38 game weeks available for optimization
- Historical data from 2024-25 season accessible

**Document Approved**: Ready for development  
**Next Step**: Begin MVP implementation