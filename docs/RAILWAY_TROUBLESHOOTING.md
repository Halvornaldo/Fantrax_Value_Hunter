# Railway Troubleshooting & Advanced Configuration

## Common Issues & Solutions

### 1. Build Failures

#### npm ci Error (Missing package-lock.json)
**Error**: `npm ci can only install with an existing package-lock.json`

**Solution**: Already handled in Dockerfile with fallback strategy:
```dockerfile
RUN if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund; \
    else \
        npm install --no-audit --no-fund; \
    fi
```

#### Docker Build Context Issues
**Error**: Files not found during COPY commands

**Check**: Ensure `.dockerignore` isn't excluding required files:
- `frontend/package.json` ✅ Not excluded
- `frontend/package-lock.json` ✅ Not excluded
- `requirements.txt` ✅ Not excluded

### 2. Database Issues

#### Connection Timeouts
**Error**: App hangs on startup or `psycopg2.OperationalError`

**Solution**: Connection timeout already configured in `app.py`:
```python
connection_params = {
    'connect_timeout': 10,
    'sslmode': 'prefer',
    'options': '-c statement_timeout=30000'
}
```

#### Database Not Initializing
**Error**: Empty database or tables missing

**Check**: Startup logs for initialization process:
```bash
railway logs --tail

# Look for:
# "✅ Database initialization completed successfully!"
# "✅ Loaded 717 players"
```

**Manual Fix**: Force reinitialization by redeployment:
```bash
railway up --service fantrax-dashboard-production
```

#### Character Encoding Issues
**Error**: Special characters (López, André) display incorrectly

**Solution**: Already fixed in `startup_with_db_init.py`:
```python
with open(dump_file, 'r', encoding='latin-1') as f:
```

### 3. Frontend Issues

#### API Connection Errors
**Error**: Frontend can't connect to backend (localhost:5001 errors)

**Solution**: Smart Railway detection already implemented:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL ||
  (window.location.origin.includes('railway.app') ?
    window.location.origin : "http://localhost:5001")
```

#### Cache Issues (Old React Code)
**Error**: Changes not visible despite successful deployment

**Verify**: Check for new JavaScript hash in logs:
```
✅ React build complete - Generated files:
main.7ff39aae.js  # Should be different each deployment
```

**Solution**: Docker deployment with cache-busting should prevent this.

### 4. Deployment Issues

#### Railway Not Detecting Pushes
**Error**: `git push` doesn't trigger deployment

**Solution**: Ensure directory is linked to correct project:
```bash
railway link -p fantrax-dashboard-production
```

#### Railway.toml vs Railway.json Conflicts
**Error**: Wrong builder being used

**Solution**: Remove `railway.toml` if present (railway.json takes precedence):
```bash
rm railway.toml  # Keep only railway.json
```

## Advanced Configuration

### Environment Variables

#### Required (Auto-Generated)
```bash
DATABASE_URL=postgresql://postgres:PASSWORD@centerbeam.proxy.rlwy.net:16207/railway
RAILWAY_DEPLOYMENT_ID=unique-deployment-id
PORT=8080
```

#### Optional
```bash
# Override API URL detection
REACT_APP_API_BASE_URL=https://your-custom-domain.railway.app

# Flask environment
FLASK_ENV=production
FLASK_DEBUG=false

# Database public URL (if needed for UI)
DATABASE_PUBLIC_URL=$DATABASE_URL
```

### Docker Build Optimization

#### Current Multi-Stage Strategy
```dockerfile
# Stage 1: Build React (Node.js)
FROM node:18-alpine AS frontend-builder
# ... React build process

# Stage 2: Python Flask + copy React build
FROM python:3.11-slim
# ... Flask setup + COPY from frontend-builder
```

#### Build Arguments
```json
{
  "buildArgs": {
    "CACHEBUST": "${{RAILWAY_DEPLOYMENT_ID}}"
  }
}
```

### Database Connection Advanced Settings

#### Railway PostgreSQL Specifics
- **TCP Proxy**: Enabled (required for external access)
- **SSL Mode**: `prefer` (Railway handles SSL termination)
- **Connection Pooling**: Not needed (single app instance)
- **Backup**: Railway handles automatic backups

#### Connection String Format
```
postgresql://postgres:PASSWORD@HOST:PORT/railway
```

#### Query Optimization
```python
# Statement timeout for long queries
'options': '-c statement_timeout=30000'  # 30 seconds
```

## Monitoring & Debugging

### Essential Commands

#### Check Service Status
```bash
railway status
```

#### View Real-Time Logs
```bash
railway logs --tail
```

#### Check Environment Variables
```bash
railway vars
```

#### Test Database Connection
```bash
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM players;"
```

### Health Check Endpoints

#### Application Health
```bash
curl https://your-app.railway.app/health
```

#### Database Health
Check logs for:
```
✅ Database connection successful
✅ All tables verified
✅ Player count: 717
```

### Performance Monitoring

#### Key Metrics to Watch
- **Startup Time**: Should be under 30 seconds
- **Memory Usage**: ~200-300MB typical
- **Response Time**: 2-3 seconds for dashboard load
- **Database Queries**: Should complete under 5 seconds

#### Log Analysis
Look for patterns:
```bash
# Successful deployments
grep "✅" logs.txt

# Connection issues
grep "timeout\|connection" logs.txt

# Database errors
grep "psycopg2\|postgresql" logs.txt
```

## Emergency Procedures

### Complete Service Recovery
```bash
# 1. Check service status
railway status

# 2. View recent logs
railway logs --tail -n 100

# 3. Force redeploy
railway up --service fantrax-dashboard-production

# 4. Monitor startup
railway logs --tail
```

### Database Recovery
```bash
# Check if database exists
railway run psql $DATABASE_URL -c "\dt"

# If empty, redeploy to trigger auto-initialization
railway up --service fantrax-dashboard-production
```

### Rollback Procedure
Railway doesn't have built-in rollback, but you can:
1. Identify last working deployment ID in logs
2. Redeploy from working git commit
3. Monitor logs during recovery

## Best Practices

### Before Deployment
- ✅ Test locally with same database structure
- ✅ Verify all environment variables
- ✅ Check Docker build locally if possible
- ✅ Review recent changes in git

### During Deployment
- ✅ Monitor logs during build process
- ✅ Watch for React build completion
- ✅ Verify database initialization
- ✅ Check for new JavaScript hash

### After Deployment
- ✅ Test dashboard loads correctly
- ✅ Verify player count (717 expected)
- ✅ Check special characters display properly
- ✅ Test key features (filters, calculations)

### Regular Maintenance
- ✅ Monitor Railway service health
- ✅ Keep local codebase in sync
- ✅ Review logs periodically for issues
- ✅ Update dependencies when needed

---

**Last Updated**: January 2025
**For**: Docker-based Railway Deployment
**Active Project**: fantrax-dashboard-production