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
    validation, reports, knowledge, audit
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    
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

# Set CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
