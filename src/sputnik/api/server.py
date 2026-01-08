"""FastAPI server for Sputnik."""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sputnik.api.middleware import clerk_auth_middleware
from sputnik.api.routes import query, rollouts, schema

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
if os.getenv("CLERK_SECRET_KEY") or os.getenv("ENABLE_AUTH", "false").lower() == "true":
    app.middleware("http")(clerk_auth_middleware)

# Include routers
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(rollouts.router, prefix="/api/v1", tags=["rollouts"])
app.include_router(schema.router, prefix="/api/v1", tags=["schema"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "Sputnik API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

