from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import Config

_engine = None
_session_factory = None


def init_db(config: Config) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(config.database_url, echo=False, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


def get_session_factory() -> async_sessionmaker:
    return _session_factory
