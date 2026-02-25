"""
FastAPI application entry point for SES Email API.
"""

import os
import signal
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import verify_token
from api.routers import config, db, drafts, email, history

app = FastAPI(
    title="SES Email API",
    description="Internal API for the SES Email Sender TUI",
    version="2.0.0",
)

# CORS — allow the local TUI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
