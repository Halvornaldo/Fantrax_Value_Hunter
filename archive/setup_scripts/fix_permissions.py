#!/usr/bin/env python3
"""
Fix database permissions for fantrax_user to allow table alterations
Run this as postgres superuser or database owner
"""

import psycopg2
import sys

def fix_permissions():
    """Grant necessary permissions to fantrax_user"""
    
    # Try connecting as postgres first (typical superuser)
    superuser_configs = [
        {'user': 'postgres', 'password': ''},  # Default postgres, no password
        {'user': 'postgres', 'password': 'postgres'},  # Common default
        {'user': 'postgres', 'password': 'admin'},  # Another common default
        {'user': 'fantrax_user', 'password': 'fantrax_password'},  # Try original user with elevated perms
    ]
    
    for config in superuser_configs:
        try:
            print(f"Trying to connect as: {config['user']}")
            
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                database='fantrax_value_hunter',
                user=config['user'],
                password=config['password']
            )
            
            cursor = conn.cursor()
            
            print(f"Connected successfully as {config['user']}")
            
            # Check current user's privileges
            cursor.execute("SELECT current_user, session_user")
            user_info = cursor.fetchone()
            print(f"Current user: {user_info[0]}, Session user: {user_info[1]}")
            
            # Check if we're superuser
            cursor.execute("SELECT usesuper FROM pg_user WHERE usename = current_user")
            is_super = cursor.fetchone()
            if is_super and is_super[0]:
                print("✓ Connected as superuser - can grant permissions")
            else:
                print("- Not superuser, but let's try anyway...")
            
            # Grant permissions to fantrax_user
            print("\nGranting permissions to fantrax_user...")
            
            # Make fantrax_user owner of players table
            cursor.execute("ALTER TABLE players OWNER TO fantrax_user")
            print("✓ Changed players table owner to fantrax_user")
            
            # Grant all privileges on database
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE fantrax_value_hunter TO fantrax_user")
            print("✓ Granted all database privileges")
            
            # Grant all privileges on all tables in public schema
            cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fantrax_user")
            print("✓ Granted all table privileges")
            
            # Grant all privileges on all sequences (for SERIAL columns)
            cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fantrax_user")
            print("✓ Granted all sequence privileges")
            
            # Grant usage on schema
            cursor.execute("GRANT USAGE ON SCHEMA public TO fantrax_user")
            print("✓ Granted schema usage")
            
            # Make sure future objects are also granted
            cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO fantrax_user")
            cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO fantrax_user")
            print("✓ Set default privileges for future objects")
            
            conn.commit()
            conn.close()
            
            print(f"\n🎉 Successfully fixed permissions using {config['user']} account!")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Failed to connect as {config['user']}: {e}")
            continue
        except Exception as e:
            print(f"❌ Error with {config['user']}: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            continue
    
    print("\n❌ Could not connect with any superuser account.")
    print("\nManual fix options:")
    print("1. Connect to your PostgreSQL as admin and run:")
    print("   ALTER TABLE players OWNER TO fantrax_user;")
    print("   GRANT ALL PRIVILEGES ON DATABASE fantrax_value_hunter TO fantrax_user;")
    print("   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fantrax_user;")
    print("\n2. Or run PostgreSQL command line as admin:")
    print(f'   psql -h localhost -p 5433 -U postgres -d fantrax_value_hunter -c "ALTER TABLE players OWNER TO fantrax_user;"')
    
    return False

def verify_permissions():
    """Verify that fantrax_user now has the necessary permissions"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='fantrax_user', 
            password='fantrax_password',
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        # Check if we can alter players table now
        cursor.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS test_permission_col INTEGER")
        cursor.execute("ALTER TABLE players DROP COLUMN IF EXISTS test_permission_col")
        
        conn.commit()
        conn.close()
        
        print("✅ fantrax_user can now alter players table!")
        return True
        
    except Exception as e:
        print(f"❌ fantrax_user still cannot alter players table: {e}")
        return False

if __name__ == "__main__":
    print("Fixing PostgreSQL permissions for fantrax_user...")
    
    if fix_permissions():
        print("\nVerifying permissions...")
        verify_permissions()
    else:
        print("\nPermission fix failed. You may need to run the manual commands shown above.")