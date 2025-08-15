# API Configuration Guide
**Fantrax Value Hunter - External API Integration**

## 🔑 API Keys Setup

### **Football-Data.org API**
**Purpose**: Real Premier League standings for fixture difficulty calculations

#### **1. Get Your API Key**
1. Visit [football-data.org](https://www.football-data.org/client/register)
2. Register for free tier account (10 requests/minute)
3. Copy your API key from the dashboard

#### **2. Configure API Key**
Create `config/api_keys.json`:
```json
{
  "description": "API keys for external services",
  "football_data_org": "YOUR_API_KEY_HERE",
  "notes": {
    "football_data_org": "Get free API key from https://www.football-data.org/client/register",
    "free_tier": "10 requests per minute, sufficient for our needs",
    "alternative": "Set FOOTBALL_DATA_API_KEY environment variable instead"
  }
}
```

#### **3. Alternative: Environment Variable**
```bash
# Windows
set FOOTBALL_DATA_API_KEY=your_api_key_here

# Linux/Mac
export FOOTBALL_DATA_API_KEY=your_api_key_here
```

#### **4. Test API Connection**
```bash
cd src/
python fixture_difficulty.py
```

**Expected Output:**
- `Calculated ranks for 20 teams`
- Real multiplier values for test teams (MCI: 0.85x, ARS: 1.3x, etc.)

---

## 🍪 Fantrax Authentication

### **1. Export Browser Cookies**
See `../Fantrax_Wrapper/WRAPPER_SUMMARY.md` for detailed guide.

**Quick Steps:**
1. Login to Fantrax in your browser
2. Navigate to your league (`gjbogdx2mcmcvzqa`)
3. Export cookies using browser extension
4. Save as `config/fantrax_cookies.json`

### **2. Test Fantrax Connection**
```bash
cd src/
python candidate_analyzer.py
```

**Expected Output:**
- `[SUCCESS] Authentication successful`
- `Retrieved 633+ total players`
- Complete candidate pool analysis

---

## 📊 API Rate Limits & Caching

### **Football-Data.org Limits**
- **Free Tier**: 10 requests per minute
- **Daily Limit**: None specified
- **Our Usage**: ~5 requests per day (well within limits)

### **Automatic Caching**
All APIs implement intelligent caching:

**Fixture Difficulty Cache:**
- **Location**: `data/fixture_difficulty_cache.json`
- **Duration**: 24 hours (refreshes daily)
- **Triggers**: Automatic refresh when data expires

**Starter Predictions Cache:**
- **Location**: `data/starter_predictions_cache.json`
- **Duration**: 6 hours (refreshes twice daily)
- **Triggers**: Before each game week analysis

### **Manual Cache Management**
```bash
# Clear all caches
rm data/*_cache.json

# View cache status
python -c "from src.fixture_difficulty import FixtureDifficultyAnalyzer; print(FixtureDifficultyAnalyzer().get_multiplier_summary())"
```

---

## 🔧 Configuration Management

### **System Parameters**
All API behavior controlled via `config/system_parameters.json`:

```json
{
  "fixture_difficulty": {
    "enabled": true,
    "api_source": "football-data.org",
    "update_frequency_hours": 24,
    "5_tier_multipliers": {
      "very_easy": {"multiplier": 1.3},
      "easy": {"multiplier": 1.15},
      "neutral": {"multiplier": 1.0},
      "hard": {"multiplier": 0.85},
      "very_hard": {"multiplier": 0.7}
    }
  },
  "starter_prediction": {
    "enabled": true,
    "update_frequency_hours": 6,
    "data_sources": ["Fantasy Football Scout", "RotoWire"],
    "multipliers": {
      "both_sources_agree": {"multiplier": 1.15},
      "single_source": {"multiplier": 1.0},
      "conflicting_sources": {"multiplier": 0.9}
    }
  }
}
```

### **Runtime Parameter Changes**
All parameters take effect immediately - no restart required:

```python
# Disable fixture difficulty
analyzer = FixtureDifficultyAnalyzer()
analyzer.config['enabled'] = False

# Adjust multipliers
analyzer.config['5_tier_multipliers']['very_easy']['multiplier'] = 1.4
```

---

## 🚨 Error Handling & Fallbacks

### **API Failure Scenarios**

#### **Football-Data.org API Down**
1. **Primary**: Use cached standings data (up to 24 hours old)
2. **Fallback**: Neutral multipliers (1.0x for all fixtures)
3. **Logging**: Warning logged, analysis continues

```python
# Example error handling
try:
    multiplier = analyzer.get_fixture_multiplier('MCI')
except APIError:
    multiplier = 1.0  # Neutral fallback
    logger.warning("Using neutral multiplier due to API error")
```

#### **Rate Limit Exceeded**
1. **Detection**: HTTP 429 response code
2. **Action**: Use cached data instead of new request
3. **Retry**: Automatic retry after cool-down period

#### **Invalid API Key**
1. **Detection**: HTTP 403 response code
2. **Action**: Log error, continue with cached data
3. **Alert**: Clear error message for user

### **Fantrax Authentication Issues**

#### **Expired Cookies**
1. **Detection**: Authentication failure during API calls
2. **Action**: Log clear error message with instructions
3. **Resolution**: Re-export cookies from browser

#### **Session Timeout**
1. **Detection**: Mid-session authentication failure
2. **Action**: Retry once, then fail gracefully
3. **Fallback**: Use cached player data if available

---

## 🔍 Debugging & Monitoring

### **API Health Checks**
```bash
# Test all API connections
python -c "
from src.fixture_difficulty import FixtureDifficultyAnalyzer
from src.candidate_analyzer import CandidateAnalyzer

# Test Football-Data.org
try:
    analyzer = FixtureDifficultyAnalyzer()
    ranks = analyzer.calculate_team_difficulty_ranks()
    print(f'✅ Football-Data.org: {len(ranks)} teams loaded')
except Exception as e:
    print(f'❌ Football-Data.org: {e}')

# Test Fantrax
try:
    candidate = CandidateAnalyzer()
    if candidate.authenticate():
        print('✅ Fantrax: Authentication successful')
    else:
        print('❌ Fantrax: Authentication failed')
except Exception as e:
    print(f'❌ Fantrax: {e}')
"
```

### **Debug Logging**
Enable detailed API logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# All API requests and responses logged
analyzer = FixtureDifficultyAnalyzer()
```

### **Response Validation**
All API responses validated for data integrity:

```python
# Automatic validation examples
def validate_standings(data):
    assert len(data) == 20, "Premier League has 20 teams"
    assert all('position' in team for team in data), "Missing position data"
    assert all(1 <= team['position'] <= 20 for team in data), "Invalid positions"

def validate_player_data(players):
    assert len(players) >= 600, "Should have 600+ players"
    assert all('scorer' in player for player in players), "Missing scorer data"
```

---

## 📈 Performance Optimization

### **Request Batching**
Minimize API calls through intelligent batching:

```python
# Single request gets all team data
standings = fetch_team_standings()  # One API call
difficulty_ranks = calculate_all_difficulties(standings)  # No additional calls

# vs inefficient approach
for team in teams:
    difficulty = get_team_difficulty(team)  # 20 API calls!
```

### **Smart Caching Strategy**
1. **Cache on Success**: Only cache successful, complete responses
2. **Validate on Load**: Check cache integrity before use
3. **Background Refresh**: Update cache during low-usage periods
4. **Graceful Degradation**: Continue with stale data if new request fails

### **Connection Pooling**
Reuse HTTP connections for multiple requests:

```python
import requests

# Efficient: Reuse session
session = requests.Session()
for endpoint in endpoints:
    response = session.get(endpoint)  # Reuses connection

# Inefficient: New connection each time
for endpoint in endpoints:
    response = requests.get(endpoint)  # New connection overhead
```

---

## 🛡️ Security Best Practices

### **API Key Protection**
1. **Never commit**: `api_keys.json` in `.gitignore`
2. **Environment variables**: Alternative to file storage
3. **Rotation**: Regularly regenerate API keys
4. **Monitoring**: Log API key usage and errors

### **Request Security**
1. **HTTPS Only**: All API requests use SSL/TLS
2. **User-Agent**: Identify requests with proper user agent
3. **Rate Limiting**: Respect API provider limits
4. **Error Handling**: Don't expose sensitive data in logs

### **Data Privacy**
1. **Local Storage**: All cached data stored locally
2. **No Transmission**: Player data never sent to external services
3. **Minimal Requests**: Only request necessary data
4. **Audit Trail**: Log all API access for monitoring

---

## 📋 API Integration Checklist

### **Initial Setup**
- [ ] Football-Data.org API key obtained and configured
- [ ] Fantrax cookies exported and working
- [ ] All test commands pass successfully
- [ ] Cache directories created and writable

### **Before Each Game Week**
- [ ] Test API connections
- [ ] Clear expired caches if needed
- [ ] Verify all multipliers are current
- [ ] Check for any API provider changes

### **Monthly Maintenance**
- [ ] Review API usage logs
- [ ] Update API keys if needed
- [ ] Check for new API features
- [ ] Validate cache performance

### **Troubleshooting Steps**
1. **Check API keys**: Verify format and validity
2. **Test network**: Ensure internet connectivity
3. **Clear caches**: Force fresh data retrieval
4. **Check logs**: Review error messages
5. **Verify configuration**: Confirm all settings correct

---

**Last Updated**: August 15, 2025
**Next Review**: Phase 3 Dashboard Implementation