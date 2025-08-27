// Fantrax Value Hunter V2.0 Enhanced Dashboard JavaScript
// Clean V2.0-only implementation with no legacy dependencies

// Global state
let currentConfig = {};
let pendingChanges = {};
let playersData = [];
let totalFilteredCount = 0;
let currentPage = 0;
let pageSize = 100;
let currentSort = { field: 'true_value', direction: 'desc' };
let currentFilters = {
    positions: ['G', 'D', 'M', 'F'],
    priceMin: 4.0,
    priceMax: 15.0,
    teams: [],
    search: ''
};

// V2.0 Enhanced formula parameters only
let v2Parameters = {
    ewma_alpha: 0.87,
    adaptation_gameweek: 16,
    xgi_enabled: false,
    xgi_strength: 1.0,
    form_cap: 2.0,
    fixture_cap: 1.8,
    xgi_cap: 2.5,
    global_cap: 3.0
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Fantrax Value Hunter V2.0 Enhanced Dashboard Loading...');
    
    // Set initial body class for v2.0
    document.body.className = 'v2-enabled';
    
    // Initialize V2.0 controls
    initializeV2Controls();
    
    // Load initial data
    loadSystemConfiguration();
    loadPlayersData();
    
    // Setup event listeners
    setupV2EventListeners();
    
    console.log('✅ V2.0 Enhanced Dashboard Ready');
});

function initializeV2Controls() {
    // Formula Version Toggle
    const v1Toggle = document.getElementById('v1Toggle');
    const v2Toggle = document.getElementById('v2Toggle');
    
    if (v1Toggle && v2Toggle) {
        v1Toggle.addEventListener('change', handleFormulaVersionChange);
        v2Toggle.addEventListener('change', handleFormulaVersionChange);
    }
    
    // EWMA Alpha slider
    const alphaSlider = document.getElementById('ewmaAlpha');
    const alphaValue = document.getElementById('ewmaAlphaValue');
    const halfLife = document.getElementById('halfLife');
    const recentWeight = document.getElementById('recentWeight');
    
    if (alphaSlider && alphaValue) {
        alphaSlider.addEventListener('input', function() {
            const alpha = parseFloat(this.value);
            alphaValue.textContent = alpha;
            
            // Calculate half-life: log(0.5) / log(alpha)
            const halfLifeValue = Math.log(0.5) / Math.log(alpha);
            if (halfLife) halfLife.textContent = `~${halfLifeValue.toFixed(1)} games`;
            
            // Show recent game weight
            if (recentWeight) recentWeight.textContent = `${Math.round(alpha * 100)}%`;
            
            handleParameterChange();
        });
        
        // Initialize display
        const initialAlpha = parseFloat(alphaSlider.value);
        alphaValue.textContent = initialAlpha;
        if (halfLife) {
            const halfLifeValue = Math.log(0.5) / Math.log(initialAlpha);
            halfLife.textContent = `~${halfLifeValue.toFixed(1)} games`;
        }
        if (recentWeight) recentWeight.textContent = `${Math.round(initialAlpha * 100)}%`;
    }
    
    // Adaptation Gameweek slider with blending visualization
    const adaptationSlider = document.getElementById('adaptationGameweek');
    const adaptationValue = document.getElementById('adaptationGameweekValue');
    
    if (adaptationSlider && adaptationValue) {
        adaptationSlider.addEventListener('input', function() {
            const k = parseInt(this.value);
            adaptationValue.textContent = k;
            updateBlendingVisualization(k);
            handleParameterChange();
        });
        
        // Initialize
        const initialK = parseInt(adaptationSlider.value);
        adaptationValue.textContent = initialK;
        updateBlendingVisualization(initialK);
    }
    
    // xGI Enable toggle
    const xgiToggle = document.getElementById('xgiEnabled');
    const xgiControls = document.getElementById('xgiControls');
    
    if (xgiToggle && xgiControls) {
        xgiToggle.addEventListener('change', function() {
            xgiControls.style.display = this.checked ? 'block' : 'none';
            handleParameterChange();
        });
    }
    
    // xGI Strength slider
    const xgiStrengthSlider = document.getElementById('xgiStrength');
    const xgiStrengthValue = document.getElementById('xgiStrengthValue');
    
    if (xgiStrengthSlider && xgiStrengthValue) {
        xgiStrengthSlider.addEventListener('input', function() {
            xgiStrengthValue.textContent = this.value;
            handleParameterChange();
        });
        xgiStrengthValue.textContent = xgiStrengthSlider.value;
    }
    
    // Multiplier Cap sliders
    const capSliders = ['formCap', 'fixtureCap', 'xgiCap', 'globalCap'];
    capSliders.forEach(id => {
        const slider = document.getElementById(id);
        const value = document.getElementById(id + 'Value');
        
        if (slider && value) {
            slider.addEventListener('input', function() {
                value.textContent = this.value;
                updateAppliedCapsDisplay();
                handleParameterChange();
            });
            value.textContent = slider.value;
        }
    });
    
    // Initialize applied caps display
    updateAppliedCapsDisplay();
}

