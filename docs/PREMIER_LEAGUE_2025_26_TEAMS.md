# Premier League 2025-26 Season Teams

**IMPORTANT**: This document lists the definitive 20 teams in the Premier League for the 2025-26 season. Do not make assumptions about team participation without referencing this list.

## Official 2025-26 Premier League Teams

| Team Name | 3-Letter Code | Notes |
|-----------|---------------|-------|
| Arsenal | ARS | |
| Aston Villa | AVL | |
| Bournemouth | BOU | |
| Brentford | BRE | |
| Brighton & Hove Albion | BHA | |
| Burnley | BUR | |
| Chelsea | CHE | |
| Crystal Palace | CRY | |
| Everton | EVE | |
| Fulham | FUL | |
| Leeds United | LEE | ⚠️ Back in Premier League |
| Liverpool | LIV | |
| Manchester City | MCI | |
| Manchester United | MUN | |
| Newcastle United | NEW | |
| Nottingham Forest | NFO | |
| Sunderland | SUN | ⚠️ Back in Premier League |
| Tottenham Hotspur | TOT | |
| West Ham United | WHU | |
| Wolverhampton Wanderers | WOL | |

## Important Notes

- **Leeds United** and **Sunderland** are both in the 2025-26 Premier League
- **Total teams**: 20 (standard Premier League format)
- **Source**: [2025-26 Premier League Wikipedia](https://en.wikipedia.org/wiki/2025%E2%80%9326_Premier_League)
- **Last Updated**: August 16, 2025

## For Developers

**DO NOT** make assumptions about which teams are in the Premier League based on historical data. Always reference this document for the current 2025-26 season teams.

When processing team data:
1. Use the 3-letter codes provided above
2. Include ALL 20 teams listed
3. Do not filter out any teams as "non-Premier League"

## Team Code Mapping for CSV Import

```python
TEAM_MAPPING_2025_26 = {
    'Arsenal': 'ARS',
    'Aston Villa': 'AVL', 
    'Bournemouth': 'BOU',
    'Brentford': 'BRE',
    'Brighton and Hove Albion': 'BHA',
    'Burnley': 'BUR',
    'Chelsea': 'CHE',
    'Crystal Palace': 'CRY',
    'Everton': 'EVE',
    'Fulham': 'FUL',
    'Leeds United': 'LEE',
    'Liverpool': 'LIV',
    'Manchester City': 'MCI',
    'Manchester United': 'MUN',
    'Newcastle United': 'NEW',
    'Nottingham Forest': 'NFO',
    'Sunderland': 'SUN',
    'Tottenham Hotspur': 'TOT',
    'West Ham United': 'WHU',
    'Wolverhampton Wanderers': 'WOL'
}
```