import uuid
from datetime import date
import pytest
from fastapi import status

from src.database.models import User
from tests.conftest import TestingAsyncSessionLocal


def _auth_headers(client, username: str, password: str):
    r = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.anyio
async def test_contacts_requires_auth(client):
    # No token should yield 401
    r = client.get("/api/contacts/")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

    # Also on create
    r = client.post("/api/contacts/", json={})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_contacts_crud_flow(client, user):
    # Login with existing confirmed user fixture
    r = client.post(
        "/api/auth/login",
        data={"username": user.username, "password": user.password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Create a contact
    body = {
        "name": "Alice",
        "surname": "Smith",
        "email": f"alice_{uuid.uuid4().hex[:8]}@example.com",
        "phone_number": f"+1000{uuid.uuid4().hex[:8]}",
        "birthday": date.today().isoformat(),
        "additional_info": "Teammate",
    }
    r = client.post("/api/contacts/", json=body, headers=headers)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    created = r.json()
    contact_id = created["id"]

    # List contacts and ensure our contact is present
    r = client.get("/api/contacts/?skip=0&limit=10", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    lst = r.json()
    assert any(c["id"] == contact_id for c in lst)

    # Get by id
    r = client.get(f"/api/contacts/{contact_id}", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["email"] == created["email"]

    # Update via PATCH
    patch = {"additional_info": "Updated note"}
    r = client.patch(f"/api/contacts/{contact_id}", json=patch, headers=headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["additional_info"] == "Updated note"

    # Upcoming birthdays endpoint (may or may not include, but should return structure)
    r = client.get("/api/contacts/upcoming_birthdays/?days=10", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert "message" in data and "contacts" in data

    # Delete
    r = client.delete(f"/api/contacts/{contact_id}", headers=headers)
    assert r.status_code == status.HTTP_200_OK

    # Subsequent get should be 404
    r = client.get(f"/api/contacts/{contact_id}", headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_cross_user_isolation(client, monkeypatch):
    # Avoid real email sending on registration flow
    monkeypatch.setattr("src.api.auth.send_confirm_email", lambda *args, **kwargs: None)

    # Register user A
    uname_a = f"usera_{uuid.uuid4().hex[:6]}"
    email_a = f"{uname_a}@example.com"
    payload_a = {"username": uname_a, "email": email_a, "password": "passA!23"}
    r = client.post("/api/auth/register", json=payload_a)
    assert r.status_code == status.HTTP_201_CREATED

    # Confirm A in DB
    async with TestingAsyncSessionLocal() as session:
        from sqlalchemy import select

        res = await session.execute(select(User).filter_by(email=email_a))
        ua = res.scalar_one()
        ua.confirmed = True
        await session.commit()

    headers_a = _auth_headers(client, uname_a, "passA!23")

    # Create a contact for A
    body_a = {
        "name": "OnlyA",
        "surname": "Contact",
        "email": f"onlya_{uuid.uuid4().hex[:8]}@example.com",
        "phone_number": f"+3555{uuid.uuid4().hex[:8]}",
        "birthday": date.today().isoformat(),
        "additional_info": "belongs to A",
    }
    r = client.post("/api/contacts/", json=body_a, headers=headers_a)
    assert r.status_code == status.HTTP_201_CREATED
    contact_id_a = r.json()["id"]

    # Register user B and confirm
    uname_b = f"userb_{uuid.uuid4().hex[:6]}"
    email_b = f"{uname_b}@example.com"
    payload_b = {"username": uname_b, "email": email_b, "password": "passB!23"}
    r = client.post("/api/auth/register", json=payload_b)
    assert r.status_code == status.HTTP_201_CREATED

    async with TestingAsyncSessionLocal() as session:
        from sqlalchemy import select

        res = await session.execute(select(User).filter_by(email=email_b))
        ub = res.scalar_one()
        ub.confirmed = True
        await session.commit()

    headers_b = _auth_headers(client, uname_b, "passB!23")

    # B should not see A's contact in list
    r = client.get("/api/contacts/", headers=headers_b)
    assert r.status_code == status.HTTP_200_OK
    ids_b = {c["id"] for c in r.json()}
    assert contact_id_a not in ids_b

    # B should get 404 when trying to access A's contact by id
    r = client.get(f"/api/contacts/{contact_id_a}", headers=headers_b)
    assert r.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_update_delete_nonexistent_contact_returns_404(client, user):
    headers = _auth_headers(client, user.username, user.password)
    nonexist = 999999
    r = client.patch(f"/api/contacts/{nonexist}", json={"name": "X"}, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND
    r = client.delete(f"/api/contacts/{nonexist}", headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_create_contact_validation_error_returns_422(client, user):
    headers = _auth_headers(client, user.username, user.password)
    # Missing required fields (e.g., name, surname, email, phone_number)
    r = client.post("/api/contacts/", json={}, headers=headers)
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
