import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, crop, yield_pred, mandi, plan, loss

app = FastAPI(
    title="AgriOptima API",
    description="Unified Connected Machine Learning & Agricultural Decision Planning System",
    version="1.0.0",
)

# Allow the local frontend. Deployments can supply their own comma-separated URLs.
# Credentialed requests must use explicit origins instead of a wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        url.strip()
        for url in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
        ).split(",")
        if url.strip()
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with /api prefix
app.include_router(loss.router, prefix="/api", tags=["Post-Harvest Loss"])
app.include_router(health.router, prefix="/api", tags=["System Health"])
app.include_router(crop.router, prefix="/api", tags=["Crop Suitability"])
app.include_router(yield_pred.router, prefix="/api", tags=["Crop Yield"])
app.include_router(mandi.router, prefix="/api", tags=["Mandi Analysis"])
app.include_router(plan.router, prefix="/api", tags=["Agricultural Planning"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
