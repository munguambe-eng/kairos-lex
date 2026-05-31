from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.api import auth, jobs, reports, exceptions, audit, dashboard, generate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if not using alembic in dev
    yield
    # Shutdown


app = FastAPI(
    title="Kairos Compliance Portal API",
    description="Regulatory reporting engine for GIFIM and Banco de Moçambique",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,       prefix="/api/auth",       tags=["Authentication"])
app.include_router(dashboard.router,  prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(jobs.router,       prefix="/api/jobs",       tags=["Jobs & Upload"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(exceptions.router, prefix="/api/exceptions", tags=["Exceptions"])
app.include_router(audit.router,      prefix="/api/audit",      tags=["Audit Logs"])
app.include_router(generate.router,   prefix="/api/generate",   tags=["Generate from DB"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "kairos-backend"}
