# Sprint 0: Comprehensive Gameweek Audit Results
## Fantasy Football Value Hunter - Gameweek Unification Implementation

**Date**: 2025-08-23  
**Audit Scope**: Complete codebase scan for gameweek references  
**Files Analyzed**: 19 Python files with gameweek usage

---

## **Executive Summary**

**CRITICAL FINDING**: Found **19 files** with inconsistent gameweek handling, confirming the need for GameweekManager unification.

**Key Patterns Discovered**:
- **5 files** using `MAX(gameweek)` detection (inconsistent results)
- **11 files** with hardcoded `gameweek = 1` references (will become outdated)
- **Multiple functions** defaulting to GW1 without validation
- **API endpoints** with manual gameweek input (dangerous)

---

## **HIGH-PRIORITY FIXES REQUIRED**

### **🚨 CRITICAL: API Endpoints with Hardcoded GW1**

#### `src/app.py` - Multiple Critical Issues:
- **Line 402**: `/api/players` - **DASHBOARD ENDPOINT** defaults to `gameweek=1`
  ```python
  gameweek = request.args.get('gameweek', 1, type=int)  # WRONG!
  ```
  **Impact**: Main dashboard stuck showing GW1 data instead of current

- **Line 249**: `recalculate_true_values(gameweek: int = 1)` - **CALCULATION FUNCTION**
  **Impact**: Default recalculations process wrong gameweek

- **Line 692**: Manual override function defaults to GW1
  **Impact**: Admin functions may process wrong gameweek

### **🚨 CRITICAL: MAX(gameweek) Detection Issues**

#### `calculation_engine_v2.py` - V2.0 Enhanced Formula:
- **Line 438**: Core calculation engine uses `MAX(gameweek)`
  ```python
  cursor.execute('SELECT MAX(gameweek) FROM player_metrics WHERE gameweek IS NOT NULL')
  ```
  **Impact**: Returns GW3 instead of correct GW2 (proven by our test case)

#### `src/app.py`:
- **Line 728**: Manual override functionality
  **Impact**: Inconsistent with dashboard display

### **🚨 CRITICAL: Data Import Functions**

#### Already Protected:
- ✅ **Line 1646**: Form import now has emergency protection

#### Still Vulnerable:
- **Line 1062**: `/api/import-lineups` defaults to `gameweek = 1`
- **Line 1188**: `/api/export` defaults to GW1

---

## **MEDIUM-PRIORITY FIXES**

### **Validation Scripts** (6 files):
- `verify_import.py` - Multiple GW1 hardcoded queries
- `check_db_structure.py` - Uses MAX(gameweek) for analysis
- `fantasy_validation.py` - Hardcoded gameweek ranges
- `fantasy_validation_simple.py` - GW1 assumptions
- `validation_engine.py` - Multiple hardcoded defaults
- `validation_pipeline.py` - Range validation functions

### **Migration Scripts** (2 files):
- `migrations/import_csv_data.py` - Hardcoded GW1 assumptions
- `import_2024_25_games.py` - Historical data import

---

## **TREND ANALYSIS SYSTEM** (Separate Architecture)

### **Files Using Raw Data Snapshots** (3 files):
- `src/trend_analysis_engine.py` - Uses `MAX(gameweek)` from raw_player_snapshots
- `src/trend_analysis_endpoints.py` - API endpoints for trend analysis
- `src/trend_analysis_engine_simple.py` - Simplified trend calculations

**Note**: These should remain separate from main dashboard but use GameweekManager for consistency

---

## **COMPLETE FILE INVENTORY**

### **Files by Priority Level:**

#### **🔴 HIGH PRIORITY** (Must fix in Sprint 1-2):
1. `src/app.py` - **4 critical functions** (dashboard, recalculation, export, import)
2. `calculation_engine_v2.py` - **Core V2.0 engine** (1 critical function)

#### **🟡 MEDIUM PRIORITY** (Fix in Sprint 3-5):
3. `verify_import.py` - Validation queries
4. `check_db_structure.py` - Analysis queries  
5. `fantasy_validation.py` - Validation framework
6. `fantasy_validation_simple.py` - Simple validation
7. `validation_engine.py` - Engine validation
8. `validation_pipeline.py` - Pipeline validation
9. `migrations/import_csv_data.py` - Migration script
10. `import_2024_25_games.py` - Historical import

#### **🟢 LOW PRIORITY** (Fix in Sprint 5-6):
11. `check_games.py` - Analysis script
12. `create_games_table.py` - Table creation
13. `src/candidate_analyzer.py` - Analysis functions
14. `src/convert_ffs_csv.py` - CSV conversion
15. `src/db_manager.py` - Database management
16. `src/fixture_difficulty.py` - Fixture calculations
17. `src/form_tracker.py` - Form tracking

