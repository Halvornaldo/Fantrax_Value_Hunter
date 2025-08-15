# Fantrax Value Hunter - Version 1.0 Specification
**Clear Definition of MVP Features**

This document defines exactly what constitutes Version 1.0 of the Fantrax Value Hunter. **No additional features should be implemented** until v1.0 is complete and working perfectly.

---

## 🎯 **Version 1.0 Mission Statement**

Build a **two-panel Flask dashboard** that enables real-time parameter tuning to discover the best value players from all 633 Premier League players.

**Core Value Proposition**: Parameter adjustment is the primary feature. Users can modify boost factors and see immediate impact on True Value rankings across the entire player database.

---

## ✅ **In Scope for Version 1.0**

### **Database Foundation**
- ✅ PostgreSQL database with 633 players
- ✅ Player metadata (name, team, position, price, PPG)
- ✅ True Value calculations: `(PPG ÷ Price) × Form × Fixture × Starter`
- ✅ All multipliers stored and adjustable

### **Two-Panel Dashboard**

#### **Left Panel - Parameter Controls**
**Form Calculation Section:**
- Enable/disable toggle
- Lookback period dropdown (3 or 5 games)
- Minimum games threshold (number input)
- **CRITICAL**: Requires player_form table with up to 5 gameweeks of historical points data per player

**Fixture Difficulty Section:**
- Enable/disable toggle
- Mode selector (3-tier vs 5-tier radio buttons)
- Multiplier sliders for each difficulty level:
  - Very Easy: 1.2x - 1.5x
  - Easy: 1.05x - 1.25x  
  - Hard: 0.75x - 0.95x
  - Very Hard: 0.6x - 0.8x

**Starter Predictions Section:**
- Enable/disable toggle
- Single-source penalty-based approach (Fantasy Football Scout via CSV import)
- Dashboard parameter sliders:
  - Auto rotation penalty: 0.5x - 0.8x (default 0.65x) - applied to non-starters from CSV
  - Force bench penalty: 0.4x - 0.8x (default 0.6x) - for manual player overrides
- **Per-player manual overrides** (3-checkbox system):
  - ☐ Force Starter (1.0x)
  - ☐ Force Bench (uses dashboard slider value)  
  - ☐ Force Out (0.0x - suspended/injured)
- **Logic**: CSV identifies 220 starters (stay at 1.0x), others get rotation penalty (0.65x), manual overrides available

**Display Filters Section:**
- Position checkboxes (G, D, M, F)
- Price range slider ($5.00 - $25.00)
- Ownership percentage threshold
- Team multi-select dropdown
- Player name search box

**Action Buttons:**
- [Import Lineups CSV] - Upload starter predictions
- [Apply Changes] - Recalculate True Values with new parameters
- [Reset to Defaults] - Restore original multipliers

#### **Right Panel - Player Table**
**Display All 633 Players:**
- Show ALL players that match display filters (not limited to top 68)
- Sortable columns: Name, Team, Position, Price, PPG, True Value, Ownership%
- Pagination (50-100 players per page for performance)
- Clear indicators of data source (Historical vs Estimated)

**Table Features:**
- Click column headers to sort ascending/descending
- Visual indicators for multiplier impact (color coding)
- Export filtered results to CSV
- Row highlighting for easy reading

### **Core Functionality**
1. **Parameter Adjustment**: Any multiplier change triggers True Value recalculation for all 633 players
2. **Real-time Updates**: Player rankings change immediately when parameters are modified
3. **Filtering**: Users can narrow down the 633 players using display filters
4. **Export**: Save filtered player lists for external use
5. **CSV Import**: Upload weekly starter predictions to update starter multipliers

### **Technical Requirements**
- **Backend**: Flask with PostgreSQL integration
- **Frontend**: HTML/CSS/JavaScript (no complex frameworks)
- **Performance**: Handle 633 players smoothly (< 2 second response times)
- **Data**: All 633 players with complete metrics for gameweek 1

