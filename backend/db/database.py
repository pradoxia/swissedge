from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine():
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.debug)


engine = build_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
