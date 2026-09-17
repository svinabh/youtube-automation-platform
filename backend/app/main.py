from fastapi import FastAPI
from app.analytics.router import router as analytics_router

app = FastAPI(title="YouTube Content Platform API", version="1.0.0")

app.include_router(analytics_router)
