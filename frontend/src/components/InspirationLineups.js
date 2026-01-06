import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  Select,
  MenuItem,
  CircularProgress,
  Chip,
  Tooltip,
  Grid,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { Lightbulb } from '@mui/icons-material';
import { fetchPlayersData } from '../services/api';

// Metric options for the dropdown
const METRIC_OPTIONS = [
  { value: 'true_value', label: 'Projected Points', color: '#4caf50' },
  { value: 'form_multiplier', label: 'Best Form', color: '#ff9800' },
  { value: 'xgi_multiplier', label: 'XG90+XA90', color: '#2196f3' },
  { value: 'ppg', label: 'Points per game', color: '#9c27b0' },
  { value: 'pp90', label: 'Points per 90', color: '#e91e63' },
  { value: 'roi', label: 'Value (ROI)', color: '#00bcd4' },
];

// Minimum minutes required
const MIN_MINUTES = 135;

// Minimum starter multiplier to be considered "likely to start"
const MIN_STARTER_MULTIPLIER = 0.8;

/**
 * InspirationPlayerCard - Compact player card for inspiration view
 */
const InspirationPlayerCard = ({ player, metric, darkMode, isBench }) => {
  const getMetricValue = () => {
    switch (metric) {
      case 'form_multiplier':
        return (parseFloat(player.form_multiplier) || 0).toFixed(2);
      case 'xgi_multiplier':
        return (parseFloat(player.xgi_multiplier) || 0).toFixed(2);
      case 'ppg':
        return (parseFloat(player.ppg) || 0).toFixed(1);
      case 'pp90':
        // Calculate PP90: (total_fpts / minutes) * 90
        const mins = parseFloat(player.minutes) || 0;
        const fpts = parseFloat(player.total_fpts) || 0;
        const pp90 = mins > 0 ? (fpts / mins) * 90 : 0;
        return pp90.toFixed(1);
      case 'roi':
        return (parseFloat(player.roi) || 0).toFixed(2);
      case 'true_value':
      default:
        return (parseFloat(player.true_value) || 0).toFixed(1);
    }
  };

  const getMetricColor = () => {
    const option = METRIC_OPTIONS.find(o => o.value === metric);
    return option?.color || '#4caf50';
  };

  // Get display name (last name)
  const getDisplayName = (name) => {
    if (!name) return 'Unknown';
    const parts = name.split(' ');
    if (parts.length > 1) {
      return parts[parts.length - 1];
    }
    return name.length > 10 ? name.substring(0, 9) + '.' : name;
  };

  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="body2" fontWeight={600}>{player.name}</Typography>
          <Typography variant="caption" display="block">Team: {player.team}</Typography>
          <Typography variant="caption" display="block">Position: {player.position}</Typography>
          <Typography variant="caption" display="block">Price: ${(parseFloat(player.price) || 0).toFixed(2)}</Typography>
          <Typography variant="caption" display="block">Minutes: {player.minutes || 0}</Typography>
          <Typography variant="caption" display="block">Projected: {(parseFloat(player.true_value) || 0).toFixed(2)}</Typography>
          <Typography variant="caption" display="block">PPG: {(parseFloat(player.ppg) || 0).toFixed(2)}</Typography>
          <Typography variant="caption" display="block">Form: {(parseFloat(player.form_multiplier) || 0).toFixed(2)}</Typography>
        </Box>
      }
      arrow
      placement="top"
    >
      <Paper
        elevation={isBench ? 2 : 3}
        sx={{
          width: isBench ? 70 : 80,
          textAlign: 'center',
          p: isBench ? 0.5 : 0.75,
          background: darkMode
            ? 'linear-gradient(145deg, #2c3e50 0%, #34495e 100%)'
            : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
          borderRadius: 1.5,
          opacity: isBench ? 0.85 : 1,
        }}
      >
        {/* Team */}
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            fontWeight: 600,
            color: darkMode ? '#8a9dc9' : '#5c6bc0',
            fontSize: '0.55rem',
          }}
        >
          {player.team}
        </Typography>

        {/* Player Name */}
        <Typography
          variant="body2"
          fontWeight={700}
          sx={{
            fontSize: isBench ? '0.65rem' : '0.7rem',
            lineHeight: 1.2,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {getDisplayName(player.name)}
        </Typography>

        {/* Price */}
        <Typography
          variant="caption"
          sx={{ display: 'block', fontSize: '0.5rem', color: 'text.secondary' }}
        >
          ${(parseFloat(player.price) || 0).toFixed(1)}
        </Typography>

        {/* Metric Value Chip */}
        <Chip
          label={getMetricValue()}
          size="small"
          sx={{
            mt: 0.25,
            height: 16,
            fontSize: '0.55rem',
            fontWeight: 700,
            backgroundColor: getMetricColor(),
            color: '#ffffff',
            '& .MuiChip-label': { px: 0.5 },
          }}
        />
      </Paper>
    </Tooltip>
  );
};

/**
 * InspirationPitchView - Read-only pitch view with bench
 */
