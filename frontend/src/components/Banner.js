import React from 'react';
import { Box } from '@mui/material';
import { useTheme } from '@mui/material/styles';

const Banner = () => {
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

      
    </Box>
  );
};

export default Banner;