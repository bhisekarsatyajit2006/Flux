import sys
import os

# Add the project root and backend folder to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from backend.main import app

# Handler for Vercel
# Vercel detects the 'app' variable in index.py for Python runtimes
