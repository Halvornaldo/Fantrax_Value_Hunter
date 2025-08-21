# FBR API Reference Guide

## API Overview

**Base URL**: `https://fbrapi.com`  
**Documentation**: https://fbrapi.com/documentation  
**Rate Limit**: 3 seconds between requests  
**Authentication**: API Key via `X-API-Key` header

## Authentication

### Generate API Key
```bash
curl -X POST https://fbrapi.com/generate_api_key
```

```python
import requests
response = requests.post('https://fbrapi.com/generate_api_key')
api_key = response.json()['api_key']
```

## Core Endpoints

### 1. Countries
**Endpoint**: `GET /countries`  
**Purpose**: Get all available countries with football data

```python
# Get all countries
response = client.get("/countries")

# Get specific country
response = client.get("/countries", {"country": "England"})
```

**Response Format**:
```json
{
    "data": [
        {
            "country": "England",
            "country_code": "ENG", 
            "governing_body": "UEFA",
            "#_clubs": 45,
            "#_players": 1250,
            "national_teams": ["M", "F"]
        }
    ]
}
```

### 2. Leagues
**Endpoint**: `GET /leagues`  
**Purpose**: Get leagues for specific country  
**Key Parameter**: `country_code` (3-letter code)

```python
# Get England leagues (includes Premier League)
response = client.get("/leagues", {"country_code": "ENG"})
```

**Response Structure**:
```json
{
    "data": [
        {
            "league_type": "domestic_leagues",
            "leagues": [
                {
                    "league_id": 9,
                    "competition_name": "Premier League",
                    "gender": "M",
                    "first_season": "1992-1993",
                    "last_season": "2024-2025",
                    "tier": "1st"
                }
            ]
        }
    ]
}
```

**Key Info**: Premier League = `league_id: 9`

### 3. League Seasons
**Endpoint**: `GET /league-seasons`  
**Purpose**: Get available seasons for specific league  
**Key Parameter**: `league_id`

```python
# Get Premier League seasons
response = client.get("/league-seasons", {"league_id": 9})
```

**Response Format**:
```json
{
    "data": [
        {
            "season_id": "2024-2025",
            "competition_name": "Premier League", 
            "#_squads": 20,
            "champion": "TBD",
            "top_scorer": {"player": "TBD", "goals_scored": 0}
        }
    ]
}
```

### 4. Teams  
**Endpoint**: `GET /teams`  
**Purpose**: Get team roster and schedule data  
**Key Parameters**: `team_id`, `season_id` (optional)

```python
# Get team data
response = client.get("/teams", {
    "team_id": "18bb7c10",  # Arsenal
    "season_id": "2024-2025"
})
```

**Response Structure**:
```json
{
    "team_roster": {
        "data": [
            {
                "player": "Bukayo Saka",
                "player_id": "bc7dc64d",
                "nationality": "ENG", 
                "position": "DF,FW",
                "age": 22,
                "mp": 38,
                "starts": 35
            }
        ]
    },
    "team_schedule": {
        "data": [
            {
                "date": "2024-08-17",
                "match_id": "67ed3ba2",
                "opponent": "Wolves",
                "home_away": "Home",
                "result": "W",
                "gf": 2,
                "ga": 0
            }
        ]
    }
}
```

### 5. Players
**Endpoint**: `GET /players`  
**Purpose**: Get individual player metadata  
**Key Parameter**: `player_id` (8-character string)

```python
# Get player details
response = client.get("/players", {"player_id": "bc7dc64d"})
```

**Response Format**:
```json
{
    "player_id": "bc7dc64d",
    "full_name": "Bukayo Saka",
    "positions": ["DF", "FW"],
    "footed": "Left",
    "date_of_birth": "2001-09-05",
    "nationality": "England",
    "height": 178.0,
    "weight": 70.0
}
```

## Statistical Endpoints

### 6. Player Season Stats
**Endpoint**: `GET /player-season-stats`  
**Purpose**: Season aggregate statistics for all team players  
**Key Parameters**: `team_id`, `league_id`, `season_id` (optional)

```python
# Get Arsenal player season stats
response = client.get("/player-season-stats", {
    "team_id": "18bb7c10",
    "league_id": 9,
    "season_id": "2024-2025"
})
```

**Key Statistical Categories**:
- `stats`: Goals, assists, minutes, xG, xA
- `shooting`: Shots, shots on target, conversion rates
- `passing`: Pass completion, progressive passes, key passes
- `defense`: Tackles, interceptions, blocks
- `possession`: Touches, dribbles, carries

### 7. Player Match Stats ⚠️ 
**Endpoint**: `GET /player-match-stats`  
**Purpose**: Match-by-match player statistics  
**Key Parameters**: `player_id`, `league_id`, `season_id` (optional)

**⚠️ IMPORTANT**: Advanced stats require 6+ requests per player (one per category). With 3-second rate limit, this takes 18+ seconds per player.

```python
# Get Son Heung-min match stats
response = client.get("/player-match-stats", {
    "player_id": "92e7e919",
    "league_id": 9, 
    "season_id": "2024-2025"
})
```

**Response Structure**:
```json
{
    "data": [
        {
            "meta_data": {
                "match_id": "67ed3ba2",
                "date": "2024-08-17",
                "opponent": "Wolves",
                "home_away": "Home"
            },
            "stats": {
                "summary": {
                    "result": "W 2–0",
                    "start": "Y",
                    "min": "90",
                    "gls": 1,
                    "ast": 1,
                    "xg": 0.8,
                    "xag": 0.3
                },
                "shooting": {...},
                "passing": {...},
                "defense": {...}
            }
        }
    ]
}
```

