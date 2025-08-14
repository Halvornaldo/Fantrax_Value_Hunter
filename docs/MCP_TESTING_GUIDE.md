# MCP Testing Guide - Fantrax Value Hunter
**Date**: August 14, 2025  
**Purpose**: Leverage MCP tools for comprehensive testing and validation

---

## 🧪 **Available MCP Tools**

### **✅ Connected MCP Servers**
```
anyquery: ✓ SQL queries against various data sources
database: ✓ PostgreSQL database operations
context7: ✓ Up-to-date library documentation  
memory: ✓ Knowledge graph for data patterns
playwright: ✓ Web browser automation and testing
github: ✓ Repository management and CI/CD
filesystem: ✓ File operations and data management
```

---

## 📊 **Phase 2: Value Engine Testing**

### **Database MCP Testing**
```sql
-- Create test dataset in PostgreSQL
CREATE TABLE player_test_data (
    name VARCHAR(100),
    position VARCHAR(10),
    salary DECIMAL(6,2),
    season_points DECIMAL(6,2),
    games_played INTEGER,
    expected_ppg DECIMAL(6,2)
);

-- Insert known test cases
INSERT INTO player_test_data VALUES
('Haaland', 'F', 22.50, 180.5, 25, 7.22),
('Salah', 'M', 19.75, 165.3, 30, 5.51),
('Injured_Player', 'D', 5.00, 12.0, 3, 4.00);

-- Validate our calculations
SELECT 
    name,
    season_points / games_played as calculated_ppg,
    expected_ppg,
    ABS((season_points / games_played) - expected_ppg) as error
FROM player_test_data;
```

### **Filesystem MCP Caching**
```python
# Use filesystem MCP to cache test results
test_results = {
    'timestamp': '2025-08-14T20:00:00Z',
    'value_engine_tests': {
        'ppg_accuracy': 0.98,
        'test_cases_passed': 47,
        'test_cases_failed': 3
    }
}

# Cache results for comparison
filesystem.write('data/test_results.json', json.dumps(test_results))
```

### **Memory MCP Pattern Storage**
```python
# Store known player patterns in memory MCP
memory.create_entities([
    {
        'name': 'Haaland_Pattern',
        'entityType': 'PlayerArchetype', 
        'observations': [
            'High salary premium striker',
            'Consistent goal scorer',  
            'Rarely rotated when fit'
        ]
    }
])

# Create relationships
memory.create_relations([
    {
        'from': 'Haaland',
        'to': 'High_Value_Striker',
        'relationType': 'exemplifies'
    }
])
```

---

## 🌐 **Phase 2: Web Scraping Validation**

### **Playwright MCP Testing**
```python
# Test injury report scraping accuracy
def test_injury_scraping():
    # Navigate to BBC Sport injuries page
    playwright.navigate('https://www.bbc.co.uk/sport/football/premier-league/injuries')
    
    # Take snapshot for debugging
    playwright.take_screenshot('injury_page_test.png')
    
    # Test scraping logic
    injuries = playwright.evaluate('''
        () => {
            const players = document.querySelectorAll('.injury-list .player');
            return Array.from(players).map(p => ({
                name: p.querySelector('.name').textContent,
                status: p.querySelector('.status').textContent
            }));
        }
    ''')
    
    # Validate we got reasonable data
    assert len(injuries) > 0, "No injuries scraped"
    assert all('name' in injury for injury in injuries), "Missing names"
```

### **Context7 MCP Documentation**
```python
# Get latest API documentation for validation
context7_docs = context7.get_library_docs(
    context7CompatibleLibraryID='/premier-league/api',
    topic='player statistics'
)

# Use for validating our data structure matches official format
```

---

## 📱 **Phase 3: Dashboard Testing**  

