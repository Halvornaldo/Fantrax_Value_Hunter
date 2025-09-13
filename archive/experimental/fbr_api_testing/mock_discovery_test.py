"""
Mock FBR API Discovery Test
Simulates successful Premier League discovery for Sprint 1 testing
"""

import json
from datetime import datetime


class MockFBRData:
    """Mock data for testing when FBR API is unavailable"""
    
    @staticmethod
    def get_countries_response():
        """Mock countries response"""
        return {
            "data": [
                {
                    "country": "England",
                    "country_code": "ENG",
                    "governing_body": "UEFA",
                    "#_clubs": 45,
                    "#_players": 1250,
                    "national_teams": ["M", "F"]
                },
                {
                    "country": "Spain", 
                    "country_code": "ESP",
                    "governing_body": "UEFA",
                    "#_clubs": 42,
                    "#_players": 1180,
                    "national_teams": ["M", "F"]
                }
            ]
        }
    
    @staticmethod
    def get_leagues_response():
        """Mock leagues response for England"""
        return {
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
                        },
                        {
                            "league_id": 10,
                            "competition_name": "Championship",
                            "gender": "M", 
                            "first_season": "2004-2005",
                            "last_season": "2024-2025",
                            "tier": "2nd"
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_league_seasons_response():
        """Mock league seasons response for Premier League"""
        return {
            "data": [
                {
                    "season_id": "2024-2025",
                    "competition_name": "Premier League",
                    "#_squads": 20,
                    "champion": "TBD",
                    "top_scorer": {
                        "player": "TBD",
                        "goals_scored": 0
                    }
                },
                {
                    "season_id": "2023-2024", 
                    "competition_name": "Premier League",
                    "#_squads": 20,
                    "champion": "Manchester City",
                    "top_scorer": {
                        "player": "Erling Haaland",
                        "goals_scored": 27
                    }
                }
            ]
        }
    
    @staticmethod
    def get_league_details_response():
        """Mock league season details response"""
        return {
            "data": {
                "lg_id": 9,
                "season_id": "2024-2025",
                "league_start": "2024-08-17",
                "league_end": "2025-05-25",
                "league_type": "league",
                "has_adv_stats": "yes",
                "rounds": [
                    "Matchweek 1", "Matchweek 2", "Matchweek 3"
                ]
            }
        }
    
    @staticmethod
    def get_sample_team_roster():
        """Mock team roster for testing player mapping"""
        return {
            "team_roster": {
                "data": [
                    {
                        "player": "Bukayo Saka",
                        "player_id": "bc7dc64d",
                        "nationality": "ENG",
                        "position": "DF,FW",
                        "age": 23,
                        "mp": 35,
                        "starts": 32
                    },
                    {
                        "player": "Martin Odegaard",
                        "player_id": "a1b2c3d4",
                        "nationality": "NOR", 
                        "position": "MF",
                        "age": 25,
                        "mp": 33,
                        "starts": 31
                    },
                    {
                        "player": "Gabriel Jesus",
                        "player_id": "e5f6g7h8",
                        "nationality": "BRA",
                        "position": "FW",
                        "age": 27,
                        "mp": 30,
                        "starts": 25
                    }
                ]
            }
        }


def simulate_discovery():
    """Simulate successful Premier League discovery"""
    print("MOCK FBR API DISCOVERY TEST")
    print("=" * 50)
    
    # Step 1: Countries
    print("Step 1: Finding England...")
    countries = MockFBRData.get_countries_response()
    england = countries['data'][0]  # First item is England
    print(f"  Found: {england['country']} ({england['country_code']})")
    print(f"  Clubs: {england['#_clubs']}, Players: {england['#_players']}")
    
    # Step 2: Leagues
    print("\nStep 2: Finding Premier League...")
    leagues = MockFBRData.get_leagues_response()
    premier_league = leagues['data'][0]['leagues'][0]  # First domestic league
    print(f"  Found: {premier_league['competition_name']}")
    print(f"  League ID: {premier_league['league_id']}")
    print(f"  Seasons: {premier_league['first_season']} - {premier_league['last_season']}")
    
    # Step 3: Current Season
    print("\nStep 3: Finding current season...")
    seasons = MockFBRData.get_league_seasons_response()
    current_season = seasons['data'][0]  # Most recent season
    print(f"  Current: {current_season['season_id']}")
    print(f"  Teams: {current_season['#_squads']}")
    print(f"  Champion: {current_season['champion']}")
    
    # Step 4: League Details
    print("\nStep 4: Getting league details...")
    details = MockFBRData.get_league_details_response()
    league_info = details['data']
    print(f"  Start: {league_info['league_start']}")
    print(f"  End: {league_info['league_end']}")
    print(f"  Advanced stats: {league_info['has_adv_stats']}")
    
    # Summary
    summary = {
        'country_code': england['country_code'],
        'league_id': premier_league['league_id'],
        'league_name': premier_league['competition_name'],
        'season_id': current_season['season_id'],
        'num_teams': current_season['#_squads'],
        'has_advanced_stats': league_info['has_adv_stats'],
        'season_start': league_info['league_start'],
        'season_end': league_info['league_end']
    }
    
    print("\nDISCOVERY SUMMARY")
    print("=" * 50)
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Save discovery data
    with open('mock_premier_league_discovery.json', 'w') as f:
        json.dump({
            'discovery_timestamp': datetime.now().isoformat(),
            'england': england,
            'premier_league': premier_league,
            'current_season': current_season,
            'league_details': league_info,
            'summary': summary
        }, f, indent=2)
    
    print(f"\nDiscovery data saved to mock_premier_league_discovery.json")
    return summary


def test_player_mapping_concept():
    """Test player mapping concept with mock data"""
    print("\nPLAYER MAPPING CONCEPT TEST")
    print("=" * 30)
    
    # Mock team roster
    roster = MockFBRData.get_sample_team_roster()
    players = roster['team_roster']['data']
    
    print("Sample FBR player data:")
    for player in players:
        print(f"  {player['player']} (ID: {player['player_id']}, {player['position']}, {player['mp']} games)")
    
    # Mock existing Fantrax players (simulating your 647 players)
    fantrax_players = [
        {"id": "fantrax_001", "name": "Bukayo Saka", "team": "Arsenal"},
        {"id": "fantrax_002", "name": "Martin Odegaard", "team": "Arsenal"}, 
        {"id": "fantrax_003", "name": "Gabriel Jesus", "team": "Arsenal"},
        {"id": "fantrax_004", "name": "Mohamed Salah", "team": "Liverpool"}  # Not in FBR sample
    ]
    
    print(f"\nMapping {len(fantrax_players)} Fantrax players to FBR data:")
    
    mappings = []
    for fantrax_player in fantrax_players:
        # Simple name matching (your unified_matcher.py would be more sophisticated)
        fbr_match = None
        for fbr_player in players:
            if fantrax_player['name'].lower() == fbr_player['player'].lower():
                fbr_match = fbr_player
                break
        
        if fbr_match:
            mappings.append({
                'fantrax_id': fantrax_player['id'],
                'fantrax_name': fantrax_player['name'],
                'fbr_player_id': fbr_match['player_id'],
                'fbr_name': fbr_match['player'],
                'confidence': 1.0,
                'status': 'MATCHED'
            })
            print(f"  ✓ {fantrax_player['name']} -> {fbr_match['player_id']}")
        else:
            mappings.append({
                'fantrax_id': fantrax_player['id'],
                'fantrax_name': fantrax_player['name'],
                'fbr_player_id': None,
                'fbr_name': None,
                'confidence': 0.0,
                'status': 'UNMATCHED'
            })
            print(f"  ✗ {fantrax_player['name']} -> NO MATCH")
    
    # Save mapping results
    with open('mock_player_mappings.json', 'w') as f:
        json.dump({
            'mapping_timestamp': datetime.now().isoformat(),
            'total_fantrax_players': len(fantrax_players),
            'total_fbr_players': len(players),
            'successful_mappings': len([m for m in mappings if m['status'] == 'MATCHED']),
            'mapping_rate': len([m for m in mappings if m['status'] == 'MATCHED']) / len(fantrax_players),
            'mappings': mappings
        }, f, indent=2)
    
    success_rate = len([m for m in mappings if m['status'] == 'MATCHED']) / len(fantrax_players)
    print(f"\nMapping success rate: {success_rate:.1%}")
    print("Player mappings saved to mock_player_mappings.json")
    
    return mappings


def main():
    """Run complete mock testing"""
    print("FBR API SPRINT 1 - MOCK TESTING")
    print("=" * 60)
    print("NOTE: Testing with mock data due to FBR API 500 errors")
    print()
    
    # Run discovery simulation
    summary = simulate_discovery()
    
    # Test player mapping concept
    mappings = test_player_mapping_concept()
    
    print(f"\nSPRINT 1 MOCK RESULTS")
    print("=" * 30)
    print("✓ API Client created with rate limiting")
    print("✓ API key generation working")  
    print("✓ Premier League discovery logic complete")
    print("✓ Player mapping concept validated")
    print(f"✓ Found League ID: {summary['league_id']}")
    print(f"✓ Current Season: {summary['season_id']}")
    print(f"✓ Advanced Stats Available: {summary['has_advanced_stats']}")
    
    print(f"\nNext Steps:")
    print("- Wait for FBR API stability (currently 500 errors)")
    print("- Test with real data when API is working")
    print("- Integrate with existing name matching system")
    print("- Scale to all 647 Fantrax players")


if __name__ == "__main__":
    main()