import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Typography,
  Box,
  Chip,
  CircularProgress,
  IconButton,
  InputAdornment,
} from '@mui/material';
import { Search, Close, SwapHoriz } from '@mui/icons-material';
import { searchPlayersForReplacement } from '../services/api';

/**
 * PlayerSearchDialog - Dialog for searching and selecting a replacement player
 */
const PlayerSearchDialog = ({
  open,
  onClose,
  onSelect,
  currentPlayer,
  darkMode,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // Debounced search
  const performSearch = useCallback(async (term) => {
    if (term.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const position = currentPlayer?.position?.split(',')[0]?.trim() || null;
      const data = await searchPlayersForReplacement(term, position);
      if (data.success) {
        // Filter out the current player from results
        const filtered = data.players.filter(
          (p) => p.id !== currentPlayer?.player_id
        );
        setResults(filtered.slice(0, 15)); // Limit to 15 results
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPlayer]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      performSearch(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm, performSearch]);

  // Reset on close
  useEffect(() => {
    if (!open) {
      setSearchTerm('');
      setResults([]);
    }
  }, [open]);

  const handleSelect = (player) => {
    onSelect(player);
    onClose();
  };

  const getTrueValueColor = (tv) => {
    if (!tv || tv <= 0) return '#9e9e9e';
    if (tv >= 20) return '#00cc66';
    if (tv >= 15) return '#28a745';
    if (tv >= 10) return '#a4c639';
    if (tv >= 5) return '#ffc107';
    return '#dc3545';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          background: darkMode
            ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
            : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
          borderRadius: 3,
        },
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SwapHoriz sx={{ color: '#667eea' }} />
            <Typography variant="h6">Replace Player</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
        {currentPlayer && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Replacing: <strong>{currentPlayer.name}</strong> ({currentPlayer.team})
          </Typography>
        )}
      </DialogTitle>

      <DialogContent>
        {/* Search Input */}
        <TextField
          fullWidth
          placeholder="Search for a player..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          autoFocus
          sx={{ mb: 2 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search color="action" />
              </InputAdornment>
            ),
            endAdornment: loading && (
              <InputAdornment position="end">
                <CircularProgress size={20} />
              </InputAdornment>
            ),
          }}
        />

        {/* Results List */}
        {searchTerm.length < 2 ? (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
            Type at least 2 characters to search
          </Typography>
        ) : results.length === 0 && !loading ? (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
            No players found
          </Typography>
        ) : (
          <List sx={{ maxHeight: 350, overflow: 'auto' }}>
            {results.map((player) => (
              <ListItem
                key={player.id}
                button
                onClick={() => handleSelect(player)}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  '&:hover': {
                    background: darkMode ? 'rgba(102, 126, 234, 0.1)' : 'rgba(102, 126, 234, 0.05)',
                  },
                }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1" fontWeight={600}>
                        {player.name}
                      </Typography>
                      <Chip
                        label={player.team}
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.65rem',
                          bgcolor: darkMode ? '#3d4466' : '#e3e8f0',
                        }}
                      />
                      <Chip
                        label={player.position}
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.65rem',
                          bgcolor: '#667eea',
                          color: 'white',
                        }}
                      />
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      Price: ${parseFloat(player.price || 0).toFixed(2)}
                    </Typography>
                  }
                />
                <ListItemSecondaryAction>
                  <Chip
                    label={`TV: ${parseFloat(player.true_value || 0).toFixed(1)}`}
                    size="small"
                    sx={{
                      fontWeight: 700,
                      backgroundColor: getTrueValueColor(parseFloat(player.true_value || 0)),
                      color: '#ffffff',
                    }}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default PlayerSearchDialog;
