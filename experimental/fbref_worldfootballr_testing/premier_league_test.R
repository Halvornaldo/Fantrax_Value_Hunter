# Premier League Data Extraction Test using worldfootballR
# This script tests the key functionality for extracting Premier League data

library(worldfootballR)
library(dplyr)
library(jsonlite)

cat("=== WORLDFOOTBALLR FBREF DATA EXTRACTION TEST ===\n\n")

# Test 1: Get Premier League match results for current season
cat("1. Testing Premier League Match Results (2024-25 season)...\n")
tryCatch({
    pl_matches <- fb_match_results(
        country = "ENG", 
        gender = "M", 
        season_end_year = 2025,
        tier = "1st"
    )
    
    cat("✓ Success! Retrieved", nrow(pl_matches), "Premier League matches\n")
    cat("Columns available:", paste(names(pl_matches), collapse = ", "), "\n")
    cat("Sample match:", pl_matches$Home[1], "vs", pl_matches$Away[1], 
        "on", pl_matches$Date[1], "\n\n")
}, error = function(e) {
    cat("✗ Error getting match results:", e$message, "\n\n")
})

# Test 2: Get league table/standings
cat("2. Testing Premier League Season Stats...\n")
tryCatch({
    pl_season_stats <- fb_league_stats(
        country = "ENG",
        gender = "M", 
        season_end_year = 2025,
        tier = "1st",
        stat_type = "league_table"
    )
    
    cat("✓ Success! Retrieved season stats for", nrow(pl_season_stats), "teams\n")
    cat("Top 3 teams:\n")
    print(head(pl_season_stats[, c("Squad", "MP", "Pts")], 3))
    cat("\n")
}, error = function(e) {
    cat("✗ Error getting season stats:", e$message, "\n\n")
})

# Test 3: Get team statistics
cat("3. Testing Team Match Stats...\n")
tryCatch({
    # Get stats for a specific team (Arsenal)
    team_stats <- fb_team_match_stats(
        team_urls = "https://fbref.com/en/squads/18bb7c10/Arsenal-Stats",
        stat_type = "shooting"
    )
    
    cat("✓ Success! Retrieved team stats with", nrow(team_stats), "records\n")
    cat("Columns available:", paste(names(team_stats), collapse = ", "), "\n\n")
}, error = function(e) {
    cat("✗ Error getting team stats:", e$message, "\n\n")
})

# Test 4: Get player season stats
cat("4. Testing Player Season Stats...\n")
tryCatch({
    player_stats <- fb_player_season_stats(
        country = "ENG",
        gender = "M",
        season_end_year = 2025,
        tier = "1st",
        stat_type = "standard"
    )
    
    cat("✓ Success! Retrieved stats for", nrow(player_stats), "players\n")
    cat("Top scorer so far:\n")
    top_scorer <- player_stats %>% 
        arrange(desc(Gls)) %>% 
        head(1)
    print(top_scorer[, c("Player", "Squad", "Gls", "Ast")])
    cat("\n")
}, error = function(e) {
    cat("✗ Error getting player stats:", e$message, "\n\n")
})

# Export sample data to JSON for Python integration
cat("5. Exporting sample data for integration...\n")
if (exists("pl_matches") && nrow(pl_matches) > 0) {
    # Sample of recent matches
    sample_matches <- head(pl_matches, 10)
    write_json(sample_matches, "sample_pl_matches.json", pretty = TRUE)
    cat("✓ Exported sample matches to sample_pl_matches.json\n")
}

if (exists("pl_season_stats") && nrow(pl_season_stats) > 0) {
    write_json(pl_season_stats, "sample_pl_season_stats.json", pretty = TRUE)
    cat("✓ Exported season stats to sample_pl_season_stats.json\n")
}

cat("\n=== TEST COMPLETE ===\n")
cat("worldfootballR provides direct access to FBRef data!\n")
cat("This could serve as an excellent alternative to the FBR API.\n")