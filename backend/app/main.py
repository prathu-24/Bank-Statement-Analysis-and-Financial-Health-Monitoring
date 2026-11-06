import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import (
    upload, transactions, dashboard, recurring,
    anomalies, health, forecast, insights,
    privacy, evidence, leakage, query, auth
)

app = FastAPI(
    title="FinSight API",
    description="AI-Based Bank Statement Intelligence & Financial Health Analyzer",
    version="1.0.0"
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

@app.on_event("startup")
def on_startup():
    init_db()

    # Security check: warn if encryption key is unset
    encryption_key = os.environ.get("FINSIGHT_ENCRYPTION_KEY")
    if not encryption_key:
        print("\n" + "=" * 75)
        print("SECURITY NOTICE: FINSIGHT_ENCRYPTION_KEY environment variable is unset!")
        print("FinSight is operating with volatile in-session memory encryption.")
        print("To persist encrypted data securely at rest, generate a 256-bit Fernet key:")
        print("    python scripts/generate_key.py")
        print("and configure FINSIGHT_ENCRYPTION_KEY in your environment.")
        print("CRITICAL WARNING: If an encryption key is lost, previously encrypted SQLite data")
        print("cannot be decrypted or recovered by anyone.")
        print("=" * 75 + "\n")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FinSight Intelligence API",
        "version": "1.0.0"
    }

# Register API routes
app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(recurring.router)
app.include_router(anomalies.router)
app.include_router(health.router)
app.include_router(forecast.router)
app.include_router(insights.router)
app.include_router(privacy.router)
app.include_router(evidence.router)
app.include_router(leakage.router)
app.include_router(query.router)
app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
