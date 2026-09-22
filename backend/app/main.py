import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.logging import logger
from app.knowledge.knowledge_loader import init_knowledge_base

# Import Routers
from app.api import (
    health, auth, projects, scans, inventory, findings,
    risk, scenarios, recommendations, graph, migration,
    validation, reports, knowledge, audit, x_engine, y_engine, z_engine, mosca_engine,
    prioritization, business_criticality, qars
)







@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    from app.core.database import sync_schema
    sync_schema()
    
    logger.info("Loading Cryptographic & PQC Knowledge Base...")
    db = SessionLocal()
    try:
        init_knowledge_base(db)
    finally:
        db.close()
        
    logger.info(f"{settings.PROJECT_NAME} backend initialized and ready.")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set CORS Middleware with explicit origins for production Vercel & local development
default_origins = [
    "https://frontend-phi-seven-18.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

allowed_origins = []
for orig in default_origins:
    clean = orig.strip().rstrip("/")
    if clean and clean not in allowed_origins:
        allowed_origins.append(clean)

cors_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("BACKEND_CORS_ORIGINS")
if cors_env:
    raw_list = cors_env.replace(" ", "\n").replace(",", "\n").split("\n")
    for item in raw_list:
        clean = item.strip().rstrip("/")
        if clean and clean != "*" and clean not in allowed_origins:
            allowed_origins.append(clean)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
api_v1_prefix = settings.API_V1_STR

app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(projects.router, prefix=api_v1_prefix)
app.include_router(scans.router, prefix=api_v1_prefix)
app.include_router(inventory.router, prefix=api_v1_prefix)
app.include_router(findings.router, prefix=api_v1_prefix)
app.include_router(risk.router, prefix=api_v1_prefix)
app.include_router(scenarios.router, prefix=api_v1_prefix)
app.include_router(recommendations.router, prefix=api_v1_prefix)
app.include_router(graph.router, prefix=api_v1_prefix)
app.include_router(migration.router, prefix=api_v1_prefix)
app.include_router(validation.router, prefix=api_v1_prefix)
app.include_router(reports.router, prefix=api_v1_prefix)
app.include_router(knowledge.router, prefix=api_v1_prefix)
app.include_router(audit.router, prefix=api_v1_prefix)
app.include_router(x_engine.router, prefix=api_v1_prefix)
app.include_router(y_engine.router, prefix=api_v1_prefix)
app.include_router(z_engine.router, prefix=api_v1_prefix)
app.include_router(mosca_engine.router, prefix=api_v1_prefix)
app.include_router(prioritization.router, prefix=api_v1_prefix)
app.include_router(business_criticality.router, prefix=api_v1_prefix)
app.include_router(qars.router, prefix=api_v1_prefix)







@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