---

## ❌ **Explicitly Out of Scope for Version 1.0**

### **Automatic Features**
- ❌ Auto-selection of "best" lineup
- ❌ Automatic optimization algorithms
- ❌ AI-powered recommendations

### **Complex UI Features**
- ❌ Drag-and-drop lineup builder
- ❌ Interactive formation diagrams
- ❌ Complex visualizations or charts

### **Advanced Integrations**
- ❌ Real-time web scraping (Playwright)
- ❌ Live data feeds
- ❌ Third-party API integrations (beyond existing fixture data)

### **Management Features**
- ❌ User accounts or authentication
- ❌ Saved configurations or favorites
- ❌ Historical performance tracking
- ❌ Price change monitoring

### **Export Features**
- ❌ Direct Fantrax submission
- ❌ Multiple export formats
- ❌ Automated lineup generation

---

## 🎯 **Success Criteria for Version 1.0**

### **Functional Requirements**
1. **Parameter Controls Work**: Every slider/toggle must trigger accurate True Value recalculation
2. **All 633 Players Displayed**: Users can see complete player database with filters
3. **Performance Acceptable**: Page loads and parameter changes complete within 2 seconds
4. **Export Functions**: Users can export filtered player lists to CSV
5. **CSV Import Works**: Starter prediction uploads correctly update multipliers

### **User Experience Requirements**
1. **Intuitive Controls**: Parameter adjustments are obvious and responsive
2. **Clear Data Sources**: Users can distinguish Historical vs Estimated data
3. **Effective Filtering**: Users can quickly narrow down to relevant players
4. **Reliable Calculations**: True Value changes are mathematically correct

### **Technical Requirements**
1. **Database Stability**: 633 players load reliably without errors
2. **Calculation Accuracy**: All multiplier math produces correct results
3. **UI Responsiveness**: Dashboard works smoothly on desktop browsers
4. **Data Integrity**: Parameter changes don't corrupt underlying data

---

## 📋 **Implementation Phases**

### **Phase 1: Backend (Days 2-3)**
- Flask application with parameter adjustment endpoints
- Database queries for all 633 players with filters
- True Value recalculation logic
- CSV import processing

### **Phase 2: Frontend (Days 4-5)**
- Two-panel dashboard layout
- All parameter control UI elements
- Player table with sorting and pagination
- JavaScript for real-time parameter updates

### **Phase 3: Integration (Days 6-7)**
- CSV import functionality
- Parameter persistence
- Export features
- Error handling and validation

### **Phase 4: Testing (Day 8)**
- Verify all parameter combinations work correctly
- Test with full 633 player dataset
- Validate calculation accuracy
- Performance optimization

---

## 🚀 **Version 1.0 Definition of Done**

Version 1.0 is complete when:

1. ✅ All 633 players display correctly with accurate True Value calculations
2. ✅ Every parameter control triggers correct recalculation
3. ✅ Filtering works smoothly to narrow player selection
4. ✅ CSV import updates starter predictions successfully
5. ✅ Export functionality saves filtered results
6. ✅ Dashboard performs acceptably with full dataset
7. ✅ All calculations are mathematically verified
8. ✅ Documentation is complete and accurate

**Version 1.0 delivers a working parameter tuning dashboard for value discovery across all 633 Premier League players.**

---

## 🔒 **Scope Protection**

This specification serves as a **scope boundary**. Any features not explicitly listed in the "In Scope" section should be **deferred to future versions**.

**For AI Assistants**: Do not implement any features from the "Out of Scope" section, regardless of how beneficial they might seem. Focus exclusively on delivering the specified v1.0 features perfectly.

**For Developers**: Resist feature creep. Version 1.0 success is measured by parameter tuning quality, not feature quantity.

---

**Version 1.0: Parameter tuning excellence for value discovery 🎯**