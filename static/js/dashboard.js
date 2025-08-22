// Fantrax Value Hunter Dashboard JavaScript
// Handles parameter controls, player table, and API communication

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
    priceMin: 5.0,
    priceMax: 25.0,
    teams: [],
    search: ''
};

// Column information database for tooltips
const columnInfo = {
    'name': {
        title: 'Player Name',
        description: 'Full name of the Premier League player',
        interpretation: 'Click on any column header to sort by that field'
    },
    'team': {
        title: 'Team Code',
        description: 'Three-letter abbreviation for player\'s current club',
        interpretation: 'Use team filter to focus on specific clubs'
    },
    'position': {
        title: 'Position',
        description: 'Primary playing position',
        interpretation: {
            'G': '🥅 Goalkeeper',
            'D': '🛡️ Defender', 
            'M': '⚡ Midfielder',
            'F': '⚽ Forward'
        }
    },
    'price': {
        title: 'Player Price',
        description: 'Current salary cost in your $100 budget',
        interpretation: 'Lower prices leave more budget for other positions',
        usage: 'Price range filter helps find value options'
    },
    'ppg': {
        title: 'Points Per Game',
        description: 'Average fantasy points per match',
        interpretation: 'Based on historical or current season data',
        formula: 'Total Points ÷ Games Played',
        note: 'Raw scoring rate before multiplier adjustments'
    },
    'value_score': {
        title: 'Points Per Dollar (PP$)',
        description: 'Raw value efficiency metric',
        interpretation: {
            'excellent': '🟢 ≥0.7 - Elite value',
            'good': '🔵 0.5-0.7 - Good value', 
            'average': '🟡 0.3-0.5 - Fair value',
            'poor': '🔴 <0.3 - Poor value'
        },
        formula: 'PPG ÷ Price',
        usage: 'Starting point before True Value adjustments'
    },
    'games': {
        title: 'Games Played',
        description: 'Number of matches used in calculations',
        interpretation: {
            'reliable': '🟢 ≥10 games - Highly reliable data',
            'moderate': '🟡 5-9 games - Use with caution',
            'unreliable': '🔴 <5 games - Limited sample size'
        },
        note: 'Early season shows "38 (24-25)" for historical data, later shows current season games or blended format "38+5"'
    },
    'true_value': {
        title: 'True Value Score',
        description: 'Complete value assessment incorporating all factors',
        interpretation: 'PP$ adjusted for form, fixtures, starting likelihood, and attacking threat',
        formula: 'PP$ × Form × Fixture × Starter × xGI',
        usage: '⭐ Primary metric for lineup decisions - sorts by this by default'
    },
    'form_multiplier': {
        title: 'Form Multiplier',
        description: 'Recent performance vs season average',
        interpretation: {
            'hot': '🔥 >1.1x - On fire',
            'normal': '➖ 0.9-1.1x - Steady performance',
            'cold': '🥶 <0.9x - Poor recent form'
        },
        calculation: 'Weighted average of recent games vs baseline'
    },
    'fixture_multiplier': {
        title: 'Fixture Difficulty',
        description: 'Opponent strength adjustment based on betting odds',
        interpretation: {
            'easy': '🟢 >1.1x - Favorable matchup',
            'neutral': '➖ 0.9-1.1x - Average difficulty', 
            'hard': '🔴 <0.9x - Tough opponent'
        },
        source: 'Real betting odds converted to 21-point difficulty scale'
    },
    'starter_multiplier': {
        title: 'Starter Prediction',
        description: 'Likelihood to start or play significant minutes',
        values: {
            'starter': '✅ 1.0x - Predicted starter',
            'rotation': '⚠️ ~0.65x - Rotation risk',
            'bench': '🪑 ~0.6x - Likely benched',
            'out': '❌ 0.0x - Injured/suspended'
        },
        source: 'Based on lineup predictions and manual overrides'
    },
    'xgi_multiplier': {
        title: 'xGI Multiplier',
        description: 'Expected Goals + Assists impact on scoring potential',
        interpretation: 'Attacking threat adjustment based on xG90 + xA90 data',
        formula: 'Various modes: Direct (xGI90 × strength), Adjusted (1 + xGI90 × strength), or Capped',
        note: 'Higher for players with greater goal/assist potential'
    },
    'manual_override': {
        title: 'Starter Override',
        description: 'Manual starter prediction override for specific players',
        interpretation: 'User-defined starter status to override automated predictions',
        usage: 'Use when you have insider knowledge about lineups or disagree with predictions',
        input: 'Select: Starter (1.0x), Bench (~0.6x), Out (0.0x), or Auto (use prediction)'
    },
    'xg90': {
        title: 'Expected Goals per 90',
        description: 'Goal probability per full match played',
        interpretation: {
            'elite': '🔥 >0.5 - Elite finisher',
            'good': '⚽ 0.3-0.5 - Regular scorer',
            'low': '🎯 <0.3 - Limited goal threat'
        },
        source: 'Understat.com advanced statistics'
    },
    'xa90': {
        title: 'Expected Assists per 90', 
        description: 'Assist probability per full match played',
        interpretation: 'Measures creative output and chance creation ability',
        note: 'Important for midfielders and attacking players',
        source: 'Understat.com advanced statistics'
    },
    'xgi90': {
        title: 'Expected Goal Involvement per 90',
        description: 'Combined attacking contribution per match',
        formula: 'xG90 + xA90',
        usage: 'Overall attacking threat metric - higher values boost xGI multiplier',
        interpretation: 'Total expected goals and assists per 90 minutes'
    },
    'minutes': {
        title: 'Total Minutes Played',
        description: 'Season minutes across all competitions',
        interpretation: 'Indicates playing time and fitness levels',
        usage: 'Higher minutes suggest regular starts and manager trust'
    }
};

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Fantrax Value Hunter Dashboard initializing...');
    
    // Load initial configuration and data
    loadSystemConfig();
    loadTeams();
    loadPlayersData();
    
    // Set up event listeners
    setupParameterControls();
    setupTableControls();
    setupFilterControls();
    setupThemeToggle();
    setupFormulaVersionToggle();
    setupValidationStatusIndicators();
    
    console.log('✅ Dashboard initialization complete');
});

// =================================================================
// CONFIGURATION AND DATA LOADING
// =================================================================

async function loadSystemConfig() {
    try {
        console.log('📡 Loading system configuration...');
        const response = await fetch('/api/config');
        const result = await response.json();
        
        if (result.success) {
            currentConfig = result.parameters;
            updateUIFromConfig();
            console.log('✅ Configuration loaded');
        } else {
            showError('Failed to load system configuration: ' + result.error);
        }
    } catch (error) {
        console.error('❌ Error loading configuration:', error);
        showError('Network error loading configuration');
    }
}

async function loadTeams() {
    try {
        console.log('📡 Loading teams list...');
        const response = await fetch('/api/teams');
        const result = await response.json();
        
        if (response.ok) {
            populateTeamDropdown(result.teams);
            console.log(`✅ Loaded ${result.count} teams`);
        } else {
            throw new Error(result.error || 'Failed to load teams');
        }
    } catch (error) {
        console.error('❌ Error loading teams:', error);
        showError('Failed to load teams: ' + error.message);
    }
}

function populateTeamDropdown(teams) {
    const teamSelect = document.getElementById('team-select');
    if (!teamSelect) {
        console.warn('⚠️ Team dropdown not found');
        return;
    }
    
    // Clear existing options except "All Teams"
    teamSelect.innerHTML = '<option value="">All Teams</option>';
    
    // Add each team as an option
    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        teamSelect.appendChild(option);
    });
    
    console.log(`✅ Team dropdown populated with ${teams.length} teams`);
}

