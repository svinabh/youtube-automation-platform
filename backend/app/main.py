from fastapi import FastAPI
from app.api.endpoints import videos
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="YouTube Automation Platform")

app.include_router(videos.router, prefix="/videos", tags=["videos"])
