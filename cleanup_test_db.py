#!/usr/bin/env python3
"""
Script to manually clean up test database connections and drop the test database.
Use this when you encounter "database is being accessed by other users" errors.
"""

import os
import subprocess
import sys
import time

def cleanup_test_database():
    """Clean up test database by terminating connections and dropping it."""
    
    # Get database connection info from environment
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "adlab")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    db_name = os.getenv("POSTGRES_DB", "adlab")
    test_db_name = f"test_{db_name}"
    
    print(f"🧹 Cleaning up test database: {test_db_name}")
    
    # Set up environment
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    
    try:
        # Step 1: Terminate all connections to the test database
        print("1. Terminating connections to test database...")
        terminate_cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", "postgres",
            "-c", f"""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = '{test_db_name}' 
            AND pid <> pg_backend_pid();
            """,
        ]
        
        result = subprocess.run(
            terminate_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            print("   ✅ Connections terminated")
        else:
            print(f"   ⚠️  Warning: {result.stderr}")
        
        # Step 2: Wait for connections to close
        print("2. Waiting for connections to close...")
        time.sleep(2)
        
        # Step 3: Drop the test database
        print("3. Dropping test database...")
        drop_cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", "postgres",
            "-c", f'DROP DATABASE IF EXISTS "{test_db_name}";',
        ]
        
        result = subprocess.run(
            drop_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            print(f"   ✅ Test database '{test_db_name}' dropped successfully")
        else:
            print(f"   ❌ Error dropping database: {result.stderr}")
            return False
            
        print("🎉 Test database cleanup completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout while cleaning up test database")
        return False
    except FileNotFoundError:
        print("❌ psql command not found. Make sure PostgreSQL client is installed.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = cleanup_test_database()
    sys.exit(0 if success else 1)