function handleFormulaVersionChange() {
    const v2Toggle = document.getElementById('v2Toggle');
    const isV2 = v2Toggle && v2Toggle.checked;
    
    // Update body class for styling
    document.body.className = isV2 ? 'v2-enabled' : 'v1-enabled';
    
    // Update version toggles visual state
    document.querySelectorAll('.version-toggle').forEach(toggle => {
        toggle.classList.remove('active');
    });
    
    if (isV2) {
        document.querySelector('label[for="v2Toggle"]').classList.add('active');
    } else {
        document.querySelector('label[for="v1Toggle"]').classList.add('active');
    }
    
    console.log(`🔄 Formula version changed to: ${isV2 ? 'v2.0 Enhanced' : 'v1.0 Legacy'}`);
    handleParameterChange();
}

function updateBlendingVisualization(adaptationGameweek) {
    // Simulate current gameweek (you might want to get this from API)
    const currentGameweek = 8; // This should come from your gameweek data
    
    // Calculate blend weights using the formula: w_current = min(1, (N-1)/(K-1))
    const currentWeight = Math.min(1, (currentGameweek - 1) / (adaptationGameweek - 1));
    const historicalWeight = 1 - currentWeight;
    
    // Update the visualization bars
    const historicalPortion = document.getElementById('historicalPortion');
    const currentPortion = document.getElementById('currentPortion');
    
    if (historicalPortion && currentPortion) {
        const historicalPercent = historicalWeight * 100;
        const currentPercent = currentWeight * 100;
        
        historicalPortion.style.width = `${historicalPercent}%`;
        currentPortion.style.width = `${currentPercent}%`;
        
        // Update labels
        const historicalGames = 38;
        const currentGames = currentGameweek;
        historicalPortion.querySelector('.portion-label').textContent = 
            `Historical ${historicalGames}+${currentGames}`;
        currentPortion.querySelector('.portion-label').textContent = 
            `Current ${currentGames}`;
    }
    
    // Update formula display
    const blendFormula = document.getElementById('blendFormula');
    if (blendFormula) {
        blendFormula.textContent = `w = min(1, (${currentGameweek}-1)/(${adaptationGameweek}-1)) = ${currentWeight.toFixed(2)}`;
    }
}

function updateAppliedCapsDisplay() {
    const appliedCaps = document.getElementById('appliedCaps');
    if (!appliedCaps) return;
    
    const formCap = document.getElementById('formCap')?.value || '2.0';
    const fixtureCap = document.getElementById('fixtureCap')?.value || '1.8';
    const xgiCap = document.getElementById('xgiCap')?.value || '2.5';
    const globalCap = document.getElementById('globalCap')?.value || '3.0';
    
    appliedCaps.textContent = `Form: ${formCap}x | Fixture: ${fixtureCap}x | xGI: ${xgiCap}x | Global: ${globalCap}x`;
}

