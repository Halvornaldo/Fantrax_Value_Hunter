const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || (window.location.origin.includes('railway.app') ? window.location.origin : "http://localhost:5001")

// Helper function to make API requests
const makeRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
};

// Fetch players data with V2.0 calculations
export const fetchPlayersData = async () => {
  try {
    const data = await makeRequest('/api/players?limit=1000');
    return {
      players: data.players || [],
      gameweek_info: data.gameweek_info || null,
      metadata: data.metadata || {},
      success: true
    };
  } catch (error) {
    return {
      players: [],
      gameweek_info: null,
      metadata: {},
      success: false,
      error: error.message
    };
  }
};

// Fetch system configuration
export const fetchSystemConfig = async () => {
  try {
    const data = await makeRequest('/api/system/config');
    
    // Ensure proper structure for V2.0 configuration
    const config = {
      ...data,
      formula_optimization_v2: {
        enabled: true,
        ewma_form: {
          alpha: 0.87
        },
        dynamic_blending: {
          adaptation_gameweek: 16
        },
        normalized_xgi: {
          enabled: false,
          normalization_strength: 1.0
        },
        multiplier_caps: {
          form: 2.0,
          fixture: 1.8,
          xgi: 2.5,
          global: 3.0
        },
        ...data.formula_optimization_v2
      }
    };
    
    return {
      config,
      success: true
    };
  } catch (error) {
    return {
      config: {
        formula_optimization_v2: {
          enabled: true,
          ewma_form: { alpha: 0.87 },
          dynamic_blending: { adaptation_gameweek: 16 },
          normalized_xgi: { enabled: false, normalization_strength: 1.0 },
          multiplier_caps: { form: 2.0, fixture: 1.8, xgi: 2.5, global: 3.0 }
        }
      },
      success: false,
      error: error.message
    };
  }
};

