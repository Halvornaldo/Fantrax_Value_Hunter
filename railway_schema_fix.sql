-- Add missing columns to player_metrics table
ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS next_opponent VARCHAR(3);
ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS is_home BOOLEAN;
ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_multiplier NUMERIC DEFAULT 1.0;
ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS csv_confidence_percentage NUMERIC;