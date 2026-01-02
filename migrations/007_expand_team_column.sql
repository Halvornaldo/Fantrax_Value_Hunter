-- Migration: Expand team column to support full team names from Understat
-- Date: 2026-01-02
-- Reason: Understat JSON exports use full team names (e.g., "Manchester City", "Wolverhampton Wanderers")
--         which exceed the original VARCHAR(10) limit

-- Drop dependent views first
DROP VIEW IF EXISTS verified_name_mappings;
DROP VIEW IF EXISTS name_mapping_stats;

-- Expand the team column from VARCHAR(10) to VARCHAR(50)
ALTER TABLE name_mappings ALTER COLUMN team TYPE VARCHAR(50);

-- Recreate the views
CREATE OR REPLACE VIEW verified_name_mappings AS
SELECT
    source_system,
    source_name,
    fantrax_id,
    fantrax_name,
    team,
    position,
    confidence_score,
    match_type,
    verification_date,
    verified_by,
    usage_count,
    last_used,
    created_at
FROM name_mappings
WHERE verified = TRUE
ORDER BY source_system, source_name;

CREATE OR REPLACE VIEW name_mapping_stats AS
SELECT
    source_system,
    COUNT(*) as total_mappings,
    COUNT(*) FILTER (WHERE verified = TRUE) as verified_mappings,
    COUNT(*) FILTER (WHERE confidence_score >= 95) as high_confidence,
    COUNT(*) FILTER (WHERE confidence_score BETWEEN 85 AND 94) as medium_confidence,
    COUNT(*) FILTER (WHERE confidence_score < 85) as low_confidence,
    AVG(confidence_score) as avg_confidence,
    MAX(usage_count) as max_usage,
    SUM(usage_count) as total_usage
FROM name_mappings
GROUP BY source_system
ORDER BY total_mappings DESC;

SELECT 'Team column expanded to VARCHAR(50)' AS result;
