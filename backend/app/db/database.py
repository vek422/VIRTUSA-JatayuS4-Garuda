import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(os.path.dirname(__file__)), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)

# Synchronous engine and session for Celery tasks
sync_engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(
    bind=sync_engine, expire_on_commit=False, autoflush=False, autocommit=False
)

# Dependency for FastAPI routes


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
