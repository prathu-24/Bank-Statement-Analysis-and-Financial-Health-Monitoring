import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.services.telemetry import NetworkTracker
from app.routes.auth import require_authenticated_user
from app.routes import (
    upload, transactions, dashboard, recurring,
    anomalies, health, forecast, insights,
    privacy, evidence, leakage, query, auth
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables
    init_db()

    # Wire in-depth socket connect telemetry tracking
    NetworkTracker.install_hook()

    # Security announcement on encryption state
    encryption_key = os.environ.get("FINSIGHT_ENCRYPTION_KEY")
    if not encryption_key:
        print("\n" + "=" * 75)
        print("SECURITY NOTICE: FINSIGHT_ENCRYPTION_KEY environment variable is unset!")
        print("Statements are stored UNENCRYPTED in SQLite.")
        print("To persist encrypted data securely at rest, generate a 256-bit Fernet key:")
        print("    python scripts/generate_key.py")
        print("and configure FINSIGHT_ENCRYPTION_KEY in your environment.")
        print("CRITICAL WARNING: If an encryption key is lost, previously encrypted SQLite data")
        print("cannot be decrypted or recovered by anyone.")
        print("=" * 75 + "\n")
    else:
        print("\n" + "=" * 75)
        print("SECURITY NOTICE: FINSIGHT_ENCRYPTION_KEY detected.")
        print("At-rest statements are transparently encrypted with AES-128 Fernet cipher.")
        print("=" * 75 + "\n")

    yield

app = FastAPI(
    title="FinSight API",
    description="AI-Based Bank Statement Intelligence & Financial Health Analyzer",
    version="1.0.0",
    lifespan=lifespan
)

# Restrict CORS to explicit local development origins
LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """Unauthenticated health check endpoint."""
    return {
        "status": "healthy",
        "service": "FinSight Intelligence API",
        "version": "1.0.0"
    }

# Protect all functional API routes with signed JWT authentication dependency
auth_dep = [Depends(require_authenticated_user)]

app.include_router(upload.router, dependencies=auth_dep)
app.include_router(transactions.router, dependencies=auth_dep)
app.include_router(dashboard.router, dependencies=auth_dep)
app.include_router(recurring.router, dependencies=auth_dep)
app.include_router(anomalies.router, dependencies=auth_dep)
app.include_router(health.router, dependencies=auth_dep)
app.include_router(forecast.router, dependencies=auth_dep)
app.include_router(insights.router, dependencies=auth_dep)
app.include_router(privacy.router, dependencies=auth_dep)
app.include_router(evidence.router, dependencies=auth_dep)
app.include_router(leakage.router, dependencies=auth_dep)
app.include_router(query.router, dependencies=auth_dep)

# Auth router contains public /api/auth/login and authenticated /api/auth/me
app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
