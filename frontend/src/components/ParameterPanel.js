import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Grid,
  Chip,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow,
  Assessment,
  TrendingUp,
  Speed,
  Info,
  Refresh,
  CloudSync,
  FileUpload,
  SportsFootball,
  SportsSoccer
} from '@mui/icons-material';
import { useTheme as useMuiTheme } from '@mui/material/styles';

import { updateSystemParameters, runModelValidation, syncUnderstatData, importLineupCSV } from '../services/api';

const ParameterPanel = ({ systemConfig, onParametersUpdate, playersCount }) => {
  const muiTheme = useMuiTheme();
  const isDark = muiTheme.palette.mode === 'dark';

  // Parameter states
  const [parameters, setParameters] = useState({
    ewmaAlpha: 0.87,
    adaptationGameweek: 12,
    xgiEnabled: false,
    xgiStrength: 1.0,
    formCap: 2.0,
    fixtureCap: 1.8,
    xgiCap: 2.5,
    globalCap: 3.0,
    // Formula toggles
    formEnabled: true,
    fixtureEnabled: true,
    starterEnabled: true,
    // Starter penalties
    rotationPenalty: 0.75,
    benchPenalty: 0.6,
    outPenalty: 0.0
  });

  // Update states
  const [updating, setUpdating] = useState(false);
  const [pendingChanges, setPendingChanges] = useState(false);

  // Initialize from system config
  useEffect(() => {
    if (systemConfig.formula_optimization_v2) {
      const v2Config = systemConfig.formula_optimization_v2;
      const starterConfig = systemConfig.starter_prediction;
      setParameters({
        ewmaAlpha: v2Config.ewma_form?.alpha || 0.87,
        adaptationGameweek: v2Config.dynamic_blending?.full_adaptation_gw || 12,
        xgiEnabled: v2Config.normalized_xgi?.enabled || false,
        xgiStrength: v2Config.normalized_xgi?.normalization_strength || 1.0,
        formCap: v2Config.multiplier_caps?.form || 2.0,
        fixtureCap: v2Config.multiplier_caps?.fixture || 1.8,
        xgiCap: v2Config.multiplier_caps?.xgi || 2.5,
        globalCap: v2Config.multiplier_caps?.global || 3.0,
        // Formula toggles
        formEnabled: v2Config.formula_toggles?.form_enabled ?? true,
        fixtureEnabled: v2Config.formula_toggles?.fixture_enabled ?? true,
        starterEnabled: v2Config.formula_toggles?.starter_enabled ?? true,
        // Starter penalties
        rotationPenalty: starterConfig?.auto_rotation_penalty || 0.75,
        benchPenalty: starterConfig?.force_bench_penalty || 0.6,
        outPenalty: starterConfig?.force_out_penalty || 0.0
      });
      setPendingChanges(false);
    }
  }, [systemConfig]);

  // Handle parameter changes
  const handleParameterChange = (key, value) => {
    setParameters(prev => ({ ...prev, [key]: value }));
    setPendingChanges(true);
  };

  // Apply parameter changes
  const handleApplyChanges = async () => {
    try {
      setUpdating(true);

      const changes = {
        formula_optimization_v2: {
          enabled: true,
          formula_toggles: {
            form_enabled: parameters.formEnabled,
            fixture_enabled: parameters.fixtureEnabled,
            starter_enabled: parameters.starterEnabled,
            xgi_enabled: parameters.xgiEnabled
          },
          exponential_form: {
            enabled: true,
            alpha: parameters.ewmaAlpha
          },
          dynamic_blending: {
            full_adaptation_gw: parameters.adaptationGameweek
          },
          normalized_xgi: {
            enabled: parameters.xgiEnabled,
            normalization_strength: parameters.xgiStrength,
            position_adjustments: {
              defenders: true,
              midfielders: true,
              forwards: true
            }
          },
          multiplier_caps: {
            form: parameters.formCap,
            fixture: parameters.fixtureCap,
            xgi: parameters.xgiCap,
            global: parameters.globalCap
          },
          ewma_form: {
            alpha: parameters.ewmaAlpha
          }
        },
        starter_prediction: {
          enabled: true,
          auto_rotation_penalty: parameters.rotationPenalty,
          force_bench_penalty: parameters.benchPenalty,
          force_out_penalty: parameters.outPenalty
        }
      };

      const response = await updateSystemParameters(changes);
      
      if (response.success) {
        setPendingChanges(false);
        await onParametersUpdate(response.updated_config || {});
      } else {
        throw new Error(response.error || 'Failed to update parameters');
      }
    } catch (error) {
      console.error('Parameter update failed:', error);
      alert('Failed to update parameters: ' + error.message);
    } finally {
      setUpdating(false);
    }
  };

  // Sync Understat data
  const handleSyncUnderstat = async () => {
    try {
      const response = await syncUnderstatData();
      if (response.success) {
        await onParametersUpdate({});
        
        // Check if verification is needed
        if (response.verification_needed && response.unmatched_players > 0) {
          const shouldVerify = window.confirm(
            `${response.message}\n\nWould you like to verify these players now?`
          );
          if (shouldVerify) {
            window.location.href = `http://localhost:5001${response.verification_url}`;
          }
        } else {
          alert(response.message || 'Understat data synced successfully');
        }
      } else {
        throw new Error(response.error || 'Sync failed');
      }
    } catch (error) {
      console.error('Sync failed:', error);
      alert('Sync failed: ' + error.message);
    }
  };

  // Handle lineup import
  const handleLineupImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const response = await importLineupCSV(file);
      
      if (response.success) {
        await onParametersUpdate({});
        alert(`Import successful!\nStarters: ${response.starters_identified}\nRotation risks: ${response.rotation_risks}`);
      } else {
        throw new Error(response.error || 'Import failed');
      }
    } catch (error) {
      console.error('Import failed:', error);
      alert('Import failed: ' + error.message);
    }
    
    // Clear the input to allow re-importing the same file
    event.target.value = '';
  };

  return (
    <Paper 
      elevation={4}
      sx={{
        borderRadius: 2,
        background: isDark 
          ? 'linear-gradient(145deg, #1e2139 0%, #252847 100%)'
          : 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
        border: `1px solid ${muiTheme.palette.divider}`,
        p: 2
      }}
    >
      <Grid container spacing={2} alignItems="center">
        {/* Header */}
        <Grid item>
          <Chip label={`${playersCount} Players`} size="small" color="success" />
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* EWMA Alpha */}
        <Grid item xs={2}>
          <Typography variant="body2" gutterBottom>EWMA α</Typography>
          <Slider
            value={parameters.ewmaAlpha}
            onChange={(e, value) => handleParameterChange('ewmaAlpha', value)}
            min={0.1}
            max={1.0}
            step={0.01}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            Current: {parameters.ewmaAlpha.toFixed(2)}
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Adaptation Gameweek */}
        <Grid item xs={2}>
          <Typography variant="body2" gutterBottom>Adaptation GW</Typography>
          <Slider
            value={parameters.adaptationGameweek}
            onChange={(e, value) => handleParameterChange('adaptationGameweek', value)}
            min={8}
            max={20}
            step={1}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            Current: GW{parameters.adaptationGameweek}
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* xGI Strength Slider */}
        {parameters.xgiEnabled && (
          <>
            <Grid item>
              <Typography variant="body2" gutterBottom>xGI Strength</Typography>
              <Slider
                value={parameters.xgiStrength}
                onChange={(e, value) => handleParameterChange('xgiStrength', value)}
                min={0.5}
                max={2.0}
                step={0.1}
                size="small"
                valueLabelDisplay="auto"
              />
              <Typography variant="caption" color="text.secondary">
                {parameters.xgiStrength.toFixed(1)}x
              </Typography>
            </Grid>
            <Divider orientation="vertical" flexItem />
          </>
        )}

        {/* Formula Toggles */}
        <Grid item>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={parameters.formEnabled}
                  onChange={(e) => handleParameterChange('formEnabled', e.target.checked)}
                  size="small"
                />
              }
              label={<Typography variant="caption">Form</Typography>}
              sx={{ m: 0 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={parameters.fixtureEnabled}
                  onChange={(e) => handleParameterChange('fixtureEnabled', e.target.checked)}
                  size="small"
                />
              }
              label={<Typography variant="caption">Fixture</Typography>}
              sx={{ m: 0 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={parameters.starterEnabled}
                  onChange={(e) => handleParameterChange('starterEnabled', e.target.checked)}
                  size="small"
                />
              }
              label={<Typography variant="caption">Starter</Typography>}
              sx={{ m: 0 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={parameters.xgiEnabled}
                  onChange={(e) => handleParameterChange('xgiEnabled', e.target.checked)}
                  size="small"
                />
              }
              label={<Typography variant="caption">xGI</Typography>}
              sx={{ m: 0 }}
            />
          </Box>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Form Cap */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Form Cap</Typography>
          <Slider
            value={parameters.formCap}
            onChange={(e, value) => handleParameterChange('formCap', value)}
            min={1.5}
            max={3.0}
            step={0.1}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.formCap.toFixed(1)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Fixture Cap */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Fixture Cap</Typography>
          <Slider
            value={parameters.fixtureCap}
            onChange={(e, value) => handleParameterChange('fixtureCap', value)}
            min={1.3}
            max={2.5}
            step={0.1}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.fixtureCap.toFixed(1)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* xGI Cap */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>xGI Cap</Typography>
          <Slider
            value={parameters.xgiCap}
            onChange={(e, value) => handleParameterChange('xgiCap', value)}
            min={2.0}
            max={4.0}
            step={0.1}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.xgiCap.toFixed(1)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Global Cap */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Global Cap</Typography>
          <Slider
            value={parameters.globalCap}
            onChange={(e, value) => handleParameterChange('globalCap', value)}
            min={2.5}
            max={5.0}
            step={0.1}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.globalCap.toFixed(1)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Rotation Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Rotation Risk</Typography>
          <Slider
            value={parameters.rotationPenalty}
            onChange={(e, value) => handleParameterChange('rotationPenalty', value)}
            min={0.0}
            max={1.0}
            step={0.05}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.rotationPenalty.toFixed(2)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Bench Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Bench</Typography>
          <Slider
            value={parameters.benchPenalty}
            onChange={(e, value) => handleParameterChange('benchPenalty', value)}
            min={0.0}
            max={1.0}
            step={0.05}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.benchPenalty.toFixed(2)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Out Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Out</Typography>
          <Slider
            value={parameters.outPenalty}
            onChange={(e, value) => handleParameterChange('outPenalty', value)}
            min={0.0}
            max={1.0}
            step={0.05}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {parameters.outPenalty.toFixed(2)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Actions */}
        <Grid item>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              size="small"
              onClick={handleApplyChanges}
              disabled={!pendingChanges || updating}
              startIcon={updating ? <Refresh className="spin" /> : <PlayArrow />}
              color={pendingChanges ? "primary" : "inherit"}
            >
              {updating ? 'Applying...' : pendingChanges ? 'Apply' : 'No Changes'}
            </Button>
            
            <Tooltip title="Sync Understat Data">
              <IconButton size="small" onClick={handleSyncUnderstat}>
                <CloudSync />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Upload Form Data">
              <IconButton size="small" onClick={() => window.open('http://localhost:5001/form-upload', '_blank')}>
                <FileUpload />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Import Lineup CSV">
              <IconButton size="small" component="label">
                <input
                  type="file"
                  accept=".csv"
                  hidden
                  onChange={handleLineupImport}
                />
                <SportsFootball />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Upload Fixture Odds">
              <IconButton size="small" onClick={() => window.open('http://localhost:5001/odds-upload', '_blank')}>
                <SportsSoccer />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Run Validation">
              <IconButton size="small" onClick={() => window.open('/api/validation-dashboard', '_blank')}>
                <Assessment />
              </IconButton>
            </Tooltip>
          </Box>
        </Grid>
      </Grid>

      {/* CSS for spin animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </Paper>
  );
};

export default ParameterPanel;