import os
import psycopg2
from urllib.parse import urlparse

def test_railway_connection():
    """Test direct connection to Railway PostgreSQL database"""

    # Railway DATABASE_URL from environment
    database_url = "postgresql://postgres:vdKkkPzLDNpflqQukOXEGQGgKZNNbFtH@postgres.railway.internal:5432/railway"

    print(f"Testing connection to: {database_url}")

    try:
        # Parse the URL
        parsed = urlparse(database_url)
        print(f"Host: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path[1:]}")  # Remove leading slash
        print(f"Username: {parsed.username}")

        # Attempt connection
        print("\nAttempting connection...")
        conn = psycopg2.connect(database_url)

        print("✓ Connection successful!")

        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players;")
        player_count = cursor.fetchone()[0]
        print(f"✓ Players in database: {player_count}")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"✗ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_public_url():
    """Test connection using public URL (backup approach)"""

    # Try to construct public URL - you'll need to get this from Railway dashboard
    print("\n" + "="*50)
    print("PUBLIC URL TEST (if internal fails)")
    print("="*50)
    print("You'll need to get the public DATABASE_URL from Railway dashboard")
    print("It should look like: postgresql://postgres:password@hostname.railway.app:port/railway")

if __name__ == "__main__":
    print("Railway PostgreSQL Connection Test")
    print("="*40)

    success = test_railway_connection()

    if not success:
        test_public_url()
        print("\nNext steps if connection fails:")
        print("1. Check Railway dashboard for PostgreSQL service status")
        print("2. Verify the service is deployed and running")
        print("3. Check if DATABASE_URL variable is correctly set in your app")
        print("4. Try using the public DATABASE_URL as a temporary workaround")