import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from web.backend.routers import leaderboard, stats, bookings

app = FastAPI(title="Команда API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leaderboard.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "komanda-web"}


# Serve Vue frontend in production
_DIST = os.path.join(os.path.dirname(__file__), "../../web/frontend/dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        return FileResponse(os.path.join(_DIST, "index.html"))
