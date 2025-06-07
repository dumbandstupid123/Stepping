#!/usr/bin/env python3
"""
NextStep Healthcare Assistant - Web Application Launcher
Run this to start the beautiful web interface.
"""

import os
import sys
import subprocess
import time
import webbrowser
from threading import Timer

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'sentence_transformers', 
        'astrapy', 'openai', 'numpy', 'pandas'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n🚨 Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies ready!")
    return True

def check_database_connection():
    """Check if database connection works."""
    print("\n🔍 Checking database connection...")
    
    try:
        from nextstep_assistant import NextStepAssistant
        assistant = NextStepAssistant()
        
        # Test connection
        resources = assistant.db.get_all_resources()
        print(f"  ✅ Connected to DataStax Astra DB")
        print(f"  📊 Found {len(resources)} resources")
        assistant.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        print("  💡 Check your .env file and DataStax credentials")
        return False

def open_browser(url, delay=3):
    """Open browser after a short delay."""
    time.sleep(delay)
    print(f"🌐 Opening {url} in your browser...")
    webbrowser.open(url)

def main():
    """Main launcher function."""
    print("🏥 NextStep Healthcare Assistant")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database_connection():
        print("\n⚠️  Warning: Database connection failed, but starting anyway...")
        print("   Some features may not work properly.")
    
    # Create static directory if needed
    os.makedirs("static", exist_ok=True)
    
    print("\n🚀 Starting NextStep web application...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Schedule browser opening
    timer = Timer(3.0, open_browser, ["http://localhost:8000"])
    timer.start()
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 NextStep server stopped. Thank you!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 