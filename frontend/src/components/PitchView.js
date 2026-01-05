import React from 'react';
import { Box, Paper, Typography, IconButton, Chip, Tooltip } from '@mui/material';
import { Lock, LockOpen, SwapHoriz } from '@mui/icons-material';

/**
 * PlayerCard - Individual player display on the pitch
 * @param {boolean} isNewPlayer - True if this player is NOT in the original CSV roster (a suggested swap)
 */
const PlayerCard = ({ player, isLocked, onToggleLock, onReplace, darkMode, isNewPlayer }) => {
  const priceDiff = (player.current_price || 0) - (player.purchase_price || 0);
  const priceColor = priceDiff > 0 ? '#4caf50' : priceDiff < 0 ? '#f44336' : '#9e9e9e';

  // Get display name (last name or shortened)
  const getDisplayName = (name) => {
    if (!name) return 'Unknown';
    const parts = name.split(' ');
    if (parts.length > 1) {
      return parts[parts.length - 1]; // Last name
    }
    return name.length > 10 ? name.substring(0, 9) + '.' : name;
  };

  // Get Projected Points color
  const getTrueValueColor = (tv) => {
    if (!tv || tv <= 0) return '#9e9e9e';
    if (tv >= 20) return '#00cc66';
    if (tv >= 15) return '#28a745';
    if (tv >= 10) return '#a4c639';
    if (tv >= 5) return '#ffc107';
    return '#dc3545';
  };

  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="body2" fontWeight={600}>{player.name}</Typography>
          <Typography variant="caption" display="block">Team: {player.team}</Typography>
          <Typography variant="caption" display="block">Position: {player.position}</Typography>
          <Typography variant="caption" display="block">
            Purchase: ${player.purchase_price?.toFixed(2) || '0.00'}
          </Typography>
          <Typography variant="caption" display="block">
            Current: ${player.current_price?.toFixed(2) || '0.00'}
          </Typography>
          <Typography variant="caption" display="block">
            Projected: {player.true_value?.toFixed(2) || '0.00'}
          </Typography>
          <Typography variant="caption" display="block">
            ROI: {player.roi?.toFixed(2) || '0.00'}
          </Typography>
          {player.next_opponent && (
            <Typography variant="caption" display="block">
              Next: {player.is_home ? 'vs' : '@'} {player.next_opponent}
            </Typography>
          )}
        </Box>
      }
      arrow
      placement="top"
    >
      <Paper
        elevation={isLocked ? 6 : isNewPlayer ? 5 : 3}
        sx={{
          width: 90,
          textAlign: 'center',
          p: 1,
          cursor: 'pointer',
          transition: 'all 0.2s',
          background: isLocked
            ? darkMode
              ? 'linear-gradient(145deg, #4a4a1a 0%, #3d3d0f 100%)'
              : 'linear-gradient(145deg, #fff8e1 0%, #ffecb3 100%)'
            : isNewPlayer
            ? darkMode
              ? 'linear-gradient(145deg, #1a3a4a 0%, #0f3d3d 100%)'  // Teal/cyan for new players (dark)
              : 'linear-gradient(145deg, #e0f7fa 0%, #b2ebf2 100%)'  // Light cyan for new players (light)
            : darkMode
            ? 'linear-gradient(145deg, #2c3e50 0%, #34495e 100%)'
            : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
          border: isLocked
            ? '2px solid #ffd700'
            : isNewPlayer
            ? '2px solid #00bcd4'  // Cyan border for new players
            : '1px solid transparent',
          borderRadius: 2,
          '&:hover': {
            transform: 'translateY(-3px)',
            boxShadow: 6,
          },
        }}
      >
        {/* Replace Icon - Top Left */}
        <Box sx={{ position: 'absolute', top: 2, left: 2 }}>
          <Tooltip title="Replace player" arrow placement="top">
            <IconButton
              size="small"
              sx={{ p: 0.25 }}
              onClick={(e) => {
                e.stopPropagation();
                onReplace(player);
              }}
            >
              <SwapHoriz sx={{ fontSize: 14, color: '#667eea' }} />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Lock Icon - Top Right */}
        <Box sx={{ position: 'absolute', top: 2, right: 2 }}>
          <Tooltip title={isLocked ? 'Unlock' : 'Lock'} arrow placement="top">
            <IconButton
              size="small"
              sx={{ p: 0.25 }}
              onClick={(e) => {
                e.stopPropagation();
                onToggleLock(player.player_id);
              }}
            >
              {isLocked ? (
                <Lock sx={{ fontSize: 14, color: '#ffd700' }} />
              ) : (
                <LockOpen sx={{ fontSize: 14, color: 'text.secondary' }} />
              )}
            </IconButton>
          </Tooltip>
        </Box>

        {/* Team Badge */}
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            fontWeight: 600,
            color: darkMode ? '#8a9dc9' : '#5c6bc0',
            fontSize: '0.65rem',
          }}
        >
          {player.team}
        </Typography>

        {/* Player Name */}
        <Typography
          variant="body2"
          fontWeight={700}
          sx={{
            fontSize: '0.75rem',
            lineHeight: 1.2,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {getDisplayName(player.name)}
        </Typography>

        {/* Price Info */}
        <Typography
          variant="caption"
          sx={{ display: 'block', fontSize: '0.6rem', color: 'text.secondary' }}
        >
          ${player.purchase_price?.toFixed(1)} → ${player.current_price?.toFixed(1)}
        </Typography>

        {/* Price Change */}
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            fontSize: '0.6rem',
            color: priceColor,
            fontWeight: 600,
          }}
        >
          ({priceDiff > 0 ? '+' : ''}{priceDiff.toFixed(1)})
        </Typography>

        {/* Projected Points Chip */}
        <Chip
          label={`Proj: ${player.true_value?.toFixed(1) || '0.0'}`}
          size="small"
          sx={{
            mt: 0.5,
            height: 18,
            fontSize: '0.6rem',
            fontWeight: 700,
            backgroundColor: getTrueValueColor(player.true_value),
            color: '#ffffff',
            '& .MuiChip-label': { px: 0.75 },
          }}
        />
      </Paper>
    </Tooltip>
  );
};

