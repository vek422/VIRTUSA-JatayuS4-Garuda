import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.database import engine
from app.db.base import Base
from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(level=logging.INFO)

app = FastAPI()

logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # Scheduler logic removed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router)


@app.get("/")
async def root():
    return {"status": "healthy", "message": "Jatayu AI Quiz Backend is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
