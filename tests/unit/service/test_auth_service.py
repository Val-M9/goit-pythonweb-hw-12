import pytest
from jose import jwt
from fastapi import HTTPException

from src.services.auth import AuthService, Hash
from src.conf.config import settings
from tests.conftest import TestingAsyncSessionLocal


class FakeRedis:
    def __init__(self):
        self._store = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value, ex: int | None = None):
        self._store[key] = value


@pytest.mark.anyio
async def test_hash_verify_and_get_password_hash():
    h = Hash()
    pwd = "secret123"
    hashed = h.get_password_hash(pwd)
    assert hashed and hashed != pwd
    assert h.verify_password(pwd, hashed) is True
    assert h.verify_password("wrong", hashed) is False


@pytest.mark.anyio
async def test_create_tokens_have_types(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(AuthService, "_get_redis_client", lambda self: fake_redis)

    async with TestingAsyncSessionLocal() as session:
        svc = AuthService(session)
        data = {"sub": "alice"}
        access = await svc.create_access_token(data)
        refresh = await svc.create_refresh_token(data)
        email_t = await svc.create_email_token(data)
        reset_t = svc.create_reset_password_token(data)

        for tkn, ttype in (
            (access, "access"),
            (refresh, "refresh"),
            (email_t, "email"),
            (reset_t, "reset"),
        ):
            payload = jwt.decode(
                tkn, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            assert payload["sub"] == "alice"
            assert payload["token_type"] == ttype


@pytest.mark.anyio
async def test_get_current_user_valid(user, monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(AuthService, "_get_redis_client", lambda self: fake_redis)

    async with TestingAsyncSessionLocal() as session:
        svc = AuthService(session)
        token = await svc.create_access_token({"sub": user.username})
        current = await svc.get_current_user(token)
        assert current.username == user.username
        # Should cache the user under user:<username>
        assert fake_redis.get(f"user:{user.username}") is not None


@pytest.mark.anyio
async def test_verify_refresh_token_wrong_type(user, monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(AuthService, "_get_redis_client", lambda self: fake_redis)

    async with TestingAsyncSessionLocal() as session:
        svc = AuthService(session)
        access = await svc.create_access_token({"sub": user.username})
        u = await svc.verify_refresh_token(access)
        assert u is None


@pytest.mark.anyio
async def test_get_email_from_token_valid_and_wrong_type(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(AuthService, "_get_redis_client", lambda self: fake_redis)

    async with TestingAsyncSessionLocal() as session:
        svc = AuthService(session)
        email = "user@example.com"
        ok = await svc.create_email_token({"sub": email})
        assert await svc.get_email_from_token(ok) == email

        wrong = await svc.create_access_token({"sub": email})
        with pytest.raises(HTTPException) as ei:
            await svc.get_email_from_token(wrong)
        assert ei.value.status_code == 422


@pytest.mark.anyio
async def test_get_email_from_reset_token_valid_and_expired(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(AuthService, "_get_redis_client", lambda self: fake_redis)

    async with TestingAsyncSessionLocal() as session:
        svc = AuthService(session)
        email = "user2@example.com"
        valid = svc.create_reset_password_token({"sub": email})
        assert await svc.get_email_from_reset_token(valid) == email

        # Build an expired token manually
        from datetime import datetime, timedelta, UTC

        payload = {
            "sub": email,
            "token_type": "reset",
            "iat": datetime.now(UTC) - timedelta(days=2),
            "exp": datetime.now(UTC) - timedelta(days=1),
        }
        expired = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        with pytest.raises(HTTPException) as ei:
            await svc.get_email_from_reset_token(expired)
        assert ei.value.status_code == 401
