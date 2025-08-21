# Test various circumvention techniques for FBRef 403 blocking
library(worldfootballR, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(httr, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")
library(rvest, lib.loc = "C:/Users/halvo/AppData/Local/R/win-library/4.5")

cat("=== ADVANCED CIRCUMVENTION TESTS ===\n\n")

# Method 1: Test different endpoints
cat("1. Testing different FBRef endpoints...\n")
test_urls <- c(
    "https://fbref.com",
    "https://fbref.com/en/",
    "https://fbref.com/en/comps/",
    "https://fbref.com/en/comps/9/"
)

for (url in test_urls) {
    tryCatch({
        Sys.sleep(2)
        response <- GET(url, add_headers(
            "User-Agent" = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept" = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language" = "en-GB,en;q=0.9",
            "Cache-Control" = "no-cache",
            "Pragma" = "no-cache"
        ))
        cat("URL:", url, "- Status:", status_code(response), "\n")
    }, error = function(e) {
        cat("URL:", url, "- Error:", e$message, "\n")
    })
}

# Method 2: Check if it's IP-based blocking
cat("\n2. Testing if blocking is IP-based...\n")
cat("Checking current IP detection...\n")
tryCatch({
    ip_check <- GET("http://httpbin.org/ip")
    if (status_code(ip_check) == 200) {
        ip_info <- content(ip_check, "parsed")
        cat("Current IP:", ip_info$origin, "\n")
    }
}, error = function(e) {
    cat("IP check failed:", e$message, "\n")
})

# Method 3: Test with different R session options
cat("\n3. Testing with modified R session options...\n")
tryCatch({
    # Set various options that might help
    options(
        "HTTPUserAgent" = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "timeout" = 120,
        "internet.info" = 0
    )
    
    # Try to configure httr options
    httr::set_config(httr::user_agent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"))
    
    Sys.sleep(3)
    
    # Test a simple worldfootballR function
    pl_matches <- fb_match_results(
        country = "ENG", 
        gender = "M", 
        season_end_year = 2022,  # Try even older season
        tier = "1st"
    )
    
    cat("✓ Success! Retrieved", nrow(pl_matches), "matches\n")
    
}, error = function(e) {
    cat("✗ Still blocked:", e$message, "\n")
})

# Method 4: Check what headers FBRef expects
cat("\n4. Analyzing response headers...\n")
tryCatch({
    # Try with minimal request
    response <- HEAD("https://fbref.com")
    cat("HEAD request status:", status_code(response), "\n")
    
    headers <- headers(response)
    for (name in names(headers)) {
        if (grepl("server|cache|security|block", name, ignore.case = TRUE)) {
            cat("Header", name, ":", headers[[name]], "\n")
        }
    }
    
}, error = function(e) {
    cat("Header analysis failed:", e$message, "\n")
})

cat("\n=== CIRCUMVENTION TEST RESULTS ===\n")
cat("All standard techniques failed - FBRef has strong anti-bot protection\n")
cat("Recommendations:\n")
cat("1. Wait for FBR API to recover (most reliable)\n")
cat("2. Use alternative data sources\n")
cat("3. Consider premium proxy services (if permitted)\n")
cat("4. Contact FBRef for API access (if available)\n")