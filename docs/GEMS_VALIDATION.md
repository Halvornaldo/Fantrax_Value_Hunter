# Gems Finder Validation Checklist
**Created**: August 14, 2025  
**Status**: ⚠️ OUTDATED - Now using flexible candidate ranking system (8 GK, 20 DEF, 20 MID, 20 FWD)
**Purpose**: Historical reference for manual validation process

**New Approach**: Candidate pools with PPM analysis for substitute/rotation upside identification

---

## 🚨 **Current System Limitations**

Our gems finder currently only looks at:
- Fantasy points vs salary (value ratio)
- Ownership percentage (<40% = differential)
- Basic position filtering

**Missing Critical Factors:**
- ❌ Minutes played per game
- ❌ Starting XI vs substitute role  
- ❌ Recent injury history
- ❌ Manager preference/rotation risk
- ❌ Recent form vs season total

---

## 📋 **Manual Validation Process**

### For Each "Gem" Player, Check:

#### 1. **Playing Time Analysis**
```
Questions to Research:
- Has player started last 3 games?
- Average minutes per appearance this season?
- Recent substitution patterns?
- Manager comments about player's role?
```

#### 2. **Fitness Status**
```
Check Sources:
- Premier League injury report
- Team official website news
- Recent training photos/videos
- Manager press conference quotes
```

#### 3. **Form Trend**
```
Compare:
- Last 5 games points vs season average
- Goals/assists in recent matches
- Shot frequency recent vs early season
```

#### 4. **Competition Analysis**
```
Position Battle:
- Who else plays this position?
- New signings affecting playing time?
- Youth players pushing for minutes?
```

---

## 🎯 **Game Week 1 Quick Validation**

### Current Top Gems to Validate:

#### **Richarlison (TOT) - $5.00, 32% owned**
**Quick Checks:**
- [ ] Started in recent pre-season friendlies?
- [ ] Any injury reports from summer?
- [ ] Postecoglou's comments on his role?
- [ ] Competition from other forwards?

#### **Jose Sa (WOL) - $5.00, 37% owned** 
**Quick Checks:**
- [ ] Confirmed as #1 goalkeeper?
- [ ] No new goalkeeper signings?
- [ ] Played in pre-season matches?
- [ ] Clean sheet record last season?

#### **Donyell Malen (AVL) - $5.00, 55% owned**
**Quick Checks:**
- [ ] Transfer to Villa confirmed/completed?
- [ ] Expected to start immediately?
- [ ] Emery's system suits his style?
- [ ] Competition for places?

---

## ⚡ **Red Flag Indicators**

### **Immediate Avoid Signals:**
- 🚫 "Doubt" or "major doubt" in injury reports
- 🚫 Less than 45 minutes in last 3 appearances  
- 🚫 Manager quotes about "rotation" or "competition"
- 🚫 New signing in same position arriving
- 🚫 Disciplinary issues or training ground problems

### **Caution Signals:**
- ⚠️ Just returned from injury in last 2 weeks
- ⚠️ Less than 60 minutes per game on average
- ⚠️ Hasn't scored/assisted in last 5 games
- ⚠️ Playing for team with new manager/system

---

## 🔧 **Quick Research Sources**

### **Reliable Information:**
1. **BBC Sport** - Injury updates, team news
2. **Sky Sports** - Press conference quotes
3. **Team Official Sites** - Training updates, lineup hints  
4. **Fantasy Premier League** - Official injury flags
5. **Premier League App** - Minutes played stats

### **Manager Press Conferences:**
- Usually 2 days before matches
- Look for lineup hints and injury updates
- Pay attention to "we'll assess" = rotation risk

---

## 📱 **30-Second Gem Validation**

### **Quick Google Search Template:**
```
"[Player Name] injury" site:bbc.com
"[Player Name] starting" site:skysports.com  
"[Player Name] minutes played" 2024
"[Team Name] team news" Game Week 1
```

### **Fantasy App Quick Check:**
- Open official Fantasy Premier League app
- Search player name
- Check for red/orange injury flag
- Look at "selected by %" vs our data

---

## 🎯 **Game Week 1 Action Plan**

### **Tonight (August 14):**
1. **Validate top 5 gems** using 30-second method
2. **Flag any obvious risks** (injury doubts, rotation)
3. **Prepare backup options** for flagged players

### **Tomorrow Morning:**
1. **Check final team news** (usually released 75 mins before kickoff)
2. **Make last-minute swaps** if needed
3. **Confirm no late injury withdrawals**

---

## 🚀 **Future System Improvements**

### **Phase 2 Automation Goals:**
- Auto-scrape injury reports from BBC/Sky
- Minutes played analysis from FPL API
- Starting XI prediction models
- Manager quotes sentiment analysis
- Team news alert system

### **Technical Implementation:**
```python
# Future gem validation function
def validate_gem(player):
    checks = {
        'minutes_per_game': get_recent_minutes(player),
        'injury_status': check_injury_reports(player),
        'starting_frequency': calculate_starts_vs_subs(player),
        'recent_form': get_last_5_games(player)
    }
    return risk_assessment(checks)
```

---

**Remember**: Better to miss a gem than pick an injured/benched player!  
**Manual validation takes 2 minutes per player but could save your entire Game Week.**