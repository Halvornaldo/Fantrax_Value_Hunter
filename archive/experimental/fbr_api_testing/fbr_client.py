"""
FBR API Client with Rate Limiting
Isolated testing client for FBR API integration experiments
"""

import requests
import time
import json
from typing import Dict, List, Optional
from datetime import datetime


class FBRAPIClient:
    """
    FBR API client with built-in rate limiting and error handling
    Rate limit: 3 seconds between requests as per FBR documentation
    """
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://fbrapi.com"
        self.api_key = api_key
        self.last_request_time = 0
        self.rate_limit_seconds = 3
        self.request_count = 0
        self.session = requests.Session()
    
    def _enforce_rate_limit(self):
        """Enforce 3-second minimum between requests"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - time_since_last
            print(f"Rate limiting: sleeping {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to FBR API"""
        self._enforce_rate_limit()
        
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        self.request_count += 1
        
        print(f"Request #{self.request_count}: {endpoint}")
        if params:
            print(f"  Params: {params}")
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def generate_api_key(self) -> Optional[str]:
        """Generate new API key"""
        print("Generating FBR API key...")
        try:
            response = self.session.post(f"{self.base_url}/generate_api_key", timeout=30)
            if response.status_code in [200, 201]:  # Accept both 200 and 201 status codes
                data = response.json()
                api_key = data.get('api_key')
                print(f"API key generated: {api_key}")
                self.api_key = api_key
                return api_key
            else:
                print(f"Failed to generate API key: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Failed to generate API key: {e}")
            return None
    
    def get_countries(self, country_name: str = None) -> Optional[Dict]:
        """Get all countries or specific country"""
        params = {"country": country_name} if country_name else None
        return self._make_request("/countries", params)
    
    def get_leagues(self, country_code: str) -> Optional[Dict]:
        """Get leagues for country code"""
        return self._make_request("/leagues", {"country_code": country_code})
    
    def get_league_seasons(self, league_id: int) -> Optional[Dict]:
        """Get available seasons for league"""
        return self._make_request("/league-seasons", {"league_id": league_id})
    
    def get_league_season_details(self, league_id: int, season_id: str = None) -> Optional[Dict]:
        """Get league season details"""
        params = {"league_id": league_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/league-season-details", params)
    
    def get_teams(self, team_id: str, season_id: str = None) -> Optional[Dict]:
        """Get team roster and schedule"""
        params = {"team_id": team_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/teams", params)
    
    def get_player_season_stats(self, team_id: str, league_id: int, season_id: str = None) -> Optional[Dict]:
        """Get season stats for all players on team"""
        params = {"team_id": team_id, "league_id": league_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/player-season-stats", params)
    
    def get_player_match_stats(self, player_id: str, league_id: int, season_id: str = None) -> Optional[Dict]:
        """Get match-by-match stats for player"""
        params = {"player_id": player_id, "league_id": league_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/player-match-stats", params)
    
    def get_team_season_stats(self, league_id: int, season_id: str = None) -> Optional[Dict]:
        """Get season stats for all teams in league"""
        params = {"league_id": league_id}
        if season_id:
            params["season_id"] = season_id
        return self._make_request("/team-season-stats", params)
    
    def print_stats(self):
        """Print client usage statistics"""
        print(f"\nFBR API Client Stats:")
        print(f"  Total requests: {self.request_count}")
        print(f"  Rate limit: {self.rate_limit_seconds}s between requests")
        print(f"  API key set: {'Yes' if self.api_key else 'No'}")


def test_client():
    """Test basic client functionality"""
    print("Testing FBR API Client...")
    
    client = FBRAPIClient()
    
    # Test API key generation
    api_key = client.generate_api_key()
    if not api_key:
        print("Failed to generate API key")
        return False
    
    # Test basic endpoint
    countries = client.get_countries()
    if countries:
        print(f"Countries endpoint working - got {len(countries.get('data', []))} countries")
    else:
        print("Countries endpoint failed")
        return False
    
    client.print_stats()
    return True


if __name__ == "__main__":
    success = test_client()
    if success:
        print("\nFBR API Client test successful!")
    else:
        print("\nFBR API Client test failed!")