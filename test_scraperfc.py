#!/usr/bin/env python3
"""
Diagnostic script to test ScraperFC league table fetching.
Run this to see what the API is actually returning.
"""

import ScraperFC as sfc

def test_league_tables():
    print("=" * 60)
    print("ScraperFC League Tables Diagnostic Test")
    print("=" * 60)

    understat = sfc.Understat()

    # Test current season
    season = '2025/2026'
    print(f"\nTesting season: {season}")
    print("-" * 40)

    try:
        tables = understat.scrape_league_tables(year=season, league='EPL')

        print(f"Result type: {type(tables)}")
        print(f"Result value: {tables}")
        print(f"Is None: {tables is None}")
        print(f"Is empty list: {tables == []}")

        if tables:
            print(f"Number of tables: {len(tables)}")
            for i, table in enumerate(tables):
                print(f"\nTable {i}:")
                print(f"  Type: {type(table)}")
                if hasattr(table, 'columns'):
                    print(f"  Columns: {table.columns.tolist()}")
                    print(f"  Shape: {table.shape}")
                    print(f"  First few rows:")
                    print(table.head(3))
        else:
            print("\n>>> WARNING: No tables returned! <<<")
            print("This is why you're getting 'list index out of range' errors.")

    except Exception as e:
        print(f"\n>>> ERROR: {type(e).__name__}: {e} <<<")
        import traceback
        traceback.print_exc()

    # Also test previous season as fallback check
    print("\n" + "=" * 60)
    print("Testing previous season as comparison...")
    print("=" * 60)

    season_prev = '2024/2025'
    print(f"\nTesting season: {season_prev}")
    print("-" * 40)

    try:
        tables_prev = understat.scrape_league_tables(year=season_prev, league='EPL')

        print(f"Result type: {type(tables_prev)}")

        if tables_prev:
            print(f"Number of tables: {len(tables_prev)}")
            if len(tables_prev) > 0 and hasattr(tables_prev[0], 'shape'):
                print(f"Table 0 shape: {tables_prev[0].shape}")
        else:
            print(">>> Previous season also returned no data <<<")

    except Exception as e:
        print(f"\n>>> ERROR: {type(e).__name__}: {e} <<<")

if __name__ == '__main__':
    test_league_tables()