function setupV2EventListeners() {
    // Apply Changes button
    const applyBtn = document.getElementById('applyChanges');
    if (applyBtn) {
        applyBtn.addEventListener('click', applyParameterChanges);
    }
    
    // Sync Understat button
    const syncBtn = document.getElementById('syncUnderstat');
    if (syncBtn) {
        syncBtn.addEventListener('click', syncUnderstatData);
    }
    
    // Import Lineup button
    const importBtn = document.getElementById('importLineup');
    if (importBtn) {
        importBtn.addEventListener('click', importLineup);
    }
    
    // Export CSV button
    const exportBtn = document.getElementById('exportCSV');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }
    
    // Position filter buttons
    const positionBtns = document.querySelectorAll('.position-btn');
    positionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            handlePositionFilter(this);
        });
    });
    
    // Price range filters
    const priceMin = document.getElementById('priceMin');
    const priceMax = document.getElementById('priceMax');
    if (priceMin) priceMin.addEventListener('input', handleFiltersChange);
    if (priceMax) priceMax.addEventListener('input', handleFiltersChange);
    
    // Team filter
    const teamFilter = document.getElementById('teamFilter');
    if (teamFilter) teamFilter.addEventListener('change', handleFiltersChange);
    
    // Search filter
    const searchInput = document.getElementById('playerSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleFiltersChange, 300));
    }
    
    // Page size selector
    const pageSizeSelect = document.getElementById('pageSize');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', function() {
            pageSize = this.value === 'all' ? 999999 : parseInt(this.value);
            currentPage = 0;
            updatePlayerTable();
        });
    }
    
    // Pagination buttons
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    if (prevBtn) prevBtn.addEventListener('click', () => changePage(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => changePage(1));
    
    // Validation buttons
    const runValidationBtn = document.getElementById('runValidation');
    const viewResultsBtn = document.getElementById('viewResults');
    if (runValidationBtn) runValidationBtn.addEventListener('click', runValidation);
    if (viewResultsBtn) viewResultsBtn.addEventListener('click', viewValidationResults);
}

function buildV2ParameterChanges() {
    const changes = {};
    
    // Build V2.0 formula_optimization_v2 parameters
    const v2Config = {
        enabled: true,
        exponential_form: {
            enabled: true
        },
        dynamic_blending: {
            adaptation_gameweek: parseInt(document.getElementById('adaptationGameweek')?.value || 16)
        },
        normalized_xgi: {
            enabled: document.getElementById('xgiEnabled')?.checked || false,
            normalization_strength: parseFloat(document.getElementById('xgiStrength')?.value || 1.0),
            position_adjustments: {
                defenders: true,
                midfielders: true,
                forwards: true
            }
        },
        multiplier_caps: {
            form: parseFloat(document.getElementById('formCap')?.value || 2.0),
            fixture: parseFloat(document.getElementById('fixtureCap')?.value || 1.8),
            xgi: parseFloat(document.getElementById('xgiCap')?.value || 2.5),
            global: parseFloat(document.getElementById('globalCap')?.value || 3.0)
        },
        ewma_form: {
            alpha: parseFloat(document.getElementById('ewmaAlpha')?.value || 0.87)
        }
    };
    
    // Only include if different from current config
    const currentV2 = currentConfig.formula_optimization_v2 || {};
    if (JSON.stringify(v2Config) !== JSON.stringify(currentV2)) {
        changes.formula_optimization_v2 = v2Config;
    }
    
    return changes;
}

function handleParameterChange() {
    pendingChanges = buildV2ParameterChanges();
    
    // Update Apply Changes button state
    const applyBtn = document.getElementById('applyChanges');
    const hasPending = Object.keys(pendingChanges).length > 0;
    
    if (applyBtn) {
        applyBtn.disabled = !hasPending;
        applyBtn.textContent = hasPending ? 'Apply Changes' : 'No Changes';
    }
}

