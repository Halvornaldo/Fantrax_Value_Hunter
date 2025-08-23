-- Raw Data Snapshot Tables for Trend Analysis
-- Fantasy Football Value Hunter
-- 
-- Purpose: Capture ONLY raw imported data (no calculations)
-- This allows retrospective calculation with consistent formulas
-- Created: 2025-08-23

-- =============================================
-- Raw Player Snapshots Table
-- =============================================

CREATE TABLE IF NOT EXISTS raw_player_snapshots (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(10) NOT NULL,
    gameweek INTEGER NOT NULL,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Core player info at time of import
    name VARCHAR(255),
    team VARCHAR(3),
    position VARCHAR(10),
    
    -- Raw Fantrax import data
    price DECIMAL(5,2),                    -- Fantrax salary/price
    fpts DECIMAL(6,2),                     -- Actual fantasy points scored
    minutes_played INTEGER DEFAULT 0,      -- Minutes played this gameweek
    
    -- Raw fixture data (from odds import)
    opponent VARCHAR(3),                   -- Opponent team code
    is_home BOOLEAN,                       -- Home/away status
    fixture_difficulty DECIMAL(5,2),      -- Raw difficulty score from odds
    
    -- Raw Expected Goals data (from Understat)
    xg90 DECIMAL(5,3),                    -- Expected goals per 90 minutes
    xa90 DECIMAL(5,3),                    -- Expected assists per 90 minutes
    xgi90 DECIMAL(5,3),                   -- Expected goals involvement per 90
    
    -- Raw lineup prediction data
    is_predicted_starter BOOLEAN DEFAULT NULL,  -- Starter prediction (if available)
    rotation_risk VARCHAR(20),                 -- Low/Medium/High/Benched
    
    -- Historical baseline data (captured once, used consistently)
    baseline_xgi DECIMAL(5,3),            -- 2024-25 xGI baseline for normalization
    historical_ppg DECIMAL(5,2),          -- 2024-25 PPG baseline
    historical_games INTEGER,              -- 2024-25 games played
    
    -- Data source tracking
    fantrax_import BOOLEAN DEFAULT FALSE,  -- Was imported from Fantrax CSV
    understat_import BOOLEAN DEFAULT FALSE, -- Was updated from Understat
    odds_import BOOLEAN DEFAULT FALSE,     -- Had fixture odds this GW
    lineup_import BOOLEAN DEFAULT FALSE,   -- Had lineup prediction
    
    -- Ensure one record per player per gameweek
    UNIQUE(player_id, gameweek)
);

-- =============================================
-- Raw Fixture Snapshots Table
-- =============================================

CREATE TABLE IF NOT EXISTS raw_fixture_snapshots (
    id SERIAL PRIMARY KEY,
    gameweek INTEGER NOT NULL,
    team VARCHAR(3) NOT NULL,
    opponent VARCHAR(3),
    is_home BOOLEAN,
    
    -- Raw betting odds
    home_odds DECIMAL(6,2),               -- Home win odds
    draw_odds DECIMAL(6,2),               -- Draw odds  
    away_odds DECIMAL(6,2),               -- Away win odds
    
    -- Calculated difficulty (but stored as raw for consistency)
    difficulty_score DECIMAL(5,2),        -- Difficulty score (-10 to +10)
    
    -- Import metadata
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    odds_source VARCHAR(50),              -- Source of odds data
    
    -- Ensure one record per team per gameweek
    UNIQUE(gameweek, team)
);

-- =============================================
-- Raw Form History Table
-- =============================================

CREATE TABLE IF NOT EXISTS raw_form_snapshots (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(10) NOT NULL,
    gameweek INTEGER NOT NULL,
    
    -- Raw performance data
    points_scored DECIMAL(6,2) NOT NULL,  -- Actual points this gameweek
    minutes_played INTEGER DEFAULT 0,     -- Minutes played
    games_played INTEGER DEFAULT 0,       -- 0 or 1 (did they play?)
    
    -- Import metadata  
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one record per player per gameweek
    UNIQUE(player_id, gameweek)
);

-- =============================================
-- Performance Indexes
-- =============================================

-- Player snapshot indexes
CREATE INDEX IF NOT EXISTS idx_raw_player_snapshots_player_id ON raw_player_snapshots(player_id);
CREATE INDEX IF NOT EXISTS idx_raw_player_snapshots_gameweek ON raw_player_snapshots(gameweek);
CREATE INDEX IF NOT EXISTS idx_raw_player_snapshots_player_gw ON raw_player_snapshots(player_id, gameweek);
CREATE INDEX IF NOT EXISTS idx_raw_player_snapshots_timestamp ON raw_player_snapshots(import_timestamp);

