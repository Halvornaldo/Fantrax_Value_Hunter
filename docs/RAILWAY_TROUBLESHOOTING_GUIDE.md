# Railway Deployment - Critical Fixes & Troubleshooting Guide

**Date**: September 2025
**Success**: 717 players successfully deployed to Railway
**Database**: 12 tables, all data preserved including special characters

## 🚨 Critical Issues & Solutions

### 1. Database Encoding Problems

**Problem**: Special characters (López, Füllkrug, André) causing encoding errors
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3
```

**✅ Solution**: Change encoding in `src/init_database.py`
```python
# BEFORE (broken):
with open(dump_file, 'r', encoding='utf-8') as f:

# AFTER (works):
with open(dump_file, 'r', encoding='latin-1') as f:
```

**Why**: Player names contain special characters that need latin-1 encoding for PostgreSQL compatibility.

### 2. Missing PostgreSQL Sequences

**Problem**: `nextval('name_mappings_id_seq')` sequences don't exist on Railway
```
ERROR: relation 'name_mappings_id_seq' does not exist
```

**✅ Solution**: Replace all sequence references with SERIAL PRIMARY KEY
```sql
# BEFORE (broken):
id INTEGER NOT NULL DEFAULT nextval('name_mappings_id_seq'::regclass),

# AFTER (works):
id SERIAL PRIMARY KEY,
```

**Tables affected**: 7 total sequences replaced in the SQL dump

### 3. Frontend API Connection Issues

**Problem**: React frontend trying to connect to localhost:5001 instead of Railway URL

**✅ Solution**: Smart Railway detection in `frontend/src/services/api.js`
```javascript
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL ||
  (window.location.origin.includes('railway.app') ? window.location.origin : "http://localhost:5001")
```

**Why**: Railway URLs contain 'railway.app' which we can detect automatically.

### 4. Decimal Display Inconsistency

**Problem**: Railway showing many decimals (14.006666666666668) vs local (14.010)

**✅ Solution**: Round override values in `src/app.py` line 1115
```python
# BEFORE:
'new_true_value': float(updated_player[0]) if updated_player else 0,

# AFTER:
'new_true_value': round(float(updated_player[0]), 3) if updated_player else 0,
```

## 🛠️ Deployment Process - Step by Step

### 1. Prepare Database Dump
```bash
# Create SQL dump with proper encoding
pg_dump fantrax_value_hunter \
  --clean \
  --no-owner \
  --no-privileges \
  -f railway_database_dump.sql

# Critical: Fix encoding and sequences in the dump file
python fix_railway_dump.py  # Script to fix both issues
```

### 2. Deploy Application
```bash
# Ensure these files are ready:
# - railway_database_dump.sql (with fixes)
# - src/init_database.py (latin-1 encoding)
# - src/app.py (rounded decimals)
# - frontend/build/ (with Railway API detection)

railway up
```

### 3. Monitor Deployment
```bash
railway logs --tail

# Look for success messages:
# "✅ Database initialization completed successfully!"
# "✅ Loaded 717 players"
# "✅ Created 12 tables"
```

## 📋 Verification Checklist

After deployment, verify:

- [ ] **717 players loaded** (check logs)
- [ ] **12 tables created** (not just 5)
- [ ] **Special characters preserved** (López, Füllkrug visible in dashboard)
- [ ] **All filters working** (position, team, price range)
- [ ] **Override buttons functional** (manual starter adjustments)
- [ ] **Decimal display consistent** (3 decimal places max)

## 🔧 Common Railway Issues

### Database Connection Timeouts
```python
# Already fixed in app.py
connection_params = {
    'connect_timeout': 10,
    'sslmode': 'prefer',
    'options': '-c statement_timeout=30000'
}
```

### Environment Variables Required
- `DATABASE_URL`: Automatically provided by Railway
- `REACT_APP_API_BASE_URL`: Optional (auto-detected)

### Build Issues
```bash
# If build fails, check:
railway logs --deployment DEPLOYMENT_ID

# Common fixes:
# 1. Ensure Dockerfile is correct
# 2. Check Python dependencies in requirements.txt
# 3. Verify Node.js build process for React
```

## 📊 Success Metrics

**Current Status**: ✅ SUCCESSFUL DEPLOYMENT
- **Players**: 717/717 (100%)
- **Tables**: 12/12 (100%)
- **Special Characters**: Preserved
- **Frontend**: Fully functional
- **Performance**: ~2-3 second load times

## 🔄 Future Deployments

For subsequent deployments:

1. **Use existing fixes** (encoding, sequences, API detection)
2. **Test locally first** with the same data
3. **Backup existing Railway DB** before updates
4. **Monitor logs** during deployment
5. **Verify player count** and special characters

## 📞 Emergency Recovery

If deployment fails:
```bash
# 1. Check logs first
railway logs --tail

# 2. Redeploy with last known good configuration
railway up --detach

# 3. If database corrupted, restore from backup
# (Keep backup SQL dumps for this purpose)
```

## 🎯 Key Lessons Learned

1. **Character encoding matters** - Always use latin-1 for PostgreSQL dumps with international characters
2. **Railway PostgreSQL differs** - SERIAL works better than explicit sequences
3. **Environment detection is crucial** - React apps need smart API URL detection
4. **Decimal precision consistency** - Backend rounding prevents frontend display issues
5. **Test locally with production data** - Same database state = predictable deployment

---

**This guide documents successful deployment of 717 players to Railway with all functionality preserved.**