function applyParameterChanges() {
    if (Object.keys(pendingChanges).length === 0) {
        console.log('⚠️ No pending changes to apply');
        return;
    }
    
    console.log('🔄 Applying V2.0 parameter changes:', pendingChanges);
    
    const applyBtn = document.getElementById('applyChanges');
    if (applyBtn) {
        applyBtn.textContent = 'Applying...';
        applyBtn.disabled = true;
    }
    
    fetch('/api/update-parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(pendingChanges)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ V2.0 parameters updated successfully');
            pendingChanges = {};
            currentConfig = { ...currentConfig, ...data.updated_config || {} };
            
            // Refresh player data with new calculations
            loadPlayersData();
            
            if (applyBtn) {
                applyBtn.textContent = 'Applied ✓';
                setTimeout(() => {
                    applyBtn.textContent = 'Apply Changes';
                    applyBtn.disabled = true;
                }, 2000);
            }
        } else {
            console.error('❌ Parameter update failed:', data.error);
            alert('Failed to update parameters: ' + data.error);
            
            if (applyBtn) {
                applyBtn.textContent = 'Apply Changes';
                applyBtn.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('❌ Parameter update error:', error);
        alert('Error updating parameters. Check console for details.');
        
        if (applyBtn) {
            applyBtn.textContent = 'Apply Changes';
            applyBtn.disabled = false;
        }
    });
}

function loadSystemConfiguration() {
    console.log('📥 Loading V2.0 system configuration...');
    
    fetch('/api/config')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentConfig = data.config;
            updateV2ControlsFromConfig();
            console.log('✅ V2.0 configuration loaded');
        } else {
            console.error('❌ Failed to load configuration:', data.error);
        }
    })
    .catch(error => {
        console.error('❌ Configuration load error:', error);
    });
}

function updateV2ControlsFromConfig() {
    const v2Config = currentConfig.formula_optimization_v2 || {};
    
    // Update EWMA Alpha
    const alpha = v2Config.ewma_form?.alpha || 0.87;
    const alphaSlider = document.getElementById('ewmaAlpha');
    const alphaValue = document.getElementById('ewmaAlphaValue');
    if (alphaSlider) alphaSlider.value = alpha;
    if (alphaValue) alphaValue.textContent = alpha;
    
    // Update Adaptation Gameweek
    const adaptationGW = v2Config.dynamic_blending?.adaptation_gameweek || 16;
    const adaptationSlider = document.getElementById('adaptationGameweek');
    const adaptationValue = document.getElementById('adaptationGameweekValue');
    if (adaptationSlider) adaptationSlider.value = adaptationGW;
    if (adaptationValue) adaptationValue.textContent = adaptationGW;
    
    // Update xGI settings
    const xgiEnabled = v2Config.normalized_xgi?.enabled || false;
    const xgiToggle = document.getElementById('xgiEnabled');
    const xgiControls = document.getElementById('xgiControls');
    if (xgiToggle) xgiToggle.checked = xgiEnabled;
    if (xgiControls) xgiControls.style.display = xgiEnabled ? 'block' : 'none';
    
    const xgiStrength = v2Config.normalized_xgi?.normalization_strength || 1.0;
    const xgiStrengthSlider = document.getElementById('xgiStrength');
    const xgiStrengthValue = document.getElementById('xgiStrengthValue');
    if (xgiStrengthSlider) xgiStrengthSlider.value = xgiStrength;
    if (xgiStrengthValue) xgiStrengthValue.textContent = xgiStrength;
    
    // Update Multiplier Caps
    const caps = v2Config.multiplier_caps || {};
    const capMappings = [
        { id: 'formCap', key: 'form', default: 2.0 },
        { id: 'fixtureCap', key: 'fixture', default: 1.8 },
        { id: 'xgiCap', key: 'xgi', default: 2.5 },
        { id: 'globalCap', key: 'global', default: 3.0 }
    ];
    
    capMappings.forEach(({ id, key, default: defaultValue }) => {
        const value = caps[key] || defaultValue;
        const slider = document.getElementById(id);
        const valueSpan = document.getElementById(id + 'Value');
        if (slider) slider.value = value;
        if (valueSpan) valueSpan.textContent = value;
    });
}