const InspirationPitchView = ({ starters, bench, metric, darkMode }) => {
  // Group starters by position
  const groupByPosition = (players) => {
    const groups = { G: [], D: [], M: [], F: [] };
    players.forEach((player) => {
      const pos = player.position?.split(',')[0]?.trim() || 'M';
      if (groups[pos]) {
        groups[pos].push(player);
      } else {
        groups['M'].push(player);
      }
    });
    return groups;
  };

  const positionGroups = groupByPosition(starters);

  return (
    <Box>
      {/* Pitch */}
      <Paper
        elevation={3}
        sx={{
          borderRadius: 2,
          overflow: 'hidden',
          position: 'relative',
          minHeight: 380,
          background: darkMode
            ? 'linear-gradient(180deg, #1b4d2e 0%, #1e5631 50%, #1b4d2e 100%)'
            : 'linear-gradient(180deg, #2d8b4e 0%, #34a853 50%, #2d8b4e 100%)',
        }}
      >
        {/* Pitch Markings */}
        <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none' }}>
          {/* Center Circle */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 80,
              height: 80,
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: '50%',
            }}
          />
          {/* Center Line */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: 0,
              right: 0,
              height: 2,
              background: 'rgba(255,255,255,0.2)',
            }}
          />
        </Box>

        {/* Players */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            p: 2,
            minHeight: 380,
            position: 'relative',
            zIndex: 1,
          }}
        >
          {/* Forwards */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5 }}>
            {positionGroups.F.map((player) => (
              <InspirationPlayerCard
                key={player.id}
                player={player}
                metric={metric}
                darkMode={darkMode}
              />
            ))}
          </Box>

          {/* Midfielders */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5 }}>
            {positionGroups.M.map((player) => (
              <InspirationPlayerCard
                key={player.id}
                player={player}
                metric={metric}
                darkMode={darkMode}
              />
            ))}
          </Box>

          {/* Defenders */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5 }}>
            {positionGroups.D.map((player) => (
              <InspirationPlayerCard
                key={player.id}
                player={player}
                metric={metric}
                darkMode={darkMode}
              />
            ))}
          </Box>

          {/* Goalkeeper */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5 }}>
            {positionGroups.G.map((player) => (
              <InspirationPlayerCard
                key={player.id}
                player={player}
                metric={metric}
                darkMode={darkMode}
              />
            ))}
          </Box>
        </Box>

        {/* Formation Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            background: 'rgba(0,0,0,0.5)',
            borderRadius: 1,
            px: 1,
            py: 0.25,
          }}
        >
          <Typography variant="caption" sx={{ color: '#fff', fontWeight: 600, fontSize: '0.65rem' }}>
            3-4-3
          </Typography>
        </Box>
      </Paper>

      {/* Bench */}
      <Paper
        elevation={2}
        sx={{
          mt: 1.5,
          p: 1.5,
          borderRadius: 2,
          background: darkMode
            ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
            : 'linear-gradient(145deg, #f5f5f5 0%, #e8e8e8 100%)',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mb: 1,
            fontWeight: 600,
            color: 'text.secondary',
            fontSize: '0.65rem',
          }}
        >
          BENCH
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
          {bench.map((player) => (
            <InspirationPlayerCard
              key={player.id}
              player={player}
              metric={metric}
              darkMode={darkMode}
              isBench
            />
          ))}
        </Box>
      </Paper>
    </Box>
  );
};

/**
 * InspirationLineups - Main component showing top players by different metrics
 */
