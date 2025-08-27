-- Performance Indexes for Fantrax Value Hunter
-- These indexes will significantly speed up the complex queries in /api/players
-- Zero risk - can be dropped if any issues arise

-- Index 1: Speed up main player_metrics JOIN (most critical)
-- This handles the WHERE pm.gameweek = %s condition
CREATE INDEX IF NOT EXISTS idx_player_metrics_gameweek_player 
ON player_metrics(gameweek, player_id);

-- Index 2: Speed up player_games_data GROUP BY subquery
-- This handles the expensive aggregation in the LEFT JOIN
CREATE INDEX IF NOT EXISTS idx_player_games_data_player_id 
ON player_games_data(player_id);

-- Index 3: Speed up team_fixtures JOIN  
-- This handles tf.team_code = p.team AND tf.gameweek = %s
CREATE INDEX IF NOT EXISTS idx_team_fixtures_team_gameweek 
ON team_fixtures(team_code, gameweek);

-- Index 4: Speed up V2 form calculations
-- This handles the recent points queries in FormulaEngineV2
CREATE INDEX IF NOT EXISTS idx_player_form_player_gameweek 
ON player_form(player_id, gameweek DESC);

-- Index 5: Primary key optimizations (if not already optimal)
-- Ensure the main tables have efficient primary key indexes
CREATE INDEX IF NOT EXISTS idx_players_id 
ON players(id);

-- Index 6: Speed up position and team filtering
-- This handles WHERE p.position IN (...) and p.team IN (...)
CREATE INDEX IF NOT EXISTS idx_players_position_team 
ON players(position, team);

-- Display current indexes for verification
SELECT 
    schemaname,
    tablename, 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('players', 'player_metrics', 'player_games_data', 'team_fixtures', 'player_form')
ORDER BY tablename, indexname;