async function loadPlayersData() {
    try {
        console.log('📡 Loading 633 players data...');
        showLoadingOverlay('Loading player data...');
        
        // Build query parameters
        const params = new URLSearchParams({
            gameweek: 1,
            limit: pageSize,
            offset: currentPage * pageSize,
            sort_by: currentSort.field,
            sort_direction: currentSort.direction
        });
        
        // Add filters
        if (currentFilters.positions.length > 0 && currentFilters.positions.length < 4) {
            params.append('position', currentFilters.positions.join(','));
        }
        if (currentFilters.priceMin > 5.0) {
            params.append('min_price', currentFilters.priceMin);
        }
        if (currentFilters.priceMax < 25.0) {
            params.append('max_price', currentFilters.priceMax);
        }
        if (currentFilters.search) {
            params.append('search', currentFilters.search);
        }
        if (currentFilters.teams.length > 0) {
            params.append('team', currentFilters.teams.join(','));
        }
        
        const response = await fetch(`/api/players?${params.toString()}`);
        const result = await response.json();
        
        if (response.ok) {
            playersData = result.players;
            totalFilteredCount = result.filtered_count;
            updatePlayerTable();
            updatePaginationInfo(result.total_count, result.filtered_count);
            updateFilterCount(result.filtered_count);
            
            // Update status bar
            document.getElementById('player-count').textContent = `${result.total_count} players loaded`;
            document.getElementById('last-updated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            
            console.log(`✅ Loaded ${result.players.length} players (${result.filtered_count} filtered)`);
        } else {
            throw new Error(result.error || 'Failed to load players');
        }
    } catch (error) {
        console.error('❌ Error loading players:', error);
        showError('Failed to load player data: ' + error.message);
    } finally {
        hideLoadingOverlay();
    }
}

// =================================================================
// UI UPDATE FUNCTIONS
// =================================================================

function updateUIFromConfig() {
    if (!currentConfig) return;
    
    // Form calculation controls
    const formCalc = currentConfig.form_calculation || {};
    document.getElementById('form-enabled').checked = formCalc.enabled || false;
    document.getElementById('lookback-period').value = formCalc.lookback_period || 5;
    document.getElementById('min-games').value = formCalc.minimum_games_for_form || 3;
    document.getElementById('baseline-switchover').value = formCalc.baseline_switchover_gameweek || 10;
    updateSlider('form-strength-slider', formCalc.form_strength || 1.0);
    
    // Fixture difficulty controls (odds-based)
    const fixtureDiff = currentConfig.fixture_difficulty || {};
    document.getElementById('fixture-enabled').checked = fixtureDiff.enabled || false;
    
    // Set preset
    const presetSelect = document.getElementById('fixture-preset');
    const currentStrength = fixtureDiff.multiplier_strength || 0.2;
    if (currentStrength === 0.1) {
        presetSelect.value = 'conservative';
    } else if (currentStrength === 0.3) {
        presetSelect.value = 'aggressive';
    } else if (currentStrength === 0.2) {
        presetSelect.value = 'balanced';
    } else {
        presetSelect.value = 'custom';
    }
    
    // Update multiplier strength
    updateSlider('multiplier-strength-slider', currentStrength);
    
    // Update position weights
    const positionWeights = fixtureDiff.position_weights || {};
    updateSlider('goalkeeper-weight-slider', positionWeights.G || 1.10);
    updateSlider('defender-weight-slider', positionWeights.D || 1.20);
    updateSlider('midfielder-weight-slider', positionWeights.M || 1.00);
    updateSlider('forward-weight-slider', positionWeights.F || 1.05);
    
    // Starter prediction controls
    const starterPred = currentConfig.starter_prediction || {};
    document.getElementById('starter-enabled').checked = starterPred.enabled || false;
    updateSlider('rotation-penalty-slider', starterPred.auto_rotation_penalty || 0.65);
    updateSlider('bench-penalty-slider', starterPred.force_bench_penalty || 0.6);
    
    // xGI Integration controls
    const xgiIntegration = currentConfig.xgi_integration || {};
    document.getElementById('xgiEnabled').checked = xgiIntegration.enabled || false;
    document.getElementById('xgiMode').value = xgiIntegration.multiplier_mode || 'direct';
    document.getElementById('xgiStrength').value = xgiIntegration.multiplier_strength || 1.0;
    document.getElementById('xgiStrengthValue').textContent = xgiIntegration.multiplier_strength || 1.0;
    
    // Blender Display controls
    const gamesDisplay = currentConfig.games_display || {};
    document.getElementById('gamesDisplayEnabled').checked = true; // Always enabled for now
    document.getElementById('baselineSwitchover').value = gamesDisplay.baseline_switchover_gameweek || 10;
    document.getElementById('transitionEnd').value = gamesDisplay.transition_period_end || 15;
    document.getElementById('showHistorical').checked = gamesDisplay.show_historical_data !== false;
    
    // Update control section visibility
    updateControlVisibility();
    
}

function updateSlider(sliderId, value) {
    const slider = document.getElementById(sliderId);
    const display = document.getElementById(sliderId.replace('-slider', '-display'));
    
    if (slider && display) {
        slider.value = value;
        // Handle different display formats
        if (sliderId.includes('multiplier-strength')) {
            display.textContent = `±${(value * 100).toFixed(0)}%`;
        } else if (sliderId.includes('weight')) {
            display.textContent = `${(value * 100).toFixed(0)}%`;
        } else {
            display.textContent = value.toFixed(2) + 'x';
        }
    }
}

function handleFixturePresetChange() {
    const preset = document.getElementById('fixture-preset').value;
    
    if (preset !== 'custom') {
        const presets = {
            'conservative': { strength: 0.1 },
            'balanced': { strength: 0.2 },
            'aggressive': { strength: 0.3 }
        };
        
        if (presets[preset]) {
            updateSlider('multiplier-strength-slider', presets[preset].strength);
            handleParameterChange();
        }
    }
}

function updateControlVisibility() {
    // Form controls
    const formEnabled = document.getElementById('form-enabled').checked;
    document.getElementById('form-controls').style.opacity = formEnabled ? '1' : '0.5';
    
    // Fixture controls
    const fixtureEnabled = document.getElementById('fixture-enabled').checked;
    document.getElementById('fixture-controls').style.opacity = fixtureEnabled ? '1' : '0.5';
    
    // Starter controls
    const starterEnabled = document.getElementById('starter-enabled').checked;
    document.getElementById('starter-controls').style.opacity = starterEnabled ? '1' : '0.5';
    
    // xGI controls
    const xgiEnabled = document.getElementById('xgiEnabled').checked;
    document.getElementById('xgiContent').style.opacity = xgiEnabled ? '1' : '0.5';
    
    // Blender Display controls (always enabled for now)
    const gamesDisplayEnabled = document.getElementById('gamesDisplayEnabled').checked;
    document.getElementById('gamesDisplayContent').style.opacity = gamesDisplayEnabled ? '1' : '0.5';
}


// =================================================================
// PLAYER TABLE FUNCTIONS
// =================================================================

function getGamesClass(player) {
    const gamesCount = parseInt(player.games_played_historical) || 0;
    if (gamesCount >= 10) return 'games-reliable';
    if (gamesCount >= 5) return 'games-moderate';
    return 'games-unreliable';
}

function updatePlayerTable() {
    const tbody = document.getElementById('player-table-body');
    
    if (!playersData || playersData.length === 0) {
        tbody.innerHTML = '<tr class="loading-row"><td colspan="18">No players found</td></tr>';
        return;
    }
    
    const rows = playersData.map(player => {
        const trueValue = parseFloat(player.true_value || 0);
        const valueClass = trueValue > 1.0 ? 'value-high' : trueValue > 0.5 ? 'value-medium' : 'value-low';
        const playerId = player.id;
        
        const ppValue = parseFloat(player.value_score || 0);
        const ppClass = ppValue >= 0.7 ? 'pp-excellent' : ppValue >= 0.5 ? 'pp-good' : ppValue >= 0.3 ? 'pp-average' : 'pp-poor';
        
        // ROI calculation and styling
        const roiValue = parseFloat(player.roi || 0);
        const roiClass = roiValue >= 1.2 ? 'roi-excellent' : roiValue >= 1.0 ? 'roi-good' : roiValue >= 0.8 ? 'roi-average' : 'roi-poor';
        
        return `
            <tr>
                <td><strong>${escapeHtml(player.name || 'Unknown')}</strong></td>
                <td>${escapeHtml(player.team || 'N/A')}</td>
                <td>${escapeHtml(player.position || 'N/A')}</td>
                <td>$${parseFloat(player.price || 0).toFixed(1)}</td>
                <td>${parseFloat(player.ppg || 0).toFixed(1)}</td>
                <td class="${ppClass}">${ppValue.toFixed(3)}</td>
                <td class="${getGamesClass(player)}" data-sort="${player.games_total || 0}">${player.games_display || '0'}</td>
                <td class="${valueClass} ${getFormulaVersion() === 'v2.0' ? 'true-value-enhanced' : ''}">${trueValue.toFixed(3)}</td>
                <td class="roi-value ${roiClass}">${roiValue.toFixed(3)}</td>
                <td>${parseFloat(player.form_multiplier || 1.0).toFixed(2)}x</td>
                <td>${parseFloat(player.fixture_multiplier || 1.0).toFixed(2)}x</td>
                <td>${parseFloat(player.starter_multiplier || 1.0).toFixed(2)}x</td>
                <td>${parseFloat(player.xgi_multiplier || 1.0).toFixed(2)}x</td>
                <td class="manual-override-cell">
                    <div class="override-checkboxes">
                        <label title="Force Starter (1.0x)">
                            <input type="radio" name="override-${playerId}" value="starter" onchange="handleManualOverride('${playerId}', 'starter')">
                            S
                        </label>
                        <label title="Force Bench (penalty)">
                            <input type="radio" name="override-${playerId}" value="bench" onchange="handleManualOverride('${playerId}', 'bench')">
                            B
                        </label>
                        <label title="Force Out (0.0x)">
                            <input type="radio" name="override-${playerId}" value="out" onchange="handleManualOverride('${playerId}', 'out')">
                            O
                        </label>
                        <label title="Auto (use prediction)">
                            <input type="radio" name="override-${playerId}" value="auto" checked onchange="handleManualOverride('${playerId}', 'auto')">
                            A
                        </label>
                    </div>
                </td>
                <td>${parseFloat(player.xg90 || 0).toFixed(3)}</td>
                <td>${parseFloat(player.xa90 || 0).toFixed(3)}</td>
                <td>${parseFloat(player.xgi90 || 0).toFixed(3)}</td>
                <td>${player.minutes || 0}</td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = rows;
}

function updatePaginationInfo(totalCount, filteredCount) {
    const totalPages = Math.ceil(filteredCount / pageSize);
    const currentPageDisplay = totalPages > 0 ? currentPage + 1 : 0;
    
    document.getElementById('page-info').textContent = `Page ${currentPageDisplay} of ${totalPages}`;
    document.getElementById('prev-page').disabled = currentPage === 0;
    document.getElementById('next-page').disabled = currentPage >= totalPages - 1;
}

function updateFilterCount(count) {
    document.getElementById('filter-count').textContent = `Showing ${count} players`;
}

// Global state for manual overrides
let manualOverrides = {};

// =================================================================
// MANUAL OVERRIDE HANDLERS
// =================================================================

async function handleManualOverride(playerId, overrideType) {
    try {
        console.log('🔧 Applying manual override:', playerId, overrideType);
        
        // Call new immediate API endpoint
        const response = await fetch('/api/manual-override', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_id: playerId,
                override_type: overrideType,
                gameweek: 1
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ ${result.player_name}: ${overrideType} → ${result.new_multiplier.toFixed(2)}x → True Value: ${result.new_true_value.toFixed(3)}`);
            
            // Update the local data
            const player = playersData.find(p => p.id == playerId);
            if (player) {
                player.starter_multiplier = result.new_multiplier;
                player.true_value = result.new_true_value;
            }
            
            // Update the table display immediately
            updatePlayerRowInTable(playerId, result.new_multiplier, result.new_true_value);
            
            // Update global manual overrides tracking (for other features)
            if (overrideType === 'auto') {
                delete manualOverrides[playerId];
            } else {
                manualOverrides[playerId] = {
                    type: overrideType,
                    multiplier: result.new_multiplier
                };
            }
            
            // Show success feedback
            showBriefSuccess(`${result.player_name}: ${overrideType.toUpperCase()} (${result.new_multiplier.toFixed(2)}x)`);
            
        } else {
            console.error('❌ Manual override failed:', result.error);
            showError('Manual override failed: ' + result.error);
            
            // Reset radio button to previous state
            const radioButtons = document.querySelectorAll(`input[name="override-${playerId}"]`);
            radioButtons.forEach(radio => {
                if (radio.value === 'auto') radio.checked = true;
                else radio.checked = false;
            });
        }
        
    } catch (error) {
        console.error('❌ Manual override error:', error);
        showError('Network error applying manual override');
        
        // Reset radio button to previous state
        const radioButtons = document.querySelectorAll(`input[name="override-${playerId}"]`);
        radioButtons.forEach(radio => {
            if (radio.value === 'auto') radio.checked = true;
            else radio.checked = false;
        });
    }
}

