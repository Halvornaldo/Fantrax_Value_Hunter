-- Migration: Add team_metrics table for NPxG-based fixture multipliers
-- Purpose: Store team-level NPxG and NPxGA stats from Understat for fixture difficulty calculations
-- Date: 2025-09-30

-- Create team_metrics table
CREATE TABLE IF NOT EXISTS team_metrics (
    team_code VARCHAR(3) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    npxg DECIMAL(6,2) NOT NULL,
    npxga DECIMAL(6,2) NOT NULL,
    npxgd DECIMAL(6,2) NOT NULL,
    matches_played INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_team_metrics_updated ON team_metrics(last_updated);

-- Add npxg_fixture_multiplier column to player_metrics table
ALTER TABLE player_metrics
ADD COLUMN IF NOT EXISTS npxg_fixture_multiplier DECIMAL(5,3) DEFAULT 1.000;

-- Add index for the new column
CREATE INDEX IF NOT EXISTS idx_player_metrics_npxg_fixture ON player_metrics(npxg_fixture_multiplier);

-- Insert league average placeholder (will be updated by the system)
INSERT INTO team_metrics (team_code, team_name, npxg, npxga, npxgd, matches_played, last_updated)
VALUES ('AVG', 'League Average', 8.00, 8.00, 0.00, 20, CURRENT_TIMESTAMP)
ON CONFLICT (team_code) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE team_metrics IS 'Team-level NPxG and NPxGA statistics from Understat for fixture difficulty calculations';
COMMENT ON COLUMN team_metrics.team_code IS 'Fantrax team code (3 letters, e.g., ARS, MCI)';
COMMENT ON COLUMN team_metrics.team_name IS 'Full team name from Understat';
COMMENT ON COLUMN team_metrics.npxg IS 'Non-penalty Expected Goals for (offensive strength)';
COMMENT ON COLUMN team_metrics.npxga IS 'Non-penalty Expected Goals Against (defensive strength)';
COMMENT ON COLUMN team_metrics.npxgd IS 'Non-penalty Expected Goal Difference (npxg - npxga)';
COMMENT ON COLUMN team_metrics.matches_played IS 'Number of matches in the calculation period';
COMMENT ON COLUMN team_metrics.last_updated IS 'Timestamp of last data update from Understat';

COMMENT ON COLUMN player_metrics.npxg_fixture_multiplier IS 'NPxG-based fixture difficulty multiplier (position-specific with home/away adjustments)';

-- Verify table creation
SELECT 'team_metrics table created successfully' as status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'team_metrics' AND table_schema = 'public'
);

-- Verify column addition
SELECT 'npxg_fixture_multiplier column added successfully' as status
WHERE EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'player_metrics'
    AND column_name = 'npxg_fixture_multiplier'
    AND table_schema = 'public'
);