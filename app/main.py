import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .github import router as github_router

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

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "modules": ["github"]}

@app.get("/api/modules")
async def modules():
    return {
        "available": [
            {"id": "github", "name": "GitHub OSINT", "status": "active", "endpoints": 7},
            {"id": "instagram", "name": "Instagram OSINT", "status": "planned"},
            {"id": "domain", "name": "Domain OSINT", "status": "planned"},
            {"id": "email", "name": "Email OSINT", "status": "planned"},
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
        # fallback for SPA - serve index if file not found, but keep /api routes
        if full_path.startswith("api/"):
            return {"error": "not found"}
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