function updatePlayerRowInTable(playerId, newMultiplier, newTrueValue) {
    // Find the correct row in the table
    const tableBody = document.getElementById('player-table-body');
    const rows = tableBody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const radioButtons = row.querySelectorAll(`input[name="override-${playerId}"]`);
        if (radioButtons.length > 0) {
            const cells = row.cells;
            
            // Update True Value (column 7 - after adding Games column)
            const valueClass = newTrueValue > 1.0 ? 'value-high' : newTrueValue > 0.5 ? 'value-medium' : 'value-low';
            cells[7].textContent = newTrueValue.toFixed(3);
            cells[7].className = valueClass;
            
            // Update Starter multiplier (column 13 - after adding Games column) with color coding
            cells[13].textContent = `${newMultiplier.toFixed(2)}x`;
            cells[13].style.fontWeight = 'bold';
            cells[13].style.color = newMultiplier === 1.0 ? '#28a745' : 
                                   newMultiplier === 0.0 ? '#dc3545' : '#ffc107';
            
            // Brief highlight animation
            cells[7].style.backgroundColor = '#fff3cd';
            cells[13].style.backgroundColor = '#fff3cd';
            setTimeout(() => {
                cells[7].style.backgroundColor = '';
                cells[13].style.backgroundColor = '';
            }, 1000);
            
            return;
        }
    });
}

function showBriefSuccess(message) {
    const indicator = document.getElementById('status-indicator');
    const originalText = indicator.textContent;
    const originalClass = indicator.className;
    
    indicator.textContent = '✅ ' + message;
    indicator.className = 'status-success';
    
    // Reset after 3 seconds
    setTimeout(() => {
        indicator.textContent = originalText;
        indicator.className = originalClass;
    }, 3000);
}

// =================================================================
// PARAMETER CONTROL HANDLERS
// =================================================================

function setupParameterControls() {
    // Form calculation controls
    document.getElementById('form-enabled').addEventListener('change', handleParameterChange);
    document.getElementById('lookback-period').addEventListener('change', handleParameterChange);
    document.getElementById('min-games').addEventListener('change', handleParameterChange);
    document.getElementById('baseline-switchover').addEventListener('change', handleParameterChange);
    setupSlider('form-strength-slider');
    
    // Fixture difficulty controls (odds-based)
    document.getElementById('fixture-enabled').addEventListener('change', handleParameterChange);
    document.getElementById('fixture-preset').addEventListener('change', handleFixturePresetChange);
    
    // Fixture sliders
    setupSlider('multiplier-strength-slider');
    setupSlider('goalkeeper-weight-slider');
    setupSlider('defender-weight-slider');
    setupSlider('midfielder-weight-slider');
    setupSlider('forward-weight-slider');
    
    // Starter prediction controls
    document.getElementById('starter-enabled').addEventListener('change', handleParameterChange);
    setupSlider('rotation-penalty-slider');
    setupSlider('bench-penalty-slider');
    
    // xGI Integration controls
    document.getElementById('xgiEnabled').addEventListener('change', handleParameterChange);
    document.getElementById('xgiMode').addEventListener('change', handleParameterChange);
    document.getElementById('xgiStrength').addEventListener('input', function() {
        document.getElementById('xgiStrengthValue').textContent = this.value;
        handleParameterChange();
    });
    document.getElementById('syncUnderstat').addEventListener('click', syncUnderstatData);
    
    // v2.0 Sync button (if it exists and is visible)
    const syncV2Button = document.getElementById('syncUnderstat-v2');
    if (syncV2Button) {
        syncV2Button.addEventListener('click', syncUnderstatData);
    }
    
    // Blender Display controls
    document.getElementById('gamesDisplayEnabled').addEventListener('change', handleParameterChange);
    document.getElementById('baselineSwitchover').addEventListener('change', handleParameterChange);
    document.getElementById('transitionEnd').addEventListener('change', handleParameterChange);
    document.getElementById('showHistorical').addEventListener('change', handleParameterChange);
    
    // Action buttons
    document.getElementById('apply-changes').addEventListener('click', applyChanges);
    document.getElementById('reset-defaults').addEventListener('click', resetToDefaults);
    document.getElementById('import-lineups').addEventListener('click', importLineups);
}

function setupSlider(sliderId) {
    const slider = document.getElementById(sliderId);
    slider.addEventListener('input', function() {
        const display = document.getElementById(sliderId.replace('-slider', '-display'));
        display.textContent = parseFloat(this.value).toFixed(2) + 'x';
        handleParameterChange();
    });
}

function handleParameterChange() {
    // Mark changes as pending
    pendingChanges = buildParameterChanges();
    
    // Show pending indicator
    const hasPendingChanges = Object.keys(pendingChanges).length > 0;
    document.getElementById('pending-changes').style.display = hasPendingChanges ? 'block' : 'none';
    document.getElementById('apply-changes').disabled = !hasPendingChanges;
    
    // Update control visibility
    updateControlVisibility();
    
    console.log('📝 Parameter changes pending:', pendingChanges);
}

