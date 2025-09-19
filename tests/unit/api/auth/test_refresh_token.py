import pytest
import anyio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt

from src.database.models import User
from src.conf.config import settings
from tests.constants import *
from tests.utils.hash_password import hash_password
from tests.conftest import TestingAsyncSessionLocal


class TestTokenRefresh:
    def test_refresh_token_success(self, client: TestClient, user):
        login_response = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": user.password},
        )
        refresh_token = login_response.json()["refresh_token"]
        response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_refresh_token_wrong_type(self, client: TestClient, user):
        token_data = {"sub": user.username, "token_type": "access"}
        access_token = jwt.encode(
            token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": access_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
