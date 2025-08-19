-- Sprint 2: Add Games Column Support
-- Migration to add games tracking columns to player_metrics table
-- Usage: Execute this SQL on fantrax_value_hunter database

-- Add games tracking columns
ALTER TABLE player_metrics 
ADD COLUMN IF NOT EXISTS total_points DECIMAL(8,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS games_played INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_points_historical DECIMAL(8,2) DEFAULT 0,  
ADD COLUMN IF NOT EXISTS games_played_historical INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS data_source VARCHAR(20) DEFAULT 'current';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_metrics_games_played ON player_metrics(games_played);
CREATE INDEX IF NOT EXISTS idx_player_metrics_games_historical ON player_metrics(games_played_historical);
CREATE INDEX IF NOT EXISTS idx_player_metrics_data_source ON player_metrics(data_source);

-- Add comments for documentation
COMMENT ON COLUMN player_metrics.total_points IS 'Current season total fantasy points';
COMMENT ON COLUMN player_metrics.games_played IS 'Current season games played count';
COMMENT ON COLUMN player_metrics.total_points_historical IS '2024-25 season total fantasy points';
COMMENT ON COLUMN player_metrics.games_played_historical IS '2024-25 season games played count';
COMMENT ON COLUMN player_metrics.data_source IS 'Primary data source: current, historical, or blended';

-- Verify columns were added
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'player_metrics' 
    AND column_name IN ('total_points', 'games_played', 'total_points_historical', 'games_played_historical', 'data_source')
ORDER BY column_name;