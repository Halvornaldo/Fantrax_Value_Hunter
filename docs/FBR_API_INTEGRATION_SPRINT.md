# FBR API Integration Sprint Plan

## Overview

Integration plan for FBR API (Football Reference API) into Fantrax Value Hunter for enhanced player analytics and statistics.

**API Documentation**: https://fbrapi.com/documentation

## Executive Summary

**Status**: HIGHLY RECOMMENDED ✅  
**Feasibility**: Excellent match for existing architecture  
**Value Addition**: Transforms system from good to industry-leading  

### Key Benefits
- **13 Statistical Categories**: Complete player/team analytics
- **Premier League Coverage**: League ID 9 with full historical data  
- **Match-Level Granularity**: Individual game statistics for all 647+ players
- **Advanced Metrics**: xG, xA, progressive passes, shot-creating actions
- **Team Analytics**: Attacking/defensive strengths for fixture difficulty

## Current System Analysis

### Architecture Compatibility ✅
- **Database**: PostgreSQL ready for FBR table extensions
- **Backend**: Flask perfect for adding FBR endpoints
- **Name Matching**: Existing system can handle FBR player/team mapping
- **Parameters**: `config/system_parameters.json` ready for FBR multipliers

### Data Integration Points
```
True Value = PPG × Form × Fixture × Starter × xGI Multipliers
```

**Enhanced with FBR**:
- **Form**: Shot-creating actions, progressive passes, xG trends
- **Fixture**: Team xG/xGA, defensive actions, attacking patterns  
- **Starter**: Minutes trends, rotation patterns, performance metrics

## FBR API Key Endpoints

### Discovery Sequence
```
/countries → /leagues → /league-seasons → /player-season-stats
```

### Critical Endpoints for Integration
1. **`/countries`** - Get country metadata (find England)
2. **`/leagues`** - Get Premier League ID (league_id: 9)
3. **`/league-seasons`** - Get available seasons for Premier League
4. **`/player-season-stats`** - Season aggregates for all players
5. **`/player-match-stats`** - Match-by-match player statistics
6. **`/team-season-stats`** - Team performance for fixture difficulty
7. **`/all-players-match-stats`** - Complete match data for advanced analytics

### Authentication & Rate Limits
- **API Key**: POST to `/generate_api_key` (no parameters)
- **Rate Limit**: 3 seconds between requests (critical constraint)
- **Header**: `X-API-Key: YOUR_API_KEY`

## Implementation Challenges

### 1. Rate Limiting Impact
- **Data Volume**: 647 players × 38 matches = ~24,586 potential calls
- **Time Constraint**: 3-second intervals = ~20 hours for full season
- **Solution**: Batch processing with intelligent caching

### 2. Data Discovery Process
```python
# Required sequence to identify Premier League:
# 1. Find England in /countries
# 2. Get league_id 9 from /leagues  
# 3. Get current season_id from /league-seasons
# 4. Use in player/team endpoints
```

### 3. Name Matching Complexity
- **FBR Player IDs**: 8-character strings (`92e7e919`)
- **Mapping Challenge**: 647 existing players need FBR ID association
- **Team Names**: May differ (`Manchester Utd` vs `Man United`)

### 4. Data Volume Management
- **Storage**: ~15MB per gameweek for all players with full stats
- **Categories**: 13 statistical categories per player per match
- **Processing**: Cache strategy essential for performance

## Three-Phase Implementation Plan

### Phase 1: Foundation & Discovery (Week 1)
**Goal**: Establish FBR connection and basic data mapping

**Tasks**:
1. **API Setup**
   ```python
   # Add to config/api_keys.json
   {
     "fbr_api_key": "generated_key_here"
   }
   ```

2. **Discovery Script**
   ```python
   # experimental/fbr_discovery.py
   # - Generate API key
   # - Find Premier League ID
   # - Get current season
   # - Test basic endpoints
   ```

3. **Rate Limiter**
   ```python
   # experimental/fbr_client.py
   # - 3-second request spacing
   # - Request queue management
   # - Error handling
   ```

4. **Player Mapping**
   ```python
   # experimental/fbr_name_matching.py
   # - Map 647 existing players to FBR IDs
   # - Use existing name matching system
   # - Export mapping for validation
   ```

**Deliverables**:
- Working FBR API client
- Premier League discovery confirmed
- Player ID mapping file
- Rate limiting framework

### Phase 2: Data Integration & Testing (Week 2-3)
**Goal**: Import FBR data and enhance existing calculations

**Tasks**:
1. **Database Schema Extensions**
   ```sql
   CREATE TABLE experimental_fbr_player_stats (
       player_id VARCHAR(8),
       fbr_player_id VARCHAR(8),
       match_date DATE,
       goals INT,
       assists INT,
       xg DECIMAL,
       xag DECIMAL,
       shot_creating_actions INT,
       progressive_passes INT,
       -- 50+ additional metrics
   );
   
   CREATE TABLE experimental_fbr_team_stats (
       team_id VARCHAR(8),
       season_id VARCHAR(9),
       attacking_strength DECIMAL,
       defensive_strength DECIMAL,
       xg_per_90 DECIMAL,
       xga_per_90 DECIMAL
   );
   ```

