"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import FRONTEND_URL
from database import connect_db, close_db
from routes.test import router as test_router
from routes.auth import router as auth_router
from routes.coding import router as coding_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="IQ Test AI",
    description="AI-powered IQ assessment platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(coding_router)
app.include_router(test_router)



# ── Serve frontend static files ───────────────────────────────────────
import os, pathlib

FRONTEND_DIR = pathlib.Path(__file__).parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/test")
    async def serve_test():
        return FileResponse(str(FRONTEND_DIR / "test.html"))

    @app.get("/result")
    async def serve_result():
        return FileResponse(str(FRONTEND_DIR / "result.html"))

    @app.get("/login")
    async def serve_login():
        return FileResponse(str(FRONTEND_DIR / "login.html"))

    @app.get("/register")
    async def serve_register():
        return FileResponse(str(FRONTEND_DIR / "register.html"))

    @app.get("/dashboard")
    async def serve_dashboard():
        return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

    @app.get("/coding")
    async def serve_coding():
        return FileResponse(str(FRONTEND_DIR / "coding.html"))

    @app.get("/prepare")
    async def serve_prepare():
        return FileResponse(str(FRONTEND_DIR / "prepare.html"))

    # fallback for assets
    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))