### **Playwright UI Testing**
```python
def test_dashboard_functionality():
    # Start dashboard
    playwright.navigate('http://localhost:8050')  # Dash default port
    
    # Test player table loading
    playwright.wait_for('table[id="player-table"]')
    
    # Test filtering
    playwright.click('[data-testid="filter-position-F"]')
    players = playwright.evaluate('() => document.querySelectorAll("tbody tr").length')
    assert players > 0, "No forwards found after filtering"
    
    # Test lineup builder
    playwright.drag(
        startElement='first player row',
        startRef='tr[data-position="F"]:first-child',
        endElement='lineup forward slot',
        endRef='[data-lineup-position="F1"]'
    )
    
    # Validate budget updates
    budget = playwright.evaluate('() => document.querySelector("#budget-remaining").textContent')
    assert '$' in budget, "Budget not updating"
```

### **Database Integration Testing**
```sql
-- Test dashboard data accuracy
WITH dashboard_data AS (
    SELECT name, position, salary FROM fantrax_players  
),
live_data AS (
    SELECT name, position, salary FROM current_api_fetch
)
SELECT 
    COUNT(*) as mismatches
FROM dashboard_data d
FULL OUTER JOIN live_data l USING (name)
WHERE d.salary != l.salary OR d.position != l.position;

-- Should return 0 mismatches
```

---

## 🔍 **Anyquery MCP Advanced Testing**

### **Cross-Platform Data Validation**
```sql
-- Use anyquery to validate against multiple sources
SELECT 
    f.name as fantrax_name,
    f.salary as fantrax_salary,
    p.name as premierleague_name,
    p.team as official_team
FROM fantrax_data f
JOIN premier_league_api('current_players') p 
ON LOWER(f.name) = LOWER(p.name)
WHERE f.team != p.team;  -- Flag discrepancies
```

---

## 📋 **Testing Workflow by Phase**

### **Phase 2 Testing Checklist**
- [ ] **Setup Test Database**: Create PostgreSQL test schema
- [ ] **Load Reference Data**: Known player stats for validation  
- [ ] **Test Value Calculations**: PPG vs season total accuracy
- [ ] **Web Scraping Validation**: Injury reports, team news
- [ ] **Cache Test Results**: Store benchmarks for regression testing

### **Phase 3 Testing Checklist**  
- [ ] **UI Component Tests**: Table, filters, lineup builder
- [ ] **Data Integrity Tests**: Dashboard vs source data
- [ ] **Performance Benchmarks**: Load time with 633 players
- [ ] **Cross-browser Testing**: Chrome, Firefox, Edge
- [ ] **Regression Testing**: Ensure Phase 2 features still work

### **Continuous Testing**
- [ ] **Weekly Data Validation**: Compare predictions vs actual results
- [ ] **API Health Checks**: Monitor Fantrax connection
- [ ] **Performance Monitoring**: Dashboard response times
- [ ] **User Acceptance**: Does it solve the core problem?

---

## 🚨 **Testing Red Flags**

### **Stop Development If:**
- Database accuracy tests fail (>5% error rate)
- Web scraping returns no data for 3+ consecutive attempts
- Dashboard loads take >10 seconds with full dataset
- Value calculations differ by >10% from manual verification

### **Investigation Required If:**
- Test pass rate drops below 90%
- Performance degrades >20% between releases
- New features break existing functionality
- User workflow takes >5 minutes for lineup creation

---

## 📊 **Test Reporting Template**

```json
{
    "test_run": {
        "timestamp": "2025-08-14T20:00:00Z",
        "phase": "Phase 2 - Value Engine",
        "environment": "development",
        "results": {
            "value_engine": {
                "ppg_calculation": "PASS - 98% accuracy",
                "constraint_validation": "PASS - all tests",
                "edge_case_handling": "PASS - 45/47 cases"
            },
            "web_scraping": {
                "injury_reports": "PASS - BBC/Sky scraped",
                "team_news": "FAIL - timeout issues",
                "fixture_odds": "PASS - OddsChecker working"
            },
            "performance": {
                "data_fetch_time": "2.3 seconds",
                "processing_time": "0.8 seconds", 
                "total_time": "3.1 seconds"
            }
        },
        "overall": "PASS with minor issues"
    }
}
```

---

**With MCP-enhanced testing, we can build bulletproof features! 🧪✅**