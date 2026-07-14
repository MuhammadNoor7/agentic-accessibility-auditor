"""FastAPI gateway — audit pipeline + HTML/PDF report download (Week 5)."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.routers.audit import router as audit_router
from backend.routers.auth_router import router as auth_router
from backend.routers.records_router import router as records_router

app = FastAPI(
    title="Agentic Accessibility Auditor API",
    version="0.4.0",
    description="POST /api/v1/audit runs parse → rules → agent report; GET …/report/download exports HTML/PDF.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(records_router, prefix="")


@app.get("/")
def read_root() -> dict:
    return {
        "status": "success",
        "message": "Agentic Accessibility Auditor API",
    }


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}
