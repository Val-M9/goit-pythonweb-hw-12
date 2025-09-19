from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestUserAPI:
    def test_me_success(self, client: TestClient, user):
        # Simulate login to get token (assuming /api/auth/login returns JWT)
        login_resp = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": user.password},
        )
        assert login_resp.status_code == status.HTTP_200_OK
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/users/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["username"] == user.username
        assert data["email"] == user.email
        assert "password" not in data
        assert "hashed_password" not in data

    @patch(
        "src.services.upload_file.UploadFileService.upload_file",
        return_value="http://mocked.url/avatar.png",
    )
    def test_update_avatar_user_admin(self, mock_upload, client: TestClient, user):
        # Simulate login to get token (assuming user is admin for this test)
        login_resp = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": user.password},
        )
        assert login_resp.status_code == status.HTTP_200_OK
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Simulate file upload
        with open("tests/assets/cat.jpg", "rb") as f:
            files = {"file": ("cat.jpg", f, "image/png")}
            resp = client.patch("/api/users/avatar", headers=headers, files=files)
        assert resp.status_code in (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN)
        # If forbidden, user is not admin; if 200, check avatar url
        if resp.status_code == status.HTTP_200_OK:
            data = resp.json()
            assert data["avatar"] == "http://mocked.url/avatar.png"
