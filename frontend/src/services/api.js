const API_BASE_URL = 'http://localhost:5001';

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
      stats: data.stats || {}
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
      rotation_risks: data.rotation_risks || 0,
      unmatched_players: data.unmatched_players || [],
      message: data.message || 'Lineup import completed successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

export default {
  fetchPlayersData,
  fetchSystemConfig,
  updateSystemParameters,
  runModelValidation,
  syncUnderstatData,
  exportPlayersCSV,
  getGameweekConsistency,
  applyStarterOverride,
  importLineupCSV,
};