const InspirationLineups = ({ darkMode }) => {
  const [allPlayers, setAllPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('true_value');
  const [startersOnly, setStartersOnly] = useState(false); // Toggle for likely starters filter
  const [starters, setStarters] = useState([]);
  const [bench, setBench] = useState([]);

  // Fetch all players on mount
  useEffect(() => {
    const loadPlayers = async () => {
      setLoading(true);
      try {
        const data = await fetchPlayersData();
        if (data.success && data.players) {
          // Filter players with minimum 135 minutes
          const eligiblePlayers = data.players.filter(p => (p.minutes || 0) >= MIN_MINUTES);
          setAllPlayers(eligiblePlayers);
        }
      } catch (error) {
        console.error('Failed to load players:', error);
      } finally {
        setLoading(false);
      }
    };
    loadPlayers();
  }, []);

  // Build lineup when metric, players, or startersOnly filter change
  useEffect(() => {
    if (allPlayers.length === 0) return;

    // Filter players by starter multiplier if toggle is enabled
    const eligiblePlayers = startersOnly
      ? allPlayers.filter(p => (parseFloat(p.starter_multiplier) || 0) >= MIN_STARTER_MULTIPLIER)
      : allPlayers;

    // Sort players by selected metric
    const getSortValue = (player) => {
      switch (selectedMetric) {
        case 'form_multiplier':
          return parseFloat(player.form_multiplier) || 0;
        case 'xgi_multiplier':
          return parseFloat(player.xgi_multiplier) || 0;
        case 'ppg':
          return parseFloat(player.ppg) || 0;
        case 'pp90':
          const mins = parseFloat(player.minutes) || 0;
          const fpts = parseFloat(player.total_fpts) || 0;
          return mins > 0 ? (fpts / mins) * 90 : 0;
        case 'roi':
          return parseFloat(player.roi) || 0;
        case 'true_value':
        default:
          return parseFloat(player.true_value) || 0;
      }
    };

    // Group by position
    const byPosition = { G: [], D: [], M: [], F: [] };
    eligiblePlayers.forEach((player) => {
      const pos = player.position?.split(',')[0]?.trim() || 'M';
      if (byPosition[pos]) {
        byPosition[pos].push(player);
      }
    });

    // Sort each position group by metric
    Object.keys(byPosition).forEach((pos) => {
      byPosition[pos].sort((a, b) => getSortValue(b) - getSortValue(a));
    });

    // Pick starters for 3-4-3: 1 GK, 3 DEF, 4 MID, 3 FWD
    const starterGK = byPosition.G.slice(0, 1);
    const starterDEF = byPosition.D.slice(0, 3);
    const starterMID = byPosition.M.slice(0, 4);
    const starterFWD = byPosition.F.slice(0, 3);

    // Pick bench: 1 GK, 2 DEF, 2 MID, 2 FWD
    const benchGK = byPosition.G.slice(1, 2);
    const benchDEF = byPosition.D.slice(3, 5);
    const benchMID = byPosition.M.slice(4, 6);
    const benchFWD = byPosition.F.slice(3, 5);

    setStarters([...starterGK, ...starterDEF, ...starterMID, ...starterFWD]);
    setBench([...benchGK, ...benchDEF, ...benchMID, ...benchFWD]);
  }, [allPlayers, selectedMetric, startersOnly]);

  // Calculate total metric value for display
  const totalMetricValue = starters.reduce((sum, p) => {
    let val = 0;
    switch (selectedMetric) {
      case 'form_multiplier':
        val = parseFloat(p.form_multiplier) || 0;
        break;
      case 'xgi_multiplier':
        val = parseFloat(p.xgi_multiplier) || 0;
        break;
      case 'ppg':
        val = parseFloat(p.ppg) || 0;
        break;
      case 'pp90':
        const mins = parseFloat(p.minutes) || 0;
        const fpts = parseFloat(p.total_fpts) || 0;
        val = mins > 0 ? (fpts / mins) * 90 : 0;
        break;
      case 'roi':
        val = parseFloat(p.roi) || 0;
        break;
      case 'true_value':
      default:
        val = parseFloat(p.true_value) || 0;
        break;
    }
    return sum + val;
  }, 0);

  const totalPrice = starters.reduce((sum, p) => sum + (parseFloat(p.price) || 0), 0);

  const metricOption = METRIC_OPTIONS.find(o => o.value === selectedMetric);

  return (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        mt: 3,
        borderRadius: 3,
        background: darkMode
          ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
          : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Lightbulb sx={{ color: '#ffc107' }} />
        <Typography variant="h6" fontWeight={700}>
          Inspiration Lineups
        </Typography>
        <Typography variant="caption" color="text.secondary">
          (Min. {MIN_MINUTES} mins played)
        </Typography>

        {/* Metric Selector */}
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <Select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            sx={{
              '& .MuiSelect-select': {
                py: 1,
                display: 'flex',
                alignItems: 'center',
              },
            }}
          >
            {METRIC_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: option.color,
                    }}
                  />
                  {option.label}
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Likely Starters Toggle */}
        <FormControlLabel
          control={
            <Switch
              checked={startersOnly}
              onChange={(e) => setStartersOnly(e.target.checked)}
              size="small"
              sx={{
                '& .MuiSwitch-switchBase.Mui-checked': {
                  color: '#4caf50',
                },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                  backgroundColor: '#4caf50',
                },
              }}
            />
          }
          label={
            <Typography variant="caption" color="text.secondary">
              Likely starters only
            </Typography>
          }
        />
      </Box>

      {/* Content */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : starters.length === 0 ? (
        <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
          No players found with minimum {MIN_MINUTES} minutes played
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {/* Pitch View */}
          <Grid item xs={12} lg={8}>
            <InspirationPitchView
              starters={starters}
              bench={bench}
              metric={selectedMetric}
              darkMode={darkMode}
            />
          </Grid>

          {/* Stats Panel */}
          <Grid item xs={12} lg={4}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                borderRadius: 2,
                background: darkMode
                  ? 'linear-gradient(145deg, #252847 0%, #2d3055 100%)'
                  : 'linear-gradient(145deg, #f8f9fa 0%, #ffffff 100%)',
              }}
            >
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Team Summary
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Total {metricOption?.label}:
                  </Typography>
                  <Chip
                    label={totalMetricValue.toFixed(1)}
                    size="small"
                    sx={{
                      backgroundColor: metricOption?.color,
                      color: 'white',
                      fontWeight: 700,
                    }}
                  />
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Team Cost:
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    ${totalPrice.toFixed(1)}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Formation:
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    3-4-3
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Starters:
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {starters.length}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Bench:
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {bench.length}
                  </Typography>
                </Box>
              </Box>

              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 2, fontStyle: 'italic' }}
              >
                Top players by {metricOption?.label.toLowerCase()} with 135+ minutes
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Paper>
  );
};

export default InspirationLineups;
