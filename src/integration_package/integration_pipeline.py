#!/usr/bin/env python3
"""
Integration Pipeline
Complete pipeline for integrating Understat stats into Value Hunter
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from .understat_integrator import UnderstatIntegrator
from .value_hunter_extension import ValueHunterExtension, DatabaseUpdater


class IntegrationPipeline:
    """Complete pipeline for Understat integration"""
    
    def __init__(self, db_config, alias_map_path=None, dry_run=True):
        """
        Initialize integration pipeline
        
        Args:
            db_config: Database connection configuration
            alias_map_path: Path to alias mapping file (unused - kept for compatibility)
            dry_run: If True, doesn't modify database (default: True for safety)
        """
        self.db_config = db_config
        self.dry_run = dry_run
        self.integrator = UnderstatIntegrator(db_config)
        
    def run_full_integration(self, season="2024/2025", leagues=["EPL"]):
        """
        Run complete integration pipeline
        
        Args:
            season: Understat season
            leagues: List of leagues to process
        
        Returns:
            Dict: Integration results and statistics
        """
        print("=" * 80)
        print("FANTRAX VALUE HUNTER - UNDERSTAT INTEGRATION PIPELINE")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"Season: {season}")
        print(f"Leagues: {', '.join(leagues)}")
        print()
        
        results = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'season': season,
            'leagues': leagues,
            'dry_run': self.dry_run
        }
        
        try:
            # Step 1: Extract and match data
            print("Step 1: Extracting Understat data and matching names...")
            matched_players, unmatched_players, multiplier_table, stats = self.integrator.generate_integration_data(season, leagues)
            
            if matched_players is None:
                print("ERROR: No data extracted from Understat")
                return results
            
            print(f"OK Successfully matched {stats['successfully_matched']} players ({stats['match_rate']:.1f}% match rate)")
            print(f"OK Top xGI90 player: {stats['top_xGI90_player']} ({stats['max_xGI90']:.3f})")
            print()
            
            # Handle unmatched players
            if unmatched_players is not None and not unmatched_players.empty:
                print(f"⚠️ {len(unmatched_players)} players need manual review")
                # Save for review UI
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unmatched_file = Path(__file__).parent / f"unmatched_players_{timestamp}.json"
                unmatched_players.to_json(unmatched_file, orient='records', indent=2)
                print(f"   Saved to: {unmatched_file.name}")
                print()
            
            # Step 2: Initialize Value Hunter extension
            print("Step 2: Initializing Value Hunter extension...")
            extension = ValueHunterExtension(multiplier_table)
            
            extension_stats = extension.get_stats_summary()
            print(f"OK Loaded xGI multipliers for {extension_stats['total_players_with_xgi']} players")
            print(f"OK Average xGI90 multiplier: {extension_stats['avg_xgi_multiplier']:.3f}")
            print()
            
            # Step 3: Generate database updates
            print("Step 3: Generating database updates...")
            
            # Schema updates
            schema_sql = DatabaseUpdater.generate_schema_update_sql()
            data_updates = DatabaseUpdater.generate_data_update_sql(matched_players)
            
            print(f"OK Generated schema updates")
            print(f"OK Generated {len(data_updates)} player data updates")
            print()
            
            # Step 4: Apply updates (or simulate in dry run)
            if self.dry_run:
                print("Step 4: DRY RUN - Simulating database updates...")
                print("Schema update SQL generated (not executed)")
                print(f"{len(data_updates)} player updates generated (not executed)")
                print("OK Dry run complete - no database changes made")
            else:
                print("Step 4: Applying database updates...")
                # In production, would execute SQL here
                print("WARNING: Live execution not implemented yet")
                print("Use dry_run=True for testing")
            
            print()
            
            # Step 5: Generate integration report
            print("Step 5: Generating integration report...")
            
            report_data = {
                'integration_summary': stats,
                'extension_summary': extension_stats,
                'schema_updates': schema_sql,
                'total_data_updates': len(data_updates),
                'unmatched_count': len(unmatched_players) if unmatched_players is not None else 0,
                'sample_enhanced_calculations': self._generate_sample_calculations(extension, matched_players.head(5))
            }
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = Path(__file__).parent / f"integration_report_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"OK Integration report saved: {report_file.name}")
            print()
            
            # Success summary
            print("=" * 80)
            print("INTEGRATION PIPELINE COMPLETE")
            print("=" * 80)
            print(f"OK {stats['successfully_matched']} players ready for integration")
            print(f"OK {stats['match_rate']:.1f}% automatic matching success")
            print(f"OK Average xGI90: {stats['avg_xGI90']:.3f}")
            print(f"OK Integration components ready for Value Hunter")
            
            if self.dry_run:
                print("OK Dry run complete - safe to proceed with live integration")
            
            results.update({
                'success': True,
                'matched_players': stats['successfully_matched'],
                'match_rate': stats['match_rate'],
                'report_file': str(report_file),
                'integration_data': report_data
            })
            
            return results
            
        except Exception as e:
            print(f"ERROR: Integration pipeline failed: {e}")
            results['error'] = str(e)
            return results
    
    def _generate_sample_calculations(self, extension, sample_players):
        """Generate sample enhanced True Value calculations"""
        
        sample_calculations = []
        
        for idx, player in sample_players.iterrows():
            # Sample calculation with hypothetical values
            enhanced_tv = extension.calculate_enhanced_true_value(
                ppg=8.0,  # Hypothetical PPG
                price=10.0,  # Hypothetical price
                form=1.1,  # Hypothetical form
                fixture=1.05,  # Hypothetical fixture
                starter=1.0,  # Hypothetical starter
                fantrax_id=player['fantrax_id']
            )
            
            xgi_multiplier = extension.get_xgi_multiplier(player['fantrax_id'])
            
            sample_calculations.append({
                'player_name': player['player_name'],
                'fantrax_id': player['fantrax_id'],
                'xGI90': player['xGI90'],
                'xgi_multiplier': xgi_multiplier,
                'sample_enhanced_true_value': enhanced_tv,
                'calculation_note': 'Sample calculation with hypothetical PPG/price/form/fixture/starter values'
            })
        
        return sample_calculations


def main():
    """Run integration pipeline"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'fantrax_value_hunter',
        'user': 'fantrax_user',
        'password': 'fantrax_password'
    }
    
    # Alias mapping path
    alias_map_path = Path(__file__).parent.parent / "data" / "fantrax_alias_map.json"
    
    # Initialize pipeline (DRY RUN by default for safety)
    pipeline = IntegrationPipeline(db_config, alias_map_path, dry_run=True)
    
    # Run integration
    results = pipeline.run_full_integration()
    
    if results['success']:
        print("\nIntegration pipeline completed successfully!")
        print(f"Report saved: {results['report_file']}")
    else:
        print("\nIntegration pipeline failed!")
        if 'error' in results:
            print(f"Error: {results['error']}")


if __name__ == "__main__":
    main()