/**
 * PlayerRow - A row of players (for each position group)
 */
const PlayerRow = ({ players, lockedPlayers, onToggleLock, onReplace, darkMode, label, originalRosterIds }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        gap: 2,
        flexWrap: 'wrap',
        position: 'relative',
      }}
    >
      {/* Position Label */}
      {label && (
        <Typography
          variant="caption"
          sx={{
            position: 'absolute',
            left: 10,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'rgba(255,255,255,0.5)',
            fontWeight: 600,
            fontSize: '0.7rem',
          }}
        >
          {label}
        </Typography>
      )}

      {/* Players */}
      {players.map((player) => (
        <PlayerCard
          key={player.player_id}
          player={player}
          isLocked={lockedPlayers.has(player.player_id)}
          onToggleLock={onToggleLock}
          onReplace={onReplace}
          darkMode={darkMode}
          isNewPlayer={originalRosterIds && originalRosterIds.size > 0 && !originalRosterIds.has(player.player_id)}
        />
      ))}
    </Box>
  );
};

/**
 * PitchView - Football pitch visualization of the lineup
 * @param {Set} originalRosterIds - Set of player IDs from the original CSV import (for highlighting new players)
 */
const PitchView = ({ players, lockedPlayers, onToggleLock, onReplace, darkMode, originalRosterIds }) => {

  // Group players by position (use selected_position from ILP if available)
  const groupByPosition = (players) => {
    const groups = {
      G: [],
      D: [],
      M: [],
      F: [],
    };

    players.forEach((player) => {
      // Use selected_position from optimizer if available, otherwise fall back to first position
      const pos = player.selected_position || player.position?.split(',')[0]?.trim() || 'M';
      if (groups[pos]) {
        groups[pos].push(player);
      } else {
        groups['M'].push(player); // Default to midfielder
      }
    });

    return groups;
  };

  const positionGroups = groupByPosition(players);

  return (
    <Paper
      elevation={4}
      sx={{
        borderRadius: 3,
        overflow: 'hidden',
        position: 'relative',
        minHeight: 600,
        background: darkMode
          ? 'linear-gradient(180deg, #1b4d2e 0%, #1e5631 25%, #1b4d2e 50%, #1e5631 75%, #1b4d2e 100%)'
          : 'linear-gradient(180deg, #2d8b4e 0%, #34a853 25%, #2d8b4e 50%, #34a853 75%, #2d8b4e 100%)',
      }}
    >
      {/* Pitch Markings */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
        }}
      >
        {/* Center Circle */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 120,
            height: 120,
            border: '2px solid rgba(255,255,255,0.3)',
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
            background: 'rgba(255,255,255,0.3)',
          }}
        />
        {/* Top Penalty Box */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: '50%',
            transform: 'translateX(-50%)',
            width: '40%',
            height: 80,
            border: '2px solid rgba(255,255,255,0.3)',
            borderTop: 'none',
          }}
        />
        {/* Bottom Penalty Box */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: '50%',
            transform: 'translateX(-50%)',
            width: '40%',
            height: 80,
            border: '2px solid rgba(255,255,255,0.3)',
            borderBottom: 'none',
          }}
        />
      </Box>

      {/* Players by Position */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          p: 3,
          minHeight: 600,
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Forwards (top) */}
        <PlayerRow
          players={positionGroups.F}
          lockedPlayers={lockedPlayers}
          onToggleLock={onToggleLock}
          onReplace={onReplace}
          darkMode={darkMode}
          label="FWD"
          originalRosterIds={originalRosterIds}
        />

        {/* Midfielders */}
        <PlayerRow
          players={positionGroups.M}
          lockedPlayers={lockedPlayers}
          onToggleLock={onToggleLock}
          onReplace={onReplace}
          darkMode={darkMode}
          label="MID"
          originalRosterIds={originalRosterIds}
        />

        {/* Defenders */}
        <PlayerRow
          players={positionGroups.D}
          lockedPlayers={lockedPlayers}
          onToggleLock={onToggleLock}
          onReplace={onReplace}
          darkMode={darkMode}
          label="DEF"
          originalRosterIds={originalRosterIds}
        />

        {/* Goalkeeper (bottom) */}
        <PlayerRow
          players={positionGroups.G}
          lockedPlayers={lockedPlayers}
          onToggleLock={onToggleLock}
          onReplace={onReplace}
          darkMode={darkMode}
          label="GK"
          originalRosterIds={originalRosterIds}
        />
      </Box>

      {/* Formation Badge */}
      {players.length === 11 && (
        <Box
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: 'rgba(0,0,0,0.5)',
            borderRadius: 2,
            px: 1.5,
            py: 0.5,
          }}
        >
          <Typography variant="caption" sx={{ color: '#fff', fontWeight: 600 }}>
            {positionGroups.D.length}-{positionGroups.M.length}-{positionGroups.F.length}
          </Typography>
        </Box>
      )}

      {/* Player Count */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 10,
          right: 10,
          background: 'rgba(0,0,0,0.5)',
          borderRadius: 2,
          px: 1.5,
          py: 0.5,
        }}
      >
        <Typography variant="caption" sx={{ color: '#fff' }}>
          {players.length} players
        </Typography>
      </Box>
    </Paper>
  );
};

export default PitchView;