-- Fixture snapshot indexes  
CREATE INDEX IF NOT EXISTS idx_raw_fixture_snapshots_gameweek ON raw_fixture_snapshots(gameweek);
CREATE INDEX IF NOT EXISTS idx_raw_fixture_snapshots_team ON raw_fixture_snapshots(team);
CREATE INDEX IF NOT EXISTS idx_raw_fixture_snapshots_team_gw ON raw_fixture_snapshots(gameweek, team);

-- Form snapshot indexes
CREATE INDEX IF NOT EXISTS idx_raw_form_snapshots_player_id ON raw_form_snapshots(player_id);
CREATE INDEX IF NOT EXISTS idx_raw_form_snapshots_gameweek ON raw_form_snapshots(gameweek);
CREATE INDEX IF NOT EXISTS idx_raw_form_snapshots_player_gw ON raw_form_snapshots(player_id, gameweek);

-- =============================================
-- Views for Easy Querying
-- =============================================

-- Complete raw data view (joins player + fixture data)
CREATE OR REPLACE VIEW raw_data_complete AS
SELECT 
    p.player_id,
    p.gameweek,
    p.import_timestamp,
    
    -- Player info
    p.name,
    p.team,
    p.position,
    
    -- Performance data
    p.price,
    p.fpts,
    p.minutes_played,
    
    -- xG data
    p.xg90,
    p.xa90, 
    p.xgi90,
    p.baseline_xgi,
    p.historical_ppg,
    
    -- Fixture data (from player snapshots for consistency)
    p.opponent,
    p.is_home,
    p.fixture_difficulty,
    f.home_odds,
    f.draw_odds,
    f.away_odds,
    
    -- Prediction data
    p.is_predicted_starter,
    p.rotation_risk,
    
    -- Import flags
    p.fantrax_import,
    p.understat_import,
    p.odds_import,
    p.lineup_import

FROM raw_player_snapshots p
LEFT JOIN raw_fixture_snapshots f 
    ON p.team = f.team 
    AND p.gameweek = f.gameweek
ORDER BY p.player_id, p.gameweek;

-- Form history view for EWMA calculations
CREATE OR REPLACE VIEW raw_form_history AS
SELECT 
    player_id,
    gameweek,
    points_scored,
    games_played,
    import_timestamp,
    
    -- Running calculations (for reference)
    AVG(points_scored) OVER (
        PARTITION BY player_id 
        ORDER BY gameweek 
        ROWS UNBOUNDED PRECEDING
    ) AS running_ppg,
    
    COUNT(*) OVER (
        PARTITION BY player_id 
        ORDER BY gameweek 
        ROWS UNBOUNDED PRECEDING
    ) AS games_to_date

FROM raw_form_snapshots
ORDER BY player_id, gameweek;

-- =============================================
-- Comments and Documentation
-- =============================================

COMMENT ON TABLE raw_player_snapshots IS 'Raw player data snapshots - contains only imported/source data without any calculations';
COMMENT ON TABLE raw_fixture_snapshots IS 'Raw fixture data snapshots - odds and difficulty scores without formula application';
COMMENT ON TABLE raw_form_snapshots IS 'Raw form history - actual points scored each gameweek for EWMA calculations';

COMMENT ON COLUMN raw_player_snapshots.price IS 'Fantrax salary/price as imported from CSV';
COMMENT ON COLUMN raw_player_snapshots.fpts IS 'Actual fantasy points scored this gameweek';
COMMENT ON COLUMN raw_player_snapshots.baseline_xgi IS '2024-25 season xGI baseline for consistent normalization';
COMMENT ON COLUMN raw_fixture_snapshots.difficulty_score IS 'Calculated from odds but stored as raw for retrospective analysis';

-- =============================================
-- Success Message
-- =============================================

DO $$
BEGIN
    RAISE NOTICE 'Raw data snapshot tables created successfully!';
    RAISE NOTICE 'Tables: raw_player_snapshots, raw_fixture_snapshots, raw_form_snapshots';
    RAISE NOTICE 'Views: raw_data_complete, raw_form_history';
    RAISE NOTICE 'Ready for raw data capture from imports';
END $$;