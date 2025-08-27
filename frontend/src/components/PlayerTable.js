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
  Paper
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Info,
  Download,
  FilterList,
  Search,
  SportsFootball,
  TrendingUp
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { Tooltip as ReactTooltip } from 'react-tooltip';

import { exportPlayersCSV, applyStarterOverride } from '../services/api';

const PlayerTable = ({ playersData, gameweekInfo, onDataRefresh }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  // Filter states
  const [positionFilter, setPositionFilter] = useState('All');
  const [priceMin, setPriceMin] = useState(5.0);
  const [priceMax, setPriceMax] = useState(30.0);
  const [teamFilter, setTeamFilter] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  // Table states
  const [sortModel, setSortModel] = useState([{ field: 'true_value', sort: 'desc' }]);
  const [pageSize, setPageSize] = useState(100);
  
  // Starter override states
  const [processingOverride, setProcessingOverride] = useState(null);

  // Get unique teams for filter
  const teams = useMemo(() => {
    const uniqueTeams = [...new Set(playersData.map(p => p.team))].sort();
    return ['All', ...uniqueTeams];
  }, [playersData]);

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
    
    const pos = position?.toUpperCase();
    
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
    
    const pos = position?.toUpperCase();
    
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
    
    const pos = position?.toUpperCase();
    
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

  // Tooltip content generator
  const getColumnTooltip = (field) => {
    const tooltips = {
      name: { title: 'Player Name', description: 'Full player name as registered in Fantasy Premier League' },
      team: { title: 'Team', description: 'Current Premier League team' },
      position: { title: 'Position', description: 'Primary playing position: G (Goalkeeper), D (Defender), M (Midfielder), F (Forward)' },
      price: { title: 'Price', description: 'Current fantasy price in millions (£)', formula: 'Set by Fantrax based on demand' },
      ppg: { title: 'Points Per Game', description: 'Average fantasy points per game played', formula: 'Total Points ÷ Games Played' },
      games: { 
        title: 'Games Data', 
        description: 'Total games used for analysis',
        interpretation: 'Green (≥10): Reliable • Yellow (5-9): Moderate • Red (<5): Limited data'
      },
      true_value: {
        title: 'True Value (V2.0)',
        description: 'V2.0 Enhanced prediction of expected points per game',
        formula: 'True Value = Blended_PPG × Form × Fixture × Starter × xGI',
        interpretation: 'Deep Green (≥20): Elite • Green (15-20): Excellent • Yellow (10-15): Good • Orange (5-10): Average • Red (<5): Poor'
      },
      roi: {
        title: 'ROI - Return on Investment (V2.0)',
        description: 'Value efficiency metric - how many points per £1 spent',
        formula: 'ROI = True Value ÷ Player Price',
        interpretation: 'Deep Green (≥3): Exceptional value • Green (2-3): Great value • Yellow (1-2): Fair value • Red (<1): Poor value'
      },
      form_multiplier: {
        title: 'Form Multiplier (V2.0)',
        description: 'EWMA weighted recent performance multiplier',
        formula: 'Exponential Weighted Moving Average (α=0.87)',
        interpretation: 'Purple (≥1.5): Hot form • Blue (1.2-1.5): Good form • Green (1.0-1.2): Average • Orange (0.8-1.0): Poor form • Red (<0.8): Very poor'
      },
      fixture_multiplier: {
        title: 'Fixture Difficulty (V2.0)',
        description: 'Upcoming fixture difficulty adjustment',
        formula: 'base^(-difficulty) using betting odds',
        interpretation: 'Higher values indicate easier fixtures ahead'
      },
      starter_multiplier: {
        title: 'Starter Prediction (V2.0)',
        description: 'Probability-based starting eleven prediction',
        interpretation: '1.0x: Guaranteed starter • 0.8x: Likely starter • 0.5x: Rotation risk • 0.2x: Unlikely to start'
      },
      xgi_multiplier: {
        title: 'xGI Multiplier (V2.0)',
        description: 'Expected Goals Involvement normalized to position',
        formula: 'Current xGI ÷ 2024-25 Position Baseline',
        interpretation: 'Measures attacking threat relative to position peers'
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

  // Custom cell renderer with gradients
  const renderValueCell = (params, colorFunc) => {
    const value = params.value;
    const color = colorFunc(value);
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
      field: 'name',
      headerName: 'Name',
      width: 180,
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Name</Typography>
          <Tooltip title={getColumnTooltip('name').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
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
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Team</Typography>
          <Tooltip title={getColumnTooltip('team').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
    },
    {
      field: 'position',
      headerName: 'Pos',
      width: 60,
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Pos</Typography>
          <Tooltip title={getColumnTooltip('position').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          size="small" 
          color={
            params.value === 'G' ? 'warning' :
            params.value === 'D' ? 'info' :
            params.value === 'M' ? 'success' : 'secondary'
          }
          sx={{ fontWeight: 600, fontSize: '0.75rem' }}
        />
      ),
    },
    {
      field: 'price',
      headerName: 'Price',
      width: 80,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Price</Typography>
          <Tooltip title={getColumnTooltip('price').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => `£${params.value}`,
    },
    {
      field: 'total_fpts',
      headerName: 'TFPts',
      width: 70,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>TFPts</Typography>
          <Tooltip title="Total Fantasy Points - Cumulative fantasy points across all gameweeks played">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => {
        const value = parseFloat(params.value);
        return isNaN(value) ? '0.0' : value.toFixed(1);
      },
    },
    {
      field: 'ppg',
      headerName: 'PPG',
      width: 80,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>PPG</Typography>
          <Tooltip title={getColumnTooltip('ppg').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => {
        const value = parseFloat(params.value);
        return isNaN(value) ? '0.0' : value.toFixed(1);
      },
    },
    {
      field: 'blended_ppg',
      headerName: 'Dynamic PPG',
      width: 120,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Dynamic PPG</Typography>
          <Tooltip title="Blended PPG used in True Value calculation. Smoothly transitions from historical (24-25) to current season data. Shows the actual baseline used in the formula.">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => {
        const value = parseFloat(params.value);
        const weight = parseFloat(params.row.current_season_weight || 0);
        const isReliable = weight > 0.5; // More than 50% current season data
        
        const cellColor = isReliable ? '#28a745' : weight > 0.2 ? '#ffc107' : '#dc3545';
        const bgColor = isReliable ? 'rgba(40, 167, 69, 0.1)' : weight > 0.2 ? 'rgba(255, 193, 7, 0.1)' : 'rgba(220, 53, 69, 0.1)';
        
        return (
          <Box sx={{ 
            color: cellColor, 
            backgroundColor: bgColor, 
            padding: '4px 8px', 
            borderRadius: 1, 
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 0.5
          }}>
            {isNaN(value) ? '0.0' : value.toFixed(1)}
            <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.7rem' }}>
              ({Math.round(weight * 100)}% curr)
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'games_played_historical',
      headerName: '24-25',
      width: 60,
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>24-25</Typography>
          <Tooltip title="Games played in 2024-25 season (historical data)">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
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
      width: 60,
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>25-26</Typography>
          <Tooltip title="Games played in current season (2025-26)">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => {
        const current = params.row.games_played || 0;
        const color = current >= 5 ? '#28a745' : current >= 2 ? '#ffc107' : current === 0 ? '#dc3545' : '#ff9800';
        
        return (
          <Typography 
            variant="body2" 
            fontWeight={600}
            sx={{ color, textAlign: 'center' }}
          >
            {current}
          </Typography>
        );
      },
    },
    {
      field: 'true_value',
      headerName: 'True Value',
      width: 110,
      type: 'number',
      renderHeader: (params) => (
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1,
            background: 'linear-gradient(135deg, #28a745, #20c997)',
            color: 'white',
            px: 1,
            py: 0.5,
            borderRadius: 1,
            fontWeight: 700
          }}
        >
          <Typography variant="subtitle2" fontWeight={700}>True Value</Typography>
          <Tooltip title={getColumnTooltip('true_value').description}>
            <Info fontSize="small" sx={{ color: 'white', cursor: 'help' }} />
          </Tooltip>
          <Chip label="V2.0" size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontSize: '0.6rem' }} />
        </Box>
      ),
      renderCell: (params) => renderValueCell(params, getTrueValueColor),
    },
    {
      field: 'roi',
      headerName: 'ROI',
      width: 100,
      type: 'number',
      renderHeader: (params) => (
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1,
            background: 'linear-gradient(135deg, #17a2b8, #138496)',
            color: 'white',
            px: 1,
            py: 0.5,
            borderRadius: 1,
            fontWeight: 700
          }}
        >
          <Typography variant="subtitle2" fontWeight={700}>ROI</Typography>
          <Tooltip title={getColumnTooltip('roi').description}>
            <Info fontSize="small" sx={{ color: 'white', cursor: 'help' }} />
          </Tooltip>
          <Chip label="V2.0" size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontSize: '0.6rem' }} />
        </Box>
      ),
      renderCell: (params) => renderValueCell(params, getROIColor),
    },
    {
      field: 'form_multiplier',
      headerName: 'Form',
      width: 90,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Form</Typography>
          <Tooltip title={getColumnTooltip('form_multiplier').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
    },
    {
      field: 'fixture_multiplier',
      headerName: 'Fixture',
      width: 90,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Fixture</Typography>
          <Tooltip title={getColumnTooltip('fixture_multiplier').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
    },
    {
      field: 'starter_multiplier',
      headerName: 'Starter',
      width: 90,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Starter</Typography>
          <Tooltip title={getColumnTooltip('starter_multiplier').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
    },
    {
      field: 'starter_override',
      headerName: 'Override',
      width: 120,
      sortable: false,
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Override</Typography>
          <Tooltip title="Manual starter override controls: S=Starter (1.0x), R=Rotation Risk (0.75x), B=Bench (0.6x), O=Out (0.0x), A=Auto">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => {
        const playerId = params.row.id;
        const currentOverride = params.row.starter_override || 'auto';
        const isLoading = processingOverride === playerId;
        
        const overrideOptions = [
          { value: 'starter', label: 'S', title: 'Starter (1.0x)', color: '#28a745' },
          { value: 'rotation', label: 'R', title: 'Rotation Risk (0.75x)', color: '#ff9800' },
          { value: 'bench', label: 'B', title: 'Bench (0.6x)', color: '#ffc107' },
          { value: 'out', label: 'O', title: 'Out (0.0x)', color: '#dc3545' },
          { value: 'auto', label: 'A', title: 'Auto (CSV)', color: '#6c757d' }
        ];

        return (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {overrideOptions.map(option => (
              <Button
                key={option.value}
                size="small"
                variant={currentOverride === option.value ? 'contained' : 'outlined'}
                disabled={isLoading}
                onClick={() => handleStarterOverride(playerId, option.value)}
                sx={{
                  minWidth: '24px',
                  width: '24px',
                  height: '24px',
                  fontSize: '0.7rem',
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
        );
      },
    },
    {
      field: 'xgi_multiplier',
      headerName: 'xGI',
      width: 90,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>xGI</Typography>
          <Tooltip title={getColumnTooltip('xgi_multiplier').description}>
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: (params) => renderValueCell(params, getMultiplierColor),
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)}x` : '--',
    },
    {
      field: 'xgi90',
      headerName: 'xGI90',
      width: 80,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>xGI90</Typography>
          <Tooltip title="Expected Goals Involvement per 90 minutes - Color based on position-specific performance tiers">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: renderXGI90Cell,
    },
    {
      field: 'xg90',
      headerName: 'xG90',
      width: 80,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>xG90</Typography>
          <Tooltip title="Expected Goals per 90 minutes - Color based on position-specific performance tiers">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: renderXG90Cell,
    },
    {
      field: 'xa90',
      headerName: 'xA90',
      width: 80,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>xA90</Typography>
          <Tooltip title="Expected Assists per 90 minutes - Color based on position-specific performance tiers">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
      renderCell: renderXA90Cell,
    },
    {
      field: 'minutes',
      headerName: 'Min',
      width: 70,
      type: 'number',
      renderHeader: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={600}>Min</Typography>
          <Tooltip title="Total minutes played this season">
            <Info fontSize="small" sx={{ opacity: 0.7, cursor: 'help' }} />
          </Tooltip>
        </Box>
      ),
    },
  ];

  // Filter data
  const filteredData = useMemo(() => {
    return playersData.filter(player => {
      // Position filter
      if (positionFilter !== 'All' && player.position !== positionFilter) return false;
      
      // Price filter
      if (player.price < priceMin || player.price > priceMax) return false;
      
      // Team filter
      if (teamFilter !== 'All' && player.team !== teamFilter) return false;
      
      // Search filter
      if (searchTerm && !player.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      
      return true;
    });
  }, [playersData, positionFilter, priceMin, priceMax, teamFilter, searchTerm]);

  // Export CSV handler
  const handleExportCSV = async () => {
    try {
      await exportPlayersCSV({
        position: positionFilter,
        priceMin,
        priceMax,
        team: teamFilter,
        search: searchTerm
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
          <SportsFootball />
          <Typography variant="h6" fontWeight={700}>
            All {filteredData.length} Premier League Players
          </Typography>
          {gameweekInfo && (
            <Chip 
              label={`Gameweek ${gameweekInfo.current_gameweek}`}
              icon={<TrendingUp />}
              sx={{ bgcolor: 'rgba(0,255,136,0.9)', color: 'black', fontWeight: 600 }}
            />
          )}
        </Box>
        <Button
          startIcon={<Download />}
          onClick={handleExportCSV}
          sx={{ color: 'white', borderColor: 'white' }}
          variant="outlined"
        >
          Export CSV
        </Button>
      </Box>

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
            '& .MuiDataGrid-cell': {
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            },
          }}
        />
      </Box>
    </Box>
  );
};

export default PlayerTable;