function buildParameterChanges() {
    const changes = {};
    
    // Check current formula version
    const isV2Enhanced = currentFormulaVersion === 'v2.0';
    
    // Form calculation changes - different parameters for v1.0 vs v2.0
    const formEnabled = document.getElementById('form-enabled').checked;
    const lookbackPeriod = parseInt(document.getElementById('lookback-period').value);
    const minGames = parseInt(document.getElementById('min-games').value);
    const baselineSwitchover = parseInt(document.getElementById('baseline-switchover').value);
    const formStrength = parseFloat(document.getElementById('form-strength-slider').value);
    
    if (isV2Enhanced) {
        // v2.0 Enhanced: Use EWMA exponential form parameters
        const currentV2Config = currentConfig.formula_optimization_v2?.exponential_form || {};
        
        if (formEnabled !== (currentV2Config.enabled !== false) ||
            Math.abs(formStrength - (currentV2Config.alpha || 0.87)) > 0.01) {
            changes.formula_optimization_v2 = {
                exponential_form: {
                    enabled: formEnabled,
                    alpha: formStrength  // In v2.0, form strength slider controls EWMA alpha (0.87 default)
                }
            };
        }
    } else {
        // v1.0 Legacy: Use traditional form calculation parameters
        if (formEnabled !== (currentConfig.form_calculation?.enabled || false) ||
            lookbackPeriod !== (currentConfig.form_calculation?.lookback_period || 5) ||
            minGames !== (currentConfig.form_calculation?.minimum_games_for_form || 3) ||
            baselineSwitchover !== (currentConfig.form_calculation?.baseline_switchover_gameweek || 10) ||
            Math.abs(formStrength - (currentConfig.form_calculation?.form_strength || 1.0)) > 0.01) {
            changes.form_calculation = {
                enabled: formEnabled,
                lookback_period: lookbackPeriod,
                minimum_games_for_form: minGames,
                baseline_switchover_gameweek: baselineSwitchover,
                form_strength: formStrength
            };
        }
    }
    
    // Fixture difficulty changes (odds-based)
    const fixtureEnabled = document.getElementById('fixture-enabled').checked;
    const multiplierStrength = parseFloat(document.getElementById('multiplier-strength-slider').value);
    const goalkeeperWeight = parseFloat(document.getElementById('goalkeeper-weight-slider').value);
    const defenderWeight = parseFloat(document.getElementById('defender-weight-slider').value);
    const midfielderWeight = parseFloat(document.getElementById('midfielder-weight-slider').value);
    const forwardWeight = parseFloat(document.getElementById('forward-weight-slider').value);
    
    const currentFixture = currentConfig.fixture_difficulty || {};
    const currentPositionWeights = currentFixture.position_weights || {};
    
    if (fixtureEnabled !== (currentFixture.enabled || false) ||
        Math.abs(multiplierStrength - (currentFixture.multiplier_strength || 0.2)) > 0.01 ||
        Math.abs(goalkeeperWeight - (currentPositionWeights.G || 1.10)) > 0.01 ||
        Math.abs(defenderWeight - (currentPositionWeights.D || 1.20)) > 0.01 ||
        Math.abs(midfielderWeight - (currentPositionWeights.M || 1.00)) > 0.01 ||
        Math.abs(forwardWeight - (currentPositionWeights.F || 1.05)) > 0.01) {
        
        changes.fixture_difficulty = {
            enabled: fixtureEnabled,
            mode: 'odds_based',
            multiplier_strength: multiplierStrength,
            position_weights: {
                G: goalkeeperWeight,
                D: defenderWeight,
                M: midfielderWeight,
                F: forwardWeight
            }
        };
    }
    
    // Starter prediction changes
    const starterEnabled = document.getElementById('starter-enabled').checked;
    const rotationPenalty = parseFloat(document.getElementById('rotation-penalty-slider').value);
    const benchPenalty = parseFloat(document.getElementById('bench-penalty-slider').value);
    
    if (starterEnabled !== (currentConfig.starter_prediction?.enabled || false) ||
        Math.abs(rotationPenalty - (currentConfig.starter_prediction?.auto_rotation_penalty || 0.65)) > 0.01 ||
        Math.abs(benchPenalty - (currentConfig.starter_prediction?.force_bench_penalty || 0.6)) > 0.01) {
        changes.starter_prediction = {
            enabled: starterEnabled,
            auto_rotation_penalty: rotationPenalty,
            force_bench_penalty: benchPenalty
        };
    }
    
    // xGI Integration changes
    const xgiEnabled = document.getElementById('xgiEnabled').checked;
    const xgiMode = document.getElementById('xgiMode').value;
    const xgiStrength = parseFloat(document.getElementById('xgiStrength').value);
    
    if (xgiEnabled !== (currentConfig.xgi_integration?.enabled || false) ||
        xgiMode !== (currentConfig.xgi_integration?.multiplier_mode || 'direct') ||
        Math.abs(xgiStrength - (currentConfig.xgi_integration?.multiplier_strength || 1.0)) > 0.01) {
        changes.xgi_integration = {
            enabled: xgiEnabled,
            multiplier_mode: xgiMode,
            multiplier_strength: xgiStrength
        };
    }
    
    // Blender Display changes
    const gamesDisplayEnabled = document.getElementById('gamesDisplayEnabled').checked;
    const gamesSwitchover = parseInt(document.getElementById('baselineSwitchover').value);
    const transitionEnd = parseInt(document.getElementById('transitionEnd').value);
    const showHistorical = document.getElementById('showHistorical').checked;
    
    if (gamesDisplayEnabled !== true || // Always enabled for now
        gamesSwitchover !== (currentConfig.games_display?.baseline_switchover_gameweek || 10) ||
        transitionEnd !== (currentConfig.games_display?.transition_period_end || 15) ||
        showHistorical !== (currentConfig.games_display?.show_historical_data !== false)) {
        changes.games_display = {
            baseline_switchover_gameweek: gamesSwitchover,
            transition_period_end: transitionEnd,
            show_historical_data: showHistorical
        };
    }
    
    // Manual overrides - add to starter_prediction changes if any exist
    if (Object.keys(manualOverrides).length > 0) {
        if (!changes.starter_prediction) {
            changes.starter_prediction = {};
        }
        changes.starter_prediction.manual_overrides = manualOverrides;
    }
    
    // v2.0 Parameter Changes Detection
    const v2Enabled = document.getElementById('formula-v2')?.checked;
    if (v2Enabled) {
        const currentV2Config = currentConfig.formula_optimization_v2 || {};
        
        // Check EWMA Form parameters
        const ewmaAlpha = parseFloat(document.getElementById('ewma-alpha-slider')?.value || 0.87);
        if (Math.abs(ewmaAlpha - (currentV2Config.ewma_form?.alpha || 0.87)) > 0.01) {
            if (!changes.formula_optimization_v2) changes.formula_optimization_v2 = {};
            changes.formula_optimization_v2.ewma_form = { alpha: ewmaAlpha };
        }
        
        // Check Dynamic Blending parameters
        const adaptationGameweek = parseInt(document.getElementById('adaptation-gameweek')?.value || 15);
        if (adaptationGameweek !== (currentV2Config.dynamic_blending?.adaptation_gameweek || 15)) {
            if (!changes.formula_optimization_v2) changes.formula_optimization_v2 = {};
            if (!changes.formula_optimization_v2.dynamic_blending) changes.formula_optimization_v2.dynamic_blending = {};
            changes.formula_optimization_v2.dynamic_blending.adaptation_gameweek = adaptationGameweek;
        }
        
        // Check Normalized xGI parameters
        const xgiEnabled = document.getElementById('xgi-enabled')?.checked !== false;
        const xgiStrength = parseFloat(document.getElementById('xgi-normalization-strength')?.value || 1.0);
        const xgiDefenders = document.getElementById('xgi-defenders')?.checked;
        const xgiMidfielders = document.getElementById('xgi-midfielders')?.checked;
        const xgiForwards = document.getElementById('xgi-forwards')?.checked;
        
        const currentXgi = currentV2Config.normalized_xgi || {};
        if (xgiEnabled !== (currentXgi.enabled !== false) ||
            Math.abs(xgiStrength - (currentXgi.normalization_strength || 1.0)) > 0.01 ||
            xgiDefenders !== (currentXgi.position_adjustments?.defenders !== false) ||
            xgiMidfielders !== (currentXgi.position_adjustments?.midfielders !== false) ||
            xgiForwards !== (currentXgi.position_adjustments?.forwards !== false)) {
            if (!changes.formula_optimization_v2) changes.formula_optimization_v2 = {};
            changes.formula_optimization_v2.normalized_xgi = {
                enabled: xgiEnabled,
                normalization_strength: xgiStrength,
                position_adjustments: {
                    defenders: xgiDefenders,
                    midfielders: xgiMidfielders,
                    forwards: xgiForwards
                }
            };
        }
        
        // Check Multiplier Cap parameters
        const formCap = parseFloat(document.getElementById('form-cap-slider')?.value || 2.0);
        const fixtureCap = parseFloat(document.getElementById('fixture-cap-slider')?.value || 1.8);
        const xgiCap = parseFloat(document.getElementById('xgi-cap-slider')?.value || 2.5);
        const globalCap = parseFloat(document.getElementById('global-cap-slider')?.value || 3.0);
        
        const currentCaps = currentV2Config.multiplier_caps || {};
        if (Math.abs(formCap - (currentCaps.form || 2.0)) > 0.01 ||
            Math.abs(fixtureCap - (currentCaps.fixture || 1.8)) > 0.01 ||
            Math.abs(xgiCap - (currentCaps.xgi || 2.5)) > 0.01 ||
            Math.abs(globalCap - (currentCaps.global || 3.0)) > 0.01) {
            if (!changes.formula_optimization_v2) changes.formula_optimization_v2 = {};
            changes.formula_optimization_v2.multiplier_caps = {
                form: formCap,
                fixture: fixtureCap,
                xgi: xgiCap,
                global: globalCap
            };
        }
    }
    
    return changes;
}

// =================================================================
// PARAMETER CHANGE DETECTION
// =================================================================

function markParameterChanged() {
    console.log('🎯 Parameter changed - checking for updates...');
    
    // Build changes and update UI
    pendingChanges = buildParameterChanges();
    
    // Show pending indicator and enable Apply Changes button
    const hasPendingChanges = Object.keys(pendingChanges).length > 0;
    document.getElementById('pending-changes').style.display = hasPendingChanges ? 'block' : 'none';
    document.getElementById('apply-changes').disabled = !hasPendingChanges;
    
    console.log('📝 Parameter changes detected:', pendingChanges);
}

// =================================================================
// API COMMUNICATION
// =================================================================

