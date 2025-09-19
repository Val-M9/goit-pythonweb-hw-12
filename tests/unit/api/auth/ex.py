class TestTokenRefresh:
    """Test token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, user):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": user.password},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_refresh_token_wrong_type(self, client: TestClient, user):
        """Test refresh with access token instead of refresh token."""
        # Create access token
        token_data = {"sub": user.username, "token_type": "access"}
        access_token = jwt.encode(
            token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": access_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordReset:
    """Test password reset endpoints."""

    def test_forgot_password_success(self, client: TestClient, user):
        """Test successful forgot password request."""
        with patch("src.api.auth.send_password_reset_email") as mock_email:
            response = client.post(
                "/api/auth/password/forgot", json={"email": user.email}
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Reset link was sent" in response.json()["message"]
            mock_email.assert_called_once()

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test forgot password with non-existent email."""
        with patch("src.api.auth.send_password_reset_email") as mock_email:
            response = client.post(
                "/api/auth/password/forgot", json={"email": "nonexistent@example.com"}
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Reset link was sent" in response.json()["message"]
            # Email should not be sent for non-existent users
            mock_email.assert_not_called()

    @patch("src.services.auth.AuthService.create_reset_password_token")
    @patch("src.services.auth.AuthService.get_email_from_reset_token")
    def test_reset_password_success(
        self, mock_get_email, mock_create_token, client: TestClient, user
    ):
        """Test successful password reset."""
        reset_token = "valid.reset.token"
        mock_get_email.return_value = user.email

        response = client.post(
            "/api/auth/password/reset",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Password updated" in response.json()["message"]
        mock_get_email.assert_called_once_with(reset_token)

    @patch("src.services.auth.AuthService.get_email_from_reset_token")
    def test_reset_password_invalid_token(self, mock_get_email, client: TestClient):
        """Test password reset with invalid token."""
        mock_get_email.side_effect = Exception("Invalid token")

        response = client.post(
            "/api/auth/password/reset",
            json={"token": "invalid.token", "new_password": "newpassword123"},
        )

        assert response.status_code != status.HTTP_200_OK


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    def test_full_auth_flow(self, client: TestClient):
        """Test complete authentication flow: register -> login -> refresh."""
        # 1. Register user
        with patch("src.api.auth.send_confirm_email"):
            register_response = client.post(
                "/api/auth/register",
                json={
                    "username": "flowuser",
                    "email": "flowuser@example.com",
                    "password": "testpass123",
                },
            )
            assert register_response.status_code == status.HTTP_201_CREATED

        # 2. Confirm email manually (simulate clicking confirmation link)
        async def _confirm_user():
            async with TestingAsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).filter(User.username == "flowuser")
                )
                user = result.scalar_one()
                user.confirmed = True
                await session.commit()

        anyio.run(_confirm_user)

        # 3. Login
        login_response = client.post(
            "/api/auth/login", data={"username": "flowuser", "password": "testpass123"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        tokens = login_response.json()

        # 4. Refresh token
        refresh_response = client.post(
            "/api/auth/refresh-token", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == status.HTTP_200_OK

        # 5. Verify new access token is different
        new_tokens = refresh_response.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] == tokens["refresh_token"]


class TestAuthServiceMethods:
    """Test AuthService methods that may need additional validation."""

    def test_missing_request_fields(self, client: TestClient):
        """Test endpoints with missing required fields."""
        # Missing password in registration
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                # Missing password
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing refresh_token in refresh endpoint
        response = client.post("/api/auth/refresh-token", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing email in forgot password
        response = client.post("/api/auth/password/forgot", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_malformed_json_requests(self, client: TestClient):
        """Test endpoints with malformed JSON."""
        response = client.post(
            "/api/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Additional fixtures for complex test scenarios
@pytest.fixture
async def confirmed_user_in_db():
    """Create a confirmed user directly in the database."""
    async with TestingAsyncSessionLocal() as session:
        user = User(
            username="confirmeduser",
            email="confirmed@example.com",
            hashed_password=hash_password("testpass123"),
            confirmed=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def unconfirmed_user_in_db():
    """Create an unconfirmed user directly in the database."""
    async with TestingAsyncSessionLocal() as session:
        user = User(
            username="unconfirmeduser",
            email="unconfirmed@example.com",
            hashed_password=hash_password("testpass123"),
            confirmed=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
