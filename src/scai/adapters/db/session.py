import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Production/Development Database URL from environment or default
DATABASE_URL = os.getenv(
    "SCAI_DATABASE_URL",
    "postgresql+psycopg://scai:scaipassword@127.0.0.1:5432/scai?connect_timeout=5",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