function loadPlayersData() {
    console.log('📥 Loading V2.0 player data...');
    
    fetch('/api/players')
    .then(response => response.json())
    .then(data => {
        if (data.players && Array.isArray(data.players)) {
            playersData = data.players;
            
            // Update gameweek status indicator
            updateGameweekStatus(data.gameweek_info);
            
            populateTeamFilter();
            updatePlayerTable();
            console.log(`✅ Loaded ${playersData.length} players with V2.0 calculations`);
        } else {
            console.error('❌ Failed to load player data:', data.error || 'No players data found');
        }
    })
    .catch(error => {
        console.error('❌ Player data load error:', error);
        updateGameweekStatus({ error: 'Failed to load gameweek data' });
    });
}

function updateGameweekStatus(gameweekInfo) {
    const statusElement = document.getElementById('gameweekStatus');
    const statusText = statusElement.querySelector('.status-text');
    const freshnessText = statusElement.querySelector('.freshness-text');
    
    if (gameweekInfo && gameweekInfo.current_gameweek) {
        // Update status badge
        statusText.textContent = `Currently viewing: Gameweek ${gameweekInfo.current_gameweek}`;
        
        // Update freshness indicator
        const now = new Date();
        const timeString = now.toLocaleString('en-GB', {
            day: '2-digit',
            month: 'short', 
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const detectionInfo = gameweekInfo.detection_method === 'GameweekManager' 
            ? 'Auto-detected' 
            : gameweekInfo.data_source;
            
        freshnessText.textContent = `${detectionInfo} | Updated: ${timeString}`;
        
        // Add protection indicator if active
        if (gameweekInfo.emergency_protection_active) {
            statusText.innerHTML += ' <span style="color: #28a745; font-size: 12px;">🛡️ GW1 Protected</span>';
        }
        
        console.log(`🎯 Gameweek status updated: GW${gameweekInfo.current_gameweek}`);
    } else {
        statusText.textContent = 'Gameweek detection failed';
        freshnessText.textContent = 'Unable to determine data status';
    }
}

function updatePlayerTable() {
    const filteredData = filterPlayers();
    const paginatedData = paginateData(filteredData);
    
    populateTable(paginatedData);
    updatePaginationInfo(filteredData.length);
    updatePlayerCount(filteredData.length);
}

function filterPlayers() {
    return playersData.filter(player => {
        // Position filter
        if (currentFilters.positions.length > 0 && 
            !currentFilters.positions.includes(player.position)) {
            return false;
        }
        
        // Price filter
        if (player.price < currentFilters.priceMin || 
            player.price > currentFilters.priceMax) {
            return false;
        }
        
        // Team filter
        if (currentFilters.teams.length > 0 && 
            !currentFilters.teams.includes(player.team)) {
            return false;
        }
        
        // Search filter
        if (currentFilters.search && 
            !player.name.toLowerCase().includes(currentFilters.search.toLowerCase())) {
            return false;
        }
        
        return true;
    });
}

function populateTable(data) {
    const tbody = document.getElementById('playersTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    data.forEach(player => {
        const row = createPlayerRow(player);
        tbody.appendChild(row);
    });
}

function createPlayerRow(player) {
    const row = document.createElement('tr');
    
    // Apply row classes based on player data
    if (player.true_value > 15) row.classList.add('high-value');
    if (player.roi > 3) row.classList.add('high-roi');
    
    row.innerHTML = `
        <td class="player-name">${player.name}</td>
        <td class="team">${player.team}</td>
        <td class="position ${player.position.toLowerCase()}">${player.position}</td>
        <td class="price">£${player.price}</td>
        <td class="ppg">${formatNumber(player.ppg, 1)}</td>
        <td class="pps">${formatNumber(player.pps || 0, 1)}</td>
        <td class="games">${formatGamesDisplay(player)}</td>
        <td class="true-value highlight">${formatNumber(player.true_value, 3)}</td>
        <td class="roi highlight">${formatNumber(player.roi, 3)}</td>
        <td class="form">${formatMultiplier(player.form_multiplier)}</td>
        <td class="fixture">${formatMultiplier(player.fixture_multiplier)}</td>
        <td class="starter">${formatMultiplier(player.starter_multiplier)}</td>
        <td class="xgi">${formatMultiplier(player.xgi_multiplier)}</td>
        <td class="starter-override">${createOverrideControls(player)}</td>
        <td class="xgi90">${formatNumber(player.xgi90, 3)}</td>
        <td class="xgi90-h">${formatNumber(player.xgi90_h, 3)}</td>
        <td class="minutes">${player.minutes || 0}</td>
    `;
    
    return row;
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    return Number(value).toFixed(decimals);
}

function formatMultiplier(value) {
    if (value === null || value === undefined || isNaN(value)) return '1.00x';
    return Number(value).toFixed(2) + 'x';
}

function formatGamesDisplay(player) {
    const currentGames = player.games_current || 0;
    const historicalGames = player.games_historical || 0;
    
    if (currentGames === 0) {
        return `${historicalGames} (24-25)`;
    } else if (currentGames < 5) {
        return `${historicalGames}+${currentGames}`;
    } else {
        return `${currentGames}`;
    }
}

function createOverrideControls(player) {
    const currentOverride = player.starter_override || 'A';
    const options = [
        { value: 'S', label: 'S', title: 'Starter' },
        { value: 'B', label: 'B', title: 'Bench' },
        { value: 'O', label: 'O', title: 'Out' },
        { value: 'A', label: 'A', title: 'Auto' }
    ];
    
    return options.map(opt => 
        `<button class="override-btn ${opt.value === currentOverride ? 'active' : ''}" 
                 data-player-id="${player.id}" 
                 data-override="${opt.value}" 
                 title="${opt.title}">${opt.label}</button>`
    ).join('');
}

// Additional utility functions for the table
function handlePositionFilter(button) {
    const position = button.dataset.position;
    
    // Remove active class from all position buttons
    document.querySelectorAll('.position-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to clicked button
    button.classList.add('active');
    
    // Update filters
    if (position === 'all') {
        currentFilters.positions = ['G', 'D', 'M', 'F'];
    } else {
        currentFilters.positions = [position];
    }
    
    currentPage = 0;
    updatePlayerTable();
}

function handleFiltersChange() {
    // Update price filters
    const priceMin = document.getElementById('priceMin');
    const priceMax = document.getElementById('priceMax');
    if (priceMin) currentFilters.priceMin = parseFloat(priceMin.value) || 4.0;
    if (priceMax) currentFilters.priceMax = parseFloat(priceMax.value) || 15.0;
    
    // Update team filter
    const teamFilter = document.getElementById('teamFilter');
    if (teamFilter) {
        currentFilters.teams = teamFilter.value === 'all' ? [] : [teamFilter.value];
    }
    
    // Update search filter
    const searchInput = document.getElementById('playerSearch');
    if (searchInput) {
        currentFilters.search = searchInput.value.trim();
    }
    
    currentPage = 0;
    updatePlayerTable();
}

function populateTeamFilter() {
    const teamFilter = document.getElementById('teamFilter');
    if (!teamFilter) return;
    
    const teams = [...new Set(playersData.map(p => p.team))].sort();
    
    teamFilter.innerHTML = '<option value="all">All Teams</option>';
    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        teamFilter.appendChild(option);
    });
}

