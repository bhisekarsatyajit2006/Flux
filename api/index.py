# Small ASGI shim to expose the FastAPI app to Vercel
import sys
import os

# Ensure backend package is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

from backend.main import app  # FastAPI instance

# For local dev: `uvicorn api.index:app --reload --port 8000`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