async function applyChanges() {
    if (Object.keys(pendingChanges).length === 0) {
        showError('No changes to apply');
        return;
    }
    
    try {
        console.log('💾 Applying parameter changes...');
        showLoadingOverlay('Recalculating True Values for all 633 players...');
        
        const response = await fetch('/api/update-parameters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ...pendingChanges,
                gameweek: 1
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ Parameters updated! ${result.updated_players} players recalculated in ${result.calculation_time.toFixed(2)}s`);
            
            // Reload configuration and data
            await loadSystemConfig();
            await loadPlayersData();
            
            // Clear pending changes
            pendingChanges = {};
            document.getElementById('pending-changes').style.display = 'none';
            document.getElementById('apply-changes').disabled = true;
            
            // Update status
            updateStatus('Parameters updated successfully!', 'success');
            
        } else {
            throw new Error(result.error || 'Failed to update parameters');
        }
    } catch (error) {
        console.error('❌ Error applying changes:', error);
        showError('Failed to apply changes: ' + error.message);
    } finally {
        hideLoadingOverlay();
    }
}

async function resetToDefaults() {
    if (!confirm('Reset all parameters to default values? This will discard any pending changes.')) {
        return;
    }
    
    try {
        console.log('🔄 Resetting to default parameters...');
        
        // Load default configuration from server
        await loadSystemConfig();
        
        // Clear pending changes
        pendingChanges = {};
        document.getElementById('pending-changes').style.display = 'none';
        document.getElementById('apply-changes').disabled = true;
        
        updateStatus('Parameters reset to defaults', 'success');
    } catch (error) {
        console.error('❌ Error resetting parameters:', error);
        showError('Failed to reset parameters');
    }
}

// =================================================================
// TABLE CONTROLS
// =================================================================

function setupTableControls() {
    // Sorting
    document.querySelectorAll('[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const field = this.dataset.sort;
            handleSort(field);
        });
    });
    
    // Pagination
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            loadPlayersData();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = Math.ceil(totalFilteredCount / pageSize);
        if (currentPage < totalPages - 1) {
            currentPage++;
            loadPlayersData();
        }
    });
    
    document.getElementById('page-size-select').addEventListener('change', function() {
        pageSize = parseInt(this.value);
        currentPage = 0;
        loadPlayersData();
    });
    
    // Export
    document.getElementById('export-csv').addEventListener('click', exportToCSV);
}

function handleSort(field) {
    if (currentSort.field === field) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.direction = 'desc';
    }
    
    // Update sort indicators
    document.querySelectorAll('.sort-indicator').forEach(span => {
        span.textContent = '';
    });
    
    const indicator = document.querySelector(`[data-sort="${field}"] .sort-indicator`);
    indicator.textContent = currentSort.direction === 'asc' ? '▲' : '▼';
    
    // Reset to first page and reload data with new sort
    currentPage = 0;
    loadPlayersData();
}

function sortPlayersData() {
    playersData.sort((a, b) => {
        let aVal = a[currentSort.field];
        let bVal = b[currentSort.field];
        
        // Special handling for Games column - always treat as numeric
        if (currentSort.field === 'games_played_historical') {
            aVal = parseInt(aVal) || 0;
            bVal = parseInt(bVal) || 0;
        }
        // Handle different data types
        else if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        } else {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
        }
        
        if (currentSort.direction === 'asc') {
            return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        } else {
            return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        }
    });
}

// =================================================================
// FILTER CONTROLS
// =================================================================

function setupFilterControls() {
    // Position filters
    ['g', 'd', 'm', 'f'].forEach(pos => {
        document.getElementById(`pos-${pos}`).addEventListener('change', handleFilterChange);
    });
    
    // Price range
    document.getElementById('price-min').addEventListener('change', handleFilterChange);
    document.getElementById('price-max').addEventListener('change', handleFilterChange);
    
    // Team filter
    document.getElementById('team-select').addEventListener('change', handleFilterChange);
    
    // Search
    document.getElementById('player-search').addEventListener('input', 
        debounce(handleFilterChange, 500));
}

function handleFilterChange() {
    // Update current filters
    currentFilters.positions = [];
    ['g', 'd', 'm', 'f'].forEach(pos => {
        if (document.getElementById(`pos-${pos}`).checked) {
            currentFilters.positions.push(pos.toUpperCase());
        }
    });
    
    currentFilters.priceMin = parseFloat(document.getElementById('price-min').value) || 5.0;
    currentFilters.priceMax = parseFloat(document.getElementById('price-max').value) || 25.0;
    currentFilters.search = document.getElementById('player-search').value.trim();
    
    // Update team filter - handle multiple select dropdown
    const teamSelect = document.getElementById('team-select');
    currentFilters.teams = [];
    if (teamSelect) {
        Array.from(teamSelect.selectedOptions).forEach(option => {
            if (option.value) { // Skip empty "All Teams" option
                currentFilters.teams.push(option.value);
            }
        });
    }
    
    // Reset to first page
    currentPage = 0;
    
    // Reload data with new filters
    loadPlayersData();
}

// =================================================================
// UTILITY FUNCTIONS
// =================================================================

function showLoadingOverlay(message) {
    const overlay = document.getElementById('loading-overlay');
    const text = overlay.querySelector('p');
    text.textContent = message || 'Loading...';
    overlay.style.display = 'flex';
}

function hideLoadingOverlay() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function updateStatus(message, type = 'info') {
    const indicator = document.getElementById('status-indicator');
    indicator.textContent = message;
    indicator.className = `status-${type}`;
    
    // Auto-clear after 5 seconds
    setTimeout(() => {
        indicator.textContent = 'Ready';
        indicator.className = '';
    }, 5000);
}

function showError(message) {
    console.error('❌', message);
    updateStatus(message, 'error');
    alert('Error: ' + message);
}

function showSuccess(message) {
    console.log('✅', message);
    updateStatus(message, 'success');
    alert(message);
}

function showMessage(message, type = 'info') {
    console.log('ℹ️', message);
    updateStatus(message, type);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

// =================================================================
// FILE OPERATIONS
// =================================================================

function importLineups() {
    document.getElementById('csv-file-input').click();
}

function exportToCSV() {
    if (!playersData || playersData.length === 0) {
        showError('No data to export');
        return;
    }
    
    const headers = ['Name', 'Team', 'Position', 'Price', 'PPG', 'True Value', 'Form Multiplier', 'Fixture Multiplier', 'Starter Multiplier'];
    const csvContent = [
        headers.join(','),
        ...playersData.map(player => [
            `"${player.name || ''}"`,
            player.team || '',
            player.position || '',
            player.price || 0,
            player.ppg || 0,
            player.true_value || 0,
            player.form_multiplier || 1.0,
            player.fixture_multiplier || 1.0,
            player.starter_multiplier || 1.0
        ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fantrax_players_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    console.log('📊 Player data exported to CSV');
}

// =================================================================
// UNDERSTAT INTEGRATION FUNCTIONS
// =================================================================

async function syncUnderstatData() {
    const statusEl = document.getElementById('syncStatus');
    const statusV2El = document.getElementById('syncStatus-v2');
    
    // Update both status displays
    if (statusEl) {
        statusEl.textContent = 'Syncing...';
        statusEl.className = 'syncing';
    }
    if (statusV2El) {
        statusV2El.textContent = 'Syncing...';
        statusV2El.className = 'syncing';
    }
    
    try {
        const response = await fetch('/api/understat/sync', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            const successMessage = `✓ Synced ${data.successfully_matched} players (${data.match_rate.toFixed(1)}% match rate)`;
            
            if (statusEl) {
                statusEl.textContent = successMessage;
                statusEl.className = 'success';
            }
            if (statusV2El) {
                statusV2El.textContent = successMessage;
                statusV2El.className = 'success';
            }
            
            // If there are unmatched players, show option to review them
            if (data.unmatched_players > 0) {
                const reviewMessage = ` - ${data.unmatched_players} need review`;
                if (statusEl) statusEl.textContent += reviewMessage;
                if (statusV2El) statusV2El.textContent += reviewMessage;
                
                setTimeout(() => {
                    if (confirm(`${data.unmatched_players} Understat players couldn't be automatically matched. Would you like to review them manually?`)) {
                        // Route to import validation for manual matching
                        window.location.href = '/import-validation?source=understat';
                    }
                }, 1000);
            }
            
            loadUnderstatStats();
            loadPlayersData(); // Refresh table
        } else {
            const errorMessage = `✗ Sync failed: ${data.error}`;
            if (statusEl) {
                statusEl.textContent = errorMessage;
                statusEl.className = 'error';
            }
            if (statusV2El) {
                statusV2El.textContent = errorMessage;
                statusV2El.className = 'error';
            }
        }
    } catch (error) {
        const errorMessage = `✗ Error: ${error.message}`;
        if (statusEl) {
            statusEl.textContent = errorMessage;
            statusEl.className = 'error';
        }
        if (statusV2El) {
            statusV2El.textContent = errorMessage;
            statusV2El.className = 'error';
        }
    }
}

async function loadUnderstatStats() {
    try {
        const response = await fetch('/api/understat/stats');
        const data = await response.json();
        
        const statsEl = document.getElementById('xgiStats');
        const statsV2El = document.getElementById('xgiStats-v2');
        
        const statsHtml = `
            <strong>Coverage:</strong> ${data.stats.players_with_xgi}/${data.stats.total_players} players |
            <strong>Avg xGI90:</strong> ${(data.stats.avg_xgi90 || 0).toFixed(3)} |
            <strong>Last sync:</strong> ${data.config.last_sync ? new Date(data.config.last_sync * 1000).toLocaleDateString() : 'Never'}
        `;
        
        if (statsEl) statsEl.innerHTML = statsHtml;
        if (statsV2El) statsV2El.innerHTML = statsHtml;
    } catch (error) {
        console.error('Failed to load Understat stats:', error);
    }
}

// Initialize CSV file input handler
document.addEventListener('DOMContentLoaded', function() {
    const csvInput = document.getElementById('csv-file-input');
    console.log('🔧 CSV input element found:', csvInput);
    
    if (csvInput) {
        csvInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            console.log('📁 File change event triggered, file:', file);
            if (file) {
                console.log('📁 CSV file selected:', file.name);
            
            // Validate file type
            if (!file.name.toLowerCase().endsWith('.csv')) {
                showError('Please select a CSV file');
                return;
            }
            
            // Show upload progress
            const uploadMessage = `Uploading ${file.name}...`;
            showMessage(uploadMessage, 'info');
            
            // Create form data for upload
            const formData = new FormData();
            formData.append('lineups_csv', file);
            
            // Upload to backend API
            fetch('/api/import-lineups', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show detailed success message
                    const successMsg = `✅ CSV imported successfully!\n` +
                        `📊 Total players: ${data.total_players}\n` +
                        `✓ Matched: ${data.matched_players} (${data.match_rate.toFixed(1)}%)\n` +
                        `⚠ Needs review: ${data.unmatched_players || 0}`;
                    
                    showSuccess(successMsg);
                    
                    // Refresh the table to show updated multipliers
                    loadPlayersData();
                    
                    // Show additional details if available
                    if (data.confidence_breakdown) {
                        console.log('📈 Confidence breakdown:', data.confidence_breakdown);
                    }
                    
                    if (data.unmatched_players > 0) {
                        console.log('⚠ Some players need manual review. Check /import-validation for details.');
                        
                        // Store unmatched data in sessionStorage for validation page
                        const validationData = {
                            unmatched_count: data.unmatched_players,
                            total_players: data.total_players,
                            matched_players: data.matched_players,
                            unmatched_details: data.unmatched_details || [],
                            csv_format: data.csv_format,
                            timestamp: Date.now()
                        };
                        sessionStorage.setItem('pendingValidation', JSON.stringify(validationData));
                        
                        // Redirect to manual validation page after showing success message
                        setTimeout(() => {
                            window.location.href = '/import-validation';
                        }, 2000); // 2 second delay to let user read the success message
                    }
                } else {
                    showError(`Import failed: ${data.error || 'Unknown error'}`);
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                showError(`Upload failed: ${error.message}`);
            });
            }
        });
    } else {
        console.error('❌ CSV input element not found!');
    }
    
    // Load Understat stats on page load
    loadUnderstatStats();
});

// =================================================================
// THEME TOGGLE FUNCTIONS
// =================================================================

function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    // Load saved theme preference or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    // Set up click handler
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    });
}

function setTheme(theme) {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update button text and icon
    const themeToggle = document.getElementById('theme-toggle');
    if (theme === 'dark') {
        themeToggle.textContent = '☀️ Light Mode';
    } else {
        themeToggle.textContent = '🌙 Dark Mode';
    }
    
    // Save preference
    localStorage.setItem('theme', theme);
    
    console.log(`🎨 Theme switched to: ${theme}`);
}

// =================================================================
// PROFESSIONAL TOOLTIP SYSTEM - SPRINT 3
// =================================================================

// Initialize tooltips after DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupTooltips();
});

function setupTooltips() {
    // Initialize tooltips for all info icons
    document.querySelectorAll('.info-icon').forEach(icon => {
        icon.addEventListener('mouseenter', showTooltip);
        icon.addEventListener('mouseleave', hideTooltip);
        
        // Mobile touch support
        icon.addEventListener('touchstart', handleTooltipTouch);
        icon.addEventListener('touchend', handleTooltipTouchEnd);
    });
    
    // Hide tooltip when scrolling or clicking elsewhere
    document.addEventListener('scroll', hideTooltip);
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.info-icon')) {
            hideTooltip();
        }
    });
}