function paginateData(data) {
    if (pageSize >= 999999) return data;
    
    const startIndex = currentPage * pageSize;
    const endIndex = startIndex + pageSize;
    return data.slice(startIndex, endIndex);
}

function changePage(direction) {
    const filteredData = filterPlayers();
    const totalPages = Math.ceil(filteredData.length / pageSize);
    
    currentPage += direction;
    
    if (currentPage < 0) currentPage = 0;
    if (currentPage >= totalPages) currentPage = totalPages - 1;
    
    updatePlayerTable();
}

function updatePaginationInfo(totalCount) {
    const pageInfo = document.getElementById('pageInfo');
    if (!pageInfo) return;
    
    if (pageSize >= 999999) {
        pageInfo.textContent = `Showing all ${totalCount} players`;
    } else {
        const totalPages = Math.ceil(totalCount / pageSize);
        const currentPageDisplay = totalPages === 0 ? 0 : currentPage + 1;
        pageInfo.textContent = `Page ${currentPageDisplay} of ${totalPages}`;
    }
}

function updatePlayerCount(count) {
    const playerCountSpan = document.getElementById('playerCount');
    if (playerCountSpan) {
        playerCountSpan.textContent = count;
    }
}

// Validation functions
function runValidation() {
    console.log('🏃 Running V2.0 model validation...');
    
    const btn = document.getElementById('runValidation');
    if (btn) {
        btn.textContent = 'Running...';
        btn.disabled = true;
    }
    
    fetch('/api/run-validation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ formula_version: 'v2.0' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateValidationDisplay(data.validation_results);
            console.log('✅ V2.0 validation completed');
        } else {
            console.error('❌ Validation failed:', data.error);
            alert('Validation failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('❌ Validation error:', error);
        alert('Validation error. Check console for details.');
    })
    .finally(() => {
        if (btn) {
            btn.textContent = '🏃 Run Validation';
            btn.disabled = false;
        }
    });
}

