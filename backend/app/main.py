from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, weather, crop, yield_pred, mandi, plan, what_if

app = FastAPI(
    title="AgriOptima API",
    description="Unified Connected Machine Learning & Agricultural Decision Planning System",
    version="1.0.0"
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with /api prefix
app.include_router(health.router, prefix="/api", tags=["System Health"])
app.include_router(weather.router, prefix="/api", tags=["Weather Integration"])
app.include_router(crop.router, prefix="/api", tags=["Crop Suitability"])
app.include_router(yield_pred.router, prefix="/api", tags=["Crop Yield"])
app.include_router(mandi.router, prefix="/api", tags=["Mandi Analysis"])
app.include_router(plan.router, prefix="/api", tags=["Agricultural Planning"])
app.include_router(what_if.router, prefix="/api", tags=["What-If Scenarios"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
