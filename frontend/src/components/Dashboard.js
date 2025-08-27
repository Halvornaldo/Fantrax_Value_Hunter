import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Alert,
  Skeleton,
  Fade
} from '@mui/material';
import { useTheme as useMuiTheme } from '@mui/material/styles';

import ParameterPanel from './ParameterPanel';
import PlayerTable from './PlayerTable';
import { fetchPlayersData, fetchSystemConfig } from '../services/api';

const Dashboard = () => {
  const muiTheme = useMuiTheme();
  
  const [playersData, setPlayersData] = useState([]);
  const [systemConfig, setSystemConfig] = useState({});
  const [gameweekInfo, setGameweekInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Load initial data
  useEffect(() => {
    let isMounted = true;
    const abortController = new AbortController();
    
    const loadData = async () => {
      if (isMounted) {
        await loadDashboardData();
      }
    };
    
    loadData();
    
    // Cleanup function to prevent duplicate calls
    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load system configuration and player data in parallel
      const [configResponse, playersResponse] = await Promise.all([
        fetchSystemConfig(),
        fetchPlayersData()
      ]);

      if (configResponse.success) {
        setSystemConfig(configResponse.config);
      }

      if (playersResponse.players && Array.isArray(playersResponse.players)) {
        setPlayersData(playersResponse.players);
        setGameweekInfo(playersResponse.gameweek_info);
        console.log(`✅ Loaded ${playersResponse.players.length} players with V2.0 calculations`);
      } else {
        throw new Error(playersResponse.error || 'Failed to load player data');
      }

    } catch (err) {
      console.error('❌ Dashboard data load error:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleParametersUpdate = async (updatedConfig) => {
    try {
      console.log('🔄 Updating V2.0 parameters and recalculating...');
      
      // Update local config immediately for responsive UI
      setSystemConfig(prev => ({ ...prev, ...updatedConfig }));
      
      // Reload player data with new calculations
      await loadDashboardData();
      
      console.log('✅ Parameters updated and data refreshed');
    } catch (err) {
      console.error('❌ Parameter update error:', err);
      setError('Failed to update parameters: ' + err.message);
    }
  };

  if (loading) {
    return (
      <Box sx={{ mt: 2 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 3, height: 600 }}>
              <Skeleton variant="text" height={40} sx={{ mb: 2 }} />
              <Skeleton variant="rectangular" height={500} />
            </Paper>
          </Grid>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 3, height: 600 }}>
              <Skeleton variant="text" height={40} sx={{ mb: 2 }} />
              <Skeleton variant="rectangular" height={500} />
            </Paper>
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 2 }}>
        <Alert 
          severity="error" 
          sx={{ 
            mb: 2,
            '& .MuiAlert-message': {
              fontSize: '1.1rem',
            }
          }}
        >
          <Typography variant="h6" gutterBottom>
            Dashboard Load Error
          </Typography>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Fade in={!loading} timeout={500}>
      <Box sx={{ mt: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Top Panel - Parameter Controls */}
          <Paper 
            elevation={4}
            sx={{
              borderRadius: 3,
              background: muiTheme.palette.mode === 'dark' 
                ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
                : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
              border: `1px solid ${muiTheme.palette.divider}`,
            }}
          >
            <ParameterPanel
              systemConfig={systemConfig}
              onParametersUpdate={handleParametersUpdate}
              playersCount={playersData.length}
            />
          </Paper>

          {/* Bottom Panel - Player Table (Full Width) */}
          <Paper 
            elevation={8}
            sx={{
              borderRadius: 3,
              overflow: 'hidden',
              background: muiTheme.palette.mode === 'dark' 
                ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
                : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
              border: `1px solid ${muiTheme.palette.divider}`,
            }}
          >
            <PlayerTable 
              playersData={playersData}
              gameweekInfo={gameweekInfo}
              onDataRefresh={loadDashboardData}
            />
          </Paper>
        </Box>
      </Box>
    </Fade>
  );
};

export default Dashboard;