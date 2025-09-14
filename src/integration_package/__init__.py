"""
Fantrax Value Hunter - Understat Integration Package

This package provides clean, production-ready components for integrating
Understat expected stats (xG90, xA90, xGI90) into the Fantrax Value Hunter system.

Modules:
- understat_integrator: Extract and match Understat data with Fantrax players
- value_hunter_extension: Enhance True Value calculations with xGI multipliers  
- integration_pipeline: Complete pipeline for safe integration

Usage:
    from integration_package import IntegrationPipeline
    
    pipeline = IntegrationPipeline(db_config, alias_map_path, dry_run=True)
    results = pipeline.run_full_integration()
"""

__version__ = "1.0.0"
__author__ = "Fantrax Value Hunter Enhancement"

from .understat_integrator import UnderstatIntegrator
from .value_hunter_extension import ValueHunterExtension, DatabaseUpdater
from .integration_pipeline import IntegrationPipeline

__all__ = [
    "UnderstatIntegrator",
    "ValueHunterExtension", 
    "DatabaseUpdater",
    "IntegrationPipeline"
]