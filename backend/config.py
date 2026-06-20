import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "iq_test")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
AI_PROVIDER    = os.getenv("AI_PROVIDER", "gemini") # "gemini" or "nvidia"

FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:5500")
JWT_SECRET     = os.getenv("JWT_SECRET", "super-secret-key-change-me")
ALGORITHM      = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Test config
TOTAL_QUESTIONS = 20
TEST_DURATION_SECONDS = 1800   # 30 minutes