function showTooltip(e) {
    const column = e.target.dataset.column;
    const info = columnInfo[column];
    
    if (!info) {
        console.warn('No tooltip info found for column:', column);
        return;
    }
    
    // Remove any existing tooltips
    hideTooltip();
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.id = 'active-tooltip';
    
    // Build tooltip content
    let html = `<div class="tooltip-title">${info.title}</div>`;
    html += `<div class="tooltip-description">${info.description}</div>`;
    
    // Add formula if available
    if (info.formula) {
        html += `<div class="tooltip-formula">Formula: ${info.formula}</div>`;
    }
    
    // Add interpretation section
    if (info.interpretation) {
        html += '<div class="tooltip-interpretation">';
        if (typeof info.interpretation === 'string') {
            html += `<div>${info.interpretation}</div>`;
        } else {
            for (const [key, value] of Object.entries(info.interpretation)) {
                html += `<div class="tooltip-interpretation-item">${value}</div>`;
            }
        }
        html += '</div>';
    }
    
    // Add values section (for starter_multiplier)
    if (info.values) {
        html += '<div class="tooltip-interpretation">';
        for (const [key, value] of Object.entries(info.values)) {
            html += `<div class="tooltip-interpretation-item">${value}</div>`;
        }
        html += '</div>';
    }
    
    // Add usage notes
    if (info.usage) {
        html += `<div class="tooltip-usage">${info.usage}</div>`;
    }
    
    // Add additional info
    if (info.note) {
        html += `<div class="tooltip-note">Note: ${info.note}</div>`;
    }
    
    if (info.calculation) {
        html += `<div class="tooltip-note">Calculation: ${info.calculation}</div>`;
    }
    
    if (info.input) {
        html += `<div class="tooltip-note">Input: ${info.input}</div>`;
    }
    
    // Add source attribution
    if (info.source) {
        html += `<div class="tooltip-source">Source: ${info.source}</div>`;
    }
    
    tooltip.innerHTML = html;
    document.body.appendChild(tooltip);
    
    // Position tooltip
    positionTooltip(tooltip, e.target);
}

function positionTooltip(tooltip, targetElement) {
    const rect = targetElement.getBoundingClientRect();
    
    // Don't show tooltip if element isn't visible or positioned
    if (rect.width === 0 || rect.height === 0) {
        tooltip.remove();
        return;
    }
    
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Default position: below the icon, centered
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.bottom + 8;
    
    // Adjust horizontal position if tooltip would go off screen
    if (left < 10) {
        left = 10;
    } else if (left + tooltipRect.width > viewportWidth - 10) {
        left = viewportWidth - tooltipRect.width - 10;
    }
    
    // Adjust vertical position if tooltip would go off screen
    if (top + tooltipRect.height > viewportHeight - 10) {
        // Position above the icon instead
        top = rect.top - tooltipRect.height - 8;
        
        // Update arrow position for top placement
        tooltip.style.setProperty('--arrow-position', 'bottom');
        const arrow = tooltip.querySelector('::after');
        if (arrow) {
            tooltip.classList.add('tooltip-top');
        }
    }
    
    // Apply position
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
}

function hideTooltip() {
    // Remove all existing tooltips (both regular and v2)
    const existingTooltips = document.querySelectorAll('.tooltip, #active-tooltip');
    existingTooltips.forEach(tooltip => tooltip.remove());
}

// Mobile touch support
let touchTimeout;

function handleTooltipTouch(e) {
    e.preventDefault(); // Prevent default touch behavior
    
    // Clear any existing touch timeout
    if (touchTimeout) {
        clearTimeout(touchTimeout);
    }
    
    // Show tooltip immediately
    showTooltip(e);
    
    // Set timeout to hide tooltip after 3 seconds
    touchTimeout = setTimeout(() => {
        hideTooltip();
    }, 3000);
}

function handleTooltipTouchEnd(e) {
    // Don't hide immediately on touch end - let timeout handle it
    // This allows users to read the tooltip
}

// Update tooltip positioning on window resize
window.addEventListener('resize', function() {
    const activeTooltip = document.getElementById('active-tooltip');
    if (activeTooltip) {
        hideTooltip();
    }
});

// Enhanced setup function to be called when new content is loaded
function refreshTooltips() {
    // Remove old event listeners and add new ones
    // This is useful when table content is dynamically updated
    document.querySelectorAll('.info-icon').forEach(icon => {
        // Remove existing listeners (if any)
        icon.removeEventListener('mouseenter', showTooltip);
        icon.removeEventListener('mouseleave', hideTooltip);
        icon.removeEventListener('touchstart', handleTooltipTouch);
        icon.removeEventListener('touchend', handleTooltipTouchEnd);
        
        // Add fresh listeners
        icon.addEventListener('mouseenter', showTooltip);
        icon.addEventListener('mouseleave', hideTooltip);
        icon.addEventListener('touchstart', handleTooltipTouch);
        icon.addEventListener('touchend', handleTooltipTouchEnd);
    });
}

// =================================================================
// SPRINT 4: FORMULA VERSION TOGGLE (v2.0 UI INTEGRATION)
// =================================================================

// Global variable to track current formula version
let currentFormulaVersion = 'v2.0'; // Default to v2.0

function setupFormulaVersionToggle() {
    console.log('🔧 Setting up formula version toggle...');
    
    // Load current formula version from server
    loadCurrentFormulaVersion();
    
    // Set up radio button event listeners
    const formulaRadios = document.querySelectorAll('input[name="formula-version"]');
    formulaRadios.forEach(radio => {
        radio.addEventListener('change', handleFormulaVersionChange);
    });
    
    console.log('✅ Formula version toggle setup complete');
}

async function loadCurrentFormulaVersion() {
    try {
        const response = await fetch('/api/get-formula-version');
        const result = await response.json();
        
        if (result.current_version) {
            currentFormulaVersion = result.current_version;
            
            // Update UI to reflect current version
            const versionRadio = document.getElementById(`formula-${result.current_version}`);
            if (versionRadio) {
                versionRadio.checked = true;
                updateFormulaInfoDisplay(result.current_version);
            }
            
            // Update v2.0 column visibility
            updateV2ColumnVisibility(result.current_version === 'v2.0');
            
            console.log('✅ Formula version loaded:', result.current_version);
        }
    } catch (error) {
        console.error('❌ Error loading formula version:', error);
        // Default to v2.0 on error
        currentFormulaVersion = 'v2.0';
    }
}

function getFormulaVersion() {
    return currentFormulaVersion;
}

async function handleFormulaVersionChange(event) {
    const newVersion = event.target.value;
    console.log('🔄 Formula version change requested:', newVersion);
    
    if (newVersion === currentFormulaVersion) {
        console.log('⏭️ No change needed - already using', newVersion);
        return;
    }
    
    try {
        showLoadingOverlay(`Switching to Formula ${newVersion}...`);
        
        // Call API to switch formula version
        const response = await fetch('/api/toggle-formula-version', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                version: newVersion
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ Formula switched to ${result.new_version}`);
            currentFormulaVersion = result.new_version;
            
            // Update UI elements
            updateFormulaInfoDisplay(result.new_version);
            updateV2ColumnVisibility(result.new_version === 'v2.0');
            
            // Show success feedback
            showBriefSuccess(`Formula switched to ${result.new_version}`);
            
            // Reload player data to get updated calculations
            await loadPlayersData();
            
        } else {
            throw new Error(result.error || 'Failed to switch formula version');
        }
    } catch (error) {
        console.error('❌ Error switching formula version:', error);
        showError('Failed to switch formula: ' + error.message);
        
        // Revert radio button selection
        const currentRadio = document.getElementById(`formula-${currentFormulaVersion}`);
        if (currentRadio) {
            currentRadio.checked = true;
        }
    } finally {
        hideLoadingOverlay();
    }
}

function updateFormulaInfoDisplay(version) {
    const v1Info = document.getElementById('formula-v1-info');
    const v2Info = document.getElementById('formula-v2-info');
    
    if (version === 'v2.0') {
        v2Info.style.display = 'block';
        v1Info.style.display = 'none';
    } else {
        v1Info.style.display = 'block';
        v2Info.style.display = 'none';
    }
    
    // Update version badge
    const versionBadge = document.querySelector('.version-badge');
    if (versionBadge) {
        versionBadge.textContent = version;
    }
}

function updateV2ColumnVisibility(showV2Columns) {
    console.log('🎯 Updating v2.0 column visibility:', showV2Columns);
    
    const roiColumn = document.querySelector('th[data-sort="roi"]');
    
    if (roiColumn) {
        roiColumn.style.display = showV2Columns ? '' : 'none';
        console.log('📊 ROI column visibility:', showV2Columns ? 'shown' : 'hidden');
    }
    
    // Update ROI cells in table rows
    const roiCells = document.querySelectorAll('td:nth-child(9)'); // ROI is 9th column
    roiCells.forEach(cell => {
        if (cell.classList.contains('roi-value')) {
            cell.style.display = showV2Columns ? '' : 'none';
        }
    });
    
    // Update colspan for loading/empty rows
    const loadingRows = document.querySelectorAll('.loading-row td');
    loadingRows.forEach(cell => {
        cell.setAttribute('colspan', showV2Columns ? '18' : '17');
    });
    
    // Update v2.0 visual indicators
    const body = document.body;
    if (showV2Columns) {
        body.classList.add('v2-enabled');
        body.classList.remove('v1-enabled');
    } else {
        body.classList.add('v1-enabled');
        body.classList.remove('v2-enabled');
    }
}

// Add ROI column info to the tooltip system
columnInfo['roi'] = {
    title: 'Return on Investment',
    description: 'v2.0 value efficiency metric - True Value divided by Player Price',
    interpretation: {
        'excellent': '🟢 ≥1.2 - Elite ROI',
        'good': '🔵 1.0-1.2 - Good ROI',
        'average': '🟡 0.8-1.0 - Fair ROI',
        'poor': '🔴 <0.8 - Poor ROI'
    },
    formula: 'True Value ÷ Price',
    usage: '⭐ v2.0 Primary value metric - considers all multipliers relative to cost',
    note: 'Only available with Formula v2.0 - provides cleaner separation of prediction vs value'
};

// Add v2.0 Parameter Control tooltips
const v2ParameterInfo = {
    'ewma-alpha': {
        title: 'EWMA Alpha (α)',
        description: 'Controls exponential decay rate for form calculation weights',
        interpretation: {
            'high': '🔥 α > 0.8 - Heavy recent game weighting',
            'balanced': '⚖️ α = 0.6-0.8 - Balanced recent/historical',
            'conservative': '🐌 α < 0.6 - More historical emphasis'
        },
        formula: 'Weight_i = α × (1-α)^i where i is games back',
        note: 'v2.0 Enhancement: Exponential weights replace fixed lookback periods'
    },
    'adaptation-gameweek': {
        title: 'Dynamic Blending Adaptation Point',
        description: 'Gameweek when current season data reaches 100% weight',
        interpretation: 'Smooth transition from historical (100%) to current season (100%) data',
        formula: 'w_current = min(1, (N-1)/(K-1)) where N=gameweek, K=adaptation',
        note: 'v2.0 Enhancement: Replaces hard baseline switchover with gradual transition'
    },
    'xgi-normalization': {
        title: 'xGI Normalization Strength',
        description: 'Controls how strongly position-specific xGI adjustments are applied',
        interpretation: {
            'strong': '💪 > 1.5x - Maximum position differentiation',
            'balanced': '⚖️ 1.0x - Standard normalization',
            'light': '🪶 < 1.0x - Minimal position adjustment'
        },
        note: 'v2.0 Enhancement: Ratio-based xGI calculation normalized around 1.0'
    },
    'multiplier-caps': {
        title: 'Multiplier Cap System',
        description: 'Prevents extreme outlier values that could skew predictions',
        interpretation: 'Applied individually to each multiplier, then globally to final result',
        formula: 'min(calculated_multiplier, cap_value)',
        note: 'v2.0 Enhancement: Maintains balanced predictions while allowing variance'
    }
};

// Flag to prevent tooltips during initialization
let tooltipsReady = false;

// Initialize v2.0 parameter tooltips
function initializeV2Tooltips() {
    // Add hover handlers for v2.0 parameter labels and controls
    Object.keys(v2ParameterInfo).forEach(paramKey => {
        const elements = document.querySelectorAll(`[data-v2-param="${paramKey}"], #${paramKey}, label[for*="${paramKey}"]`);
        elements.forEach(element => {
            if (element && !element.hasAttribute('data-tooltip-initialized')) {
                element.setAttribute('data-tooltip-initialized', 'true');
                element.addEventListener('mouseenter', function(e) {
                    if (tooltipsReady) {
                        showV2ParameterTooltip(e, paramKey);
                    }
                });
                element.addEventListener('mouseleave', function() {
                    hideTooltip();
                });
            }
        });
    });
    
    // Enable tooltips after a short delay
    setTimeout(() => {
        tooltipsReady = true;
    }, 500);
}