// Update system parameters
export const updateSystemParameters = async (parameters) => {
  try {
    const data = await makeRequest('/api/system/update-parameters', {
      method: 'POST',
      body: JSON.stringify(parameters),
    });
    
    return {
      success: true,
      updated_config: data.updated_config || parameters,
      message: data.message || 'Parameters updated successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Reset system parameters to defaults
export const resetSystemParametersToDefaults = async () => {
  try {
    const data = await makeRequest('/api/system/reset-to-defaults', {
      method: 'POST',
    });

    return {
      success: true,
      updated_config: data.updated_config,
      message: data.message || 'Parameters reset to defaults successfully',
      updated_players: data.updated_players
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Run model validation
export const runModelValidation = async (version = 'v2.0') => {
  try {
    const data = await makeRequest(`/api/validation/run/${version}`, {
      method: 'POST',
    });
    
    return {
      success: true,
      validation_results: data.validation_results || {},
      message: data.message || 'Validation completed'
    };
  } catch (error) {
    return {
      success: false,
      validation_results: null,
      error: error.message
    };
  }
};

// Sync Understat data
export const syncUnderstatData = async () => {
  try {
    const data = await makeRequest('/api/understat/sync', {
      method: 'POST',
    });
    
    return {
      success: true,
      message: data.message || 'Data synced successfully',
      stats: data.stats || {},
      verification_needed: data.verification_needed,
      verification_url: data.verification_url,
      unmatched_players: data.unmatched_players
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Export players data as CSV
export const exportPlayersCSV = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== 'All') {
        queryParams.append(key, value);
      }
    });
    
    const url = `${API_BASE_URL}/api/export?${queryParams.toString()}`;
    
    // For file downloads, we use a different approach
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }
    
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `fantrax-players-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
    
    return {
      success: true,
      message: 'CSV export completed'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Get gameweek consistency status
export const getGameweekConsistency = async () => {
  try {
    const data = await makeRequest('/api/gameweek-consistency');
    return {
      success: true,
      ...data
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Apply manual starter override for a player
export const applyStarterOverride = async (playerId, overrideType) => {
  try {
    const data = await makeRequest('/api/manual-override', {
      method: 'POST',
      body: JSON.stringify({
        player_id: playerId,
        override_type: overrideType.toLowerCase()
      }),
    });
    
    return {
      success: true,
      message: data.message || 'Override applied successfully',
      multiplier: data.multiplier,
      recalculated: data.recalculated || false
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Import lineup predictions from CSV
export const importLineupCSV = async (csvFile) => {
  try {
    const formData = new FormData();
    formData.append('lineups_csv', csvFile);

    const response = await fetch(`${API_BASE_URL}/api/import-lineups`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Import failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      starters_identified: data.starters_identified || 0,
      rotation_risks: data.rotation_risk || 0,
      matched_players: data.matched_players || 0,
      total_players: data.total_players || 0,
      unmatched_players: data.unmatched_players || 0,
      match_rate: data.match_rate || 0,
      verification_needed: data.verification_needed || false,
      verification_url: data.verification_url || null,
      message: data.message || 'Lineup import completed successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Import fixture odds from CSV
export const importOddsCSV = async (csvFile, gameweek) => {
  try {
    const formData = new FormData();
    formData.append('file', csvFile);
    formData.append('gameweek', gameweek.toString());

    const response = await fetch(`${API_BASE_URL}/api/import-odds`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Import failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      processed_matches: data.processed_matches || 0,
      skipped_matches: data.skipped_matches || 0,
      gameweek: data.gameweek,
      message: data.message || 'Odds import completed successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};


// NPxG team stats sync
export const syncNPxGTeamStats = async () => {
  try {
    const data = await makeRequest('/api/npxg/sync-team-stats', {
      method: 'POST',
    });

    return {
      success: true,
      message: data.message || 'NPxG team stats synced successfully',
      teams_updated: data.teams_updated || 0,
      league_avg_npxg: data.league_avg_npxg || 0,
      league_avg_npxga: data.league_avg_npxga || 0
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Get current NPxG team statistics
export const fetchNPxGTeamStats = async () => {
  try {
    const data = await makeRequest('/api/npxg/team-stats');

    return {
      success: true,
      teams: data.teams || [],
      total_teams: data.total_teams || 0
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      teams: [],
      total_teams: 0
    };
  }
};

// Get NPxG configuration
export const fetchNPxGConfig = async () => {
  try {
    const data = await makeRequest('/api/npxg/config');

    return {
      success: true,
      config: data.config || {}
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      config: {}
    };
  }
};

// Update NPxG configuration
export const updateNPxGConfig = async (config) => {
  try {
    const data = await makeRequest('/api/npxg/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });

    return {
      success: true,
      message: data.message || 'NPxG configuration updated successfully',
      config: data.config || {}
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// ============================================================================
// LINEUP OPTIMIZER API FUNCTIONS
// ============================================================================

/**
 * Import team roster CSV for lineup optimization.
 * @param {File} csvFile - The CSV file to upload
 * @returns {Promise<Object>} - Roster data with current prices and True Values
 */
export const importLineupRoster = async (csvFile) => {
  try {
    const formData = new FormData();
    formData.append('roster_csv', csvFile);

    const response = await fetch(`${API_BASE_URL}/api/lineup/import`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: data.success,
      roster: data.roster || [],
      unmatched: data.unmatched || [],
      totalPlayers: data.total_players || 0,
      matchedCount: data.matched_count || 0,
      totals: data.totals || {}
    };
  } catch (error) {
    console.error('Lineup import failed:', error);
    return {
      success: false,
      error: error.message,
      roster: []
    };
  }
};

/**
 * Get the current imported lineup roster.
 * @returns {Promise<Object>} - Current roster and totals
 */
export const getCurrentLineup = async () => {
  try {
    const data = await makeRequest('/api/lineup/current');
    return {
      success: true,
      roster: data.roster || [],
      formation: data.formation || '',
      totals: data.totals || {},
      message: data.message
    };
  } catch (error) {
    console.error('Get current lineup failed:', error);
    return {
      success: false,
      error: error.message,
      roster: []
    };
  }
};

/**
 * Generate 3 optimized lineup alternatives.
 * @param {string[]} lockedPlayerIds - IDs of players to keep in lineup
 * @param {number} budget - Total budget constraint (default 100)
 * @param {Object[]} lockedPlayersData - Locked players with purchase prices
 * @returns {Promise<Object>} - 3 alternative lineup suggestions
 */
export const optimizeLineup = async (lockedPlayerIds = [], budget = 100, lockedPlayersData = [], rosterPlayersData = []) => {
  try {
    const data = await makeRequest('/api/lineup/optimize', {
      method: 'POST',
      body: JSON.stringify({
        locked_player_ids: lockedPlayerIds,
        locked_players_data: lockedPlayersData,
        roster_players_data: rosterPlayersData,  // Full roster with purchase prices for owned players
        budget: budget
      }),
    });

    return {
      success: data.success,
      alternatives: data.alternatives || [],
      lockedPlayers: data.locked_players || [],
      lockedCost: data.locked_cost || 0,
      budget: data.budget || 100
    };
  } catch (error) {
    console.error('Lineup optimization failed:', error);
    return {
      success: false,
      error: error.message,
      alternatives: []
    };
  }
};

// Toggle player exclusion from optimizer
export const togglePlayerExclusion = async (playerId) => {
  try {
    const data = await makeRequest(`/api/players/${playerId}/toggle-exclude`, {
      method: 'POST',
    });

    return {
      success: true,
      ...data
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Reset all player exclusions
export const resetAllExclusions = async () => {
  try {
    const data = await makeRequest('/api/players/reset-exclusions', {
      method: 'POST',
    });

    return {
      success: true,
      ...data
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Search players for lineup replacement
export const searchPlayersForReplacement = async (search, position = null) => {
  try {
    let url = `/api/players?limit=50&search=${encodeURIComponent(search)}`;
    if (position) {
      url += `&position=${position}`;
    }
    const data = await makeRequest(url);
    return {
      success: true,
      players: data.players || []
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      players: []
    };
  }
};

export default {
  fetchPlayersData,
  fetchSystemConfig,
  updateSystemParameters,
  resetSystemParametersToDefaults,
  runModelValidation,
  syncUnderstatData,
  exportPlayersCSV,
  getGameweekConsistency,
  applyStarterOverride,
  importLineupCSV,
  importOddsCSV,
  syncNPxGTeamStats,
  fetchNPxGTeamStats,
  fetchNPxGConfig,
  updateNPxGConfig,
  // Lineup Optimizer
  importLineupRoster,
  getCurrentLineup,
  optimizeLineup,
  // Player Exclusions
  togglePlayerExclusion,
  resetAllExclusions,
  // Player Search
  searchPlayersForReplacement,
};