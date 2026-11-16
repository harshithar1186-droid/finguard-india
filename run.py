"""
FinGuard India - Main Server Runner
Launches Uvicorn server with FastAPI backend and mounted responsive web dashboard.
"""

import uvicorn
import os
import sys

# Ensure current project directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    print("=" * 70)
    print("  FinGuard India — Banking Health Early Warning System")
    print("  RBI DBIE Master Dataset 2015–2024 | 112 Commercial & Scheduled Banks")
    print("=" * 70)
    print("  Server starting on: http://127.0.0.1:8000")
    print("  API Documentation:  http://127.0.0.1:8000/docs")
    print("=" * 70)
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

