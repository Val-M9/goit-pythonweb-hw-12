from fastapi import status
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def contact_data():
    return {
        "name": "John",
        "surname": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+1234567890",
        "birthday": "1990-01-01",
        "additional_info": "Friend from work",
    }


@pytest.fixture
def update_contact_data():
    return {
        "name": "Jane",
        "surname": "Smith",
        "email": "jane.smith@example.com",
        "phone_number": "+1987654321",
        "birthday": "1992-02-02",
        "additional_info": "Colleague",
    }


@pytest.fixture
def delete_contact_data():
    return {
        "name": "Delete",
        "surname": "Me",
        "email": "delete@example.com",
        "phone_number": "+1111111111",
        "birthday": "2000-01-01",
        "additional_info": "To be deleted",
    }


class TestContactsAPI:
    def login_and_get_token(self, client, user):
        resp = client.post(
            "/api/auth/login",
            data={"username": user.username, "password": user.password},
        )
        assert resp.status_code == status.HTTP_200_OK
        return resp.json()["access_token"]

    def test_read_contacts_empty(self, client: TestClient, user):
        token = self.login_and_get_token(client, user)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/contacts/", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_create_and_read_contact(self, client: TestClient, user, contact_data):
        token = self.login_and_get_token(client, user)
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = client.post("/api/contacts/", json=contact_data, headers=headers)
        assert create_resp.status_code == status.HTTP_201_CREATED
        contact = create_resp.json()
        for k in contact_data:
            assert contact[k] == contact_data[k]

        # Read contact
        contact_id = contact["id"]
        get_resp = client.get(f"/api/contacts/{contact_id}", headers=headers)
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.json()["id"] == contact_id

    def test_update_contact(self, client: TestClient, user, update_contact_data):
        token = self.login_and_get_token(client, user)
        headers = {"Authorization": f"Bearer {token}"}
        # Create contact
        create_resp = client.post(
            "/api/contacts/", json=update_contact_data, headers=headers
        )
        contact_id = create_resp.json()["id"]
        # Update
        update_data = {"additional_info": "Best friend"}
        patch_resp = client.patch(
            f"/api/contacts/{contact_id}", json=update_data, headers=headers
        )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()["additional_info"] == "Best friend"

    def test_delete_contact(self, client: TestClient, user, delete_contact_data):
        token = self.login_and_get_token(client, user)
        headers = {"Authorization": f"Bearer {token}"}
        # Create contact
        create_resp = client.post(
            "/api/contacts/", json=delete_contact_data, headers=headers
        )
        contact_id = create_resp.json()["id"]
        # Delete
        del_resp = client.delete(f"/api/contacts/{contact_id}", headers=headers)
        assert del_resp.status_code == status.HTTP_200_OK
        assert del_resp.json()["id"] == contact_id
        # Confirm deletion
        get_resp = client.get(f"/api/contacts/{contact_id}", headers=headers)
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    def test_upcoming_birthdays_empty(self, client: TestClient, user):
        token = self.login_and_get_token(client, user)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/contacts/upcoming_birthdays/", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["contacts"] == []
        assert "No birthdays" in data["message"]
