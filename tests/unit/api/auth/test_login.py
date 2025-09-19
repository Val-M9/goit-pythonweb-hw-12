from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt

from src.conf.config import settings


class TestUserLogin:
    def test_login_success(self, client: TestClient, user):
        response = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": user.password},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify token payload
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == user.username
        assert payload["token_type"] == "access"

    def test_login_wrong_password(self, client: TestClient, user):
        response = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect login or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect login or password" in response.json()["detail"]

    def test_login_unconfirmed_user(self, client: TestClient, unconfirmed_user):
        response = client.post(
            "/api/auth/login",
            data={
                "username": unconfirmed_user.username,
                "password": unconfirmed_user.password,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Email is not confirmed" in response.json()["detail"]