function updateValidationDisplay(results) {
    const rmseValue = document.getElementById('rmse-value');
    const correlationValue = document.getElementById('correlation-value');
    const precisionValue = document.getElementById('precision-value');
    
    if (rmseValue) rmseValue.textContent = results.rmse?.toFixed(2) || '--';
    if (correlationValue) correlationValue.textContent = results.correlation?.toFixed(3) || '--';
    if (precisionValue) precisionValue.textContent = results.precision_at_20?.toFixed(1) + '%' || '--';
    
    // Update status indicator
    const statusIndicator = document.querySelector('.status-indicator');
    if (statusIndicator) {
        statusIndicator.className = 'status-indicator available';
    }
}

function viewValidationResults() {
    window.open('/api/validation-dashboard', '_blank');
}

// Additional API functions
function syncUnderstatData() {
    console.log('🔄 Syncing Understat data...');
    
    const btn = document.getElementById('syncUnderstat');
    if (btn) {
        btn.textContent = 'Syncing...';
        btn.disabled = true;
    }
    
    fetch('/api/understat/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ Understat sync completed');
            loadPlayersData(); // Refresh data
        } else {
            console.error('❌ Understat sync failed:', data.error);
            alert('Sync failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('❌ Sync error:', error);
        alert('Sync error. Check console for details.');
    })
    .finally(() => {
        if (btn) {
            btn.textContent = 'Sync Understat Data';
            btn.disabled = false;
        }
    });
}

function importLineup() {
    // This would typically open a file input dialog
    // For now, redirect to the lineup import page
    window.open('/import-validation', '_blank');
}

function exportToCSV() {
    const filteredData = filterPlayers();
    
    if (filteredData.length === 0) {
        alert('No data to export');
        return;
    }
    
    // Create CSV content
    const headers = [
        'Name', 'Team', 'Position', 'Price', 'PPG', 'PPS', 'Games',
        'True Value', 'ROI', 'Form', 'Fixture', 'Starter', 'xGI',
        'xGI90', 'xGI90_H', 'Minutes'
    ];
    
    const csvContent = [
        headers.join(','),
        ...filteredData.map(player => [
            `"${player.name}"`,
            player.team,
            player.position,
            player.price,
            player.ppg || 0,
            player.pps || 0,
            player.games_current || 0,
            player.true_value || 0,
            player.roi || 0,
            player.form_multiplier || 1,
            player.fixture_multiplier || 1,
            player.starter_multiplier || 1,
            player.xgi_multiplier || 1,
            player.xgi90 || 0,
            player.xgi90_h || 0,
            player.minutes || 0
        ].join(','))
    ].join('\n');
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fantrax-players-v2-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for potential external use
window.FantraxDashboard = {
    loadPlayersData,
    applyParameterChanges,
    exportToCSV,
    runValidation
};