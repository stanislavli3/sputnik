"""FastAPI server for Sputnik."""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sputnik.api.middleware import clerk_auth_middleware
from sputnik.api.routes import query, queries, reviews, risk, metrics, templates, export, rollouts, schema, models

app = FastAPI(
    title="Sputnik API",
    description="AI reliability layer for ERP analytics",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        os.getenv("FRONTEND_URL", "http://localhost:8080"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clerk authentication middleware (if enabled)
# Only enable if explicitly configured to avoid blocking requests in dev mode
clerk_secret = os.getenv("CLERK_SECRET_KEY")
enable_auth = os.getenv("ENABLE_AUTH", "false").lower() == "true"
if clerk_secret and enable_auth:
    app.middleware("http")(clerk_auth_middleware)
    print("🔐 Clerk authentication enabled")
else:
    print("🔓 Running without authentication (dev mode)")

# Include routers
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(queries.router, prefix="/api/v1", tags=["queries"])
app.include_router(reviews.router, prefix="/api/v1", tags=["reviews"])
app.include_router(risk.router, prefix="/api/v1", tags=["risk"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(rollouts.router, prefix="/api/v1", tags=["rollouts"])
app.include_router(schema.router, prefix="/api/v1", tags=["schema"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "Sputnik API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint with dependency checks.
    
    Returns:
        Health status with dependency information
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {},
    }
    
    # Check database connectivity
    try:
        from sputnik.api.db import get_history_db
        db = get_history_db()
        conn = db._get_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
    
    # Check job queue
    try:
        from sputnik.api.jobs import get_job_queue
        queue = get_job_queue()
        health_status["dependencies"]["job_queue"] = "healthy"
        health_status["dependencies"]["job_queue_size"] = len(queue._queue)
    except Exception as e:
        health_status["dependencies"]["job_queue"] = f"unhealthy: {str(e)}"
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Start job queue
    get_job_queue()
    print("✅ Job queue started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Stop job queue
    queue = get_job_queue()
    queue.stop()
    print("✅ Job queue stopped")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

