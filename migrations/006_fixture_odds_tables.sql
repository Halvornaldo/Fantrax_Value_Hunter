-- Sprint 6: Fixture Difficulty - Database Schema
-- Creates tables for odds-based fixture difficulty system
-- Date: August 18, 2025

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS team_fixtures;
DROP TABLE IF EXISTS fixture_odds;

-- Store raw odds data from CSV uploads
CREATE TABLE fixture_odds (
    id SERIAL PRIMARY KEY,
    gameweek INTEGER NOT NULL,
    match_date DATE NOT NULL,
    home_team VARCHAR(5) NOT NULL,
    away_team VARCHAR(5) NOT NULL,
    home_odds DECIMAL(5,2) NOT NULL,
    draw_odds DECIMAL(5,2) NOT NULL,
    away_odds DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure no duplicate fixtures per gameweek
    UNIQUE(gameweek, home_team, away_team)
);

-- Store calculated difficulty scores per team per gameweek
CREATE TABLE team_fixtures (
    gameweek INTEGER NOT NULL,
    team_code VARCHAR(5) NOT NULL,
    opponent_code VARCHAR(5) NOT NULL,
    is_home BOOLEAN NOT NULL,
    difficulty_score DECIMAL(3,1) NOT NULL,  -- -10.0 to +10.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- One fixture per team per gameweek
    PRIMARY KEY (gameweek, team_code)
);

-- Create indexes for performance
CREATE INDEX idx_fixture_odds_gameweek ON fixture_odds(gameweek);
CREATE INDEX idx_fixture_odds_teams ON fixture_odds(home_team, away_team);

CREATE INDEX idx_team_fixtures_gameweek ON team_fixtures(gameweek);
CREATE INDEX idx_team_fixtures_team ON team_fixtures(team_code);

-- Add some helpful comments
COMMENT ON TABLE fixture_odds IS 'Raw betting odds data imported from oddsportal.com CSV files';
COMMENT ON TABLE team_fixtures IS 'Calculated difficulty scores (-10 to +10) for each team per gameweek';

COMMENT ON COLUMN fixture_odds.difficulty_score IS 'Difficulty score from -10.0 (easiest) to +10.0 (hardest)';
COMMENT ON COLUMN team_fixtures.is_home IS 'TRUE if team is playing at home, FALSE for away fixtures';

-- Verify tables created
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name IN ('fixture_odds', 'team_fixtures')
ORDER BY table_name, ordinal_position;