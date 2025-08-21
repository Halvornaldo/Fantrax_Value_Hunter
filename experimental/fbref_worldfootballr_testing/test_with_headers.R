# Test worldfootballR with custom headers and delays to bypass 403 blocking
library(worldfootballR, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(httr, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(dplyr, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")

cat("=== TESTING ANTI-DETECTION TECHNIQUES ===\n\n")

# Method 1: Set custom user agent and headers
cat("1. Testing with custom User-Agent...\n")
tryCatch({
    # Set a browser-like user agent
    options(HTTPUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Add delay
    Sys.sleep(3)
    
    # Try a simple request first
    url <- "https://fbref.com/en/comps/9/Premier-League-Stats"
    response <- GET(url, add_headers(
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept" = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language" = "en-US,en;q=0.5",
        "Accept-Encoding" = "gzip, deflate",
        "Connection" = "keep-alive"
    ))
    
    cat("Response status:", status_code(response), "\n")
    
    if (status_code(response) == 200) {
        cat("✓ Success! Direct HTTP request worked\n")
        
        # Now try worldfootballR function
        cat("Trying worldfootballR with custom headers...\n")
        Sys.sleep(2)
        
        pl_matches <- fb_match_results(
            country = "ENG", 
            gender = "M", 
            season_end_year = 2024,
            tier = "1st"
        )
        
        cat("✓ worldfootballR success! Got", nrow(pl_matches), "matches\n")
        
    } else {
        cat("✗ Direct HTTP request also blocked:", status_code(response), "\n")
    }
    
}, error = function(e) {
    cat("✗ Error:", e$message, "\n")
})

# Method 2: Test with session and cookies
cat("\n2. Testing with session persistence...\n")
tryCatch({
    # Create a session
    session <- html_session("https://fbref.com", add_headers(
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ))
    
    cat("Session status:", session$response$status_code, "\n")
    
}, error = function(e) {
    cat("✗ Session error:", e$message, "\n")
})

# Method 3: Check if there's a rate limit reset time
cat("\n3. Testing with longer delays...\n")
cat("Waiting 10 seconds before next attempt...\n")
Sys.sleep(10)

tryCatch({
    # Try with even longer delay
    pl_matches <- fb_match_results(
        country = "ENG", 
        gender = "M", 
        season_end_year = 2023,  # Try older season
        tier = "1st"
    )
    
    cat("✓ Success with delay! Got", nrow(pl_matches), "matches\n")
    
}, error = function(e) {
    cat("✗ Still blocked after delay:", e$message, "\n")
})

cat("\n=== ANTI-DETECTION TEST COMPLETE ===\n")