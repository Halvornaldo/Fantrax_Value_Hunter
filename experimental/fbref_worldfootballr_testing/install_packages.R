# Install worldfootballR packages to user library
# This script handles permission issues by using user library

# Set CRAN mirror
options(repos = c(CRAN = "https://cran.rstudio.com/"))

# Create user library if it doesn't exist
user_lib <- file.path(Sys.getenv("R_LIBS_USER"))
if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE)
}

# Install to user library
install.packages("devtools", lib = user_lib)
library(devtools, lib.loc = user_lib)

# Install worldfootballR
devtools::install_github("JaseZiv/worldfootballR", lib = user_lib)

# Install other useful packages
required_packages <- c("dplyr", "tidyr", "jsonlite", "httr", "rvest", "xml2")

for (pkg in required_packages) {
    if (!require(pkg, character.only = TRUE, lib.loc = user_lib)) {
        install.packages(pkg, lib = user_lib)
    }
}

cat("Installation complete!\n")
cat("Packages installed to user library:", user_lib, "\n")