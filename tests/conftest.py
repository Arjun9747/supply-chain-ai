import asyncio
import os
import sys

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from scai.adapters.db.base import Base

# Force WindowsSelectorEventLoopPolicy on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Explicitly use 127.0.0.1 and set connect_timeout
TEST_DATABASE_URL = os.getenv(
    "SCAI_TEST_DATABASE_URL",
    "postgresql+psycopg://scai:scaipassword@127.0.0.1:5432/scai?connect_timeout=5",
)


@pytest.fixture(scope="session")
def setup_database():
    """Create all tables synchronously before any async tests run."""
    sync_url = TEST_DATABASE_URL.replace("+psycopg", "")
    sync_engine = create_engine(sync_url, poolclass=NullPool)
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database: None):
    """Yields an async SQLAlchemy session with NullPool."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    await engine.dispose()
