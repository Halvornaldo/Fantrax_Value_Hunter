# Simple worldfootballR test with older season data
# Load packages from user library

library(worldfootballR, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(dplyr, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")

cat("=== WORLDFOOTBALLR SIMPLE TEST ===\n\n")

# Test with 2023-24 season (completed season)
cat("Testing Premier League 2023-24 season results...\n")
tryCatch({
    # Add delay and use completed season
    Sys.sleep(2)
    
    pl_matches_2024 <- fb_match_results(
        country = "ENG", 
        gender = "M", 
        season_end_year = 2024,
        tier = "1st"
    )
    
    cat("✓ Success! Retrieved", nrow(pl_matches_2024), "matches from 2023-24 season\n")
    cat("Sample matches:\n")
    print(head(pl_matches_2024[, c("Date", "Home", "Score", "Away")], 3))
    
}, error = function(e) {
    cat("✗ Error:", e$message, "\n")
    cat("This might be due to FBRef rate limiting or blocking.\n")
})

# Test package installation
cat("\nPackage info:\n")
cat("worldfootballR version:", as.character(packageVersion("worldfootballR")), "\n")

cat("\n=== TEST COMPLETE ===\n")