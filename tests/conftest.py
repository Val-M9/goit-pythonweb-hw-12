import uuid
import anyio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from src.main import app
from src.database.db import get_db
from src.database.models import Base, User
from tests.constants import *
from tests.utils.hash_password import hash_password


engine = create_async_engine(
    ASYNC_DB_URL,
    connect_args={"check_same_thread": False, "uri": True},
)
TestingAsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def _create_test_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="module", autouse=True)
def setup_database() -> None:
    anyio.run(_create_test_tables)


async def _override_get_db():
    async with TestingAsyncSessionLocal() as session:
        yield session


# Override the app's DB dependency with async test session
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def user():
    suffix = uuid.uuid4().hex[:8]
    username = f"{USER_USERNAME}_{suffix}"
    email = f"{username}@example.com"

    async def _persist():
        async with TestingAsyncSessionLocal() as session:
            u = User(
                username=username,
                email=email,
                hashed_password=hash_password(USER_PASSWORD),
                confirmed=True,
            )
            session.add(u)
            await session.commit()
            await session.refresh(u)
            return u

    u = anyio.run(_persist)

    class _U:
        id = u.id
        username = u.username
        email = u.email
        password = USER_PASSWORD
        hashed_password = u.hashed_password

    return _U()


@pytest.fixture
def unconfirmed_user():
    suffix = uuid.uuid4().hex[:8]
    username = f"unconfirmed_{suffix}"
    email = f"{username}@example.com"

    async def _persist():
        async with TestingAsyncSessionLocal() as session:
            u = User(
                username=username,
                email=email,
                hashed_password=hash_password("testpass123"),
                confirmed=False,
            )
            session.add(u)
            await session.commit()
            await session.refresh(u)
            return u

    u = anyio.run(_persist)

    class _U:
        id = u.id
        username = u.username
        email = u.email
        password = "testpass123"

    return _U()


# Ensure pytest-anyio uses asyncio backend so trio is not required
@pytest.fixture
def anyio_backend():
    return "asyncio"


# Service tests that require a real SQLAlchemy User instance can use this fixture
@pytest.fixture
def user_model(user):
    async def _get():
        async with TestingAsyncSessionLocal() as session:
            stmt = select(User).filter_by(id=user.id)
            result = await session.execute(stmt)
            return result.scalar_one()

    return anyio.run(_get)
