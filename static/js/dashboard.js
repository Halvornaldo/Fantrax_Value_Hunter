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

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Fantrax Value Hunter Dashboard initializing...');
    
    // Load initial configuration and data
    loadSystemConfig();
    loadPlayersData();
    
    // Set up event listeners
    setupParameterControls();
    setupTableControls();
    setupFilterControls();
    
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

async function loadPlayersData() {
    try {
        console.log('📡 Loading 633 players data...');
        showLoadingOverlay('Loading player data...');
        
        // Build query parameters
        const params = new URLSearchParams({
            gameweek: 1,
            limit: pageSize,
            offset: currentPage * pageSize
        });
        
        // Add filters
        if (currentFilters.positions.length < 4) {
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
    
    // Fixture difficulty controls
    const fixtureDiff = currentConfig.fixture_difficulty || {};
    document.getElementById('fixture-enabled').checked = fixtureDiff.enabled || false;
    
    if (fixtureDiff.mode === '3_tier') {
        document.getElementById('mode-3tier').checked = true;
    } else {
        document.getElementById('mode-5tier').checked = true;
    }
    
    // Update 5-tier sliders
    const tier5 = fixtureDiff['5_tier_multipliers'] || {};
    updateSlider('very-easy-slider', tier5.very_easy?.multiplier || 1.3);
    updateSlider('easy-slider', tier5.easy?.multiplier || 1.15);
    updateSlider('hard-slider', tier5.hard?.multiplier || 0.85);
    updateSlider('very-hard-slider', tier5.very_hard?.multiplier || 0.7);
    
    // Update 3-tier sliders
    const tier3 = fixtureDiff['3_tier_multipliers'] || {};
    updateSlider('easy-3tier-slider', tier3.easy?.multiplier || 1.2);
    updateSlider('hard-3tier-slider', tier3.hard?.multiplier || 0.8);
    
    // Starter prediction controls
    const starterPred = currentConfig.starter_prediction || {};
    document.getElementById('starter-enabled').checked = starterPred.enabled || false;
    updateSlider('rotation-penalty-slider', starterPred.auto_rotation_penalty || 0.65);
    updateSlider('bench-penalty-slider', starterPred.force_bench_penalty || 0.6);
    
    // Update control section visibility
    updateControlVisibility();
    
    // Update tier mode visibility
    toggleTierMode();
}

function updateSlider(sliderId, value) {
    const slider = document.getElementById(sliderId);
    const display = document.getElementById(sliderId.replace('-slider', '-display'));
    
    if (slider && display) {
        slider.value = value;
        display.textContent = value.toFixed(2) + 'x';
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
}

function toggleTierMode() {
    const tier3Selected = document.getElementById('mode-3tier').checked;
    document.getElementById('tier-5-controls').style.display = tier3Selected ? 'none' : 'block';
    document.getElementById('tier-3-controls').style.display = tier3Selected ? 'block' : 'none';
}

// =================================================================
// PLAYER TABLE FUNCTIONS
// =================================================================

function updatePlayerTable() {
    const tbody = document.getElementById('player-table-body');
    
    if (!playersData || playersData.length === 0) {
        tbody.innerHTML = '<tr class="loading-row"><td colspan="10">No players found</td></tr>';
        return;
    }
    
    const rows = playersData.map(player => {
        const trueValue = parseFloat(player.true_value || 0);
        const valueClass = trueValue > 1.0 ? 'value-high' : trueValue > 0.5 ? 'value-medium' : 'value-low';
        const playerId = player.id;
        
        return `
            <tr>
                <td><strong>${escapeHtml(player.name || 'Unknown')}</strong></td>
                <td>${escapeHtml(player.team || 'N/A')}</td>
                <td>${escapeHtml(player.position || 'N/A')}</td>
                <td>$${parseFloat(player.price || 0).toFixed(1)}</td>
                <td>${parseFloat(player.ppg || 0).toFixed(1)}</td>
                <td class="${valueClass}">${trueValue.toFixed(3)}</td>
                <td>${parseFloat(player.form_multiplier || 1.0).toFixed(2)}x</td>
                <td>${parseFloat(player.fixture_multiplier || 1.0).toFixed(2)}x</td>
                <td>${parseFloat(player.starter_multiplier || 1.0).toFixed(2)}x</td>
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

function handleManualOverride(playerId, overrideType) {
    if (overrideType === 'auto') {
        // Remove override
        delete manualOverrides[playerId];
    } else {
        // Set override
        manualOverrides[playerId] = {
            type: overrideType,
            multiplier: overrideType === 'starter' ? 1.0 : 
                       overrideType === 'bench' ? parseFloat(document.getElementById('bench-penalty-slider').value) :
                       0.0 // out
        };
    }
    
    // Mark as pending change
    handleParameterChange();
    console.log('🔧 Manual override set:', playerId, overrideType, manualOverrides[playerId]);
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
    
    // Fixture difficulty controls
    document.getElementById('fixture-enabled').addEventListener('change', handleParameterChange);
    document.getElementById('mode-3tier').addEventListener('change', handleParameterChange);
    document.getElementById('mode-5tier').addEventListener('change', handleParameterChange);
    
    // 5-tier sliders
    setupSlider('very-easy-slider');
    setupSlider('easy-slider');
    setupSlider('hard-slider');
    setupSlider('very-hard-slider');
    
    // 3-tier sliders  
    setupSlider('easy-3tier-slider');
    setupSlider('hard-3tier-slider');
    
    // Tier mode switching
    document.getElementById('mode-3tier').addEventListener('change', toggleTierMode);
    document.getElementById('mode-5tier').addEventListener('change', toggleTierMode);
    
    // Starter prediction controls
    document.getElementById('starter-enabled').addEventListener('change', handleParameterChange);
    setupSlider('rotation-penalty-slider');
    setupSlider('bench-penalty-slider');
    
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
    
    // Fixture difficulty changes
    const fixtureEnabled = document.getElementById('fixture-enabled').checked;
    const mode = document.getElementById('mode-5tier').checked ? '5_tier' : '3_tier';
    
    const tier5Multipliers = {};
    const tier3Multipliers = {};
    const currentTier5 = currentConfig.fixture_difficulty?.['5_tier_multipliers'] || {};
    const currentTier3 = currentConfig.fixture_difficulty?.['3_tier_multipliers'] || {};
    
    // Handle 5-tier multipliers
    ['very-easy', 'easy', 'hard', 'very-hard'].forEach(tier => {
        const slider = document.getElementById(`${tier}-slider`);
        const newValue = parseFloat(slider.value);
        const currentValue = currentTier5[tier.replace('-', '_')]?.multiplier || 
                            (tier === 'very-easy' ? 1.3 : tier === 'easy' ? 1.15 : 
                             tier === 'hard' ? 0.85 : 0.7);
        
        if (Math.abs(newValue - currentValue) > 0.01) {
            tier5Multipliers[tier.replace('-', '_')] = { multiplier: newValue };
        }
    });
    
    // Handle 3-tier multipliers
    ['easy', 'hard'].forEach(tier => {
        const slider = document.getElementById(`${tier}-3tier-slider`);
        const newValue = parseFloat(slider.value);
        const currentValue = currentTier3[tier]?.multiplier || 
                            (tier === 'easy' ? 1.2 : 0.8);
        
        if (Math.abs(newValue - currentValue) > 0.01) {
            tier3Multipliers[tier] = { multiplier: newValue };
        }
    });
    
    // Build fixture difficulty changes object
    const fixtureChanges = {
        enabled: fixtureEnabled,
        mode: mode
    };
    
    if (mode === '5_tier' && Object.keys(tier5Multipliers).length > 0) {
        fixtureChanges['5_tier_multipliers'] = tier5Multipliers;
    } else if (mode === '3_tier' && Object.keys(tier3Multipliers).length > 0) {
        fixtureChanges['3_tier_multipliers'] = tier3Multipliers;
    }
    
    if (fixtureEnabled !== (currentConfig.fixture_difficulty?.enabled || false) ||
        mode !== (currentConfig.fixture_difficulty?.mode || '5_tier') ||
        Object.keys(tier5Multipliers).length > 0 ||
        Object.keys(tier3Multipliers).length > 0) {
        changes.fixture_difficulty = fixtureChanges;
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
    
    // Manual overrides - add to changes if any exist
    if (Object.keys(manualOverrides).length > 0) {
        changes.manual_overrides = manualOverrides;
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
    
    // Sort current data and update table
    sortPlayersData();
    updatePlayerTable();
}

function sortPlayersData() {
    playersData.sort((a, b) => {
        let aVal = a[currentSort.field];
        let bVal = b[currentSort.field];
        
        // Handle different data types
        if (typeof aVal === 'string') {
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

// Initialize CSV file input handler
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('csv-file-input').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            console.log('📁 CSV file selected:', file.name);
            // TODO: Implement CSV upload to /api/import-lineups
            showError('CSV import functionality coming in Day 6');
        }
    });
});