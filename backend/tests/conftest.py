import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, async_session_maker
from app.main import app
from app.seed import clean_test_artifacts


@pytest.fixture(autouse=True)
async def cleanup_db_connections():
    """Clean up test entities and ensure engine connection pool is cleanly closed between test event loops."""
    await clean_test_artifacts()
    yield
    try:
        await clean_test_artifacts()
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated async session for direct test assertions or seeding."""
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client bound to FastAPI application with high concurrency limits."""
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        limits=limits,
    ) as ac:
        yield ac