function showV2ParameterTooltip(event, paramKey) {
    const info = v2ParameterInfo[paramKey];
    if (!info) return;
    
    // Remove any existing tooltips first
    hideTooltip();
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip v2-tooltip';
    tooltip.id = 'active-tooltip';
    tooltip.innerHTML = `
        <div class="tooltip-title">${info.title}</div>
        <div class="tooltip-description">${info.description}</div>
        ${info.formula ? `<div class="tooltip-formula">${info.formula}</div>` : ''}
        ${info.interpretation ? `
            <div class="tooltip-interpretation">
                ${typeof info.interpretation === 'string' ? 
                    `<div class="tooltip-interpretation-item">${info.interpretation}</div>` :
                    Object.entries(info.interpretation).map(([key, value]) => 
                        `<div class="tooltip-interpretation-item">${value}</div>`
                    ).join('')
                }
            </div>
        ` : ''}
        ${info.note ? `<div class="tooltip-note">${info.note}</div>` : ''}
        <div class="tooltip-source">v2.0 Enhanced Controls</div>
    `;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = event.target.getBoundingClientRect();
    
    // Don't show tooltip if element isn't visible or positioned
    if (rect.width === 0 || rect.height === 0) {
        tooltip.remove();
        return;
    }
    
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top - tooltipRect.height - 8;
    
    // Adjust if tooltip goes off screen
    if (left < 8) left = 8;
    if (left + tooltipRect.width > window.innerWidth - 8) {
        left = window.innerWidth - tooltipRect.width - 8;
    }
    if (top < 8) {
        top = rect.bottom + 8;
        tooltip.classList.add('tooltip-top');
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
}

// =================================================================
// SPRINT 4: VALIDATION STATUS INDICATORS (v2.0 UI INTEGRATION)
// =================================================================

// Global validation status
let validationStatus = {
    loaded: false,
    lastValidation: null,
    metrics: {
        rmse: null,
        correlation: null,
        precision: null
    }
};

function setupValidationStatusIndicators() {
    console.log('🔧 Setting up validation status indicators...');
    
    // Load current validation status from server
    loadValidationStatus();
    
    console.log('✅ Validation status indicators setup complete');
}

async function loadValidationStatus() {
    try {
        // Check if there's a recent validation history
        const response = await fetch('/api/validation-history');
        const validationHistory = await response.json();
        
        if (validationHistory && validationHistory.length > 0) {
            // Get the most recent validation
            const latestValidation = validationHistory[0];
            updateValidationDisplay(latestValidation);
        } else {
            // No validation history found
            updateValidationDisplay(null);
        }
    } catch (error) {
        console.warn('⚠️ Could not load validation status:', error);
        updateValidationDisplay(null);
    }
}

function updateValidationDisplay(validationData) {
    const badge = document.getElementById('validation-badge');
    const rmseValue = document.getElementById('rmse-value');
    const rmseStatus = document.getElementById('rmse-status');
    const correlationValue = document.getElementById('correlation-value');
    const correlationStatus = document.getElementById('correlation-status');
    const precisionValue = document.getElementById('precision-value');
    const precisionStatus = document.getElementById('precision-status');
    const lastValidation = document.getElementById('last-validation');
    const qualitySummary = document.getElementById('quality-summary');
    
    if (validationData && validationData.metrics) {
        // Update validation badge status
        const overallQuality = assessOverallQuality(validationData.metrics);
        badge.textContent = overallQuality.label;
        badge.className = 'status-badge ' + overallQuality.class;
        
        // Update RMSE
        rmseValue.textContent = validationData.metrics.rmse ? validationData.metrics.rmse.toFixed(2) : '--';
        const rmseQuality = assessRMSE(validationData.metrics.rmse);
        rmseStatus.textContent = rmseQuality.label;
        rmseStatus.className = 'metric-status ' + rmseQuality.class;
        
        // Update Correlation
        correlationValue.textContent = validationData.metrics.spearman_correlation ? 
            validationData.metrics.spearman_correlation.toFixed(3) : '--';
        const corrQuality = assessCorrelation(validationData.metrics.spearman_correlation);
        correlationStatus.textContent = corrQuality.label;
        correlationStatus.className = 'metric-status ' + corrQuality.class;
        
        // Update Precision@20
        precisionValue.textContent = validationData.metrics.precision_at_20 ? 
            validationData.metrics.precision_at_20.toFixed(3) : '--';
        const precQuality = assessPrecision(validationData.metrics.precision_at_20);
        precisionStatus.textContent = precQuality.label;
        precisionStatus.className = 'metric-status ' + precQuality.class;
        
        // Update last validation time
        if (validationData.timestamp) {
            const date = new Date(validationData.timestamp);
            lastValidation.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        }
        
        // Update quality summary
        qualitySummary.textContent = generateQualitySummary(validationData.metrics);
        
        validationStatus.loaded = true;
        validationStatus.lastValidation = validationData.timestamp;
        validationStatus.metrics = validationData.metrics;
        
    } else {
        // No validation data available
        badge.textContent = 'Not Available';
        badge.className = 'status-badge warning';
        
        rmseValue.textContent = '--';
        rmseStatus.textContent = '--';
        rmseStatus.className = 'metric-status';
        
        correlationValue.textContent = '--';
        correlationStatus.textContent = '--';
        correlationStatus.className = 'metric-status';
        
        precisionValue.textContent = '--';
        precisionStatus.textContent = '--';
        precisionStatus.className = 'metric-status';
        
        lastValidation.textContent = 'Not run';
        qualitySummary.textContent = 'Run validation to assess model quality and performance metrics.';
    }
}

function assessOverallQuality(metrics) {
    const rmseQuality = assessRMSE(metrics.rmse);
    const corrQuality = assessCorrelation(metrics.spearman_correlation);
    const precQuality = assessPrecision(metrics.precision_at_20);
    
    // Calculate overall score (0-3, where 3 is best)
    const scores = [rmseQuality, corrQuality, precQuality].map(q => {
        if (q.class === 'excellent') return 3;
        if (q.class === 'good') return 2;
        if (q.class === 'needs-work') return 1;
        return 0;
    });
    
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    
    if (avgScore >= 2.5) return { label: 'Excellent', class: 'good' };
    if (avgScore >= 2.0) return { label: 'Good', class: 'good' };
    if (avgScore >= 1.5) return { label: 'Fair', class: 'warning' };
    return { label: 'Needs Work', class: 'error' };
}

function assessRMSE(rmse) {
    if (!rmse) return { label: 'Unknown', class: '' };
    
    if (rmse < 2.8) return { label: 'Excellent', class: 'excellent' };
    if (rmse < 3.0) return { label: 'Good', class: 'good' };
    if (rmse < 3.5) return { label: 'Fair', class: 'needs-work' };
    return { label: 'Poor', class: 'poor' };
}

function assessCorrelation(correlation) {
    if (!correlation) return { label: 'Unknown', class: '' };
    
    if (correlation > 0.35) return { label: 'Excellent', class: 'excellent' };
    if (correlation > 0.25) return { label: 'Good', class: 'good' };
    if (correlation > 0.15) return { label: 'Fair', class: 'needs-work' };
    return { label: 'Poor', class: 'poor' };
}

function assessPrecision(precision) {
    if (!precision) return { label: 'Unknown', class: '' };
    
    if (precision > 0.40) return { label: 'Excellent', class: 'excellent' };
    if (precision > 0.30) return { label: 'Good', class: 'good' };
    if (precision > 0.20) return { label: 'Fair', class: 'needs-work' };
    return { label: 'Poor', class: 'poor' };
}

function generateQualitySummary(metrics) {
    const rmseQuality = assessRMSE(metrics.rmse);
    const corrQuality = assessCorrelation(metrics.spearman_correlation);
    const precQuality = assessPrecision(metrics.precision_at_20);
    
    const strengths = [];
    const concerns = [];
    
    if (rmseQuality.class === 'excellent' || rmseQuality.class === 'good') {
        strengths.push('prediction accuracy');
    } else {
        concerns.push('prediction accuracy');
    }
    
    if (corrQuality.class === 'excellent' || corrQuality.class === 'good') {
        strengths.push('player ranking');
    } else {
        concerns.push('player ranking');
    }
    
    if (precQuality.class === 'excellent' || precQuality.class === 'good') {
        strengths.push('top player identification');
    } else {
        concerns.push('top player identification');
    }
    
    if (strengths.length >= 2) {
        return `Model performing well in ${strengths.join(' and ')}.${concerns.length > 0 ? ` Opportunity to improve ${concerns[0]}.` : ''}`;
    } else if (concerns.length >= 2) {
        return `Model needs improvement in ${concerns.join(' and ')}.${strengths.length > 0 ? ` Strong ${strengths[0]} performance.` : ''}`;
    } else {
        return 'Mixed model performance - some metrics strong, others need attention.';
    }
}

async function runValidation() {
    const runButton = document.getElementById('run-validation');
    const badge = document.getElementById('validation-badge');
    
    // Disable button and show loading state
    runButton.disabled = true;
    runButton.innerHTML = '⏳ Running...';
    badge.textContent = 'Running...';
    badge.className = 'status-badge warning';
    
    try {
        const response = await fetch('/api/run-validation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                validation_type: 'temporal'
            })
        });
        
        const result = await response.json();
        
        if (result.validation_id) {
            showBriefSuccess('Validation completed successfully!');
            
            // Wait a moment then reload validation status
            setTimeout(() => {
                loadValidationStatus();
            }, 1000);
            
        } else {
            throw new Error(result.error || 'Validation failed');
        }
        
    } catch (error) {
        console.error('❌ Error running validation:', error);
        showError('Failed to run validation: ' + error.message);
        
        // Reset to previous state
        badge.textContent = 'Error';
        badge.className = 'status-badge error';
        
    } finally {
        runButton.disabled = false;
        runButton.innerHTML = '🔍 Run Validation';
    }
}

