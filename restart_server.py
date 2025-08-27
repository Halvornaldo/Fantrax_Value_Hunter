#!/usr/bin/env python3
"""
Server Management Script
Fantasy Football Value Hunter

This script helps manage the Flask server to prevent caching issues
when code changes are made to calculation engines or other modules.
"""

import os
import sys
import subprocess
import time
import requests
import psutil

def kill_flask_servers():
    """Kill any running Flask servers on port 5001"""
    print("🔍 Checking for running Flask servers...")
    
    killed_any = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'app.py' in cmdline and '5001' in cmdline:
                    print(f"🔪 Killing Flask server (PID: {proc.info['pid']})")
                    proc.kill()
                    killed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_any:
        print("⏳ Waiting for processes to terminate...")
        time.sleep(2)
    else:
        print("✅ No Flask servers found running")

def start_server():
    """Start the Flask server"""
    print("🚀 Starting fresh Flask server...")
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Start the server
    subprocess.Popen([sys.executable, 'src/app.py'], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    for i in range(10):
        try:
            response = requests.get('http://localhost:5001/api/health', timeout=2)
            if response.status_code == 200:
                print("✅ Server started successfully!")
                print("🌐 Available at: http://localhost:5001")
                return True
        except:
            pass
        time.sleep(1)
        print(f"   Attempt {i+1}/10...")
    
    print("❌ Failed to start server")
    return False

def main():
    """Main restart function"""
    print("🔄 Restarting Fantrax Value Hunter Server...")
    print("   This prevents calculation engine caching issues")
    print()
    
    # Kill existing servers
    kill_flask_servers()
    
    # Start new server
    if start_server():
        print()
        print("🎉 Server restart complete!")
        print("💡 TIP: The server now has auto-reload enabled")
        print("   Future code changes should auto-restart the server")
    else:
        print("❌ Server restart failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())