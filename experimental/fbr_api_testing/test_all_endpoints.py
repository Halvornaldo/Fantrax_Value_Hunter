"""
Test All FBR API Endpoints
Check which endpoints are working vs returning 500 errors
"""

from fbr_client import FBRAPIClient
import time


def test_all_endpoints():
    """Test each FBR API endpoint individually"""
    api_key = "R-MyTM5rhscARahLBCuyyCRI5idYIbDheKk2fzLZUUk"
    client = FBRAPIClient(api_key)
    
    print("TESTING ALL FBR API ENDPOINTS")
    print("=" * 50)
    
    # Test basic endpoints (no parameters needed)
    basic_tests = [
        ("Countries", lambda: client.get_countries()),
        ("Documentation", lambda: client._make_request("/documentation"))
    ]
    
    print("BASIC ENDPOINTS (no parameters)")
    print("-" * 30)
    for name, test_func in basic_tests:
        try:
            result = test_func()
            status = "✓ WORKING" if result else "✗ FAILED"
            print(f"{name:15} {status}")
        except Exception as e:
            print(f"{name:15} ✗ ERROR: {e}")
        time.sleep(1)  # Brief pause between tests
    
    print()
    
    # Test endpoints that might work with common parameters
    param_tests = [
        ("Leagues (ENG)", lambda: client.get_leagues("ENG")),
        ("Leagues (ESP)", lambda: client.get_leagues("ESP")), 
        ("League Seasons (PL)", lambda: client.get_league_seasons(9)),
        ("League Seasons (La Liga)", lambda: client.get_league_seasons(12)),
        ("League Details (PL)", lambda: client.get_league_season_details(9)),
        ("Team Season Stats (PL)", lambda: client.get_team_season_stats(9))
    ]
    
    print("PARAMETER-BASED ENDPOINTS")
    print("-" * 30)
    for name, test_func in param_tests:
        try:
            result = test_func()
            status = "✓ WORKING" if result else "✗ FAILED"
            print(f"{name:20} {status}")
        except Exception as e:
            print(f"{name:20} ✗ ERROR: {e}")
        time.sleep(3.1)  # Respect rate limit
    
    print()
    
    # Test with potentially valid team/player IDs (from documentation examples)
    specific_tests = [
        ("Son Player Stats", lambda: client.get_player_match_stats("92e7e919", 9, "2023-2024")),
        ("Arsenal Team Data", lambda: client.get_teams("18bb7c10")),
        ("Jordan Pickford", lambda: client._make_request("/players", {"player_id": "4806ec67"}))
    ]
    
    print("SPECIFIC ID ENDPOINTS")  
    print("-" * 30)
    for name, test_func in specific_tests:
        try:
            result = test_func()
            status = "✓ WORKING" if result else "✗ FAILED" 
            print(f"{name:20} {status}")
        except Exception as e:
            print(f"{name:20} ✗ ERROR: {e}")
        time.sleep(3.1)  # Respect rate limit
    
    print()
    client.print_stats()


def test_simple_endpoints():
    """Quick test of just a few key endpoints"""
    api_key = "R-MyTM5rhscARahLBCuyyCRI5idYIbDheKk2fzLZUUk"
    client = FBRAPIClient(api_key)
    
    print("QUICK ENDPOINT TEST")
    print("=" * 30)
    
    # Try documentation endpoint (might be cached/static)
    print("Testing /documentation...")
    doc_result = client._make_request("/documentation")
    print(f"Documentation: {'✓ WORKING' if doc_result else '✗ FAILED'}")
    
    time.sleep(3.1)
    
    # Try league seasons with known Premier League ID
    print("Testing /league-seasons with Premier League ID 9...")
    seasons_result = client.get_league_seasons(9)
    print(f"League Seasons: {'✓ WORKING' if seasons_result else '✗ FAILED'}")
    
    time.sleep(3.1)
    
    # Try a specific player from the documentation example
    print("Testing /player-match-stats with Son Heung-min...")
    player_result = client.get_player_match_stats("92e7e919", 9, "2023-2024")
    print(f"Player Stats: {'✓ WORKING' if player_result else '✗ FAILED'}")
    
    client.print_stats()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        test_simple_endpoints()
    else:
        test_all_endpoints()