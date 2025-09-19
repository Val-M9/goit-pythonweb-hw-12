from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient


class TestUserRegistration:

    def test_register_user_success(self, client: TestClient):
        with patch("src.api.auth.send_confirm_email") as mock_email:
            response = client.post(
                "/api/auth/register",
                json={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "testpassword123",
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["username"] == "newuser"
            assert data["email"] == "newuser@example.com"
            assert "password" not in data
            assert "hashed_password" not in data
            mock_email.assert_called_once()

    def test_register_user_duplicate_email(self, client: TestClient, user):
        """Test registration with existing email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": user.email,  # Using existing email
                "password": "testpassword123",
            },
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "email already exists" in response.json()["detail"]

    def test_register_user_duplicate_username(self, client: TestClient, user):
        response = client.post(
            "/api/auth/register",
            json={
                "username": user.username,  # Using existing username
                "email": "different@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "name already exists" in response.json()["detail"]
