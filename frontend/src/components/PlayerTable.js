import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  Checkbox,
  FormControlLabel,
  Collapse,
  Card,
  CardContent
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Info,
  Download,
  FilterList,
  Search,
  SportsFootball,
  TrendingUp,
  Add,
  Remove,
  ExpandMore,
  Help
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { Tooltip as ReactTooltip } from 'react-tooltip';

import { exportPlayersCSV, applyStarterOverride, togglePlayerExclusion, resetAllExclusions } from '../services/api';

const PlayerTable = ({ playersData, gameweekInfo, systemConfig, onDataRefresh }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  // Filter states
  const [positionFilter, setPositionFilter] = useState('All');
  const [priceMin, setPriceMin] = useState(5.0);
  const [priceMax, setPriceMax] = useState(30.0);
  const [teamFilter, setTeamFilter] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [historicalDataFilter, setHistoricalDataFilter] = useState('All');
  const [minutesFilterEnabled, setMinutesFilterEnabled] = useState(false);
  const [minutesThreshold, setMinutesThreshold] = useState(180);
  const [starterFilterEnabled, setStarterFilterEnabled] = useState(false);
  const [starterThreshold, setStarterThreshold] = useState(0.8);
  const [roiFilterEnabled, setRoiFilterEnabled] = useState(false);
  const [roiThreshold, setRoiThreshold] = useState(0.75);
  const [overrideFilter, setOverrideFilter] = useState('All');
  const [excludedFilter, setExcludedFilter] = useState('All');
  const [includeAllPlayers, setIncludeAllPlayers] = useState(false);

  // Table states
  const [sortModel, setSortModel] = useState([{ field: 'true_value', sort: 'desc' }]);
  const [pageSize, setPageSize] = useState(100);

  // Starter override states
  const [processingOverride, setProcessingOverride] = useState(null);

  // Exclusion states
  const [processingExclusion, setProcessingExclusion] = useState(null);
  const [resettingExclusions, setResettingExclusions] = useState(false);

  // Help panel state
  const [helpPanelOpen, setHelpPanelOpen] = useState(false);

  // Get unique teams for filter
  const teams = useMemo(() => {
    const uniqueTeams = [...new Set(playersData.map(p => p.team))].sort();
    return ['All', ...uniqueTeams];
  }, [playersData]);

  // Helper function to adjust minutes threshold
  const adjustMinutesThreshold = (increment) => {
    setMinutesThreshold(prev => Math.max(0, prev + (increment ? 45 : -45)));
  };

  // Helper function to adjust starter threshold
  const adjustStarterThreshold = (increment) => {
    setStarterThreshold(prev => Math.max(0, Math.min(1, prev + (increment ? 0.05 : -0.05))));
  };

  // Helper function to adjust ROI threshold
  const adjustRoiThreshold = (increment) => {
    setRoiThreshold(prev => Math.max(0, prev + (increment ? 0.05 : -0.05)));
  };

  // Gradient color functions
  const getTrueValueColor = (value) => {
    if (!value || value <= 0) return theme.palette.text.disabled;
    if (value >= 20) return '#00cc66'; // Deep green
    if (value >= 15) return '#28a745'; // Green
    if (value >= 10) return '#a4c639'; // Yellow-green
    if (value >= 5) return '#ffc107';  // Yellow
    return '#dc3545'; // Red
  };

  const getROIColor = (value) => {
    if (!value || value <= 0) return theme.palette.text.disabled;
    if (value >= 3) return '#00cc66';  // Deep green with glow
    if (value >= 2) return '#28a745';  // Green
    if (value >= 1) return '#ffc107';  // Yellow
    return '#dc3545'; // Red
  };

  const getDynamicColor = (value, maxValue) => {
    if (!value || value <= 0) return '#dc3545'; // Red for 0
    const percentage = (value / maxValue) * 100;

    if (percentage >= 90) return '#00cc66';  // Deep green (90%+ of max)
    if (percentage >= 75) return '#28a745';  // Green (75-90%)
    if (percentage >= 50) return '#a4c639';  // Yellow-green (50-75%)
    if (percentage >= 25) return '#ffc107';  // Yellow (25-50%)
    return '#dc3545'; // Red (<25%)
  };

  const getDynamicColorReverse = (value, maxValue) => {
    if (!value || value <= 0) return '#00cc66'; // Green for 0 (lowest price is best)
    const percentage = (value / maxValue) * 100;

    if (percentage >= 90) return '#dc3545';  // Red (90%+ of max - highest prices)
    if (percentage >= 75) return '#ffc107';  // Yellow (75-90%)
    if (percentage >= 50) return '#a4c639';  // Yellow-green (50-75%)
    if (percentage >= 25) return '#28a745';  // Green (25-50%)
    return '#00cc66'; // Deep green (<25% - lowest prices)
  };

  const getMultiplierColor = (value) => {
    if (!value) return theme.palette.text.disabled;
    const base = parseFloat(value);
    if (base >= 1.5) return '#9c27b0'; // Purple for high multipliers
    if (base >= 1.2) return '#2196f3'; // Blue
    if (base >= 1.0) return '#4caf50'; // Green
    if (base >= 0.8) return '#ff9800'; // Orange
    return '#f44336'; // Red for low multipliers
  };

  const getGamesColor = (currentGames, historicalGames) => {
    const total = currentGames + (historicalGames || 0);
    if (total >= 10) return '#28a745'; // Green - reliable
    if (total >= 5) return '#ffc107';  // Yellow - moderate
    return '#dc3545'; // Red - unreliable
  };

  // Position-aware performance tier calculation
  // Individual tier functions for xG90 and xA90
  const getXG90Tier = (position, xg90) => {
    if (!xg90 || xg90 === 0) return 'Poor';

    // Handle multi-position players
    let pos = position?.toUpperCase();
    if (pos?.includes(',')) {
      const positions = pos.split(',').map(p => p.trim());
      // Priority: G > D > M > F
      if (positions.includes('G')) pos = 'G';
      else if (positions.includes('D')) pos = 'D';
      else if (positions.includes('M')) pos = 'M';
      else if (positions.includes('F') || positions.includes('A')) pos = 'F';
    }

    // Attackers/Forwards (F)
    if (pos === 'F') {
      if (xg90 >= 0.60) return 'Elite';
      if (xg90 >= 0.45) return 'Good';
      if (xg90 >= 0.30) return 'Above Average';
      if (xg90 >= 0.15) return 'Below Average';
      return 'Poor';
    }

    // Midfielders (M)
    if (pos === 'M') {
      if (xg90 >= 0.30) return 'Elite';
      if (xg90 >= 0.20) return 'Good';
      if (xg90 >= 0.10) return 'Above Average';
      if (xg90 >= 0.05) return 'Below Average';
      return 'Poor';
    }

    // Defenders (D)
    if (pos === 'D') {
      if (xg90 >= 0.15) return 'Elite';
      if (xg90 >= 0.10) return 'Good';
      if (xg90 >= 0.05) return 'Above Average';
      if (xg90 >= 0.02) return 'Below Average';
      return 'Poor';
    }

    return 'Poor';
  };

  const getXA90Tier = (position, xa90) => {
    if (!xa90 || xa90 === 0) return 'Poor';

    // Handle multi-position players
    let pos = position?.toUpperCase();
    if (pos?.includes(',')) {
      const positions = pos.split(',').map(p => p.trim());
      // Priority: G > D > M > F
      if (positions.includes('G')) pos = 'G';
      else if (positions.includes('D')) pos = 'D';
      else if (positions.includes('M')) pos = 'M';
      else if (positions.includes('F') || positions.includes('A')) pos = 'F';
    }

    // Attackers/Forwards (F)
    if (pos === 'F') {
      if (xa90 >= 0.25) return 'Elite';
      if (xa90 >= 0.18) return 'Good';
      if (xa90 >= 0.12) return 'Above Average';
      if (xa90 >= 0.07) return 'Below Average';
      return 'Poor';
    }

    // Midfielders (M)
    if (pos === 'M') {
      if (xa90 >= 0.20) return 'Elite';
      if (xa90 >= 0.15) return 'Good';
      if (xa90 >= 0.10) return 'Above Average';
      if (xa90 >= 0.05) return 'Below Average';
      return 'Poor';
    }

    // Defenders (D)
    if (pos === 'D') {
      if (xa90 >= 0.12) return 'Elite';
      if (xa90 >= 0.08) return 'Good';
      if (xa90 >= 0.05) return 'Above Average';
      if (xa90 >= 0.02) return 'Below Average';
      return 'Poor';
    }

    return 'Poor';
  };

  // Performance tier color mapping
  const getPerformanceTierColor = (tier) => {
    switch (tier) {
      case 'Elite': return '#00cc66';        // Deep green
      case 'Good': return '#28a745';         // Green
      case 'Above Average': return '#a4c639'; // Yellow-green
      case 'Below Average': return '#ffc107'; // Yellow
      case 'Poor': return '#dc3545';         // Red
      default: return theme.palette.text.disabled;
    }
  };

  // Position-aware xGI90 tier calculation
  const getXGI90Tier = (position, xgi90) => {
    if (!xgi90 || xgi90 === 0) return 'Poor';

    // Handle multi-position players
    let pos = position?.toUpperCase();
    if (pos?.includes(',')) {
      const positions = pos.split(',').map(p => p.trim());
      // Priority: G > D > M > F
      if (positions.includes('G')) pos = 'G';
      else if (positions.includes('D')) pos = 'D';
      else if (positions.includes('M')) pos = 'M';
      else if (positions.includes('F') || positions.includes('A')) pos = 'F';
    }

    // Attackers/Forwards (F)
    if (pos === 'F') {
      if (xgi90 >= 0.80) return 'Elite';
      if (xgi90 >= 0.60) return 'Good';
      if (xgi90 >= 0.40) return 'Above Average';
      if (xgi90 >= 0.20) return 'Below Average';
      return 'Poor';
    }

    // Midfielders (M)
    if (pos === 'M') {
      if (xgi90 >= 0.45) return 'Elite';
      if (xgi90 >= 0.30) return 'Good';
      if (xgi90 >= 0.20) return 'Above Average';
      if (xgi90 >= 0.10) return 'Below Average';
      return 'Poor';
    }

    // Defenders (D)
    if (pos === 'D') {
      if (xgi90 >= 0.25) return 'Elite';
      if (xgi90 >= 0.18) return 'Good';
      if (xgi90 >= 0.10) return 'Above Average';
      if (xgi90 >= 0.05) return 'Below Average';
      return 'Poor';
    }

    return 'Poor';
  };

  // Enhanced tooltip content for help panel
  const getColumnTooltip = (field) => {
    const tooltips = {
      exclude_from_optimizer: {
        title: 'Exclude from Optimizer',
        description: 'Checkbox to exclude player from lineup optimization',
        interpretation: 'Check to exclude unreliable players (low sample size, injury risk). Use Reset Exclusions button to clear all.',
        details: 'Excluded players will not appear in optimizer suggestions but remain in the main table for tracking.'
      },
      name: {
        title: 'Player Name',
        description: 'Full player name as registered in Fantasy Premier League'
      },
      team: {
        title: 'Team',
        description: 'Current Premier League team'
      },
      position: {
        title: 'Position',
        description: 'Playing position with multi-position support',
        details: 'G (Goalkeeper), D (Defender), M (Midfielder), F (Forward). Multi-position players (D,M or M,F) use primary position for calculations.'
      },
      price: {
        title: 'Price',
        description: 'Current fantasy price in millions (£)',
        formula: 'Set by Fantrax based on player demand and performance'
      },
      total_fpts: {
        title: 'Total Fantasy Points',
        description: 'Cumulative fantasy points for current season (2025-26)',
        interpretation: 'Higher values indicate consistent scoring across multiple gameweeks.'
      },
      ppg: {
        title: 'Points Per Game',
        description: 'Average fantasy points per game for current season (2025-26)',
        formula: 'Total Points ÷ Games Played',
        interpretation: 'Current season form indicator. Compare with Dynamic PPG to see historical context.'
      },
      pp90: {
        title: 'Points Per 90',
        description: 'Fantasy points per 90 minutes played',
        formula: '(Total FPts ÷ Minutes) × 90',
        interpretation: 'Rate statistic showing efficiency per full match. Shows "-" if < 90 mins played.',
        details: 'Higher PP90 indicates better scoring rate when on the pitch. Useful for identifying high-impact substitutes.'
      },
      blended_ppg: {
        title: 'Dynamic PPG (V2.0)',
        description: 'Enhanced PPG blending current season with historical data',
        formula: 'Blended_PPG = (Current_PPG × Games_Weight) + (Previous_PPG × Carryover_Weight)',
        details: 'Adjustable via "Adaptation GW" in parameter panel - controls adaptation speed to current season.'
      },
      games_played_historical: {
        title: '24-25 Games',
        description: 'Total games played in 2024-25 season (historical data)',
        interpretation: 'Green (≥10): Reliable • Yellow (5-9): Moderate • Red (<5): Limited historical data'
      },
      games_played: {
        title: '25-26 Games',
        description: 'Total games played in current season (2025-26)',
        interpretation: 'Green (≥5): Regular starter • Yellow (2-4): Some starts • Red (0-1): Limited appearances'
      },
      true_value: {
        title: 'Projected Score (V2.0)',
        description: 'Advanced prediction using 5-factor model',
        formula: 'True Value = Dynamic_PPG × Form × Fixture × Starter × xGI',
        interpretation: 'Deep Green (≥20): Elite • Green (15-20): Excellent • Yellow (10-15): Good • Red (<5): Poor'
      },
      roi: {
        title: 'ROI - Return on Investment (V2.0)',
        description: 'Value efficiency metric - expected points per £1 spent',
        formula: 'ROI = True Value ÷ Player Price',
        interpretation: 'Deep Green (≥3): Exceptional • Green (2-3): Great • Yellow (1-2): Fair • Red (<1): Poor'
      },
      form_multiplier: {
        title: 'Form Multiplier (V2.0)',
        description: 'Recent performance trend using exponential decay weighting',
        formula: 'Exponentially weighted average of recent games',
        interpretation: 'Measures current form relative to season average. Range automatically adjusts based on games played.',
        details: 'Controlled by "EWMA α" slider (decay rate) and "Form Cap" parameter (maximum range). Lower α = faster decay, more focus on recent games. Form Cap sets the maximum multiplier possible.'
      },
      fixture_multiplier: {
        title: 'NPxG Fixture System (V2.0)',
        description: 'Upcoming fixture difficulty based on team NPxG strength',
        formula: 'Position-specific calculations using team attacking/defensive NPxG metrics',
        interpretation: 'Higher = easier fixtures. Includes home/away adjustments. Weight controlled by NPxG Weight slider (-20% to +20%)',
        details: 'Uses Non-Penalty Expected Goals data to assess team strength. Automatic team code aliasing (BRF→BRE, NOT→NFO) ensures accurate mappings.'
      },
      starter_multiplier: {
        title: 'Starter Prediction (V2.0)',
        description: 'Confidence-based starting probability (5 categories)',
        interpretation: '1.0x: Nailed (≥90%) • 0.90x: Likely (70-89%) • 0.75x: Rotation (50-69%) • 0.50x: Unlikely (30-49%) • 0.35x: Bench (<30%)',
        details: 'From Fantasy Football Pundit. Multipliers adjustable in parameter panel. Override using buttons.'
      },
      starter_override: {
        title: 'Starter Override',
        description: 'Manual controls for starter predictions',
        interpretation: 'S=Starter (1.0x) • L=Likely (0.90x) • R=Rotation (0.75x) • U=Unlikely (0.50x) • B=Bench (dynamic) • O=Out (0.0x) • A=Auto',
        details: 'Click to override automatic predictions. Values adjustable in parameter panel.'
      },
      xgi_multiplier: {
        title: 'xGI Multiplier (V2.0)',
        description: 'Expected Goals Involvement vs position baseline',
        formula: 'Current xGI per 90min ÷ 2024-25 Position Average',
        interpretation: '>1.0 = above average attacking threat for position'
      },
      xgi90: {
        title: 'xGI per 90',
        description: 'Expected Goals Involvement per 90 minutes',
        interpretation: 'Position-specific color coding shows total attacking contribution'
      },
      xg90: {
        title: 'xG per 90',
        description: 'Expected Goals per 90 minutes',
        interpretation: 'Position-specific color coding shows goal threat level'
      },
      xa90: {
        title: 'xA per 90',
        description: 'Expected Assists per 90 minutes',
        interpretation: 'Position-specific color coding shows creative output'
      },
      minutes: {
        title: 'Minutes Played',
        description: 'Total minutes in current season (2025-26)',
        interpretation: 'Use "Min Minutes" filter to exclude limited game time players',
        details: 'Higher minutes = regular playing time and fitness'
      }
    };

    return tooltips[field] || { title: field, description: 'No description available' };
  };

  // Handle starter override
  const handleStarterOverride = async (playerId, overrideType) => {
    try {
      setProcessingOverride(playerId);

      const response = await applyStarterOverride(playerId, overrideType);

      if (response.success) {
        // Refresh data to show updated values
        if (onDataRefresh) {
          await onDataRefresh();
        }
      } else {
        throw new Error(response.error || 'Override failed');
      }
    } catch (error) {
      console.error('Override failed:', error);
      alert('Override failed: ' + error.message);
    } finally {
      setProcessingOverride(null);
    }
  };

  // Handle exclusion toggle
  const handleToggleExclusion = async (playerId) => {
    try {
      setProcessingExclusion(playerId);
      const response = await togglePlayerExclusion(playerId);
      if (response.success) {
        if (onDataRefresh) {
          await onDataRefresh();
        }
      } else {
        throw new Error(response.error || 'Toggle exclusion failed');
      }
    } catch (error) {
      console.error('Toggle exclusion failed:', error);
      alert('Toggle exclusion failed: ' + error.message);
    } finally {
      setProcessingExclusion(null);
    }
  };

  // Handle reset all exclusions
  const handleResetExclusions = async () => {
    try {
      setResettingExclusions(true);
      const response = await resetAllExclusions();
      if (response.success) {
        if (onDataRefresh) {
          await onDataRefresh();
        }
      } else {
        throw new Error(response.error || 'Reset exclusions failed');
      }
    } catch (error) {
      console.error('Reset exclusions failed:', error);
      alert('Reset exclusions failed: ' + error.message);
    } finally {
      setResettingExclusions(false);
    }
  };

  // Custom cell renderer with gradients
  const renderValueCell = (params, colorFunc) => {
    const value = params.value;
    const color = colorFunc(value);
    // Handle both number and string representations (Railway returns decimals as strings)
    const numValue = parseFloat(value);
    const displayValue = !isNaN(numValue) ? numValue.toFixed(3) : (value || '--');

    return (
      <Box
        sx={{
          color,
          fontWeight: 600,
          textAlign: 'center',
          py: 0.5,
          px: 0.25,
          borderRadius: 1,
          background: `linear-gradient(135deg, ${color}15, ${color}08)`,
          border: `1px solid ${color}30`,
          textShadow: isDark ? `0 0 4px ${color}40` : 'none',
        }}
      >
        {displayValue}
      </Box>
    );
  };

  // Render function for dynamic color cells
  const renderDynamicColorCell = (params, maxValue) => {
    const value = parseFloat(params.value) || 0;
    const color = getDynamicColor(value, maxValue);

    return (
      <Box sx={{
        color,
        fontWeight: 600,
        textAlign: 'center',
        py: 0.5,
        px: 1,
        borderRadius: 1,
        background: `linear-gradient(135deg, ${color}15, ${color}08)`,
        border: `1px solid ${color}30`,
        textShadow: isDark ? `0 0 4px ${color}40` : 'none',
      }}>
        {value.toFixed(
          params.field === 'roi' ? 3 :
          params.field === 'price' ? 2 :
          params.field === 'ppg' || params.field === 'total_fpts' ? 1 :
          0
        )}
      </Box>
    );
  };

  // Position-aware xG90 cell renderer
  const renderXG90Cell = (params) => {
    const value = params.value;
    const position = params.row.position;
    const xg90 = params.row.xg90 || 0;

    const tier = getXG90Tier(position, xg90);
    const color = getPerformanceTierColor(tier);
    const displayValue = typeof value === 'number' ? value.toFixed(3) : (value || '--');

    return (
      <Box
        sx={{
          color,
          fontWeight: 600,
          textAlign: 'center',
          py: 0.5,
          px: 1,
          borderRadius: 1,
          background: `linear-gradient(135deg, ${color}15, ${color}08)`,
          border: `1px solid ${color}30`,
          textShadow: isDark ? `0 0 4px ${color}40` : 'none',
        }}
      >
        {displayValue}
      </Box>
    );
  };

  // Position-aware xA90 cell renderer
  const renderXA90Cell = (params) => {
    const value = params.value;
    const position = params.row.position;
    const xa90 = params.row.xa90 || 0;

    const tier = getXA90Tier(position, xa90);
    const color = getPerformanceTierColor(tier);
    const displayValue = typeof value === 'number' ? value.toFixed(3) : (value || '--');

    return (
      <Box
        sx={{
          color,
          fontWeight: 600,
          textAlign: 'center',
          py: 0.5,
          px: 1,
          borderRadius: 1,
          background: `linear-gradient(135deg, ${color}15, ${color}08)`,
          border: `1px solid ${color}30`,
          textShadow: isDark ? `0 0 4px ${color}40` : 'none',
        }}
      >
        {displayValue}
      </Box>
    );
  };

  // Position-aware xGI90 cell renderer
  const renderXGI90Cell = (params) => {
    const value = params.value;
    const position = params.row.position;
    const xgi90 = params.row.xgi90 || 0;

    const tier = getXGI90Tier(position, xgi90);
    const color = getPerformanceTierColor(tier);
    const displayValue = typeof value === 'number' ? value.toFixed(3) : (value || '--');

    return (
      <Box
        sx={{
          color,
          fontWeight: 600,
          textAlign: 'center',
          py: 0.5,
          px: 1,
          borderRadius: 1,
          background: `linear-gradient(135deg, ${color}15, ${color}08)`,
          border: `1px solid ${color}30`,
          textShadow: isDark ? `0 0 4px ${color}40` : 'none',
        }}
      >
        {displayValue}
      </Box>
    );
  };

  // Column definitions with tooltips
  const columns = [
    {
      field: 'exclude_from_optimizer',
      headerName: 'Excl',
      width: 50,
      sortable: true,
      renderCell: (params) => {
        const playerId = params.row.id;
        const isExcluded = params.value || false;
        const isLoading = processingExclusion === playerId;

        return (
          <Checkbox
            checked={isExcluded}
            disabled={isLoading}
            onChange={() => handleToggleExclusion(playerId)}
            size="small"
            sx={{
              color: isExcluded ? '#f44336' : 'text.secondary',
              '&.Mui-checked': {
                color: '#f44336',
              },
              padding: 0,
            }}
            title={isExcluded ? 'Excluded from optimizer - click to include' : 'Click to exclude from optimizer'}
          />
        );
      },
    },
    {
      field: 'name',
      headerName: 'Name',
      width: 180,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight={500}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'team',
      headerName: 'Team',
      width: 80,
    },
    {
      field: 'next_opponent',
      headerName: 'Next',
      width: 60,
      renderCell: (params) => {
        if (!params.value) return '-';
        const isHome = params.row.is_home;
        return (
          <span style={{ fontSize: '0.8rem' }}>
            {isHome ? 'vs ' : '@ '}{params.value}
          </span>
        );
      },
    },
    {
      field: 'position',
      headerName: 'Pos',
      width: 80,
      renderCell: (params) => {
        const positions = params.value ? params.value.split(',').map(p => p.trim()) : [];
        const getPositionColor = (pos) => {
          switch (pos) {
            case 'G': return 'warning';
            case 'D': return 'info';
            case 'M': return 'success';
            case 'F': return 'secondary';
            default: return 'default';
          }
        };

        return (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {positions.map((pos, index) => (
              <Chip
                key={pos + "-" + index}
                label={pos}
                size="small"
                color={getPositionColor(pos)}
                sx={{ fontWeight: 600, fontSize: '0.7rem', minWidth: 'auto' }}
              />
            ))}
          </Box>
        );
      },
    },
    {
      field: 'price',
      headerName: 'Price',
      width: 80,
      type: 'number',
      renderCell: (params) => {
        const value = parseFloat(params.value) || 0;
        const color = getDynamicColorReverse(value, columnMaxValues.maxPrice);

        return (
          <Box sx={{
            color,
            fontWeight: 600,
            textAlign: 'center',
            py: 0.5,
            px: 1,
            borderRadius: 1,
            background: `linear-gradient(135deg, ${color}15, ${color}08)`,
            border: `1px solid ${color}30`,
            textShadow: isDark ? `0 0 4px ${color}40` : 'none',
          }}>
            £{value.toFixed(2)}
          </Box>
        );
      },
    },
    {
      field: 'total_fpts',
      headerName: 'TFPts',
      width: 70,
      type: 'number',
      renderCell: (params) => renderDynamicColorCell(params, columnMaxValues.maxTotalFpts),
    },
    {
      field: 'ppg',
      headerName: 'PPG',
      width: 80,
      type: 'number',
      renderCell: (params) => renderDynamicColorCell(params, columnMaxValues.maxPpg),
    },
    {
      field: 'pp90',
      headerName: 'PP90',
      width: 80,
      type: 'number',
      renderCell: (params) => {
        const pp90Value = params.row.pp90;
        if (pp90Value === null || pp90Value === undefined || pp90Value === 0) {
          return (
            <Box sx={{ color: 'text.secondary', fontStyle: 'italic' }}>-</Box>
          );
        }
        // Format to 1 decimal place and use custom display
        const formattedValue = pp90Value.toFixed(1);
        const color = getDynamicColor(pp90Value, columnMaxValues.maxPp90);
        return (
          <Box sx={{ color, fontWeight: 500 }}>
            {formattedValue}
          </Box>
        );
      }
    },
    {
      field: 'minutes',
      headerName: 'Min',
      width: 70,
      type: 'number',
      renderCell: (params) => renderDynamicColorCell(params, columnMaxValues.maxMinutes),
    },
    {
      field: 'blended_ppg',
      headerName: 'Dynamic PPG',
      width: 120,
      type: 'number',
      renderCell: (params) => {
        const value = parseFloat(params.value);
        const weight = parseFloat(params.row.current_season_weight || 0);
        const percentage = weight * 100;

        // Gradient color based on current season weight (higher % = more current data = better)
        let cellColor;
        if (percentage >= 90) cellColor = '#00cc66';       // Deep green (90-100%)
        else if (percentage >= 75) cellColor = '#28a745';  // Green (75-90%)
        else if (percentage >= 50) cellColor = '#a4c639';  // Yellow-green (50-75%)
        else if (percentage >= 25) cellColor = '#ffc107';  // Yellow (25-50%)
        else if (percentage >= 10) cellColor = '#ff9800';  // Orange (10-25%)
        else cellColor = '#dc3545';                        // Red (<10%)

        return (
          <Box sx={{
            color: cellColor,
            backgroundColor: `${cellColor}15`,
            padding: '4px 8px',
            borderRadius: 1,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            border: `1px solid ${cellColor}30`,
            textShadow: isDark ? `0 0 4px ${cellColor}40` : 'none',
          }}>
            {isNaN(value) ? '0.0' : value.toFixed(1)}
            <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.7rem' }}>
              ({Math.round(percentage)}% curr)
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'games_played_historical',
      headerName: '24-25',
      width: 80,
      renderCell: (params) => {
        const historical = params.row.games_played_historical || 0;
        const color = historical >= 10 ? '#28a745' : historical >= 5 ? '#ffc107' : '#dc3545';

        return (
          <Typography
            variant="body2"
            fontWeight={600}
            sx={{ color, textAlign: 'center' }}
          >
            {historical}
          </Typography>
        );
      },
    },
    {
      field: 'games_played',
      headerName: '25-26',
      width: 80,
      renderCell: (params) => renderDynamicColorCell(params, columnMaxValues.maxGamesPlayed),
    },
    {
      field: 'true_value',
      headerName: 'Projected',
      width: 110,
      type: 'number',
      renderCell: (params) => renderValueCell(params, getTrueValueColor),
    },
    {
      field: 'roi',
      headerName: 'ROI',
      width: 100,
      type: 'number',
      renderCell: (params) => renderDynamicColorCell(params, columnMaxValues.maxRoi),
    },
    {
      field: 'form_multiplier',
      headerName: 'Form',
      width: 90,
      type: 'number',
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
      headerClassName: 'multiplier-group',
    },
    {
      field: 'fixture_multiplier',
      headerName: 'Fixture',
      width: 90,
      type: 'number',
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
      headerClassName: 'multiplier-group',
    },
    {
      field: 'xgi_multiplier',
      headerName: 'xGI',
      width: 90,
      type: 'number',
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
      headerClassName: 'multiplier-group',
    },
    {
      field: 'starter_multiplier',
      headerName: 'Starter',
      width: 90,
      type: 'number',
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
      headerClassName: 'multiplier-group',
    },
    {
      field: 'starter_override',
      headerName: 'Override',
      width: 130,
      sortable: false,
      renderCell: (params) => {
        const playerId = params.row.id;
        const currentOverride = params.row.starter_override || 'auto';
        const isLoading = processingOverride === playerId;

        // Get current penalty values from system config
        const starterConfig = systemConfig?.starter_prediction || {};
        const likelyPenalty = starterConfig.likely_starter_penalty || 0.85;
        const rotationPenalty = starterConfig.auto_rotation_penalty || 0.7;
        const unlikelyPenalty = starterConfig.unlikely_starter_penalty || 0.5;
        const benchPenalty = starterConfig.force_bench_penalty || 0.15;
        const outPenalty = starterConfig.force_out_penalty || 0.0;

        const overrideOptions = [
          { value: 'starter', label: 'S', title: `Definite Starter (1.0x)`, color: '#28a745' },
          { value: 'likely', label: 'L', title: `Likely Starter (${likelyPenalty.toFixed(2)}x)`, color: '#20c997' },
          { value: 'rotation', label: 'R', title: `Rotation Risk (${rotationPenalty.toFixed(2)}x)`, color: '#ff9800' },
          { value: 'unlikely', label: 'U', title: `Unlikely Starter (${unlikelyPenalty.toFixed(2)}x)`, color: '#fd7e14' },
          { value: 'bench', label: 'B', title: `Bench (${benchPenalty.toFixed(2)}x)`, color: '#ffc107' },
          { value: 'out', label: 'O', title: `Out (${outPenalty.toFixed(2)}x)`, color: '#dc3545' }
        ];

        const autoOption = { value: 'auto', label: 'A', title: 'Auto (CSV)', color: '#6c757d' };

        return (
          <Box sx={{ display: 'flex', gap: 0.1, alignItems: 'center' }}>
            {/* 2x3 Grid for S/L/R/U/B/O */}
            <Box sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 16px)',
              gridTemplateRows: 'repeat(2, 16px)',
              gap: 0.15,
              mr: 0.15
            }}>
              {overrideOptions.map(option => (
                <Button
                  key={option.value}
                  size="small"
                  variant={currentOverride === option.value ? 'contained' : 'outlined'}
                  disabled={isLoading}
                  onClick={() => handleStarterOverride(playerId, option.value)}
                  sx={{
                    minWidth: '16px',
                    width: '16px',
                    height: '16px',
                    fontSize: '0.55rem',
                    fontWeight: 600,
                    p: 0,
                    borderColor: option.color,
                    color: currentOverride === option.value ? 'white' : option.color,
                    bgcolor: currentOverride === option.value ? option.color : 'transparent',
                    '&:hover': {
                      bgcolor: option.color,
                      color: 'white',
                    },
                  }}
                  title={option.title}
                >
                  {option.label}
                </Button>
              ))}
            </Box>

            {/* Auto button behind the grid */}
            <Button
              key={autoOption.value}
              size="small"
              variant={currentOverride === autoOption.value ? 'contained' : 'outlined'}
              disabled={isLoading}
              onClick={() => handleStarterOverride(playerId, autoOption.value)}
              sx={{
                minWidth: '28px',
                width: '28px',
                height: '28px',
                fontSize: '0.7rem',
                fontWeight: 600,
                p: 0,
                borderColor: autoOption.color,
                color: currentOverride === autoOption.value ? 'white' : autoOption.color,
                bgcolor: currentOverride === autoOption.value ? autoOption.color : 'transparent',
                '&:hover': {
                  bgcolor: autoOption.color,
                  color: 'white',
                },
              }}
              title={autoOption.title}
            >
              {autoOption.label}
            </Button>
          </Box>
        );
      },
    },
    {
      field: 'xgi90',
      headerName: 'xGI90',
      width: 80,
      type: 'number',
      renderCell: renderXGI90Cell,
    },
    {
      field: 'xg90',
      headerName: 'xG90',
      width: 80,
      type: 'number',
      renderCell: renderXG90Cell,
    },
    {
      field: 'xa90',
      headerName: 'xA90',
      width: 80,
      type: 'number',
      renderCell: renderXA90Cell,
    },
  ];

  // Filter data
  const filteredData = useMemo(() => {
    return playersData.filter(player => {
      // Position filter
      if (positionFilter !== 'All') {
        const playerPositions = player.position ? player.position.split(',').map(p => p.trim()) : [];
        if (!playerPositions.includes(positionFilter)) return false;
      }

      // Price filter
      if (player.price < priceMin || player.price > priceMax) return false;

      // Team filter
      if (teamFilter !== 'All' && player.team !== teamFilter) return false;

      // Search filter
      if (searchTerm && !player.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;

      // Historical data filter
      if (historicalDataFilter !== 'All') {
        const hasHistorical = (player.games_played_historical || 0) > 0;
        if (historicalDataFilter === 'Has Historical' && !hasHistorical) return false;
        if (historicalDataFilter === 'No Historical' && hasHistorical) return false;
      }

      // Minutes filter
      if (minutesFilterEnabled) {
        const minutes = player.minutes || 0;
        if (minutes < minutesThreshold) return false;
      }

      // Starter threshold filter
      if (starterFilterEnabled) {
        const starterMultiplier = player.starter_multiplier || 0;
        if (starterMultiplier < starterThreshold) return false;
      }

      // ROI threshold filter
      if (roiFilterEnabled) {
        const roi = player.roi || 0;
        if (roi < roiThreshold) return false;
      }

      // Override filter
      if (overrideFilter !== 'All') {
        const hasOverride = player.override_type && player.override_type !== 'auto';
        if (overrideFilter === 'Has Override' && !hasOverride) return false;
        if (overrideFilter === 'No Override' && hasOverride) return false;
      }

      // Excluded filter
      if (excludedFilter !== 'All') {
        const isExcluded = player.exclude_from_optimizer || false;
        if (excludedFilter === 'Excluded' && !isExcluded) return false;
        if (excludedFilter === 'Not Excluded' && isExcluded) return false;
      }

      return true;
    });
  }, [playersData, positionFilter, priceMin, priceMax, teamFilter, searchTerm, historicalDataFilter, minutesFilterEnabled, minutesThreshold, starterFilterEnabled, starterThreshold, roiFilterEnabled, roiThreshold, overrideFilter, excludedFilter]);

  // Calculate maximum values for dynamic color coding
  const columnMaxValues = useMemo(() => {
    return {
      maxMinutes: Math.max(...playersData.map(p => p.minutes || 0)),
      maxGamesPlayed: Math.max(...playersData.map(p => p.games_played || 0)),
      maxTotalFpts: Math.max(...playersData.map(p => p.total_fpts || 0)),
      maxPpg: Math.max(...playersData.map(p => p.ppg || 0)),
      maxPp90: Math.max(...playersData.map(p => p.pp90 || 0)),
      maxPrice: Math.max(...playersData.map(p => p.price || 0)),
      maxRoi: Math.max(...playersData.map(p => p.roi || 0))
    };
  }, [playersData]);

  // Export CSV handler
  const handleExportCSV = async () => {
    try {
      await exportPlayersCSV({
        position: positionFilter,
        priceMin,
        priceMax,
        team: teamFilter,
        search: searchTerm,
        include_all: includeAllPlayers
      });
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed: ' + error.message);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{
        background: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
        color: 'white',
        p: 2,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" fontWeight={700}>
            All Active {filteredData.length} Premier League Players
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={includeAllPlayers}
                onChange={(e) => setIncludeAllPlayers(e.target.checked)}
                size="small"
                sx={{ color: "white" }}
              />
            }
            label={`Include all (${includeAllPlayers ? playersData.length : filteredData.length} total)`}
            sx={{ color: "white", fontSize: "0.9rem" }}
          />
          <Button
            startIcon={<Download />}
            onClick={handleExportCSV}
            sx={{ color: "white", borderColor: "white" }}
            variant="outlined"
          >
            Export CSV
          </Button>
          <Tooltip title="Reset all player exclusions from lineup optimizer">
            <Button
              onClick={handleResetExclusions}
              disabled={resettingExclusions}
              sx={{ color: "#ff9800", borderColor: "#ff9800" }}
              variant="outlined"
              size="small"
            >
              {resettingExclusions ? 'Resetting...' : 'Reset Exclusions'}
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Help Panel */}
      <Card sx={{
        mb: 2,
        bgcolor: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
        border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`
      }}>
        <Box
          sx={{
            p: 2,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            '&:hover': {
              bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
            }
          }}
          onClick={() => setHelpPanelOpen(!helpPanelOpen)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Help sx={{ color: isDark ? '#fff' : '#000' }} />
            <Typography variant="h6" sx={{ color: isDark ? '#fff' : '#000' }}>
              Column Explanations & Formulas
            </Typography>
          </Box>
          <ExpandMore
            sx={{
              color: isDark ? '#fff' : '#000',
              transform: helpPanelOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s'
            }}
          />
        </Box>

        <Collapse in={helpPanelOpen}>
          <CardContent sx={{ pt: 0 }}>
            <Grid container spacing={1.5}>
              {[
                'exclude_from_optimizer', 'name', 'team', 'position', 'price', 'total_fpts', 'ppg', 'pp90', 'blended_ppg',
                'games_played_historical', 'games_played', 'true_value', 'roi',
                'form_multiplier', 'fixture_multiplier', 'starter_multiplier', 'starter_override',
                'xgi_multiplier', 'xgi90', 'xg90', 'xa90', 'minutes'
              ].map(field => {
                const tooltip = getColumnTooltip(field);
                return (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={field}>
                    <Paper sx={{ p: 1.5, minHeight: 'auto',
                      bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                      border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`
                    }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5,
                        color: isDark ? '#4fc3f7' : '#1976d2'
                      }}>
                        {tooltip.title}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 0.5,
                        color: isDark ? '#fff' : '#000',
                        fontSize: '0.875rem'
                      }}>
                        {tooltip.description}
                      </Typography>
                      {tooltip.formula && (
                        <Typography variant="caption" sx={{
                          display: 'block',
                          fontFamily: 'monospace',
                          bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                          p: 1,
                          borderRadius: 1, mb: 0.5,
                          color: isDark ? '#90caf9' : '#1565c0'
                        }}>
                          <strong>Formula:</strong> {tooltip.formula}
                        </Typography>
                      )}
                      {tooltip.interpretation && (
                        <Typography variant="caption" sx={{
                          display: 'block',
                          color: isDark ? '#a5d6a7' : '#2e7d32',
                          fontSize: '0.75rem'
                        }}>
                          <strong>Guide:</strong> {tooltip.interpretation}
                        </Typography>
                      )}
                      {tooltip.details && (
                        <Typography variant="caption" sx={{
                          display: 'block',
                          color: isDark ? '#ffcc80' : '#f57c00',
                          fontSize: '0.75rem',
                          mt: 0.5
                        }}>
                          <strong>Details:</strong> {tooltip.details}
                        </Typography>
                      )}
                    </Paper>
                  </Grid>
                );
              })}
            </Grid>
          </CardContent>
        </Collapse>
      </Card>

      {/* Filters */}
      <Box sx={{ p: 2, bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)' }}>
        <Grid container spacing={2} alignItems="center">
          {/* Position Filter */}
          <Grid item>
            <ToggleButtonGroup
              value={positionFilter}
              exclusive
              onChange={(e, newValue) => newValue && setPositionFilter(newValue)}
              size="small"
            >
              {['All', 'G', 'D', 'M', 'F'].map(pos => (
                <ToggleButton key={pos} value={pos}>
                  {pos}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Grid>

          {/* Price Range */}
          <Grid item>
            <TextField
              label="Min Price"
              type="number"
              value={priceMin}
              onChange={(e) => setPriceMin(parseFloat(e.target.value) || 5.0)}
              size="small"
              sx={{ width: 100 }}
            />
          </Grid>
          <Grid item>
            <TextField
              label="Max Price"
              type="number"
              value={priceMax}
              onChange={(e) => setPriceMax(parseFloat(e.target.value) || 30.0)}
              size="small"
              sx={{ width: 100 }}
            />
          </Grid>

          {/* Team Filter */}
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Team</InputLabel>
              <Select
                value={teamFilter}
                label="Team"
                onChange={(e) => setTeamFilter(e.target.value)}
              >
                {teams.map(team => (
                  <MenuItem key={team} value={team}>{team}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Historical Data Filter */}
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Historical Data</InputLabel>
              <Select
                value={historicalDataFilter}
                label="Historical Data"
                onChange={(e) => setHistoricalDataFilter(e.target.value)}
              >
                <MenuItem value="All">All</MenuItem>
                <MenuItem value="Has Historical">Has Historical</MenuItem>
                <MenuItem value="No Historical">No Historical</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Override Filter */}
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 130 }}>
              <InputLabel>Override</InputLabel>
              <Select
                value={overrideFilter}
                label="Override"
                onChange={(e) => setOverrideFilter(e.target.value)}
              >
                <MenuItem value="All">All</MenuItem>
                <MenuItem value="Has Override">Has Override</MenuItem>
                <MenuItem value="No Override">No Override</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Excluded Filter */}
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Excluded</InputLabel>
              <Select
                value={excludedFilter}
                label="Excluded"
                onChange={(e) => setExcludedFilter(e.target.value)}
              >
                <MenuItem value="All">All</MenuItem>
                <MenuItem value="Excluded">Excluded</MenuItem>
                <MenuItem value="Not Excluded">Not Excluded</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Minutes Filter */}
          <Grid item>
            <FormControlLabel
              control={
                <Checkbox
                  checked={minutesFilterEnabled}
                  onChange={(e) => setMinutesFilterEnabled(e.target.checked)}
                  size="small"
                />
              }
              label="Min Minutes"
            />
          </Grid>
          <Grid item>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton
                size="small"
                onClick={() => adjustMinutesThreshold(false)}
                disabled={!minutesFilterEnabled}
                sx={{ bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
              >
                <Remove fontSize="small" />
              </IconButton>
              <TextField
                type="number"
                value={minutesThreshold}
                onChange={(e) => setMinutesThreshold(parseInt(e.target.value) || 180)}
                size="small"
                disabled={!minutesFilterEnabled}
                sx={{ width: 80 }}
              />
              <IconButton
                size="small"
                onClick={() => adjustMinutesThreshold(true)}
                disabled={!minutesFilterEnabled}
                sx={{ bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
              >
                <Add fontSize="small" />
              </IconButton>
            </Box>
          </Grid>

          {/* Starter Filter */}
          <Grid item>
            <FormControlLabel
              control={
                <Checkbox
                  checked={starterFilterEnabled}
                  onChange={(e) => setStarterFilterEnabled(e.target.checked)}
                  size="small"
                />
              }
              label="Min Starter"
            />
          </Grid>
          <Grid item>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton
                size="small"
                onClick={() => adjustStarterThreshold(false)}
                disabled={!starterFilterEnabled}
                sx={{ bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
              >
                <Remove fontSize="small" />
              </IconButton>
              <TextField
                type="number"
                value={starterThreshold.toFixed(2)}
                onChange={(e) => setStarterThreshold(parseFloat(e.target.value) || 0.8)}
                size="small"
                disabled={!starterFilterEnabled}
                sx={{ width: 80 }}
                inputProps={{ step: 0.05, min: 0, max: 1 }}
              />
              <IconButton
                size="small"
                onClick={() => adjustStarterThreshold(true)}
                disabled={!starterFilterEnabled}
                sx={{ bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
              >
                <Add fontSize="small" />
              </IconButton>
            </Box>
          </Grid>

          {/* ROI Filter */}
          <Grid item>
            <FormControlLabel
              control={
                <Checkbox
                  checked={roiFilterEnabled}
                  onChange={(e) => setRoiFilterEnabled(e.target.checked)}
                  size="small"
                />
              }
              label="Min ROI"
            />
          </Grid>
          <Grid item>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton
                size="small"
                onClick={() => adjustRoiThreshold(false)}
                disabled={!roiFilterEnabled}
                sx={{ bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
              >
                <Remove fontSize="small" />
              </IconButton>
              <TextField
                type="number"
                value={roiThreshold.toFixed(2)}
                onChange={(e) => setRoiThreshold(parseFloat(e.target.value) || 0.75)}
                size="small"
                disabled={!roiFilterEnabled}
                sx={{ width: 80 }}
                inputProps={{ step: 0.05, min: 0 }}
              />
              <IconButton
                size="small"
                onClick={() => adjustRoiThreshold(true)}
                disabled={!roiFilterEnabled}
                sx={{ bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
              >
                <Add fontSize="small" />
              </IconButton>
            </Box>
          </Grid>

          {/* Search */}
          <Grid item xs>
            <TextField
              placeholder="Search players..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
              fullWidth
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, opacity: 0.6 }} />,
              }}
            />
          </Grid>
        </Grid>
      </Box>

      {/* Data Grid */}
      <Box sx={{ height: 600 }}>
        <DataGrid
          rows={filteredData}
          columns={columns}
          pageSize={pageSize}
          onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
          rowsPerPageOptions={[50, 100, 200]}
          sortModel={sortModel}
          onSortModelChange={(newSortModel) => setSortModel(newSortModel)}
          disableSelectionOnClick
          density="compact"
          sx={{
            border: 'none',
            '& .MuiDataGrid-row:hover': {
              bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)',
            },
            '& .MuiDataGrid-columnHeader': {
              bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
              fontWeight: 600,
            },
            '& .MuiDataGrid-columnHeader.multiplier-group': {
              bgcolor: isDark ? 'rgba(76, 175, 80, 0.15)' : 'rgba(76, 175, 80, 0.1)',
              borderLeft: isDark ? '2px solid rgba(76, 175, 80, 0.3)' : '2px solid rgba(76, 175, 80, 0.2)',
              borderRight: isDark ? '2px solid rgba(76, 175, 80, 0.3)' : '2px solid rgba(76, 175, 80, 0.2)',
            },
            '& .MuiDataGrid-cell': {
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            },
          }}
        />
      </Box>
      {/* Build Version Footer */}
      <Box sx={{
        mt: 2,
        textAlign: "center",
        opacity: 0.6,
        fontSize: "0.75rem",
        color: theme.palette.text.secondary
      }}>
        Build: {process.env.REACT_APP_BUILD_TIME || new Date().toISOString().slice(0, 19).replace("T", " ")} |
        Tooltips: {columns.length} columns
      </Box>
    </Box>
  );
};

export default PlayerTable;