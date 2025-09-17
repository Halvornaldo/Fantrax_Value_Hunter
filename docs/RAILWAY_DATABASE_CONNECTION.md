# Railway Database Connection Guide

## Connection Details

### Database URL
```
postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway
```

### Connection Parameters
- **Host**: `centerbeam.proxy.rlwy.net`
- **Port**: `16207`
- **Database**: `railway`
- **User**: `postgres`
- **Password**: `bwSnKgVZWqlCPtpYqzYAvGypxObPadTM`
- **SSL Mode**: `prefer` or `require`

## Railway Configuration Requirements

### 1. TCP Proxy Setup (CRITICAL)
The Railway database UI requires a TCP proxy to be enabled:

1. Go to your PostgreSQL service in Railway dashboard
2. Navigate to **Settings** tab
3. Under **Networking** section, find **Public Networking**
4. Ensure TCP proxy is enabled and pointing to port `5432` internally
5. This generates the public endpoint (centerbeam.proxy.rlwy.net:16207)

### 2. Environment Variables
Required variables in Railway:

```bash
# Primary database URL (already set)
DATABASE_URL=postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway

# Public URL for Railway UI (must be added)
DATABASE_PUBLIC_URL=postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway

# Flask configuration
PORT=8080
FLASK_ENV=production
FLASK_DEBUG=false
```

## Connection Testing

### From Local Machine
```bash
# Test connection (will timeout from local - this is normal)
psql "postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway"
```

Note: The Railway database is only accessible from within Railway's network, not from external locations.

### From Railway (via Railway CLI)
```bash
# Connect through Railway CLI
railway connect
# Select: Postgres service

# Or run commands directly
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM players"
```

## Python Connection

### With Timeout and SSL (REQUIRED for Railway)
```python
import psycopg2
import os

def get_railway_connection():
    """Connect to Railway PostgreSQL with proper settings"""

    DATABASE_URL = os.getenv('DATABASE_URL')

    # Parse URL
    import urllib.parse
    result = urllib.parse.urlparse(DATABASE_URL)

    # Connection parameters with Railway optimizations
    conn_params = {
        'host': result.hostname,
        'port': result.port,
        'user': result.username,
        'password': result.password,
        'database': result.path[1:],
        'connect_timeout': 10,  # CRITICAL: Prevents hanging
        'sslmode': 'prefer',    # Railway proxy SSL handling
        'options': '-c statement_timeout=30000'  # 30 second query timeout
    }

    return psycopg2.connect(**conn_params)
```

## Import/Export Commands

### Export from Local
```bash
# Full database
pg_dump fantrax_value_hunter > database.sql

# Specific tables only
pg_dump fantrax_value_hunter \
  -t players \
  -t player_metrics \
  -t team_fixtures \
  > essential_tables.sql

# Data only (structure exists)
pg_dump fantrax_value_hunter --data-only > data_only.sql
```

### Import to Railway
```bash
# Set environment variable
export DATABASE_URL="postgresql://postgres:bwSnKgVZWqlCPtpYqzYAvGypxObPadTM@centerbeam.proxy.rlwy.net:16207/railway"

# Import full database
psql $DATABASE_URL < database.sql

# Or use Railway CLI
railway run psql $DATABASE_URL < database.sql
```

## Common Issues and Solutions

### Issue: Database UI Stuck Loading
**Cause**: Missing TCP proxy or DATABASE_PUBLIC_URL
**Solution**:
1. Enable TCP proxy in Railway settings
2. Add DATABASE_PUBLIC_URL environment variable
3. Redeploy service

### Issue: Connection Timeout from Local
**Cause**: Railway database only accessible within Railway network
**Solution**: This is normal - use Railway CLI or deploy app to test

### Issue: App Hangs on Startup
**Cause**: No connection timeout specified
**Solution**: Already fixed in app.py with 10-second timeout

### Issue: SSL Connection Error
**Cause**: Incorrect SSL mode
**Solution**: Use `sslmode='prefer'` not `'require'`

## Verification Commands

### Check if Tables Exist
```sql
-- Run via Railway CLI
railway run psql $DATABASE_URL -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema='public'
ORDER BY table_name;"
```

### Check Player Count
```sql
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM players;"
```

### Check Database Size
```sql
railway run psql $DATABASE_URL -c "
SELECT pg_database_size('railway')/1024/1024 as size_mb;"
```

## Best Practices

1. **Always use timeouts** in connection parameters
2. **Test locally with Railway CLI** before deploying
3. **Keep backups** before major imports
4. **Use transactions** for data imports
5. **Monitor logs** after deployment: `railway logs`

---

*Last Updated: January 2025*
*Connection verified and working with timeout fixes applied*