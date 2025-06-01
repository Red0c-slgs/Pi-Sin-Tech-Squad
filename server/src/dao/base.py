import contextvars
import functools
import threading
from typing import Any, Callable, Optional, TypeVar

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from utils.config import CONFIG

Base = declarative_base()

db_config = CONFIG.db

# Sync engine
engine = create_engine(f"postgresql+psycopg2://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}")

# Async engine
async_engine = create_async_engine(f"postgresql+asyncpg://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}")


class SessionFactory:
    def __init__(self):
        # Sync session maker
        self.sessionmaker = sessionmaker(engine)
        self.thread_load = threading.local()

        # Async session maker
        self.async_sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False)
        self.async_context_var = contextvars.ContextVar[Optional[AsyncSession]]("async_session", default=None)

    # Sync methods
    def open(self):
        if hasattr(self.thread_load, "db_session") and self.thread_load.db_session:
            return self.thread_load.db_session
        session = self.sessionmaker()
        self.thread_load.db_session = session
        return session

    def get(self) -> Session:
        res = self.get_or_none()
        if res:
            return res
        raise Exception("DB Session is required")

    def get_or_none(self) -> Session | None:
        if hasattr(self.thread_load, "db_session") and self.thread_load.db_session:
            return self.thread_load.db_session
        return None

    def close(self):
        session = self.thread_load.db_session
        session.commit()
        self.thread_load.db_session = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # Async methods
    async def open_async(self) -> AsyncSession:
        current_session = self.async_context_var.get()
        if current_session is not None:
            return current_session

        session = self.async_sessionmaker()
        self.async_context_var.set(session)
        return session

    def get_async(self) -> AsyncSession:
        res = self.get_async_or_none()
        if res:
            return res
        raise Exception("DB Session is required")

    def get_async_or_none(self) -> AsyncSession | None:
        return self.async_context_var.get()

    async def close_async(self):
        session = self.async_context_var.get()
        if session is not None:
            await session.commit()
            await session.close()
            self.async_context_var.set(None)

    async def __aenter__(self):
        return await self.open_async()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_async()


session_factory = SessionFactory()


def with_db_session(func):
    """Decorator for synchronous functions that need a database session"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if session_factory.get_or_none() is None:
            try:
                session_factory.open()
                return func(*args, **kwargs)
            finally:
                session_factory.close()
        else:
            return func(*args, **kwargs)

    return wrapper


T = TypeVar("T")


def with_async_db_session(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for async functions that need a database session"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if session_factory.get_async_or_none() is None:
            try:
                await session_factory.open_async()
                return await func(*args, **kwargs)
            finally:
                await session_factory.close_async()
        else:
            return await func(*args, **kwargs)

    return wrapper


async def next_id_from_sequence_async(sequence_name: str) -> int:
    session = session_factory.get_async()
    result = await session.execute(text(f"SELECT nextval('{sequence_name}')"))
    res = result.first()
    if res is None:
        raise Exception(f"Failed to fetch nextval from sequence {sequence_name}")
    return int(res[0])



def required(val: T | None, field_name: str) -> T:
    if val is not None:
        return val
    else:
        raise Exception(f"Field {field_name} is required")
