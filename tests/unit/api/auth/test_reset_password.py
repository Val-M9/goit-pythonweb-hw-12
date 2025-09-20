from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient



class TestPasswordReset:
    def test_forgot_password_success(self, client: TestClient, user):
        with patch("src.api.auth.send_password_reset_email") as mock_email:
            response = client.post(
                "/api/auth/password/forgot", json={"email": user.email}
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Reset link was sent" in response.json()["message"]
            mock_email.assert_called_once()

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        with patch("src.api.auth.send_password_reset_email") as mock_email:
            response = client.post(
                "/api/auth/password/forgot", json={"email": "nonexistent@example.com"}
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Reset link was sent" in response.json()["message"]
            mock_email.assert_not_called()

    @patch("src.services.auth.AuthService.create_reset_password_token")
    @patch("src.services.auth.AuthService.get_email_from_reset_token")
    def test_reset_password_success(
        self, mock_get_email, mock_create_token, client: TestClient, user
    ):
        reset_token = "valid_reset_token"
        mock_get_email.return_value = user.email
        mock_create_token.return_value = reset_token

        response = client.post(
            "/api/auth/password/reset",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Password updated" in response.json()["message"]
        mock_get_email.assert_called_once_with(reset_token)

    @patch("src.services.auth.AuthService.get_email_from_reset_token")
    def test_reset_password_invalid_token(self, mock_get_email, client: TestClient):
        mock_get_email.side_effect = Exception("Invalid token")

        response = client.post(
            "/api/auth/password/reset",
            json={"token": "invalid.token", "new_password": "newpassword123"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid reset token"