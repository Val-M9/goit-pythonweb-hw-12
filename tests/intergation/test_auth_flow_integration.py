import uuid
import pytest
from fastapi import status

from tests.conftest import TestingAsyncSessionLocal
from src.database.models import User


@pytest.mark.anyio
async def test_register_then_login_after_confirm(monkeypatch, client):
    # Avoid real email sending
    monkeypatch.setattr(
        "src.services.email.send_confirm_email", lambda *args, **kwargs: None
    )

    # Register a new user
    uname = f"int_{uuid.uuid4().hex[:8]}"
    email = f"{uname}@example.com"
    payload = {"username": uname, "email": email, "password": "passw0rd!"}

    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    data = r.json()
    assert data["username"] == uname
    assert data["email"] == email

    # Login should fail until confirmed
    r = client.post(
        "/api/auth/login",
        data={"username": uname, "password": "passw0rd!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

    # Confirm the user directly in DB
    async with TestingAsyncSessionLocal() as session:
        # Fetch user
        from sqlalchemy import select

        res = await session.execute(select(User).filter_by(email=email))
        u = res.scalar_one()
        u.confirmed = True
        await session.commit()

    # Login should succeed now
    r = client.post(
        "/api/auth/login",
        data={"username": uname, "password": "passw0rd!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    tokens = r.json()
    assert "access_token" in tokens and "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Use access token with /api/users/me
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = client.get("/api/users/me", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    me = r.json()
    assert me["username"] == uname
    assert me["email"] == email