2. **Data Import Scripts**
   ```python
   # experimental/import_season_stats.py
   # experimental/import_match_stats.py  
   # experimental/import_team_stats.py
   ```

3. **Enhanced Multiplier Calculations**
   ```python
   # experimental/fbr_form_calculator.py
   # experimental/fbr_fixture_difficulty.py
   # experimental/fbr_starter_predictor.py
   ```

4. **Testing & Validation**
   ```python
   # experimental/validate_fbr_data.py
   # experimental/compare_calculations.py
   ```

**Deliverables**:
- FBR data in experimental database tables
- Enhanced calculation algorithms
- Validation reports comparing old vs new
- Performance benchmarks

### Phase 3: Advanced Analytics & Integration (Week 4+)
**Goal**: Production-ready FBR integration with advanced features

**Tasks**:
1. **Advanced Analytics**
   ```python
   # experimental/match_prediction_models.py
   # experimental/team_style_analytics.py
   # experimental/player_form_trends.py
   ```

2. **Dashboard Integration**
   ```python
   # Add FBR parameters to config/system_parameters.json
   # Create FBR multiplier controls in dashboard
   # Add FBR data columns to player table
   ```

3. **Historical Data Backfill**
   ```python
   # experimental/historical_import.py
   # - Previous seasons data
   # - Performance trend analysis
   ```

4. **Production Migration**
   ```python
   # Move from experimental/ to main system
   # Update main database schema
   # Integrate into main Flask app
   ```

**Deliverables**:
- Production-ready FBR integration
- Enhanced True Value calculations
- Historical trend analysis
- Advanced prediction models

## Database Schema Extensions

### Core FBR Tables
```sql
-- Player match-level statistics (primary integration point)
CREATE TABLE fbr_player_match_stats (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(id),
    fbr_player_id VARCHAR(8) NOT NULL,
    match_id VARCHAR(8) NOT NULL,
    match_date DATE NOT NULL,
    
    -- Basic stats
    goals INT DEFAULT 0,
    assists INT DEFAULT 0,
    minutes_played INT DEFAULT 0,
    
    -- Advanced metrics
    xg DECIMAL(4,2) DEFAULT 0,
    xag DECIMAL(4,2) DEFAULT 0,
    shot_creating_actions INT DEFAULT 0,
    goal_creating_actions INT DEFAULT 0,
    progressive_passes INT DEFAULT 0,
    progressive_carries INT DEFAULT 0,
    
    -- Defensive stats
    tackles INT DEFAULT 0,
    interceptions INT DEFAULT 0,
    blocks INT DEFAULT 0,
    clearances INT DEFAULT 0,
    
    -- Possession stats
    touches INT DEFAULT 0,
    pass_completion_pct DECIMAL(5,2) DEFAULT 0,
    dribbles_completed INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team season statistics for fixture difficulty
CREATE TABLE fbr_team_stats (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    fbr_team_id VARCHAR(8) NOT NULL,
    season_id VARCHAR(9) NOT NULL,
    
    -- Attacking metrics
    goals_per_90 DECIMAL(4,2) DEFAULT 0,
    xg_per_90 DECIMAL(4,2) DEFAULT 0,
    shots_per_90 DECIMAL(4,2) DEFAULT 0,
    
    -- Defensive metrics  
    goals_against_per_90 DECIMAL(4,2) DEFAULT 0,
    xga_per_90 DECIMAL(4,2) DEFAULT 0,
    tackles_per_90 DECIMAL(4,2) DEFAULT 0,
    
    -- Overall strength indicators
    attacking_strength DECIMAL(4,2) DEFAULT 1.0,
    defensive_strength DECIMAL(4,2) DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player-to-FBR ID mapping table
CREATE TABLE fbr_player_mapping (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(id),
    fbr_player_id VARCHAR(8) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    fbr_player_name VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0,
    manually_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Client Implementation

### Core Client Structure
```python
# experimental/fbr_client.py
import requests
import time
from typing import Dict, List, Optional
import json

