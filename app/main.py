import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .scan import router as scan_router
from .tools import router as tools_router

app = FastAPI(title="OSINT Hub", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(scan_router)
app.include_router(tools_router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    @app.get("/")
    async def index():
        return FileResponse(os.path.join(static_dir, "index.html"))
    @app.get("/{path:path}")
    async def spa(path: str):
        fp = os.path.join(static_dir, path)
        if path and os.path.isfile(fp):
            return FileResponse(fp)
        return FileResponse(os.path.join(static_dir, "index.html"))
