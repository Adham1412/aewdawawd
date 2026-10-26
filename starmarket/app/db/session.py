from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_dev_schema() -> None:
    """Auto-create tables ONLY for local SQLite development. PostgreSQL/production use Alembic."""
    if settings.app_env.lower() != "production" and settings.database_url.startswith("sqlite"):
        from app.models import entities  # noqa: F401 - register models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
