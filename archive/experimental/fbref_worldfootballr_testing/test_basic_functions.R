# Basic worldfootballR functionality test
# Load packages from user library

library(worldfootballR, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(dplyr, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(jsonlite, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")

cat("=== WORLDFOOTBALLR BASIC TEST ===\n\n")

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
    cat("First few matches:\n")
    print(head(pl_matches[, c("Date", "Home", "Score", "Away")], 5))
    
    # Save sample data
    write_json(head(pl_matches, 20), "sample_premier_league_matches.json", pretty = TRUE)
    cat("✓ Sample data saved to sample_premier_league_matches.json\n\n")
    
}, error = function(e) {
    cat("✗ Error getting match results:", e$message, "\n\n")
})

cat("=== TEST COMPLETE ===\n")