### 8. Team Season Stats
**Endpoint**: `GET /team-season-stats`  
**Purpose**: Season-level team statistics  
**Key Parameters**: `league_id`, `season_id` (optional)

```python
# Get Premier League team stats
response = client.get("/team-season-stats", {
    "league_id": 9,
    "season_id": "2024-2025"
})
```

**Key Team Categories**:
- `stats`: Goals for/against, xG, roster size
- `shooting`: Team shooting efficiency
- `defense`: Tackles, blocks, clearances
- `possession`: Pass completion, possession %

### 9. All Players Match Stats
**Endpoint**: `GET /all-players-match-stats`  
**Purpose**: Complete match statistics for both teams  
**Key Parameter**: `match_id` (8-character string)

```python
# Get all player stats for specific match
response = client.get("/all-players-match-stats", {
    "match_id": "67ed3ba2"
})
```

## Premier League Specific Information

### League Discovery
```python
# Step-by-step Premier League discovery
def discover_premier_league(client):
    # 1. Get England
    countries = client.get("/countries")
    england = find_country(countries, "England")
    
    # 2. Get Premier League 
    leagues = client.get("/leagues", {"country_code": "ENG"})
    premier_league = find_league(leagues, "Premier League")  # league_id: 9
    
    # 3. Get current season
    seasons = client.get("/league-seasons", {"league_id": 9})
    current_season = seasons['data'][0]['season_id']  # "2024-2025"
    
    return {
        "league_id": 9,
        "season_id": current_season,
        "country_code": "ENG"
    }
```

### Team IDs (Examples)
```python
PREMIER_LEAGUE_TEAMS = {
    "Arsenal": "18bb7c10",
    "Manchester City": "b8fd03ef", 
    "Liverpool": "822bd0ba",
    "Chelsea": "cff3d9bb",
    "Tottenham": "361ca564",
    "Manchester Utd": "19538871"
    # ... (obtain full list via /teams endpoint)
}
```

## Rate Limiting Implementation

### Python Rate Limiter
```python
import time
from typing import Dict, Optional

class FBRRateLimiter:
    def __init__(self, min_interval: float = 3.0):
        self.min_interval = min_interval
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Enforce minimum interval between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

class FBRAPIClient:
    def __init__(self, api_key: str):
        self.base_url = "https://fbrapi.com"
        self.api_key = api_key
        self.rate_limiter = FBRRateLimiter(3.0)
    
    def get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited GET request"""
        self.rate_limiter.wait_if_needed()
        
        headers = {"X-API-Key": self.api_key}
        response = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
```

## Error Handling

### HTTP Status Codes
- **200 OK**: Request successful
- **400 Bad Request**: Missing/invalid parameters  
- **401 Unauthorized**: Invalid/missing API key
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Robust Error Handling
```python
def safe_api_call(client, endpoint, params=None, max_retries=3):
    """Make API call with retry logic"""
    for attempt in range(max_retries):
        try:
            response = client.get(endpoint, params)
            if response:
                return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
    
    return None
```

## Data Integration Patterns

### Player Mapping Strategy
```python
def map_fantrax_to_fbr_players(fantrax_players, fbr_team_rosters):
    """Map existing Fantrax players to FBR player IDs"""
    mappings = []
    
    for fantrax_player in fantrax_players:
        # Use existing name matching system
        fbr_match = unified_matcher.find_best_match(
            fantrax_player['name'],
            fbr_team_rosters,
            threshold=0.8
        )
        
        if fbr_match:
            mappings.append({
                'fantrax_id': fantrax_player['id'],
                'fbr_player_id': fbr_match['player_id'],
                'confidence': fbr_match['confidence']
            })
    
    return mappings
```

### Batch Data Import
```python
def import_player_season_stats(client, team_mappings, league_id=9):
    """Import season stats for all Premier League players"""
    all_player_stats = []
    
    for team_name, team_id in team_mappings.items():
        print(f"Importing {team_name} players...")
        
        team_stats = client.get("/player-season-stats", {
            "team_id": team_id,
            "league_id": league_id
        })
        
        if team_stats and 'players' in team_stats:
            all_player_stats.extend(team_stats['players'])
        
        # Rate limiter built into client handles delays
    
    return all_player_stats
```

## Usage Examples

### Basic Discovery Flow
```python
# Initialize client
client = FBRAPIClient(api_key="your_api_key_here")

# Discover Premier League
premier_league_info = discover_premier_league(client)
print(f"Premier League ID: {premier_league_info['league_id']}")
print(f"Current Season: {premier_league_info['season_id']}")

# Get team rosters for player mapping
teams = get_premier_league_teams(client, premier_league_info['league_id'])
```

### Enhanced Form Calculation
```python
def calculate_enhanced_form(player_id, fbr_client, games_back=5):
    """Calculate form using FBR match data"""
    
    # Get recent match stats
    match_stats = fbr_client.get("/player-match-stats", {
        "player_id": player_id,
        "league_id": 9
    })
    
    recent_matches = match_stats['data'][-games_back:]
    
    # Calculate form components
    scoring_form = sum(m['stats']['summary']['xg'] for m in recent_matches)
    creativity_form = sum(m['stats']['summary']['xag'] for m in recent_matches) 
    involvement_form = sum(m['stats']['summary']['touches'] for m in recent_matches)
    
    # Weighted composite form score
    form_multiplier = (
        scoring_form * 0.4 +
        creativity_form * 0.3 + 
        involvement_form * 0.3
    ) / games_back
    
    return max(0.5, min(2.0, form_multiplier))  # Clamp between 0.5-2.0
```

---

*Reference guide for FBR API integration with Fantrax Value Hunter*  
*Last updated: 2025-08-21*