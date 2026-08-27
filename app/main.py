import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .github import router as github_router
from .tiktok import router as tiktok_router
from .instagram import router as instagram_router
from .twitter import router as twitter_router
from .youtube import router as youtube_router
from .discord import router as discord_router

app = FastAPI(
    title="OSINT Website - GitHub Module",
    description="GitHub OSINT starter pack. Hostable on Railway.app. No auth required for 60 req/hr, add GITHUB_TOKEN env for 5000/hr.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github_router)
app.include_router(tiktok_router)
app.include_router(instagram_router)
app.include_router(twitter_router)
app.include_router(youtube_router)
app.include_router(discord_router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "modules": ["github", "tiktok", "instagram", "twitter", "youtube", "discord"]}

@app.get("/api/modules")
async def modules():
    return {
        "available": [
            {"id": "github", "name": "GitHub OSINT", "status": "active", "endpoints": 7},
            {"id": "tiktok", "name": "TikTok OSINT", "status": "active", "endpoints": 3},
            {"id": "instagram", "name": "Instagram OSINT", "status": "active", "endpoints": 2},
            {"id": "twitter", "name": "Twitter/X OSINT", "status": "active", "endpoints": 2},
            {"id": "youtube", "name": "YouTube OSINT", "status": "active", "endpoints": 3},
            {"id": "discord", "name": "Discord OSINT", "status": "active", "endpoints": 3},
        ]
    }

# Serve frontend static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
static_dir = os.path.abspath(static_dir)

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
