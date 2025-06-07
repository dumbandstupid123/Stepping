#!/usr/bin/env python3
"""
NextStep Healthcare Navigator
Professional startup script
"""

import os
import sys

def main():
    """Start NextStep Healthcare Navigator"""
    print("🏥 Starting NextStep Healthcare Navigator...")
    
    # Set environment variables to fix warnings
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # Check if we're in the right directory
    if not os.path.exists("backend"):
        print("❌ Backend directory not found!")
        print("📁 Please run this script from the NextStep project root")
        sys.exit(1)
    
    # Change to backend directory where modules are located
    os.chdir("backend")
    
    print("📍 Server starting on http://localhost:8000")
    print("🛑 Press Ctrl+C to stop")
    print("--------------------------------------------------")
    
    try:
        # Start the server from backend directory
        import uvicorn
        uvicorn.run(
            "app:app",  # Use app module directly from backend directory
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 NextStep Healthcare Navigator stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main() 