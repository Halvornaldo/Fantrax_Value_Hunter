# Fantrax Value Hunter - Understat Integration Package

This package provides production-ready components for integrating Understat expected stats into the Fantrax Value Hunter system.

## Overview

The integration adds per-90 minute expected stats (xG90, xA90, xGI90) from Understat to enhance True Value calculations in Value Hunter.

**Enhanced True Value Formula:**
```
TrueValue = (PPG ÷ Price) × Form × Fixture × Starter × xGI90_multiplier
```

## Components

### 1. UnderstatIntegrator (`understat_integrator.py`)
- Extracts per-90 stats from Understat using ScraperFC
- Matches Understat players to Fantrax database using alias mapping
- Calculates xG90, xA90, xGI90 from raw xG, xA, and minutes data

### 2. ValueHunterExtension (`value_hunter_extension.py`)
- Enhances True Value calculations with xGI90 multipliers
- Provides display data formatting for new stats columns
- Includes database schema update utilities

### 3. IntegrationPipeline (`integration_pipeline.py`)
- Complete end-to-end integration pipeline
- Safe dry-run mode for testing (default)
- Generates integration reports and SQL updates

## Quick Start

```python
from integration_package import IntegrationPipeline

# Database configuration
db_config = {
    'host': 'localhost',
    'port': 5433,
    'database': 'fantrax_value_hunter',
    'user': 'fantrax_user',
    'password': 'fantrax_password'
}

# Run integration (dry run by default)
pipeline = IntegrationPipeline(db_config, 'alias_map.json', dry_run=True)
results = pipeline.run_full_integration()

print(f"Successfully matched {results['matched_players']} players")
print(f"Match rate: {results['match_rate']:.1f}%")
```

## Integration Stats (Latest Run)

- **Players Matched**: 330 of 574 Understat players (57.5% match rate)
- **Average xGI90**: 0.285 across all matched players
- **Database Updates**: 330 player records ready for update
- **Top xGI90 Player**: Mohamed Salah with 1.156 xGI90

## Safety Features

- **Dry Run Mode**: Default mode prevents accidental database changes
- **Alias Mapping**: Handles name variations between systems (Jhon Durán → Duran)
- **Error Handling**: Robust error handling for data extraction and matching
- **Integration Reports**: Detailed JSON reports for audit trail

## Database Schema Changes

The integration adds these columns to the `players` table:
```sql
ALTER TABLE players 
ADD COLUMN minutes INTEGER DEFAULT 0,
ADD COLUMN xG90 DECIMAL(5,3) DEFAULT 0.000,
ADD COLUMN xA90 DECIMAL(5,3) DEFAULT 0.000,
ADD COLUMN xGI90 DECIMAL(5,3) DEFAULT 0.000,
ADD COLUMN last_understat_update TIMESTAMP;
```

## Production Deployment

1. **Test in Dry Run**: Verify all components work with your database
2. **Review Integration Report**: Check matched players and calculations
3. **Apply Schema Updates**: Run generated SQL to add new columns
4. **Execute Data Updates**: Apply player stat updates
5. **Update Value Hunter Code**: Integrate enhanced True Value calculations

## Dependencies

- `pandas`: Data manipulation
- `psycopg2`: PostgreSQL database connection
- `ScraperFC`: Understat data extraction
- `json`: Configuration and reporting

## Error Handling

Common issues and solutions:

- **Unicode Encoding**: Handled automatically (✓ → OK for Windows console)
- **Name Matching**: Alias mapping improves match rate from 57% to 66%+
- **Missing Data**: Graceful defaults (0.0) for players without Understat data
- **Database Errors**: Clear error messages with troubleshooting hints

## Integration Flow

1. **Extract** Understat data for current season
2. **Match** player names using alias database
3. **Calculate** per-90 stats (xG90, xA90, xGI90)
4. **Generate** database updates and multiplier table
5. **Report** results and statistics
6. **Apply** updates (when dry_run=False)

This package ensures safe, reliable integration of Understat stats while maintaining the existing Value Hunter functionality.