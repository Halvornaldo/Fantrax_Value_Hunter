# Setup script for worldfootballR experimentation
# Install required packages and dependencies

# Install devtools if not already installed
if (!require(devtools)) {
    install.packages("devtools")
    library(devtools)
}

# Install worldfootballR from GitHub
if (!require(worldfootballR)) {
    devtools::install_github("JaseZiv/worldfootballR")
    library(worldfootballR)
}

# Install other potentially useful packages
required_packages <- c("dplyr", "tidyr", "ggplot2", "jsonlite", "httr")

for (pkg in required_packages) {
    if (!require(pkg, character.only = TRUE)) {
        install.packages(pkg)
        library(pkg, character.only = TRUE)
    }
}

cat("Setup complete! worldfootballR and dependencies installed.\n")
cat("worldfootballR version:", packageVersion("worldfootballR"), "\n")