class FBRAPIClient:
    def __init__(self, api_key: str = None):
        self.base_url = "https://fbrapi.com"
        self.api_key = api_key
        self.last_request_time = 0
        self.rate_limit_seconds = 3
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make rate-limited request to FBR API"""
        # Enforce 3-second rate limit
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - time_since_last)
        
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
    
    def generate_api_key(self) -> str:
        """Generate new API key"""
        response = requests.post(f"{self.base_url}/generate_api_key")
        if response.status_code == 200:
            return response.json()['api_key']
        return None
    
    def get_countries(self) -> List[Dict]:
        """Get all countries"""
        return self._make_request("/countries")
    
    def get_leagues(self, country_code: str) -> List[Dict]:
        """Get leagues for country"""
        return self._make_request("/leagues", {"country_code": country_code})
    
    def get_player_season_stats(self, team_id: str, league_id: int, season_id: str = None) -> List[Dict]:
        """Get season stats for all players on team"""
        params = {"team_id": team_id, "league_id": league_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/player-season-stats", params)
    
    def get_player_match_stats(self, player_id: str, league_id: int, season_id: str = None) -> List[Dict]:
        """Get match-by-match stats for player"""
        params = {"player_id": player_id, "league_id": league_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/player-match-stats", params)
```

## Value Enhancement Opportunities

### 1. Enhanced Form Calculation
```python
# Current form calculation (basic PPG weighting)
def calculate_form_multiplier(recent_games):
    return weighted_average(recent_ppg)

# Enhanced with FBR data
def calculate_fbr_form_multiplier(recent_games, fbr_stats):
    form_components = {
        'scoring_form': trend_analysis(fbr_stats.xg, fbr_stats.goals),
        'creativity_form': trend_analysis(fbr_stats.shot_creating_actions),
        'involvement_form': trend_analysis(fbr_stats.touches, fbr_stats.progressive_passes)
    }
    return weighted_composite(form_components)
```

### 2. Advanced Fixture Difficulty
```python
# Current (betting odds only)
def calculate_fixture_difficulty(odds_data):
    return odds_to_difficulty_scale(odds_data)

# Enhanced with FBR team analytics  
def calculate_fbr_fixture_difficulty(opponent_team, fbr_team_stats):
    attacking_matchup = player_position_strength / opponent_defensive_strength
    defensive_matchup = team_defensive_support / opponent_attacking_strength
    return composite_difficulty_score(attacking_matchup, defensive_matchup)
```

### 3. Intelligent Starter Prediction
```python
# Current (manual CSV imports)
def get_starter_probability(csv_data):
    return manual_starter_predictions

# Enhanced with FBR rotation analysis
def calculate_fbr_starter_probability(player_id, fbr_match_history):
    rotation_pattern = analyze_minutes_trend(fbr_match_history)
    performance_form = analyze_recent_performance(fbr_match_history)
    return predictive_starter_model(rotation_pattern, performance_form)
```

## Testing & Validation Framework

### Data Quality Tests
```python
# experimental/test_fbr_integration.py
def test_api_connection():
    """Test basic API connectivity and authentication"""

def test_premier_league_discovery():
    """Verify Premier League ID and current season"""

def test_player_mapping_accuracy():
    """Validate player name matching between systems"""

def test_data_completeness():
    """Check for missing data in FBR responses"""

def test_calculation_improvements():
    """Compare enhanced vs original True Value calculations"""
```

### Performance Benchmarks
```python
# experimental/benchmark_fbr_performance.py
def benchmark_api_response_times():
    """Measure FBR API response performance"""

def benchmark_calculation_speed():
    """Compare processing time with FBR enhancements"""

def benchmark_data_storage():
    """Measure database impact of FBR tables"""
```

## Risk Assessment & Mitigation

### Technical Risks
1. **Rate Limiting Constraints**
   - **Risk**: 3-second intervals limit real-time updates
   - **Mitigation**: Intelligent caching, batch processing, priority queues

2. **Data Volume Growth**
   - **Risk**: 13 categories × 647 players × 38 matches = large dataset
   - **Mitigation**: Selective data import, archival strategy, query optimization

3. **API Dependency**
   - **Risk**: External service availability
   - **Mitigation**: Graceful fallbacks, cached data, error handling

### Integration Risks
1. **Name Matching Complexity**
   - **Risk**: Player/team name mismatches
   - **Mitigation**: Use existing name matching system, manual validation

2. **Calculation Changes**
   - **Risk**: Enhanced formulas may affect existing user expectations
   - **Mitigation**: A/B testing, gradual rollout, user configuration options

## Success Metrics

### Phase 1 Success Criteria
- [ ] API key generation successful
- [ ] Premier League discovery complete
- [ ] 90%+ player mapping accuracy
- [ ] Rate limiting framework operational

### Phase 2 Success Criteria  
- [ ] FBR data imported for current season
- [ ] Enhanced calculations show measurable improvement
- [ ] Performance within acceptable limits
- [ ] Data validation passes all tests

### Phase 3 Success Criteria
- [ ] Production integration complete
- [ ] User acceptance of enhanced features
- [ ] System performance maintained
- [ ] Historical data analysis available

## Next Steps

1. **Immediate**: Review this sprint plan and confirm approach
2. **Week 1**: Begin Phase 1 implementation in experimental folder
3. **Week 2**: Data integration and enhanced calculations
4. **Week 3**: Testing and validation
5. **Week 4+**: Production integration and advanced features

## Resources & References

- **FBR API Documentation**: https://fbrapi.com/documentation
- **Existing System Architecture**: `docs/DATABASE_SCHEMA.md`
- **Current Formula Reference**: `docs/FORMULA_REFERENCE.md`
- **Name Matching System**: `src/name_matching/unified_matcher.py`
- **Calculation Research**: `calculation-research/` folder

---

*Document created: 2025-08-21*  
*Last updated: 2025-08-21*  
*Status: Planning Phase*