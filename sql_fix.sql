-- Fix for line 2660 in app.py
-- Replace the problematic PPG calculation query

            UPDATE player_metrics pm
            SET ppg = (
                SELECT
                    CASE
                        WHEN COALESCE(players.games_current_season, 0) > 0
                        THEN COALESCE(pf_max.total_points, 0) / players.games_current_season
                        ELSE 0
                    END
                FROM players
                LEFT JOIN (
                    SELECT player_id, MAX(points) as total_points
                    FROM player_form
                    WHERE player_id = pm.player_id
                    GROUP BY player_id
                ) pf_max ON players.id = pf_max.player_id
                WHERE players.id = pm.player_id
            )
            WHERE pm.gameweek = %s