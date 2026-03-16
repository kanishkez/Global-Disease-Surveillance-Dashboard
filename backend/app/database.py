from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sync_sessionmaker
from app.config import get_settings

settings = get_settings()

# Async engine for FastAPI
async_engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for Celery workers
sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
SyncSessionLocal = sync_sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
