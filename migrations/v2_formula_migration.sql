-- Fantasy Football Value Hunter v2.0 Migration
-- Implements research-based formula optimizations

BEGIN;

-- Add new columns to players table
ALTER TABLE players ADD COLUMN IF NOT EXISTS true_value DECIMAL(8,2);
ALTER TABLE players ADD COLUMN IF NOT EXISTS roi DECIMAL(8,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS formula_version VARCHAR(10) DEFAULT 'v2.0';
ALTER TABLE players ADD COLUMN IF NOT EXISTS exponential_form_score DECIMAL(5,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS baseline_xgi DECIMAL(5,3);
ALTER TABLE players ADD COLUMN IF NOT EXISTS blended_ppg DECIMAL(5,2);
ALTER TABLE players ADD COLUMN IF NOT EXISTS current_season_weight DECIMAL(4,3);

-- Create validation tables
CREATE TABLE IF NOT EXISTS player_predictions (
    player_id VARCHAR(50),
    gameweek INTEGER,
    predicted_value DECIMAL(8,2),
    actual_points DECIMAL(5,2),
    model_version VARCHAR(50),
    error_abs DECIMAL(8,2) GENERATED ALWAYS AS (ABS(predicted_value - actual_points)) STORED,
    error_signed DECIMAL(8,2) GENERATED ALWAYS AS (predicted_value - actual_points) STORED,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, gameweek, model_version)
);

CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50),
    season VARCHAR(10),
    rmse DECIMAL(5,3),
    mae DECIMAL(5,3),
    spearman_correlation DECIMAL(5,3),
    spearman_p_value DECIMAL(6,4),
    precision_at_20 DECIMAL(5,3),
    r_squared DECIMAL(5,3),
    n_predictions INTEGER,
    test_date TIMESTAMP DEFAULT NOW(),
    parameters JSONB,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS parameter_optimization (
    id SERIAL PRIMARY KEY,
    test_date TIMESTAMP DEFAULT NOW(),
    parameters JSONB,
    rmse DECIMAL(5,3),
    mae DECIMAL(5,3),
    spearman_correlation DECIMAL(5,3),
    precision_at_20 DECIMAL(5,3),
    season_tested VARCHAR(10),
    notes TEXT
);

-- Create form tracking table for EWMA
CREATE TABLE IF NOT EXISTS form_scores (
    player_id VARCHAR(50),
    gameweek INTEGER,
    exponential_score DECIMAL(5,3),
    alpha_used DECIMAL(4,3),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, gameweek)
);

-- Create Gemini usage tracking
CREATE TABLE IF NOT EXISTS gemini_usage (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    endpoint VARCHAR(50),
    requests_count INTEGER DEFAULT 1,
    cached_responses INTEGER DEFAULT 0,
    estimated_cost DECIMAL(8,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, endpoint)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_error ON player_predictions(error_abs DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_gameweek ON player_predictions(gameweek);
CREATE INDEX IF NOT EXISTS idx_validation_rmse ON validation_results(rmse);
CREATE INDEX IF NOT EXISTS idx_players_roi ON players(roi DESC);
CREATE INDEX IF NOT EXISTS idx_players_true_value ON players(true_value DESC);
CREATE INDEX IF NOT EXISTS idx_form_scores_player_gw ON form_scores(player_id, gameweek);

-- Create views for analysis
CREATE OR REPLACE VIEW worst_predictions AS
SELECT 
    pp.*,
    p.name,
    p.position,
    p.team
FROM player_predictions pp
JOIN players p ON pp.player_id = p.id
WHERE pp.error_abs >= 5.0
ORDER BY pp.error_abs DESC;

CREATE OR REPLACE VIEW model_comparison AS
SELECT 
    model_version,
    COUNT(*) as tests_run,
    AVG(rmse) as avg_rmse,
    AVG(mae) as avg_mae,
    AVG(spearman_correlation) as avg_spearman,
    AVG(precision_at_20) as avg_precision_20
FROM validation_results
GROUP BY model_version
ORDER BY avg_rmse;

-- Add comments for documentation
COMMENT ON COLUMN players.true_value IS 'Pure point prediction (no price factor) - v2.0 formula';
COMMENT ON COLUMN players.roi IS 'Return on Investment: true_value / price';
COMMENT ON COLUMN players.exponential_form_score IS 'EWMA form score using exponential decay';
COMMENT ON COLUMN players.baseline_xgi IS 'Historical xGI baseline for normalization';
COMMENT ON COLUMN players.blended_ppg IS 'Dynamically blended PPG (historical + current)';
COMMENT ON COLUMN players.current_season_weight IS 'Current season weight in blending (0-1)';

-- Initialize baseline xGI for existing players
UPDATE players 
SET baseline_xgi = COALESCE(xgi90, 0.3)
WHERE baseline_xgi IS NULL;

COMMIT;

-- Verify migration
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as players_with_new_columns
FROM players 
WHERE true_value IS NULL;  -- Check new columns exist