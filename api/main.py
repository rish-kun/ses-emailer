"""
FastAPI application entry point for SES Email API.
"""

import asyncio
import os
import signal
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import verify_token
from api.routers import config, db, drafts, email, history, jobs, templates
from api.worker import worker_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background send worker for the app's lifetime."""
    stop_event = asyncio.Event()
    task = asyncio.create_task(worker_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        try:
            await asyncio.wait_for(task, timeout=5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            task.cancel()


app = FastAPI(
    title="SES Email API",
    description="Internal API for the SES Email Sender TUI",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — the API is bound to localhost and only the local TUI talks to it, so
# restrict origins to loopback rather than the wildcard "*".
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(email.router, prefix="/api", tags=["Email"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(db.router, prefix="/api/db", tags=["Database"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])


# ── Health check (no auth) ────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Shutdown (called by TUI on exit) ────────────────────────────────────
@app.post("/shutdown")
async def shutdown(_token: str = Depends(verify_token)):
    """Gracefully stop the API server by sending SIGTERM to self."""
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting down"}


# ── Runner ────────────────────────────────────────────────────────────
def run_server(host: str = "127.0.0.1", port: int = 8787):
    """Run the API server."""
    uvicorn.run("api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run_server()
