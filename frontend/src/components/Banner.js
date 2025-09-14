import React from 'react';
import { Box, Chip, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';

const Banner = ({ playersCount = 0 }) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        position: 'relative',
        height: 'auto',
        overflow: 'hidden',
        mb: 3,
        borderRadius: '0 0 16px 16px',
        boxShadow: theme.palette.mode === 'dark' 
          ? '0 8px 32px rgba(0,0,0,0.6)' 
          : '0 8px 32px rgba(0,0,0,0.2)',
      }}
    >
      {/* Dragon banner image - full size */}
      <Box
        component="img"
        src="/fantrax-dominator-banner-full.png"
        alt="Fantrax Dominator"
        sx={{
          width: '100%',
          height: 'auto',
          display: 'block',
        }}
      />

      {/* Status overlay */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          display: 'flex',
          gap: 1,
          flexWrap: 'wrap',
        }}
      >
        <Chip
          label="Analyzing for: Gameweek 3"
          color="secondary"
          size="small"
          sx={{
            fontWeight: 600,
            backgroundColor: 'rgba(76, 175, 80, 0.9)',
            color: 'white',
          }}
        />
        <Chip
          label="V2.0 Enhanced"
          color="primary"
          size="small"
          sx={{
            fontWeight: 600,
            backgroundColor: 'rgba(255,255,255,0.9)',
            color: theme.palette.primary.main,
          }}
        />
        <Chip
          label={`${playersCount} Players`}
          size="small"
          sx={{
            fontWeight: 600,
            backgroundColor: 'rgba(40,167,69,0.9)',
            color: 'white',
          }}
        />
      </Box>
      
      {/* Gameweek explanation subtitle */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          color: 'rgba(255,255,255,0.9)',
          backgroundColor: 'rgba(0,0,0,0.6)',
          padding: '8px 16px',
          borderRadius: 2,
          backdropFilter: 'blur(10px)',
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          Data current through GW2 completion
        </Typography>
      </Box>
    </Box>
  );
};

export default Banner;