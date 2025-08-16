-- Name Mapping System Database Migration
-- This creates the tables for the unified name matching system

-- Main table for storing name mappings between different data sources and Fantrax IDs
CREATE TABLE IF NOT EXISTS name_mappings (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL,        -- 'ffs', 'understat', 'fbref', etc.
    source_name VARCHAR(255) NOT NULL,         -- Original name from external source
    fantrax_id VARCHAR(50) NOT NULL,          -- Our canonical player ID
    fantrax_name VARCHAR(255),                -- Current Fantrax name for reference
    team VARCHAR(10),                         -- Team code for additional validation
    position VARCHAR(10),                     -- Position for additional validation
    confidence_score FLOAT DEFAULT 0,         -- Match confidence 0-100
    match_type VARCHAR(50),                   -- 'exact', 'normalized', 'fuzzy', 'alias', 'manual'
    verified BOOLEAN DEFAULT FALSE,           -- Has this mapping been human-verified?
    verification_date TIMESTAMP,             -- When was it verified?
    verified_by VARCHAR(100),                -- Who verified it?
    last_used TIMESTAMP,                     -- When was this mapping last used?
    usage_count INTEGER DEFAULT 0,           -- How many times has this mapping been used?
    notes TEXT,                              -- Optional notes about the mapping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique mapping per source system
    CONSTRAINT unique_source_mapping UNIQUE(source_system, source_name),
    
    -- Ensure fantrax_id references actual players
    CONSTRAINT fk_fantrax_player FOREIGN KEY (fantrax_id) REFERENCES players(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_name_mappings_source ON name_mappings(source_system, source_name);
CREATE INDEX IF NOT EXISTS idx_name_mappings_fantrax ON name_mappings(fantrax_id);
CREATE INDEX IF NOT EXISTS idx_name_mappings_verified ON name_mappings(verified);
CREATE INDEX IF NOT EXISTS idx_name_mappings_team_pos ON name_mappings(team, position);
CREATE INDEX IF NOT EXISTS idx_name_mappings_confidence ON name_mappings(confidence_score DESC);

-- Audit trail table for tracking changes to name mappings
CREATE TABLE IF NOT EXISTS name_mapping_history (
    id SERIAL PRIMARY KEY,
    mapping_id INTEGER,                       -- References name_mappings.id (nullable for deleted mappings)
    action VARCHAR(50) NOT NULL,              -- 'created', 'verified', 'updated', 'rejected', 'deleted'
    old_values JSONB,                        -- Previous values before change
    new_values JSONB,                        -- New values after change
    user_id VARCHAR(100),                    -- Who made the change
    user_ip VARCHAR(45),                     -- IP address for audit
    user_agent TEXT,                         -- Browser/client info
    session_id VARCHAR(100),                 -- Session identifier
    notes TEXT,                              -- Optional notes about the change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint (allows NULL for deleted mappings)
    CONSTRAINT fk_mapping_history FOREIGN KEY (mapping_id) REFERENCES name_mappings(id) ON DELETE SET NULL
);

-- Indexes for audit history
CREATE INDEX IF NOT EXISTS idx_mapping_history_mapping ON name_mapping_history(mapping_id);
CREATE INDEX IF NOT EXISTS idx_mapping_history_action ON name_mapping_history(action);
CREATE INDEX IF NOT EXISTS idx_mapping_history_user ON name_mapping_history(user_id);
CREATE INDEX IF NOT EXISTS idx_mapping_history_date ON name_mapping_history(created_at);

-- Trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_name_mappings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_name_mappings_timestamp
    BEFORE UPDATE ON name_mappings
    FOR EACH ROW
    EXECUTE FUNCTION update_name_mappings_timestamp();

-- Function to log changes to name_mapping_history
CREATE OR REPLACE FUNCTION log_name_mapping_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO name_mapping_history (mapping_id, action, new_values, user_id)
        VALUES (NEW.id, 'created', to_jsonb(NEW), 'system');
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO name_mapping_history (mapping_id, action, old_values, new_values, user_id)
        VALUES (NEW.id, 'updated', to_jsonb(OLD), to_jsonb(NEW), 'system');
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO name_mapping_history (mapping_id, action, old_values, user_id)
        VALUES (OLD.id, 'deleted', to_jsonb(OLD), 'system');
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_name_mapping_changes
    AFTER INSERT OR UPDATE OR DELETE ON name_mappings
    FOR EACH ROW
    EXECUTE FUNCTION log_name_mapping_changes();

-- View for easy querying of verified mappings
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

-- View for mapping statistics
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

-- Insert some initial test data to verify the schema works
INSERT INTO name_mappings (source_system, source_name, fantrax_id, fantrax_name, team, position, confidence_score, match_type, verified) 
VALUES 
    ('test', 'Test Player', 'test_001', 'Test Player', 'TST', 'M', 100.0, 'exact', true),
    ('ffs', 'Raya Martin', 'ars_raya', 'David Raya', 'ARS', 'G', 85.0, 'fuzzy', false)
ON CONFLICT (source_system, source_name) DO NOTHING;

-- Add helpful comments
COMMENT ON TABLE name_mappings IS 'Master table for mapping external data source player names to Fantrax player IDs';
COMMENT ON TABLE name_mapping_history IS 'Audit trail for all changes to name mappings';
COMMENT ON COLUMN name_mappings.source_system IS 'Identifier for the external data source (ffs, understat, fbref, etc.)';
COMMENT ON COLUMN name_mappings.confidence_score IS 'Matching confidence score from 0-100, where 100 is exact match';
COMMENT ON COLUMN name_mappings.verified IS 'Whether this mapping has been manually verified by a human';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON name_mappings TO fantrax_user;
-- GRANT SELECT ON name_mapping_history TO fantrax_user;
-- GRANT SELECT ON verified_name_mappings TO fantrax_user;
-- GRANT SELECT ON name_mapping_stats TO fantrax_user;

-- Migration complete
SELECT 'Name mapping schema created successfully' AS result;