"""
Startup script for the Semantic Modeling Assistant API.

Run this script to start the FastAPI server:
    python run_api.py

Or use uvicorn directly:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
