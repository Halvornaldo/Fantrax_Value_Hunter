# Railway Deployment Guide - Fantrax Value Hunter

## Current System Overview

**Active Project**: `fantrax-dashboard-production` on Railway
**Deployment Method**: Docker (multi-stage build)
**Database**: Railway PostgreSQL with auto-initialization
**Status**: ✅ Successfully deployed with 717 players

## Quick Deploy

```bash
# Deploy updates to Railway
railway up --service fantrax-dashboard-production
```

## Docker Deployment Architecture

### Multi-Stage Build Process
The current deployment uses a **Docker multi-stage build** that completely bypasses Railway's Nixpacks caching issues:

1. **Stage 1**: Build React frontend with cache-busting
2. **Stage 2**: Build Python Flask backend with fresh React assets

### Key Files
- `Dockerfile` - Multi-stage build configuration
- `railway.json` - Forces Docker builder with cache-busting
- `startup_with_db_init.py` - Auto-initializes database on startup

### Docker Configuration
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "./Dockerfile",
    "buildArgs": {
      "CACHEBUST": "${{RAILWAY_DEPLOYMENT_ID}}"
    }
  }
}
```

## Database Configuration

### Connection Details
- **Host**: `centerbeam.proxy.rlwy.net`
- **Port**: `16207`
- **Database**: `railway`
- **Auto-Initialize**: Yes (717 players loaded on startup)

### Required Environment Variables
Railway automatically provides:
- `DATABASE_URL` - Primary connection string
- `RAILWAY_DEPLOYMENT_ID` - Used for cache-busting

### Connection Features
- **Timeout Protection**: 10-second connection timeout
- **SSL Support**: `sslmode=prefer`
- **Query Timeout**: 30-second statement timeout
- **Auto-Recovery**: Database recreated if missing

## Deployment Process

### 1. Deploy Updates
```bash
# From project root
railway up --service fantrax-dashboard-production
```

### 2. Monitor Deployment
```bash
# Watch deployment logs
railway logs --tail

# Look for success indicators:
# "✅ Database initialization completed successfully!"
# "✅ Loaded 717 players"
# "React build complete - Generated files"
```

### 3. Verify Deployment
Check these after deployment:
- [ ] Dashboard loads (typically 2-3 second load time)
- [ ] 717 players visible
- [ ] Fresh React assets (new JavaScript hash in filename)
- [ ] All filters and features working
- [ ] Special characters preserved (López, Füllkrug, André)

## Cache-Proof Features

### Why Docker Deployment?
The Docker approach completely solves Railway's aggressive caching that was preventing fresh React builds from deploying.

### Cache-Busting Mechanisms
1. **Build Argument**: `CACHEBUST=${{RAILWAY_DEPLOYMENT_ID}}`
2. **Fresh React Build**: New JavaScript hash every deployment
3. **Docker Layer Optimization**: Strategic file copying for cache efficiency

### Verification of Fresh Builds
Look for new JavaScript filenames in logs:
```
✅ React build complete - Generated files:
main.7ff39aae.js  # New hash = fresh build
```

## Troubleshooting

### Build Failures
If deployment fails:
```bash
# Check build logs
railway logs --deployment DEPLOYMENT_ID

# Common issue: Missing package-lock.json
# Solution: Already handled with fallback to npm install
```

### App Won't Start
```bash
# Check startup logs
railway logs --tail

# Verify environment variables
railway vars

# Force redeploy
railway up --service fantrax-dashboard-production
```

### Database Issues
```bash
# Check database connection
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM players;"

# Expected output: 717 players
```

## Performance & Features

### What Friends Get
✅ **Full Dashboard Access**
- All 717 players with complete metrics
- True Value and ROI calculations
- Sorting, filtering, and CSV export
- Mobile-responsive interface

✅ **Read-Only Stability**
- No parameter editing (prevents conflicts)
- Consistent calculations
- Fast load times

### Performance Metrics
- **Load Time**: 2-3 seconds
- **Uptime**: 99%+ (Railway infrastructure)
- **Data Freshness**: Updated when you deploy
- **Maintenance**: ~5 minutes per deployment

## Maintenance Workflow

### Weekly Process (Optional)
1. **Update Local Data** (if needed)
   - Import new player data
   - Update fixtures and odds
   - Verify calculations locally

2. **Deploy to Railway**
   ```bash
   railway up --service fantrax-dashboard-production
   ```

3. **Verify Online**
   - Check dashboard loads correctly
   - Verify player count and data

### Emergency Recovery
If deployment fails:
```bash
# Redeploy last working version
railway up --service fantrax-dashboard-production

# Check service status
railway status
```

## Migration Notes

### From Previous Setup
- ✅ **Nixpacks Disabled**: Docker deployment bypasses Nixpacks entirely
- ✅ **Cache Issues Resolved**: Fresh builds guaranteed every time
- ✅ **Auto-Database**: No manual database setup required
- ✅ **Simplified Process**: Single command deployment

### File Changes Made
- Created `Dockerfile` (multi-stage build)
- Created `railway.json` (forces Docker)
- Updated `startup_with_db_init.py` (auto-initialization)
- Removed `railway.toml` (conflicted with railway.json)

---

**Last Updated**: January 2025
**Deployment Method**: Docker Multi-Stage Build
**Status**: ✅ Production Ready
**Active Project**: fantrax-dashboard-production