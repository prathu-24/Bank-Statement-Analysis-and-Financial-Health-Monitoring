from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import upload, transactions, dashboard, recurring, anomalies, health, forecast, insights, privacy

app = FastAPI(
    title="FinSight API",
    description="AI-Based Bank Statement Intelligence & Financial Health Analyzer",
    version="1.0.0"
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

