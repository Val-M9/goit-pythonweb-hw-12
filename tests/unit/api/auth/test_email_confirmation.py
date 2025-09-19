import anyio
from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient

from jose import jwt

from src.database.models import User
from src.conf.config import settings
from tests.constants import *
from tests.utils.hash_password import hash_password
from tests.conftest import TestingAsyncSessionLocal


class TestEmailConfirmation:
    def test_confirm_email_success(self, client: TestClient, unconfirmed_user):
        token_data = {"sub": unconfirmed_user.email, "token_type": "email"}
        token = jwt.encode(
            token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        response = client.get(f"/api/auth/confirmed_email/{token}")

        assert response.status_code == status.HTTP_200_OK
        assert "Email is not confirmed" in response.json()["message"]

    def test_confirm_email_already_confirmed(self, client: TestClient, user):
        token_data = {"sub": user.email, "token_type": "email"}
        token = jwt.encode(
            token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        response = client.get(f"/api/auth/confirmed_email/{token}")

        assert response.status_code == status.HTTP_200_OK
        assert "Email already confirmed" in response.json()["message"]

    def test_confirm_email_invalid_token(self, client: TestClient):
        invalid_token = "invalid.token.here"

        response = client.get(f"/api/auth/confirmed_email/{invalid_token}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_request_email_confirmation(self, client: TestClient):
        with patch("src.api.auth.send_confirm_email") as mock_email:
            response = client.post(
                "/api/auth/request_email", json={"email": "test@example.com"}
            )

            assert response.status_code == status.HTTP_200_OK
            assert (
                "Please check your email for confirmation" in response.json()["message"]
            )
