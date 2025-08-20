// Fantrax Value Hunter Dashboard JavaScript
// Handles parameter controls, player table, and API communication

// Global state
let currentConfig = {};
let pendingChanges = {};
let playersData = [];
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
    
    // Games Display controls
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
    
    // Games Display controls (always enabled for now)
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
        tbody.innerHTML = '<tr class="loading-row"><td colspan="17">No players found</td></tr>';
        return;
    }
    
    const rows = playersData.map(player => {
        const trueValue = parseFloat(player.true_value || 0);
        const valueClass = trueValue > 1.0 ? 'value-high' : trueValue > 0.5 ? 'value-medium' : 'value-low';
        const playerId = player.id;
        
        const ppValue = parseFloat(player.value_score || 0);
        const ppClass = ppValue >= 0.7 ? 'pp-excellent' : ppValue >= 0.5 ? 'pp-good' : ppValue >= 0.3 ? 'pp-average' : 'pp-poor';
        
        return `
            <tr>
                <td><strong>${escapeHtml(player.name || 'Unknown')}</strong></td>
                <td>${escapeHtml(player.team || 'N/A')}</td>
                <td>${escapeHtml(player.position || 'N/A')}</td>
                <td>$${parseFloat(player.price || 0).toFixed(1)}</td>
                <td>${parseFloat(player.ppg || 0).toFixed(1)}</td>
                <td class="${ppClass}">${ppValue.toFixed(3)}</td>
                <td class="${getGamesClass(player)}">${player.games_display || '0'}</td>
                <td class="${valueClass}">${trueValue.toFixed(3)}</td>
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
    
    // Games Display controls
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
    
    // Form calculation changes
    const formEnabled = document.getElementById('form-enabled').checked;
    const lookbackPeriod = parseInt(document.getElementById('lookback-period').value);
    const minGames = parseInt(document.getElementById('min-games').value);
    const baselineSwitchover = parseInt(document.getElementById('baseline-switchover').value);
    const formStrength = parseFloat(document.getElementById('form-strength-slider').value);
    
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
    
    // Games Display changes
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
    
    return changes;
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
        currentPage++;
        loadPlayersData();
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
    statusEl.textContent = 'Syncing...';
    statusEl.className = 'syncing';
    
    try {
        const response = await fetch('/api/understat/sync', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            statusEl.textContent = `✓ Synced ${data.successfully_matched} players (${data.match_rate.toFixed(1)}% match rate)`;
            statusEl.className = 'success';
            
            // If there are unmatched players, show option to review them
            if (data.unmatched_players > 0) {
                statusEl.textContent += ` - ${data.unmatched_players} need review`;
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
            statusEl.textContent = `✗ Sync failed: ${data.error}`;
            statusEl.className = 'error';
        }
    } catch (error) {
        statusEl.textContent = `✗ Error: ${error.message}`;
        statusEl.className = 'error';
    }
}

async function loadUnderstatStats() {
    try {
        const response = await fetch('/api/understat/stats');
        const data = await response.json();
        
        const statsEl = document.getElementById('xgiStats');
        statsEl.innerHTML = `
            <strong>Coverage:</strong> ${data.stats.players_with_xgi}/${data.stats.total_players} players |
            <strong>Avg xGI90:</strong> ${(data.stats.avg_xgi90 || 0).toFixed(3)} |
            <strong>Last sync:</strong> ${data.config.last_sync ? new Date(data.config.last_sync * 1000).toLocaleDateString() : 'Never'}
        `;
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
    const existingTooltip = document.getElementById('active-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
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