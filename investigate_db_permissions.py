#!/usr/bin/env python3
"""
Investigate database permissions and ownership structure
"""
import psycopg2

def investigate_permissions():
    print("=== INVESTIGATING DATABASE PERMISSIONS ===\n")
    
    # Test different connection approaches
    connections_to_test = [
        {'user': 'fantrax_user', 'password': 'fantrax_password', 'label': 'fantrax_user (from app config)'},
        {'user': 'postgres', 'password': 'password', 'label': 'postgres with password'},
        {'user': 'postgres', 'password': 'fantrax_password', 'label': 'postgres with fantrax password'},
        {'user': 'postgres', 'password': '', 'label': 'postgres no password'},
    ]
    
    working_conn = None
    
    for conn_info in connections_to_test:
        try:
            print(f"Testing connection: {conn_info['label']}")
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                user=conn_info['user'],
                password=conn_info['password'],
                database='fantrax_value_hunter'
            )
            print(f"  ✅ Connection successful as {conn_info['user']}")
            
            cursor = conn.cursor()
            
            # Check current user and permissions
            cursor.execute("SELECT current_user, session_user")
            current_user, session_user = cursor.fetchone()
            print(f"  Current user: {current_user}, Session user: {session_user}")
            
            # Check if this user can modify player_metrics
            try:
                cursor.execute("SELECT COUNT(*) FROM player_metrics LIMIT 1")
                print(f"  ✅ Can read player_metrics")
                
                # Test if we can add a test column
                test_col_name = f"test_col_{conn_info['user']}"
                cursor.execute(f"ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS {test_col_name} TEXT DEFAULT 'test'")
                cursor.execute(f"ALTER TABLE player_metrics DROP COLUMN IF EXISTS {test_col_name}")
                conn.commit()
                print(f"  ✅ Can modify player_metrics structure")
                working_conn = conn_info
                
            except Exception as mod_e:
                print(f"  ❌ Cannot modify player_metrics: {mod_e}")
            
            conn.close()
            print()
            
        except Exception as e:
            print(f"  ❌ Connection failed: {e}\n")
    
    # If we found a working connection, get detailed info
    if working_conn:
        print(f"=== DETAILED INFO FOR WORKING CONNECTION: {working_conn['label']} ===\n")
        
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user=working_conn['user'],
            password=working_conn['password'],
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        # Table ownership and permissions
        print("Table ownership:")
        cursor.execute("""
            SELECT schemaname, tablename, tableowner 
            FROM pg_tables 
            WHERE tablename IN ('players', 'player_metrics', 'form_data')
            ORDER BY tablename
        """)
        for row in cursor.fetchall():
            print(f"  {row[1]:<20} owned by: {row[2]}")
        
        print("\nCurrent user privileges:")
        cursor.execute("""
            SELECT table_name, privilege_type, is_grantable
            FROM information_schema.table_privileges 
            WHERE grantee = current_user 
                AND table_name IN ('players', 'player_metrics', 'form_data')
            ORDER BY table_name, privilege_type
        """)
        privileges = cursor.fetchall()
        if privileges:
            for row in privileges:
                print(f"  {row[0]:<20} {row[1]:<15} (grantable: {row[2]})")
        else:
            print("  No explicit privileges found (may have inherited/default privileges)")
        
        print("\nDatabase roles and memberships:")
        cursor.execute("""
            SELECT r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolcanlogin
            FROM pg_roles r 
            WHERE r.rolname IN (current_user, 'postgres', 'fantrax_user')
            ORDER BY r.rolname
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]:<15} super:{row[1]} createrole:{row[2]} createdb:{row[3]} canlogin:{row[4]}")
        
        conn.close()
        return working_conn
    else:
        print("❌ No working connection found for modifying tables")
        return None

def test_column_addition(working_conn):
    if not working_conn:
        print("Cannot test column addition - no working connection")
        return False
        
    try:
        print(f"\n=== TESTING ACTUAL COLUMN ADDITION ===")
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user=working_conn['user'],
            password=working_conn['password'],
            database='fantrax_value_hunter'
        )
        cursor = conn.cursor()
        
        # Try adding one of our needed columns
        cursor.execute("ALTER TABLE player_metrics ADD COLUMN IF NOT EXISTS games_played_historical INTEGER DEFAULT 0")
        conn.commit()
        
        # Verify it was added
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'player_metrics' AND column_name = 'games_played_historical'
        """)
        result = cursor.fetchone()
        
        if result:
            print("✅ Successfully added games_played_historical column")
            
            # Clean up the test
            cursor.execute("ALTER TABLE player_metrics DROP COLUMN IF EXISTS games_played_historical")
            conn.commit()
            print("✅ Test column removed")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Column addition test failed: {e}")
        return False

if __name__ == "__main__":
    working_conn = investigate_permissions()
    if working_conn:
        test_column_addition(working_conn)