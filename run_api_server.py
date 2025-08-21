#!/usr/bin/env python3
"""
Main script to run the enhanced NAI Project Planning API server
"""

import sys
import os
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    print("🚀 Starting NAI Project Planning API Server")
    print("="*50)
    print("Features:")
    print("  • Multi-user session management")
    print("  • Project-specific document storage")
    print("  • SQLite state persistence")
    print("  • Real-time collaboration")
    print()
    print("Access points:")
    print("  • API: http://localhost:8000")
    print("  • Docs: http://localhost:8000/docs")
    print("  • Frontend: http://localhost:3000 (if running)")
    print("="*50)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()