#### **🔵 SEPARATE SYSTEM** (Maintain independence):
18. `src/trend_analysis_engine.py` - Trend analysis
19. `src/trend_analysis_endpoints.py` - Trend API

---

## **GAMEWEEK USAGE PATTERNS IDENTIFIED**

### **Pattern 1: Hardcoded Defaults**
```python
gameweek = request.args.get('gameweek', 1, type=int)  # Will become outdated
def function_name(gameweek: int = 1):  # Static assumption
```
**Files**: 11 files  
**Risk**: High - Will show wrong data as season progresses

### **Pattern 2: MAX(gameweek) Detection**
```python
cursor.execute('SELECT MAX(gameweek) FROM player_metrics WHERE gameweek IS NOT NULL')
```
**Files**: 5 files  
**Risk**: High - Returns wrong results (GW3 instead of GW2 proven)

### **Pattern 3: Range-Based Functions**
```python
for gameweek in range(1, 15):  # Fixed ranges
gameweek_range: Tuple[int, int] = (1, 15)  # Static ranges
```
**Files**: 6 files  
**Risk**: Medium - May process wrong gameweek ranges

### **Pattern 4: Manual User Input**
```python
gameweek = request.form.get('gameweek')  # User can input anything
```
**Files**: 3 files (1 now protected)  
**Risk**: High - User error can corrupt data

---

## **DEPENDENCY ANALYSIS**

### **Critical Data Flow Chain:**
1. **Data Import** → `player_metrics` table → **Dashboard Display**
2. **Dashboard Query** → `calculation_engine_v2.py` → **User Interface**
3. **Manual Uploads** → **Database Updates** → **System State**

### **Failure Points Identified:**
- **Import functions** can write to wrong gameweek
- **Dashboard** can display wrong gameweek  
- **Calculations** can process wrong gameweek data
- **Exports** can extract wrong gameweek data

---

## **REAL-WORLD VALIDATION**

### **GW3 Anomaly Case Study:**
- **Problem**: 5 records uploaded to GW3 when should be GW2
- **Root Cause**: User manually entered "3" in form upload
- **System Response**: `MAX(gameweek)` now returns 3 (wrong)
- **GameweekManager Solution**: ✅ Detects anomaly, returns 2 (correct)

### **Success Metrics:**
- ✅ **Emergency protection working**: GW1 uploads blocked
- ✅ **Smart detection working**: GW2 detected instead of anomalous GW3
- ✅ **Validation working**: Future gameweeks properly handled

---

## **SPRINT IMPLEMENTATION PRIORITIES**

### **Sprint 1: Foundation** 
- ✅ GameweekManager core functionality (COMPLETE)
- 🎯 **Next**: Update `/api/players` (src/app.py:402) - **CRITICAL DASHBOARD**

### **Sprint 2: Critical Functions**
- Update `calculation_engine_v2.py` (Line 438)
- Update `/api/export` (src/app.py:1188)
- Update `/api/import-lineups` (src/app.py:1062)

### **Sprint 3: High-Risk Imports**
- Complete import function security
- Add comprehensive validation

### **Sprint 4-5: Legacy Cleanup** 
- Update all 19 files systematically
- Remove hardcoded assumptions
- Replace MAX(gameweek) detection

---

## **TESTING REQUIREMENTS**

### **Test Scenarios Needed:**
1. **Empty database** → GameweekManager should return GW1
2. **GW1 data only** → Should return GW1
3. **GW1 + GW2 data** → Should return GW2
4. **Anomalous data** (like GW3) → Should detect and ignore
5. **Mixed table data** → Should handle inconsistencies

### **Integration Testing:**
- Dashboard displays correct gameweek
- Calculations use correct gameweek  
- Imports validate correctly
- Exports contain correct data

---

## **CONCLUSION**

**Sprint 0 Audit CONFIRMS the critical need for GameweekManager.**

**Key Findings:**
- ✅ **19 files** require gameweek unification
- ✅ **5 critical functions** must be fixed immediately  
- ✅ **Real-world validation** proves system works
- ✅ **Emergency protection** successfully prevents data loss

**Ready for Sprint 1 continuation** with clear priorities and comprehensive understanding of the codebase gameweek usage patterns.

---

**Next Steps**: Complete Sprint 0 with testing infrastructure, then proceed to Sprint 1 critical dashboard integration using this audit as the implementation roadmap.