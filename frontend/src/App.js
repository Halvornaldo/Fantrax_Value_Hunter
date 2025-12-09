import React, { useState, useEffect, useRef } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, IconButton, Toolbar, AppBar, Button, Menu, MenuItem, Divider } from '@mui/material';
import { Brightness4, Brightness7, Upload, CloudSync, Archive, SportsEsports, Sports, FileUpload } from '@mui/icons-material';
import Banner from './components/Banner';
import Dashboard from './components/Dashboard';
import './App.css';

const App = () => {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved !== null ? JSON.parse(saved) : true;
  });

  const [uploadMenuAnchor, setUploadMenuAnchor] = useState(null);

  // Refs for hidden file inputs
  const npxgCsvInputRef = useRef(null);
  const understatCsvInputRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: darkMode ? '#667eea' : '#764ba2',
        light: darkMode ? '#8aa7ed' : '#9575cd',
        dark: darkMode ? '#4c63d2' : '#5e35b1',
      },
      secondary: {
        main: darkMode ? '#764ba2' : '#667eea',
      },
      background: {
        default: darkMode ? '#0a0e27' : '#f5f5f5',
        paper: darkMode ? '#1a1d3a' : '#ffffff',
      },
      text: {
        primary: darkMode ? '#ffffff' : '#333333',
        secondary: darkMode ? '#b0b0b0' : '#666666',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 700,
        color: darkMode ? '#ffffff' : '#333333',
      },
      h6: {
        fontWeight: 600,
      },
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiDataGrid: {
        styleOverrides: {
          root: {
            border: 'none',
            '& .MuiDataGrid-cell': {
              borderBottom: `1px solid ${darkMode ? '#2a2d4a' : '#e0e0e0'}`,
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: darkMode ? '#2c3e50' : '#f8f9fa',
              borderBottom: `2px solid ${darkMode ? '#34495e' : '#e0e0e0'}`,
            },
            '& .MuiDataGrid-columnHeaderTitle': {
              fontWeight: 600,
              color: darkMode ? '#ffffff' : '#333333',
            },
          },
        },
      },
    },
  });

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleUploadMenuOpen = (event) => {
    setUploadMenuAnchor(event.currentTarget);
  };

  const handleUploadMenuClose = () => {
    setUploadMenuAnchor(null);
  };

  const handleSyncUnderstat = async () => {
    try {
      const response = await fetch('/api/understat/sync', { method: 'POST' });
      const result = await response.json();
      
      if (result.verification_needed && result.unmatched_players > 0) {
        const shouldVerify = window.confirm(
          `${result.message}\n\nWould you like to verify these players now?`
        );
        if (shouldVerify) {
          window.location.href = `http://localhost:5001${result.verification_url}`;
        }
      } else {
        alert(result.message || 'Sync completed');
      }
    } catch (error) {
      alert('Sync failed: ' + error.message);
    }
    handleUploadMenuClose();
  };

  const handleSyncNPxGTeams = async () => {
    try {
      const response = await fetch('/api/npxg/sync-team-stats', { method: 'POST' });
      const result = await response.json();

      if (result.success) {
        alert(`NPxG sync completed successfully!\n\nTeams updated: ${result.teams_updated}\nLeague avg NPxG: ${result.league_avg_npxg}\nLeague avg NPxGA: ${result.league_avg_npxga}`);
      } else {
        alert('NPxG sync failed: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      alert('NPxG sync failed: ' + error.message);
    }
    handleUploadMenuClose();
  };

  const handleRunValidation = () => {
    window.open('http://localhost:5001/api/validation-dashboard', '_blank');
    handleUploadMenuClose();
  };

  const handleArchiveWeek = async () => {
    if (!window.confirm('Archive current gameweek analysis? This will prepare the system for the next gameweek.')) {
      handleUploadMenuClose();
      return;
    }

    try {
      const response = await fetch('http://localhost:5001/api/archive-week', { method: 'POST' });
      const result = await response.json();

      if (result.success) {
        alert(`${result.message}\n\nArchived ${result.archived_data.players} players, ${result.archived_data.form_records} form records\n\n${result.next_steps}`);
      } else {
        alert(`Archive failed: ${result.error}`);
      }
    } catch (error) {
      alert('Archive failed: ' + error.message);
    }
    handleUploadMenuClose();
  };

  // CSV Import Handlers (Workaround for broken ScraperFC)
  const handleNPxGCsvUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/npxg/import-team-csv', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();

      if (result.success) {
        alert(`NPxG CSV import completed!\n\nTeams updated: ${result.teams_updated}\nLeague avg NPxG: ${result.league_avg_npxg}\nLeague avg NPxGA: ${result.league_avg_npxga}`);
      } else {
        alert('NPxG CSV import failed: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      alert('NPxG CSV import failed: ' + error.message);
    }

    // Reset file input
    event.target.value = '';
    handleUploadMenuClose();
  };

  const handleUnderstatCsvUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/understat/import-player-csv', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();

      if (result.verification_needed && result.unmatched_players > 0) {
        // Show confirmation with stats, then redirect to validation page
        const shouldVerify = window.confirm(
          `CSV parsed successfully!\n\nMatched: ${result.successfully_matched} players\nNeed verification: ${result.unmatched_players} players\n\nWould you like to verify unmatched players now?`
        );

        if (shouldVerify) {
          // Store matched data for later application
          sessionStorage.setItem('understat_csv_matched', JSON.stringify(result.matched_data));
          window.location.href = 'http://localhost:5001/import-validation?source=understat_csv';
        } else {
          // Apply only matched players immediately
          const applyResponse = await fetch('/api/understat/apply-player-csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matched_players: result.matched_data, confirmed_mappings: {} }),
          });
          const applyResult = await applyResponse.json();
          alert(`Applied ${applyResult.players_updated} matched players. ${result.unmatched_players} players skipped.`);
        }
      } else if (result.success) {
        // All players matched - apply immediately
        const applyResponse = await fetch('/api/understat/apply-player-csv', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ matched_players: result.matched_data, confirmed_mappings: {} }),
        });
        const applyResult = await applyResponse.json();
        alert(`Understat CSV import completed!\n\nPlayers updated: ${applyResult.players_updated}`);
      } else {
        alert('Understat CSV import failed: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      alert('Understat CSV import failed: ' + error.message);
    }

    // Reset file input
    event.target.value = '';
    handleUploadMenuClose();
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        minHeight: '100vh',
        background: darkMode 
          ? 'linear-gradient(135deg, #0a0e27 0%, #1a1d3a 50%, #2c3e50 100%)'
          : 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%)',
      }}>
        {/* Top App Bar with Upload Menu and Theme Toggle */}
        <AppBar position="static" elevation={0} sx={{ background: 'transparent' }}>
          <Toolbar sx={{ justifyContent: 'space-between' }}>
            {/* Upload Menu */}
            <Button
              variant="outlined"
              startIcon={<Upload />}
              onClick={handleUploadMenuOpen}
              sx={{
                color: darkMode ? '#ffffff' : '#333333',
                borderColor: darkMode ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)',
                '&:hover': {
                  backgroundColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                  borderColor: darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)',
                },
              }}
            >
              Upload & Sync
            </Button>
            
            {/* Hidden file inputs for CSV uploads */}
            <input
              type="file"
              ref={npxgCsvInputRef}
              style={{ display: 'none' }}
              accept=".csv"
              onChange={handleNPxGCsvUpload}
            />
            <input
              type="file"
              ref={understatCsvInputRef}
              style={{ display: 'none' }}
              accept=".csv"
              onChange={handleUnderstatCsvUpload}
            />

            <Menu
              anchorEl={uploadMenuAnchor}
              open={Boolean(uploadMenuAnchor)}
              onClose={handleUploadMenuClose}
              PaperProps={{
                sx: {
                  backgroundColor: darkMode ? '#2c3e50' : '#ffffff',
                  border: darkMode ? '1px solid #34495e' : '1px solid #e0e0e0',
                },
              }}
            >
              <MenuItem
                onClick={handleSyncUnderstat}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <CloudSync sx={{ mr: 1 }} />
                Sync Understat (API)
              </MenuItem>
              <MenuItem
                onClick={() => understatCsvInputRef.current?.click()}
                sx={{ color: darkMode ? '#ffffff' : '#333333', pl: 4 }}
              >
                <FileUpload sx={{ mr: 1, fontSize: '1rem' }} />
                Import Understat CSV
              </MenuItem>
              <MenuItem
                onClick={handleSyncNPxGTeams}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <Sports sx={{ mr: 1 }} />
                Sync NPxG Teams (API)
              </MenuItem>
              <MenuItem
                onClick={() => npxgCsvInputRef.current?.click()}
                sx={{ color: darkMode ? '#ffffff' : '#333333', pl: 4 }}
              >
                <FileUpload sx={{ mr: 1, fontSize: '1rem' }} />
                Import NPxG CSV
              </MenuItem>
              <MenuItem
                onClick={() => { window.open('http://localhost:5001/railway-sync', '_blank'); handleUploadMenuClose(); }}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <CloudSync sx={{ mr: 1, color: '#0ea5e9' }} />
                Sync to Railway
              </MenuItem>
              <MenuItem
                onClick={() => { window.open('http://localhost:5001/form-upload', '_blank'); handleUploadMenuClose(); }}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <Upload sx={{ mr: 1 }} />
                Upload Form Data
              </MenuItem>
              <MenuItem
                onClick={() => { window.open('http://localhost:5001/import-games', '_blank'); handleUploadMenuClose(); }}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <SportsEsports sx={{ mr: 1 }} />
                Import Game Scores
              </MenuItem>
              <MenuItem
                onClick={() => { window.open('http://localhost:5001/import-validation', '_blank'); handleUploadMenuClose(); }}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <Upload sx={{ mr: 1 }} />
                Import Lineup CSV
              </MenuItem>
              <MenuItem 
                onClick={() => { window.open('http://localhost:5001/odds-upload', '_blank'); handleUploadMenuClose(); }}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <Upload sx={{ mr: 1 }} />
                Upload Fixture Odds
              </MenuItem>
              <Divider sx={{ backgroundColor: darkMode ? '#34495e' : '#e0e0e0' }} />
              <MenuItem 
                onClick={handleArchiveWeek}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                <Archive sx={{ mr: 1 }} />
                Archive Week
              </MenuItem>
              <MenuItem 
                onClick={handleRunValidation}
                sx={{ color: darkMode ? '#ffffff' : '#333333' }}
              >
                Run Validation
              </MenuItem>
            </Menu>

            {/* Theme Toggle */}
            <IconButton
              onClick={toggleDarkMode}
              color="inherit"
              sx={{
                color: darkMode ? '#ffffff' : '#333333',
                '&:hover': {
                  backgroundColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                },
              }}
            >
              {darkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Dragon Banner */}
        <Banner />

        {/* Main Dashboard */}
        <Box sx={{ px: 3, pb: 3 }}>
          <Dashboard />
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;