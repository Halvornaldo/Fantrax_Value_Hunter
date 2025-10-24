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
  Restore
} from '@mui/icons-material';
import { useTheme as useMuiTheme } from '@mui/material/styles';

import { updateSystemParameters, resetSystemParametersToDefaults, runModelValidation, syncUnderstatData, importLineupCSV, importOddsCSV } from '../services/api';

const ParameterPanel = ({ systemConfig, onParametersUpdate, playersCount }) => {
  const muiTheme = useMuiTheme();
  const isDark = muiTheme.palette.mode === 'dark';

  // Parameter states
  const [parameters, setParameters] = useState({
    ewmaAlpha: 0.44,
    adaptationGameweek: 10,
    xgiEnabled: false,
    xgiWeight: 0.13,
    mfPositionWeight: 0.3,
    formCap: 1.4,
    fixtureCap: 1.8,
    xgiCap: 2.5,
    globalCap: 3.0,
    fixtureBase: 1.3,
    // Formula toggles
    formEnabled: false,
    fixtureEnabled: true,
    starterEnabled: true,
    // Starter penalties (6-tier system)
    likelyStarterPenalty: 0.85,
    rotationPenalty: 0.7,
    unlikelyStarterPenalty: 0.5,
    benchPenalty: 0.15,
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
        ewmaAlpha: v2Config.ewma_form?.alpha || 0.44,
        adaptationGameweek: v2Config.dynamic_blending?.full_adaptation_gw || 10,
        xgiEnabled: v2Config.positional_xgi?.enabled || false,
        xgiWeight: v2Config.positional_xgi?.xgi_weight || 0.13,
        mfPositionWeight: v2Config.positional_xgi?.mf_position_weight || 0.3,
        formCap: v2Config.multiplier_caps?.form || 1.4,
        fixtureCap: v2Config.multiplier_caps?.fixture || 1.8,
        xgiCap: v2Config.multiplier_caps?.xgi || 2.5,
        globalCap: v2Config.multiplier_caps?.global || 3.0,
        fixtureBase: v2Config.exponential_fixture?.base || 1.3,
        // Formula toggles
        formEnabled: v2Config.formula_toggles?.form_enabled ?? false,
        fixtureEnabled: v2Config.formula_toggles?.fixture_enabled ?? true,
        starterEnabled: v2Config.formula_toggles?.starter_enabled ?? true,
        // Starter penalties (5-tier system)
        likelyStarterPenalty: starterConfig?.likely_starter_penalty || 0.85,
        rotationPenalty: starterConfig?.auto_rotation_penalty || 0.7,
        unlikelyStarterPenalty: starterConfig?.unlikely_starter_penalty || 0.5,
        benchPenalty: starterConfig?.force_bench_penalty || 0.15,
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
          positional_xgi: {
            enabled: parameters.xgiEnabled,
            xgi_weight: parameters.xgiWeight,
            mf_position_weight: parameters.mfPositionWeight
          },
          multiplier_caps: {
            form: parameters.formCap,
            fixture: parameters.fixtureCap,
            xgi: parameters.xgiCap,
            global: parameters.globalCap
          },
          ewma_form: {
            alpha: parameters.ewmaAlpha
          },
          exponential_fixture: {
            enabled: true,
            base: parameters.fixtureBase
          }
        },
        starter_prediction: {
          enabled: true,
          likely_starter_penalty: parameters.likelyStarterPenalty,
          auto_rotation_penalty: parameters.rotationPenalty,
          unlikely_starter_penalty: parameters.unlikelyStarterPenalty,
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
      console.log('Sync response:', response);
      if (response.success) {
        await onParametersUpdate({});
        
        console.log('Checking verification:', {
          verification_needed: response.verification_needed,
          unmatched_players: response.unmatched_players,
          verification_url: response.verification_url
        });
        
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

  // Reset parameters to defaults
  const handleResetToDefaults = async () => {
    const confirmReset = window.confirm(
      'Are you sure you want to reset all parameters to their default values?\n\n' +
      'This will:\n' +
      '• Reset all sliders to baseline values\n' +
      '• Update all player calculations\n' +
      '• Cannot be undone\n\n' +
      'Proceed with reset?'
    );

    if (!confirmReset) return;

    try {
      setUpdating(true);
      const response = await resetSystemParametersToDefaults();

      if (response.success) {
        setPendingChanges(false);
        await onParametersUpdate(response.updated_config || {});
        alert(`${response.message}\n\nUpdated ${response.updated_players} players with default parameter values.`);
      } else {
        throw new Error(response.error || 'Failed to reset parameters');
      }
    } catch (error) {
      console.error('Reset failed:', error);
      alert('Reset failed: ' + error.message);
    } finally {
      setUpdating(false);
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
        
        let alertMessage = `Import successful!\n`;
        alertMessage += `Matched: ${response.matched_players}/${response.total_players} players (${response.match_rate}%)\n`;
        alertMessage += `Starters: ${response.starters_identified}\n`;
        alertMessage += `Rotation risks: ${response.rotation_risks}\n`;
        
        if (response.unmatched_players > 0) {
          alertMessage += `\n⚠️ ${response.unmatched_players} players need validation!\n`;
          alertMessage += `(May include star players with 0.35x multiplier)\n`;
          alertMessage += `\nClick OK to go to validation page.`;
          
          alert(alertMessage);
          
          if (response.verification_needed && response.verification_url) {
            window.location.href = 'http://localhost:5001' + response.verification_url;
          }
        } else {
          alert(alertMessage);
        }
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
            min={0.25}
            max={0.75}
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
            min={5}
            max={15}
            step={1}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            Current: GW{parameters.adaptationGameweek}
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* xGI Weight Slider */}
        {parameters.xgiEnabled && (
          <>
            <Grid item xs={1.5}>
              <Typography variant="body2" gutterBottom>xGI Weight</Typography>
              <Slider
                value={parameters.xgiWeight}
                onChange={(e, value) => handleParameterChange('xgiWeight', value)}
                min={0.00}
                max={0.25}
                step={0.01}
                size="small"
                valueLabelDisplay="auto"
              />
              <Typography variant="caption" color="text.secondary">
                {(parameters.xgiWeight * 100).toFixed(0)}%
              </Typography>
            </Grid>
            <Divider orientation="vertical" flexItem />
          </>
        )}

        {/* M/F Position Weight Slider */}
        {parameters.xgiEnabled && (
          <>
            <Grid item xs={1.5}>
              <Typography variant="body2" gutterBottom>M/F Split</Typography>
              <Slider
                value={parameters.mfPositionWeight}
                onChange={(e, value) => handleParameterChange('mfPositionWeight', value)}
                min={0.10}
                max={0.50}
                step={0.01}
                size="small"
                valueLabelDisplay="auto"
              />
              <Typography variant="caption" color="text.secondary">
                {((1 - parameters.mfPositionWeight) * 100).toFixed(0)}:{(parameters.mfPositionWeight * 100).toFixed(0)}
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
            min={1.1}
            max={2.0}
            step={0.05}
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

        {/* NPxG Weight */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>NPxG Weight</Typography>
          <Box display="flex" alignItems="center" gap={0.5}>
            <Slider
              value={parameters.fixtureBase || 1.3}
              onChange={(e, value) => handleParameterChange('fixtureBase', value)}
              min={1.15}
              max={1.50}
              step={0.01}
              size="small"
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => {
                // Convert to percentage: (value - 1.15) / 0.35 * 40 - 20
                const percentage = ((value - 1.15) / 0.35 * 40 - 20);
                return `${percentage.toFixed(0)}%`;
              }}
              sx={{ flex: 1 }}
            />
          </Box>
          <Typography variant="caption" color="text.secondary">
            {(() => {
              const percentage = ((parameters.fixtureBase - 1.15) / 0.35 * 40 - 20);
              return `${percentage.toFixed(0)}%`;
            })()}
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

        {/* Likely Starter Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Likely Starter</Typography>
          <Slider
            value={parameters.likelyStarterPenalty}
            onChange={(e, value) => handleParameterChange('likelyStarterPenalty', value)}
            min={0.7}
            max={0.95}
            step={0.01}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {(parameters.likelyStarterPenalty || 0.85).toFixed(2)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Rotation Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Rotation Risk</Typography>
          <Slider
            value={parameters.rotationPenalty}
            onChange={(e, value) => handleParameterChange('rotationPenalty', value)}
            min={0.5}
            max={0.85}
            step={0.01}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {(parameters.rotationPenalty || 0.7).toFixed(2)}x
          </Typography>
        </Grid>


        <Divider orientation="vertical" flexItem />

        {/* Unlikely Starter Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Unlikely Starter</Typography>
          <Slider
            value={parameters.unlikelyStarterPenalty}
            onChange={(e, value) => handleParameterChange('unlikelyStarterPenalty', value)}
            min={0.30}
            max={0.65}
            step={0.01}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {(parameters.unlikelyStarterPenalty || 0.5).toFixed(2)}x
          </Typography>
        </Grid>

        <Divider orientation="vertical" flexItem />

        {/* Bench Penalty */}
        <Grid item xs={1.5}>
          <Typography variant="body2" gutterBottom>Bench</Typography>
          <Slider
            value={parameters.benchPenalty}
            onChange={(e, value) => handleParameterChange('benchPenalty', value)}
            min={0.05}
            max={0.25}
            step={0.01}
            size="small"
            valueLabelDisplay="auto"
          />
          <Typography variant="caption" color="text.secondary">
            {(parameters.benchPenalty || 0.15).toFixed(2)}x
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
            
            
            <Tooltip title="Run Validation">
              <IconButton size="small" onClick={() => window.open('/api/validation-dashboard', '_blank')}>
                <Assessment />
              </IconButton>
            </Tooltip>

            <Tooltip title="Reset to Defaults">
              <IconButton
                size="small"
                onClick={handleResetToDefaults}
                disabled={updating}
                color="warning"
              >
                <Restore />
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