function viewValidationResults() {
    // Open validation dashboard in new window
    window.open('/api/validation-dashboard', '_blank');
}

// =================================================================
// v2.0 Enhanced Parameter Controls JavaScript
// =================================================================

// Initialize v2.0 controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeV2Controls();
    setupFormulaVersionToggle();
    updateV2ControlsVisibility();
    initializeV2Tooltips();
});

function initializeV2Controls() {
    console.log('🔬 Initializing v2.0 parameter controls...');
    
    // EWMA Form Controls
    setupEWMAControls();
    
    // Dynamic Blending Controls  
    setupBlendingControls();
    
    // Normalized xGI Controls
    setupXGIControls();
    
    // Multiplier Cap Controls
    setupCapControls();
    
    console.log('✅ v2.0 controls initialized');
}

function setupEWMAControls() {
    const alphaSlider = document.getElementById('ewma-alpha-slider');
    const alphaDisplay = document.getElementById('ewma-alpha-display');
    const halfLifeDisplay = document.getElementById('ewma-half-life');
    const recentWeightDisplay = document.getElementById('ewma-recent-weight');
    
    if (alphaSlider) {
        alphaSlider.addEventListener('input', function() {
            const alpha = parseFloat(this.value);
            alphaDisplay.textContent = alpha.toFixed(2);
            
            // Calculate half-life: ln(0.5) / ln(1 - alpha)
            const halfLife = Math.log(0.5) / Math.log(1 - alpha);
            halfLifeDisplay.textContent = `~${halfLife.toFixed(1)} games`;
            
            // Recent game weight is just alpha * 100
            recentWeightDisplay.textContent = `${Math.round(alpha * 100)}%`;
            
            // Mark as pending change
            markParameterChanged();
        });
        
        // Initialize displays
        alphaSlider.dispatchEvent(new Event('input'));
    }
}

function setupBlendingControls() {
    const adaptationInput = document.getElementById('adaptation-gameweek');
    const historicalBar = document.getElementById('historical-weight-bar');
    const currentBar = document.getElementById('current-weight-bar');
    
    if (adaptationInput) {
        adaptationInput.addEventListener('input', function() {
            updateBlendingVisualization();
            markParameterChanged();
        });
        
        // Initialize visualization
        updateBlendingVisualization();
    }
}

function updateBlendingVisualization() {
    const adaptationGameweek = parseInt(document.getElementById('adaptation-gameweek').value);
    const currentGameweek = 2; // TODO: Get from API or config
    
    // Calculate current weight: min(1, (N-1)/(K-1))
    const currentWeight = Math.min(1, Math.max(0, (currentGameweek - 1) / (adaptationGameweek - 1)));
    const historicalWeight = 1 - currentWeight;
    
    // Update visualization bars
    const historicalBar = document.getElementById('historical-weight-bar');
    const currentBar = document.getElementById('current-weight-bar');
    
    if (historicalBar && currentBar) {
        const historicalPercent = Math.round(historicalWeight * 100);
        const currentPercent = Math.round(currentWeight * 100);
        
        historicalBar.style.width = `${historicalPercent}%`;
        historicalBar.querySelector('span').textContent = `Historical: ${historicalPercent}%`;
        
        currentBar.style.width = `${currentPercent}%`;
        currentBar.querySelector('span').textContent = `${currentPercent}%`;
    }
}

function setupXGIControls() {
    const normalizationSlider = document.getElementById('xgi-normalization-strength');
    const normalizationDisplay = document.getElementById('xgi-normalization-display');
    
    // Position toggles
    const defenderToggle = document.getElementById('xgi-defenders');
    const midfielderToggle = document.getElementById('xgi-midfielders');
    const forwardToggle = document.getElementById('xgi-forwards');
    
    // xGI enabled toggle
    const xgiEnabledToggle = document.getElementById('xgi-enabled');
    
    if (normalizationSlider) {
        normalizationSlider.addEventListener('input', function() {
            normalizationDisplay.textContent = `${parseFloat(this.value).toFixed(1)}x`;
            markParameterChanged();
        });
    }
    
    // Position toggle handlers
    [defenderToggle, midfielderToggle, forwardToggle].forEach(toggle => {
        if (toggle) {
            toggle.addEventListener('change', function() {
                markParameterChanged();
            });
        }
    });
    
    // xGI enabled toggle handler
    if (xgiEnabledToggle) {
        xgiEnabledToggle.addEventListener('change', function() {
            markParameterChanged();
        });
    }
}

function setupCapControls() {
    const capSliders = [
        { id: 'form-cap-slider', display: 'form-cap-display' },
        { id: 'fixture-cap-slider', display: 'fixture-cap-display' },
        { id: 'xgi-cap-slider', display: 'xgi-cap-display' },
        { id: 'global-cap-slider', display: 'global-cap-display' }
    ];
    
    capSliders.forEach(({ id, display }) => {
        const slider = document.getElementById(id);
        const displayElement = document.getElementById(display);
        
        if (slider && displayElement) {
            slider.addEventListener('input', function() {
                displayElement.textContent = `${parseFloat(this.value).toFixed(1)}x`;
                markParameterChanged();
                updateCapsAppliedIndicator();
            });
        }
    });
}

function updateCapsAppliedIndicator() {
    // This would typically show how many players are affected by caps
    // For now, we'll show a placeholder
    const indicator = document.getElementById('caps-applied-indicator');
    const countElement = document.getElementById('caps-applied-count');
    
    if (indicator && countElement) {
        // TODO: Get actual count from API
        countElement.textContent = '12'; // Placeholder
        indicator.style.display = 'block';
    }
}

function setupFormulaVersionToggle() {
    const v1Radio = document.getElementById('formula-v1');
    const v2Radio = document.getElementById('formula-v2');
    
    if (v1Radio && v2Radio) {
        v1Radio.addEventListener('change', function() {
            if (this.checked) {
                updateV2ColumnVisibility(false);
                updateV2ControlsVisibility();
                console.log('🔄 Switched to v1.0 formula');
            }
        });
        
        v2Radio.addEventListener('change', function() {
            if (this.checked) {
                updateV2ColumnVisibility(true);
                updateV2ControlsVisibility();
                console.log('🎯 Switched to v2.0 formula');
            }
        });
    }
}

function updateV2ControlsVisibility() {
    const v2Enabled = document.getElementById('formula-v2').checked;
    const v2Sections = document.querySelectorAll('.v2-enhanced-section');
    
    console.log('🎯 Updating v2.0 controls visibility:', v2Enabled);
    
    // Update body classes for CSS rules
    document.body.classList.toggle('v2-enabled', v2Enabled);
    document.body.classList.toggle('v1-enabled', !v2Enabled);
    
    // Show/hide v2.0 sections
    v2Sections.forEach(section => {
        section.style.display = v2Enabled ? 'block' : 'none';
    });
}

// Collect v2.0 parameters for API submission
function collectV2Parameters() {
    const v2Params = {
        ewma_form: {
            alpha: parseFloat(document.getElementById('ewma-alpha-slider').value)
        },
        dynamic_blending: {
            adaptation_gameweek: parseInt(document.getElementById('adaptation-gameweek').value)
        },
        normalized_xgi: {
            normalization_strength: parseFloat(document.getElementById('xgi-normalization-strength').value),
            position_adjustments: {
                defenders: document.getElementById('xgi-defenders').checked,
                midfielders: document.getElementById('xgi-midfielders').checked,
                forwards: document.getElementById('xgi-forwards').checked
            }
        },
        multiplier_caps: {
            form: parseFloat(document.getElementById('form-cap-slider').value),
            fixture: parseFloat(document.getElementById('fixture-cap-slider').value),
            xgi: parseFloat(document.getElementById('xgi-cap-slider').value),
            global: parseFloat(document.getElementById('global-cap-slider').value)
        }
    };
    
    console.log('📊 Collected v2.0 parameters:', v2Params);
    return v2Params;
}

// Wire v2.0 parameters to API update
function updateV2ParametersAPI() {
    const v2Enabled = document.getElementById('formula-v2').checked;
    
    if (!v2Enabled) {
        console.log('⚠️ Skipping v2.0 parameter update - v1.0 mode active');
        return;
    }
    
    const v2Params = collectV2Parameters();
    
    // Add to pending changes
    pendingChanges.formula_optimization_v2 = v2Params;
    
    console.log('✅ v2.0 parameters added to pending changes');
}

// Override the existing applyChanges function to include v2.0 params
const originalApplyChanges = window.applyChanges;
window.applyChanges = async function() {
    const v2Enabled = document.getElementById('formula-v2').checked;
    
    if (v2Enabled) {
        updateV2ParametersAPI();
    }
    
    // Call original function
    if (originalApplyChanges) {
        return await originalApplyChanges();
    }
}