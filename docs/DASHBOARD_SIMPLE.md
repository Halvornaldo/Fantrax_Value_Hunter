# Simple Dashboard Specification
**Date**: August 14, 2025  
**Purpose**: Streamlined web dashboard for fantasy decision making

---

## 🎯 **Simple Dashboard Requirements**

### **Core Features** 
- **Player Table**: Sortable list of all 633 players
- **Basic Filters**: Position, price range, ownership %
- **Lineup Builder**: Simple 11-player selection
- **Budget Tracker**: Shows remaining money

### **Layout: Single Page**
```
┌─────────────────────────────────────────────────────┐
│ FANTRAX VALUE HUNTER                                │
├─────────────────────────────────────────────────────┤
│ Filters: [G][D][M][F] Price: $5-$25 Own: <50%     │
├─────────────────────────────────────────────────────┤
│ PLAYER TABLE           │ MY LINEUP                  │
│ Name | Team | Pos |$   │ Budget: $67 / $100        │
│ Haaland MCI F $22.50   │ [Formation View]          │
│ Salah LIV M $19.75     │ GK: [Select]              │
│ ...sortable...         │ DEF: [4 slots]            │
│                        │ MID: [4 slots]            │
│                        │ FWD: [2 slots]            │
└─────────────────────────────────────────────────────┘
```

### **Technology: Plotly Dash** 
- **Python-based**: Matches existing stack
- **Built-in tables**: DataTable component
- **Simple deployment**: Single file app
- **No mobile responsive**: Desktop only

---

## 🔧 **Implementation Plan**

### **Phase 1: Basic Table** (Week 2)
- [ ] Display all players in sortable table
- [ ] Add position/price filters
- [ ] Calculate and show value ratios

### **Phase 2: Lineup Builder** (Week 3)  
- [ ] Click to add players to lineup
- [ ] Budget validation
- [ ] Export lineup feature

### **Phase 3: Polish** (Week 4)
- [ ] Better styling
- [ ] Data refresh button
- [ ] Save/load lineups

**Keep it simple - function over form!**