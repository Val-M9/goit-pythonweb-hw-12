import uuid
import pytest

from src.services.users import UserService
from src.schemas.schemas import UserCreate
from src.database.models import User
from tests.conftest import TestingAsyncSessionLocal


@pytest.mark.anyio
async def test_create_user_with_gravatar(monkeypatch):
    # Mock Gravatar.get_image to return a fixed URL
    class DummyG:
        def __init__(self, email):
            self.email = email
        def get_image(self):
            return f"https://gravatar.example.com/avatar/{self.email}"

    monkeypatch.setattr("src.services.users.Gravatar", DummyG)

    async with TestingAsyncSessionLocal() as session:
        svc = UserService(session)
        email = f"u_{uuid.uuid4().hex[:8]}@example.com"
        body = UserCreate(username=f"user_{uuid.uuid4().hex[:6]}", email=email, password="pwd12345")
        user = await svc.create_user(body)
        assert isinstance(user, User)
        assert user.email == email
        assert user.avatar and user.avatar.startswith("https://gravatar.example.com/avatar/")


@pytest.mark.anyio
async def test_create_user_gravatar_failure(monkeypatch):
    class DummyG:
        def __init__(self, email):
            raise RuntimeError("gravatar init fail")

    monkeypatch.setattr("src.services.users.Gravatar", DummyG)

    async with TestingAsyncSessionLocal() as session:
        svc = UserService(session)
        email = f"u_{uuid.uuid4().hex[:8]}@example.com"
        body = UserCreate(username=f"user_{uuid.uuid4().hex[:6]}", email=email, password="pwd12345")
        user = await svc.create_user(body)
        assert user.email == email
        assert user.avatar is None


@pytest.mark.anyio
async def test_get_and_update_user(user):
    async with TestingAsyncSessionLocal() as session:
        svc = UserService(session)
        got_by_username = await svc.get_user_by_username(user.username)
        got_by_email = await svc.get_user_by_email(user.email)
        got_by_id = await svc.get_user_by_id(user.id)
        assert got_by_username and got_by_username.id == user.id
        assert got_by_email and got_by_email.username == user.username
        assert got_by_id and got_by_id.email == user.email

        await svc.confirmed_email(user.email)
        updated = await svc.update_avatar_url(user.email, "http://cdn.example.com/a.png")
        assert updated.avatar == "http://cdn.example.com/a.png"
