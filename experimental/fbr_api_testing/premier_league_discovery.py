"""
Premier League Discovery Script
Find Premier League ID and current season from FBR API
"""

import json
from fbr_client import FBRAPIClient


class PremierLeagueDiscovery:
    """Discover Premier League information from FBR API"""
    
    def __init__(self, api_key: str):
        self.client = FBRAPIClient(api_key)
        self.discovery_data = {}
    
    def discover_england(self):
        """Find England in countries list"""
        print("Step 1: Finding England in countries...")
        
        # Try getting all countries first
        countries_data = self.client.get_countries()
        if not countries_data:
            print("  Failed to get countries list, trying specific query...")
            countries_data = self.client.get_countries("England")
        
        if not countries_data or 'data' not in countries_data:
            print("  ❌ Failed to get England data")
            return False
        
        # Find England
        countries = countries_data['data']
        england = None
        
        for country in countries:
            if country.get('country', '').lower() in ['england', 'united kingdom']:
                england = country
                break
        
        if not england:
            print("  ❌ England not found in countries")
            return False
        
        self.discovery_data['england'] = england
        print(f"  ✅ Found England: {england['country']} ({england['country_code']})")
        print(f"     Clubs: {england.get('#_clubs', 'N/A')}, Players: {england.get('#_players', 'N/A')}")
        return True
    
    def discover_premier_league(self):
        """Find Premier League in England's leagues"""
        if 'england' not in self.discovery_data:
            print("  ❌ England data not available")
            return False
        
        print("Step 2: Finding Premier League...")
        country_code = self.discovery_data['england']['country_code']
        
        leagues_data = self.client.get_leagues(country_code)
        if not leagues_data or 'data' not in leagues_data:
            print("  ❌ Failed to get leagues data")
            return False
        
        # Search through league categories
        premier_league = None
        for league_category in leagues_data['data']:
            if league_category.get('league_type') == 'domestic_leagues':
                for league in league_category.get('leagues', []):
                    if 'premier league' in league.get('competition_name', '').lower():
                        premier_league = league
                        break
                if premier_league:
                    break
        
        if not premier_league:
            print("  ❌ Premier League not found")
            return False
        
        self.discovery_data['premier_league'] = premier_league
        print(f"  ✅ Found Premier League:")
        print(f"     ID: {premier_league['league_id']}")
        print(f"     Name: {premier_league['competition_name']}")
        print(f"     Seasons: {premier_league.get('first_season')} - {premier_league.get('last_season')}")
        return True
    
    def discover_current_season(self):
        """Find current season for Premier League"""
        if 'premier_league' not in self.discovery_data:
            print("  ❌ Premier League data not available")
            return False
        
        print("Step 3: Finding current season...")
        league_id = self.discovery_data['premier_league']['league_id']
        
        seasons_data = self.client.get_league_seasons(league_id)
        if not seasons_data or 'data' not in seasons_data:
            print("  ❌ Failed to get seasons data")
            return False
        
        # Get most recent season (first in list)
        seasons = seasons_data['data']
        if not seasons:
            print("  ❌ No seasons found")
            return False
        
        current_season = seasons[0]  # Most recent season
        self.discovery_data['current_season'] = current_season
        
        print(f"  ✅ Current season: {current_season['season_id']}")
        print(f"     Teams: {current_season.get('#_squads', 'N/A')}")
        print(f"     Champion: {current_season.get('champion', 'TBD')}")
        
        if current_season.get('top_scorer'):
            top_scorer = current_season['top_scorer']
            print(f"     Top scorer: {top_scorer.get('player', 'TBD')} ({top_scorer.get('goals_scored', 0)} goals)")
        
        return True
    
    def get_league_details(self):
        """Get detailed league information"""
        if 'premier_league' not in self.discovery_data or 'current_season' not in self.discovery_data:
            print("  ❌ Missing premier league or season data")
            return False
        
        print("Step 4: Getting league details...")
        league_id = self.discovery_data['premier_league']['league_id']
        season_id = self.discovery_data['current_season']['season_id']
        
        details = self.client.get_league_season_details(league_id, season_id)
        if not details or 'data' not in details:
            print("  ❌ Failed to get league details")
            return False
        
        self.discovery_data['league_details'] = details['data']
        details_data = details['data']
        
        print(f"  ✅ League details:")
        print(f"     Start: {details_data.get('league_start', 'TBD')}")
        print(f"     End: {details_data.get('league_end', 'TBD')}")
        print(f"     Type: {details_data.get('league_type', 'N/A')}")
        print(f"     Advanced stats: {details_data.get('has_adv_stats', 'N/A')}")
        
        return True
    
    def run_full_discovery(self):
        """Run complete Premier League discovery process"""
        print("🔍 Starting Premier League Discovery...")
        print("=" * 50)
        
        steps = [
            self.discover_england,
            self.discover_premier_league, 
            self.discover_current_season,
            self.get_league_details
        ]
        
        for i, step in enumerate(steps, 1):
            try:
                if not step():
                    print(f"\n❌ Discovery failed at step {i}")
                    return False
                print()  # Add spacing between steps
            except Exception as e:
                print(f"\n💥 Error in step {i}: {e}")
                return False
        
        print("🎉 Premier League discovery completed successfully!")
        return True
    
    def get_summary(self):
        """Get summary of discovered information"""
        if not self.discovery_data:
            return None
        
        summary = {
            'country_code': self.discovery_data.get('england', {}).get('country_code'),
            'league_id': self.discovery_data.get('premier_league', {}).get('league_id'),
            'league_name': self.discovery_data.get('premier_league', {}).get('competition_name'),
            'season_id': self.discovery_data.get('current_season', {}).get('season_id'),
            'num_teams': self.discovery_data.get('current_season', {}).get('#_squads'),
            'has_advanced_stats': self.discovery_data.get('league_details', {}).get('has_adv_stats'),
            'season_start': self.discovery_data.get('league_details', {}).get('league_start'),
            'season_end': self.discovery_data.get('league_details', {}).get('league_end')
        }
        
        return summary
    
    def save_discovery_data(self, filename: str = "premier_league_discovery.json"):
        """Save discovery data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.discovery_data, f, indent=2)
        print(f"💾 Discovery data saved to {filename}")


def main():
    """Main discovery script"""
    # Use the API key we generated
    api_key = "R-MyTM5rhscARahLBCuyyCRI5idYIbDheKk2fzLZUUk"
    
    discovery = PremierLeagueDiscovery(api_key)
    
    if discovery.run_full_discovery():
        # Print summary
        summary = discovery.get_summary()
        if summary:
            print("\n📋 DISCOVERY SUMMARY")
            print("=" * 50)
            for key, value in summary.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Save data
        discovery.save_discovery_data()
        discovery.client.print_stats()
    else:
        print("\n💥 Discovery failed - check API connectivity")


if __name__ == "__main__":
    main()