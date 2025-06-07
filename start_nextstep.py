#!/usr/bin/env python3
"""
NextStep Healthcare Assistant Startup Script
Professional Healthcare Navigator for Houston, Texas
"""

import os
import sys
import subprocess
import webbrowser
from time import sleep

def check_dependencies():
    """Check if required packages are installed."""
    print("🔍 Checking dependencies...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'sentence_transformers',
        'astrapy',
        'openai',
        'numpy',
        'pandas'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("📦 Install with: pip install", ' '.join(missing))
        return False
    
    print("✅ All dependencies ready!")
    return True

def check_environment():
    """Check environment variables."""
    print("🔍 Checking environment...")
    
    # Check for .env file
    if os.path.exists('.env'):
        print("  ✅ .env file found")
        return True
    
    # Check for environment variables
    required_env = ['ASTRA_DB_APPLICATION_TOKEN', 'ASTRA_DB_API_ENDPOINT', 'OPENAI_API_KEY']
    missing_env = []
    
    for var in required_env:
        if not os.getenv(var):
            missing_env.append(var)
    
    if missing_env:
        print(f"  ⚠️  Missing environment variables: {', '.join(missing_env)}")
        print("  📝 Create .env file with your API keys")
        return False
    
    print("  ✅ Environment configured")
    return True

def start_server():
    """Start the NextStep server."""
    print("🚀 Starting NextStep Professional Healthcare Navigator...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Change to backend directory and start server
    os.chdir('backend')
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main startup function."""
    print("🏥 NextStep Healthcare Assistant")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment (optional for demo)
    env_ok = check_environment()
    if not env_ok:
        print("⚠️  Continuing without full environment setup...")
        print("   Some features may not work without API keys")
    
    # Check if backend directory exists
    if not os.path.exists('backend'):
        print("❌ Backend directory not found!")
        print("   Make sure you're running from the project root")
        sys.exit(1)
    
    # Check if frontend directory exists
    if not os.path.exists('frontend'):
        print("❌ Frontend directory not found!")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main() 