# Database Access Credentials

## PostgreSQL Connection Details

**Database**: `fantrax_value_hunter`  
**Host**: `localhost`  
**Port**: `5433`

## User Accounts

### fantrax_user (Standard Application User)
- **Username**: `fantrax_user`
- **Password**: `fantrax_password`
- **Permissions**: Owner of all application tables
- **Usage**: Standard application operations, migrations

### postgres (Superuser - Admin Only)
- **Username**: `postgres`  
- **Password**: `Password`
- **Permissions**: Database superuser
- **Usage**: Administrative tasks, permission changes, emergency access

## Connection Methods

### Command Line (psql)
```bash
# Application user
psql.exe -h localhost -p 5433 -U fantrax_user -d fantrax_value_hunter -W

# Admin user  
psql.exe -h localhost -p 5433 -U postgres -d fantrax_value_hunter -W
```

### Python Application
```python
# Standard connection
conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='fantrax_user',
    password='fantrax_password', 
    database='fantrax_value_hunter'
)

# Admin connection (emergency only)
admin_conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='postgres',
    password='Password',
    database='fantrax_value_hunter'
)
```

## Notes

- PostgreSQL 17 installation location: `C:\Program Files\PostgreSQL\17\bin`
- All application tables now owned by `fantrax_user` after permission fix
- Formula Optimization v2.0 migration completed successfully on 2025-08-21
- 647 players in database with v2.0 schema (true_value, roi, exponential_form_score columns added)
- Data type handling fixed for Decimal/float compatibility
- Unicode encoding: Use Windows Terminal or `set PYTHONIOENCODING=utf-8` to avoid emoji errors

## Security

⚠️ **Keep this file secure** - contains database passwords  
📝 **Last updated**: 2025-08-21 after v2.0 migration success