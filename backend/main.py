import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI application
app = FastAPI(
    title="YouTube Automation Platform API",
    version="0.1.0",
    description="Backend for the AI-Powered YouTube Content & Growth Automation Platform"
)

# Configure CORS for development
# DO NOT overly permissive in production!
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000 http://127.0.0.1:3000")
allowed_origins = allowed_origins_str.split()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API v1 router
api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.get("/health")
def health_check():
    """
    Basic health check endpoint returning HTTP 200 with deterministic status.
    """
    return {"status": "ok", "service": "youtube-automation-platform"}

# Include the router in the application
app.include_router(api_v1_router)
