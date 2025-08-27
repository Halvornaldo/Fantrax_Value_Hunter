import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, IconButton, Toolbar, AppBar } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import Banner from './components/Banner';
import Dashboard from './components/Dashboard';
import './App.css';

const App = () => {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved !== null ? JSON.parse(saved) : true;
  });

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

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        minHeight: '100vh',
        background: darkMode 
          ? 'linear-gradient(135deg, #0a0e27 0%, #1a1d3a 50%, #2c3e50 100%)'
          : 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%)',
      }}>
        {/* Top App Bar with Theme Toggle */}
        <AppBar position="static" elevation={0} sx={{ background: 'transparent' }}>
          <Toolbar sx={{ justifyContent: 'flex-end' }}>
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