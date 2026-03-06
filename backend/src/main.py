from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Demand Forecasting System API",
    description="API for AI-powered Demand Intelligence Copilot",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Demand Forecasting API is running"}

from src.api.routers import ingestion, forecasts, recommendations

app.include_router(ingestion.router)
app.include_router(forecasts.router)
app.include_router(recommendations.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# AWS Lambda Handler
from mangum import Mangum
handler = Mangum(app)
