import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Upload,
  AutoAwesome,
  Lock,
  TrendingUp,
  AttachMoney,
  OpenInNew,
  Replay,
  HelpOutline,
} from '@mui/icons-material';
import PitchView from './PitchView';
import PlayerSearchDialog from './PlayerSearchDialog';
import InspirationLineups from './InspirationLineups';
import { importLineupRoster, optimizeLineup } from '../services/api';

const LineupOptimizer = ({ darkMode }) => {
  const fileInputRef = useRef(null);

  // State
  const [roster, setRoster] = useState([]);
  const [originalRoster, setOriginalRoster] = useState([]); // Store CSV roster with purchase prices
  const [lockedPlayers, setLockedPlayers] = useState(new Set());
  const [alternatives, setAlternatives] = useState([]);
  const [selectedAlternative, setSelectedAlternative] = useState(null);
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState(null);
  const [totals, setTotals] = useState({
    purchase_price: 0,
    current_price: 0,
    true_value: 0,
    price_change: 0,
  });

  // Replacement dialog state
  const [replaceDialogOpen, setReplaceDialogOpen] = useState(false);
  const [playerToReplace, setPlayerToReplace] = useState(null);

  const BUDGET = 100;

  // Handle CSV file import
  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const result = await importLineupRoster(file);

      if (result.success) {
        setRoster(result.roster);
        setOriginalRoster(result.roster); // Store original CSV roster with purchase prices
        setTotals(result.totals);
        setLockedPlayers(new Set()); // Reset locks on new import
        setAlternatives([]); // Clear previous alternatives
        setSelectedAlternative(null);
      } else {
        setError(result.error || 'Import failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      event.target.value = ''; // Reset file input
    }
  };

  // Handle player lock toggle
  const handleToggleLock = (playerId) => {
    setLockedPlayers((prev) => {
      const newLocks = new Set(prev);
      if (newLocks.has(playerId)) {
        newLocks.delete(playerId);
      } else {
        newLocks.add(playerId);
      }
      return newLocks;
    });
  };

  // Lock all players where purchase price < current price (discounted buys)
  const handleLockDiscounted = () => {
    const discountedPlayerIds = roster
      .filter((p) => {
        const purchasePrice = parseFloat(p.purchase_price || 0);
        const currentPrice = parseFloat(p.current_price || 0);
        return purchasePrice < currentPrice;
      })
      .map((p) => p.player_id);

    setLockedPlayers((prev) => {
      const newLocks = new Set(prev);
      discountedPlayerIds.forEach((id) => newLocks.add(id));
      return newLocks;
    });
  };

  // Count discounted players for button label
  const discountedCount = roster.filter((p) => {
    const purchasePrice = parseFloat(p.purchase_price || 0);
    const currentPrice = parseFloat(p.current_price || 0);
    return purchasePrice < currentPrice;
  }).length;

  // Handle player replacement dialog
  const handleOpenReplace = (player) => {
    setPlayerToReplace(player);
    setReplaceDialogOpen(true);
  };

  // Handle replacement selection
  const handleReplacePlayer = (newPlayer) => {
    if (!playerToReplace) return;

    // Create the replacement player object with proper structure
    const playerPrice = parseFloat(newPlayer.price || 0);
    const playerTV = parseFloat(newPlayer.true_value || 0);
    const replacementPlayer = {
      player_id: newPlayer.id,
      name: newPlayer.name,
      team: newPlayer.team,
      position: newPlayer.position,
      purchase_price: playerPrice, // Use current price as purchase price
      current_price: playerPrice,
      true_value: playerTV,
      roi: parseFloat(newPlayer.roi || 0),
      is_home: newPlayer.is_home,
      next_opponent: newPlayer.next_opponent,
      is_manual_addition: true, // Mark as manually added
    };

    // Replace in roster - use String comparison to handle type mismatches
    const targetPlayerId = String(playerToReplace.player_id);
    setRoster((prev) => {
      const newRoster = prev.map((p) =>
        String(p.player_id) === targetPlayerId ? replacementPlayer : p
      );
      return newRoster;
    });

    // Lock the new player automatically
    setLockedPlayers((prev) => {
      const newLocks = new Set(prev);
      // Remove old player lock - check both string and original format
      newLocks.delete(playerToReplace.player_id);
      newLocks.delete(String(playerToReplace.player_id));
      newLocks.add(newPlayer.id); // Lock new player
      return newLocks;
    });

    // Recalculate totals
    setTotals((prev) => {
      const oldPrice = parseFloat(playerToReplace.purchase_price || 0);
      const oldCurrentPrice = parseFloat(playerToReplace.current_price || 0);
      const oldTV = parseFloat(playerToReplace.true_value || 0);

      return {
        ...prev,
        purchase_price: prev.purchase_price - oldPrice + playerPrice,
        current_price: prev.current_price - oldCurrentPrice + playerPrice,
        true_value: prev.true_value - oldTV + playerTV,
      };
    });

    // Clear alternatives since roster changed
    setAlternatives([]);
    setSelectedAlternative(null);

    setReplaceDialogOpen(false);
    setPlayerToReplace(null);
  };

  // Handle optimization
  const handleOptimize = async () => {
    setOptimizing(true);
    setError(null);

    try {
      // Build locked players data with their purchase prices
      const lockedPlayersData = roster
        .filter(p => lockedPlayers.has(p.player_id))
        .map(p => ({
          player_id: p.player_id,
          purchase_price: p.purchase_price
        }));

      // Send FULL roster with purchase prices so optimizer knows your discounts
      // This way, even unlocked CSV players use their purchase price (not market price)
      const rosterPlayersData = roster.map(p => ({
        player_id: p.player_id,
        purchase_price: parseFloat(p.purchase_price || 0)
      }));

      const result = await optimizeLineup(
        Array.from(lockedPlayers),
        BUDGET,
        lockedPlayersData,
        rosterPlayersData  // New: full roster with purchase prices
      );

      if (result.success) {
        setAlternatives(result.alternatives);
        setSelectedAlternative(null);
      } else {
        setError(result.error || 'Optimization failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setOptimizing(false);
    }
  };

  // Apply selected alternative to view
  const handleSelectAlternative = (alt, index) => {
    setSelectedAlternative(index);

    // Backend now sends purchase_price with each player
    // - CSV players: their discounted purchase price
    // - New players: current market price
    setRoster(alt.lineup);

    // Calculate values from the lineup
    const budgetSpent = alt.lineup.reduce((sum, player) => {
      return sum + parseFloat(player.purchase_price || player.current_price || 0);
    }, 0);

    const marketValue = alt.lineup.reduce((sum, player) => {
      return sum + parseFloat(player.current_price || 0);
    }, 0);

    setTotals({
      purchase_price: budgetSpent,        // What you actually pay (CSV discounts applied)
      current_price: marketValue,          // Current market value of the team
      true_value: alt.total_true_value,
      price_change: marketValue - budgetSpent,  // Profit from your discounts
    });
  };

  // Reset to original imported lineup
  const handleResetToOriginal = () => {
    setRoster(originalRoster);
    setSelectedAlternative(null);

    // Recalculate totals from original roster
    const budgetSpent = originalRoster.reduce((sum, p) => sum + parseFloat(p.purchase_price || 0), 0);
    const marketValue = originalRoster.reduce((sum, p) => sum + parseFloat(p.current_price || 0), 0);
    const totalTV = originalRoster.reduce((sum, p) => sum + parseFloat(p.true_value || 0), 0);

    setTotals({
      purchase_price: budgetSpent,
      current_price: marketValue,
      true_value: totalTV,
      price_change: marketValue - budgetSpent,
    });
  };

  // Create a set of original roster player IDs for highlighting new players
  const originalRosterIds = new Set(originalRoster.map(p => p.player_id));

  // Calculate budget usage - use PURCHASE price (what you actually spent)
  const budgetUsed = totals.purchase_price || 0;
  const budgetRemaining = BUDGET - budgetUsed;
  const budgetPercentage = (budgetUsed / BUDGET) * 100;

  return (
    <Box>
      {/* Header */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          mb: 3,
          borderRadius: 3,
          background: darkMode
            ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
            : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h5" fontWeight={700}>
            Lineup Optimizer
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".csv"
              onChange={handleFileSelect}
            />
            <Button
              variant="outlined"
              startIcon={loading ? <CircularProgress size={20} /> : <Upload />}
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              Import Team Roster CSV
            </Button>
            {/* Reset button - shows when viewing a generated lineup */}
            {alternatives.length > 0 && selectedAlternative !== null && (
              <Button
                variant="outlined"
                startIcon={<Replay />}
                onClick={handleResetToOriginal}
                color="secondary"
              >
                Reset to Original
              </Button>
            )}
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Budget Bar */}
        {roster.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Budget Used: ${budgetUsed.toFixed(1)} / ${BUDGET}
              </Typography>
              <Typography
                variant="body2"
                sx={{ color: budgetRemaining >= 0 ? '#4caf50' : '#f44336' }}
              >
                Remaining: ${budgetRemaining.toFixed(1)}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={Math.min(budgetPercentage, 100)}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: darkMode ? '#2a2d4a' : '#e0e0e0',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  background:
                    budgetPercentage > 100
                      ? '#f44336'
                      : budgetPercentage > 90
                      ? '#ff9800'
                      : 'linear-gradient(45deg, #667eea, #764ba2)',
                },
              }}
            />
          </Box>
        )}
      </Paper>

      {/* Main Content */}
      {roster.length === 0 ? (
        <Paper
          elevation={3}
          sx={{
            p: 6,
            textAlign: 'center',
            borderRadius: 3,
            background: darkMode
              ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
              : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
          }}
        >
          <Upload sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Import Your Team Roster
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Export your team roster CSV from Fantrax and import it here to start optimizing.
          </Typography>

          <Divider sx={{ my: 3 }} />

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            <strong>Instructions:</strong>
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              href="https://www.fantrax.com/fantasy/league/gjbogdx2mcmcvzqa/team/roster"
              target="_blank"
              rel="noopener noreferrer"
              endIcon={<OpenInNew />}
              sx={{ mb: 1 }}
            >
              Open Fantrax Roster
            </Button>
            <Typography variant="body2" color="text.secondary">
              1. Choose "Current Period" from the dropdown
            </Typography>
            <Typography variant="body2" color="text.secondary">
              2. Click "Download all as CSV"
            </Typography>
            <Typography variant="body2" color="text.secondary">
              3. Import the downloaded file using the button above
            </Typography>
          </Box>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {/* Pitch View */}
          <Grid item xs={12} lg={8}>
            <PitchView
              players={roster}
              lockedPlayers={lockedPlayers}
              onToggleLock={handleToggleLock}
              onReplace={handleOpenReplace}
              darkMode={darkMode}
              originalRosterIds={originalRosterIds}
            />
          </Grid>

          {/* Control Panel */}
          <Grid item xs={12} lg={4}>
            {/* Stats Summary */}
            <Paper
              elevation={3}
              sx={{
                p: 3,
                mb: 3,
                borderRadius: 3,
                background: darkMode
                  ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
                  : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
              }}
            >
              <Typography variant="h6" gutterBottom>
                Team Stats
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <TrendingUp sx={{ color: '#4caf50', fontSize: 28 }} />
                    <Typography variant="h5" fontWeight={700}>
                      {totals.true_value?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total Projected
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <AttachMoney sx={{ color: '#667eea', fontSize: 28 }} />
                    <Typography variant="h5" fontWeight={700}>
                      ${totals.purchase_price?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Budget Spent
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <AttachMoney sx={{ color: '#2196f3', fontSize: 28 }} />
                    <Typography variant="h5" fontWeight={700}>
                      ${totals.current_price?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Market Value
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <Typography
                      variant="h5"
                      fontWeight={700}
                      sx={{
                        color:
                          totals.price_change > 0
                            ? '#4caf50'
                            : totals.price_change < 0
                            ? '#f44336'
                            : 'text.primary',
                      }}
                    >
                      {totals.price_change > 0 ? '+' : ''}
                      ${totals.price_change?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Value Gain
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <Lock sx={{ color: '#ff9800', fontSize: 28 }} />
                    <Typography variant="h5" fontWeight={700}>
                      {lockedPlayers.size}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Locked Players
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* Lock Discounted Button */}
              {discountedCount > 0 && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Lock />}
                  onClick={handleLockDiscounted}
                  fullWidth
                  sx={{
                    mt: 2,
                    borderColor: '#4caf50',
                    color: '#4caf50',
                    '&:hover': {
                      borderColor: '#388e3c',
                      backgroundColor: 'rgba(76, 175, 80, 0.08)',
                    },
                  }}
                >
                  Lock Discounted ({discountedCount})
                </Button>
              )}

              {/* Generate Lineups Button */}
              <Button
                variant="contained"
                size="large"
                startIcon={optimizing ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
                onClick={handleOptimize}
                disabled={roster.length === 0 || optimizing}
                fullWidth
                sx={{
                  mt: 2,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 700,
                  background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #5a6fd6 0%, #6a4190 100%)',
                  },
                  boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
                }}
              >
                GENERATE LINEUPS
              </Button>
            </Paper>

            {/* Alternative Lineups - Grouped by Formation */}
            {alternatives.length > 0 && (
              <Paper
                elevation={3}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  background: darkMode
                    ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
                    : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
                }}
              >
                <Typography variant="h6" gutterBottom>
                  Optimized Lineups
                </Typography>

                {/* Side by side formations */}
                <Grid container spacing={2}>
                  {['3-5-2', '3-4-3'].map((formation) => {
                    const formationAlts = alternatives.filter(a => a.formation === formation);
                    if (formationAlts.length === 0) return null;

                    const optimalAlts = formationAlts.filter(a => a.type === 'optimal' || !a.type);
                    const differentialAlts = formationAlts.filter(a => a.type === 'differential');

                    return (
                      <Grid item xs={6} key={formation}>
                        <Typography
                          variant="subtitle2"
                          sx={{
                            mb: 1,
                            color: formation === '3-5-2' ? '#667eea' : '#764ba2',
                            fontWeight: 700,
                            fontSize: '0.75rem'
                          }}
                        >
                          {formation}
                        </Typography>

                        {/* Optimal Lineups */}
                        {optimalAlts.length > 0 && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="caption" sx={{ color: '#4caf50', fontWeight: 600, fontSize: '0.65rem', display: 'block' }}>
                              Optimal
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.3 }}>
                              {optimalAlts.map((alt, idx) => {
                                const globalIndex = alternatives.indexOf(alt);
                                return (
                                  <Card
                                    key={globalIndex}
                                    onClick={() => handleSelectAlternative(alt, globalIndex)}
                                    sx={{
                                      cursor: 'pointer',
                                      transition: 'all 0.2s',
                                      border: selectedAlternative === globalIndex
                                        ? '2px solid #4caf50'
                                        : '1px solid transparent',
                                      '&:hover': { transform: 'translateY(-1px)', boxShadow: 2 },
                                      background: darkMode ? '#252847' : '#f8f9fa',
                                    }}
                                  >
                                    <CardContent sx={{ py: 0.5, px: 1, '&:last-child': { pb: 0.5 } }}>
                                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.7rem' }}>
                                          #{idx + 1}
                                        </Typography>
                                        <Chip
                                          label={alt.total_true_value.toFixed(1)}
                                          size="small"
                                          color="success"
                                          sx={{ height: 16, fontSize: '0.6rem', '& .MuiChip-label': { px: 0.5 } }}
                                        />
                                      </Box>
                                    </CardContent>
                                  </Card>
                                );
                              })}
                            </Box>
                          </Box>
                        )}

                        {/* Differential Lineups */}
                        {differentialAlts.length > 0 && (
                          <Box>
                            <Typography variant="caption" sx={{ color: '#ff9800', fontWeight: 600, fontSize: '0.65rem', display: 'block' }}>
                              Differential
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.3 }}>
                              {differentialAlts.map((alt, idx) => {
                                const globalIndex = alternatives.indexOf(alt);
                                return (
                                  <Card
                                    key={globalIndex}
                                    onClick={() => handleSelectAlternative(alt, globalIndex)}
                                    sx={{
                                      cursor: 'pointer',
                                      transition: 'all 0.2s',
                                      border: selectedAlternative === globalIndex
                                        ? '2px solid #ff9800'
                                        : '1px solid transparent',
                                      '&:hover': { transform: 'translateY(-1px)', boxShadow: 2 },
                                      background: darkMode ? '#2d2847' : '#fff8e1',
                                    }}
                                  >
                                    <CardContent sx={{ py: 0.5, px: 1, '&:last-child': { pb: 0.5 } }}>
                                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.7rem' }}>
                                          D{idx + 1}
                                        </Typography>
                                        <Chip
                                          label={alt.total_true_value.toFixed(1)}
                                          size="small"
                                          sx={{ height: 16, fontSize: '0.6rem', bgcolor: '#ff9800', color: 'white', '& .MuiChip-label': { px: 0.5 } }}
                                        />
                                      </Box>
                                    </CardContent>
                                  </Card>
                                );
                              })}
                            </Box>
                          </Box>
                        )}
                      </Grid>
                    );
                  })}
                </Grid>

                <Divider sx={{ my: 2 }} />

                <Typography variant="body2" color="text.secondary">
                  <Lock sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                  {lockedPlayers.size} players locked. Click players to lock or replace.
                </Typography>
              </Paper>
            )}

            {/* Help Section */}
            <Paper
              elevation={2}
              sx={{
                p: 2,
                mt: 2,
                borderRadius: 3,
                background: darkMode
                  ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
                  : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <HelpOutline sx={{ fontSize: 18, color: 'text.secondary' }} />
                <Typography variant="subtitle2" fontWeight={600}>
                  How to Use
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Box>
                  <Typography variant="caption" fontWeight={600} color="primary">
                    Lock Players
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Click the lock icon on any player to keep them in your lineup. Locked players won't be replaced during optimization.
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" fontWeight={600} color="primary">
                    Lock Discounted
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    One-click locks all players you bought below current market price - protecting your value picks.
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" fontWeight={600} color="primary">
                    Replace Players
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Click the swap icon to manually search and replace any player with another from the database.
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" fontWeight={600} color="primary">
                    Optimal vs Differential
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Optimal lineups maximize projected points. Differential lineups exclude top performers to find under-the-radar picks.
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" fontWeight={600} color="primary">
                    Exclude Players
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    In the Players table, click the checkbox to the left of a player's name to exclude them from optimization. Use "Reset Exclusions" to clear all.
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" fontWeight={600} sx={{ color: '#00bcd4' }}>
                    Cyan Border = New Player
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Players with a cyan border are suggestions not in your current roster.
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Inspiration Lineups - Only visible after roster import */}
      {roster.length > 0 && <InspirationLineups darkMode={darkMode} />}

      {/* Player Replacement Dialog */}
      <PlayerSearchDialog
        open={replaceDialogOpen}
        onClose={() => {
          setReplaceDialogOpen(false);
          setPlayerToReplace(null);
        }}
        onSelect={handleReplacePlayer}
        currentPlayer={playerToReplace}
        darkMode={darkMode}
      />
    </Box>
  );
};

export default LineupOptimizer;
